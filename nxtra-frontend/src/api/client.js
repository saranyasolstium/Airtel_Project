const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function apiRequest(path, options = {}) {
  const { method = "GET", body, headers = {} } = options;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json", ...headers },
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await res.json().catch(() => null);
  if (!res.ok)
    throw new Error(data?.detail || data?.message || `HTTP ${res.status}`);
  return data;
}
