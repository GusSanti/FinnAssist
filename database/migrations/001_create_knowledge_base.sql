-- Execute manualmente no banco finnassist_db antes da primeira ingestao.
-- Requer permissao para instalar a extensao pgvector.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    content TEXT NOT NULL CHECK (BTRIM(content) <> ''),
    embedding vector(768) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

-- O indice acelera a distancia por cosseno usada pela aplicacao.
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);

COMMIT;

-- Conferencia apos executar scripts/ingest_knowledge.py:
-- SELECT id, title, source FROM documents ORDER BY id;
--
-- SELECT
--     document_id,
--     chunk_index,
--     LEFT(content, 100) AS content_preview,
--     vector_dims(embedding) AS embedding_dimensions
-- FROM document_chunks
-- ORDER BY document_id, chunk_index;
