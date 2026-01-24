// src/pages/DashboardAlerts.jsx
import React, { useEffect, useMemo, useState } from "react";
import bg from "../assets/nxtra-bg.png";
import { getAuth } from "../utils/storage";

export default function DashboardAlert() {
  const auth = getAuth();
  const user = auth?.user;

  // Live time
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Demo alerts
  const [alerts, setAlerts] = useState([
    {
      id: 1,
      type: "UNAUTHORIZED ENTRY",
      status: "Active",
      severity: "Critical",
      message: "Person detected in restricted zone - Substation Room B",
      cam: "CAM-012",
      location: "North Perimeter",
      time: "2026-01-24 11:59:12",
    },
    {
      id: 2,
      type: "PPE COMPLIANCE",
      status: "Active",
      severity: "Warning",
      message: "Personnel without helmet detected in Data Floor 3",
      cam: "CAM-045",
      location: "Data Centre Floor 3",
      time: "2026-01-24 11:52:40",
    },
    {
      id: 3,
      type: "CROWD FORMATION",
      status: "Resolved",
      severity: "Warning",
      message: "Crowd density threshold exceeded near Entry Gate",
      cam: "CAM-018",
      location: "Main Gate",
      time: "2026-01-24 11:35:08",
    },
  ]);

  const stats = useMemo(() => {
    const total = alerts.length;
    const active = alerts.filter((a) => a.status === "Active").length;
    const critical = alerts.filter((a) => a.severity === "Critical").length;
    const resolved = alerts.filter((a) => a.status === "Resolved").length;
    return { total, active, critical, resolved };
  }, [alerts]);

  function resolveAlert(id) {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: "Resolved" } : a)),
    );
  }

  function dismissAlert(id) {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  }

  const dateStr = now.toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const timeStr = now.toLocaleTimeString();

  return (
    <div style={styles.page(bg)}>
      <div style={styles.overlay} />

      {/* ✅ Only the main content — sidebar is already in DashboardLayout */}
      <div style={styles.content}>
        {/* Header */}
        <div style={styles.headerRow}>
          <div>
            <div style={styles.h1}>Alerts Management</div>
            <div style={styles.h2}>{dateStr}</div>
            {user ? (
              <div style={styles.userLine}>
                Logged in as <b>{user.full_name || user.email}</b>
              </div>
            ) : null}
          </div>

          <div style={styles.headerRight}>
            <div style={styles.clockChip}>🕒 {timeStr}</div>
            <div style={styles.bell}>
              🔔 <span style={styles.bellBadge}>3</span>
            </div>
          </div>
        </div>

        {/* KPI */}
        <div style={styles.kpis}>
          <Kpi label="Total Alerts" value={stats.total} />
          <Kpi label="Active" value={stats.active} accent="warn" />
          <Kpi label="Critical" value={stats.critical} accent="crit" />
          <Kpi label="Resolved" value={stats.resolved} accent="ok" />
        </div>

        {/* List */}
        <div style={styles.section}>
          <div style={styles.sectionHead}>
            <div style={styles.sectionTitle}>Alert Management</div>

            <div style={styles.controls}>
              <select style={styles.select}>
                <option>All Alerts</option>
                <option>Active</option>
                <option>Resolved</option>
                <option>Critical</option>
              </select>

              <select style={styles.select}>
                <option>Latest First</option>
                <option>Oldest First</option>
              </select>

              <button style={styles.exportBtn}>Export Report</button>
            </div>
          </div>

          <div style={styles.list}>
            {alerts.map((a) => (
              <AlertCard
                key={a.id}
                a={a}
                onResolve={() => resolveAlert(a.id)}
                onDismiss={() => dismissAlert(a.id)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Kpi({ label, value, accent }) {
  const color =
    accent === "crit"
      ? "var(--nxtra-red)"
      : accent === "ok"
        ? "#22c55e"
        : accent === "warn"
          ? "#f59e0b"
          : "rgba(255,255,255,0.92)";

  return (
    <div style={styles.kpiCard}>
      <div style={styles.kpiLabel}>{label}</div>
      <div style={{ ...styles.kpiValue, color }}>{value}</div>
    </div>
  );
}

function AlertCard({ a, onResolve, onDismiss }) {
  const bg =
    a.severity === "Critical"
      ? "rgba(227,27,35,0.12)"
      : "rgba(245,158,11,0.12)";

  const border =
    a.severity === "Critical"
      ? "rgba(227,27,35,0.25)"
      : "rgba(245,158,11,0.25)";

  return (
    <div
      style={{
        ...styles.alertCard,
        background: bg,
        border: `1px solid ${border}`,
      }}
    >
      <div style={styles.alertTop}>
        <div style={styles.alertIcon}>
          {a.severity === "Critical" ? "⛔" : "⚠️"}
        </div>

        <div style={{ flex: 1 }}>
          <div style={styles.alertTypeRow}>
            <div style={styles.alertType}>{a.type}</div>
            <div style={styles.pill(a.status)}>{a.status}</div>
          </div>

          <div style={styles.alertMsg}>{a.message}</div>

          <div style={styles.metaRow}>
            <div style={styles.meta}>👁 {a.cam}</div>
            <div style={styles.meta}>📍 {a.location}</div>
            <div style={styles.meta}>🕒 {a.time}</div>
            <div style={styles.meta}>ID: {a.id}</div>
          </div>

          <div style={styles.btnRow}>
            <button style={styles.viewBtn}>View Details</button>
            {a.status !== "Resolved" ? (
              <button style={styles.resolveBtn} onClick={onResolve}>
                Resolve
              </button>
            ) : null}
            <button style={styles.dismissBtn} onClick={onDismiss}>
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: (bgUrl) => ({
    position: "relative",
    minHeight: "calc(100vh - 36px)",
    borderRadius: 18,
    overflow: "hidden",
    backgroundImage: `url(${bgUrl})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
  }),
  overlay: {
    position: "absolute",
    inset: 0,
    background: "linear-gradient(180deg, rgba(0,0,0,0.30), rgba(0,0,0,0.55))",
    pointerEvents: "none",
  },
  content: { position: "relative", zIndex: 2, padding: 18 },

  headerRow: { display: "flex", justifyContent: "space-between", gap: 16 },
  h1: { fontSize: 30, fontWeight: 900, color: "rgba(255,255,255,0.95)" },
  h2: { color: "rgba(255,255,255,0.70)", marginTop: 6 },
  userLine: { marginTop: 6, color: "rgba(255,255,255,0.70)", fontSize: 13 },

  headerRight: { display: "flex", gap: 12, alignItems: "center" },
  clockChip: {
    padding: "10px 12px",
    borderRadius: 999,
    background: "rgba(255,255,255,0.10)",
    border: "1px solid rgba(255,255,255,0.18)",
    color: "rgba(255,255,255,0.92)",
    fontWeight: 900,
  },
  bell: {
    position: "relative",
    width: 44,
    height: 44,
    borderRadius: 14,
    display: "grid",
    placeItems: "center",
    background: "rgba(255,255,255,0.10)",
    border: "1px solid rgba(255,255,255,0.18)",
    color: "rgba(255,255,255,0.92)",
  },
  bellBadge: {
    position: "absolute",
    top: -6,
    right: -6,
    width: 22,
    height: 22,
    borderRadius: 999,
    display: "grid",
    placeItems: "center",
    background: "var(--nxtra-red)",
    color: "white",
    fontWeight: 900,
    fontSize: 12,
  },

  kpis: {
    marginTop: 18,
    display: "grid",
    gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
    gap: 12,
  },
  kpiCard: {
    borderRadius: 16,
    padding: 16,
    background: "rgba(255,255,255,0.10)",
    border: "1px solid rgba(255,255,255,0.18)",
  },
  kpiLabel: { color: "rgba(255,255,255,0.70)", fontSize: 13 },
  kpiValue: { marginTop: 10, fontSize: 32, fontWeight: 900 },

  section: {
    marginTop: 16,
    borderRadius: 16,
    padding: 16,
    background: "rgba(255,255,255,0.10)",
    border: "1px solid rgba(255,255,255,0.18)",
  },
  sectionHead: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 900,
    color: "rgba(255,255,255,0.95)",
  },

  controls: {
    display: "flex",
    gap: 10,
    alignItems: "center",
    flexWrap: "wrap",
  },
  select: {
    padding: "10px 12px",
    borderRadius: 12,
    border: "1px solid rgba(255,255,255,0.18)",
    background: "rgba(0,0,0,0.18)",
    color: "rgba(255,255,255,0.90)",
    outline: "none",
  },
  exportBtn: {
    padding: "10px 14px",
    borderRadius: 12,
    border: "none",
    cursor: "pointer",
    fontWeight: 900,
    color: "white",
    background:
      "linear-gradient(180deg, var(--nxtra-red), var(--nxtra-red-dark))",
    boxShadow: "0 12px 30px rgba(227, 27, 35, 0.18)",
  },

  list: { display: "flex", flexDirection: "column", gap: 14 },

  alertCard: { borderRadius: 16, padding: 14 },
  alertTop: { display: "flex", gap: 12, alignItems: "flex-start" },
  alertIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    display: "grid",
    placeItems: "center",
    background: "rgba(255,255,255,0.10)",
    border: "1px solid rgba(255,255,255,0.18)",
    fontSize: 18,
  },
  alertTypeRow: {
    display: "flex",
    gap: 10,
    alignItems: "center",
    justifyContent: "space-between",
  },
  alertType: { fontWeight: 900, color: "rgba(255,255,255,0.92)" },
  pill: (status) => ({
    padding: "6px 10px",
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 900,
    background:
      status === "Resolved" ? "rgba(34,197,94,0.16)" : "rgba(227,27,35,0.16)",
    color: status === "Resolved" ? "#22c55e" : "var(--nxtra-red)",
    border: "1px solid rgba(255,255,255,0.14)",
  }),
  alertMsg: { marginTop: 6, fontSize: 15, color: "rgba(255,255,255,0.90)" },
  metaRow: {
    marginTop: 10,
    display: "grid",
    gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
    gap: 10,
    color: "rgba(255,255,255,0.70)",
    fontSize: 12,
  },
  meta: { display: "flex", gap: 6, alignItems: "center" },

  btnRow: { marginTop: 12, display: "flex", gap: 10, flexWrap: "wrap" },
  viewBtn: {
    padding: "8px 12px",
    borderRadius: 12,
    border: "none",
    cursor: "pointer",
    fontWeight: 900,
    color: "white",
    background: "rgba(37,99,235,0.85)",
  },
  resolveBtn: {
    padding: "8px 12px",
    borderRadius: 12,
    border: "none",
    cursor: "pointer",
    fontWeight: 900,
    color: "white",
    background: "rgba(34,197,94,0.85)",
  },
  dismissBtn: {
    padding: "8px 12px",
    borderRadius: 12,
    border: "1px solid rgba(255,255,255,0.18)",
    cursor: "pointer",
    fontWeight: 900,
    background: "rgba(0,0,0,0.18)",
    color: "rgba(255,255,255,0.90)",
  },
};
