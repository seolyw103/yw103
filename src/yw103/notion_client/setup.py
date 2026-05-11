"""Idempotent Notion database setup under the parent "economic" page.

Creates three linked databases: Sources, Analyses, Scenarios.
Caches generated IDs in `.notion_ids.json` at repo root.
"""
from __future__ import annotations

from typing import Any

from ..config import get_settings, load_notion_ids, save_notion_ids
from ..schema import AssetClass, Confidence, Outlook, Region, SourceType, TimeHorizon
from .client import get_client


def _select_opts(values) -> list[dict]:
    return [{"name": v.value if hasattr(v, "value") else v} for v in values]


def _find_existing_db(parent_page_id: str, title: str) -> str | None:
    """Walk children of parent page, return database id whose title matches."""
    notion = get_client()
    cursor = None
    while True:
        resp = notion.blocks.children.list(block_id=parent_page_id, start_cursor=cursor) \
            if cursor else notion.blocks.children.list(block_id=parent_page_id)
        for block in resp.get("results", []):
            if block.get("type") == "child_database":
                if block["child_database"]["title"] == title:
                    return block["id"]
        if not resp.get("has_more"):
            return None
        cursor = resp.get("next_cursor")


def _create_db(parent_page_id: str, title: str, properties: dict[str, Any]) -> str:
    notion = get_client()
    resp = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": title}}],
        properties=properties,
    )
    return resp["id"]


def _sources_props() -> dict[str, Any]:
    return {
        "Name": {"title": {}},
        "Type": {"select": {"options": _select_opts(SourceType)}},
        "Region": {"select": {"options": _select_opts(Region)}},
        "Channel URL": {"url": {}},
        "Influence": {"number": {"format": "number"}},
        "Notes": {"rich_text": {}},
    }


def _analyses_props(sources_db_id: str) -> dict[str, Any]:
    return {
        "Title": {"title": {}},
        "Source": {"relation": {"database_id": sources_db_id, "single_property": {}}},
        "Date": {"date": {}},
        "Format": {"select": {"options": _select_opts(
            ["Video", "Speech", "Report", "Article", "Podcast"]
        )}},
        "Link": {"url": {}},
        "Asset Classes": {"multi_select": {"options": _select_opts(AssetClass)}},
        "Time Horizon": {"multi_select": {"options": _select_opts(TimeHorizon)}},
        "Overall Outlook": {"select": {"options": _select_opts(Outlook)}},
        "Region": {"select": {"options": _select_opts(Region)}},
        "Macro Conditions": {"multi_select": {"options": []}},  # free-form
        "Key Thesis": {"rich_text": {}},
        "Time-period View": {"rich_text": {}},
        "Asset Recommendations": {"rich_text": {}},
        "Confidence": {"select": {"options": _select_opts(Confidence)}},
        "Transcript": {"url": {}},
    }


def _scenarios_props(analyses_db_id: str) -> dict[str, Any]:
    outlook_opts = {"select": {"options": _select_opts(Outlook)}}
    return {
        "Scenario": {"title": {}},
        "Trigger": {"multi_select": {"options": []}},  # free-form
        "Probability %": {"number": {"format": "percent"}},
        "주식": outlook_opts,
        "채권": outlook_opts,
        "원자재": outlook_opts,
        "부동산": outlook_opts,
        "암호화폐": outlook_opts,
        "Time Horizon": {"multi_select": {"options": _select_opts(TimeHorizon)}},
        "Supporting Analyses": {
            "relation": {"database_id": analyses_db_id, "single_property": {}}
        },
        "Notes": {"rich_text": {}},
    }


def setup_databases() -> dict[str, str]:
    settings = get_settings()
    if not settings.notion_parent_page_id:
        raise RuntimeError("NOTION_PARENT_PAGE_ID is not set")
    parent = settings.notion_parent_page_id

    ids = load_notion_ids()

    if "sources_db" not in ids:
        found = _find_existing_db(parent, "Sources")
        ids["sources_db"] = found or _create_db(parent, "Sources", _sources_props())

    if "analyses_db" not in ids:
        found = _find_existing_db(parent, "Analyses")
        ids["analyses_db"] = found or _create_db(
            parent, "Analyses", _analyses_props(ids["sources_db"])
        )

    if "scenarios_db" not in ids:
        found = _find_existing_db(parent, "Scenarios")
        ids["scenarios_db"] = found or _create_db(
            parent, "Scenarios", _scenarios_props(ids["analyses_db"])
        )

    save_notion_ids(ids)

    return ids


VIEWS_MARKER = "📑 분석 뷰 (Group by 설정 안내)"

VIEW_SPECS = [
    ("📊 자산군별 컨센서스", "Asset Classes", "주식·채권·원자재 등 자산군별로 그룹핑"),
    ("⏱ 기간별 전망", "Time Horizon", "단기·중기·장기로 그룹핑"),
    ("🌍 지역별 전망", "Region", "US·EU·KR·China·Global로 그룹핑"),
    ("📈 강세 vs 약세", "Overall Outlook", "강세·중립·약세로 그룹핑"),
]


def _has_views_marker(parent_page_id: str) -> bool:
    notion = get_client()
    cursor = None
    while True:
        resp = (
            notion.blocks.children.list(block_id=parent_page_id, start_cursor=cursor)
            if cursor
            else notion.blocks.children.list(block_id=parent_page_id)
        )
        for block in resp.get("results", []):
            if block.get("type") == "heading_1":
                rt = block["heading_1"].get("rich_text", [])
                text = "".join(seg.get("plain_text", "") for seg in rt)
                if VIEWS_MARKER in text:
                    return True
        if not resp.get("has_more"):
            return False
        cursor = resp.get("next_cursor")


def setup_views(parent_page_id: str, analyses_db_id: str) -> None:
    """Scaffold a 'Views' section on the parent page.

    Notion's API can't preconfigure filter/sort/group on linked database views,
    so this only lays down a heading + link_to_database + instruction per view.
    The user opens each linked DB and applies the suggested grouping (~5s/view).
    Idempotent: skips if the section heading already exists.
    """
    if _has_views_marker(parent_page_id):
        return

    children: list[dict] = [
        {"object": "block", "type": "divider", "divider": {}},
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {"rich_text": [{"type": "text", "text": {"content": VIEWS_MARKER}}]},
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": (
                                "아래 각 링크는 Analyses DB를 가리킵니다. 처음 열어서 "
                                "View 옵션 → Group by → 추천 필드를 한 번만 설정하면 끝."
                            )
                        },
                    }
                ]
            },
        },
    ]
    for title, group_by, desc in VIEW_SPECS:
        children.extend(
            [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"{title}  —  Group by: {group_by}"
                                },
                            }
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": desc}}
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "link_to_page",
                    "link_to_page": {
                        "type": "database_id",
                        "database_id": analyses_db_id,
                    },
                },
            ]
        )

    get_client().blocks.children.append(block_id=parent_page_id, children=children)
