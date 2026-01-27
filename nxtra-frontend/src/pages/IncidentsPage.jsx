// src/pages/IncidentsPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import "../styles/incidents.css";
import {
  listIncidentAlerts,
  resolveIncidentAlert,
  getIncidentFilters,
} from "../api/incidents";

/* ------------------------- Helpers ------------------------- */
const pad2 = (n) => String(n).padStart(2, "0");
const toInputDate = (d) =>
  `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;

function formatTime(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return String(ts);
  return d.toLocaleString();
}

function dateKey(ts) {
  const d = new Date(ts || 0);
  if (Number.isNaN(d.getTime())) return "";
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function toImgSrc(v) {
  if (!v) return "";
  const s = String(v);
  if (s.startsWith("data:image")) return s;
  if (/^[A-Za-z0-9+/=]+$/.test(s) && s.length > 200) {
    return `data:image/jpeg;base64,${s}`;
  }
  return s;
}

function buildIncidentMessage(a) {
  const it = (a?.incident_type || "").toLowerCase();
  const ot = (a?.object_type || "").toLowerCase();

  if (it === "crowd") {
    const pc = a?.person_count ?? "-";
    const mc = a?.max_count ?? "-";
    return `Crowd detected. People ${pc} exceeded limit ${mc}.`;
  }

  if (ot.includes("vehicle"))
    return "Unauthorized vehicle detected in restricted zone.";
  if (ot.includes("hand")) return "Hand intrusion detected in restricted zone.";
  if (ot.includes("door")) return "Door event detected in restricted zone.";
  if (ot.includes("person") || ot.includes("people"))
    return "Person detected in restricted zone.";

  return a?.message || "Unauthorized activity detected.";
}

export default function IncidentsPage() {
  // Filters
  const [incidentType, setIncidentType] = useState("all");
  const [camera, setCamera] = useState("all");
  const [objectType, setObjectType] = useState("all");

  // Date filter (default today)
  const [selectedDate, setSelectedDate] = useState(() =>
    toInputDate(new Date()),
  );

  const [filterOptions, setFilterOptions] = useState({
    cameras: [],
    incident_types: [],
    object_types: [],
  });

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(12);

  // Data
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  // Modal
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(null);

  // Load dropdown filters
  useEffect(() => {
    const ac = new AbortController();
    (async () => {
      try {
        const f = await getIncidentFilters({ signal: ac.signal });
        setFilterOptions({
          cameras: Array.isArray(f?.cameras) ? f.cameras : [],
          incident_types: Array.isArray(f?.incident_types)
            ? f.incident_types
            : [],
          object_types: Array.isArray(f?.object_types) ? f.object_types : [],
        });
      } catch {
        // ignore
      }
    })();
    return () => ac.abort();
  }, []);

  // Reset page on filters change
  useEffect(() => {
    setPage(1);
  }, [incidentType, camera, objectType, pageSize, selectedDate]);

  // Load alerts
  useEffect(() => {
    const ac = new AbortController();

    async function load() {
      setLoading(true);
      setErr("");
      try {
        const data = await listIncidentAlerts(
          {
            status: "active",
            incident_type: incidentType,
            camera_name: camera !== "all" ? camera : undefined,
            object_type: objectType !== "all" ? objectType : undefined,
            limit: 500,
          },
          { signal: ac.signal },
        );

        const arr = Array.isArray(data) ? data : [];

        // latest first
        arr.sort((a, b) => {
          const ta = new Date(a?.timestamp || 0).getTime() || 0;
          const tb = new Date(b?.timestamp || 0).getTime() || 0;
          return tb - ta;
        });

        // filter by selected date
        const filtered = arr.filter((x) => {
          const dk = dateKey(x?.timestamp);
          if (!dk) return true;
          return dk === selectedDate;
        });

        setAlerts(filtered);
      } catch (e) {
        if (e?.name === "AbortError") return;
        setErr(e?.message || "Failed to load incident alerts");
        setAlerts([]);
      } finally {
        setLoading(false);
      }
    }

    load();
    return () => ac.abort();
  }, [incidentType, camera, objectType, selectedDate]);

  // Pagination logic
  const total = alerts.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(page, totalPages);

  const pageItems = useMemo(() => {
    const start = (safePage - 1) * pageSize;
    const end = start + pageSize;
    return alerts.slice(start, end);
  }, [alerts, safePage, pageSize]);

  const countText = useMemo(() => {
    if (loading) return "Loading…";
    if (err) return "Error";
    return `Showing ${pageItems.length} / ${total}`;
  }, [loading, err, pageItems.length, total]);

  // Actions
  async function onResolve(a) {
    try {
      await resolveIncidentAlert(a.alert_id);
      setAlerts((prev) => prev.filter((x) => x.alert_id !== a.alert_id));
      setTimeout(() => {
        setPage((p) => Math.max(1, Math.min(p, totalPages)));
      }, 0);
    } catch (e) {
      alert(e?.message || "Failed to resolve alert");
    }
  }

  function openModal(a) {
    setSelected(a);
    setOpen(true);
  }

  function closeModal() {
    setOpen(false);
    setSelected(null);
  }

  // Options
  const incidentOptions = useMemo(() => {
    const base = [
      "crowd",
      "unauthorized",
      "door_open",
      "door_close",
      "vehicle_unauthorized",
    ];
    const extra = (filterOptions.incident_types || []).filter(
      (t) => t && !base.includes(t),
    );
    return ["all", ...base, ...extra];
  }, [filterOptions.incident_types]);

  const objectOptions = useMemo(() => {
    const base = ["people", "person", "vehicle", "door", "hand"];
    const extra = (filterOptions.object_types || []).filter(
      (o) => o && !base.includes(o),
    );
    return ["all", ...base, ...extra];
  }, [filterOptions.object_types]);

  return (
    <div className="iPage">
      {/* TOP HEADER + FILTERS */}
      <div className="iTop">
        <div>
          <div className="iHeading">Incident Alerts</div>
          <div className="iSubheading">
            Live active alerts (crowd / unauthorized / door / vehicle etc)
          </div>
        </div>

        <div className="iFiltersRow">
          {/* Incident Type */}
          <div className="iFilter">
            <label className="iLabel">Incident Type</label>
            <select
              className="iSelect"
              value={incidentType}
              onChange={(e) => setIncidentType(e.target.value)}
            >
              {incidentOptions.map((t) => (
                <option key={t} value={t}>
                  {t === "all" ? "All" : t}
                </option>
              ))}
            </select>
          </div>

          {/* Camera */}
          <div className="iFilter">
            <label className="iLabel">Camera</label>
            <select
              className="iSelect"
              value={camera}
              onChange={(e) => setCamera(e.target.value)}
            >
              <option value="all">All</option>
              {(filterOptions.cameras || []).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Object Type */}
          <div className="iFilter">
            <label className="iLabel">Object Type</label>
            <select
              className="iSelect"
              value={objectType}
              onChange={(e) => setObjectType(e.target.value)}
            >
              {objectOptions.map((o) => (
                <option key={o} value={o}>
                  {o === "all" ? "All" : o}
                </option>
              ))}
            </select>
          </div>

          {/* Date */}
          <div className="iFilter">
            <label className="iLabel">Date</label>
            <input
              className="iDate"
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            />
          </div>

          {/* Rows */}
          <div className="iFilter">
            <label className="iLabel">Rows</label>
            <select
              className="iSelect"
              value={pageSize}
              onChange={(e) => setPageSize(parseInt(e.target.value, 10))}
            >
              <option value={6}>6</option>
              <option value={9}>9</option>
              <option value={12}>12</option>
              <option value={15}>15</option>
              <option value={18}>18</option>
            </select>
          </div>
        </div>
      </div>

      {/* PANEL */}
      <div className="iPanel">
        <div className="iPanelHeader">
          <div>
            <div className="iTitle">Alerts</div>
            <div className="iSub">
              {err ? (
                <span className="iErr">{err}</span>
              ) : (
                `Active alerts only • ${selectedDate}`
              )}
            </div>
          </div>
          <div className="iCount">{countText}</div>
        </div>

        {/* ✅ Scrollable grid area (ONLY HERE) */}
        <div className="iGridScroll">
          {loading ? (
            <div className="iEmpty">Loading alerts…</div>
          ) : pageItems.length === 0 ? (
            <div className="iEmpty">
              No active alerts found for selected date.
            </div>
          ) : (
            <div className="iGrid iGrid3">
              {pageItems.map((a) => {
                const type = a.incident_type || "unknown";
                const isCrowd = String(type).toLowerCase() === "crowd";
                const badgeClass = isCrowd ? "iBadgeCrowd" : "iBadgeUnauth";
                const badgeText = isCrowd
                  ? "Crowd"
                  : String(type).replaceAll("_", " ");

                const imgSrc = toImgSrc(a.image_base64 || "");
                const showCounts = isCrowd;
                const showResolveBtn = !isCrowd;

                return (
                  <div key={a.alert_id} className="iCard">
                    <div className="iCardTop">
                      <div className="iCardTitle">
                        {a.camera_name || "Camera"}
                        <div className="iCardMeta">
                          {a.zone_name ? `• ${a.zone_name}` : ""}
                          {a.object_type ? ` • ${a.object_type}` : ""}
                        </div>
                      </div>
                      <span className={`iBadge ${badgeClass}`}>
                        {badgeText}
                      </span>
                    </div>

                    <div
                      className="iImgWrap"
                      onClick={() => openModal(a)}
                      title="Click to view full"
                      role="button"
                    >
                      {imgSrc ? (
                        <img className="iImg" src={imgSrc} alt="incident" />
                      ) : (
                        <div className="iImgEmpty">No image</div>
                      )}
                    </div>

                    <div className="iCardDesc">{buildIncidentMessage(a)}</div>

                    <div className="iRow">
                      {showCounts ? (
                        <>
                          <div className="iPill">
                            People: <b>{a.person_count ?? "-"}</b>
                          </div>
                          <div className="iPill">
                            Limit: <b>{a.max_count ?? "-"}</b>
                          </div>
                        </>
                      ) : (
                        <div className="iPill">
                          Object: <b>{a.object_type ?? "-"}</b>
                        </div>
                      )}

                      <div className="iPill">
                        Time: <b>{formatTime(a.timestamp)}</b>
                      </div>

                      {showResolveBtn && (
                        <button
                          className="iResolveBtn"
                          onClick={() => onResolve(a)}
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ✅ Pagination INSIDE panel (fixed) */}
        <div className="iPager">
          <div className="iPagerLeft">
            Total: {total} • Page {safePage} / {totalPages}
          </div>

          <div className="iPagerRight">
            <button
              className="iPageBtn"
              disabled={safePage <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Prev
            </button>

            <div className="iPageInfo">
              {safePage} / {totalPages}
            </div>

            <button
              className="iPageBtn"
              disabled={safePage >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* MODAL */}
      {open && selected && (
        <div className="iModalOverlay" onClick={closeModal}>
          <div className="iModal" onClick={(e) => e.stopPropagation()}>
            <div className="iModalHeader">
              <div className="iModalTitle">
                {selected.camera_name} • {selected.zone_name} •{" "}
                {selected.incident_type}
              </div>
              <button className="iModalClose" onClick={closeModal}>
                ✕
              </button>
            </div>

            <div className="iModalBody">
              <div className="iModalImgFrame">
                {toImgSrc(selected.image_base64) ? (
                  <img
                    className="iModalImg"
                    src={toImgSrc(selected.image_base64)}
                    alt="full"
                  />
                ) : (
                  <div className="iImgEmpty">No image</div>
                )}
              </div>

              <div className="iModalDetails">
                <div className="iModalLine">
                  <b>Camera:</b> {selected.camera_name}
                </div>
                <div className="iModalLine">
                  <b>Zone:</b> {selected.zone_name}
                </div>
                <div className="iModalLine">
                  <b>Type:</b> {selected.incident_type}
                </div>
                <div className="iModalLine">
                  <b>Object:</b> {selected.object_type ?? "-"}
                </div>
                <div className="iModalLine">
                  <b>Time:</b> {formatTime(selected.timestamp)}
                </div>

                {String(selected.incident_type || "").toLowerCase() ===
                "crowd" ? (
                  <div className="iModalLine">
                    <b>People / Limit:</b> {selected.person_count ?? "-"} /{" "}
                    {selected.max_count ?? "-"}
                  </div>
                ) : null}

                <div className="iModalMsg">
                  {buildIncidentMessage(selected)}
                </div>
              </div>
            </div>

            <div className="iModalFooter">
              {String(selected.incident_type || "").toLowerCase() !==
                "crowd" && (
                <button
                  className="iResolveBtn"
                  onClick={async () => {
                    await onResolve(selected);
                    closeModal();
                  }}
                >
                  Resolve
                </button>
              )}
              <button className="iBtn iBtnGhost" onClick={closeModal}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
