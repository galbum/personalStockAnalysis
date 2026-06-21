"""Shared Plotly styling so research charts match the infographic aesthetic.

One template ("equity"), one palette, fixed heights, last-point labels, minimal
chart junk. Import `line_chart` / `peer_bar` from here instead of hand-rolling
figures in the app.
"""
from __future__ import annotations

from typing import Optional

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

PALETTE = ["#e8552d", "#ffffff", "#4c9be8", "#f0c419", "#9b59b6"]
PEER_COLOR = "#4c9be8"
TARGET_COLOR = "#e8552d"
MEDIAN_COLOR = "#9b59b6"

pio.templates["equity"] = go.layout.Template(
    layout=dict(
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#f2f2f2", size=12),
        colorway=PALETTE,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(gridcolor="#222", zeroline=False),
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.06, x=0, bgcolor="rgba(0,0,0,0)"),
    )
)


def _last_valid(values):
    for i in range(len(values) - 1, -1, -1):
        if values[i] is not None:
            return i, values[i]
    return None, None


def line_chart(series: dict, title: str, height: int = 320, value_suffix: str = ""):
    """Render a multi-series line chart from {"labels": [...], name: [...]}."""
    labels = series.get("labels") or []
    fig = go.Figure()
    plotted = False
    for name, values in series.items():
        if name == "labels":
            continue
        if values and any(v is not None for v in values):
            fig.add_trace(go.Scatter(x=labels, y=values, mode="lines+markers", name=name))
            idx, val = _last_valid(values)
            if idx is not None:
                fig.add_annotation(
                    x=labels[idx] if idx < len(labels) else None,
                    y=val, text=f"{val:,.1f}{value_suffix}", showarrow=False,
                    xshift=28, font=dict(size=11), align="left",
                )
            plotted = True
    if not plotted:
        st.info("No time-series data available.")
        return
    fig.update_layout(template="equity", title=title, height=height)
    st.plotly_chart(fig, use_container_width=True)


def peer_bar(peer_metric: dict, title: str, target_ticker: Optional[str] = None, height: int = 300):
    """Bar chart of a single metric across the target + peers + median."""
    names = list(peer_metric.keys())
    values = [peer_metric[n] for n in names]
    if not any(v is not None for v in values):
        return
    colors = []
    for n in names:
        if n == "Peer median":
            colors.append(MEDIAN_COLOR)
        elif target_ticker and n == target_ticker:
            colors.append(TARGET_COLOR)
        else:
            colors.append(PEER_COLOR)
    fig = go.Figure(go.Bar(x=names, y=values, marker_color=colors,
                           text=[f"{v:,.1f}" if v is not None else "" for v in values],
                           textposition="outside"))
    fig.update_layout(template="equity", title=title, height=height, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
