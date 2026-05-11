from __future__ import annotations

import json

from ..prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from ..schema import AnalysisRecord, RawContent
from .base import LLMClient, truncate


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str | None, model: str):
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def analyze(self, raw: RawContent) -> AnalysisRecord:
        schema = AnalysisRecord.model_json_schema()
        user_text = USER_PROMPT_TEMPLATE.format(
            title=raw.title,
            author=raw.author,
            published_at=raw.published_at or "(unknown)",
            format=raw.format,
            url=raw.url,
            text=truncate(raw.text),
        )

        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "AnalysisRecord",
                    "schema": schema,
                    "strict": False,
                },
            },
        )

        content = resp.choices[0].message.content or "{}"
        payload = json.loads(content)
        payload.setdefault("url", raw.url)
        payload.setdefault("format", raw.format)
        payload.setdefault("title", raw.title)
        if not payload.get("speaker"):
            payload["speaker"] = raw.author
        return AnalysisRecord.model_validate(payload)
