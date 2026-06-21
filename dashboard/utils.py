"""Shared helpers used across the dashboard: numeric coercion, time-series math,
ticker normalization, and display formatting.

Each helper is defined exactly once here so the providers, scorers, charts, and
UI all share one implementation instead of re-declaring near-identical copies.
"""
from __future__ import annotations

import math
from typing import Optional


# --------------------------------------------------------------------------- #
# Tickers
# --------------------------------------------------------------------------- #
def norm_ticker(ticker: str) -> str:
    return (ticker or "").strip().upper()


# --------------------------------------------------------------------------- #
# Numeric coercion & series math
# --------------------------------------------------------------------------- #
def clean(value) -> Optional[float]:
    """Coerce to float or None (treats ""/NaN/inf as missing)."""
    if value is None or value == "":
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def pct_ratio(numerator, denominator) -> Optional[float]:
    """100 * numerator / denominator, rounded to 2dp, or None."""
    n, d = clean(numerator), clean(denominator)
    if n is None or d in (None, 0):
        return None
    return round(100.0 * n / d, 2)


def pct_change(series: list, lag: int) -> list:
    """Percent change vs `lag` periods earlier (lag=4 quarterly YoY, lag=1 annual)."""
    out = [None] * len(series)
    for i in range(lag, len(series)):
        cur, prev = series[i], series[i - lag]
        if cur is not None and prev not in (None, 0):
            out[i] = round(100.0 * (cur - prev) / abs(prev), 2)
    return out


def yoy(series: list) -> list:
    """Year-over-year % change for a quarterly series (period i vs i-4)."""
    return pct_change(series, 4)


def cagr(series):
    """CAGR % over an annual series (oldest->newest). Returns (cagr_pct, years)."""
    vals = [v for v in (series or []) if v is not None]
    if len(vals) < 2:
        return None, 0
    yrs = len(vals) - 1
    first, last = vals[0], vals[-1]
    if first is None or first <= 0 or last <= 0:
        return None, yrs
    return round(((last / first) ** (1 / yrs) - 1) * 100, 1), yrs


def latest(series: list):
    """Last non-None value of a series, else None."""
    for v in reversed(series or []):
        if v is not None:
            return v
    return None


def ttm(series: list):
    """Trailing-twelve-month sum of the last 4 periods, or None if <4 present."""
    vals = [v for v in (series or [])[-4:] if v is not None]
    return sum(vals) if len(vals) == 4 else None


# --------------------------------------------------------------------------- #
# Display formatting
# --------------------------------------------------------------------------- #
def fmt_money(v, currency: str = "") -> str:
    """Compact money: T/B/M suffixes, else thousands-separated."""
    if v is None:
        return "n/a"
    for unit, label in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(v) >= unit:
            return f"{currency}{v / unit:.2f}{label}"
    return f"{currency}{v:,.2f}"


def fmt_num(v, suffix: str = "") -> str:
    return "n/a" if v is None else f"{v:,.2f}{suffix}"


def fmt_pct(v, digits: int = 1) -> str:
    return "n/a" if v is None else f"{v:.{digits}f}%"
