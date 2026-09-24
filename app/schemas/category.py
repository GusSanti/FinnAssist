"""Validation contracts for financial categories."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


TransactionType = Literal["INCOME", "EXPENSE"]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: TransactionType

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("category name must not be empty")
        return normalized


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: TransactionType | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("category name must not be empty")
        return normalized

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("at least one category field must be provided")
        return self


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: TransactionType
