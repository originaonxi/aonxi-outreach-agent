"""
Enriches each company with multiple data sources:
1. Hunter — verify/find email
2. Exa — deep company intelligence (description, news, hiring signals)
3. Signal computation from all collected data
"""

from __future__ import annotations
import requests
from config import HUNTER_API_KEY, EXA_API_KEY


def enrich(company: dict) -> dict:
    company = _hunter_verify(company)
    company = _exa_enrich(company)
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


def _exa_enrich(company: dict) -> dict:
    """Use Exa deep search to find company intelligence."""
    if not EXA_API_KEY:
        return company

    try:
        from exa_py import Exa
        exa = Exa(api_key=EXA_API_KEY)

        domain = company.get("domain", "")
        company_name = company.get("company", "")
        if not company_name:
            return company

        # Deep search for company info — structured output
        results = exa.search(
            f"{company_name} {domain}",
            type="auto",
            num_results=3,
            category="company",
        )

        if results and results.results:
            top = results.results[0]
            if not company.get("short_description") and hasattr(top, "text"):
                company["short_description"] = (top.text or "")[:300]
            company["exa_url"] = top.url if hasattr(top, "url") else ""

        # Check for hiring/growth signals
        news_results = exa.search_and_contents(
            f"{company_name} hiring OR funding OR growth OR expansion",
            type="auto",
            num_results=2,
            text={"max_characters": 500},
        )

        exa_signals = []
        if news_results and news_results.results:
            for nr in news_results.results:
                text = (nr.text or "").lower()
                if "hiring" in text or "job" in text:
                    exa_signals.append("actively_hiring")
                if "funding" in text or "raised" in text or "series" in text:
                    exa_signals.append("recently_funded")
                if "growth" in text or "expanding" in text or "launch" in text:
                    exa_signals.append("growth_signals")

        company["exa_signals"] = list(set(exa_signals))

    except Exception:
        pass

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

    # VP+ level
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

    # Tech stack
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

    # Exa signals (from web intelligence)
    exa_signals = company.get("exa_signals", [])
    signals.extend(exa_signals)

    company["signals"] = signals
    company["signal_count"] = len(signals)
    return company
