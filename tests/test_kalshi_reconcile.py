"""Tests for the reconciliation guard in scripts/kalshi_fetch.py.

Run from the repo root:
    python -m unittest discover -s tests -v

No network: a fake client stands in for the Kalshi API.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import kalshi_fetch  # noqa: E402
from kalshi_common import write_if_changed  # noqa: E402

# Three markets, using the deposits/credits in kalshi_common ($10 + $25 in,
# $0.20 deposit fee):
#   AAA: bought 10 YES @ 40c (fee 10c), settled YES -> pays $10.00
#   BBB: bought 5 NO @ 30c (fee 5c), sold them @ 80c (recorded as buying
#        5 YES @ 20c, fee 3c) -> 5 matched pairs pay $5.00
#   CCC: bought 4 YES @ 50c (fee 4c), still open, YES bid 55c
#
# Expected cash, worked by hand in the user's terms:
#   deposits + credits      35.00
#   + sale proceeds          4.00   (5 NO sold @ 80c)
#   + settlement payouts    10.00
#   - purchase costs         7.50   (4.00 + 1.50 + 2.00)
#   - all fees               0.42   (0.10 + 0.05 + 0.03 + 0.04 + 0.20 deposit)
#   = 41.08
GOOD_CASH_CENTS = 4108
OPEN_VALUE_CENTS = 220  # 4 x 55c


def make_fill(num, ticker, side, count, price, fee, taker=True):
    return {
        "fill_id": "fill-%d" % num,
        "order_id": "order-%d" % num,
        "ticker": ticker,
        "outcome_side": side,
        "count_fp": "%.2f" % count,
        "yes_price_dollars": "%.4f" % (price if side == "yes" else 1 - price),
        "no_price_dollars": "%.4f" % (price if side == "no" else 1 - price),
        "is_taker": taker,
        "fee_cost": "%.4f" % fee,
        "created_time": "2026-10-0%dT12:00:00Z" % (num + 1),
    }


FILLS = [
    make_fill(0, "AAA", "yes", 10, 0.40, 0.10),
    make_fill(1, "BBB", "no", 5, 0.30, 0.05),
    make_fill(2, "BBB", "yes", 5, 0.20, 0.03),
    make_fill(3, "CCC", "yes", 4, 0.50, 0.04),
]


class FakeClient:
    def __init__(self, cash_cents=GOOD_CASH_CENTS, settlement_cents=1000):
        self.cash_cents = cash_cents
        self.settlement_cents = settlement_cents

    def get(self, endpoint, params=None, allow_missing=False):
        if endpoint == "/portfolio/balance":
            return {"balance": self.cash_cents, "portfolio_value": OPEN_VALUE_CENTS}
        if endpoint.startswith("/markets/"):
            code = endpoint.rsplit("/", 1)[-1]
            return {"market": {"title": "Test market " + code, "result": "", "yes_bid_dollars": "0.55", "no_bid_dollars": "0.44"}}
        return None

    def paginate(self, endpoint, list_key, extra=None):
        pages = {
            "/portfolio/fills": FILLS,
            "/historical/fills": [],
            "/portfolio/settlements": [
                {"ticker": "AAA", "revenue": self.settlement_cents, "settled_time": "2026-10-05T00:00:00Z"}
            ],
            "/portfolio/positions": [{"ticker": "CCC", "position_fp": "4.00"}],
        }
        return pages[endpoint]


class RecordingWriter:
    def __init__(self):
        self.calls = []

    def __call__(self, dashboard):
        self.calls.append(dashboard)
        return True


def run_quietly(client, writer):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        kalshi_fetch.run(client, writer=writer)
    return output.getvalue().strip()


class ReconcileTests(unittest.TestCase):
    def test_expected_cash_matches_hand_arithmetic(self):
        dashboard, fills, payouts, cash, portfolio = kalshi_fetch.build_from_api(FakeClient())
        self.assertAlmostEqual(kalshi_fetch.expected_cash(fills, payouts), 41.08, places=6)

    def test_consistent_data_writes_and_prints_one_line(self):
        writer = RecordingWriter()
        printed = run_quietly(FakeClient(), writer)
        self.assertEqual(len(writer.calls), 1)
        self.assertEqual(printed, "reconciled: cash diff $0.00, net +$8.28 (data.json updated)")
        self.assertEqual(len(printed.splitlines()), 1)

    def test_one_dollar_settlement_error_blocks_write(self):
        # The API claims AAA paid $11.00, but cash only reflects $10.00.
        writer = RecordingWriter()
        with self.assertRaises(kalshi_fetch.ReconciliationError) as caught:
            run_quietly(FakeClient(settlement_cents=1100), writer)
        self.assertEqual(writer.calls, [])
        message = str(caught.exception)
        self.assertEqual(
            message,
            "Reconciliation failed: expected cash $42.08, actual cash $41.08, diff $-1.00. data.json not updated.",
        )
        # Only totals: no market names, codes or IDs leak into the public log.
        for secret_ish in ("AAA", "BBB", "CCC", "Test market", "fill-", "order-"):
            self.assertNotIn(secret_ish, message)

    def test_blocked_run_leaves_data_json_untouched_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = os.path.join(scratch, "data.json")
            last_good = {"source": "csv", "summary": {"net_pnl": 0.31}, "updated": "2026-10-10T00:00:00Z"}
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(last_good, handle)
            with open(path, "rb") as handle:
                before = handle.read()

            def writer(dashboard):
                return write_if_changed(dashboard, path=path)

            with self.assertRaises(SystemExit) as caught:
                run_quietly(FakeClient(cash_cents=GOOD_CASH_CENTS - 100), writer)
            self.assertNotIn(caught.exception.code, (0, None))
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), before)

    def test_four_cents_is_within_tolerance(self):
        writer = RecordingWriter()
        printed = run_quietly(FakeClient(cash_cents=GOOD_CASH_CENTS + 4), writer)
        self.assertEqual(len(writer.calls), 1)
        self.assertTrue(printed.startswith("reconciled: cash diff $0.04"))

    def test_six_cents_is_blocked(self):
        writer = RecordingWriter()
        with self.assertRaises(kalshi_fetch.ReconciliationError):
            run_quietly(FakeClient(cash_cents=GOOD_CASH_CENTS - 6), writer)
        self.assertEqual(writer.calls, [])

    def test_net_pnl_mismatch_blocks(self):
        dashboard, fills, payouts, cash, portfolio = kalshi_fetch.build_from_api(FakeClient())
        dashboard["summary"]["net_pnl"] += 1.00
        with self.assertRaises(kalshi_fetch.ReconciliationError) as caught:
            kalshi_fetch.reconcile(dashboard, fills, payouts, cash, portfolio)
        self.assertIn("expected net P&L $+8.28, dashboard net P&L $+9.28, diff $+1.00", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
