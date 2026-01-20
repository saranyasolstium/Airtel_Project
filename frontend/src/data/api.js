const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function getJson(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export const api = {
  stats: () => getJson("/api/stats"),
  alerts: () => getJson("/api/alerts"),
  cameras: () => getJson("/api/cameras"),
  vehicles: () => getJson("/api/vehicles"),
  ppe: () => getJson("/api/ppe"),
  traffic: () => getJson("/api/traffic"),
  zones: () => getJson("/api/zones"),
};
