from fastapi import FastAPI

from app.services.financial_service import (
    get_total_income,
    get_total_expenses
)


app = FastAPI()


@app.get("/")
def home():

    return {
        "message": "FinAssist API funcionando"
    }


@app.get("/users/{user_id}/financial-summary")
def financial_summary(user_id: int):

    income = get_total_income(user_id)

    expenses = get_total_expenses(user_id)

    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses
    }