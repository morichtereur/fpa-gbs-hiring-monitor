"""
Draw a stratified sample for the hand-labelled gold set.

Stratified across predicted tier x GBS signal x label source so the gold set
exercises every cell the classifier can land in — including the model
fallback, which is where errors hide. The template deliberately does NOT
include the predicted labels: the labeller reads title + description cold,
so the gold labels anchor on the text, not on the prediction.
"""

from __future__ import annotations

import csv
import random

import duckdb

from src import config as C

PER_CELL = 5
SEED = 26


def run() -> None:
    con = duckdb.connect(str(C.DB_PATH), read_only=True)
    rows = con.execute("""
        SELECT p.id, p.country, p.title, p.company, p.description,
               l.tier, l.gbs_signal, l.source
        FROM postings p JOIN labels l ON p.id = l.id
    """).fetchall()
    con.close()

    rng = random.Random(SEED)
    cells: dict[tuple, list] = {}
    for r in rows:
        cells.setdefault((r[5], r[6], r[7]), []).append(r)

    sample = []
    for key in sorted(cells, key=str):
        pool = cells[key]
        rng.shuffle(pool)
        sample.extend(pool[:PER_CELL])

    out = C.ROOT / "eval" / "gold_template.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "country", "title", "company", "description",
                    "tier_gold", "gbs_gold"])
        for r in sample:
            w.writerow([r[0], r[1], r[2], r[3], (r[4] or "")[:1200], "", ""])

    print(f"Wrote {len(sample)} rows across {len(cells)} strata to {out}")


if __name__ == "__main__":
    run()
