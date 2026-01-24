// src/components/DashboardSidebar.jsx
import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { createPortal } from "react-dom";
import "../styles/sidebar.css";
import { clearAuth } from "../utils/storage"; // optional

export default function DashboardSidebar({ active }) {
  const location = useLocation();
  const navigate = useNavigate();

  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  // ✅ safer auto-detect
  const path = location.pathname;
  const current =
    active ||
    (path.includes("dashboard-alert")
      ? "alerts"
      : path.includes("dashboard-cameras")
        ? "cameras"
        : path.includes("dashboard-vehicles")
          ? "vehicles"
          : path.includes("dashboard-incidents")
            ? "incidents"
            : path.includes("dashboard-access")
              ? "access"
              : path.includes("dashboard-traffic")
                ? "traffic"
                : "");

  const menu = [
    {
      key: "alerts",
      label: "Alerts",
      to: "/dashboard-alert",
      icon: "🚨",
      badge: 3,
    },
    { key: "cameras", label: "Cameras", to: "/dashboard-cameras", icon: "📷" },
    {
      key: "vehicles",
      label: "Vehicle Management",
      to: "/dashboard-vehicles",
      icon: "🚗",
    },
    {
      key: "incidents",
      label: "Incident Types",
      to: "/dashboard-incidents",
      icon: "🛡️",
    },
    {
      key: "traffic",
      label: "Traffic Flow",
      to: "/dashboard-traffic",
      icon: "🛣️",
    },
  ];

  const doLogout = () => {
    try {
      clearAuth?.();
      localStorage.removeItem("auth");
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    } catch (e) {
      console.warn("logout failed:", e);
    }
    navigate("/login");
  };

  // ✅ ESC closes popup
  useEffect(() => {
    if (!showLogoutConfirm) return;
    const onKey = (e) => {
      if (e.key === "Escape") setShowLogoutConfirm(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [showLogoutConfirm]);

  // ✅ Optional: prevent background scroll when modal open
  useEffect(() => {
    if (!showLogoutConfirm) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [showLogoutConfirm]);

  return (
    <div className="sb">
      {/* USER */}
      <div className="sbUserCard">
        <div className="sbUserTitle">Nxtra Data Center</div>
        <div className="sbUserSub">admin@nxtra.com</div>
      </div>

      {/* MENU */}
      <div className="sbMenu">
        {menu.map((m) => (
          <Link
            key={m.key}
            to={m.to}
            className={`sbItem ${current === m.key ? "active" : ""}`}
          >
            <span className="sbIcon">{m.icon}</span>
            <span className="sbLabel">{m.label}</span>
            {m.badge ? <span className="sbBadge">{m.badge}</span> : null}
          </Link>
        ))}
      </div>

      {/* FOOTER */}
      <div className="sbFooter">
        <button
          className="sbLogout"
          type="button"
          onClick={() => setShowLogoutConfirm(true)}
        >
          ⏻ Logout
        </button>
        <div className="sbVer">Platform v1.0.1</div>
      </div>

      {/* ✅ MODAL (PORTAL) => centered on whole page */}
      {showLogoutConfirm &&
        createPortal(
          <div
            className="nxModalOverlay"
            role="dialog"
            aria-modal="true"
            onClick={() => setShowLogoutConfirm(false)} // click outside closes
          >
            <div className="nxModal" onClick={(e) => e.stopPropagation()}>
              <div className="nxModalTop">
                <div className="nxModalIcon">⏻</div>
                <div>
                  <div className="nxModalTitle">Confirm Logout</div>
                  <div className="nxModalSub">
                    Are you sure you want to logout?
                  </div>
                </div>
              </div>

              <div className="nxModalActions">
                <button
                  className="nxBtn nxBtnGhost"
                  type="button"
                  onClick={() => setShowLogoutConfirm(false)}
                >
                  Cancel
                </button>

                <button
                  className="nxBtn nxBtnDanger"
                  type="button"
                  onClick={() => {
                    setShowLogoutConfirm(false);
                    doLogout();
                  }}
                >
                  Logout
                </button>
              </div>

              <div className="nxModalHint">
                Tip: Press <b>Esc</b> to close
              </div>
            </div>
          </div>,
          document.body,
        )}
    </div>
  );
}
