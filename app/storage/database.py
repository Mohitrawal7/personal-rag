import psycopg2
from pgvector.psycopg2 import register_vector

from app.config import DATABASE_URL


def get_connection():
    """Create a PostgreSQL connection with pgvector support."""
    connection = psycopg2.connect(DATABASE_URL)
    register_vector(connection)
    return connection
