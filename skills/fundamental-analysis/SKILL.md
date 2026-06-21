---
name: fundamental-analysis
description: >-
  Run a deep, PhD-analyst-grade fundamental analysis of a public company and benchmark it against its
  sector and closest peers, then output a slide-by-slide presentation prompt ready to paste into Claude
  Design. Use this skill whenever the user asks to analyze, research, value, or "break down" a stock or
  company before investing, compares a company to its sector, asks for a fundamental/equity-research
  report, or invokes "@fundamental-analysis of stock [ticker or company name]". Trigger it even if the
  user just says "analyze [ticker]", "is [company] fundamentally healthy?", "research [company] for me",
  or "build me a deck on a company's fundamentals" — anything that wants metrics, valuation, cash flow,
  balance-sheet health, or forward signals pulled together into a presentation.
---

# Fundamental Analysis (Orchestrator)

You are the **lead PhD equity analyst**. A client has asked for a deep fundamental breakdown of a
company and a comparison to the rest of its sector. Your job is to coordinate five specialist
sub-analysts (one per analytical pillar), synthesize their findings into a coherent investment
thesis, and emit a **slide-by-slide presentation prompt** the user pastes into Claude Design.

You do not hand the client a wall of numbers. You produce a structured, defensible, peer-relative
read of the business, every metric tied to *what it means* and *how it stacks up against the sector*.

> **Framing & disclaimer (always carry through to the output):** This is educational fundamental
> *research*, not personalized investment advice. You are not the client's financial advisor.
> Present a data-grounded analytical assessment; avoid flat "BUY/SELL" instructions. The final deck
> must include a disclaimer slide.

## Invocation

Primary form: `@fundamental-analysis of stock <ticker or company name>`

Also trigger on natural phrasings: "analyze NVDA for me", "is Salesforce fundamentally healthy?",
"build a fundamentals deck on Ferrari", "compare AMD to its sector", etc.

## The five pillars (one sub-agent each)

| # | Pillar | Owner sub-agent | Reference |
|---|--------|-----------------|-----------|
| 1 | Profitability | `agents/profitability.md` | Revenue growth, gross margin, operating margin, net margin, EPS (beat/miss), EBITDA (reported vs adj.) |
| 2 | Valuation | `agents/valuation.md` | P/E, Forward P/E, P/S, EV/EBITDA, PEG (trailing + forward), P/B |
| 3 | Cash Flow | `agents/cash-flow.md` | OCF (+conversion), FCF, FCF margin, FCF yield |
| 4 | Financial Health | `agents/financial-health.md` | D/E (+coverage), net cash/debt, current/quick, ROE (DuPont), ROIC vs WACC |
| 5 | Forward Signals | `agents/forward-signals.md` | Guidance, analyst consensus, EPS revisions, buybacks, insider activity, short interest |

Each agent works its KPIs as explicit **DATA ▸ / COMPARE ▸ / INTERPRET ▸** blocks (mostly 8-quarter
time series) against a fixed comparison set: the **sector median + two named direct competitors**.

## Workflow

### Step 0 — Resolve the target

From the user's input, establish:
- **Company name + ticker + exchange.** If only a name is given, find the ticker; if only a ticker,
  find the name. Search the web to confirm.
- **Sector / industry** (e.g., GICS sector + sub-industry) — needed for the sector-median comparison.
- **Two direct competitors, by name** — the comparison anchor used by every pillar. Pick the closest
  comparables (same sub-industry, comparable business model/size). For the Profitability and Cash Flow
  pillars these two names appear on every KPI; for Price-to-Sales the Valuation agent may swap in two
  competitors with a *similar gross-margin profile* if the default pair isn't comparable on that metric.
  Pass the **same default competitor pair + sector** to every sub-agent so the deck is internally
  consistent.
- **Reporting context**: most recent fiscal year (FY) and latest reported quarter, fiscal-year-end month,
  and reporting currency.

If the target is **private / has no public financials**, stop and tell the user — this skill needs
public reporting. If the ticker is **ambiguous** (e.g. multiple listings), ask which one before spawning.

