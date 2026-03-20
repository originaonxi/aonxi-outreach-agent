"""
Hyper-personalized cold email writer.

Every email MUST open with ONE specific fact that proves
we researched THIS company and nobody else.

Not "you're growing fast." That's garbage.
Instead: "Taktile's Agentic Decision Platform just launched
for financial institutions" — something only they did.

The email connects that fact to their pain, then to Aonxi.
Under 100 words. Short. Specific. Human. Not corporate.
"""

from __future__ import annotations
import json
import uuid
import requests
import anthropic
from config import ANTHROPIC_API_KEY, GROK_API_KEY

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Vertical-specific Aonxi positioning — not generic "we deliver meetings"
VERTICAL_PITCH = {
    "SaaS": (
        "We replace your SDR team with an AI agent that finds your ICP, "
        "personalizes at scale, and books meetings. You pay per meeting."
    ),
    "Professional Services": (
        "We handle your entire new business pipeline — you focus on delivery, "
        "we fill your calendar with qualified prospects who already said yes."
    ),
    "E-Commerce": (
        "We find the B2B buyers and partners your brand needs — distributors, "
        "wholesalers, retail chains — and get them on your calendar."
    ),
    "Real Estate & Finance": (
        "We find qualified investors, partners, or clients in your exact market. "
        "You pay only when they show up to the meeting."
    ),
}


def _build_prompt(company: dict) -> str:
    first_name = company.get("name", "").split()[0] or "there"
    vertical = company.get("vertical", "SaaS")
    pitch = VERTICAL_PITCH.get(vertical, VERTICAL_PITCH["SaaS"])

    # Gather ALL intelligence
    news = company.get("recent_news", "")
    x_signals = company.get("x_signals", "")
    description = company.get("short_description", "")
    employees = company.get("employees", 0)
    why_now = company.get("why_now", "")
    hook = company.get("hook", "")
    signals = company.get("signals", [])

    intel_block = f"""ALL INTELLIGENCE (you MUST use at least 2 of these):
- Company description: {description or 'N/A'}
- Recent news: {news or 'none'}
- Founder X posts: {x_signals or 'none'}
- Why now: {why_now or 'N/A'}
- Personal hook: {hook or 'N/A'}
- Employees: {employees or 'unknown'}
- Signals: {', '.join(signals) if signals else 'none'}
- Vertical: {vertical}
- Their pain: {company.get('pain', '')}"""

    return f"""You are writing a cold email from Sam Anmol (CTO @ Aonxi) to {first_name} at {company.get('company', '')}.

{intel_block}

AONXI FOR THIS VERTICAL:
{pitch}
30+ clients. Non-competing per vertical per geography.
If they sign, no other {vertical.lower()} company in their geo gets this agent.

STRICT EMAIL STRUCTURE (follow EXACTLY):

LINE 1 — THE HOOK (mandatory):
Write ONE specific fact about THIS company that proves we researched them.
NOT "you're growing fast" or "I see you're in {vertical}."
USE the news, description, or X signals. Be SPECIFIC.
Good: "Saw Taktile just launched Agentic Decision Platform for banks."
Good: "Your 111% YoY growth across 6 countries is hard to ignore."
Good: "Your recent post about hiring 3 SDRs caught my eye."
Bad: "I noticed you're in the SaaS space." (generic trash)
Bad: "Running a growing company is tough." (says nothing)

LINE 2 — THE PAIN (connect hook to their problem):
Name what that specific fact means for their outbound.
"That means your sales team needs to reach every mid-size bank — without hiring 10 SDRs."
"At that growth rate, manual outbound becomes the bottleneck before you can justify a full team."

LINE 3 — WHAT AONXI DOES (one sentence, outcome only):
"{pitch}"

LINE 4 — PROOF + EXCLUSIVITY:
"30+ clients. Non-competing — if you sign, no other {vertical.lower()} company in your market gets this."

LINE 5 — CLOSE WITH THEIR SITUATION (not generic):
Ask about THEIR specific reality. Reference a number, a signal, or their situation.
Good: "You're at 88% growth — is outbound keeping up?"
Good: "With 6 countries to cover, how's pipeline looking?"
Bad: "Worth a conversation?" (lazy)
Bad: "Interested?" (zero effort)

SIGN-OFF: "Sam | origin@aonxi.com | aonxi.today"

RULES:
- Subject: "{company.get('subject', 'Quick question')}"
- Greeting: "Hi {first_name}," only
- Under 100 words body
- Plain text. No HTML. No bullets. No bold.
- NO: "I hope", "I wanted to", "reaching out", "I came across",
  "synergy", "leverage", "game-changing", "innovative", "seamless"
- Every sentence must be specific to THIS company. Zero generic filler.

Unique seed: {uuid.uuid4()}

Return JSON:
{{
  "subject": "subject line",
  "body": "the full email with greeting and sign-off",
  "confidence": 0-100,
  "confidence_reasons": ["reason 1", "reason 2", "reason 3"]
}}

confidence scoring:
- +30 if opening references specific news/product/event
- +20 if pain is connected to a real fact about them
- +15 if close references their specific numbers/situation
- +15 if vertical pitch is relevant
- +10 if under 80 words
- +10 if subject is under 6 words
- -20 if any line is generic (could apply to any company)
- -30 if opening is "I noticed you're in [vertical]" type garbage"""


def _parse_response(text: str) -> dict:
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.split("```")[0]
    return json.loads(text.strip())


def _write_claude(prompt: str) -> dict:
    msg = claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return _parse_response(msg.content[0].text.strip())


def _write_grok(prompt: str) -> dict:
    if not GROK_API_KEY:
        raise Exception("No Grok key")
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
            "max_tokens": 500,
        },
        timeout=20,
    )
    text = r.json()["choices"][0]["message"]["content"].strip()
    return _parse_response(text)


def write(company: dict) -> dict:
    first_name = company.get("name", "").split()[0] or "there"
    prompt = _build_prompt(company)

    data = None
    try:
        data = _write_claude(prompt)
    except Exception:
        try:
            data = _write_grok(prompt)
        except Exception:
            pass

    if data:
        company["email_subject"] = data.get("subject", company.get("subject", ""))
        company["email_body"] = data.get("body", "")
        company["email_confidence"] = data.get("confidence", 50)
        company["confidence_reasons"] = data.get("confidence_reasons", [])
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
        company["email_confidence"] = 30
        company["confidence_reasons"] = ["Fallback template — no personalization"]

    return company
