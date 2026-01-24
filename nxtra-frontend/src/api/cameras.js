// src/api/cameras.js
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

  // generate HLS for ONE camera
  generateHls: (rtsp_url) =>
    apiRequest("/api/cameras/generate-hls", {
      method: "POST",
      body: { rtsp_url },
    }),

  // generate HLS for MANY cameras
  generateHlsBulk: (rtsp_urls) =>
    apiRequest("/api/generate-hls-bulk", {
      method: "POST",
      body: { rtsp_urls },
    }),
};
