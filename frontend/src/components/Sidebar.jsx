// Sidebar.jsx - WITHOUT SETTINGS
import React from "react";
import { AlertTriangle, Camera, Car, Shield, TrendingUp } from "lucide-react";

const NavItem = ({ icon: Icon, label, active, badge, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
        active
          ? "bg-blue-600 text-white shadow-sm"
          : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
      }`}
    >
      <Icon className="w-5 h-5" />
      <span className="font-medium">{label}</span>
      {badge && (
        <span className="ml-auto bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
          {badge}
        </span>
      )}
    </button>
  );
};

const Sidebar = ({ activeAlerts, currentPage, onPageChange }) => {
  // 5 main menu items ONLY
  const menuItems = [
    {
      id: "alerts",
      label: "Alerts",
      icon: AlertTriangle,
      badge: activeAlerts,
    },
    {
      id: "cameras",
      label: "Cameras",
      icon: Camera,
    },
    {
      id: "vehicles",
      label: "Vehicle Management",
      icon: Car,
    },
    {
      id: "access-control",
      label: "Access Control",
      icon: Shield,
    },
    {
      id: "traffic-flow",
      label: "Traffic Flow",
      icon: TrendingUp,
    },
  ];

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen shadow-sm">
      {/* Logo/Header */}
      <div className="p-6 border-b border-gray-200">
        <div
          className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
          onClick={() => onPageChange("alerts")}
        >
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center shadow-sm">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-gray-900 font-bold text-lg">Airtel</h1>
            <p className="text-gray-500 text-xs">Security Platform</p>
          </div>
        </div>
      </div>

      {/* Main Navigation - 5 items ONLY */}
      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => (
          <NavItem
            key={item.id}
            icon={item.icon}
            label={item.label}
            badge={item.badge}
            active={currentPage === item.id}
            onClick={() => onPageChange(item.id)}
          />
        ))}
      </nav>

      {/* Bottom Section - System Status Only */}
      <div className="p-4 border-t border-gray-200">
        <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-gray-600">System Status</span>
          </div>
          <p className="text-gray-900 text-sm font-semibold">
            All Systems Operational
          </p>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
