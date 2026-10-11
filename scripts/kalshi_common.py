"""Shared logic for the /kalshi dashboard data builders.

Both kalshi_fetch.py (live API) and kalshi_from_csv.py (CSV fallback) turn raw
fills into per-bet records, then hand them to build_dashboard(), which writes
the sanitized kalshi/data.json the page reads.

PRIVACY: nothing in the dict returned by build_dashboard() may contain an order
ID, fill ID, market ticker/ID, or account identifier. Tickers are used only as
internal grouping keys and are dropped before writing.

EXACTNESS (non-negotiable, see CLAUDE.md): every amount, price, contract count
and fee is a decimal.Decimal parsed straight from its string form. No float,
no round(), no quantize (Kalshi's own rounding rules live in kalshi_rules.py
and nowhere else). data.json stores every amount as a full-precision string.
"""

import json
import os
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from kalshi_rules import ZERO

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(REPO_ROOT, "kalshi", "data.json")

# Money put into the account. The Trade API has no deposits endpoint, so these
# are maintained by hand. Add a row here whenever you deposit or get a credit.
DEPOSITS = [
    {"date": "2025-12-02", "amount": Decimal("10.00"), "fee": Decimal("0.20")},
]
CREDITS = [
    {"date": "2026-02-03", "amount": Decimal("25.00"), "reason": "Referral bonus"},
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
    "KXWCGROUPWIN-26B-CAN": "Canada wins WC Group B",
    "KXWCADVANCE-26JUL01USABIH-USA": "USA vs Bosnia: USA advances",
}

# Parlays known to be all World Cup legs, for when the API doesn't return the
# legs themselves (normally detected from mve_selected_legs).
WORLD_CUP_PARLAYS = {"KXMVESPORTSMULTIGAMEEXTENDED-S20260905EFE5661-C299BAD43AB"}
TITLE_MAX = 40

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


def to_decimal(value):
    """Exact Decimal from an API/CSV string (or an int, e.g. cents). Floats are refused."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError("refusing to build a Decimal from {!r}: parse the original string".format(value))
    if value is None or value == "":
        return ZERO
    return Decimal(value) if isinstance(value, int) else Decimal(str(value).strip())


def dec_str(value):
    """Full-precision string for data.json: no exponent, trailing zeros trimmed, never rounded."""
    if value is None:
        return None
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("-0", ""):
        text = "0"
    return text


def group_fills(fills):
    """Group normalized fills by ticker into per-market position summaries.

    Each fill is a dict: ticker, side ("yes"/"no", the outcome it buys exposure
    to), count, price (dollars for that side), fee, is_taker, time (datetime),
    and optionally cost_fee (see below). All amounts are Decimal. Selling YES
    at 67c is the same as buying NO at 33c, so every fill is treated as a buy
    of its side. A YES + NO pair always pays exactly $1, which is how
    closed-early positions are valued without any settlement data.

    fee is the fee that actually left the balance and feeds every fee total.
    cost_fee is only for showing an open position's cost basis the way the
    app does (CSV mode); it defaults to fee.
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
                "count": {"yes": ZERO, "no": ZERO},
                "cost": {"yes": ZERO, "no": ZERO},
                "fee": {"yes": ZERO, "no": ZERO},
                "cost_fee": {"yes": ZERO, "no": ZERO},
                "fills": [],
            },
        )
        side = fill["side"]
        entry["fills"].append(fill)
        entry["count"][side] += fill["count"]
        entry["cost"][side] += fill["count"] * fill["price"]
        entry["fee"][side] += fill["fee"]
        entry["cost_fee"][side] += fill.get("cost_fee", fill["fee"])
        entry["last_time"] = fill["time"]
    return list(markets.values())


ONE = Decimal("1")


