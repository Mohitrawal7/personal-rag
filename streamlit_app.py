import hashlib
import tempfile
from pathlib import Path

import streamlit as st

from app.generation.answer_generator import generate_answer
from app.storage.ingest_to_db import ingest_file


st.set_page_config(
    page_title="Personal PDF RAG",
    page_icon="📚",
    layout="centered",
)

st.title("📚 Personal PDF Assistant")
st.caption("Upload a PDF, ask questions, and explore its contents.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "ingested_hashes" not in st.session_state:
    st.session_state.ingested_hashes = set()

uploaded_pdf = st.file_uploader(
    "Upload one PDF",
    type=["pdf"],
    accept_multiple_files=False,
)

if uploaded_pdf is not None:
    pdf_bytes = uploaded_pdf.getvalue()
    file_hash = hashlib.sha256(pdf_bytes).hexdigest()

    if file_hash not in st.session_state.ingested_hashes:
        with st.spinner("Processing PDF and creating embeddings..."):
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    pdf_path = Path(temp_dir) / uploaded_pdf.name
                    pdf_path.write_bytes(pdf_bytes)
                    chunk_count = ingest_file(pdf_path)

                st.session_state.ingested_hashes.add(file_hash)
                st.session_state.active_file_hash = file_hash
                st.session_state.active_filename = uploaded_pdf.name
                st.session_state.chat_history = []
                st.success(
                    f"Processed {uploaded_pdf.name}: "
                    f"{chunk_count} chunks indexed."
                )
            except Exception as exc:
                st.error(f"Could not process PDF: {exc}")
    else:
        st.session_state.active_file_hash = file_hash
        st.session_state.active_filename = uploaded_pdf.name
        st.info(f"Ready: {uploaded_pdf.name}")

st.divider()
st.subheader("Ask a question")

question = st.text_input(
    "Your question",
    placeholder="What are the main points in this document?",
    disabled=uploaded_pdf is None,
)

if st.button("Ask", type="primary", disabled=not question.strip()):
    with st.spinner("Searching documents and generating an answer..."):
        try:
            result = generate_answer(question)

            st.session_state.chat_history.append({
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"],
            })
        except Exception as exc:
            st.error(f"Could not generate an answer: {exc}")

for item in reversed(st.session_state.chat_history):
    with st.chat_message("user"):
        st.write(item["question"])

    with st.chat_message("assistant"):
        st.write(item["answer"])

        if item["sources"]:
            with st.expander("Sources"):
                for source in item["sources"]:
                    st.write(
                        f"📄 {source['filename']} — "
                        f"Page {source['page_number']}"
                    )

if st.session_state.chat_history:
    if st.button("Clear chat history"):
        st.session_state.chat_history = []
        st.rerun()
