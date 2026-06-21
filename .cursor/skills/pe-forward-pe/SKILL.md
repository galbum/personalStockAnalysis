---
name: pe-forward-pe
description: Report and interpret trailing P/E and forward P/E for a ticker (plus PEG and the implied earnings-growth signal). Use when the user asks about P/E, forward P/E, earnings multiples, whether a stock is cheap/expensive vs its growth, or wants a quick valuation read across peers.
---

# P/E and Forward P/E

Valuation read built on the dashboard data bundle. Reports trailing P/E,
forward P/E, PEG, and what the trailing-vs-forward gap implies about expected
earnings.

## Where the numbers come from

- **Trailing P/E (`pe`):** price / trailing-12-month EPS. Sourced from
  TradingView (`price_earnings_ttm`), falls back to yfinance `trailingPE`.
- **Forward P/E (`forward_pe`):** price / consensus next-12-month EPS estimate.
  Sourced from yfinance `forwardPE` (TradingView does not expose a usable
  forward multiple here).
- **PEG (`peg`):** P/E divided by expected EPS growth.

All three already live in the bundle from `dashboard/data_provider.py`, so no
new fetch is needed.

## Quick start

Run with the dashboard virtualenv:

```bash
cd <repo>/dashboard && source .venv/bin/activate
python ../.cursor/skills/pe-forward-pe/scripts/pe_forward_pe.py NVDA
python ../.cursor/skills/pe-forward-pe/scripts/pe_forward_pe.py NVDA AMD AVGO
```

Output: a table of P/E, forward P/E, PEG, and the implied EPS-growth signal,
then a one-line interpretation per ticker.

## How to read it

- **Forward P/E < trailing P/E** -> the market expects EPS to *grow*; the
  multiple compresses on higher next-year earnings (common for growth names).
- **Forward P/E > trailing P/E** -> the market expects EPS to *fall*.
- **Implied EPS growth** = trailing/forward - 1. A rough read of the earnings
  growth baked into the gap.
- **PEG** < 1 = cheap vs growth, ~1-2 = fair, > 2 = expensive vs growth.
- **Trailing P/E is n/a** (negative TTM earnings) but forward P/E exists ->
  the company is expected to turn profitable; lean on forward P/E and PEG.

## Discipline

- Compare P/E only within the same sector/industry; absolute levels mean little
  across sectors.
- Forward P/E depends on analyst estimates and can be stale or optimistic - treat
  it as a signal, not truth.
- Never fabricate a multiple; if EPS is negative or data is missing, report n/a.

## Related stages

- Data: `fetch-stock-data`
- Full analysis: `fundamental-analysis`
- Visual: `stock-infographic`
