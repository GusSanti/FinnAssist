import unittest
from datetime import date

from app.services.financial_service import (
    _month_bounds,
    _selected_month,
    _shift_month,
)


class FinancialPeriodTests(unittest.TestCase):
    def test_month_bounds_for_regular_month(self):
        self.assertEqual(
            _month_bounds(2026, 9),
            (date(2026, 9, 1), date(2026, 10, 1)),
        )

    def test_month_bounds_for_december(self):
        self.assertEqual(
            _month_bounds(2026, 12),
            (date(2026, 12, 1), date(2027, 1, 1)),
        )

    def test_shift_month_across_year(self):
        self.assertEqual(_shift_month(2026, 1, -1), (2025, 12))

    def test_rejects_invalid_month(self):
        with self.assertRaisesRegex(ValueError, "month must be between 1 and 12"):
            _month_bounds(2026, 13)

    def test_rejects_incomplete_period(self):
        with self.assertRaisesRegex(
            ValueError,
            "year and month must be provided together",
        ):
            _selected_month(2026, None)


if __name__ == "__main__":
    unittest.main()
