"""Composite quality / solvency scores: Piotroski F-score and Altman Z-score.

Pure functions over already-extracted annual figures (no I/O), so they are easy
to test and stay source-agnostic. Every input may be None; tests that cannot be
evaluated are skipped rather than fabricated, and the score reports how many of
the nine checks were actually evaluable.
"""
from __future__ import annotations

from typing import Optional

from utils import clean as _num


def _safe_div(n, d) -> Optional[float]:
    n, d = _num(n), _num(d)
    if n is None or d in (None, 0):
        return None
    return n / d


def piotroski(cur: dict, prev: dict) -> dict:
    """Piotroski F-score (0-9). `cur`/`prev` are dicts of annual figures:

    net_income, total_assets, ocf, long_term_debt, current_assets,
    current_liab, shares, gross_profit, revenue.

    Returns {score, evaluated, max, signals: {test: bool|None}}.
    """
    s: dict = {}

    roa = _safe_div(cur.get("net_income"), cur.get("total_assets"))
    roa_prev = _safe_div(prev.get("net_income"), prev.get("total_assets"))
    ocf = _num(cur.get("ocf"))
    ni = _num(cur.get("net_income"))
    ta = _num(cur.get("total_assets"))

    # Profitability
    s["roa_positive"] = (roa > 0) if roa is not None else None
    s["ocf_positive"] = (ocf > 0) if ocf is not None else None
    s["roa_rising"] = (roa > roa_prev) if (roa is not None and roa_prev is not None) else None
    s["accruals_ok"] = (ocf > ni) if (ocf is not None and ni is not None) else None  # OCF > NI

    # Leverage / liquidity
    ltd_ratio = _safe_div(cur.get("long_term_debt"), cur.get("total_assets"))
    ltd_ratio_prev = _safe_div(prev.get("long_term_debt"), prev.get("total_assets"))
    s["leverage_falling"] = (ltd_ratio < ltd_ratio_prev) if (ltd_ratio is not None and ltd_ratio_prev is not None) else None

    cr = _safe_div(cur.get("current_assets"), cur.get("current_liab"))
    cr_prev = _safe_div(prev.get("current_assets"), prev.get("current_liab"))
    s["current_ratio_rising"] = (cr > cr_prev) if (cr is not None and cr_prev is not None) else None

    sh, sh_prev = _num(cur.get("shares")), _num(prev.get("shares"))
    s["no_dilution"] = (sh <= sh_prev * 1.01) if (sh is not None and sh_prev not in (None, 0)) else None

    # Efficiency
    gm = _safe_div(cur.get("gross_profit"), cur.get("revenue"))
    gm_prev = _safe_div(prev.get("gross_profit"), prev.get("revenue"))
    s["gross_margin_rising"] = (gm > gm_prev) if (gm is not None and gm_prev is not None) else None

    at = _safe_div(cur.get("revenue"), ta)
    at_prev = _safe_div(prev.get("revenue"), prev.get("total_assets"))
    s["asset_turnover_rising"] = (at > at_prev) if (at is not None and at_prev is not None) else None

    evaluated = [v for v in s.values() if v is not None]
    score = sum(1 for v in evaluated if v)
    return {
        "score": score,
        "evaluated": len(evaluated),
        "max": 9,
        "signals": s,
        "verdict": _piotroski_verdict(score, len(evaluated)),
    }


def _piotroski_verdict(score: int, evaluated: int) -> str:
    if evaluated < 5:
        return "insufficient data"
    if score >= 7:
        return "strong"
    if score <= 2:
        return "weak"
    return "middling"


def altman_z(d: dict) -> dict:
    """Altman Z-score. `d` has: working_capital, total_assets, retained_earnings,
    ebit, market_cap, total_liabilities, revenue. Uses the classic manufacturer
    formula; treat as orientation, not law, for non-manufacturers.
    """
    ta = _num(d.get("total_assets"))
    tl = _num(d.get("total_liabilities"))
    if ta in (None, 0):
        return {"z": None, "zone": "n/a", "components": {}}

    A = _safe_div(d.get("working_capital"), ta)
    B = _safe_div(d.get("retained_earnings"), ta)
    C = _safe_div(d.get("ebit"), ta)
    D = _safe_div(d.get("market_cap"), tl)
    E = _safe_div(d.get("revenue"), ta)
    parts = {"A_wc_ta": A, "B_re_ta": B, "C_ebit_ta": C, "D_mcap_tl": D, "E_rev_ta": E}
    if any(v is None for v in (A, B, C, E)):  # D can be missing if no liabilities
        return {"z": None, "zone": "insufficient data", "components": parts}

    z = 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * (D or 0) + 1.0 * E
    if z > 2.99:
        zone = "safe"
    elif z >= 1.81:
        zone = "grey"
    else:
        zone = "distress"
    return {"z": round(z, 2), "zone": zone, "components": parts}
