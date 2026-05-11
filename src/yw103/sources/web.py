from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup
from readability import Document

from ..schema import RawContent


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def extract(url: str) -> RawContent:
    resp = httpx.get(
        url,
        follow_redirects=True,
        timeout=30.0,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "ko,en;q=0.8"},
    )
    resp.raise_for_status()

    doc = Document(resp.text)
    title = (doc.short_title() or "").strip()
    summary_html = doc.summary(html_partial=True)

    soup = BeautifulSoup(summary_html, "lxml")
    text = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n").strip())

    # Author best-effort: meta tags
    meta_soup = BeautifulSoup(resp.text, "lxml")
    author = ""
    for sel in [
        ('meta', {"name": "author"}),
        ('meta', {"property": "article:author"}),
        ('meta', {"name": "twitter:creator"}),
    ]:
        tag = meta_soup.find(*sel)
        if tag and tag.get("content"):
            author = tag["content"].strip()
            break
    if not author:
        og_site = meta_soup.find("meta", {"property": "og:site_name"})
        author = (og_site.get("content").strip() if og_site and og_site.get("content") else "(unknown)")

    return RawContent(
        title=title or url,
        author=author,
        published_at=None,
        url=url,
        format="Article",
        text=text,
    )
