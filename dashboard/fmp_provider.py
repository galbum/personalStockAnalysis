"""Optional deep-history provider: Financial Modeling Prep (FMP).

yfinance free only returns ~5 quarters, which breaks YoY trends. When an
``FMP_API_KEY`` is set (env or .env), this module pulls 8-12 quarters + ~5 fiscal
years of income / cash-flow / balance-sheet lines, plus stock-based compensation.

It is entirely optional: with no key, or on any error, every function returns
an empty result and the caller keeps yfinance. Series are returned oldest->newest
so they drop straight into the existing bundle shape.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

import requests

_BASE = "https://financialmodelingprep.com/api/v3"
_TIMEOUT = 12


def api_key() -> Optional[str]:
    return os.environ.get("FMP_API_KEY") or None


def available() -> bool:
    return bool(api_key())


def _num(v) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        f = float(v)
        return None if (f != f) else f  # NaN guard
    except (TypeError, ValueError):
        return None


def _get(endpoint: str, ticker: str, period: str, limit: int) -> list:
    key = api_key()
    if not key:
        return []
    url = f"{_BASE}/{endpoint}/{ticker.upper()}"
    try:
        r = requests.get(url, params={"period": period, "limit": limit, "apikey": key}, timeout=_TIMEOUT)
        if r.status_code != 200:
            return []
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _col(rows: list, field: str) -> list:
    """Extract one field across statement rows, oldest->newest."""
    return [_num(row.get(field)) for row in reversed(rows)]


def _labels(rows: list, fmt: str) -> list:
    out = []
    for row in reversed(rows):
        d = row.get("date") or ""
        if fmt == "quarter":
            out.append(str(d)[:7])  # YYYY-MM
        else:
            out.append(str(d)[:4])  # YYYY
    return out


@lru_cache(maxsize=64)
def fetch_history(ticker: str, quarters: int = 12, years: int = 5) -> dict:
    """Return deep history series, or {} if FMP is unavailable / fails."""
    if not available():
        return {}
    ticker = ticker.strip().upper()

    q_inc = _get("income-statement", ticker, "quarter", quarters)
    q_cf = _get("cash-flow-statement", ticker, "quarter", quarters)
    q_bs = _get("balance-sheet-statement", ticker, "quarter", quarters)
    a_inc = _get("income-statement", ticker, "annual", years)
    a_cf = _get("cash-flow-statement", ticker, "annual", years)
    a_bs = _get("balance-sheet-statement", ticker, "annual", years)

    if not q_inc and not a_inc:
        return {}

    out: dict = {"data_source_history": "fmp"}

    # ---- Quarterly ----
    if q_inc:
        out["quarters"] = _labels(q_inc, "quarter")
        revenue = _col(q_inc, "revenue")
        gross = _col(q_inc, "grossProfit")
        op_inc = _col(q_inc, "operatingIncome")
        net_inc = _col(q_inc, "netIncome")
        ebitda = _col(q_inc, "ebitda")
        out["revenue"] = revenue
        out["gross_margin"] = _margin(gross, revenue)
        out["op_margin"] = _margin(op_inc, revenue)
        out["net_margin"] = _margin(net_inc, revenue)
        out["ebitda"] = ebitda
        out["ebitda_margin"] = _margin(ebitda, revenue)
        out["net_income"] = net_inc
        out["rev_yoy"] = _pct_change(revenue, 4)

    if q_cf:
        # cash-flow series aligned to its own quarters; reuse income labels if equal length
        ocf = _col(q_cf, "operatingCashFlow")
        capex = _col(q_cf, "capitalExpenditure")
        fcf = _col(q_cf, "freeCashFlow")
        sbc = _col(q_cf, "stockBasedCompensation")
        rev = out.get("revenue") or []
        if not fcf or all(v is None for v in fcf):
            fcf = [(ocf[i] + capex[i]) if (i < len(ocf) and i < len(capex)
                   and ocf[i] is not None and capex[i] is not None) else None
                   for i in range(max(len(ocf), len(capex)))]
        out["ocf"] = ocf
        out["capex"] = capex
        out["fcf"] = fcf
        out["sbc_series"] = sbc
        if rev:
            out["fcf_margin"] = _margin(fcf, rev)
        out["ocf_to_ni"] = [
            round(ocf[i] / out["net_income"][i], 2)
            if (out.get("net_income") and i < len(out["net_income"])
                and ocf[i] is not None and out["net_income"][i] not in (None, 0)) else None
            for i in range(len(ocf))
        ]
        cap_abs = [abs(x) if x is not None else None for x in capex]
        out["capex_growth"] = _pct_change(cap_abs, 4)

    if q_bs:
        out["bs_quarters"] = _labels(q_bs, "quarter")
        out["total_debt_series"] = _col(q_bs, "totalDebt")

    # ---- Annual (for clear YoY + composite scores) ----
    if a_inc:
        out["annual_labels"] = _labels(a_inc, "annual")
        rev_a = _col(a_inc, "revenue")
        ni_a = _col(a_inc, "netIncome")
        gp_a = _col(a_inc, "grossProfit")
        ebit_a = _col(a_inc, "operatingIncome")
        out["revenue_annual"] = rev_a
        out["rev_yoy_annual"] = _pct_change(rev_a, 1)
        out["net_margin_annual"] = _margin(ni_a, rev_a)
        out["_annual_income"] = {
            "net_income": ni_a, "gross_profit": gp_a, "revenue": rev_a, "ebit": ebit_a,
            "shares": _col(a_inc, "weightedAverageShsOutDil"),
        }
    if a_cf:
        out["annual_cf_labels"] = _labels(a_cf, "annual")
        ocf_a = _col(a_cf, "operatingCashFlow")
        capex_a = _col(a_cf, "capitalExpenditure")
        fcf_a = _col(a_cf, "freeCashFlow")
        if not fcf_a or all(v is None for v in fcf_a):
            fcf_a = [(ocf_a[i] + capex_a[i]) if (i < len(ocf_a) and i < len(capex_a)
                     and ocf_a[i] is not None and capex_a[i] is not None) else None
                     for i in range(max(len(ocf_a), len(capex_a)))]
        out["fcf_annual"] = fcf_a
        cap_abs_a = [abs(x) if x is not None else None for x in capex_a]
        out["capex_growth_annual"] = _pct_change(cap_abs_a, 1)
        out["_annual_cf"] = {"ocf": ocf_a, "sbc": _col(a_cf, "stockBasedCompensation")}
    if a_bs:
        out["annual_bs_labels"] = _labels(a_bs, "annual")
        out["total_debt_annual"] = _col(a_bs, "totalDebt")
        out["_annual_bs"] = {
            "total_assets": _col(a_bs, "totalAssets"),
            "total_liabilities": _col(a_bs, "totalLiabilities"),
            "current_assets": _col(a_bs, "totalCurrentAssets"),
            "current_liab": _col(a_bs, "totalCurrentLiabilities"),
            "retained_earnings": _col(a_bs, "retainedEarnings"),
            "long_term_debt": _col(a_bs, "longTermDebt"),
        }
    return out


def _margin(numer: list, denom: list) -> list:
    out = []
    for i in range(len(numer)):
        n = numer[i]
        d = denom[i] if i < len(denom) else None
        out.append(round(100.0 * n / d, 2) if (n is not None and d not in (None, 0)) else None)
    return out


def _pct_change(series: list, lag: int) -> list:
    out = [None] * len(series)
    for i in range(lag, len(series)):
        cur, prev = series[i], series[i - lag]
        if cur is not None and prev not in (None, 0):
            out[i] = round(100.0 * (cur - prev) / abs(prev), 2)
    return out
