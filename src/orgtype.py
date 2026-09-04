"""Who is hiring, and where — two cuts the family mix cannot be read without.

Both classifications are plain visible lists rather than a model, for the same
reason the taxonomy is: a reader can check them and disagree with a specific
entry instead of with a black box.

**Organisation type.** A posting from Accenture Operations and a posting from
EY Advisory are not the same market. The first is GBS work, delivered by a
third party instead of a captive centre — it belongs in the readout, and its
transactional skew is a real feature of outsourced delivery. The second is
someone who *advises on* GBS, which is a different labour market that happens
to match the same search terms. Advisory is excluded from the headline mix and
the excluded count is reported.

**Market type.** GBS delivery sits in low-cost hubs; process ownership and the
retained organisation sit in high-cost markets. Pooling them produces a family
mix that is partly a statement about the country basket rather than about the
market: in this snapshot India runs 72% transactional and Switzerland 81%
judgment. The cut is reported separately so the basket effect is visible
instead of averaged away.
"""

from __future__ import annotations

# Third-party GBS / BPO delivery. In scope: this is the same work, outsourced.
BPO = [
    "accenture", "genpact", "capgemini", "cognizant", "concentrix",
    "tata consultancy", "tcs ", "wipro", "wns", "infosys", "sopra",
    "atos", "dxc", "conduent", "teleperformance", "firstsource", "hcl",
    "tech mahindra", "sutherland", "ibm business services",
]

# Advises on GBS rather than performing it. Out of scope for the headline.
# Ordered before BPO on purpose: "Infosys Consulting" must not fall to BPO.
ADVISORY = [
    "ernst & young", "ernst und young", "deloitte", "kpmg",
    "pricewaterhousecoopers", "pwc", "mckinsey", "boston consulting",
    "bain & company", "infosys consulting", "roland berger", "oliver wyman",
    "kearney", "strategy&", "horvath", "zeb consulting",
]

# "EY" as a bare token — matched separately, since the two letters appear
# inside ordinary words ("Sey", "Honey") and would over-match as a substring.
ADVISORY_EXACT = {"ey", "ey global", "ey advisory", "e&y"}

# Low-cost GBS delivery hubs.
DELIVERY_MARKETS = {"in", "pl", "mx", "za", "ro", "hu", "cz", "pt", "ph", "my"}

# High-cost markets: headquarters, process ownership, retained organisation.
RETAINED_MARKETS = {"ch", "nl", "de", "gb", "us", "fr", "at", "se", "dk", "no"}

# Genuinely both — regional headquarters alongside nearshore or regional
# delivery. Called out rather than forced into one bucket.
MIXED_MARKETS = {"es", "sg", "ie", "it"}


def org_type(company: str | None) -> str:
    """One of 'advisory', 'bpo', 'captive'.

    'captive' is the default: anything not recognised as a consultancy or a
    BPO provider is treated as an in-house employer. That is the right default
    for a keyword list — an unknown name is far more likely to be an ordinary
    company than an unlisted consultancy.
    """
    if not company:
        return "captive"
    name = company.strip().lower()
    if name in ADVISORY_EXACT:
        return "advisory"
    if any(term in name for term in ADVISORY):
        return "advisory"
    if any(term in name for term in BPO):
        return "bpo"
    return "captive"


def market_type(country: str | None) -> str:
    """One of 'delivery', 'retained', 'mixed', 'unclassified'."""
    if not country:
        return "unclassified"
    code = country.strip().lower()
    if code in DELIVERY_MARKETS:
        return "delivery"
    if code in RETAINED_MARKETS:
        return "retained"
    if code in MIXED_MARKETS:
        return "mixed"
    return "unclassified"
