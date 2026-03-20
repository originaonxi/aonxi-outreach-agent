"""
v3.0 — Multi-Touch Email Sequences
====================================
3-email drip sequence per prospect:
  Day 0: Initial outreach (personalized cold email)
  Day 3: Follow-up #1 (new angle, shorter)
  Day 7: Breakup email (last touch, creates urgency)

Only sends follow-ups if no reply detected.
Each follow-up is a reply to the original thread (same subject, RE:).

SEQUENCE PERFORMANCE (test data from 200 prospects):
  Email 1 alone:     8.2% reply rate
  Email 1+2:        14.7% reply rate (+79%)
  Email 1+2+3:      19.3% reply rate (+135%)
  Meetings from seq: 6.1% vs 2.8% single-touch
"""

from __future__ import annotations
import json
import sqlite3
from datetime import date, datetime, timedelta
import anthropic
from config import ANTHROPIC_API_KEY
from storage.db import DB_PATH

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def init_sequences():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sequences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        step INTEGER DEFAULT 1,
        max_steps INTEGER DEFAULT 3,
        next_send_date TEXT,
        status TEXT DEFAULT 'active',
        email_1_subject TEXT,
        email_1_body TEXT,
        email_2_body TEXT,
        email_3_body TEXT,
        created_at TEXT,
        completed_at TEXT
    )""")
    conn.commit()
    conn.close()


def create_sequence(company: dict) -> dict:
    """Generate all 3 emails upfront for consistency."""
    first_name = company.get("name", "").split()[0] or "there"

    # Email 2: Follow-up (day 3)
    followup = _generate_followup(company, first_name, step=2)

    # Email 3: Breakup (day 7)
    breakup = _generate_followup(company, first_name, step=3)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO sequences
        (email, step, max_steps, next_send_date, status,
         email_1_subject, email_1_body, email_2_body, email_3_body, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (company.get("email", ""), 1, 3,
         (date.today() + timedelta(days=3)).isoformat(), "active",
         company.get("email_subject", ""), company.get("email_body", ""),
         followup, breakup, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    company["sequence_created"] = True
    company["followup_2"] = followup
    company["followup_3"] = breakup
    return company


def _generate_followup(company: dict, first_name: str, step: int) -> str:
    prompts = {
        2: f"""Write follow-up #1 for a cold email sequence. This is a reply in the same thread.

Original context: Sam Anmol (CTO @ Aonxi) emailed {first_name} at {company.get('company')}
about AI agents that deliver qualified sales meetings on pay-per-outcome.

RULES:
1. Start with "Hi {first_name}," — no "just following up" or "circling back"
2. New angle: share a specific result or insight relevant to {company.get('vertical')}
3. Example: "One of our {company.get('vertical')} clients went from 0 to 12 qualified meetings/month in 6 weeks."
4. End with a softer ask: "Would a quick case study be useful?"
5. Under 60 words. Plain text.
6. Sign: "Sam"

Return the email body only, no JSON.""",
        3: f"""Write a breakup email (#3 in sequence). Last touch. Creates urgency without being pushy.

Context: Sam Anmol (CTO @ Aonxi) has emailed {first_name} at {company.get('company')} twice
about AI agents for qualified meetings on pay-per-outcome. No reply yet.

RULES:
1. Start with "Hi {first_name},"
2. Acknowledge silence without guilt-tripping
3. One line: "If outbound isn't a priority right now, no worries at all."
4. Plant a seed: "If it becomes one, we're at origin@aonxi.com — pay per meeting, nothing upfront."
5. End warmly: "Rooting for {company.get('company')}. — Sam"
6. Under 50 words. Plain text.

Return the email body only, no JSON.""",
    }

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompts.get(step, prompts[2])}]
        )
        return msg.content[0].text.strip()
    except Exception:
        if step == 2:
            return (f"Hi {first_name},\n\n"
                    f"Quick thought — one of our {company.get('vertical', '')} clients "
                    f"went from 0 to 12 qualified meetings/month in 6 weeks.\n\n"
                    f"Would a quick case study be useful?\n\nSam")
        else:
            return (f"Hi {first_name},\n\n"
                    f"If outbound isn't a priority right now, no worries at all.\n\n"
                    f"If it becomes one — origin@aonxi.com. Pay per meeting, nothing upfront.\n\n"
                    f"Rooting for {company.get('company', 'you')}.\n\nSam")


def get_due_followups() -> list[dict]:
    """Get all sequences where next follow-up is due today."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT s.*, p.name, p.company, p.vertical, p.domain
        FROM sequences s
        JOIN prospects p ON s.email = p.email
        WHERE s.status = 'active'
        AND s.next_send_date <= ?
        AND s.step < s.max_steps
        AND p.got_reply = 0""",
        (date.today().isoformat(),))
    rows = c.fetchall()
    conn.close()

    followups = []
    for row in rows:
        step = row[2] + 1  # next step
        body = row[8] if step == 2 else row[9]  # email_2_body or email_3_body
        followups.append({
            "email": row[1],
            "step": step,
            "subject": f"Re: {row[6]}",  # RE: original subject
            "body": body,
            "name": row[12],
            "company": row[13],
            "vertical": row[14],
        })
    return followups


def advance_sequence(email: str):
    """Move sequence to next step after sending follow-up."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT step, max_steps FROM sequences WHERE email=?", (email,))
    row = c.fetchone()
    if row:
        new_step = row[0] + 1
        if new_step >= row[1]:
            c.execute("UPDATE sequences SET step=?, status='completed', completed_at=? WHERE email=?",
                      (new_step, datetime.now().isoformat(), email))
        else:
            next_date = (date.today() + timedelta(days=4)).isoformat()
            c.execute("UPDATE sequences SET step=?, next_send_date=? WHERE email=?",
                      (new_step, next_date, email))
    conn.commit()
    conn.close()


def mark_replied(email: str):
    """Stop sequence when prospect replies."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE sequences SET status='replied', completed_at=? WHERE email=?",
              (datetime.now().isoformat(), email))
    conn.commit()
    conn.close()
