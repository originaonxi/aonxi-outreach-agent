#!/usr/bin/env python3
"""
aonxi-feedback — Log replies to teach the agent what works.

Run every 3 days. Shows emails sent 3+ days ago.
You tell it: did they reply? (y/n/meeting)
The agent learns and adjusts future scoring.
"""

from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.db import init
from storage.learning_db import init_learning_db, get_pending_feedback, record_feedback

# MemCollab — update trajectory outcomes from manual feedback
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "memcollab"))
try:
    from memcollab import update_outcome as mc_update_outcome
    MEMCOLLAB_AVAILABLE = True
except ImportError:
    MEMCOLLAB_AVAILABLE = False

FEEDBACK_TO_OUTCOME = {
    "reply": "HOT",
    "meeting": "MEETING",
    "no_reply": "NO_REPLY",
}


def _mc_update(email_addr: str, feedback_type: str):
    """Update MemCollab trajectory outcome from manual feedback."""
    if not MEMCOLLAB_AVAILABLE:
        return
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "aonxi.db"))
        c = conn.cursor()
        c.execute("SELECT memcollab_tid FROM prospects WHERE email=?", (email_addr,))
        row = c.fetchone()
        conn.close()
        tid = row[0] if row and row[0] else ""
        if tid:
            outcome = FEEDBACK_TO_OUTCOME.get(feedback_type)
            if outcome:
                mc_update_outcome(tid, outcome)
    except Exception:
        pass


class C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"


def run():
    print()
    print(f"  {C.BOLD}{C.CYAN}")
    print(f"   ┌─────────────────────────────────────────────┐")
    print(f"   │         AONXI FEEDBACK LOOP                 │")
    print(f"   │         Teach the agent what works           │")
    print(f"   └─────────────────────────────────────────────┘{C.RESET}")
    print()

    init()
    init_learning_db()

    pending = get_pending_feedback()

    if not pending:
        print(f"  {C.GREEN}No emails need feedback yet.{C.RESET}")
        print(f"  {C.DIM}(Emails need to be 3+ days old with no logged outcome){C.RESET}")
        print()
        return

    print(f"  {C.BOLD}{len(pending)} emails need feedback{C.RESET}")
    print(f"  {C.DIM}  y = they replied    m = meeting booked    n = no reply    q = quit{C.RESET}")
    print()

    replies = 0
    meetings = 0
    no_reply = 0

    for i, p in enumerate(pending, 1):
        days_ago = p.get("date_sent", "?")
        print(f"  {C.BOLD}[{i}/{len(pending)}]{C.RESET} {C.CYAN}{p['company']}{C.RESET} — {p['name']} ({p['title']})")
        print(f"  {C.DIM}Sent: {days_ago} | {p['vertical']} | Intent: {p['intent_score']}/10{C.RESET}")
        print(f"  {C.DIM}Subject: {p['subject']}{C.RESET}")

        while True:
            try:
                action = input(f"  {C.BOLD}Did {p['name'].split()[0]} reply? [y/n/m/q] → {C.RESET}").strip().lower()
            except (EOFError, KeyboardInterrupt):
                action = "q"

            if action in ("y", "n", "m", "q"):
                break
            print(f"  {C.DIM}  y=replied, n=no reply, m=meeting booked, q=quit{C.RESET}")

        if action == "q":
            print(f"\n  {C.DIM}Stopped.{C.RESET}")
            break
        elif action == "y":
            record_feedback(p["email"], "reply")
            replies += 1
            print(f"  {C.GREEN}  Logged: replied{C.RESET}")
            _mc_update(p["email"], "reply")
        elif action == "m":
            record_feedback(p["email"], "meeting")
            meetings += 1
            print(f"  {C.GREEN}{C.BOLD}  Logged: MEETING BOOKED{C.RESET}")
            _mc_update(p["email"], "meeting")
        else:
            record_feedback(p["email"], "no_reply")
            no_reply += 1
            print(f"  {C.DIM}  Logged: no reply{C.RESET}")
            _mc_update(p["email"], "no_reply")

        print()

    # Summary
    total = replies + meetings + no_reply
    if total > 0:
        print(f"  {C.BOLD}{C.CYAN}┌─────────────────────────────────────────────┐{C.RESET}")
        print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  Logged: {C.GREEN}{replies} replies{C.RESET}, {C.GREEN}{C.BOLD}{meetings} meetings{C.RESET}, {no_reply} silent  {C.BOLD}{C.CYAN}│{C.RESET}")
        if total > 0:
            rate = (replies + meetings) / total * 100
            print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  Reply rate: {rate:.0f}%                            {C.BOLD}{C.CYAN}│{C.RESET}")
        print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  {C.DIM}The agent will use this to improve scoring{C.RESET}   {C.BOLD}{C.CYAN}│{C.RESET}")
        print(f"  {C.BOLD}{C.CYAN}└─────────────────────────────────────────────┘{C.RESET}")
        print()


if __name__ == "__main__":
    run()
