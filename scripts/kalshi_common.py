"""Shared logic for the /kalshi dashboard data builders.

Both kalshi_fetch.py (live API) and kalshi_from_csv.py (CSV fallback) turn raw
fills into per-bet records, then hand them to build_dashboard(), which writes
the sanitized kalshi/data.json the page reads.

PRIVACY: nothing in the dict returned by build_dashboard() may contain an order
ID, fill ID, market ticker/ID, or account identifier. Tickers are used only as
internal grouping keys and are dropped before writing.
"""

import json
import os
from collections import OrderedDict
from decimal import ROUND_HALF_UP, Decimal
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(REPO_ROOT, "kalshi", "data.json")

# Money put into the account. The Trade API has no deposits endpoint, so these
# are maintained by hand. Add a row here whenever you deposit or get a credit.
DEPOSITS = [
    {"date": "2025-12-02", "amount": 10.00, "fee": 0.20},
]
CREDITS = [
    {"date": "2026-02-03", "amount": 25.00, "reason": "Referral bonus"},
]

# Ticker prefix -> dashboard category. First match wins, so keep longer
# prefixes above shorter ones that share a start.
CATEGORY_PREFIXES = [
    ("KXNCAA", "College"),
    ("KXNFL", "NFL"),
    ("KXNBA", "NBA"),
    ("KXWC", "Soccer"),
    ("KXEPL", "Soccer"),
    ("KXUCL", "Soccer"),
    ("KXMLS", "Soccer"),
    ("KXF1", "F1"),
    ("KXBTC", "Crypto"),
    ("KXETH", "Crypto"),
    ("KXSOL", "Crypto"),
    ("KXHONDURAS", "Politics"),
    ("KXPRES", "Politics"),
    ("KXSENATE", "Politics"),
    ("KXHOUSE", "Politics"),
]
CATEGORY_ORDER = ["NFL", "NBA", "College", "Soccer", "F1", "Crypto", "Politics", "Other"]

# Per-market fixes, keyed by market ticker (tickers stay in code, never in
# data.json). Parlays are normally categorized from their legs (see
# kalshi_fetch.category_from_legs); this pins the one we know about in case
# the legs aren't returned.
CATEGORY_OVERRIDES = {
    "KXMVESPORTSMULTIGAMEEXTENDED-S20260905EFE5661-C299BAD43AB": "Soccer",  # World Cup parlay
}

# Hand-written titles that win over the API's. Keep them under ~40 chars.
TITLE_OVERRIDES = {
    "KXNFLGAME-26SEP27HOUIND-HOU": "Texans vs Colts: Texans win",
    "KXNFLGAME-26SEP24ATLGB-GB": "Packers vs Falcons: Packers win",
    "KXHONDURASPRES-25-NASF": "Honduras president: Nasry Asfura",
    "KXBTCD-26JUN3019-T58499.99": "Bitcoin $58,500+ on Jun 30, 2026",
}

try:
    from zoneinfo import ZoneInfo

    LOCAL_TZ = ZoneInfo("America/Chicago")
except ImportError:  # Python 3.8 has no zoneinfo; CDT is close enough.
    LOCAL_TZ = timezone(timedelta(hours=-5))


def category_for(ticker):
    if ticker in CATEGORY_OVERRIDES:
        return CATEGORY_OVERRIDES[ticker]
    upper = ticker.upper()
    for prefix, name in CATEGORY_PREFIXES:
        if upper.startswith(prefix):
            return name
    return "Other"


def parse_time(stamp):
    """ISO-8601 string -> aware UTC datetime."""
    cleaned = stamp.replace("Z", "+00:00")
    # Python 3.8's fromisoformat only accepts 0, 3 or 6 fractional digits.
    if "." in cleaned:
        head, tail = cleaned.split(".", 1)
        digits = ""
        rest = ""
        for pos, char in enumerate(tail):
            if char.isdigit():
                digits += char
            else:
                rest = tail[pos:]
                break
        cleaned = head + "." + (digits + "000000")[:6] + rest
    moment = datetime.fromisoformat(cleaned)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def local_date(moment):
    return moment.astimezone(LOCAL_TZ).strftime("%Y-%m-%d")


