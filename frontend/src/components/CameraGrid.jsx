import React from "react";
import { Camera, Circle, Maximize2, Settings } from "lucide-react";

const CameraCard = ({ camera }) => {
  const getStatusConfig = (status) => {
    const configs = {
      online: {
        dot: "text-emerald-500",
        text: "Online",
        pulse: true,
        pillBg: "bg-emerald-100",
      },
      warning: {
        dot: "text-amber-500",
        text: "Warning",
        pulse: false,
        pillBg: "bg-amber-100",
      },
      offline: {
        dot: "text-rose-500",
        text: "Offline",
        pulse: false,
        pillBg: "bg-rose-100",
      },
    };
    return configs[status] || configs.offline;
  };

  const statusConfig = getStatusConfig(camera.status);

  const healthColor =
    camera.health >= 95
      ? "text-emerald-600"
      : camera.health >= 80
      ? "text-amber-600"
      : "text-rose-600";

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:border-blue-400 transition-all group shadow-sm hover:shadow">
      <div className="relative aspect-video bg-gray-50 flex items-center justify-center">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-gray-100" />

        <div className="relative z-10 flex flex-col items-center justify-center">
          <Camera className="w-12 h-12 text-gray-400 mb-2" />
          <span className="text-gray-500 text-sm">Live Feed</span>
        </div>

        {/* Status Pill */}
        <div className="absolute top-3 left-3 flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 px-2 py-1 rounded ${statusConfig.pillBg} border border-gray-300`}
          >
            <Circle
              className={`w-2 h-2 ${statusConfig.dot} ${
                statusConfig.pulse ? "animate-pulse" : ""
              }`}
              fill="currentColor"
            />
            <span className="text-xs font-medium text-gray-700">
              {statusConfig.text}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="absolute top-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="p-1.5 bg-white hover:bg-blue-50 border border-gray-300 rounded shadow-sm">
            <Maximize2 className="w-4 h-4 text-gray-700" />
          </button>
          <button className="p-1.5 bg-white hover:bg-blue-50 border border-gray-300 rounded shadow-sm">
            <Settings className="w-4 h-4 text-gray-700" />
          </button>
        </div>

        {/* Bottom info */}
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
          <div className="px-2 py-1 bg-white/90 border border-gray-300 rounded shadow-sm">
            <span className="text-xs text-gray-700 font-mono">14:23:45</span>
          </div>
          <div className="px-2 py-1 bg-white/90 border border-gray-300 rounded shadow-sm">
            <span className={`text-xs font-medium ${healthColor}`}>
              {camera.health}%
            </span>
          </div>
        </div>
      </div>

      <div className="p-3">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-gray-900 font-semibold text-sm">{camera.id}</h3>
            <p className="text-gray-600 text-xs mt-0.5">{camera.name}</p>
          </div>
          <span className="text-xs text-gray-500">{camera.location}</span>
        </div>
      </div>
    </div>
  );
};

const CameraGrid = ({ cameras }) => {
  const onlineCameras = cameras.filter((c) => c.status === "online").length;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Live Video Wall</h2>
          <p className="text-gray-600 text-sm mt-1">
            {onlineCameras} of {cameras.length} cameras online
          </p>
        </div>

        <div className="flex gap-2">
          <button className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded transition-colors border border-gray-300">
            Grid Layout
          </button>
          <button className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded transition-colors border border-gray-300">
            Full Screen
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {cameras.map((camera) => (
          <CameraCard key={camera.id} camera={camera} />
        ))}
      </div>
    </div>
  );
};

export default CameraGrid;
