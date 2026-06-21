"""CLI: dividend yield for one or more tickers."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[4] / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

from data_provider import fetch_company  # noqa: E402


def _pct(v) -> str:
    return "n/a" if v is None else f"{float(v):.2f}%"


def _read(v) -> str:
    if v is None or float(v) == 0:
        return "no dividend -> growth/reinvestment profile, total return from price"
    v = float(v)
    if v < 2:
        return "low yield -> growth-tilted, dividend is a small part of return"
    if v < 4:
        return "moderate yield -> blend of income and growth"
    if v <= 6:
        return "high yield -> income-oriented; check payout sustainability"
    return "very high yield -> verify it isn't a yield trap (falling price / payout risk)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Dividend yield for tickers.")
    parser.add_argument("tickers", nargs="+")
    args = parser.parse_args()

    rows = [(t, fetch_company(t)) for t in args.tickers]
    header = f"{'TICKER':8}{'DIV YIELD':>11}"
    print(header)
    print("-" * len(header))
    for t, d in rows:
        print(f"{d.get('ticker', t):8}{_pct(d.get('dividend_yield')):>11}")
    print()
    for t, d in rows:
        print(f"{d.get('ticker', t)}: {_read(d.get('dividend_yield'))}")


if __name__ == "__main__":
    main()
