"""CRUD and filtered listing operations for financial transactions."""

from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.database import SessionLocal
from app.errors import ResourceConflictError, ResourceNotFoundError


TRANSACTION_SELECT = """
    SELECT
        t.id,
        t.user_id,
        t.category_id,
        c.name AS category,
        t.description,
        t.amount,
        t.type,
        t.transaction_date,
        t.created_at
    FROM transactions AS t
    JOIN categories AS c ON c.id = t.category_id
"""


def _ensure_user(session, user_id: int) -> None:
    exists = session.execute(
        text("SELECT 1 FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    ).first()
    if exists is None:
        raise ResourceNotFoundError("Usuário não encontrado.")


def _ensure_compatible_category(session, category_id: int, transaction_type: str) -> None:
    category_type = session.execute(
        text("SELECT type FROM categories WHERE id = :category_id"),
        {"category_id": category_id},
    ).scalar_one_or_none()
    if category_type is None:
        raise ResourceNotFoundError("Categoria não encontrada.")
    if category_type != transaction_type:
        raise ResourceConflictError(
            "O tipo da categoria deve ser igual ao tipo da transação."
        )


def list_transactions(
    user_id: int,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: int | None = None,
    transaction_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, object]:
    conditions = ["t.user_id = :user_id"]
    parameters: dict[str, object] = {
        "user_id": user_id,
        "limit": limit,
        "offset": offset,
    }
    if start_date is not None:
        conditions.append("t.transaction_date >= :start_date")
        parameters["start_date"] = start_date
    if end_date is not None:
        conditions.append("t.transaction_date <= :end_date")
        parameters["end_date"] = end_date
    if category_id is not None:
        conditions.append("t.category_id = :category_id")
        parameters["category_id"] = category_id
    if transaction_type is not None:
        conditions.append("t.type = :transaction_type")
        parameters["transaction_type"] = transaction_type

    where_clause = " AND ".join(conditions)
    with SessionLocal() as session:
        _ensure_user(session, user_id)
        total = session.execute(
            text(f"SELECT COUNT(*) FROM transactions AS t WHERE {where_clause}"),
            parameters,
        ).scalar_one()
        rows = session.execute(
            text(f"""
                {TRANSACTION_SELECT}
                WHERE {where_clause}
                ORDER BY t.transaction_date DESC, t.id DESC
                LIMIT :limit OFFSET :offset
            """),
            parameters,
        ).mappings()
        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


def get_transaction(user_id: int, transaction_id: int) -> dict[str, object]:
    with SessionLocal() as session:
        row = session.execute(
            text(f"""
                {TRANSACTION_SELECT}
                WHERE t.id = :transaction_id AND t.user_id = :user_id
            """),
            {"transaction_id": transaction_id, "user_id": user_id},
        ).mappings().one_or_none()
    if row is None:
        raise ResourceNotFoundError("Transação não encontrada.")
    return dict(row)


def create_transaction(
    user_id: int,
    *,
    category_id: int,
    description: str,
    amount: Decimal,
    transaction_type: str,
    transaction_date: date,
) -> dict[str, object]:
    with SessionLocal.begin() as session:
        _ensure_user(session, user_id)
        _ensure_compatible_category(session, category_id, transaction_type)
        transaction_id = session.execute(
            text("""
                INSERT INTO transactions
                    (user_id, category_id, description, amount, type, transaction_date)
                VALUES
                    (:user_id, :category_id, :description, :amount,
                     :transaction_type, :transaction_date)
                RETURNING id
            """),
            {
                "user_id": user_id,
                "category_id": category_id,
                "description": description.strip(),
                "amount": amount,
                "transaction_type": transaction_type,
                "transaction_date": transaction_date,
            },
        ).scalar_one()
        row = session.execute(
            text(f"{TRANSACTION_SELECT} WHERE t.id = :transaction_id"),
            {"transaction_id": transaction_id},
        ).mappings().one()
        return dict(row)


def update_transaction(
    user_id: int,
    transaction_id: int,
    **changes,
) -> dict[str, object]:
    with SessionLocal.begin() as session:
        current = session.execute(
            text("""
                SELECT id, category_id, description, amount, type, transaction_date
                FROM transactions
                WHERE id = :transaction_id AND user_id = :user_id
            """),
            {"transaction_id": transaction_id, "user_id": user_id},
        ).mappings().one_or_none()
        if current is None:
            raise ResourceNotFoundError("Transação não encontrada.")

        values = dict(current)
        values.update({key: value for key, value in changes.items() if value is not None})
        _ensure_compatible_category(session, values["category_id"], values["type"])
        session.execute(
            text("""
                UPDATE transactions
                SET category_id = :category_id,
                    description = :description,
                    amount = :amount,
                    type = :type,
                    transaction_date = :transaction_date
                WHERE id = :id
            """),
            values,
        )
        row = session.execute(
            text(f"{TRANSACTION_SELECT} WHERE t.id = :transaction_id"),
            {"transaction_id": transaction_id},
        ).mappings().one()
        return dict(row)


def delete_transaction(user_id: int, transaction_id: int) -> None:
    with SessionLocal.begin() as session:
        deleted_id = session.execute(
            text("""
                DELETE FROM transactions
                WHERE id = :transaction_id AND user_id = :user_id
                RETURNING id
            """),
            {"transaction_id": transaction_id, "user_id": user_id},
        ).scalar_one_or_none()
        if deleted_id is None:
            raise ResourceNotFoundError("Transação não encontrada.")
