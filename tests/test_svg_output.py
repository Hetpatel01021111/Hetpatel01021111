import os
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from xml.etree import ElementTree as ET

from scripts.make_ascii_svg import NAMESPACE, PORTRAIT, read_rows, sample_rows
from scripts.prep_photo import PREPPED, SOURCE, prepare
from scripts.render_readme_cards import activity, heatmap, render
from scripts.svg_art import ROOT


class SvgTests(unittest.TestCase):
    def test_readme_embeds_all_eleven_valid_cards(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        expected = re.findall(r'(?:src|srcset)="\./(cards/[^"]+\.svg)"', readme)
        self.assertEqual(len(expected), 11)
        self.assertEqual(set(expected), {f"cards/{file.name}" for file in (ROOT / "cards").glob("*.svg")})
        for filename in expected:
            with self.subTest(filename=filename):
                image = ET.parse(ROOT / filename).getroot()
                self.assertEqual(image.tag, f"{NAMESPACE}svg")
                self.assertTrue(image.findtext(f"{NAMESPACE}title"))
                self.assertTrue(image.findtext(f"{NAMESPACE}desc"))
                self.assertIn("data:font/woff;base64,", image.findtext(f"{NAMESPACE}style"))
                self.assertNotIn("script", [node.tag.removeprefix(NAMESPACE) for node in image.iter()])

    def test_hero_rows_match_the_reproducible_jpeg_transformation(self):
        with TemporaryDirectory() as directory:
            regenerated = Path(directory) / PREPPED.name
            prepare(SOURCE, regenerated)
            rows = sample_rows(regenerated)
        self.assertEqual(rows, read_rows(PORTRAIT))
        portrait = ET.parse(ROOT / "cards/hero.svg").getroot()
        hero_rows = [node.text for node in portrait.iter(f"{NAMESPACE}text") if node.get("class") == "portrait-row"]
        self.assertEqual(len(hero_rows), 96)
        self.assertTrue(all(len(row) == 180 for row in hero_rows))
        self.assertEqual(rows, hero_rows)

    def test_valuation_animates_dollars_and_renders_a_static_final_frame(self):
        animated = (ROOT / "cards/valuation.svg").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: no-preference", animated)
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
            display = (output / "valuation.svg").read_text(encoding="utf-8")
            self.assertIn("$909K", display)
            self.assertIn("post-money", display)
            self.assertIn("$200K offered for 22% equity.", display)
            self.assertIn("Offer-implied valuation.", display)

    def test_missing_data_renders_as_unavailable(self):
        for card in [heatmap(None), activity(None)]:
            root = ET.fromstring(card)
            self.assertIn("temporarily unavailable", "".join(root.itertext()))
            self.assertFalse(any(node.get("class") in ("bar", "cell") for node in root.iter()))
