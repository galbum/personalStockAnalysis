---
name: inst-ownership
description: Report and interpret institutional ownership (% of shares held by institutions) for a ticker, with peer comparison. Use when the user asks about institutional ownership, who owns the stock, fund/holder concentration, or how crowded a name is.
---

# Institutional Ownership

Share of a company held by institutions (funds, banks, insurers). Sourced from
the dashboard bundle field `inst_ownership` (yfinance `heldPercentInstitutions`,
already normalized to a percent in `dashboard/data_provider.py`).

## Quick start

```bash
cd <repo>/dashboard && source .venv/bin/activate
python ../.cursor/skills/inst-ownership/scripts/inst_ownership.py NVDA AMD AVGO
```

## How to read it

- **>= 70%** -> heavily institution-owned: high conviction, but crowded and
  sensitive to fund flows / rebalancing.
- **40-70%** -> balanced ownership.
- **< 40%** -> more retail / insider-held; can be less liquid and more volatile.
- Compare within peers; mega-caps usually sit high (70-85%).

## Discipline

- It's a snapshot; ownership changes each quarter (13F filings).
- Very high figures can mean limited float; pair with shares outstanding.
- If data is missing, report n/a - never estimate.

## Related: `fetch-stock-data`, `fundamental-analysis`, `stock-infographic`
