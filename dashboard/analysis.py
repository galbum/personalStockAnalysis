"""Assemble the five analytical pillars from real company data.

Produces a structured, JSON-serialisable dict the UI renders and the LLM
layer interprets. Verdicts here are simple, transparent, rule-based
*preliminary* reads; the LLM refines them into the analyst narrative.
"""
from __future__ import annotations

import datetime as dt
from statistics import median
from typing import Optional

from data_provider import fetch_company, latest

PILLARS = ["profitability", "valuation", "cash_flow", "financial_health", "forward_signals"]


def _median(values) -> Optional[float]:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return round(median(vals), 2)


def _verdict(score: int) -> str:
    if score >= 2:
        return "Strong"
    if score <= -2:
        return "Weak"
    return "Adequate"


def _peer_block(metric_key, target, comps, higher_is_better=True):
    """Build a {label: value} comparison incl. a peer median of shown peers."""
    block = {target["ticker"]: _resolve_metric(target, metric_key)}
    peer_vals = []
    for c in comps:
        v = _resolve_metric(c, metric_key)
        block[c["ticker"]] = v
        peer_vals.append(v)
    block["Peer median"] = _median(peer_vals)
    return block


def _resolve_metric(company, key):
    """Return a latest scalar for a metric key (series -> latest, else field)."""
    series_keys = {
        "rev_yoy", "gross_margin", "op_margin", "net_margin", "ebitda_margin",
        "fcf_margin", "fcf_ex_sbc_margin", "ocf_to_ni",
    }
    if key in series_keys:
        return latest(company.get(key))
    return company.get(key)


def build_analysis(target_ticker: str, competitor_tickers: list) -> dict:
    target = fetch_company(target_ticker)
    comps = [fetch_company(t) for t in competitor_tickers if t]

    out = {
        "as_of": dt.date.today().isoformat(),
        "target": {
            "ticker": target["ticker"],
            "name": target["name"],
            "sector": target["sector"],
            "industry": target["industry"],
            "exchange": target["exchange"],
            "currency": target["currency"],
            "price": target["price"],
            "market_cap": target["market_cap"],
            "summary": target["summary"],
        },
        "competitors": [c["ticker"] for c in comps],
        "scores": {
            "piotroski": target.get("piotroski"),
            "altman": target.get("altman"),
        },
        "data_source": target.get("data_source"),
        "history_quarters": target.get("history_quarters"),
        "raw": {"target": target, "competitors": comps},
        "pillars": {},
    }

    out["pillars"]["profitability"] = _profitability(target, comps)
    out["pillars"]["valuation"] = _valuation(target, comps)
    out["pillars"]["cash_flow"] = _cash_flow(target, comps)
    out["pillars"]["financial_health"] = _financial_health(target, comps)
    out["pillars"]["forward_signals"] = _forward_signals(target, comps)
    return out


def _profitability(target, comps):
    score = 0
    yoy = latest(target["rev_yoy"])
    if yoy is not None:
        score += 1 if yoy > 10 else (-1 if yoy < 0 else 0)
    om = latest(target["op_margin"])
    peer_om = _median([latest(c["op_margin"]) for c in comps])
    if om is not None and peer_om is not None:
        score += 1 if om > peer_om else -1
    return {
        "title": "Profitability",
        "series": {
            "labels": target["quarters"],
            "Revenue YoY %": target["rev_yoy"],
            "Gross margin %": target["gross_margin"],
            "Operating margin %": target["op_margin"],
            "Net margin %": target["net_margin"],
        },
        "peers": {
            "Revenue YoY %": _peer_block("rev_yoy", target, comps),
            "Gross margin %": _peer_block("gross_margin", target, comps),
            "Operating margin %": _peer_block("op_margin", target, comps),
            "Net margin %": _peer_block("net_margin", target, comps),
        },
        "rule_verdict": _verdict(score),
    }


def _valuation(target, comps):
    # Cheaper than peers on EV/EBITDA & P/E => leans attractive.
    score = 0
    for key in ("pe", "ev_ebitda"):
        tv = target.get(key)
        peer = _median([c.get(key) for c in comps])
        if tv is not None and peer is not None and tv > 0:
            score += 1 if tv < peer else -1
    return {
        "title": "Valuation",
        "peers": {
            "P/E (TTM)": _peer_block("pe", target, comps),
            "Forward P/E": _peer_block("forward_pe", target, comps),
            "P/S": _peer_block("ps", target, comps),
            "EV/EBITDA": _peer_block("ev_ebitda", target, comps),
            "PEG": _peer_block("peg", target, comps),
            "P/B": _peer_block("pb", target, comps),
            "FCF yield %": _peer_block("fcf_yield", target, comps),
        },
        # Note: lower multiple = "Strong" (attractive) in valuation.
        "rule_verdict": _verdict(score),
    }


