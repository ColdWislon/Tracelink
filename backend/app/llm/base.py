"""LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class LLMMessage:
    role: Role
    content: str


class LLMProvider(ABC):
    """Minimal chat-completion interface backing future AI features.

    Concrete providers (Anthropic Claude, Azure OpenAI, Bedrock, local) implement
    :meth:`complete`. The default Claude model when implemented should be the
    latest and most capable (e.g. ``claude-opus-4-8``).
    """

    name: str = "abstract"

    @abstractmethod
    def complete(
        self, messages: list[LLMMessage], *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> str:
        """Return the assistant's completion for a conversation."""
        raise NotImplementedError
