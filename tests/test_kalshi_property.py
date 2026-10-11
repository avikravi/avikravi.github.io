"""Property-based tests (hypothesis): random fills, partial sells and settlements.

Kalshi's ledger is simulated here INDEPENDENTLY of the pipeline: real buy/sell
semantics (a sale has positive revenue), the documented floor-to-precision
rule and the per-order rebate accumulator, re-implemented from the docs. The
pipeline must reproduce that cash exactly and satisfy every identity.
"""

import os
import unittest
from decimal import ROUND_FLOOR, Decimal

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import kalshi_fixtures as fx
import kalshi_common
import kalshi_fetch

D = Decimal
EXAMPLES = int(os.environ.get("KALSHI_PROPERTY_EXAMPLES", "120"))


def cents_from(text):
    return D(text) / 100


counts = st.integers(min_value=1, max_value=5000).map(lambda num: D(num) / 100)          # 0.01 .. 50.00 contracts
prices = st.integers(min_value=100, max_value=9900).map(lambda num: D(num) / 10000)      # 0.0100 .. 0.9900
taker_fees = st.integers(min_value=0, max_value=200000).map(lambda num: D(num) / 1000000)  # up to 6 decimals


@st.composite
def markets(draw):
    side = draw(st.sampled_from(["yes", "no"]))
    buy_price = draw(prices)
    pieces = draw(st.lists(st.tuples(counts, taker_fees, st.booleans()), min_size=1, max_size=3))
    held = sum((piece[0] for piece in pieces), D(0))
    sell = None
    if draw(st.booleans()):
        fraction = draw(st.integers(min_value=1, max_value=100))
        sell_count = (held * fraction / 100).quantize(D("0.01"), rounding=ROUND_FLOOR)
        if sell_count > 0:
            sell = (sell_count, draw(prices), draw(taker_fees), draw(st.booleans()))
    ending = draw(st.sampled_from(["open", "won", "lost"]))
    return {"side": side, "buy_price": buy_price, "pieces": pieces, "sell": sell, "ending": ending}


def stamp(serial):
    """Strictly increasing timestamps, so fill order (and rebate order) is unambiguous."""
    return "2026-01-01T{:02d}:{:02d}:{:02d}Z".format(serial // 3600, (serial // 60) % 60, serial % 60)


def other(side):
    return "no" if side == "yes" else "yes"


def simulate(market_list, precision):
    """Independent Kalshi ledger: returns API-shaped fills/settlements/positions and the true cash."""
    cash = D("35.00") - D("0.20")
    fills, settlements, positions, bids = [], [], [], {}
    serial = 0
    for index, market in enumerate(market_list):
        ticker = "KXTEST-M{}".format(index)
        side = market["side"]
        # One buy order, possibly in several fills; maker fills pay no trade fee.
        buy_accumulator = D(0)
        for count, fee, taker in market["pieces"]:
            serial += 1
            fee = fee if taker else D(0)
            revenue = -(count * market["buy_price"])
            buy_accumulator, change = ledger_change(revenue, fee, buy_accumulator, precision)
            cash += change
            yes_price = market["buy_price"] if side == "yes" else 1 - market["buy_price"]
            fills.append(fx.api_fill(serial, ticker, "buy-{}".format(index), side, kalshi_common.dec_str(count),
                                     kalshi_common.dec_str(yes_price), kalshi_common.dec_str(fee), taker,
                                     stamp(serial)))
            fills[-1]["ts"] = serial
        held = sum((piece[0] for piece in market["pieces"]), D(0))
        if market["sell"]:
            count, price, fee, taker = market["sell"]
            serial += 1
            fee = fee if taker else D(0)
            revenue = count * price  # a real sale: money comes in
            _unused, change = ledger_change(revenue, fee, D(0), precision)
            cash += change
            # The API reports selling `side` at `price` as exposure to the other side.
            yes_price = price if side == "yes" else 1 - price
            fills.append(fx.api_fill(serial, ticker, "sell-{}".format(index), other(side), kalshi_common.dec_str(count),
                                     kalshi_common.dec_str(yes_price), kalshi_common.dec_str(fee), taker,
                                     stamp(serial)))
            fills[-1]["ts"] = serial
            held -= count
        if held == 0:
            continue
        if market["ending"] == "open":
            positions.append({"ticker": ticker, "position_fp": kalshi_common.dec_str(held if side == "yes" else -held)})
            bids[ticker] = ("0.5", "0.5")
        else:
            revenue_cents = int(held * 100) if market["ending"] == "won" else 0
            cash += D(revenue_cents) / 100
            settlements.append({"ticker": ticker, "revenue": revenue_cents, "settled_time": "2026-03-01T00:00:00Z",
                                "fee_cost": "0"})
    return fills, settlements, positions, bids, cash


def ledger_change(revenue, trade_fee, accumulator, precision):
    """Docs rule, re-implemented: floor (revenue - fee) to precision; rebate whole units of the accumulator."""
    raw = revenue - trade_fee
    aligned = raw.quantize(precision, rounding=ROUND_FLOOR)
    accumulator += raw - aligned
    units = accumulator.quantize(precision, rounding=ROUND_FLOOR)
    cap = (trade_fee + raw - aligned).quantize(precision, rounding=ROUND_FLOOR)
    rebate = min(units, cap) if units > 0 else D(0)
    return accumulator - rebate, aligned + rebate


class PropertyTests(unittest.TestCase):
    @settings(max_examples=EXAMPLES, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(markets(), min_size=1, max_size=6), st.sampled_from([D("0.0001"), D("0.01")]),
           st.integers(min_value=0, max_value=100000))
    def test_pipeline_reconciles_exactly_and_identities_hold(self, market_list, precision, portfolio_cents):
        fills, settlements, positions, bids, cash = simulate(market_list, precision)
        client = fx.FakeClient(fills=fills, settlements=settlements, positions=positions,
                               cash=kalshi_common.dec_str(cash), portfolio_cents=portfolio_cents, bids=bids, titles={})
        dashboard, out_fills, payouts, actual, portfolio = kalshi_fetch.build_from_api(client)
        kalshi_fetch.reconcile(dashboard, out_fills, payouts, actual, portfolio)  # raises on any difference
        self.assertEqual(fx.identity_failures(dashboard, out_fills), [])

    @settings(max_examples=max(20, EXAMPLES // 4), deadline=None)
    @given(st.lists(markets(), min_size=1, max_size=4), st.sampled_from([D("0.0001"), D("0.01")]))
    def test_any_difference_blocks(self, market_list, precision):
        fills, settlements, positions, bids, cash = simulate(market_list, precision)
        client = fx.FakeClient(fills=fills, settlements=settlements, positions=positions,
                               # Off both documented grids, so no precision can match it by coincidence.
                               cash=kalshi_common.dec_str(cash + D("0.00005")), portfolio_cents=0, bids=bids, titles={})
        with self.assertRaises(kalshi_fetch.ReconciliationError):
            kalshi_fetch.build_from_api(client)


if __name__ == "__main__":
    unittest.main()
