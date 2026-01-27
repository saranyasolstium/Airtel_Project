import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

export async function listWhitelist() {
  const res = await axios.get(`${API_BASE}/api/vehicle-whitelist/`);
  return res.data;
}

export async function createWhitelist(payload) {
  const res = await axios.post(`${API_BASE}/api/vehicle-whitelist/`, payload);
  return res.data;
}

export async function updateWhitelist(id, payload) {
  const res = await axios.put(
    `${API_BASE}/api/vehicle-whitelist/${id}`,
    payload,
  );
  return res.data;
}

export async function deleteWhitelist(id) {
  const res = await axios.delete(`${API_BASE}/api/vehicle-whitelist/${id}`);
  return res.data;
}

export async function setWhitelistStatus(id, status) {
  const res = await axios.put(
    `${API_BASE}/api/vehicle-whitelist/${id}/status/${status}`,
  );
  return res.data;
}
