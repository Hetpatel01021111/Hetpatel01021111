import json
import unittest
from decimal import Decimal

from scripts.startup import DATA, compact_dollars, read_valuation, valuation


class ValuationTests(unittest.TestCase):
    def setUp(self):
        self.offer = json.loads((DATA / "startup_valuation.json").read_text(encoding="utf-8"))

    def test_offer_basis_and_amounts(self):
        post, pre = valuation(self.offer)
        self.assertEqual(post.quantize(Decimal(".01")), Decimal("909090.91"))
        self.assertEqual(pre.quantize(Decimal(".01")), Decimal("709090.91"))
        self.assertEqual(compact_dollars(post), "$909K")
        self.assertEqual(read_valuation(), ("$909K", "ShipMitra", "From a $200K offer for 22% equity."))
        self.assertIs(self.offer["is_funding_raised"], False)

    def test_invalid_equity_and_changed_offer_status_fail(self):
        for equity in (0, -22, 101):
            with self.subTest(equity=equity), self.assertRaises(ValueError):
                valuation(self.offer | {"equity_percent": equity})
        with self.assertRaises(ValueError):
            valuation(self.offer | {"is_funding_raised": True})
