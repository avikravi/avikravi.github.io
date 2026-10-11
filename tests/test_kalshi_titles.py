"""Tests for titles, categories and resolution dates in scripts/kalshi_fetch.py."""

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import kalshi_fetch  # noqa: E402
from kalshi_common import category_for  # noqa: E402
from kalshi_common import parse_time  # noqa: E402

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

    def test_world_cup_parlay_from_legs_is_clipped(self):
        market = {"title": "yes Ivory Coast,yes Germany,yes Netherlands",
                  "mve_selected_legs": [{"market_ticker": "KXWCGAME-A"}, {"market_ticker": "KXWCGAME-B"}]}
        title = title_for("KXMVESPORTSMULTIGAMEEXTENDED-NEW", market)
        self.assertEqual(title, "WC Parlay: Ivory Coast, Germany, Nether…")
        self.assertLessEqual(len(title), 40)

    def test_known_world_cup_parlay_without_legs(self):
        title = title_for("KXMVESPORTSMULTIGAMEEXTENDED-S20260905EFE5661-C299BAD43AB",
                          {"title": "yes Ivory Coast,yes Germany,yes Netherlands"})
        self.assertTrue(title.startswith("WC Parlay: Ivory Coast, Germany"))

    def test_mixed_parlay_and_no_legs(self):
        market = {"title": "yes Chiefs,no Lakers",
                  "mve_selected_legs": [{"market_ticker": "KXNFLGAME-A"}, {"market_ticker": "KXNBAGAME-B"}]}
        self.assertEqual(title_for("KXMVE-X", market), "Parlay: Chiefs, not Lakers")

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
            {"ticker": "KXWCGROUPWIN-26B-CAN", "side": "yes", "count": 74, "price": 0.14, "fee": 0.63,
             "is_taker": True, "time": parse_time("2026-01-22T07:15:00Z")},
            {"ticker": "KXWCGROUPWIN-26B-CAN", "side": "no", "count": 74, "price": 0.67, "fee": 1.14,
             "is_taker": True, "time": parse_time("2026-06-18T17:47:00Z")},
        ]
        entry = group_fills(fills)[0]
        bet = make_bet(entry, "Canada", settlement_payout=0.0, resolved_time=parse_time("2026-06-24T22:00:00Z"))
        self.assertEqual(bet["status"], "sold")
        self.assertEqual(bet["resolved"], "2026-06-18")
        self.assertEqual(bet["profit"], 12.29)


if __name__ == "__main__":
    unittest.main()
