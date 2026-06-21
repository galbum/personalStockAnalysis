---
name: stock-dashboard
description: Run and operate the local Streamlit stock-analysis dashboard that takes a ticker, pulls real fundamentals (yfinance), runs five-pillar fundamental research, generates head-to-head infographics, and caches results locally. Use when the user wants to start the dashboard, analyze a ticker in the app, compare tickers, or generate stock infographics through the dashboard.
---

# Stock Dashboard

Local Streamlit app in `dashboard/` with two modes:

- **Research (single ticker):** five-pillar fundamental analysis + Claude thesis
  + a ready-to-paste Claude Design deck prompt.
- **Infographic (compare):** head-to-head PNG infographic for 1-2 tickers.

## Run

```bash
cd <repo>/dashboard
python3 -m venv .venv && source .venv/bin/activate   # first time only
pip install -r requirements.txt                       # first time only
streamlit run app.py
```

Open http://localhost:8501. Set the Anthropic API key in the sidebar (or in a
`.env` file) to enable the narrative, deck prompt, and competitor auto-pick.

## Pipeline stages (each has its own skill)

| Stage | Skill |
|-------|-------|
| 1. Fetch + cache data (TradingView snapshot + yfinance history) | `fetch-stock-data` |
| 2. Analyze (five pillars + thesis + deck prompt) | `fundamental-analysis` |
| 3. Build infographic | `stock-infographic` |

This skill orchestrates those stages in the UI.

## Flow

```
ticker -> [fetch-stock-data] cache check (24h) + TradingView/yfinance
       -> [fundamental-analysis] five-pillar research (optional)
       -> [stock-infographic] head-to-head image (optional)
       -> cache results
```

## Caching

- `dashboard/cache/data/<TICKER>.json` — metrics + `fetched_at`
- `dashboard/cache/infographics/<KEY>.png` — generated images

Re-requests reuse the cache when younger than 24h. Use the **Force refresh**
checkbox to bypass it and re-fetch.

## Components

| File | Role |
|------|------|
| `app.py` | UI + orchestration (modes, caching, rendering) |
| `data_provider.py` | yfinance fetch + metric extraction |
| `analysis.py` | five-pillar assembly + rule-based verdicts |
| `llm.py` | Claude narrative + deck prompt (reads `skills/fundamental-analysis`) |
| `infographic.py`, `infographic_data.py` | spec assembly + matplotlib generator |
| `cache.py` | local JSON/PNG cache |

## Related skills

- `fundamental-analysis` — the research engine (five pillars + deck prompt).
- `stock-infographic` — the standalone infographic generator.
