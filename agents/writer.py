"""
Hyper-personalized cold email writer.

Aonxi is NOT an outreach tool. Aonxi builds a CUSTOM AI AGENT
for each client that:
- Pulls from 30+ data sources
- Researches every prospect like a team of senior analysts
- Micro-tests subject lines and angles automatically
- Learns after every send — gets smarter every week
- Books qualified meetings
- Pay per meeting — zero cost until it delivers

Every line of every email must reference something TRUE and
SPECIFIC about THIS company. No line should be sendable to
any other company on earth.
"""

from __future__ import annotations
import json
import re
import uuid
import requests
import anthropic
from config import ANTHROPIC_API_KEY, GROK_API_KEY

# MemCollab — cross-agent shared memory
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "memcollab"))
try:
    from memcollab import build_memory_injection
    MEMCOLLAB_AVAILABLE = True
except ImportError:
    MEMCOLLAB_AVAILABLE = False

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

VERTICAL_PITCH = {
    "SaaS": (
        "We build a custom AI agent for your exact ICP — "
        "pulls 30+ data sources, researches every prospect "
        "like a senior analyst, micro-tests angles, and books "
        "qualified meetings. Pay per meeting. Zero SDR cost."
    ),
    "Professional Services": (
        "We build a custom AI agent for your new business pipeline — "
        "researches your exact target clients using 30+ data sources, "
        "micro-tests outreach angles, and fills your calendar with "
        "qualified prospects. Pay only when a meeting happens."
    ),
    "E-Commerce": (
        "We build a custom AI agent that finds your B2B buyers — "
        "distributors, wholesalers, retail chains — using 30+ data "
        "sources, micro-tests messaging, and books qualified meetings. "
        "Pay per meeting."
    ),
    "Real Estate & Finance": (
        "We build a custom AI agent for your exact market — "
        "researches qualified investors, partners, or clients "
        "using 30+ data sources, and books qualified meetings. "
        "Pay only when they show up."
    ),
}

FORBIDDEN = [
    "I noticed", "I came across", "reaching out", "hope this finds",
    "just wanted to", "I wanted to", "touch base", "quick question",
    "circle back", "follow up", "synergy", "leverage", "game-changing",
    "innovative", "seamless", "world-class", "best-in-class",
    "cutting-edge", "excited to", "passionate about", "I hope",
    "robust", "scalable solution",
]

EXAMPLES = """
EXAMPLE 1 — SaaS (post-acquisition):
Subject: Your pipeline after the DealHub deal
Hi David,
DealHub acquired Subskribe to go agentic — your pipeline needs to match that ambition without rebuilding headcount.
We build a custom AI agent for your exact ICP: pulls from 30+ data sources, researches each prospect like a senior analyst, micro-tests subject lines and angles, and books qualified meetings. You pay only when a meeting lands. Zero SDR cost.
This is not a tool. It is your outbound team — fully autonomous, learning after every send, getting sharper every week.
Non-competing — no other quote-to-revenue company in your market gets this.
Is this worth 15 minutes?
Sam | origin@aonxi.com | aonxi.today

EXAMPLE 2 — E-Commerce:
Subject: Merchant acquisition on autopilot
Hi Amir,
Cart.com powers thousands of storefronts — but enterprise merchant acquisition is still manual.
We build a custom AI agent that handles your entire B2B outbound: researches distributors, wholesalers, and retail chains using 30+ data sources, micro-tests messaging until something converts, and books qualified meetings. Pay per meeting.
30+ clients running this. No competing commerce platforms in the same geo.
How's enterprise merchant pipeline looking right now?
Sam | origin@aonxi.com | aonxi.today

EXAMPLE 3 — Agency:
Subject: New business without the BD grind
Hi Marcus,
SPEED Agency is growing fast — but new business development still eats time you should spend on clients.
We build a custom AI agent for your agency: pulls data from 30+ sources to find your exact ICP brands, researches each one like a senior strategist, micro-tests outreach angles, and books qualified intro calls. Pay only when a meeting happens.
This is not an email tool. It is your entire new business function — running 24/7, learning after every send.
Non-competing — no other agency in your market gets this.
Open to seeing it in action?
Sam | origin@aonxi.com | aonxi.today
"""


