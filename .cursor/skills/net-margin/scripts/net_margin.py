"""CLI: net profit margin for one or more tickers, with multi-year trend."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[4] / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

from data_provider import fetch_company, latest  # noqa: E402


def _pct(v) -> str:
    return "n/a" if v is None else f"{float(v):.1f}%"


def _first(series):
    for v in series or []:
        if v is not None:
            return v
    return None


def _trend(series) -> str:
    a, b = _first(series), latest(series)
    if a is None or b is None:
        return "trend n/a"
    chg = b - a  # margins are already in percentage points
    arrow = "expanding" if chg > 0.5 else ("compressing" if chg < -0.5 else "stable")
    return f"{arrow} ({a:.1f}% -> {b:.1f}%)"


def _read(v) -> str:
    if v is None:
        return "margin n/a"
    v = float(v)
    if v < 0:
        return "loss-making (negative net margin)"
    if v >= 20:
        return "high profitability"
    if v >= 10:
        return "healthy profitability"
    return "thin profitability"


def main() -> None:
    parser = argparse.ArgumentParser(description="Net profit margin for tickers.")
    parser.add_argument("tickers", nargs="+")
    args = parser.parse_args()

    rows = [(t, fetch_company(t)) for t in args.tickers]
    header = f"{'TICKER':8}{'NET MARGIN':>12}"
    print(header)
    print("-" * len(header))
    for t, d in rows:
        m = d.get("net_margin")
        cur = latest(m) if isinstance(m, list) else m
        print(f"{d.get('ticker', t):8}{_pct(cur):>12}")
    print()
    for t, d in rows:
        m = d.get("net_margin")
        cur = latest(m) if isinstance(m, list) else m
        annual = d.get("net_margin_annual")
        print(f"{d.get('ticker', t)}: {_read(cur)} | {_trend(annual)} (annual)")


if __name__ == "__main__":
    main()
