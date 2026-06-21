# Fundamental Analysis Skill

A Claude Code skill that runs PhD-analyst-grade fundamental analysis on any publicly traded company, benchmarks it against its sector and closest peers, and outputs a slide-by-slide presentation prompt ready to paste into Claude Design.

## What it does

Given a ticker or company name, the skill:

1. Resolves the company, its sector, and two direct competitors
2. Spawns five specialist sub-agents in parallel — one per analytical pillar
3. Reconciles the findings and synthesizes an investment thesis
4. Emits a complete Claude Design prompt for a professional equity-research deck

## The five pillars

| Pillar | Key metrics |
|--------|-------------|
| **Profitability** | Revenue growth, gross/operating/net margin, EPS beat/miss, EBITDA |
| **Valuation** | P/E, Forward P/E, P/S, EV/EBITDA, PEG, P/B |
| **Cash Flow** | OCF, FCF, FCF margin, FCF yield |
| **Financial Health** | D/E, net cash/debt, current/quick ratio, ROE (DuPont), ROIC vs WACC |
| **Forward Signals** | Guidance, analyst consensus, EPS revisions, buybacks, insider activity, short interest |

Every metric is shown as an 8-quarter time series and benchmarked against the sector median and two named direct competitors.

## Usage

```
@fundamental-analysis of stock <ticker or company name>
```

Natural phrasings also work:

- `analyze NVDA for me`
- `is Salesforce fundamentally healthy?`
- `build a fundamentals deck on Ferrari`
- `compare AMD to its sector`

## Output

The skill produces:

- A **slide-by-slide Claude Design prompt** with actual data embedded — paste it directly into Claude Design to generate a polished institutional equity-research deck
- A **3–5 sentence plain-English thesis summary** with bull/bear cases and key risks

> **Disclaimer:** This skill produces educational fundamental research, not personalized investment advice. All output includes a disclaimer slide and should not be interpreted as a buy/sell recommendation.

## Project structure

```
.claude/skills/fundamental-analysis/
├── SKILL.md                        # Orchestrator instructions
├── agents/
│   ├── profitability.md
│   ├── valuation.md
│   ├── cash-flow.md
│   ├── financial-health.md
│   └── forward-signals.md
├── assets/
│   └── deck-prompt-template.md
└── references/
    ├── data-sources.md
    └── metric-definitions.md
```

## Requirements

- Claude Code with subagent support (for parallel pillar execution)
- Works on Claude.ai as well — pillars run sequentially in that environment
