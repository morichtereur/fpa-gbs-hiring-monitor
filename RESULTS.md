# Results — snapshot of 2026-09-04

Point-in-time cross-section: 4,802 distinct postings fetched from Adzuna
across eight markets (pl, in, mx, nl, de, ch, es, sg) on six FP&A search
terms. 122 advisory postings (consultancies advising on FP&A) and 1,754
non-FP&A postings excluded, leaving **2,926 FP&A postings**. Jooble (pt, ro,
hu, cz) returned 403 on every call — those markets are absent from this
snapshot.

## The headline

**The strategic tier is absent from GBS hiring — 0 of 137 GBS-evidenced FP&A
postings — while planning work is already overrepresented there.**

| lens | n | core | planning | strategic |
|---|---|---|---|---|
| GBS phrase signal | 61 | 59.0% | 41.0% | **0.0%** |
| BPO employer | 77 | 33.8% | 66.2% | **0.0%** |
| GBS combined (either) | 137 | 45.3% | 54.7% | **0.0%** |
| no GBS evidence | 2,789 | 51.6% | 41.7% | 6.6% |
| all FP&A | 2,926 | 51.3% | 42.3% | 6.3% |

Read against the EY survey's gradient (transactional core broadly in GBS,
planning the declared 1–3-year expansion wave, strategy retained):

- **Strategy retained — corroborated, and robustly.** Strategic-tier work is
  6.6% of FP&A hiring outside GBS and zero inside it. The strategic class
  over-triggers if anything (40% measured precision), so a zero cannot be a
  classifier artifact: the survey's 20%-support / +3pt-planned top of the
  pyramid is exactly what the hiring market shows.
- **Planning as the expansion wave — directionally corroborated.** Planning
  work is 54.7% of GBS-evidenced FP&A hiring against 41.7% outside — new GBS
  capacity leans toward budgeting and forecasting, not just reporting. This
  is the finding to hold loosely: planning precision measures 58.3% on a
  small gold class, and n=137 puts roughly ±8pp on any share.
- **The provider channel leads the tilt.** The two GBS lenses disagree
  informatively: phrase-signalled postings (mostly captive SSC/GCC contexts)
  run 59% core, while third-party BPO providers run 66% planning. If that
  split holds, the planning wave is being sold before it is being built
  in-house — the same only-the-employer-cut-separates-them pattern as
  gbs-agentic-shift's captive/provider finding.

## The market cut

| market type | n | GBS-evidenced share | core | planning | strategic |
|---|---|---|---|---|---|
| delivery (pl, in, mx) | 1,066 | 11.8% | 48.1% | 48.1% | 3.8% |
| retained (nl, de, ch) | 1,105 | 0.6% | 63.6% | 31.0% | 5.3% |
| mixed (es, sg) | 755 | 0.5% | 37.9% | 50.7% | 11.4% |

Retained markets hire FP&A as analysis and reporting; delivery hubs hire it
tilted toward planning. The pooled figure is therefore partly a statement
about the country basket — reported separately so the basket effect is
visible instead of averaged away.

## Measured accuracy (hand-labelled gold set, n=66, labelled cold)

| axis | result |
|---|---|
| tier accuracy | 78.6% overall (model fallback 83.3%, taxonomy 70.0%) |
| tier per class | core P 81 / R 90 · planning P 58 / R 70 · strategic P 40 / R 100 · none P 100 / R 72 |
| GBS signal | accuracy 87.9% · precision 73.1% · recall 95.0% |

The residual split is 27% taxonomy / 73% model — inverted from the usual
architecture because Adzuna truncates descriptions at ~500 characters, which
starves the phrase taxonomy. The model fallback is the *more* accurate stage
here and its reasoning is logged per posting. Planning precision (58.3%) is
the number to keep in view: the planning-tilt finding survives it
directionally but not to the decimal.

## What this cannot say

- **A cross-section is not a trend.** Planning overrepresentation in GBS
  hiring is consistent with an expansion wave; it does not prove one.
- **The GBS split is a lower bound.** Absence of a phrase or a listed
  employer is not evidence a role is retained (signal recall vs the visible
  concept is 95%, but the truncated text hides most delivery-model naming).
- **Small cells.** 137 GBS-evidenced postings; 61/77 per lens; 7 in retained
  markets. Read positions and zeros, not decimal points.
- **One source.** Adzuna only in this snapshot; Jooble's four CEE markets
  are missing, and mention-rate exhibits inherit the 500-character truncation.
