"""Assemble the infographic spec (exact metric set) from fetched bundles.

Mirrors the reference layout: 3 top stats (Dividend Yield, Market Cap,
Inst. Ownership) + 6 chart panels (Revenue Growth, Free Cash Flow, Total Debt,
Capital Expenditure Growth, Stock Performance, Net Profit Margin).
"""
from __future__ import annotations

from typing import Optional

from config import BRAND, INFOGRAPHIC_COLORS
from utils import fmt_money, fmt_pct, latest

COLORS = INFOGRAPHIC_COLORS  # [brand orange, white, ...] matches the reference

_NAME_SUFFIXES = [
    " corporation", " incorporated", " inc.", " inc", " company", " co.", " co",
    " holdings", " technologies", " group", " plc", " ltd.", " ltd", " limited",
    " corp.", " corp", " s.a.", " ag", " se", " nv", " n.v.",
]


def _short_name(name: Optional[str], ticker: str) -> str:
    if not name:
        return ticker
    n = name.split(",")[0].strip()
    changed = True
    while changed:
        changed = False
        for suf in _NAME_SUFFIXES:
            if n.lower().endswith(suf):
                n = n[: -len(suf)].strip()
                changed = True
    return n or ticker


def _series_div(values, divisor):
    return [(v / divisor) if v is not None else None for v in (values or [])]


def _top_stat(label, fmt, bundles, key):
    return {"label": label, "values": [fmt(b.get(key)) for b in bundles]}


def _panel(title, bundles, value_key, label_key, end_fmt, divisor=1.0, subtitle=""):
    series = []
    for b in bundles:
        raw = b.get(value_key) or []
        values = _series_div(raw, divisor) if divisor != 1.0 else list(raw)
        series.append({
            "labels": b.get(label_key) or [],
            "values": values,
            "end_label": end_fmt(latest(values)),
        })
    return {"title": title, "subtitle": subtitle, "series": series}


def _price_panel(bundles):
    series = []
    for b in bundles:
        perf = b.get("price_perf") or {"dates": [], "pct": []}
        series.append({
            "labels": perf.get("dates", []),
            "values": perf.get("pct", []),
            "end_label": fmt_pct(latest(perf.get("pct", []))),
        })
    return {"title": "Stock Performance", "subtitle": "% change over the window", "series": series}


def build_spec(bundles: list, period: str = "", brand: str = BRAND,
               handle: str = "") -> dict:
    companies = []
    for i, b in enumerate(bundles):
        companies.append({
            "ticker": b.get("ticker", "?"),
            "name": _short_name(b.get("name"), b.get("ticker", "?")),
            "color": COLORS[i % len(COLORS)],
        })

    top_stats = [
        _top_stat("Dividend Yield", fmt_pct, bundles, "dividend_yield"),
        _top_stat("Market Cap", fmt_money, bundles, "market_cap"),
        _top_stat("Inst. Ownership", fmt_pct, bundles, "inst_ownership"),
    ]

    panels = [
        # Growth panels: a few YEARS (annual YoY) so the trend is clear.
        _panel("Revenue Growth", bundles, "rev_yoy_annual", "annual_labels", fmt_pct, subtitle="YoY, annual"),
        # Level panels: a few QUARTERS, quarter by quarter.
        _panel("Free Cash Flow", bundles, "fcf", "quarters", lambda v: f"${v:,.1f}" if v is not None else "n/a", divisor=1e9, subtitle="*Billions, quarterly"),
        _panel("Total Debt", bundles, "total_debt_series", "bs_quarters", lambda v: f"${v:,.0f}" if v is not None else "n/a", divisor=1e9, subtitle="*Billions, quarterly"),
        _panel("Capital Expenditure Growth", bundles, "capex_growth_annual", "annual_cf_labels", fmt_pct, subtitle="YoY, annual"),
        _price_panel(bundles),
        _panel("Net Profit Margin", bundles, "net_margin", "quarters", fmt_pct, subtitle="quarterly"),
    ]

    return {
        "period": period,
        "brand": brand,
        "handle": handle,
        "companies": companies,
        "top_stats": top_stats,
        "panels": panels,
    }
