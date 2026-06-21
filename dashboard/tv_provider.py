"""TradingView snapshot provider (primary source for current values).

Uses the `tradingview-screener` package (official /screener endpoint, no API
key) to pull current valuation + fundamental snapshot fields. TradingView does
not expose multi-quarter history here, so the dashboard keeps yfinance for the
8-quarter time-series charts; this module supplies everything else.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

import pandas as pd

# TradingView column -> our metric key.
_COLS = {
    "description": "name",
    "sector": "sector",
    "industry": "industry",
    "close": "price",
    "market_cap_basic": "market_cap",
    "price_earnings_ttm": "pe",
    "price_sales_current": "ps",
    "enterprise_value_ebitda_ttm": "ev_ebitda",
    "price_book_fq": "pb",
    "price_earnings_growth_ttm": "peg",
    "total_revenue_ttm": "revenue_ttm",
    "free_cash_flow_ttm": "fcf_ttm",
    "total_debt": "total_debt",
    "dividends_yield": "dividend_yield",
    "net_margin": "net_margin",
    "return_on_equity": "roe",
    "Recommend.All": "recommend_score",
}


def _recommendation(score: Optional[float]) -> Optional[str]:
    """Map TradingView's -1..1 Recommend.All score to a label."""
    if score is None:
        return None
    if score >= 0.5:
        return "strong_buy"
    if score >= 0.1:
        return "buy"
    if score > -0.1:
        return "hold"
    if score > -0.5:
        return "sell"
    return "strong_sell"


@lru_cache(maxsize=64)
def fetch_snapshot(ticker: str) -> dict:
    """Return a current snapshot dict from TradingView, or {} on any failure."""
    ticker = ticker.strip().upper()
    try:
        from tradingview_screener import Column, Query

        _, df = (
            Query()
            .select(*_COLS.keys())
            .where(Column("name") == ticker)
            .get_scanner_data()
        )
    except Exception:
        return {}
    if df is None or df.empty:
        return {}

    # If a symbol lists on multiple exchanges, prefer the largest by market cap.
    if "market_cap_basic" in df and len(df) > 1:
        df = df.sort_values("market_cap_basic", ascending=False, na_position="last")
    row = df.iloc[0]

    out: dict = {}
    for tv_col, key in _COLS.items():
        val = row.get(tv_col)
        out[key] = None if (val is None or (isinstance(val, float) and pd.isna(val))) else val

    out["recommendation"] = _recommendation(out.pop("recommend_score", None))
    out["tv_ticker"] = row.get("ticker")
    return out
