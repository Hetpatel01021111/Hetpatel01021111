import json
import unittest
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import URLError

from scripts.fetch_contributions import PROFILE, load_snapshot, parse_calendar, refresh, snapshot
from scripts.startup import DATA, brand_metrics


def example_days():
    first = date(2025, 4, 1)
    return [{"date": (first + timedelta(days=i)).isoformat(), "count": 0} for i in range(365)]


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
        markup = ['<h2 id="js-contribution-activity-description">\n1,234\n contributions\n in the last year</h2>']
        for i, day in reversed(list(enumerate(days))):
            count = "1,234" if i == 20 else "No"
            level = 4 if i == 20 else 0
            markup.append(
                f'<td class="ContributionCalendar-day" data-date="{day["date"]}" data-level="{level}" id="d{i}"></td>'
            )
            markup.append(f'<tool-tip for="d{i}">{count} contributions on April 21st.</tool-tip>')
        data = parse_calendar("".join(markup), PROFILE)
        self.assertEqual(data["total_contributions"], 1234)
        self.assertEqual(data["days"][20]["level"], 4)
        with self.assertRaisesRegex(ValueError, "do not add up"):
            parse_calendar("".join(markup).replace("1,234", "1,235", 1), PROFILE)
        with self.assertRaises(ValueError):
            parse_calendar("".join(markup[:-1]), PROFILE)
        with self.assertRaises(ValueError):
            snapshot(PROFILE, days[:10] + days[11:])

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
        self.assertEqual(metrics["company"], "ShipMitra")
        with self.assertRaises(ValueError):
            brand_metrics(blank | {"website_users": True})
