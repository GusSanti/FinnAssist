from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.database import SessionLocal


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    if not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")
    if year < 1:
        raise ValueError("year must be greater than zero")

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    return start, end


def _shift_month(year: int, month: int, offset: int) -> tuple[int, int]:
    _month_bounds(year, month)
    absolute_month = year * 12 + month - 1 + offset
    shifted_year, shifted_month = divmod(absolute_month, 12)
    return shifted_year, shifted_month + 1


def _selected_month(year: int | None, month: int | None) -> tuple[int, int]:
    if year is None and month is None:
        today = date.today()
        return today.year, today.month
    if year is None or month is None:
        raise ValueError("year and month must be provided together")

    _month_bounds(year, month)
    return year, month


def get_total_income(user_id: int) -> Decimal:
    with SessionLocal() as session:
        query = text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = :user_id
              AND type = 'INCOME'
        """)
        result = session.execute(query, {"user_id": user_id})
        return result.scalar_one()


def get_total_expenses(user_id: int) -> Decimal:
    with SessionLocal() as session:
        query = text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = :user_id
              AND type = 'EXPENSE'
        """)
        result = session.execute(query, {"user_id": user_id})
        return result.scalar_one()


def get_balance(user_id: int) -> Decimal:
    return get_total_income(user_id) - get_total_expenses(user_id)


def get_monthly_balance(
    user_id: int,
    year: int | None = None,
    month: int | None = None,
) -> Decimal:
    year, month = _selected_month(year, month)
    start_date, end_date = _month_bounds(year, month)

    with SessionLocal() as session:
        query = text("""
            SELECT
                COALESCE(SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END), 0)
                -
                COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0)
            FROM transactions
            WHERE user_id = :user_id
              AND transaction_date >= :start_date
              AND transaction_date < :end_date
        """)
        result = session.execute(
            query,
            {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        return result.scalar_one()


def get_expenses_by_category(
    user_id: int,
    year: int | None = None,
    month: int | None = None,
) -> list[dict[str, object]]:
    year, month = _selected_month(year, month)
    start_date, end_date = _month_bounds(year, month)

    with SessionLocal() as session:
        query = text("""
            SELECT
                c.id AS category_id,
                c.name AS category,
                SUM(t.amount) AS total
            FROM transactions AS t
            JOIN categories AS c ON c.id = t.category_id
            WHERE t.user_id = :user_id
              AND t.type = 'EXPENSE'
              AND t.transaction_date >= :start_date
              AND t.transaction_date < :end_date
            GROUP BY c.id, c.name
            ORDER BY total DESC, c.name ASC
        """)
        rows = session.execute(
            query,
            {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        ).mappings()

        return [dict(row) for row in rows]


def get_monthly_average(
    user_id: int,
    months: int = 6,
    year: int | None = None,
    month: int | None = None,
) -> Decimal:
    if months < 1:
        raise ValueError("months must be greater than zero")

    year, month = _selected_month(year, month)
    start_year, start_month = _shift_month(year, month, -(months - 1))
    start_date, _ = _month_bounds(start_year, start_month)
    _, end_date = _month_bounds(year, month)

    with SessionLocal() as session:
        query = text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = :user_id
              AND type = 'EXPENSE'
              AND transaction_date >= :start_date
              AND transaction_date < :end_date
        """)
        result = session.execute(
            query,
            {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        total = result.scalar_one()

    return (total / Decimal(months)).quantize(Decimal("0.01"))


def get_financial_summary(
    user_id: int,
    year: int | None = None,
    month: int | None = None,
    average_months: int = 6,
) -> dict[str, object]:
    if average_months < 1:
        raise ValueError("average_months must be greater than zero")

    year, month = _selected_month(year, month)
    start_date, end_date = _month_bounds(year, month)

    with SessionLocal() as session:
        totals_query = text("""
            SELECT
                COALESCE(SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END), 0)
                    AS income,
                COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0)
                    AS expenses
            FROM transactions
            WHERE user_id = :user_id
              AND transaction_date >= :start_date
              AND transaction_date < :end_date
        """)
        totals = session.execute(
            totals_query,
            {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        ).mappings().one()

    income = totals["income"]
    expenses = totals["expenses"]

    return {
        "user_id": user_id,
        "period": {"year": year, "month": month},
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
        "monthly_expense_average": get_monthly_average(
            user_id,
            months=average_months,
            year=year,
            month=month,
        ),
        "average_period_months": average_months,
        "expenses_by_category": get_expenses_by_category(user_id, year, month),
    }
