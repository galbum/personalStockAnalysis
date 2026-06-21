---
name: dashboard-ux-design
description: Design standards and review checklist for the Streamlit stock dashboard (and similar data-heavy dashboards) - visual hierarchy, theming, chart styling, progressive disclosure, loading/empty states, accessibility, and Streamlit performance patterns. Use when editing the dashboard UI, reviewing its layout or visuals, or when asked to make the dashboard cleaner, more efficient, or better designed.
---

# Dashboard UX Design

Standards for keeping the stock dashboard clean, fast, and legible. Apply these
when changing `dashboard/app.py` or its visuals. Senior-designer default: reduce
what's on screen, increase clarity, make state and feedback obvious.

## Principles

1. **Hierarchy first.** One clear focal point per view (the verdict/scorecard or
   the infographic). Everything else is secondary and visually quieter.
2. **Progressive disclosure.** Show the summary; hide depth behind tabs/expanders.
   Never make the user scroll a wall of charts to find the takeaway.
3. **Consistency.** One palette, one type scale, one chart style everywhere.
   Company A is always the same color across every chart and the infographic.
4. **Feedback.** Every wait shows staged progress; every error is human-readable
   and actionable; every empty state explains the next step.
5. **Accessibility.** WCAG-AA contrast, color never the only signal (pair with
   icon/label), alt text on images, readable default font sizes.

## Theme (drop-in)

Create `dashboard/.streamlit/config.toml`:

```toml
[theme]
base = "dark"
primaryColor = "#e8552d"
backgroundColor = "#0a0a0a"
secondaryBackgroundColor = "#161616"
textColor = "#f2f2f2"
font = "sans serif"
```

## Layout spec for this dashboard

- **Sticky summary:** header (company, price, as-of) + 5-pillar scorecard stay at
  the top of Research mode.
- **Tabs, not one long scroll:** `Overview | Pillars | Thesis | Deck prompt`.
  Use `st.tabs([...])`.
- **Cards:** group related metrics in `st.container(border=True)` instead of bare
  `st.metric` rows.
- **Recent tickers:** read `cache/data/` and render the last N tickers as quick
  buttons for one-click re-analysis.
- **Mode switch keeps state:** persist inputs in `st.session_state` so switching
  Research <-> Infographic doesn't clear them.

## Chart styling (Plotly)

Apply one template so research charts match the infographic aesthetic:

```python
import plotly.graph_objects as go
import plotly.io as pio

pio.templates["equity"] = go.layout.Template(layout=dict(
    paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
    font=dict(color="#f2f2f2", size=12),
    colorway=["#e8552d", "#ffffff", "#4c9be8", "#f0c419"],
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(gridcolor="#222", zeroline=False),
    margin=dict(l=10, r=10, t=40, b=10),
    hovermode="x unified", legend=dict(orientation="h", y=1.04, x=0),
))
```

Set `template="equity"`, fixed heights (~320px), label the last point, and drop
chart junk (no heavy gridlines, no redundant legends).

## Feedback patterns

- Replace stacked spinners with one `st.status("Analyzing...")` that logs stages:
  Resolving -> Fetching (cache/live) -> Pillars -> Narrative.
- Show cache provenance inline ("AAPL: cached 2026-06-21 14:02 UTC").
- Validate tickers before fetch; show a friendly error, not a stack trace.

## Performance / efficiency

- Wrap pure fetches in `@st.cache_data(ttl=...)` so reruns don't re-hit the network.
- Keep computed results in `st.session_state`; recompute only on new input or
  Force refresh.
- Render heavy sections (deck prompt, all pillar charts) only when their tab is open.

## Review checklist

- [ ] One clear focal point; secondary content is quieter
- [ ] Summary visible without scrolling; depth behind tabs/expanders
- [ ] Single palette + type scale; company colors consistent everywhere
- [ ] Charts use the shared template, fixed heights, last-point labels
- [ ] Staged progress + readable errors + helpful empty states
- [ ] AA contrast; color paired with icon/label; image alt text
- [ ] Fetches cached; results memoized in session_state

## Anti-patterns

- Default Streamlit light theme mixed with the dark infographic.
- A dozen `st.metric`s in a row with no grouping.
- Re-fetching/recomputing on every widget interaction.
- Raw exceptions shown to the user.
