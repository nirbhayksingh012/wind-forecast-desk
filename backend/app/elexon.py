"""Thin client for the Elexon BMRS open-data API (no API key needed)."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import httpx

from .config import ELEXON_BASE


def _rows(payload):
    # The stream endpoints return a bare JSON array; some return {"data": [...]}.
    if isinstance(payload, dict):
        return payload.get("data", [])
    return payload


def _get(client: httpx.Client, path: str, params: dict) -> list[dict]:
    r = client.get(f"{ELEXON_BASE}{path}", params=params, timeout=90)
    if r.status_code >= 400:
        raise RuntimeError(f"Elexon {path} {params} -> HTTP {r.status_code}: {r.text[:300]}")
    return _rows(r.json())


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_actuals(client: httpx.Client, start: date, end: date, chunk_days: int = 7):
    """FUELHH, WIND only. Returns [(startTime, generation_MW)] de-duplicated."""
    out: dict[str, float] = {}
    d = start
    while d <= end:
        stop = min(d + timedelta(days=chunk_days - 1), end)
        rows = _get(client, "/datasets/FUELHH/stream", {
            "settlementDateFrom": d.isoformat(),
            "settlementDateTo": stop.isoformat(),
            "fuelType": "WIND",
        })
        for r in rows:
            if r.get("fuelType", "WIND") == "WIND":
                out[r["startTime"]] = float(r["generation"])
        d = stop + timedelta(days=1)
    return sorted(out.items())


def fetch_forecasts(client: httpx.Client, frm: datetime, to: datetime, chunk_days: int = 2):
    """WINDFOR by publish time. Returns [(startTime, publishTime, generation_MW)]."""
    out: dict[tuple[str, str], float] = {}
    t = frm
    while t < to:
        stop = min(t + timedelta(days=chunk_days), to)
        rows = _get(client, "/datasets/WINDFOR/stream", {
            "publishDateTimeFrom": _iso(t),
            "publishDateTimeTo": _iso(stop),
        })
        for r in rows:
            if r.get("generation") is not None:
                out[(r["startTime"], r["publishTime"])] = float(r["generation"])
        t = stop
    return sorted((s, p, g) for (s, p), g in out.items())
