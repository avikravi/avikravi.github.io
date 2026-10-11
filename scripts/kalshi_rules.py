"""Kalshi's own rounding rules, modeled explicitly.

This is the ONLY module allowed to round (tests/test_kalshi_lint.py enforces
it). Everything else in the pipeline is exact Decimal arithmetic.

Source: https://docs.kalshi.com/getting_started/fee_rounding (2026).
  - Non-direct (retail) member balances are kept to $0.01; direct members to
    $0.0001 (DOCUMENTED_PRECISIONS). Which one applies is not assumed: the
    fetch reconciles under each and uses the one that matches Kalshi's cash
    exactly (see kalshi_fetch.choose_balance_precision).
  - On each fill, the balance moves by floor_to_precision(revenue - trade_fee).
    The part floored away is a "rounding fee".
  - Rounding fees accumulate per order. Whenever the accumulator holds at
    least one precision unit, that many whole units are rebated, capped so the
    fill's net fee (trade fee + rounding fee - rebate) never goes negative.

Revenue is signed: negative when paying (buying), positive when receiving.
The pipeline records every fill as a buy of its side (selling YES at P is
buying NO at 1 - P, and the YES+NO pair then pays $1). Because contract
counts have 2 decimals, that $1-per-pair credit is always a whole number of
cents, so flooring in either representation gives the same rounding fee.
"""

from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal, getcontext

# Exact arithmetic everywhere: nothing Kalshi sends comes close to 50 digits.
getcontext().prec = 50

CENT = Decimal("0.01")
HUNDREDTH_CENT = Decimal("0.0001")
# Finest first: if no fill ever needed rounding, both match and nothing changes.
DOCUMENTED_PRECISIONS = (HUNDREDTH_CENT, CENT)
BALANCE_PRECISION = CENT  # default for helpers; the live precision is detected
ZERO = Decimal("0")


def floor_to_precision(amount, precision=BALANCE_PRECISION):
    """Kalshi rule: balance changes are floored onto the member's precision grid."""
    return amount.quantize(precision, rounding=ROUND_FLOOR)


def is_on_grid(amount, precision=BALANCE_PRECISION):
    return floor_to_precision(amount, precision) == amount


def apply_fee_rounding(fills, precision=BALANCE_PRECISION):
    """Model Kalshi's rounding fee and per-order rebates on each fill, in place.

    Each fill needs: order_key, time, count, price (dollars, for the side
    bought) and fee_reported (the API's fee_cost, used as the trade fee).
    Adds: rounding_fee, rebate, and fee = trade fee + rounding fee - rebate
    (the fee that actually left the balance).

    If Kalshi's fee_cost already includes the rounding fee, every fill's
    revenue - fee_cost is already on the grid, the modeled rounding fee is
    exactly 0, and fee == fee_reported. Either way the balance change per fill
    is -(count * price) - fee, which is always on the grid.
    """
    accumulators = {}
    for fill in sorted(fills, key=lambda item: (item["time"], item.get("seq", 0))):
        revenue = -(fill["count"] * fill["price"])
        trade_fee = fill["fee_reported"]
        raw_change = revenue - trade_fee
        aligned = floor_to_precision(raw_change, precision)
        rounding_fee = raw_change - aligned

        held = accumulators.get(fill["order_key"], ZERO) + rounding_fee
        available_units = floor_to_precision(held, precision)
        fee_before_rebate = trade_fee + rounding_fee
        cap = floor_to_precision(fee_before_rebate, precision)
        rebate = min(available_units, cap) if available_units > ZERO else ZERO
        accumulators[fill["order_key"]] = held - rebate

        fill["rounding_fee"] = rounding_fee
        fill["rebate"] = rebate
        fill["fee"] = fee_before_rebate - rebate
    return fills


def app_display_cents(amount):
    """How Kalshi's app displays a dollar amount: half-up to the cent.

    Used ONLY to compare against figures read off the app (CSV fallback
    checks). Never used to compute or store anything.
    """
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def decimal_places(text):
    """Digits after the decimal point in a numeric string ("0.5600" -> 4)."""
    text = str(text)
    return len(text.split(".", 1)[1]) if "." in text else 0
