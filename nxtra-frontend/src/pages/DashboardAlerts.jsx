// src/pages/DashboardAlerts.jsx
import React, { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Users,
  ShieldAlert,
  Clock,
  MapPin,
  Camera,
  RefreshCw,
} from "lucide-react";

import {
  listIncidentAlerts,
  getIncidentAlertStats, // ✅ ADD THIS
} from "../api/incidents";
import { listTrafficFlowVehicles } from "../api/trafficFlow";

import "../styles/dashboardAlerts.css";

// ✅ reuse same card UI styles from TrafficFlowPage
import "../styles/traffic.css";

/* ================= helpers ================= */
const pad2 = (n) => String(n).padStart(2, "0");
const toInputDate = (d) =>
  `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;

function formatTime(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return String(ts);
  return d.toLocaleString();
}

function toImgSrc(v) {
  if (!v) return "";
  if (String(v).startsWith("data:image")) return v;
  if (/^[A-Za-z0-9+/=]+$/.test(v) && v.length > 200) {
    return `data:image/jpeg;base64,${v}`;
  }
  return v;
}

// Traffic severity rules
const computeSeverity = (dwellSeconds) => {
  const s = Number(dwellSeconds || 0);
  if (s >= 10 * 3600) return "CRITICAL";
  if (s >= 2 * 3600) return "WARNING";
  return "INFO";
};

/* ✅ message based on object_type + incident_type */
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

function incidentTag(type) {
  const t = (type || "").toLowerCase();
  if (t === "crowd") return { text: "Crowd", cls: "tagRed" };
  if (t === "unauthorized") return { text: "Unauthorized", cls: "tagYellow" };
  return { text: (type || "Alert").replaceAll("_", " "), cls: "tagBlue" };
}

/* ======= Severity mapping (same as TrafficFlowPage) ======= */
const severityClass = (severity) => {
  const s = (severity || "").toLowerCase();
  if (s === "critical") return "tCard tCritical";
  if (s === "warning") return "tCard tWarning";
  return "tCard tInfo";
};

/* ================= Card (exactly like TrafficFlowPage) ================= */
const DwellAlertCard = ({ alert }) => {
  const sev = alert.severity || "INFO";

  return (
    <div className={severityClass(sev)}>
      <div className="tCardRow">
        <div className="tIconWrap">
          <AlertTriangle size={18} />
        </div>

        <div className="tCardBody">
          <div className="tPills">
            <span className="tPill">{sev.toUpperCase()}</span>
          </div>

          <div className="tCardTitle">
            <b>{alert.plate_text || "-"}</b> exceeded dwell time limit
          </div>

          <div className="tMeta">
            <div className="tMetaItem">
              <MapPin size={14} />
              <span>{alert.location_text || "-"}</span>
            </div>

            <div className="tMetaItem">
              <Clock size={14} />
              <span>{alert.dwell_text || "-"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ================= Small KPI Circles ================= */
function MiniKpi({ value, label, active, color = "blue" }) {
  return (
    <div className={`daKpi ${color}`}>
      <div className="daKpiInner">
        <div className="daKpiVal">{value}</div>
        <div className="daKpiLabel">{label}</div>
        <div className="daKpiSub">{active} Active</div>
      </div>
    </div>
  );
}

/* ================= Page ================= */
export default function DashboardAlerts() {
  const POLL_MS = 10 * 60 * 1000;

  const [now, setNow] = useState(new Date());
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const [incidentList, setIncidentList] = useState([]);
  const [trafficList, setTrafficList] = useState([]);

  // ✅ NEW: stats state
  const [statsLoading, setStatsLoading] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    resolved: 0,
    by_type: {},
  });

  // ✅ always today for dashboard
  const today = useMemo(() => toInputDate(new Date()), []);

  // live clock
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const loadAll = async () => {
    setLoading(true);
    setErr("");

    try {
      // ✅ 1) STATS for today, incident_type = all
      setStatsLoading(true);
      try {
        const payload = await getIncidentAlertStats({
          incident_type: "all",
          date: today,
        });

        const summary = payload?.summary || {};
        const byType = payload?.by_type || {};
        setStats({
          total: Number(summary.total || 0),
          active: Number(summary.active || 0),
          resolved: Number(summary.resolved || 0),
          by_type: byType,
        });
      } catch {
        setStats({ total: 0, active: 0, resolved: 0, by_type: {} });
      } finally {
        setStatsLoading(false);
      }

      // ============ 2) INCIDENTS: last 10 (active) ============
      const inc = await listIncidentAlerts({
        status: "active",
        incident_type: "all",
        limit: 300,
      });

      const arr = Array.isArray(inc) ? inc : [];
      arr.sort((a, b) => {
        const ta = new Date(a?.timestamp || 0).getTime() || 0;
        const tb = new Date(b?.timestamp || 0).getTime() || 0;
        return tb - ta;
      });

      // ✅ keep only today’s alerts (dashboard)
      const filteredToday = arr.filter((x) => {
        const d = new Date(x?.timestamp || 0);
        if (Number.isNaN(d.getTime())) return true;
        return toInputDate(d) === today;
      });

      setIncidentList(filteredToday.slice(0, 10));

      // ============ 3) TRAFFIC: last 10 ============
      const tr = await listTrafficFlowVehicles({
        limit: 10,
        offset: 0,
        date: today,
        dwell_limit_seconds: 7200,
      });

      const rows = tr?.data || tr?.items || [];
      const fixed = (Array.isArray(rows) ? rows : []).map((r) => ({
        ...r,
        severity: computeSeverity(r?.dwell_seconds),
      }));

      fixed.sort(
        (a, b) => Number(b?.dwell_seconds || 0) - Number(a?.dwell_seconds || 0),
      );

      setTrafficList(fixed.slice(0, 10));
    } catch (e) {
      console.error(e);
      setErr(e?.message || "Failed to load alerts");
      setIncidentList([]);
      setTrafficList([]);
    } finally {
      setLoading(false);
    }
  };

  // polling
  useEffect(() => {
    loadAll();
    const t = setInterval(loadAll, POLL_MS);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ✅ ring counts from backend stats
  const crowd = stats?.by_type?.crowd || { total: 0, active: 0, resolved: 0 };
  const unauth = stats?.by_type?.unauthorized || {
    total: 0,
    active: 0,
    resolved: 0,
  };

  const otherTotal = Math.max(
    0,
    (stats.total || 0) - ((crowd.total || 0) + (unauth.total || 0)),
  );
  const otherActive = Math.max(
    0,
    (stats.active || 0) - ((crowd.active || 0) + (unauth.active || 0)),
  );

  return (
    <div className="alPage">
      {/* ======= Top header ======= */}
      <div className="alTop">
        <div>
          <div className="alHeading">Active Alerts</div>
          <div className="alSub">
            Today <b>{today}</b> • Last <b>10 Incident</b> + <b>10 Traffic</b>{" "}
            (auto refresh)
          </div>
        </div>

        <div className="alTopRight">
          {/* ✅ ADD COUNTS HERE */}
          <div className="daKpiRow">
            <MiniKpi
              color="blue"
              value={statsLoading ? "…" : stats.total}
              label="TOTAL"
              active={statsLoading ? "…" : stats.active}
            />
            <MiniKpi
              color="green"
              value={statsLoading ? "…" : crowd.total || 0}
              label="CROWD"
              active={statsLoading ? "…" : crowd.active || 0}
            />
            <MiniKpi
              color="red"
              value={statsLoading ? "…" : unauth.total || 0}
              label="UNAUTH"
              active={statsLoading ? "…" : unauth.active || 0}
            />
            <MiniKpi
              color="gray"
              value={statsLoading ? "…" : otherTotal}
              label="TAMPER"
              active={statsLoading ? "…" : otherActive}
            />
          </div>

          <div className="alClock">
            <Clock size={16} />
            <span>{now.toLocaleTimeString()}</span>
          </div>

          <button className="alBtn" onClick={loadAll} disabled={loading}>
            <RefreshCw size={16} className={loading ? "spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {err ? <div className="alErr">{err}</div> : null}

      {/* ======= INCIDENT LIST PANEL ======= */}
      <div className="alPanel">
        <div className="alPanelHead">
          <div className="alPanelTitle">
            <ShieldAlert size={18} />
            Incident Alerts
          </div>
          <div className="alPanelHint">Last 10 (today)</div>
        </div>

        {incidentList.length === 0 ? (
          <div className="alEmpty">No incident alerts today</div>
        ) : (
          <div className="alList">
            {incidentList.map((a) => {
              const tag = incidentTag(a?.incident_type);
              const isCrowd =
                String(a?.incident_type || "").toLowerCase() === "crowd";

              return (
                <div key={a?.alert_id} className="alRow">
                  <div
                    className={`alIcon ${isCrowd ? "alIconRed" : "alIconOrange"}`}
                  >
                    {isCrowd ? <Users size={18} /> : <ShieldAlert size={18} />}
                  </div>

                  <div className="alBody">
                    <div className="alTitleLine">
                      <div className="alTitle">
                        {isCrowd ? "Incident Alert" : "Unauthorized Alert"}
                      </div>
                      <span className={`alTag ${tag.cls}`}>{tag.text}</span>
                    </div>

                    <div className="alMsg">{buildIncidentMessage(a)}</div>

                    <div className="alMeta">
                      <span className="alMetaItem">
                        <Camera size={14} />
                        {a?.camera_name || "-"}
                      </span>
                      <span className="alMetaItem">
                        <MapPin size={14} />
                        {a?.zone_name || "-"}
                      </span>
                      <span className="alMetaItem">
                        <Clock size={14} />
                        {formatTime(a?.timestamp)}
                      </span>
                    </div>
                  </div>

                  <div className="alThumbBox">
                    {a?.image_base64 ? (
                      <img
                        className="alThumb"
                        src={toImgSrc(a.image_base64)}
                        alt="incident"
                      />
                    ) : (
                      <div className="alThumbEmpty">No image</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ======= TRAFFIC LIST PANEL ======= */}
      <div className="alPanel">
        <div className="alPanelHead">
          <div className="alPanelTitle">
            <AlertTriangle size={18} />
            Traffic Flow Alerts
          </div>
          <div className="alPanelHint">Last 10 (today)</div>
        </div>

        {trafficList.length === 0 ? (
          <div className="alEmpty">No traffic alerts today</div>
        ) : (
          <div className="tList" style={{ paddingTop: 0 }}>
            {trafficList.map((t, idx) => (
              <DwellAlertCard
                key={t?.id ?? `${t?.plate_text}-${idx}`}
                alert={{
                  ...t,
                  plate_text: t?.plate_text,
                  location_text: t?.location_text || t?.location || "-",
                  dwell_text:
                    t?.dwell_text ||
                    t?.dwell_time ||
                    `${Math.round(Number(t?.dwell_seconds || 0) / 60)} min`,
                }}
              />
            ))}
          </div>
        )}

        <div className="alFoot">
          Severity rule: &lt; 2h = Info • ≥ 2h = Warning • ≥ 10h = Critical
        </div>
      </div>
    </div>
  );
}


// // src/pages/DashboardAlerts.jsx
// import React, { useEffect, useMemo, useState } from "react";
// import {
//   AlertTriangle,
//   Users,
//   ShieldAlert,
//   Clock,
//   MapPin,
//   Camera,
//   RefreshCw,
//   Car,
// } from "lucide-react";

// import { listIncidentAlerts } from "../api/incidents";
// import { listTrafficFlowVehicles } from "../api/trafficFlow";

// import "../styles/dashboardAlerts.css";

// // ✅ ADD: reuse same card UI styles from TrafficFlowPage
// import "../styles/traffic.css";

// /* ================= helpers ================= */
// const pad2 = (n) => String(n).padStart(2, "0");
// const toInputDate = (d) =>
//   `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;

