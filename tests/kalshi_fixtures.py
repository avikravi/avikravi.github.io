"""Golden API fixtures and the exact identity checks shared by the Kalshi tests.

Fills are API-shaped (strings, like Kalshi sends). Expected values are worked
out by hand below as Decimal literals, independently of the pipeline.

Golden fills. Every fee_cost below was VERIFIED against Kalshi's live API on
2026-10-11 (the first exact run). Canada's sell fee is 1.1453, not the 1.15
inferred earlier from the app's cent display: the app's "$23.27 / +$12.28" are
cent-rounded views of the exact 23.2747 / 12.2847.
  Robinson  buy 3.52 YES @ 0.55, fee 0.0610; sell 3.52 YES @ 0.99 (maker, fee 0)
            cost 1.936 + 0.061 = 1.997; payout 3.52 x 0.99 = 3.4848; profit 1.4878
  Penix     buy 1.20 NO @ 0.83, fee 0.0119; sell 1.20 NO @ 0.99 (maker)
            cost 0.996 + 0.0119 = 1.0079; payout 1.188; profit 0.1801
  Mexico    buy 1.90 YES @ 0.64, fee 0.0307; sell 1.90 YES @ 0.95 (maker)
            cost 1.216 + 0.0307 = 1.2467; payout 1.805; profit 0.5583
  Canada    buy 64 + 10 YES @ 0.14 (one order), fees 0.54 + 0.09; sell 74 YES @ 0.33, fee 1.1453
            cost 10.36 + 0.63 = 10.99; payout 24.42 - 1.1453 = 23.2747; profit 12.2847
  Bitcoin   buy 12.32 YES @ 0.79, fee 0.1431; settles YES, revenue 1232c
            cost 9.7328 + 0.1431 = 9.8759; payout 12.32; profit 2.4441
  Texans    buy 16.42 YES @ 0.29, fee 0.2367; settles NO, revenue 0
            cost 4.7618 + 0.2367 = 4.9985; payout 0; profit -4.9985
  Golden    buy 5.80 NO @ 0.33, fee 0.0895; still open, NO bid 0.31
            cost 1.914 + 0.0895 = 2.0035; value 5.80 x 0.31 = 1.798
Cash = 35.00 in - 0.20 deposit fee + 1.4878 + 0.1801 + 0.5583 + 12.2847 + 2.4441
       - 4.9985 - 2.0035 = 44.753 (every change is on the $0.0001 grid)
Headline net = realized 11.9565 - 0.20 deposit fee + unrealized -0.2055 (Golden at its
0.31 bid: 1.798 - 2.0035) = 11.551 = cash 44.753 + open at bid 1.798 - 35.
Kalshi's own portfolio value (180 cents = $1.80) is shown only as a secondary figure.
"""

from decimal import ROUND_FLOOR, Decimal

import kalshi_paths  # noqa: F401  (puts scripts/ on sys.path)
import kalshi_common
import kalshi_fetch

D = Decimal

ROBINSON = "KXNFLTD-26SEP24ATLGB-ATLBROBINSON7-1"
PENIX = "KXNFLPASSYDS-26SEP24ATLGB-ATLMPENIX9-275"
MEXICO = "KXWCADVANCE-26JUN30MEXECU-MEX"
CANADA = "KXWCGROUPWIN-26B-CAN"
BITCOIN = "KXBTCD-26JUN3019-T58499.99"
TEXANS = "KXNFLGAME-26SEP27HOUIND-HOU"
GOLDEN = "KXNFLRECYDS-26OCT11CHIGB-GBMGOLDEN0-40"


def api_fill(num, ticker, order, outcome, count, yes_price, fee, taker, when):
    """An API-shaped fill. Prices are strings; no_price = 1 - yes_price exactly."""
    return {
        "fill_id": "fill-%d" % num,
        "order_id": order,
        "ticker": ticker,
        "outcome_side": outcome,
        "count_fp": count,
        "yes_price_dollars": yes_price,
        "no_price_dollars": kalshi_common.dec_str(D(1) - D(yes_price)),
        "is_taker": taker,
        "fee_cost": fee,
        "created_time": when,
    }


