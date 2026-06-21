"""CLI: trailing P/E vs forward P/E for one or more tickers.

Reads the dashboard data bundle (TradingView trailing P/E + yfinance forward P/E)
and reports the trailing/forward multiples, the implied earnings-growth signal,
and PEG context. Pass several tickers for a quick peer comparison.

Run with the dashboard virtualenv:

    cd <repo>/dashboard && source .venv/bin/activate
    python ../.cursor/skills/pe-forward-pe/scripts/pe_forward_pe.py NVDA
    python ../.cursor/skills/pe-forward-pe/scripts/pe_forward_pe.py NVDA AMD AVGO
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[4] / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

from data_provider import fetch_company  # noqa: E402


def _fmt(v) -> str:
    return "n/a" if v is None else f"{float(v):.1f}"


def _implied_growth(pe, fwd) -> str:
    """Trailing/forward gap implies expected next-year EPS change."""
    if pe is None or fwd in (None, 0):
        return "n/a"
    g = (float(pe) / float(fwd) - 1.0) * 100.0
    return f"{g:+.1f}% implied EPS growth"


def _read(pe, fwd) -> str:
    if pe is None and fwd is None:
        return "no earnings multiple (loss-making or missing data)"
    if pe is None:
        return "trailing P/E n/a (likely unprofitable TTM); forward P/E prices in a return to profit"
    if fwd is None:
        return "forward P/E n/a (no consensus EPS estimate)"
    if fwd < pe:
        return "forward < trailing -> market expects EPS to grow (multiple compresses on next-year earnings)"
    if fwd > pe:
        return "forward > trailing -> market expects EPS to fall"
    return "forward ~= trailing -> flat earnings expectations"


def report(ticker: str) -> dict:
    d = fetch_company(ticker)
    return {
        "ticker": d.get("ticker", ticker),
        "name": d.get("name"),
        "price": d.get("price"),
        "pe": d.get("pe"),
        "forward_pe": d.get("forward_pe"),
        "peg": d.get("peg"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Trailing vs forward P/E for tickers.")
    parser.add_argument("tickers", nargs="+", help="One or more symbols, e.g. NVDA AMD")
    args = parser.parse_args()

    rows = [report(t) for t in args.tickers]

    header = f"{'TICKER':8}{'P/E':>9}{'FWD P/E':>10}{'PEG':>8}   SIGNAL"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['ticker']:8}{_fmt(r['pe']):>9}{_fmt(r['forward_pe']):>10}{_fmt(r['peg']):>8}"
              f"   {_implied_growth(r['pe'], r['forward_pe'])}")

    print()
    for r in rows:
        print(f"{r['ticker']}: {_read(r['pe'], r['forward_pe'])}")
        if r.get("peg") is not None:
            peg = float(r["peg"])
            tag = "cheap vs growth" if peg < 1 else ("fair" if peg <= 2 else "expensive vs growth")
            print(f"        PEG {peg:.2f} -> {tag}")


if __name__ == "__main__":
    main()
