"""The page's JS money code, run in Node and checked against Python Decimal.

  - exact.js property test (hypothesis): random decimal strings through
    Exact.sum/add/sub/neg/cmp must equal Python Decimal exactly.
  - Parity test: kalshi/bets.js filtering, facet counts, month groups, the
    Open group and the footer totals, for many filter combinations, must equal
    an INDEPENDENT Python implementation, digit for digit.
  - URL state: parse/serialize round-trips, "Reset to all time" keeps status
    and categories and drops only the dates.

Needs Node. Skipped locally if it's missing; in CI (env CI set) that fails.
"""

import json
import os
import random
import shutil
import subprocess
import tempfile
import unittest
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

import kalshi_fixtures as fx
import kalshi_paths
from kalshi_common import dec_str

D = Decimal
HARNESS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js", "harness.js")
TODAY = "2026-10-11"
STATUSES = ["open", "won", "lost", "sold", "pending"]
CATEGORIES = ["NFL", "NBA", "College", "Soccer", "F1", "Crypto", "Politics", "Other"]


def node_or_skip():
    node = shutil.which("node")
    if not node:
        if os.environ.get("CI"):
            raise AssertionError("CI needs Node for the JS parity tests")
        raise unittest.SkipTest("node not installed")
    return node


def run_harness(request):
    result = subprocess.run([node_or_skip(), HARNESS], input=json.dumps(request), capture_output=True, text=True,
                            timeout=120)
    if result.returncode != 0:
        raise AssertionError("harness failed: " + result.stderr[-2000:])
    return json.loads(result.stdout)


# ---------- exact.js vs Decimal ----------
decimal_text = st.builds(
    lambda sign, whole, frac: sign + str(whole) + ("." + frac if frac else ""),
    st.sampled_from(["", "-"]),
    st.integers(min_value=0, max_value=10 ** 12),
    st.text(alphabet="0123456789", min_size=0, max_size=18),
)
operation = st.one_of(
    st.builds(lambda args: {"op": "sum", "args": args}, st.lists(decimal_text, min_size=0, max_size=8)),
    st.builds(lambda left, right: {"op": "add", "args": [left, right]}, decimal_text, decimal_text),
    st.builds(lambda left, right: {"op": "sub", "args": [left, right]}, decimal_text, decimal_text),
    st.builds(lambda value: {"op": "neg", "args": [value]}, decimal_text),
    st.builds(lambda left, right: {"op": "cmp", "args": [left, right]}, decimal_text, decimal_text),
)


def python_expected(op):
    args = [D(arg) for arg in op["args"]]
    if op["op"] == "sum":
        return dec_str(sum(args, D(0)))
    if op["op"] == "add":
        return dec_str(args[0] + args[1])
    if op["op"] == "sub":
        return dec_str(args[0] - args[1])
    if op["op"] == "neg":
        return dec_str(-args[0])
    if op["op"] == "cmp":
        return (args[0] > args[1]) - (args[0] < args[1])
    raise ValueError(op)


class ExactJsTests(unittest.TestCase):
    @settings(max_examples=int(os.environ.get("KALSHI_JS_EXAMPLES", "40")), deadline=None)
    @given(st.lists(operation, min_size=1, max_size=60))
    def test_exact_js_matches_decimal(self, ops):
        results = run_harness({"exact": ops})["exact"]
        for op, result in zip(ops, results):
            self.assertIn("ok", result, (op, result))
            self.assertEqual(result["ok"], python_expected(op), op)

    def test_refuses_what_it_cannot_do_exactly(self):
        results = run_harness({"exact": [
            {"op": "sum", "args": ["1." + "0" * 18 + "1"]},  # 19 decimal places
            {"op": "sum", "args": [1.5]},                      # a JS number, not a string
            {"op": "sum", "args": ["1e5"]},                    # exponent notation
        ]})["exact"]
        self.assertTrue(results[0]["error"].startswith("RangeError"))
        self.assertTrue(results[1]["error"].startswith("TypeError"))
        self.assertIn("not a decimal string", results[2]["error"])

    def test_scale_covers_every_value_in_data(self):
        scale = run_harness({"exact": []})["scale"]
        dashboard, _fills = fx.full_dashboard()
        self.assertLessEqual(dashboard["max_decimal_places"], scale)
        live_path = os.path.join(kalshi_paths.REPO, "kalshi", "data.json")
        with open(live_path, encoding="utf-8") as handle:
            live = json.load(handle)
        if "max_decimal_places" in live:
            self.assertLessEqual(live["max_decimal_places"], scale)


