"""SQLite for dedup + Airtable for CRM."""

from __future__ import annotations
import sqlite3
from datetime import date

DB_PATH = "aonxi.db"


def init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS prospects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        domain TEXT,
        company TEXT,
        name TEXT,
        title TEXT,
        vertical TEXT,
        intent_score INTEGER,
        email_subject TEXT,
        email_body TEXT,
        sent INTEGER DEFAULT 0,
        date_added TEXT,
        date_sent TEXT,
        got_reply INTEGER DEFAULT 0,
        meeting_booked INTEGER DEFAULT 0,
        rating INTEGER
    )""")
    conn.commit()
    conn.close()


def get_seen_domains() -> set:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT domain FROM prospects")
    domains = {r[0] for r in c.fetchall()}
    conn.close()
    return domains


def save(company: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""INSERT OR IGNORE INTO prospects
            (email, domain, company, name, title, vertical,
             intent_score, email_subject, email_body, date_added)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (company.get("email", ""), company.get("domain", ""),
             company.get("company", ""), company.get("name", ""),
             company.get("title", ""), company.get("vertical", ""),
             company.get("intent_score", 0),
             company.get("email_subject", ""),
             company.get("email_body", ""),
             date.today().isoformat()))
        conn.commit()
    except Exception:
        pass
    conn.close()


def mark_sent(email: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE prospects SET sent=1, date_sent=? WHERE email=?",
              (date.today().isoformat(), email))
    conn.commit()
    conn.close()


def sync_airtable(company: dict, status: str = "Emailed"):
    from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE
    if not AIRTABLE_API_KEY:
        return
    try:
        from pyairtable import Api
        api = Api(AIRTABLE_API_KEY)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE)
        table.create({
            "Company": company.get("company", ""),
            "Name": company.get("name", ""),
            "Title": company.get("title", ""),
            "Email": company.get("email", ""),
            "Vertical": company.get("vertical", ""),
            "Intent Score": company.get("intent_score", 0),
            "Why Now": company.get("why_now", "")[:200],
            "Subject": company.get("email_subject", ""),
            "Body": company.get("email_body", "")[:2000],
            "Status": status,
            "Date": date.today().isoformat(),
        })
    except Exception as e:
        print(f"  Airtable: {e}")
