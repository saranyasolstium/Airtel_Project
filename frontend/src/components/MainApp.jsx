// MainApp.jsx - UPDATED WITH TRAFFIC FLOW AND PPE REMOVED
import React, { useState } from "react";
import Layout from "./Layout";
import AlertsPage from "../pages/AlertsPage";
import CamerasPage from "../pages/CamerasPage";
import VehiclesPage from "../pages/VehiclesPage";
import AccessControlPage from "../pages/AccessControlPage";
import TrafficFlowPage from "../pages/TrafficFlowPage"; // Added
import SettingsPage from "../pages/SettingsPage";
import { alertsData } from "../data/dummyData";

const MainApp = () => {
  const [currentPage, setCurrentPage] = useState("alerts"); // Default to alerts
  const activeAlerts = alertsData.filter((a) => a.status === "active").length;

  // UPDATED: 6 pages with Traffic Flow instead of PPE
  const pageConfig = {
    alerts: {
      title: "Alerts Management",
      component: <AlertsPage />,
    },
    cameras: {
      title: "Camera Management",
      component: <CamerasPage />,
    },
    vehicles: {
      title: "Vehicle Management & LPR",
      component: <VehiclesPage />,
    },
    "access-control": {
      title: "Access Control & Security",
      component: <AccessControlPage />,
    },
    "traffic-flow": {
      // Added Traffic Flow
      title: "Traffic Flow Management",
      component: <TrafficFlowPage />,
    },
    settings: {
      title: "Settings & Configuration",
      component: <SettingsPage />,
    },
    // PPE Compliance has been removed
  };

  const currentConfig = pageConfig[currentPage] || pageConfig.alerts;

  return (
    <Layout
      title={currentConfig.title}
      activeAlerts={activeAlerts}
      onPageChange={setCurrentPage}
      currentPage={currentPage}
    >
      {currentConfig.component}
    </Layout>
  );
};

export default MainApp;
