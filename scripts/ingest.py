"""Batch ingest URLs listed in data/sources.yaml.

YAML structure:
  urls:
    - https://...
    - https://...
"""
from __future__ import annotations

from pathlib import Path

import yaml

from yw103.pipeline import ingest_url


def main() -> None:
    cfg_path = Path(__file__).resolve().parents[1] / "data" / "sources.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    urls = cfg.get("urls", [])
    for url in urls:
        try:
            page_id = ingest_url(url)
            print(f"OK  {url} -> {page_id}")
        except Exception as e:
            print(f"ERR {url}: {e}")


if __name__ == "__main__":
    main()
