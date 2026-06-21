# Asset: Claude Design Deck Prompt Template

This is the **final deliverable skeleton**. After collecting all five pillar findings and writing the
thesis, the orchestrator fills this in with the *actual gathered data* and outputs it as ONE
self-contained block the user pastes into Claude Design. Do not tell Design to "go find the numbers" —
embed them, including the two named competitors and the sector median for every comparison. Keep each
figure's period/as-of label. Time-series KPIs should be shown as 8-quarter trend visuals, not single points.

Slide count is adaptive, but follow this spine. Default = 13 slides.

---

## TEMPLATE — copy everything below the line, fill the brackets, paste into Claude Design

---

Create a polished institutional equity-research presentation. Audience: an investor wanting a deep
fundamental breakdown of **[COMPANY] ([TICKER], [exchange])** versus its sector and two named direct
competitors (**[Competitor A], [Competitor B]**). Aesthetic: clean, data-forward, professional — a
top-tier sell-side research deck. Restrained palette (deep navy / slate / one accent), generous
whitespace, crisp data tables, simple 8-quarter bar/line trend charts, grouped bars for peer comparison,
no clip-art. Every data slide shows [TICKER] next to its two competitors and the sector median. Footer on
each slide: "Data as of [date] · Educational research, not investment advice."

**Slide 1 — Title.** "[COMPANY] ([TICKER]) — Fundamental Analysis". Subtitle: sector / sub-industry,
report date, comparison set ([Competitor A], [Competitor B], sector median). Author line: "PhD Equity Research".

**Slide 2 — Company snapshot.** One-paragraph business description, how it makes money, key segments,
market cap, share price (as-of [date]), and the two competitors + sector used for comparison.

**Slide 3 — Executive summary & thesis.** Thesis in 2–3 sentences. The core tension (one line). Pillar
scorecard strip: Profitability [S/A/W] · Valuation [S/A/W] · Cash Flow [S/A/W] · Financial Health [S/A/W]
· Forward Signals [S/A/W].

**Slide 4 — Scorecard detail.** Five-row table: each layer, its verdict, one-line justification. Clean
visual of where the business is strong vs exposed.

**Slide 5 — Layer 01: Profitability.** 8-quarter trend charts for revenue growth (YoY & QoQ), gross
margin, operating margin, and net margin, each with [Competitor A], [Competitor B], and sector median
overlaid or in a comparison strip; call out the operating→net margin spread and its driver. EPS panel:
reported vs consensus with beat/miss % and whether the beat streak is expanding or shrinking. EBITDA
panel: reported vs adjusted with the gap trend (widening = earnings-quality flag) and what's being
excluded. Takeaway box: is growth accelerating/decelerating; pricing power; operating leverage. [watch-items]

**Slide 6 — Layer 02: Valuation.** Table: P/E (TTM) vs 5y own avg, Forward P/E (+3-month change, flag if
expanding on falling estimates), P/S vs 3y avg, EV/EBITDA (net cash/debt adjusted), PEG shown both ways
(trailing P/E ÷ 3y EPS CAGR as primary, forward P/E ÷ forward growth as cross-check — note any divergence),
P/B vs 5y avg — each vs sector median, [Competitor A], [Competitor B], with premium/discount. As-of price
[$… on date]. Takeaway: rich/fair/cheap across the three lenses (peers / own history / growth) and *why*.
[watch-items]

**Slide 7 — Layer 03: Cash Flow.** 8-quarter trends: OCF vs net income with the conversion ratio (flag
sustained divergence + drivers), FCF with YoY growth shown against revenue and net-income growth, FCF
margin vs sector/competitors (quartile). FCF-yield panel: LTM FCF/market cap vs the 10-year Treasury yield,
vs sector median, vs the stock's own 3-year range. Takeaway: earnings→cash quality and whether the yield
compensates for equity risk. [watch-items]

**Slide 8 — Layer 04: Financial Health.** D/E + interest coverage over 4 years with the "EBITDA −30%"
stress-test result; net cash/debt with quarters-of-opex covered and management's capital-allocation stance;
current & quick ratio trend (4q) with any receivables/inventory flag and near-term maturities. Returns
panel: 5y ROE with DuPont decomposition (is it operations or leverage?) and ROIC-vs-WACC spread over 5
years (widening = compounder). All vs sector median + the two competitors. Takeaway: solvency + capital
efficiency verdict. [watch-items]

**Slide 9 — Layer 05: Forward Signals.** Management guidance vs consensus and vs year-ago (conservative or
aggressive track record; embedded growth bar). Analyst consensus: buy/hold/sell split, median PT (implied
up/downside), PT range, and the 3-month change. Earnings revisions: % raised vs lowered over 90 days and
consensus move (leading-indicator reliability). Buybacks: 8-quarter spend/shares/avg price, net share-count
change after SBC (real reduction vs compensation subsidy), annualized buyback yield. Insider activity:
6-month buy/sell, buy:sell vs historical norm, any cluster buying. Short interest: % of float, days-to-cover,
and the 12-month trend vs sector median (flag elevated >10% / squeeze-watch >20%, or rising shorts with no
price drop). Takeaway: net forward lean. [watch-items]

**Slide 10 — Peer & sector comparison.** The headline cross-peer view: grouped bar charts placing
[TICKER] against [Competitor A], [Competitor B], and the sector median on the 5–6 most decision-relevant
KPIs (e.g. revenue growth, operating margin, FCF margin, FCF yield, EV/EBITDA, ROIC−WACC spread). One line
on where the company ranks overall in its sub-industry.

**Slide 11 — Bull case vs bear case.** Two columns. Bull: 3–4 bullets from the findings. Bear: 3–4 bullets
on the risks the data raises.

**Slide 12 — Risks & red flags.** The specific watch-items across all five layers, prioritized (e.g.
widening reported-vs-adjusted EBITDA gap, OCF<NI divergence, buybacks only offsetting SBC, ROE that's
leverage not operations). Note any low-data-confidence areas.

**Slide 13 — Conclusion & disclaimer.** Synthesized analytical read: what the fundamentals imply about
business quality and how the valuation reflects it (analysis, not a buy/sell order). Disclaimer: "This
presentation is educational fundamental research, not personalized investment advice. Figures are as of
[date] and may be revised; verify against primary filings before acting. The author is not your financial
advisor."

---

## Notes for the orchestrator filling this in

- Replace every bracket with real, sourced data from the pillar findings — including the competitor and
  sector-median numbers and the 8-quarter series.
- Render time-series KPIs as trend charts (8 quarters) and cross-peer KPIs as grouped bars — that's where
  acceleration/deceleration and quartile ranking become visible.
- If a pillar flagged Low data quality or an "n/a", reflect that honestly on its slide.
- Keep tables to the decision-relevant values, not every figure gathered.
- If the user asked for a different emphasis (e.g. "focus on valuation"), reweight slide depth while
  keeping the disclaimer slide.
