"""Twitter / X tweet extractor.

Strategy: use Twitter's public syndication endpoint (cdn.syndication.twimg.com)
which serves embedded-tweet JSON without API auth. This is what publish.twitter.com
uses under the hood for embeds. The endpoint requires a "token" derived from the
tweet ID — the algorithm below mirrors the publicly-known formula used by Twitter's
own embed widget.

Caveats:
- Reply chains are not stitched (only the requested tweet's text is returned).
- For protected accounts or deleted tweets the endpoint returns 404.
- For threads, ingest each tweet URL separately.
"""
from __future__ import annotations

import datetime as dt
import math
import re

import httpx

from ..schema import RawContent


def _tweet_id(url: str) -> str:
    m = re.search(r"/status(?:es)?/(\d+)", url)
    if not m:
        raise ValueError(f"Cannot parse tweet ID from URL: {url}")
    return m.group(1)


def _syndication_token(tweet_id: str) -> str:
    """Replicates the token used by twitter.com embed widgets."""
    n = (int(tweet_id) / 1e15) * math.pi
    base = 36
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    integer_part = int(n)
    while integer_part > 0:
        out = digits[integer_part % base] + out
        integer_part //= base
    fraction = n - int(n)
    out_frac = ""
    for _ in range(20):
        fraction *= base
        d = int(fraction)
        out_frac += digits[d]
        fraction -= d
    raw = (out + out_frac).replace("0", "").replace(".", "")
    return raw or "a"


def extract(url: str) -> RawContent:
    tid = _tweet_id(url)
    token = _syndication_token(tid)
    syndication_url = (
        f"https://cdn.syndication.twimg.com/tweet-result?id={tid}&token={token}"
    )
    resp = httpx.get(
        syndication_url,
        timeout=20.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://platform.twitter.com/",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    text = data.get("text", "") or ""
    user = data.get("user") or {}
    author = user.get("name") or user.get("screen_name") or "(unknown)"

    created_at = data.get("created_at")
    published = None
    if created_at:
        try:
            published = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
        except Exception:
            try:
                published = dt.datetime.strptime(
                    created_at, "%a %b %d %H:%M:%S %z %Y"
                ).date()
            except Exception:
                pass

    return RawContent(
        title=(text[:80] + ("…" if len(text) > 80 else "")) or f"Tweet {tid}",
        author=author,
        published_at=published,
        url=url,
        format="Article",
        text=text,
    )
