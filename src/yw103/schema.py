from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class AssetClass(str, Enum):
    EQUITY = "주식"
    BOND = "채권"
    COMMODITY = "원자재"
    REAL_ESTATE = "부동산"
    CRYPTO = "암호화폐"
    FX = "외환"
    CASH = "현금"


class TimeHorizon(str, Enum):
    SHORT = "단기"
    MID = "중기"
    LONG = "장기"


class Outlook(str, Enum):
    BULL = "강세"
    NEUTRAL = "중립"
    BEAR = "약세"


class Confidence(str, Enum):
    HIGH = "높음"
    MID = "중간"
    LOW = "낮음"


class SourceType(str, Enum):
    OFFICIAL = "공식기관"
    INVESTOR = "투자자"
    ECONOMIST = "이코노미스트"
    YOUTUBE = "유튜브채널"
    RESEARCH = "리서치하우스"


class Region(str, Enum):
    US = "US"
    EU = "EU"
    KR = "KR"
    CN = "China"
    GLOBAL = "Global"


class TimePeriodView(BaseModel):
    short: str = Field(default="", description="단기(0-6M) 전망 한 문단. 발화자가 언급 안했으면 빈 문자열.")
    mid: str = Field(default="", description="중기(6-24M) 전망 한 문단.")
    long: str = Field(default="", description="장기(2Y+) 전망 한 문단.")


class AssetReaction(BaseModel):
    asset: AssetClass
    direction: Outlook
    rationale: str = Field(default="", description="이 시나리오에서 해당 자산이 그렇게 움직이는 이유 한 줄.")


class Scenario(BaseModel):
    name: str = Field(description='예: "Fed 2026Q3 피벗", "미국 침체 진입"')
    triggers: list[str] = Field(default_factory=list, description="이 시나리오를 촉발하는 거시지표·이벤트")
    probability_pct: float | None = Field(default=None, description="발화자가 명시한 확률(%). 없으면 null.")
    horizon: list[TimeHorizon] = Field(default_factory=list)
    asset_reactions: list[AssetReaction] = Field(default_factory=list)
    notes: str = ""


class AnalysisRecord(BaseModel):
    """LLM이 자료를 읽고 채우는 구조화 출력. Notion Analyses DB와 1:1 매핑."""

    title: str = Field(description="자료 제목. 원본 제목을 정리해서 한 줄.")
    speaker: str = Field(description="발화자/저자. 'Jerome Powell', 'IMF', '슈카' 등.")
    speaker_type: SourceType
    region: Region
    published_at: date | None = None
    format: Literal["Video", "Speech", "Report", "Article", "Podcast"]
    url: str

    asset_classes: list[AssetClass] = Field(default_factory=list)
    time_horizons: list[TimeHorizon] = Field(default_factory=list)
    overall_outlook: Outlook
    macro_conditions: list[str] = Field(
        default_factory=list,
        description='예: ["인플레이션 상승", "금리 인상", "연착륙", "달러 강세"]. 자유 텍스트.',
    )

    key_thesis: str = Field(description="핵심 주장 3-5줄.")
    time_period_view: TimePeriodView = Field(default_factory=TimePeriodView)
    asset_recommendations: str = Field(
        default="",
        description="자산군별 권고를 한 블록 텍스트로. 발화자가 명시한 것만.",
    )
    scenarios: list[Scenario] = Field(default_factory=list)
    confidence: Confidence = Confidence.MID


class RawContent(BaseModel):
    """source extractor 출력. LLM 입력으로 들어감."""

    title: str
    author: str
    published_at: date | None = None
    url: str
    format: Literal["Video", "Speech", "Report", "Article", "Podcast"]
    text: str
