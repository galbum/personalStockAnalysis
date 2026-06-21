"""CLI: fetch + cache one ticker's data (TradingView snapshot + yfinance history).

Data-acquisition stage of the dashboard pipeline. Thin wrapper over the
dashboard's data layer + cache so the app and skill stay in sync.

Run with the dashboard virtualenv:

    cd <repo>/dashboard && source .venv/bin/activate
    python ../.cursor/skills/fetch-stock-data/scripts/fetch_stock_data.py AAPL
    python ../.cursor/skills/fetch-stock-data/scripts/fetch_stock_data.py AAPL --force --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[4] / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

import cache  # noqa: E402
from data_provider import fetch_company, fetch_price_performance  # noqa: E402


def fetch_full(ticker: str) -> dict:
    data = fetch_company(ticker)
    data["price_perf"] = fetch_price_performance(ticker)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch + cache stock data for a ticker.")
    parser.add_argument("ticker")
    parser.add_argument("--force", action="store_true", help="Ignore the 24h cache and re-fetch")
    parser.add_argument("--json", action="store_true", help="Print the full bundle as JSON")
    args = parser.parse_args()

    data, from_cache, fetched_at = cache.get_or_fetch(args.ticker, fetch_full, force=args.force)
    if args.json:
        print(json.dumps(data, default=str, indent=2))
        return

    print(f"{data.get('ticker')}  {data.get('name')}  | source={data.get('data_source')} | "
          f"{'cached' if from_cache else 'fetched'} {fetched_at}")
    for k in ("price", "market_cap", "pe", "ps", "ev_ebitda", "pb", "peg",
              "dividend_yield", "roe", "recommendation"):
        print(f"  {k:14} {data.get(k)}")


if __name__ == "__main__":
    main()
