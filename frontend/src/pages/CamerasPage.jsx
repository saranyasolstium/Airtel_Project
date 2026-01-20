// src/pages/CamerasPage.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import Hls from "hls.js";
import {
  Camera,
  Plus,
  Edit2,
  Trash2,
  Search,
  RefreshCw,
  Eye,
  X,
  AlertCircle,
  Maximize2,
  PlayCircle,
  Loader2,
} from "lucide-react";

// ✅ API
const API_BASE_URL = "http://localhost:8000/api";

/* ------------------------- Small helpers ------------------------- */
const safeJson = async (res) => {
  try {
    return await res.json();
  } catch {
    return null;
  }
};

const extractBulkMap = (payload) => {
  const map = {};
  if (!payload) return map;

  if (Array.isArray(payload)) {
    payload.forEach((x) => {
      const k = x?.rtsp_url || x?.input || x?.url;
      const v = x?.hls_url || x?.hls || x?.output;
      if (k && v) map[k] = v;
    });
    return map;
  }

  if (payload.map && typeof payload.map === "object") {
    Object.entries(payload.map).forEach(([k, v]) => {
      if (k && v) map[k] = v;
    });
    return map;
  }

  const arr = payload.items || payload.results || payload.data;
  if (Array.isArray(arr)) {
    arr.forEach((x) => {
      const k = x?.rtsp_url || x?.input || x?.url;
      const v = x?.hls_url || x?.hls || x?.output;
      if (k && v) map[k] = v;
    });
  }
  return map;
};

/* ------------------------- HLS Preview (card) ------------------------- */
const HlsPreview = ({ hlsUrl, isLive, onLiveChange }) => {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // cleanup old
    if (hlsRef.current) {
      try {
        hlsRef.current.destroy();
      } catch {}
      hlsRef.current = null;
    }

    if (!hlsUrl) {
      video.removeAttribute("src");
      video.load();
      onLiveChange?.(false);
      return;
    }

    // Native HLS (Safari)
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = hlsUrl;
      video
        .play()
        .then(() => onLiveChange?.(true))
        .catch(() => onLiveChange?.(false));
      return;
    }

    // HLS.js
    if (Hls.isSupported()) {
      const hls = new Hls({
        lowLatencyMode: true,
        enableWorker: true,
        backBufferLength: 30,
      });
      hlsRef.current = hls;

      hls.loadSource(hlsUrl);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video
          .play()
          .then(() => onLiveChange?.(true))
          .catch(() => onLiveChange?.(false));
      });

      // ✅ More reliable live detection: when fragments load, stream is actually flowing
      hls.on(Hls.Events.FRAG_LOADED, () => {
        onLiveChange?.(true);
      });

      hls.on(Hls.Events.ERROR, (_, data) => {
        if (!data?.fatal) return;

        onLiveChange?.(false);

        try {
          if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
            hls.startLoad();
          } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
            hls.recoverMediaError();
          } else {
            hls.destroy();
          }
        } catch {}
      });

      return () => {
        try {
          hls.destroy();
        } catch {}
      };
    }
  }, [hlsUrl, onLiveChange]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // ✅ Use correct events for "Live"
    const onPlaying = () => onLiveChange?.(true);
    const onWaiting = () => onLiveChange?.(false);
    const onStalled = () => onLiveChange?.(false);
    const onPause = () => onLiveChange?.(false);
    const onError = () => onLiveChange?.(false);

    video.addEventListener("playing", onPlaying);
    video.addEventListener("waiting", onWaiting);
    video.addEventListener("stalled", onStalled);
    video.addEventListener("pause", onPause);
    video.addEventListener("error", onError);

    return () => {
      video.removeEventListener("playing", onPlaying);
      video.removeEventListener("waiting", onWaiting);
      video.removeEventListener("stalled", onStalled);
      video.removeEventListener("pause", onPause);
      video.removeEventListener("error", onError);
    };
  }, [onLiveChange]);

  return (
    <div className="absolute inset-0">
      {hlsUrl ? (
        <video
          ref={videoRef}
          muted
          playsInline
          autoPlay
          className="w-full h-full object-cover bg-black"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center">
          <div className="flex flex-col items-center">
            <Camera className="w-12 h-12 text-gray-400 mb-2" />
            <span className="text-gray-500 text-sm">No Stream</span>
          </div>
        </div>
      )}

      {/* status badge */}
      <div className="absolute bottom-3 left-3 pointer-events-none">
        {hlsUrl ? (
          <span
            className={`text-xs font-medium px-2 py-1 rounded border shadow-sm ${
              isLive
                ? "bg-green-100 text-green-700 border-green-200"
                : "bg-yellow-100 text-yellow-700 border-yellow-200"
            }`}
          >
            {isLive ? "Live" : "Loading..."}
          </span>
        ) : (
          <span className="text-xs font-medium px-2 py-1 rounded bg-gray-100 text-gray-700 border border-gray-200 shadow-sm">
            Not Generated
          </span>
        )}
      </div>
    </div>
  );
};

