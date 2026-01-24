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
  Video,
} from "lucide-react";

import { CamerasAPI } from "../api/cameras";
import "../styles/cameras.css";

/* ------------------------- Helpers ------------------------- */
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

/* ------------------------- HLS Preview ------------------------- */
const HlsPreview = ({ hlsUrl, isLive, onLiveChange }) => {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // cleanup old instance
    if (hlsRef.current) {
      try {
        hlsRef.current.destroy();
      } catch (e) {
        console.warn("HLS destroy failed:", e);
      }
      hlsRef.current = null;
    }

    if (!hlsUrl) {
      video.removeAttribute("src");
      video.load();
      onLiveChange?.(false);
      return;
    }

    // Native HLS
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

      hls.on(Hls.Events.FRAG_LOADED, () => onLiveChange?.(true));

      hls.on(Hls.Events.ERROR, (_, data) => {
        if (!data?.fatal) return;
        onLiveChange?.(false);

        try {
          if (data.type === Hls.ErrorTypes.NETWORK_ERROR) hls.startLoad();
          else if (data.type === Hls.ErrorTypes.MEDIA_ERROR)
            hls.recoverMediaError();
          else hls.destroy();
        } catch (e) {
          console.warn("HLS fatal recovery failed:", e);
        }
      });

      return () => {
        try {
          hls.destroy();
        } catch (e) {
          console.warn("HLS destroy failed:", e);
        }
      };
    }
  }, [hlsUrl, onLiveChange]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

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
    <div className="camPreview">
      {hlsUrl ? (
        <video ref={videoRef} muted playsInline autoPlay className="camVideo" />
      ) : (
        <div className="camEmpty">
          <Video size={44} className="camEmptyIcon" />
          <div className="camEmptyText">No Stream</div>
          <div className="camEmptySub">Not Generated</div>
        </div>
      )}

      <div className="camBadge">
        {hlsUrl ? (
          <span className={`badge ${isLive ? "badgeLive" : "badgeLoading"}`}>
            {isLive ? "Live" : "Loading..."}
          </span>
        ) : (
          <span className="badge badgeOff">Not Generated</span>
        )}
      </div>
    </div>
  );
};

