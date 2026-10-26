"""Snapshot persistence + lazy loading.

January 2026 is historic, so the data is fetched once into a compressed JSON
snapshot (backend/data/snapshot.json.gz) and served from memory. That keeps the
app fast and lets it run on serverless hosts that have no database or disk.
"""
from __future__ import annotations

import gzip
import json
import threading
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from .analysis import Dataset, build_dataset
from .config import DATA_PATH, DECISION_END, DECISION_START

_lock = threading.Lock()
_cache: dict = {}


def save_snapshot(path: Path, actuals, forecasts, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": source,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "actuals": actuals,
        "forecasts": forecasts,
    }
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))


def fetch_live_and_save(path: Path = DATA_PATH) -> None:
    import httpx
    from .elexon import fetch_actuals, fetch_forecasts

    # Delivery days are decision days + 1; forecasts may be published a little
    # before the first decision day.
    d_start, d_end = DECISION_START + timedelta(days=1), DECISION_END + timedelta(days=1)
    pub_from = datetime.combine(DECISION_START - timedelta(days=2), time(0), tzinfo=timezone.utc)
    pub_to = datetime.combine(DECISION_END + timedelta(days=1), time(0), tzinfo=timezone.utc)
    with httpx.Client() as client:
        actuals = fetch_actuals(client, d_start - timedelta(days=1), d_end + timedelta(days=1))
        forecasts = fetch_forecasts(client, pub_from, pub_to)
    if not actuals or not forecasts:
        raise RuntimeError(f"Elexon returned no data (actuals={len(actuals)}, forecasts={len(forecasts)})")
    save_snapshot(path, [list(a) for a in actuals], [list(f) for f in forecasts], "elexon")


def get_data() -> tuple[Dataset, dict]:
    """Returns (dataset, meta). Loads the snapshot, fetching live data if missing."""
    with _lock:
        if "ds" not in _cache:
            if not DATA_PATH.exists():
                fetch_live_and_save(DATA_PATH)
            with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
                raw = json.load(f)
            _cache["ds"] = build_dataset(raw["actuals"], raw["forecasts"])
            _cache["meta"] = {
                "source": raw.get("source", "unknown"),
                "fetched_at": raw.get("fetched_at"),
                "n_actuals": len(raw["actuals"]),
                "n_forecasts": len(raw["forecasts"]),
            }
        return _cache["ds"], _cache["meta"]
