"""Headless render of kalshi/index.html against a fixture data.json.

Renders several views (#bets, #bets?status=open, #bets?status=lost&cat=NFL,
#bets?from=2026-09-01, #overview) and checks, with no tolerance:
  - every amount the page shows (data-field) equals its stored string,
    formatted by the display rule (an independent Python implementation below);
  - every bet row visibly adds up: Stake + Buy fees = Cost,
    Payout - Sell fees = Net payout, Net payout - Cost = Profit (open bets too);
  - every row's fills (plus settlement / live-bid line) add up to the row;
  - month subtotals, the Open group total and the footer totals (computed in
    the browser by exact.js) equal Python Decimal totals for that filter, and
    the footer equation holds; All time footer = realized + unrealized P&L;
  - URL filter state, "Reset to all time", parlay legs, the Overview open link.

Needs Google Chrome/Chromium. In CI (env CI set) a missing or hung browser
fails. Locally, where desktop Chrome on some Macs hangs in headless mode, it
skips; render in a real browser instead:
    python3 tests/test_kalshi_display.py --serve 8765
    for each view below, open http://localhost:8765/index.html#<view> and POST the DOM:
      fetch('/dom?name=<key>', {method: 'POST', body: document.documentElement.outerHTML})
    KALSHI_DISPLAY_DOM_DIR=<printed folder> python3 -m unittest discover -s tests -p test_kalshi_display.py
"""

import functools
import html.parser
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
from decimal import Decimal

import kalshi_fixtures as fx
import kalshi_paths
from test_kalshi_js import py_filter, py_totals

