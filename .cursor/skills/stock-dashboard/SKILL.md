---
name: stock-dashboard
description: Run and operate the local Streamlit stock-analysis dashboard that takes a ticker, pulls real fundamentals (yfinance), runs five-pillar fundamental research, generates head-to-head infographics, and caches results locally. Use when the user wants to start the dashboard, analyze a ticker in the app, compare tickers, or generate stock infographics through the dashboard.
---

# Stock Dashboard

Local Streamlit app in `dashboard/` with two modes:

- **Research (single ticker):** five-pillar fundamental analysis + Piotroski
  F-score & Altman Z-score + Claude thesis + a Claude Design deck prompt.
  Tabbed layout (Overview / Pillars / Thesis / Deck prompt) on a dark theme.
- **Infographic (compare):** head-to-head PNG infographic for 1-2 tickers.

The Overview surfaces FCF yield, Rule of 40, net debt/EBITDA, interest coverage,
revenue/FCF CAGR, and shareholder yield; the Cash Flow pillar shows SBC-adjusted
FCF (FCF ex-SBC) alongside raw FCF.

## Run

```bash
cd <repo>/dashboard
python3 -m venv .venv && source .venv/bin/activate   # first time only
pip install -r requirements.txt                       # first time only
streamlit run app.py
```

Open http://localhost:8501. Set the Anthropic API key in the sidebar (or in a
`.env` file) to enable the narrative, deck prompt, and competitor auto-pick.
Set `FMP_API_KEY` in `.env` for deep history (8-12 quarters + ~5 fiscal years);
without it the app falls back to yfinance (~5 quarters) and labels the depth.

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

## Caching & history

Durable store under `dashboard/cache/`:

- `tickers/<TICKER>/latest.json` — newest bundle + metadata (`first_seen`, `fetch_count`, `history_depth`)
- `tickers/<TICKER>/snapshots.jsonl` — append-only price/valuation snapshot per fetch
- `infographics/<KEY>.png` + `infographics/index.json` — images + registry (tickers, period, brand, regen count)
- `history/events.jsonl` — append-only log of research / infographic requests

Behavior:
- Re-requests reuse `latest.json` while younger than 24h; **Force refresh** bypasses it.
- **History-merging:** period-keyed series (quarters/annual) are merged on every
  save, so a later shallow fetch keeps deep history from an earlier FMP pull.
  Scalars (price, multiples, scores) always come from the newest fetch.
- Helpers: `cache.recent_tickers()`, `recent_searches()`, `recent_infographics()`,
  `infographics_for_ticker()`, `snapshot_history()`. The sidebar **History & saved**
  panel surfaces recent searches and saved infographics.
- Reads legacy `cache/data/<TICKER>.json` as a fallback.

## Components

| File | Role |
|------|------|
| `app.py` | Tabbed UI + orchestration (modes, caching, `st.status`, rendering) |
| `data_provider.py` | TradingView + yfinance fetch + metric extraction + scores |
| `fmp_provider.py` | Optional FMP deep history (graceful no-key fallback) |
| `tv_provider.py` | TradingView snapshot/valuation (no key) |
| `scores.py` | Piotroski F-score + Altman Z-score (pure functions) |
| `analysis.py` | five-pillar assembly + rule-based verdicts |
| `charts.py` | shared Plotly "equity" template (dark, last-point labels) |
| `llm.py` | Claude narrative + deck prompt (reads `skills/fundamental-analysis`) |
| `infographic.py`, `infographic_data.py` | spec assembly + matplotlib generator |
| `cache.py` | durable per-ticker store (history-merging) + infographic registry + search log |
| `.streamlit/config.toml` | dark theme |

## Related skills

- `fundamental-analysis` — the research engine (five pillars + deck prompt).
- `stock-infographic` — the standalone infographic generator.
