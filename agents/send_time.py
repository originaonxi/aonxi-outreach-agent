"""
Send time optimization.
Best cold email times: Tue-Thu, 8:30-10:00am in the prospect's timezone.
"""

from __future__ import annotations
from datetime import datetime, timedelta
import pytz

TIMEZONE_MAP = {
    "united states": "America/New_York",
    "usa": "America/New_York",
    "new york": "America/New_York",
    "boston": "America/New_York",
    "miami": "America/New_York",
    "atlanta": "America/New_York",
    "chicago": "America/Chicago",
    "dallas": "America/Chicago",
    "houston": "America/Chicago",
    "austin": "America/Chicago",
    "denver": "America/Denver",
    "california": "America/Los_Angeles",
    "san francisco": "America/Los_Angeles",
    "los angeles": "America/Los_Angeles",
    "seattle": "America/Los_Angeles",
    "portland": "America/Los_Angeles",
    "canada": "America/Toronto",
    "toronto": "America/Toronto",
    "vancouver": "America/Vancouver",
    "united kingdom": "Europe/London",
    "london": "Europe/London",
    "uk": "Europe/London",
    "india": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "bangalore": "Asia/Kolkata",
    "australia": "Australia/Sydney",
    "sydney": "Australia/Sydney",
    "melbourne": "Australia/Sydney",
    "united arab emirates": "Asia/Dubai",
    "uae": "Asia/Dubai",
    "dubai": "Asia/Dubai",
    "abu dhabi": "Asia/Dubai",
}


def _get_timezone(location: str) -> str:
    """Map a location string to a timezone."""
    loc = location.lower()
    for key, tz in TIMEZONE_MAP.items():
        if key in loc:
            return tz
    return "America/New_York"  # default


def is_optimal_send_time(location: str) -> bool:
    """Check if now is a good time to send to this location."""
    tz_str = _get_timezone(location)
    tz = pytz.timezone(tz_str)
    now = datetime.now(tz)

    # Tue=1, Wed=2, Thu=3 are best; Mon=0, Fri=4 are ok
    good_day = now.weekday() in [0, 1, 2, 3, 4]  # weekdays
    good_hour = 8 <= now.hour <= 11  # 8am-11am their time

    return good_day and good_hour


def get_send_window(location: str) -> str:
    """Get a human-readable description of the next optimal send window."""
    tz_str = _get_timezone(location)
    tz = pytz.timezone(tz_str)
    now = datetime.now(tz)

    # Find next Tue-Thu 9am
    target_hour = 9
    days_ahead = 0

    for i in range(7):
        check = now + timedelta(days=i)
        if check.weekday() in [1, 2, 3]:  # Tue, Wed, Thu
            if i == 0 and check.hour < target_hour:
                days_ahead = 0
                break
            elif i > 0:
                days_ahead = i
                break

    next_send = (now + timedelta(days=days_ahead)).replace(
        hour=target_hour, minute=0, second=0)

    day_name = next_send.strftime("%A")
    time_str = next_send.strftime("%-I:%M %p")
    tz_abbr = next_send.strftime("%Z")

    return f"{day_name} {time_str} {tz_abbr}"


def get_send_status(location: str) -> tuple[bool, str]:
    """Returns (is_optimal, description)."""
    optimal = is_optimal_send_time(location)
    if optimal:
        tz_str = _get_timezone(location)
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        return True, f"NOW ({now.strftime('%-I:%M %p %Z')})"
    else:
        window = get_send_window(location)
        return False, f"Best: {window}"
