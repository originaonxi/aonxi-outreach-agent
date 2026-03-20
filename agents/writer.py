"""
Writes spam-proof, reply-optimized cold emails.

Anti-spam rules baked in:
- No mass-email phrases ("I hope this finds you", "reaching out")
- Personalized first line (specific to them)
- Plain text, no HTML, no images, no links except one
- Short (under 100 words body)
- One clear ask — a yes/no question or a one-word reply
- From a real person, to a real person
- No attachments
- Sends individually with name in To: field

Reply optimization:
- Opens with something true and specific about them
- Names their exact pain in their language
- One sentence on what Aonxi does (outcome-focused)
- Social proof (30 clients, pay per outcome)
- Closes with a question they want to answer
"""

from __future__ import annotations
import json
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

AONXI_BIO = """Sam Anmol, CTO @ Aonxi (aonxi.today).
We build AI agents that deliver qualified sales meetings on pay-per-outcome.
You pay only when a meeting happens. Not for software. Not for seats.
30+ clients. Non-competing per vertical per geography.
Ex-Meta Ads ML. Ex-Apple Face ID."""


def write(company: dict) -> dict:
    first_name = company.get("name", "").split()[0] or "there"

    prompt = f"""Write a cold email from Sam Anmol (CTO @ Aonxi) to this prospect.

PROSPECT:
First name: {first_name}
Title: {company.get('title')}
Company: {company.get('company')}
Industry: {company.get('industry')}
Employees: {company.get('employees')}
Location: {company.get('location')}
Vertical: {company.get('vertical')}

INTEL:
Why they need Aonxi now: {company.get('why_now')}
Personal hook: {company.get('hook')}
Their pain: {company.get('pain')}
Best angle: {company.get('angle')}

ABOUT AONXI:
{AONXI_BIO}

EMAIL RULES (follow exactly):
1. Subject: use this — "{company.get('subject', 'Quick question')}"
2. Greeting: "Hi {first_name}," — nothing else
3. Line 1: One specific, true observation about them or their company.
   NOT generic. References their vertical, size, or situation specifically.
4. Line 2: Name their exact pain. One sentence. Their words, not ours.
5. Line 3: What Aonxi does. One sentence. Outcome first.
   "We deliver qualified meetings to your calendar — you pay only when one lands."
6. Line 4: One proof point. "30+ clients. Pay per outcome. Non-competing per market."
7. Line 5: ONE yes/no question or single-word-reply ask.
   Example: "Worth a 15-min call this week?"
   Example: "Relevant?"
   Example: "Open to hearing how it works for {company.get('vertical')} companies?"
8. Sign-off: "Sam | origin@aonxi.com | aonxi.today"
9. NO: "I hope", "I wanted to", "I came across", "synergy", "leverage",
   "game-changing", "innovative", "best-in-class", "seamless", "robust"
10. Total body: under 100 words
11. Plain text only. No HTML. No bullet points. No bold.

Return JSON only:
{{
  "subject": "subject line",
  "body": "full email body with greeting and sign-off"
}}"""

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.split("```")[0]
        data = json.loads(text.strip())
        company["email_subject"] = data.get("subject", company.get("subject", ""))
        company["email_body"] = data.get("body", "")
    except Exception as e:
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