def make_bet(entry, title, settlement_payout=None, resolved_time=None, is_open=False, live_bid=None, category=None,
             legs=None, tag=None, kind="single"):
    """Turn a grouped market into a bet record, read left to right like an equation.

    All amounts are exact Decimals (serialized later):
      Zone A (money in):   contracts x price = stake;  stake + buy_fees = cost
      Zone B (money back): payout - sell_fees = net_payout
                           payout = sale proceeds (contracts sold x sale price)
                                  + settlement (contracts held x $1 or $0)
                                  + for OPEN bets: "if sold now" value (contracts held x current bid)
      Zone C (result):     profit = net_payout - cost  (unrealized for open bets)

    Every fill is recorded as a buy of its side, so a fill on the other side
    at price q is a sale of this bet's side at 1 - q.

    settlement_payout: dollars received at settlement (Decimal), or None if unknown.
    is_open: the market hasn't settled yet and contracts are still held.
    live_bid: current bid (Decimal) for the side held, for open bets.
    """
    opening = entry["opening_side"]
    fills = entry["fills"]
    buys = [fill for fill in fills if fill["side"] == opening]
    sells = [fill for fill in fills if fill["side"] != opening]
    contracts = sum((fill["count"] for fill in buys), ZERO)
    sold_contracts = sum((fill["count"] for fill in sells), ZERO)
    remaining = contracts - sold_contracts

    if remaining == ZERO:
        status = "sold"
    elif settlement_payout is not None:
        status = "settled"
    elif is_open:
        status = "open"
    else:
        status = "pending"

    # Open bets in CSV mode show the app's cost basis (cost_fee); otherwise
    # the fee that actually left the balance.
    def buy_fee(fill):
        return fill.get("cost_fee", fill["fee"]) if status == "open" else fill["fee"]

    fill_rows = []
    for fill in sorted(fills, key=lambda item: item["time"]):
        is_buy = fill["side"] == opening
        price = fill["price"] if is_buy else ONE - fill["price"]
        fill_rows.append({
            "time": fill["time"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "action": "buy" if is_buy else "sell",
            "contracts": fill["count"],
            "price": price,
            "amount": fill["count"] * price,
            "fee": buy_fee(fill) if is_buy else fill["fee"],
            "liquidity": "taker" if fill["is_taker"] else "maker",
        })

    stake = sum((row["amount"] for row in fill_rows if row["action"] == "buy"), ZERO)
    buy_fees = sum((row["fee"] for row in fill_rows if row["action"] == "buy"), ZERO)
    sale_proceeds = sum((row["amount"] for row in fill_rows if row["action"] == "sell"), ZERO)
    sell_fees = sum((row["fee"] for row in fill_rows if row["action"] == "sell"), ZERO)
    prices = {row["price"] for row in fill_rows if row["action"] == "buy"}

    settlement = None
    live = None
    payout = None
    if status in ("sold", "settled"):
        payout = sale_proceeds
        if status == "settled":
            per_contract = settlement_payout / remaining if remaining else ZERO
            settlement = {"contracts": remaining, "per_contract": per_contract, "amount": settlement_payout}
            payout += settlement_payout
    elif status == "open" and live_bid is not None:
        live = {"contracts": abs(remaining), "bid": live_bid, "amount": abs(remaining) * live_bid}
        payout = sale_proceeds + live["amount"]

    cost = stake + buy_fees
    net_payout = None if payout is None else payout - sell_fees
    profit = None if net_payout is None else net_payout - cost

    if status == "settled":
        outcome = "won" if profit > ZERO else "lost"
    else:
        outcome = status  # open / sold / pending

    # A bet sold off early resolves on its sale date, even if the market later
    # settled; anything else uses the settlement time when one is known.
    finished = status in ("sold", "settled")
    when = entry["last_time"] if status == "sold" else (resolved_time or entry["last_time"])
    placed = local_date(entry["first_time"])
    resolved = local_date(when) if finished else None
    return {
        "kind": kind,
        "tag": tag,
        "date": placed,
        "resolved": resolved,
        # The date a bet sits at on the timeline and in date filters: when it
        # finished, or when it was placed if it's still open.
        "event_date": resolved or placed,
        "title": title,
        "side": opening.capitalize(),
        "category": category or category_for(entry["ticker"]),
        "status": status,
        "outcome": outcome,
        "unrealized": status == "open",
        "contracts": contracts,
        "remaining": abs(remaining) if status == "open" else None,
        "price": next(iter(prices)) if len(prices) == 1 else None,
        "stake": stake,
        "buy_fees": buy_fees,
        "cost": cost,
        "payout": payout,
        "sell_fees": sell_fees,
        "net_payout": net_payout,
        "profit": profit,
        # Kept for the fee and win-rate summaries.
        "fee": buy_fees + sell_fees,
        "fills": fill_rows,
        "settlement": settlement,
        "live": live,
        "legs": legs or [],
    }


def fee_breakdown(fills):
    maker = [fill for fill in fills if not fill["is_taker"]]
    taker = [fill for fill in fills if fill["is_taker"]]
    return {
        "maker_fills": len(maker),
        "maker_fees": dec_str(sum((fill["fee"] for fill in maker), ZERO)),
        "taker_fills": len(taker),
        "taker_fees": dec_str(sum((fill["fee"] for fill in taker), ZERO)),
        # What Kalshi's fill records say, plus the modeled rounding fees and
        # rebates (kalshi_rules.apply_fee_rounding). trading = reported +
        # rounding - rebates, exactly.
        "reported": dec_str(sum((fill.get("fee_reported", fill["fee"]) for fill in fills), ZERO)),
        "rounding": dec_str(sum((fill.get("rounding_fee", ZERO) for fill in fills), ZERO)),
        "rebates": dec_str(sum((fill.get("rebate", ZERO) for fill in fills), ZERO)),
    }


def approx_percent(part, whole):
    """Whole-number percent for the win-rate tile (a ratio, not money; shown with "≈")."""
    return (part * 200 + whole) // (whole * 2)


def to_json(value):
    """Recursively turn Decimals into exact strings for data.json."""
    if isinstance(value, Decimal):
        return dec_str(value)
    if isinstance(value, dict):
        return {key: to_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_json(item) for item in value]
    return value


BET_KEYS = ("kind", "tag", "date", "resolved", "event_date", "title", "side", "category", "status", "outcome",
            "unrealized", "contracts", "remaining", "price", "stake", "buy_fees", "cost", "payout", "sell_fees",
            "net_payout", "profit", "fills", "settlement", "live", "legs")


def build_dashboard(bets, fills, cash, kalshi_open_value, source, fee_source, pnl_series=None, series_note="",
                    resolution_sources=None, ledger=None):
    """Assemble data.json. All arithmetic happens here, exactly; the page only formats strings.

    Headline net P&L (live API data) = realized P&L - deposit fees + unrealized
    P&L of open bets at the current bid. That is exactly the sum of every row's
    profit minus the deposit fees, so the headline always equals what the Bets
    table adds up to. (When cash reconciles it also equals cash + open bets at
    bid - money in; kalshi_fetch.reconcile checks that.) Kalshi's own
    portfolio value is kept only as a labeled secondary figure.

    CSV fallback: no bids and finished bets with unknown payouts, so the rows
    can't add up; the headline there is the app snapshot (cash + Kalshi's open
    value - money in), labeled net_pnl_basis = "snapshot".
    """
    deposited = sum((row["amount"] for row in DEPOSITS), ZERO)
    deposit_fees = sum((row["fee"] for row in DEPOSITS), ZERO)
    credited = sum((row["amount"] for row in CREDITS), ZERO)
    trading_fees = sum((fill["fee"] for fill in fills), ZERO)

    # Resolved = sold early or settled. Open positions never count toward the
    # win rate or realized P&L; their profit is unrealized (at the current bid).
    resolved = [bet for bet in bets if bet["status"] in ("sold", "settled")]
    wins = [bet for bet in resolved if bet["profit"] > ZERO]
    pending = [bet for bet in bets if bet["status"] == "pending"]
    open_bets = [bet for bet in bets if bet["status"] == "open"]
    open_profits = [bet["profit"] for bet in open_bets]
    valued_open = [bet for bet in open_bets if bet["profit"] is not None]
    realized_total = sum((bet["profit"] for bet in resolved), ZERO)
    unrealized_total = sum((bet["profit"] for bet in valued_open), ZERO)

    if source == "csv":
        net_basis = "snapshot"
        open_value = kalshi_open_value
        account_value = cash + open_value
        net_pnl = account_value - deposited - credited
    else:
        net_basis = "bets_at_bid"
        open_value = sum((bet["live"]["amount"] for bet in valued_open), ZERO)
        account_value = cash + open_value
        net_pnl = realized_total - deposit_fees + unrealized_total

    by_category = OrderedDict((name, {"profit": ZERO, "resolved": 0, "pending": 0}) for name in CATEGORY_ORDER)
    for bet in bets:
        bucket = by_category[bet["category"]]
        if bet["status"] in ("sold", "settled"):
            bucket["profit"] += bet["profit"]
            bucket["resolved"] += 1
        elif bet["status"] == "pending":
            bucket["pending"] += 1
    categories = [
        {"name": name, "profit": dec_str(bucket["profit"]), "resolved": bucket["resolved"], "pending": bucket["pending"]}
        for name, bucket in by_category.items()
        if bucket["resolved"] or bucket["pending"]
    ]
    realized = sum((bet["profit"] for bet in resolved), ZERO)

    if pnl_series is None:
        pnl_series = daily_series(resolved, deposit_fees, net_pnl)

    best = max(resolved, key=lambda bet: bet["profit"]) if resolved else None
    worst = min(resolved, key=lambda bet: bet["profit"]) if resolved else None
    # Every bet ever, open first, then newest event first. No limit: the page
    # filters and sums them itself (exactly, via kalshi/exact.js).
    def newest_first(group):
        return sorted(group, key=lambda bet: (bet["event_date"], bet["date"], bet["title"]), reverse=True)

    ordered = newest_first(open_bets) + newest_first([bet for bet in bets if bet["status"] != "open"])
    dashboard = {
        "source": source,
        "summary": {
            "net_pnl": dec_str(net_pnl),
            # How net_pnl was computed: "bets_at_bid" = realized - deposit fees +
            # unrealized at current bid (sum of rows - deposit fees); "snapshot" = CSV mode.
            "net_pnl_basis": net_basis,
            "account_value": dec_str(account_value),
            "cash": dec_str(cash),
            # Open bets at the current bid (what the rows use).
            "open_value": dec_str(open_value),
            # Kalshi's own portfolio value for the same bets (secondary, labeled on the page).
            "kalshi_open_value": dec_str(kalshi_open_value),
            # Open bets with no current bid (left out of the headline and the totals).
            "unvalued_open": len(open_bets) - len(valued_open),
            "deposited": dec_str(deposited),
            "credits": dec_str(credited),
            "credit_reasons": [row["reason"] for row in CREDITS],
            "trading_fees": dec_str(trading_fees),
            "deposit_fees": dec_str(deposit_fees),
            "total_fees": dec_str(trading_fees + deposit_fees),
            "realized_pnl": dec_str(realized),
            # Open bets marked at the current bid; null if any open bet has no bid.
            "unrealized_pnl": dec_str(sum(open_profits, ZERO)) if None not in open_profits else None,
            "started": DEPOSITS[0]["date"] if DEPOSITS else None,
            "bets": len(bets),
            "won": sum(1 for bet in bets if bet["outcome"] == "won"),
            "lost": sum(1 for bet in bets if bet["outcome"] == "lost"),
            "sold": sum(1 for bet in bets if bet["outcome"] == "sold"),
            "sold_profitable": sum(1 for bet in bets if bet["outcome"] == "sold" and bet["profit"] > ZERO),
            "resolved": len(resolved),
            "wins": len(wins),
            "losses": len(resolved) - len(wins),
            "pending": len(pending),
            "open": len(open_bets),
            # "pending" = finished but result unknown (CSV mode only). While any
            # exist, the known results are mostly bets sold early, which skew
            # toward winners, so show no percentage.
            "win_rate_approx_pct": approx_percent(len(wins), len(resolved)) if resolved and not pending else None,
            "best_bet": {"title": best["title"], "profit": dec_str(best["profit"])} if best else None,
            "worst_bet": {"title": worst["title"], "profit": dec_str(worst["profit"])} if worst else None,
        },
        "fees": dict(fee_breakdown(fills), source=fee_source),
        "ledger": ledger or {},
        "pnl_series": pnl_series,
        "pnl_series_note": series_note,
        # How each settled bet's date was found (counts only). "last_fill" means
        # no settlement or close time was available and the bet's last trade
        # date was used instead.
        "resolution_dates": resolution_sources or {},
        "categories": categories,
        "bets": [to_json({key: bet[key] for key in BET_KEYS}) for bet in ordered],
    }
    # The most decimal places any amount uses; kalshi/exact.js must handle at least this many.
    dashboard["max_decimal_places"] = max_places(dashboard)
    return dashboard


def max_places(node):
    """Largest number of digits after the decimal point in any numeric string in node."""
    if isinstance(node, dict):
        return max((max_places(value) for value in node.values()), default=0)
    if isinstance(node, list):
        return max((max_places(value) for value in node), default=0)
    if isinstance(node, str) and node and node.lstrip("-").replace(".", "", 1).isdigit() and "." in node:
        return len(node.split(".", 1)[1])
    return 0


OPEN_POSITIONS_LABEL = "Open bets at current bid (unrealized)"
MAX_DAY_ITEMS = 8


def daily_series(resolved, deposit_fees, net_pnl, today=None):
    """One point per day for the step chart: that day's results and the running total.

    Each point is {date, day, pnl, items} with amounts as exact strings: items
    list what moved the total that day ({label, amount}), day is their exact
    sum, and pnl is the exact running total after it. The final point is today
    and ends exactly at net_pnl; the gap between realized results and net P&L
    is the open positions' mark, listed as its own item.
    """
    today = today or local_date(datetime.now(timezone.utc))
    days = OrderedDict()
    if DEPOSITS and deposit_fees:
        days.setdefault(DEPOSITS[0]["date"], []).append({"label": "Deposit fee", "amount": -deposit_fees})
    for bet in sorted(resolved, key=lambda item: (item["resolved"], -item["profit"])):  # finished bets only
        days.setdefault(bet["resolved"], []).append({"label": bet["title"], "amount": bet["profit"]})

    realized = sum((item["amount"] for items in days.values() for item in items), ZERO)
    open_mark = net_pnl - realized
    if open_mark != ZERO or today not in days:
        days.setdefault(today, []).append({"label": OPEN_POSITIONS_LABEL, "amount": open_mark})

    points = []
    running = ZERO
    for day in sorted(days):
        items = days[day]
        day_total = sum((item["amount"] for item in items), ZERO)
        running += day_total
        shown = [{"label": item["label"], "amount": dec_str(item["amount"])} for item in items[:MAX_DAY_ITEMS]]
        if len(items) > MAX_DAY_ITEMS:
            rest = sum((item["amount"] for item in items[MAX_DAY_ITEMS:]), ZERO)
            shown.append({"label": "{} more".format(len(items) - MAX_DAY_ITEMS), "amount": dec_str(rest)})
        points.append({"date": day, "day": dec_str(day_total), "pnl": dec_str(running), "items": shown})
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
