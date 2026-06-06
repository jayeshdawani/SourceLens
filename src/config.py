from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(ValueError):
    """Raised when application settings are missing or invalid."""


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    chat_model: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    retrieval_count: int
    max_history_messages: int
    max_context_chars: int
    embedding_batch_size: int


def load_settings(*, require_api_key: bool = True) -> Settings:
    """Load SourceLens configuration from environment variables."""

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if require_api_key and not api_key:
        raise ConfigurationError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and add "
            "your OpenAI API key before building an index."
        )

    chat_model = _read_text("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    embedding_model = _read_text(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small",
    )
    chunk_size = _read_positive_int("SOURCE_LENS_CHUNK_SIZE", 1100)
    chunk_overlap = _read_non_negative_int("SOURCE_LENS_CHUNK_OVERLAP", 180)

    if chunk_overlap >= chunk_size:
        raise ConfigurationError(
            "SOURCE_LENS_CHUNK_OVERLAP must be smaller than "
            "SOURCE_LENS_CHUNK_SIZE."
        )

    return Settings(
        openai_api_key=api_key,
        chat_model=chat_model,
        embedding_model=embedding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        retrieval_count=_read_positive_int("SOURCE_LENS_TOP_K", 4),
        max_history_messages=_read_non_negative_int(
            "SOURCE_LENS_MAX_HISTORY_MESSAGES",
            6,
        ),
        max_context_chars=_read_positive_int(
            "SOURCE_LENS_MAX_CONTEXT_CHARS",
            9000,
        ),
        embedding_batch_size=_read_positive_int(
            "SOURCE_LENS_EMBEDDING_BATCH_SIZE",
            64,
        ),
    )


def _read_text(variable_name: str, default: str) -> str:
    value = os.getenv(variable_name, default).strip()

    if not value:
        raise ConfigurationError(f"{variable_name} cannot be empty.")

    return value


def _read_positive_int(variable_name: str, default: int) -> int:
    value = _read_integer(variable_name, default)

    if value <= 0:
        raise ConfigurationError(f"{variable_name} must be greater than zero.")

    return value


def _read_non_negative_int(variable_name: str, default: int) -> int:
    value = _read_integer(variable_name, default)

    if value < 0:
        raise ConfigurationError(f"{variable_name} cannot be negative.")

    return value


def _read_integer(variable_name: str, default: int) -> int:
    raw_value = os.getenv(variable_name, str(default)).strip()

    try:
        return int(raw_value)
    except ValueError as error:
        raise ConfigurationError(f"{variable_name} must be an integer.") from error
