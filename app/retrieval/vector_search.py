from pgvector import Vector

from app.embeddings.model import embed_texts
from app.storage.database import get_connection


def search_similar_chunks(
    question: str,
    top_k: int = 5,
) -> list[dict]:
    """Return the most semantically similar stored chunks."""

    if not question.strip():
        raise ValueError("Question cannot be empty")

    if top_k <= 0:
        raise ValueError("top_k must be positive")

    query_vector = Vector(embed_texts([question])[0].tolist())

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    d.filename,
                    c.page_number,
                    c.chunk_index,
                    c.content,
                    1 - (c.embedding <=> %s) AS similarity
                FROM chunks AS c
                JOIN documents AS d
                    ON d.document_id = c.document_id
                ORDER BY c.embedding <=> %s
                LIMIT %s
                """,
                (query_vector, query_vector, top_k),
            )
            rows = cursor.fetchall()

    return [
        {
            "source_filename": row[0],
            "page_number": row[1],
            "chunk_id": row[2],
            "chunk_text": row[3],
            "similarity": float(row[4]),
        }
        for row in rows
    ]
