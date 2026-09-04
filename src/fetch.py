"""Fetch the two-source, point-in-time GBS posting sample into DuckDB."""

from __future__ import annotations

import hashlib
import sys
import time

import duckdb
import requests

from src import config as C


ADZUNA_API = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
JOOBLE_API = "https://jooble.org/api/{api_key}"
POSTING_COLUMNS = [
    "id", "source", "source_id", "country", "term", "title", "company",
    "description", "category", "created", "redirect_url", "location",
    "fetched_at",
]


def _init_db(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS postings (
            id VARCHAR PRIMARY KEY, country VARCHAR, term VARCHAR, title VARCHAR,
            company VARCHAR, description VARCHAR, category VARCHAR,
            created VARCHAR, redirect_url VARCHAR
        )
    """)
    existing = {row[0] for row in con.execute("DESCRIBE postings").fetchall()}
    additions = {
        "source": "VARCHAR DEFAULT 'adzuna'",
        "source_id": "VARCHAR",
        "location": "VARCHAR DEFAULT ''",
        "fetched_at": "VARCHAR DEFAULT ''",
    }
    for name, definition in additions.items():
        if name not in existing:
            con.execute(f"ALTER TABLE postings ADD COLUMN {name} {definition}")
    con.execute("UPDATE postings SET source = 'adzuna' WHERE source IS NULL")
    con.execute("UPDATE postings SET source_id = id WHERE source_id IS NULL")


def _stable_id(source: str, source_id: str, title: str, company: str, location: str) -> str:
    if source == "adzuna" and source_id:
        return source_id
    raw = source_id or "|".join((title, company, location))
    digest = hashlib.sha256(f"{source}:{raw}".encode()).hexdigest()[:32]
    return f"{source}_{digest}"


def _adzuna_page(country: str, term: str, page: int) -> list[dict]:
    response = requests.get(
        ADZUNA_API.format(country=country, page=page),
        params={"app_id": C.ADZUNA_APP_ID, "app_key": C.ADZUNA_APP_KEY,
                "what": term, "results_per_page": C.RESULTS_PER_PAGE,
                "content-type": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("results", [])


def _jooble_page(country: str, term: str, page: int) -> list[dict]:
    response = requests.post(
        JOOBLE_API.format(api_key=C.JOOBLE_API_KEY),
        json={"keywords": term, "location": country.upper(), "page": page},
        headers={"Accept": "application/json", "Content-Type": "application/json",
                 "User-Agent": "gbs-agentic-shift/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("jobs", payload.get("results", []))


def _normalise(source: str, country: str, term: str, item: dict) -> list:
    if source == "adzuna":
        source_id = str(item.get("id", ""))
        title = item.get("title", "")
        company = (item.get("company") or {}).get("display_name", "")
        description = item.get("description", "")
        location = (item.get("location") or {}).get("display_name", "")
        category = (item.get("category") or {}).get("label", "")
        created = item.get("created", "")
        url = item.get("redirect_url", "")
    else:
        source_id = str(item.get("id") or item.get("link") or "")
        title = item.get("title", "")
        company = item.get("company", "") or item.get("companyName", "")
        description = item.get("snippet", "") or item.get("description", "")
        location = item.get("location", "")
        category = item.get("type", "")
        created = item.get("updated", "") or item.get("timestamp", "")
        url = item.get("link", "") or item.get("url", "")
    return [_stable_id(source, source_id, title, company, location), source,
            source_id, country, term, title, company, description, category,
            created, url, location, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())]


def _upsert(con: duckdb.DuckDBPyConnection, row: list) -> None:
    placeholders = ",".join("?" for _ in POSTING_COLUMNS)
    con.execute(
        f"INSERT OR REPLACE INTO postings ({','.join(POSTING_COLUMNS)}) VALUES ({placeholders})",
        row,
    )


def run() -> int:
    if not (C.ADZUNA_APP_ID and C.ADZUNA_APP_KEY):
        sys.exit("Set ADZUNA_APP_ID and ADZUNA_APP_KEY (see .env.example).")
    if not C.JOOBLE_API_KEY:
        sys.exit("Set JOOBLE_API_KEY (see .env.example).")

    C.DATA.mkdir(exist_ok=True)
    con = duckdb.connect(str(C.DB_PATH))
    _init_db(con)
    inserted = 0
    jooble_requests = 0

    for source, countries, fetcher in (
        ("adzuna", C.ADZUNA_COUNTRIES, _adzuna_page),
        ("jooble", C.JOOBLE_COUNTRIES, _jooble_page),
    ):
        for country in countries:
            for term in C.SEARCH_TERMS:
                for page in range(1, C.MAX_PAGES + 1):
                    if source == "jooble":
                        jooble_requests += 1
                        if jooble_requests > C.JOOBLE_REQUEST_LIMIT:
                            sys.exit("Jooble request budget exhausted.")
                    try:
                        results = fetcher(country.strip(), term, page)
                    except requests.RequestException as exc:
                        print(f"  ! {source}/{country}/{term} p{page}: {exc}")
                        break
                    if not results:
                        break
                    for item in results:
                        _upsert(con, _normalise(source, country.strip(), term, item))
                        inserted += 1
                    print(f"  {source}/{country}/{term:24} p{page}: {len(results)} rows")
                    time.sleep(C.JOOBLE_REQUEST_INTERVAL if source == "jooble" else 0.3)

    total = con.execute("SELECT count(*) FROM postings").fetchone()[0]
    con.close()
    print(f"\nUpserted {inserted} rows. Table now holds {total} distinct postings.")
    return total


if __name__ == "__main__":
    run()
