"""Build kalshi/data.json from a Kalshi "Recent Activity" CSV export.

Fallback for before the API secrets are set up. The CSV has fills but no
settlement payouts and no market titles, so:
  - bets sold back before settlement get exact results (YES+NO pairs pay $1),
  - bets that ran to settlement are marked "pending" until the API fills them in,
  - titles come from the hand-written SEED_TITLES map below,
  - account value / cash / open value come from SNAPSHOT (read off the app).

Usage:
    python scripts/kalshi_from_csv.py ~/Downloads/Kalshi-Recent-Activity-All.csv

Don't commit the CSV itself: it contains order and market IDs.
"""

import csv
import sys

from kalshi_common import build_dashboard, group_fills, make_bet, money, parse_time, write_if_changed

# Read off the Kalshi app on Oct 10, 2026.
SNAPSHOT = {"date": "2026-10-10", "cash": 28.01, "open_value": 7.30}

# Markets still open on the snapshot date.
OPEN_TICKERS = {
    "KXNFLRECYDS-26OCT11CHIGB-GBMGOLDEN0-40",
    "KXNFLRECYDS-26OCT11LVNE-NERDOUBS87-40",
    "KXNFLRECYDS-26OCT11CLENYJ-CLEDBOSTON12-60",
}

# The CSV's Market_Title column is empty, so readable titles live here.
SEED_TITLES = {
    "KXNFLRECYDS-26OCT11CHIGB-GBMGOLDEN0-40": "Matthew Golden 40+ receiving yards",
    "KXNFLRECYDS-26OCT11LVNE-NERDOUBS87-40": "Romeo Doubs 40+ receiving yards",
    "KXNFLRECYDS-26OCT11CLENYJ-CLEDBOSTON12-60": "Denzel Boston 60+ receiving yards",
    "KXNFLGAME-26SEP27HOUIND-HOU": "Texans vs. Colts: Houston wins",
    "KXNFLPASSYDS-26SEP24ATLGB-ATLMPENIX9-275": "Michael Penix Jr. 275+ passing yards",
    "KXNFLTD-26SEP24ATLGB-ATLBROBINSON7-1": "Bijan Robinson anytime touchdown",
    "KXNFLGAME-26SEP24ATLGB-GB": "Falcons vs. Packers: Green Bay wins",
    "KXF1RACE-AZEGP26-ANT": "Azerbaijan GP winner: Kimi Antonelli",
    "KXWCADVANCE-26JUL01USABIH-USA": "World Cup: USA advances vs. Bosnia",
    "KXWCADVANCE-26JUN30MEXECU-MEX": "World Cup: Mexico advances vs. Ecuador",
    "KXBTCD-26JUN3019-T58499.99": "Bitcoin above $58,500 on Jun 30",
    "KXMVESPORTSMULTIGAMEEXTENDED-S20260905EFE5661-C299BAD43AB": "Multi-game sports parlay",
    "KXWCGROUPWIN-26B-CAN": "World Cup Group B winner: Canada",
    "KXNBAPTS-26MAY06MINSAS-MINJMCDANIELS3-10": "Jaden McDaniels 10+ points",
    "KXNBAGAME-26FEB04BOSHOU-HOU": "Celtics vs. Rockets: Houston wins",
    "KXNCAAMBGAME-26FEB03NEVBSU-BSU": "Nevada vs. Boise State: Boise State wins",
    "KXHONDURASPRES-25-NASF": "Honduras presidential election: Asfura wins",
}


def formula_fee(row, yes_price):
    """Kalshi's taker fee, 0.07 x contracts x P x (1 - P), left unrounded.

    Used ONLY for an open position's cost basis. The CSV's Fee_In_Dollars is
    rounded per fill and runs ~1-2c low, so a cost basis built from it misses
    the app's display; the unrounded formula matches it for all three open
    positions. Every fee TOTAL uses Fee_In_Dollars, Kalshi's own record.
    Maker fills were $0 in every row of the CSV.
    """
    if row["Order_Type"] != "Taker":
        return 0.0
    return 0.07 * float(row["Amount_In_Dollars"]) * yes_price * (1 - yes_price)


