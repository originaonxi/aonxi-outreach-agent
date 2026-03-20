#!/usr/bin/env python3
"""
aonxi-outreach — The Aonxi Outreach CLI
=========================================
Type `aonxi-outreach` → see fresh companies → y/n on each email → sent.

Every run finds different companies. Every email is unique.
Real-time signals from Exa + Grok make it elite.
Auto-pushes results to git after every run.
"""

from __future__ import annotations
import os
import sys
import smtplib
import subprocess
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Ensure we can import from project root
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
    MIN_INTENT_SCORE, ANTHROPIC_API_KEY, APOLLO_API_KEY, ICP,
)
from storage.db import init, get_seen_domains, save, mark_sent, sync_airtable
from storage.learning_db import init_learning_db, get_combo_boost, save_to_icp_table, mark_icp_sent
from agents.discovery import discover
from agents.enrichment import enrich
from agents.intent import score
from agents.signals import enrich_with_signals
from agents.writer import write
from agents.send_time import get_send_status


# ── COLORS ──────────────────────────────────────────────
class C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    RESET = "\033[0m"


def banner():
    print()
    print(f"  {C.BOLD}{C.CYAN}")
    print(f"   ┌─────────────────────────────────────────────┐")
    print(f"   │         AONXI OUTREACH AGENT                │")
    print(f"   │         Find. Signal. Write. Send. Close.   │")
    print(f"   └─────────────────────────────────────────────┘{C.RESET}")
    print(f"  {C.DIM}  {datetime.now().strftime('%A, %B %d %Y  %H:%M')}{C.RESET}")
    print()


def send_email(company: dict) -> bool:
    if not SMTP_PASS:
        print(f"  {C.RED}SMTP_PASS not set — email not sent{C.RESET}")
        return False
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
        print(f"  {C.RED}Send failed: {e}{C.RESET}")
        return False


def show_email(company: dict, idx: int, total: int):
    """Show a single email for review."""
    score_val = company.get("intent_score", 0)
    bar = f"{C.GREEN}{'█' * score_val}{C.DIM}{'░' * (10 - score_val)}{C.RESET}"
    signals = company.get("signals", [])
    signal_tags = " ".join(f"{C.DIM}[{s}]{C.RESET}" for s in signals[:5])

    # Send time
    loc = company.get("location", "")
    optimal, time_str = get_send_status(loc)
    time_color = C.GREEN if optimal else C.YELLOW
    time_label = f"{time_color}{time_str}{C.RESET}"

    print()
    print(f"  {C.BOLD}{C.WHITE}┌── [{idx}/{total}] ─────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.BOLD}│ {company['company']}{C.RESET} — {company['name']} ({company['title']})")
    emp = company.get('employees', '?')
    print(f"  │ {C.CYAN}{company['vertical']}{C.RESET} · {emp} emp · {loc}")
    print(f"  │ Intent: {bar} {score_val}/10  Send: {time_label}")
    print(f"  │ {signal_tags}")
    if company.get("recent_news"):
        print(f"  │ {C.MAGENTA}News: {company['recent_news'][:70]}...{C.RESET}")
    if company.get("x_signals"):
        print(f"  │ {C.MAGENTA}X: {company['x_signals'][:70]}...{C.RESET}")
    if company.get("why_now"):
        print(f"  │ {C.DIM}{company['why_now'][:80]}{C.RESET}")
    print(f"  ├──────────────────────────────────────────────────────┤")
    print(f"  │ {C.DIM}To:{C.RESET} {company['name']} <{company['email']}>")
    print(f"  │ {C.BOLD}Subject: {company['email_subject']}{C.RESET}")
    print(f"  │")
    for line in company["email_body"].split("\n"):
        print(f"  │ {line}")
    print(f"  {C.WHITE}└──────────────────────────────────────────────────────┘{C.RESET}")


def git_push_results(sent: int, skipped: int, total: int):
    """Auto-push run results to git."""
    try:
        os.chdir(PROJECT_DIR)
        # Stage the database (has the new prospects + feedback data)
        subprocess.run(["git", "add", "aonxi.db"], capture_output=True, timeout=10)
        msg = (
            f"Run {datetime.now().strftime('%Y-%m-%d %H:%M')}: "
            f"{total} found, {sent} sent, {skipped} skipped"
        )
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            push = subprocess.run(
                ["git", "push", "origin", "main"],
                capture_output=True, text=True, timeout=30
            )
            if push.returncode == 0:
                print(f"  {C.DIM}Git: pushed results{C.RESET}")
            else:
                print(f"  {C.DIM}Git: committed locally{C.RESET}")
    except Exception:
        pass


