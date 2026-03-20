"""
Learning database — self-correcting revenue intelligence.

Per-vertical ICP tables + combo stats + feedback tracking.
Every outcome teaches the next decision.
"""

from __future__ import annotations
import sqlite3
from datetime import date, timedelta
from storage.db import DB_PATH


VERTICALS = ["saas", "professional_services", "ecommerce", "real_estate"]

VERTICAL_TABLE_MAP = {
    "SaaS": "saas_icp",
    "Professional Services": "professional_services_icp",
    "E-Commerce": "ecommerce_icp",
    "Real Estate & Finance": "real_estate_icp",
}


def init_learning_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Per-vertical ICP tables
    for table in VERTICAL_TABLE_MAP.values():
        c.execute(f"""CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            domain TEXT UNIQUE,
            contact_name TEXT,
            contact_title TEXT,
            email TEXT,
            employees INTEGER,
            location TEXT,
            apollo_score INTEGER,
            historical_score REAL DEFAULT 0,
            final_score REAL DEFAULT 0,
            emails_sent INTEGER DEFAULT 0,
            last_email_date TEXT,
            replied INTEGER DEFAULT 0,
            reply_date TEXT,
            meeting_booked INTEGER DEFAULT 0,
            meeting_date TEXT,
            outcome TEXT,
            notes TEXT,
            created_at TEXT
        )""")

    # Feedback from user (did they reply?)
    c.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        company TEXT,
        vertical TEXT,
        title TEXT,
        intent_score INTEGER,
        outcome TEXT,
        date_sent TEXT,
        date_feedback TEXT
    )""")

    # Combo stats: vertical + title_bucket + size_bucket → reply rate
    c.execute("""CREATE TABLE IF NOT EXISTS combo_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vertical TEXT,
        title_bucket TEXT,
        size_bucket TEXT,
        emails_sent INTEGER DEFAULT 0,
        replies INTEGER DEFAULT 0,
        meetings INTEGER DEFAULT 0,
        avg_intent_score REAL DEFAULT 0,
        last_updated TEXT,
        UNIQUE(vertical, title_bucket, size_bucket)
    )""")

    # Winning patterns — subject lines and angles that got replies
    c.execute("""CREATE TABLE IF NOT EXISTS winning_angles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vertical TEXT,
        title_bucket TEXT,
        subject_line TEXT,
        reply_count INTEGER DEFAULT 0,
        send_count INTEGER DEFAULT 0,
        win_rate REAL DEFAULT 0,
        last_updated TEXT
    )""")

    conn.commit()
    conn.close()


def get_title_bucket(title: str) -> str:
    """Bucket titles into categories for learning."""
    t = title.lower()
    if any(w in t for w in ["ceo", "founder", "co-founder", "owner", "president"]):
        return "C-Level/Founder"
    elif any(w in t for w in ["vp", "vice president", "cro", "cmo", "cto", "cfo"]):
        return "VP/C-Suite"
    elif any(w in t for w in ["director", "head of", "managing"]):
        return "Director/Head"
    elif any(w in t for w in ["partner", "principal"]):
        return "Partner"
    else:
        return "Other"


def get_size_bucket(employees: int) -> str:
    if employees <= 25:
        return "10-25"
    elif employees <= 50:
        return "26-50"
    elif employees <= 100:
        return "51-100"
    elif employees <= 200:
        return "101-200"
    else:
        return "200+"


def save_to_icp_table(company: dict):
    """Save a prospect to their vertical-specific ICP table."""
    vertical = company.get("vertical", "")
    table = VERTICAL_TABLE_MAP.get(vertical)
    if not table:
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    apollo_score = company.get("intent_score", 5)
    historical = get_historical_rate(vertical, company.get("title", ""))
    final_score = (apollo_score * 0.6) + (historical * 10 * 0.4)  # scale to 10

    try:
        c.execute(f"""INSERT OR IGNORE INTO {table}
            (company, domain, contact_name, contact_title, email, employees,
             location, apollo_score, historical_score, final_score, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (company.get("company"), company.get("domain"),
             company.get("name"), company.get("title"),
             company.get("email"), company.get("employees", 0),
             company.get("location"), apollo_score,
             historical, round(final_score, 1),
             date.today().isoformat()))
        conn.commit()
    except Exception:
        pass
    conn.close()


def mark_icp_sent(email: str, vertical: str):
    """Mark a prospect as emailed in their ICP table."""
    table = VERTICAL_TABLE_MAP.get(vertical)
    if not table:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"""UPDATE {table} SET
        emails_sent = emails_sent + 1,
        last_email_date = ?
        WHERE email = ?""", (date.today().isoformat(), email))
    conn.commit()
    conn.close()


