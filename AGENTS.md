# AGENTS.md — yw103

Handbook for any coding agent (Cursor Cloud, Devin, Claude Code, Copilot coding agent, Codex) working in this repository.

## What this project does
Collects authoritative economic-market analyses (Fed/IMF/World Bank, Ray Dalio, Howard Marks, KR YouTube channels like 김단테/슈카월드) and writes structured records to Notion across three axes:

1. 자산군별 전망 — equities / bonds / commodities / real estate / crypto / FX / cash
2. 기간별 전망 — short (0–6M) / mid (6–24M) / long (2Y+)
3. 거시지표 시나리오 — IF (rates/CPI/unemployment) → THEN market reaction

Korean prompts and Korean output are intentional.

## Setup
```bash
pip install -e .
cp .env.example .env  # fill in keys
```

Required env vars are documented in `README.md` and `.env.example`. At minimum: `LLM_PROVIDER`, the matching API key, `NOTION_TOKEN`, `NOTION_PARENT_PAGE_ID`.

## How the code is organized
```
src/yw103/
  schema.py            # AnalysisRecord, Scenario (Pydantic v2)
  prompts.py           # Korean analysis prompts — do not translate
  config.py            # env loading
  llm/                 # Claude / OpenAI adapters
  sources/             # youtube, twitter, rss, pdf, web extractors
  notion_client/       # DB creation + writer
  pipeline.py          # extract → analyze → write
scripts/
  setup_notion.py      # one-time DB creation
  add.py               # CLI single-URL ingest
  ingest.py            # batch from data/sources.yaml
  poll_feeds.py        # RSS poller, new-items-only
  seed.py              # sample authority seeding
```

## Working in parallel (multi-agent)
- Each agent works on its own branch named `agent/<slug>`.
- One branch = one PR = one logical change.
- See `.cursor/rules/worktree.mdc` for the full worktree convention.
- Don't touch another agent's branch.

## Verify before declaring done
- `pip install -e .` succeeds in your worktree.
- Modified scripts import cleanly: `python -c "import scripts.<name>"`.
- If schema changed, `setup_notion.py` is updated to match.
- Korean prompts/outputs are preserved verbatim.

## Don't
- Don't add paid third-party services (vector DBs, hosted scrapers, etc.) without being asked.
- Don't replace `httpx` with `requests`.
- Don't make the RSS poller re-emit already-seen entries.
- Don't translate Korean prompts to English.
- Don't add comments that just restate what the code does.

## Tablet workflow note
This repo is configured for multi-agent cloud workflows so the maintainer can dispatch work from a tablet. Keep PRs small and self-describing — the reviewer may be reading on a 10-inch screen.
