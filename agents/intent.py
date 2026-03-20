"""
Scores buying intent 1-10 using Claude.

High intent (8-10):
- Decision maker (CEO/Founder/VP) at right-size company
- Early stage with growth signals
- Industry known to need outbound
- Title suggests they own the budget

Low intent (1-5):
- Wrong size (too big = enterprise, too small = no budget)
- Wrong title (not a decision maker)
- Industry doesn't match ICP
"""

from __future__ import annotations
import json
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def score(company: dict) -> dict:
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
- Signals: {', '.join(company.get('signals', []))}

Score 1-10. Then give:
- One sentence on why they need Aonxi RIGHT NOW
- The most personal hook (something specific to them)
- Best subject line (under 8 words, no clickbait, makes them curious)

Return JSON only:
{{
  "score": 7,
  "why_now": "one sentence",
  "hook": "specific personal observation",
  "subject": "under 8 words"
}}"""

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
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
