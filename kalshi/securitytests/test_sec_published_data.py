"""kalshi/data.json is public: it must hold no account, order or market identifiers.

kalshi_common's contract: no order ID, fill ID, market ticker/ID or account
identifier ever reaches data.json. These tests enforce it on the live file.
"""

import json
import re
import unittest

import sec_helpers as helpers

FORBIDDEN_KEYS = {
    "order_id", "client_order_id", "trade_id", "fill_id", "member_id", "user_id", "account_id",
    "ticker", "market_ticker", "event_ticker", "series_ticker", "key_id", "api_key", "private_key",
    "signature", "token", "access_token", "email", "password", "secret",
}
UUID_PATTERN = helpers.SECRET_PATTERNS["UUID (Kalshi API key IDs and order IDs are UUIDs)"]
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Kalshi market/event tickers look like KXNFLRECYDS-26OCT12BUFLAR-... or KXWCGAME-26JUN25-CIV.
TICKER_PATTERN = re.compile(r"\bKX[A-Z0-9]{2,}-[0-9]{2}[A-Z]{3}[0-9]{2}")


def walk(node, path="$"):
    """Yield (json path, key or None, value) for every key and leaf in the document."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield path, key, value
            yield from walk(value, "{}.{}".format(path, key))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from walk(item, "{}[{}]".format(path, index))
    else:
        yield path, None, node


class PublishedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(helpers.DATA_JSON, encoding="utf-8") as handle:
            cls.raw = handle.read()
        cls.data = json.loads(cls.raw)

    def test_no_identifier_keys(self):
        bad = sorted({"{}.{}".format(path, key) for path, key, _ in walk(self.data)
                      if key is not None and (key.lower() in FORBIDDEN_KEYS or "secret" in key.lower())})
        self.assertEqual(bad, [], "identifier keys in public data.json: {}".format(bad))

    def test_no_uuids(self):
        self.assertIsNone(UUID_PATTERN.search(self.raw), "a UUID (order/key ID?) is in data.json")

    def test_no_market_tickers(self):
        found = TICKER_PATTERN.search(self.raw)
        self.assertIsNone(found, "a Kalshi ticker is in data.json near offset {}".format(
            found.start() if found else None))

    def test_no_email_addresses(self):
        self.assertIsNone(EMAIL_PATTERN.search(self.raw), "an email address is in data.json")

    def test_no_secret_patterns(self):
        self.assertEqual(helpers.find_secrets(self.raw), [])

    def test_detectors_catch_planted_identifiers(self):
        # The checks above are only meaningful if they would catch a leak.
        fake_uuid = "-".join(["0f1e2d3c", "4b5a", "6978", "8a9b", "0c1d2e3f4a5b"])
        planted = {"bets": [{"title": "x", "order_id": fake_uuid, "ticker": "KXNFLRECYDS-" + "26OCT12BUFLAR"}]}
        raw = json.dumps(planted)
        keys = {key for _, key, _ in walk(planted) if key}
        self.assertTrue(keys & FORBIDDEN_KEYS)
        self.assertIsNotNone(UUID_PATTERN.search(raw))
        self.assertIsNotNone(TICKER_PATTERN.search(raw))


if __name__ == "__main__":
    unittest.main()
