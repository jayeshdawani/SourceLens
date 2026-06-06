from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from openai import OpenAI

from src.config import Settings
from src.models import RetrievedPassage, TextChunk
from src.retrieval import VectorIndex


SYSTEM_INSTRUCTIONS = """You answer questions using only the PDF passages supplied by SourceLens.
If the retrieved passages do not contain enough information, say that you could not find a supported answer in the indexed PDFs.
Do not invent facts, page numbers, or document names.
Use concise, clear language. Refer to passage labels such as [1] or [2] when that helps the reader verify the answer."""


class OpenAIService:
    """Small wrapper around the OpenAI embeddings and Responses APIs."""

    def __init__(self, settings: Settings, *, client: Any | None = None) -> None:
        self.settings = settings
        self.client = client or OpenAI(api_key=settings.openai_api_key)

    def build_vector_index(self, chunks: Sequence[TextChunk]) -> VectorIndex:
        """Embed searchable chunks and store their vectors in memory."""

        if not chunks:
            raise ValueError("At least one chunk is required to build an index.")

        embeddings = self.embed_texts([chunk.content for chunk in chunks])
        return VectorIndex(chunks, embeddings)

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        """Embed a sequence of texts in batches while preserving input order."""

        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        embeddings: list[list[float]] = []
        batch_size = self.settings.embedding_batch_size

        for batch_start in range(0, len(texts), batch_size):
            batch = list(texts[batch_start : batch_start + batch_size])
            response = self.client.embeddings.create(
                model=self.settings.embedding_model,
                input=batch,
            )
            ordered_items = sorted(response.data, key=lambda item: item.index)
            embeddings.extend(item.embedding for item in ordered_items)

        return np.asarray(embeddings, dtype=np.float32)

    def embed_question(self, question: str) -> np.ndarray:
        """Create one query embedding after validating the user question."""

        clean_question = validate_question(question)
        return self.embed_texts([clean_question])[0]

    def answer_question(
        self,
        *,
        question: str,
        passages: Sequence[RetrievedPassage],
        chat_history: Sequence[dict[str, Any]],
    ) -> str:
        """Generate a grounded answer from retrieved PDF passages."""

        clean_question = validate_question(question)
        prompt = build_answer_prompt(
            question=clean_question,
            passages=passages,
            chat_history=chat_history,
            max_history_messages=self.settings.max_history_messages,
            max_context_chars=self.settings.max_context_chars,
        )
        response = self.client.responses.create(
            model=self.settings.chat_model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=prompt,
        )
        answer = (response.output_text or "").strip()

        if not answer:
            return "I could not generate an answer from the retrieved PDF passages."

        return answer


def build_answer_prompt(
    *,
    question: str,
    passages: Sequence[RetrievedPassage],
    chat_history: Sequence[dict[str, Any]],
    max_history_messages: int,
    max_context_chars: int,
) -> str:
    """Create a compact prompt containing recent chat turns and retrieved text."""

    history_text = _format_recent_history(chat_history, max_history_messages)
    passage_text = _format_passages(passages, max_context_chars)

    return (
        "Recent conversation:\n"
        f"{history_text}\n\n"
        "Retrieved PDF passages:\n"
        f"{passage_text}\n\n"
        "Current question:\n"
        f"{question}"
    )


def validate_question(question: str) -> str:
    """Reject empty questions and return normalized input."""

    clean_question = question.strip()

    if not clean_question:
        raise ValueError("Enter a question before submitting.")

    return clean_question


def _format_recent_history(
    chat_history: Sequence[dict[str, Any]],
    max_history_messages: int,
) -> str:
    if max_history_messages == 0:
        return "No earlier conversation was included."

    relevant_messages = [
        message
        for message in chat_history
        if message.get("role") in {"user", "assistant"} and message.get("content")
    ][-max_history_messages:]

    if not relevant_messages:
        return "No earlier conversation was included."

    formatted_lines = []

    for message in relevant_messages:
        role = "User" if message["role"] == "user" else "Assistant"
        formatted_lines.append(f"{role}: {message['content']}")

    return "\n".join(formatted_lines)


def _format_passages(
    passages: Sequence[RetrievedPassage],
    max_context_chars: int,
) -> str:
    if not passages:
        return "No relevant PDF passages were retrieved."

    formatted_passages: list[str] = []
    used_characters = 0

    for passage in passages:
        label = f"[{passage.rank}] {passage.source}, page {passage.page_number}"
        available_characters = max_context_chars - used_characters - len(label) - 2

        if available_characters <= 0:
            break

        content = passage.content[:available_characters]
        formatted_passages.append(f"{label}\n{content}")
        used_characters += len(label) + len(content) + 2

    return "\n\n".join(formatted_passages)
