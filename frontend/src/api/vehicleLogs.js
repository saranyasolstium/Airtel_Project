// src/api/vehicleLogs.js
import { http } from "./http";

export function listVehicleLogs({
  limit = 10,
  offset = 0,
  search = "",
  date_from,
  date_to,
} = {}) {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  if (search) qs.set("search", search);
  if (date_from) qs.set("date_from", date_from);
  if (date_to) qs.set("date_to", date_to);

  return http.request(`/vehicle-logs/?${qs.toString()}`);
}

export function createVehicleLog(payload) {
  return http.request(`/vehicle-logs/`, { method: "POST", body: payload });
}

export function markVehicleExit(id, exit_time) {
  return http.request(`/vehicle-logs/${id}/exit`, {
    method: "PUT",
    body: { exit_time },
  });
}

export function deleteVehicleLog(id) {
  return http.request(`/vehicle-logs/${id}`, { method: "DELETE" });
}
