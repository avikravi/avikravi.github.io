"""Golden API fixtures and the exact identity checks shared by the Kalshi tests.

Fills are API-shaped (strings, like Kalshi sends). Expected values are worked
out by hand below as Decimal literals, independently of the pipeline.

Golden fills (fee_cost values for Robinson/Penix/Mexico are the trade fee
rounded up to $0.0001, matching what the dashboard showed; Canada's are the
two charged amounts that reproduce the app's $10.99 / $23.27):
  Robinson  buy 3.52 YES @ 0.55, fee 0.0610; sell 3.52 YES @ 0.99 (maker, fee 0)
            cost 1.936 + 0.061 = 1.997; payout 3.52 x 0.99 = 3.4848; profit 1.4878
  Penix     buy 1.20 NO @ 0.83, fee 0.0119; sell 1.20 NO @ 0.99 (maker)
            cost 0.996 + 0.0119 = 1.0079; payout 1.188; profit 0.1801
  Mexico    buy 1.90 YES @ 0.64, fee 0.0307; sell 1.90 YES @ 0.95 (maker)
            cost 1.216 + 0.0307 = 1.2467; payout 1.805; profit 0.5583
  Canada    buy 64 + 10 YES @ 0.14 (one order), fees 0.54 + 0.09; sell 74 YES @ 0.33, fee 1.15
            cost 10.36 + 0.63 = 10.99; payout 24.42 - 1.15 = 23.27; profit 12.28
  Bitcoin   buy 12.32 YES @ 0.79, fee 0.1431; settles YES, revenue 1232c
            cost 9.7328 + 0.1431 = 9.8759; payout 12.32; profit 2.4441
  Texans    buy 16.42 YES @ 0.29, fee 0.2367; settles NO, revenue 0
            cost 4.7618 + 0.2367 = 4.9985; payout 0; profit -4.9985
  Golden    buy 5.80 NO @ 0.33, fee 0.0895; still open, NO bid 0.31
            cost 1.914 + 0.0895 = 2.0035; value 5.80 x 0.31 = 1.798
Cash = 35.00 in - 0.20 deposit fee + 1.4878 + 0.1801 + 0.5583 + 12.28 + 2.4441
       - 4.9985 - 2.0035 = 44.7483 (every change is on the $0.0001 grid)
Portfolio value (Kalshi's own figure) = 180 cents. Net = 44.7483 + 1.80 - 35 = 11.5483.
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
    api_fill(9, CANADA, "o-can-sell", "no", "74.00", "0.3300", "1.15", True, "2026-06-18T17:47:00Z"),
    api_fill(10, BITCOIN, "o-btc", "yes", "12.32", "0.7900", "0.1431", True, "2026-06-30T22:49:00Z"),
    api_fill(11, TEXANS, "o-hou", "yes", "16.42", "0.2900", "0.2367", True, "2026-09-27T18:31:00Z"),
    api_fill(12, GOLDEN, "o-gold", "no", "5.80", "0.6700", "0.0895", True, "2026-10-11T03:24:00Z"),
]

GOLDEN_SETTLEMENTS = [
    {"ticker": BITCOIN, "revenue": 1232, "settled_time": "2026-06-30T23:30:00Z", "fee_cost": "0"},
    {"ticker": TEXANS, "revenue": 0, "settled_time": "2026-09-28T03:00:00Z", "fee_cost": "0"},
]
GOLDEN_POSITIONS = [{"ticker": GOLDEN, "position_fp": "-5.80"}]
GOLDEN_CASH = "44.7483"
GOLDEN_PORTFOLIO_CENTS = 180

# Expected rows, by title, worked out by hand above.
GOLDEN_ROWS = {
    "Bijan Robinson TD": (D("1.997"), D("3.4848"), D("1.4878")),
    "Penix 275+": (D("1.0079"), D("1.188"), D("0.1801")),
    "Mexico advances": (D("1.2467"), D("1.805"), D("0.5583")),
    "Canada wins WC Group B": (D("10.99"), D("23.27"), D("12.28")),
    "Bitcoin $58,500+ on Jun 30, 2026": (D("9.8759"), D("12.32"), D("2.4441")),
    "Texans vs Colts: Texans win": (D("4.9985"), D("0"), D("-4.9985")),
}
GOLDEN_CATEGORIES = {"NFL": D("-3.3306"), "Soccer": D("12.8383"), "Crypto": D("2.4441")}
GOLDEN_NET = D("11.5483")
GOLDEN_OPEN = {"cost": D("2.0035"), "value": D("1.798")}
TITLES = {ROBINSON: "Bijan Robinson TD", PENIX: "Penix 275+", MEXICO: "Mexico advances", GOLDEN: "Golden 40+"}


class FakeClient:
    """Stands in for the Kalshi API. Everything is strings/ints, like the real thing."""

    def __init__(self, fills=None, settlements=None, positions=None, cash=GOLDEN_CASH,
                 portfolio_cents=GOLDEN_PORTFOLIO_CENTS, bids=None, titles=None):
        self.fills = GOLDEN_FILLS if fills is None else fills
        self.settlements = GOLDEN_SETTLEMENTS if settlements is None else settlements
        self.positions = GOLDEN_POSITIONS if positions is None else positions
        self.cash = cash
        self.portfolio_cents = portfolio_cents
        self.bids = bids or {GOLDEN: ("0.69", "0.31")}
        self.titles = TITLES if titles is None else titles

    def get(self, endpoint, params=None, allow_missing=False):
        if endpoint == "/portfolio/balance":
            # Kalshi's integer-cents view of the balance (informational; sub-cent cash is dropped).
            cents = int((D(self.cash) * 100).to_integral_value(rounding=ROUND_FLOOR))
            return {"balance": cents, "balance_dollars": self.cash, "portfolio_value": self.portfolio_cents}
        if endpoint.startswith("/markets/"):
            code = endpoint.rsplit("/", 1)[-1]
            yes_bid, no_bid = self.bids.get(code, (None, None))
            return {"market": {"title": self.titles.get(code, ""), "result": "", "yes_bid_dollars": yes_bid, "no_bid_dollars": no_bid}}
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
    "maker_fees", "taker_fees", "reported", "rounding", "rebates", "contracts",
}


def identity_failures(dashboard, fills=None):
    """Every exactness identity the dashboard must satisfy. Returns a list of failures (empty = all hold)."""
    problems = []
    summ = dashboard["summary"]

    for path, value in money_fields(dashboard):
        if path.rsplit(".", 1)[-1] in MONEY_KEYS and value is not None and not isinstance(value, str):
            problems.append("{} is stored as {} {!r}, not a string".format(path, type(value).__name__, value))
        if isinstance(value, float):
            problems.append("{} is a float".format(path))

    # Row identity: profit == payout - cost, exactly.
    for bet in dashboard["recent_bets"]:
        if bet["profit"] is not None and D(bet["profit"]) != D(bet["payout"]) - D(bet["cost"]):
            problems.append("row {!r}: {} != {} - {}".format(bet["title"], bet["profit"], bet["payout"], bet["cost"]))

    # Categories sum exactly to total realized P&L.
    cat_total = sum((D(cat["profit"]) for cat in dashboard["categories"]), D(0))
    if cat_total != D(summ["realized_pnl"]):
        problems.append("categories sum {} != realized {}".format(cat_total, summ["realized_pnl"]))

    # Chart: running total is the cumulative sum of days at every point; the
    # last point is net P&L; each day is the exact sum of its items when complete.
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

    # Net P&L == account value - deposits - credits; account value == cash + open value.
    if D(summ["net_pnl"]) != D(summ["account_value"]) - D(summ["deposited"]) - D(summ["credits"]):
        problems.append("net != account - deposits - credits")
    if D(summ["account_value"]) != D(summ["cash"]) + D(summ["open_value"]):
        problems.append("account != cash + open value")

    # Fees: total == trading + deposit; trading == exact sum of every fill's fee;
    # trading == reported + rounding - rebates; maker + taker == trading.
    fees = dashboard["fees"]
    if D(summ["total_fees"]) != D(summ["trading_fees"]) + D(summ["deposit_fees"]):
        problems.append("total fees != trading + deposit")
    if D(fees["maker_fees"]) + D(fees["taker_fees"]) != D(summ["trading_fees"]):
        problems.append("maker + taker fees != trading fees")
    if D(fees["reported"]) + D(fees["rounding"]) - D(fees["rebates"]) != D(summ["trading_fees"]):
        problems.append("reported + rounding - rebates != trading fees")
    if fills is not None and sum((fill["fee"] for fill in fills), D(0)) != D(summ["trading_fees"]):
        problems.append("trading fees != exact sum of fill fees")

    # Open totals are the exact sums of the rows.
    rows = dashboard["open_positions"]
    if sum((D(row["cost"]) for row in rows), D(0)) != D(dashboard["open_totals"]["cost"]):
        problems.append("open cost total != sum of rows")
    if dashboard["open_totals"]["value"] is not None:
        if sum((D(row["value"]) for row in rows), D(0)) != D(dashboard["open_totals"]["value"]):
            problems.append("open value total != sum of rows")
    return problems


def golden_dashboard(**kwargs):
    """Run the real pipeline (fetch -> build -> reconcile) on the golden fixture."""
    client = FakeClient(**kwargs)
    dashboard, fills, payouts, cash, portfolio = kalshi_fetch.build_from_api(client)
    kalshi_fetch.reconcile(dashboard, fills, payouts, cash, portfolio)
    return dashboard, fills