def run():
    banner()

    # Preflight
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not APOLLO_API_KEY:
        missing.append("APOLLO_API_KEY")
    if missing:
        print(f"  {C.RED}Missing: {', '.join(missing)}{C.RESET}")
        print(f"  {C.DIM}Set them in .env{C.RESET}")
        sys.exit(1)

    init()
    init_learning_db()

    # ── DISCOVER ───────────────────────────────────────
    seen = get_seen_domains()
    print(f"  {C.DIM}Already contacted: {len(seen)} domains{C.RESET}")
    print()
    print(f"  {C.BOLD}[1/5] Finding fresh companies...{C.RESET}")

    companies = discover(seen)

    if not companies:
        print(f"\n  {C.YELLOW}No new companies found. Try again later.{C.RESET}")
        return

    print(f"\n  {C.GREEN}Found {len(companies)} new companies{C.RESET}")

    # ── ENRICH + SCORE ─────────────────────────────────
    print(f"\n  {C.BOLD}[2/5] Enriching + scoring...{C.RESET}")
    for i, c in enumerate(companies):
        companies[i] = enrich(c)
        companies[i] = score(companies[i])

        # Self-correcting: boost/lower based on historical combo performance
        boost = get_combo_boost(c.get("vertical", ""), c.get("title", ""))
        if boost != 0:
            raw = companies[i].get("intent_score", 5)
            adjusted = max(1, min(10, round(raw + boost)))
            companies[i]["intent_score"] = adjusted
            companies[i]["score_boost"] = boost

        s = companies[i].get("intent_score", 0)
        bar = f"{C.GREEN}{'█' * s}{C.DIM}{'░' * (10 - s)}{C.RESET}"
        boost_str = ""
        if boost > 0:
            boost_str = f" {C.GREEN}+{boost:.0f}{C.RESET}"
        elif boost < 0:
            boost_str = f" {C.RED}{boost:.0f}{C.RESET}"
        print(f"    {bar} {s}/10 {c['company']} ({c['vertical']}){boost_str}")

    # Sort by intent (highest first)
    companies.sort(key=lambda x: x.get("intent_score", 0), reverse=True)

    # Filter to qualified
    qualified = [c for c in companies if c.get("intent_score", 0) >= MIN_INTENT_SCORE]
    below = len(companies) - len(qualified)

    print(f"\n  {C.GREEN}Qualified: {len(qualified)}{C.RESET}", end="")
    if below:
        print(f"  {C.DIM}(skipped {below} below {MIN_INTENT_SCORE}/10){C.RESET}")
    else:
        print()

    if not qualified:
        print(f"\n  {C.YELLOW}No qualified prospects this run. Try again for fresh results.{C.RESET}")
        return

    # ── REAL-TIME SIGNALS ─────────────────────────────
    print(f"\n  {C.BOLD}[3/5] Getting real-time signals (Exa + Grok)...{C.RESET}")
    for i, c in enumerate(qualified):
        qualified[i] = enrich_with_signals(c)

    # ── WRITE EMAILS ──────────────────────────────────
    print(f"\n  {C.BOLD}[4/5] Writing emails (Claude + signals)...{C.RESET}")
    for i, c in enumerate(qualified):
        qualified[i] = write(c)
        save(qualified[i])
        save_to_icp_table(qualified[i])
        news_tag = f" {C.MAGENTA}[+news]{C.RESET}" if c.get("recent_news") else ""
        x_tag = f" {C.MAGENTA}[+X]{C.RESET}" if c.get("x_signals") else ""
        print(f"    {C.DIM}Wrote: {c['company']}{C.RESET}{news_tag}{x_tag}")

    # ── REVIEW & SEND ─────────────────────────────────
    print()
    print(f"  {C.BOLD}{C.CYAN}[5/5] REVIEW & SEND ════════════════════════════════{C.RESET}")
    print(f"  {C.DIM}  y = send now    n = skip    q = quit{C.RESET}")

    sent = 0
    skipped = 0

    for i, company in enumerate(qualified, 1):
        show_email(company, i, len(qualified))

        while True:
            try:
                action = input(f"\n  {C.BOLD}  [{company['company']}] y/n/q → {C.RESET}").strip().lower()
            except (EOFError, KeyboardInterrupt):
                action = "q"

            if action in ("y", "n", "q"):
                break
            print(f"  {C.DIM}  Type y, n, or q{C.RESET}")

        if action == "q":
            print(f"\n  {C.DIM}Stopped.{C.RESET}")
            break
        elif action == "y":
            if send_email(company):
                mark_sent(company["email"])
                mark_icp_sent(company["email"], company.get("vertical", ""))
                sync_airtable(company)
                sent += 1
                print(f"  {C.GREEN}  Sent → {company['email']}{C.RESET}")
                if i < len(qualified):
                    wait = 15
                    print(f"  {C.DIM}  Cooling down {wait}s...{C.RESET}", end="", flush=True)
                    time.sleep(wait)
                    print(f" done{C.RESET}")
            else:
                skipped += 1
        else:
            skipped += 1
            print(f"  {C.DIM}  Skipped{C.RESET}")

    # ── SUMMARY + GIT PUSH ────────────────────────────
    print()
    print(f"  {C.BOLD}{C.CYAN}┌─────────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  {C.GREEN}Sent: {sent}{C.RESET}    Skipped: {skipped}    Total: {len(qualified)}  {C.BOLD}{C.CYAN}│{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  Replies land at: origin@aonxi.com          {C.BOLD}{C.CYAN}│{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  Run again anytime for fresh companies       {C.BOLD}{C.CYAN}│{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}└─────────────────────────────────────────────┘{C.RESET}")

    # Auto-push to git
    git_push_results(sent, skipped, len(qualified))
    print()


if __name__ == "__main__":
    run()
