"""CLI: institutional ownership for one or more tickers."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[4] / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

from data_provider import fetch_company  # noqa: E402


def _pct(v) -> str:
    return "n/a" if v is None else f"{float(v):.1f}%"


def _read(v) -> str:
    if v is None:
        return "ownership data n/a"
    v = float(v)
    if v >= 70:
        return "heavily institution-owned -> high conviction but crowded; sensitive to fund flows"
    if v >= 40:
        return "balanced institutional ownership"
    return "low institutional ownership -> more retail / insider-held, can be less liquid"


def main() -> None:
    parser = argparse.ArgumentParser(description="Institutional ownership for tickers.")
    parser.add_argument("tickers", nargs="+")
    args = parser.parse_args()

    rows = [(t, fetch_company(t)) for t in args.tickers]
    header = f"{'TICKER':8}{'INST OWN':>10}"
    print(header)
    print("-" * len(header))
    for t, d in rows:
        print(f"{d.get('ticker', t):8}{_pct(d.get('inst_ownership')):>10}")
    print()
    for t, d in rows:
        print(f"{d.get('ticker', t)}: {_read(d.get('inst_ownership'))}")


if __name__ == "__main__":
    main()
