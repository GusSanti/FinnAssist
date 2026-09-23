import json
import unittest
from decimal import Decimal
from unittest.mock import patch

from app.ai.financial_tools import execute_financial_tool


class FinancialToolTests(unittest.TestCase):
    def test_executes_allow_listed_function_with_bound_user(self):
        def fake_summary(user_id, year=None, month=None, average_months=6):
            return {"user_id": user_id, "balance": Decimal("42.50")}

        with patch.dict(
            "app.ai.financial_tools.TOOL_FUNCTIONS",
            {"get_financial_summary": fake_summary},
            clear=True,
        ):
            result = execute_financial_tool(
                "get_financial_summary",
                {"year": 2026, "month": 9},
                user_id=7,
            )

        self.assertEqual(
            json.loads(result),
            {"user_id": 7, "balance": "42.50"},
        )

    def test_rejects_model_supplied_user_id(self):
        result = execute_financial_tool("get_balance", {"user_id": 999}, user_id=7)
        self.assertIn("não pode ser definido", json.loads(result)["error"])

    def test_rejects_unknown_tool(self):
        result = execute_financial_tool("drop_database", {}, user_id=7)
        self.assertEqual(json.loads(result), {"error": "Ferramenta desconhecida."})


if __name__ == "__main__":
    unittest.main()