# ---------- bets.js parity vs an independent Python implementation ----------
def py_filter(bets, state, skip=None):
    rows = []
    for bet in bets:
        if state["from"] and bet["event_date"] < state["from"]:
            continue
        if state["to"] and bet["event_date"] > state["to"]:
            continue
        if skip != "status" and state["status"] != "all" and bet["outcome"] != state["status"]:
            continue
        if skip != "cats" and state["cats"] and bet["category"] not in state["cats"]:
            continue
        rows.append(bet)
    return rows


def py_totals(rows):
    valued = [bet for bet in rows if bet["payout"] is not None]

    def total(group, key):
        return dec_str(sum((D(bet[key]) for bet in group), D(0)))

    return {
        "count": len(rows), "unvalued": len(rows) - len(valued),
        "stake": total(rows, "stake"), "buy_fees": total(rows, "buy_fees"), "cost": total(rows, "cost"),
        "payout": total(valued, "payout"), "sell_fees": total(valued, "sell_fees"),
        "net_payout": total(valued, "net_payout"), "profit": total(valued, "profit"),
        "valued_cost": total(valued, "cost"),
    }


def query_for(status, cats, start, end):
    parts = []
    if status != "all":
        parts.append("status=" + status)
    if cats:
        parts.append("cat=" + ",".join(cats))
    if start:
        parts.append("from=" + start)
    if end:
        parts.append("to=" + end)
    return ("?" + "&".join(parts)) if parts else ""


def parity_states(bets, count=150):
    randomizer = random.Random(20261011)
    dates = sorted({bet["event_date"] for bet in bets})
    states = [""] + ["?status=" + status for status in STATUSES] + ["?cat=" + cat for cat in CATEGORIES]
    states += ["?status=open&cat=NFL", "?status=lost&cat=NFL,Soccer", "?from=2026-09-01", "?to=2026-06-30",
               "?from=2026-06-18&to=2026-06-30", "?from=" + TODAY, "?status=bogus&cat=Nope&from=xx"]
    for _ in range(count):
        status = randomizer.choice(["all"] + STATUSES)
        cats = randomizer.sample(CATEGORIES, randomizer.randint(0, 3))
        span = sorted(randomizer.sample(dates + ["2025-12-02", TODAY], 2))
        start = span[0] if randomizer.random() < 0.6 else None
        end = span[1] if randomizer.random() < 0.6 else None
        states.append(query_for(status, cats, start, end))
    return states


