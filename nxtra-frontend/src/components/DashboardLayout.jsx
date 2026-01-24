// src/components/DashboardLayout.jsx
import React from "react";
import DashboardSidebar from "./DashboardSidebar";
import bg from "../assets/nxtra-bg.png"; // ✅ same bg used everywhere

export default function DashboardLayout({ children, active }) {
  return (
    <div style={styles.root(bg)}>
      <div style={styles.overlay} />

      <div style={styles.shell}>
        <DashboardSidebar active={active} />
        <main style={styles.main}>{children}</main>
      </div>
    </div>
  );
}

const styles = {
  root: (bgUrl) => ({
    minHeight: "100vh",
    padding: 18,
    position: "relative",
    backgroundImage: `url(${bgUrl})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    backgroundAttachment: "fixed",
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial',
  }),
  overlay: {
    position: "absolute",
    inset: 0,
    background: "linear-gradient(180deg, rgba(0,0,0,0.30), rgba(0,0,0,0.55))",
    pointerEvents: "none",
  },
  shell: {
    position: "relative",
    zIndex: 2,
    display: "grid",
    gridTemplateColumns: "290px 1fr",
    gap: 16,
    alignItems: "start",
  },
  main: {
    borderRadius: 18,
    background: "rgba(0,0,0,0.40)",

    // background: "rgba(255,255,255,0.10)",
    border: "1px solid rgba(255,255,255,0.18)",
    boxShadow: "0 18px 40px rgba(0,0,0,0.25)",
    backdropFilter: "blur(14px)",
    WebkitBackdropFilter: "blur(14px)",
    padding: 18,
    minHeight: "calc(100vh - 36px)",
  },
};
