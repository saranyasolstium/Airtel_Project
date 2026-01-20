import React, { useEffect, useState } from "react";
import { api } from "../data/api.js";
import { restrictedZoneEvents as fallbackA, thermalBreachEvents as fallbackB } from "../data/dummyData.js";

function sevTag(s) {
  if (s === "critical") return "tag tagCritical";
  if (s === "warning") return "tag tagWarning";
  return "tag tagInfo";
}
function thermalTag(s) {
  if (s === "breach") return "tag tagCritical";
  return "tag tagOk";
}

export default function RestrictedZones() {
  const [zoneEvents, setZoneEvents] = useState(fallbackA);
  const [thermal, setThermal] = useState(fallbackB);

  const refresh = () => {
    api.zones()
      .then((d) => {
        setZoneEvents(d.restrictedZoneEvents || fallbackA);
        setThermal(d.thermalBreachEvents || fallbackB);
      })
      .catch(() => {});
  };

  useEffect(() => { refresh(); }, []);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div className="cardTitle">Restricted Zones</div>
          <div className="muted">Zone events + thermal status</div>
        </div>
        <button className="btn btnPrimary" onClick={refresh}>Refresh</button>
      </div>

      <div className="grid grid2">
        <div className="card">
          <div className="cardTitle">Zone Events</div>
          <div className="tableWrap" style={{ marginTop: 10 }}>
            <table style={{ minWidth: 650 }}>
              <thead>
                <tr>
                  <th>Zone</th>
                  <th>Event</th>
                  <th>Severity</th>
                  <th>Persons</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {zoneEvents.map((e) => (
                  <tr key={e.id}>
                    <td style={{ fontWeight: 900 }}>{e.zone}</td>
                    <td>{e.eventType}</td>
                    <td><span className={sevTag(e.severity)}>{e.severity}</span></td>
                    <td>{e.personCount}</td>
                    <td className="muted">{e.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="cardTitle">Thermal Breaches</div>
          <div className="tableWrap" style={{ marginTop: 10 }}>
            <table style={{ minWidth: 650 }}>
              <thead>
                <tr>
                  <th>Aisle</th>
                  <th>Temp</th>
                  <th>Threshold</th>
                  <th>Status</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {thermal.map((t) => (
                  <tr key={t.id}>
                    <td style={{ fontWeight: 900 }}>{t.aisle}</td>
                    <td>{t.temperature}°C</td>
                    <td>{t.threshold}°C</td>
                    <td><span className={thermalTag(t.status)}>{t.status}</span></td>
                    <td className="muted">{t.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
