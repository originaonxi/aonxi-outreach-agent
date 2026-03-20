"""
Finds new ICP companies per vertical.
Never contacts the same domain twice (SQLite dedup).
Randomizes keywords + pages so every run finds different companies.

Apollo flow:
1. api_search → get person IDs + preview
2. people/match → reveal full contact + email
   If rate-limited: fallback to Hunter domain-search by company name
"""

from __future__ import annotations
import random
import time
import requests
from config import APOLLO_API_KEY, HUNTER_API_KEY, ICP

SEARCH_URL = "https://api.apollo.io/v1/mixed_people/api_search"
MATCH_URL = "https://api.apollo.io/v1/people/match"

_rate_limited = False
_hunter_limited = False


def _headers():
    return {"X-Api-Key": APOLLO_API_KEY, "Content-Type": "application/json"}


def discover(seen_domains: set, per_vertical: int = 5) -> list[dict]:
    global _rate_limited, _hunter_limited
    _rate_limited = False
    _hunter_limited = False
    all_companies = []

    verticals = list(ICP)
    random.shuffle(verticals)

    for vertical in verticals:
        # If both APIs are rate-limited, stop trying
        if _rate_limited and _hunter_limited:
            print(f"  → Both Apollo + Hunter rate-limited. Try again in ~1 hour.")
            break

        print(f"  → {vertical['name']}: searching...")
        found = _search_apollo(vertical, seen_domains, per_vertical)
        all_companies.extend(found)
        print(f"    {len(found)} found")
        time.sleep(1)

    return all_companies


def _reveal_person(person_id: str) -> dict | None:
    """Reveal via Apollo people/match."""
    global _rate_limited
    if _rate_limited:
        return None

    try:
        r = requests.post(
            MATCH_URL,
            json={"id": person_id, "reveal_personal_emails": False},
            headers=_headers(),
            timeout=15,
        )
        if r.status_code == 200:
            return r.json().get("person")
        elif r.status_code == 429:
            _rate_limited = True
            print(f"    Apollo reveal rate-limited. Using Hunter fallback.")
            return None
    except Exception as e:
        print(f"    Reveal error: {e}")
    return None


def _hunter_domain_search(company_name: str) -> list[dict]:
    """Use Hunter.io to find emails at a company by domain search."""
    global _hunter_limited
    if not HUNTER_API_KEY or _hunter_limited:
        return []
    try:
        r = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={
                "company": company_name,
                "api_key": HUNTER_API_KEY,
                "limit": 5,
                "type": "personal",
                "seniority": "senior,executive",
            },
            timeout=15,
        )
        if r.status_code == 429:
            _hunter_limited = True
            print(f"    Hunter rate-limited.")
            return []
        if r.status_code == 200:
            data = r.json().get("data", {})
            domain = data.get("domain", "")
            emails = data.get("emails", [])
            results = []
            for e in emails:
                if e.get("value") and e.get("confidence", 0) > 50:
                    results.append({
                        "email": e["value"],
                        "first_name": e.get("first_name", ""),
                        "last_name": e.get("last_name", ""),
                        "position": e.get("position", ""),
                        "seniority": e.get("seniority", ""),
                        "domain": domain,
                        "confidence": e.get("confidence", 0),
                    })
            return results
    except Exception:
        pass
    return []


def _build_from_hunter(hunter_result: dict, company_name: str, vertical: dict) -> dict:
    """Build a company dict from Hunter domain search result."""
    return {
        "name": f"{hunter_result.get('first_name', '')} {hunter_result.get('last_name', '')}".strip(),
        "title": hunter_result.get("position", ""),
        "email": hunter_result["email"],
        "company": company_name,
        "domain": hunter_result.get("domain", ""),
        "employees": 0,
        "industry": "",
        "location": "",
        "linkedin": "",
        "vertical": vertical["name"],
        "pain": vertical["pain"],
        "angle": vertical["angle"],
        "founded_year": None,
        "short_description": "",
        "annual_revenue": "",
        "technologies": [],
        "seniority": hunter_result.get("seniority", ""),
        "headline": "",
        "email_confidence": hunter_result.get("confidence", 70),
    }


def _extract_from_revealed(person: dict, vertical: dict) -> dict | None:
    """Extract company data from a fully revealed person."""
    org = person.get("organization") or {}
    domain = org.get("primary_domain", "")
    email = person.get("email", "")

    if not domain or not email:
        return None

    return {
        "name": f"{person.get('first_name','')} {person.get('last_name','')}".strip(),
        "title": person.get("title", ""),
        "email": email,
        "company": org.get("name", ""),
        "domain": domain,
        "employees": org.get("estimated_num_employees", 0) or org.get("num_employees", 0),
        "industry": org.get("industry", ""),
        "location": f"{person.get('city','')}, {person.get('country','')}",
        "linkedin": person.get("linkedin_url", ""),
        "vertical": vertical["name"],
        "pain": vertical["pain"],
        "angle": vertical["angle"],
        "founded_year": org.get("founded_year"),
        "short_description": org.get("short_description", ""),
        "annual_revenue": org.get("annual_revenue_printed", ""),
        "technologies": org.get("technology_names", [])[:5],
        "seniority": person.get("seniority", ""),
        "headline": person.get("headline", ""),
    }


def _search_apollo(vertical: dict, seen_domains: set, limit: int) -> list[dict]:
    results = []

    keywords = list(vertical["keywords"])
    random.shuffle(keywords)
    keywords_to_try = keywords[:5]

    for keyword in keywords_to_try:
        if len(results) >= limit:
            break
        if _rate_limited and _hunter_limited:
            break

        page = random.randint(1, 5)

        try:
            r = requests.post(
                SEARCH_URL,
                json={
                    "q_organization_keyword_tags": [keyword],
                    "person_titles": vertical["titles"],
                    "organization_num_employees_ranges": ["10,300"],
                    "person_locations": [
                        "United States", "Canada", "United Kingdom",
                        "Australia", "India", "United Arab Emirates"
                    ],
                    "per_page": 25,
                    "page": page,
                },
                headers=_headers(),
                timeout=20,
            )

            if r.status_code != 200:
                print(f"    Search error: {r.status_code}")
                continue

            people_preview = r.json().get("people", [])
            if not people_preview:
                continue

            random.shuffle(people_preview)

            for preview in people_preview:
                if len(results) >= limit:
                    break

                # Try Apollo reveal first
                company = None
                if not _rate_limited:
                    person = _reveal_person(preview["id"])
                    if person:
                        company = _extract_from_revealed(person, vertical)
                        time.sleep(0.5)

                # Fallback: use Hunter to find email by company name
                if not company and _rate_limited:
                    org_name = (preview.get("organization") or {}).get("name", "")
                    if org_name:
                        hunter_results = _hunter_domain_search(org_name)
                        for hr in hunter_results:
                            if hr["domain"] not in seen_domains:
                                company = _build_from_hunter(hr, org_name, vertical)
                                break
                        time.sleep(0.5)

                if company and company["email"] and company["domain"] not in seen_domains:
                    seen_domains.add(company["domain"])
                    results.append(company)

            time.sleep(1)

        except Exception as e:
            print(f"    Apollo error: {e}")

    return results
