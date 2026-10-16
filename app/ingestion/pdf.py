
import hashlib
from pathlib import Path

import pymupdf

from app.chunking.full import hybrid_chunk


def ingest_pdf(
    pdf_path: str | Path,
    chunk_size: int = 500,
) -> list[dict]:
    """Extract a PDF and return chunks with source metadata."""

    path = Path(pdf_path)

    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Expected a PDF file")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    # Identify the document consistently by its content.
    document_id = hashlib.sha256(path.read_bytes()).hexdigest()

    results = []

    with pymupdf.open(path) as pdf:
        document_metadata = pdf.metadata or {}
        page_count = len(pdf)

        for page_index, page in enumerate(pdf):
            # PDF page numbers shown to users start at 1.
            page_number = page_index + 1

            # Extract text in an approximate natural reading order.
            page_text = page.get_text("text", sort=True)

            if not page_text.strip():
                # Scanned/image-only pages may need OCR later.
                continue

            # Chunk each page separately to preserve page provenance.
            chunks = hybrid_chunk(page_text, chunk_size)

            for chunk in chunks:
                results.append({
                    "document_id": document_id,
                    "source_filename": path.name,
                    "file_type": "pdf",
                    "document_title": document_metadata.get("title"),
                    "page_number": page_number,
                    "chunk_id": len(results),
                    "heading": chunk.heading or None,
                    "heading_level": chunk.level,
                    "start_offset": chunk.start,
                    "end_offset": chunk.end,
                    "chunk_text": chunk.text,
                    "page_count": page_count,
                })

    return results
