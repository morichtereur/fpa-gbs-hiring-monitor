"""Central config. All secrets come from the environment — nothing is hardcoded."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB_PATH = DATA / "postings.duckdb"

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY", "")
JOOBLE_REQUEST_LIMIT = int(os.getenv("JOOBLE_REQUEST_LIMIT", "400"))
JOOBLE_REQUEST_INTERVAL = float(os.getenv("JOOBLE_REQUEST_INTERVAL", "0.5"))

# Same country basket as gbs-agentic-shift, so the two studies are comparable.
ADZUNA_COUNTRIES = os.getenv("ADZUNA_COUNTRIES", "pl,in,mx,nl,de,ch,es,sg").split(",")
JOOBLE_COUNTRIES = os.getenv("JOOBLE_COUNTRIES", "pt,ro,hu,cz").split(",")
COUNTRIES = ADZUNA_COUNTRIES + JOOBLE_COUNTRIES

# Population: FP&A work, on both sides of the GBS boundary. The terms cast for
# the FUNCTION (planning/analysis roles), not for the delivery model — whether
# a posting carries a GBS signal is measured afterwards, never assumed from
# the search term. "controlling" is the DACH name for FP&A work and is what
# keeps de/ch/at postings in the population.
SEARCH_TERMS = [
    "fp&a",
    "financial planning and analysis",
    "financial planning analyst",
    "budgeting and forecasting",
    "financial analyst",
    "controlling",
]

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLASSIFIER_MODEL = os.getenv("CLASSIFIER_MODEL", "claude-sonnet-5")

# Fallback backend: "anthropic" (direct API) or "bedrock" (AWS, bearer-token
# auth via AWS_BEARER_TOKEN_BEDROCK; EU needs an inference-profile model id).
CLASSIFIER_BACKEND = os.getenv("CLASSIFIER_BACKEND", "anthropic")
BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "eu.anthropic.claude-sonnet-4-5-20250929-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
RECLASSIFY = os.getenv("FPA_RECLASSIFY", "0").lower() in {"1", "true", "yes"}
MODEL_WORKERS = int(os.getenv("FPA_MODEL_WORKERS", "3"))
MODEL_REQUEST_INTERVAL = float(os.getenv("FPA_MODEL_REQUEST_INTERVAL", "0.25"))
MODEL_TIMEOUT = float(os.getenv("FPA_MODEL_TIMEOUT", "10"))

RESULTS_PER_PAGE = 50
MAX_PAGES = int(os.getenv("FPA_MAX_PAGES", "4"))