GOLDEN_FILLS = [
    api_fill(1, ROBINSON, "o-rob-buy", "yes", "3.52", "0.5500", "0.0610", True, "2026-09-25T00:23:00Z"),
    api_fill(2, ROBINSON, "o-rob-sell", "no", "3.52", "0.9900", "0", False, "2026-09-25T00:51:00Z"),
    api_fill(3, PENIX, "o-pen-buy", "no", "1.20", "0.1700", "0.0119", True, "2026-09-25T00:24:00Z"),
    api_fill(4, PENIX, "o-pen-sell", "yes", "1.20", "0.0100", "0", False, "2026-09-25T02:03:00Z"),
    api_fill(5, MEXICO, "o-mex-buy", "yes", "1.90", "0.6400", "0.0307", True, "2026-07-01T01:34:00Z"),
    api_fill(6, MEXICO, "o-mex-sell", "no", "1.90", "0.9500", "0", False, "2026-07-01T02:32:00Z"),
    api_fill(7, CANADA, "o-can-buy", "yes", "64.00", "0.1400", "0.54", True, "2026-01-22T07:15:00Z"),
    api_fill(8, CANADA, "o-can-buy", "yes", "10.00", "0.1400", "0.09", True, "2026-01-22T07:15:01Z"),
    api_fill(9, CANADA, "o-can-sell", "no", "74.00", "0.3300", "1.1453", True, "2026-06-18T17:47:00Z"),
    api_fill(10, BITCOIN, "o-btc", "yes", "12.32", "0.7900", "0.1431", True, "2026-06-30T22:49:00Z"),
    api_fill(11, TEXANS, "o-hou", "yes", "16.42", "0.2900", "0.2367", True, "2026-09-27T18:31:00Z"),
    api_fill(12, GOLDEN, "o-gold", "no", "5.80", "0.6700", "0.0895", True, "2026-10-11T03:24:00Z"),
]

GOLDEN_SETTLEMENTS = [
    {"ticker": BITCOIN, "revenue": 1232, "settled_time": "2026-06-30T23:30:00Z", "fee_cost": "0"},
    {"ticker": TEXANS, "revenue": 0, "settled_time": "2026-09-28T03:00:00Z", "fee_cost": "0"},
]
GOLDEN_POSITIONS = [{"ticker": GOLDEN, "position_fp": "-5.80"}]
GOLDEN_CASH = "44.753"
GOLDEN_PORTFOLIO_CENTS = 180

# Expected rows, by title, worked out by hand above.
GOLDEN_ROWS = {
    "Bijan Robinson TD": (D("1.997"), D("3.4848"), D("1.4878")),
    "Penix 275+": (D("1.0079"), D("1.188"), D("0.1801")),
    "Mexico advances": (D("1.2467"), D("1.805"), D("0.5583")),
    "Canada wins WC Group B": (D("10.99"), D("23.2747"), D("12.2847")),
    "Bitcoin $58,500+ on Jun 30, 2026": (D("9.8759"), D("12.32"), D("2.4441")),
    "Texans vs Colts: Texans win": (D("4.9985"), D("0"), D("-4.9985")),
}
GOLDEN_CATEGORIES = {"NFL": D("-3.3306"), "Soccer": D("12.843"), "Crypto": D("2.4441")}
GOLDEN_NET = D("11.551")
GOLDEN_OPEN = {"cost": D("2.0035"), "value": D("1.798")}
TITLES = {ROBINSON: "Bijan Robinson TD", PENIX: "Penix 275+", MEXICO: "Mexico advances", GOLDEN: "Golden 40+"}


# A 3-leg World Cup parlay that lost because the Netherlands leg missed.
#   buy 15.67 YES @ 0.466, fee 0.27308 -> cost 7.30222 + 0.27308 = 7.5753; settles NO -> profit -7.5753
PARLAY = "KXMVESPORTSMULTIGAMEEXTENDED-S20260905EFE5661-C299BAD43AB"
PARLAY_FILLS = [api_fill(13, PARLAY, "o-parlay", "yes", "15.67", "0.4660", "0.27308", True, "2026-06-25T14:57:00Z")]
PARLAY_SETTLEMENTS = [{"ticker": PARLAY, "revenue": 0, "settled_time": "2026-06-25T23:00:00Z", "fee_cost": "0"}]
PARLAY_MARKETS = {
    PARLAY: {"title": "yes Ivory Coast,yes Germany,yes Netherlands", "result": "no", "mve_selected_legs": [
        {"event_ticker": "KXWCGAME-A", "market_ticker": "KXWCGAME-26JUN25-CIV", "side": "yes", "yes_settlement_value_dollars": "1.0000"},
        {"event_ticker": "KXWCGAME-B", "market_ticker": "KXWCGAME-26JUN25-GER", "side": "yes", "yes_settlement_value_dollars": "1.0000"},
        {"event_ticker": "KXWCGAME-C", "market_ticker": "KXWCGAME-26JUN25-NED", "side": "yes", "yes_settlement_value_dollars": "0.0000"},
    ]},
    "KXWCGAME-26JUN25-CIV": {"yes_sub_title": "Ivory Coast", "result": "yes"},
    "KXWCGAME-26JUN25-GER": {"yes_sub_title": "Germany", "result": "yes"},
    "KXWCGAME-26JUN25-NED": {"yes_sub_title": "Netherlands", "result": "no"},
}
FULL_CASH = "37.1777"  # GOLDEN_CASH 44.753 - 7.5753
FULL_NET = D("3.9757")  # 4.3812 realized - 0.20 fee - 0.2055 unrealized = 37.1777 + 1.798 - 35
EXPECTED_LEGS = [
    {"name": "Ivory Coast", "side": "Yes", "result": "hit"},
    {"name": "Germany", "side": "Yes", "result": "hit"},
    {"name": "Netherlands", "side": "Yes", "result": "missed"},
]


