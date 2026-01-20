// src/api/trafficFlow.js
import { http } from "./http";

/**
 * Alerts (Dwell Time Alerts)
 * Backend endpoint example:
 *   GET /traffic-flow/alerts?limit=20&offset=0&date=2026-01-20&dwell_limit_seconds=7200
 */
export function listTrafficFlowAlerts({
  limit = 10,
  offset = 0,
  date, // "YYYY-MM-DD"
  dwell_limit_seconds = 7200,
} = {}) {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  if (date) qs.set("date", date);
  if (dwell_limit_seconds != null)
    qs.set("dwell_limit_seconds", String(dwell_limit_seconds));

  return http.request(`/traffic-flow/alerts?${qs.toString()}`);
}

/**
 * Vehicles list (optional, if you use it)
 * Example:
 *   GET /traffic-flow/vehicles?limit=20&offset=0&date=2026-01-20
 */
export function listTrafficFlowVehicles({
  limit = 10,
  offset = 0,
  date, // "YYYY-MM-DD"
} = {}) {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  if (date) qs.set("date", date);

  return http.request(`/traffic-flow/vehicles?${qs.toString()}`);
}
