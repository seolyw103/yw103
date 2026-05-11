from __future__ import annotations

import datetime as dt
from urllib.parse import parse_qs, urlparse

from ..schema import RawContent


def _video_id(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host == "youtu.be":
        return parsed.path.lstrip("/")
    if parsed.path == "/watch":
        return parse_qs(parsed.query).get("v", [""])[0]
    if parsed.path.startswith("/shorts/"):
        return parsed.path.split("/")[2]
    if parsed.path.startswith("/embed/"):
        return parsed.path.split("/")[2]
    raise ValueError(f"Cannot parse YouTube video id from URL: {url}")


def _metadata(url: str) -> dict:
    from yt_dlp import YoutubeDL

    opts = {"quiet": True, "skip_download": True, "extract_flat": False}
    with YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def _transcript(video_id: str) -> str:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        NoTranscriptFound,
        TranscriptsDisabled,
    )

    try:
        listing = YouTubeTranscriptApi.list_transcripts(video_id)
    except TranscriptsDisabled:
        return ""

    for langs in (["ko"], ["en"], ["ko-KR"], ["en-US"]):
        try:
            t = listing.find_transcript(langs).fetch()
            return " ".join(seg["text"] for seg in t)
        except NoTranscriptFound:
            continue

    # Last resort: try any auto-generated transcript and translate to Korean.
    for tr in listing:
        if tr.is_generated:
            try:
                t = tr.translate("ko").fetch()
                return " ".join(seg["text"] for seg in t)
            except Exception:
                try:
                    return " ".join(seg["text"] for seg in tr.fetch())
                except Exception:
                    continue
    return ""


def extract(url: str) -> RawContent:
    vid = _video_id(url)
    meta = _metadata(url)

    text = _transcript(vid)
    if not text:
        # Fallback: description only. LLM will note that transcript was unavailable.
        text = meta.get("description") or ""

    upload_date = meta.get("upload_date")  # YYYYMMDD
    published = None
    if upload_date and len(upload_date) == 8:
        published = dt.date(int(upload_date[:4]), int(upload_date[4:6]), int(upload_date[6:8]))

    return RawContent(
        title=meta.get("title") or "(no title)",
        author=meta.get("uploader") or meta.get("channel") or "(unknown)",
        published_at=published,
        url=url,
        format="Video",
        text=text,
    )
