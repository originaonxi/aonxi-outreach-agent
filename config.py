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
AIRTABLE_TABLE = "Outreach"
EXA_API_KEY = os.environ.get("EXA_API_KEY", "")
GROK_API_KEY = os.environ.get("GROK_API_KEY", "")

COMPANIES_PER_DAY = 20
MIN_INTENT_SCORE = 6

ICP = [
    {
        "name": "SaaS",
        "keywords": [
            "saas", "b2b software", "cloud software", "software as a service",
            "enterprise software", "b2b saas", "saas platform", "cloud platform",
            "subscription software", "saas startup", "devtools", "developer tools",
            "martech", "marketing technology", "sales technology", "salestech",
            "fintech software", "hr tech", "hrtech", "edtech", "healthtech",
            "proptech", "legaltech", "insurtech", "regtech", "cybersecurity software",
        ],
        "titles": ["CEO", "Founder", "VP Sales", "Head of Growth", "CRO",
                    "Co-Founder", "Chief Revenue Officer", "VP Growth",
                    "Head of Sales", "VP Business Development"],
        "pain": "scaling outbound without hiring SDRs",
        "angle": "You pay only when a qualified meeting lands on your calendar. Zero before that.",
    },
    {
        "name": "Professional Services",
        "keywords": [
            "consulting", "agency", "advisory", "law firm", "management consulting",
            "marketing agency", "digital agency", "creative agency", "staffing agency",
            "recruiting firm", "accounting firm", "cpa firm", "engineering services",
            "it consulting", "strategy consulting", "business consulting",
            "design agency", "pr agency", "advertising agency", "media agency",
            "tax advisory", "bookkeeping", "fractional cfo", "web agency",
        ],
        "titles": ["Managing Partner", "CEO", "Founder", "Director of Business Development",
                    "Partner", "Co-Founder", "Principal", "Owner",
                    "VP Sales", "Head of Growth"],
        "pain": "business development stealing time from client work",
        "angle": "Our agent runs your entire outbound. You only talk to people already interested.",
    },
    {
        "name": "E-Commerce",
        "keywords": [
            "ecommerce", "direct to consumer", "dtc", "online retail",
            "shopify", "ecommerce brand", "online store", "d2c",
            "amazon seller", "ecommerce agency", "cpg brand", "consumer brand",
            "retail brand", "wholesale", "dropshipping", "b2b ecommerce",
            "marketplace", "subscription box", "food and beverage brand",
        ],
        "titles": ["CEO", "Founder", "CMO", "VP Marketing", "Head of Growth",
                    "Co-Founder", "VP Sales", "Head of Partnerships",
                    "Director of Marketing", "Chief Growth Officer"],
        "pain": "paid CAC rising, organic pipeline nonexistent",
        "angle": "We build a B2B pipeline for your brand. Pay only for meetings that happen.",
    },
    {
        "name": "Real Estate & Finance",
        "keywords": [
            "real estate", "mortgage", "financial services", "wealth management",
            "property management", "commercial real estate", "real estate tech",
            "insurance agency", "investment management", "financial advisory",
            "private equity", "venture capital", "family office", "hedge fund",
            "fintech", "lending", "mortgage broker", "real estate brokerage",
            "asset management", "credit union",
        ],
        "titles": ["CEO", "Founder", "Managing Director", "VP Business Development",
                    "Partner", "Principal", "Co-Founder", "Head of Sales",
                    "Chief Investment Officer", "VP Growth"],
        "pain": "lead gen expensive, conversion rates too low",
        "angle": "Qualified prospects delivered to your calendar. You pay per meeting. Simple.",
    },
]