def money(amount):
    """Round to cents half-up, like Kalshi's app ($1.805 -> $1.81, not $1.80)."""
    if amount is None:
        return None
    # Go through a 9-place string first so float noise (1.8049999...) can't
    # tip a half-cent the wrong way.
    exact = Decimal("{:.9f}".format(float(amount)))
    return float(exact.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def group_fills(fills):
    """Group normalized fills by ticker into per-market position summaries.

    Each fill is a dict: ticker, side ("yes"/"no", the outcome it buys exposure
    to), count, price (dollars for that side), fee, is_taker, time (datetime),
    and optionally cost_fee (see below). Selling YES at 67c is the same as
    buying NO at 33c, so every fill is treated as a buy of its side. A YES + NO
    pair always pays exactly $1, which is how closed-early positions are
    valued without any settlement data.

    fee is Kalshi's own fee record and feeds every fee total. cost_fee is only
    for showing an open position's cost basis the way the app does; it
    defaults to fee (the API's fee_cost is already exact).
    """
    markets = OrderedDict()
    for fill in sorted(fills, key=lambda item: item["time"]):
        entry = markets.setdefault(
            fill["ticker"],
            {
                "ticker": fill["ticker"],
                "opening_side": fill["side"],
                "first_time": fill["time"],
                "last_time": fill["time"],
                "count": {"yes": 0.0, "no": 0.0},
                "cost": {"yes": 0.0, "no": 0.0},
                "fee": {"yes": 0.0, "no": 0.0},
                "cost_fee": {"yes": 0.0, "no": 0.0},
            },
        )
        side = fill["side"]
        entry["count"][side] += fill["count"]
        entry["cost"][side] += fill["count"] * fill["price"]
        entry["fee"][side] += fill["fee"]
        entry["cost_fee"][side] += fill.get("cost_fee", fill["fee"])
        entry["last_time"] = fill["time"]
    return list(markets.values())


def make_bet(entry, title, settlement_payout=None, resolved_time=None, is_open=False, open_value=None, category=None):
    """Turn a grouped market into a sanitized bet record.

    Money is on the app's basis: cost includes the fees paid to open the
    position, payout is net of the fees paid to close it, and
    profit = payout - cost.

    settlement_payout: dollars received at settlement, or None if unknown.
    is_open: the market hasn't settled yet and contracts are still held.
    """
    opening = entry["opening_side"]
    closing = "no" if opening == "yes" else "yes"
    pairs = min(entry["count"]["yes"], entry["count"]["no"])
    remaining = round(entry["count"][opening] - entry["count"][closing], 2)
    # Selling back early: each matched YES+NO pair pays $1, minus what the
    # closing side cost and its fees.
    early_proceeds = (pairs - entry["cost"][closing] - entry["fee"][closing]) if pairs > 0 else 0.0

    if abs(remaining) < 0.005:
        status = "sold"
        payout = early_proceeds
    elif settlement_payout is not None:
        status = "settled"
        payout = early_proceeds + settlement_payout
    elif is_open:
        status = "open"
        payout = None
    else:
        status = "pending"
        payout = None

    if status == "open":
        fee = entry["cost_fee"][opening]
    else:
        fee = entry["fee"][opening] + entry["fee"][closing]
    cost = entry["cost"][opening] + (fee if status == "open" else entry["fee"][opening])
    profit = None if payout is None else payout - cost
    when = resolved_time or entry["last_time"]
    return {
        "date": local_date(entry["first_time"]),
        "resolved": local_date(when) if payout is not None else None,
        "title": title,
        "side": opening.capitalize(),
        "category": category or category_for(entry["ticker"]),
        "cost": money(cost),
        "payout": money(payout),
        "profit": money(profit),
        "fee": money(fee),
        "status": status,
        "contracts": abs(remaining) if status == "open" else None,
        "value": money(open_value) if status == "open" else None,
    }


def fee_breakdown(fills):
    maker = [fill for fill in fills if not fill["is_taker"]]
    taker = [fill for fill in fills if fill["is_taker"]]
    return {
        "maker_fills": len(maker),
        "maker_fees": money(sum(fill["fee"] for fill in maker)),
        "taker_fills": len(taker),
        "taker_fees": money(sum(fill["fee"] for fill in taker)),
    }


def build_dashboard(bets, fills, cash, open_value, source, fee_source, pnl_series=None, series_note="",
                    resolution_sources=None):
    deposited = sum(row["amount"] for row in DEPOSITS)
    deposit_fees = sum(row["fee"] for row in DEPOSITS)
    credited = sum(row["amount"] for row in CREDITS)
    trading_fees = sum(fill["fee"] for fill in fills)
    account_value = cash + open_value
    net_pnl = account_value - deposited - credited

    # Resolved = sold early or settled. Open positions never count toward the
    # win rate; they neither help it nor block it.
    resolved = [bet for bet in bets if bet["profit"] is not None]
    wins = [bet for bet in resolved if bet["profit"] > 0]
    pending = [bet for bet in bets if bet["status"] == "pending"]
    open_bets = [bet for bet in bets if bet["status"] == "open"]

    by_category = OrderedDict((name, {"profit": 0.0, "resolved": 0, "pending": 0}) for name in CATEGORY_ORDER)
    for bet in bets:
        bucket = by_category[bet["category"]]
        if bet["profit"] is not None:
            bucket["profit"] += bet["profit"]
            bucket["resolved"] += 1
        elif bet["status"] == "pending":
            bucket["pending"] += 1
    categories = [
        {"name": name, "profit": money(bucket["profit"]), "resolved": bucket["resolved"], "pending": bucket["pending"]}
        for name, bucket in by_category.items()
        if bucket["resolved"] or bucket["pending"]
    ]

    if pnl_series is None:
        pnl_series = realized_series(resolved, deposit_fees, net_pnl)

    newest_first = sorted(bets, key=lambda bet: bet["date"], reverse=True)
    return {
        "source": source,
        "summary": {
            "net_pnl": money(net_pnl),
            "account_value": money(account_value),
            "cash": money(cash),
            "open_value": money(open_value),
            "deposited": money(deposited),
            "credits": money(credited),
            "credit_reasons": [row["reason"] for row in CREDITS],
            "trading_fees": money(trading_fees),
            "deposit_fees": money(deposit_fees),
            "total_fees": money(trading_fees + deposit_fees),
            "bets": len(bets),
            "resolved": len(resolved),
            "wins": len(wins),
            "losses": len(resolved) - len(wins),
            "pending": len(pending),
            "open": len(open_bets),
            # "pending" = finished but result unknown (CSV mode only). While any
            # exist, the known results are mostly bets sold early, which skew
            # toward winners, so show no percentage.
            "win_rate": round(len(wins) / len(resolved), 3) if resolved and not pending else None,
        },
        "fees": dict(fee_breakdown(fills), source=fee_source),
        "pnl_series": pnl_series,
        "pnl_series_note": series_note,
        # How each settled bet's date was found (counts only). "last_fill" means
        # no settlement or close time was available and the bet's last trade
        # date was used instead.
        "resolution_dates": resolution_sources or {},
        "categories": categories,
        "open_positions": [
            {
                "date": bet["date"],
                "title": bet["title"],
                "side": bet["side"],
                "contracts": bet["contracts"],
                "cost": bet["cost"],
                "value": bet["value"],
                "category": bet["category"],
            }
            for bet in open_bets
        ],
        "recent_bets": [
            {key: bet[key] for key in ("date", "title", "side", "cost", "payout", "profit", "fee", "category", "status")}
            for bet in newest_first[:20]
        ],
    }


def realized_series(resolved, deposit_fees, net_pnl):
    """Cumulative realized P&L by resolution date, ending at today's net P&L."""
    running = -deposit_fees
    points = [{"date": DEPOSITS[0]["date"], "pnl": money(running)}] if DEPOSITS else []
    for bet in sorted(resolved, key=lambda item: item["resolved"]):
        running += bet["profit"]
        points.append({"date": bet["resolved"], "pnl": money(running)})
    points.append({"date": local_date(datetime.now(timezone.utc)), "pnl": money(net_pnl)})
    return points


def write_if_changed(dashboard, path=DATA_PATH):
    """Write data.json, but only bump the timestamp when the numbers changed.

    Returns True if the file was written. Keeps the GitHub Action from making
    a commit every 6 hours when nothing happened.
    """
    previous = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            try:
                previous = json.load(handle)
            except ValueError:
                previous = None

    comparable = dict(dashboard)
    if previous is not None:
        old = dict(previous)
        old.pop("updated", None)
        # The trailing "today" point moves daily even when nothing else did.
        for blob in (old, comparable):
            series = blob.get("pnl_series") or []
            blob["pnl_series"] = series[:-1]
        if old == comparable:
            return False

    dashboard["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(dashboard, handle, indent=2)
        handle.write("\n")
    return True
