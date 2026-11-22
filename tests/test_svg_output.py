import os
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from xml.etree import ElementTree as ET

from scripts.fetch_contributions import load_snapshot
from scripts.render_readme_cards import activity, heatmap, render
from scripts.svg_art import ROOT


NAMESPACE = "{http://www.w3.org/2000/svg}"


class SvgTests(unittest.TestCase):
    def test_readme_embeds_all_ten_theme_adaptive_cards(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        expected = re.findall(r'(?:src|srcset)="\./(cards/[^"]+\.svg)"', readme)
        still_sources = re.findall(r'<source media="[^"]*prefers-reduced-motion[^"]*" srcset="\./(cards/[^"]+\.svg)#still"', readme)
        self.assertEqual(len(expected), 10)
        self.assertCountEqual(still_sources, expected)
        self.assertEqual(set(expected), {f"cards/{file.name}" for file in (ROOT / "cards").glob("*.svg")})
        for filename in expected:
            with self.subTest(filename=filename):
                image = ET.parse(ROOT / filename).getroot()
                self.assertEqual(image.tag, f"{NAMESPACE}svg")
                self.assertEqual(image.get("id"), "still")
                self.assertTrue(image.findtext(f"{NAMESPACE}title"))
                self.assertTrue(image.findtext(f"{NAMESPACE}desc"))
                style = image.findtext(f"{NAMESPACE}style")
                self.assertIn("data:font/woff;base64,", style)
                self.assertIn("@media (prefers-color-scheme: dark)", style)
                self.assertNotIn("script", [node.tag.removeprefix(NAMESPACE) for node in image.iter()])
                self.assertNotRegex("".join(image.itertext()), r"[–—]")

    def test_hero_shows_developer_recognition(self):
        hero = ET.parse(ROOT / "cards/hero.svg").getroot()
        recognition = hero.find(f".//{NAMESPACE}g[@id='recognition']")
        self.assertIsNotNone(recognition)
        labels = [node.text for node in recognition.iter(f"{NAMESPACE}text")]
        self.assertEqual(labels, ["VIBECON", "Top 100", "Developer", "9+", "Hackathon", "podium finishes"])
        self.assertFalse(list(hero.iter(f"{NAMESPACE}image")))

    def test_valuation_animates_dollars_and_renders_a_static_final_frame(self):
        animated = (ROOT / "cards/valuation.svg").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: no-preference", animated)
        self.assertIn(":root:target .motion { display: none }", animated)
        root = ET.fromstring(animated)
        amounts = [node.text for node in root.iter(f"{NAMESPACE}text") if node.text.startswith("$") and node.text.endswith("K")]
        self.assertEqual(amounts[0], "$909K")
        self.assertEqual(amounts[1], "$0K")
        self.assertEqual(amounts[-1], "$909K")
        self.assertEqual(len(list(root.iter(f"{NAMESPACE}set"))), 19)

        with TemporaryDirectory() as directory, patch.dict(os.environ, {"STATIC": "1"}):
            output = Path(directory)
            render(output)
            for file in output.glob("*.svg"):
                root = ET.parse(file).getroot()
                self.assertFalse(any(node.tag in [f"{NAMESPACE}set", f"{NAMESPACE}animateTransform"] for node in root.iter()))
                self.assertNotIn("@keyframes", root.findtext(f"{NAMESPACE}style"))
            display = ET.parse(output / "valuation.svg").getroot()
            labels = {node.text: float(node.get("y")) for node in display.iter(f"{NAMESPACE}text")}
            self.assertIn("VALUATION", labels)
            self.assertLess(labels["$909K"], labels["ShipMitra valued at $909K"])
            self.assertLess(labels["ShipMitra valued at $909K"], labels["From a $200K offer for 22% equity."])
            self.assertNotIn("ShipMitra", labels)

    def test_missing_data_renders_as_unavailable(self):
        for card in [heatmap(None), activity(None)]:
            root = ET.fromstring(card)
            self.assertIn("temporarily unavailable", "".join(root.itertext()))
            self.assertFalse(any(node.get("class") in ("bar", "cell") for node in root.iter()))

    def test_charts_cover_the_same_verified_dates_and_total(self):
        data = load_snapshot()
        if data is None:
            self.skipTest("Contribution snapshot unavailable")

        def counts(svg, css_class):
            root = ET.fromstring(svg)
            elements = root.findall(f".//{NAMESPACE}rect[@class='{css_class}']")
            return [int(node.findtext(f"{NAMESPACE}title").split(" · ")[1].split()[0].replace(",", ""))
                    for node in elements]

        self.assertEqual(counts(heatmap(data), "cell"), [day["count"] for day in data["days"]])
        self.assertEqual(counts(activity(data), "bar"), [month["total"] for month in data["monthly"]])
