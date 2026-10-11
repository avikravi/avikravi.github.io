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
import re
import sys
import time
from datetime import datetime, timezone

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa

from kalshi_common import (
    CREDITS,
    DEPOSITS,
    TITLE_MAX,
    TITLE_OVERRIDES,
    WORLD_CUP_PARLAYS,
    build_dashboard,
    category_for,
    group_fills,
    make_bet,
    parse_time,
    write_if_changed,
)

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


# A title that is only "<team> wins": no colon, no "at"/"vs" naming an opponent.
BARE_WINNER = re.compile(r"^(?P<team>[^:]+?) wins?$", re.IGNORECASE)
# Parlay titles come back as "yes Ivory Coast,yes Germany,yes Netherlands".
PARLAY_LEG = re.compile(r"^\s*(yes|no)\s+(.+?)\s*$", re.IGNORECASE)
TO_ADVANCE = re.compile(r":\s*To Advance:\s*", re.IGNORECASE)
HAS_OPPONENT = re.compile(r"\b(at|vs\.?|v\.?)\b", re.IGNORECASE)


def clean_event_title(title):
    """'Boston at Houston Winner?' -> 'Boston at Houston'."""
    cleaned = re.sub(r"\s*(winner)?\s*\?$", "", title.strip(), flags=re.IGNORECASE)
    return cleaned.strip()


def clip_title(title, limit=TITLE_MAX):
    return title if len(title) <= limit else title[: limit - 1].rstrip(" ,") + "…"


def parlay_title(ticker, market, title):
    """"yes X,yes Y,no Z" -> "Parlay: X, Y, not Z" ("WC Parlay" if every leg is World Cup).

    Returns None when the title isn't a list of yes/no legs.
    """
    parts = title.split(",")
    if len(parts) < 2:
        return None
    legs = []
    for part in parts:
        leg = PARLAY_LEG.match(part)
        if not leg:
            return None
        legs.append(leg.group(2) if leg.group(1).lower() == "yes" else "not " + leg.group(2))

    leg_tickers = [leg.get("market_ticker") or "" for leg in market.get("mve_selected_legs") or []]
    if leg_tickers:
        world_cup = all(code.upper().startswith("KXWC") for code in leg_tickers)
    else:
        world_cup = ticker in WORLD_CUP_PARLAYS
    return clip_title(("WC Parlay: " if world_cup else "Parlay: ") + ", ".join(legs))


def readable_title(ticker, market, event_title_lookup):
    """Override map first, then the API title, with the opponent added to a bare "X wins"."""
    if ticker in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[ticker]

    title = market.get("title") or ""
    if not title:
        title = event_title_lookup() or ""
    sub_title = market.get("yes_sub_title") or ""
    if sub_title and sub_title.lower() not in title.lower():
        title = "{}: {}".format(title, sub_title) if title else sub_title

    # "USA vs Bosnia: To Advance: USA advances" -> "USA vs Bosnia: USA advances"
    title = TO_ADVANCE.sub(": ", title)

    parlay = parlay_title(ticker, market, title)
    if parlay:
        return parlay

    # "Houston wins" says nothing about who they played: prefix the event.
    bare = BARE_WINNER.match(title)
    if bare and not HAS_OPPONENT.search(bare.group("team")):
        event = clean_event_title(event_title_lookup() or "")
        if event and event.lower() != title.lower():
            title = "{}: {}".format(event, title)
    return title or "Kalshi market"


def category_from_legs(market):
    """A parlay takes its legs' category when every leg agrees (e.g. all World Cup -> Soccer)."""
    legs = market.get("mve_selected_legs") or []
    names = {category_for(leg.get("market_ticker") or "") for leg in legs}
    if len(names) == 1:
        name = names.pop()
        return None if name == "Other" else name
    return None


def market_info(client, ticker):
    """Readable title, category, result, timing and bids for one market."""
    data = client.get("/markets/" + ticker, allow_missing=True)
    if data is None:
        data = client.get("/historical/markets/" + ticker, allow_missing=True)
    market = (data or {}).get("market") or {}

    event_cache = {}

    def event_title_lookup():
        event_ticker = market.get("event_ticker")
        if not event_ticker:
            return ""
        if "title" not in event_cache:
            event = client.get("/events/" + event_ticker, allow_missing=True) or {}
            event_cache["title"] = (event.get("event") or {}).get("title") or ""
        return event_cache["title"]

    return {
        "title": readable_title(ticker, market, event_title_lookup),
        "category": category_from_legs(market),
        "result": market.get("result") or "",
        "settlement_ts": market.get("settlement_ts"),
        "close_time": market.get("close_time"),
        "yes_bid": market.get("yes_bid_dollars"),
        "no_bid": market.get("no_bid_dollars"),
    }


def resolution_time(settlement, info, entry, now):
    """Best-known settlement moment and where it came from.

    Order: the portfolio settlement record, the market's settlement_ts, the
    market's close_time (ignored if it's in the future), then the bet's last
    fill as a last resort.
    """
    if settlement is not None and settlement.get("settled_time"):
        return parse_time(settlement["settled_time"]), "settlement"
    if info.get("settlement_ts"):
        return parse_time(info["settlement_ts"]), "market_settlement_ts"
    if info.get("close_time"):
        closed = parse_time(info["close_time"])
        if closed <= now:
            return closed, "market_close_time"
    return entry["last_time"], "last_fill"


