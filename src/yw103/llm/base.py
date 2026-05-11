from __future__ import annotations

from abc import ABC, abstractmethod

from ..schema import AnalysisRecord, RawContent


MAX_INPUT_CHARS = 60_000  # ~15k tokens, leaves headroom for prompt + completion


def truncate(text: str, limit: int = MAX_INPUT_CHARS) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n\n[... 중략 ...]\n\n" + text[-half:]


class LLMClient(ABC):
    @abstractmethod
    def analyze(self, raw: RawContent) -> AnalysisRecord: ...
