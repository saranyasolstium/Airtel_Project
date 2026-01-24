// src/utils/storage.js
const KEY = "nxtra_auth";

export function saveAuth(payload) {
  localStorage.setItem(KEY, JSON.stringify(payload || {}));
}

export function getAuth() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearAuth() {
  localStorage.removeItem(KEY);
}

export function isAuthed() {
  const a = getAuth();
  return !!a?.token;
}