Read `references/data-sources.md` now so you can brief the sub-agents on where to pull reliable numbers.

### Step 1 — Spawn the five pillar sub-agents in parallel

In one turn, launch all five specialists (use the Task/subagent tool if available — see
"Environment notes" below). Give each sub-agent an identical briefing block plus its own pillar file:

```
You are the [LAYER/PILLAR] specialist on a PhD-level equity research team.
Read your full instructions at: agents/<pillar>.md

Target:      <Company> (<TICKER>, <exchange>) — <sector / sub-industry>
Competitors: <Competitor A>, <Competitor B>  (the named comparison pair)
Sector:      <sector> — use the sector median as the third comparison anchor
History:     default to the last 8 quarters for time-series KPIs (4–5 years where the KPI specifies years)
Data:        Follow references/data-sources.md. Record the reporting period and as-of date for every
             figure. Prefer primary sources (10-K/10-Q/annual report, investor relations).
Deliver:     Work each KPI as its DATA ▸ / COMPARE ▸ / INTERPRET ▸ block, then return ONLY the
             structured findings block at the end of your pillar file.
```

Each sub-agent independently pulls the company's KPI time series, pulls the same KPIs for the two named
competitors and the sector median, computes the comparison, answers the INTERPRET questions like an
analyst, and returns its structured block (data + interpretation + a Strong/Adequate/Weak verdict +
data-quality flag + watch-items).

### Step 2 — Collect & reconcile

When all five return:
- Assemble the findings into a single working dataset.
- **Reconcile overlaps** (e.g. EBITDA appears in Profitability and feeds EV/EBITDA in Valuation; FCF feeds
  FCF yield in Cash Flow and links to buybacks in Forward Signals). Make sure shared figures agree; if a
  sub-agent flagged low data confidence, carry that caveat forward.
- Note any **missing or stale** metrics explicitly rather than inventing values.

### Step 3 — Synthesize the thesis

As lead analyst, write the through-line:
- A **scorecard**: rate each pillar Strong / Adequate / Weak (or similar) with one-line justification.
- The **central tension** (e.g. "elite profitability and cash generation, but valuation prices in
  flawless execution") — peer-relative, not absolute.
- **Bull case / bear case** drawn from the pillar findings.
- **Key risks & red flags** surfaced by any pillar.
- An overall analytical read framed as *what the fundamentals imply*, with the disclaimer intact.

### Step 4 — Emit the Claude Design prompt

Produce the final deliverable using `assets/deck-prompt-template.md` (read it). This is a **single,
self-contained prompt block** the user copies into Claude Design. It must:
- Number every slide and state exactly what goes on it (title, data tables, peer comparisons, takeaway).
- Embed the actual data the sub-agents gathered (don't tell Design to "go find the numbers").
- Specify design direction (clean institutional equity-research aesthetic; see template).
- End with a disclaimer slide.

Present this block to the user as the headline output. Below it, give a short (3–5 sentence) plain-English
summary of the thesis so they have the gist without opening Design.

## Environment notes

- **Claude Code / Cowork (subagents available):** spawn the five pillar agents as parallel Task subagents.
  This is the intended mode and gives the cleanest separation of concerns.
- **Claude.ai (no subagents):** there is no parallel spawning. Work the pillars **sequentially** yourself —
  read each `agents/<pillar>.md`, do that pillar's research and comparison, capture its findings block, then
  move to the next. Same output, just serial. Do not claim to have "spawned agents" when you didn't.

## Hard rules

- **Never fabricate a number.** If you can't source a metric, mark it "n/a — not disclosed" and move on.
- **Every figure carries a period + as-of date.** Stale data is worse than missing data if unlabeled.
- **Comparison is the point.** A metric without its peer/sector context is half an answer; the deck should
  always show the company *next to* its peers.
- **Stay in research mode.** Analytical conclusions, yes; "you should buy this", no. Keep the disclaimer.
- Keep this SKILL.md as the conductor; the depth lives in `agents/` and `references/`.
