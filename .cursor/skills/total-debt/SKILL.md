---
name: total-debt
description: Report and interpret total debt and leverage (debt-to-equity, net cash) for a ticker, including a multi-year debt trend. Use when the user asks about total debt, leverage, balance-sheet health, net cash/net debt, or how indebted a company is.
---

# Total Debt & Leverage

Balance-sheet leverage read. Uses bundle fields `total_debt` (latest),
`net_cash`, `debt_to_equity`, plus the `total_debt_annual` /
`total_debt_series` history for the trend (`dashboard/data_provider.py`).

## Quick start

```bash
cd <repo>/dashboard && source .venv/bin/activate
python ../.cursor/skills/total-debt/scripts/total_debt.py AAPL ORCL MSFT
```

## How to read it

- **Net cash positive** (cash > debt) -> very strong balance sheet.
- **Debt-to-equity:** < 0.5 conservative, 0.5-1 moderate, 1-2 elevated, > 2 high.
- **Trend:** debt rising fast can fund growth (capex/buybacks) or signal stress -
  read alongside FCF and interest coverage.

## Discipline

- D/E varies hugely by sector (utilities/banks run high by design); compare to peers.
- Gross total debt ignores cash - always pair with net cash / net debt.
- Report n/a rather than guessing when a field is missing.

## Related: `fetch-stock-data`, `fundamental-analysis`, `stock-infographic`
