"""HTTP routes for category management."""

from typing import Literal

from fastapi import APIRouter, Query, Response, status

from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import (
    create_category,
    delete_category,
    get_category,
    list_categories,
    update_category,
)


router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def categories_list(
    category_type: Literal["INCOME", "EXPENSE"] | None = Query(
        default=None,
        alias="type",
    ),
):
    return list_categories(category_type)


@router.get("/{category_id}", response_model=CategoryResponse)
def category_detail(category_id: int):
    return get_category(category_id)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def category_create(payload: CategoryCreate):
    return create_category(payload.name, payload.type)


@router.patch("/{category_id}", response_model=CategoryResponse)
def category_update(category_id: int, payload: CategoryUpdate):
    return update_category(
        category_id,
        name=payload.name,
        category_type=payload.type,
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def category_delete(category_id: int):
    delete_category(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
