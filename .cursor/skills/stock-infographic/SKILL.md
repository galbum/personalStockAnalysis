---
name: stock-infographic
description: Generate a dark, branded head-to-head stock comparison infographic (PNG) for one or two tickers, with top stats and multi-quarter line charts (revenue growth, free cash flow, total debt, capex growth, stock performance, net profit margin). Use when the user asks to create a stock infographic, a head-to-head ticker comparison image, or a "$TICKER x $TICKER" visual.
---

# Stock Infographic

Generates a portrait PNG comparing 1-2 public companies, styled like a
head-to-head equity comparison: dark canvas, company-name header, a row of
single-value stats, and a 2x3 grid of multi-quarter line charts.

## Quick start

Run with the dashboard virtualenv (has matplotlib + yfinance):

```bash
cd <repo>/dashboard && source .venv/bin/activate
python ../.cursor/skills/stock-infographic/scripts/build_infographic.py ORCL MSFT \
  --out /tmp/orcl_msft.png --period "Q2'26"
```

- One ticker produces a single-company infographic; two produce a head-to-head.
- The image is written to `--out`.

## Fixed layout

- Top stats: Dividend Yield, Market Cap, Inst. Ownership.
- Panels: Revenue Growth, Free Cash Flow, Total Debt, Capital Expenditure Growth,
  Stock Performance, Net Profit Margin.
- First ticker renders red, second white (matches the reference style).

## Data and limits

Data comes from yfinance (free, no key). Free quarterly history is limited
(~5 quarters), so year-over-year growth panels may show few points. For deeper
history, wire a paid provider (e.g. Financial Modeling Prep) into
`dashboard/data_provider.py`.

## Implementation

- Generator: `dashboard/infographic.py` -> `build_infographic(spec, out_path)`
- Metric assembly: `dashboard/infographic_data.py` -> `build_spec(bundles)`
- This script is a thin CLI over them, so the dashboard and skill stay in sync.
