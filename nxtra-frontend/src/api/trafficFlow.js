// src/api/trafficFlow.js
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000"; // backend host

export async function listTrafficFlowVehicles({
  limit = 10,
  offset = 0,
  dwell_limit_seconds = 7200,
  date,
}) {
  const params = { limit, offset, dwell_limit_seconds };
  if (date) params.date = date;

  const res = await axios.get(`${API_BASE}/api/traffic-flow/vehicles`, {
    params,
  });

  return res.data;
}

// ✅ ADD THIS (export api)
export async function exportTrafficFlowCSV({
  date,
  dwell_limit_seconds = 7200,
}) {
  const params = { dwell_limit_seconds };
  if (date) params.date = date;

  // important: blob
  const res = await axios.get(`${API_BASE}/api/traffic-flow/vehicles/export`, {
    params,
    responseType: "blob",
  });

  return res;
}