// function formatTime(ts) {
//   if (!ts) return "";
//   const d = new Date(ts);
//   if (Number.isNaN(d.getTime())) return String(ts);
//   return d.toLocaleString();
// }

// function toImgSrc(v) {
//   if (!v) return "";
//   if (String(v).startsWith("data:image")) return v;
//   if (/^[A-Za-z0-9+/=]+$/.test(v) && v.length > 200) {
//     return `data:image/jpeg;base64,${v}`;
//   }
//   return v;
// }

// // Traffic severity rules
// const computeSeverity = (dwellSeconds) => {
//   const s = Number(dwellSeconds || 0);
//   if (s >= 10 * 3600) return "CRITICAL";
//   if (s >= 2 * 3600) return "WARNING";
//   return "INFO";
// };

// /* ✅ message based on object_type + incident_type */
// function buildIncidentMessage(a) {
//   const it = (a?.incident_type || "").toLowerCase();
//   const ot = (a?.object_type || "").toLowerCase();

//   if (it === "crowd") {
//     const pc = a?.person_count ?? "-";
//     const mc = a?.max_count ?? "-";
//     return `Crowd detected. People ${pc} exceeded limit ${mc}.`;
//   }

//   if (ot.includes("vehicle"))
//     return "Unauthorized vehicle detected in restricted zone.";
//   if (ot.includes("hand")) return "Hand intrusion detected in restricted zone.";
//   if (ot.includes("door")) return "Door event detected in restricted zone.";
//   if (ot.includes("person") || ot.includes("people"))
//     return "Person detected in restricted zone.";

