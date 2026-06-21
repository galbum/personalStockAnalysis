"""Fundamental Analysis Dashboard (Streamlit).

Enter a ticker -> pulls real fundamentals (yfinance) -> computes the five
pillars -> (optionally) has Claude write the analyst narrative + Claude Design
deck prompt. Hybrid engine, faithful to the fundamental-analysis skill.
"""
from __future__ import annotations

import os

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from analysis import PILLARS, build_analysis
import cache
from data_provider import fetch_company, fetch_price_performance
from infographic import build_infographic
from infographic_data import build_spec
import llm


def fetch_full(ticker: str) -> dict:
    """Combined, JSON-serialisable bundle used for caching + infographics."""
    data = fetch_company(ticker)
    data["price_perf"] = fetch_price_performance(ticker)
    return data

load_dotenv()

st.set_page_config(page_title="Fundamental Analysis Dashboard", page_icon=":chart_with_upwards_trend:", layout="wide")

VERDICT_COLORS = {"Strong": "#1a7f37", "Adequate": "#9a6700", "Weak": "#b42318"}
PILLAR_LABELS = {
    "profitability": "Profitability",
    "valuation": "Valuation",
    "cash_flow": "Cash Flow",
    "financial_health": "Financial Health",
    "forward_signals": "Forward Signals",
}


def fmt_money(v, currency=""):
    if v is None:
        return "n/a"
    suffix = ""
    for unit, label in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(v) >= unit:
            return f"{currency}{v / unit:.2f}{label}"
    return f"{currency}{v:,.2f}"


def fmt_num(v, suffix=""):
    if v is None:
        return "n/a"
    return f"{v:,.2f}{suffix}"