RECONCILE_TOLERANCE = 0.05


class ReconciliationError(SystemExit):
    """Raised (exit code 1) when API data doesn't add up; data.json is left alone."""


def expected_cash(fills, settlement_payouts):
    """Cash the account should hold, from API data alone.

    deposits + credits + sale proceeds + settlement payouts - purchase costs - all fees

    Every fill is recorded as a buy of its side (selling YES at P is buying NO
    at 1 - P), so "sale proceeds - purchase costs" is computed as
    (matched YES+NO pairs x $1) - (every fill's count x price). The two forms
    are the same money; this one needs no buy/sell flag.
    """
    money_in = sum(row["amount"] for row in DEPOSITS) + sum(row["amount"] for row in CREDITS)
    deposit_fees = sum(row["fee"] for row in DEPOSITS)
    spent = sum(fill["count"] * fill["price"] for fill in fills)
    trading_fees = sum(fill["fee"] for fill in fills)
    pair_payouts = sum(min(entry["count"]["yes"], entry["count"]["no"]) for entry in group_fills(fills))
    return money_in + pair_payouts + sum(settlement_payouts) - spent - trading_fees - deposit_fees


def reconcile(dashboard, fills, settlement_payouts, actual_cash, portfolio_value):
    """Block the write unless the numbers add up. Returns the success line.

    Failure messages carry only the compared totals and their difference.
    """
    expected = expected_cash(fills, settlement_payouts)
    cash_diff = actual_cash - expected
    if abs(cash_diff) > RECONCILE_TOLERANCE:
        raise ReconciliationError(
            "Reconciliation failed: expected cash ${:.2f}, actual cash ${:.2f}, diff ${:+.2f}. "
            "data.json not updated.".format(expected, actual_cash, cash_diff)
        )

    money_in = sum(row["amount"] for row in DEPOSITS) + sum(row["amount"] for row in CREDITS)
    expected_net = actual_cash + portfolio_value - money_in
    published_net = dashboard["summary"]["net_pnl"]
    net_diff = published_net - expected_net
    if abs(net_diff) > RECONCILE_TOLERANCE:
        raise ReconciliationError(
            "Reconciliation failed: expected net P&L ${:+.2f}, dashboard net P&L ${:+.2f}, diff ${:+.2f}. "
            "data.json not updated.".format(expected_net, published_net, net_diff)
        )
    return "reconciled: cash diff ${:.2f}, net {}${:.2f}".format(
        abs(cash_diff), "+" if published_net >= 0 else "-", abs(published_net)
    )


def build_from_api(client):
    """Fetch everything and build the dashboard. Writes nothing.

    Returns (dashboard, fills, settlement_payouts, cash, portfolio_value).
    """
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
    settlement_payouts = []
    resolution_sources = {}
    now = datetime.now(timezone.utc)
    for entry in group_fills(fills):
        ticker = entry["ticker"]
        info = market_info(client, ticker)
        settlement = settlements.get(ticker)
        payout = None
        resolved_time = None
        if settlement is not None:
            payout = settlement["revenue"] / 100
        elif info["result"] in ("yes", "no"):
            # Archived out of /portfolio/settlements: winning contracts pay $1.
            remaining = entry["count"][info["result"]] - entry["count"]["no" if info["result"] == "yes" else "yes"]
            payout = max(remaining, 0.0)
        if payout is not None:
            settlement_payouts.append(payout)
            resolved_time, source_name = resolution_time(settlement, info, entry, now)
            # Bets sold off before settlement resolve on their sale date (make_bet),
            # so only count the ones that actually rode to settlement.
            if abs(entry["count"]["yes"] - entry["count"]["no"]) >= 0.005:
                resolution_sources[source_name] = resolution_sources.get(source_name, 0) + 1

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
        bets.append(make_bet(entry, info["title"], payout, resolved_time, is_open, open_value, info["category"]))

    dashboard = build_dashboard(
        bets,
        fills,
        cash=cash,
        open_value=portfolio_value,
        source="api",
        fee_source="api_fee_cost",
        series_note="One step per day: bets count on the day they settled or were sold. "
        "The last step is today, with open positions at Kalshi's value.",
        resolution_sources=resolution_sources,
    )
    return dashboard, fills, settlement_payouts, cash, portfolio_value


def run(client, writer=write_if_changed):
    """Build, reconcile, then write. A failed reconciliation never reaches writer."""
    dashboard, fills, settlement_payouts, cash, portfolio_value = build_from_api(client)
    line = reconcile(dashboard, fills, settlement_payouts, cash, portfolio_value)
    wrote = writer(dashboard)
    # One line, aggregates only: safe for a public log.
    print("{} ({})".format(line, "data.json updated" if wrote else "data.json unchanged"))


def main():
    key_id = os.environ.get("KALSHI_API_KEY_ID", "").strip()
    private_key = os.environ.get("KALSHI_PRIVATE_KEY", "")
    if not key_id or not private_key:
        raise SystemExit("KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY must be set")
    run(KalshiClient(key_id, private_key))


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        # Exception text can include the URL but never headers; keep it terse anyway.
        sys.exit("Network error talking to Kalshi: {}".format(type(exc).__name__))
