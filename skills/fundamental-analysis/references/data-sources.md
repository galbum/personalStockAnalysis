# Reference: Data Sources & Sourcing Discipline

Every sub-agent uses this. The goal is **defensible, timestamped numbers from the best available
source** — a PhD analyst can always say where a figure came from and as of when.

## Source hierarchy (prefer top to bottom)

1. **Primary filings** — the company's own SEC filings (10-K annual, 10-Q quarterly, 8-K events) via the
   SEC EDGAR system, or the equivalent regulatory filing for non-US listings (annual report, interim
   report). These are the ground truth for reported financials.
2. **Investor relations** — the company's IR site: earnings press releases, investor presentations,
   guidance statements, buyback authorizations. Best source for management guidance and segment KPIs.
3. **Reputable financial-data aggregators** — for quick multiples, consensus estimates, peer screens, and
   historical ratios. Convenient and usually current, but treat as secondary: they can lag, differ in
   methodology (e.g. how each computes EV or adjusted EPS), and occasionally carry errors. When an
   aggregator figure drives a conclusion, sanity-check it against the filing.
4. **Sell-side / consensus data** — for analyst ratings, price targets, consensus estimates, and revision
   trends. Inherently opinion-based; report as sentiment, not fact.

## Sourcing rules

- **Search the web** to retrieve current figures — multiples and prices move daily, fundamentals update
  quarterly. Do not rely on memory for any number.
- **Timestamp everything.** Record the reporting period (e.g. "TTM through Q1 FY26", "FY2025") and the
  as-of date. Price-based multiples also need the share price and its date.
- **Watch methodology mismatches.** GAAP vs non-GAAP/adjusted; TTM vs latest-FY vs annualized;
  EV definitions; fiscal-year-end differences across peers (compare like periods). State your choice.
- **Currency.** Note the reporting currency; if comparing peers across currencies, say so.
- **Never fabricate.** If a figure isn't disclosed or can't be found, mark it "n/a — not disclosed" and
  proceed. A labeled gap is fine; an invented number is a failure.
- **Confidence flag.** Each pillar returns a data-quality flag (High/Medium/Low). Lower it when relying on
  aggregators for key figures, when data is stale, or when adjustments are large and opaque.

## Peer set discipline

The orchestrator picks one peer set (3–5 names) and passes the **same set to every pillar** so the deck's
comparisons are internally consistent. Peers should share sub-industry and, ideally, comparable size and
business model. If a "peer" is a poor comparable for a specific metric (e.g. P/B for a non-financial),
note the limitation rather than forcing the comparison.

## Important framing

This skill produces **educational fundamental research**, not personalized investment advice, and the
analyst persona is not the user's financial advisor. Present analysis of what the data implies; keep the
disclaimer in the final deck. Do not source from or amplify pump-and-dump promotion, unverified rumor, or
low-quality forums.
