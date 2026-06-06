from __future__ import annotations

import pytest

from src.config import ConfigurationError, load_settings


def test_load_settings_uses_expected_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SOURCE_LENS_CHUNK_SIZE", raising=False)
    monkeypatch.delenv("SOURCE_LENS_CHUNK_OVERLAP", raising=False)

    settings = load_settings(require_api_key=False)

    assert settings.chat_model == "gpt-4.1-mini"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.chunk_size == 1100
    assert settings.chunk_overlap == 180
    assert settings.retrieval_count == 4


def test_load_settings_requires_api_key_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY is missing"):
        load_settings()


def test_load_settings_rejects_overlap_equal_to_chunk_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_LENS_CHUNK_SIZE", "100")
    monkeypatch.setenv("SOURCE_LENS_CHUNK_OVERLAP", "100")

    with pytest.raises(ConfigurationError, match="must be smaller"):
        load_settings(require_api_key=False)
