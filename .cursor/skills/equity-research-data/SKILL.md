---
name: equity-research-data
description: Equity-research data standards for the stock dashboard - which financial metrics to add (valuation, quality/returns, cash-flow quality incl. stock-based comp, solvency, growth durability, per-share/dilution, forward signals, market risk), their formulas, composite scores (Piotroski F-score, Altman Z-score), interpretation thresholds, and data sourcing/quality discipline. Use when adding or reviewing financial metrics in the dashboard, deciding what data to add, or improving analytical rigor.
---

# Equity Research Data

What data the dashboard should carry and how to source it defensibly. Senior-analyst
default: comparison-relative, timestamped, never fabricated. Complements the
`fundamental-analysis` skill (which produces the deck); this one governs data
coverage and quality.

## Sourcing discipline

- **Depth matters.** yfinance free gives ~5 quarters, which breaks YoY trends. Add
  a provider with 5y quarterly + annual history (e.g. Financial Modeling Prep,
  Alpha Vantage). Add it behind a `DataProvider` interface in
  `dashboard/data_provider.py` so yfinance stays the no-key fallback.
- **Label everything:** GAAP vs non-GAAP/adjusted, TTM vs latest-FY vs annualized,
  reporting currency, and an as-of date for every figure.
- **Reconcile** shared figures across sources; lower the data-quality flag when
  relying on aggregators or large/opaque adjustments. Never invent a number -
  mark "n/a - not disclosed".

## Metrics to add (by priority)

### Tier 1 - highest analytical value
- **History depth**: 8-12 quarters + 5 fiscal years for every statement line.
- **SBC-adjusted FCF**: FCF and FCF margin after stock-based comp; SBC as % of
  revenue and % of FCF. (Buybacks that only offset SBC are not shareholder return.)
- **Solvency in cash-flow terms**: Net debt / EBITDA, interest coverage
  (EBIT / interest), debt maturity wall.
- **Composite quality scores**: Piotroski F-score and Altman Z-score (below).
- **Estimate revisions**: NTM EPS/revenue revision breadth and direction (90d).

### Tier 2 - completeness
- **Valuation**: EV/Sales, P/FCF, FCF yield vs own 3y range and vs 10y Treasury,
  dividend payout ratio, shareholder yield (dividend + net buyback).
- **Returns/quality**: ROIC vs WACC spread (trend), gross-margin stability,
  Rule of 40 for software (revenue growth % + FCF margin %).
- **Growth durability**: 3y/5y revenue & FCF CAGR, organic vs inorganic, backlog/RPO
  and net revenue retention where disclosed.
- **Per-share**: diluted share-count trend, net buyback yield after SBC.

### Tier 3 - market/risk context
- Beta, annualized volatility, max drawdown, total shareholder return vs a sector
  index, relative strength. True **sector-median** benchmarking (not just two peers).

## Composite scores (concrete formulas)

### Piotroski F-score (0-9; >=7 strong, <=2 weak)
Profitability: (1) ROA > 0; (2) operating cash flow > 0; (3) ROA rising YoY;
(4) OCF > net income (accruals). Leverage/liquidity: (5) long-term debt ratio
falling; (6) current ratio rising; (7) no new shares issued. Efficiency:
(8) gross margin rising; (9) asset turnover rising. Sum the nine 1/0 tests.

### Altman Z-score (manufacturers; use Z'' for others)
Z = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E, where
A = working capital / total assets; B = retained earnings / total assets;
C = EBIT / total assets; D = market cap / total liabilities;
E = revenue / total assets. **Z > 2.99 safe, 1.81-2.99 grey, < 1.81 distress.**

## Interpretation rules

- All thresholds are **sector-relative** orientation, not universal law.
- Direction and acceleration beat absolute level (a decelerating grower is often
  riskier than a steady low-grower).
- Pair every metric with peers + the company's own history + growth context.

## Data-quality checklist

- [ ] >= 8 quarters of history for trend metrics
- [ ] FCF shown both raw and after SBC
- [ ] Net debt/EBITDA + interest coverage present
- [ ] Piotroski F-score and Altman Z-score computed
- [ ] Estimate-revision trend included
- [ ] Every figure carries period + as-of date + GAAP/non-GAAP label
- [ ] Missing data marked "n/a", never fabricated
