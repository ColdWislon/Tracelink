"""Pluggable LLM provider seam.

Nothing in the app depends on a concrete provider yet — only on the
:class:`LLMProvider` interface — so Claude, Azure OpenAI, Bedrock, or a local
model can be dropped in later (Phase 6).
"""

from app.llm.base import LLMMessage, LLMProvider
from app.llm.stub import StubLLMProvider, get_llm_provider

__all__ = ["LLMMessage", "LLMProvider", "StubLLMProvider", "get_llm_provider"]
