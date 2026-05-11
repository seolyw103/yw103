from __future__ import annotations

import io

import httpx

from ..schema import RawContent


def extract(url: str) -> RawContent:
    from pypdf import PdfReader

    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()

    reader = PdfReader(io.BytesIO(resp.content))
    text_parts = []
    for page in reader.pages:
        try:
            text_parts.append(page.extract_text() or "")
        except Exception:
            continue
    text = "\n".join(text_parts).strip()

    info = reader.metadata or {}
    title = (info.title if info else None) or url.rsplit("/", 1)[-1]
    author = (info.author if info else None) or "(unknown)"

    return RawContent(
        title=title,
        author=author,
        published_at=None,
        url=url,
        format="Report",
        text=text,
    )
