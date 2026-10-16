# Personal RAG — PDF Question Answering

A local Retrieval-Augmented Generation (RAG) application that lets users ask questions about PDF documents. It retrieves relevant passages using semantic vector search and keyword search, combines the results with Reciprocal Rank Fusion (RRF), and generates grounded answers using a locally running language model.

## Features

- PDF text extraction with PyMuPDF
- Hybrid retrieval combining PostgreSQL full-text search and pgvector similarity search
- Reciprocal Rank Fusion (RRF) for ranking retrieval results
- Local text embeddings using Sentence Transformers
- Answer generation using Ollama
- Source references with PDF filenames and page numbers
- PostgreSQL persistence for documents, chunks, and embeddings
- Docker Compose for PostgreSQL with pgvector
- Automated unit tests using Python's `unittest`

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python |
| PDF processing | PyMuPDF |
| Embeddings | Sentence Transformers |
| Embedding model | `all-MiniLM-L6-v2` |
| Database | PostgreSQL |
| Vector search | pgvector |
| Keyword search | PostgreSQL full-text search |
| Local LLM runtime | Ollama |
| LLM | `llama3.2:1b` |
| Infrastructure | Docker Compose |
| Testing | unittest |

## Architecture

```text
PDF Documents
     |
     v
PDF Text Extraction
     |
     v
Text Chunking
     |
     v
Sentence Transformer Embeddings
     |
     v
PostgreSQL + pgvector
     |
     v
Question
     |
     +----------------------+
     |                      |
     v                      v
Keyword Search        Vector Search
     |                      |
     +----------+-----------+
                |
                v
     Reciprocal Rank Fusion
                |
                v
       Retrieved Context
                |
                v
         Ollama LLM
                |
                v
     Answer with Sources
```

## Requirements

- Python 3.12 or a compatible Python version
- Docker Engine and Docker Compose
- Ollama installed and running on the host
- Sufficient memory and disk space for the embedding model and LLM

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Mohitrawal7/personal-rag.git
cd personal-rag
```


### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set your own database password. Ensure `DATABASE_URL` uses the same credentials and the PostgreSQL host port configured in `docker-compose.yml`.

Never commit `.env` or publish real credentials.

### 5. Start PostgreSQL with pgvector

```bash
docker compose up -d postgres
```

### 6. Initialize the database

```bash
python scripts/init_db.py
```

### 7. Prepare Ollama

Install Ollama using its official installation instructions if needed. Start the Ollama service, then download the configured model:

```bash
ollama pull llama3.2:1b
```

Ensure `OLLAMA_URL` and `OLLAMA_MODEL` in `.env` match your local setup.

## Ingest a PDF

Pass the path to a text-based PDF:

```bash
python scripts/ingest_pdf.py path/to/document.pdf
```

The script extracts text, splits it into chunks, generates embeddings, and stores the document and its chunks in PostgreSQL.

Scanned PDFs without an extractable text layer may require OCR before ingestion.

## Run Tests

```bash
python -m unittest discover -s tests -v
```

The unit tests mock external calls where appropriate. They do not replace integration tests against a real database or end-to-end tests of the full RAG pipeline.

## Project Structure

```text
app/
├── chunking/       # Text chunking
├── embeddings/     # Embedding model
├── generation/     # LLM answer generation
├── ingestion/      # PDF extraction and ingestion
├── retrieval/      # Keyword, vector, and hybrid search
└── storage/        # Database connection and persistence

scripts/
├── ingest_pdf.py   # PDF ingestion command
└── init_db.py      # Database schema initialization

sql/
└── schema.sql      # PostgreSQL and pgvector schema

tests/              # Automated tests
docker-compose.yml  # PostgreSQL service
requirements.txt    # Python dependencies
.env.example        # Example configuration
```

## Current Scope

This project focuses on the core PDF ingestion, retrieval, and answer-generation pipeline. A user interface, broader integration tests, and additional production hardening can be added in future iterations.

## Future Improvements

- Web interface for uploading PDFs and asking questions
- Improved retrieval evaluation with a labeled question set
- Better chunking and retrieval parameter tuning
- Integration tests for database operations
- Document management and deletion workflows
- Dockerized application deployment

## License

No license has been added yet. A license can be selected when the intended reuse and distribution terms are decided.
