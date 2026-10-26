# Wind Forecast Desk - Day-Ahead Wind Forecast Viewer & Accuracy Analyser

A full-stack web application designed for a UK electricity utility's day-ahead power-purchasing desk. It answers two fundamental trading questions using official Elexon open datasets (national-level wind):

1. **What wind forecast would I have seen when I had to decide?** For every delivery slot of a target delivery day, it presents the latest `WINDFOR` forecast published *at or before* the trading cutoff on the previous day (D-1), eliminating look-ahead bias.
2. **How wrong is that forecast, typically?** It evaluates those forecasts against `FUELHH` outturn generation across standard error metrics (MAE, RMSE, bias, nMAE, P50/P90 error percentiles, diurnal patterns, horizon degradation, and cutoff sensitivity) and displays an empirical 5th–95th percentile uncertainty band around the forecast curve.

**Scope:** Purchase decisions made across **January 2026** (delivery dates 2 Jan 2026 – 1 Feb 2026).

---

## Verified January 2026 Performance Metrics

Evaluated at the default **09:00 UK decision cutoff** across all 31 delivery days:

| Metric | Verified Value | Trading Interpretation |
|---|---|---|
| **MAE** | **2,022.5 MW** | Average absolute miss per hourly delivery interval |
| **RMSE** | **2,497.4 MW** | Penalises large forecast misses during volatile wind periods |
| **Bias** | **+1,745.9 MW** | Pronounced net over-forecast bias (system systematically predicted more wind than materialized) |
| **nMAE** | **17.92%** | Normalized against mean outturn wind generation (11,288.6 MW) |
| **Over-forecast Share** | **84.7%** | In ~85% of intervals, actual generation fell short of forecast |
| **Mean Shortfall** | **2,060.9 MW** | Average deficit volume requiring thermal balancing or cashout exposure when over-forecast |
| **P50 Absolute Error** | **1,659.8 MW** | Median error magnitude |
| **P90 Absolute Error** | **4,154.4 MW** | 90% of all forecast misses remained below this threshold |
| **Hourly Forecast Coverage** | **100.0%** (744 / 744) | All on-the-hour settlement slots have valid forecasts |

> **Dataset Resolution Architecture:** The Elexon `WINDFOR` feed publishes forecasts at **hourly** intervals (`:00` start times), whereas `FUELHH` actuals are metered at **half-hourly** settlement intervals (`:00` and `:30`). The application transparently distinguishes native hourly delivery slots from interstitial half-hour slots. Forecast coverage is measured against the native hourly denominator (744/744 = 100%), with matched error metrics evaluated on all 744 coincident slots.

---

## Market Cutoff Assumptions & Verification

### Great Britain Day-Ahead Power Auction Timings
In Great Britain, physical electricity delivery is traded in wholesale day-ahead auctions on day D-1:
- **EPEX SPOT GB Day-Ahead 60-min Auction:** Order book gate closure is at **09:20 UK time** (Europe/London) on D-1.
- **Nord Pool GB Day-Ahead Auction (N2EX):** Order book gate closure is at **09:50 UK time** (Europe/London) on D-1.
- **EPEX SPOT GB Half-Hourly Day-Ahead Auction:** Order book gate closure is at **15:30 UK time** on D-1.

### Why 09:00 UK Time is the Primary Decision Cutoff
1. **Zero Look-Ahead Guarantee:** Traders and automated bidding models must finalize volume commitments and order books prior to the 09:20 and 09:50 auction gate closures. A decision cutoff of **09:00 UK time** guarantees that every forecast evaluated was genuinely in the trader's hands before bid submission.
2. **Point-in-Time Selection:** Using `bisect_right`, each delivery slot selects the latest forecast record whose `publishTime <= cutoff_utc`. Any forecast published at `09:00:01` or later is strictly excluded.
3. **Timezone Awareness:** Cutoffs are specified in `Europe/London` and converted to UTC based on UK daylight saving rules (GMT = UTC+0; BST = UTC+1). On DST transition days, 46 or 50 half-hours are correctly handled.
4. **Cutoff Sensitivity (06:00 – 12:00):**
   - **06:00 / 08:00:** Early-morning indicative positions before final model updates.
   - **09:00:** Primary morning auction commitment (Default).
   - **10:00 / 12:00:** Post-auction intra-day rebalancing decisions.
   - *Empirical Impact:* Moving from 06:00 to 12:00 reduces MAE from 2,050.4 MW to 1,980.6 MW as forecast lead horizons decrease by 3–6 hours.

---

## Key Analysis Decisions Summary

| Decision | Choice | Rationale |
|---|---|---|
| **Decision Cutoff** | **09:00 UK time on D-1** (selectable 06:00–12:00) | Strictly precedes EPEX (09:20) and Nord Pool (09:50) auction gate closures on D-1. |
| **Forecast Selection** | Latest `publishTime <= cutoff` for that `startTime` | Implemented via `bisect_right`. Exactly replicates historical point-in-time visibility with zero look-ahead bias. |
| **Sign Convention** | `error = forecast - actual` | Industry standard: positive error indicates wind was over-forecast (short position, requiring thermal power or balancing purchase). |
| **Timezone & DST** | `Europe/London` with UTC storage | Handles British Summer Time transitions (46, 48, or 50 half-hours per day) correctly. |
| **Uncertainty Corridor** | 5th–95th percentile historical error | Quantifies empirical forecast dispersion around the expected generation curve. |

---

## Security & Environment Configuration