/* ------------------------- Fullscreen Stream Modal ------------------------- */
const FullViewModal = ({ camera, onClose }) => {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);

  useEffect(() => {
    const onEsc = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onEsc);
    return () => window.removeEventListener("keydown", onEsc);
  }, [onClose]);

  useEffect(() => {
    if (hlsRef.current) {
      try {
        hlsRef.current.destroy();
      } catch {}
      hlsRef.current = null;
    }

    const video = videoRef.current;
    const url = camera?.hls_url;

    if (!video || !url) return;

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = url;
      video.play().catch(() => {});
      return;
    }

    if (Hls.isSupported()) {
      const hls = new Hls({ lowLatencyMode: true, enableWorker: true });
      hlsRef.current = hls;
      hls.loadSource(url);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => {});
      });

      return () => {
        try {
          hls.destroy();
        } catch {}
      };
    }
  }, [camera]);

  if (!camera) return null;

  return (
    // ✅ click outside closes
    <div
      className="fixed inset-0 z-[9999] bg-black/80 backdrop-blur-sm"
      onMouseDown={(e) => {
        // only close if clicking backdrop (not inner content)
        if (e.target === e.currentTarget) onClose?.();
      }}
    >
      <div className="absolute top-0 left-0 right-0 h-14 flex items-center justify-between px-4 bg-black/50 border-b border-white/10 z-10">
        <div className="text-white">
          <div className="text-sm font-semibold">{camera.name}</div>
          <div className="text-xs text-white/70">ID: {camera.camera_id}</div>
        </div>

        {/* ✅ Close button fix */}
        <button
          type="button"
          onMouseDown={(e) => e.stopPropagation()}
          onClick={(e) => {
            e.stopPropagation();
            onClose?.();
          }}
          className="pointer-events-auto p-2 rounded-lg hover:bg-white/10 text-white"
          title="Close"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="absolute inset-0 pt-14 flex items-center justify-center p-4">
        <div className="w-full h-full max-w-6xl">
          <div className="w-full h-full bg-black rounded-xl overflow-hidden border border-white/10 shadow-2xl">
            {camera.hls_url ? (
              <video
                ref={videoRef}
                controls
                autoPlay
                muted
                playsInline
                className="w-full h-full object-contain bg-black"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-white/70">
                HLS URL not available for this camera.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

/* ------------------------- View Camera Modal ------------------------- */
const ViewCameraModal = ({ camera, onClose }) => {
  if (!camera) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-lg rounded-xl border border-gray-200 shadow-xl overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-900">Camera Details</h3>
          <button onClick={onClose} className="p-2 rounded hover:bg-gray-100">
            <X className="w-5 h-5 text-gray-700" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div className="text-gray-500">Camera ID</div>
            <div className="col-span-2 font-semibold text-gray-900">
              {camera.camera_id}
            </div>

            <div className="text-gray-500">Name</div>
            <div className="col-span-2 font-semibold text-gray-900">
              {camera.name}
            </div>

            <div className="text-gray-500">RTSP</div>
            <div className="col-span-2">
              {camera.rtsp_url ? (
                <div className="break-all text-gray-800 bg-gray-50 border border-gray-200 rounded p-2 font-mono text-xs">
                  {camera.rtsp_url}
                </div>
              ) : (
                <span className="text-gray-500">Not configured</span>
              )}
            </div>

            <div className="text-gray-500">HLS</div>
            <div className="col-span-2">
              {camera.hls_url ? (
                <div className="break-all text-gray-800 bg-gray-50 border border-gray-200 rounded p-2 font-mono text-xs">
                  {camera.hls_url}
                </div>
              ) : (
                <span className="text-gray-500">Not generated</span>
              )}
            </div>

            <div className="text-gray-500">Created</div>
            <div className="col-span-2 text-gray-800">
              {camera.created_at
                ? new Date(camera.created_at).toLocaleString()
                : "-"}
            </div>

            <div className="text-gray-500">Updated</div>
            <div className="col-span-2 text-gray-800">
              {camera.updated_at
                ? new Date(camera.updated_at).toLocaleString()
                : camera.created_at
                ? new Date(camera.created_at).toLocaleString()
                : "-"}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-gray-200 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 border border-gray-300 text-gray-800"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

/* ------------------------- Confirm Delete Modal ------------------------- */
const ConfirmDeleteModal = ({ camera, onClose, onConfirm, loading }) => {
  if (!camera) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-md rounded-xl border border-gray-200 shadow-xl overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
            <Trash2 className="w-5 h-5 text-red-600" />
          </div>
          <h3 className="text-lg font-bold text-gray-900">Delete Camera</h3>
        </div>

        <div className="p-5 text-sm text-gray-800 space-y-2">
          <p>
            Are you sure you want to delete{" "}
            <span className="font-semibold">{camera.name}</span>?
          </p>
          <div className="bg-gray-50 border border-gray-200 rounded p-3">
            <div className="text-xs text-gray-500">Camera ID</div>
            <div className="font-mono text-sm">{camera.camera_id}</div>
          </div>
        </div>

        <div className="p-4 border-t border-gray-200 flex justify-end gap-2">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 border border-gray-300 text-gray-800 disabled:opacity-60"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="px-4 py-2 rounded bg-red-600 hover:bg-red-700 text-white disabled:opacity-60"
          >
            {loading ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
};

/* ------------------------- Camera Card ------------------------- */
const CameraCard = ({ camera, onEdit, onDelete, onView, onFullView }) => {
  const [isLive, setIsLive] = useState(false);

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:border-blue-200 transition-all group shadow-sm">
      <div className="relative aspect-video bg-gradient-to-br from-gray-50 to-gray-100 overflow-hidden">
        <HlsPreview
          hlsUrl={camera.hls_url}
          isLive={isLive}
          onLiveChange={setIsLive}
        />

        <div className="absolute top-3 left-3">
          <span className="text-xs font-medium px-2 py-1 rounded bg-blue-100 text-blue-700 border border-blue-200">
            ID: {camera.camera_id}
          </span>
        </div>

        {/* top-right actions */}
        <div className="absolute top-3 right-3 flex gap-1">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onFullView(camera);
            }}
            className="p-1.5 bg-white/90 hover:bg-gray-100 rounded border border-gray-300 shadow-sm"
            title="Full View"
          >
            <Maximize2 className="w-4 h-4 text-gray-700" />
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              onView(camera);
            }}
            className="p-1.5 bg-white/90 hover:bg-gray-100 rounded border border-gray-300 shadow-sm"
            title="View Details"
          >
            <Eye className="w-4 h-4 text-gray-700" />
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(camera);
            }}
            className="p-1.5 bg-white/90 hover:bg-blue-50 rounded border border-blue-300 shadow-sm"
            title="Edit"
          >
            <Edit2 className="w-4 h-4 text-blue-600" />
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(camera);
            }}
            className="p-1.5 bg-white/90 hover:bg-red-50 rounded border border-red-300 shadow-sm"
            title="Delete"
          >
            <Trash2 className="w-4 h-4 text-red-600" />
          </button>
        </div>

        {/* ✅ Regen button removed */}
      </div>

      <div className="p-4">
        <h3 className="text-gray-800 font-semibold text-sm mb-1 truncate">
          {camera.name}
        </h3>
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">
            Created:{" "}
            {camera.created_at
              ? new Date(camera.created_at).toLocaleDateString()
              : "-"}
          </span>
          <span className="text-gray-500">
            Updated:{" "}
            {camera.updated_at || camera.created_at
              ? new Date(
                  camera.updated_at || camera.created_at
                ).toLocaleDateString()
              : "-"}
          </span>
        </div>
      </div>
    </div>
  );
};

