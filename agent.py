"""
Aonxi HAGI Outreach Agent
=========================
Runs at 7am PST daily.
Finds 20 ICP companies. Scores them. Writes emails.
Shows each one: y=send, n=skip.
Sends from lifeislovesam@gmail.com.
Logs to SQLite + Airtable.
"""

from __future__ import annotations
import sys
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
    MIN_INTENT_SCORE, ANTHROPIC_API_KEY
)
from storage.db import init, get_seen_domains, save, mark_sent, sync_airtable
from agents.discovery import discover
from agents.enrichment import enrich
from agents.intent import score
from agents.writer import write


def send(company: dict) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = company["email_subject"]
        msg["From"] = f"Sam Anmol <{SMTP_USER}>"
        msg["To"] = f"{company['name']} <{company['email']}>"
        msg["Reply-To"] = "origin@aonxi.com"
        msg.attach(MIMEText(company["email_body"], "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.ehlo()
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, company["email"], msg.as_string())
        return True
    except Exception as e:
        print(f"  ✗ Send failed: {e}")
        return False


def preview(company: dict, idx: int, total: int) -> str:
    print()
    print(f"  ┌─ [{idx}/{total}] ─────────────────────────────────────")
    print(f"  │ {company['company']} — {company['name']} ({company['title']})")
    print(f"  │ {company['vertical']} · {company['employees']} employees · {company['location']}")
    print(f"  │ Intent: {company.get('intent_score',0)}/10 · {company.get('why_now','')}")
    print(f"  ├────────────────────────────────────────────────────")
    print(f"  │ To: {company['name']} <{company['email']}>")
    print(f"  │ Subject: {company['email_subject']}")
    print(f"  │")
    for line in company["email_body"].split("\n"):
        print(f"  │ {line}")
    print(f"  └────────────────────────────────────────────────────")
    return input("     [y] send  [n] skip  [e] edit  [q] quit → ").strip().lower()


def run():
    print()
    print("━" * 55)
    print("  AONXI HAGI OUTREACH AGENT")
    print(f"  {datetime.now().strftime('%A, %B %d %Y · %H:%M PST')}")
    print("━" * 55)
    print()

    if not ANTHROPIC_API_KEY:
        print("  ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    init()

    # ── DISCOVER ──────────────────────────────────────────
    print("  [1/4] Discovering 20 companies...")
    companies = discover(get_seen_domains())
    print(f"  Found: {len(companies)} new companies\n")

    if not companies:
        print("  No new companies today.")
        return

    # ── ENRICH ────────────────────────────────────────────
    print("  [2/4] Enriching...")
    for i, c in enumerate(companies):
        companies[i] = enrich(c)
    print(f"  Done.\n")

    # ── SCORE ─────────────────────────────────────────────
    print("  [3/4] Scoring intent...")
    for i, c in enumerate(companies):
        companies[i] = score(c)
        s = companies[i].get("intent_score", 0)
        bar = "█" * s + "░" * (10 - s)
        print(f"  {bar} {s}/10 · {c['company']} ({c['vertical']})")

    qualified = [c for c in companies if c.get("intent_score", 0) >= MIN_INTENT_SCORE]
    print(f"\n  Qualified (≥{MIN_INTENT_SCORE}/10): {len(qualified)}/{len(companies)}\n")

    if not qualified:
        print("  No qualified prospects today.")
        return

    # ── WRITE ─────────────────────────────────────────────
    print("  [4/4] Writing emails...")
    for i, c in enumerate(qualified):
        qualified[i] = write(c)
        save(qualified[i])
    print(f"  Done. {len(qualified)} emails ready.\n")

    # ── HUMAN REVIEW ──────────────────────────────────────
    print("  ── REVIEW QUEUE ──────────────────────────────────")
    print("  y=send  n=skip  e=edit subject  q=quit\n")

    sent = skipped = 0

    for i, company in enumerate(qualified, 1):
        action = preview(company, i, len(qualified))

        if action == "q":
            print("\n  Stopped.")
            break
        elif action == "e":
            new_subj = input("  New subject: ").strip()
            if new_subj:
                company["email_subject"] = new_subj
            action = input("  Send now? y/n → ").strip().lower()

        if action == "y":
            if send(company):
                mark_sent(company["email"])
                sync_airtable(company)
                print(f"  ✓ Sent → {company['email']}")
                sent += 1
            else:
                skipped += 1
        else:
            skipped += 1

    print()
    print("━" * 55)
    print(f"  ✓ Sent: {sent}  ✗ Skipped: {skipped}")
    print(f"  Replies land at: origin@aonxi.com")
    print(f"  Next run: tomorrow 7am PST")
    print("━" * 55)
    print()


if __name__ == "__main__":
    run()