//   return a?.message || "Unauthorized activity detected.";
// }

// function incidentTag(type) {
//   const t = (type || "").toLowerCase();
//   if (t === "crowd") return { text: "Crowd", cls: "tagRed" };
//   if (t === "unauthorized") return { text: "Unauthorized", cls: "tagYellow" };
//   return { text: (type || "Alert").replaceAll("_", " "), cls: "tagBlue" };
// }

// /* ======= Severity mapping (same as TrafficFlowPage) ======= */
// const severityClass = (severity) => {
//   const s = (severity || "").toLowerCase();
//   if (s === "critical") return "tCard tCritical";
//   if (s === "warning") return "tCard tWarning";
//   return "tCard tInfo";
// };

// /* ================= Card (exactly like TrafficFlowPage) ================= */
// const DwellAlertCard = ({ alert }) => {
//   const sev = alert.severity || "INFO";

//   return (
//     <div className={severityClass(sev)}>
//       <div className="tCardRow">
//         <div className="tIconWrap">
//           <AlertTriangle size={18} />
//         </div>

//         <div className="tCardBody">
//           <div className="tPills">
//             <span className="tPill">{sev.toUpperCase()}</span>
//           </div>

//           <div className="tCardTitle">
//             <b>{alert.plate_text || "-"}</b> exceeded dwell time limit
//           </div>

