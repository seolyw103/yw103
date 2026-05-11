from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass
class FeedItem:
    title: str
    link: str
    published_at: dt.date | None
    summary: str


def fetch_feed(feed_url: str, limit: int = 20) -> list[FeedItem]:
    """Return recent items from an RSS/Atom feed. Each item's link is meant
    to be fed to `sources.extract()` for full-content extraction."""
    import feedparser

    parsed = feedparser.parse(feed_url)
    out: list[FeedItem] = []
    for entry in parsed.entries[:limit]:
        published = None
        for key in ("published_parsed", "updated_parsed"):
            tm = entry.get(key)
            if tm:
                published = dt.date(tm.tm_year, tm.tm_mon, tm.tm_mday)
                break
        out.append(
            FeedItem(
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                published_at=published,
                summary=entry.get("summary", ""),
            )
        )
    return out
