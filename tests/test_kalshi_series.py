"""Tests for the daily step-chart series and the dashboard's finished-bet lists."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import kalshi_common  # noqa: E402


def finished(title, resolved, profit, status="settled"):
    return {"title": title, "resolved": resolved, "profit": profit, "status": status}


class DailySeriesTests(unittest.TestCase):
    def test_same_day_results_become_one_step(self):
        bets = [finished("A", "2026-09-24", -0.99), finished("B", "2026-09-24", 1.49, "sold"), finished("C", "2026-09-26", -3.20)]
        points = kalshi_common.daily_series(bets, 0.20, net_pnl=-3.10, today="2026-10-11")
        self.assertEqual([point["date"] for point in points], ["2025-12-02", "2026-09-24", "2026-09-26", "2026-10-11"])
        self.assertEqual(len({point["date"] for point in points}), len(points))  # no duplicate days
        self.assertEqual(points[1]["day"], 0.50)
        self.assertEqual(points[1]["pnl"], 0.30)
        self.assertEqual([item["label"] for item in points[1]["items"]], ["B", "A"])  # biggest win first

    def test_last_point_ends_at_net_pnl_with_open_mark(self):
        bets = [finished("A", "2026-09-24", 2.00)]
        points = kalshi_common.daily_series(bets, 0.20, net_pnl=1.33, today="2026-10-11")
        self.assertEqual(points[-1]["pnl"], 1.33)
        self.assertEqual(points[-1]["items"], [{"label": kalshi_common.OPEN_POSITIONS_LABEL, "amount": -0.47}])

    def test_running_total_is_sum_of_days(self):
        bets = [finished("A", "2026-01-01", 1.11), finished("B", "2026-02-02", -2.22), finished("C", "2026-02-02", 3.33)]
        points = kalshi_common.daily_series(bets, 0.20, net_pnl=2.02, today="2026-10-11")
        running = 0.0
        for point in points:
            running += point["day"]
            self.assertAlmostEqual(point["pnl"], round(running, 2), places=6)

    def test_many_bets_in_one_day_are_capped(self):
        bets = [finished("Bet %d" % num, "2026-03-03", 1.0) for num in range(11)]
        points = kalshi_common.daily_series(bets, 0.0, net_pnl=11.0, today="2026-03-03")
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0]["items"][-1], {"label": "3 more", "amount": 3.0})
        self.assertEqual(points[0]["day"], 11.0)


if __name__ == "__main__":
    unittest.main()
