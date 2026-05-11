from __future__ import annotations

from ..config import get_settings
from ..schema import AnalysisRecord, RawContent
from .base import LLMClient


def get_llm() -> LLMClient:
    settings = get_settings()
    provider = settings.llm_provider
    if provider == "claude":
        from .claude_client import ClaudeClient
        return ClaudeClient(api_key=settings.anthropic_api_key, model=settings.anthropic_model)
    if provider == "openai":
        from .openai_client import OpenAIClient
        return OpenAIClient(api_key=settings.openai_api_key, model=settings.openai_model)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'claude' or 'openai')")


def analyze(raw: RawContent) -> AnalysisRecord:
    return get_llm().analyze(raw)


__all__ = ["LLMClient", "get_llm", "analyze"]
