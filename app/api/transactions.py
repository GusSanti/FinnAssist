"""HTTP routes for transaction management."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Query, Response, status

from app.schemas.transaction import (
    TransactionCreate,
    TransactionPage,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.transaction_service import (
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
)


router = APIRouter(prefix="/users/{user_id}/transactions", tags=["transactions"])


@router.get("", response_model=TransactionPage)
def transactions_list(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: int | None = Query(default=None, gt=0),
    transaction_type: Literal["INCOME", "EXPENSE"] | None = Query(
        default=None,
        alias="type",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if start_date is not None and end_date is not None and start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date")
    return list_transactions(
        user_id,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        transaction_type=transaction_type,
        limit=limit,
        offset=offset,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def transaction_detail(user_id: int, transaction_id: int):
    return get_transaction(user_id, transaction_id)


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def transaction_create(user_id: int, payload: TransactionCreate):
    return create_transaction(
        user_id,
        category_id=payload.category_id,
        description=payload.description,
        amount=payload.amount,
        transaction_type=payload.type,
        transaction_date=payload.transaction_date,
    )


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def transaction_update(
    user_id: int,
    transaction_id: int,
    payload: TransactionUpdate,
):
    return update_transaction(
        user_id,
        transaction_id,
        **payload.model_dump(exclude_unset=True),
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def transaction_delete(user_id: int, transaction_id: int):
    delete_transaction(user_id, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
