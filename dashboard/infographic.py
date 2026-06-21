"""Programmatic head-to-head stock infographic (matplotlib).

Renders a dark, branded infographic in the style of a head-to-head equity
comparison: a header of company names, a strip of single-value stats, a 2x3
grid of multi-quarter line charts, and a footer. Handles 1 or 2 companies.

The generator is *pure*: it takes a fully-resolved `spec` dict (see SPEC SHAPE
below) and writes a PNG. Data fetching lives elsewhere (infographic_data.py).

SPEC SHAPE
----------
{
  "period": "Q2'26",
  "brand": "Gabi Album",
  "handle": "",
  "companies": [{"ticker": "ORCL", "name": "ORACLE", "color": "#e8552d"}, ...],
  "top_stats": [{"label": "Dividend Yield", "values": ["1.1%", "0.9%"]}, ...],
  "panels": [
    {"title": "Revenue Growth", "subtitle": "",
     "series": [{"labels": [...], "values": [...], "end_label": "20.6%"}, ...]},
    ...
  ]
}
"""
from __future__ import annotations

import argparse
import json
import math
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from config import (BG_DARK as BG, BRAND, DIVIDER, INFOGRAPHIC_COLORS as DEFAULT_COLORS,
                    INFOGRAPHIC_FG as FG, MUTED, WHITE)  # noqa: E402


def _nan(values):
    return [float(v) if v is not None else math.nan for v in (values or [])]


def _header_fontsize(max_len: int, base: float, floor: float = 12.0) -> float:
    """Shrink the header font for long company names so they don't overflow."""
    if max_len <= 10:
        return base
    return max(floor, base - (max_len - 10) * 0.9)


def _draw_header(bgax, companies):
    n = len(companies)
    if n == 1:
        c = companies[0]
        fs = _header_fontsize(len(c["name"]), base=30, floor=16)
        bgax.text(0.5, 0.965, c["name"].upper(), color=c.get("color", FG),
                  ha="center", va="center", fontsize=fs, fontweight="bold")
    else:
        a, b = companies[0], companies[1]
        fs = _header_fontsize(max(len(a["name"]), len(b["name"])), base=23)
        bgax.text(0.475, 0.965, a["name"].upper(), color=a.get("color", FG),
                  ha="right", va="center", fontsize=fs, fontweight="bold")
        bgax.text(0.50, 0.965, "x", color=MUTED, ha="center", va="center", fontsize=fs * 0.78)
        bgax.text(0.525, 0.965, b["name"].upper(), color=b.get("color", FG),
                  ha="left", va="center", fontsize=fs, fontweight="bold")
    bgax.plot([0.05, 0.95], [0.93, 0.93], color=DIVIDER, lw=1)


def _draw_top_stats(bgax, top_stats, companies):
    if not top_stats:
        return
    centers = [0.21, 0.5, 0.79][: len(top_stats)]
    colors = [c.get("color", FG) for c in companies]
    for cx, stat in zip(centers, top_stats):
        bgax.text(cx, 0.905, stat["label"], color=FG, ha="center", va="center",
                  fontsize=13, fontweight="bold")
        vals = stat.get("values", [])
        if len(vals) == 1:
            bgax.text(cx, 0.882, vals[0], color=colors[0], ha="center", va="center", fontsize=12)
        elif len(vals) >= 2:
            bgax.text(cx - 0.012, 0.882, vals[0], color=colors[0], ha="right", va="center", fontsize=12)
            bgax.text(cx, 0.882, "x", color=MUTED, ha="center", va="center", fontsize=11)
            bgax.text(cx + 0.012, 0.882, vals[1], color=colors[1] if colors[1] != WHITE else FG,
                      ha="left", va="center", fontsize=12)
    bgax.plot([0.05, 0.95], [0.86, 0.86], color=DIVIDER, lw=1)


