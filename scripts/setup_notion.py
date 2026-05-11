"""Create three databases (Sources/Analyses/Scenarios) under the parent
"economic" page. Idempotent — re-running detects existing DBs by title.
"""
from __future__ import annotations

from yw103.notion_client import setup_databases


def main() -> None:
    ids = setup_databases()
    print("Notion DBs ready:")
    for key, value in ids.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
