from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.ai.financial_agent import answer_financial_question
from app.services.financial_service import get_financial_summary


app = FastAPI(title="FinAssist API")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str


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


@app.post("/users/{user_id}/chat", response_model=ChatResponse)
def financial_chat(user_id: int, request: ChatRequest):
    try:
        answer = answer_financial_question(user_id, request.message)
        return ChatResponse(answer=answer)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
