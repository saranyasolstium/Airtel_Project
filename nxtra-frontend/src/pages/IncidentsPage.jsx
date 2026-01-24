import React, { useEffect, useMemo, useState } from "react";
import "../styles/incidents.css";
import { listIncidentAlerts } from "../api/incidents";

// UI filter -> API incident_type mapping (match your DB enum: crowd, unauthorized)
const FILTER_TO_API = {
  all: "all",
  crowd: "crowd",
  unauthorized: "unauthorized",
};

function formatTime(ts) {
  if (!ts) return "";
  // if backend already sends ISO, this works. If "YYYY-MM-DD HH:mm:ss", still fine in most browsers.
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString();
}

export default function IncidentsPage() {
  const [filter, setFilter] = useState("all");
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    const ac = new AbortController();

    async function load() {
      setLoading(true);
      setErr("");
      try {
        const incident_type = FILTER_TO_API[filter] ?? "all";
        const data = await listIncidentAlerts(
          { incident_type },
          { signal: ac.signal },
        );
        setAlerts(Array.isArray(data) ? data : []);
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
  }, [filter]);

  const countText = useMemo(() => {
    if (loading) return "Loading…";
    if (err) return "Error";
    return `Showing ${alerts.length}`;
  }, [loading, err, alerts.length]);

  return (
    <div className="iPage">
      {/* Top header */}
      <div className="iTop">
        <div>
          <div className="iHeading">Incident Alerts</div>
          <div className="iSubheading">
            Live alerts from cameras (crowd / unauthorized)
          </div>
        </div>

        {/* Filter dropdown */}
        <div className="iFilter">
          <label className="iLabel">Filter</label>
          <select
            className="iSelect"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All</option>
            <option value="crowd">Crowd</option>
            <option value="unauthorized">Unauthorized Entry</option>
          </select>
        </div>
      </div>

      {/* Panel */}
      <div className="iPanel">
        <div className="iPanelHeader">
          <div>
            <div className="iTitle">Alerts</div>
            <div className="iSub">
              {err ? (
                <span className="iErr">{err}</span>
              ) : (
                "Each alert includes snapshot + message"
              )}
            </div>
          </div>

          <div className="iCount">{countText}</div>
        </div>

        {/* Body */}
        {loading ? (
          <div className="iEmpty">Loading alerts…</div>
        ) : alerts.length === 0 ? (
          <div className="iEmpty">No alerts found for this filter.</div>
        ) : (
          <div className="iGrid iGrid3">
            {alerts.map((a) => {
              const type = a.incident_type || "unknown";
              const badgeClass =
                type === "crowd" ? "iBadgeCrowd" : "iBadgeUnauth";
              const badgeText =
                type === "crowd" ? "Crowd" : "Unauthorized Entry";

              // Your DB stores image_base64 as "data:image/...."
              const imgSrc = a.image_base64 || "";

              return (
                <div
                  key={a.alert_id ?? `${a.timestamp}-${a.camera_name}`}
                  className="iCard"
                >
                  <div className="iCardTop">
                    <div className="iCardTitle">
                      {a.camera_name || "Camera"}{" "}
                      <span className="iCardMeta">
                        {a.zone_name ? `• ${a.zone_name}` : ""}
                      </span>
                    </div>

                    <span className={`iBadge ${badgeClass}`}>{badgeText}</span>
                  </div>

                  {/* Image */}
                  <div className="iImgWrap">
                    {imgSrc ? (
                      <img className="iImg" src={imgSrc} alt="incident" />
                    ) : (
                      <div className="iImgEmpty">No image</div>
                    )}
                  </div>

                  {/* Message */}
                  <div className="iCardDesc">{a.message || "—"}</div>

                  {/* Stats row */}
                  <div className="iRow">
                    <div className="iPill">
                      People: <b>{a.person_count ?? "-"}</b>
                    </div>
                    <div className="iPill">
                      Limit: <b>{a.max_count ?? "-"}</b>
                    </div>
                    <div className="iPill">
                      Time: <b>{formatTime(a.timestamp)}</b>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