def _cash_flow(target, comps):
    score = 0
    fcfm = latest(target["fcf_margin"])
    peer_fcfm = _median([latest(c["fcf_margin"]) for c in comps])
    if fcfm is not None and peer_fcfm is not None:
        score += 1 if fcfm > peer_fcfm else -1
    conv = latest(target["ocf_to_ni"])
    if conv is not None:
        score += 1 if conv >= 1 else -1
    # Heavy SBC relative to FCF quietly erodes real owner cash flow.
    sbc_pct_fcf = target.get("sbc_pct_fcf")
    if sbc_pct_fcf is not None:
        score += -1 if sbc_pct_fcf > 25 else (1 if sbc_pct_fcf < 10 else 0)
    return {
        "title": "Cash Flow",
        "series": {
            "labels": target["quarters"],
            "FCF margin %": target["fcf_margin"],
            "FCF margin ex-SBC %": target.get("fcf_ex_sbc_margin"),
            "OCF/Net income (x)": target["ocf_to_ni"],
        },
        "peers": {
            "FCF margin %": _peer_block("fcf_margin", target, comps),
            "FCF margin ex-SBC %": _peer_block("fcf_ex_sbc_margin", target, comps),
        },
        "sbc_pct_revenue": target.get("sbc_pct_revenue"),
        "sbc_pct_fcf": sbc_pct_fcf,
        "rule_verdict": _verdict(score),
    }


def _financial_health(target, comps):
    score = 0
    de = target.get("debt_to_equity")
    peer_de = _median([c.get("debt_to_equity") for c in comps])
    if de is not None and peer_de is not None:
        score += 1 if de < peer_de else -1
    if target.get("net_cash") is not None:
        score += 1 if target["net_cash"] > 0 else -1
    roe = target.get("roe")
    peer_roe = _median([c.get("roe") for c in comps])
    if roe is not None and peer_roe is not None:
        score += 1 if roe > peer_roe else -1
    # Cash-flow solvency: leverage and the ability to service it.
    nde = target.get("net_debt_to_ebitda")
    if nde is not None:
        score += 1 if nde < 1 else (-1 if nde > 3 else 0)
    cov = target.get("interest_coverage")
    if cov is not None:
        score += 1 if cov > 8 else (-1 if cov < 3 else 0)
    return {
        "title": "Financial Health",
        "peers": {
            "Debt/Equity": _peer_block("debt_to_equity", target, comps),
            "Net debt/EBITDA": _peer_block("net_debt_to_ebitda", target, comps),
            "Interest coverage": _peer_block("interest_coverage", target, comps),
            "Current ratio": _peer_block("current_ratio", target, comps),
            "ROE %": _peer_block("roe", target, comps),
        },
        "net_cash": target.get("net_cash"),
        "net_debt_to_ebitda": nde,
        "interest_coverage": cov,
        "currency": target.get("currency"),
        "rule_verdict": _verdict(score),
    }


def _forward_signals(target, comps):
    score = 0
    rec = (target.get("recommendation") or "").lower()
    if rec in ("buy", "strong_buy"):
        score += 1
    elif rec in ("sell", "strong_sell", "underperform"):
        score -= 1
    upside = None
    if target.get("target_mean_price") and target.get("price"):
        upside = round(100.0 * (target["target_mean_price"] - target["price"]) / target["price"], 1)
        score += 1 if upside > 10 else (-1 if upside < -5 else 0)
    return {
        "title": "Forward Signals",
        "recommendation": target.get("recommendation"),
        "num_analysts": target.get("num_analysts"),
        "target_mean_price": target.get("target_mean_price"),
        "target_high_price": target.get("target_high_price"),
        "target_low_price": target.get("target_low_price"),
        "price": target.get("price"),
        "implied_upside_pct": upside,
        "short_percent_float": target.get("short_percent_float"),
        "rule_verdict": _verdict(score),
    }