//           <div className="tMeta">
//             <div className="tMetaItem">
//               <MapPin size={14} />
//               <span>{alert.location_text || "-"}</span>
//             </div>

//             <div className="tMetaItem">
//               <Clock size={14} />
//               <span>{alert.dwell_text || "-"}</span>
//             </div>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// /* ================= Page ================= */
// export default function DashboardAlerts() {
//   const POLL_MS = 5 * 60 * 1000;

//   const [now, setNow] = useState(new Date());
//   const [loading, setLoading] = useState(false);
//   const [err, setErr] = useState("");

//   const [incidentList, setIncidentList] = useState([]);
//   const [trafficList, setTrafficList] = useState([]);

//   const today = useMemo(() => toInputDate(new Date()), []);

//   // live clock
//   useEffect(() => {
//     const t = setInterval(() => setNow(new Date()), 1000);
//     return () => clearInterval(t);
//   }, []);

//   const loadAll = async () => {
//     setLoading(true);
//     setErr("");

//     try {
//       // ============ INCIDENTS: last 10 ============
//       const inc = await listIncidentAlerts({
//         status: "active",
//         incident_type: "all",
//         limit: 300,
//       });

//       const arr = Array.isArray(inc) ? inc : [];
//       arr.sort((a, b) => {
//         const ta = new Date(a?.timestamp || 0).getTime() || 0;
//         const tb = new Date(b?.timestamp || 0).getTime() || 0;
//         return tb - ta;
//       });
//       setIncidentList(arr.slice(0, 10));

//       // ============ TRAFFIC: last 10 ============
//       const tr = await listTrafficFlowVehicles({
//         limit: 10,
//         offset: 0,
//         date: today,
//         dwell_limit_seconds: 7200,
//       });

//       const rows = tr?.data || tr?.items || [];
//       const fixed = (Array.isArray(rows) ? rows : []).map((r) => ({
//         ...r,
//         severity: computeSeverity(r?.dwell_seconds),
//       }));

//       fixed.sort(
//         (a, b) => Number(b?.dwell_seconds || 0) - Number(a?.dwell_seconds || 0),
//       );

//       setTrafficList(fixed.slice(0, 10));
//     } catch (e) {
//       console.error(e);
//       setErr(e?.message || "Failed to load alerts");
//       setIncidentList([]);
//       setTrafficList([]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   // polling
//   useEffect(() => {
//     loadAll();
//     const t = setInterval(loadAll, POLL_MS);
//     return () => clearInterval(t);
//     // eslint-disable-next-line react-hooks/exhaustive-deps
//   }, []);

