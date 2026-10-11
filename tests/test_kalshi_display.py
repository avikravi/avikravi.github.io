"""Headless render of kalshi/index.html against a fixture data.json.

Checks, with no tolerance:
  - every amount the page shows (each element with data-field) equals the
    stored string, formatted by the display rule (an independent Python
    implementation below: trailing zeros trimmed, at least 2 decimals);
  - every finished-bet row visibly adds up: shown payout - shown cost == shown profit;
  - nothing on the page is a rounded version of a longer stored value.

Needs Google Chrome/Chromium. Skipped locally if none is installed; in CI
(env CI set, as on GitHub Actions) a missing browser is a failure.

Without a usable headless Chrome (e.g. a desktop Mac where it hangs), render
it in any real browser instead:
    python3 tests/test_kalshi_display.py --serve 8765
    open http://localhost:8765/index.html#bets, then POST the DOM back:
      fetch('/dom', {method: 'POST', body: document.documentElement.outerHTML})
    KALSHI_DISPLAY_DOM=<printed dom.html path> python3 -m unittest discover -s tests -p test_kalshi_display.py
The same assertions then run against that captured DOM.
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
from decimal import Decimal

import kalshi_fixtures as fx
import kalshi_paths

D = Decimal
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


def display(text, mode):
    """The page's money display rule, re-implemented independently."""
    if text is None:
        return "—"
    negative = text.startswith("-") and D(text) != 0
    body = text.lstrip("+-")
    whole, _dot, frac = body.partition(".")
    whole = whole.lstrip("0") or "0"
    frac = frac.rstrip("0").ljust(2, "0")
    shown = "$" + whole + "." + frac
    if mode == "signed":
        return shown if D(text) == 0 else ("−" if negative else "+") + shown
    return ("−" if negative else "") + shown


def parse_shown(text):
    return D(text.replace("−", "-").replace("+", "").replace("$", ""))


def lookup(data, path):
    node = data
    for part in path.split("."):
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


class FieldCollector(html.parser.HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.fields = []  # (field, format, text)
        self.rendered = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "body" and attrs.get("data-rendered") == "true":
            self.rendered = True
        if tag in self.VOID:
            return
        self.stack.append([tag, attrs, []])

    def handle_endtag(self, tag):
        if tag in self.VOID or not self.stack:
            return
        while self.stack:
            open_tag, attrs, parts = self.stack.pop()
            text = "".join(parts)
            if self.stack:
                self.stack[-1][2].append(text)
            if "data-field" in attrs:
                self.fields.append((attrs["data-field"], attrs.get("data-format"), text.strip()))
            if open_tag == tag:
                break

    def handle_data(self, data):
        if self.stack:
            self.stack[-1][2].append(data)


def write_fixture(folder):
    """Fixture page + data.json (the golden pipeline output) into folder; returns the data."""
    dashboard, _fills = fx.golden_dashboard()
    dashboard["updated"] = "2026-10-11T05:00:00Z"
    data = json.loads(json.dumps(dashboard))
    shutil.copy(os.path.join(kalshi_paths.REPO, "kalshi", "index.html"), os.path.join(folder, "index.html"))
    with open(os.path.join(folder, "data.json"), "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    return data


class DisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        captured = os.environ.get("KALSHI_DISPLAY_DOM")
        if captured:
            cls.server = None
            cls.tmp = None
            with open(os.path.join(os.path.dirname(captured), "data.json"), encoding="utf-8") as handle:
                cls.data = json.load(handle)
            cls.collector = FieldCollector()
            with open(captured, encoding="utf-8") as handle:
                cls.collector.feed(handle.read())
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
        url = "http://127.0.0.1:{}/index.html#bets".format(cls.server.server_address[1])

        profile = os.path.join(cls.tmp, "profile")
        try:
            result = subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
                 "--no-default-browser-check", "--use-mock-keychain", "--disable-extensions",
                 "--disable-background-networking", "--disable-component-update",
                 # Hermetic: only the local fixture server resolves, so analytics and
                 # the Chart.js CDN fail fast instead of stalling virtual time. Every
                 # amount checked here is in the DOM tables, which don't need Chart.js.
                 "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
                 "--user-data-dir=" + profile, "--virtual-time-budget=10000", "--dump-dom", url],
                capture_output=True, text=True, timeout=90 if os.environ.get("CI") else 40,
            )
        except subprocess.TimeoutExpired:
            cls.server.shutdown()
            shutil.rmtree(cls.tmp, ignore_errors=True)
            if os.environ.get("CI"):
                raise
            # Desktop Chrome on some Macs hangs in headless mode. Locally, say so
            # plainly and point at the --serve mode; in CI this is a failure.
            raise unittest.SkipTest("local headless Chrome hung; use --serve mode (see module docstring)")
        collector = FieldCollector()
        collector.feed(result.stdout)
        cls.collector = collector

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.shutdown()
        if cls.tmp:
            shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_page_rendered(self):
        self.assertTrue(self.collector.rendered, "page never finished rendering data.json")

    def test_every_shown_amount_is_the_stored_string(self):
        fields = self.collector.fields
        self.assertGreaterEqual(len(fields), 40, "too few amounts found on the page")
        for field, mode, shown in fields:
            stored = lookup(self.data, field)
            self.assertEqual(shown, display(stored, mode), field)
            if stored is not None:
                self.assertEqual(parse_shown(shown), D(stored), "shown value is not exactly the stored value: " + field)

    def test_every_finished_row_adds_up_on_screen(self):
        rows = {}
        for field, _mode, shown in self.collector.fields:
            if field.startswith("recent_bets."):
                _prefix, index, key = field.split(".")
                rows.setdefault(index, {})[key] = shown
        self.assertEqual(len(rows), len(self.data["recent_bets"]))
        for index, row in rows.items():
            self.assertEqual(parse_shown(row["payout"]) - parse_shown(row["cost"]), parse_shown(row["profit"]),
                             "row {} does not add up as shown: {}".format(index, row))

    def test_golden_values_appear_exactly(self):
        shown = {field: text for field, _mode, text in self.collector.fields}
        robinson = [bet["title"] for bet in self.data["recent_bets"]].index("Bijan Robinson TD")
        prefix = "recent_bets.{}.".format(robinson)
        self.assertEqual((shown[prefix + "cost"], shown[prefix + "payout"], shown[prefix + "profit"]),
                         ("$1.997", "$3.4848", "+$1.4878"))
        self.assertEqual(shown["summary.net_pnl"], "+$11.553")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        """Manual mode: the browser posts its rendered DOM here."""
        if self.path != "/dom":
            self.send_error(404)
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode("utf-8")
        target = os.path.join(self.directory, "dom.html")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(body)
        self.send_response(204)
        self.end_headers()
        print("saved rendered DOM to " + target, flush=True)


class DisplayRuleTests(unittest.TestCase):
    def test_rule(self):
        self.assertEqual(display("2", "plain"), "$2.00")
        self.assertEqual(display("1.997", "plain"), "$1.997")
        self.assertEqual(display("3.4848", "plain"), "$3.4848")
        self.assertEqual(display("1.4878", "signed"), "+$1.4878")
        self.assertEqual(display("-4.9985", "signed"), "−$4.9985")
        self.assertEqual(display("0", "signed"), "$0.00")
        self.assertEqual(display("12.280", "plain"), "$12.28")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        port = int(sys.argv[sys.argv.index("--serve") + 1])
        folder = tempfile.mkdtemp(prefix="kalshi-display-")
        write_fixture(folder)
        print("serving fixture from " + folder, flush=True)
        http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(QuietHandler, directory=folder)).serve_forever()
    else:
        unittest.main()
