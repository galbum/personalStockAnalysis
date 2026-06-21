---
name: net-margin
description: Report and interpret net profit margin for a ticker, with a multi-year (annual) expanding/compressing trend and peer comparison. Use when the user asks about net margin, net profit margin, profitability, or whether margins are improving.
---

# Net Profit Margin

Net income / revenue. Uses bundle field `net_margin` (quarterly series, latest
value) and `net_margin_annual` for the multi-year trend
(`dashboard/data_provider.py`).

## Quick start

```bash
cd <repo>/dashboard && source .venv/bin/activate
python ../.cursor/skills/net-margin/scripts/net_margin.py NVDA AMD INTC
```

## How to read it

- **>= 20%** high, **10-20%** healthy, **0-10%** thin, **< 0%** loss-making.
- **Trend matters most:** expanding margins (annual) signal pricing power /
  operating leverage; compressing margins signal cost or competitive pressure.
- Compare within sector - software runs far higher than retail/hardware.

## Discipline

- Net margin includes one-offs (taxes, write-offs); cross-check with operating
  margin for the core trend.
- Report n/a when earnings are missing; never fabricate.

## Related: `fetch-stock-data`, `fundamental-analysis`, `stock-infographic`
