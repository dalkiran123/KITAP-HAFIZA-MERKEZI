"""Regression tests for ChessOnline Glicko-2 and virtual roster."""
import unittest
from chess_rating import Rating, BOT_ROSTER, league, update_rating


class RatingTests(unittest.TestCase):
    def test_reference_example(self):
        # Glicko-2 specification example, tau=0.5.
        result = update_rating(Rating(1500, 200, 0.06), [
            (Rating(1400, 30), 1),
            (Rating(1550, 100), 0),
            (Rating(1700, 300), 0),
        ])
        self.assertAlmostEqual(result.rating, 1464.06, delta=0.15)
        self.assertAlmostEqual(result.rd, 151.52, delta=0.15)
        self.assertAlmostEqual(result.volatility, 0.05999, delta=0.0001)

    def test_no_games_increases_uncertainty(self):
        result = update_rating(Rating(1500, 100, 0.06), [])
        self.assertEqual(result.rating, 1500)
        self.assertGreater(result.rd, 100)

    def test_roster_is_explicitly_virtual(self):
        self.assertEqual(len(BOT_ROSTER), 10)
        self.assertEqual(sum(b["level"] == "beginner" for b in BOT_ROSTER), 4)
        self.assertEqual(sum(b["level"] == "intermediate" for b in BOT_ROSTER), 3)
        self.assertEqual(sum(b["level"] == "advanced" for b in BOT_ROSTER), 3)
        self.assertTrue(all(b["is_bot"] for b in BOT_ROSTER))
        self.assertEqual(len({b["id"] for b in BOT_ROSTER}), 10)

    def test_leagues(self):
        self.assertEqual(league(1199), "Acemi")
        self.assertEqual(league(1200), "Gelişen")
        self.assertEqual(league(1500), "Orta")
        self.assertEqual(league(1800), "İleri")
        self.assertEqual(league(2100), "Usta")


if __name__ == "__main__":
    unittest.main()
