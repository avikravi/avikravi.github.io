"""Fetch Avi's Kalshi portfolio from the Trade API v2 and write kalshi/data.json.

Runs in GitHub Actions (.github/workflows/kalshi.yml). Needs two env vars,
supplied from repo secrets:
    KALSHI_API_KEY_ID    the key ID shown when the API key was created
    KALSHI_PRIVATE_KEY   the full PEM private key (RSA or Ed25519)

Auth (docs.kalshi.com, "API Keys"): every request carries
    KALSHI-ACCESS-KEY        key ID
    KALSHI-ACCESS-TIMESTAMP  milliseconds since epoch
    KALSHI-ACCESS-SIGNATURE  base64(sign(timestamp + METHOD + path))
where path includes /trade-api/v2 and excludes the query string. RSA keys sign
with RSA-PSS / SHA-256 / MGF1-SHA-256 / salt = digest length; Ed25519 keys
sign the message directly.

THIS REPO IS PUBLIC, SO ITS ACTION LOGS ARE TOO. This script never prints
credentials, request headers, or response bodies. Errors print only the HTTP
status and the endpoint path.
"""

import base64
import os
import sys
import time

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa

from kalshi_common import build_dashboard, group_fills, make_bet, parse_time, write_if_changed

API_HOST = os.environ.get("KALSHI_API_HOST", "https://external-api.kalshi.com")
API_PREFIX = "/trade-api/v2"
PAGE_LIMIT = 1000


class KalshiClient:
    def __init__(self, key_id, private_key_pem):
        self.key_id = key_id
        # Secrets pasted as one line sometimes arrive with literal "\n".
        pem_text = private_key_pem.replace("\\n", "\n").strip().encode()
        self.private_key = serialization.load_pem_private_key(pem_text, password=None)
        self.session = requests.Session()

    def _sign(self, message):
        if isinstance(self.private_key, rsa.RSAPrivateKey):
            signature = self.private_key.sign(
                message,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
                hashes.SHA256(),
            )
        elif isinstance(self.private_key, ed25519.Ed25519PrivateKey):
            signature = self.private_key.sign(message)
        else:
            raise SystemExit("KALSHI_PRIVATE_KEY must be an RSA or Ed25519 private key")
        return base64.b64encode(signature).decode()

    def get(self, endpoint, params=None, allow_missing=False):
        path = API_PREFIX + endpoint
        for attempt in range(4):
            stamp = str(int(time.time() * 1000))
            headers = {
                "KALSHI-ACCESS-KEY": self.key_id,
                "KALSHI-ACCESS-TIMESTAMP": stamp,
                "KALSHI-ACCESS-SIGNATURE": self._sign((stamp + "GET" + path).encode()),
            }
            resp = self.session.get(API_HOST + path, headers=headers, params=params, timeout=30)
            if resp.status_code == 429 and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            break
        if allow_missing and resp.status_code == 404:
            return None
        if resp.status_code != 200:
            # Status and path only: never echo the body or headers.
            raise SystemExit("Kalshi API error {} on {}".format(resp.status_code, endpoint))
        return resp.json()

    def paginate(self, endpoint, list_key, extra=None):
        items = []
        cursor = ""
        while True:
            params = {"limit": PAGE_LIMIT}
            params.update(extra or {})
            if cursor:
                params["cursor"] = cursor
            page = self.get(endpoint, params)
            items.extend(page.get(list_key) or [])
            cursor = page.get("cursor") or ""
            if not cursor:
                return items


def normalize_fill(raw):
    # outcome_side is the exposure gained: selling Yes reports "no", priced at
    # no_price_dollars. The deprecated side/action pair reports that same sale
    # as side "yes", action "sell", so flip it when falling back.
    side = raw.get("outcome_side")
    if not side:
        side = raw.get("side")
        if raw.get("action") == "sell":
            side = "no" if side == "yes" else "yes"
    price_key = "yes_price_dollars" if side == "yes" else "no_price_dollars"
    stamp = raw.get("created_time")
    moment = parse_time(stamp) if stamp else parse_time(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(raw["ts"])))
    return {
        "fill_key": raw.get("fill_id") or raw.get("trade_id"),
        "ticker": raw.get("ticker") or raw.get("market_ticker"),
        "side": side,
        "count": float(raw.get("count_fp") or 0),
        "price": float(raw.get(price_key) or 0),
        "fee": float(raw.get("fee_cost") or 0),
        "is_taker": bool(raw.get("is_taker")),
        "time": moment,
    }


