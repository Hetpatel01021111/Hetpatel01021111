"""ShipMitra metrics used in the three profile cards."""

import json
from decimal import Decimal, ROUND_HALF_UP

from .svg_art import ROOT


DATA = ROOT / "data"


def valuation(offer):
    if (offer["currency"], offer["basis"], offer["offer_status"]) != (
        "USD", "investment_offer", "received"
    ) or offer["is_funding_raised"] is not False:
        raise ValueError("Expected a received USD investment offer with no funding raised")
    amount = Decimal(str(offer["investment_amount"]))
    equity = Decimal(str(offer["equity_percent"]))
    if not amount.is_finite() or not equity.is_finite() or amount <= 0 or not 0 < equity <= 100:
        raise ValueError("Offer amount must be positive and equity must be in (0, 100]")
    post = amount * 100 / equity
    return post, post - amount


def compact_dollars(amount):
    for scale, suffix in [(1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K"), (1, "")]:
        if amount >= scale:
            rounded = (amount / scale).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            return f"${rounded}{suffix}"
    return "$0"


def read_valuation():
    offer = json.loads((DATA / "startup_valuation.json").read_text(encoding="utf-8"))
    post, _ = valuation(offer)
    display = compact_dollars(post)
    if offer["display_value"] != display:
        raise ValueError(f"Valuation display should be {display} for the current offer")
    amount = compact_dollars(Decimal(str(offer["investment_amount"])))
    return display, offer["company"], f'From a {amount} offer for {offer["equity_percent"]}% equity.'


def brand_metrics(metrics):
    website = metrics["website_users"]
    registered = metrics["registered_product_users"]
    minimum = metrics.get("users_lower_bound")
    if any(value is not None and (type(value) is not int or value < 0)
           for value in (website, registered, minimum)):
        raise ValueError("User metrics must be non-negative integers or null")
    if registered is not None:
        return f"{registered:,}", "registered users", ("ShipMitra product registrations.",)
    if website is not None:
        return f"{website:,}", "website users", ("ShipMitra website analytics.",)
    if minimum is not None:
        display = f"{minimum // 1000}k+" if minimum >= 1000 and minimum % 1000 == 0 else f"{minimum:,}+"
        return display, "users", ("ShipMitra user growth.",)
    return "-", "users", ("ShipMitra user growth.", "Verified analytics coming soon.")


def read_metrics():
    return brand_metrics(json.loads((DATA / "startup_metrics.json").read_text(encoding="utf-8")))