/* ------------------------- Fullscreen Modal ------------------------- */
const FullViewModal = ({ camera, onClose }) => {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);

  useEffect(() => {
    const onEsc = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    window.addEventListener("keydown", onEsc);
    return () => window.removeEventListener("keydown", onEsc);
  }, [onClose]);

  useEffect(() => {
    if (hlsRef.current) {
      try {
        hlsRef.current.destroy();
      } catch (e) {
        console.warn("HLS destroy failed:", e);
      }
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
        } catch (e) {
          console.warn("HLS destroy failed:", e);
        }
      };
    }
  }, [camera]);

  if (!camera) return null;

  return (
    <div
      className="modalOverlay"
      onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}
    >
      <div className="modalTopBar">
        <div>
          <div className="modalTitle">{camera.name}</div>
          <div className="modalSub">ID: {camera.camera_id}</div>
        </div>
        <button className="iconBtn" onClick={onClose} title="Close">
          <X size={18} />
        </button>
      </div>

      <div className="modalBody">
        <div className="modalPlayer">
          {camera.hls_url ? (
            <video
              ref={videoRef}
              controls
              autoPlay
              muted
              playsInline
              className="modalVideo"
            />
          ) : (
            <div className="modalEmpty">
              HLS URL not available for this camera.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/* ------------------------- Details Modal ------------------------- */
const ViewCameraModal = ({ camera, onClose }) => {
  if (!camera) return null;

  return (
    <div className="popupOverlay">
      <div className="popup">
        <div className="popupHeader">
          <div className="popupHeaderTitle">Camera Details</div>
          <button className="iconBtn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="popupBody">
          <div className="kv">
            <div className="k">Camera ID</div>
            <div className="v">{camera.camera_id}</div>

            <div className="k">Name</div>
            <div className="v">{camera.name}</div>

            <div className="k">RTSP</div>
            <div className="v">
              {camera.rtsp_url ? (
                <pre className="monoBox">{camera.rtsp_url}</pre>
              ) : (
                <span className="muted">Not configured</span>
              )}
            </div>

            <div className="k">HLS</div>
            <div className="v">
              {camera.hls_url ? (
                <pre className="monoBox">{camera.hls_url}</pre>
              ) : (
                <span className="muted">Not generated</span>
              )}
            </div>

            <div className="k">Created</div>
            <div className="v">
              {camera.created_at
                ? new Date(camera.created_at).toLocaleString()
                : "-"}
            </div>

            <div className="k">Updated</div>
            <div className="v">
              {camera.updated_at
                ? new Date(camera.updated_at).toLocaleString()
                : camera.created_at
                  ? new Date(camera.created_at).toLocaleString()
                  : "-"}
            </div>
          </div>
        </div>

        <div className="popupFooter">
          <button className="btn btnGhost" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

/* ------------------------- Delete Modal ------------------------- */
const ConfirmDeleteModal = ({ camera, onClose, onConfirm, loading }) => {
  if (!camera) return null;

  return (
    <div className="popupOverlay">
      <div className="popup popupSmall">
        <div className="popupHeader">
          <div className="popupHeaderTitle">Delete Camera</div>
          <button className="iconBtn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="popupBody">
          <div className="warnRow">
            <Trash2 size={18} />
            <div>
              Are you sure you want to delete <b>{camera.name}</b>?
              <div className="muted" style={{ marginTop: 6 }}>
                ID: <span className="mono">{camera.camera_id}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="popupFooter">
          <button className="btn btnGhost" disabled={loading} onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btnDanger"
            disabled={loading}
            onClick={onConfirm}
          >
            {loading ? "Deleting..." : "Delete"}
          </button>
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

    // ✅ RTSP mandatory
    if (!formData.rtsp_url.trim()) {
      newErrors.rtsp_url = "RTSP URL is required";
    } else if (!formData.rtsp_url.startsWith("rtsp://")) {
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
      setErrors({ submit: error?.message || "Failed to save camera" });
    }
  };

  return (
    <div className="popupOverlay">
      <div className="popup popupSmall">
        <div className="popupHeader">
          <div className="popupHeaderTitle">
            {mode === "create" ? "Add New Camera" : "Edit Camera"}
          </div>
          <button className="iconBtn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="popupBody">
          <div className="formRow">
            <label>Camera ID *</label>
            <input
              value={formData.camera_id}
              onChange={(e) =>
                setFormData({ ...formData, camera_id: e.target.value })
              }
              disabled={mode === "edit"}
              placeholder="e.g., CAM-001"
              className={errors.camera_id ? "input error" : "input"}
            />
            {errors.camera_id && (
              <div className="fieldError">{errors.camera_id}</div>
            )}
          </div>

          <div className="formRow">
            <label>Camera Name *</label>
            <input
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              placeholder="e.g., Main Entrance"
              className={errors.name ? "input error" : "input"}
            />
            {errors.name && <div className="fieldError">{errors.name}</div>}
          </div>

          <div className="formRow">
            <label>RTSP URL *</label>
            <input
              value={formData.rtsp_url}
              onChange={(e) =>
                setFormData({ ...formData, rtsp_url: e.target.value })
              }
              placeholder="rtsp://username:password@ip:port/path"
              className={errors.rtsp_url ? "input error" : "input"}
            />
            {errors.rtsp_url && (
              <div className="fieldError">{errors.rtsp_url}</div>
            )}
            <div className="muted" style={{ marginTop: 6 }}>
              Optional: Provide RTSP to auto-generate HLS preview
            </div>
          </div>

          {errors.submit && <div className="inlineError">{errors.submit}</div>}

          <div className="popupFooter">
            <button type="button" className="btn btnGhost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btnPrimary">
              {mode === "create" ? "Add Camera" : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

/* ------------------------- Card ------------------------- */
const CameraCard = ({ camera, onEdit, onDelete, onView, onFullView }) => {
  const [isLive, setIsLive] = useState(false);

  return (
    <div className="camCard">
      <div className="camCardTop">
        <HlsPreview
          hlsUrl={camera.hls_url}
          isLive={isLive}
          onLiveChange={setIsLive}
        />

        <div className="camCardId">ID: {camera.camera_id}</div>

        <div className="camCardActions">
          <button
            className="iconBtnSmall"
            title="Full View"
            onClick={() => onFullView(camera)}
          >
            <Maximize2 size={16} />
          </button>
          <button
            className="iconBtnSmall"
            title="View"
            onClick={() => onView(camera)}
          >
            <Eye size={16} />
          </button>
          <button
            className="iconBtnSmall"
            title="Edit"
            onClick={() => onEdit(camera)}
          >
            <Edit2 size={16} />
          </button>
          <button
            className="iconBtnSmall danger"
            title="Delete"
            onClick={() => onDelete(camera)}
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <div className="camCardBody">
        <div className="camName">{camera.name}</div>
        <div className="camMetaRow">
          <div className="muted">
            Created:{" "}
            {camera.created_at
              ? new Date(camera.created_at).toLocaleDateString()
              : "-"}
          </div>
          <div className="muted">
            Updated:{" "}
            {camera.updated_at || camera.created_at
              ? new Date(
                  camera.updated_at || camera.created_at,
                ).toLocaleDateString()
              : "-"}
          </div>
        </div>
      </div>
    </div>
  );
};

/* ------------------------- Page ------------------------- */
export default function CamerasPage() {
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

  // auto bulk only once after load
  const bulkRanRef = useRef(false);

  useEffect(() => {
    fetchCameras();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!loading && cameras.length > 0 && !bulkRanRef.current) {
      bulkRanRef.current = true;
      generateAllHlsForCameras(cameras).catch((e) =>
        console.warn("auto bulk gen error:", e),
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, cameras]);

  const fetchCameras = async () => {
    try {
      setLoading(true);
      const data = await CamerasAPI.list();
      const items = data?.items || data || [];
      setCameras(Array.isArray(items) ? items : []);
      setError(null);
      bulkRanRef.current = false;
    } catch (e) {
      setError(`Failed to fetch cameras: ${e?.message || e}`);
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
      const payload = await CamerasAPI.generateHlsBulk(rtspUrls);
      const map = extractBulkMap(payload);

      setCameras((prev) =>
        prev.map((c) => {
          const hls = c.rtsp_url ? map[c.rtsp_url] : null;
          return hls ? { ...c, hls_url: hls } : c;
        }),
      );
    } catch (e) {
      console.warn("Bulk HLS error:", e);
    } finally {
      setGenerating(false);
    }
  };

  const generateOne = async (camera) => {
    if (!camera?.rtsp_url) return;
    setGenerating(true);
    try {
      const data = await CamerasAPI.generateHls(camera.rtsp_url);
      const hls = data?.hls_url;
      if (!hls) throw new Error("HLS URL not returned by API.");

      setCameras((prev) =>
        prev.map((c) =>
          c.camera_id === camera.camera_id ? { ...c, hls_url: hls } : c,
        ),
      );
    } catch (e) {
      alert(e?.message || "Failed to generate HLS");
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

  const handleDeleteCamera = (camera) => setDeleteCamera(camera);

  const confirmDelete = async () => {
    if (!deleteCamera) return;
    try {
      setDeleteLoading(true);
      await CamerasAPI.remove(deleteCamera.camera_id);
      setCameras((prev) =>
        prev.filter((c) => c.camera_id !== deleteCamera.camera_id),
      );
      setDeleteCamera(null);
    } catch (e) {
      alert(`Error deleting camera: ${e?.message || e}`);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleSaveCamera = async (cameraData) => {
    let savedCamera;

    if (formMode === "create") {
      savedCamera = await CamerasAPI.create(cameraData);
      setCameras((prev) => [savedCamera, ...prev]);
    } else {
      savedCamera = await CamerasAPI.update(cameraData.camera_id, cameraData);
      setCameras((prev) =>
        prev.map((c) =>
          c.camera_id === savedCamera.camera_id ? savedCamera : c,
        ),
      );
    }

    setShowForm(false);

    if (savedCamera?.rtsp_url?.startsWith("rtsp://")) {
      generateOne(savedCamera).catch(() => {});
    }
  };

  return (
    <div className="pageShell">
      <div className="pageHeader">
        <div>
          <div className="pageTitle">Cameras Management</div>
          <div className="pageSub">
            Add / Edit / Delete cameras and preview live streams
          </div>
        </div>

        <div className="rightPills">{generating}</div>
      </div>

      <div className="glassPanel">
        <div className="toolbar">
          <div className="searchBox">
            <Search size={16} />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by Camera ID or Name"
            />
          </div>

          <div className="btnRow">
            <button
              className="btn btnGhost"
              onClick={fetchCameras}
              disabled={loading}
            >
              <RefreshCw size={16} className={loading ? "spin" : ""} />
              Refresh
            </button>

            <button className="btn btnPrimary" onClick={handleAddCamera}>
              <Plus size={16} />
              Add Camera
            </button>
          </div>
        </div>

        <div className="sectionTop">
          <div className="sectionTitle">Cameras</div>
          <div className="muted">
            {loading ? "Loading…" : `${filteredCameras.length} cameras found`}
          </div>
        </div>

        {loading ? (
          <div className="centerBox">
            <RefreshCw size={26} className="spin" />
            <div className="muted" style={{ marginTop: 10 }}>
              Loading cameras…
            </div>
          </div>
        ) : error ? (
          <div className="centerBox">
            <AlertCircle size={30} />
            <div style={{ fontWeight: 700, marginTop: 10 }}>
              Error loading cameras
            </div>
            <div className="muted" style={{ marginTop: 8 }}>
              {error}
            </div>
            <button
              className="btn btnPrimary"
              style={{ marginTop: 16 }}
              onClick={fetchCameras}
            >
              Retry
            </button>
          </div>
        ) : filteredCameras.length === 0 ? (
          <div className="centerBox">
            <Camera size={36} />
            <div style={{ fontWeight: 700, marginTop: 10 }}>
              No cameras found
            </div>
            <div className="muted" style={{ marginTop: 8 }}>
              {searchQuery
                ? "Try a different search term"
                : "Add your first camera to get started"}
            </div>
            <button
              className="btn btnPrimary"
              style={{ marginTop: 16 }}
              onClick={handleAddCamera}
            >
              Add Camera
            </button>
          </div>
        ) : (
          <div className="grid3">
            {filteredCameras.map((camera) => (
              <CameraCard
                key={camera.id || camera.camera_id}
                camera={camera}
                onEdit={handleEditCamera}
                onDelete={handleDeleteCamera}
                onView={(cam) => setViewCamera(cam)}
                onFullView={(cam) => setFullViewCamera(cam)}
                onGenerate={generateOne}
              />
            ))}
          </div>
        )}
      </div>

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
}
