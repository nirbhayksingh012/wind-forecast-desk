export const mw = (v, digits = 0) =>
  v == null || Number.isNaN(v) ? "–" : `${Math.round(v * 10 ** digits) / 10 ** digits}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",");

export const gw = (v) => (v == null ? "–" : (v / 1000).toFixed(1));

export const pct = (v, d = 1) => (v == null ? "–" : `${v.toFixed(d)}%`);

// Elexon timestamps are UTC; the buyer works on UK clock time.
export const ukTime = (iso) =>
  new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/London" });

export const ukDateTime = (iso) =>
  new Date(iso).toLocaleString("en-GB", {
    weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/London",
  });

export const shortDate = (d) =>
  new Date(`${d}T12:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
