"""Tests for the zero-tolerance reconciliation guard in scripts/kalshi_fetch.py.

Run from the repo root:
    python -m unittest discover -s tests -v

No network: a fake client stands in for the Kalshi API.
"""

import contextlib
import io
import json
import os
import tempfile
import unittest
from decimal import Decimal

import kalshi_fixtures as fx
import kalshi_fetch
from kalshi_common import write_if_changed

D = Decimal

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
#   = 41.08 exactly
FILLS = [
    fx.api_fill(0, "AAA", "order-0", "yes", "10.00", "0.4000", "0.10", True, "2026-10-01T12:00:00Z"),
    fx.api_fill(1, "BBB", "order-1", "no", "5.00", "0.7000", "0.05", True, "2026-10-02T12:00:00Z"),
    fx.api_fill(2, "BBB", "order-2", "yes", "5.00", "0.2000", "0.03", True, "2026-10-03T12:00:00Z"),
    fx.api_fill(3, "CCC", "order-3", "yes", "4.00", "0.5000", "0.04", True, "2026-10-04T12:00:00Z"),
]
POSITIONS = [{"ticker": "CCC", "position_fp": "4.00"}]
BIDS = {"CCC": ("0.55", "0.45")}


def client(cash="41.08", settlement_cents=1000):
    settlements = [{"ticker": "AAA", "revenue": settlement_cents, "settled_time": "2026-10-05T00:00:00Z", "fee_cost": "0"}]
    return fx.FakeClient(fills=FILLS, settlements=settlements, positions=POSITIONS, cash=cash, portfolio_cents=220,
                         bids=BIDS, titles={})


class RecordingWriter:
    def __init__(self):
        self.calls = []

    def __call__(self, dashboard):
        self.calls.append(dashboard)
        return True


def run_quietly(fake, writer):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        kalshi_fetch.run(fake, writer=writer)
    return output.getvalue().strip().splitlines()


class ReconcileTests(unittest.TestCase):
    def test_expected_cash_matches_hand_arithmetic(self):
        dashboard, fills, payouts, cash, portfolio = kalshi_fetch.build_from_api(client())
        self.assertEqual(kalshi_fetch.expected_cash(fills, payouts), D("41.08"))

    def test_consistent_data_writes_and_prints(self):
        writer = RecordingWriter()
        lines = run_quietly(client(), writer)
        self.assertEqual(len(writer.calls), 1)
        self.assertTrue(lines[0].startswith("ledger precision: "))
        self.assertEqual(lines[1], "reconciled exactly: expected cash $41.08 = actual cash $41.08, diff $0; "
                                   "net $8.28 (data.json updated)")

    def test_one_dollar_settlement_error_blocks_write(self):
        # The API claims AAA paid $11.00, but cash only reflects $10.00.
        writer = RecordingWriter()
        with self.assertRaises(kalshi_fetch.ReconciliationError) as caught:
            run_quietly(client(settlement_cents=1100), writer)
        self.assertEqual(writer.calls, [])
        message = str(caught.exception)
        self.assertEqual(
            message,
            "Reconciliation failed: actual cash $41.08; at $0.0001 precision expected cash $42.08, diff $-1; "
            "at $0.01 precision expected cash $42.08, diff $-1. data.json not updated.",
        )
        for secret_ish in ("AAA", "BBB", "CCC", "Kalshi market", "fill-", "order-"):
            self.assertNotIn(secret_ish, message)

    def test_blocked_run_leaves_data_json_untouched_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = os.path.join(scratch, "data.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"source": "csv", "summary": {"net_pnl": "0.31"}, "updated": "2026-10-10T00:00:00Z"}, handle)
            with open(path, "rb") as handle:
                before = handle.read()
            with self.assertRaises(SystemExit) as caught:
                run_quietly(client(cash="41.07"), lambda dashboard: write_if_changed(dashboard, path=path))
            self.assertNotIn(caught.exception.code, (0, None))
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), before)

    def test_smallest_differences_are_blocked(self):
        for cash in ("41.0801", "41.0799", "41.09", "41.080001"):
            with self.assertRaises(kalshi_fetch.ReconciliationError, msg=cash):
                run_quietly(client(cash=cash), RecordingWriter())

    def test_net_pnl_mismatch_blocks(self):
        dashboard, fills, payouts, cash, portfolio = kalshi_fetch.build_from_api(client())
        dashboard["summary"]["net_pnl"] = "9.28"
        with self.assertRaises(kalshi_fetch.ReconciliationError) as caught:
            kalshi_fetch.reconcile(dashboard, fills, payouts, cash, portfolio)
        self.assertIn("expected net P&L $8.28, dashboard net P&L $9.28, diff $1", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
