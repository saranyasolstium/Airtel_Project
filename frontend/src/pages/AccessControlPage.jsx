// AccessControlPage.jsx - ENHANCED VISUAL DESIGN
import React, { useState } from "react";
import {
  Shield,
  UserCheck,
  UserX,
  Camera,
  AlertTriangle,
  MapPin,
  Clock,
  Download,
  CheckCircle,
  XCircle,
  Activity,
  Zap,
  TrendingUp,
  BarChart3,
  Users,
  Filter,
} from "lucide-react";

// Color Theme: Modern Blue/Teal with gradients
const colorTheme = {
  primary: "bg-gradient-to-r from-teal-500 to-cyan-500",
  primaryHover: "hover:from-teal-600 hover:to-cyan-600",
  primaryLight: "bg-gradient-to-br from-teal-50 to-cyan-50",
  primaryBorder: "border-cyan-200",
  primaryText: "text-cyan-700",

  success: "bg-gradient-to-r from-emerald-500 to-green-500",
  successLight: "bg-gradient-to-br from-emerald-50 to-green-50",
  successBorder: "border-emerald-200",
  successText: "text-emerald-700",

  warning: "bg-gradient-to-r from-amber-500 to-orange-500",
  warningLight: "bg-gradient-to-br from-amber-50 to-orange-50",
  warningBorder: "border-amber-200",
  warningText: "text-amber-700",

  danger: "bg-gradient-to-r from-rose-500 to-pink-500",
  dangerLight: "bg-gradient-to-br from-rose-50 to-pink-50",
  dangerBorder: "border-rose-200",
  dangerText: "text-rose-700",

  secondary: "bg-gradient-to-r from-indigo-500 to-purple-500",
  secondaryLight: "bg-gradient-to-br from-indigo-50 to-purple-50",
  secondaryBorder: "border-indigo-200",
  secondaryText: "text-indigo-700",
};

