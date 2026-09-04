from src.taxonomy import classify_text


def test_planning_role():
    r = classify_text("FP&A Analyst - annual budgeting, rolling forecast for the CFO")
    assert r.tier == "planning" and not r.gbs_signal


def test_core_role_with_gbs_signal():
    r = classify_text("Financial Analyst, Shared Services Center Krakow - management reporting, KPI packs")
    assert r.tier == "core" and r.gbs_signal


def test_strategic_role():
    r = classify_text("Manager Strategic Planning & Corporate Development - long-range planning, M&A support")
    assert r.tier == "strategic"


def test_non_fpa_guard():
    r = classify_text("Credit Controller - chasing overdue invoices and cash collection")
    assert r.tier == "none"


def test_tie_goes_to_model():
    r = classify_text("Analyst - budgeting and cost accounting")
    assert r.ambiguous


def test_no_phrases_goes_to_model():
    r = classify_text("Team member for our finance department")
    assert r.ambiguous


def test_gbs_signal_polish():
    r = classify_text("Analityk finansowy, Centrum Usług Wspólnych - raportowanie zarządcze")
    assert r.gbs_signal
