"""
Score the classifier against the hand-labelled gold set.

Reports overall accuracy, per-class precision/recall for the tier axis, and
accuracy for the GBS-signal axis — split by label source, because the
taxonomy and the model fallback earn trust separately.
"""

from __future__ import annotations

import csv
from collections import defaultdict

import duckdb

from src import config as C

GOLD = C.ROOT / "eval" / "gold.csv"
TIER_CLASSES = ["core", "planning", "strategic", "none"]


def run() -> None:
    with open(GOLD, newline="") as f:
        gold_all = {r["id"]: r for r in csv.DictReader(f)}
    gold = {i: g for i, g in gold_all.items() if g.get("tier_gold")}

    con = duckdb.connect(str(C.DB_PATH), read_only=True)
    pred = {r[0]: {"tier": r[1], "gbs": bool(r[2]), "source": r[3]}
            for r in con.execute(
                "SELECT id, tier, gbs_signal, source FROM labels").fetchall()}
    con.close()

    matched = [(g, pred[i]) for i, g in gold.items() if i in pred]
    print(f"Gold rows: {len(gold_all)} total, {len(gold)} with a tier label "
          f"(the rest are truncated past judging) · matched: {len(matched)}\n")

    # --- tier axis ---
    conf = defaultdict(int)
    by_source = defaultdict(lambda: [0, 0])
    for g, p in matched:
        conf[(g["tier_gold"], p["tier"])] += 1
        by_source[p["source"]][0] += int(g["tier_gold"] == p["tier"])
        by_source[p["source"]][1] += 1

    correct = sum(v for (a, b), v in conf.items() if a == b)
    total = sum(conf.values())
    print(f"TIER accuracy: {correct}/{total} = {100*correct/total:.1f}%")
    for src, (c, n) in sorted(by_source.items()):
        print(f"  by source — {src}: {c}/{n} = {100*c/n:.1f}%")

    print(f"\n{'class':<10} {'precision':>9} {'recall':>7} {'n gold':>7}")
    for cls in TIER_CLASSES:
        tp = conf[(cls, cls)]
        fp = sum(v for (a, b), v in conf.items() if b == cls and a != cls)
        fn = sum(v for (a, b), v in conf.items() if a == cls and b != cls)
        prec = tp / (tp + fp) if tp + fp else float("nan")
        rec = tp / (tp + fn) if tp + fn else float("nan")
        print(f"{cls:<10} {prec:>9.1%} {rec:>7.1%} {tp+fn:>7}")

    print("\nConfusion (gold -> predicted):")
    for (a, b), v in sorted(conf.items(), key=lambda kv: -kv[1]):
        if a != b:
            print(f"  {a} -> {b}: {v}")

    # --- GBS-signal axis: scored over ALL gold rows (a truncated posting can
    # still support a signal judgment even when its tier cannot be judged) ---
    gm = [(g, pred[i]) for i, g in gold_all.items()
          if i in pred and g.get("gbs_gold")]
    truthy = {"1", "true", "yes"}
    g_correct = sum(1 for g, p in gm
                    if (g["gbs_gold"].strip().lower() in truthy) == p["gbs"])
    tp = sum(1 for g, p in gm if g["gbs_gold"].strip().lower() in truthy and p["gbs"])
    fp = sum(1 for g, p in gm if g["gbs_gold"].strip().lower() not in truthy and p["gbs"])
    fn = sum(1 for g, p in gm if g["gbs_gold"].strip().lower() in truthy and not p["gbs"])
    print(f"\nGBS-SIGNAL accuracy: {g_correct}/{len(gm)} = {100*g_correct/len(gm):.1f}%")
    if tp + fp:
        print(f"  precision {tp/(tp+fp):.1%} · ", end="")
    if tp + fn:
        print(f"recall {tp/(tp+fn):.1%} (n gold-positive: {tp+fn})")


if __name__ == "__main__":
    run()
