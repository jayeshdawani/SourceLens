from __future__ import annotations

from typing import Any

import streamlit as st

from src.config import ConfigurationError, Settings, load_settings
from src.models import CollectionSummary, ExtractionReport
from src.openai_service import OpenAIService, validate_question
from src.pdf_processing import (
    PDFProcessingError,
    extract_pdf_pages,
    split_pages_into_chunks,
    validate_searchable_collection,
)
from src.retrieval import VectorIndex
from src.ui import (
    render_collection_summary,
    render_empty_state,
    render_extraction_warnings,
    render_header,
    render_referenced_passages,
    render_styles,
)


st.set_page_config(
    page_title="SourceLens",
    page_icon="📚",
    layout="wide",
)


def initialize_session_state() -> None:
    defaults: dict[str, Any] = {
        "vector_index": None,
        "collection_summary": None,
        "chat_messages": [],
        "uploader_version": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_chat() -> None:
    st.session_state.chat_messages = []


def remove_collection() -> None:
    st.session_state.vector_index = None
    st.session_state.collection_summary = None
    st.session_state.chat_messages = []
    st.session_state.uploader_version += 1


def build_collection(pdf_files: list[Any]) -> tuple[ExtractionReport, CollectionSummary]:
    if not pdf_files:
        raise PDFProcessingError("Add at least one PDF before building the index.")

    settings = load_settings()
    report = extract_pdf_pages(pdf_files)
    chunks = split_pages_into_chunks(
        report.pages,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    validate_searchable_collection(report, chunks)

    service = OpenAIService(settings)
    vector_index = service.build_vector_index(chunks)
    summary = CollectionSummary(
        document_names=tuple(report.indexed_files),
        total_pages=report.total_pages,
        extracted_pages=report.extracted_page_count,
        chunk_count=vector_index.chunk_count,
        skipped_pages=report.skipped_pages,
        failed_files=tuple(report.failed_files),
        encrypted_files=tuple(report.encrypted_files),
        non_extractable_files=tuple(report.non_extractable_files),
    )

    st.session_state.vector_index = vector_index
    st.session_state.collection_summary = summary
    reset_chat()

    return report, summary


def answer_user_question(question: str) -> None:
    clean_question = validate_question(question)
    vector_index = _get_vector_index()
    settings = load_settings()
    service = OpenAIService(settings)

    earlier_messages = list(st.session_state.chat_messages)
    st.session_state.chat_messages.append(
        {
            "role": "user",
            "content": clean_question,
        }
    )

    query_embedding = service.embed_question(clean_question)
    passages = vector_index.search(
        query_embedding,
        top_k=settings.retrieval_count,
    )
    answer = service.answer_question(
        question=clean_question,
        passages=passages,
        chat_history=earlier_messages,
    )
    st.session_state.chat_messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": passages,
        }
    )


def _get_vector_index() -> VectorIndex:
    vector_index = st.session_state.vector_index

    if vector_index is None:
        raise PDFProcessingError(
            "Build a document index before asking questions. Add PDFs in the sidebar first."
        )

    return vector_index


def render_sidebar() -> None:
    with st.sidebar:
        st.subheader("PDF Collection")
        st.caption("Add text-based PDFs and create a local search index for this session.")

        pdf_files = st.file_uploader(
            "Add PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            key=f"pdf-uploader-{st.session_state.uploader_version}",
            help="Scanned image-only PDFs are not supported unless OCR is added.",
        )

        if st.button("Build Document Index", type="primary", use_container_width=True):
            try:
                with st.status("Building document index...", expanded=True) as status:
                    st.write("Reading PDFs, creating passages, and requesting embeddings")
                    report, summary = build_collection(pdf_files)
                    st.write("Stored searchable passages in the local vector index")
                    status.update(label="Collection ready", state="complete")

                render_extraction_warnings(report)
                st.success(
                    f"Indexed {len(summary.document_names)} documents and "
                    f"{summary.chunk_count} passages."
                )
            except (ConfigurationError, PDFProcessingError, ValueError) as error:
                st.error(str(error))
            except Exception as error:
                st.error(
                    "The index could not be built. Check your OpenAI API key, model "
                    "access, internet connection, and uploaded PDFs."
                )
                st.caption(f"Technical detail: {error}")

        summary: CollectionSummary | None = st.session_state.collection_summary

        if summary is not None:
            render_collection_summary(summary)
            st.divider()

            if st.button("Start New Conversation", use_container_width=True):
                reset_chat()
                st.rerun()

            if st.button("Remove Collection", use_container_width=True):
                remove_collection()
                st.rerun()

        st.divider()
        st.caption(
            "Your index stays in memory for the current Streamlit session. "
            "Uploaded document text is not persisted by this app."
        )


def render_chat() -> None:
    summary: CollectionSummary | None = st.session_state.collection_summary

    if summary is None:
        render_empty_state()

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                render_referenced_passages(message.get("sources", []))

    question = st.chat_input("Search your PDF collection")

    if question is None:
        return

    try:
        with st.spinner("Searching indexed passages and preparing an answer..."):
            answer_user_question(question)
        st.rerun()
    except (ConfigurationError, PDFProcessingError, ValueError) as error:
        st.warning(str(error))
    except Exception as error:
        st.error(
            "The question could not be answered. Check your OpenAI API key, model "
            "access, and internet connection, then try again."
        )
        st.caption(f"Technical detail: {error}")


def main() -> None:
    initialize_session_state()
    render_styles()
    render_sidebar()
    render_header()
    render_chat()


if __name__ == "__main__":
    main()
