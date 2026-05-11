from __future__ import annotations

from typing import Any

from ..config import load_notion_ids
from ..schema import AnalysisRecord, RawContent, Scenario
from .client import get_client

NOTION_TEXT_LIMIT = 1900  # safety margin under 2000


def _rt(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"rich_text": []}
    # Notion caps each rich_text segment at 2000 chars; split if needed.
    chunks = [text[i : i + NOTION_TEXT_LIMIT] for i in range(0, len(text), NOTION_TEXT_LIMIT)]
    return {"rich_text": [{"type": "text", "text": {"content": c}} for c in chunks]}


def _title(text: str) -> dict:
    text = (text or "").strip()[:NOTION_TEXT_LIMIT]
    return {"title": [{"type": "text", "text": {"content": text}}]}


def _select(value) -> dict | None:
    if value is None:
        return None
    name = value.value if hasattr(value, "value") else str(value)
    return {"select": {"name": name}}


def _multi(values) -> dict:
    out = []
    for v in values or []:
        name = v.value if hasattr(v, "value") else str(v)
        out.append({"name": name})
    return {"multi_select": out}


def _date(value) -> dict | None:
    if not value:
        return None
    return {"date": {"start": value.isoformat() if hasattr(value, "isoformat") else str(value)}}


def _rel(page_ids: list[str]) -> dict:
    return {"relation": [{"id": pid} for pid in page_ids]}


def _query_db(database_id: str, *, filter_: dict | None = None) -> list[dict]:
    notion = get_client()
    results: list[dict] = []
    cursor: str | None = None
    while True:
        body: dict[str, Any] = {"database_id": database_id}
        if filter_:
            body["filter"] = filter_
        if cursor:
            body["start_cursor"] = cursor
        resp = notion.databases.query(**body)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            return results
        cursor = resp.get("next_cursor")


def upsert_source(
    name: str,
    *,
    type_: str | None = None,
    region: str | None = None,
    channel_url: str | None = None,
    influence: int | None = None,
    notes: str | None = None,
) -> str:
    """Find a Sources row by Name; create if missing. Return page id."""
    ids = load_notion_ids()
    db_id = ids["sources_db"]

    matches = _query_db(
        db_id,
        filter_={"property": "Name", "title": {"equals": name}},
    )
    if matches:
        return matches[0]["id"]

    props: dict[str, Any] = {"Name": _title(name)}
    if type_:
        props["Type"] = {"select": {"name": type_}}
    if region:
        props["Region"] = {"select": {"name": region}}
    if channel_url:
        props["Channel URL"] = {"url": channel_url}
    if influence is not None:
        props["Influence"] = {"number": influence}
    if notes:
        props["Notes"] = _rt(notes)

    page = get_client().pages.create(parent={"database_id": db_id}, properties=props)
    return page["id"]


def _format_time_period_view(record: AnalysisRecord) -> str:
    v = record.time_period_view
    parts: list[str] = []
    if v.short:
        parts.append(f"[단기 0–6M] {v.short}")
    if v.mid:
        parts.append(f"[중기 6–24M] {v.mid}")
    if v.long:
        parts.append(f"[장기 2Y+] {v.long}")
    return "\n\n".join(parts)


def _scenarios_block_children(record: AnalysisRecord) -> list[dict]:
    """Render scenarios as bullet/heading blocks under the analysis page body."""
    children: list[dict] = []
    if not record.scenarios:
        return children
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "시나리오"}}]},
    })
    for s in record.scenarios:
        triggers = " · ".join(s.triggers) if s.triggers else ""
        prob = f" (확률 {s.probability_pct:.0f}%)" if s.probability_pct is not None else ""
        header = f"{s.name}{prob}"
        if triggers:
            header += f"  — Trigger: {triggers}"
        children.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": header}}]},
        })
        for r in s.asset_reactions:
            line = f"{r.asset.value}: {r.direction.value}"
            if r.rationale:
                line += f" — {r.rationale}"
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                },
            })
        if s.notes:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": s.notes}}]},
            })
    return children


def write_analysis(record: AnalysisRecord, source_page_id: str, raw: RawContent | None = None) -> str:
    ids = load_notion_ids()
    db_id = ids["analyses_db"]

    props: dict[str, Any] = {
        "Title": _title(record.title),
        "Source": _rel([source_page_id]),
        "Format": {"select": {"name": record.format}},
        "URL": {"url": record.url},
        "Asset Classes": _multi(record.asset_classes),
        "Time Horizon": _multi(record.time_horizons),
        "Overall Outlook": _select(record.overall_outlook),
        "Macro Conditions": _multi(record.macro_conditions),
        "Key Thesis": _rt(record.key_thesis),
        "Time-period View": _rt(_format_time_period_view(record)),
        "Asset Recommendations": _rt(record.asset_recommendations),
        "Confidence": _select(record.confidence),
    }
    if record.published_at:
        props["Date"] = _date(record.published_at)
    # Drop None values
    props = {k: v for k, v in props.items() if v is not None}

    children = _scenarios_block_children(record)

    page = get_client().pages.create(
        parent={"database_id": db_id},
        properties=props,
        children=children,
    )
    return page["id"]


def _outlook_for_asset(scenario: Scenario, asset_name: str) -> dict | None:
    for r in scenario.asset_reactions:
        if r.asset.value == asset_name:
            return {"select": {"name": r.direction.value}}
    return None


def upsert_scenario(scenario: Scenario, analysis_page_id: str) -> str:
    """Append the analysis as a supporting source for a scenario, creating the row if absent."""
    ids = load_notion_ids()
    db_id = ids["scenarios_db"]

    matches = _query_db(
        db_id,
        filter_={"property": "Scenario", "title": {"equals": scenario.name}},
    )

    if matches:
        page = matches[0]
        existing = [r["id"] for r in page["properties"]["Supporting Analyses"]["relation"]]
        if analysis_page_id not in existing:
            existing.append(analysis_page_id)
            get_client().pages.update(
                page_id=page["id"],
                properties={"Supporting Analyses": _rel(existing)},
            )
        return page["id"]

    props: dict[str, Any] = {
        "Scenario": _title(scenario.name),
        "Trigger": _multi(scenario.triggers),
        "Time Horizon": _multi(scenario.horizon),
        "Supporting Analyses": _rel([analysis_page_id]),
        "Notes": _rt(scenario.notes),
    }
    if scenario.probability_pct is not None:
        props["Probability %"] = {"number": scenario.probability_pct / 100.0}
    for asset_name in ("주식", "채권", "원자재", "부동산", "암호화폐"):
        v = _outlook_for_asset(scenario, asset_name)
        if v:
            props[asset_name] = v

    page = get_client().pages.create(parent={"database_id": db_id}, properties=props)
    return page["id"]
