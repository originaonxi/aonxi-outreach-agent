"""
Finds 5 new ICP companies per vertical = 20/day.
Never contacts the same domain twice (SQLite dedup).

Apollo flow (2026):
1. api_search → get person IDs (obfuscated preview)
2. bulk_match → reveal full contact details + email
"""

from __future__ import annotations
import time
import requests
from config import APOLLO_API_KEY, ICP

SEARCH_URL = "https://api.apollo.io/v1/mixed_people/api_search"
REVEAL_URL = "https://api.apollo.io/v1/people/bulk_match"


def _headers():
    return {"X-Api-Key": APOLLO_API_KEY, "Content-Type": "application/json"}


def discover(seen_domains: set) -> list[dict]:
    all_companies = []
    per_vertical = 5

    for vertical in ICP:
        print(f"  → {vertical['name']}: searching...")
        found = _search_apollo(vertical, seen_domains, per_vertical)
        all_companies.extend(found)
        print(f"    {len(found)} found")
        time.sleep(2)

    return all_companies


def _reveal_people(person_ids: list[str]) -> list[dict]:
    """Reveal full contact details, chunked into batches of 10 (Apollo limit)."""
    if not person_ids:
        return []
    all_matches = []
    for i in range(0, len(person_ids), 10):
        chunk = person_ids[i:i + 10]
        try:
            r = requests.post(
                REVEAL_URL,
                json={
                    "details": [{"id": pid} for pid in chunk],
                    "reveal_personal_emails": False,
                },
                headers=_headers(),
                timeout=30,
            )
            if r.status_code == 200:
                all_matches.extend(r.json().get("matches", []))
            time.sleep(1)
        except Exception as e:
            print(f"    Reveal error: {e}")
    return all_matches


def _search_apollo(vertical: dict, seen_domains: set, limit: int) -> list[dict]:
    results = []

    for keyword in vertical["keywords"][:2]:
        if len(results) >= limit:
            break
        try:
            # Step 1: Search for person IDs
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
                    "per_page": limit * 4,
                    "page": 1,
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

            # Step 2: Reveal full details in batch
            person_ids = [p["id"] for p in people_preview]
            revealed = _reveal_people(person_ids)

            for person in revealed:
                org = person.get("organization") or {}
                domain = org.get("primary_domain", "")
                email = person.get("email", "")

                if not domain or not email or domain in seen_domains:
                    continue

                seen_domains.add(domain)
                results.append({
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
                })

                if len(results) >= limit:
                    return results

            time.sleep(1)

        except Exception as e:
            print(f"    Apollo error: {e}")

    return results
