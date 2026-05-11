"""RSS / Atom feed handling.

Two responsibilities:
1. Fetching feed items (`fetch_feed`) — used for one-off inspection.
2. Polling for *new* items since the last run (`poll_new`), with
   per-feed cursor state persisted in `.feed_state.json` at the repo root.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

from ..config import REPO_ROOT

FEED_STATE_PATH: Path = REPO_ROOT / ".feed_state.json"


@dataclass
class FeedItem:
    title: str
    link: str
    published_at: dt.date | None
    summary: str


def fetch_feed(feed_url: str, limit: int = 20) -> list[FeedItem]:
    """Return recent items from an RSS/Atom feed (no state mutation)."""
    import feedparser

    parsed = feedparser.parse(feed_url)
    out: list[FeedItem] = []
    for entry in parsed.entries[:limit]:
        out.append(_to_item(entry))
    return out


def _to_item(entry) -> FeedItem:
    published = None
    for key in ("published_parsed", "updated_parsed"):
        tm = entry.get(key)
        if tm:
            published = dt.date(tm.tm_year, tm.tm_mon, tm.tm_mday)
            break
    return FeedItem(
        title=entry.get("title", ""),
        link=entry.get("link", ""),
        published_at=published,
        summary=entry.get("summary", ""),
    )


def _load_state() -> dict[str, str]:
    if not FEED_STATE_PATH.exists():
        return {}
    return json.loads(FEED_STATE_PATH.read_text())


def _save_state(state: dict[str, str]) -> None:
    FEED_STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def poll_new(feed_url: str, *, limit: int = 50) -> list[FeedItem]:
    """Return only items published *after* the last poll for this feed.
    State is keyed by feed_url and updated to the newest item's link.
    """
    items = fetch_feed(feed_url, limit=limit)
    state = _load_state()
    last_link = state.get(feed_url)

    new: list[FeedItem] = []
    for item in items:
        if item.link == last_link:
            break
        new.append(item)

    if items:
        state[feed_url] = items[0].link
        _save_state(state)

    return new
