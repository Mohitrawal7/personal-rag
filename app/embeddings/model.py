import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_DIMENSION, EMBEDDING_MODEL


_model = None


def get_model() -> SentenceTransformer:
    """Load the embedding model once per Python process."""
    global _model

    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)

    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Convert multiple text strings into normalized embeddings."""
    if not texts:
        return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)

    embeddings = get_model().encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    if embeddings.shape != (len(texts), EMBEDDING_DIMENSION):
        raise ValueError(
            f"Expected embeddings shaped "
            f"({len(texts)}, {EMBEDDING_DIMENSION}), "
            f"got {embeddings.shape}"
        )

    if not np.isfinite(embeddings).all():
        raise ValueError("Embeddings contain invalid values")

    return embeddings