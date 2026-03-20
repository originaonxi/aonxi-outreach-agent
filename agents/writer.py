"""
Writes spam-proof, reply-optimized cold emails.
Uses real-time signals (Exa news, Grok X posts) when available.
Falls back to Claude Sonnet → Grok if Claude fails.

An email that opens with something that happened THIS WEEK
gets 28% reply rate vs 8% for generic.
"""

from __future__ import annotations
import json
import uuid
import requests
import anthropic
from config import ANTHROPIC_API_KEY, GROK_API_KEY

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

AONXI_BIO = """Sam Anmol, CTO @ Aonxi (aonxi.today).
We build AI agents that deliver qualified sales meetings on pay-per-outcome.
You pay only when a meeting happens. Not for software. Not for seats.
30+ clients. Non-competing per vertical per geography.
Ex-Meta Ads ML. Ex-Apple Face ID."""


def _build_prompt(company: dict) -> str:
    first_name = company.get("name", "").split()[0] or "there"
    recent_news = company.get("recent_news", "")
    x_signals = company.get("x_signals", "")

    signal_block = ""
    if recent_news or x_signals:
        signal_block = f"""
REAL-TIME INTELLIGENCE (use this to personalize the opening):
Recent company news: {recent_news or 'none found'}
Founder X/Twitter activity: {x_signals or 'none found'}

PRIORITY: If recent_news contains something specific and timely
(funding, hiring, product launch, expansion, partnership) —
open the email referencing it. This makes the email feel researched.

Example with news:
"Saw [Company] just closed its Series A — congrats.
The next question most founders have at that stage
is how to build pipeline without burning the raise on headcount."

Example with X signals:
"Your recent post about scaling outbound caught my eye —
that's exactly the problem we solve."

If no news/signals → fall back to vertical-specific observation.
"""

    return f"""Write a cold email from Sam Anmol (CTO @ Aonxi) to this prospect.

PROSPECT:
First name: {first_name}
Title: {company.get('title')}
Company: {company.get('company')}
Industry: {company.get('industry')}
Employees: {company.get('employees')}
Location: {company.get('location')}
Vertical: {company.get('vertical')}
Company description: {company.get('short_description', 'N/A')[:200]}

INTEL:
Why they need Aonxi now: {company.get('why_now')}
Personal hook: {company.get('hook')}
Their pain: {company.get('pain')}
Best angle: {company.get('angle')}
{signal_block}
ABOUT AONXI:
{AONXI_BIO}

EMAIL RULES (follow exactly):
1. Subject: use this — "{company.get('subject', 'Quick question')}"
2. Greeting: "Hi {first_name}," — nothing else
3. Line 1: One specific, TRUE observation about them or their company.
   If real-time news exists, reference it. If not, be specific to their size/vertical.
   NOT generic. NOT "I came across your company."
4. Line 2: Name their exact pain. One sentence. Their words, not ours.
5. Line 3: What Aonxi does. One sentence. Outcome first.
   "We deliver qualified meetings to your calendar — you pay only when one lands."
6. Line 4: One proof point. "30+ clients. Pay per outcome. Non-competing per market."
7. Line 5: ONE yes/no question or single-word-reply ask.
8. Sign-off: "Sam | origin@aonxi.com | aonxi.today"
9. NO: "I hope", "I wanted to", "I came across", "synergy", "leverage",
   "game-changing", "innovative", "best-in-class", "seamless", "robust"
10. Total body: under 100 words
11. Plain text only. No HTML. No bullet points. No bold.

Unique seed (ignore, just ensures uniqueness): {uuid.uuid4()}

Return JSON only:
{{
  "subject": "subject line",
  "body": "full email body with greeting and sign-off"
}}"""


def _parse_response(text: str) -> dict:
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.split("```")[0]
    return json.loads(text.strip())


def _write_claude(prompt: str) -> dict:
    """Write with Claude Sonnet (primary)."""
    msg = claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    return _parse_response(msg.content[0].text.strip())


def _write_grok(prompt: str) -> dict:
    """Write with Grok (fallback)."""
    r = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROK_API_KEY}",
        },
        json={
            "model": "grok-4-1-fast",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 400,
        },
        timeout=20,
    )
    text = r.json()["choices"][0]["message"]["content"].strip()
    return _parse_response(text)


def write(company: dict) -> dict:
    first_name = company.get("name", "").split()[0] or "there"
    prompt = _build_prompt(company)

    try:
        data = _write_claude(prompt)
    except Exception:
        try:
            if GROK_API_KEY:
                data = _write_grok(prompt)
            else:
                raise
        except Exception:
            data = None

    if data:
        company["email_subject"] = data.get("subject", company.get("subject", ""))
        company["email_body"] = data.get("body", "")
    else:
        company["email_subject"] = company.get("subject", "Quick question")
        company["email_body"] = (
            f"Hi {first_name},\n\n"
            f"{company.get('why_now', '')}\n\n"
            f"We deliver qualified meetings to your calendar — "
            f"you pay only when one lands. 30+ clients. "
            f"Non-competing per market.\n\n"
            f"Worth a 15-min call this week?\n\n"
            f"Sam | origin@aonxi.com | aonxi.today"
        )

    return company
