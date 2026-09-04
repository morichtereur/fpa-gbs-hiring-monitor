"""
Two-stage classification, same architecture as gbs-agentic-shift.

Stage 1 (taxonomy.py): deterministic and auditable — decides the clear cases
and the GBS signal for every posting.
Stage 2 (here): the LLM decides ONLY the tier of the residual the taxonomy
flagged ambiguous (no process phrases, or a tie between tiers). Its label and
reason are logged so a reader can audit stage 2 the same way as stage 1.
"""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import duckdb

from src import config as C
from src.taxonomy import classify_text

FALLBACK_PROMPT = """You classify a finance job posting into exactly one tier of FP&A work, by what the role CENTRES on:

- core: executing financial analysis, cost accounting, or management/performance reporting.
- planning: owning or running budgeting, forecasting, annual planning, or capex planning.
- strategic: strategic/long-range planning, corporate development, or M&A support.
- none: not FP&A work at all (bookkeeping, AP/AR processing, audit, sales, IT, credit collection, unrelated roles).

A role that merely mentions several tiers goes to the tier its day-to-day work centres on. Pure accounting execution (journal entries, reconciliations, month-end close processing) is none, not core.

Return ONLY compact JSON: {"tier": "...", "reason": "<12 words"}. No prose, no markdown."""


def _make_client():
    if C.CLASSIFIER_BACKEND == "bedrock":
        # Bearer-token auth: botocore prefers AWS_BEARER_TOKEN_BEDROCK
        # automatically. EU needs an inference-profile model id.
        import boto3
        from botocore.config import Config
        return boto3.client("bedrock-runtime", region_name=C.AWS_REGION,
                            config=Config(read_timeout=C.MODEL_TIMEOUT,
                                          retries={"max_attempts": 2}))
    from anthropic import Anthropic
    return Anthropic(api_key=C.ANTHROPIC_API_KEY,
                     timeout=C.MODEL_TIMEOUT, max_retries=1)


def _model_label(client, title: str, description: str) -> dict:
    text = f"TITLE: {title}\n\nDESCRIPTION: {description[:2500]}"
    if C.CLASSIFIER_BACKEND == "bedrock":
        resp = client.converse(
            modelId=C.BEDROCK_MODEL,
            system=[{"text": FALLBACK_PROMPT}],
            messages=[{"role": "user", "content": [{"text": text}]}],
            inferenceConfig={"maxTokens": 120},
        )
        raw = "".join(b.get("text", "")
                      for b in resp["output"]["message"]["content"]).strip()
    else:
        msg = client.messages.create(
            model=C.CLASSIFIER_MODEL,
            max_tokens=120,
            system=FALLBACK_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
        raw = "".join(b.text for b in msg.content if b.type == "text").strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        out = json.loads(raw)
        if out.get("tier") not in {"core", "planning", "strategic", "none"}:
            out["tier"] = "none"
        return out
    except json.JSONDecodeError:
        return {"tier": "none", "reason": "unparseable model output"}


_RATE_LOCK = threading.Lock()
_NEXT_REQUEST = 0.0
_THREAD_STATE = threading.local()


def _model_label_safe(title: str, description: str) -> dict:
    global _NEXT_REQUEST
    with _RATE_LOCK:
        now = time.monotonic()
        wait = max(0.0, _NEXT_REQUEST - now)
        _NEXT_REQUEST = max(now, _NEXT_REQUEST) + C.MODEL_REQUEST_INTERVAL
    if wait:
        time.sleep(wait)
    try:
        client = getattr(_THREAD_STATE, "client", None)
        if client is None:
            client = _make_client()
            _THREAD_STATE.client = client
        return _model_label(client, title, description)
    except Exception as exc:
        return {"tier": "none", "reason": f"model request failed: {type(exc).__name__}"}


def run() -> None:
    con = duckdb.connect(str(C.DB_PATH))
    con.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id VARCHAR PRIMARY KEY,
            tier VARCHAR,
            gbs_signal BOOLEAN,
            source VARCHAR,          -- 'taxonomy' | 'model'
            score_core INT,
            score_planning INT,
            score_strategic INT,
            proc_hits VARCHAR,
            gbs_hits VARCHAR,
            reason VARCHAR
        )
    """)

    if C.RECLASSIFY:
        rows = con.execute("SELECT id, title, description FROM postings ORDER BY id").fetchall()
    else:
        rows = con.execute("""
            SELECT p.id, p.title, p.description FROM postings p
            LEFT JOIN labels l ON p.id = l.id WHERE l.id IS NULL
        """).fetchall()

    if not rows:
        print("Nothing new to classify.")
        return

    tax_rows, model_tasks = [], []
    for pid, title, desc in rows:
        r = classify_text(desc, title=title)
        (model_tasks if r.ambiguous else tax_rows).append((pid, title, desc, r))

    for pid, _, _, r in tax_rows:
        row = r.to_row()
        con.execute(
            "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?,?,?,?,?)",
            [pid, r.tier, r.gbs_signal, "taxonomy", row["score_core"],
             row["score_planning"], row["score_strategic"], row["proc_hits"],
             row["gbs_hits"], ""],
        )

    model_results = {}
    if model_tasks:
        workers = max(1, min(C.MODEL_WORKERS, len(model_tasks)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_model_label_safe, title, desc): (pid, r)
                       for pid, title, desc, r in model_tasks}
            for future in as_completed(futures):
                pid, r = futures[future]
                model_results[pid] = (r, future.result())

    for pid, _, _, r in model_tasks:
        tax_result, out = model_results[pid]
        row = tax_result.to_row()
        con.execute(
            "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?,?,?,?,?)",
            [pid, out["tier"], tax_result.gbs_signal, "model", row["score_core"],
             row["score_planning"], row["score_strategic"], row["proc_hits"],
             row["gbs_hits"], out.get("reason", "")],
        )

    con.close()
    print(f"Classified {len(rows)}: {len(tax_rows)} by taxonomy, "
          f"{len(model_tasks)} by model fallback.")


if __name__ == "__main__":
    run()
