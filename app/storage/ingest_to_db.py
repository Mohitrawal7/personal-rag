
import hashlib
from pathlib import Path

from app.config import CHUNK_SIZE
from app.embeddings.model import embed_texts
from app.ingestion.pdf import ingest_pdf
from app.storage.database import get_connection
from app.storage.documents import is_document_complete


def ingest_file(pdf_path: str | Path) -> int:
    """Extract a PDF and store it, skipping verified duplicate content."""
    path = Path(pdf_path)

    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    chunks = ingest_pdf(path, chunk_size=CHUNK_SIZE)

    page_count = max(
        (chunk["page_count"] for chunk in chunks),
        default=0,
    )

    # Skip embedding generation only when stored data is verified.
    if is_document_complete(file_hash, chunks, page_count):
        return len(chunks)

    embeddings = embed_texts(
        [chunk["chunk_text"] for chunk in chunks]
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents (
                    document_id, filename, file_hash, page_count
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    file_hash = EXCLUDED.file_hash,
                    page_count = EXCLUDED.page_count
                """,
                (
                    file_hash,
                    path.name,
                    file_hash,
                    page_count,
                ),
            )

            # Replace existing chunks within the same transaction.
            cursor.execute(
                "DELETE FROM chunks WHERE document_id = %s",
                (file_hash,),
            )

            for chunk, embedding in zip(chunks, embeddings, strict=True):
                cursor.execute(
                    """
                    INSERT INTO chunks (
                        document_id, chunk_index, page_number, heading,
                        start_offset, end_offset, content, embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        file_hash,
                        chunk["chunk_id"],
                        chunk["page_number"],
                        chunk["heading"],
                        chunk["start_offset"],
                        chunk["end_offset"],
                        chunk["chunk_text"],
                        embedding.tolist(),
                    ),
                )

    return len(chunks)
