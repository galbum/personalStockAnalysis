# Future work

## Dashboard UX simplification (future)
- Hide from the UI: the Anthropic API key input, the Claude model selector, and
  the automatic "compare to competitors" logic (auto-pick + LLM resolution).
  Move API key + model to config/.env only (not user-facing).
- **Keep the manual competitor option** (let the user type competitors explicitly).

## Data source
- Source the data the dashboard needs from TradingView (see data_provider).

## TradingView watchlists -> infographics (future)
- Pull all of the user's watchlists from TradingView (list names + their tickers).
- For each watchlist, generate an infographic per ticker (or per pairing, per the
  infographic modes).
- Output layout:
  - Each watchlist keeps its own infographics in its **own separate folder**
    (e.g. `output/watchlists/<watchlist-name>/`).
  - All generated infographics also live in a single **shared folder** that acts
    as the cache, so when multiple watchlists contain the same ticker the
    infographic is generated once and reused. The per-watchlist folders reference
    (symlink/copy) from the shared cache instead of regenerating.
  - Key the shared cache by ticker (and period/compare-set) so identical requests
    across watchlists hit the cache; respect the existing 24h TTL + force-refresh.
- Reuse the existing pipeline: `fetch-stock-data` -> `stock-infographic`, plus
  `cache.py` for the shared store.
- Note: TradingView watchlists likely need an authenticated API/session - the
  free `tradingview-screener` path used today does not expose user watchlists, so
  scope an auth approach (or manual watchlist input) as part of this.
