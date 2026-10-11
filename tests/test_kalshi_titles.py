"""Tests for titles, categories and resolution dates in scripts/kalshi_fetch.py."""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

import kalshi_paths  # noqa: F401
import kalshi_fetch
import kalshi_fixtures as fx
from kalshi_common import category_for, parse_time

NOW = datetime(2026, 10, 11, tzinfo=timezone.utc)


def title_for(ticker, market, event_title=""):
    return kalshi_fetch.readable_title(ticker, market, lambda: event_title)


class TitleTests(unittest.TestCase):
    def test_override_wins_over_api_title(self):
        self.assertEqual(title_for("KXNFLGAME-26SEP27HOUIND-HOU", {"title": "Houston wins"}), "Texans vs Colts: Texans win")
        self.assertEqual(title_for("KXNFLGAME-26SEP24ATLGB-GB", {"title": "Green Bay wins"}), "Packers vs Falcons: Packers win")

    def test_override_titles_are_short(self):
        for title in kalshi_fetch.TITLE_OVERRIDES.values():
            self.assertLessEqual(len(title), 40, title)

    def test_bare_winner_gets_opponent_from_event(self):
        title = title_for("KXNFLGAME-27JAN01DALNYG-DAL", {"title": "Dallas wins"}, "Dallas at New York G Winner?")
        self.assertEqual(title, "Dallas at New York G: Dallas wins")

    def test_title_with_opponent_is_left_alone(self):
        market = {"title": "Boston at Houston Winner?", "yes_sub_title": "Houston"}
        self.assertEqual(title_for("KXNBAGAME-X", market, "Boston at Houston Winner?"), "Boston at Houston Winner?")
        self.assertEqual(title_for("KXNBAGAME-Y", {"title": "Boston at Houston: Houston wins"}, "Boston at Houston"),
                         "Boston at Houston: Houston wins")

    def test_to_advance_is_collapsed(self):
        market = {"title": "USA vs Bosnia and Herzegovina: To Advance", "yes_sub_title": "USA advances"}
        self.assertEqual(title_for("KXWCADVANCE-X", market), "USA vs Bosnia and Herzegovina: USA advances")
        self.assertEqual(title_for("KXWCADVANCE-Y", {"title": "Mexico vs Ecuador: To Advance: Mexico advances"}),
                         "Mexico vs Ecuador: Mexico advances")

    def test_canada_override(self):
        self.assertEqual(title_for("KXWCGROUPWIN-26B-CAN", {"title": "Will Canada finish first in World Cup Group B?"}),
                         "Canada wins WC Group B")

    def test_usa_override(self):
        self.assertEqual(title_for("KXWCADVANCE-26JUL01USABIH-USA", {"title": "USA vs Bosnia and Herzegovina: To Advance"}),
                         "USA vs Bosnia: USA advances")

    def test_parlay_title_counts_legs(self):
        market = {"title": "yes Ivory Coast,yes Germany,yes Netherlands",
                  "mve_selected_legs": [{"market_ticker": "KXWCGAME-A"}, {"market_ticker": "KXWCGAME-B"},
                                        {"market_ticker": "KXWCGAME-C"}]}
        self.assertEqual(title_for("KXMVESPORTSMULTIGAMEEXTENDED-NEW", market), "Parlay · 3 legs")
        self.assertEqual(title_for("KXMVE-X", {"title": "yes Chiefs,no Lakers"}), "Parlay · 2 legs")

    def test_parlay_legs_results_and_world_cup_tag(self):
        client = fx.FakeClient(markets=fx.PARLAY_MARKETS)
        legs, world_cup = kalshi_fetch.parlay_details(client, fx.PARLAY, fx.PARLAY_MARKETS[fx.PARLAY],
                                                      fx.PARLAY_MARKETS[fx.PARLAY]["title"])
        self.assertEqual(legs, fx.EXPECTED_LEGS)
        self.assertTrue(world_cup)
        for leg in legs:
            self.assertNotIn("KX", repr(leg))  # names only, never tickers

    def test_leg_result_rules(self):
        self.assertEqual(kalshi_fetch.leg_result("yes", "1.0000", None), "hit")
        self.assertEqual(kalshi_fetch.leg_result("yes", "0", None), "missed")
        self.assertEqual(kalshi_fetch.leg_result("no", "0.0000", None), "hit")
        self.assertEqual(kalshi_fetch.leg_result("no", "1", None), "missed")
        self.assertEqual(kalshi_fetch.leg_result("yes", None, {"result": "no"}), "missed")
        self.assertEqual(kalshi_fetch.leg_result("yes", None, {"result": ""}), "unknown")

    def test_parlay_without_api_legs_falls_back_to_title(self):
        legs, world_cup = kalshi_fetch.parlay_details(fx.FakeClient(), fx.PARLAY, {}, "yes Chiefs,no Lakers")
        self.assertEqual(legs, [{"name": "Chiefs", "side": "Yes", "result": "unknown"},
                                {"name": "Lakers", "side": "No", "result": "unknown"}])

    def test_non_parlay_comma_title_untouched(self):
        self.assertEqual(title_for("KXOTHER-X", {"title": "Paris, France: rain"}), "Paris, France: rain")

    def test_bare_winner_without_event_stays_as_is(self):
        self.assertEqual(title_for("KXNFLGAME-Z", {"title": "Dallas wins"}, ""), "Dallas wins")


