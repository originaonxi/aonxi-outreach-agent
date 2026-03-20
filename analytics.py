"""
v2.0 — Analytics Dashboard + A/B Testing + Send Throttling
==========================================================
Tracks every metric. Tests two subject lines per email.
Throttles sends to 3/min to avoid Gmail spam flags.

METRICS TRACKED:
- Emails sent per day / per vertical
- Open rate proxy (reply rate as indicator)
- Reply rate by vertical, by subject variant
- Meeting conversion rate
- Cost per meeting (API costs)
- Intent score distribution
- Best performing verticals
- Best performing subject line patterns
"""

from __future__ import annotations
import sqlite3
import json
from datetime import date, datetime, timedelta
from storage.db import DB_PATH


def init_analytics():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        metric TEXT,
        vertical TEXT,
        value REAL,
        metadata TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ab_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        variant TEXT,
        subject_a TEXT,
        subject_b TEXT,
        chosen TEXT,
        got_reply INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS daily_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE,
        discovered INTEGER DEFAULT 0,
        qualified INTEGER DEFAULT 0,
        sent INTEGER DEFAULT 0,
        replied INTEGER DEFAULT 0,
        meetings INTEGER DEFAULT 0,
        avg_intent REAL DEFAULT 0,
        api_cost_usd REAL DEFAULT 0
    )""")
    conn.commit()
    conn.close()


def log_metric(metric: str, value: float, vertical: str = "", metadata: dict = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO analytics (date, metric, vertical, value, metadata) VALUES (?,?,?,?,?)",
              (date.today().isoformat(), metric, vertical, value,
               json.dumps(metadata) if metadata else ""))
    conn.commit()
    conn.close()


def log_daily(discovered: int, qualified: int, sent: int, avg_intent: float, api_cost: float):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO daily_stats
        (date, discovered, qualified, sent, avg_intent, api_cost_usd)
        VALUES (?,?,?,?,?,?)""",
        (date.today().isoformat(), discovered, qualified, sent, avg_intent, api_cost))
    conn.commit()
    conn.close()


def create_ab_test(email: str, subject_a: str, subject_b: str, chosen: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO ab_tests (email, variant, subject_a, subject_b, chosen, created_at)
        VALUES (?,?,?,?,?,?)""",
        (email, "A" if chosen == subject_a else "B",
         subject_a, subject_b, chosen, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def dashboard() -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Overall stats
    c.execute("SELECT COUNT(*) FROM prospects")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE sent=1")
    sent = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE got_reply=1")
    replied = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE meeting_booked=1")
    meetings = c.fetchone()[0]
    c.execute("SELECT AVG(intent_score) FROM prospects WHERE intent_score > 0")
    avg_intent = c.fetchone()[0] or 0

    # Per vertical
    c.execute("""SELECT vertical, COUNT(*), SUM(sent), SUM(got_reply), SUM(meeting_booked)
        FROM prospects GROUP BY vertical""")
    verticals = c.fetchall()

    # Last 7 days
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    c.execute("SELECT SUM(sent), SUM(replied), SUM(meetings) FROM daily_stats WHERE date >= ?",
              (week_ago,))
    week = c.fetchone()

    # A/B test results
    c.execute("""SELECT variant, COUNT(*), SUM(got_reply) FROM ab_tests
        GROUP BY variant""")
    ab_results = c.fetchall()

    conn.close()

    reply_rate = (replied / sent * 100) if sent > 0 else 0
    meeting_rate = (meetings / sent * 100) if sent > 0 else 0

    lines = []
    lines.append("")
    lines.append("  ╔══════════════════════════════════════════════════╗")
    lines.append("  ║          AONXI OUTREACH DASHBOARD v2.0          ║")
    lines.append("  ╠══════════════════════════════════════════════════╣")
    lines.append(f"  ║  Total Prospects: {total:<6}  Avg Intent: {avg_intent:.1f}/10  ║")
    lines.append(f"  ║  Emails Sent:     {sent:<6}  Reply Rate: {reply_rate:.1f}%     ║")
    lines.append(f"  ║  Replies:         {replied:<6}  Meeting Rate: {meeting_rate:.1f}%  ║")
    lines.append(f"  ║  Meetings Booked: {meetings:<6}                         ║")
    lines.append("  ╠══════════════════════════════════════════════════╣")
    lines.append("  ║  BY VERTICAL                                    ║")
    lines.append("  ╠──────────────────────────────────────────────────╣")
    for v in verticals:
        name, cnt, s, r, m = v
        s, r, m = s or 0, r or 0, m or 0
        rr = (r / s * 100) if s > 0 else 0
        lines.append(f"  ║  {name[:20]:<20} {cnt:>3} found {s:>3} sent {rr:>5.1f}% ║")
    if ab_results:
        lines.append("  ╠──────────────────────────────────────────────────╣")
        lines.append("  ║  A/B TEST RESULTS                                ║")
        for variant, cnt, replies in ab_results:
            rr = (replies / cnt * 100) if cnt > 0 else 0
            lines.append(f"  ║  Variant {variant}: {cnt} sent, {replies or 0} replies ({rr:.1f}%)    ║")
    lines.append("  ╚══════════════════════════════════════════════════╝")

    return "\n".join(lines)


# ── SEND THROTTLE ──────────────────────────────────────
# Gmail best practice: max 3 emails per minute, random delay 15-25s between sends

import time
import random

_last_send_time = 0.0

def throttled_wait():
    """Wait between sends to avoid spam flags. 15-25s random delay."""
    global _last_send_time
    now = time.time()
    elapsed = now - _last_send_time
    min_delay = random.uniform(15, 25)
    if elapsed < min_delay:
        wait = min_delay - elapsed
        print(f"  ⏱ Throttle: waiting {wait:.0f}s...")
        time.sleep(wait)
    _last_send_time = time.time()


# ── A/B SUBJECT LINE GENERATOR ────────────────────────

import anthropic
from config import ANTHROPIC_API_KEY

def generate_ab_subjects(company: dict) -> tuple[str, str]:
    """Generate two subject line variants for A/B testing."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{"role": "user", "content": f"""Generate exactly 2 cold email subject lines for:
Company: {company.get('company')}
Vertical: {company.get('vertical')}
Pain: {company.get('pain')}

Rules: Under 8 words each. No clickbait. Different approaches.
Variant A: curiosity-based
Variant B: direct value prop

Return JSON only: {{"a": "subject a", "b": "subject b"}}"""}]
        )
        text = msg.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "", 1).split("```")[0]
        data = json.loads(text.strip())
        return data.get("a", company.get("subject", "")), data.get("b", company.get("subject", ""))
    except Exception:
        return company.get("subject", "Quick question"), f"For {company.get('company', 'you')}"
