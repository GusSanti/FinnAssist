"""CRUD operations for transaction categories."""

from sqlalchemy import text

from app.database import SessionLocal
from app.errors import ResourceConflictError, ResourceNotFoundError


def list_categories(category_type: str | None = None) -> list[dict[str, object]]:
    parameters: dict[str, object] = {}
    condition = ""
    if category_type is not None:
        condition = "WHERE type = :category_type"
        parameters["category_type"] = category_type

    with SessionLocal() as session:
        rows = session.execute(
            text(f"""
                SELECT id, name, type
                FROM categories
                {condition}
                ORDER BY type, name, id
            """),
            parameters,
        ).mappings()
        return [dict(row) for row in rows]


def get_category(category_id: int) -> dict[str, object]:
    with SessionLocal() as session:
        row = session.execute(
            text("SELECT id, name, type FROM categories WHERE id = :category_id"),
            {"category_id": category_id},
        ).mappings().one_or_none()
    if row is None:
        raise ResourceNotFoundError("Categoria não encontrada.")
    return dict(row)


def _ensure_unique_name(
    session,
    name: str,
    *,
    exclude_id: int | None = None,
) -> None:
    row = session.execute(
        text("""
            SELECT id
            FROM categories
            WHERE LOWER(name) = LOWER(:name)
              AND (:exclude_id IS NULL OR id <> :exclude_id)
            LIMIT 1
        """),
        {"name": name, "exclude_id": exclude_id},
    ).first()
    if row is not None:
        raise ResourceConflictError("Já existe uma categoria com esse nome.")


def create_category(name: str, category_type: str) -> dict[str, object]:
    with SessionLocal.begin() as session:
        _ensure_unique_name(session, name)
        row = session.execute(
            text("""
                INSERT INTO categories (name, type)
                VALUES (:name, :category_type)
                RETURNING id, name, type
            """),
            {"name": name, "category_type": category_type},
        ).mappings().one()
        return dict(row)


def update_category(
    category_id: int,
    *,
    name: str | None = None,
    category_type: str | None = None,
) -> dict[str, object]:
    with SessionLocal.begin() as session:
        current = session.execute(
            text("SELECT id, name, type FROM categories WHERE id = :category_id"),
            {"category_id": category_id},
        ).mappings().one_or_none()
        if current is None:
            raise ResourceNotFoundError("Categoria não encontrada.")

        selected_name = name if name is not None else current["name"]
        selected_type = category_type if category_type is not None else current["type"]
        _ensure_unique_name(session, selected_name, exclude_id=category_id)

        incompatible = session.execute(
            text("""
                SELECT COUNT(*)
                FROM transactions
                WHERE category_id = :category_id
                  AND type <> :category_type
            """),
            {"category_id": category_id, "category_type": selected_type},
        ).scalar_one()
        if incompatible:
            raise ResourceConflictError(
                "O tipo da categoria conflita com transações já cadastradas."
            )

        row = session.execute(
            text("""
                UPDATE categories
                SET name = :name, type = :category_type
                WHERE id = :category_id
                RETURNING id, name, type
            """),
            {
                "category_id": category_id,
                "name": selected_name,
                "category_type": selected_type,
            },
        ).mappings().one()
        return dict(row)


def delete_category(category_id: int) -> None:
    with SessionLocal.begin() as session:
        usage_count = session.execute(
            text("SELECT COUNT(*) FROM transactions WHERE category_id = :category_id"),
            {"category_id": category_id},
        ).scalar_one()
        if usage_count:
            raise ResourceConflictError(
                "A categoria possui transações e não pode ser excluída."
            )
        deleted_id = session.execute(
            text("DELETE FROM categories WHERE id = :category_id RETURNING id"),
            {"category_id": category_id},
        ).scalar_one_or_none()
        if deleted_id is None:
            raise ResourceNotFoundError("Categoria não encontrada.")
