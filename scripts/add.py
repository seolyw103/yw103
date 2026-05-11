"""CLI: ingest a single URL (YouTube/PDF/article) into Notion."""
from __future__ import annotations

import sys

from yw103.pipeline import ingest_url


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.add <URL>", file=sys.stderr)
        sys.exit(2)

    url = sys.argv[1]
    page_id = ingest_url(url)
    notion_url = f"https://www.notion.so/{page_id.replace('-', '')}"
    print(f"Created Notion page: {notion_url}")


if __name__ == "__main__":
    main()
