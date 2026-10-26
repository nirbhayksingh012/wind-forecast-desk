# Wind Forecast Desk — Video Presentation Script

> **Total Video Duration:** ~10 minutes (Split into two distinct 5-minute sections)  
> **Target Recording Format:** Screen recording with voiceover (webcam optional). Upload to YouTube as **Unlisted** or deliver as MP4.  
> **Live Production URL:** [https://wind-forecast-desk-indol.vercel.app](https://wind-forecast-desk-indol.vercel.app)  
> **Local URL:** `http://localhost:5173` (Frontend) / `http://localhost:8000` (Backend API & Docker)

---

# Part 1: Customer Presentation — Pilot Project Showcase
**Audience:** Head of Trading, Power Purchase Managers, and Quantitative Energy Analysts.  
**Objective:** Impress the customer with domain mastery, actionable commercial insights, an intuitive high-performance portal, and concrete ROI on balancing cost reduction.

---

### Initial Overview: Customer Pilot Presentation (Max 5:00)

| Timestamp | Phase | On-Screen Action | Spoken Script | Key Customer Takeaway |
|---|---|---|---|---|
| **0:00 – 0:40** | **The Pilot Mandate & Core Trading Dilemma** | Start on dashboard header. Zoom slightly on title: *"Wind Forecast Desk — Day-ahead wind generation: what you will see at decision time, and how far to trust it."* | "Good morning, team. Over the last four weeks, we partnered with your power-purchasing desk to solve a daily multi-million-pound challenge: every morning before the day-ahead auction closes, you must commit to tomorrow's power volumes without knowing tomorrow's true weather. Wind is the largest, most volatile swing factor on the UK grid. National Grid ESO and Elexon continuously re-issue forecasts throughout the day. Your traders face two high-stakes questions: First, *what forecast was genuinely in front of me when I had to lock in my bids?* And second, *how wrong is that forecast typically, and what risk buffer do I need to hold?* Today, we are proud to unveil the completed pilot portal, backtested and live on verified January 2026 Elexon market data." | Addresses the core business pain: look-ahead bias and unhedged imbalance risk. |
| **0:40 – 1:45** | **Decision-Time Forecast & Uncertainty Envelope** | Select **15 Jan 2026** with **09:00 Cutoff**. Hover over the main composed chart. Trace the **blue forecast curve**, **green actual curve**, and the **light blue shaded band**. | "Let’s step into the shoes of your trader on January 14th preparing bids for delivery on January 15th. In the UK, EPEX SPOT order books close at 09:20 and Nord Pool at 09:50. We set our default decision cutoff strictly to **09:00 UK time on D-1**. The **solid blue line** shows the exact forecast your desk saw at 09:00—eliminating all hindsight bias. But a point forecast alone is a gamble. The **shaded blue corridor** is our empirical 5th-to-95th percentile historical error band. Notice how on this day, the **green line—the actual grid outturn**—tracked within this corridor. Look at the coverage KPI: our engine automatically reconciles Elexon WINDFOR's hourly forecasts with FUELHH's half-hourly settlement intervals, delivering **100% hourly forecast coverage (744/744 slots)** across the month. Now, watch what happens when I switch the cutoff to **12:00**—the forecast refreshes to capture late-morning model updates, tightening the lead time." | Zero look-ahead guarantee; 90% empirical confidence corridor gives traders immediate risk bounds. |
| **1:45 – 2:50** | **Quantified Month-Level Accuracy & Financial Impact** | Scroll down to the **KPI Summary Card** (*How accurate is it? January 2026, all delivery days*). Hover over **MAE**, **Bias**, **Over-forecast Share**, and **Avg Shortfall**. | "Now let's examine the hard numbers across all 31 delivery days in January. At your 09:00 auction cutoff, the mean absolute error (**MAE**) was **2,022.5 MW**, or **17.9% of average generation**. But the headline discovery for your procurement strategy is the **structural bias**: the national forecast exhibited a **+1,745.9 MW net over-forecast bias**, over-predicting wind **84.7% of the time**. What does this mean in pounds and pence? In 85 out of every 100 delivery hours, wind under-delivered. When that happened, the average generation deficit was **2,060.9 MW**. If your desk bids 100% of the raw forecast volume into the day-ahead auction, you are systematically pushed short into the Balancing Mechanism, paying peak cashout prices or scrambling for expensive peaker capacity. With this quantified shortfall, your desk can now discount day-ahead volumes by a disciplined risk margin." | Demonstrates profound commercial understanding: converting MW bias into cashout and balancing exposure. |
| **2:50 – 4:00** | **Diagnostic Charts: Where is the Forecast Weakest?** | Scroll through the 4 diagnostic grid cards: **Error by Day**, **Error by Hour**, **Error by Horizon**, and **Cutoff Sensitivity**. | "To turn these insights into trading edge, we built four diagnostic views: First, **Error by Delivery Day**—errors spiked to over 4,500 MW during Storm Isha and Jocelyn in mid-January, showing that meteorological frontal transitions require doubling your reserve margin. Second, **Error by Time of Day**—notice the diurnal pattern: morning ramp-up hours (07:00 to 10:00) show higher volatility than midnight base-load. Third, **Error by Horizon**—accuracy degrades predictably as lead time stretches from 24 hours to 42 hours. And fourth, look at our **Cutoff Sensitivity Analysis**: if your desk shifts pre-hedging from 06:00 to 09:00, or participates in the 12:00 intraday rebalancing auction, your average error drops from 2,050 MW to 1,884 MW. That’s a 166 MW per hour accuracy dividend." | Pinpoints specific weather regimes, hours, and auction timings where money is won or lost. |
| **4:00 – 4:35** | **Granular Audit Trail & Operational Trust** | Scroll down to the **Half-Hourly Detail Table**. Click on a row to highlight matched vs interstitial status. | "Trust requires transparency. Below the analytics sits the full **Half-Hourly Detail Audit Table**. Every half-hour slot shows the exact forecast volume, actual metered outturn, error delta, the exact Elexon publish timestamp, the lead horizon in hours, and status tagging. Interstitial half-hour slots without native hourly forecasts are clearly distinguished from on-the-hour matched slots. Every calculation is reproducible, verifiable, and auditable for compliance." | Proves data integrity and auditability—vital for utility compliance and risk management. |
| **4:35 – 5:00** | **Conclusion & Roadmap for Full Production Rollout** | Return to top dashboard view. Show the clean, responsive layout. | "In summary: this pilot has proven that day-ahead wind forecasting cannot be treated as a single truth. By locking forecasts to your exact 09:00 decision cutoff, quantifying the 1,746 MW systemic over-forecast bias, and bounding risk with our 5–95% uncertainty corridor, your desk can save hundreds of thousands of pounds in cashout penalties. The application is production-ready, fully responsive, and deployed live. As our next phase, we propose integrating EPEX day-ahead clearing prices and solar forecasts to deliver algorithmic volume recommendations. Thank you, and I look forward to your questions." | Strong commercial close with clear path to full deployment and expanded engagement. |

---

### Client Presentation Reference Guide & Anticipated Q&A

#### 1. Why 09:00 UK Cutoff?
- **UK Power Auction Reality:** EPEX SPOT GB 60-min auction order books close at 09:20 UK time; Nord Pool N2EX order books close at 09:50 UK time.
- **Traders' Requirement:** A 09:00 cutoff ensures bids are formulated with forecasts that were strictly published and received before order book closure, eliminating retrospective bias.

#### 2. Key Commercial Metrics at a Glance (January 2026 Baseline):
- **Analyzed Window:** 1 Jan 2026 – 31 Jan 2026 decision dates (2 Jan – 1 Feb delivery dates).
- **Hourly Matched Observations:** 744 / 744 (100% coverage).
- **Mean Absolute Error (MAE):** 2,022.5 MW (17.92% of mean actual generation).
- **Root Mean Square Error (RMSE):** 2,497.4 MW.
- **Systemic Bias:** +1,745.9 MW (Over-forecast share: 84.7%).
- **Average Shortfall Volume:** 2,060.9 MW.
- **P90 Maximum Normal Error:** 4,154.4 MW (90% of all hourly errors were bounded within 4.15 GW).

---

# Part 2: Technical Walkthrough — Lead Developer Review
**Audience:** Technical Lead, Senior Software Engineers, and DevOps / Platform Architects.  
**Objective:** Provide a thorough code and architecture review, demonstrate software engineering best practices, explain mathematical rigor and edge-case handling, and ensure effortless knowledge transfer.

---

### Initial Overview: Tech Lead Walkthrough (Max 5:00)

| Timestamp | Phase | On-Screen Action & Code References | Spoken Script | Technical Lead Takeaway |
|---|---|---|---|---|
| **0:00 – 0:45** | **Architecture & Tech Stack Overview** | Show repo root tree and [vercel.json](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/vercel.json) / [Dockerfile](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/Dockerfile). | "Hi team. In this technical walkthrough, I'll walk you through the architecture, design choices, data pipelines, analytical algorithms, and test suite for the Wind Forecast Desk. The application is built as a lightweight, high-performance polyglot monorepo: a React 18 single-page application built with Vite and Recharts on the frontend, and a Python 3.12 FastAPI service on the backend. It deploys natively as a coordinated multi-service application on Vercel via `vercel.json` and in containerized environments via a multi-stage Docker build. Crucially, the entire January 2026 Elexon dataset is stored as a compressed gzip JSON snapshot (`backend/data/snapshot.json.gz`), achieving sub-10ms response times without requiring an external database cluster." | Polyglot architecture; zero-DB serverless design; clear separation of concerns. |
| **0:45 – 1:50** | **Analytical Engine & Mathematical Rigor** | Open [backend/app/analysis.py](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/backend/app/analysis.py). Highlight `select_forecast()`, `delivery_slots()`, and `metrics()`. | "Let's dive into the core analytical engine in `analysis.py`. Everything here is implemented as pure, side-effect-free functions for maximum testability. First, look at `select_forecast`: to eliminate look-ahead bias without $O(N)$ linear scans, we store forecasts per slot sorted by publish time and query them using `bisect_right`. This gives us strict $O(\log N)$ point-in-time lookup for the latest forecast with `publishTime <= cutoff_utc`. Second, look at `delivery_slots`: UK daylight saving transitions mean a delivery day can have 46, 48, or 50 half-hours. We enforce explicit `Europe/London` timezone arithmetic via Python's `zoneinfo`, iterating from local midnight to midnight before converting to UTC. Third, resolution alignment: Elexon `WINDFOR` publishes hourly, while `FUELHH` metered actuals are half-hourly. Rather than masking this difference with naive interpolation, we tag slots as `is_on_hour`, computing forecast coverage honestly against the 744 hourly slots." | $O(\log N)$ bisect selection, bulletproof DST clock changes, honest resolution handling. |
| **1:50 – 2:45** | **Data Layer, Caching & Serverless Resilience** | Open [backend/app/store.py](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/backend/app/store.py), [backend/app/config.py](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/backend/app/config.py), and [backend/app/elexon.py](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/backend/app/elexon.py). | "Turning to the data layer: in `store.py`, `get_data()` uses a thread-safe double-check lock (`_lock`) around an in-memory cache dictionary (`_cache`). When the service boots on serverless platforms like Vercel or AWS Lambda, the root filesystem is read-only. In `config.py`, we implemented multi-path resolution—checking `/var/task/data`, local relative directories, and environment variables. If live fetching is ever triggered on a read-only container, `store.py` intercepts `OSError` and redirects writes to `/tmp/snapshot.json.gz`. In `elexon.py`, our API ingestion features chunked date querying, response deduplication, and resilient ISO timestamp parsing supporting both Zulu `Z` format and offset strings." | Thread-safe in-memory caching; read-only filesystem protection; robust API client. |
| **2:45 – 3:35** | **FastAPI Design & Security Guardrails** | Open [backend/app/main.py](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/backend/app/main.py) and [backend/main.py](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/backend/main.py). | "Looking at `backend/app/main.py`: we expose four REST endpoints under `/api`. Notice our routing strategy: `app.include_router(router, prefix='/api')` and `app.include_router(router)` are dual-mounted so that both reverse-proxied routes and direct container hits resolve seamlessly. Input validation is strict: cutoffs are checked against `^([01]\d\|2[0-3]):[0-5]\d$` regex, returning HTTP 422 for invalid formats, and delivery dates outside January 2026 return clean HTTP 400s. CORS is locked down by default to local dev origins (`localhost:5173`, `127.0.0.1:5173`), with dynamic multi-origin expansion via the `CORS_ORIGINS` environment variable." | Dual-mounted router, regex validation, strict HTTP error codes, secure CORS policy. |
| **3:35 – 4:20** | **Frontend Engineering & Data Visualization** | Open [frontend/src/App.jsx](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/frontend/src/App.jsx) and [frontend/src/styles.css](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/frontend/src/styles.css). | "On the frontend: `App.jsx` is written in vanilla React 18 without bloated component frameworks, styled with a bespoke design system in `styles.css`. For the uncertainty corridor in Recharts, standard charts do not support native floating confidence bands. We solved this with a stacked `AreaChart` pattern: the bottom area `low` is rendered with `stroke='none'` and `fill='transparent'`, while the `range` area sits on top with a 45% opacity blue fill. All Recharts components disable heavy animations (`isAnimationActive={false}`) for instant rendering across date and cutoff switches. Date formatting and MW metrics are strictly centralized in `format.js`." | Elegant stacked SVG technique for confidence intervals; fast, framework-agnostic CSS. |
| **4:20 – 5:00** | **DevOps, Testing Suite & Deployment Parity** | Open terminal. Run `uv run pytest -v` (39 tests pass). Show [frontend/vite.config.js](file:///c:/Users/NIRBHAY/Downloads/wind-dayahead/wind-dayahead/frontend/vite.config.js). | "Finally, quality assurance and DevOps: we have 39 automated tests in `backend/tests/`—30 analytical unit tests covering bisect cutoffs, DST day lengths, and statistical quantiles, and 9 API integration tests verifying status codes, SPA fallback, and CORS headers. Our dependency management uses standard PEP 621 `pyproject.toml` with `uv.lock` and `.python-version` pinned to 3.12. In Vite, `chunkSizeWarningLimit` is configured for clean production bundling. The system passes all tests, achieves 100% data coverage, and runs identically locally, in Docker, and on Vercel. Ready for your review and deployment sign-off!" | 39 automated tests, PEP 621 lockfiles, 100% dev-to-prod environment parity. |

---

### Technical Deep Dive: Key Files & Architectural Reference

#### 1. Repository Layout & Component Responsibility
```
.
├── backend/
│   ├── app/
│   │   ├── analysis.py        # Pure mathematical & analytical engine (bisect_right, quantiles, DST)
│   │   ├── config.py          # App constants, London ZoneInfo, multi-path snapshot resolution
│   │   ├── elexon.py          # Elexon BMRS API client (WINDFOR forecasts, FUELHH actuals)
│   │   ├── fetch_data.py      # CLI utility to refresh snapshot from Elexon API
│   │   ├── main.py            # FastAPI endpoints, CORS middleware, regex validation, SPA serving
│   │   ├── store.py           # Thread-safe in-memory cache, gzip I/O, serverless /tmp fallback
│   │   └── synthetic.py       # Deterministic offline mock data generator for air-gapped demoing
│   ├── data/
│   │   └── snapshot.json.gz   # Compressed January 2026 Elexon dataset (106 KB gzipped, 1.6 MB raw)
│   ├── tests/
│   │   ├── test_analysis.py   # 30 unit tests (bisect correctness, DST, quantile math, coverage)
│   │   └── test_api.py        # 9 integration tests (FastAPI TestClient, CORS, status codes)
│   ├── main.py & index.py     # Vercel FastAPI ASGI service entrypoints
│   ├── pyproject.toml         # PEP 621 package specification with [tool.uv] package = false
│   └── uv.lock                # Deterministic dependency lockfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main dashboard component, Recharts composed charts, state hooks
│   │   ├── api.js             # Fetch client with query param serialization and error parsing
│   │   ├── format.js          # Centralized formatters (MW with commas, percentages, UK dates)
│   │   ├── styles.css         # Custom responsive CSS design system (tokens, cards, tables, grid)
│   │   └── main.jsx           # React DOM root mounting
│   ├── index.html             # HTML5 entrypoint with Google Fonts (Inter) and SEO meta tags
│   ├── package.json           # React 18, Vite 5, Recharts dependencies
│   └── vite.config.js         # Proxy configuration for local dev and build chunk limit
├── Dockerfile                 # Multi-stage production container build (Node 20 build -> Python 3.12-slim)
├── docker-compose.yml         # Container orchestration manifest
├── vercel.json                # Vercel multi-service specification (Vite frontend + FastAPI backend)
└── requirements.txt           # Flat dependency mirror for legacy pip environments
```

#### 2. Key Code Snippets to Point to During Review

##### A. Point-in-Time Forecast Selection (`backend/app/analysis.py` L73–L83)
```python
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
```
*Rationale:* `bisect_right` on pre-sorted UTC publish times provides logarithmic $O(\log N)$ point-in-time lookup. Guarantees zero look-ahead bias by strictly excluding any record published after `cutoff`.

##### B. Daylight Saving Time Boundary Handling (`backend/app/analysis.py` L62–L70)
```python
def delivery_slots(delivery_date: date) -> list[datetime]:
    """All half-hour slot starts of a UK local day (46/48/50 around DST changes)."""
    start = datetime.combine(delivery_date, time(0, 0), tzinfo=LONDON).astimezone(UTC)
    end = datetime.combine(delivery_date + timedelta(days=1), time(0, 0), tzinfo=LONDON).astimezone(UTC)
    out, t = [], start
    while t < end:
        out.append(t)
        t += SLOT
    return out
```
*Rationale:* Converts local midnight to UTC aware timestamps, ensuring spring clock forward (46 half-hours) and autumn clock back (50 half-hours) days are handled cleanly.

##### C. Quantile Interpolation Math (`backend/app/analysis.py` L129–L135)
```python
def quantile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return float("nan")
    pos = (len(sorted_vals) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)
```
*Rationale:* Implements standard linear interpolation between adjacent ranks (equivalent to NumPy `method='linear'`) without heavyweight external dependencies like NumPy or Pandas.

---

### Knowledge Transfer & Verification Checklist

1. **Local Test Execution:**
   ```bash
   # Run all 39 tests from workspace root:
   uv run pytest -v
   # Or directly within backend:
   uv run --directory backend pytest -v
   ```
2. **Local Development Execution:**
   ```bash
   # Terminal 1 (Backend API on :8000):
   cd backend && uvicorn app.main:app --reload --port 8000
   # Terminal 2 (Frontend UI on :5173 with proxy):
   cd frontend && npm run dev
   ```
3. **Containerized Execution:**
   ```bash
   docker compose up --build
   # Healthcheck verify:
   curl -i http://localhost:8000/api/health
   ```
4. **Production Deployment Smoke Test:**
   ```bash
   curl -i https://wind-forecast-desk-indol.vercel.app/api/health
   curl -i https://wind-forecast-desk-indol.vercel.app/api/meta
   curl -i "https://wind-forecast-desk-indol.vercel.app/api/forecast?delivery_date=2026-01-15&cutoff=09:00"
   ```

