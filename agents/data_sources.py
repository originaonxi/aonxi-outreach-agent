"""
Waterfall data enrichment — every API adds a layer.
More APIs = better personalization = higher reply rates.
Agent uses whatever keys are available, gracefully skips missing ones.

TIER 1 (free/cheap — always run):
  Apollo, Hunter, Exa, Grok

TIER 2 (paid — run if key present):
  Clearbit, Proxycurl, Crunchbase, BuiltWith

TIER 3 (enterprise — run if key present):
  Clay, Bombora, 6sense, ZoomInfo, Demandbase

TIER 4 (ads intelligence):
  Meta Marketing API, Google Ads, LinkedIn Campaign Manager, TikTok Business
"""

from __future__ import annotations
import os

SUPPORTED_APIS = {
    # Tier 1 — free/cheap
    "apollo":       {"env": "APOLLO_API_KEY",       "tier": 1, "cost": "free tier",     "purpose": "Company discovery + contacts"},
    "hunter":       {"env": "HUNTER_API_KEY",       "tier": 1, "cost": "$49/mo",        "purpose": "Email verification + domain search"},
    "exa":          {"env": "EXA_API_KEY",          "tier": 1, "cost": "free tier",      "purpose": "Web intelligence + company search"},
    "grok":         {"env": "GROK_API_KEY",         "tier": 1, "cost": "included",       "purpose": "X/Twitter signals + contact research"},
    "anthropic":    {"env": "ANTHROPIC_API_KEY",    "tier": 1, "cost": "$0.003/call",    "purpose": "Intent scoring + email writing"},

    # Tier 2 — paid
    "clearbit":     {"env": "CLEARBIT_API_KEY",     "tier": 2, "cost": "$99/mo",        "purpose": "Company tech stack, revenue, growth stage"},
    "proxycurl":    {"env": "PROXYCURL_API_KEY",    "tier": 2, "cost": "$49/mo",        "purpose": "LinkedIn profile depth + work history"},
    "crunchbase":   {"env": "CRUNCHBASE_API_KEY",   "tier": 2, "cost": "$29/mo",        "purpose": "Funding history, investors, valuation"},
    "builtwith":    {"env": "BUILTWITH_API_KEY",    "tier": 2, "cost": "$49/mo",        "purpose": "Tech stack detection on any domain"},
    "diffbot":      {"env": "DIFFBOT_API_KEY",      "tier": 2, "cost": "$299/mo",       "purpose": "Structured web data extraction"},
    "perplexity":   {"env": "PERPLEXITY_API_KEY",   "tier": 2, "cost": "$20/mo",        "purpose": "AI-powered web research"},
    "openai":       {"env": "OPENAI_API_KEY",       "tier": 2, "cost": "$0.005/call",   "purpose": "GPT-4o fallback for writing + scoring"},

    # Tier 3 — enterprise
    "clay":         {"env": "CLAY_API_KEY",         "tier": 3, "cost": "$800/mo",       "purpose": "Waterfall enrichment orchestration"},
    "bombora":      {"env": "BOMBORA_API_KEY",      "tier": 3, "cost": "enterprise",    "purpose": "Intent data — who is researching your category"},
    "sixsense":     {"env": "SIXSENSE_API_KEY",     "tier": 3, "cost": "enterprise",    "purpose": "Account-level buying stage prediction"},
    "zoominfo":     {"env": "ZOOMINFO_API_KEY",     "tier": 3, "cost": "$15K+/yr",      "purpose": "Verified contacts + org charts"},
    "demandbase":   {"env": "DEMANDBASE_API_KEY",   "tier": 3, "cost": "enterprise",    "purpose": "Account-based marketing intelligence"},
    "lusha":        {"env": "LUSHA_API_KEY",        "tier": 3, "cost": "$29/mo",        "purpose": "Direct phone + verified email"},
    "rocketreach":  {"env": "ROCKETREACH_API_KEY",  "tier": 3, "cost": "$39/mo",        "purpose": "Email + phone lookup"},
    "cognism":      {"env": "COGNISM_API_KEY",      "tier": 3, "cost": "enterprise",    "purpose": "GDPR-compliant B2B contacts"},
    "seamless":     {"env": "SEAMLESS_API_KEY",     "tier": 3, "cost": "$65/mo",        "purpose": "Real-time contact data"},

    # Tier 4 — ads platforms
    "meta_ads":     {"env": "META_ADS_TOKEN",       "tier": 4, "cost": "ad spend",      "purpose": "Facebook/Instagram lookalike audiences"},
    "google_ads":   {"env": "GOOGLE_ADS_KEY",       "tier": 4, "cost": "ad spend",      "purpose": "Customer Match + search campaigns"},
    "linkedin_ads": {"env": "LINKEDIN_ADS_TOKEN",   "tier": 4, "cost": "ad spend",      "purpose": "Matched audiences + InMail campaigns"},
    "tiktok_ads":   {"env": "TIKTOK_ADS_TOKEN",     "tier": 4, "cost": "ad spend",      "purpose": "Custom audience retargeting"},

    # Tier 5 — delivery
    "sendgrid":     {"env": "SENDGRID_API_KEY",     "tier": 5, "cost": "$15/mo",        "purpose": "Scalable email delivery (better than Gmail SMTP)"},
    "mailgun":      {"env": "MAILGUN_API_KEY",      "tier": 5, "cost": "$35/mo",        "purpose": "Transactional email with analytics"},
    "postmark":     {"env": "POSTMARK_API_KEY",     "tier": 5, "cost": "$15/mo",        "purpose": "High deliverability transactional email"},
}


def get_available_apis() -> dict[str, dict]:
    """Returns dict of APIs with valid keys."""
    available = {}
    for name, config in SUPPORTED_APIS.items():
        key = os.environ.get(config["env"], "")
        if key:
            available[name] = config
    return available


def get_api_status() -> str:
    """Pretty-print which APIs are connected."""
    available = get_available_apis()
    lines = []
    for tier in range(1, 6):
        tier_apis = {k: v for k, v in SUPPORTED_APIS.items() if v["tier"] == tier}
        tier_names = {1: "CORE", 2: "PAID", 3: "ENTERPRISE", 4: "ADS", 5: "DELIVERY"}
        if tier_apis:
            connected = [k for k in tier_apis if k in available]
            disconnected = [k for k in tier_apis if k not in available]
            if connected:
                lines.append(f"  {tier_names.get(tier, '?')}: {', '.join(connected)}")
            if disconnected:
                lines.append(f"  {tier_names.get(tier, '?')} (add): {', '.join(disconnected)}")
    return "\n".join(lines)
