"""
Multi-channel decision engine.
Agent recommends. Human approves. Agent executes.

Channel logic:
- Email: always (primary)
- LinkedIn: if intent >= 8 AND linkedin_url present
- Google Ads: if 5+ replies in a vertical
- Meta Ads: if 10+ total replies (enough for lookalike)
- LinkedIn Ads: if 15+ replied contacts
"""

from __future__ import annotations
from storage.learning_db import get_performance_report


def recommend_channels() -> list[dict]:
    """Analyze current data and recommend next actions."""
    r = get_performance_report()

    total_replies = r.get("total_replies", 0)
    total_sent = r.get("total_sent", 0)
    verticals = r.get("by_vertical", [])

    best_v = max(verticals, key=lambda x: x["reply_rate"]) if verticals else None
    recommendations = []

    # LinkedIn Matched Audience
    if total_replies >= 10:
        recommendations.append({
            "channel": "LinkedIn Ads",
            "action": f"Upload {total_replies} replied contacts as matched audience",
            "cost": "$500-1000 campaign",
            "outcome": "Reach 500-2000 similar decision makers",
            "priority": "HIGH" if total_replies >= 20 else "MEDIUM",
        })

    # Google Ads Customer Match
    if best_v and best_v["reply_rate"] > 15:
        recommendations.append({
            "channel": "Google Ads",
            "action": f"Customer Match for {best_v['vertical']} ({best_v['reply_rate']:.0f}% reply rate)",
            "cost": "$300-500/mo",
            "outcome": "Retarget engaged contacts + similar profiles",
            "priority": "HIGH",
        })

    # Meta Lookalike
    if total_replies >= 20:
        recommendations.append({
            "channel": "Meta Ads",
            "action": f"1% lookalike of {total_replies} responders",
            "cost": "$200-500/mo",
            "outcome": "~500K people similar to your best prospects",
            "priority": "MEDIUM",
        })

    # TikTok retargeting
    if total_replies >= 30:
        recommendations.append({
            "channel": "TikTok Ads",
            "action": f"Custom audience from {total_replies} engaged contacts",
            "cost": "$200-300/mo",
            "outcome": "Video retargeting of engaged prospects",
            "priority": "LOW",
        })

    # Vertical-specific recommendation
    if best_v and best_v["sent"] >= 20 and best_v["reply_rate"] > 20:
        recommendations.append({
            "channel": "Double Down",
            "action": f"Increase {best_v['vertical']} to 10/day (from 5) — {best_v['reply_rate']:.0f}% reply rate",
            "cost": "+$0.10/day API cost",
            "outcome": f"~{best_v['reply_rate'] * 10 / 100:.0f} extra replies/day",
            "priority": "HIGH",
        })

    # Pause underperformers
    for v in verticals:
        if v["sent"] >= 10 and v["reply_rate"] < 3:
            recommendations.append({
                "channel": "Pause",
                "action": f"Stop {v['vertical']} — {v['reply_rate']:.1f}% reply rate after {v['sent']} emails",
                "cost": "Saves wasted sends",
                "outcome": "Focus budget on winning verticals",
                "priority": "HIGH",
            })

    return recommendations
