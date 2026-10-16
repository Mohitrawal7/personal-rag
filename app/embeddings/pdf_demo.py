
import numpy as np
from sentence_transformers import SentenceTransformer

from app.ingestion.pdf import ingest_pdf

pdf_path = "sample_documents/pdfs/2.pdf"

# Extract PDF text and metadata using your existing pipeline.
chunks = ingest_pdf(pdf_path, chunk_size=500)

if not chunks:
    raise ValueError("No chunks found. Check PDF ingestion.")

# Load the model you already downloaded.
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

texts = [chunk["chunk_text"] for chunk in chunks]

# Generate one vector for each chunk.
embeddings = model.encode(
    texts,
    convert_to_numpy=True,
    normalize_embeddings=True,
)

# Validate the output.
assert len(embeddings) == len(chunks)
assert embeddings.shape[1] == 384
assert np.isfinite(embeddings).all()

for chunk, embedding in zip(chunks, embeddings):
    chunk["embedding"] = embedding.tolist()

print("Chunks:", len(chunks))
print("Embedding dimensions:", embeddings.shape)
print("All vector values finite:", np.isfinite(embeddings).all())
print("First chunk page:", chunks[0]["page_number"])
print("First vector sample:", chunks[0]["embedding"][:5])
