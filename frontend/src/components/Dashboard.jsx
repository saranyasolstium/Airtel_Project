import React, { useEffect, useState } from "react";
import { api } from "../data/api.js";
import { statisticsData as fallbackStats } from "../data/dummyData.js";

export default function Dashboard() {
  const [stats, setStats] = useState(fallbackStats);

  useEffect(() => {
    api.stats().then(setStats).catch(() => {});
  }, []);

  const items = [
    { label: "Total Cameras", value: stats.totalCameras },
    { label: "Active Cameras", value: stats.activeCameras },
    { label: "Active Alerts", value: stats.activeAlerts },
    { label: "Today Incidents", value: stats.todayIncidents },
    { label: "Authorized Vehicles", value: stats.authorizedVehicles },
    { label: "Blacklisted Attempts", value: stats.blacklistedAttempts },
    { label: "PPE Compliance", value: `${stats.ppeCompliance}%` },
    { label: "Avg Response Time", value: stats.avgResponseTime },
  ];

  return (
    <div className="grid grid4">
      {items.map((x) => (
        <div className="card" key={x.label}>
          <div className="muted">{x.label}</div>
          <div className="kpi">{x.value}</div>
        </div>
      ))}
    </div>
  );
}
