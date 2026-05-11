from __future__ import annotations

from urllib.parse import urlparse

from ..schema import RawContent
from . import pdf, rss, twitter, web, youtube


def extract(url: str) -> RawContent:
    """Dispatch URL to the appropriate extractor."""
    host = (urlparse(url).hostname or "").lower()

    if host.endswith("youtube.com") or host == "youtu.be":
        return youtube.extract(url)
    if host in {"twitter.com", "x.com"} or host.endswith(".twitter.com") or host.endswith(".x.com"):
        return twitter.extract(url)
    if url.lower().endswith(".pdf"):
        return pdf.extract(url)
    return web.extract(url)


__all__ = ["extract", "youtube", "pdf", "web", "rss", "twitter"]
