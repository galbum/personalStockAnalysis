---
name: dividend-yield
description: Report and interpret dividend yield for a ticker, with peer comparison and yield-trap caution. Use when the user asks about dividend yield, dividends, income, payout, or whether a stock pays a dividend.
---

# Dividend Yield

Annual dividend / price. Uses bundle field `dividend_yield` (TradingView /
yfinance, normalized to a percent in `dashboard/data_provider.py`).

## Quick start

```bash
cd <repo>/dashboard && source .venv/bin/activate
python ../.cursor/skills/dividend-yield/scripts/dividend_yield.py KO PG NVDA
```

## How to read it

- **0%** -> growth/reinvestment profile; return comes from price.
- **< 2%** low (growth-tilted), **2-4%** moderate (income + growth),
  **4-6%** high (income-oriented), **> 6%** very high -> check for a yield trap
  (a falling price inflating the yield, or an unsustainable payout).

## Discipline

- A high yield is only good if it's sustainable - pair with FCF / payout ratio.
- Yield moves inversely with price; a spike often means the stock dropped.
- Report n/a / 0 honestly for non-payers; never invent a yield.

## Related: `fetch-stock-data`, `fundamental-analysis`, `stock-infographic`
