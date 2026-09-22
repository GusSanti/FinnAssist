from sqlalchemy import text
from app.database import SessionLocal


def get_total_income(user_id: int):

    with SessionLocal() as session:

        query = text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = :user_id
            AND type = 'INCOME'
        """)

        result = session.execute(
            query,
            {"user_id": user_id}
        )

        return result.scalar()


def get_total_expenses(user_id: int):

    with SessionLocal() as session:

        query = text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = :user_id
            AND type = 'EXPENSE'
        """)

        result = session.execute(
            query,
            {"user_id": user_id}
        )

        return result.scalar()


def get_balance(user_id: int):

    income = get_total_income(user_id)

    expenses = get_total_expenses(user_id)

    return income - expenses