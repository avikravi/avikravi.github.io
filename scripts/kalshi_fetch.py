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
    ONE,
    dec_str,
    to_decimal,
    TITLE_OVERRIDES,
    WORLD_CUP_PARLAYS,
    build_dashboard,
    category_for,
    group_fills,
    make_bet,
    parse_time,
    write_if_changed,
)
from kalshi_rules import CENT, DOCUMENTED_PRECISIONS, ZERO, apply_fee_rounding, decimal_places, is_on_grid

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
    fill_key = raw.get("fill_id") or raw.get("trade_id")
    count_text = raw.get("count_fp") or "0"
    price_text = raw.get(price_key) or "0"
    fee_text = raw.get("fee_cost") or "0"
    return {
        "fill_key": fill_key,
        # Internal only (fee-rounding accumulator is per order); never written out.
        "order_key": raw.get("order_id") or fill_key,
        "ticker": raw.get("ticker") or raw.get("market_ticker"),
        "side": side,
        # Exact Decimals straight from Kalshi's strings.
        "count": to_decimal(count_text),
        "price": to_decimal(price_text),
        "fee_reported": to_decimal(fee_text),
        "is_taker": bool(raw.get("is_taker")),
        "time": moment,
        "seq": raw.get("ts") or 0,
        "places": {"count": decimal_places(count_text), "price": decimal_places(price_text), "fee": decimal_places(fee_text)},
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
    # Fees are set later by choose_balance_precision() / apply_fee_rounding().
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


def title_legs(title):
    """"yes X,yes Y,no Z" -> [("yes", "X"), ("yes", "Y"), ("no", "Z")]; None if it isn't a parlay title."""
    parts = title.split(",")
    if len(parts) < 2:
        return None
    legs = []
    for part in parts:
        leg = PARLAY_LEG.match(part)
        if not leg:
            return None
        legs.append((leg.group(1).lower(), leg.group(2)))
    return legs


def leg_result(side, settlement_value, leg_market):
    """hit / missed / unknown for one parlay leg.

    Kalshi's mve_selected_legs[].yes_settlement_value_dollars is the YES payout
    of that leg once determined ($1 or $0); a YES leg hits on $1, a NO leg on
    $0. Falls back to the leg market's own result, else unknown.
    """
    if settlement_value not in (None, ""):
        yes_paid = to_decimal(settlement_value) == ONE
        return "hit" if yes_paid == (side == "yes") else "missed"
    result = (leg_market or {}).get("result") or ""
    if result in ("yes", "no"):
        return "hit" if result == side else "missed"
    return "unknown"


def parlay_details(client, ticker, market, title):
    """(legs, world_cup) for a parlay, or None. Legs carry only name, side and result (no tickers)."""
    raw_legs = market.get("mve_selected_legs") or []
    if raw_legs:
        legs = []
        for index, leg in enumerate(raw_legs):
            side = (leg.get("side") or "yes").lower()
            leg_market = lookup_market(client, leg.get("market_ticker") or "")
            name = leg_market.get("yes_sub_title") or leg_market.get("title") or "Leg {}".format(index + 1)
            legs.append({"name": name, "side": side.capitalize(),
                         "result": leg_result(side, leg.get("yes_settlement_value_dollars"), leg_market)})
        world_cup = all((leg.get("market_ticker") or "").upper().startswith("KXWC") for leg in raw_legs)
        return legs, world_cup
    parsed = title_legs(title)
    if parsed:
        legs = [{"name": name, "side": side.capitalize(), "result": "unknown"} for side, name in parsed]
        return legs, ticker in WORLD_CUP_PARLAYS
    return None


def lookup_market(client, ticker):
    if not ticker:
        return {}
    data = client.get("/markets/" + ticker, allow_missing=True)
    if data is None:
        data = client.get("/historical/markets/" + ticker, allow_missing=True)
    return (data or {}).get("market") or {}


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

    parsed = title_legs(title)
    if parsed or market.get("mve_selected_legs"):
        return "Parlay · {} legs".format(len(market.get("mve_selected_legs") or parsed))

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
    """Readable title, category, parlay legs, result, timing and bids for one market."""
    market = lookup_market(client, ticker)

    event_cache = {}

    def event_title_lookup():
        event_ticker = market.get("event_ticker")
        if not event_ticker:
            return ""
        if "title" not in event_cache:
            event = client.get("/events/" + event_ticker, allow_missing=True) or {}
            event_cache["title"] = (event.get("event") or {}).get("title") or ""
        return event_cache["title"]

    title = readable_title(ticker, market, event_title_lookup)
    raw_title = market.get("title") or ""
    parlay = parlay_details(client, ticker, market, raw_title) if title.startswith("Parlay · ") else None
    return {
        "title": title,
        "kind": "parlay" if parlay else "single",
        "legs": parlay[0] if parlay else [],
        "tag": ("WC" if parlay[1] else None) if parlay else None,
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


class ReconciliationError(SystemExit):
    """Raised (exit code 1) when API data doesn't add up exactly; data.json is left alone."""


def money_in_total():
    return sum((row["amount"] for row in DEPOSITS), ZERO) + sum((row["amount"] for row in CREDITS), ZERO)


def expected_cash(fills, settlement_payouts):
    """Cash the account should hold, from API data alone, exactly.

    deposits + credits + sale proceeds + settlement payouts - purchase costs - all fees

    Every fill is recorded as a buy of its side (selling YES at P is buying NO
    at 1 - P), so "sale proceeds - purchase costs" is computed as
    (matched YES+NO pairs x $1) - (every fill's count x price). Fees are what
    actually left the balance (kalshi_rules.apply_fee_rounding).
    """
    deposit_fees = sum((row["fee"] for row in DEPOSITS), ZERO)
    spent = sum((fill["count"] * fill["price"] for fill in fills), ZERO)
    trading_fees = sum((fill["fee"] for fill in fills), ZERO)
    pair_payouts = sum((min(entry["count"]["yes"], entry["count"]["no"]) for entry in group_fills(fills)), ZERO)
    return money_in_total() + pair_payouts + sum(settlement_payouts, ZERO) - spent - trading_fees - deposit_fees


def reconcile(dashboard, fills, settlement_payouts, actual_cash, portfolio_value):
    """Block the write unless the numbers add up EXACTLY. Returns the success line.

    Zero tolerance: Decimal equality at Kalshi's own precision (the balance is
    a whole number of cents; every modeled per-fill change is on that grid).
    Failure messages carry only the compared totals and their difference,
    with every digit.
    """
    expected = expected_cash(fills, settlement_payouts)
    cash_diff = actual_cash - expected
    if cash_diff != ZERO:
        raise ReconciliationError(
            "Reconciliation failed: expected cash ${}, actual cash ${}, diff ${}. data.json not updated.".format(
                dec_str(expected), dec_str(actual_cash), dec_str(cash_diff)
            )
        )

    expected_net = actual_cash + portfolio_value - money_in_total()
    published_net = to_decimal(dashboard["summary"]["net_pnl"])
    net_diff = published_net - expected_net
    if net_diff != ZERO:
        raise ReconciliationError(
            "Reconciliation failed: expected net P&L ${}, dashboard net P&L ${}, diff ${}. data.json not updated.".format(
                dec_str(expected_net), dec_str(published_net), dec_str(net_diff)
            )
        )
    return "reconciled exactly: expected cash ${} = actual cash ${}, diff $0; net ${}".format(
        dec_str(expected), dec_str(actual_cash), dec_str(published_net)
    )


def choose_balance_precision(fills, settlement_payouts, actual_cash):
    """Which documented Kalshi balance precision reproduces the cash EXACTLY?

    Applies Kalshi's fee-rounding rule (kalshi_rules.apply_fee_rounding) at
    each documented precision and returns the first whose expected cash equals
    the actual cash to the last digit. No tolerance. If none matches, blocks
    the write and reports every candidate's exact difference.
    """
    misses = []
    for precision in DOCUMENTED_PRECISIONS:
        apply_fee_rounding(fills, precision)
        diff = actual_cash - expected_cash(fills, settlement_payouts)
        if diff == ZERO:
            return precision
        misses.append("at ${} precision expected cash ${}, diff ${}".format(
            dec_str(precision), dec_str(actual_cash - diff), dec_str(diff)))
    raise ReconciliationError(
        "Reconciliation failed: actual cash ${}; {}. data.json not updated.".format(dec_str(actual_cash), "; ".join(misses))
    )


def ledger_report(balance, fills, settlements, precision):
    """Precision facts about Kalshi's data (types and digit counts, aggregate only)."""
    on_grid = sum(1 for fill in fills if is_on_grid(-(fill["count"] * fill["price"]) - fill["fee_reported"], CENT))
    cents_view = to_decimal(balance["balance"]) / 100 if isinstance(balance.get("balance"), int) else None
    return {
        "balance": "integer cents" if isinstance(balance.get("balance"), int) else type(balance.get("balance")).__name__,
        "balance_dollars_places": decimal_places(balance.get("balance_dollars", "")),
        "balance_cents_field_matches_dollars": cents_view == to_decimal(balance.get("balance_dollars") or "0"),
        "portfolio_value": "integer cents" if isinstance(balance.get("portfolio_value"), int) else "other",
        "balance_precision_matched": dec_str(precision),
        "fee_cost_max_places": max((fill["places"]["fee"] for fill in fills), default=0),
        "price_max_places": max((fill["places"]["price"] for fill in fills), default=0),
        "count_max_places": max((fill["places"]["count"] for fill in fills), default=0),
        "settlement_revenue": "integer cents" if all(isinstance(item.get("revenue"), int) for item in settlements) else "other",
        "fills": len(fills),
        "fills_whose_cash_change_is_whole_cents": on_grid,
        "fills_with_modeled_rounding_fee": sum(1 for fill in fills if fill["rounding_fee"] != ZERO),
        "settlements_with_fee_cost": sum(1 for item in settlements if to_decimal(item.get("fee_cost") or "0") != ZERO),
    }


def build_from_api(client):
    """Fetch everything and build the dashboard. Writes nothing.

    Returns (dashboard, fills, settlement_payouts, cash, portfolio_value).
    """
    balance = client.get("/portfolio/balance")
    # Cash at full precision from Kalshi's fixed-point string. The integer-cents
    # "balance" field can hide sub-cent cash, so it's only reported, not used.
    cash = to_decimal(balance["balance_dollars"]) if balance.get("balance_dollars") else to_decimal(balance["balance"]) / 100
    portfolio_value = to_decimal(balance["portfolio_value"]) / 100

    fills = fetch_fills(client)
    settlement_list = client.paginate("/portfolio/settlements", "settlements")
    settlements = {item["ticker"]: item for item in settlement_list}
    held = {
        item["ticker"]: to_decimal(item.get("position_fp") or "0")
        for item in client.paginate("/portfolio/positions", "market_positions", {"count_filter": "position"})
    }

    # Settlement payouts first (they don't depend on fees), then find the
    # balance precision that makes the cash match exactly, which fixes every
    # fill's real fee before any bet is built.
    payouts_by_ticker = {}
    for entry in group_fills([dict(fill, fee=ZERO) for fill in fills]):
        ticker = entry["ticker"]
        settlement = settlements.get(ticker)
        if settlement is not None:
            payouts_by_ticker[ticker] = to_decimal(settlement["revenue"]) / 100
    infos = {}
    for entry in group_fills([dict(fill, fee=ZERO) for fill in fills]):
        ticker = entry["ticker"]
        infos[ticker] = market_info(client, ticker)
        if ticker not in payouts_by_ticker and infos[ticker]["result"] in ("yes", "no"):
            won = infos[ticker]["result"]
            # Archived out of /portfolio/settlements: winning contracts pay $1.
            payouts_by_ticker[ticker] = max(entry["count"][won] - entry["count"]["no" if won == "yes" else "yes"], ZERO)
    precision = choose_balance_precision(fills, list(payouts_by_ticker.values()), cash)

    bets = []
    settlement_payouts = []
    resolution_sources = {}
    now = datetime.now(timezone.utc)
    for entry in group_fills(fills):
        ticker = entry["ticker"]
        info = infos[ticker]
        settlement = settlements.get(ticker)
        payout = payouts_by_ticker.get(ticker)
        resolved_time = None
        if payout is not None:
            settlement_payouts.append(payout)
            resolved_time, source_name = resolution_time(settlement, info, entry, now)
            # Bets sold off before settlement resolve on their sale date (make_bet),
            # so only count the ones that actually rode to settlement.
            if entry["count"]["yes"] != entry["count"]["no"]:
                resolution_sources[source_name] = resolution_sources.get(source_name, 0) + 1

        position = held.get(ticker, ZERO)
        is_open = payout is None and position != ZERO
        live_bid = None
        if is_open:
            # Value = contracts x the current BID for the side held (yes_bid for
            # a YES position, no_bid for NO): what selling right now would
            # actually fetch. Mid flatters thin markets with wide spreads, and
            # last-trade can be hours stale. No bid -> leave it blank ("—").
            bid = info["yes_bid"] if position > ZERO else info["no_bid"]
            live_bid = to_decimal(bid) if bid not in (None, "") else None
        bets.append(make_bet(entry, info["title"], payout, resolved_time, is_open, live_bid, info["category"],
                             legs=info["legs"], tag=info["tag"], kind=info["kind"]))

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
        ledger=ledger_report(balance, fills, settlement_list, precision),
    )
    return dashboard, fills, settlement_payouts, cash, portfolio_value


def run(client, writer=write_if_changed):
    """Build, reconcile, then write. A failed reconciliation never reaches writer."""
    dashboard, fills, settlement_payouts, cash, portfolio_value = build_from_api(client)
    # Precision facts first (types and digit counts only), so they're in the
    # log even if reconciliation blocks the write.
    print("ledger precision: " + ", ".join("{}={}".format(key, value) for key, value in dashboard["ledger"].items()))
    line = reconcile(dashboard, fills, settlement_payouts, cash, portfolio_value)
    wrote = writer(dashboard)
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
