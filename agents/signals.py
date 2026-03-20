"""
Real-time signal enrichment — Exa + Grok.
This is what makes emails feel researched, not templated.

For each prospect:
1. Exa: what happened to this company recently?
2. Grok: what is the founder posting on X?
3. Combine into hooks the writer uses in the email opening.
"""

from __future__ import annotations
import time
import requests
from config import EXA_API_KEY, GROK_API_KEY


def get_company_news(company_name: str, domain: str) -> str:
    """Get recent news/context about the company using Exa."""
    if not EXA_API_KEY:
        return ""
    try:
        from exa_py import Exa
        exa = Exa(api_key=EXA_API_KEY)
        results = exa.search_and_contents(
            f"{company_name} {domain}",
            type="auto",
            num_results=3,
            text={"max_characters": 300},
        )
        snippets = []
        if results and results.results:
            for r in results.results:
                if hasattr(r, "text") and r.text:
                    snippets.append(r.text[:200])
        return " | ".join(snippets[:2]) if snippets else ""
    except Exception:
        return ""


def get_founder_signals(name: str, company_name: str) -> str:
    """Get what the founder is talking about on X using Grok."""
    if not GROK_API_KEY:
        return ""
    try:
        r = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROK_API_KEY}",
            },
            json={
                "model": "grok-4-1-fast",
                "messages": [{"role": "user", "content": f"""Search X/Twitter for recent posts by {name}, who works at {company_name}.
What are they talking about professionally? What problems or wins are they mentioning?
Give me 2-3 sentences of context only.
If no posts found, respond with exactly: no_data"""}],
                "temperature": 0,
                "max_tokens": 200,
            },
            timeout=15,
        )
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"].strip()
            if "no_data" in text.lower() or "no posts" in text.lower():
                return ""
            return text
    except Exception:
        pass
    return ""


def enrich_with_signals(company: dict) -> dict:
    """Add real-time signals to a company dict. Called before writing."""
    company_name = company.get("company", "")
    domain = company.get("domain", "")
    contact_name = company.get("name", "")

    print(f"    → {company_name}...", end="", flush=True)

    # Exa: company news
    news = get_company_news(company_name, domain)
    company["recent_news"] = news

    # Signal boosts for intent
    news_lower = (news or "").lower()
    signal_boost = 0
    if any(w in news_lower for w in ["series a", "series b", "funding", "raised", "investment"]):
        signal_boost += 1
        company.setdefault("signals", []).append("recently_funded")
    if any(w in news_lower for w in ["hiring", "job opening", "new hire", "team growing"]):
        signal_boost += 1
        company.setdefault("signals", []).append("actively_hiring")
    if any(w in news_lower for w in ["launch", "expansion", "new product", "growth"]):
        signal_boost += 1
        company.setdefault("signals", []).append("growth_signals")

    # Grok: founder X activity (only for C-level/founders)
    title = company.get("title", "").lower()
    x_signals = ""
    if any(t in title for t in ["ceo", "founder", "owner", "co-founder"]):
        x_signals = get_founder_signals(contact_name, company_name)
        company["x_signals"] = x_signals
        if x_signals and any(w in x_signals.lower() for w in ["sales", "pipeline", "outbound", "growth", "revenue"]):
            signal_boost += 2
            company.setdefault("signals", []).append("talking_about_sales")
    else:
        company["x_signals"] = ""

    # Apply signal boost to intent score
    if signal_boost > 0:
        old = company.get("intent_score", 5)
        company["intent_score"] = min(10, old + signal_boost)
        company["signal_boost"] = signal_boost

    # Print status
    parts = []
    if news:
        parts.append("news")
    if x_signals:
        parts.append("X")
    if signal_boost:
        parts.append(f"+{signal_boost}")
    status = f" [{', '.join(parts)}]" if parts else ""
    print(f"{status}")

    time.sleep(0.3)
    return company