# ── Defense Profiling ─────────────────────────────────────────────

GTM_COMPANIES = {
    "gong", "outreach", "salesloft", "hubspot", "salesforce", "apollo",
    "zoominfo", "chorus", "clari", "drift", "intercom", "sendoso",
    "6sense", "bombora", "demandbase", "seismic", "highspot", "clearbit",
}

DEFENSE_MODES = {
    "MOTIVE_INFERENCE": {
        "title_signals": {"partner", "vp", "director", "founder", "head of sales", "chief revenue", "cro"},
        "forbidden_phrases": [
            "excited", "reach out", "love to", "synergy", "opportunity",
            "quick call", "touching base", "circle back", "on your radar",
        ],
        "bypass_strategy": "PURE_DATA",
    },
    "TACTIC_RECOGNITION": {
        "title_signals": {"founder", "co-founder", "serial entrepreneur", "repeat founder", "ceo"},
        "forbidden_phrases": [
            "I noticed you", "I came across", "relevant to your work",
            "fellow founder", "as a fellow", "I saw that you",
            "your impressive", "your amazing",
        ],
        "bypass_strategy": "SIGNAL_HOOK",
    },
    "OVERLOAD_AVOIDANCE": {
        "title_signals": {"ceo", "owner", "operator", "president", "managing director", "gm"},
        "forbidden_phrases": [
            "just wanted to", "hope this finds you", "I know you're busy",
            "when you get a chance", "at your convenience", "quick question",
        ],
        "bypass_strategy": "PURE_DATA",
    },
    "SOCIAL_PROOF_SKEPTICISM": {
        "title_signals": {"cto", "engineer", "vp engineering", "technical", "data", "architect", "developer"},
        "forbidden_phrases": [
            "industry-leading", "best-in-class", "proven", "trusted by",
            "world-class", "top-tier", "leading provider", "market leader",
        ],
        "bypass_strategy": "CREDIBILITY_FIRST",
    },
}

BYPASS_INSTRUCTIONS_MAP = {
    "PURE_DATA": "Open with a concrete number. Never open with 'I'. Lead with verifiable data. No persuasion language — let the numbers do the work.",
    "SIGNAL_HOOK": "Open by referencing something specific from the last 7 days — their post, their hire, their funding news. Prove you did real research, not a template merge.",
    "CREDIBILITY_FIRST": "Open with exact numbers and a public-verifiable proof point (GitHub link, public metric). No round numbers. No unverifiable claims.",
}


def _detect_defense_mode_outreach(company: dict) -> str:
    """Detect primary defense mode from company/contact profile."""
    title = (company.get("title") or "").lower()
    company_name = (company.get("company") or "").lower()

    # GTM company background → MOTIVE_INFERENCE
    if any(gtm in company_name for gtm in GTM_COMPANIES):
        return "MOTIVE_INFERENCE"

    # Check title signals in priority order
    for mode_name in ["SOCIAL_PROOF_SKEPTICISM", "MOTIVE_INFERENCE", "TACTIC_RECOGNITION", "OVERLOAD_AVOIDANCE"]:
        mode = DEFENSE_MODES[mode_name]
        for signal in mode["title_signals"]:
            if signal in title:
                return mode_name

    # Fallback based on seniority
    if any(kw in title for kw in ("c-suite", "chief", "vp", "head")):
        return "MOTIVE_INFERENCE"

    return "TACTIC_RECOGNITION"


