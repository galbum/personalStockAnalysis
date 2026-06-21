"""Real fundamental data via yfinance.

Pulls quarterly financials, cash-flow, balance-sheet and current valuation
multiples for a ticker and packages them into a flat, chart-ready dict.

Everything is defensive: any missing figure becomes None (rendered as "n/a"),
never a fabricated value -- consistent with the skill's sourcing discipline.
"""
from __future__ import annotations

import math
from functools import lru_cache
from typing import Optional

import pandas as pd
import yfinance as yf

MAX_QUARTERS = 8


def _clean(value) -> Optional[float]:
    """Coerce to float or None (treats NaN/inf as missing)."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _get_row(df: Optional[pd.DataFrame], *candidates: str) -> Optional[pd.Series]:
    """Return the first row whose index label matches any candidate.

    Tries exact (case-insensitive) match first, then a substring match.
    """
    if df is None or getattr(df, "empty", True):
        return None
    index_map = {str(i).strip().lower(): i for i in df.index}
    for cand in candidates:
        key = cand.strip().lower()
        if key in index_map:
            return df.loc[index_map[key]]
    for cand in candidates:
        key = cand.strip().lower()
        for low, original in index_map.items():
            if key in low:
                return df.loc[original]
    return None


def _series_to_list(row: Optional[pd.Series], columns) -> list:
    """Align a statement row to the chosen (oldest->newest) column order."""
    if row is None:
        return [None] * len(columns)
    out = []
    for col in columns:
        try:
            out.append(_clean(row.get(col)))
        except Exception:
            out.append(None)
    return out


def _pct(numerator, denominator) -> Optional[float]:
    n, d = _clean(numerator), _clean(denominator)
    if n is None or d in (None, 0):
        return None
    return round(100.0 * n / d, 2)


def _yoy(series: list) -> list:
    """Year-over-year % change for a quarterly series (period i vs i-4)."""
    out = [None] * len(series)
    for i in range(4, len(series)):
        cur, prev = series[i], series[i - 4]
        if cur is not None and prev not in (None, 0):
            out[i] = round(100.0 * (cur - prev) / abs(prev), 2)
    return out


@lru_cache(maxsize=64)
def fetch_company(ticker: str) -> dict:
    """Fetch and assemble a company's metric bundle. Cached per process."""
    ticker = ticker.strip().upper()
    t = yf.Ticker(ticker)

    info = {}
    try:
        info = t.info or {}
    except Exception:
        info = {}

    try:
        income = t.quarterly_income_stmt
    except Exception:
        income = None
    try:
        cashflow = t.quarterly_cashflow
    except Exception:
        cashflow = None
    try:
        balance = t.quarterly_balance_sheet
    except Exception:
        balance = None

    # Choose up to 8 most-recent quarters from the income statement, oldest->newest.
    if income is not None and not income.empty:
        cols = list(income.columns)[:MAX_QUARTERS]
        cols = list(reversed(cols))
    else:
        cols = []
    quarter_labels = [pd.Timestamp(c).strftime("%Y-%m") for c in cols]

    revenue = _series_to_list(_get_row(income, "Total Revenue", "Revenue"), cols)
    gross_profit = _series_to_list(_get_row(income, "Gross Profit"), cols)
    operating_income = _series_to_list(
        _get_row(income, "Operating Income", "Operating Income Or Loss"), cols
    )
    net_income = _series_to_list(
        _get_row(income, "Net Income", "Net Income Common Stockholders"), cols
    )
    ebitda_row = _get_row(income, "EBITDA", "Normalized EBITDA")
    ebitda = _series_to_list(ebitda_row, cols)

    def margins(numer):
        return [_pct(numer[i], revenue[i]) for i in range(len(cols))]

    gross_margin = margins(gross_profit)
    op_margin = margins(operating_income)
    net_margin = margins(net_income)
    ebitda_margin = margins(ebitda)
    rev_yoy = _yoy(revenue)

    # Cash flow (align to income-statement columns where possible).
    cf_cols = cols if cols else (list(reversed(list(cashflow.columns)[:MAX_QUARTERS])) if cashflow is not None and not cashflow.empty else [])
    ocf = _series_to_list(
        _get_row(cashflow, "Operating Cash Flow", "Total Cash From Operating Activities"),
        cf_cols,
    )
    capex = _series_to_list(
        _get_row(cashflow, "Capital Expenditure", "Capital Expenditures"), cf_cols
    )
    fcf_row = _get_row(cashflow, "Free Cash Flow")
    if fcf_row is not None:
        fcf = _series_to_list(fcf_row, cf_cols)
    else:
        fcf = [
            (ocf[i] + capex[i]) if (ocf[i] is not None and capex[i] is not None) else None
            for i in range(len(cf_cols))
        ]
    fcf_margin = [_pct(fcf[i], revenue[i]) if i < len(revenue) else None for i in range(len(fcf))]
    ocf_to_ni = [
        round(ocf[i] / net_income[i], 2)
        if (i < len(net_income) and ocf[i] is not None and net_income[i] not in (None, 0))
        else None
        for i in range(len(ocf))
    ]

    # Balance sheet -- latest column only.
    latest_bs = balance.columns[0] if (balance is not None and not balance.empty) else None

    def bs(*names):
        row = _get_row(balance, *names)
        if row is None or latest_bs is None:
            return None
        return _clean(row.get(latest_bs))

    total_debt = bs("Total Debt")
    if total_debt is None:
        ltd = bs("Long Term Debt") or 0
        std = bs("Current Debt", "Short Term Debt") or 0
        total_debt = (ltd + std) or None
    cash = bs("Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments")
    sti = bs("Other Short Term Investments")
    cash_total = None
    if cash is not None:
        cash_total = cash + (sti or 0)
    equity = bs("Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity")
    current_assets = bs("Current Assets", "Total Current Assets")
    current_liab = bs("Current Liabilities", "Total Current Liabilities")
    inventory = bs("Inventory")

    debt_to_equity = round(total_debt / equity, 2) if (total_debt is not None and equity not in (None, 0)) else None
    current_ratio = round(current_assets / current_liab, 2) if (current_assets is not None and current_liab not in (None, 0)) else None
    quick_ratio = (
        round((current_assets - (inventory or 0)) / current_liab, 2)
        if (current_assets is not None and current_liab not in (None, 0))
        else None
    )
    net_cash = None
    if cash_total is not None and total_debt is not None:
        net_cash = cash_total - total_debt

    # Valuation / returns / forward -- from info.
    def gv(*keys):
        for k in keys:
            v = _clean(info.get(k))
            if v is not None:
                return v
        return None

    roe = gv("returnOnEquity")
    if roe is not None and abs(roe) <= 5:  # yfinance gives a fraction
        roe = round(roe * 100, 2)
    roa = gv("returnOnAssets")
    if roa is not None and abs(roa) <= 5:
        roa = round(roa * 100, 2)

    return {
        "ticker": ticker,
        "name": info.get("longName") or info.get("shortName") or ticker,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "exchange": info.get("fullExchangeName") or info.get("exchange"),
        "currency": info.get("currency") or info.get("financialCurrency"),
        "price": gv("currentPrice", "regularMarketPrice"),
        "market_cap": gv("marketCap"),
        "summary": info.get("longBusinessSummary"),
        # series (oldest -> newest)
        "quarters": quarter_labels,
        "revenue": revenue,
        "rev_yoy": rev_yoy,
        "gross_margin": gross_margin,
        "op_margin": op_margin,
        "net_margin": net_margin,
        "ebitda": ebitda,
        "ebitda_margin": ebitda_margin,
        "net_income": net_income,
        "ocf": ocf,
        "capex": capex,
        "fcf": fcf,
        "fcf_margin": fcf_margin,
        "ocf_to_ni": ocf_to_ni,
        # balance / returns (latest)
        "total_debt": total_debt,
        "cash": cash_total,
        "equity": equity,
        "current_assets": current_assets,
        "current_liab": current_liab,
        "debt_to_equity": debt_to_equity,
        "current_ratio": current_ratio,
        "quick_ratio": quick_ratio,
        "net_cash": net_cash,
        "roe": roe,
        "roa": roa,
        # valuation multiples (current)
        "pe": gv("trailingPE"),
        "forward_pe": gv("forwardPE"),
        "ps": gv("priceToSalesTrailing12Months"),
        "ev_ebitda": gv("enterpriseToEbitda"),
        "peg": gv("trailingPegRatio", "pegRatio"),
        "pb": gv("priceToBook"),
        # forward signals
        "recommendation": info.get("recommendationKey"),
        "target_mean_price": gv("targetMeanPrice"),
        "target_high_price": gv("targetHighPrice"),
        "target_low_price": gv("targetLowPrice"),
        "num_analysts": gv("numberOfAnalystOpinions"),
        "shares_outstanding": gv("sharesOutstanding"),
        "short_percent_float": (lambda v: round(v * 100, 2) if v is not None and abs(v) <= 5 else v)(gv("shortPercentOfFloat")),
    }


def latest(series: list):
    """Last non-None value of a series, else None."""
    for v in reversed(series or []):
        if v is not None:
            return v
    return None
