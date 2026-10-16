
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Chunk:
    chunk_id: int
    text: str
    start: int
    end: int
    heading: str = ""
    level: int = 0

# Split at paragraph, sentence, and word boundaries, in that order.
SEPARATORS = (
    re.compile(r"\n[ \t]*\n+"),  # Paragraph boundary
    re.compile(r"(?<=[.!?])\s+"),  # Sentence boundary
    re.compile(r"\s+"),  # Word boundary
)

HEADING_PATTERN = re.compile(
    r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$",
    re.MULTILINE,
)

def _split_at_boundaries(
    text: str,
    separator_index: int,
    chunk_size: int,
) -> list[str]:
    """Split oversized text using progressively smaller boundaries."""

    if len(text) <= chunk_size:
        return [text] if text else []

    # Final fallback: split by character count.
    if separator_index >= len(SEPARATORS):
        return [
            text[i : i + chunk_size]
            for i in range(0, len(text), chunk_size)
        ]

    separator = SEPARATORS[separator_index]
    boundaries = [
        match.end()
        for match in separator.finditer(text)
    ]

    # If this boundary does not exist, try the next one.
    if not boundaries:
        return _split_at_boundaries(
            text, separator_index + 1, chunk_size
        )

    # Divide the text into pieces without discarding separators.
    pieces = []
    start = 0

    for boundary in boundaries:
        pieces.append(text[start:boundary])
        start = boundary

    if start < len(text):
        pieces.append(text[start:])

    chunks = []
    current = ""

    for piece in pieces:
        # A single paragraph/sentence may still be too large.
        if len(piece) > chunk_size:
            if current.strip():
                chunks.append(current.strip())
            current = ""

            chunks.extend(
                _split_at_boundaries(
                    piece, separator_index + 1, chunk_size
                )
            )
            continue

        if len(current) + len(piece) <= chunk_size:
            current += piece
        else:
            if current.strip():
                chunks.append(current.strip())
            current = piece

    if current.strip():
        chunks.append(current.strip())

    return chunks

def hybrid_chunk(
    text: str,
    chunk_size: int = 500,
) -> list[Chunk]:
    """
    Split a Markdown document by structure first,
    then paragraphs, sentences, words, and characters.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if not text.strip():
        return []

    headings = list(HEADING_PATTERN.finditer(text))

    # First, identify document sections.
    sections = []

    if not headings:
        sections.append((text, "", 0))
    else:
        # Preserve content appearing before the first heading.
        if text[: headings[0].start()].strip():
            sections.append(
                (text[: headings[0].start()], "", 0)
            )

        for index, match in enumerate(headings):
            start = match.start()

            end = (
                headings[index + 1].start()
                if index + 1 < len(headings)
                else len(text)
            )

            sections.append(
                (
                    text[start:end],
                    match.group(2).strip(),
                    len(match.group(1)),
                )
            )

    result = []
    search_from = 0

    # Then recursively split only sections that are too large.
    for section_text, heading, level in sections:
        pieces = _split_at_boundaries(
            section_text, 0, chunk_size
        )

        for piece in pieces:
            piece = piece.strip()

            if not piece:
                continue

            # Locate the chunk in the original document.
            start = text.find(piece, search_from)

            if start == -1:
                start = text.find(piece)

            if start == -1:
                raise ValueError(
                    "Could not locate chunk in source document"
                )

            end = start + len(piece)

            result.append(
                Chunk(
                    chunk_id=len(result),
                    text=piece,
                    start=start,
                    end=end,
                    heading=heading,
                    level=level,
                )
            )

            search_from = end

    return result
