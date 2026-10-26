async function get(path, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`/api${path}${qs ? `?${qs}` : ""}`);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  meta: () => get("/meta"),
  forecast: (delivery_date, cutoff) => get("/forecast", { delivery_date, cutoff }),
  accuracy: (cutoff) => get("/accuracy", { cutoff }),
  sensitivity: () => get("/cutoff-sensitivity"),
};
