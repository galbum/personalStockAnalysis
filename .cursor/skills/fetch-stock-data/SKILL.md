---
name: fetch-stock-data
description: Fetch and cache a stock ticker's data for the dashboard pipeline - current snapshot + valuation from TradingView and 8-quarter history from yfinance, cached locally for 24h. Use when you need to pull, refresh, or inspect raw data for a ticker, or as the data-acquisition stage before analysis or an infographic.
---

# Fetch Stock Data (data stage)

First stage of the dashboard pipeline: get a ticker's data and cache it.

- **Snapshot + valuation:** TradingView (`dashboard/tv_provider.py`, no key).
- **Quarterly series + price history:** yfinance (`dashboard/data_provider.py`).
- **Annual series (a few fiscal years):** yfinance, so YoY growth is easy to see -
  `annual_labels`, `revenue_annual`, `rev_yoy_annual`, `net_margin_annual`,
  `fcf_annual`, `capex_growth_annual`, `total_debt_annual`. Use annual (YoY) for
  growth panels and quarterly (QoQ) for level panels.
- **Cache:** durable per-ticker store `dashboard/cache/tickers/<TICKER>/latest.json`
  (reused for 24h, long-lived series history-merged across fetches) via `dashboard/cache.py`.

## Quick start

Run with the dashboard virtualenv:

```bash
cd <repo>/dashboard && source .venv/bin/activate
python ../.cursor/skills/fetch-stock-data/scripts/fetch_stock_data.py AAPL
python ../.cursor/skills/fetch-stock-data/scripts/fetch_stock_data.py AAPL --force --json
```

- `--force` ignores the 24h cache and re-fetches.
- `--json` prints the full data bundle.

## Behavior

- Returns one JSON-serializable bundle (snapshot + series + price performance).
- TradingView is primary for current values; yfinance fills history and any gaps.
- Robust: TradingView failure falls back to yfinance; missing fields are null,
  never fabricated.

## Next stages

- Analyze: `fundamental-analysis`
- Infographic: `stock-infographic`
- Orchestration: `stock-dashboard`
