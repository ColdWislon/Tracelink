"""Stub LLM provider — no external calls. Replaced by a real provider in Phase 6."""

from __future__ import annotations

from app.llm.base import LLMMessage, LLMProvider


class StubLLMProvider(LLMProvider):
    name = "stub"

    def complete(
        self, messages: list[LLMMessage], *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> str:
        raise NotImplementedError(
            "No LLM provider is configured. Register a concrete LLMProvider in Phase 6."
        )


_provider: LLMProvider = StubLLMProvider()


def get_llm_provider() -> LLMProvider:
    """Return the active LLM provider (the stub until one is configured)."""
    return _provider
