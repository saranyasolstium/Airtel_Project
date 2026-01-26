// src/App.jsx
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import AuthPage from "./pages/AuthPage";
import DashboardAlert from "./pages/DashboardAlerts";
import CamerasPage from "./pages/CamerasPage";
import VehiclesPage from "./pages/VehiclesPage";
import DashboardLayout from "./components/DashboardLayout";
import TrafficFlowPage from "./pages/TrafficFlowPage";
import IncidentsPage from "./pages/IncidentsPage";
import WhitelistPage from "./pages/WhitelistPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />

        <Route path="/login" element={<AuthPage defaultMode="login" />} />
        <Route path="/register" element={<AuthPage defaultMode="register" />} />

        {/* Alerts */}
        <Route
          path="/dashboard-alert"
          element={
            <DashboardLayout active="alerts">
              <DashboardAlert />
            </DashboardLayout>
          }
        />

        {/* Cameras */}
        <Route
          path="/dashboard-cameras"
          element={
            <DashboardLayout active="cameras">
              <CamerasPage />
            </DashboardLayout>
          }
        />

        {/* ✅ Vehicles */}
        <Route
          path="/dashboard-vehicles"
          element={
            <DashboardLayout active="vehicles">
              <VehiclesPage />
            </DashboardLayout>
          }
        />

        <Route
          path="/dashboard-traffic"
          element={
            <DashboardLayout active="traffic">
              <TrafficFlowPage />
            </DashboardLayout>
          }
        />

        <Route
          path="/dashboard-incidents"
          element={
            <DashboardLayout active="incidents">
              <IncidentsPage />
            </DashboardLayout>
          }
        />
        <Route
          path="/dashboard-whitelist"
          element={
            <DashboardLayout active="whitelist">
              <WhitelistPage />
            </DashboardLayout>
          }
        />

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