//   return (
//     <div className="alPage">
//       {/* ======= Top header like your image ======= */}
//       <div className="alTop">
//         <div>
//           <div className="alHeading">Active Alerts</div>
//           <div className="alSub">
//             Showing last <b>10 Incident</b> alerts + last <b>10 Traffic</b>{" "}
//             alerts (auto refresh)
//           </div>
//         </div>

//         <div className="alTopRight">
//           <div className="alClock">
//             <Clock size={16} />
//             <span>{now.toLocaleTimeString()}</span>
//           </div>

//           <button className="alBtn" onClick={loadAll} disabled={loading}>
//             <RefreshCw size={16} className={loading ? "spin" : ""} />
//             Refresh
//           </button>
//         </div>
//       </div>

//       {err ? <div className="alErr">{err}</div> : null}

//       {/* ======= INCIDENT LIST PANEL ======= */}
//       <div className="alPanel">
//         <div className="alPanelHead">
//           <div className="alPanelTitle">
//             <ShieldAlert size={18} />
//             Incident Alerts
//           </div>
//           <div className="alPanelHint">Last 10 (latest first)</div>
//         </div>

//         {incidentList.length === 0 ? (
//           <div className="alEmpty">No incident alerts</div>
//         ) : (
//           <div className="alList">
//             {incidentList.map((a) => {
//               const tag = incidentTag(a?.incident_type);
//               const isCrowd =
//                 String(a?.incident_type || "").toLowerCase() === "crowd";

//               return (
//                 <div key={a?.alert_id} className="alRow">
//                   <div
//                     className={`alIcon ${isCrowd ? "alIconRed" : "alIconOrange"}`}
//                   >
//                     {isCrowd ? <Users size={18} /> : <ShieldAlert size={18} />}
//                   </div>

//                   <div className="alBody">
//                     <div className="alTitleLine">
//                       <div className="alTitle">
//                         {isCrowd ? "Incident Alert" : "Unauthorized Alert"}
//                       </div>
//                       <span className={`alTag ${tag.cls}`}>{tag.text}</span>
//                     </div>

//                     <div className="alMsg">{buildIncidentMessage(a)}</div>

//                     <div className="alMeta">
//                       <span className="alMetaItem">
//                         <Camera size={14} />
//                         {a?.camera_name || "-"}
//                       </span>
//                       <span className="alMetaItem">
//                         <MapPin size={14} />
//                         {a?.zone_name || "-"}
//                       </span>
//                       <span className="alMetaItem">
//                         <Clock size={14} />
//                         {formatTime(a?.timestamp)}
//                       </span>
//                     </div>
//                   </div>

//                   <div className="alThumbBox">
//                     {a?.image_base64 ? (
//                       <img
//                         className="alThumb"
//                         src={toImgSrc(a.image_base64)}
//                         alt="incident"
//                       />
//                     ) : (
//                       <div className="alThumbEmpty">No image</div>
//                     )}
//                   </div>
//                 </div>
//               );
//             })}
//           </div>
//         )}
//       </div>

//       {/* ======= TRAFFIC LIST PANEL (✅ NOW SAME AS TrafficFlowPage) ======= */}
//       <div className="alPanel">
//         <div className="alPanelHead">
//           <div className="alPanelTitle">
//             <AlertTriangle size={18} />
//             Traffic Flow Alerts
//           </div>
//           <div className="alPanelHint">Last 10 (today)</div>
//         </div>

//         {trafficList.length === 0 ? (
//           <div className="alEmpty">No traffic alerts today</div>
//         ) : (
//           <div className="tList" style={{ paddingTop: 0 }}>
//             {trafficList.map((t, idx) => (
//               <DwellAlertCard
//                 key={t?.id ?? `${t?.plate_text}-${idx}`}
//                 alert={{
//                   ...t,
//                   // ensure these fields exist so card shows properly
//                   plate_text: t?.plate_text,
//                   location_text: t?.location_text || t?.location || "-",
//                   dwell_text:
//                     t?.dwell_text ||
//                     t?.dwell_time ||
//                     `${Math.round(Number(t?.dwell_seconds || 0) / 60)} min`,
//                 }}
//               />
//             ))}
//           </div>
//         )}

//         <div className="alFoot">
//           Severity rule: &lt; 2h = Info • ≥ 2h = Warning • ≥ 10h = Critical
//         </div>
//       </div>
//     </div>
//   );
// }
