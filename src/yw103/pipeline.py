from __future__ import annotations

from . import sources
from .llm import analyze
from .notion_client import upsert_scenario, upsert_source, write_analysis
from .schema import AnalysisRecord, RawContent


def ingest_url(url: str) -> str:
    """Full pipeline: extract → analyze → write to Notion. Returns analysis page id."""
    raw = sources.extract(url)
    record = analyze(raw)
    return write_record(record, raw)


def write_record(record: AnalysisRecord, raw: RawContent | None = None) -> str:
    source_page_id = upsert_source(
        name=record.speaker,
        type_=record.speaker_type.value,
        region=record.region.value,
        channel_url=raw.url if raw else None,
    )
    analysis_page_id = write_analysis(record, source_page_id, raw)
    for scenario in record.scenarios:
        upsert_scenario(scenario, analysis_page_id)
    return analysis_page_id
