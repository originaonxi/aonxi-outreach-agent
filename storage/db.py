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
    """Push record to Airtable Outreach table."""
    from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE
    if not AIRTABLE_API_KEY:
        return
    try:
        import requests
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json",
        }

        # Map intent score to level
        score = company.get("intent_score", 0)
        intent_level = "High" if score >= 8 else ("Medium" if score >= 6 else "Low")

        # Build signals text
        signals = company.get("signals", [])
        news = company.get("recent_news", "")
        signal_text = ", ".join(signals)
        if news:
            signal_text += f"\nNews: {news[:200]}"

        fields = {
            "Name": company.get("name", ""),
            "Company": company.get("company", ""),
            "Title": company.get("title", ""),
            "Email": company.get("email", ""),
            "Vertical": company.get("vertical", ""),
            "Location": company.get("location", ""),
            "Company Size": str(company.get("employees", "")),
            "Intent Score": score,
            "Intent Level": intent_level,
            "Intent Signals": signal_text[:1000],
            "Email Subject": company.get("email_subject", ""),
            "Email Body": company.get("email_body", "")[:2000],
            "Status": status,
            "Source": company.get("source", "apollo"),
            "LinkedIn URL": company.get("linkedin", ""),
            "Date Added": date.today().isoformat(),
            "Sent Date": date.today().isoformat(),
            "Notes": f"Confidence: {company.get('email_confidence', 0)}/100",
        }

        r = requests.post(url, json={"fields": fields}, headers=headers, timeout=10)
        if r.status_code in (200, 201):
            return
        elif r.status_code == 422:
            # Some fields might not match select options — retry with text fields only
            safe_fields = {k: v for k, v in fields.items()
                          if k not in ("Vertical", "Intent Level", "Status", "Funding Stage")}
            r2 = requests.post(url, json={"fields": safe_fields}, headers=headers, timeout=10)
            if r2.status_code not in (200, 201):
                print(f"  Airtable: field mismatch — {r2.status_code}")
        else:
            print(f"  Airtable: {r.status_code}")
    except Exception as e:
        print(f"  Airtable: {e}")
