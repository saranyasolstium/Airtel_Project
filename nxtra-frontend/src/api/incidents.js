// src/api/incidents.js
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Get alerts list
 * Supports:
 *  - incident_type (all/crowd/unauthorized/door_open/door_close/...)
 *  - status (all/active/resolved)
 *  - camera_name (optional)
 *  - object_type (optional)
 */
export async function listIncidentAlerts(
  {
    incident_type = "all",
    status = "active",
    camera_name = "",
    object_type = "",
  } = {},
  { signal } = {},
) {
  const url = new URL(`${BASE_URL}/api/incidents/alerts`);
  url.searchParams.set("incident_type", incident_type);
  url.searchParams.set("status", status);

  if (camera_name) url.searchParams.set("camera_name", camera_name);
  if (object_type) url.searchParams.set("object_type", object_type);

  const r = await fetch(url.toString(), {
    method: "GET",
    headers: { accept: "application/json" },
    signal,
  });

  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(txt || `Request failed with status code ${r.status}`);
  }

  return r.json(); // array
}

/**
 * ✅ NEW: Get filter dropdown values from backend
 * returns: { cameras: [], object_types: [] }
 */
export async function getIncidentFilters({ signal } = {}) {
  const url = new URL(`${BASE_URL}/api/incidents/alerts/filters`);

  const r = await fetch(url.toString(), {
    method: "GET",
    headers: { accept: "application/json" },
    signal,
  });

  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(txt || `Request failed with status code ${r.status}`);
  }

  return r.json();
}

/**
 * ✅ NEW: Manual resolve (for unauthorized etc)
 * PUT /api/incidents/alerts/{id}/resolve
 */
export async function resolveIncidentAlert(alert_id) {
  const url = `${BASE_URL}/api/incidents/alerts/${alert_id}/resolve`;

  const r = await fetch(url, {
    method: "PUT",
    headers: { accept: "application/json" },
  });

  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(txt || `Resolve failed with status code ${r.status}`);
  }

  return r.json();
}

// // src/api/incidents.js
// const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

// export async function listIncidentAlerts(
//   { incident_type = "all" } = {},
//   { signal } = {},
// ) {
//   const url = new URL(`${BASE_URL}/api/incidents/alerts`);
//   url.searchParams.set("incident_type", incident_type);

//   const r = await fetch(url.toString(), {
//     method: "GET",
//     headers: { accept: "application/json" },
//     signal,
//   });

//   if (!r.ok) {
//     const txt = await r.text().catch(() => "");
//     throw new Error(txt || `Request failed with status code ${r.status}`);
//   }

//   return r.json(); // expected: array
// }
