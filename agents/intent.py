"""
Scores buying intent 1-10 using Claude + enrichment signals.

High intent (8-10):
- Decision maker at right-size company (20-100 sweet spot)
- Multiple buying signals (has_budget + decision_maker + growth)
- Industry known to need outbound

Low intent (1-5):
- Wrong size, wrong title, no signals
"""

from __future__ import annotations
import json
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def score(company: dict) -> dict:
    signals = company.get("signals", [])
    signal_str = ", ".join(signals) if signals else "none detected"

    prompt = f"""Score this prospect's buying intent for Aonxi (1-10).

Aonxi sells: AI agents that deliver qualified sales meetings on pay-per-outcome.
Target: $1M-$50M ARR companies that need to scale outbound without hiring SDRs.

Prospect:
- Name: {company.get('name')}
- Title: {company.get('title')}
- Company: {company.get('company')}
- Employees: {company.get('employees')}
- Industry: {company.get('industry')}
- Location: {company.get('location')}
- Vertical: {company.get('vertical')}
- Company description: {company.get('short_description', 'N/A')[:200]}
- Annual revenue: {company.get('annual_revenue', 'N/A')}
- Founded: {company.get('founded_year', 'N/A')}
- Seniority: {company.get('seniority', 'N/A')}
- Headline: {company.get('headline', 'N/A')[:100]}
- Signals detected: {signal_str}
- Signal count: {company.get('signal_count', 0)}

SCORING GUIDE:
- 9-10: Decision maker (C-suite/Founder), sweet spot size (20-100), multiple signals, perfect ICP
- 7-8: Senior leader, good size, some signals, strong ICP match
- 5-6: Decent fit but missing something (wrong title, or too big/small)
- 1-4: Poor fit (wrong size, wrong title, wrong industry)

BONUS for: decision_maker + sweet_spot_size + has_budget combo
PENALTY for: no signals, >200 employees, non-English markets

Score 1-10. Then give:
- One sentence on why they need Aonxi RIGHT NOW (specific to THEIR situation)
- The most personal hook (reference something TRUE about their company)
- Best subject line (under 8 words, no clickbait, makes them curious)

Return JSON only:
{{
  "score": 7,
  "why_now": "one sentence specific to their company",
  "hook": "specific personal observation about them",
  "subject": "under 8 words"
}}"""

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.split("```")[0]
        data = json.loads(text.strip())
        company["intent_score"] = data.get("score", 5)
        company["why_now"] = data.get("why_now", "")
        company["hook"] = data.get("hook", "")
        company["subject"] = data.get("subject", "")
    except Exception:
        company["intent_score"] = 5
        company["why_now"] = ""
        company["hook"] = ""
        company["subject"] = f"Quick question about {company.get('company', '')}"

    return company
