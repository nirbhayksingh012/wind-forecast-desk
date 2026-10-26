import { useEffect, useMemo, useState } from "react";
import {
  Area, Bar, BarChart, CartesianGrid, ComposedChart, Legend, Line, LineChart, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "./api.js";
import { mw, pct, ukDateTime, ukTime, shortDate } from "./format.js";

const C = { forecast: "#2563eb", actual: "#16a34a", band: "#93c5fd", err: "#ea580c", grid: "#e5e7eb" };

const STATUS_LABELS = {
  matched: "✓ Matched",
  forecast_only: "Forecast only",
  actual_only: "Actual only",
  interstitial: "HH gap",
  no_forecast: "No forecast",
};

function Card({ title, sub, children }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      {sub && <p className="sub">{sub}</p>}
      {children}
    </section>
  );
}

function Kpi({ label, value, unit, hint }) {
  return (
    <div className="kpi" title={hint}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">
        {value}
        {unit && <span className="kpi-unit"> {unit}</span>}
      </div>
    </div>
  );
}

const Axis = ({ unit }) => <YAxis tick={{ fontSize: 12 }} width={56} label={unit ? { value: unit, angle: -90, position: "insideLeft", fontSize: 12 } : undefined} />;

export default function App() {
  const [meta, setMeta] = useState(null);
  const [day, setDay] = useState(null);
  const [cutoff, setCutoff] = useState(null);
  const [fc, setFc] = useState(null);
  const [acc, setAcc] = useState(null);
  const [sens, setSens] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.meta().then((m) => {
      setMeta(m);
      setCutoff(m.default_cutoff);
      setDay(m.delivery_dates[13]); // mid-month, a day with full actuals
    }).catch((e) => setError(e.message));
    api.sensitivity().then(setSens).catch(() => {});
  }, []);

  useEffect(() => {
    if (!day || !cutoff) return;
    setError(null);
    Promise.all([api.forecast(day, cutoff), api.accuracy(cutoff)])
      .then(([f, a]) => { setFc(f); setAcc(a); })
      .catch((e) => setError(e.message));
  }, [day, cutoff]);

  const chartData = useMemo(() => {
    if (!fc) return [];
    const { err_q05, err_q95 } = fc.band;
    return fc.slots.map((s) => {
      const low = s.forecast == null ? null : Math.max(0, s.forecast - err_q95);
      const high = s.forecast == null ? null : s.forecast - err_q05;
      return { t: ukTime(s.start), forecast: s.forecast, actual: s.actual, low, range: low == null ? null : high - low, error: s.error };
    });
  }, [fc]);

  // Error distribution data for histogram
  const errorDistData = useMemo(() => {
    if (!acc?.overall?.n) return [];
    const scored = (fc?.slots || []).filter((s) => s.error != null);
    if (scored.length < 5) return [];
    const bins = {};
    const step = 500;
    scored.forEach((s) => {
      const bin = Math.floor(s.error / step) * step;
      bins[bin] = (bins[bin] || 0) + 1;
    });
    return Object.entries(bins).map(([k, v]) => ({ bin: `${Number(k)}`, count: v })).sort((a, b) => Number(a.bin) - Number(b.bin));
  }, [fc, acc]);

  if (error && !meta) return <div className="page"><div className="alert">Could not load data: {error}</div></div>;
  if (!meta) return <div className="page">Loading…</div>;

  const o = acc?.overall;
  const d = fc?.summary;
  const cov = acc?.coverage;
  // Use latest_publish from API response (max across all slots)
  const latestPub = fc?.latest_publish;

  return (
    <div className="page">
      <header>
        <div>
          <h1>Wind Forecast Desk</h1>
          <p className="tag">Day-ahead wind generation: what you will see at decision time, and how far to trust it.</p>
        </div>
        <div className="controls">
          <label>Delivery day
            <select value={day || ""} onChange={(e) => setDay(e.target.value)}>
              {meta.delivery_dates.map((x) => <option key={x} value={x}>{shortDate(x)} 2026</option>)}
            </select>
          </label>
          <label>Decision cutoff (UK time, day before)
            <select value={cutoff || ""} onChange={(e) => setCutoff(e.target.value)}>
              {meta.cutoff_options.map((x) => <option key={x} value={x}>{x}</option>)}
            </select>
          </label>
        </div>
      </header>

      {meta.source === "synthetic" && (
        <div className="alert">⚠ Showing SYNTHETIC demo data, not Elexon data. Run <code>python -m app.fetch_data</code> to load the real January 2026 dataset.</div>
      )}
      {error && <div className="alert">{error}</div>}

      <Card
        title={`Forecast for ${shortDate(day)} as known at ${fc ? ukDateTime(fc.cutoff_utc) : "…"}`}
        sub="For each hour the line shows the latest forecast published before your cutoff. The shaded band is the 5–95% range of the error this forecast has historically had; the green line is what wind actually delivered. Note: WINDFOR forecasts are hourly; half-hourly interstitial slots have no forecast."
      >
        {d?.n > 0 && (
          <div className="kpis">
            <Kpi label="Avg forecast wind" value={mw(chartData.reduce((a, r) => a + (r.forecast ?? 0), 0) / chartData.filter((r) => r.forecast != null).length)} unit="MW" hint="Mean of the hourly forecasts for this day" />
            <Kpi label="This day's MAE" value={mw(d.mae)} unit="MW" hint={`Mean absolute error vs. actual (${d.n} matched observations)`} />
            <Kpi label="This day's bias" value={mw(d.bias)} unit="MW" hint="Positive = wind over-forecast, so you would have been short" />
            <Kpi label="Forecast last updated" value={latestPub ? ukDateTime(latestPub) : "–"} hint="Latest publishTime across all slots' forecasts" />
          </div>
        )}
        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid stroke={C.grid} vertical={false} />
            <XAxis dataKey="t" tick={{ fontSize: 12 }} interval={3} />
            <Axis unit="MW" />
            <Tooltip formatter={(v, n) => (n === "range" ? null : [`${mw(v)} MW`, n])} />
            <Legend />
            <Area dataKey="low" stackId="b" stroke="none" fill="transparent" legendType="none" isAnimationActive={false} />
            <Area dataKey="range" stackId="b" stroke="none" fill={C.band} fillOpacity={0.45} name="5–95% error band" isAnimationActive={false} />
            <Line dataKey="forecast" name="Forecast at cutoff" stroke={C.forecast} strokeWidth={2.2} dot={false} isAnimationActive={false} />
            <Line dataKey="actual" name="Actual" stroke={C.actual} strokeWidth={2} dot={false} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </Card>

      <Card title="How accurate is it? January 2026, all delivery days" sub={`Judged on the forecast available at ${cutoff} on the day before delivery. Error = forecast − actual. Positive error means wind was over‑forecast (buyer is short).`}>
        {o?.n > 0 ? (
          <div className="kpis">
            <Kpi label="Mean absolute error" value={mw(o.mae)} unit="MW" hint={`Typical size of a miss (${o.n} matched observations)`} />
            <Kpi label="RMSE" value={mw(o.rmse)} unit="MW" hint={`Penalises large misses (${o.n} observations)`} />
            <Kpi label="Error as % of wind" value={pct(o.nmae_pct)} hint="MAE ÷ average actual wind" />
            <Kpi label="Bias" value={mw(o.bias)} unit="MW" hint="Average of forecast − actual; positive = over-forecast" />
            <Kpi label="90% of misses below" value={mw(o.p90_abs_error)} unit="MW" />
            <Kpi label="Worst miss" value={mw(o.max_abs_error)} unit="MW" />
            <Kpi label="Over-forecast share" value={pct(o.over_forecast_share * 100, 0)} hint="Share of hours where wind came in lower than forecast" />
            <Kpi label="Avg shortfall when over-forecast" value={mw(o.mean_over_forecast)} unit="MW" hint="Extra power you would have had to buy" />
          </div>
        ) : <p>No scored half-hours.</p>}
        {cov && (
          <div className="coverage-box">
            <p className="note">
              <strong>Coverage:</strong>{" "}
              Forecasts available for {cov.with_forecast} of {cov.hourly_slots} hourly slots ({pct(cov.forecast_coverage_pct)}).
              {" "}Matched with actuals: {cov.matched} observations used for error metrics.
              {" "}Total half-hourly slots: {cov.total_hh_slots} (WINDFOR provides hourly forecasts only, so {cov.total_hh_slots - cov.hourly_slots} interstitial half-hour slots have no forecast).
            </p>
          </div>
        )}
      </Card>

      <div className="grid2">
        <Card title="Error by delivery day" sub="Mean absolute error (MW). Some weather days are much harder than others.">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={acc?.by_day || []}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="date" tickFormatter={shortDate} tick={{ fontSize: 11 }} interval={2} />
              <Axis />
              <Tooltip labelFormatter={shortDate} formatter={(v) => [`${mw(v)} MW`, "MAE"]} />
              <Bar dataKey="mae" fill={C.err} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Error by time of day" sub="MAE by UK clock hour: when in the day is the forecast weakest?">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={acc?.by_hour || []}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
              <Axis />
              <Tooltip labelFormatter={(h) => `${h}:00`} formatter={(v) => [`${mw(v)} MW`, "MAE"]} />
              <Bar dataKey="mae" fill={C.forecast} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Error by forecast horizon" sub="Forecasts further ahead are less accurate. Horizon = target time minus publishTime.">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={acc?.by_horizon || []}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
              <Axis />
              <Tooltip formatter={(v, n) => [`${mw(v)} MW`, n]} />
              <Legend />
              <Bar dataKey="mae" name="MAE" fill={C.err} radius={[3, 3, 0, 0]} />
              <Bar dataKey="rmse" name="RMSE" fill="#7c3aed" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Does the cutoff time matter?" sub="MAE if you had to decide earlier or later. Later cutoffs see fresher forecasts.">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={sens || []}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="cutoff" tick={{ fontSize: 11 }} />
              <Axis />
              <Tooltip formatter={(v, n) => [`${mw(v)} MW`, n]} />
              <Legend />
              {cutoff && <ReferenceLine x={cutoff} stroke="#9ca3af" strokeDasharray="4 4" />}
              <Line dataKey="mae" name="MAE" stroke={C.err} strokeWidth={2.2} />
              <Line dataKey="rmse" name="RMSE" stroke="#7c3aed" strokeWidth={2.2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {errorDistData.length > 0 && (
        <Card title="Error distribution (this day)" sub="Distribution of forecast errors for the selected delivery day. Positive = over-forecast (buyer short), negative = under-forecast (buyer long).">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={errorDistData}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="bin" tick={{ fontSize: 11 }} label={{ value: "Error (MW)", position: "insideBottom", offset: -2, fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} width={40} label={{ value: "Count", angle: -90, position: "insideLeft", fontSize: 12 }} />
              <Tooltip formatter={(v) => [v, "Slots"]} />
              <Bar dataKey="count" fill={C.err} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      <Card title="Half-hourly detail" sub="Positive error = forecast above actual = wind under-delivered. Status: ✓ Matched = forecast and actual available; HH gap = interstitial half-hour slot (WINDFOR is hourly).">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Slot (UK)</th><th>Forecast MW</th><th>Actual MW</th><th>Error MW</th><th>Published (UK)</th><th>Horizon h</th><th>Status</th></tr></thead>
            <tbody>
              {(fc?.slots || []).map((s) => (
                <tr key={s.start} className={s.status === "interstitial" ? "row-dim" : ""}>
                  <td>{ukTime(s.start)}</td><td>{mw(s.forecast)}</td><td>{mw(s.actual)}</td>
                  <td className={s.error > 0 ? "pos" : s.error != null && s.error < 0 ? "neg" : ""}>{s.error == null ? "–" : (s.error > 0 ? "+" : "") + mw(s.error)}</td>
                  <td>{s.publish ? ukDateTime(s.publish) : "–"}</td><td>{s.horizon_h ?? "–"}</td>
                  <td className={`status-${s.status}`}>{STATUS_LABELS[s.status] || s.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <footer>
        Source: Elexon BMRS (FUELHH wind actuals, WINDFOR wind forecasts), national level. Data fetched {meta.fetched_at?.slice(0, 10)}.
        {" "}WINDFOR provides hourly forecasts; FUELHH provides half-hourly actuals. Accuracy metrics are computed from {o?.n || "–"} matched hourly observations.
        {" "}The error band is computed from the same month it is shown on (in-sample), so treat it as indicative, not a validated prediction interval.
      </footer>
    </div>
  );
}
