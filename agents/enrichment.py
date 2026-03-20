"""
Enriches each company:
1. Hunter — verify email, find alternatives if needed
2. Signals — buying signals from Apollo data + title analysis
"""

from __future__ import annotations
import requests
from config import HUNTER_API_KEY


def enrich(company: dict) -> dict:
    company = _hunter_verify(company)
    company = _compute_signals(company)
    return company


def _hunter_verify(company: dict) -> dict:
    if not HUNTER_API_KEY:
        company.setdefault("email_confidence", 70)
        return company
    try:
        first = company["name"].split()[0] if company["name"] else ""
        last = company["name"].split()[-1] if company["name"] else ""

        r = requests.get(
            "https://api.hunter.io/v2/email-finder",
            params={
                "domain": company["domain"],
                "first_name": first,
                "last_name": last,
                "api_key": HUNTER_API_KEY,
            },
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json().get("data", {})
            if data.get("email"):
                company["email"] = data["email"]
                company["email_confidence"] = data.get("score", 0)
    except Exception:
        pass

    company.setdefault("email_confidence", 70)
    return company


def _compute_signals(company: dict) -> dict:
    """Compute buying signals from all available data."""
    signals = []

    # Decision maker
    title_lower = company.get("title", "").lower()
    dm_titles = ["founder", "ceo", "owner", "managing partner", "partner",
                 "co-founder", "chief", "president", "principal"]
    if any(w in title_lower for w in dm_titles):
        signals.append("decision_maker")

    # VP+ level (can buy without CEO approval at smaller cos)
    vp_titles = ["vp", "vice president", "head of", "director", "cro"]
    if any(w in title_lower for w in vp_titles):
        signals.append("vp_plus")

    # Company size signals
    emp = company.get("employees", 0) or 0
    if 10 <= emp <= 50:
        signals.append("early_stage")
    elif 51 <= emp <= 150:
        signals.append("growth_stage")
    elif 151 <= emp <= 300:
        signals.append("scale_stage")

    if emp >= 20:
        signals.append("has_budget")

    # Sweet spot (20-100 employees = ideal for Aonxi)
    if 20 <= emp <= 100:
        signals.append("sweet_spot_size")

    # Seniority from Apollo
    seniority = company.get("seniority", "").lower()
    if seniority in ("c_suite", "owner", "founder"):
        signals.append("c_level")
    elif seniority in ("vp", "director"):
        signals.append("senior_leader")

    # Revenue signals
    revenue = company.get("annual_revenue", "") or ""
    if revenue and any(x in revenue.lower() for x in ["million", "m", "$1", "$2", "$5", "$10"]):
        signals.append("has_revenue")

    # Tech stack (if they use sales/marketing tools = outbound aware)
    tech = [t.lower() for t in company.get("technologies", [])]
    sales_tech = ["salesforce", "hubspot", "outreach", "salesloft", "apollo",
                  "pipedrive", "zoho crm", "close.io", "gong", "drift"]
    if any(t in " ".join(tech) for t in sales_tech):
        signals.append("uses_sales_tech")

    # Headline analysis
    headline = company.get("headline", "").lower()
    growth_words = ["growth", "scaling", "building", "leading", "growing"]
    if any(w in headline for w in growth_words):
        signals.append("growth_focused")

    company["signals"] = signals
    company["signal_count"] = len(signals)
    return company
