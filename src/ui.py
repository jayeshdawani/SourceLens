from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

from src.models import CollectionSummary, ExtractionReport, RetrievedPassage


APP_STYLES = """
<style>
    :root {
        --sl-ink: #1d2939;
        --sl-muted: #667085;
        --sl-border: #e4e7ec;
        --sl-panel: #f8fafc;
        --sl-accent: #355c7d;
    }

    .block-container {
        max-width: 1120px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .sl-header {
        border-bottom: 1px solid var(--sl-border);
        margin-bottom: 1.2rem;
        padding-bottom: 1rem;
    }

    .sl-eyebrow {
        color: var(--sl-accent);
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
    }

    .sl-title {
        color: var(--sl-ink);
        font-size: 2.2rem;
        font-weight: 720;
        letter-spacing: -0.04em;
        line-height: 1.05;
        margin: 0;
    }

    .sl-subtitle {
        color: var(--sl-muted);
        font-size: 1rem;
        margin-top: 0.55rem;
        max-width: 680px;
    }

    .sl-empty-state {
        background: var(--sl-panel);
        border: 1px solid var(--sl-border);
        border-radius: 0.85rem;
        margin-top: 1rem;
        padding: 1.35rem 1.45rem;
    }

    .sl-empty-state h3 {
        color: var(--sl-ink);
        font-size: 1.05rem;
        margin: 0 0 0.35rem 0;
    }

    .sl-empty-state p {
        color: var(--sl-muted);
        font-size: 0.92rem;
        margin: 0;
    }

    .sl-status {
        background: var(--sl-panel);
        border: 1px solid var(--sl-border);
        border-radius: 0.7rem;
        margin: 0.75rem 0;
        padding: 0.75rem 0.85rem;
    }

    .sl-status strong {
        color: var(--sl-ink);
        display: block;
        font-size: 0.88rem;
        margin-bottom: 0.2rem;
    }

    .sl-status span {
        color: var(--sl-muted);
        font-size: 0.79rem;
    }

    .sl-source-meta {
        color: var(--sl-muted);
        font-size: 0.78rem;
        margin-bottom: 0.4rem;
    }

    .sl-source-text {
        color: var(--sl-ink);
        font-size: 0.9rem;
        line-height: 1.55;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid var(--sl-border);
    }
</style>
"""


def render_styles() -> None:
    st.markdown(APP_STYLES, unsafe_allow_html=True)


def render_header() -> None:
    st.markdown(
        """
        <div class="sl-header">
            <div class="sl-eyebrow">PDF collection workspace</div>
            <h1 class="sl-title">SourceLens</h1>
            <div class="sl-subtitle">
                Ask focused questions across a collection of PDF documents and inspect
                the passages used to support each response.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="sl-empty-state">
            <h3>Build a searchable PDF collection</h3>
            <p>
                Add one or more text-based PDF files in the sidebar, then select
                <strong>Build Document Index</strong>. Once indexing finishes, ask a
                question here and expand the referenced passages under each answer.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_collection_summary(summary: CollectionSummary) -> None:
    st.markdown(
        f"""
        <div class="sl-status">
            <strong>Collection ready</strong>
            <span>{len(summary.document_names)} documents · {summary.extracted_pages} readable pages · {summary.chunk_count} searchable passages</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Indexed documents")

    for document_name in summary.document_names:
        st.markdown(f"- `{document_name}`")

    if summary.skipped_pages:
        st.caption(f"Skipped pages without readable text: {summary.skipped_pages}")


def render_extraction_warnings(report: ExtractionReport) -> None:
    if report.failed_files:
        st.warning("Could not read: " + ", ".join(report.failed_files))

    if report.encrypted_files:
        st.warning("Password-protected PDFs skipped: " + ", ".join(report.encrypted_files))

    if report.non_extractable_files:
        st.warning(
            "No readable text found in: " + ", ".join(report.non_extractable_files)
        )

    if report.skipped_pages:
        st.info(f"Skipped {report.skipped_pages} pages without readable text.")


def render_referenced_passages(passages: Sequence[RetrievedPassage]) -> None:
    if not passages:
        return

    with st.expander(f"Referenced passages ({len(passages)})"):
        for passage in passages:
            st.markdown(
                f"**[{passage.rank}] {passage.source} · page {passage.page_number}**"
            )
            st.markdown(
                f'<div class="sl-source-meta">Chunk {passage.chunk_number} · similarity score {passage.similarity_score:.3f}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="sl-source-text">{_escape_html(passage.content)}</div>',
                unsafe_allow_html=True,
            )

            if passage.rank != len(passages):
                st.divider()


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
        .replace("\n", "<br>")
    )
