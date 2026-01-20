import React, { useEffect, useState } from "react";
import { api } from "../data/api.js";
import { camerasData as fallback } from "../data/dummyData.js";

function statusTag(s) {
  if (s === "online") return "tag tagOk";
  if (s === "warning") return "tag tagWarning";
  return "tag tagCritical";
}

export default function Cameras() {
  const [cameras, setCameras] = useState(fallback);

  useEffect(() => {
    api.cameras().then(setCameras).catch(() => {});
  }, []);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div className="cardTitle">Cameras</div>
          <div className="muted">{cameras.length} cameras</div>
        </div>
        <button className="btn btnPrimary" onClick={() => api.cameras().then(setCameras).catch(() => {})}>Refresh</button>
      </div>

      <div className="grid grid4">
        {cameras.map((c) => (
          <div className="card" key={c.id}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
              <div style={{ fontWeight: 900 }}>{c.name}</div>
              <span className={statusTag(c.status)}>{c.status}</span>
            </div>
            <div className="muted" style={{ marginTop: 8 }}>ID: {c.id}</div>
            <div style={{ marginTop: 10, display: "flex", justifyContent: "space-between" }}>
              <span className="muted">Location</span>
              <span>{c.location}</span>
            </div>
            <div style={{ marginTop: 10, display: "flex", justifyContent: "space-between" }}>
              <span className="muted">Health</span>
              <span style={{ fontWeight: 900 }}>{c.health}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
