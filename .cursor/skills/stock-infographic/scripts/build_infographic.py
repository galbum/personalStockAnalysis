"""CLI wrapper: build a stock infographic for 1-2 tickers.

Thin layer over the dashboard's generator so the skill and the app stay in
sync. Fetches data via yfinance, assembles the spec, and renders a PNG.

Run with the dashboard virtualenv (matplotlib + yfinance installed):

    cd <repo>/dashboard && source .venv/bin/activate
    python ../.cursor/skills/stock-infographic/scripts/build_infographic.py ORCL MSFT \
        --out /tmp/orcl_msft.png --period "Q2'26"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[4] / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

from data_provider import fetch_company, fetch_price_performance  # noqa: E402
from infographic import build_infographic  # noqa: E402
from infographic_data import build_spec  # noqa: E402


def _full(ticker: str) -> dict:
    data = fetch_company(ticker)
    data["price_perf"] = fetch_price_performance(ticker)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a stock comparison infographic (PNG).")
    parser.add_argument("tickers", nargs="+", help="One or two tickers, e.g. ORCL MSFT")
    parser.add_argument("--out", default="infographic.png", help="Output PNG path")
    parser.add_argument("--period", default="", help="Period label for the footer")
    parser.add_argument("--brand", default="Gabi Album", help="Footer brand text")
    parser.add_argument("--handle", default="", help="Right-footer handle/text")
    args = parser.parse_args()

    bundles = [_full(t.upper()) for t in args.tickers[:2]]
    spec = build_spec(bundles, period=args.period, brand=args.brand, handle=args.handle)
    build_infographic(spec, args.out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
