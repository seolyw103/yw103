from __future__ import annotations

from functools import lru_cache

from notion_client import Client

from ..config import get_settings


@lru_cache(maxsize=1)
def get_client() -> Client:
    settings = get_settings()
    if not settings.notion_token:
        raise RuntimeError("NOTION_TOKEN is not set")
    return Client(auth=settings.notion_token)
