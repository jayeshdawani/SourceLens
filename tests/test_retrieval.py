from __future__ import annotations

import numpy as np
import pytest

from src.models import TextChunk
from src.retrieval import VectorIndex, VectorIndexError


def make_chunks() -> list[TextChunk]:
    return [
        TextChunk("ml-notes.pdf", 1, 1, "Neural networks learn layered representations."),
        TextChunk("database.pdf", 2, 2, "Indexes improve database lookup performance."),
        TextChunk("web.pdf", 4, 3, "HTTP is a request-response protocol."),
    ]


def test_vector_index_returns_highest_similarity_first() -> None:
    index = VectorIndex(
        make_chunks(),
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
        ),
    )

    passages = index.search(np.array([0.95, 0.05, 0.0]), top_k=2)

    assert [passage.source for passage in passages] == [
        "ml-notes.pdf",
        "database.pdf",
    ]
    assert passages[0].similarity_score > passages[1].similarity_score


def test_vector_index_limits_results_to_available_chunks() -> None:
    index = VectorIndex(make_chunks(), np.eye(3))

    passages = index.search(np.array([1.0, 0.0, 0.0]), top_k=10)

    assert len(passages) == 3


def test_vector_index_rejects_dimension_mismatch() -> None:
    index = VectorIndex(make_chunks(), np.eye(3))

    with pytest.raises(VectorIndexError, match="dimensions do not match"):
        index.search(np.array([1.0, 0.0]), top_k=2)


def test_vector_index_rejects_zero_vector() -> None:
    with pytest.raises(VectorIndexError, match="zero length"):
        VectorIndex(make_chunks(), np.zeros((3, 3)))
