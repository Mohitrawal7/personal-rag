
import hashlib
import tempfile
from pathlib import Path

import streamlit as st

from app.generation.answer_generator import generate_answer
from app.storage.ingest_to_db import ingest_file
from app.storage.documents import list_documents, delete_document


st.set_page_config(
    page_title="Personal PDF RAG",
    page_icon="📚",
    layout="centered",
)

st.title("📚 Personal PDF Assistant")
st.caption("Upload a PDF, ask questions, and explore your indexed documents.")

# --------------------------------------------------
# Session state
# --------------------------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "ingested_hashes" not in st.session_state:
    st.session_state.ingested_hashes = set()

if "pending_delete_document" not in st.session_state:
    st.session_state.pending_delete_document = None

if "deleted_upload_hash" not in st.session_state:
    st.session_state.deleted_upload_hash = None


# --------------------------------------------------
# PDF upload and ingestion
# --------------------------------------------------

uploaded_pdf = st.file_uploader(
    "Upload one PDF",
    type=["pdf"],
    accept_multiple_files=False,
)

if uploaded_pdf is None:
    # Allow a deleted PDF to be uploaded again after the user
    # removes it from the uploader.
    st.session_state.deleted_upload_hash = None

else:
    pdf_bytes = uploaded_pdf.getvalue()
    file_hash = hashlib.sha256(pdf_bytes).hexdigest()

    if st.session_state.deleted_upload_hash == file_hash:
        st.warning(
            "This PDF was deleted from the library. "
            "Remove it from the uploader before uploading it again."
        )

    elif file_hash not in st.session_state.ingested_hashes:
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


# --------------------------------------------------
# Document library
# --------------------------------------------------

st.divider()
st.header("Document Library")

if st.button("Refresh library"):
    st.rerun()

documents = []

try:
    documents = list_documents()

    if not documents:
        st.info("No indexed documents yet. Upload a PDF to get started.")

    else:
        st.caption(f"{len(documents)} indexed document(s)")

        for document in documents:
            document_id = document["document_id"]

            with st.container(border=True):
                st.write(f"**{document['filename']}**")
                st.caption(f"ID: {document_id}")

                col1, col2, col3 = st.columns(3)

                col1.metric("Pages", document["page_count"])
                col2.metric("Chunks", document["chunk_count"])

                created_at = document["created_at"]

                col3.metric(
                    "Added",
                    created_at.strftime("%Y-%m-%d")
                    if created_at
                    else "Unknown",
                )

                if st.button(
                    "Delete document",
                    key=f"delete_{document_id}",
                ):
                    st.session_state.pending_delete_document = document_id
                    st.rerun()

except Exception as exc:
    st.error(f"Could not load the document library: {exc}")


# --------------------------------------------------
# Delete confirmation
# --------------------------------------------------

pending_id = st.session_state.pending_delete_document

if pending_id:
    selected_document = next(
        (
            document
            for document in documents
            if document["document_id"] == pending_id
        ),
        None,
    )

    if selected_document is None:
        st.warning(
            "The selected document is no longer in the library. "
            "Refresh the library before continuing."
        )

        if st.button("Dismiss deletion request"):
            st.session_state.pending_delete_document = None
            st.rerun()

    else:
        st.warning(
            f"Permanently delete **{selected_document['filename']}** "
            "and all its indexed chunks? This cannot be undone."
        )

        confirm_col, cancel_col = st.columns(2)

        with confirm_col:
            if st.button(
                "Permanently delete",
                type="primary",
                key="confirm_delete_document",
            ):
                try:
                    deleted = delete_document(pending_id)

                    if deleted:
                        # Clear active session state if the deleted
                        # document was the active PDF.
                        if (
                            st.session_state.get("active_file_hash")
                            == pending_id
                        ):
                            st.session_state.pop("active_file_hash", None)
                            st.session_state.pop("active_filename", None)

                        # Clear conversation history because answers
                        # may have cited the deleted document.
                        st.session_state.chat_history = []

                        # Allow normal upload processing again only
                        # after the uploader is cleared.
                        st.session_state.ingested_hashes.discard(pending_id)
                        st.session_state.deleted_upload_hash = pending_id
                        st.session_state.pending_delete_document = None

                        st.success(
                            "Document and associated chunks deleted."
                        )
                        st.rerun()

                    else:
                        st.warning(
                            "The document was not found or was already deleted."
                        )

                except Exception as exc:
                    st.error(f"Could not delete the document: {exc}")

        with cancel_col:
            if st.button(
                "Cancel",
                key="cancel_delete_document",
            ):
                st.session_state.pending_delete_document = None
                st.rerun()


# --------------------------------------------------
# Question answering
# --------------------------------------------------

st.divider()
st.subheader("Ask a question")

question = st.text_input(
    "Your question",
    placeholder="What are the main points in this document?",
    disabled=(
        uploaded_pdf is None
        or st.session_state.get("deleted_upload_hash")
        == hashlib.sha256(uploaded_pdf.getvalue()).hexdigest()
    ),
)

if st.button(
    "Ask",
    type="primary",
    disabled=not question.strip(),
):
    with st.spinner("Searching documents and generating an answer..."):
        try:
            result = generate_answer(question)

            st.session_state.chat_history.append(
                {
                    "question": question,
                    "answer": result["answer"],
                    "sources": result["sources"],
                }
            )

        except Exception as exc:
            st.error(f"Could not generate an answer: {exc}")


# --------------------------------------------------
# Chat history and sources
# --------------------------------------------------

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
