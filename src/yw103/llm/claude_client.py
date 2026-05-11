from __future__ import annotations

from ..prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from ..schema import AnalysisRecord, RawContent
from .base import LLMClient, truncate


class ClaudeClient(LLMClient):
    def __init__(self, api_key: str | None, model: str):
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        from anthropic import Anthropic
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def analyze(self, raw: RawContent) -> AnalysisRecord:
        schema = AnalysisRecord.model_json_schema()
        # Anthropic tool_use requires `input_schema` (object). Pydantic emits a valid one.
        tool = {
            "name": "record_analysis",
            "description": "발화자의 시장 분석을 구조화하여 기록한다.",
            "input_schema": schema,
        }
        user_text = USER_PROMPT_TEMPLATE.format(
            title=raw.title,
            author=raw.author,
            published_at=raw.published_at or "(unknown)",
            format=raw.format,
            url=raw.url,
            text=truncate(raw.text),
        )

        resp = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[tool],
            tool_choice={"type": "tool", "name": "record_analysis"},
            messages=[{"role": "user", "content": user_text}],
        )

        for block in resp.content:
            if block.type == "tool_use" and block.name == "record_analysis":
                # block.input is already a dict.
                return AnalysisRecord.model_validate(_merge_defaults(block.input, raw))

        raise RuntimeError("Claude did not return tool_use for record_analysis")


def _merge_defaults(payload: dict, raw: RawContent) -> dict:
    """Backfill URL / format / title from raw content if the model forgot them."""
    payload = dict(payload)
    payload.setdefault("url", raw.url)
    payload.setdefault("format", raw.format)
    payload.setdefault("title", raw.title)
    if not payload.get("speaker"):
        payload["speaker"] = raw.author
    return payload
