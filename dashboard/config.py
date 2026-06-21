"""Central configuration: the single source of truth for branding, the LLM
model, data-fetch limits, cache policy, and the color palette.

Import constants from here instead of hard-coding values in each module.

Note: Streamlit reads its theme from ``.streamlit/config.toml`` at startup and
cannot import this module, so the few colors there must be kept in sync with the
palette below (they derive from PRIMARY / BG_DARK / TEXT).
"""
from __future__ import annotations

import os

# --------------------------------------------------------------------------- #
# Branding
# --------------------------------------------------------------------------- #
BRAND = "Gabi Album"
HANDLE = ""

# --------------------------------------------------------------------------- #
# LLM (Anthropic)
# --------------------------------------------------------------------------- #
API_KEY_ENV = "ANTHROPIC_API_KEY"
MODEL_ENV = "ANTHROPIC_MODEL"
DEFAULT_MODEL = os.environ.get(MODEL_ENV, "claude-3-5-sonnet-latest")

# --------------------------------------------------------------------------- #
# Data fetch
# --------------------------------------------------------------------------- #
MAX_QUARTERS = 12   # quarters pulled from the yfinance statements
ANNUAL_YEARS = 5    # fiscal years pulled for the annual series

# --------------------------------------------------------------------------- #
# Cache policy
# --------------------------------------------------------------------------- #
CACHE_TTL_HOURS = 24
MAX_QUARTERS_KEPT = 40   # cap on merged quarterly history
MAX_ANNUAL_KEPT = 12     # cap on merged annual history

# --------------------------------------------------------------------------- #
# Color palette
# --------------------------------------------------------------------------- #
PRIMARY = "#e8552d"   # brand orange (target / accent)
WHITE = "#ffffff"
BG_DARK = "#0a0a0a"
TEXT = "#f2f2f2"      # plotly text
MUTED = "#8a8a8a"
GRID = "#222"
DIVIDER = "#2a2a2a"
NEUTRAL = "#57606a"   # fallback badge color
LABEL_MUTED = "#9aa0a6"

# Plotly research charts
CHART_PALETTE = [PRIMARY, WHITE, "#4c9be8", "#f0c419", "#9b59b6"]
PEER_COLOR = "#4c9be8"
TARGET_COLOR = PRIMARY
MEDIAN_COLOR = "#9b59b6"

# Infographic (matplotlib)
INFOGRAPHIC_COLORS = [PRIMARY, WHITE, "#4c9be8", "#f0c419"]
INFOGRAPHIC_FG = WHITE

# Status colors for verdict / score badges
STRONG = "#1a7f37"
WARN = "#9a6700"
BAD = "#b42318"
VERDICT_COLORS = {"Strong": STRONG, "Adequate": WARN, "Weak": BAD}
SCORE_COLORS = {"strong": STRONG, "safe": STRONG, "middling": WARN,
                "grey": WARN, "weak": BAD, "distress": BAD}