def fetch_fills(client):
    """Live fills plus anything already moved to the historical archive."""
    raw = client.paginate("/portfolio/fills", "fills")
    raw += client.paginate("/historical/fills", "fills")
    seen = set()
    fills = []
    for item in raw:
        fill = normalize_fill(item)
        if fill["fill_key"] in seen:
            continue
        seen.add(fill["fill_key"])
        del fill["fill_key"]  # used only for de-duping, never written out
        fills.append(fill)
    return fills


def market_info(client, ticker):
    """Readable title, result and a mark price for one market."""
    data = client.get("/markets/" + ticker, allow_missing=True)
    if data is None:
        data = client.get("/historical/markets/" + ticker, allow_missing=True)
    market = (data or {}).get("market") or {}

    title = market.get("title") or ""
    event_ticker = market.get("event_ticker")
    if not title and event_ticker:
        event = client.get("/events/" + event_ticker, allow_missing=True) or {}
        title = (event.get("event") or {}).get("title") or ""
    sub_title = market.get("yes_sub_title") or ""
    if sub_title and sub_title.lower() not in title.lower():
        title = "{}: {}".format(title, sub_title) if title else sub_title
    return {
        "title": title or "Kalshi market",
        "result": market.get("result") or "",
        "yes_bid": market.get("yes_bid_dollars"),
        "no_bid": market.get("no_bid_dollars"),
    }


def main():
    key_id = os.environ.get("KALSHI_API_KEY_ID", "").strip()
    private_key = os.environ.get("KALSHI_PRIVATE_KEY", "")
    if not key_id or not private_key:
        raise SystemExit("KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY must be set")

    client = KalshiClient(key_id, private_key)

    balance = client.get("/portfolio/balance")
    cash = balance["balance"] / 100
    portfolio_value = balance["portfolio_value"] / 100

    fills = fetch_fills(client)
    settlements = {
        item["ticker"]: item for item in client.paginate("/portfolio/settlements", "settlements")
    }
    held = {
        item["ticker"]: float(item.get("position_fp") or 0)
        for item in client.paginate("/portfolio/positions", "market_positions", {"count_filter": "position"})
    }

    bets = []
    for entry in group_fills(fills):
        ticker = entry["ticker"]
        info = market_info(client, ticker)
        settlement = settlements.get(ticker)
        payout = None
        resolved_time = None
        if settlement is not None:
            payout = settlement["revenue"] / 100
            resolved_time = parse_time(settlement["settled_time"])
        elif info["result"] in ("yes", "no"):
            # Archived out of /portfolio/settlements: winning contracts pay $1.
            remaining = entry["count"][info["result"]] - entry["count"]["no" if info["result"] == "yes" else "yes"]
            payout = max(remaining, 0.0)
            resolved_time = entry["last_time"]

        position = held.get(ticker, 0.0)
        is_open = payout is None and abs(position) > 0
        open_value = None
        if is_open:
            # Value = contracts x the current BID for the side held (yes_bid for
            # a YES position, no_bid for NO): what selling right now would
            # actually fetch. Mid flatters thin markets with wide spreads, and
            # last-trade can be hours stale. No bid -> leave it blank ("—").
            bid = info["yes_bid"] if position > 0 else info["no_bid"]
            open_value = abs(position) * float(bid) if bid not in (None, "") else None
        bets.append(make_bet(entry, info["title"], payout, resolved_time, is_open, open_value))

    dashboard = build_dashboard(
        bets,
        fills,
        cash=cash,
        open_value=portfolio_value,
        source="api",
        fee_source="api_fee_cost",
        series_note="Cumulative profit of settled and sold bets by date; the last point is today's "
        "net P&L including open positions.",
    )
    wrote = write_if_changed(dashboard)
    summary = dashboard["summary"]
    # Aggregate counts only: safe for a public log.
    print("data.json {}".format("updated" if wrote else "unchanged"))
    print("bets={bets} resolved={resolved} pending={pending} open={open}".format(**summary))


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        # Exception text can include the URL but never headers; keep it terse anyway.
        sys.exit("Network error talking to Kalshi: {}".format(type(exc).__name__))
