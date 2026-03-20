import os
from dotenv import load_dotenv
load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER", "lifeislovesam@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "appJQFHuYU3NxZA8A")
AIRTABLE_TABLE = "Aonxi_Outreach"

COMPANIES_PER_DAY = 20
MIN_INTENT_SCORE = 6

ICP = [
    {
        "name": "SaaS",
        "keywords": ["saas", "b2b software", "cloud software"],
        "titles": ["CEO", "Founder", "VP Sales", "Head of Growth", "CRO"],
        "pain": "scaling outbound without hiring SDRs",
        "angle": "You pay only when a qualified meeting lands on your calendar. Zero before that.",
    },
    {
        "name": "Professional Services",
        "keywords": ["consulting", "agency", "advisory", "law firm"],
        "titles": ["Managing Partner", "CEO", "Founder", "Director of Business Development"],
        "pain": "business development stealing time from client work",
        "angle": "Our agent runs your entire outbound. You only talk to people already interested.",
    },
    {
        "name": "E-Commerce",
        "keywords": ["ecommerce", "direct to consumer", "dtc", "online retail"],
        "titles": ["CEO", "Founder", "CMO", "VP Marketing", "Head of Growth"],
        "pain": "paid CAC rising, organic pipeline nonexistent",
        "angle": "We build a B2B pipeline for your brand. Pay only for meetings that happen.",
    },
    {
        "name": "Real Estate & Finance",
        "keywords": ["real estate", "mortgage", "financial services", "wealth management"],
        "titles": ["CEO", "Founder", "Managing Director", "VP Business Development"],
        "pain": "lead gen expensive, conversion rates too low",
        "angle": "Qualified prospects delivered to your calendar. You pay per meeting. Simple.",
    },
]
