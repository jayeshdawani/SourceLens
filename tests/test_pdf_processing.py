from __future__ import annotations

from io import BytesIO

import pytest

import src.pdf_processing as pdf_processing
from src.models import ExtractionReport, PageText
from src.pdf_processing import (
    PDFProcessingError,
    clean_extracted_text,
    extract_pdf_pages,
    split_pages_into_chunks,
    split_text,
    validate_searchable_collection,
)


class NamedBytesIO(BytesIO):
    def __init__(self, name: str, content: bytes = b"placeholder") -> None:
        super().__init__(content)
        self.name = name


class FakePage:
    def __init__(self, text: str | None, *, should_fail: bool = False) -> None:
        self.text = text
        self.should_fail = should_fail

    def extract_text(self) -> str | None:
        if self.should_fail:
            raise ValueError("Could not extract page text.")

        return self.text


class FakeReader:
    def __init__(
        self,
        pages: list[FakePage],
        *,
        is_encrypted: bool = False,
    ) -> None:
        self.pages = pages
        self.is_encrypted = is_encrypted


def test_clean_extracted_text_reduces_spacing_noise() -> None:
    raw_text = "  First   line  \n\n\n\n  Second\tline "

    assert clean_extracted_text(raw_text) == "First line\n\nSecond line"


def test_extract_pdf_pages_preserves_filename_and_page_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader = FakeReader([FakePage("Introduction"), FakePage("Second page")])
    monkeypatch.setattr(pdf_processing, "PdfReader", lambda _: reader)

    report = extract_pdf_pages([NamedBytesIO("guide.pdf")])

    assert report.indexed_files == ["guide.pdf"]
    assert report.document_count == 1
    assert report.extracted_page_count == 2
    assert report.pages[0] == PageText("guide.pdf", 1, "Introduction")
    assert report.pages[1] == PageText("guide.pdf", 2, "Second page")


def test_extract_pdf_pages_skips_blank_and_unreadable_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader = FakeReader(
        [
            FakePage("Readable text"),
            FakePage("   "),
            FakePage(None),
            FakePage("Ignored", should_fail=True),
        ]
    )
    monkeypatch.setattr(pdf_processing, "PdfReader", lambda _: reader)

    report = extract_pdf_pages([NamedBytesIO("mixed.pdf")])

    assert report.total_pages == 4
    assert report.extracted_page_count == 1
    assert report.skipped_pages == 3


def test_extract_pdf_pages_records_corrupted_file_and_continues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reader_factory(pdf_file: NamedBytesIO) -> FakeReader:
        if pdf_file.name == "broken.pdf":
            raise ValueError("Invalid PDF")

        return FakeReader([FakePage("Valid content")])

    monkeypatch.setattr(pdf_processing, "PdfReader", reader_factory)

    report = extract_pdf_pages(
        [NamedBytesIO("broken.pdf"), NamedBytesIO("working.pdf")]
    )

    assert report.failed_files == ["broken.pdf"]
    assert report.indexed_files == ["working.pdf"]
    assert report.extracted_page_count == 1


def test_extract_pdf_pages_records_encrypted_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pdf_processing,
        "PdfReader",
        lambda _: FakeReader([], is_encrypted=True),
    )

    report = extract_pdf_pages([NamedBytesIO("protected.pdf")])

    assert report.encrypted_files == ["protected.pdf"]
    assert report.pages == []


def test_split_text_creates_overlapping_chunks() -> None:
    text = " ".join(f"token-{index}" for index in range(80))

    chunks = split_text(text, chunk_size=100, chunk_overlap=20)

    assert len(chunks) > 1
    assert all(chunks)
    assert max(len(chunk) for chunk in chunks) <= 100


def test_split_pages_into_chunks_preserves_source_metadata() -> None:
    pages = [PageText("notes.pdf", 3, " ".join(["sample"] * 80))]

    chunks = split_pages_into_chunks(pages, chunk_size=80, chunk_overlap=10)

    assert len(chunks) > 1
    assert all(chunk.source == "notes.pdf" for chunk in chunks)
    assert all(chunk.page_number == 3 for chunk in chunks)
    assert [chunk.chunk_number for chunk in chunks] == list(range(1, len(chunks) + 1))


def test_validate_searchable_collection_rejects_empty_result() -> None:
    report = ExtractionReport(non_extractable_files=["scan.pdf"])

    with pytest.raises(PDFProcessingError, match="No searchable text"):
        validate_searchable_collection(report, [])
