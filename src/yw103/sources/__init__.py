from __future__ import annotations

from urllib.parse import urlparse

from ..schema import RawContent
from . import pdf, web, youtube


def extract(url: str) -> RawContent:
    """Dispatch URL to the appropriate extractor."""
    host = (urlparse(url).hostname or "").lower()

    if host.endswith("youtube.com") or host == "youtu.be":
        return youtube.extract(url)
    if url.lower().endswith(".pdf"):
        return pdf.extract(url)
    return web.extract(url)


__all__ = ["extract", "youtube", "pdf", "web"]
