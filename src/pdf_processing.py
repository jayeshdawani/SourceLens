from __future__ import annotations

import re
from collections.abc import Sequence
from typing import BinaryIO

from pypdf import PdfReader

from src.models import ExtractionReport, PageText, TextChunk


class PDFProcessingError(ValueError):
    """Raised when a document collection cannot produce searchable chunks."""


def clean_extracted_text(text: str) -> str:
    """Reduce spacing noise while preserving useful paragraph boundaries."""

    normalized_lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    cleaned_text = "\n".join(normalized_lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    return cleaned_text.strip()


def extract_pdf_pages(pdf_files: Sequence[BinaryIO]) -> ExtractionReport:
    """
    Extract readable text page by page from uploaded PDFs.

    A damaged, encrypted, or image-only PDF is recorded and skipped without
    preventing other uploaded documents from being processed.
    """

    report = ExtractionReport()

    for pdf_file in pdf_files:
        file_name = _get_file_name(pdf_file)

        try:
            if hasattr(pdf_file, "seek"):
                pdf_file.seek(0)

            reader = PdfReader(pdf_file)

            if reader.is_encrypted:
                _append_unique(report.encrypted_files, file_name)
                continue

            extracted_pages_for_file = 0

            for page_number, page in enumerate(reader.pages, start=1):
                report.total_pages += 1

                try:
                    page_text = clean_extracted_text(page.extract_text() or "")
                except Exception:
                    report.skipped_pages += 1
                    continue

                if not page_text:
                    report.skipped_pages += 1
                    continue

                report.pages.append(
                    PageText(
                        source=file_name,
                        page_number=page_number,
                        content=page_text,
                    )
                )
                extracted_pages_for_file += 1

            if extracted_pages_for_file:
                _append_unique(report.indexed_files, file_name)
            else:
                _append_unique(report.non_extractable_files, file_name)

        except Exception:
            _append_unique(report.failed_files, file_name)

    return report


def split_pages_into_chunks(
    pages: Sequence[PageText],
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    """Split page text into overlapping chunks while retaining source metadata."""

    _validate_chunk_settings(chunk_size, chunk_overlap)
    chunks: list[TextChunk] = []
    next_chunk_number = 1

    for page in pages:
        for content in split_text(
            page.content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        ):
            chunks.append(
                TextChunk(
                    source=page.source,
                    page_number=page.page_number,
                    chunk_number=next_chunk_number,
                    content=content,
                )
            )
            next_chunk_number += 1

    return chunks


def split_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Create paragraph-aware sliding chunks.

    The splitter prefers paragraph, line, sentence, and word boundaries near
    the end of each window. It falls back to a character boundary when needed.
    """

    _validate_chunk_settings(chunk_size, chunk_overlap)
    cleaned_text = clean_extracted_text(text)

    if not cleaned_text:
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(cleaned_text)

    while start < text_length:
        maximum_end = min(start + chunk_size, text_length)
        end = maximum_end

        if maximum_end < text_length:
            end = _find_preferred_boundary(
                cleaned_text,
                start=start,
                maximum_end=maximum_end,
            )

        content = cleaned_text[start:end].strip()

        if content:
            chunks.append(content)

        if end >= text_length:
            break

        next_start = max(end - chunk_overlap, start + 1)
        start = _skip_leading_whitespace(cleaned_text, next_start)

    return chunks


def validate_searchable_collection(
    report: ExtractionReport,
    chunks: Sequence[TextChunk],
) -> None:
    """Raise a clear error when uploaded files do not yield searchable text."""

    if chunks:
        return

    if not report.indexed_files:
        raise PDFProcessingError(
            "No searchable text was extracted. Try a text-based PDF. "
            "Scanned image-only PDFs require OCR, which this version does not include."
        )

    raise PDFProcessingError(
        "Text was extracted, but no searchable chunks were created. "
        "Check the chunk settings in your .env file."
    )


def _find_preferred_boundary(text: str, *, start: int, maximum_end: int) -> int:
    search_floor = start + int((maximum_end - start) * 0.55)

    for separator in ("\n\n", "\n", ". ", " "):
        boundary = text.rfind(separator, search_floor, maximum_end)

        if boundary != -1:
            return boundary + len(separator)

    return maximum_end


def _skip_leading_whitespace(text: str, start: int) -> int:
    while start < len(text) and text[start].isspace():
        start += 1

    return start


def _validate_chunk_settings(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")


def _get_file_name(pdf_file: BinaryIO) -> str:
    return str(getattr(pdf_file, "name", "uploaded-document.pdf"))


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