D = Decimal
VIEWS = {
    "all": "bets",
    "open": "bets?status=open",
    "lost_nfl": "bets?status=lost&cat=NFL",
    "since_sep": "bets?from=2026-09-01",
    "overview": "overview",
}
CHROME_CANDIDATES = [
    os.environ.get("CHROME_BIN", ""),
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_chrome():
    for candidate in CHROME_CANDIDATES:
        if candidate and (shutil.which(candidate) or os.path.isfile(candidate)):
            return shutil.which(candidate) or candidate
    return None


# ---------- The page's display rules, re-implemented independently ----------
def money_digits(text):
    whole, _dot, frac = text.lstrip("+-").partition(".")
    return (whole.lstrip("0") or "0") + "." + frac.rstrip("0").ljust(2, "0")


def display(text, mode):
    if text is None:
        return "—"
    negative = text.startswith("-") and D(text) != 0
    if mode == "plain":
        return ("−" if negative else "") + "$" + money_digits(text)
    if mode == "signed":
        return "$" + money_digits(text) if D(text) == 0 else ("−" if negative else "+") + "$" + money_digits(text)
    sign = "+" if mode.startswith("fee-plus") else "−"
    if mode.endswith("-maker") and D(text) == 0:
        return "$0 maker"
    return sign + "$" + money_digits(text)


def parse_shown(text, mode="plain"):
    """Displayed amount -> Decimal.

    Fee columns show their operator ("+$0.061" adds to cost, "−$1.1453" comes
    off the payout); that sign belongs to the column, not the amount, so for
    fee formats it's dropped. "$0 maker" is zero.
    """
    text = text.strip()
    if text == "$0 maker":
        return D(0)
    if mode.startswith("fee"):
        text = text.lstrip("+−")
    return D(text.replace("−", "-").replace("+", "").replace("$", ""))


def lookup(data, path):
    node = data
    for part in path.split("."):
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


# ---------- A tiny DOM tree from the dumped HTML ----------
class Node:
    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children = []
        self.parts = []

    def text(self):
        return "".join(part if isinstance(part, str) else part.text() for part in self.parts)

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def find_all(self, predicate):
        return [node for node in self.walk() if predicate(node)]

    def find(self, predicate):
        found = self.find_all(predicate)
        return found[0] if found else None


class TreeBuilder(html.parser.HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.root = Node("#root", {}, None)
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.current)
        self.current.children.append(node)
        self.current.parts.append(node)
        if tag not in self.VOID:
            self.current = node

    def handle_endtag(self, tag):
        node = self.current
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.current = node.parent

    def handle_data(self, data):
        self.current.parts.append(data)


def parse_dom(markup):
    builder = TreeBuilder()
    builder.feed(markup)
    return builder.root


def write_fixture(folder):
    """Fixture page + scripts + data.json (golden + parlay, real pipeline output) into folder."""
    dashboard, _fills = fx.full_dashboard()
    dashboard["updated"] = "2026-10-11T05:00:00Z"
    data = json.loads(json.dumps(dashboard))
    for name in ("index.html", "exact.js", "bets.js"):
        shutil.copy(os.path.join(kalshi_paths.REPO, "kalshi", name), os.path.join(folder, name))
    with open(os.path.join(folder, "data.json"), "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    return data


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        """Manual mode: the browser posts its rendered DOM here (?name=<view key>)."""
        parsed = urllib.parse.urlparse(self.path)
        name = urllib.parse.parse_qs(parsed.query).get("name", ["dom"])[0]
        if parsed.path != "/dom" or name not in list(VIEWS) + ["dom"]:
            self.send_error(404)
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode("utf-8")
        target = os.path.join(self.directory, "dom-{}.html".format(name))
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(body)
        self.send_response(204)
        self.end_headers()
        print("saved {} DOM to {}".format(name, target), flush=True)


class DisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = None
        cls.tmp = None
        cls.doms = {}
        captured = os.environ.get("KALSHI_DISPLAY_DOM_DIR")
        if captured:
            with open(os.path.join(captured, "data.json"), encoding="utf-8") as handle:
                cls.data = json.load(handle)
            for key in VIEWS:
                with open(os.path.join(captured, "dom-{}.html".format(key)), encoding="utf-8") as handle:
                    cls.doms[key] = parse_dom(handle.read())
            return

        chrome = find_chrome()
        if not chrome:
            if os.environ.get("CI"):
                raise AssertionError("CI needs Chrome/Chromium for the display test")
            raise unittest.SkipTest("no Chrome/Chromium installed")
        cls.tmp = tempfile.mkdtemp()
        cls.data = write_fixture(cls.tmp)
        handler = functools.partial(QuietHandler, directory=cls.tmp)
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        for key, view in VIEWS.items():
            url = "http://127.0.0.1:{}/index.html#{}".format(cls.server.server_address[1], view)
            profile = os.path.join(cls.tmp, "profile-" + key)
            try:
                result = subprocess.run(
                    [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
                     "--no-default-browser-check", "--use-mock-keychain", "--disable-extensions",
                     "--disable-background-networking", "--disable-component-update", "--window-size=1280,900",
                     # Hermetic: only the local fixture server resolves, so analytics and
                     # the Chart.js CDN fail fast instead of stalling virtual time.
                     "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
                     "--user-data-dir=" + profile, "--virtual-time-budget=10000", "--dump-dom", url],
                    capture_output=True, text=True, timeout=90 if os.environ.get("CI") else 40,
                )
            except subprocess.TimeoutExpired:
                cls.tearDownClass()
                if os.environ.get("CI"):
                    raise
                # Desktop Chrome on some Macs hangs in headless mode. Locally, say so
                # plainly and point at the --serve mode; in CI this is a failure.
                raise unittest.SkipTest("local headless Chrome hung; use --serve mode (see module docstring)")
            cls.doms[key] = parse_dom(result.stdout)

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.shutdown()
            cls.server = None
        if cls.tmp:
            shutil.rmtree(cls.tmp, ignore_errors=True)
            cls.tmp = None

    # ---------- helpers ----------
    def bet_rows(self, dom):
        return dom.find_all(lambda node: node.tag == "tr" and "data-row" in node.attrs)

    def fields_in(self, node):
        """{key: Decimal shown (or None for "—")} for the amounts inside node."""
        shown = {}
        for child in node.walk():
            if "data-field" in child.attrs:
                text = child.text().strip()
                key = child.attrs["data-field"].rsplit(".", 1)[-1]
                shown[key] = None if text == "—" else parse_shown(text, child.attrs.get("data-format", "plain"))
        return shown

    def state_rows(self, query):
        state = {"status": "all", "cats": [], "from": None, "to": None}
        for key, value in urllib.parse.parse_qsl(query):
            if key == "status":
                state["status"] = value
            if key == "cat":
                state["cats"] = value.split(",")
            if key in ("from", "to"):
                state[key] = value
        return py_filter(self.data["bets"], state)

    # ---------- checks ----------
    def test_every_view_rendered(self):
        for key, dom in self.doms.items():
            body = dom.find(lambda node: node.tag == "body")
            self.assertEqual(body.attrs.get("data-rendered"), "true", key)

    def test_every_shown_amount_is_the_stored_string(self):
        for key, dom in self.doms.items():
            fields = dom.find_all(lambda node: "data-field" in node.attrs)
            self.assertGreater(len(fields), 10, key)
            for node in fields:
                stored = lookup(self.data, node.attrs["data-field"])
                shown = node.text().strip()
                label = "{}: {}".format(key, node.attrs["data-field"])
                self.assertEqual(shown, display(stored, node.attrs["data-format"]), label)
                if stored is not None:
                    self.assertEqual(parse_shown(shown, node.attrs["data-format"]), D(stored), label)

    def test_every_row_adds_up_on_screen_including_open(self):
        rows = self.bet_rows(self.doms["all"])
        self.assertEqual(len(rows), len(self.data["bets"]))  # every bet ever, no limit
        for row in rows:
            shown = self.fields_in(row)
            label = row.attrs["data-row"]
            self.assertEqual(shown["stake"] + shown["buy_fees"], shown["cost"], label)
            if shown["payout"] is not None:
                self.assertEqual(shown["payout"] - shown["sell_fees"], shown["net_payout"], label)
                self.assertEqual(shown["net_payout"] - shown["cost"], shown["profit"], label)

    def test_fills_add_up_to_their_row_on_screen(self):
        dom = self.doms["all"]
        for row in self.bet_rows(dom):
            field = row.attrs["data-row"]
            shown = self.fields_in(row)
            detail = dom.find(lambda node: node.attrs.get("data-detail") == field)
            lines = detail.find_all(lambda node: node.tag == "tr" and "data-fill" in node.attrs)
            stake = buy_fees = payout = sell_fees = D(0)
            for line in lines:
                values = self.fields_in(line)
                action = line.attrs["data-action"]
                if action == "buy":
                    stake += values["amount"]
                    buy_fees += values["fee"]
                elif action == "sell":
                    payout += values["amount"]
                    sell_fees += values["fee"]
                else:  # settlement or live bid
                    payout += values["amount"]
            self.assertEqual(stake, shown["stake"], field)
            self.assertEqual(buy_fees, shown["buy_fees"], field)
            self.assertEqual(sell_fees, shown["sell_fees"], field)
            if shown["payout"] is not None:
                self.assertEqual(payout, shown["payout"], field)

    def test_footer_month_and_open_totals(self):
        names = ("stake", "buy_fees", "cost", "payout", "sell_fees", "net_payout", "profit")
        for key, view in VIEWS.items():
            if not view.startswith("bets"):
                continue
            dom = self.doms[key]
            rows = self.state_rows(view.partition("?")[2])
            expected = py_totals(rows)
            totals = {node.attrs["data-total"]: parse_shown(node.text(), node.attrs.get("data-format", "plain"))
                      for node in dom.walk() if "data-total" in node.attrs}
            footer = {name: totals["footer." + name] for name in names}
            for name in names:
                self.assertEqual(footer[name], D(expected[name]), "{} footer {}".format(key, name))
            self.assertEqual(footer["stake"] + footer["buy_fees"], footer["cost"], key)
            self.assertEqual(footer["payout"] - footer["sell_fees"], footer["net_payout"], key)
            self.assertEqual(footer["net_payout"] - footer["cost"], footer["profit"], key)

            months = {}
            for bet in rows:
                if bet["status"] != "open":
                    months.setdefault(bet["event_date"][:7], []).append(bet)
            for month, bets in months.items():
                self.assertEqual(totals["month.{}.profit".format(month)], D(py_totals(bets)["profit"]), "{} {}".format(key, month))
            opened = [bet for bet in rows if bet["status"] == "open"]
            if opened:
                self.assertEqual(totals["open.profit"], D(py_totals(opened)["profit"]), key)

    def test_all_time_footer_is_realized_plus_unrealized(self):
        summary = self.data["summary"]
        footer = self.doms["all"].find(lambda node: node.attrs.get("data-total") == "footer.profit")
        self.assertEqual(parse_shown(footer.text()), D(summary["realized_pnl"]) + D(summary["unrealized_pnl"]))
        opened = self.doms["open"].find(lambda node: node.attrs.get("data-total") == "footer.profit")
        self.assertEqual(parse_shown(opened.text()), D(summary["unrealized_pnl"]))

    def test_all_time_footer_minus_deposit_fee_is_the_headline(self):
        footer = self.doms["all"].find(lambda node: node.attrs.get("data-total") == "footer.profit")
        headline = self.doms["overview"].find(lambda node: node.attrs.get("id") == "netPnl")
        fee = self.doms["overview"].find(lambda node: node.attrs.get("data-field") == "summary.deposit_fees")
        self.assertEqual(parse_shown(footer.text(), "signed") - parse_shown(fee.text(), "plain"),
                         parse_shown(headline.text(), "signed"))
        self.assertEqual(parse_shown(headline.text(), "signed"), fx.FULL_NET)
        kalshi = self.doms["overview"].find(lambda node: node.attrs.get("id") == "kalshiLine").text()
        self.assertTrue(kalshi.startswith("Kalshi values open bets at $1.80; this page uses the current bid ($1.798)."), kalshi)

    def test_url_filter_state(self):
        open_dom = self.doms["open"]
        rows = self.bet_rows(open_dom)
        self.assertEqual(len(rows), self.data["summary"]["open"])
        self.assertTrue(all(row.attrs["data-outcome"] == "open" for row in rows))
        pressed = open_dom.find(lambda node: node.attrs.get("data-status") == "open")
        self.assertEqual(pressed.attrs.get("aria-pressed"), "true")

        lost = self.doms["lost_nfl"]
        self.assertEqual(len(self.bet_rows(lost)), len(self.state_rows("status=lost&cat=NFL")))
        cat = lost.find(lambda node: node.attrs.get("data-cat") == "NFL")
        self.assertEqual(cat.attrs.get("aria-pressed"), "true")

    def test_reset_to_all_time(self):
        dom = self.doms["since_sep"]
        reset = dom.find(lambda node: node.attrs.get("id") == "rangeReset")
        self.assertNotIn("hidden", reset.attrs)
        self.assertEqual(reset.attrs.get("href"), "#bets")
        label = dom.find(lambda node: node.attrs.get("id") == "rangeLabel").text()
        self.assertTrue(label.startswith("Showing: Custom range · Sep 1, 2026 → "), label)
        self.assertTrue(label.endswith(" · {} bets".format(len(self.state_rows("from=2026-09-01")))), label)
        all_dom = self.doms["all"]
        self.assertIn("hidden", all_dom.find(lambda node: node.attrs.get("id") == "rangeReset").attrs)
        self.assertTrue(all_dom.find(lambda node: node.attrs.get("id") == "rangeLabel").text().startswith(
            "Showing: All time · Dec 2, 2025 → "))

    def test_parlay_legs_render(self):
        dom = self.doms["all"]
        legs = dom.find(lambda node: "data-legs" in node.attrs)
        items = legs.find_all(lambda node: node.tag == "li")
        self.assertEqual([item.attrs["data-leg"] for item in items], ["hit", "hit", "missed"])
        self.assertTrue(items[0].text().startswith("✓ Ivory Coast (Yes): hit"), items[0].text())
        self.assertIn("✗ Netherlands (Yes): missed", items[2].text())
        self.assertIn("busted the parlay", items[2].text())
        self.assertIn("All legs must hit to win.", legs.parent.text())
        row = dom.find(lambda node: node.attrs.get("data-row") == legs.attrs["data-legs"])
        self.assertIn("Parlay · 3 legs", row.text())
        self.assertIn("WC", row.text())

    def test_sidebar_shows_account_value_on_every_view(self):
        summary = self.data["summary"]
        self.assertEqual(D(summary["account_value"]), D(summary["cash"]) + D(summary["open_value"]))
        for key, dom in self.doms.items():
            sidebar = dom.find(lambda node: node.attrs.get("id") == "sidebar")

            def shown(element_id):
                return sidebar.find(lambda node: node.attrs.get("id") == element_id).text().strip()

            self.assertEqual(shown("sideAccount"), display(summary["account_value"], "plain"), key)
            self.assertEqual(shown("sideCash"), display(summary["cash"], "plain"), key)
            self.assertEqual(shown("sideOpenLabel"), "Open at bid", key)
            self.assertEqual(shown("sideOpen"), display(summary["open_value"], "plain"), key)
            self.assertEqual(shown("sideNet"), display(summary["net_pnl"], "signed"), key)
            # The breakdown adds up on screen: cash + open at bid = account value.
            self.assertEqual(parse_shown(shown("sideCash")) + parse_shown(shown("sideOpen")), parse_shown(shown("sideAccount")), key)

    def test_overview_open_link_and_nav(self):
        dom = self.doms["overview"]
        link = dom.find(lambda node: node.attrs.get("id") == "openLink")
        self.assertEqual(link.attrs.get("href"), "#bets?status=open")
        self.assertNotIn("hidden", link.attrs)
        self.assertEqual(link.text().strip(), "1 open bet →")
        nav = [node.attrs.get("href") for node in dom.find_all(
            lambda node: node.tag == "a" and node.parent is not None and node.parent.attrs.get("id") == "nav")]
        self.assertEqual(nav, ["#overview", "#performance", "#bets", "#fees", "#about"])
        current = dom.find(lambda node: node.attrs.get("aria-current") == "page")
        self.assertEqual(current.attrs.get("href"), "#overview")
        bets_current = self.doms["all"].find(lambda node: node.attrs.get("aria-current") == "page")
        self.assertEqual(bets_current.attrs.get("href"), "#bets")


class DisplayRuleTests(unittest.TestCase):
    def test_parse_shown_treats_fee_signs_as_operators(self):
        self.assertEqual(parse_shown("−$1.1453", "fee-minus"), D("1.1453"))
        self.assertEqual(parse_shown("+$0.061", "fee-plus"), D("0.061"))
        self.assertEqual(parse_shown("−$4.9985", "signed"), D("-4.9985"))
        self.assertEqual(parse_shown("$0 maker", "fee-minus-maker"), D(0))

    def test_rule(self):
        self.assertEqual(display("2", "plain"), "$2.00")
        self.assertEqual(display("1.997", "plain"), "$1.997")
        self.assertEqual(display("1.4878", "signed"), "+$1.4878")
        self.assertEqual(display("-4.9985", "signed"), "−$4.9985")
        self.assertEqual(display("0", "signed"), "$0.00")
        self.assertEqual(display("0.061", "fee-plus"), "+$0.061")
        self.assertEqual(display("1.1453", "fee-minus"), "−$1.1453")
        self.assertEqual(display("0", "fee-minus-maker"), "$0 maker")
        self.assertEqual(display("0", "fee-minus"), "−$0.00")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        port = int(sys.argv[sys.argv.index("--serve") + 1])
        folder = tempfile.mkdtemp(prefix="kalshi-display-")
        write_fixture(folder)
        print("serving fixture from " + folder, flush=True)
        http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(QuietHandler, directory=folder)).serve_forever()
    else:
        unittest.main()
