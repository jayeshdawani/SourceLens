from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
import pytest

from src.config import Settings
from src.models import RetrievedPassage, TextChunk
from src.openai_service import OpenAIService, build_answer_prompt, validate_question


@dataclass
class FakeEmbeddingItem:
    index: int
    embedding: list[float]


class FakeEmbeddingsAPI:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, *, model: str, input: list[str]) -> SimpleNamespace:
        self.calls.append({"model": model, "input": input})
        data = [
            FakeEmbeddingItem(index=index, embedding=[float(len(text)), float(index + 1)])
            for index, text in enumerate(input)
        ]
        return SimpleNamespace(data=data)


class FakeResponsesAPI:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="Supported answer [1]")


class FakeClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsAPI()
        self.responses = FakeResponsesAPI()


def make_settings(**overrides: object) -> Settings:
    values = {
        "openai_api_key": "test-key",
        "chat_model": "gpt-4.1-mini",
        "embedding_model": "text-embedding-3-small",
        "chunk_size": 1100,
        "chunk_overlap": 180,
        "retrieval_count": 4,
        "max_history_messages": 6,
        "max_context_chars": 9000,
        "embedding_batch_size": 2,
    }
    values.update(overrides)
    return Settings(**values)


def test_embed_texts_batches_requests() -> None:
    client = FakeClient()
    service = OpenAIService(make_settings(), client=client)

    embeddings = service.embed_texts(["one", "two", "three"])

    assert embeddings.shape == (3, 2)
    assert len(client.embeddings.calls) == 2
    assert client.embeddings.calls[0]["input"] == ["one", "two"]
    assert client.embeddings.calls[1]["input"] == ["three"]


def test_build_vector_index_uses_embedded_chunk_text() -> None:
    client = FakeClient()
    service = OpenAIService(make_settings(), client=client)
    chunks = [
        TextChunk("guide.pdf", 1, 1, "alpha"),
        TextChunk("guide.pdf", 2, 2, "beta"),
    ]

    index = service.build_vector_index(chunks)

    assert index.chunk_count == 2
    assert client.embeddings.calls[0]["input"] == ["alpha", "beta"]


def test_answer_question_calls_responses_api() -> None:
    client = FakeClient()
    service = OpenAIService(make_settings(), client=client)
    passages = [
        RetrievedPassage(1, "guide.pdf", 2, 4, "Relevant text", 0.92),
    ]

    answer = service.answer_question(
        question="What does the guide say?",
        passages=passages,
        chat_history=[],
    )

    assert answer == "Supported answer [1]"
    assert client.responses.calls[0]["model"] == "gpt-4.1-mini"
    assert "guide.pdf, page 2" in str(client.responses.calls[0]["input"])


def test_build_answer_prompt_limits_context_characters() -> None:
    passages = [
        RetrievedPassage(1, "guide.pdf", 1, 1, "x" * 200, 0.9),
    ]

    prompt = build_answer_prompt(
        question="Summarize this.",
        passages=passages,
        chat_history=[],
        max_history_messages=6,
        max_context_chars=80,
    )

    assert "x" * 200 not in prompt
    assert "guide.pdf, page 1" in prompt


def test_validate_question_rejects_whitespace() -> None:
    with pytest.raises(ValueError, match="Enter a question"):
        validate_question("   ")
