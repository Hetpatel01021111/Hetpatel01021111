import os
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from xml.etree import ElementTree as ET

from scripts.render_readme_cards import activity, heatmap, render
from scripts.svg_art import ROOT


NAMESPACE = "{http://www.w3.org/2000/svg}"


class SvgTests(unittest.TestCase):
    def test_readme_embeds_all_eleven_valid_cards(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        expected = re.findall(r'(?:src|srcset)="\./(cards/[^"]+\.svg)"', readme)
        still_sources = re.findall(r'<source media="[^"]*prefers-reduced-motion[^"]*" srcset="\./(cards/[^"]+\.svg)#still"', readme)
        self.assertEqual(len(expected), 11)
        self.assertCountEqual(still_sources, expected)
        self.assertEqual(set(expected), {f"cards/{file.name}" for file in (ROOT / "cards").glob("*.svg")})
        for filename in expected:
            with self.subTest(filename=filename):
                image = ET.parse(ROOT / filename).getroot()
                self.assertEqual(image.tag, f"{NAMESPACE}svg")
                self.assertEqual(image.get("id"), "still")
                self.assertTrue(image.findtext(f"{NAMESPACE}title"))
                self.assertTrue(image.findtext(f"{NAMESPACE}desc"))
                self.assertIn("data:font/woff;base64,", image.findtext(f"{NAMESPACE}style"))
                self.assertNotIn("script", [node.tag.removeprefix(NAMESPACE) for node in image.iter()])
                self.assertNotRegex("".join(image.itertext()), r"[–—]")

    def test_hero_uses_a_vector_shipping_route(self):
        hero = ET.parse(ROOT / "cards/hero.svg").getroot()
        route = hero.find(f".//{NAMESPACE}g[@id='shipping-route']")
        self.assertIsNotNone(route)
        self.assertTrue(list(route.iter(f"{NAMESPACE}path")))
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
            self.assertLess(labels["$909K"], labels["ShipMitra"])
            self.assertIn("From a $200K offer for 22% equity.", labels)

    def test_missing_data_renders_as_unavailable(self):
        for card in [heatmap(None), activity(None)]:
            root = ET.fromstring(card)
            self.assertIn("temporarily unavailable", "".join(root.itertext()))
            self.assertFalse(any(node.get("class") in ("bar", "cell") for node in root.iter()))
