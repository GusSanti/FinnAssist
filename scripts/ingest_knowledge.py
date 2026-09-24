"""Ingest the MVP Markdown knowledge files into PostgreSQL/pgvector."""

from pathlib import Path

from sqlalchemy import text

from app.database import SessionLocal
from app.services.knowledge_service import create_embeddings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_FILES = (
    PROJECT_ROOT / "knowledge" / "tesouro_selic.md",
    PROJECT_ROOT / "knowledge" / "reserva_emergencia.md",
)


def split_markdown(content: str) -> list[str]:
    """Split on level-two headings and retain headings in self-contained chunks."""
    sections: list[str] = []
    current: list[str] = []
    document_title = ""

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        if line.startswith("# ") and not document_title:
            document_title = line
            continue
        if line.startswith("## ") and current:
            sections.append("\n".join(current).strip())
            current = []
        if line or current:
            current.append(line)

    if current:
        sections.append("\n".join(current).strip())

    prefix = f"{document_title}\n\n" if document_title else ""
    return [prefix + section for section in sections if section]


def _title(content: str, path: Path) -> str:
    first_line = content.splitlines()[0].strip() if content.splitlines() else ""
    return first_line.removeprefix("# ").strip() or path.stem.replace("_", " ").title()


def ingest_file(path: Path) -> tuple[int, int]:
    content = path.read_text(encoding="utf-8")
    chunks = split_markdown(content)
    if not chunks:
        raise ValueError(f"Nenhum chunk foi gerado para {path}")
    embeddings = create_embeddings(chunks)
    source = path.relative_to(PROJECT_ROOT).as_posix()

    with SessionLocal.begin() as session:
        document_id = session.execute(
            text("""
                INSERT INTO documents (title, source, content)
                VALUES (:title, :source, :content)
                ON CONFLICT (source) DO UPDATE
                SET title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    updated_at = NOW()
                RETURNING id
            """),
            {
                "title": _title(content, path),
                "source": source,
                "content": content,
            },
        ).scalar_one()
        session.execute(
            text("DELETE FROM document_chunks WHERE document_id = :document_id"),
            {"document_id": document_id},
        )
        session.execute(
            text("""
                INSERT INTO document_chunks
                    (document_id, chunk_index, content, embedding)
                VALUES
                    (:document_id, :chunk_index, :content, CAST(:embedding AS vector))
            """),
            [
                {
                    "document_id": document_id,
                    "chunk_index": index,
                    "content": chunk,
                    "embedding": "[" + ",".join(map(str, embedding)) + "]",
                }
                for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ],
        )
    return document_id, len(chunks)


def main() -> None:
    for path in KNOWLEDGE_FILES:
        document_id, chunk_count = ingest_file(path)
        print(f"{path.name}: document_id={document_id}, chunks={chunk_count}")


if __name__ == "__main__":
    main()
