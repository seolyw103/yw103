"""Poll RSS feeds + Twitter handles listed in data/sources.yaml; ingest only NEW items.

State is persisted in .feed_state.json so subsequent runs only process new items.
Designed for cron / scheduled execution.

YAML structure expected:
  feeds:
    - name: <label>
      url: <rss_url>
  twitter_handles:
    - name: <author>
      handle: <handle without @>
      rss: <optional RSS bridge URL like nitter>
"""
from __future__ import annotations

from pathlib import Path

import yaml

from yw103.pipeline import ingest_url
from yw103.sources.rss import poll_new


def main() -> None:
    cfg_path = Path(__file__).resolve().parents[1] / "data" / "sources.yaml"
    cfg = yaml.safe_load(cfg_path.read_text()) or {}

    feed_specs: list[dict] = cfg.get("feeds", []) or []
    twitter_specs: list[dict] = cfg.get("twitter_handles", []) or []

    ok = err = 0

    for spec in feed_specs:
        name = spec.get("name", spec.get("url", "?"))
        url = spec.get("url")
        if not url:
            continue
        try:
            new_items = poll_new(url)
            print(f"[FEED] {name}: {len(new_items)} new")
            for item in new_items:
                if not item.link:
                    continue
                try:
                    page_id = ingest_url(item.link)
                    print(f"  OK  {item.link} -> {page_id}")
                    ok += 1
                except Exception as e:
                    print(f"  ERR {item.link}: {e}")
                    err += 1
        except Exception as e:
            print(f"[FEED] {name} poll failed: {e}")
            err += 1

    for spec in twitter_specs:
        rss_bridge = spec.get("rss")
        if not rss_bridge:
            continue
        name = spec.get("name", spec.get("handle", "?"))
        try:
            new_items = poll_new(rss_bridge)
            print(f"[TWITTER] @{spec.get('handle')}: {len(new_items)} new")
            for item in new_items:
                if not item.link:
                    continue
                try:
                    page_id = ingest_url(item.link)
                    print(f"  OK  {item.link} -> {page_id}")
                    ok += 1
                except Exception as e:
                    print(f"  ERR {item.link}: {e}")
                    err += 1
        except Exception as e:
            print(f"[TWITTER] {name} poll failed: {e}")
            err += 1

    print(f"\nDone. {ok} ingested, {err} errors.")


if __name__ == "__main__":
    main()
