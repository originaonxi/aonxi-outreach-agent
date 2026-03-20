"""
Scores buying intent 1-10 using dual-LLM scoring:
- Claude Haiku: primary scorer (fast, reliable)
- Grok: second opinion scorer (real-time X/web intelligence)
- Final score: weighted average of both

High intent (8-10):
- Decision maker at right-size company (20-100 sweet spot)
- Multiple buying signals (has_budget + decision_maker + growth)
- Industry known to need outbound

Low intent (1-5):
- Wrong size, wrong title, no signals
"""

from __future__ import annotations
import json
import requests
import anthropic
from config import ANTHROPIC_API_KEY, GROK_API_KEY

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SCORING_PROMPT = """Score this prospect's buying intent for Aonxi (1-10).

Aonxi sells: AI agents that deliver qualified sales meetings on pay-per-outcome.
Target: $1M-$50M ARR companies that need to scale outbound without hiring SDRs.

Prospect:
- Name: {name}
- Title: {title}
- Company: {company}
- Employees: {employees}
- Industry: {industry}
- Location: {location}
- Vertical: {vertical}
- Company description: {description}
- Annual revenue: {revenue}
- Founded: {founded}
- Seniority: {seniority}
- Headline: {headline}
- Signals detected: {signals}
- Signal count: {signal_count}

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


def _build_prompt(company: dict) -> str:
    signals = company.get("signals", [])
    return SCORING_PROMPT.format(
        name=company.get("name", ""),
        title=company.get("title", ""),
        company=company.get("company", ""),
        employees=company.get("employees", ""),
        industry=company.get("industry", ""),
        location=company.get("location", ""),
        vertical=company.get("vertical", ""),
        description=company.get("short_description", "N/A")[:200],
        revenue=company.get("annual_revenue", "N/A"),
        founded=company.get("founded_year", "N/A"),
        seniority=company.get("seniority", "N/A"),
        headline=company.get("headline", "N/A")[:100],
        signals=", ".join(signals) if signals else "none detected",
        signal_count=company.get("signal_count", 0),
    )


def _parse_json(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown fences."""
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.split("```")[0]
    return json.loads(text.strip())


def _score_claude(prompt: str) -> dict | None:
    """Score with Claude Haiku."""
    try:
        msg = claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        return _parse_json(msg.content[0].text.strip())
    except Exception:
        return None


def _score_grok(prompt: str) -> dict | None:
    """Score with Grok (via X.AI API, OpenAI-compatible)."""
    if not GROK_API_KEY:
        return None
    try:
        r = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROK_API_KEY}",
            },
            json={
                "model": "grok-4-1-fast",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 250,
            },
            timeout=15,
        )
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"].strip()
            return _parse_json(text)
    except Exception:
        pass
    return None


def score(company: dict) -> dict:
    prompt = _build_prompt(company)

    # Primary: Claude Haiku
    claude_result = _score_claude(prompt)

    # Secondary: Grok (second opinion)
    grok_result = _score_grok(prompt)

    if claude_result and grok_result:
        # Dual scoring: 60% Claude + 40% Grok
        claude_score = claude_result.get("score", 5)
        grok_score = grok_result.get("score", 5)
        final_score = round(claude_score * 0.6 + grok_score * 0.4)
        final_score = max(1, min(10, final_score))

        company["intent_score"] = final_score
        company["claude_score"] = claude_score
        company["grok_score"] = grok_score
        # Use Claude's text (higher quality) but Grok's score as validation
        company["why_now"] = claude_result.get("why_now", "")
        company["hook"] = claude_result.get("hook", "")
        company["subject"] = claude_result.get("subject", "")

    elif claude_result:
        company["intent_score"] = claude_result.get("score", 5)
        company["why_now"] = claude_result.get("why_now", "")
        company["hook"] = claude_result.get("hook", "")
        company["subject"] = claude_result.get("subject", "")

    elif grok_result:
        company["intent_score"] = grok_result.get("score", 5)
        company["why_now"] = grok_result.get("why_now", "")
        company["hook"] = grok_result.get("hook", "")
        company["subject"] = grok_result.get("subject", "")

    else:
        company["intent_score"] = 5
        company["why_now"] = ""
        company["hook"] = ""
        company["subject"] = f"Quick question about {company.get('company', '')}"

    return company
