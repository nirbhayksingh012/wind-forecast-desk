# Video script (max 10 min total)

Screen-record with voice-over (face optional). Upload to YouTube as **Unlisted**. Rehearse once; aim for ~4:30 per part.

## Part 1 - Client pitch (~4:30)  *talk to the energy buyers*

**0:00 - The problem (30s)**
"Every morning you commit to tomorrow's power before you know tomorrow's weather. Wind is the biggest swing factor in the UK grid, and the forecast you rely on keeps being re-issued. Two questions every buyer faces: what did the forecast actually say when I had to decide, and how far can I trust it?"

**0:30 - Forecast at decision time (90s)** - open the dashboard, top chart.
- Pick a delivery day (e.g. 15 Jan) and the default 09:00 cutoff. "The blue line is the latest forecast published before your 09:00 deadline, for every hourly delivery slot of tomorrow."
- Point out the coverage card: "Notice WINDFOR delivers native hourly forecasts—giving 100% hourly forecast coverage (744/744 slots across January). The dashboard clearly distinguishes on-the-hour delivery from half-hourly interstitial settlement intervals."
- Point at the shaded band: "Historically, 90% of actual wind generation landed inside this 5th-to-95th percentile uncertainty corridor."
- Show the green actual line: "Here is what really happened on the grid."
- Change the cutoff from 09:00 to 12:00: "See how later decisions gain fresher forecasts with shorter horizons."

**2:00 - Quantified accuracy (90s)** - KPI cards.
- "Over all 744 matched hourly intervals in January, the forecast missed by **2,023 MW on average** (MAE), representing **17.9% of mean generation** (11,289 MW)."
- "90% of all absolute forecast misses were below **4,154 MW** (P90 error)."
- Over-forecast share and bias: "Crucially, the system exhibited a **+1,746 MW average bias**, over-forecasting wind **84.7% of the time**. When wind under-delivered, the average volume shortfall was **2,061 MW**—this directly translates to the volume of flexible thermal generation or cashout imbalance exposure you had to manage."

**3:30 - Where it's weakest (60s)** - the diagnostic charts.
- By day: "Look at the day-by-day error chart—high wind/storm days saw spikes where errors doubled."
- By hour: "Diurnal error patterns highlight morning ramp-up vulnerabilities."
- By horizon: "Longer lead times degrade accuracy predictably; 24-30h horizons have significantly higher dispersion."
- Cutoff sensitivity: "Moving gate closure from 06:00 to 12:00 trims MAE from ~2,050 MW to ~1,980 MW."
- "With these breakdowns, trading desks can size dynamic risk buffers rather than static margins."

**4:30 - Close (15s)**
"Live, interactive, built strictly on official Elexon open datasets (WINDFOR & FUELHH). Next logical step: integrate demand forecasts and day-ahead auction clearing prices to generate algorithmic procurement volume recommendations."

---

## Part 2 - Technical walkthrough (~4:30)  *talk to the tech lead*

**0:00 - Architecture (60s)** - show the folder tree from the README.
"Full-stack production architecture: React + Vite front end with Recharts, FastAPI Python back end, containerised in a multi-stage Docker build serving both static assets and API from port 8000. Data is snapshotted deterministically into compressed gzip JSON (`backend/data/snapshot.json.gz`), enabling sub-millisecond query responses and zero external DB dependencies for serverless platforms like Vercel and Heroku."

**1:00 - The core analysis engine (90s)** - open `backend/app/analysis.py`.
- `select_forecast`: point to `bisect_right` on publish timestamps. Guarantees point-in-time correctness with zero look-ahead bias (strictly `publishTime <= cutoff`).
- `cutoff_utc` / `delivery_slots`: explicit `Europe/London` timezone arithmetic, safely handling UK clock changes (46 / 48 / 50 half-hours per delivery day).
- Error convention: `error = forecast - actual`. Positive indicates over-forecast (shortage of power).
- Resolution handling: transparently identifies `is_on_hour` to account for WINDFOR's native 60-min cadence versus FUELHH's 30-min settlement intervals.
- `metrics`: MAE, RMSE, bias, nMAE, quantile interpolation for P50, P90, P05/P95 error bands.

**2:30 - Data pipelines and API (60s)** - `elexon.py`, `store.py`, `main.py`.
- Resilient Elexon API integration: chunked date queries, response deduplication, robust ISO timestamp parsing (supporting `Z`, offsets, and naive formats).
- REST API: clean schema, input validation (`HH:MM` regex, delivery date window checks), environment-aware CORS origins, and static asset fallback routing.

**3:30 - Quality assurance and DevOps (60s)**
- Run test suite: `pytest` with 38 unit and integration tests covering point-in-time cutoffs, DST boundaries, metrics accuracy, edge cases, and API responses.
- Containerisation: multi-stage `Dockerfile` with Node build and Python slim runtime, plus Docker `HEALTHCHECK` hitting `/api/health`.
- Multi-cloud readiness: ready to deploy via Docker Compose, Vercel serverless (`vercel.json`), or Heroku container stack (`heroku.yml`).
- Synthetic mode: `app.synthetic` provides offline mock data, clearly tagged and highlighted with an in-app banner for complete auditability.

**4:30 - Limitations and roadmap (30s)**
- In-sample uncertainty corridor: production should use a rolling 30-to-60 day out-of-sample window.
- Asset scope: extend from national wind to solar, interconnectors, and embedded generation.
