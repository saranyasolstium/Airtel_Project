// src/api/cameras.js  (swagger-correct)
import { apiRequest } from "./client";

export const CamerasAPI = {
  list: () => apiRequest("/api/cameras"),

  create: (payload) =>
    apiRequest("/api/cameras", { method: "POST", body: payload }),

  update: (cameraId, payload) =>
    apiRequest(`/api/cameras/${encodeURIComponent(cameraId)}`, {
      method: "PUT",
      body: payload,
    }),

  remove: (cameraId) =>
    apiRequest(`/api/cameras/${encodeURIComponent(cameraId)}`, {
      method: "DELETE",
    }),

  // Swagger: GET /api/generate-hls?rtsp_url=...
  generateHls: (rtsp_url) => {
    const qs = new URLSearchParams({ rtsp_url }).toString();
    return apiRequest(`/api/generate-hls?${qs}`);
  },

  // Swagger: POST /api/generate-hls-bulk  { rtsp_urls: [...] }
  generateHlsBulk: (rtsp_urls) =>
    apiRequest("/api/generate-hls-bulk", {
      method: "POST",
      body: { rtsp_urls },
    }),
};