const AccessEventCard = ({ event }) => {
  const getEventConfig = (type) => {
    const configs = {
      unauthorized: {
        icon: UserX,
        bgColor: "bg-gradient-to-br from-rose-50/80 to-pink-50/80",
        borderColor: "border-rose-200",
        iconColor: "text-rose-600",
        iconBg: "bg-gradient-to-br from-rose-100 to-pink-100",
      },
      loitering: {
        icon: AlertTriangle,
        bgColor: "bg-gradient-to-br from-amber-50/80 to-orange-50/80",
        borderColor: "border-amber-200",
        iconColor: "text-amber-600",
        iconBg: "bg-gradient-to-br from-amber-100 to-orange-100",
      },
      trespassing: {
        icon: Shield,
        bgColor: "bg-gradient-to-br from-indigo-50/80 to-purple-50/80",
        borderColor: "border-indigo-200",
        iconColor: "text-indigo-600",
        iconBg: "bg-gradient-to-br from-indigo-100 to-purple-100",
      },
      authorized: {
        icon: UserCheck,
        bgColor: "bg-gradient-to-br from-emerald-50/80 to-green-50/80",
        borderColor: "border-emerald-200",
        iconColor: "text-emerald-600",
        iconBg: "bg-gradient-to-br from-emerald-100 to-green-100",
      },
    };
    return configs[type] || configs.unauthorized;
  };

  const config = getEventConfig(event.type);
  const Icon = config.icon;

  return (
    <div
      className={`${config.bgColor} border ${config.borderColor} rounded-xl p-4 backdrop-blur-sm transition-all hover:shadow-md hover:scale-[1.01]`}
    >
      <div className="flex items-start gap-4">
        <div
          className={`p-3 rounded-xl ${config.iconBg} border ${config.borderColor} shadow-sm`}
        >
          <Icon className={`w-5 h-5 ${config.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <span
              className={`text-xs font-semibold ${config.iconColor} bg-white/70 px-2 py-1 rounded-full border ${config.borderColor}`}
            >
              {event.type.charAt(0).toUpperCase() + event.type.slice(1)}
            </span>
            <span className="text-xs font-medium px-2 py-1 rounded-full bg-white/50 border border-gray-300 text-gray-600">
              {event.severity}
            </span>
          </div>
          <h3 className="text-gray-900 font-medium text-sm mb-3 leading-snug">
            {event.title}
          </h3>
          <div className="flex flex-wrap gap-4 text-xs">
            <div className="flex items-center gap-2 text-gray-600">
              <MapPin className="w-3 h-3" />
              <span>{event.zone}</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <Camera className="w-3 h-3" />
              <span>{event.camera}</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <Clock className="w-3 h-3" />
              <span>{event.timestamp}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const AccessControlPage = () => {
  const [activeFilter, setActiveFilter] = useState("all");
  const [timeRange, setTimeRange] = useState("24h");

  // Mock data
  const accessEvents = [
    {
      id: 1,
      type: "unauthorized",
      title: "Person detected in restricted zone - Substation Room B",
      severity: "critical",
      zone: "Substation Area",
      camera: "CAM-012",
      timestamp: "14:23:15",
    },
    {
      id: 2,
      type: "loitering",
      title: "Suspicious loitering near perimeter fence - North side",
      severity: "warning",
      zone: "North Perimeter",
      camera: "CAM-008",
      timestamp: "13:45:30",
    },
    {
      id: 3,
      type: "trespassing",
      title: "Unauthorized vehicle attempting gate access",
      severity: "critical",
      zone: "Main Gate",
      camera: "CAM-001",
      timestamp: "12:15:22",
    },
    {
      id: 4,
      type: "authorized",
      title: "Maintenance crew entry - Scheduled activity",
      severity: "info",
      zone: "East Gate",
      camera: "CAM-005",
      timestamp: "11:30:45",
    },
  ];

  const stats = [
    {
      label: "Secure Zones",
      value: "9/12",
      icon: CheckCircle,
      color: "text-emerald-600",
      bgColor: "bg-gradient-to-br from-emerald-50 to-green-50",
      trend: "+2 this week",
      progress: 75,
    },
    {
      label: "Active Alerts",
      value: "3",
      icon: AlertTriangle,
      color: "text-amber-600",
      bgColor: "bg-gradient-to-br from-amber-50 to-orange-50",
      trend: "1 critical",
    },
    {
      label: "Cameras Active",
      value: "45",
      icon: Camera,
      color: "text-cyan-600",
      bgColor: "bg-gradient-to-br from-cyan-50 to-teal-50",
      trend: "2 offline",
      progress: 96,
    },
    {
      label: "Blocked Today",
      value: "8",
      icon: XCircle,
      color: "text-rose-600",
      bgColor: "bg-gradient-to-br from-rose-50 to-pink-50",
      trend: "AI-powered",
    },
  ];

  const performanceMetrics = [
    {
      label: "Detection Accuracy",
      value: "95%",
      color: "text-emerald-600",
      icon: Activity,
    },
    {
      label: "Response Time",
      value: "2.3s",
      color: "text-cyan-600",
      icon: Zap,
    },
    {
      label: "System Uptime",
      value: "99.9%",
      color: "text-emerald-600",
      icon: Shield,
    },
    {
      label: "AI Prevented",
      value: "8 breaches",
      color: "text-rose-600",
      icon: Users,
    },
  ];

  const filteredEvents =
    activeFilter === "all"
      ? accessEvents
      : accessEvents.filter((event) => event.type === activeFilter);

  return (
    <div className="space-y-6">
      {/* Stats Cards - Moved to top since header is removed */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className={`${stat.bgColor} border border-gray-200 rounded-xl p-5 backdrop-blur-sm`}
            >
              <div className="flex items-center justify-between mb-3">
                <div
                  className={`p-2 rounded-lg bg-white/70 border ${stat.color.replace(
                    "text",
                    "border"
                  )} border-opacity-30`}
                >
                  <Icon className={`w-4 h-4 ${stat.color}`} />
                </div>
                <span className="text-xs font-medium text-gray-500">
                  {stat.trend}
                </span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-sm text-gray-600 mt-1">{stat.label}</p>
              {stat.progress && (
                <div className="mt-3">
                  <div className="h-1.5 bg-white/50 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${stat.color.replace(
                        "text",
                        "bg"
                      )} rounded-full`}
                      style={{ width: `${stat.progress}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Main Events Section */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Security Events
            </h2>
            <p className="text-gray-600 text-sm">
              Recent perimeter security alerts
            </p>
          </div>

          <div className="flex gap-3">
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="pl-10 pr-4 py-2.5 bg-white border border-gray-300 text-gray-700 text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent appearance-none"
              >
                <option value="1h">Last hour</option>
                <option value="24h">Last 24h</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
              </select>
            </div>
            <button
              className={`px-4 py-2.5 bg-gradient-to-r from-teal-500 to-cyan-500 text-white text-sm font-medium rounded-lg hover:from-teal-600 hover:to-cyan-600 transition-all flex items-center gap-2 shadow-sm hover:shadow`}
            >
              <Download className="w-4 h-4" />
              Export Report
            </button>
          </div>
        </div>

        {/* Filter Buttons */}
        <div className="flex gap-2 bg-gray-100 p-1 rounded-lg mb-6">
          {[
            "all",
            "unauthorized",
            "loitering",
            "trespassing",
            "authorized",
          ].map((filter) => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeFilter === filter
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {filter === "all"
                ? "All Events"
                : filter.charAt(0).toUpperCase() + filter.slice(1)}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          {filteredEvents.map((event) => (
            <AccessEventCard key={event.id} event={event} />
          ))}
        </div>

        {/* Events Summary */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              {[
                { color: "bg-rose-500", label: "Unauthorized" },
                { color: "bg-amber-500", label: "Loitering" },
                { color: "bg-indigo-500", label: "Trespassing" },
                { color: "bg-emerald-500", label: "Authorized" },
              ].map((item, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
                  <span className="text-sm text-gray-700">{item.label}</span>
                </div>
              ))}
            </div>
            <div className="text-sm text-gray-500">
              Showing {filteredEvents.length} of {accessEvents.length} events
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccessControlPage;
