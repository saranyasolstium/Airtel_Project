import React, { useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Info,
  Eye,
  Trash2,
  CheckCircle,
  Filter,
} from "lucide-react";
import { alertsData } from "../data/dummyData";

const AlertItem = ({ alert, onResolve, onDelete }) => {
  const getAlertConfig = (type) => {
    const configs = {
      critical: {
        icon: AlertCircle,
        bgColor: "bg-red-50",
        borderColor: "border-red-200",
        iconColor: "text-red-600",
        badgeColor: "bg-red-600",
      },
      warning: {
        icon: AlertTriangle,
        bgColor: "bg-amber-50",
        borderColor: "border-amber-200",
        iconColor: "text-amber-600",
        badgeColor: "bg-amber-600",
      },
      info: {
        icon: Info,
        bgColor: "bg-blue-50",
        borderColor: "border-blue-200",
        iconColor: "text-blue-600",
        badgeColor: "bg-blue-600",
      },
    };
    return configs[type] || configs.info;
  };

  const config = getAlertConfig(alert.type);
  const Icon = config.icon;

  const getStatusBadge = (status) => {
    const badges = {
      active: { label: "Active", color: "bg-red-600" },
      investigating: { label: "Investigating", color: "bg-amber-600" },
      resolved: { label: "Resolved", color: "bg-green-600" },
    };
    return badges[status] || badges.active;
  };

  const statusBadge = getStatusBadge(alert.status);

  return (
    <div
      className={`${config.bgColor} border ${config.borderColor} rounded-lg p-4 hover:shadow-md transition-all`}
    >
      <div className="flex items-start gap-4">
        <div
          className={`p-3 rounded-lg ${config.iconColor} bg-white flex-shrink-0`}
        >
          <Icon className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-semibold text-gray-500 uppercase">
              {alert.category}
            </span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full text-white ${statusBadge.color}`}
            >
              {statusBadge.label}
            </span>
          </div>
          <p className="text-gray-800 font-medium mb-3">{alert.message}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-gray-500 mb-3">
            <div className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              <span>{alert.camera}</span>
            </div>
            <div>{alert.location}</div>
            <div>{alert.timestamp}</div>
            <div>ID: {alert.id}</div>
          </div>
          <div className="flex gap-2">
            <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
              View Details
            </button>
            <button
              onClick={() => onResolve(alert.id)}
              className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors flex items-center gap-1"
            >
              <CheckCircle className="w-4 h-4" />
              Resolve
            </button>
            <button
              onClick={() => onDelete(alert.id)}
              className="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-800 text-sm rounded transition-colors flex items-center gap-1"
            >
              <Trash2 className="w-4 h-4" />
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const AlertsPage = () => {
  const [alerts, setAlerts] = useState(alertsData);
  const [filterType, setFilterType] = useState("all");
  const [sortBy, setSortBy] = useState("latest");

  const handleResolve = (alertId) => {
    setAlerts(
      alerts.map((a) => (a.id === alertId ? { ...a, status: "resolved" } : a))
    );
  };

  const handleDelete = (alertId) => {
    setAlerts(alerts.filter((a) => a.id !== alertId));
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (filterType === "all") return true;
    if (filterType === "active") return alert.status === "active";
    if (filterType === "critical") return alert.type === "critical";
    return true;
  });

  const sortedAlerts = [...filteredAlerts].sort((a, b) => {
    if (sortBy === "latest")
      return new Date(b.timestamp) - new Date(a.timestamp);
    if (sortBy === "severity") {
      const severityOrder = { critical: 0, warning: 1, info: 2 };
      return severityOrder[a.type] - severityOrder[b.type];
    }
    return 0;
  });

  const stats = {
    total: alerts.length,
    active: alerts.filter((a) => a.status === "active").length,
    critical: alerts.filter((a) => a.type === "critical").length,
    resolved: alerts.filter((a) => a.status === "resolved").length,
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <p className="text-gray-500 text-sm">Total Alerts</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{stats.total}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <p className="text-gray-500 text-sm">Active</p>
          <p className="text-3xl font-bold text-red-600 mt-2">{stats.active}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <p className="text-gray-500 text-sm">Critical</p>
          <p className="text-3xl font-bold text-red-700 mt-2">
            {stats.critical}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <p className="text-gray-500 text-sm">Resolved</p>
          <p className="text-3xl font-bold text-green-600 mt-2">
            {stats.resolved}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-800">Alert Management</h2>
          <div className="flex gap-3">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-2 bg-white border border-gray-300 rounded text-gray-800 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="all">All Alerts</option>
                <option value="active">Active Only</option>
                <option value="critical">Critical Only</option>
              </select>
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 bg-white border border-gray-300 rounded text-gray-800 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="latest">Latest First</option>
              <option value="severity">By Severity</option>
            </select>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors">
              Export Report
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {sortedAlerts.length > 0 ? (
            sortedAlerts.map((alert) => (
              <AlertItem
                key={alert.id}
                alert={alert}
                onResolve={handleResolve}
                onDelete={handleDelete}
              />
            ))
          ) : (
            <div className="text-center py-12">
              <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
              <p className="text-gray-800 font-medium">All Clear</p>
              <p className="text-gray-500 text-sm">
                No alerts matching current filters
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AlertsPage;

// import React, { useState } from "react";
// import {
//   AlertCircle,
//   AlertTriangle,
//   Info,
//   Eye,
//   Trash2,
//   CheckCircle,
//   Filter,
// } from "lucide-react";
// import { alertsData } from "../data/dummyData";

// const AlertItem = ({ alert, onResolve, onDelete }) => {
//   const getAlertConfig = (type) => {
//     const configs = {
//       critical: {
//         icon: AlertCircle,
//         bgColor: "bg-red-500/10",
//         borderColor: "border-red-500/30",
//         iconColor: "text-red-500",
//         badgeColor: "bg-red-500",
//       },
//       warning: {
//         icon: AlertTriangle,
//         bgColor: "bg-amber-500/10",
//         borderColor: "border-amber-500/30",
//         iconColor: "text-amber-500",
//         badgeColor: "bg-amber-500",
//       },
//       info: {
//         icon: Info,
//         bgColor: "bg-blue-500/10",
//         borderColor: "border-blue-500/30",
//         iconColor: "text-blue-500",
//         badgeColor: "bg-blue-500",
//       },
//     };
//     return configs[type] || configs.info;
//   };

//   const config = getAlertConfig(alert.type);
//   const Icon = config.icon;

//   const getStatusBadge = (status) => {
//     const badges = {
//       active: { label: "Active", color: "bg-red-500" },
//       investigating: { label: "Investigating", color: "bg-amber-500" },
//       resolved: { label: "Resolved", color: "bg-green-500" },
//     };
//     return badges[status] || badges.active;
//   };

//   const statusBadge = getStatusBadge(alert.status);

//   return (
//     <div
//       className={`${config.bgColor} border ${config.borderColor} rounded-lg p-4 hover:shadow-lg transition-all`}
//     >
//       <div className="flex items-start gap-4">
//         <div
//           className={`p-3 rounded-lg ${config.iconColor} bg-slate-800/50 flex-shrink-0`}
//         >
//           <Icon className="w-6 h-6" />
//         </div>
//         <div className="flex-1 min-w-0">
//           <div className="flex items-center gap-2 mb-2">
//             <span className="text-sm font-semibold text-slate-400 uppercase">
//               {alert.category}
//             </span>
//             <span
//               className={`text-xs px-2 py-0.5 rounded-full text-white ${statusBadge.color}`}
//             >
//               {statusBadge.label}
//             </span>
//           </div>
//           <p className="text-white font-medium mb-3">{alert.message}</p>
//           <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-slate-400 mb-3">
//             <div className="flex items-center gap-1">
//               <Eye className="w-3 h-3" />
//               <span>{alert.camera}</span>
//             </div>
//             <div>{alert.location}</div>
//             <div>{alert.timestamp}</div>
//             <div>ID: {alert.id}</div>
//           </div>
//           <div className="flex gap-2">
//             <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
//               View Details
//             </button>
//             <button
//               onClick={() => onResolve(alert.id)}
//               className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors flex items-center gap-1"
//             >
//               <CheckCircle className="w-4 h-4" />
//               Resolve
//             </button>
//             <button
//               onClick={() => onDelete(alert.id)}
//               className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded transition-colors flex items-center gap-1"
//             >
//               <Trash2 className="w-4 h-4" />
//               Dismiss
//             </button>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// const AlertsPage = () => {
//   const [alerts, setAlerts] = useState(alertsData);
//   const [filterType, setFilterType] = useState("all");
//   const [sortBy, setSortBy] = useState("latest");

//   const handleResolve = (alertId) => {
//     setAlerts(
//       alerts.map((a) => (a.id === alertId ? { ...a, status: "resolved" } : a))
//     );
//   };

//   const handleDelete = (alertId) => {
//     setAlerts(alerts.filter((a) => a.id !== alertId));
//   };

//   const filteredAlerts = alerts.filter((alert) => {
//     if (filterType === "all") return true;
//     if (filterType === "active") return alert.status === "active";
//     if (filterType === "critical") return alert.type === "critical";
//     return true;
//   });

//   const sortedAlerts = [...filteredAlerts].sort((a, b) => {
//     if (sortBy === "latest")
//       return new Date(b.timestamp) - new Date(a.timestamp);
//     if (sortBy === "severity") {
//       const severityOrder = { critical: 0, warning: 1, info: 2 };
//       return severityOrder[a.type] - severityOrder[b.type];
//     }
//     return 0;
//   });

//   const stats = {
//     total: alerts.length,
//     active: alerts.filter((a) => a.status === "active").length,
//     critical: alerts.filter((a) => a.type === "critical").length,
//     resolved: alerts.filter((a) => a.status === "resolved").length,
//   };

//   return (
//     <div className="space-y-6">
//       <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
//         <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
//           <p className="text-slate-400 text-sm">Total Alerts</p>
//           <p className="text-3xl font-bold text-white mt-2">{stats.total}</p>
//         </div>
//         <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
//           <p className="text-slate-400 text-sm">Active</p>
//           <p className="text-3xl font-bold text-red-500 mt-2">{stats.active}</p>
//         </div>
//         <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
//           <p className="text-slate-400 text-sm">Critical</p>
//           <p className="text-3xl font-bold text-red-600 mt-2">
//             {stats.critical}
//           </p>
//         </div>
//         <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
//           <p className="text-slate-400 text-sm">Resolved</p>
//           <p className="text-3xl font-bold text-green-500 mt-2">
//             {stats.resolved}
//           </p>
//         </div>
//       </div>

//       <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
//         <div className="flex items-center justify-between mb-6">
//           <h2 className="text-xl font-bold text-white">Alert Management</h2>
//           <div className="flex gap-3">
//             <div className="flex items-center gap-2">
//               <Filter className="w-4 h-4 text-slate-400" />
//               <select
//                 value={filterType}
//                 onChange={(e) => setFilterType(e.target.value)}
//                 className="px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
//               >
//                 <option value="all">All Alerts</option>
//                 <option value="active">Active Only</option>
//                 <option value="critical">Critical Only</option>
//               </select>
//             </div>
//             <select
//               value={sortBy}
//               onChange={(e) => setSortBy(e.target.value)}
//               className="px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
//             >
//               <option value="latest">Latest First</option>
//               <option value="severity">By Severity</option>
//             </select>
//             <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors">
//               Export Report
//             </button>
//           </div>
//         </div>

//         <div className="space-y-3">
//           {sortedAlerts.length > 0 ? (
//             sortedAlerts.map((alert) => (
//               <AlertItem
//                 key={alert.id}
//                 alert={alert}
//                 onResolve={handleResolve}
//                 onDelete={handleDelete}
//               />
//             ))
//           ) : (
//             <div className="text-center py-12">
//               <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
//               <p className="text-white font-medium">All Clear</p>
//               <p className="text-slate-400 text-sm">
//                 No alerts matching current filters
//               </p>
//             </div>
//           )}
//         </div>
//       </div>
//     </div>
//   );
// };

// export default AlertsPage;
