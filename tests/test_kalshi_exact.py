"""Exactness tests: golden values, row/aggregate identities, round-trips, zero-tolerance reconciliation.

Every comparison here is Decimal equality. There is no tolerance anywhere.
"""

import io
import contextlib
import json
import unittest
from decimal import Decimal

import kalshi_fixtures as fx
import kalshi_common
import kalshi_fetch
import kalshi_rules

D = Decimal


def rows_by_title(dashboard):
    return {bet["title"]: bet for bet in dashboard["bets"]}


class GoldenTests(unittest.TestCase):
    """Figures from the Kalshi app / hand arithmetic (see kalshi_fixtures docstring)."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard, cls.fills = fx.golden_dashboard()
        cls.rows = rows_by_title(cls.dashboard)

    def test_every_golden_row_exact(self):
        for title, (cost, payout, profit) in fx.GOLDEN_ROWS.items():
            row = self.rows[title]
            self.assertEqual((D(row["cost"]), D(row["net_payout"]), D(row["profit"])), (cost, payout, profit), title)

    def test_robinson_full_precision_strings(self):
        row = self.rows["Bijan Robinson TD"]
        self.assertEqual((row["stake"], row["buy_fees"], row["cost"]), ("1.936", "0.061", "1.997"))
        self.assertEqual((row["payout"], row["sell_fees"], row["net_payout"], row["profit"]), ("3.4848", "0", "3.4848", "1.4878"))
        self.assertEqual(D("3.52") * D("0.55") + D("0.0610"), D(row["cost"]))

    def test_penix_mexico_canada(self):
        self.assertEqual(self.rows["Penix 275+"]["cost"], "1.0079")
        self.assertEqual(D(self.rows["Penix 275+"]["cost"]), D("0.996") + D("0.0119"))
        self.assertEqual(self.rows["Penix 275+"]["payout"], "1.188")
        self.assertEqual(self.rows["Mexico advances"]["payout"], "1.805")
        canada = self.rows["Canada wins WC Group B"]
        self.assertEqual((canada["stake"], canada["buy_fees"], canada["cost"]), ("10.36", "0.63", "10.99"))
        self.assertEqual((canada["payout"], canada["sell_fees"], canada["net_payout"], canada["profit"]),
                         ("24.42", "1.1453", "23.2747", "12.2847"))

    def test_categories_net_and_open(self):
        cats = {cat["name"]: D(cat["profit"]) for cat in self.dashboard["categories"]}
        self.assertEqual(cats, fx.GOLDEN_CATEGORIES)
        self.assertEqual(D(self.dashboard["summary"]["net_pnl"]), fx.GOLDEN_NET)
        golden = self.rows["Golden 40+"]
        self.assertEqual((D(golden["cost"]), D(golden["payout"])), (fx.GOLDEN_OPEN["cost"], fx.GOLDEN_OPEN["value"]))
        self.assertTrue(golden["unrealized"])
        # Open bets obey the same equation, with the live bid as the payout.
        self.assertEqual((golden["live"]["contracts"], golden["live"]["bid"], golden["live"]["amount"]), ("5.8", "0.31", "1.798"))
        self.assertEqual(golden["profit"], "-0.2055")
        self.assertEqual(self.dashboard["summary"]["unrealized_pnl"], "-0.2055")

    def test_precision_detected(self):
        self.assertEqual(self.dashboard["ledger"]["balance_precision_matched"], "0.0001")
        self.assertEqual(self.dashboard["fees"]["rounding"], "0")

    def test_all_identities_hold(self):
        self.assertEqual(fx.identity_failures(self.dashboard, self.fills), [])


class CentRuleTests(unittest.TestCase):
    """Kalshi's documented cent-rounding rule, for a $0.01-precision (retail) balance.

    Robinson again, but the cash only moved in whole cents:
      buy:  -(1.936 + 0.0610) = -1.997 -> floored to -2.00, rounding fee 0.003
      sell: +3.4848            -> floored to +3.48, rounding fee 0.0048
    """

    def setUp(self):
        fills = [fx.GOLDEN_FILLS[0], fx.GOLDEN_FILLS[1]]
        # 35.00 in - 0.20 deposit fee - 2.00 + 3.48 = 36.28
        self.dashboard, self.fills = fx.golden_dashboard(fills=fills, settlements=[], positions=[], cash="36.28",
                                                         portfolio_cents=0)

    def test_cent_precision_chosen_and_rounding_modeled(self):
        self.assertEqual(self.dashboard["ledger"]["balance_precision_matched"], "0.01")
        row = rows_by_title(self.dashboard)["Bijan Robinson TD"]
        # buy: 1.936 + (0.061 + 0.003 rounding) = 2; sell: 3.4848 - 0.0048 rounding = 3.48
        self.assertEqual((row["stake"], row["buy_fees"], row["cost"]), ("1.936", "0.064", "2"))
        self.assertEqual((row["payout"], row["sell_fees"], row["net_payout"], row["profit"]), ("3.4848", "0.0048", "3.48", "1.48"))
        self.assertEqual(self.dashboard["fees"]["rounding"], "0.0078")
        self.assertEqual(fx.identity_failures(self.dashboard, self.fills), [])

    def test_floor_rule_directly(self):
        self.assertEqual(kalshi_rules.floor_to_precision(D("-1.997"), D("0.01")), D("-2.00"))
        self.assertEqual(kalshi_rules.floor_to_precision(D("3.4848"), D("0.01")), D("3.48"))
        self.assertEqual(kalshi_rules.floor_to_precision(D("-1.997"), D("0.0001")), D("-1.997"))

    def test_accumulator_rebate_matches_docs_example(self):
        # Docs, worked example 2: three fills each adding $0.004 of rounding on
        # one order; the third rebates $0.01 and carries $0.002.
        fills = []
        for num in range(3):
            fills.append({"order_key": "one-order", "time": num, "count": D("1"), "price": D("0.996"),
                          "fee_reported": D("0.010")})
        kalshi_rules.apply_fee_rounding(fills, D("0.01"))
        self.assertEqual([fill["rounding_fee"] for fill in fills], [D("0.004")] * 3)
        self.assertEqual([fill["rebate"] for fill in fills], [D("0"), D("0"), D("0.01")])
        self.assertEqual(fills[2]["fee"], D("0.010") + D("0.004") - D("0.01"))


class ReconcileExactTests(unittest.TestCase):
    def test_smallest_unit_off_is_blocked_with_every_digit(self):
        client = fx.FakeClient(cash="44.7531")  # one $0.0001 more than the ledger supports
        with self.assertRaises(kalshi_fetch.ReconciliationError) as caught:
            kalshi_fetch.build_from_api(client)
        message = str(caught.exception)
        self.assertIn("actual cash $44.7531", message)
        self.assertIn("at $0.0001 precision expected cash $44.753, diff $0.0001", message)
        self.assertIn("data.json not updated", message)
        for secret_ish in ("KX", "fill-", "o-rob", "Robinson"):
            self.assertNotIn(secret_ish, message)

    def test_blocked_run_never_writes(self):
        written = []
        with self.assertRaises(SystemExit):
            kalshi_fetch.run(fx.FakeClient(cash="44.7529"), writer=written.append)
        self.assertEqual(written, [])

    def test_exact_run_writes_and_prints_full_digits(self):
        written = []
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            kalshi_fetch.run(fx.FakeClient(), writer=lambda dash: written.append(dash) or True)
        lines = output.getvalue().strip().splitlines()
        self.assertEqual(len(written), 1)
        self.assertTrue(lines[0].startswith("ledger precision: "))
        self.assertEqual(lines[1], "reconciled exactly: expected cash $44.753 = actual cash $44.753, diff $0; "
                                   "net $11.553 (data.json updated)")

    def test_net_mismatch_blocks(self):
        dashboard, fills = fx.golden_dashboard()
        payouts = [D("12.32"), D("0")]
        dashboard["summary"]["net_pnl"] = kalshi_common.dec_str(D(dashboard["summary"]["net_pnl"]) + D("0.0001"))
        with self.assertRaises(kalshi_fetch.ReconciliationError) as caught:
            kalshi_fetch.reconcile(dashboard, fills, payouts, D(fx.GOLDEN_CASH), D("1.80"))
        self.assertIn("diff $0.0001", str(caught.exception))


class RoundTripTests(unittest.TestCase):
    VALUES = ["3.4848", "-1.4878", "0", "-0", "0.000001", "1E-7", "100", "1E+2", "12.280000", "-0.0000",
              "123456789.123456789", "0.1", "-7.58"]

    def test_decimal_string_decimal_is_exact(self):
        for text in self.VALUES:
            value = D(text)
            stored = kalshi_common.dec_str(value)
            self.assertNotIn("E", stored.upper(), text)
            self.assertEqual(D(stored), value, text)

    def test_json_round_trip_of_whole_dashboard(self):
        dashboard, fills = fx.golden_dashboard()
        reloaded = json.loads(json.dumps(dashboard))
        for (path, before), (_same, after) in zip(fx.money_fields(dashboard), fx.money_fields(reloaded)):
            if isinstance(before, str) and path.rsplit(".", 1)[-1] in fx.MONEY_KEYS:
                self.assertEqual(D(before), D(after), path)
                self.assertEqual(before, after, path)

    def test_floats_are_refused(self):
        with self.assertRaises(TypeError):
            kalshi_common.to_decimal(3.52)


if __name__ == "__main__":
    unittest.main()
