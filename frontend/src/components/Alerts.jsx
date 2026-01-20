import React, { useEffect, useMemo, useState } from "react";
import { api } from "../data/api.js";
import { alertsData as fallbackAlerts } from "../data/dummyData.js";

function tagClass(type) {
  if (type === "critical") return "tag tagCritical";
  if (type === "warning") return "tag tagWarning";
  return "tag tagInfo";
}

export default function Alerts() {
  const [alerts, setAlerts] = useState(fallbackAlerts);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    api.alerts().then(setAlerts).catch(() => {});
  }, []);

  const filtered = useMemo(() => {
    if (filter === "all") return alerts;
    if (filter === "active") return alerts.filter((a) => a.status === "active");
    if (filter === "critical") return alerts.filter((a) => a.type === "critical");
    return alerts;
  }, [alerts, filter]);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
        <div>
          <div className="cardTitle">Alert Management</div>
          <div className="muted">{alerts.length} total alerts</div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <select className="btn" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="critical">Critical</option>
          </select>
          <button className="btn btnPrimary" onClick={() => api.alerts().then(setAlerts).catch(() => {})}>Refresh</button>
        </div>
      </div>

      <div className="card">
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Category</th>
                <th>Message</th>
                <th>Camera</th>
                <th>Location</th>
                <th>Status</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={a.id}>
                  <td><span className={tagClass(a.type)}>{a.type}</span></td>
                  <td>{a.category}</td>
                  <td>{a.message}</td>
                  <td>{a.camera}</td>
                  <td>{a.location}</td>
                  <td><span className={`tag ${a.status === "resolved" ? "tagOk" : a.status === "investigating" ? "tagWarning" : "tagCritical"}`}>{a.status}</span></td>
                  <td className="muted">{a.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
