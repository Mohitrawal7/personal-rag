from pathlib import Path

from app.storage.database import get_connection


def main() -> None:
    schema_path = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema_sql)

    print("Database schema initialized successfully.")


if __name__ == "__main__":
    main()
