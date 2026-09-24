"""Embedding generation and semantic retrieval for the financial knowledge base."""

import os
from typing import Any, Sequence

from ollama import embed
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal


EMBEDDING_DIMENSIONS = 768
DEFAULT_RESULT_LIMIT = 5
MAX_RESULT_LIMIT = 20


def embedding_model() -> str:
    return os.getenv("OLLAMA_EMBEDDING_MODEL", "embeddinggemma")


def create_embeddings(texts: str | Sequence[str]) -> list[list[float]]:
    """Create and validate embeddings using the configured Ollama model."""
    inputs = [texts] if isinstance(texts, str) else list(texts)
    if not inputs or any(not item.strip() for item in inputs):
        raise ValueError("embedding input must not be empty")

    try:
        response = embed(model=embedding_model(), input=inputs)
    except Exception as error:
        raise RuntimeError("Não foi possível gerar embeddings no Ollama.") from error

    embeddings = [list(values) for values in response["embeddings"]]
    if len(embeddings) != len(inputs):
        raise RuntimeError("O Ollama retornou uma quantidade inesperada de embeddings.")
    if any(len(values) != EMBEDDING_DIMENSIONS for values in embeddings):
        dimensions = sorted({len(values) for values in embeddings})
        raise RuntimeError(
            f"O modelo {embedding_model()} gerou dimensões {dimensions}; "
            f"eram esperadas {EMBEDDING_DIMENSIONS}."
        )
    return embeddings


def _vector_literal(values: Sequence[float]) -> str:
    if len(values) != EMBEDDING_DIMENSIONS:
        raise ValueError(f"embedding must have {EMBEDDING_DIMENSIONS} dimensions")
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def search_financial_knowledge(
    query: str,
    limit: int = DEFAULT_RESULT_LIMIT,
) -> dict[str, list[dict[str, Any]]]:
    """Return the most similar knowledge chunks with their source metadata."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= limit <= MAX_RESULT_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_RESULT_LIMIT}")

    query_embedding = create_embeddings(query.strip())[0]
    statement = text("""
        SELECT
            d.title,
            d.source,
            dc.content,
            1 - (dc.embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM document_chunks AS dc
        JOIN documents AS d ON d.id = dc.document_id
        ORDER BY dc.embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """)

    try:
        with SessionLocal() as session:
            rows = session.execute(
                statement,
                {"embedding": _vector_literal(query_embedding), "limit": limit},
            ).mappings()
            results = [
                {
                    "title": row["title"],
                    "source": row["source"],
                    "content": row["content"],
                    "similarity": round(float(row["similarity"]), 6),
                }
                for row in rows
            ]
    except SQLAlchemyError as error:
        raise RuntimeError("Não foi possível consultar a base de conhecimento.") from error

    return {"results": results}