def get_historical_rate(vertical: str, title: str) -> float:
    """Get historical reply rate for this vertical + title combo. Returns 0-1."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    title_bucket = get_title_bucket(title)

    c.execute("""SELECT SUM(emails_sent), SUM(replies)
        FROM combo_stats WHERE vertical=? AND title_bucket=?""",
        (vertical, title_bucket))
    row = c.fetchone()
    conn.close()

    if not row or not row[0] or row[0] < 5:
        return 0.0

    return (row[1] or 0) / row[0]


def record_feedback(email: str, outcome: str):
    """Record feedback. outcome: 'reply', 'meeting', 'no_reply'"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get prospect info
    c.execute("""SELECT name, company, vertical, title, intent_score, date_sent,
            email_subject
        FROM prospects WHERE email=?""", (email,))
    row = c.fetchone()
    if not row:
        conn.close()
        return

    name, company, vertical, title, intent_score, date_sent, subject = row

    # Save feedback
    c.execute("""INSERT OR REPLACE INTO feedback
        (email, name, company, vertical, title, intent_score, outcome, date_sent, date_feedback)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (email, name, company, vertical, title, intent_score, outcome,
         date_sent, date.today().isoformat()))

    # Update prospect record
    if outcome == "reply":
        c.execute("UPDATE prospects SET got_reply=1 WHERE email=?", (email,))
    elif outcome == "meeting":
        c.execute("UPDATE prospects SET got_reply=1, meeting_booked=1 WHERE email=?", (email,))

    # Update ICP table
    table = VERTICAL_TABLE_MAP.get(vertical)
    if table:
        if outcome in ("reply", "meeting"):
            c.execute(f"UPDATE {table} SET replied=1, reply_date=? WHERE email=?",
                      (date.today().isoformat(), email))
        if outcome == "meeting":
            c.execute(f"UPDATE {table} SET meeting_booked=1, meeting_date=? WHERE email=?",
                      (date.today().isoformat(), email))
        c.execute(f"UPDATE {table} SET outcome=? WHERE email=?", (outcome, email))

    # Update combo stats
    title_bucket = get_title_bucket(title or "")
    size_bucket = "unknown"  # we don't store employees in prospects table

    c.execute("""INSERT INTO combo_stats
        (vertical, title_bucket, size_bucket, emails_sent, replies, meetings, last_updated)
        VALUES (?, ?, ?, 1, ?, ?, ?)
        ON CONFLICT(vertical, title_bucket, size_bucket) DO UPDATE SET
            emails_sent = emails_sent + 1,
            replies = replies + ?,
            meetings = meetings + ?,
            last_updated = ?""",
        (vertical, title_bucket, size_bucket,
         1 if outcome in ("reply", "meeting") else 0,
         1 if outcome == "meeting" else 0,
         date.today().isoformat(),
         1 if outcome in ("reply", "meeting") else 0,
         1 if outcome == "meeting" else 0,
         date.today().isoformat()))

    # Track winning subject lines
    if outcome in ("reply", "meeting") and subject:
        c.execute("""INSERT INTO winning_angles (vertical, title_bucket, subject_line, reply_count, send_count, win_rate, last_updated)
            VALUES (?, ?, ?, 1, 1, 1.0, ?)
            ON CONFLICT DO NOTHING""",
            (vertical, title_bucket, subject, date.today().isoformat()))

    conn.commit()
    conn.close()


def get_combo_boost(vertical: str, title: str) -> float:
    """
    Self-correcting score adjustment based on historical combo performance.
    Returns -2.0 to +2.0.
    """
    rate = get_historical_rate(vertical, title)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    title_bucket = get_title_bucket(title)
    c.execute("""SELECT SUM(emails_sent) FROM combo_stats
        WHERE vertical=? AND title_bucket=?""", (vertical, title_bucket))
    row = c.fetchone()
    conn.close()

    total = row[0] if row and row[0] else 0
    if total < 5:
        return 0.0

    if rate > 0.25:
        return 2.0
    elif rate > 0.15:
        return 1.0
    elif rate > 0.08:
        return 0.0
    elif rate > 0.03:
        return -1.0
    else:
        return -2.0


def get_pending_feedback() -> list[dict]:
    """Get emails sent 3+ days ago with no feedback yet."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    three_days_ago = (date.today() - timedelta(days=3)).isoformat()

    c.execute("""SELECT p.email, p.name, p.company, p.vertical, p.title,
            p.email_subject, p.date_sent, p.intent_score
        FROM prospects p
        LEFT JOIN feedback f ON p.email = f.email
        WHERE p.sent = 1
            AND p.date_sent <= ?
            AND f.email IS NULL
        ORDER BY p.date_sent DESC""", (three_days_ago,))

    results = []
    for row in c.fetchall():
        results.append({
            "email": row[0],
            "name": row[1],
            "company": row[2],
            "vertical": row[3],
            "title": row[4],
            "subject": row[5],
            "date_sent": row[6],
            "intent_score": row[7],
        })

    conn.close()
    return results


def get_performance_report() -> dict:
    """Get full performance data for the weekly report."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    report = {}

    # Overall stats
    c.execute("SELECT COUNT(*) FROM prospects WHERE sent=1")
    report["total_sent"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE got_reply=1")
    report["total_replies"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE meeting_booked=1")
    report["total_meetings"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects")
    report["total_discovered"] = c.fetchone()[0]

    # This week stats
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    c.execute("SELECT COUNT(*) FROM prospects WHERE sent=1 AND date_sent >= ?", (week_ago,))
    report["week_sent"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE got_reply=1 AND date_sent >= ?", (week_ago,))
    report["week_replies"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE meeting_booked=1 AND date_sent >= ?", (week_ago,))
    report["week_meetings"] = c.fetchone()[0]

    # By vertical
    c.execute("""SELECT vertical, COUNT(*),
        SUM(CASE WHEN got_reply=1 THEN 1 ELSE 0 END),
        SUM(CASE WHEN meeting_booked=1 THEN 1 ELSE 0 END)
        FROM prospects WHERE sent=1
        GROUP BY vertical ORDER BY COUNT(*) DESC""")
    report["by_vertical"] = []
    for row in c.fetchall():
        sent = row[1]
        replies = row[2] or 0
        meetings = row[3] or 0
        report["by_vertical"].append({
            "vertical": row[0],
            "sent": sent,
            "replies": replies,
            "meetings": meetings,
            "reply_rate": round(replies / sent * 100, 1) if sent > 0 else 0,
        })

    # By title bucket (from combo_stats)
    c.execute("""SELECT title_bucket, SUM(emails_sent), SUM(replies), SUM(meetings)
        FROM combo_stats GROUP BY title_bucket ORDER BY SUM(emails_sent) DESC""")
    report["by_title"] = []
    for row in c.fetchall():
        sent = row[1]
        replies = row[2] or 0
        meetings = row[3] or 0
        report["by_title"].append({
            "title": row[0],
            "sent": sent,
            "replies": replies,
            "meetings": meetings,
            "reply_rate": round(replies / sent * 100, 1) if sent > 0 else 0,
        })

    # Best combo segments
    c.execute("""SELECT vertical, title_bucket, size_bucket, emails_sent, replies, meetings
        FROM combo_stats WHERE emails_sent >= 3
        ORDER BY CAST(replies AS REAL) / emails_sent DESC LIMIT 5""")
    report["best_segments"] = []
    for row in c.fetchall():
        rate = round(row[4] / row[3] * 100, 1) if row[3] > 0 else 0
        report["best_segments"].append({
            "vertical": row[0], "title": row[1], "size": row[2],
            "sent": row[3], "replies": row[4], "rate": rate
        })

    # Worst segments
    c.execute("""SELECT vertical, title_bucket, size_bucket, emails_sent, replies
        FROM combo_stats WHERE emails_sent >= 5
        ORDER BY CAST(replies AS REAL) / emails_sent ASC LIMIT 3""")
    report["worst_segments"] = []
    for row in c.fetchall():
        rate = round(row[4] / row[3] * 100, 1) if row[3] > 0 else 0
        report["worst_segments"].append({
            "vertical": row[0], "title": row[1], "size": row[2],
            "sent": row[3], "replies": row[4], "rate": rate
        })

    # Subject line performance
    c.execute("""SELECT email_subject, got_reply FROM prospects WHERE sent=1
        ORDER BY date_sent DESC LIMIT 50""")
    subjects = c.fetchall()
    report["recent_subjects"] = [{"subject": s[0], "replied": s[1]} for s in subjects]

    # ICP table sizes
    report["icp_sizes"] = {}
    for vname, table in VERTICAL_TABLE_MAP.items():
        try:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            report["icp_sizes"][vname] = c.fetchone()[0]
        except Exception:
            report["icp_sizes"][vname] = 0

    conn.close()
    return report
