
from app.storage.database import get_connection


def list_documents() -> list[dict]:
    """Return indexed documents with their stored chunk counts."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    d.document_id,
                    d.filename,
                    d.file_hash,
                    d.page_count,
                    d.created_at,
                    COUNT(c.id)::INTEGER AS chunk_count
                FROM documents AS d
                LEFT JOIN chunks AS c
                    ON c.document_id = d.document_id
                GROUP BY
                    d.document_id,
                    d.filename,
                    d.file_hash,
                    d.page_count,
                    d.created_at
                ORDER BY d.created_at DESC, d.filename ASC
                """
            )

            columns = [column[0] for column in cursor.description]
            return [
                dict(zip(columns, row, strict=True))
                for row in cursor.fetchall()
            ]


def delete_document(document_id: str) -> bool:
    """
    Delete one indexed document and its associated chunks.

    Returns True if a document was deleted, or False if it did not exist.
    The connection context commits on success and rolls back on exceptions.
    """
    if not document_id:
        raise ValueError("document_id cannot be empty")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM documents
                WHERE document_id = %s
                RETURNING document_id
                """,
                (document_id,),
            )
            return cursor.fetchone() is not None

def is_document_complete(
    document_id: str,
    expected_chunks: list[dict],
    expected_page_count: int,
) -> bool:
    """Check whether stored document data matches freshly extracted chunks."""
    if not document_id or not expected_chunks:
        return False

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT page_count
                FROM documents
                WHERE document_id = %s
                """,
                (document_id,),
            )
            document = cursor.fetchone()

            if document is None or document[0] != expected_page_count:
                return False

            cursor.execute(
                """
                SELECT
                    chunk_index,
                    page_number,
                    heading,
                    start_offset,
                    end_offset,
                    content
                FROM chunks
                WHERE document_id = %s
                ORDER BY chunk_index
                """,
                (document_id,),
            )
            stored_chunks = cursor.fetchall()

            expected = [
                (
                    chunk["chunk_id"],
                    chunk["page_number"],
                    chunk["heading"],
                    chunk["start_offset"],
                    chunk["end_offset"],
                    chunk["chunk_text"],
                )
                for chunk in expected_chunks
            ]

            return stored_chunks == expected