class FakeClient:
    """Stands in for the Kalshi API. Everything is strings/ints, like the real thing."""

    def __init__(self, fills=None, settlements=None, positions=None, cash=GOLDEN_CASH,
                 portfolio_cents=GOLDEN_PORTFOLIO_CENTS, bids=None, titles=None, markets=None):
        self.fills = GOLDEN_FILLS if fills is None else fills
        self.settlements = GOLDEN_SETTLEMENTS if settlements is None else settlements
        self.positions = GOLDEN_POSITIONS if positions is None else positions
        self.cash = cash
        self.portfolio_cents = portfolio_cents
        self.bids = bids or {GOLDEN: ("0.69", "0.31")}
        self.titles = TITLES if titles is None else titles
        self.markets = markets or {}

    def get(self, endpoint, params=None, allow_missing=False):
        if endpoint == "/portfolio/balance":
            # Kalshi's integer-cents view of the balance (informational; sub-cent cash is dropped).
            cents = int((D(self.cash) * 100).to_integral_value(rounding=ROUND_FLOOR))
            return {"balance": cents, "balance_dollars": self.cash, "portfolio_value": self.portfolio_cents}
        if endpoint.startswith("/markets/"):
            code = endpoint.rsplit("/", 1)[-1]
            yes_bid, no_bid = self.bids.get(code, (None, None))
            market = {"title": self.titles.get(code, ""), "result": "", "yes_bid_dollars": yes_bid, "no_bid_dollars": no_bid}
            market.update(self.markets.get(code, {}))
            return {"market": market}
        return None

    def paginate(self, endpoint, list_key, extra=None):
        return {
            "/portfolio/fills": self.fills,
            "/historical/fills": [],
            "/portfolio/settlements": self.settlements,
            "/portfolio/positions": self.positions,
        }[endpoint]


