"""
Seed the database with test data to demonstrate the learning engine.
Simulates 30 days of outreach across all 4 verticals.

RUN: python3 test_data.py
"""

from __future__ import annotations
import sqlite3
import random
from datetime import date, timedelta
from storage.db import DB_PATH, init

# Simulated companies per vertical
TEST_DATA = {
    "SaaS": {
        "companies": [
            ("Alex Chen", "CEO", "alex@cloudmetrics.io", "CloudMetrics", "cloudmetrics.io", 45, "Software"),
            ("Maria Santos", "VP Sales", "maria@pipelineai.com", "PipelineAI", "pipelineai.com", 28, "Software"),
            ("James Wilson", "Founder", "james@deploystack.com", "DeployStack", "deploystack.com", 15, "Software"),
            ("Sarah Kim", "Head of Growth", "sarah@revscale.io", "RevScale", "revscale.io", 62, "Software"),
            ("David Park", "CRO", "david@salesloop.com", "SalesLoop", "salesloop.com", 38, "Software"),
            ("Lisa Thompson", "CEO", "lisa@datapulse.io", "DataPulse", "datapulse.io", 22, "Software"),
            ("Mike Johnson", "Founder", "mike@apiforge.dev", "APIForge", "apiforge.dev", 11, "Software"),
            ("Emma Davis", "VP Sales", "emma@growthkit.io", "GrowthKit", "growthkit.io", 55, "Software"),
            ("Ryan O'Brien", "CEO", "ryan@stackflow.com", "StackFlow", "stackflow.com", 78, "Software"),
            ("Nina Patel", "Head of Growth", "nina@segmently.io", "Segmently", "segmently.io", 33, "Software"),
        ],
        "reply_rate": 0.22,
        "meeting_rate": 0.08,
    },
    "Professional Services": {
        "companies": [
            ("Robert Miller", "Managing Partner", "robert@mckinley-advisors.com", "McKinley Advisors", "mckinley-advisors.com", 35, "Consulting"),
            ("Jennifer Lee", "CEO", "jennifer@crescentconsulting.com", "Crescent Consulting", "crescentconsulting.com", 18, "Consulting"),
            ("Tom Harris", "Founder", "tom@elevateagency.co", "Elevate Agency", "elevateagency.co", 25, "Agency"),
            ("Amanda Brooks", "Director BD", "amanda@stratton-group.com", "Stratton Group", "stratton-group.com", 42, "Advisory"),
            ("Chris Reynolds", "CEO", "chris@apex-legal.com", "Apex Legal", "apex-legal.com", 30, "Legal"),
            ("Diana Cruz", "Managing Partner", "diana@vectoradvisors.com", "Vector Advisors", "vectoradvisors.com", 20, "Consulting"),
            ("Kevin Wright", "Founder", "kevin@brightpath.agency", "BrightPath", "brightpath.agency", 14, "Agency"),
            ("Laura Martinez", "CEO", "laura@peaklegal.com", "Peak Legal", "peaklegal.com", 50, "Legal"),
        ],
        "reply_rate": 0.18,
        "meeting_rate": 0.06,
    },
    "E-Commerce": {
        "companies": [
            ("Sophie Turner", "CEO", "sophie@nativgoods.com", "NativGoods", "nativgoods.com", 40, "E-Commerce"),
            ("Mark Zhang", "CMO", "mark@urbanthread.co", "UrbanThread", "urbanthread.co", 65, "Fashion"),
            ("Rachel Green", "Founder", "rachel@pureleaf.shop", "PureLeaf", "pureleaf.shop", 22, "Health"),
            ("Jake Sullivan", "VP Marketing", "jake@peakperform.co", "PeakPerform", "peakperform.co", 48, "Fitness"),
            ("Olivia Brown", "Head of Growth", "olivia@bloombox.com", "BloomBox", "bloombox.com", 30, "Lifestyle"),
            ("Tyler Adams", "CEO", "tyler@voltgear.com", "VoltGear", "voltgear.com", 55, "Electronics"),
        ],
        "reply_rate": 0.15,
        "meeting_rate": 0.05,
    },
    "Real Estate & Finance": {
        "companies": [
            ("Michael Ross", "CEO", "michael@primeequity.com", "Prime Equity", "primeequity.com", 35, "Real Estate"),
            ("Karen White", "Managing Director", "karen@summitwealth.com", "Summit Wealth", "summitwealth.com", 28, "Finance"),
            ("Brian Taylor", "Founder", "brian@keystoneproperties.com", "Keystone Properties", "keystoneproperties.com", 42, "Real Estate"),
            ("Samantha Lee", "VP BD", "samantha@atlascapital.com", "Atlas Capital", "atlascapital.com", 60, "Finance"),
            ("Greg Foster", "CEO", "greg@harborrealty.com", "Harbor Realty", "harborrealty.com", 20, "Real Estate"),
            ("Angela Wong", "Founder", "angela@meridianfinance.com", "Meridian Finance", "meridianfinance.com", 15, "Finance"),
        ],
        "reply_rate": 0.12,
        "meeting_rate": 0.04,
    },
}

SUBJECTS = [
    "Quick question about {company}",
    "{company}'s outbound pipeline",
    "Meetings on autopilot for {company}",
    "Scaling without SDR hires",
    "One question about growth at {company}",
    "Pay-per-meeting for {vertical} companies",
    "{first_name}, worth 15 minutes?",
]

