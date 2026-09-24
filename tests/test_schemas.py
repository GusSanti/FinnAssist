import unittest
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from app.schemas.category import CategoryCreate
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class SchemaTests(unittest.TestCase):
    def test_category_name_is_normalized(self):
        category = CategoryCreate(name="  Casa   e contas ", type="EXPENSE")
        self.assertEqual(category.name, "Casa e contas")

    def test_transaction_requires_positive_amount(self):
        with self.assertRaises(ValidationError):
            TransactionCreate(
                category_id=1,
                description="Teste",
                amount=Decimal("0"),
                type="EXPENSE",
                transaction_date=date(2026, 9, 24),
            )

    def test_empty_transaction_update_is_rejected(self):
        with self.assertRaises(ValidationError):
            TransactionUpdate()


if __name__ == "__main__":
    unittest.main()