def money_fields(node, path=""):
    """Yield (path, value) for every amount-like leaf, to prove none is a JSON number."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from money_fields(value, path + "." + key if path else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from money_fields(value, "{}.{}".format(path, index))
    else:
        yield path, node


MONEY_KEYS = {
    "cost", "payout", "profit", "fee", "value", "pnl", "day", "amount", "net_pnl", "account_value", "cash",
    "open_value", "deposited", "credits", "trading_fees", "deposit_fees", "total_fees", "realized_pnl",
    "unrealized_pnl", "maker_fees", "taker_fees", "reported", "rounding", "rebates", "contracts", "remaining",
    "stake", "buy_fees", "sell_fees", "net_payout", "price", "bid", "per_contract", "money_in", "change",
}


def bet_identity_failures(bet):
    """The equation identities for ONE bet, from its stored strings."""
    problems = []
    name = bet["title"]
    if D(bet["stake"]) + D(bet["buy_fees"]) != D(bet["cost"]):
        problems.append("{}: stake + buy fees != cost".format(name))
    if bet["price"] is not None and D(bet["contracts"]) * D(bet["price"]) != D(bet["stake"]):
        problems.append("{}: contracts x price != stake".format(name))
    if bet["payout"] is not None:
        if D(bet["payout"]) - D(bet["sell_fees"]) != D(bet["net_payout"]):
            problems.append("{}: payout - sell fees != net payout".format(name))
        if D(bet["net_payout"]) - D(bet["cost"]) != D(bet["profit"]):
            problems.append("{}: net payout - cost != profit".format(name))
    # Fills (plus the settlement / live-bid line) sum exactly to the row.
    buys = [fill for fill in bet["fills"] if fill["action"] == "buy"]
    sells = [fill for fill in bet["fills"] if fill["action"] == "sell"]
    for fill in bet["fills"]:
        if D(fill["contracts"]) * D(fill["price"]) != D(fill["amount"]):
            problems.append("{}: a fill's contracts x price != amount".format(name))
    if sum((D(fill["contracts"]) for fill in buys), D(0)) != D(bet["contracts"]):
        problems.append("{}: buy fills' contracts != contracts".format(name))
    if sum((D(fill["amount"]) for fill in buys), D(0)) != D(bet["stake"]):
        problems.append("{}: buy fills don't sum to stake".format(name))
    if sum((D(fill["fee"]) for fill in buys), D(0)) != D(bet["buy_fees"]):
        problems.append("{}: buy fills' fees don't sum to buy fees".format(name))
    if sum((D(fill["fee"]) for fill in sells), D(0)) != D(bet["sell_fees"]):
        problems.append("{}: sell fills' fees don't sum to sell fees".format(name))
    if bet["payout"] is not None:
        back = sum((D(fill["amount"]) for fill in sells), D(0))
        if bet["settlement"]:
            back += D(bet["settlement"]["amount"])
            if D(bet["settlement"]["contracts"]) * D(bet["settlement"]["per_contract"]) != D(bet["settlement"]["amount"]):
                problems.append("{}: settlement contracts x per contract != amount".format(name))
        if bet["live"]:
            back += D(bet["live"]["amount"])
            if D(bet["live"]["contracts"]) * D(bet["live"]["bid"]) != D(bet["live"]["amount"]):
                problems.append("{}: live contracts x bid != amount".format(name))
        if back != D(bet["payout"]):
            problems.append("{}: sells + settlement + live bid != payout".format(name))
    if bet["status"] == "open" and not bet["unrealized"]:
        problems.append("{}: open bet not marked unrealized".format(name))
    return problems


def identity_failures(dashboard, fills=None):
    """Every exactness identity the dashboard must satisfy. Returns a list of failures (empty = all hold)."""
    problems = []
    summ = dashboard["summary"]

    for path, value in money_fields(dashboard):
        if path.rsplit(".", 1)[-1] in MONEY_KEYS and value is not None and not isinstance(value, str):
            problems.append("{} is stored as {} {!r}, not a string".format(path, type(value).__name__, value))
        if isinstance(value, float):
            problems.append("{} is a float".format(path))

    bets = dashboard["bets"]
    if len(bets) != summ["bets"]:
        problems.append("bets list has {} rows, summary says {}".format(len(bets), summ["bets"]))
    for bet in bets:
        problems += bet_identity_failures(bet)

    finished = [bet for bet in bets if bet["status"] in ("sold", "settled")]
    open_bets = [bet for bet in bets if bet["status"] == "open"]
    realized = sum((D(bet["profit"]) for bet in finished), D(0))
    if realized != D(summ["realized_pnl"]):
        problems.append("realized {} != sum of finished bets {}".format(summ["realized_pnl"], realized))
    if summ.get("unrealized_pnl") is not None:
        unrealized = sum((D(bet["profit"]) for bet in open_bets), D(0))
        if unrealized != D(summ["unrealized_pnl"]):
            problems.append("unrealized {} != sum of open bets {}".format(summ["unrealized_pnl"], unrealized))
    for key in ("won", "lost", "sold", "open", "pending"):
        if summ[key] != sum(1 for bet in bets if bet["outcome"] == key):
            problems.append("summary {} count is wrong".format(key))

    # Categories sum exactly to total realized P&L.
    cat_total = sum((D(cat["profit"]) for cat in dashboard["categories"]), D(0))
    if cat_total != D(summ["realized_pnl"]):
        problems.append("categories sum {} != realized {}".format(cat_total, summ["realized_pnl"]))

    # Chart: running total is the cumulative sum of days at every point; the
    # last point is net P&L; each day is the exact sum of its items.
    running = D(0)
    for point in dashboard["pnl_series"]:
        running += D(point["day"])
        if D(point["pnl"]) != running:
            problems.append("chart {}: running {} != cumulative {}".format(point["date"], point["pnl"], running))
        items_total = sum((D(item["amount"]) for item in point["items"]), D(0))
        if items_total != D(point["day"]):
            problems.append("chart {}: items {} != day {}".format(point["date"], items_total, point["day"]))
    if dashboard["pnl_series"] and D(dashboard["pnl_series"][-1]["pnl"]) != D(summ["net_pnl"]):
        problems.append("last chart point {} != net {}".format(dashboard["pnl_series"][-1]["pnl"], summ["net_pnl"]))

    # Account-value chart: each weekly point = money in + P&L to that date; changes add up;
    # the last point is today's account value.
    weekly = dashboard.get("account_series") or []
    previous = None
    for point in weekly:
        if D(point["account_value"]) != D(point["money_in"]) + D(point["pnl"]):
            problems.append("account chart {}: value != money in + pnl".format(point["date"]))
        if previous is not None and D(point["change"]) != D(point["account_value"]) - previous:
            problems.append("account chart {}: change is wrong".format(point["date"]))
        previous = D(point["account_value"])
    if weekly and D(weekly[-1]["account_value"]) != D(summ["account_value"]):
        problems.append("last account chart point {} != account value {}".format(weekly[-1]["account_value"], summ["account_value"]))

    # Net P&L == account value - deposits - credits; account value == cash + open value.
    if D(summ["net_pnl"]) != D(summ["account_value"]) - D(summ["deposited"]) - D(summ["credits"]):
        problems.append("net != account - deposits - credits")
    if D(summ["account_value"]) != D(summ["cash"]) + D(summ["open_value"]):
        problems.append("account != cash + open value")
    if summ.get("net_pnl_basis") == "bets_at_bid":
        # The headline is exactly what the rows add up to, minus the deposit fee.
        rows_total = sum((D(bet["profit"]) for bet in bets if bet["profit"] is not None
                          and bet["status"] in ("sold", "settled", "open")), D(0))
        if D(summ["net_pnl"]) != rows_total - D(summ["deposit_fees"]):
            problems.append("headline {} != sum of row profits {} - deposit fee {}".format(
                summ["net_pnl"], rows_total, summ["deposit_fees"]))
        live_total = sum((D(bet["live"]["amount"]) for bet in bets if bet["status"] == "open" and bet["live"]), D(0))
        if D(summ["open_value"]) != live_total:
            problems.append("open value {} != sum of open bets at bid {}".format(summ["open_value"], live_total))

    # Fees: total == trading + deposit; trading == exact sum of every fill's fee;
    # trading == reported + rounding - rebates; maker + taker == trading.
    fees = dashboard["fees"]
    if D(summ["total_fees"]) != D(summ["trading_fees"]) + D(summ["deposit_fees"]):
        problems.append("total fees != trading + deposit")
    if D(fees["maker_fees"]) + D(fees["taker_fees"]) != D(summ["trading_fees"]):
        problems.append("maker + taker fees != trading fees")
    if D(fees["reported"]) + D(fees["rounding"]) - D(fees["rebates"]) != D(summ["trading_fees"]):
        problems.append("reported + rounding - rebates != trading fees")
    # Fees page: before fees - buy fees - sell fees - deposit fee = headline, exactly;
    # buy + sell fees = trading fees; each bet's fee = its buy + sell fees.
    if "before_fees_pnl" in fees:
        if D(fees["before_fees_pnl"]) - D(fees["buy_total"]) - D(fees["sell_total"]) - D(summ["deposit_fees"]) != D(summ["net_pnl"]):
            problems.append("fees page equation doesn't land on the headline")
        if D(fees["buy_total"]) + D(fees["sell_total"]) != D(summ["trading_fees"]):
            problems.append("buy + sell fees != trading fees")
        if sum((D(bet["stake"]) for bet in bets), D(0)) != D(fees["stake_total"]):
            problems.append("stake total != sum of stakes")
    for bet in bets:
        if "fee" in bet and D(bet["fee"]) != D(bet["buy_fees"]) + D(bet["sell_fees"]):
            problems.append("{}: fee != buy fees + sell fees".format(bet["title"]))
    if fills is not None and sum((fill["fee"] for fill in fills), D(0)) != D(summ["trading_fees"]):
        problems.append("trading fees != exact sum of fill fees")
    if dashboard.get("max_decimal_places", 0) > 18:
        problems.append("max_decimal_places {} exceeds exact.js SCALE 18".format(dashboard["max_decimal_places"]))
    return problems


def golden_dashboard(**kwargs):
    """Run the real pipeline (fetch -> build -> reconcile) on the golden fixture."""
    client = FakeClient(**kwargs)
    dashboard, fills, payouts, cash, portfolio = kalshi_fetch.build_from_api(client)
    kalshi_fetch.reconcile(dashboard, fills, payouts, cash, portfolio)
    return dashboard, fills


def full_dashboard():
    """Golden fixture plus the 3-leg World Cup parlay (used by the display and JS parity tests)."""
    client = FakeClient(fills=GOLDEN_FILLS + PARLAY_FILLS, settlements=GOLDEN_SETTLEMENTS + PARLAY_SETTLEMENTS,
                        cash=FULL_CASH, markets=PARLAY_MARKETS)
    dashboard, fills, payouts, cash, portfolio = kalshi_fetch.build_from_api(client)
    kalshi_fetch.reconcile(dashboard, fills, payouts, cash, portfolio)
    return dashboard, fills
