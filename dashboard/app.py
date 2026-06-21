"""Fundamental Analysis Dashboard (Streamlit).

Enter a ticker -> pulls real fundamentals (TradingView + yfinance, optional FMP
deep history) -> computes the five pillars + composite quality scores ->
(optionally) has Claude write the analyst narrative + Claude Design deck prompt.

Dark theme, tabbed layout, staged progress, and cached fetches per the
dashboard-ux-design skill.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
from dotenv import load_dotenv

from analysis import PILLARS, build_analysis
import cache
from charts import line_chart, peer_bar
import config
from data_provider import fetch_company, fetch_price_performance
from infographic import build_infographic
from infographic_data import build_spec
import llm
from utils import fmt_money, fmt_num

load_dotenv()

st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

VERDICT_COLORS = config.VERDICT_COLORS
SCORE_COLORS = config.SCORE_COLORS
PILLAR_LABELS = {
    "profitability": "Profitability",
    "valuation": "Valuation",
    "cash_flow": "Cash Flow",
    "financial_health": "Financial Health",
    "forward_signals": "Forward Signals",
}


# --------------------------------------------------------------------------- #
# Cached data access (network calls memoized so reruns are instant)
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def cached_company(ticker: str) -> dict:
    return fetch_company(ticker)


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def cached_full(ticker: str) -> dict:
    data = fetch_company(ticker)
    data["price_perf"] = fetch_price_performance(ticker)
    return data


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def cached_analysis(ticker: str, comps: tuple) -> dict:
    return build_analysis(ticker, list(comps))


def fetch_full(ticker: str) -> dict:
    """Used by the on-disk cache (infographics)."""
    return cached_full(ticker)


# --------------------------------------------------------------------------- #
# Badges (fmt_money / fmt_num come from utils)
# --------------------------------------------------------------------------- #
def verdict_badge(label, verdict):
    color = VERDICT_COLORS.get(verdict, config.NEUTRAL)
    st.markdown(
        f"<div style='text-align:center;padding:10px 6px;border-radius:10px;"
        f"background:{color}1a;border:1px solid {color}55;'>"
        f"<div style='font-size:0.8rem;color:{config.LABEL_MUTED};'>{label}</div>"
        f"<div style='font-size:1.05rem;font-weight:700;color:{color};'>{verdict}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def score_badge(label, value, sub, key):
    color = SCORE_COLORS.get(str(key).lower(), config.NEUTRAL)
    st.markdown(
        f"<div style='text-align:center;padding:10px 6px;border-radius:10px;"
        f"background:{color}1a;border:1px solid {color}55;'>"
        f"<div style='font-size:0.8rem;color:{config.LABEL_MUTED};'>{label}</div>"
        f"<div style='font-size:1.3rem;font-weight:700;color:{color};'>{value}</div>"
        f"<div style='font-size:0.72rem;color:{config.LABEL_MUTED};'>{sub}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


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


# --------------------------------------------------------------------------- #
# Render: tabbed research view
# --------------------------------------------------------------------------- #
def render(analysis: dict, narrative: dict | None):
    t = analysis["target"]
    cur = (t.get("currency") or "") and (t.get("currency") + " ")

    # --- Sticky summary: header + scorecard ---
    st.subheader(f"{t['name']} ({t['ticker']})")
    meta = " · ".join(filter(None, [t.get("exchange"), t.get("sector"), t.get("industry")]))
    st.caption(meta or "")

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Price", fmt_money(t.get("price"), cur))
        c2.metric("Market cap", fmt_money(t.get("market_cap"), cur))
        c3.metric("Competitors", ", ".join(analysis["competitors"]) or "n/a")
        c4.metric("As of", analysis["as_of"])

        st.markdown("**Pillar scorecard**")
        cols = st.columns(5)
        for i, key in enumerate(PILLARS):
            pill = analysis["pillars"][key]
            verdict = pill["rule_verdict"]
            if narrative:
                verdict = narrative.get("pillars", {}).get(key, {}).get("verdict", verdict)
            with cols[i]:
                verdict_badge(PILLAR_LABELS[key], verdict)

        # Composite quality scores
        scores = analysis.get("scores") or {}
        pio, alt = scores.get("piotroski"), scores.get("altman")
        if pio or alt:
            sc1, sc2, _ = st.columns([1, 1, 3])
            if pio:
                with sc1:
                    score_badge("Piotroski F", f"{pio['score']}/{pio['max']}",
                                f"{pio['verdict']} · {pio['evaluated']} tests", pio["verdict"])
            if alt:
                with sc2:
                    z = alt.get("z")
                    score_badge("Altman Z", "n/a" if z is None else f"{z}",
                                alt.get("zone", "n/a"), alt.get("zone"))
            with st.expander("What do these scores mean?"):
                st.markdown(
                    "- **Piotroski F-score (0-9):** nine pass/fail checks on "
                    "profitability, leverage/liquidity, and efficiency. **≥7 strong, "
                    "≤2 weak.** Higher = better fundamental quality and improving trend.\n"
                    "- **Altman Z-score:** distress model. **>2.99 safe, 1.81-2.99 grey, "
                    "<1.81 distress.** Built for manufacturers, so read cash-rich tech "
                    "names (very high Z) as orientation, not gospel."
                )
                if pio and pio.get("signals"):
                    passed = [k.replace("_", " ") for k, v in pio["signals"].items() if v]
                    failed = [k.replace("_", " ") for k, v in pio["signals"].items() if v is False]
                    st.caption("Passed: " + (", ".join(passed) or "—"))
                    st.caption("Failed: " + (", ".join(failed) or "—"))

    tabs = st.tabs(["Overview", "Pillars", "Thesis", "Deck prompt"])

    with tabs[0]:
        _tab_overview(analysis, t, cur)
    with tabs[1]:
        _tab_pillars(analysis, narrative, cur)
    with tabs[2]:
        _tab_thesis(narrative)
    with tabs[3]:
        _tab_deck(narrative, t)

    st.divider()
    src = analysis.get("data_source", "yfinance")
    hq = analysis.get("history_quarters") or 0
    depth = "deep (FMP)" if "fmp" in str(src) else (f"shallow — {hq}q free; set FMP_API_KEY for ~5y")
    st.caption(
        "Educational fundamental research, not personalized investment advice. "
        f"Source: {src}; history: {depth}; figures as of {analysis['as_of']}. "
        "Verify against primary filings before acting."
    )


def _tab_overview(analysis, t, cur):
    if t.get("summary"):
        with st.expander("Business summary", expanded=False):
            st.write(t["summary"])

    raw = analysis.get("raw", {}).get("target", {})
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("FCF yield", fmt_num(raw.get("fcf_yield"), "%"))
    r40 = raw.get("rule_of_40")
    k2.metric("Rule of 40", "n/a" if r40 is None else f"{r40}",
              help="Revenue growth % + FCF margin %. ≥40 is the software bar.")
    k3.metric("Net debt/EBITDA", fmt_num(raw.get("net_debt_to_ebitda"), "x"))
    k4.metric("Interest coverage", fmt_num(raw.get("interest_coverage"), "x"))

    g1, g2, g3, g4 = st.columns(4)
    rc, rcy = raw.get("rev_cagr"), raw.get("rev_cagr_years")
    fc, fcy = raw.get("fcf_cagr"), raw.get("fcf_cagr_years")
    g1.metric(f"Revenue CAGR ({rcy or '?'}y)", fmt_num(rc, "%"))
    g2.metric(f"FCF CAGR ({fcy or '?'}y)", fmt_num(fc, "%"))
    g3.metric("Net buyback yield", fmt_num(raw.get("net_buyback_yield"), "%"),
              help="Annual reduction in diluted share count. Negative = dilution.")
    g4.metric("Shareholder yield", fmt_num(raw.get("shareholder_yield"), "%"),
              help="Dividend yield + net buyback yield.")

    prof = analysis["pillars"]["profitability"]
    cf = analysis["pillars"]["cash_flow"]
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("**Revenue & margins**")
            line_chart(
                {"labels": prof["series"]["labels"],
                 "Revenue YoY %": prof["series"]["Revenue YoY %"],
                 "Gross margin %": prof["series"]["Gross margin %"],
                 "Operating margin %": prof["series"]["Operating margin %"]},
                "", value_suffix="%",
            )
    with right:
        with st.container(border=True):
            st.markdown("**Cash flow quality**")
            line_chart(
                {"labels": cf["series"]["labels"],
                 "FCF margin %": cf["series"]["FCF margin %"],
                 "FCF margin ex-SBC %": cf["series"].get("FCF margin ex-SBC %")},
                "", value_suffix="%",
            )
            sbc_rev, sbc_fcf = cf.get("sbc_pct_revenue"), cf.get("sbc_pct_fcf")
            if sbc_rev is not None or sbc_fcf is not None:
                m1, m2 = st.columns(2)
                m1.metric("SBC / revenue", fmt_num(sbc_rev, "%"))
                m2.metric("SBC / FCF", fmt_num(sbc_fcf, "%"))


def _tab_pillars(analysis, narrative, cur):
    for key in PILLARS:
        pill = analysis["pillars"][key]
        nar = (narrative or {}).get("pillars", {}).get(key, {})
        with st.expander(f"{PILLAR_LABELS[key]} — {nar.get('verdict', pill['rule_verdict'])}",
                         expanded=(key == "profitability")):
            left, right = st.columns([3, 2])
            with left:
                if pill.get("series"):
                    line_chart(pill["series"], f"{PILLAR_LABELS[key]} trend")
                if pill.get("peers"):
                    first_metric = next(iter(pill["peers"]))
                    peer_bar(pill["peers"][first_metric], f"{first_metric} — peers",
                             target_ticker=analysis["target"]["ticker"])
            with right:
                if pill.get("peers"):
                    st.markdown("**Peer comparison**")
                    peer_table(pill["peers"])
                if key == "cash_flow":
                    if pill.get("sbc_pct_fcf") is not None:
                        st.metric("SBC / FCF", fmt_num(pill["sbc_pct_fcf"], "%"))
                if key == "financial_health":
                    if pill.get("net_cash") is not None:
                        st.metric("Net cash / (debt)", fmt_money(pill["net_cash"], cur))
                    if pill.get("net_debt_to_ebitda") is not None:
                        st.metric("Net debt/EBITDA", fmt_num(pill["net_debt_to_ebitda"], "x"))
                    if pill.get("interest_coverage") is not None:
                        st.metric("Interest coverage", fmt_num(pill["interest_coverage"], "x"))
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


def _tab_thesis(narrative):
    if not (narrative and narrative.get("thesis")):
        st.info("Turn on Claude in the sidebar (and add an API key) to generate the "
                "investment thesis, bull/bear case, and key risks.")
        return
    th = narrative["thesis"]
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


def _tab_deck(narrative, t):
    if not (narrative and narrative.get("deck_prompt")):
        st.info("Turn on Claude in the sidebar to generate a Claude Design deck prompt.")
        return
    st.caption("Copy this into Claude Design to generate the full presentation.")
    st.code(narrative["deck_prompt"], language="markdown")
    st.download_button("Download deck prompt", narrative["deck_prompt"],
                       file_name=f"{t['ticker']}_deck_prompt.md")


# --------------------------------------------------------------------------- #
# Mode runners
# --------------------------------------------------------------------------- #
def run_research(ticker, manual_comps, api_key, model, use_llm):
    try:
        with st.status(f"Analyzing {ticker}…", expanded=True) as status:
            st.write("Resolving company…")
            target = cached_company(ticker)
            if not target.get("price") and not target.get("revenue"):
                status.update(label="No data found", state="error")
                st.error(f"Could not find usable data for '{ticker}'. Check the symbol.")
                return

            # Persist the company bundle to the durable per-ticker store so the
            # data (and its long-lived history) is reusable across sessions.
            cache.save_data(ticker, target)
            cstat = cache.cache_status(ticker)
            if cstat.get("exists"):
                when = (cstat.get("fetched_at") or "")[:19].replace("T", " ")
                depth = cstat.get("history_depth")
                n = cstat.get("fetch_count")
                extra = f" · {depth}q history · seen {n}x" if depth else ""
                st.write(f"Cache: {ticker} last fetched {when} UTC{extra}")

            comps = manual_comps
            if not comps and use_llm and api_key:
                st.write("Picking competitors via Claude…")
                comps = llm.resolve_competitors(target, model, api_key)
            elif not comps:
                st.write("No competitors given (add some in the sidebar for peers).")

            st.write("Pulling fundamentals & building pillars…")
            analysis = cached_analysis(ticker, tuple(comps))

            narrative = None
            if use_llm and api_key:
                st.write("Claude is writing the thesis & deck prompt…")
                try:
                    narrative = llm.generate_narrative(analysis, model, api_key)
                except Exception as e:  # noqa: BLE001
                    st.warning(f"LLM narrative failed ({e}). Showing data-only results.")
            status.update(label=f"{ticker} analysis ready", state="complete", expanded=False)

        cache.record_search("research", [ticker], {"competitors": comps})
        st.session_state["last_research"] = (analysis, narrative)
        render(analysis, narrative)
    except Exception as e:  # noqa: BLE001
        st.error(f"Analysis failed for '{ticker}': {e}")


def run_infographic(primary, compare, api_key, model, use_llm, force, brand, handle, period):
    try:
        tickers = [primary] + ([compare] if compare else [])
        bundles, cache_notes = [], []
        with st.status("Building infographic…", expanded=True) as status:
            st.write(f"Fetching {', '.join(tickers)} concurrently (checking cache)…")

            def _one(tk):
                return (tk,) + cache.get_or_fetch(tk, fetch_full, force=force)

            with ThreadPoolExecutor(max_workers=min(4, len(tickers))) as ex:
                results = list(ex.map(_one, tickers))
            for tk, data, from_cache, fetched_at in results:
                if not data.get("price") and not data.get("revenue"):
                    status.update(label="No data found", state="error")
                    st.error(f"Could not find usable data for '{tk}'. Check the symbol.")
                    return
                bundles.append(data)
                when = (fetched_at or "")[:19].replace("T", " ")
                cache_notes.append(f"**{tk}**: {'cached' if from_cache else 'fetched'} ({when} UTC)")

            if len(bundles) == 1 and not compare and use_llm and api_key:
                st.write("Picking a competitor via Claude…")
                try:
                    picks = llm.resolve_competitors(bundles[0], model, api_key)
                    if picks:
                        data, from_cache, fetched_at = cache.get_or_fetch(picks[0], fetch_full, force=force)
                        bundles.append(data)
                        when = (fetched_at or "")[:19].replace("T", " ")
                        cache_notes.append(f"**{picks[0]}** (auto): {'cached' if from_cache else 'fetched'} ({when} UTC)")
                except Exception:
                    pass

            st.write("Rendering infographic…")
            spec = build_spec(bundles, period=period, brand=brand or config.BRAND, handle=handle or "")
            bundle_tickers = [b.get("ticker", "X") for b in bundles]
            key = "_".join(bundle_tickers)
            out_path = str(cache.infographic_path(key))
            build_infographic(spec, out_path)
            cache.register_infographic(key, bundle_tickers, period=period,
                                       brand=brand or config.BRAND, path=out_path)
            cache.record_search("infographic", bundle_tickers, {"period": period})
            status.update(label="Infographic ready", state="complete", expanded=False)

        alt = "Stock comparison infographic: " + " vs ".join(b.get("ticker", "?") for b in bundles)
        st.image(out_path, use_container_width=True, caption=alt)
        st.caption(" · ".join(cache_notes))
        with open(out_path, "rb") as fh:
            st.download_button("Download infographic (PNG)", fh.read(),
                               file_name=f"{key}_infographic.png", mime="image/png")
    except Exception as e:  # noqa: BLE001
        st.error(f"Infographic failed: {e}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    st.title(":chart_with_upwards_trend: Stock Analysis Dashboard")

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input(
            "Anthropic API key", value=llm.get_api_key() or "", type="password",
            help="Needed for the analyst narrative & deck prompt, and competitor auto-pick.",
        )
        model = st.text_input(
            "Claude model", value=config.DEFAULT_MODEL,
            help="Use a model your key supports.",
        )
        use_llm = st.toggle("Use Claude (narrative / auto-pick)", value=bool(api_key))
        st.divider()
        st.subheader("Infographic branding")
        brand = st.text_input("Brand footer", value=config.BRAND)
        handle = st.text_input("Handle / period (right footer)", value="")
        st.divider()
        deep = "on" if os.environ.get("FMP_API_KEY") else "off (set FMP_API_KEY for 5y history)"
        st.caption(f"Data: TradingView + yfinance, cached 24h. Deep history (FMP): {deep}. "
                   "Narrative: your Anthropic key.")

        st.divider()
        with st.expander("History & saved", expanded=False):
            searches = cache.recent_searches(limit=10)
            if searches:
                st.caption("Recent searches")
                for ev in searches:
                    icon = "📈" if ev.get("kind") == "research" else "🖼️"
                    label = " / ".join(ev.get("tickers", [])) or "?"
                    when = (ev.get("ts") or "")[:16].replace("T", " ")
                    st.write(f"{icon} **{label}** · {when}")
            else:
                st.caption("No searches recorded yet.")

            infos = cache.recent_infographics(limit=6)
            if infos:
                st.caption("Saved infographics")
                for e in infos:
                    st.write(f"🖼️ {' vs '.join(e.get('tickers', []))}"
                             + (f" · {e['period']}" if e.get("period") else "")
                             + (f" · x{e['count']}" if e.get("count", 0) > 1 else ""))

    mode = st.radio("Mode", ["Research (single ticker)", "Infographic (compare tickers)"],
                    horizontal=True, key="mode")

    if mode.startswith("Research"):
        comp_override = st.text_input(
            "Competitors (optional)", placeholder="e.g. MSFT, GOOGL", key="research_comps",
            help="Comma-separated tickers. Leave blank to let Claude pick (if enabled).",
        )
        ticker = st.text_input("Ticker or symbol", placeholder="e.g. NVDA", key="research_ticker").strip().upper()

        recents = cache.recent_tickers()
        if recents:
            st.caption("Recent:")
            rcols = st.columns(min(len(recents), 8))
            for i, rt in enumerate(recents[:8]):
                if rcols[i].button(rt, key=f"recent_{rt}"):
                    st.session_state["research_ticker"] = rt
                    st.rerun()

        run = st.button("Analyze", type="primary", disabled=not ticker)
        if not run:
            st.info("Pulls real fundamentals, builds the five pillars + Piotroski/Altman "
                    "scores, and (with an Anthropic key) writes the thesis + deck prompt.")
            return
        manual_comps = [c.strip().upper() for c in comp_override.split(",") if c.strip()]
        run_research(ticker, manual_comps, api_key, model, use_llm)
    else:
        c1, c2 = st.columns(2)
        primary = c1.text_input("Primary ticker", placeholder="e.g. ORCL", key="info_primary").strip().upper()
        compare = c2.text_input("Compare with (optional)", placeholder="e.g. MSFT", key="info_compare").strip().upper()
        period = st.text_input("Period label (footer)", placeholder="e.g. Q2'26", key="info_period").strip()
        force = st.checkbox("Force refresh (ignore cache)", value=False, key="info_force")

        if primary:
            saved = cache.infographics_for_ticker(primary)
            if saved:
                with st.expander(f"Previously generated for {primary} ({len(saved)})", expanded=False):
                    for e in saved[:6]:
                        st.image(e["path"], use_container_width=True,
                                 caption=f"{' vs '.join(e['tickers'])}"
                                         + (f" · {e['period']}" if e.get("period") else "")
                                         + f" · {(e.get('updated_at') or '')[:10]}")

        run = st.button("Generate infographic", type="primary", disabled=not primary)
        if not run:
            st.info("Enter one ticker for a single-company infographic, or two for a "
                    "head-to-head comparison. Leave the second blank and Claude will pick "
                    "a competitor (if enabled). Data is cached locally for 24h.")
            return
        run_infographic(primary, compare, api_key, model, use_llm, force, brand, handle, period)


if __name__ == "__main__":
    main()
