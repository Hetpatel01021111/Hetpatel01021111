"""Refresh a snapshot from the public calendar on the specified GitHub profile."""

import json
import os
import re
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
PROFILE = "Hetpatel01021111"
SNAPSHOT = ROOT / "data/contributions.json"
DAY = timedelta(days=1)
COUNT = re.compile(r"(No|[1-9]\d{0,2}(?:,\d{3})+|\d+) contributions? on .+", re.I)
TOTAL = re.compile(r"([\d,]+)\s+contributions?\s+in the last year", re.I)


def snapshot(username, days):
    """Validate the rolling calendar before calculating any derived figures."""
    dates = [date.fromisoformat(day["date"]) for day in days]
    if not 365 <= len(dates) <= 372 or any(
        second - first != DAY for first, second in zip(dates, dates[1:])
    ):
        raise ValueError("Expected a continuous year of contribution days")
    if any(type(day["count"]) is not int or day["count"] < 0 for day in days):
        raise ValueError("Contribution counts must be non-negative integers")
    for day in days:
        if "level" in day:
            level = day["level"]
            if type(level) is not int or level not in range(5) or (level == 0) != (day["count"] == 0):
                raise ValueError(f'Invalid contribution level for {day["date"]}')

    monthly = Counter()
    streaks = []
    run = []
    for day in days:
        count, stamp = day["count"], day["date"]
        monthly[stamp[:7]] += count
        if count:
            run.append(stamp)
        elif run:
            streaks.append({"length": len(run), "start": run[0], "end": run[-1]})
            run = []
    if run:
        streaks.append({"length": len(run), "start": run[0], "end": run[-1]})

    empty = {"length": 0, "start": None, "end": None}
    latest_active = (dates[-1] if days[-1]["count"] else dates[-2]).isoformat()
    current = streaks[-1] if streaks and streaks[-1]["end"] == latest_active else empty
    best = max(days, key=lambda day: day["count"])
    return {
        "username": username,
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": sum(monthly.values()),
        "active_days": sum(day["count"] > 0 for day in days),
        "current_streak": current,
        "longest_streak": max(streaks, key=lambda streak: streak["length"], default=empty),
        "best_day": {"date": best["date"] if best["count"] else None, "count": best["count"]},
        "monthly": [{"month": month, "total": total} for month, total in monthly.items()],
        "days": days,
    }


def parse_calendar(markup, username):
    page = BeautifulSoup(markup, "html.parser")
    heading = page.select_one("#js-contribution-activity-description")
    total_match = TOTAL.fullmatch(heading.get_text(" ", strip=True)) if heading else None
    if total_match is None:
        raise ValueError("GitHub did not return a yearly contribution total")
    tooltips = {tip["for"]: tip.get_text(" ", strip=True) for tip in page.select("tool-tip[for]")}
    days = []
    for cell in page.select("td.ContributionCalendar-day[data-date]"):
        stamp = cell["data-date"]
        match = COUNT.fullmatch(tooltips.get(cell.get("id"), ""))
        if match is None:
            raise ValueError(f"Missing or unreadable contribution count for {stamp}")
        number = match[1]
        level = cell.get("data-level", "")
        if level not in ("0", "1", "2", "3", "4"):
            raise ValueError(f"Missing or unreadable contribution level for {stamp}")
        days.append({
            "date": stamp,
            "count": 0 if number.lower() == "no" else int(number.replace(",", "")),
            "level": int(level),
        })
    data = snapshot(username, sorted(days, key=lambda day: day["date"]))
    if data["total_contributions"] != int(total_match[1].replace(",", "")):
        raise ValueError("Daily counts do not add up to GitHub's yearly total")
    return data


def load_snapshot(path=SNAPSHOT, username=PROFILE):
    data = json.loads(path.read_text(encoding="utf-8"))
    if data == {"username": username, "status": "unavailable"}:
        return None
    if data != snapshot(username, data["days"]):
        raise ValueError(f"Contribution snapshot does not match the calendar for {username}")
    return data


def refresh(username, path=SNAPSHOT):
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", username):
        raise ValueError("Invalid GitHub username")
    request = Request(
        f"https://github.com/users/{username}/contributions",
        headers={
            "User-Agent": "Public profile calendar refresh",
            "Accept-Language": "en-US",
            "Cache-Control": "no-cache",
        },
    )
    try:
        try:
            previous = load_snapshot(path, username)
        except (OSError, ValueError, KeyError, TypeError):
            previous = None
        with urlopen(request, timeout=30) as response:
            data = parse_calendar(response.read(), username)
        if previous and data["range"]["end"] < previous["range"]["end"]:
            raise ValueError("GitHub served an older contribution calendar")
    except (OSError, ValueError) as error:
        print(f"::warning::GitHub calendar refresh failed ({error})")
        if previous:
            print(f"Keeping the last verified calendar through {previous['range']['end']}")
            return
        data = {"username": username, "status": "unavailable"}

    contents = json.dumps(data, indent=2) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != contents:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(contents, encoding="utf-8")
        temporary.replace(path)
    if "range" in data:
        print(f"{data['total_contributions']:,} GitHub contributions through {data['range']['end']}")


if __name__ == "__main__":
    refresh(os.environ.get("GH_PROFILE_USER", PROFILE))
