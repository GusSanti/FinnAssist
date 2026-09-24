"""Validation contracts for financial transactions."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.schemas.category import TransactionType


class TransactionCreate(BaseModel):
    category_id: int = Field(gt=0)
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    type: TransactionType
    transaction_date: date


class TransactionUpdate(BaseModel):
    category_id: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=14,
        decimal_places=2,
    )
    type: TransactionType | None = None
    transaction_date: date | None = None

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("at least one transaction field must be provided")
        return self


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    category: str
    description: str
    amount: Decimal
    type: TransactionType
    transaction_date: date
    created_at: datetime | None = None


class TransactionPage(BaseModel):
    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int
