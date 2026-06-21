"""Durable local cache for ticker data, infographics, and search history.

Layout (v2)::

    cache/
      tickers/<TICKER>/
        latest.json       # newest full bundle + metadata (first_seen, fetch_count…)
        snapshots.jsonl    # append-only log of volatile fields (price, multiples…)
      infographics/
        <KEY>.png          # rendered image (canonical)
        index.json         # registry: key -> {tickers, period, brand, path, counts, ts}
      history/
        events.jsonl       # append-only log of research / infographic requests

Design goals
------------
* **Reuse**: asking for the same ticker again serves the stored bundle while it
  is younger than the TTL; an expired entry or a forced refresh re-fetches.
* **Permanence**: period-keyed time series (revenue per quarter, etc.) never
  change once reported, so on every save we *merge* fresh data into the stored
  series. Deep history (e.g. an earlier FMP pull) survives later shallow fetches.
* **Record-keeping**: every search and every generated infographic is logged so
  the UI can surface recent activity and saved infographics.

Backward compatible with the old flat ``cache/data/<TICKER>.json`` files (read
as a fallback). Public function names are unchanged.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Optional

from config import CACHE_TTL_HOURS, MAX_ANNUAL_KEPT, MAX_QUARTERS_KEPT

CACHE_DIR = Path(__file__).resolve().parent / "cache"
TICKERS_DIR = CACHE_DIR / "tickers"
IMG_DIR = CACHE_DIR / "infographics"
HISTORY_DIR = CACHE_DIR / "history"
LEGACY_DATA_DIR = CACHE_DIR / "data"  # pre-v2 flat files

IMG_INDEX = IMG_DIR / "index.json"
EVENTS_LOG = HISTORY_DIR / "events.jsonl"

TTL_HOURS = CACHE_TTL_HOURS

# Volatile fields snapshotted on every fetch (build a price/valuation history).
SNAPSHOT_FIELDS = (
    "price", "market_cap", "pe", "forward_pe", "ps", "ev_ebitda", "peg", "pb",
    "dividend_yield", "recommendation", "target_mean_price", "roe", "roa",
    "fcf_yield", "rule_of_40",
)

# Period-keyed time-series groups: label array -> metric arrays aligned to it.
# Merging by period label preserves long-lived history across fetches.
SERIES_GROUPS = {
    "quarters": [
        "revenue", "rev_yoy", "gross_margin", "op_margin", "net_margin", "ebitda",
        "ebitda_margin", "net_income", "ocf", "capex", "capex_growth", "fcf",
        "fcf_margin", "sbc_series", "fcf_ex_sbc", "fcf_ex_sbc_margin", "ocf_to_ni",
    ],
    "bs_quarters": ["total_debt_series"],
    "annual_labels": ["revenue_annual", "rev_yoy_annual", "net_margin_annual", "shares_annual"],
    "annual_cf_labels": ["fcf_annual", "capex_growth_annual"],
    "annual_bs_labels": ["total_debt_annual"],
}


# --------------------------------------------------------------------------- #
# Paths / time helpers
# --------------------------------------------------------------------------- #
def _ensure_dirs() -> None:
    TICKERS_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _norm(ticker: str) -> str:
    return ticker.strip().upper()


def ticker_dir(ticker: str) -> Path:
    return TICKERS_DIR / _norm(ticker)


def data_path(ticker: str) -> Path:
    """Path to the newest stored bundle for a ticker."""
    return ticker_dir(ticker) / "latest.json"


def snapshots_path(ticker: str) -> Path:
    return ticker_dir(ticker) / "snapshots.jsonl"


def infographic_path(key: str) -> Path:
    return IMG_DIR / f"{key}.png"


def is_fresh(fetched_at: Optional[str], ttl_hours: int = TTL_HOURS) -> bool:
    if not fetched_at:
        return False
    try:
        ts = dt.datetime.fromisoformat(fetched_at)
    except ValueError:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    return (_now() - ts) < dt.timedelta(hours=ttl_hours)


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Time-series merge (keep long-lived history across fetches)
# --------------------------------------------------------------------------- #
def _merge_group(new: dict, old: dict, label_key: str, metrics: list, cap: int) -> None:
    """Extend `new`'s series for one group with older periods from `old`.

    Periods are keyed by their label (e.g. "2024-03"); newer values win, but
    periods only present in the stored history are carried forward.
    """
    old_labels = old.get(label_key) or []
    new_labels = new.get(label_key) or []
    if not old_labels:
        return  # nothing to add
    combined = sorted(set(map(str, old_labels)) | set(map(str, new_labels)))
    if cap and len(combined) > cap:
        combined = combined[-cap:]

    def aligned(metric: str) -> list:
        old_map = dict(zip(map(str, old_labels), old.get(metric) or []))
        new_map = dict(zip(map(str, new_labels), new.get(metric) or []))
        out = []
        for lab in combined:
            nv = new_map.get(lab)
            out.append(nv if nv is not None else old_map.get(lab, nv))
        return out

    new[label_key] = combined
    for m in metrics:
        if m in old or m in new:
            new[m] = aligned(m)


def merge_bundle(new: dict, old: Optional[dict]) -> dict:
    """Return `new` enriched with any deeper period history from `old`.

    Scalars (price, multiples, scores…) stay as freshly fetched; only the
    period-keyed series are extended.
    """
    if not old:
        return new
    for label_key, metrics in SERIES_GROUPS.items():
        cap = MAX_QUARTERS_KEPT if "quarter" in label_key else MAX_ANNUAL_KEPT
        _merge_group(new, old, label_key, metrics, cap)
    new["history_quarters"] = len(new.get("quarters") or [])
    return new


# --------------------------------------------------------------------------- #
# Per-ticker data store
# --------------------------------------------------------------------------- #
def load_data(ticker: str, ttl_hours: int = TTL_HOURS) -> Optional[dict]:
    """Return the stored bundle if present and fresh, else None.

    Reads the v2 ``latest.json`` first, falling back to the legacy flat file.
    """
    payload = _read_json(data_path(ticker)) or _read_json(LEGACY_DATA_DIR / f"{_norm(ticker)}.json")
    if not payload:
        return None
    if not is_fresh(payload.get("fetched_at"), ttl_hours):
        return None
    return payload.get("data")


def load_stored(ticker: str) -> Optional[dict]:
    """Return the stored bundle regardless of freshness (for history merging)."""
    payload = _read_json(data_path(ticker)) or _read_json(LEGACY_DATA_DIR / f"{_norm(ticker)}.json")
    return payload.get("data") if payload else None


def save_data(ticker: str, data: dict) -> str:
    """Persist a bundle, merging long-lived series and logging a snapshot.

    Returns the ISO timestamp it was stored at.
    """
    _ensure_dirs()
    tk = _norm(ticker)
    tdir = ticker_dir(tk)
    tdir.mkdir(parents=True, exist_ok=True)

    prior = _read_json(data_path(tk))
    merged = merge_bundle(dict(data), load_stored(tk))

    fetched_at = _now().isoformat()
    first_seen = (prior or {}).get("first_seen") or fetched_at
    fetch_count = int((prior or {}).get("fetch_count") or 0) + 1
    payload = {
        "ticker": tk,
        "fetched_at": fetched_at,
        "first_seen": first_seen,
        "fetch_count": fetch_count,
        "history_depth": len(merged.get("quarters") or []),
        "data_source": merged.get("data_source"),
        "data": merged,
    }
    data_path(tk).write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")

    # Append a compact snapshot of the volatile fields.
    snap = {"ts": fetched_at}
    for f in SNAPSHOT_FIELDS:
        if data.get(f) is not None:
            snap[f] = data.get(f)
    with snapshots_path(tk).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(snap, default=str) + "\n")

    return fetched_at


def cache_status(ticker: str) -> dict:
    """Describe the stored entry for the UI."""
    payload = _read_json(data_path(ticker)) or _read_json(LEGACY_DATA_DIR / f"{_norm(ticker)}.json")
    if not payload:
        return {"exists": False, "fetched_at": None, "fresh": False}
    fetched_at = payload.get("fetched_at")
    return {
        "exists": True,
        "fetched_at": fetched_at,
        "fresh": is_fresh(fetched_at),
        "first_seen": payload.get("first_seen"),
        "fetch_count": payload.get("fetch_count"),
        "history_depth": payload.get("history_depth"),
    }


def get_or_fetch(ticker: str, fetch_fn, force: bool = False, ttl_hours: int = TTL_HOURS):
    """Return (data, from_cache, fetched_at). Fetches & stores on miss/force."""
    if not force:
        cached = load_data(ticker, ttl_hours)
        if cached is not None:
            return cached, True, cache_status(ticker)["fetched_at"]
    data = fetch_fn(ticker)
    fetched_at = save_data(ticker, data)
    # save_data merges history, so return the stored (merged) view.
    stored = load_stored(ticker) or data
    return stored, False, fetched_at


def recent_tickers(limit: int = 8) -> list:
    """Most-recently fetched tickers (newest first), v2 store + legacy."""
    seen, out = set(), []
    entries = []
    if TICKERS_DIR.exists():
        for d in TICKERS_DIR.iterdir():
            latest = d / "latest.json"
            if latest.exists():
                entries.append((latest.stat().st_mtime, d.name))
    if LEGACY_DATA_DIR.exists():
        for p in LEGACY_DATA_DIR.glob("*.json"):
            entries.append((p.stat().st_mtime, p.stem))
    for _, name in sorted(entries, key=lambda e: e[0], reverse=True):
        if name not in seen:
            seen.add(name)
            out.append(name)
        if len(out) >= limit:
            break
    return out


def snapshot_history(ticker: str, limit: int = 200) -> list:
    """Return the stored volatile-field snapshots (oldest -> newest)."""
    path = snapshots_path(ticker)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows[-limit:]


# --------------------------------------------------------------------------- #
# Infographic registry
# --------------------------------------------------------------------------- #
def save_infographic(key: str, png_bytes: bytes) -> Path:
    _ensure_dirs()
    path = infographic_path(key)
    path.write_bytes(png_bytes)
    return path


def register_infographic(key: str, tickers: list, period: str = "",
                         brand: str = "", path: Optional[str] = None) -> None:
    """Record (or update) an infographic in the registry index."""
    _ensure_dirs()
    index = _read_json(IMG_INDEX) or {}
    now = _now().isoformat()
    entry = index.get(key) or {}
    index[key] = {
        "key": key,
        "tickers": [t.upper() for t in tickers if t],
        "period": period,
        "brand": brand,
        "path": path or str(infographic_path(key)),
        "created_at": entry.get("created_at", now),
        "updated_at": now,
        "count": int(entry.get("count", 0)) + 1,
    }
    IMG_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")


def recent_infographics(limit: int = 8) -> list:
    """Registry entries, most-recently generated first."""
    index = _read_json(IMG_INDEX) or {}
    entries = [e for e in index.values() if Path(e.get("path", "")).exists()]
    entries.sort(key=lambda e: e.get("updated_at", ""), reverse=True)
    return entries[:limit]


def infographics_for_ticker(ticker: str) -> list:
    """All registered infographics that feature `ticker`."""
    tk = _norm(ticker)
    index = _read_json(IMG_INDEX) or {}
    out = [e for e in index.values() if tk in e.get("tickers", []) and Path(e.get("path", "")).exists()]
    out.sort(key=lambda e: e.get("updated_at", ""), reverse=True)
    return out


# --------------------------------------------------------------------------- #
# Search-history log
# --------------------------------------------------------------------------- #
def record_search(kind: str, tickers: list, params: Optional[dict] = None,
                  note: str = "") -> None:
    """Append a search/generation event to the history log."""
    _ensure_dirs()
    event = {
        "ts": _now().isoformat(),
        "kind": kind,  # "research" | "infographic"
        "tickers": [t.upper() for t in tickers if t],
        "params": params or {},
        "note": note,
    }
    with EVENTS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, default=str) + "\n")


def recent_searches(limit: int = 10, dedupe: bool = True) -> list:
    """Most-recent search events (newest first)."""
    if not EVENTS_LOG.exists():
        return []
    lines = EVENTS_LOG.read_text(encoding="utf-8").splitlines()
    events = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    if dedupe:
        seen, out = set(), []
        for e in events:
            sig = (e.get("kind"), tuple(e.get("tickers", [])))
            if sig in seen:
                continue
            seen.add(sig)
            out.append(e)
            if len(out) >= limit:
                break
        return out
    return events[:limit]
