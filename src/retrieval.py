from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from src.models import RetrievedPassage, TextChunk


class VectorIndexError(ValueError):
    """Raised when a local vector index cannot be built or searched."""


class VectorIndex:
    """In-memory cosine-similarity index for document chunk embeddings."""

    def __init__(self, chunks: Sequence[TextChunk], embeddings: np.ndarray) -> None:
        if not chunks:
            raise VectorIndexError("At least one text chunk is required.")

        matrix = np.asarray(embeddings, dtype=np.float32)

        if matrix.ndim != 2:
            raise VectorIndexError("Embeddings must be a two-dimensional matrix.")

        if matrix.shape[0] != len(chunks):
            raise VectorIndexError(
                "The number of embeddings must match the number of text chunks."
            )

        if matrix.shape[1] == 0:
            raise VectorIndexError("Embedding vectors cannot be empty.")

        self._chunks = tuple(chunks)
        self._embeddings = normalize_rows(matrix)

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    @property
    def embedding_dimensions(self) -> int:
        return int(self._embeddings.shape[1])

    def search(self, query_embedding: np.ndarray, *, top_k: int) -> list[RetrievedPassage]:
        """Return the highest-scoring document chunks for an embedded question."""

        if top_k <= 0:
            raise VectorIndexError("top_k must be greater than zero.")

        query_vector = normalize_vector(np.asarray(query_embedding, dtype=np.float32))

        if query_vector.shape[0] != self.embedding_dimensions:
            raise VectorIndexError(
                "The query embedding dimensions do not match the document index."
            )

        scores = self._embeddings @ query_vector
        result_count = min(top_k, len(self._chunks))
        ranked_indices = np.argsort(-scores, kind="stable")[:result_count]
        passages: list[RetrievedPassage] = []

        for rank, index in enumerate(ranked_indices, start=1):
            chunk = self._chunks[int(index)]
            passages.append(
                RetrievedPassage(
                    rank=rank,
                    source=chunk.source,
                    page_number=chunk.page_number,
                    chunk_number=chunk.chunk_number,
                    content=chunk.content,
                    similarity_score=float(scores[int(index)]),
                )
            )

        return passages


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    """L2-normalize an embedding matrix for cosine-similarity search."""

    norms = np.linalg.norm(matrix, axis=1, keepdims=True)

    if np.any(norms == 0):
        raise VectorIndexError("Embedding vectors cannot have zero length.")

    return matrix / norms


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """L2-normalize one embedding vector."""

    if vector.ndim != 1:
        raise VectorIndexError("The query embedding must be one-dimensional.")

    norm = np.linalg.norm(vector)

    if norm == 0:
        raise VectorIndexError("The query embedding cannot have zero length.")

    return vector / norm