/* ------------------------- Form Modal ------------------------- */
const CameraFormModal = ({ camera, onClose, onSave, mode = "create" }) => {
  const [formData, setFormData] = useState({
    camera_id: camera?.camera_id || "",
    name: camera?.name || "",
    rtsp_url: camera?.rtsp_url || "",
  });
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    if (!formData.camera_id.trim())
      newErrors.camera_id = "Camera ID is required";
    if (!formData.name.trim()) newErrors.name = "Camera name is required";
    if (formData.rtsp_url && !formData.rtsp_url.startsWith("rtsp://")) {
      newErrors.rtsp_url = "RTSP URL should start with rtsp://";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    try {
      await onSave(formData);
    } catch (error) {
      setErrors({ submit: error.message });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white border border-gray-200 rounded-lg max-w-md w-full shadow-xl">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-800">
            {mode === "create" ? "Add New Camera" : "Edit Camera"}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Camera ID *
            </label>
            <input
              type="text"
              value={formData.camera_id}
              onChange={(e) =>
                setFormData({ ...formData, camera_id: e.target.value })
              }
              className={`w-full px-3 py-2 border rounded text-gray-800 focus:outline-none ${
                errors.camera_id
                  ? "border-red-500"
                  : "border-gray-300 focus:border-blue-500"
              }`}
              placeholder="e.g., CAM-001"
              required
              disabled={mode === "edit"}
            />
            {errors.camera_id && (
              <p className="mt-1 text-xs text-red-600">{errors.camera_id}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Camera Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              className={`w-full px-3 py-2 border rounded text-gray-800 focus:outline-none ${
                errors.name
                  ? "border-red-500"
                  : "border-gray-300 focus:border-blue-500"
              }`}
              placeholder="e.g., Main Entrance Camera"
              required
            />
            {errors.name && (
              <p className="mt-1 text-xs text-red-600">{errors.name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              RTSP URL
            </label>
            <input
              type="text"
              value={formData.rtsp_url}
              onChange={(e) =>
                setFormData({ ...formData, rtsp_url: e.target.value })
              }
              className={`w-full px-3 py-2 border rounded text-gray-800 focus:outline-none ${
                errors.rtsp_url
                  ? "border-red-500"
                  : "border-gray-300 focus:border-blue-500"
              }`}
              placeholder="rtsp://username:password@ip:port/path"
            />
            {errors.rtsp_url && (
              <p className="mt-1 text-xs text-red-600">{errors.rtsp_url}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Optional: Enter RTSP stream URL for live viewing
            </p>
          </div>

          {errors.submit && (
            <div className="p-3 bg-red-50 border border-red-200 rounded">
              <p className="text-sm text-red-600">{errors.submit}</p>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            >
              {mode === "create" ? "Add Camera" : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

/* ------------------------- Page ------------------------- */
const CamerasPage = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  // modals
  const [showForm, setShowForm] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [formMode, setFormMode] = useState("create");

  const [viewCamera, setViewCamera] = useState(null);
  const [deleteCamera, setDeleteCamera] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const [fullViewCamera, setFullViewCamera] = useState(null);

  // avoid calling bulk repeatedly on every render
  const bulkRanRef = useRef(false);

  useEffect(() => {
    fetchCameras();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    // ✅ Auto-generate HLS once after cameras are loaded
    if (!loading && cameras.length > 0 && !bulkRanRef.current) {
      bulkRanRef.current = true;
      generateAllHlsForCameras(cameras).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, cameras]);

  const fetchCameras = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/cameras/`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const items = data?.items || data || [];
      setCameras(Array.isArray(items) ? items : []);
      setError(null);
      bulkRanRef.current = false;
    } catch (err) {
      setError(`Failed to fetch cameras: ${err.message}`);
      console.error("Error fetching cameras:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredCameras = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return cameras;
    return cameras.filter((c) => {
      const id = (c.camera_id || "").toLowerCase();
      const name = (c.name || "").toLowerCase();
      return id.includes(q) || name.includes(q);
    });
  }, [cameras, searchQuery]);

  /* ------------------------- HLS generation ------------------------- */
  const generateAllHlsForCameras = async (cameraList) => {
    const rtspUrls = cameraList
      .map((c) => c.rtsp_url)
      .filter((u) => typeof u === "string" && u.startsWith("rtsp://"));

    if (rtspUrls.length === 0) return;

    setGenerating(true);
    try {
      const res = await fetch(`${API_BASE_URL}/generate-hls-bulk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rtsp_urls: rtspUrls }),
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || `Bulk HLS failed (HTTP ${res.status})`);
      }

      const payload = await safeJson(res);
      const map = extractBulkMap(payload);

      setCameras((prev) =>
        prev.map((c) => {
          const hls = c.rtsp_url ? map[c.rtsp_url] : null;
          return hls ? { ...c, hls_url: hls } : c;
        })
      );
    } finally {
      setGenerating(false);
    }
  };

  const generateOne = async (camera) => {
    if (!camera?.rtsp_url) return;
    setGenerating(true);
    try {
      const url = `${API_BASE_URL}/generate-hls?rtsp_url=${encodeURIComponent(
        camera.rtsp_url
      )}`;
      const res = await fetch(url);
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || `Generate failed (HTTP ${res.status})`);
      }
      const data = await safeJson(res);
      const hls = data?.hls_url;
      if (!hls) throw new Error("HLS URL not returned by API.");

      setCameras((prev) =>
        prev.map((c) =>
          c.camera_id === camera.camera_id ? { ...c, hls_url: hls } : c
        )
      );
    } finally {
      setGenerating(false);
    }
  };

  /* ------------------------- CRUD ------------------------- */
  const handleAddCamera = () => {
    setSelectedCamera(null);
    setFormMode("create");
    setShowForm(true);
  };

  const handleEditCamera = (camera) => {
    setSelectedCamera(camera);
    setFormMode("edit");
    setShowForm(true);
  };

  const handleDeleteCamera = (camera) => {
    setDeleteCamera(camera);
  };

  const confirmDelete = async () => {
    if (!deleteCamera) return;
    try {
      setDeleteLoading(true);
      const response = await fetch(
        `${API_BASE_URL}/cameras/${deleteCamera.camera_id}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText || "Failed to delete camera");
      }

      setCameras((prev) =>
        prev.filter((c) => c.camera_id !== deleteCamera.camera_id)
      );
      setDeleteCamera(null);
    } catch (err) {
      alert(`Error deleting camera: ${err.message}`);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleSaveCamera = async (cameraData) => {
    const url = `${API_BASE_URL}/cameras${
      formMode === "edit" ? `/${cameraData.camera_id}` : ""
    }`;
    const method = formMode === "create" ? "POST" : "PUT";

    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cameraData),
    });

    if (!response.ok) {
      const errorData = await safeJson(response);
      throw new Error(errorData?.detail || "Failed to save camera");
    }

    const savedCamera = await response.json();

    setCameras((prev) => {
      if (formMode === "create") return [savedCamera, ...prev];
      return prev.map((c) =>
        c.camera_id === savedCamera.camera_id ? savedCamera : c
      );
    });

    setShowForm(false);

    // ✅ if RTSP present, auto-generate stream for this one
    if (savedCamera?.rtsp_url?.startsWith("rtsp://")) {
      generateOne(savedCamera).catch(() => {});
    }
  };

  return (
    <div className="space-y-4">
      {/* Search + actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Camera ID or Name..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={fetchCameras}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg transition-colors"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>

          <button
            onClick={handleAddCamera}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Camera
          </button>
        </div>
      </div>

      {/* Grid */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-800">Cameras</h2>
          <span className="text-gray-600 text-sm">
            {loading ? "Loading..." : `${filteredCameras.length} cameras found`}
          </span>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto" />
            <p className="text-gray-600 mt-2">Loading cameras...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <AlertCircle className="w-8 h-8 text-red-600 mx-auto" />
            <p className="text-gray-800 font-medium mt-2">
              Error loading cameras
            </p>
            <p className="text-gray-600 text-sm mt-1">{error}</p>
            <button
              onClick={fetchCameras}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            >
              Retry
            </button>
          </div>
        ) : filteredCameras.length === 0 ? (
          <div className="text-center py-12">
            <Camera className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-800 font-medium">No cameras found</p>
            <p className="text-gray-600 text-sm mt-1">
              {searchQuery
                ? "Try a different search term"
                : "Add your first camera to get started"}
            </p>
            <button
              onClick={handleAddCamera}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            >
              Add Camera
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCameras.map((camera) => (
              <CameraCard
                key={camera.id || camera.camera_id}
                camera={camera}
                onEdit={handleEditCamera}
                onDelete={handleDeleteCamera}
                onView={(cam) => setViewCamera(cam)}
                onFullView={(cam) => setFullViewCamera(cam)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {showForm && (
        <CameraFormModal
          camera={selectedCamera}
          onClose={() => setShowForm(false)}
          onSave={handleSaveCamera}
          mode={formMode}
        />
      )}

      {viewCamera && (
        <ViewCameraModal
          camera={viewCamera}
          onClose={() => setViewCamera(null)}
        />
      )}

      {deleteCamera && (
        <ConfirmDeleteModal
          camera={deleteCamera}
          onClose={() => setDeleteCamera(null)}
          onConfirm={confirmDelete}
          loading={deleteLoading}
        />
      )}

      {fullViewCamera && (
        <FullViewModal
          camera={fullViewCamera}
          onClose={() => setFullViewCamera(null)}
        />
      )}
    </div>
  );
};

export default CamerasPage;

// // src/pages/CamerasPage.jsx
// import React, { useEffect, useMemo, useState } from "react";
// import {
//   Camera,
//   Plus,
//   Edit2,
//   Trash2,
//   Search,
//   RefreshCw,
//   Eye,
//   X,
//   AlertCircle,
//   CheckCircle,
// } from "lucide-react";

// // API
// const API_BASE_URL = "http://localhost:8000/api";

// /* ------------------------- View Camera Modal ------------------------- */
// const ViewCameraModal = ({ camera, onClose }) => {
//   if (!camera) return null;

//   return (
//     <div className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4">
//       <div className="bg-white w-full max-w-lg rounded-xl border border-gray-200 shadow-xl overflow-hidden">
//         <div className="p-4 border-b border-gray-200 flex items-center justify-between">
//           <div>
//             <h3 className="text-lg font-bold text-gray-900">Camera Details</h3>
//           </div>
//           <button onClick={onClose} className="p-2 rounded hover:bg-gray-100">
//             <X className="w-5 h-5 text-gray-700" />
//           </button>
//         </div>

//         <div className="p-5 space-y-4">
//           <div className="grid grid-cols-3 gap-3 text-sm">
//             <div className="text-gray-500">Camera ID</div>
//             <div className="col-span-2 font-semibold text-gray-900">
//               {camera.camera_id}
//             </div>

//             <div className="text-gray-500">Name</div>
//             <div className="col-span-2 font-semibold text-gray-900">
//               {camera.name}
//             </div>

//             <div className="text-gray-500">RTSP</div>
//             <div className="col-span-2">
//               {camera.rtsp_url ? (
//                 <div className="flex items-start gap-2">
//                   <div className="flex-1 break-all text-gray-800 bg-gray-50 border border-gray-200 rounded p-2 font-mono text-xs">
//                     {camera.rtsp_url}
//                   </div>
//                 </div>
//               ) : (
//                 <span className="text-gray-500">Not configured</span>
//               )}
//             </div>

//             <div className="text-gray-500">Created</div>
//             <div className="col-span-2 text-gray-800">
//               {camera.created_at
//                 ? new Date(camera.created_at).toLocaleString()
//                 : "-"}
//             </div>

//             <div className="text-gray-500">Updated</div>
//             <div className="col-span-2 text-gray-800">
//               {camera.updated_at
//                 ? new Date(camera.updated_at).toLocaleString()
//                 : camera.created_at
//                 ? new Date(camera.created_at).toLocaleString()
//                 : "-"}
//             </div>
//           </div>
//         </div>

//         <div className="p-4 border-t border-gray-200 flex justify-end gap-2">
//           <button
//             onClick={onClose}
//             className="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 border border-gray-300 text-gray-800"
//           >
//             Close
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// };

// /* ------------------------- Confirm Delete Modal ------------------------- */
// const ConfirmDeleteModal = ({ camera, onClose, onConfirm, loading }) => {
//   if (!camera) return null;

//   return (
//     <div className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4">
//       <div className="bg-white w-full max-w-md rounded-xl border border-gray-200 shadow-xl overflow-hidden">
//         <div className="p-4 border-b border-gray-200 flex items-center gap-3">
//           <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
//             <Trash2 className="w-5 h-5 text-red-600" />
//           </div>
//           <div>
//             <h3 className="text-lg font-bold text-gray-900">Delete Camera</h3>
//           </div>
//         </div>

//         <div className="p-5 text-sm text-gray-800 space-y-2">
//           <p>
//             Are you sure you want to delete{" "}
//             <span className="font-semibold">{camera.name}</span>?
//           </p>
//           <div className="bg-gray-50 border border-gray-200 rounded p-3">
//             <div className="text-xs text-gray-500">Camera ID</div>
//             <div className="font-mono text-sm">{camera.camera_id}</div>
//           </div>
//         </div>

//         <div className="p-4 border-t border-gray-200 flex justify-end gap-2">
//           <button
//             onClick={onClose}
//             disabled={loading}
//             className="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 border border-gray-300 text-gray-800 disabled:opacity-60"
//           >
//             Cancel
//           </button>
//           <button
//             onClick={onConfirm}
//             disabled={loading}
//             className="px-4 py-2 rounded bg-red-600 hover:bg-red-700 text-white disabled:opacity-60"
//           >
//             {loading ? "Deleting..." : "Delete"}
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// };

// /* ------------------------- Camera Card ------------------------- */
// const CameraCard = ({ camera, onEdit, onDelete, onView }) => {
//   return (
//     <div className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:border-blue-200 transition-all group shadow-sm">
//       <div className="relative aspect-video bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
//         <div className="relative z-10 flex flex-col items-center justify-center">
//           <Camera className="w-12 h-12 text-gray-400 mb-2" />
//           <span className="text-gray-500 text-sm">RTSP Camera</span>
//         </div>

//         <div className="absolute top-3 left-3">
//           <span className="text-xs font-medium px-2 py-1 rounded bg-blue-100 text-blue-700 border border-blue-200">
//             ID: {camera.camera_id}
//           </span>
//         </div>

//         <div className="absolute top-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
//           <button
//             onClick={(e) => {
//               e.stopPropagation();
//               onView(camera);
//             }}
//             className="p-1.5 bg-white/90 hover:bg-gray-100 rounded border border-gray-300 shadow-sm"
//             title="View Details"
//           >
//             <Eye className="w-4 h-4 text-gray-700" />
//           </button>
//           <button
//             onClick={(e) => {
//               e.stopPropagation();
//               onEdit(camera);
//             }}
//             className="p-1.5 bg-white/90 hover:bg-blue-50 rounded border border-blue-300 shadow-sm"
//             title="Edit"
//           >
//             <Edit2 className="w-4 h-4 text-blue-600" />
//           </button>
//           <button
//             onClick={(e) => {
//               e.stopPropagation();
//               onDelete(camera);
//             }}
//             className="p-1.5 bg-white/90 hover:bg-red-50 rounded border border-red-300 shadow-sm"
//             title="Delete"
//           >
//             <Trash2 className="w-4 h-4 text-red-600" />
//           </button>
//         </div>

//         <div className="absolute bottom-3 right-3"></div>
//       </div>

//       <div className="p-4">
//         <h3 className="text-gray-800 font-semibold text-sm mb-1 truncate">
//           {camera.name}
//         </h3>
//         <div className="flex items-center justify-between text-xs">
//           <span className="text-gray-500">
//             Created:{" "}
//             {camera.created_at
//               ? new Date(camera.created_at).toLocaleDateString()
//               : "-"}
//           </span>
//           <span className="text-gray-500">
//             Updated:{" "}
//             {camera.updated_at || camera.created_at
//               ? new Date(
//                   camera.updated_at || camera.created_at
//                 ).toLocaleDateString()
//               : "-"}
//           </span>
//         </div>
//       </div>
//     </div>
//   );
// };

// /* ------------------------- Form Modal ------------------------- */
// const CameraFormModal = ({ camera, onClose, onSave, mode = "create" }) => {
//   const [formData, setFormData] = useState({
//     camera_id: camera?.camera_id || "",
//     name: camera?.name || "",
//     rtsp_url: camera?.rtsp_url || "",
//   });
//   const [errors, setErrors] = useState({});

//   const validateForm = () => {
//     const newErrors = {};
//     if (!formData.camera_id.trim())
//       newErrors.camera_id = "Camera ID is required";
//     if (!formData.name.trim()) newErrors.name = "Camera name is required";
//     if (formData.rtsp_url && !formData.rtsp_url.startsWith("rtsp://")) {
//       newErrors.rtsp_url = "RTSP URL should start with rtsp://";
//     }
//     setErrors(newErrors);
//     return Object.keys(newErrors).length === 0;
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     if (!validateForm()) return;

//     try {
//       await onSave(formData);
//     } catch (error) {
//       setErrors({ submit: error.message });
//     }
//   };

//   return (
//     <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
//       <div className="bg-white border border-gray-200 rounded-lg max-w-md w-full shadow-xl">
//         <div className="p-4 border-b border-gray-200 flex items-center justify-between">
//           <h2 className="text-lg font-bold text-gray-800">
//             {mode === "create" ? "Add New Camera" : "Edit Camera"}
//           </h2>
//           <button
//             onClick={onClose}
//             className="text-gray-500 hover:text-gray-800 transition-colors"
//           >
//             <X className="w-5 h-5" />
//           </button>
//         </div>

//         <form onSubmit={handleSubmit} className="p-6 space-y-4">
//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               Camera ID *
//             </label>
//             <input
//               type="text"
//               value={formData.camera_id}
//               onChange={(e) =>
//                 setFormData({ ...formData, camera_id: e.target.value })
//               }
//               className={`w-full px-3 py-2 border rounded text-gray-800 focus:outline-none ${
//                 errors.camera_id
//                   ? "border-red-500"
//                   : "border-gray-300 focus:border-blue-500"
//               }`}
//               placeholder="e.g., CAM-001"
//               required
//               disabled={mode === "edit"}
//             />
//             {errors.camera_id && (
//               <p className="mt-1 text-xs text-red-600">{errors.camera_id}</p>
//             )}
//           </div>

//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               Camera Name *
//             </label>
//             <input
//               type="text"
//               value={formData.name}
//               onChange={(e) =>
//                 setFormData({ ...formData, name: e.target.value })
//               }
//               className={`w-full px-3 py-2 border rounded text-gray-800 focus:outline-none ${
//                 errors.name
//                   ? "border-red-500"
//                   : "border-gray-300 focus:border-blue-500"
//               }`}
//               placeholder="e.g., Main Entrance Camera"
//               required
//             />
//             {errors.name && (
//               <p className="mt-1 text-xs text-red-600">{errors.name}</p>
//             )}
//           </div>

//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               RTSP URL
//             </label>
//             <input
//               type="text"
//               value={formData.rtsp_url}
//               onChange={(e) =>
//                 setFormData({ ...formData, rtsp_url: e.target.value })
//               }
//               className={`w-full px-3 py-2 border rounded text-gray-800 focus:outline-none ${
//                 errors.rtsp_url
//                   ? "border-red-500"
//                   : "border-gray-300 focus:border-blue-500"
//               }`}
//               placeholder="rtsp://username:password@ip:port/path"
//             />
//             {errors.rtsp_url && (
//               <p className="mt-1 text-xs text-red-600">{errors.rtsp_url}</p>
//             )}
//             <p className="mt-1 text-xs text-gray-500">
//               Optional: Enter RTSP stream URL for live viewing
//             </p>
//           </div>

//           {errors.submit && (
//             <div className="p-3 bg-red-50 border border-red-200 rounded">
//               <p className="text-sm text-red-600">{errors.submit}</p>
//             </div>
//           )}

//           <div className="flex gap-3 pt-4">
//             <button
//               type="button"
//               onClick={onClose}
//               className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded transition-colors"
//             >
//               Cancel
//             </button>
//             <button
//               type="submit"
//               className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
//             >
//               {mode === "create" ? "Add Camera" : "Save Changes"}
//             </button>
//           </div>
//         </form>
//       </div>
//     </div>
//   );
// };

// /* ------------------------- Page ------------------------- */
// const CamerasPage = () => {
//   const [cameras, setCameras] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);

//   // auto-filter client side
//   const [searchQuery, setSearchQuery] = useState("");

//   // modals
//   const [showForm, setShowForm] = useState(false);
//   const [selectedCamera, setSelectedCamera] = useState(null);
//   const [formMode, setFormMode] = useState("create");

//   const [viewCamera, setViewCamera] = useState(null);

//   const [deleteCamera, setDeleteCamera] = useState(null);
//   const [deleteLoading, setDeleteLoading] = useState(false);

//   useEffect(() => {
//     fetchCameras();
//   }, []);

//   const fetchCameras = async () => {
//     try {
//       setLoading(true);
//       const response = await fetch(`${API_BASE_URL}/cameras/`);
//       if (!response.ok) throw new Error(`HTTP ${response.status}`);

//       const data = await response.json();
//       setCameras(data.items || []);
//       setError(null);
//     } catch (err) {
//       setError(`Failed to fetch cameras: ${err.message}`);
//       console.error("Error fetching cameras:", err);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const filteredCameras = useMemo(() => {
//     const q = searchQuery.trim().toLowerCase();
//     if (!q) return cameras;

//     return cameras.filter((c) => {
//       const id = (c.camera_id || "").toLowerCase();
//       const name = (c.name || "").toLowerCase();
//       return id.includes(q) || name.includes(q);
//     });
//   }, [cameras, searchQuery]);

//   const handleAddCamera = () => {
//     setSelectedCamera(null);
//     setFormMode("create");
//     setShowForm(true);
//   };

//   const handleEditCamera = (camera) => {
//     setSelectedCamera(camera);
//     setFormMode("edit");
//     setShowForm(true);
//   };

//   // ✅ no browser confirm — open custom modal
//   const handleDeleteCamera = (camera) => {
//     setDeleteCamera(camera);
//   };

//   const confirmDelete = async () => {
//     if (!deleteCamera) return;

//     try {
//       setDeleteLoading(true);
//       const response = await fetch(
//         `${API_BASE_URL}/cameras/${deleteCamera.camera_id}`,
//         {
//           method: "DELETE",
//         }
//       );

//       if (!response.ok) {
//         const errText = await response.text();
//         throw new Error(errText || "Failed to delete camera");
//       }

//       setCameras((prev) =>
//         prev.filter((c) => c.camera_id !== deleteCamera.camera_id)
//       );
//       setDeleteCamera(null);
//     } catch (err) {
//       alert(`Error deleting camera: ${err.message}`);
//     } finally {
//       setDeleteLoading(false);
//     }
//   };

//   const handleSaveCamera = async (cameraData) => {
//     const url = `${API_BASE_URL}/cameras${
//       formMode === "edit" ? `/${cameraData.camera_id}` : ""
//     }`;
//     const method = formMode === "create" ? "POST" : "PUT";

//     const response = await fetch(url, {
//       method,
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify(cameraData),
//     });

//     if (!response.ok) {
//       const errorData = await response.json().catch(() => ({}));
//       throw new Error(errorData.detail || "Failed to save camera");
//     }

//     const savedCamera = await response.json();

//     setCameras((prev) => {
//       if (formMode === "create") return [savedCamera, ...prev];
//       return prev.map((c) =>
//         c.camera_id === savedCamera.camera_id ? savedCamera : c
//       );
//     });

//     setShowForm(false);
//   };

//   return (
//     <div className="space-y-4">
//       {/* Search + actions */}
//       <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
//         <div className="flex-1 relative">
//           <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
//           <input
//             type="text"
//             value={searchQuery}
//             onChange={(e) => setSearchQuery(e.target.value)}
//             placeholder="Search by Camera ID or Name..."
//             className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500"
//           />
//         </div>

//         <div className="flex gap-2">
//           <button
//             onClick={fetchCameras}
//             className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg transition-colors"
//           >
//             <RefreshCw className="w-4 h-4" />
//             Refresh
//           </button>

//           <button
//             onClick={handleAddCamera}
//             className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
//           >
//             <Plus className="w-4 h-4" />
//             Add Camera
//           </button>
//         </div>
//       </div>

//       {/* Grid */}
//       <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
//         <div className="flex items-center justify-between mb-6">
//           <h2 className="text-xl font-bold text-gray-800">Cameras</h2>
//           <span className="text-gray-600 text-sm">
//             {loading ? "Loading..." : `${filteredCameras.length} cameras found`}
//           </span>
//         </div>

//         {loading ? (
//           <div className="text-center py-12">
//             <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto" />
//             <p className="text-gray-600 mt-2">Loading cameras...</p>
//           </div>
//         ) : error ? (
//           <div className="text-center py-12">
//             <AlertCircle className="w-8 h-8 text-red-600 mx-auto" />
//             <p className="text-gray-800 font-medium mt-2">
//               Error loading cameras
//             </p>
//             <p className="text-gray-600 text-sm mt-1">{error}</p>
//             <button
//               onClick={fetchCameras}
//               className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
//             >
//               Retry
//             </button>
//           </div>
//         ) : filteredCameras.length === 0 ? (
//           <div className="text-center py-12">
//             <Camera className="w-12 h-12 text-gray-400 mx-auto mb-3" />
//             <p className="text-gray-800 font-medium">No cameras found</p>
//             <p className="text-gray-600 text-sm mt-1">
//               {searchQuery
//                 ? "Try a different search term"
//                 : "Add your first camera to get started"}
//             </p>
//             <button
//               onClick={handleAddCamera}
//               className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
//             >
//               Add Camera
//             </button>
//           </div>
//         ) : (
//           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
//             {filteredCameras.map((camera) => (
//               <CameraCard
//                 key={camera.id}
//                 camera={camera}
//                 onEdit={handleEditCamera}
//                 onDelete={handleDeleteCamera}
//                 onView={(cam) => setViewCamera(cam)} // ✅ custom view modal
//               />
//             ))}
//           </div>
//         )}
//       </div>

//       {/* Modals */}
//       {showForm && (
//         <CameraFormModal
//           camera={selectedCamera}
//           onClose={() => setShowForm(false)}
//           onSave={handleSaveCamera}
//           mode={formMode}
//         />
//       )}

//       {viewCamera && (
//         <ViewCameraModal
//           camera={viewCamera}
//           onClose={() => setViewCamera(null)}
//         />
//       )}

//       {deleteCamera && (
//         <ConfirmDeleteModal
//           camera={deleteCamera}
//           onClose={() => setDeleteCamera(null)}
//           onConfirm={confirmDelete}
//           loading={deleteLoading}
//         />
//       )}
//     </div>
//   );
// };

// export default CamerasPage;