def _draw_panel(ax, panel, companies):
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=6.5, length=0)
    ax.grid(False)

    series = panel.get("series", [])
    labels = None
    for i, s in enumerate(series):
        color = companies[i].get("color", DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
        vals = _nan(s.get("values"))
        labels = s.get("labels") or labels or list(range(len(vals)))
        x = list(range(len(vals)))
        ax.plot(x, vals, color=color, lw=1.8, marker="o", markersize=2.5,
                label=f"${companies[i]['ticker']}")
        # End-value label near the last finite point.
        last_idx = next((j for j in range(len(vals) - 1, -1, -1) if not math.isnan(vals[j])), None)
        if last_idx is not None and s.get("end_label"):
            ax.annotate(s["end_label"], (x[last_idx], vals[last_idx]),
                        textcoords="offset points", xytext=(6, 0), color=color,
                        fontsize=7.5, fontweight="bold", va="center")

    title = panel["title"]
    if panel.get("subtitle"):
        title_obj = ax.set_title(title, color=FG, fontsize=11, fontweight="bold", loc="left", pad=14)
        ax.text(0, 1.02, panel["subtitle"], transform=ax.transAxes, color=MUTED, fontsize=6.5)
    else:
        ax.set_title(title, color=FG, fontsize=11, fontweight="bold", loc="left", pad=8)

    # Legend chips for the companies.
    handles = [Line2D([0], [0], color=companies[i].get("color", FG), lw=0, marker="s",
                      markersize=6, label=f"${companies[i]['ticker']}")
               for i in range(len(series))]
    if handles:
        leg = ax.legend(handles=handles, loc="upper right", frameon=False, fontsize=6.5,
                        labelcolor=FG, handletextpad=0.3, ncol=len(handles), columnspacing=0.8)
        for txt in leg.get_texts():
            txt.set_color(FG)

    # Thin x ticks (avoid crowding).
    if labels:
        n = len(labels)
        step = max(1, n // 8)
        idxs = list(range(0, n, step))
        ax.set_xticks(idxs)
        ax.set_xticklabels([labels[i] for i in idxs], rotation=90)
    ax.margins(x=0.08, y=0.18)


def build_infographic(spec: dict, out_path: str) -> str:
    companies = spec.get("companies", [])
    for i, c in enumerate(companies):
        c.setdefault("color", DEFAULT_COLORS[i % len(DEFAULT_COLORS)])

    fig = plt.figure(figsize=(10, 12.7), dpi=110)
    fig.patch.set_facecolor(BG)

    bgax = fig.add_axes([0, 0, 1, 1])
    bgax.set_xlim(0, 1)
    bgax.set_ylim(0, 1)
    bgax.axis("off")

    _draw_header(bgax, companies)
    _draw_top_stats(bgax, spec.get("top_stats", []), companies)

    panels = spec.get("panels", [])
    gs = fig.add_gridspec(3, 2, left=0.07, right=0.94, top=0.82, bottom=0.085,
                          hspace=0.55, wspace=0.22)
    for idx, panel in enumerate(panels[:6]):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        _draw_panel(ax, panel, companies)

    # Footer.
    brand = spec.get("brand", BRAND)
    bgax.plot([0.05, 0.95], [0.055, 0.055], color=DIVIDER, lw=1)
    bgax.text(0.05, 0.03, brand, color=FG, ha="left", va="center", fontsize=12, fontweight="bold")
    right = spec.get("handle") or spec.get("period") or ""
    if right:
        bgax.text(0.95, 0.03, right, color=MUTED, ha="right", va="center", fontsize=10)

    fig.savefig(out_path, facecolor=BG, bbox_inches=None)
    plt.close(fig)
    return out_path


def _main():
    parser = argparse.ArgumentParser(description="Build a stock infographic PNG from a JSON spec.")
    parser.add_argument("--data", required=True, help="Path to the JSON spec file.")
    parser.add_argument("--out", required=True, help="Output PNG path.")
    args = parser.parse_args()
    with open(args.data, encoding="utf-8") as f:
        spec = json.load(f)
    path = build_infographic(spec, args.out)
    print(f"Wrote {path}")


if __name__ == "__main__":
    _main()
