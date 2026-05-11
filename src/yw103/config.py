import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTION_IDS_PATH = REPO_ROOT / ".notion_ids.json"


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    anthropic_api_key: str | None
    anthropic_model: str
    openai_api_key: str | None
    openai_model: str
    notion_token: str | None
    notion_parent_page_id: str | None


def get_settings() -> Settings:
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "claude").lower(),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        notion_token=os.getenv("NOTION_TOKEN"),
        notion_parent_page_id=os.getenv("NOTION_PARENT_PAGE_ID"),
    )


def load_notion_ids() -> dict[str, str]:
    if not NOTION_IDS_PATH.exists():
        return {}
    return json.loads(NOTION_IDS_PATH.read_text())


def save_notion_ids(ids: dict[str, str]) -> None:
    NOTION_IDS_PATH.write_text(json.dumps(ids, indent=2, ensure_ascii=False))
