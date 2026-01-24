import { apiRequest } from "./client";

export function registerApi({ full_name, email, password }) {
  return apiRequest("/api/auth/register", {
    method: "POST",
    body: { full_name, email, password },
  });
}

export function loginApi({ email, password }) {
  return apiRequest("/api/auth/login", {
    method: "POST",
    body: { email, password },
  });
}
