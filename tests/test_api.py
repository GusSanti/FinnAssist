import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class ApiTests(unittest.TestCase):
    def test_health(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "FinAssist API funcionando")

    def test_home_serves_interface(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("FinAssist", response.text)

    @patch("app.api.categories.list_categories")
    def test_lists_categories(self, mock_list):
        mock_list.return_value = [{"id": 1, "name": "Alimentação", "type": "EXPENSE"}]
        response = client.get("/categories?type=EXPENSE")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["name"], "Alimentação")
        mock_list.assert_called_once_with("EXPENSE")

    @patch("app.api.transactions.create_transaction")
    def test_creates_transaction(self, mock_create):
        mock_create.return_value = {
            "id": 10,
            "user_id": 1,
            "category_id": 1,
            "category": "Alimentação",
            "description": "Mercado",
            "amount": Decimal("100.50"),
            "type": "EXPENSE",
            "transaction_date": date(2026, 9, 24),
            "created_at": datetime(2026, 9, 24, 12, 0),
        }
        response = client.post(
            "/users/1/transactions",
            json={
                "category_id": 1,
                "description": "Mercado",
                "amount": "100.50",
                "type": "EXPENSE",
                "transaction_date": "2026-09-24",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["amount"], "100.50")
        mock_create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
