import React from "react";
import {
  AlertCircle,
  AlertTriangle,
  Info,
  Eye,
  CheckCircle,
} from "lucide-react";

const AlertItem = ({ alert }) => {
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
      className={`${config.bgColor} border ${config.borderColor} rounded-lg p-4 hover:shadow transition-all`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`p-2 rounded-lg ${config.iconColor} bg-white border border-gray-200`}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-gray-500 uppercase">
              {alert.category}
            </span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full text-white ${statusBadge.color}`}
            >
              {statusBadge.label}
            </span>
          </div>
          <p className="text-gray-900 font-medium mb-2">{alert.message}</p>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              {alert.camera}
            </span>
            <span>{alert.location}</span>
            <span>{alert.timestamp}</span>
          </div>
        </div>
        <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
          View
        </button>
      </div>
    </div>
  );
};

const AlertsPanel = ({ alerts }) => {
  const activeAlerts = alerts.filter((a) => a.status === "active");
  const criticalCount = alerts.filter(
    (a) => a.type === "critical" && a.status === "active"
  ).length;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Real-Time Alerts</h2>
          <p className="text-gray-600 text-sm mt-1">
            {activeAlerts.length} active alerts • {criticalCount} critical
          </p>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded transition-colors border border-gray-300">
            Filter
          </button>
          <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
            View All
          </button>
        </div>
      </div>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alerts.map((alert) => (
          <AlertItem key={alert.id} alert={alert} />
        ))}
      </div>
    </div>
  );
};

export default AlertsPanel;

// import React from "react";
// import {
//   AlertCircle,
//   AlertTriangle,
//   Info,
//   Eye,
//   CheckCircle,
// } from "lucide-react";

// const AlertItem = ({ alert }) => {
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
//       <div className="flex items-start gap-3">
//         <div className={`p-2 rounded-lg ${config.iconColor} bg-slate-800/50`}>
//           <Icon className="w-5 h-5" />
//         </div>
//         <div className="flex-1 min-w-0">
//           <div className="flex items-center gap-2 mb-1">
//             <span className="text-xs font-semibold text-slate-400 uppercase">
//               {alert.category}
//             </span>
//             <span
//               className={`text-xs px-2 py-0.5 rounded-full text-white ${statusBadge.color}`}
//             >
//               {statusBadge.label}
//             </span>
//           </div>
//           <p className="text-white font-medium mb-2">{alert.message}</p>
//           <div className="flex items-center gap-4 text-xs text-slate-400">
//             <span className="flex items-center gap-1">
//               <Eye className="w-3 h-3" />
//               {alert.camera}
//             </span>
//             <span>{alert.location}</span>
//             <span>{alert.timestamp}</span>
//           </div>
//         </div>
//         <button className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded transition-colors">
//           View
//         </button>
//       </div>
//     </div>
//   );
// };

// const AlertsPanel = ({ alerts }) => {
//   const activeAlerts = alerts.filter((a) => a.status === "active");
//   const criticalCount = alerts.filter(
//     (a) => a.type === "critical" && a.status === "active"
//   ).length;

//   return (
//     <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
//       <div className="flex items-center justify-between mb-4">
//         <div>
//           <h2 className="text-xl font-bold text-white">Real-Time Alerts</h2>
//           <p className="text-slate-400 text-sm mt-1">
//             {activeAlerts.length} active alerts • {criticalCount} critical
//           </p>
//         </div>
//         <div className="flex gap-2">
//           <button className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded transition-colors">
//             Filter
//           </button>
//           <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
//             View All
//           </button>
//         </div>
//       </div>
//       <div className="space-y-3 max-h-96 overflow-y-auto">
//         {alerts.map((alert) => (
//           <AlertItem key={alert.id} alert={alert} />
//         ))}
//       </div>
//     </div>
//   );
// };

// export default AlertsPanel;
