import React, { useEffect, useState } from "react";
import { api } from "../data/api.js";
import { ppeComplianceData as fallback } from "../data/dummyData.js";

function statusTag(s) {
  if (s === "compliant") return "tag tagOk";
  return "tag tagWarning";
}

export default function PPE() {
  const [rows, setRows] = useState(fallback);

  useEffect(() => {
    api.ppe().then(setRows).catch(() => {});
  }, []);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div className="cardTitle">PPE Compliance</div>
          <div className="muted">{rows.length} zones</div>
        </div>
        <button className="btn btnPrimary" onClick={() => api.ppe().then(setRows).catch(() => {})}>Refresh</button>
      </div>

      <div className="grid grid2">
        {rows.map((p) => (
          <div className="card" key={p.id}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
              <div style={{ fontWeight: 900 }}>{p.zone}</div>
              <span className={statusTag(p.status)}>{p.status}</span>
            </div>
            <div style={{ marginTop: 10, display: "flex", justifyContent: "space-between" }}>
              <span className="muted">Personnel</span>
              <span style={{ fontWeight: 800 }}>{p.personnel}</span>
            </div>
            <div style={{ marginTop: 8, display: "flex", justifyContent: "space-between" }}>
              <span className="muted">Compliant</span>
              <span style={{ fontWeight: 800 }}>{p.compliant}</span>
            </div>
            <div style={{ marginTop: 8, display: "flex", justifyContent: "space-between" }}>
              <span className="muted">Violations</span>
              <span style={{ fontWeight: 900, color: p.violations ? "var(--warn)" : "var(--ok)" }}>{p.violations}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
