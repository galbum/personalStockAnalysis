# Stock Analysis Dashboard

An interactive Streamlit dashboard with two modes.

### Research (single ticker)

Enter a ticker, click **Analyze**, and it:

1. Pulls **real fundamentals** from TradingView + yfinance (and **FMP** for deep
   history when `FMP_API_KEY` is set) for the company and competitors
2. Computes the [`fundamental-analysis`](../skills/fundamental-analysis) skill's
   **five pillars** (Profitability, Valuation, Cash Flow, Financial Health,
   Forward Signals) plus **Piotroski F-score** and **Altman Z-score**
3. Surfaces analyst metrics: **SBC-adjusted FCF**, FCF yield, Rule of 40,
   net debt/EBITDA, interest coverage, revenue/FCF CAGR, and shareholder yield
4. (Optional) Has **Claude** read the skill's own instruction files and the real
   data, then write the analyst interpretation, verdicts, investment thesis, and a
   ready-to-paste **Claude Design deck prompt**

A tabbed, dark-themed UI (Overview / Pillars / Thesis / Deck prompt) with staged
progress and cached fetches. It's a **hybrid engine**: real numbers + analyst-grade
narrative from the LLM. Without an Anthropic key it still runs in **data-only mode**.

### Infographic (compare)

Enter one ticker for a single-company infographic, or two for a **head-to-head**
comparison (dark, branded PNG in the style of a "$A x $B" equity comparison):
3 top stats (Dividend Yield, Market Cap, Inst. Ownership) + 6 line-chart panels
(Revenue Growth, Free Cash Flow, Total Debt, Capital Expenditure Growth, Stock
Performance, Net Profit Margin). Leave the second ticker blank and Claude picks a
competitor. Generate it standalone via the [`stock-infographic`](../.cursor/skills/stock-infographic)
skill too.

### Caching

Fetched data is cached locally and reused for **24 hours**:

- `cache/data/<TICKER>.json` — metrics + `fetched_at`
- `cache/infographics/<KEY>.png` — generated images

Re-requesting a ticker reuses the cache unless it's older than 24h or you tick
**Force refresh**.

## Setup

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add your Anthropic key (for the narrative + deck prompt):

```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY
```

You can also paste the key directly into the app's sidebar at runtime.

## Run

```bash
source .venv/bin/activate
streamlit run app.py
```

It opens at http://localhost:8501. Enter a ticker (e.g. `NVDA`), optionally set
competitors in the sidebar (otherwise Claude picks two), and click **Analyze**.

## How it works

| Layer | File | Role |
|-------|------|------|
| Data | `data_provider.py` | TradingView + yfinance fetch + metrics + composite scores |
| Deep history | `fmp_provider.py` | Optional FMP (8-12 quarters + ~5y); no-key fallback |
| Snapshot | `tv_provider.py` | TradingView valuation/snapshot (no key) |
| Scores | `scores.py` | Piotroski F-score + Altman Z-score (pure functions) |
| Analysis | `analysis.py` | Builds the five pillars + rule-based preliminary verdicts |
| Charts | `charts.py` | Shared Plotly "equity" template (dark, last-point labels) |
| Narrative | `llm.py` | Sends real data + skill files to Claude; returns thesis + deck prompt |
| Infographic | `infographic.py`, `infographic_data.py` | Assembles the spec + renders the PNG (matplotlib) |
| Cache | `cache.py` | Local JSON/PNG cache with 24h TTL + force refresh |
| UI | `app.py` | Tabbed Streamlit dashboard: research mode + infographic mode |

## Notes & limits

- **Data source:** TradingView + yfinance are free/unofficial; figures can lag or
  differ from primary filings. Without `FMP_API_KEY` history is ~5 quarters (the
  UI labels the depth). "Peer median" is the median of the **shown peers only**,
  not a full sector median. Verify against 10-K/10-Q before acting.
- **Forward signals** (guidance, revisions, buybacks, insider activity) are
  partially available via yfinance; gaps show as `n/a`.
- **Not investment advice.** Educational research only.
