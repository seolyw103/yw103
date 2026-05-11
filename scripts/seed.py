"""Seed 3~5 hand-curated authority samples into the Notion DBs.

Reads data/seed_analyses.yaml directly (no LLM call, no network extraction)
so this works even before API keys for the LLM provider are configured.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from yw103.pipeline import write_record
from yw103.schema import AnalysisRecord


def main() -> None:
    cfg_path = Path(__file__).resolve().parents[1] / "data" / "seed_analyses.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    for entry in cfg.get("analyses", []):
        record = AnalysisRecord.model_validate(entry)
        page_id = write_record(record, raw=None)
        print(f"OK  {record.speaker} — {record.title} -> {page_id}")


if __name__ == "__main__":
    main()
