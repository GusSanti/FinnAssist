from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.api.categories import router as categories_router
from app.api.transactions import router as transactions_router
from app.ai.financial_agent import answer_financial_question
from app.errors import ResourceConflictError, ResourceNotFoundError
from app.services.financial_service import get_financial_summary
from app.services.knowledge_service import search_financial_knowledge


app = FastAPI(title="FinAssist API")
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(categories_router)
app.include_router(transactions_router)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str


class KnowledgeSearchResponse(BaseModel):
    results: list[dict[str, object]]


@app.exception_handler(ResourceNotFoundError)
async def not_found_handler(_request: Request, error: ResourceNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(ResourceConflictError)
async def conflict_handler(_request: Request, error: ResourceConflictError):
    return JSONResponse(status_code=409, content={"detail": str(error)})


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, error: ValueError):
    return JSONResponse(status_code=422, content={"detail": str(error)})


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["system"])
def health():
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


@app.get("/knowledge/search", response_model=KnowledgeSearchResponse)
def knowledge_search(
    query: str = Query(min_length=1, max_length=1000),
    limit: int = Query(default=5, ge=1, le=20),
):
    """Inspect semantic retrieval without invoking the conversational model."""
    try:
        return search_financial_knowledge(query, limit)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
