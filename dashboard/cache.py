"""Local cache for fetched ticker data and generated infographics.

- Data:        cache/data/<TICKER>.json   (metric bundle + fetched_at)
- Infographic: cache/infographics/<KEY>.png

Re-requests reuse cached data while it is younger than TTL_HOURS; a forced
refresh or an expired entry triggers a re-fetch and overwrites the cache.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Optional

CACHE_DIR = Path(__file__).resolve().parent / "cache"
DATA_DIR = CACHE_DIR / "data"
IMG_DIR = CACHE_DIR / "infographics"
TTL_HOURS = 24


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def data_path(ticker: str) -> Path:
    return DATA_DIR / f"{ticker.strip().upper()}.json"


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


def load_data(ticker: str, ttl_hours: int = TTL_HOURS) -> Optional[dict]:
    """Return cached bundle if present and fresh, else None."""
    path = data_path(ticker)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not is_fresh(payload.get("fetched_at"), ttl_hours):
        return None
    return payload.get("data")


def save_data(ticker: str, data: dict) -> str:
    _ensure_dirs()
    fetched_at = _now().isoformat()
    payload = {"ticker": ticker.strip().upper(), "fetched_at": fetched_at, "data": data}
    data_path(ticker).write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")
    return fetched_at


def cache_status(ticker: str) -> dict:
    """Describe the cache entry for the UI (exists / fetched_at / fresh)."""
    path = data_path(ticker)
    if not path.exists():
        return {"exists": False, "fetched_at": None, "fresh": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"exists": False, "fetched_at": None, "fresh": False}
    fetched_at = payload.get("fetched_at")
    return {"exists": True, "fetched_at": fetched_at, "fresh": is_fresh(fetched_at)}


def get_or_fetch(ticker: str, fetch_fn, force: bool = False, ttl_hours: int = TTL_HOURS):
    """Return (data, from_cache, fetched_at). Fetches & caches on miss/force."""
    if not force:
        cached = load_data(ticker, ttl_hours)
        if cached is not None:
            return cached, True, cache_status(ticker)["fetched_at"]
    data = fetch_fn(ticker)
    fetched_at = save_data(ticker, data)
    return data, False, fetched_at


def save_infographic(key: str, png_bytes: bytes) -> Path:
    _ensure_dirs()
    path = infographic_path(key)
    path.write_bytes(png_bytes)
    return path