BODIES = [
    "Hi {first_name},\n\n{company} is at that stage where outbound needs to scale but hiring SDRs costs $60K+ each.\n\nWe deliver qualified meetings to your calendar — you pay only when one lands.\n\n30+ clients. Pay per outcome. Non-competing per market.\n\nWorth a 15-min call this week?\n\nSam | origin@aonxi.com | aonxi.today",
    "Hi {first_name},\n\nRunning a {employees}-person {vertical} company means your time is split between client work and finding the next client.\n\nWhat if qualified meetings just appeared on your calendar? That's what we do. You pay per meeting. Nothing upfront.\n\n30+ companies trust us. Non-competing per geography.\n\nRelevant?\n\nSam | origin@aonxi.com | aonxi.today",
    "Hi {first_name},\n\nMost {vertical} founders I talk to say the same thing: great at delivery, hate business development.\n\nWe built an AI agent that runs your entire outbound. Qualified meetings land on your calendar. You pay only when one happens.\n\n30+ clients. Zero until a meeting books.\n\nOpen to hearing how it works?\n\nSam | origin@aonxi.com | aonxi.today",
]


def seed():
    init()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create analytics tables
    c.execute("""CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, metric TEXT, vertical TEXT, value REAL, metadata TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS daily_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE, discovered INTEGER DEFAULT 0,
        qualified INTEGER DEFAULT 0, sent INTEGER DEFAULT 0,
        replied INTEGER DEFAULT 0, meetings INTEGER DEFAULT 0,
        avg_intent REAL DEFAULT 0, api_cost_usd REAL DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ab_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT, variant TEXT, subject_a TEXT, subject_b TEXT,
        chosen TEXT, got_reply INTEGER DEFAULT 0, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS learnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, type TEXT, insight TEXT, confidence REAL, applied INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS winning_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_type TEXT, pattern TEXT, win_rate REAL, sample_size INTEGER,
        vertical TEXT, last_updated TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS sequences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT, step INTEGER DEFAULT 1, max_steps INTEGER DEFAULT 3,
        next_send_date TEXT, status TEXT DEFAULT 'active',
        email_1_subject TEXT, email_1_body TEXT,
        email_2_body TEXT, email_3_body TEXT,
        created_at TEXT, completed_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS linkedin_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, company TEXT, title TEXT, linkedin_url TEXT,
        message TEXT, status TEXT DEFAULT 'pending',
        created_at TEXT, sent_at TEXT
    )""")

    total_inserted = 0
    total_sent = 0
    total_replied = 0
    total_meetings = 0

    for vertical_name, vdata in TEST_DATA.items():
        for person in vdata["companies"]:
            name, title, email, company, domain, employees, industry = person
            first_name = name.split()[0]

            # Random date in last 30 days
            days_ago = random.randint(1, 30)
            added = (date.today() - timedelta(days=days_ago)).isoformat()

            intent = random.randint(5, 10)
            subject = random.choice(SUBJECTS).format(
                company=company, vertical=vertical_name, first_name=first_name)
            body = random.choice(BODIES).format(
                first_name=first_name, company=company,
                employees=employees, vertical=vertical_name)

            # Determine outcomes
            sent = 1 if intent >= 6 else 0
            sent_date = added if sent else None
            got_reply = 1 if sent and random.random() < vdata["reply_rate"] else 0
            meeting = 1 if got_reply and random.random() < (vdata["meeting_rate"] / vdata["reply_rate"]) else 0

            try:
                c.execute("""INSERT OR IGNORE INTO prospects
                    (email, domain, company, name, title, vertical,
                     intent_score, email_subject, email_body,
                     sent, date_added, date_sent, got_reply, meeting_booked)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (email, domain, company, name, title, vertical_name,
                     intent, subject, body,
                     sent, added, sent_date, got_reply, meeting))
                total_inserted += 1
                total_sent += sent
                total_replied += got_reply
                total_meetings += meeting
            except Exception:
                pass

            # Daily stats
            if sent:
                try:
                    c.execute("""INSERT OR IGNORE INTO daily_stats (date, discovered, qualified, sent, replied, meetings, avg_intent, api_cost_usd)
                        VALUES (?,0,0,0,0,0,0,0)""", (added,))
                    c.execute("""UPDATE daily_stats SET
                        discovered=discovered+1, qualified=qualified+1,
                        sent=sent+?, replied=replied+?, meetings=meetings+?,
                        avg_intent=?, api_cost_usd=api_cost_usd+0.011
                        WHERE date=?""",
                        (sent, got_reply, meeting, intent, added))
                except Exception:
                    pass

    conn.commit()
    conn.close()

    reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
    meeting_rate = (total_meetings / total_sent * 100) if total_sent > 0 else 0

    print()
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  TEST DATA SEEDED")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Prospects inserted: {total_inserted}")
    print(f"  Emails sent:        {total_sent}")
    print(f"  Replies:            {total_replied} ({reply_rate:.1f}%)")
    print(f"  Meetings booked:    {total_meetings} ({meeting_rate:.1f}%)")
    print()
    print("  BY VERTICAL:")
    for v in TEST_DATA:
        count = len(TEST_DATA[v]["companies"])
        print(f"    {v}: {count} prospects (expected {TEST_DATA[v]['reply_rate']*100:.0f}% reply)")
    print()
    print("  Run `python3 agent.py --dashboard` to see analytics")
    print("  Run `python3 agent.py --report` to see weekly report")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()


if __name__ == "__main__":
    seed()