def profile_defenses(target: dict) -> dict:
    """
    Profile a target's psychological defenses against cold outreach.
    Returns awareness_score, defense_mode, bypass_strategy, forbidden_phrases.
    """
    title = (target.get("title") or "").lower()
    company_name = (target.get("company") or "").lower()
    employees = target.get("employees", 0) or 0

    # Awareness score: 0-10
    score = 3  # baseline
    if any(kw in title for kw in ("vp", "director", "chief", "head", "partner")):
        score += 3
    elif any(kw in title for kw in ("founder", "ceo", "cto", "president")):
        score += 2
    if any(gtm in company_name for gtm in GTM_COMPANIES):
        score += 3
    if employees and employees > 500:
        score += 1
    elif employees and employees > 100:
        score += 1

    # Estimate inbox volume
    estimated_volume = 50
    if any(kw in title for kw in ("ceo", "founder", "vp", "director")):
        estimated_volume = 150
    if employees and employees > 200:
        estimated_volume += 50
    if estimated_volume >= 150:
        score += 1

    score = min(score, 10)

    defense_mode = _detect_defense_mode_outreach(target)
    mode_profile = DEFENSE_MODES[defense_mode]

    return {
        "awareness_score": score,
        "defense_mode": defense_mode,
        "bypass_strategy": mode_profile["bypass_strategy"],
        "forbidden_phrases": mode_profile["forbidden_phrases"],
        "estimated_weekly_cold_emails": estimated_volume,
    }


def _extract_specifics(company: dict) -> list[str]:
    """Pull every specific, usable fact about this company."""
    specifics = []
    news = company.get("recent_news", "") or ""
    desc = company.get("short_description", "") or ""
    x = company.get("x_signals", "") or ""
    all_text = f"{news} {desc} {x}"

    # Revenue numbers
    for match in re.findall(r'\$[\d,.]+[MBK]?\s*(?:ARR|revenue|raised|funding|valuation)?', all_text, re.IGNORECASE):
        specifics.append(f"Revenue/funding: {match.strip()}")

    # Percentages
    for match in re.findall(r'[\d.]+%\s*(?:YoY|growth|increase|decline)?', all_text):
        specifics.append(f"Growth metric: {match.strip()}")

    # Employee count
    emp = company.get("employees", 0)
    if emp and emp > 0:
        specifics.append(f"Headcount: {emp} employees")

    # Product names from description
    if desc and len(desc) > 20:
        specifics.append(f"Product/Description: {desc[:150]}")

    # News events
    news_lower = news.lower()
    if "acqui" in news_lower:
        specifics.append("Event: acquisition/merger")
    if "launch" in news_lower:
        specifics.append("Event: product launch")
    if any(w in news_lower for w in ["series a", "series b", "series c", "seed", "raised"]):
        specifics.append("Event: funding round")
    if "hir" in news_lower:
        specifics.append("Event: hiring/growth")

    # Signals
    signals = company.get("signals", [])
    if signals:
        specifics.append(f"Signals: {', '.join(signals)}")

    return specifics


def _build_prompt(company: dict, defense: dict | None = None) -> str:
    first_name = company.get("name", "").split()[0] or "there"
    vertical = company.get("vertical", "SaaS")
    pitch = VERTICAL_PITCH.get(vertical, VERTICAL_PITCH["SaaS"])
    specifics = _extract_specifics(company)

    return f"""You are Sam Anmol, CTO at Aonxi. Ex-Meta Ads ML (billions/day), ex-Apple Face ID (500M devices). You understand scale. Write like a smart peer talking to another smart operator — not a salesperson pitching a prospect.

Write a cold email to {first_name} at {company.get('company', '')}.

COMPANY DATA (use ALL of this):
- Company: {company.get('company', '')}
- Contact: {first_name} {company.get('name', '').split()[-1] if len(company.get('name', '').split()) > 1 else ''} ({company.get('title', '')})
- Vertical: {vertical}
- Employees: {company.get('employees', 'unknown')}
- Description: {company.get('short_description', 'N/A')[:250]}
- Recent news: {company.get('recent_news', 'none')[:300]}
- X/Twitter: {company.get('x_signals', 'none')[:200]}
- Why now: {company.get('why_now', 'N/A')}
- Hook: {company.get('hook', 'N/A')}
- Signals: {', '.join(company.get('signals', [])) or 'none'}

EXTRACTED SPECIFICS (you MUST weave at least 2 into the email):
{chr(10).join(f'  - {s}' for s in specifics) if specifics else '  - No specifics found — use description and vertical context'}

WHAT AONXI IS (say this, not "outreach tool"):
{pitch}

This is NOT a tool. It is their outbound team — fully autonomous, learning after every send, getting sharper every week.

Non-competing — if they sign, no other {vertical.lower()} company in their market gets this agent.

{EXAMPLES}

EMAIL STRUCTURE:
1. HOOK: One sentence about something SPECIFIC to THIS company. A fact, a number, a recent event. Not "you're in SaaS." Reference their actual product, their actual news, their actual numbers.
2. PAIN: Connect that fact to their outbound challenge. Why does THAT fact mean they need pipeline help RIGHT NOW?
3. PITCH: The Aonxi custom agent pitch (from above). Not "we deliver meetings." Say what the agent DOES — 30+ sources, researches like an analyst, micro-tests, books meetings.
4. DIFFERENTIATOR: "This is not a tool. It is your outbound team." + non-competing exclusivity.
5. CLOSE: Ask about THEIR specific situation using a number or fact from their data. NOT "Worth a chat?" — that is lazy garbage.

RULES:
- Subject must reference something specific to them (not generic)
- Greeting: "Hi {first_name}," only
- Under 120 words body
- Plain text. No HTML. No bullets. No bold.
- Sign-off: "Sam | origin@aonxi.com | aonxi.today"
- FORBIDDEN PHRASES (instant -30 confidence if used): {', '.join(f'"{f}"' for f in FORBIDDEN[:12])}
- Every sentence must fail the "could this be sent to any other company?" test. If yes, rewrite it.

{_defense_prompt_block(defense) if defense else ''}
{_memcollab_block(defense, vertical) if defense else ''}
Unique seed: {uuid.uuid4()}

Return JSON only:
{{
  "subject": "specific subject referencing their company/situation",
  "body": "the full email with greeting and sign-off",
  "confidence": 0-100,
  "confidence_reasons": ["reason1", "reason2", "reason3"]
}}

Confidence scoring:
+30 opening references specific fact (product name, revenue, event)
+20 pain connects to a real data point about them
+15 close uses their specific number or situation
+15 pitch is customized to their vertical
+10 under 100 words
-20 any generic line (sendable to another company)
-30 any forbidden phrase used"""


