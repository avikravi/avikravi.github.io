"""The public dashboard page must never talk to Kalshi or hold credentials.

The browser only reads the already-sanitized data.json. If the page ever
called Kalshi directly, the key would have to be in the page, i.e. public.
"""

import os
import re
import unittest

import sec_helpers as helpers

PAGE_FILES = ["index.html", "bets.js", "exact.js"]


def read_page(name):
    with open(os.path.join(helpers.KALSHI_DIR, name), encoding="utf-8") as handle:
        return handle.read()


class PageTests(unittest.TestCase):
    def test_page_never_calls_kalshi(self):
        for name in PAGE_FILES:
            text = read_page(name).lower()
            with self.subTest(file=name):
                for marker in ("kalshi-access", "trade-api", "external-api.kalshi", "api.elections.kalshi"):
                    self.assertNotIn(marker, text)

    def test_only_network_read_is_data_json(self):
        for name in PAGE_FILES:
            text = read_page(name)
            with self.subTest(file=name):
                fetches = re.findall(r"fetch\(\s*['\"]([^'\"]+)['\"]", text)
                self.assertTrue(all(url == "data.json" for url in fetches), fetches)
                self.assertNotIn("XMLHttpRequest", text)
                self.assertNotIn("WebSocket(", text)
                self.assertNotRegex(text, r"\b(localStorage|sessionStorage)\.setItem\([^)]*(key|token|secret)",
                                    "credentials must never be stored in the browser")

    def test_external_scripts_are_https(self):
        sources = re.findall(r"<script[^>]*\ssrc=['\"]([^'\"]+)['\"]", read_page("index.html"))
        external = [src for src in sources if "//" in src]
        self.assertTrue(external, "expected at least the chart library")
        self.assertEqual([src for src in external if not src.startswith("https://")], [])

    def test_no_secret_patterns_in_page_files(self):
        for name in PAGE_FILES:
            with self.subTest(file=name):
                self.assertEqual(helpers.find_secrets(read_page(name)), [])


if __name__ == "__main__":
    unittest.main()