class BetsJsParityTests(unittest.TestCase):
    def check_parity(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(data, handle)
            out = run_harness({"bets": {"data": path, "today": TODAY, "states": parity_states(data["bets"])}})
        bets = data["bets"]
        for result in out["states"]:
            state = result["state"]
            rows = py_filter(bets, state)
            label = result["query"]
            self.assertEqual(result["indexes"], [bets.index(bet) for bet in rows], label)
            self.assertEqual(result["totals"], py_totals(rows), label)

            counts = {"all": len(py_filter(bets, state, skip="status"))}
            for status in STATUSES:
                counts[status] = sum(1 for bet in py_filter(bets, state, skip="status") if bet["outcome"] == status)
            self.assertEqual(result["status_counts"], counts, label)
            cat_pool = py_filter(bets, state, skip="cats")
            cat_counts = {cat: sum(1 for bet in cat_pool if bet["category"] == cat) for cat in CATEGORIES}
            self.assertEqual(result["category_counts"], {cat: num for cat, num in cat_counts.items() if num}, label)

            opened = [bet for bet in rows if bet["status"] == "open"]
            self.assertEqual(result["open"]["indexes"], [bets.index(bet) for bet in opened], label)
            self.assertEqual(result["open"]["totals"], py_totals(opened), label)
            months = {}
            for bet in rows:
                if bet["status"] != "open":
                    months.setdefault(bet["event_date"][:7], []).append(bet)
            self.assertEqual([month["key"] for month in result["months"]], sorted(months, reverse=True), label)
            for month in result["months"]:
                self.assertEqual(month["totals"], py_totals(months[month["key"]]), label + " " + month["key"])

            # The footer's equation holds exactly on the JS totals.
            totals = {key: (D(value) if isinstance(value, str) else value) for key, value in result["totals"].items()}
            self.assertEqual(totals["stake"] + totals["buy_fees"], totals["cost"], label)
            self.assertEqual(totals["payout"] - totals["sell_fees"], totals["net_payout"], label)
            self.assertEqual(totals["net_payout"] - totals["valued_cost"], totals["profit"], label)
        return out

    def test_parity_on_full_fixture(self):
        dashboard, _fills = fx.full_dashboard()
        out = self.check_parity(json.loads(json.dumps(dashboard)))
        everything = [result for result in out["states"] if result["query"] == ""][0]
        summary = dashboard["summary"]
        # All time: footer profit == realized + unrealized, exactly as stored.
        self.assertEqual(D(everything["totals"]["profit"]), D(summary["realized_pnl"]) + D(summary["unrealized_pnl"]))
        opened = [result for result in out["states"] if result["query"] == "?status=open"][0]
        self.assertEqual(D(opened["totals"]["profit"]), D(summary["unrealized_pnl"]))

    def test_parity_on_live_data(self):
        with open(os.path.join(kalshi_paths.REPO, "kalshi", "data.json"), encoding="utf-8") as handle:
            live = json.load(handle)
        if "bets" not in live:
            self.skipTest("live data.json predates the all-bets format")
        self.check_parity(live)


class UrlStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dashboard, _fills = fx.full_dashboard()
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(json.loads(json.dumps(dashboard)), handle)
            cls.out = run_harness({"bets": {"data": path, "today": TODAY, "states": [
                "", "?status=open", "?status=won&cat=NFL,Soccer&from=2026-06-01&to=2026-09-30",
                "?from=2026-09-10&range=nfl", "?status=nope&cat=Nope&from=bad", "?cat=Soccer&from=2026-06-01",
            ]}})
        cls.by_query = {result["query"]: result for result in cls.out["states"]}

    def test_default_is_all_time_every_bet(self):
        result = self.by_query[""]
        self.assertEqual(result["state"], {"status": "all", "cats": [], "from": None, "to": None, "range": "all"})
        self.assertEqual(len(result["indexes"]), 8)
        self.assertEqual(result["label"], "Showing: All time · Dec 2, 2025 → Oct 11, 2026 · 8 bets")

    def test_round_trip(self):
        for query in ("?status=open", "?status=won&cat=NFL,Soccer&from=2026-06-01&to=2026-09-30",
                      "?from=2026-09-10&range=nfl"):
            self.assertEqual(self.by_query[query]["round_trip"], query)

    def test_reset_keeps_status_and_categories(self):
        self.assertEqual(self.by_query["?status=won&cat=NFL,Soccer&from=2026-06-01&to=2026-09-30"]["reset"],
                         "?status=won&cat=NFL,Soccer")
        self.assertEqual(self.by_query["?cat=Soccer&from=2026-06-01"]["reset"], "?cat=Soccer")
        self.assertEqual(self.by_query["?from=2026-09-10&range=nfl"]["reset"], "")

    def test_bad_params_are_ignored(self):
        self.assertEqual(self.by_query["?status=nope&cat=Nope&from=bad"]["state"],
                         {"status": "all", "cats": [], "from": None, "to": None, "range": "all"})

    def test_presets_and_labels(self):
        keys = [preset["key"] for preset in self.out["presets"]]
        self.assertEqual(keys, ["all", "nfl", "30d", "2025", "2026"])
        nfl = [preset for preset in self.out["presets"] if preset["key"] == "nfl"][0]
        self.assertEqual(nfl["from"], "2026-09-10")
        self.assertTrue(self.by_query["?from=2026-09-10&range=nfl"]["label"].startswith(
            "Showing: This NFL season · Sep 10, 2026 → Oct 11, 2026 · "))


if __name__ == "__main__":
    unittest.main()