class CategoryTests(unittest.TestCase):
    def test_world_cup_parlay_from_legs(self):
        market = {"mve_selected_legs": [{"market_ticker": "KXWCGAME-A"}, {"market_ticker": "KXWCGAME-B"}]}
        self.assertEqual(kalshi_fetch.category_from_legs(market), "Soccer")

    def test_mixed_parlay_has_no_leg_category(self):
        market = {"mve_selected_legs": [{"market_ticker": "KXWCGAME-A"}, {"market_ticker": "KXNFLGAME-B"}]}
        self.assertIsNone(kalshi_fetch.category_from_legs(market))

    def test_known_parlay_override_and_college(self):
        self.assertEqual(category_for("KXMVESPORTSMULTIGAMEEXTENDED-S20260905EFE5661-C299BAD43AB"), "Soccer")
        self.assertEqual(category_for("KXNCAAMBGAME-26FEB03NEVBSU-BSU"), "College")
        self.assertEqual(category_for("KXNBAGAME-26FEB04BOSHOU-HOU"), "NBA")


class ResolutionDateTests(unittest.TestCase):
    entry = {"last_time": parse_time("2026-06-25T14:57:00Z")}

    def test_priority_order(self):
        settlement = {"settled_time": "2026-09-06T03:00:00Z"}
        info = {"settlement_ts": "2026-09-06T05:00:00Z", "close_time": "2026-09-06T02:00:00Z"}
        self.assertEqual(kalshi_fetch.resolution_time(settlement, info, self.entry, NOW)[1], "settlement")
        self.assertEqual(kalshi_fetch.resolution_time(None, info, self.entry, NOW),
                         (parse_time("2026-09-06T05:00:00Z"), "market_settlement_ts"))
        self.assertEqual(kalshi_fetch.resolution_time(None, {"close_time": "2026-09-06T02:00:00Z"}, self.entry, NOW)[1],
                         "market_close_time")

    def test_future_close_time_and_missing_fields_fall_back(self):
        self.assertEqual(kalshi_fetch.resolution_time(None, {"close_time": "2027-01-01T00:00:00Z"}, self.entry, NOW),
                         (self.entry["last_time"], "last_fill"))
        self.assertEqual(kalshi_fetch.resolution_time(None, {}, self.entry, NOW)[1], "last_fill")


class SoldBetDateTests(unittest.TestCase):
    def test_sold_bet_resolves_on_sale_date_not_settlement(self):
        from kalshi_common import group_fills, make_bet

        fills = [
            {"ticker": "KXWCGROUPWIN-26B-CAN", "side": "yes", "count": Decimal("74"), "price": Decimal("0.14"),
             "fee": Decimal("0.63"), "is_taker": True, "time": parse_time("2026-01-22T07:15:00Z")},
            {"ticker": "KXWCGROUPWIN-26B-CAN", "side": "no", "count": Decimal("74"), "price": Decimal("0.67"),
             "fee": Decimal("1.15"), "is_taker": True, "time": parse_time("2026-06-18T17:47:00Z")},
        ]
        entry = group_fills(fills)[0]
        bet = make_bet(entry, "Canada", settlement_payout=Decimal("0"), resolved_time=parse_time("2026-06-24T22:00:00Z"))
        self.assertEqual(bet["status"], "sold")
        self.assertEqual(bet["resolved"], "2026-06-18")
        self.assertEqual(bet["profit"], Decimal("12.28"))  # 23.27 - 10.99, exactly


if __name__ == "__main__":
    unittest.main()
