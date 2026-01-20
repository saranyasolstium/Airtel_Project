import React from "react";
import {
  Car,
  Truck,
  AlertTriangle,
  CheckCircle,
  Clock,
  MapPin,
} from "lucide-react";

const VehicleRow = ({ vehicle }) => {
  const getStatusConfig = (status) => {
    const configs = {
      authorized: {
        icon: CheckCircle,
        color: "text-green-600",
        bgColor: "bg-green-100",
        label: "Authorized",
      },
      blacklisted: {
        icon: AlertTriangle,
        color: "text-red-600",
        bgColor: "bg-red-100",
        label: "Blacklisted",
      },
    };
    return configs[status] || configs.authorized;
  };

  const statusConfig = getStatusConfig(vehicle.status);
  const StatusIcon = statusConfig.icon;
  const VehicleIcon = vehicle.type === "Truck" ? Truck : Car;

  return (
    <tr className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-100 rounded">
            <VehicleIcon className="w-4 h-4 text-gray-600" />
          </div>
          <div>
            <p className="text-gray-900 font-semibold font-mono">
              {vehicle.licensePlate}
            </p>
            <p className="text-gray-500 text-xs">{vehicle.type}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <div
          className={`inline-flex items-center gap-2 px-2 py-1 rounded ${statusConfig.bgColor}`}
        >
          <StatusIcon className={`w-3 h-3 ${statusConfig.color}`} />
          <span className={`text-xs font-medium ${statusConfig.color}`}>
            {statusConfig.label}
          </span>
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2 text-gray-700 text-sm">
          <Clock className="w-4 h-4 text-gray-500" />
          {vehicle.entryTime}
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="text-gray-700 text-sm">{vehicle.exitTime || "-"}</span>
      </td>
      <td className="px-4 py-3">
        <span className="text-gray-700 text-sm font-medium">
          {vehicle.dwellTime}
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2 text-gray-700 text-sm">
          <MapPin className="w-4 h-4 text-gray-500" />
          {vehicle.location}
        </div>
      </td>
      <td className="px-4 py-3">
        <button className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors">
          Details
        </button>
      </td>
    </tr>
  );
};

const VehicleMonitoring = ({ vehicles }) => {
  const authorizedCount = vehicles.filter(
    (v) => v.status === "authorized"
  ).length;
  const blacklistedCount = vehicles.filter(
    (v) => v.status === "blacklisted"
  ).length;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            Vehicle Management (LPR)
          </h2>
          <p className="text-gray-600 text-sm mt-1">
            {authorizedCount} authorized • {blacklistedCount} blocked
          </p>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded transition-colors border border-gray-300">
            Export
          </button>
          <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
            Add Vehicle
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Vehicle
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Entry Time
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Exit Time
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Dwell Time
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Location
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {vehicles.map((vehicle) => (
              <VehicleRow key={vehicle.id} vehicle={vehicle} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default VehicleMonitoring;