def read_fills(csv_path):
    fills = []
    with open(csv_path, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("type") != "Trade":
                continue
            side = row["Direction"].lower()
            # Price_In_Cents is ALWAYS the Yes price, whatever the Direction.
            # A "No" fill at P means the No side traded at (100 - P) cents; if
            # it closes a Yes position, Yes was sold at P cents.
            yes_price = float(row["Price_In_Cents"]) / 100
            fills.append(
                {
                    "ticker": row["Market_Ticker"],
                    "side": side,
                    # Despite the column name, this is the contract count:
                    # it matches the order's "Filled" quantity, and the fees
                    # only reconcile (to $3.23) when read that way.
                    "count": float(row["Amount_In_Dollars"]),
                    "price": round(yes_price if side == "yes" else 1 - yes_price, 6),
                    "fee": float(row["Fee_In_Dollars"] or 0),
                    "cost_fee": formula_fee(row, yes_price),
                    "is_taker": row["Order_Type"] == "Taker",
                    "time": parse_time(row["Original_Date"]),
                }
            )
    return fills


# The app rounds to the cent and the CSV's fee column is rounded per fill, so
# allow a cent and a half of drift on these older checks.
CHECK_TOLERANCE = 0.015


def expect(label, actual, target):
    if abs(actual - target) > CHECK_TOLERANCE:
        raise SystemExit("CSV check failed: {} = {:.4f}, app shows {:.2f}".format(label, actual, target))


def expect_cents(label, actual, target):
    """Exact match to the cent, after the app's half-up rounding."""
    if money(actual) != target:
        raise SystemExit("CSV check failed: {} = {:.2f}, app shows {:.2f}".format(label, money(actual), target))


def fills_for(fills, ticker, side):
    return [fill for fill in fills if fill["ticker"] == ticker and fill["side"] == side]


def check_against_app(fills, bets_by_ticker):
    """Numbers read off the Kalshi app, so the Yes/No price bug can't come back.

    Each check runs only if its market is in the CSV being parsed.
    """
    mexico = "KXWCADVANCE-26JUN30MEXECU-MEX"
    penix = "KXNFLPASSYDS-26SEP24ATLGB-ATLMPENIX9-275"
    doubs = "KXNFLRECYDS-26OCT11LVNE-NERDOUBS87-40"
    canada = "KXWCGROUPWIN-26B-CAN"

    if mexico in bets_by_ticker:
        # Direction No, price 95 -> "Sold Yes at 95c", $1.81.
        closing = fills_for(fills, mexico, "no")
        expect("Mexico sold-Yes proceeds", sum(fill["count"] * (1 - fill["price"]) for fill in closing), 1.81)

    if penix in bets_by_ticker:
        # Direction No, price 17 -> "Bought No at 83.9c" incl. fee, $1.01.
        opening = fills_for(fills, penix, "no")
        expect("Penix No cost incl. fee", sum(fill["count"] * fill["price"] + fill["fee"] for fill in opening), 1.01)

    if doubs in bets_by_ticker:
        # Direction No, price 59 -> "Bought No at 42.6c", $2.18.
        opening = fills_for(fills, doubs, "no")
        total = sum(fill["count"] * fill["price"] + fill["fee"] for fill in opening)
        contracts = sum(fill["count"] for fill in opening)
        expect("Doubs No cost incl. fee", total, 2.18)
        expect("Doubs No price per contract", total / contracts, 0.426)

    if canada in bets_by_ticker:
        # Bought 74 Yes @ 14c = $10.99 with fees; sold Yes @ 33c = $23.27 net
        # of the $1.14 fee; profit +$12.28.
        opening = fills_for(fills, canada, "yes")
        closing = fills_for(fills, canada, "no")
        expect("Canada Yes cost incl. fees", sum(fill["count"] * fill["price"] + fill["fee"] for fill in opening), 10.99)
        expect(
            "Canada sold-Yes proceeds net of fee",
            sum(fill["count"] * (1 - fill["price"]) - fill["fee"] for fill in closing),
            23.27,
        )
        expect("Canada profit", bets_by_ticker[canada]["profit"], 12.28)
        # The dashboard row itself, on the app's basis.
        expect_cents("Canada row cost incl. fees", bets_by_ticker[canada]["cost"], 10.99)
        expect("Canada row payout net of fee", bets_by_ticker[canada]["payout"], 23.27)

    # The display-only formula fee should never stray far from what the CSV recorded.
    for fill in fills:
        expect("formula fee vs CSV Fee_In_Dollars on a " + fill["side"] + " fill", fill["cost_fee"], fill["fee"])

    # Open-position cost basis including fees, as the app shows it.
    app_cost_basis = {
        "KXNFLRECYDS-26OCT11CHIGB-GBMGOLDEN0-40": ("Golden", 1.99),
        "KXNFLRECYDS-26OCT11LVNE-NERDOUBS87-40": ("Doubs", 2.18),
        "KXNFLRECYDS-26OCT11CLENYJ-CLEDBOSTON12-60": ("Boston", 3.50),
    }
    present = [ticker for ticker in app_cost_basis if ticker in bets_by_ticker]
    for ticker in present:
        name, target = app_cost_basis[ticker]
        expect_cents(name + " open cost basis incl. fees", bets_by_ticker[ticker]["cost"], target)
    if len(present) == len(app_cost_basis):
        total = sum(bets_by_ticker[ticker]["cost"] for ticker in present)
        expect_cents("open cost basis total", total, 7.67)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/kalshi_from_csv.py <Kalshi-Recent-Activity.csv>")

    fills = read_fills(sys.argv[1])
    bets = []
    bets_by_ticker = {}
    for entry in group_fills(fills):
        ticker = entry["ticker"]
        title = SEED_TITLES.get(ticker, "Kalshi market")
        bet = make_bet(entry, title, is_open=ticker in OPEN_TICKERS)
        bets.append(bet)
        bets_by_ticker[ticker] = bet
    check_against_app(fills, bets_by_ticker)

    dashboard = build_dashboard(
        bets,
        fills,
        cash=SNAPSHOT["cash"],
        open_value=SNAPSHOT["open_value"],
        source="csv",
        fee_source="csv_fee_column",
        pnl_series=None,
        series_note="Seeded from a CSV export. Bets that ran to settlement show as pending "
        "until the live API sync fills in their payouts.",
    )
    # Fee totals must come from Kalshi's own Fee_In_Dollars column, never the
    # display-only formula fee.
    expect_cents("dashboard trading fees vs CSV Fee_In_Dollars sum", dashboard["summary"]["trading_fees"],
                 money(sum(fill["fee"] for fill in fills)))
    expect_cents("dashboard taker fees vs CSV Fee_In_Dollars sum", dashboard["fees"]["taker_fees"],
                 money(sum(fill["fee"] for fill in fills if fill["is_taker"])))

    # With most settlements unknown, a per-bet curve would be misleading, so
    # the CSV chart only shows the two points we actually know.
    net = dashboard["summary"]["net_pnl"]
    dashboard["pnl_series"] = [
        {"date": "2025-12-02", "day": -0.20, "pnl": -0.20, "items": [{"label": "Deposit fee", "amount": -0.20}]},
        {
            "date": SNAPSHOT["date"],
            "day": money(net + 0.20),
            "pnl": net,
            "items": [{"label": "Net change to the CSV snapshot (per-bet dates need the API)", "amount": money(net + 0.20)}],
        },
    ]

    wrote = write_if_changed(dashboard)
    summary = dashboard["summary"]
    print("wrote kalshi/data.json" if wrote else "no change, kept kalshi/data.json")
    print("bets={bets} resolved={resolved} pending={pending} open={open} net_pnl={net_pnl}".format(**summary))


if __name__ == "__main__":
    main()
