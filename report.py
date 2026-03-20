#!/usr/bin/env python3
"""
aonxi-report — Revenue Intelligence Dashboard.

Shows: pipeline, verticals, segments, TAM/SAM, multi-channel, actions.
The self-correcting HAGI feedback loop in one screen.
"""

from __future__ import annotations
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.db import init
from storage.learning_db import init_learning_db, get_performance_report


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


# TAM estimates (US + target geos, 10-300 employees)
TAM = {
    "SaaS": 85000,
    "Professional Services": 210000,
    "E-Commerce": 45000,
    "Real Estate & Finance": 120000,
}


def run():
    init()
    init_learning_db()

    r = get_performance_report()

    total_sent = r["total_sent"]
    total_replies = r["total_replies"]
    total_meetings = r["total_meetings"]
    total_discovered = r["total_discovered"]
    reply_rate = (total_replies / total_sent * 100) if total_sent > 0 else 0
    meeting_rate = (total_meetings / total_sent * 100) if total_sent > 0 else 0

    week_sent = r["week_sent"]
    week_replies = r["week_replies"]
    week_meetings = r["week_meetings"]
    w_rr = (week_replies / week_sent * 100) if week_sent > 0 else 0
    w_mr = (week_meetings / week_sent * 100) if week_sent > 0 else 0

    pipeline_value = total_meetings * 5000  # est $5K avg deal

    # ── HEADER ────────────────────────────────────────
    print()
    print(f"  {C.BOLD}{C.CYAN}╔═══════════════════════════════════════════════════════╗")
    print(f"  ║       AONXI REVENUE INTELLIGENCE REPORT             ║")
    print(f"  ║       Week of {date.today().isoformat()}                          ║")
    print(f"  ╚═══════════════════════════════════════════════════════╝{C.RESET}")
    print()

    # ── PIPELINE SUMMARY ──────────────────────────────
    print(f"  {C.BOLD}PIPELINE SUMMARY{C.RESET}")
    print(f"  {C.DIM}{'─' * 50}{C.RESET}")
    print(f"  Discovered:      {C.BOLD}{total_discovered}{C.RESET}")
    print(f"  Emails sent:     {C.BOLD}{total_sent}{C.RESET}  (this week: {week_sent})")
    print(f"  Replies:         {C.GREEN}{total_replies}{C.RESET}  ({reply_rate:.1f}% reply rate)")
    print(f"  Meetings booked: {C.GREEN}{C.BOLD}{total_meetings}{C.RESET}  ({meeting_rate:.1f}% meeting rate)")
    print(f"  Pipeline value:  {C.GREEN}{C.BOLD}${pipeline_value:,}{C.RESET}  ({total_meetings} x $5K avg)")
    print()

    # ── THIS WEEK ─────────────────────────────────────
    if week_sent > 0:
        print(f"  {C.BOLD}THIS WEEK{C.RESET}")
        print(f"  {C.DIM}{'─' * 50}{C.RESET}")
        print(f"  Sent: {week_sent}  |  Replies: {C.GREEN}{week_replies}{C.RESET} ({w_rr:.1f}%)  |  Meetings: {C.GREEN}{C.BOLD}{week_meetings}{C.RESET} ({w_mr:.1f}%)")
        print()

    # ── BY VERTICAL ───────────────────────────────────
    verticals = r.get("by_vertical", [])
    if verticals:
        print(f"  {C.BOLD}BY VERTICAL{C.RESET}")
        print(f"  {C.DIM}{'Vertical':<25} {'Sent':>5} {'Replies':>8} {'Rate':>7} {'Meetings':>9} {'Trend':>6}{C.RESET}")
        print(f"  {C.DIM}{'─' * 65}{C.RESET}")

        best_v = max(verticals, key=lambda x: x["reply_rate"]) if verticals else None
        worst_v = min(verticals, key=lambda x: x["reply_rate"]) if verticals else None

        for v in verticals:
            trend = "  "
            if v == best_v and v["reply_rate"] > 10:
                trend = f"{C.GREEN} ↑{C.RESET}"
            elif v == worst_v and v["reply_rate"] < 5:
                trend = f"{C.RED} ↓{C.RESET}"
            else:
                trend = f"{C.YELLOW} →{C.RESET}"

            color = C.GREEN if v["reply_rate"] >= 15 else (C.YELLOW if v["reply_rate"] >= 5 else C.RED)
            print(f"  {v['vertical']:<25} {v['sent']:>5} {v['replies']:>8} {color}{v['reply_rate']:>6.1f}%{C.RESET} {v['meetings']:>9} {trend}")
        print()

    # ── BEST SEGMENTS ─────────────────────────────────
    best = r.get("best_segments", [])
    if best:
        print(f"  {C.BOLD}{C.GREEN}BEST PERFORMING SEGMENTS{C.RESET}")
        print(f"  {C.DIM}{'─' * 50}{C.RESET}")
        for s in best:
            print(f"  {C.GREEN}  {s['vertical']} + {s['title']}: {s['rate']}% reply rate ({s['sent']} sent){C.RESET}")
        print()

    worst = r.get("worst_segments", [])
    if worst:
        print(f"  {C.BOLD}{C.RED}WORST PERFORMING SEGMENTS{C.RESET}")
        print(f"  {C.DIM}{'─' * 50}{C.RESET}")
        for s in worst:
            print(f"  {C.RED}  {s['vertical']} + {s['title']}: {s['rate']}% reply rate ({s['sent']} sent){C.RESET}")
            print(f"  {C.DIM}  → Auto-reducing priority next week{C.RESET}")
        print()

    # ── SUBJECT LINES ─────────────────────────────────
    subjects = r.get("recent_subjects", [])
    winners = [s for s in subjects if s["replied"]]
    losers = [s for s in subjects if not s["replied"]]

    if winners:
        print(f"  {C.BOLD}{C.GREEN}WINNING SUBJECT LINES{C.RESET}")
        print(f"  {C.DIM}{'─' * 50}{C.RESET}")
        for s in winners[:5]:
            print(f"  {C.GREEN}  + \"{s['subject']}\"{C.RESET}")
        print()

    if losers:
        print(f"  {C.BOLD}{C.DIM}SILENT SUBJECT LINES{C.RESET}")
        print(f"  {C.DIM}{'─' * 50}{C.RESET}")
        for s in losers[:3]:
            print(f"  {C.DIM}  - \"{s['subject']}\" → retiring{C.RESET}")
        print()

    # ── ICP DATABASE SIZES ────────────────────────────
    icp_sizes = r.get("icp_sizes", {})
    if any(v > 0 for v in icp_sizes.values()):
        print(f"  {C.BOLD}ICP DATABASES{C.RESET}")
        print(f"  {C.DIM}{'─' * 50}{C.RESET}")
        for vname, count in icp_sizes.items():
            print(f"  {vname:<30} {count:>5} contacts")
        print()

    # ── TAM / SAM ANALYSIS ────────────────────────────
    total_tam = sum(TAM.values())
    print(f"  {C.BOLD}TAM / SAM ANALYSIS{C.RESET}")
    print(f"  {C.DIM}{'─' * 50}{C.RESET}")
    print(f"  {C.DIM}Total Addressable Market (US + target geos, 10-300 emp):{C.RESET}")
    for vertical, tam in TAM.items():
        print(f"    {vertical:<30} {tam:>8,} companies")
    print(f"    {C.BOLD}{'Total TAM':<30} {total_tam:>8,} companies{C.RESET}")
    print()
    print(f"  {C.DIM}At 20/day:          {total_tam // 20:,} days to exhaust (never will){C.RESET}")
    if reply_rate > 0:
        potential_replies = int(total_tam * reply_rate / 100)
        potential_meetings = int(total_tam * meeting_rate / 100) if meeting_rate > 0 else int(potential_replies * 0.3)
        print(f"  {C.DIM}At {reply_rate:.1f}% reply rate:  {potential_replies:,} potential replies{C.RESET}")
        print(f"  {C.DIM}At {meeting_rate:.1f}% meeting rate: {potential_meetings:,} potential meetings{C.RESET}")
        print(f"  {C.DIM}At 30% close rate:   {int(potential_meetings * 0.3):,} potential clients{C.RESET}")
        print(f"  {C.DIM}At $2K/mo ARR:       ${int(potential_meetings * 0.3 * 2000):,}/mo potential ARR{C.RESET}")
    print()

    # ── MULTI-CHANNEL INTELLIGENCE ────────────────────
    print(f"  {C.BOLD}MULTI-CHANNEL INTELLIGENCE{C.RESET}")
    print(f"  {C.DIM}{'─' * 50}{C.RESET}")
    print(f"  {C.GREEN}Email outreach: ACTIVE{C.RESET} ({total_sent} sent)")
    print()
    print(f"  {C.BOLD}READY TO ACTIVATE{C.RESET} (consent-based, legal):")
    replied_contacts = total_replies
    print(f"  {C.CYAN}  LinkedIn:{C.RESET}    Upload {replied_contacts} replied contacts →")
    print(f"  {C.DIM}               matched audiences for retargeting{C.RESET}")
    print(f"  {C.CYAN}  Google Ads:{C.RESET}  Upload replied email list →")
    print(f"  {C.DIM}               Customer Match campaign{C.RESET}")
    print(f"  {C.CYAN}  Meta Ads:{C.RESET}    Upload replied email list →")
    print(f"  {C.DIM}               1% Lookalike audience of responders{C.RESET}")
    print(f"  {C.CYAN}  TikTok Ads:{C.RESET}  Upload replied list →")
    print(f"  {C.DIM}               Custom audience retargeting{C.RESET}")
    print()
    print(f"  {C.DIM}All legal: matching people who already engaged.{C.RESET}")
    print(f"  {C.DIM}Platform ToS compliant. GDPR legitimate interest.{C.RESET}")
    print()

    # ── ACTION ITEMS ──────────────────────────────────
    print(f"  {C.BOLD}{C.YELLOW}ACTION ITEMS THIS WEEK{C.RESET}")
    print(f"  {C.DIM}{'─' * 50}{C.RESET}")

    actions = []
    if verticals:
        if worst_v and worst_v["reply_rate"] < 5 and worst_v["sent"] >= 5:
            actions.append(f"Pause {worst_v['vertical']} ({worst_v['reply_rate']:.1f}% rate)")
        if best_v and best_v["reply_rate"] > 10:
            actions.append(f"Double down on {best_v['vertical']} ({best_v['reply_rate']:.1f}% rate)")
    if replied_contacts >= 10:
        actions.append(f"Upload {replied_contacts} replied contacts to LinkedIn for matched audience")
    if replied_contacts >= 20:
        actions.append(f"Create Meta Lookalike from {replied_contacts} responders")

    if not actions:
        actions.append("Keep sending — need more data for recommendations")
        actions.append("Run aonxi-feedback in 3 days to log replies")

    for i, a in enumerate(actions, 1):
        print(f"  {C.YELLOW}  {i}. {a}{C.RESET}")
    print()

    # ── HAGI LOOP ─────────────────────────────────────
    print(f"  {C.DIM}The HAGI loop:{C.RESET}")
    print(f"  {C.DIM}  aonxi-outreach  → send emails{C.RESET}")
    print(f"  {C.DIM}  aonxi-feedback  → log replies (every 3 days){C.RESET}")
    print(f"  {C.DIM}  aonxi-report    → this dashboard (weekly){C.RESET}")
    print(f"  {C.DIM}  Every outcome teaches the next decision.{C.RESET}")
    print()


if __name__ == "__main__":
    run()
