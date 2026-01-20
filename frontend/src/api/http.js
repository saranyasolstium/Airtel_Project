// src/api/http.js
export const API_BASE =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api";

async function request(path, { method = "GET", body, headers } = {}) {
  const isForm = body instanceof FormData;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...(headers || {}),
    },
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }

  // handle empty response (204 etc.)
  const ct = res.headers.get("content-type") || "";
  if (!ct.includes("application/json")) return null;

  return res.json();
}

export const http = { request };
