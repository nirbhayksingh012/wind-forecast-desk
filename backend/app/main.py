"""FastAPI app: JSON API under /api, React build served from / when present."""
from __future__ import annotations

import logging
import os
import re
from datetime import date

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import analysis
from .config import CUTOFF_OPTIONS, DECISION_END, DECISION_START, DEFAULT_CUTOFF, STATIC_DIR
from .store import get_data

logger = logging.getLogger(__name__)

app = FastAPI(title="Day-ahead wind forecast analyser", version="1.0.0")

# CORS: restricted by default to local development hosts; set CORS_ORIGINS for custom origins or "*" if explicitly needed.
_DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
_env_origins = os.getenv("CORS_ORIGINS")
_cors_origins = [o.strip() for o in _env_origins.split(",") if o.strip()] if _env_origins else _DEFAULT_CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _cutoff(value: str) -> str:
    if not _HHMM.match(value):
        raise HTTPException(422, "cutoff must be HH:MM (UK local time), e.g. 09:00")
    return value


def _data():
    try:
        return get_data()
    except Exception as exc:  # surface a readable message instead of a bare 500
        raise HTTPException(503, f"Data not available: {exc}")


router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/meta")
def meta():
    ds, info = _data()
    days = analysis.delivery_dates(DECISION_START, DECISION_END)
    return {
        **info,
        "decision_window": [DECISION_START.isoformat(), DECISION_END.isoformat()],
        "delivery_dates": [d.isoformat() for d in days],
        "default_cutoff": DEFAULT_CUTOFF,
        "cutoff_options": CUTOFF_OPTIONS,
        "timezone": "Europe/London",
    }


@router.get("/forecast")
def forecast(delivery_date: date, cutoff: str = Query(DEFAULT_CUTOFF)):
    """The forecast a buyer sees at the cutoff for each half-hour of the delivery day."""
    cutoff = _cutoff(cutoff)
    # Validate delivery date is within the analysis window
    delivery_dates = analysis.delivery_dates(DECISION_START, DECISION_END)
    if delivery_date not in delivery_dates:
        raise HTTPException(
            400,
            f"delivery_date {delivery_date} is outside the analysis window "
            f"({delivery_dates[0]} to {delivery_dates[-1]})"
        )
    ds, _ = _data()
    rows = analysis.day_rows(ds, delivery_date, cutoff)
    rep = analysis.accuracy_report(ds, DECISION_START, DECISION_END, cutoff)
    o = rep["overall"]
    latest_pub = analysis.latest_publish(rows)
    day_coverage = {
        "total_hh_slots": len(rows),
        "hourly_slots": sum(1 for r in rows if r["is_on_hour"]),
        "with_forecast": sum(1 for r in rows if r["forecast"] is not None),
        "matched": sum(1 for r in rows if r["error"] is not None),
    }
    return {
        "delivery_date": delivery_date.isoformat(),
        "cutoff": cutoff,
        "cutoff_utc": analysis.cutoff_utc(delivery_date, cutoff).isoformat().replace("+00:00", "Z"),
        "latest_publish": latest_pub,
        # error = forecast - actual  =>  actual ~ forecast - error, so the 5-95%
        # band of historical error gives an uncertainty band around the forecast.
        "band": {"err_q05": o.get("err_q05"), "err_q95": o.get("err_q95")},
        "summary": analysis.metrics(rows),
        "coverage": day_coverage,
        "slots": rows,
    }


@router.get("/accuracy")
def accuracy(cutoff: str = Query(DEFAULT_CUTOFF)):
    ds, _ = _data()
    return analysis.accuracy_report(ds, DECISION_START, DECISION_END, _cutoff(cutoff))


@router.get("/cutoff-sensitivity")
def cutoff_sensitivity():
    ds, _ = _data()
    return analysis.cutoff_sensitivity(ds, DECISION_START, DECISION_END, CUTOFF_OPTIONS)


# Mount router under both /api and root so both /api/health and /health work
app.include_router(router, prefix="/api")
app.include_router(router)

# --- static frontend (Docker / Heroku). On Vercel the CDN serves it instead. ---
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = STATIC_DIR / path
        return FileResponse(f if path and f.is_file() else STATIC_DIR / "index.html")