def _memcollab_block(defense: dict | None, vertical: str = "") -> str:
    """Inject cross-agent learned patterns from MemCollab shared memory."""
    if not defense or not MEMCOLLAB_AVAILABLE:
        return ""
    try:
        return build_memory_injection(defense["defense_mode"], vertical=vertical)
    except Exception:
        return ""


def _defense_prompt_block(defense: dict) -> str:
    """Build the defense profiling injection for the prompt."""
    if not defense:
        return ""
    banned = ", ".join(f'"{p}"' for p in defense["forbidden_phrases"])
    bypass = BYPASS_INSTRUCTIONS_MAP[defense["bypass_strategy"]]
    block = f"""
DEFENSE PROFILE (awareness: {defense['awareness_score']}/10, mode: {defense['defense_mode']}):
ADDITIONAL BANNED WORDS — never use any of these phrases: {banned}
WRITING STRATEGY OVERRIDE: {bypass}"""
    if defense["defense_mode"] == "OVERLOAD_AVOIDANCE":
        block += "\nHARD OVERRIDE: Under 60 words. One specific ask. Specific calendar slot, never 'let me know'."
    return block


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
        max_tokens=600,
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
            "max_tokens": 600,
        },
        timeout=25,
    )
    text = r.json()["choices"][0]["message"]["content"].strip()
    return _parse_response(text)


def write(company: dict, use_defense_profiling: bool = True) -> dict:
    first_name = company.get("name", "").split()[0] or "there"

    # Defense profiling
    defense = profile_defenses(company) if use_defense_profiling else None
    prompt = _build_prompt(company, defense=defense)

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
        company["defense_profile"] = defense
    else:
        vertical = company.get("vertical", "SaaS")
        pitch = VERTICAL_PITCH.get(vertical, VERTICAL_PITCH["SaaS"])
        company["email_subject"] = company.get("subject", "Quick question")
        company["email_body"] = (
            f"Hi {first_name},\n\n"
            f"{company.get('why_now', '')}\n\n"
            f"{pitch}\n\n"
            f"Non-competing — no other {vertical.lower()} company "
            f"in your market gets this.\n\n"
            f"Sam | origin@aonxi.com | aonxi.today"
        )
        company["email_confidence"] = 30
        company["confidence_reasons"] = ["Fallback template — no hyper-personalization"]

    return company
