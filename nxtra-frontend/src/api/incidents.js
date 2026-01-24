// src/api/incidents.js
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function listIncidentAlerts(
  { incident_type = "all" } = {},
  { signal } = {},
) {
  const url = new URL(`${BASE_URL}/api/incidents/alerts`);
  url.searchParams.set("incident_type", incident_type);

  const r = await fetch(url.toString(), {
    method: "GET",
    headers: { accept: "application/json" },
    signal,
  });

  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(txt || `Request failed with status code ${r.status}`);
  }

  return r.json(); // expected: array
}
