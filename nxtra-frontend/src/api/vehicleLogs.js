import axios from "axios";

/**
 * Axios instance
 * Adjust baseURL if needed
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://localhost:8000",
  timeout: 15000,
});

/**
 * List vehicle logs
 */
export async function listVehicleLogs(params = {}) {
  const res = await api.get("api/vehicle-logs", {
    params,
  });
  return res.data;
}
