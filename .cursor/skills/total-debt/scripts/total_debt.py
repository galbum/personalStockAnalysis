"""CLI: total debt + leverage for one or more tickers, with multi-year trend."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[4] / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

from data_provider import fetch_company, latest  # noqa: E402


def _bil(v) -> str:
    return "n/a" if v is None else f"${float(v) / 1e9:,.1f}B"


def _num(v) -> str:
    return "n/a" if v is None else f"{float(v):.2f}"


def _first(series):
    for v in series or []:
        if v is not None:
            return v
    return None


def _trend(series) -> str:
    a, b = _first(series), latest(series)
    if a is None or b is None:
        return "trend n/a"
    if a == 0:
        return "rising from ~0" if b > 0 else "flat"
    chg = (b - a) / abs(a) * 100
    arrow = "up" if chg > 5 else ("down" if chg < -5 else "flat")
    return f"{arrow} {chg:+.0f}% over the window"


def _read(d) -> str:
    de = d.get("debt_to_equity")
    net_cash = d.get("net_cash")
    parts = []
    if net_cash is not None and float(net_cash) > 0:
        parts.append("net cash positive (cash > debt)")
    if de is not None:
        de = float(de)
        de = de / 100 if de > 5 else de  # some sources report D/E as a percent
        if de < 0.5:
            parts.append(f"conservative leverage (D/E {de:.2f})")
        elif de < 1:
            parts.append(f"moderate leverage (D/E {de:.2f})")
        elif de <= 2:
            parts.append(f"elevated leverage (D/E {de:.2f})")
        else:
            parts.append(f"high leverage (D/E {de:.2f})")
    return "; ".join(parts) if parts else "leverage data n/a"


def main() -> None:
    parser = argparse.ArgumentParser(description="Total debt + leverage for tickers.")
    parser.add_argument("tickers", nargs="+")
    args = parser.parse_args()

    rows = [(t, fetch_company(t)) for t in args.tickers]
    header = f"{'TICKER':8}{'TOTAL DEBT':>13}{'NET CASH':>13}{'D/E':>8}"
    print(header)
    print("-" * len(header))
    for t, d in rows:
        print(f"{d.get('ticker', t):8}{_bil(d.get('total_debt')):>13}"
              f"{_bil(d.get('net_cash')):>13}{_num(d.get('debt_to_equity')):>8}")
    print()
    for t, d in rows:
        annual = d.get("total_debt_annual") or d.get("total_debt_series")
        print(f"{d.get('ticker', t)}: {_read(d)} | debt {_trend(annual)}")


if __name__ == "__main__":
    main()
