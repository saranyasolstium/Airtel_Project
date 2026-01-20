// src/pages/TrafficFlowPage.jsx
import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  Clock,
  MapPin,
  Filter,
  Download,
  RefreshCw,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import { listTrafficFlowVehicles } from "../api/trafficFlow";

// helpers
const pad2 = (n) => String(n).padStart(2, "0");
const toInputDate = (d) =>
  `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;

const getSeverityConfig = (severity) => {
  const s = (severity || "").toLowerCase();
  const configs = {
    critical: {
      color: "text-rose-600",
      bgColor: "bg-rose-50",
      borderColor: "border-rose-200",
      iconBg: "bg-rose-100",
    },
    warning: {
      color: "text-amber-600",
      bgColor: "bg-amber-50",
      borderColor: "border-amber-200",
      iconBg: "bg-amber-100",
    },
    info: {
      color: "text-blue-600",
      bgColor: "bg-blue-50",
      borderColor: "border-blue-200",
      iconBg: "bg-blue-100",
    },
  };
  return configs[s] || configs.info;
};

// Vehicle type removed (as you asked)
const DwellAlertCard = ({ alert }) => {
  const cfg = getSeverityConfig(alert.severity);

  return (
    <div
      className={`${cfg.bgColor} border ${cfg.borderColor} rounded-xl p-4 transition-all hover:shadow-sm`}
    >
      <div className="flex items-start gap-4">
        <div
          className={`p-3 rounded-lg ${cfg.iconBg} border ${cfg.borderColor}`}
        >
          <AlertTriangle className={`w-5 h-5 ${cfg.color}`} />
        </div>

        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-3">
            <span
              className={`text-xs font-medium px-2 py-1 rounded-full ${cfg.color} bg-white/80 border ${cfg.borderColor}`}
            >
              {(alert.severity || "INFO").toUpperCase()}
            </span>
          </div>

          <h3 className="text-gray-900 font-medium text-sm">
            {alert.plate_text} exceeded dwell time limit
          </h3>

          <div className="flex flex-wrap gap-4 text-xs">
            <div className="flex items-center gap-2 text-gray-600">
              <MapPin className="w-3 h-3" />
              <span>{alert.location_text || "-"}</span>
            </div>

            <div className="flex items-center gap-2 text-gray-600">
              <Clock className="w-3 h-3" />
              <span>{alert.dwell_text || "-"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function TrafficFlowPage() {
  const [selectedDate, setSelectedDate] = useState(toInputDate(new Date()));
  const [limit, setLimit] = useState(10);
  const [page, setPage] = useState(1);

  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const offset = (page - 1) * limit;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const loadAlerts = async () => {
    setLoading(true);
    setErr("");
    try {
      const res = await listTrafficFlowVehicles({
        limit,
        offset,
        date: selectedDate,
        dwell_limit_seconds: 7200, // keep as per your backend default
      });

      setAlerts(res?.data || []);
      setTotal(res?.total || 0);
    } catch (e) {
      console.error(e);
      setAlerts([]);
      setTotal(0);
      setErr("Failed to load alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate, limit, page]);

  return (
    <div className="space-y-6">
      {/* Header card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Dwell Time Alerts
            </h2>
            <p className="text-gray-600 text-sm">
              Vehicles exceeding allowed dwell time limits
            </p>
          </div>

          <div className="flex gap-3 items-center">
            {/* Date Picker */}
            <div className="relative">
              <CalendarDays className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => {
                  setPage(1);
                  setSelectedDate(e.target.value);
                }}
                className="pl-10 pr-4 py-2.5 bg-white border border-gray-300 text-gray-700 text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Rows per page */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={limit}
                onChange={(e) => {
                  setPage(1);
                  setLimit(Number(e.target.value));
                }}
                className="pl-10 pr-4 py-2.5 bg-white border border-gray-300 text-gray-700 text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none"
              >
                <option value={5}>5 / page</option>
                <option value={10}>10 / page</option>
                <option value={20}>20 / page</option>
              </select>
            </div>

            <button className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors">
              <Download className="w-4 h-4" />
              Export Report
            </button>
          </div>
        </div>

        {/* Content */}
        {loading && (
          <div className="text-sm text-gray-500 py-8">Loading alerts...</div>
        )}

        {!loading && err && (
          <div className="border border-rose-200 bg-rose-50 rounded-xl p-4 text-sm text-rose-700">
            {err}
          </div>
        )}

        {!loading && !err && alerts.length === 0 && (
          <div className="border border-dashed border-gray-300 rounded-xl p-10 text-center">
            <AlertTriangle className="w-8 h-8 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600 text-sm font-medium">
              No dwell time alerts for selected date
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Try selecting a different date
            </p>
          </div>
        )}

        {!loading && !err && alerts.length > 0 && (
          <div className="space-y-3">
            {alerts.map((a) => (
              <DwellAlertCard key={a.id} alert={a} />
            ))}
          </div>
        )}

        {/* Footer: pagination + refresh */}
        <div className="mt-6 pt-6 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Showing <span className="font-medium">{alerts.length}</span> of{" "}
            <span className="font-medium">{total}</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadAlerts}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>

            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50 flex items-center gap-1"
              >
                <ChevronLeft className="w-4 h-4" />
                Prev
              </button>

              <span className="text-sm text-gray-600">
                {page} / {totalPages}
              </span>

              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50 flex items-center gap-1"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// // TrafficFlowPage.jsx - FULL WIDTH VERSION
// import React, { useState } from "react";
// import {
//   Car,
//   Clock,
//   AlertTriangle,
//   MapPin,
//   TrendingUp,
//   BarChart3,
//   Filter,
//   Download,
//   Settings,
//   Eye,
//   EyeOff,
//   Play,
//   Pause,
//   RefreshCw,
//   Zap,
//   Shield,
//   Activity,
//   Maximize2,
//   Minimize2,
// } from "lucide-react";

// // Traffic Flow Dwell Time Alert Component
// const DwellAlertCard = ({ alert }) => {
//   const getSeverityConfig = (severity) => {
//     const configs = {
//       critical: {
//         color: "text-rose-600",
//         bgColor: "bg-rose-50",
//         borderColor: "border-rose-200",
//         iconBg: "bg-gradient-to-r from-rose-100 to-pink-100",
//       },
//       warning: {
//         color: "text-amber-600",
//         bgColor: "bg-amber-50",
//         borderColor: "border-amber-200",
//         iconBg: "bg-gradient-to-r from-amber-100 to-orange-100",
//       },
//       info: {
//         color: "text-blue-600",
//         bgColor: "bg-blue-50",
//         borderColor: "border-blue-200",
//         iconBg: "bg-gradient-to-r from-blue-100 to-cyan-100",
//       },
//     };
//     return configs[severity] || configs.info;
//   };

//   const severityConfig = getSeverityConfig(alert.severity);

//   return (
//     <div
//       className={`${severityConfig.bgColor} border ${severityConfig.borderColor} rounded-xl p-4 transition-all hover:shadow-md`}
//     >
//       <div className="flex items-start justify-between">
//         <div className="flex items-start gap-4">
//           <div
//             className={`p-3 rounded-lg ${severityConfig.iconBg} border ${severityConfig.borderColor}`}
//           >
//             <AlertTriangle className={`w-5 h-5 ${severityConfig.color}`} />
//           </div>
//           <div className="space-y-2">
//             <div className="flex items-center gap-3">
//               <span
//                 className={`text-xs font-semibold ${severityConfig.color} bg-white px-2 py-1 rounded-full border ${severityConfig.borderColor}`}
//               >
//                 {alert.vehicleType}
//               </span>
//               <span
//                 className={`text-xs font-medium px-2 py-1 rounded-full ${severityConfig.color} bg-white/70 border ${severityConfig.borderColor}`}
//               >
//                 {alert.severity.toUpperCase()}
//               </span>
//             </div>
//             <h3 className="text-gray-900 font-medium text-sm">
//               {alert.plateNumber} exceeded dwell time limit
//             </h3>
//             <div className="flex flex-wrap gap-4 text-xs">
//               <div className="flex items-center gap-2 text-gray-600">
//                 <MapPin className="w-3 h-3" />
//                 <span>{alert.zone}</span>
//               </div>
//               <div className="flex items-center gap-2 text-gray-600">
//                 <Clock className="w-3 h-3" />
//                 <span>
//                   {alert.dwellTime} / Limit: {alert.timeLimit}
//                 </span>
//               </div>
//               <div className="flex items-center gap-2 text-gray-600">
//                 <Car className="w-3 h-3" />
//                 <span>{alert.vehicleType}</span>
//               </div>
//             </div>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// // Zone Statistics Component
// const ZoneStats = ({ zone, vehicleCount, avgDwellTime, alerts, capacity }) => {
//   const occupancy = Math.round((vehicleCount / capacity) * 100);

//   return (
//     <div className="bg-white border border-gray-200 rounded-xl p-4">
//       <div className="flex items-center justify-between mb-3">
//         <div className="flex items-center gap-3">
//           <div className="p-2 bg-gray-100 rounded-lg">
//             <MapPin className="w-4 h-4 text-gray-600" />
//           </div>
//           <div>
//             <h4 className="font-medium text-gray-900">{zone}</h4>
//             <p className="text-xs text-gray-500">{vehicleCount} vehicles</p>
//           </div>
//         </div>
//         <div className="text-right">
//           <span className="text-sm font-semibold text-gray-900">
//             {avgDwellTime}
//           </span>
//           <p className="text-xs text-gray-500">Avg dwell</p>
//         </div>
//       </div>

//       <div className="space-y-2">
//         <div className="flex justify-between text-xs">
//           <span className="text-gray-600">Occupancy</span>
//           <span className="font-medium text-gray-900">{occupancy}%</span>
//         </div>
//         <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
//           <div
//             className={`h-full ${
//               occupancy > 80
//                 ? "bg-rose-500"
//                 : occupancy > 60
//                   ? "bg-amber-500"
//                   : "bg-emerald-500"
//             } rounded-full`}
//             style={{ width: `${occupancy}%` }}
//           ></div>
//         </div>
//         <div className="flex justify-between text-xs">
//           <span className="text-gray-600">Alerts</span>
//           <span className="font-medium text-rose-600">{alerts}</span>
//         </div>
//       </div>
//     </div>
//   );
// };

// const TrafficFlowPage = () => {
//   const [timeRange, setTimeRange] = useState("24h");
//   const [viewMode, setViewMode] = useState("grid");
//   const [isLive, setIsLive] = useState(true);

//   // Mock data
//   const dwellAlerts = [
//     {
//       id: 1,
//       plateNumber: "ABC-1234",
//       vehicleType: "Delivery Truck",
//       zone: "Loading Dock A",
//       dwellTime: "45m 23s",
//       timeLimit: "30m",
//       severity: "critical",
//       timestamp: "14:23:15",
//     },
//     {
//       id: 2,
//       plateNumber: "XYZ-5678",
//       vehicleType: "SUV",
//       zone: "Visitor Parking",
//       dwellTime: "2h 15m",
//       timeLimit: "1h",
//       severity: "warning",
//       timestamp: "13:45:30",
//     },
//     {
//       id: 3,
//       plateNumber: "DEF-9012",
//       vehicleType: "Sedan",
//       zone: "Employee Parking B",
//       dwellTime: "8h 30m",
//       timeLimit: "8h",
//       severity: "info",
//       timestamp: "12:15:22",
//     },
//     {
//       id: 4,
//       plateNumber: "GHI-3456",
//       vehicleType: "Van",
//       zone: "Loading Dock B",
//       dwellTime: "52m 10s",
//       timeLimit: "30m",
//       severity: "critical",
//       timestamp: "11:30:45",
//     },
//   ];

//   const zones = [
//     {
//       name: "Main Parking",
//       vehicleCount: 142,
//       avgDwellTime: "2h 15m",
//       alerts: 3,
//       capacity: 200,
//     },
//     {
//       name: "Loading Docks",
//       vehicleCount: 8,
//       avgDwellTime: "35m",
//       alerts: 2,
//       capacity: 12,
//     },
//     {
//       name: "Visitor Parking",
//       vehicleCount: 24,
//       avgDwellTime: "1h 45m",
//       alerts: 1,
//       capacity: 30,
//     },
//     {
//       name: "Employee Parking",
//       vehicleCount: 189,
//       avgDwellTime: "8h",
//       alerts: 0,
//       capacity: 200,
//     },
//   ];

//   const overallStats = [
//     {
//       label: "Total Vehicles Tracked",
//       value: "1,245",
//       change: "+12%",
//       icon: Car,
//       color: "text-blue-600",
//     },
//     {
//       label: "Dwell Time Alerts",
//       value: "23",
//       change: "-5%",
//       icon: AlertTriangle,
//       color: "text-rose-600",
//     },
//     {
//       label: "Avg Response Time",
//       value: "3.2s",
//       change: "-0.5s",
//       icon: Zap,
//       color: "text-emerald-600",
//     },
//     {
//       label: "System Accuracy",
//       value: "97.5%",
//       change: "+1.2%",
//       icon: Shield,
//       color: "text-indigo-600",
//     },
//   ];

//   return (
//     <div className="space-y-6">
//       {/* Overall Stats */}
//       <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
//         {overallStats.map((stat, index) => {
//           const Icon = stat.icon;
//           return (
//             <div
//               key={index}
//               className="bg-white border border-gray-200 rounded-xl p-5"
//             >
//               <div className="flex items-center justify-between mb-3">
//                 <div
//                   className={`p-2 rounded-lg ${stat.color.replace(
//                     "text",
//                     "bg",
//                   )} bg-opacity-10`}
//                 >
//                   <Icon className={`w-5 h-5 ${stat.color}`} />
//                 </div>
//                 <span
//                   className={`text-xs font-medium ${
//                     stat.change.startsWith("+")
//                       ? "text-emerald-600"
//                       : stat.change.startsWith("-")
//                         ? "text-rose-600"
//                         : "text-gray-600"
//                   }`}
//                 >
//                   {stat.change}
//                 </span>
//               </div>
//               <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
//               <p className="text-sm text-gray-600 mt-1">{stat.label}</p>
//             </div>
//           );
//         })}
//       </div>

//       {/* Main Content - Single Column (Full Width) */}
//       <div className="space-y-6">
//         {/* Dwell Alerts Section - Full Width */}
//         <div className="bg-white rounded-xl border border-gray-200 p-6">
//           <div className="flex items-center justify-between mb-6">
//             <div>
//               <h2 className="text-lg font-semibold text-gray-900">
//                 Dwell Time Alerts
//               </h2>
//               <p className="text-gray-600 text-sm">
//                 Vehicles exceeding allowed dwell time limits
//               </p>
//             </div>
//             <div className="flex gap-3">
//               <div className="relative">
//                 <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
//                 <select
//                   value={timeRange}
//                   onChange={(e) => setTimeRange(e.target.value)}
//                   className="pl-10 pr-4 py-2.5 bg-white border border-gray-300 text-gray-700 text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
//                 >
//                   <option value="1h">Last hour</option>
//                   <option value="24h">Last 24h</option>
//                   <option value="7d">Last 7 days</option>
//                   <option value="30d">Last 30 days</option>
//                 </select>
//               </div>
//               <button className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors">
//                 <Download className="w-4 h-4" />
//                 Export Report
//               </button>
//             </div>
//           </div>

//           {/* Alerts List - Full Width */}
//           <div className="space-y-3">
//             {dwellAlerts.map((alert) => (
//               <DwellAlertCard key={alert.id} alert={alert} />
//             ))}
//           </div>

//           {/* Alerts Summary */}
//           <div className="mt-6 pt-6 border-t border-gray-200">
//             <div className="flex items-center justify-between">
//               <div className="text-sm text-gray-600">
//                 Showing {dwellAlerts.length} active alerts
//               </div>
//               <button className="flex items-center gap-2 px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700">
//                 <RefreshCw className="w-4 h-4" />
//                 Refresh Data
//               </button>
//             </div>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default TrafficFlowPage;
