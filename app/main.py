from fastapi import FastAPI, HTTPException, Query

from app.services.financial_service import get_financial_summary


app = FastAPI(title="FinAssist API")


@app.get("/")
def home():
    return {"message": "FinAssist API funcionando"}


@app.get("/users/{user_id}/financial-summary")
def financial_summary(
    user_id: int,
    year: int | None = Query(default=None, ge=1),
    month: int | None = Query(default=None, ge=1, le=12),
    average_months: int = Query(default=6, ge=1, le=120),
):
    try:
        return get_financial_summary(
            user_id,
            year=year,
            month=month,
            average_months=average_months,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
