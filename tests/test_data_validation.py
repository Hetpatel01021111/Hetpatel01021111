import json
import unittest
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import URLError

from scripts.fetch_contributions import PROFILE, load_snapshot, parse_calendar, refresh, snapshot
from scripts.startup import DATA, brand_metrics


def example_days(first=date(2025, 4, 1)):
    return [{"date": (first + timedelta(days=i)).isoformat(), "count": 0} for i in range(365)]


def calendar_markup(days, total, period, start=None):
    parts = [f'<h2 id="js-contribution-activity-description">\n{total:,}\n contributions\n in {period}</h2>']
    if start:
        parts.append(f'<div data-graph-url="/contributions" data-from="{start} 00:00:00 UTC" '
                     f'data-to="{days[-1]["date"]} 23:59:59 UTC"></div>')
    for day in days:
        stamp, count = day["date"], day["count"]
        level = 4 if count else 0
        parts.append(f'<td class="ContributionCalendar-day" data-date="{stamp}" data-level="{level}" id="d{stamp}"></td>')
        parts.append(f'<tool-tip for="d{stamp}">{format(count, ",") if count else "No"} contributions on {stamp}.</tool-tip>')
    return "".join(parts)


class DataTests(unittest.TestCase):
    def test_contributions_are_reconciled_against_raw_days(self):
        current = load_snapshot()
        if current is not None:
            self.assertEqual(current["total_contributions"], sum(d["count"] for d in current["days"]))
            self.assertEqual(current["total_contributions"], sum(m["total"] for m in current["monthly"]))
            self.assertEqual(current["username"], PROFILE)

    def test_summary_preserves_current_streak_until_day_ends(self):
        days = example_days()
        for row in days[-3:-1]:
            row["count"] = 2
        days[5]["count"] = 12
        stats = snapshot(PROFILE, days)
        self.assertEqual(stats["current_streak"]["length"], 2)
        self.assertEqual(stats["longest_streak"]["length"], 2)
        self.assertEqual(stats["active_days"], 3)
        self.assertEqual(stats["best_day"], days[5])

    def test_parser_handles_real_calendar_order_without_guessing_counts(self):
        days = example_days()
        days[20]["count"] = 1234
        markup = calendar_markup(days[::-1], 1234, "the last year")
        data = parse_calendar(markup, PROFILE)
        self.assertEqual(data["total_contributions"], 1234)
        self.assertEqual(data["days"][20]["level"], 4)
        with self.assertRaisesRegex(ValueError, "do not add up"):
            parse_calendar(markup.replace("1,234", "1,235", 1), PROFILE)
        with self.assertRaises(ValueError):
            parse_calendar(markup.rsplit("<tool-tip", 1)[0], PROFILE)
        with self.assertRaises(ValueError):
            snapshot(PROFILE, days[:10] + days[11:])

    def test_recovers_the_leading_week_from_githubs_annual_calendar(self):
        visible = example_days(date(2025, 11, 23))
        visible[-1]["count"] = 1160
        annual = example_days(date(2025, 1, 1))
        next(day for day in annual if day["date"] == "2025-11-20")["count"] = 1
        archive = calendar_markup(annual, 1, "2025")
        rolling = calendar_markup(visible, 1161, "the last year", start="2025-11-16")
        requested_years = []

        def fetch_year(year):
            requested_years.append(year)
            return archive

        data = parse_calendar(rolling, PROFILE, fetch_year)
        self.assertEqual(requested_years, [2025])
        self.assertEqual(data["total_contributions"], 1161)
        self.assertEqual(data["range"]["start"], "2025-11-16")
        self.assertEqual(len(data["days"]), 372)
        self.assertEqual(data["days"][4]["count"], 1)
        with self.assertRaisesRegex(ValueError, "do not add up"):
            parse_calendar(rolling.replace("1,161", "1,162", 1), PROFILE, fetch_year)

    @patch("scripts.fetch_contributions.urlopen", side_effect=URLError("offline"))
    def test_failed_refresh_preserves_last_snapshot_or_writes_unavailable(self, _):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "contributions.json"
            refresh(PROFILE, path)
            self.assertIsNone(load_snapshot(path))
            previous = json.dumps(snapshot(PROFILE, example_days()))
            path.write_text(previous, encoding="utf-8")
            refresh(PROFILE, path)
            self.assertEqual(path.read_text(encoding="utf-8"), previous)

    def test_product_and_website_users_remain_distinct(self):
        metrics = json.loads((DATA / "startup_metrics.json").read_text(encoding="utf-8"))
        blank = {"website_users": None, "registered_product_users": None}
        self.assertEqual(brand_metrics(blank)[:2], ("-", "users"))
        self.assertEqual(brand_metrics(blank | {"website_users": 1350})[:2], ("1,350", "website users"))
        self.assertEqual(brand_metrics(blank | {"registered_product_users": 0})[:2], ("0", "registered users"))
        self.assertEqual(
            brand_metrics(blank | {"users_lower_bound": 5000}),
            ("5k+", "users", ("ShipMitra user growth.",)),
        )
        self.assertEqual(metrics["company"], "ShipMitra")
        with self.assertRaises(ValueError):
            brand_metrics(blank | {"website_users": True})
