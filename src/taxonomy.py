"""
Deterministic taxonomy for FP&A job postings, on two independent axes.

Axis 1 — process tier, mirroring the three plateaus in EY's 2026 FP&A-in-GBS
survey (p. 5): the transactional core (cost accounting, financial analysis,
performance reporting), the planning tier (budgeting, forecasting, capex),
and the strategic tier (strategic planning, M&A support). A posting is also
scored per individual survey process, so mention rates can be compared
shape-for-shape with the survey's own exhibit.

Axis 2 — visible GBS-delivery signal. A posting either names a shared-services
/ GBS / GCC / CoE context or it does not. Absence of a phrase is not proof the
role is retained — employers do not always name the delivery model — so the
signal is reported as a LOWER BOUND on GBS hiring, never as "retained".

Every label is traceable to the exact phrases that produced it. The LLM
fallback in classify.py only decides the residual this file flags ambiguous,
and only on axis 1 — the GBS signal stays deterministic end to end.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

# ---------------------------------------------------------------------------
# The eight survey processes. Phrase lists are matched on word boundaries,
# case-insensitive; multi-word phrases as phrases. German and Polish forms are
# included because de/ch and pl are in the country basket.
# ---------------------------------------------------------------------------

PROCESSES: Dict[str, List[str]] = {
    "financial_analysis": [
        "financial analysis", "variance analysis", "abweichungsanalyse",
        "profitability analysis", "margin analysis", "cost analysis",
        "ad hoc analysis", "ad-hoc analysis", "analiza finansowa",
        "financial modelling", "financial modeling", "business case analysis",
        "análisis financiero", "analisis financiero", "análisis de datos financieros",
        "financiële analyse", "financiele analyse", "finanzanalyse",
        "financial analyst", "analista financiero", "financieel analist",
        "finanzanalyst", "analityk finansowy",
    ],
    "cost_accounting": [
        "cost accounting", "cost controlling", "kostenrechnung",
        "product costing", "standard costing", "cost center", "cost centre",
        "kostenstellen", "inventory valuation", "overhead allocation",
        "rachunek kosztów", "contabilidad de costos", "contabilidad de costes",
        "control de costos", "control de costes", "cost control",
        "kostencontrolling", "kostprijs",
    ],
    "performance_reporting": [
        "management reporting", "performance reporting", "monthly reporting",
        "kpi reporting", "board reporting", "reporting package", "reporting pack",
        "berichtswesen", "management-reporting", "raportowanie zarządcze",
        "performance management", "dashboards", "dashboarding",
        "informes de gestión", "reportes financieros", "reporting financiero",
        "managementrapportage", "rapportage", "monatsreporting",
        "mis reporting", "mis reports", "management information",
    ],
    "budgeting": [
        "budgeting", "annual budget", "budget process", "budget planning",
        "annual planning", "operative planung", "budgetierung", "budgetplanung",
        "budżetowanie", "planning cycle", "aop", "annual operating plan",
        "presupuesto", "presupuestos", "presupuestación", "presupuestacion",
        "planificación presupuestaria", "budgettering", "budget preparation",
        "budget management", "planning & budgeting", "planning and budgeting",
        "jahresplanung",
    ],
    "forecasting": [
        "forecasting", "forecast", "rolling forecast", "prognose", "prognosen",
        "driver-based planning", "driver based planning", "demand planning",
        "prognozowanie", "scenario planning", "scenario modelling",
        "scenario modeling", "previsión", "previsiones", "prevision",
        "pronóstico", "pronósticos", "proyecciones financieras", "proyecciones",
        "prognoses", "forecasts", "financial planning", "planificación financiera",
        "planificacion financiera", "financiële planning", "finanzplanung",
        "planowanie finansowe",
    ],
    "capex_management": [
        "capex", "capital expenditure", "investment planning", "capital planning",
        "investitionsplanung", "investment appraisal", "investment controlling",
        "plan de inversiones", "investeringsplan",
    ],
    "strategic_planning": [
        "strategic planning", "long-range planning", "long range planning",
        "long-term planning", "strategische planung",
        "planowanie strategiczne", "5-year plan",
        "five-year plan", "mid-term planning", "mittelfristplanung",
        "planificación estratégica", "planificacion estrategica",
        "strategische planning", "plan estratégico", "langfristplanung",
    ],
    "ma_support": [
        "m&a", "mergers and acquisitions", "due diligence",
        "corporate development", "divestiture", "divestment", "post-merger",
        "transaction support", "deal support", "fusiones y adquisiciones",
        "fusies en overnames",
    ],
}

# Tier membership mirrors the survey's clustering (p. 5).
TIERS: Dict[str, List[str]] = {
    "core": ["financial_analysis", "cost_accounting", "performance_reporting"],
    "planning": ["budgeting", "forecasting", "capex_management"],
    "strategic": ["strategic_planning", "ma_support"],
}

# Axis 2 — visible GBS-delivery signal. Deterministic only.
GBS_SIGNAL: List[str] = [
    "shared services", "shared service", "shared-services", "ssc",
    "global business services", "gbs", "global capability center",
    "global capability centre", "gcc", "capability center", "capability centre",
    "center of excellence", "centre of excellence", "coe", "center of expertise",
    "centre of expertise", "delivery center", "delivery centre", "delivery hub",
    "service delivery", "captive center", "captive centre", "business services center",
    "business services centre", "business services organisation",
    "business services organization", "finance hub", "regional hub",
    "centrum usług wspólnych", "usług wspólnych",
    "centro de servicios compartidos", "servicios compartidos",
]

# The function's own name must not vote for a tier: "financial planning and
# analysis" contains "financial planning", which would hand every FP&A-titled
# posting a planning point. The name is neutralised before matching.
FPA_NAME = re.compile(
    r"(?i)financial planning\s*(?:and|&|\+|y)\s*analys\w+"
    r"|planificaci[oó]n y an[aá]lisis financiero"
    r"|planning\s*(?:and|&)\s*analysis"
)

# Accounting-execution phrases. These do not name a tier — they name work the
# survey's FP&A scope does NOT cover (R2R execution, AP/AR, statutory). When
# they outweigh every tier, the posting goes to the model, which decides
# whether this is FP&A described sparsely or an accounting role the dragnet
# caught. Deterministic core labels must not sit on accounting postings.
ACCOUNTING_EXECUTION = [
    "journal entries", "journal entry", "reconciliation", "reconciliations",
    "month-end close", "month end close", "close activities", "statutory",
    "accounts payable", "accounts receivable", "general ledger", "bookkeeping",
    "invoicing", "invoices", "invoice processing", "payroll", "audit trails",
    "external audit", "record to report", "tax compliance", "tax returns",
    "conciliaciones", "cierre contable", "cuentas por pagar",
    "cuentas por cobrar", "buchhaltung", "jahresabschluss", "hauptbuch",
    "kreditoren", "debitoren", "księgowość", "credit control",
    "cash application", "billing",
]

# Guard: postings whose role is clearly not finance planning/analysis work at
# all (the "financial analyst" and "controlling" dragnets catch these).
NOT_FPA = re.compile(
    r"(?i)\b(air traffic controll|document controller|quality controller|"
    r"credit controller|stock controller|inventory controller|site controller\b.*construction|"
    r"controller of exams|doorman|warehouse|nurse|physician|"
    r"wealth management advisor|wealth advisor|personal financial planner|"
    r"financial adviser|financial advisor|insurance agent|asesor financiero)\b"
)


def _compile(phrases: List[str]) -> List[tuple]:
    ordered = sorted(set(phrases), key=len, reverse=True)
    return [(p, re.compile(r"(?<!\w)" + re.escape(p) + r"(?!\w)", re.IGNORECASE))
            for p in ordered]


_PROC_COMPILED = {proc: _compile(ph) for proc, ph in PROCESSES.items()}
_GBS_COMPILED = _compile(GBS_SIGNAL)
_ACC_COMPILED = _compile(ACCOUNTING_EXECUTION)


@dataclass
class TaxonomyResult:
    tier: str                       # core | planning | strategic | ambiguous
    gbs_signal: bool
    proc_hits: Dict[str, List[str]] = field(default_factory=dict)
    tier_scores: Dict[str, int] = field(default_factory=dict)
    gbs_hits: List[str] = field(default_factory=list)
    ambiguous: bool = False

    def to_row(self) -> dict:
        return {
            "tier": self.tier,
            "gbs_signal": self.gbs_signal,
            "score_core": self.tier_scores.get("core", 0),
            "score_planning": self.tier_scores.get("planning", 0),
            "score_strategic": self.tier_scores.get("strategic", 0),
            "proc_hits": "; ".join(
                f"{p}:{','.join(ph)}" for p, ph in self.proc_hits.items() if ph),
            "gbs_hits": ",".join(self.gbs_hits),
            "ambiguous": self.ambiguous,
        }


def classify_text(text: str, title: str = "") -> TaxonomyResult:
    """Score one posting. A phrase found in the TITLE counts double: the title
    names what the role centres on, and this resolves most core/planning ties
    deterministically instead of handing them to the model."""
    text = f"{title} {text or ''}"
    gbs_hits = [p for p, rx in _GBS_COMPILED if rx.search(text)]

    # Neutralise the function's own name before tier scoring (see FPA_NAME).
    text = FPA_NAME.sub(" fpa-function ", text)
    scored_title = FPA_NAME.sub(" fpa-function ", title or "")

    proc_hits = {proc: [p for p, rx in pats if rx.search(text)]
                 for proc, pats in _PROC_COMPILED.items()}
    title_hits = {proc: [p for p, rx in pats if scored_title and rx.search(scored_title)]
                  for proc, pats in _PROC_COMPILED.items()}
    tier_scores = {tier: sum(len(proc_hits[p]) + len(title_hits[p]) for p in procs)
                   for tier, procs in TIERS.items()}
    acc_score = sum(1 for p, rx in _ACC_COMPILED if rx.search(text))

    if NOT_FPA.search(text[:200]):
        return TaxonomyResult("none", bool(gbs_hits), proc_hits, tier_scores,
                              gbs_hits, ambiguous=False)

    top = max(tier_scores.values())
    if top == 0:
        # No process phrase at all — the model decides whether this is FP&A
        # work described in other words, or not FP&A at all.
        return TaxonomyResult("ambiguous", bool(gbs_hits), proc_hits,
                              tier_scores, gbs_hits, ambiguous=True)

    if acc_score >= top:
        # Accounting-execution language outweighs every tier: the model
        # decides whether this is an accounting role the dragnet caught.
        return TaxonomyResult("ambiguous", bool(gbs_hits), proc_hits,
                              tier_scores, gbs_hits, ambiguous=True)

    leaders = [t for t, s in tier_scores.items() if s == top]
    if len(leaders) > 1:
        # FP&A roles bundle processes, so ties are common and genuinely
        # ambiguous — the model reads which tier the role centres on.
        return TaxonomyResult("ambiguous", bool(gbs_hits), proc_hits,
                              tier_scores, gbs_hits, ambiguous=True)

    return TaxonomyResult(leaders[0], bool(gbs_hits), proc_hits, tier_scores,
                          gbs_hits, ambiguous=False)


if __name__ == "__main__":
    samples = [
        "FP&A Analyst — annual budgeting, rolling forecast, variance commentary for the CFO.",
        "Financial Analyst, Shared Services Center Krakow — management reporting and month-end KPI packs.",
        "Senior Manager Strategic Planning & Corporate Development — long-range planning, M&A support.",
        "Credit Controller — chasing overdue invoices.",
    ]
    for s in samples:
        r = classify_text(s)
        print(f"{r.tier:10} gbs={r.gbs_signal}  {r.tier_scores}  <- {s[:60]}")
