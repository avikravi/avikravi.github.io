"""Tests for the daily step-chart series and the dashboard's finished-bet lists."""

import unittest
from decimal import Decimal

import kalshi_paths  # noqa: F401
import kalshi_common

D = Decimal


def finished(title, resolved, profit, status="settled"):
    return {"title": title, "resolved": resolved, "profit": D(profit), "status": status}


class DailySeriesTests(unittest.TestCase):
    def test_same_day_results_become_one_step(self):
        bets = [finished("A", "2026-09-24", "-0.99"), finished("B", "2026-09-24", "1.4878", "sold"),
                finished("C", "2026-09-26", "-3.20")]
        points = kalshi_common.daily_series(bets, D("0.20"), net_pnl=D("-3.10"), today="2026-10-11")
        self.assertEqual([point["date"] for point in points], ["2025-12-02", "2026-09-24", "2026-09-26", "2026-10-11"])
        self.assertEqual(len({point["date"] for point in points}), len(points))  # no duplicate days
        self.assertEqual(points[1]["day"], "0.4978")   # exact: -0.99 + 1.4878
        self.assertEqual(points[1]["pnl"], "0.2978")   # exact: -0.20 + 0.4978
        self.assertEqual([item["label"] for item in points[1]["items"]], ["B", "A"])  # biggest win first

    def test_last_point_ends_at_net_pnl_with_open_mark(self):
        bets = [finished("A", "2026-09-24", "2.00")]
        points = kalshi_common.daily_series(bets, D("0.20"), net_pnl=D("1.33"), today="2026-10-11")
        self.assertEqual(points[-1]["pnl"], "1.33")
        self.assertEqual(points[-1]["items"], [{"label": kalshi_common.OPEN_POSITIONS_LABEL, "amount": "-0.47"}])

    def test_running_total_is_sum_of_days(self):
        bets = [finished("A", "2026-01-01", "1.111111"), finished("B", "2026-02-02", "-2.22"),
                finished("C", "2026-02-02", "3.330001")]
        points = kalshi_common.daily_series(bets, D("0.20"), net_pnl=D("2.021112"), today="2026-10-11")
        running = D(0)
        for point in points:
            running += D(point["day"])
            self.assertEqual(D(point["pnl"]), running)  # exact, no tolerance

    def test_many_bets_in_one_day_are_capped(self):
        bets = [finished("Bet {}".format(num), "2026-03-03", "1") for num in range(11)]
        points = kalshi_common.daily_series(bets, D("0"), net_pnl=D("11"), today="2026-03-03")
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0]["items"][-1], {"label": "3 more", "amount": "3"})
        self.assertEqual(points[0]["day"], "11")


if __name__ == "__main__":
    unittest.main()