### CORS Configuration
- **Default:** Restricted to local development origins (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:8000`, `http://127.0.0.1:8000`).
- **Custom Origins:** Pass a comma-separated list of origins via the `CORS_ORIGINS` environment variable (e.g. `CORS_ORIGINS="https://my-desk.vercel.app,https://mycompany.com"`). Set `CORS_ORIGINS="*"` only if public unauthenticated access is explicitly intended.

### Environment Variables
| Variable | Default | Purpose |
|---|---|---|
| `CORS_ORIGINS` | `localhost/127.0.0.1` origins | Allowed CORS origins for browser API consumers. |
| `DATA_PATH` | `backend/data/snapshot.json.gz` | Path to Elexon compressed snapshot dataset. |
| `STATIC_DIR` | `frontend/dist` | Path to compiled React production bundle served by FastAPI. |
| `PORT` | `8000` | Port for the Uvicorn web server (automatically set on Heroku). |

---

## Architecture & Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── config.py             # Decision window, default cutoff, paths, timezones
│   │   ├── elexon.py             # Elexon BMRS API client (WINDFOR forecasts, FUELHH actuals)
│   │   ├── store.py              # Compressed snapshot I/O (gzip JSON) + live fetch fallback
│   │   ├── analysis.py           # Pure analytical engine: bisect selection, metrics, DST logic
│   │   ├── main.py               # FastAPI application with input validation & SPA static hosting
│   │   ├── fetch_data.py         # CLI tool to download historic Elexon data
│   │   └── synthetic.py          # Offline synthetic data generator (clearly watermarked)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_analysis.py      # 30 unit tests covering selection, DST, metrics, coverage
│   │   └── test_api.py           # 9 integration tests covering FastAPI routes, CORS, and SPA serving
│   ├── data/
│   │   └── snapshot.json.gz      # Real Elexon snapshot for January 2026
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # React dashboard: Recharts curves, KPI cards, diagnostic charts
│   │   ├── api.js                # Frontend API client
│   │   ├── format.js             # MW, percentage, and date formatters
│   │   ├── styles.css            # Custom CSS design system
│   │   └── main.jsx
│   ├── index.html                # HTML entrypoint with metadata and typography
│   └── package.json
├── Dockerfile                    # Multi-stage Docker build (Node.js build -> Python slim runtime)
├── docker-compose.yml            # Single-command local containerised execution
├── vercel.json                   # Vercel multi-service routing configuration (Vite + FastAPI)
├── heroku.yml                    # Heroku container deployment manifest
├── requirements.txt              # Production Python dependencies
├── pyproject.toml                # Root pytest configuration
└── VIDEO_SCRIPT.md               # Presentation script (Client pitch & Technical walkthrough)
```

---

## API Reference

All endpoints return JSON and are prefixed under `/api`:

| Method & Route | Query Parameters | Description |
|---|---|---|
| `GET /api/health` | None | Service liveness probe (used by Docker `HEALTHCHECK`). Returns `{"status": "ok"}`. |
| `GET /api/meta` | None | Returns data source metadata, fetch timestamp, decision window, delivery dates, and cutoff choices. |
| `GET /api/forecast` | `delivery_date` (YYYY-MM-DD), `cutoff` (HH:MM) | Returns 48 half-hourly delivery slots with forecast at cutoff, outturn actual, error, lead horizon, latest publish timestamp, day summary, and coverage metadata. |
| `GET /api/accuracy` | `cutoff` (HH:MM, default `09:00`) | Returns month-level aggregate metrics (MAE, RMSE, bias, percentiles) and decompositions by day, hour of day, and lead horizon bucket. |
| `GET /api/cutoff-sensitivity` | None | Evaluates month-level MAE and RMSE across all supported cutoff times (`06:00` through `12:00`). |

---

## Running Locally

### 1. Run with Docker (Recommended)

```bash
docker compose up --build
# Open http://localhost:8000
```

### 2. Run in Local Development Mode

**Terminal 1 — Backend API:**
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | Unix: source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend UI:**
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173 (proxies /api requests to http://localhost:8000)
```

### 3. Frontend Build

To compile the production frontend bundle into `frontend/dist`:

```bash
cd frontend
npm run build
```

FastAPI will automatically detect `frontend/dist` and serve the compiled single-page application at `/`.

### 4. Running the Test Suite

Execute the 39 unit and integration tests from the repository root:

```bash
pytest -v
```

All 39 tests validate:
- Point-in-time forecast selection at and before cutoff timestamps
- Strict exclusion of look-ahead forecasts published after cutoff
- Strict handling of Daylight Saving Time day lengths (46, 48, 50 settlement periods)
- Statistical metric correctness (MAE, RMSE, bias, nMAE, quantile interpolation)
- Hourly vs half-hourly slot categorization and honest coverage metrics
- FastAPI route validation (HTTP 200, 400 for out-of-bounds dates, 422 for invalid cutoffs, SPA serving)
- CORS origin restriction and header filtering

---

## Deployment Options

1. **Vercel (Multi-Service Native):**
   - Connect the repository to Vercel.
   - `vercel.json` deploys the frontend (`frontend/`, Vite) and backend (`backend/`, FastAPI) as native coordinated services with `/api/*` routed directly to FastAPI.
2. **Heroku / Container Platform:**
   - Deploy using the multi-stage `Dockerfile` and `heroku.yml`.
   - The container builds the frontend assets and runs `uvicorn` to serve both the JSON API and static files with health monitoring.
