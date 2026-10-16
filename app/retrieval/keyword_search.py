import re

from app.storage.database import get_connection


def search_keyword_chunks(question: str, top_k: int = 5) -> list[dict]:
    if not question.strip():
        raise ValueError("Question cannot be empty.")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    words = list(dict.fromkeys(re.findall(r"[a-zA-Z0-9]+", question.lower())))
    if not words:
        return []

    keyword_query = " OR ".join(words)

    sql = """
        WITH search_query AS (
            SELECT websearch_to_tsquery('english', %s) AS query
        )
        SELECT
            d.filename,
            c.page_number,
            c.chunk_index,
            c.content,
            ts_rank_cd(
                to_tsvector('english', c.content),
                search_query.query
            ) AS rank
        FROM chunks AS c
        JOIN documents AS d ON d.document_id = c.document_id
        CROSS JOIN search_query
        WHERE to_tsvector('english', c.content) @@ search_query.query
        ORDER BY rank DESC, c.chunk_index
        LIMIT %s
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (keyword_query, top_k))
            rows = cursor.fetchall()

    return [
        {
            "source_filename": row[0],
            "page_number": row[1],
            "chunk_id": row[2],
            "chunk_text": row[3],
            "rank": float(row[4]),
        }
        for row in rows
    ]
