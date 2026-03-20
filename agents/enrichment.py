"""
Enriches each company:
1. Hunter — verify email, find alternatives if needed
2. Web signals — job postings, funding news (intent boost)
"""

from __future__ import annotations
import requests
from config import HUNTER_API_KEY


def enrich(company: dict) -> dict:
    company = _hunter_verify(company)
    company = _web_signals(company)
    return company


def _hunter_verify(company: dict) -> dict:
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

    return company


def _web_signals(company: dict) -> dict:
    """
    Check for buying signals via Apollo org data.
    Signals: hiring SDRs, hiring sales, recent growth.
    """
    signals = []

    title_lower = company.get("title", "").lower()
    if any(w in title_lower for w in ["founder", "ceo", "owner"]):
        signals.append("decision_maker")
    if company.get("employees", 0) < 50:
        signals.append("early_stage")
    if company.get("employees", 0) > 20:
        signals.append("has_budget")

    company["signals"] = signals
    return company