def verdict_badge(label, verdict):
    color = VERDICT_COLORS.get(verdict, "#57606a")
    st.markdown(
        f"<div style='text-align:center;padding:10px 6px;border-radius:10px;"
        f"background:{color}1a;border:1px solid {color}55;'>"
        f"<div style='font-size:0.8rem;color:#57606a;'>{label}</div>"
        f"<div style='font-size:1.05rem;font-weight:700;color:{color};'>{verdict}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def line_chart(series: dict, title: str):
    labels = series.get("labels") or []
    fig = go.Figure()
    plotted = False
    for name, values in series.items():
        if name == "labels":
            continue
        if values and any(v is not None for v in values):
            fig.add_trace(go.Scatter(x=labels, y=values, mode="lines+markers", name=name))
            plotted = True
    if not plotted:
        st.info("No time-series data available for this pillar.")
        return
    fig.update_layout(
        title=title, height=340, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def peer_bar(peer_metric: dict, title: str):
    names = list(peer_metric.keys())
    values = [peer_metric[n] for n in names]
    if not any(v is not None for v in values):
        return
    colors = ["#0969da" if n != "Peer median" else "#8250df" for n in names]
    fig = go.Figure(go.Bar(x=names, y=values, marker_color=colors))
    fig.update_layout(title=title, height=300, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def peer_table(peers: dict):
    rows = list(peers.keys())
    cols = []
    for metric in peers.values():
        for k in metric.keys():
            if k not in cols:
                cols.append(k)
    data = {"Metric": rows}
    for c in cols:
        data[c] = [fmt_num(peers[r].get(c)) for r in rows]
    st.dataframe(data, use_container_width=True, hide_index=True)


def render(analysis: dict, narrative: dict | None):
    t = analysis["target"]
    cur = (t.get("currency") or "") and (t.get("currency") + " ")

    # Header
    st.subheader(f"{t['name']} ({t['ticker']})")
    meta = " · ".join(filter(None, [t.get("exchange"), t.get("sector"), t.get("industry")]))
    st.caption(meta or "")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", fmt_money(t.get("price"), cur))
    c2.metric("Market cap", fmt_money(t.get("market_cap"), cur))
    c3.metric("Competitors", ", ".join(analysis["competitors"]) or "n/a")
    c4.metric("As of", analysis["as_of"])
    if t.get("summary"):
        with st.expander("Business summary"):
            st.write(t["summary"])

    # Scorecard
    st.markdown("### Scorecard")
    cols = st.columns(5)
    for i, key in enumerate(PILLARS):
        pill = analysis["pillars"][key]
        verdict = pill["rule_verdict"]
        if narrative:
            verdict = narrative.get("pillars", {}).get(key, {}).get("verdict", verdict)
        with cols[i]:
            verdict_badge(PILLAR_LABELS[key], verdict)

    # Thesis
    if narrative and narrative.get("thesis"):
        th = narrative["thesis"]
        st.markdown("### Investment thesis")
        if th.get("central_tension"):
            st.info(f"**Central tension:** {th['central_tension']}")
        if th.get("summary"):
            st.write(th["summary"])
        bcol, rcol = st.columns(2)
        with bcol:
            st.markdown("**Bull case**")
            for b in th.get("bull", []):
                st.markdown(f"- {b}")
        with rcol:
            st.markdown("**Bear case**")
            for b in th.get("bear", []):
                st.markdown(f"- {b}")
        if th.get("risks"):
            st.markdown("**Key risks & red flags**")
            for r in th["risks"]:
                st.markdown(f"- {r}")

    # Pillars
    st.markdown("### Pillar detail")
    for key in PILLARS:
        pill = analysis["pillars"][key]
        nar = (narrative or {}).get("pillars", {}).get(key, {})
        with st.expander(f"{PILLAR_LABELS[key]} — {nar.get('verdict', pill['rule_verdict'])}", expanded=(key == "profitability")):
            left, right = st.columns([3, 2])
            with left:
                if pill.get("series"):
                    line_chart(pill["series"], f"{PILLAR_LABELS[key]} — 8-quarter trend")
                if pill.get("peers"):
                    first_metric = next(iter(pill["peers"]))
                    peer_bar(pill["peers"][first_metric], f"{first_metric} — peer comparison")
            with right:
                if pill.get("peers"):
                    st.markdown("**Peer comparison**")
                    peer_table(pill["peers"])
                if key == "financial_health" and pill.get("net_cash") is not None:
                    st.metric("Net cash / (debt)", fmt_money(pill["net_cash"], cur))
                if key == "forward_signals":
                    st.metric("Analyst rec.", (pill.get("recommendation") or "n/a"))
                    st.metric("Mean target", fmt_money(pill.get("target_mean_price"), cur))
                    if pill.get("implied_upside_pct") is not None:
                        st.metric("Implied upside", f"{pill['implied_upside_pct']}%")
                    if pill.get("short_percent_float") is not None:
                        st.metric("Short % float", f"{pill['short_percent_float']}%")
            if nar.get("interpretation"):
                st.markdown(f"**Analyst read:** {nar['interpretation']}")
            for w in nar.get("watch_items", []) or []:
                st.markdown(f"- :warning: {w}")

    # Deck prompt
    if narrative and narrative.get("deck_prompt"):
        st.markdown("### Claude Design deck prompt")
        st.caption("Copy this into Claude Design to generate the full presentation.")
        st.code(narrative["deck_prompt"], language="markdown")
        st.download_button(
            "Download deck prompt",
            narrative["deck_prompt"],
            file_name=f"{t['ticker']}_deck_prompt.md",
        )

    st.divider()
    st.caption(
        "Educational fundamental research, not personalized investment advice. "
        f"Figures as of {analysis['as_of']} via yfinance; verify against primary "
        "filings before acting. 'Peer median' = median of the shown peers only."
    )


def run_research(ticker, manual_comps, api_key, model, use_llm):
    try:
        with st.spinner("Resolving company & competitors..."):
            target = fetch_company(ticker)
            if not target.get("price") and not target.get("revenue"):
                st.error(f"Could not find usable data for '{ticker}'. Check the symbol.")
                return
            comps = manual_comps
            if not comps:
                if use_llm and api_key:
                    comps = llm.resolve_competitors(target, model, api_key)
                else:
                    st.warning("No competitors given and LLM is off. Add competitors "
                               "in the sidebar for peer comparison.")
        with st.spinner("Pulling fundamentals & building pillars..."):
            analysis = build_analysis(ticker, comps)

        narrative = None
        if use_llm and api_key:
            with st.spinner("Claude is writing the analysis & deck prompt..."):
                try:
                    narrative = llm.generate_narrative(analysis, model, api_key)
                except Exception as e:  # noqa: BLE001
                    st.warning(f"LLM narrative failed ({e}). Showing data-only results.")

        render(analysis, narrative)
    except Exception as e:  # noqa: BLE001
        st.error(f"Analysis failed: {e}")
        st.exception(e)


def run_infographic(primary, compare, api_key, model, use_llm, force, brand, handle, period):
    try:
        tickers = [primary] + ([compare] if compare else [])
        bundles = []
        cache_notes = []
        for tk in tickers:
            with st.spinner(f"Fetching {tk} (checking cache)..."):
                data, from_cache, fetched_at = cache.get_or_fetch(tk, fetch_full, force=force)
            if not data.get("price") and not data.get("revenue"):
                st.error(f"Could not find usable data for '{tk}'. Check the symbol.")
                return
            bundles.append(data)
            when = (fetched_at or "")[:19].replace("T", " ")
            cache_notes.append(f"**{tk}**: {'cached' if from_cache else 'fetched'} ({when} UTC)")

        # Auto-pick a comparison ticker if only one was given and LLM is available.
        if len(bundles) == 1 and not compare and use_llm and api_key:
            with st.spinner("Picking a competitor via Claude..."):
                try:
                    picks = llm.resolve_competitors(bundles[0], model, api_key)
                    if picks:
                        data, from_cache, fetched_at = cache.get_or_fetch(picks[0], fetch_full, force=force)
                        bundles.append(data)
                        when = (fetched_at or "")[:19].replace("T", " ")
                        cache_notes.append(f"**{picks[0]}** (auto): {'cached' if from_cache else 'fetched'} ({when} UTC)")
                except Exception:
                    pass

        with st.spinner("Rendering infographic..."):
            spec = build_spec(bundles, period=period, brand=brand or "Gabi Album",
                              handle=handle or "")
            key = "_".join(b.get("ticker", "X") for b in bundles)
            out_path = str(cache.infographic_path(key))
            build_infographic(spec, out_path)

        st.image(out_path, use_container_width=True)
        st.caption(" · ".join(cache_notes))
        with open(out_path, "rb") as fh:
            st.download_button("Download infographic (PNG)", fh.read(),
                               file_name=f"{key}_infographic.png", mime="image/png")
        st.caption("Educational research, not investment advice. Data via yfinance; "
                   "free quarterly history is limited, so some panels may show few points.")
    except Exception as e:  # noqa: BLE001
        st.error(f"Infographic failed: {e}")
        st.exception(e)


def main():
    st.title(":chart_with_upwards_trend: Stock Analysis Dashboard")

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input(
            "Anthropic API key", value=llm.get_api_key() or "", type="password",
            help="Needed for the analyst narrative & deck prompt, and competitor auto-pick.",
        )
        model = st.text_input(
            "Claude model", value=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            help="Use a model your key supports.",
        )
        use_llm = st.toggle("Use Claude (narrative / auto-pick)", value=bool(api_key))
        st.divider()
        st.subheader("Infographic branding")
        brand = st.text_input("Brand footer", value="Gabi Album")
        handle = st.text_input("Handle / period (right footer)", value="")
        st.divider()
        st.caption("Data: yfinance (free, cached locally for 24h). Narrative: your Anthropic key.")

    mode = st.radio("Mode", ["Research (single ticker)", "Infographic (compare tickers)"],
                    horizontal=True)

    if mode.startswith("Research"):
        comp_override = st.text_input(
            "Competitors (optional)", placeholder="e.g. MSFT, GOOGL",
            help="Comma-separated tickers. Leave blank to let Claude pick.",
        )
        ticker = st.text_input("Ticker or symbol", placeholder="e.g. NVDA").strip().upper()
        run = st.button("Analyze", type="primary", disabled=not ticker)
        if not run:
            st.info("Pulls real fundamentals, builds the five pillars, and (with an "
                    "Anthropic key) writes the analyst thesis + a Claude Design deck prompt.")
            return
        manual_comps = [c.strip().upper() for c in comp_override.split(",") if c.strip()]
        run_research(ticker, manual_comps, api_key, model, use_llm)
    else:
        c1, c2 = st.columns(2)
        primary = c1.text_input("Primary ticker", placeholder="e.g. ORCL").strip().upper()
        compare = c2.text_input("Compare with (optional)", placeholder="e.g. MSFT").strip().upper()
        period = st.text_input("Period label (footer)", placeholder="e.g. Q2'26").strip()
        force = st.checkbox("Force refresh (ignore cache)", value=False)
        run = st.button("Generate infographic", type="primary", disabled=not primary)
        if not run:
            st.info("Enter one ticker for a single-company infographic, or two for a "
                    "head-to-head comparison (like the reference). Leave the second blank "
                    "and Claude will pick a competitor. Data is cached locally for 24h.")
            return
        run_infographic(primary, compare, api_key, model, use_llm, force, brand, handle, period)


if __name__ == "__main__":
    main()
