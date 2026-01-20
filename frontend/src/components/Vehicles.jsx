import React, { useEffect, useMemo, useState } from "react";
import { api } from "../data/api.js";
import { vehicleLogsData as fallback } from "../data/dummyData.js";

function statusTag(s) {
  if (s === "authorized") return "tag tagOk";
  return "tag tagCritical";
}

export default function Vehicles() {
  const [rows, setRows] = useState(fallback);

  useEffect(() => {
    api.vehicles().then(setRows).catch(() => {});
  }, []);

  const counts = useMemo(() => {
    const authorized = rows.filter((r) => r.status === "authorized").length;
    const blacklisted = rows.filter((r) => r.status === "blacklisted").length;
    return { authorized, blacklisted };
  }, [rows]);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div className="cardTitle">Vehicle Management (LPR)</div>
          <div className="muted">{counts.authorized} authorized • {counts.blacklisted} blacklisted</div>
        </div>
        <button className="btn btnPrimary" onClick={() => api.vehicles().then(setRows).catch(() => {})}>Refresh</button>
      </div>

      <div className="card">
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Plate</th>
                <th>Type</th>
                <th>Status</th>
                <th>Entry</th>
                <th>Exit</th>
                <th>Dwell</th>
                <th>Location</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((v) => (
                <tr key={v.id}>
                  <td style={{ fontWeight: 900 }}>{v.licensePlate}</td>
                  <td>{v.type}</td>
                  <td><span className={statusTag(v.status)}>{v.status}</span></td>
                  <td>{v.entryTime}</td>
                  <td>{v.exitTime || "-"}</td>
                  <td style={{ fontWeight: 800 }}>{v.dwellTime}</td>
                  <td>{v.location}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
