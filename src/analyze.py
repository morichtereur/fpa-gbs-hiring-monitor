"""
Aggregate the classified postings into the study's exhibits.

Everything here is a GROUP BY over the labels table — no model, no judgment.
Output: printed tables plus data/results.json for the dashboard.

GBS delivery is read through three independent lenses, each honest on its own
terms, because no single one is sufficient:

  1. phrase signal — the posting names a shared-services / GBS / GCC / CoE
     context. High precision, low recall: Adzuna truncates descriptions at
     ~500 characters, so absence of the phrase proves nothing.
  2. BPO employer — the posting sits at a third-party GBS provider
     (Accenture, Genpact, TCS, ...). Outsourced GBS delivery by construction.
  3. delivery market — the posting sits in a low-cost delivery hub
     (in, pl, mx, ...). Where GBS capacity concentrates, but not all of it
     is GBS — this lens is reported separately, never folded into the signal.

Advisory employers (consultancies that advise on FP&A rather than run it)
are excluded from every headline number; the excluded count is reported.

The comparison logic, stated once: the EY survey measures the share of
COMPANIES whose GBS supports a process; this study measures the share of
POSTINGS that mention or centre on it. Levels are not comparable across the
two — only the ORDERING (the gradient) is.
"""

from __future__ import annotations

import json

import duckdb

from src import config as C
from src.orgtype import market_type, org_type
from src.taxonomy import PROCESSES

# EY survey reference values (coordinate-verified from the published PDF).
EY_SURVEY = {
    "current": {
        "performance_reporting": 53, "financial_analysis": 50, "cost_accounting": 47,
        "budgeting": 38, "forecasting": 35, "capex_management": 26,
        "strategic_planning": 18, "ma_support": 15,
    },
    "planned": {
        "performance_reporting": 35, "financial_analysis": 29, "cost_accounting": 24,
        "budgeting": 24, "forecasting": 24, "capex_management": 15,
        "strategic_planning": 6, "ma_support": 3,
    },
}

TIERS3 = ("core", "planning", "strategic")


def run() -> dict:
    con = duckdb.connect(str(C.DB_PATH), read_only=True)
    raw = con.execute("""
        SELECT p.id, p.country, p.title, p.company, l.tier, l.gbs_signal,
               l.source, l.proc_hits
        FROM postings p JOIN labels l ON p.id = l.id
    """).fetchall()
    con.close()

    rows = [{"id": r[0], "country": r[1], "title": r[2], "company": r[3],
             "tier": r[4], "phrase": bool(r[5]), "source": r[6],
             "proc_hits": r[7] or "", "org": org_type(r[3]),
             "market": market_type(r[1])} for r in raw]

    advisory = [r for r in rows if r["org"] == "advisory"]
    inscope = [r for r in rows if r["org"] != "advisory"]
    fpa = [r for r in inscope if r["tier"] in TIERS3]

    def tier_mix(subset):
        n = len(subset) or 1
        return {t: round(100 * sum(1 for r in subset if r["tier"] == t) / n, 1)
                for t in TIERS3} | {"n": len(subset)}

    def mention_rates(subset):
        n = len(subset) or 1
        return {proc: round(100 * sum(1 for r in subset
                                      if f"{proc}:" in r["proc_hits"]) / n, 1)
                for proc in PROCESSES}

    phrase = [r for r in fpa if r["phrase"]]
    bpo = [r for r in fpa if r["org"] == "bpo"]
    gbs = [r for r in fpa if r["phrase"] or r["org"] == "bpo"]
    rest = [r for r in fpa if not (r["phrase"] or r["org"] == "bpo")]

    out = {
        "fetched": len(rows),
        "excluded_advisory": len(advisory),
        "excluded_none": len(inscope) - len(fpa),
        "fpa": len(fpa),
        "by_source": {s: sum(1 for r in rows if r["source"] == s)
                      for s in ("taxonomy", "model")},
        "lenses": {
            "phrase_signal": tier_mix(phrase),
            "bpo_employer": tier_mix(bpo),
            "gbs_combined": tier_mix(gbs),
            "no_gbs_evidence": tier_mix(rest),
            "all_fpa": tier_mix(fpa),
        },
        "overlap_phrase_and_bpo": sum(1 for r in fpa
                                      if r["phrase"] and r["org"] == "bpo"),
        "process_mentions": {
            "gbs_combined": mention_rates(gbs),
            "no_gbs_evidence": mention_rates(rest),
        },
        "by_market_type": {},
        "ey_survey": EY_SURVEY,
    }

    for mtype in ("delivery", "retained", "mixed"):
        subset = [r for r in fpa if r["market"] == mtype]
        gsub = [r for r in subset if r["phrase"] or r["org"] == "bpo"]
        out["by_market_type"][mtype] = {
            "n": len(subset),
            "gbs_combined_share": round(100 * len(gsub) / (len(subset) or 1), 1),
            "tier_mix_all": tier_mix(subset),
            "tier_mix_gbs": tier_mix(gsub),
        }

    C.DATA.mkdir(exist_ok=True)
    with open(C.DATA / "results.json", "w") as f:
        json.dump(out, f, indent=2)

    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    run()
