import argparse
from pathlib import Path

from app.storage.ingest_to_db import ingest_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a PDF into the personal RAG database."
    )
    parser.add_argument("pdf", type=Path, help="Path to the PDF file")
    args = parser.parse_args()

    count = ingest_file(args.pdf)
    print(f"Ingestion complete: stored {count} chunks.")


if __name__ == "__main__":
    main()
