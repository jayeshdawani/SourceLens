from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PageText:
    """Readable text extracted from one PDF page."""

    source: str
    page_number: int
    content: str


@dataclass(frozen=True)
class TextChunk:
    """A searchable text segment that retains its PDF location."""

    source: str
    page_number: int
    chunk_number: int
    content: str


@dataclass(frozen=True)
class RetrievedPassage:
    """A text chunk returned by semantic similarity search."""

    rank: int
    source: str
    page_number: int
    chunk_number: int
    content: str
    similarity_score: float


@dataclass
class ExtractionReport:
    """Summary of PDF extraction results for one uploaded collection."""

    pages: list[PageText] = field(default_factory=list)
    indexed_files: list[str] = field(default_factory=list)
    failed_files: list[str] = field(default_factory=list)
    encrypted_files: list[str] = field(default_factory=list)
    non_extractable_files: list[str] = field(default_factory=list)
    skipped_pages: int = 0
    total_pages: int = 0

    @property
    def document_count(self) -> int:
        return len(self.indexed_files)

    @property
    def extracted_page_count(self) -> int:
        return len(self.pages)


@dataclass(frozen=True)
class CollectionSummary:
    """Metadata shown in the sidebar after indexing succeeds."""

    document_names: tuple[str, ...]
    total_pages: int
    extracted_pages: int
    chunk_count: int
    skipped_pages: int
    failed_files: tuple[str, ...] = ()
    encrypted_files: tuple[str, ...] = ()
    non_extractable_files: tuple[str, ...] = ()
