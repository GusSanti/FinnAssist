-- Correcao para bancos em que a tabela documents ja existia antes da migration 001.
-- A restricao e necessaria para o ON CONFLICT (source) da ingestao idempotente.

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'documents'::regclass
          AND contype = 'u'
          AND conkey = ARRAY[
              (
                  SELECT attnum
                  FROM pg_attribute
                  WHERE attrelid = 'documents'::regclass
                    AND attname = 'source'
                    AND NOT attisdropped
              )
          ]::SMALLINT[]
    ) THEN
        ALTER TABLE documents
            ADD CONSTRAINT documents_source_unique UNIQUE (source);
    END IF;
END
$$;

COMMIT;
