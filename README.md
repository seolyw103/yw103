# yw103 — 글로벌 경제 시장 분석 수집·정리 시스템

Fed/IMF/세계은행 같은 공식기관, Ray Dalio·Howard Marks 등 유명 투자자, 김단테·슈카월드 같은 유튜브 채널의
경제 시장 분석을 자동 수집·요약해서 Notion에 누적합니다.

세 가지 분석 축으로 구조화합니다:

- **자산군별 전망** — 주식/채권/원자재/부동산/암호화폐/외환/현금
- **기간별 전망** — 단기(0–6M) / 중기(6–24M) / 장기(2Y+)
- **거시지표 조건별 시나리오** — IF 금리/CPI/실업률 조건 → THEN 시장 반응

## 빠른 시작

```bash
pip install -e .
cp .env.example .env  # 키 채우기

# 1) Notion에 DB 3종(Sources/Analyses/Scenarios) 생성
python -m scripts.setup_notion

# 2) 샘플 권위자 3~5건 시드
python -m scripts.seed

# 3) 새 자료 추가 (유튜브, RSS 피드 항목, PDF URL, 일반 웹페이지 지원)
python -m scripts.add https://www.youtube.com/watch?v=...
```

## 환경변수

| 변수 | 설명 |
|---|---|
| `LLM_PROVIDER` | `claude` (기본) 또는 `openai` |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | Claude 사용 시 (기본 모델: `claude-sonnet-4-6`) |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | OpenAI 사용 시 (기본 모델: `gpt-4o`) |
| `NOTION_TOKEN` | Notion integration 토큰 |
| `NOTION_PARENT_PAGE_ID` | 기존 "경제 분석" 페이지 ID |

## 구조

```
src/yw103/
  schema.py            # AnalysisRecord, Scenario (Pydantic)
  prompts.py           # 한국어 분석 프롬프트
  config.py            # 환경변수 로딩
  llm/                 # Claude / OpenAI 어댑터
  sources/             # youtube, rss, pdf, web 추출기
  notion_client/       # DB 생성 + writer
  pipeline.py          # extract → analyze → write
scripts/
  setup_notion.py      # 1회 DB 생성
  add.py               # CLI 단건 추가
  ingest.py            # data/sources.yaml 일괄 처리
  seed.py              # 샘플 권위자 3~5건 주입
```
