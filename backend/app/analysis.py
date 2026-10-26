"""Pure analysis logic (no I/O) so it is easy to test and reason about.

Core idea
---------
A buyer bidding on the day-ahead market for delivery day D must decide at a
cutoff time on D-1. For every half-hour slot of D the forecast they could have
seen is the *most recently published* WINDFOR forecast for that slot with
publishTime <= cutoff. Comparing that to the FUELHH actual gives the error the
buyer would really have faced.

Sign convention: error = forecast - actual (MW).
  error > 0  -> wind was over-forecast -> buyer is short and must buy more.
"""
from __future__ import annotations

import math
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from .config import LONDON

UTC = timezone.utc
SLOT = timedelta(minutes=30)


def parse_ts(value: str) -> datetime:
    """Parse an ISO timestamp (Elexon uses a trailing Z) to aware UTC."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)


@dataclass
class Dataset:
    actuals: dict[datetime, float] = field(default_factory=dict)
    # startTime -> (sorted publish times, generation aligned with them)
    forecasts: dict[datetime, tuple[list[datetime], list[float]]] = field(default_factory=dict)


def build_dataset(actual_rows, forecast_rows) -> Dataset:
    """actual_rows: [(start_iso, MW)], forecast_rows: [(start_iso, publish_iso, MW)]."""
    ds = Dataset()
    for start, gen in actual_rows:
        ds.actuals[parse_ts(start)] = float(gen)
    tmp: dict[datetime, dict[datetime, float]] = defaultdict(dict)
    for start, publish, gen in forecast_rows:
        tmp[parse_ts(start)][parse_ts(publish)] = float(gen)
    for start, by_pub in tmp.items():
        pubs = sorted(by_pub)
        ds.forecasts[start] = (pubs, [by_pub[p] for p in pubs])
    return ds


def cutoff_utc(delivery_date: date, cutoff_hhmm: str) -> datetime:
    """Decision deadline: cutoff time (UK clock) on the day before delivery."""
    hh, mm = (int(x) for x in cutoff_hhmm.split(":"))
    local = datetime.combine(delivery_date - timedelta(days=1), time(hh, mm), tzinfo=LONDON)
    return local.astimezone(UTC)


def delivery_slots(delivery_date: date) -> list[datetime]:
    """All half-hour slot starts of a UK local day (46/48/50 around DST changes)."""
    start = datetime.combine(delivery_date, time(0, 0), tzinfo=LONDON).astimezone(UTC)
    end = datetime.combine(delivery_date + timedelta(days=1), time(0, 0), tzinfo=LONDON).astimezone(UTC)
    out, t = [], start
    while t < end:
        out.append(t)
        t += SLOT
    return out


def select_forecast(ds: Dataset, slot: datetime, cutoff: datetime):
    """Latest forecast for `slot` published at or before `cutoff`, else None."""
    entry = ds.forecasts.get(slot)
    if not entry:
        return None
    pubs, gens = entry
    i = bisect_right(pubs, cutoff)
    if i == 0:
        return None
    return pubs[i - 1], gens[i - 1]


def day_rows(ds: Dataset, delivery_date: date, cutoff_hhmm: str) -> list[dict]:
    cutoff = cutoff_utc(delivery_date, cutoff_hhmm)
    rows = []
    for slot in delivery_slots(delivery_date):
        sel = select_forecast(ds, slot, cutoff)
        actual = ds.actuals.get(slot)
        on_hour = slot.minute == 0
        row = {
            "start": slot.isoformat().replace("+00:00", "Z"),
            "local_hour": slot.astimezone(LONDON).hour,
            "local_minute": slot.astimezone(LONDON).minute,
            "is_on_hour": on_hour,
            "forecast": None, "publish": None, "horizon_h": None,
            "actual": actual, "error": None,
            "status": "no_forecast",
        }
        if sel:
            pub, gen = sel
            row.update(
                forecast=gen,
                publish=pub.isoformat().replace("+00:00", "Z"),
                horizon_h=round((slot - pub).total_seconds() / 3600, 2),
            )
            if actual is not None:
                row["error"] = gen - actual
                row["status"] = "matched"
            else:
                row["status"] = "forecast_only"
        elif not on_hour:
            row["status"] = "interstitial"  # HH slot with no hourly forecast available
        elif actual is not None:
            row["status"] = "actual_only"
        rows.append(row)
    return rows


def delivery_dates(start: date, end: date) -> list[date]:
    d, out = start + timedelta(days=1), []
    while d <= end + timedelta(days=1):
        out.append(d)
        d += timedelta(days=1)
    return out


def quantile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return float("nan")
    pos = (len(sorted_vals) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def metrics(rows: list[dict]) -> dict:
    """Error statistics over rows that have both a forecast and an actual."""
    scored = [r for r in rows if r["error"] is not None]
    n = len(scored)
    if n == 0:
        return {"n": 0}
    errs = [r["error"] for r in scored]
    abs_errs = sorted(abs(e) for e in errs)
    sorted_errs = sorted(errs)
    mean_actual = sum(r["actual"] for r in scored) / n
    mae = sum(abs_errs) / n
    over = [e for e in errs if e > 0]
    return {
        "n": n,
        "mae": mae,
        "rmse": math.sqrt(sum(e * e for e in errs) / n),
        "bias": sum(errs) / n,
        "mean_actual": mean_actual,
        "nmae_pct": mae / mean_actual * 100 if mean_actual else None,
        "p50_abs_error": quantile(abs_errs, 0.5),
        "p90_abs_error": quantile(abs_errs, 0.9),
        "max_abs_error": abs_errs[-1],
        "err_q05": quantile(sorted_errs, 0.05),
        "err_q95": quantile(sorted_errs, 0.95),
        "over_forecast_share": len(over) / n,
        "mean_over_forecast": sum(over) / len(over) if over else 0.0,
    }


def _group(rows, keyfn):
    groups = defaultdict(list)
    for r in rows:
        k = keyfn(r)
        if k is not None:
            groups[k].append(r)
    return groups


def horizon_bucket(r: dict) -> str | None:
    h = r["horizon_h"]
    if h is None:
        return None
    lo = int(h // 6) * 6
    return f"{lo:02d}-{lo + 6:02d}h"


def latest_publish(rows: list[dict]) -> str | None:
    """Latest publishTime across all rows that have a forecast."""
    pubs = [r["publish"] for r in rows if r["publish"] is not None]
    return max(pubs) if pubs else None


def accuracy_report(ds: Dataset, start: date, end: date, cutoff_hhmm: str) -> dict:
    all_rows, by_day = [], []
    for d in delivery_dates(start, end):
        rows = day_rows(ds, d, cutoff_hhmm)
        all_rows.extend(rows)
        m = metrics(rows)
        if m["n"]:
            by_day.append({"date": d.isoformat(), **m})
    by_hour = [
        {"hour": h, **metrics(rs)} for h, rs in sorted(_group(all_rows, lambda r: r["local_hour"]).items())
        if metrics(rs)["n"]
    ]
    by_horizon = [
        {"bucket": b, **metrics(rs)} for b, rs in sorted(_group(all_rows, horizon_bucket).items())
        if metrics(rs)["n"]
    ]
    total_hh = sum(1 for r in all_rows)
    hourly_slots = sum(1 for r in all_rows if r["is_on_hour"])
    with_fc = sum(1 for r in all_rows if r["forecast"] is not None)
    matched = sum(1 for r in all_rows if r["error"] is not None)
    with_actual = sum(1 for r in all_rows if r["actual"] is not None)
    return {
        "cutoff": cutoff_hhmm,
        "overall": metrics(all_rows),
        "coverage": {
            "total_hh_slots": total_hh,
            "hourly_slots": hourly_slots,
            "with_forecast": with_fc,
            "with_actual": with_actual,
            "matched": matched,
            # Primary coverage: forecasts ÷ hourly slots (native WINDFOR resolution)
            "forecast_coverage_pct": with_fc / hourly_slots * 100 if hourly_slots else 0,
            # Secondary: forecasts ÷ all HH slots (for transparency)
            "hh_coverage_pct": with_fc / total_hh * 100 if total_hh else 0,
            "note": "WINDFOR provides hourly forecasts; FUELHH provides half-hourly actuals. "
                    "Coverage is calculated against hourly slots (the forecast's native resolution).",
        },
        "by_day": by_day,
        "by_hour": by_hour,
        "by_horizon": by_horizon,
    }


def cutoff_sensitivity(ds: Dataset, start: date, end: date, cutoffs: list[str]) -> list[dict]:
    out = []
    for c in cutoffs:
        rows = [r for d in delivery_dates(start, end) for r in day_rows(ds, d, c)]
        m = metrics(rows)
        if m["n"]:
            out.append({"cutoff": c, "mae": m["mae"], "rmse": m["rmse"], "bias": m["bias"], "n": m["n"]})
    return out
