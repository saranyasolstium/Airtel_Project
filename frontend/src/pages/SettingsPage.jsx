import React, { useState } from "react";
import {
  Settings,
  Bell,
  Lock,
  Database,
  Palette,
  Save,
  ToggleRight,
  ToggleLeft,
} from "lucide-react";

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    emailNotifications: true,
    pushNotifications: true,
    smsAlerts: false,
    darkMode: true,
    autoRefresh: true,
    soundAlerts: true,
    securityLock: true,
    twoFactorAuth: true,
    backupFrequency: "daily",
    retentionPeriod: "90days",
    alertSensitivity: "medium",
    timezone: "UTC",
  });

  const [savedMessage, setSavedMessage] = useState(false);

  const handleToggle = (key) => {
    setSettings((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleSelectChange = (key, value) => {
    setSettings((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSave = () => {
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 3000);
  };

  const SettingToggle = ({ label, value, onChange }) => {
    return (
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
        <span className="text-gray-700">{label}</span>
        <button onClick={onChange} className="focus:outline-none">
          {value ? (
            <ToggleRight className="w-6 h-6 text-green-600" />
          ) : (
            <ToggleLeft className="w-6 h-6 text-gray-400" />
          )}
        </button>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">
            Settings & Configuration
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            Manage system preferences and security settings
          </p>
        </div>
        {savedMessage && (
          <div className="flex items-center gap-2 px-4 py-2 bg-green-100 rounded border border-green-200">
            <span className="text-green-700 text-sm font-medium">
              Settings saved successfully
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5 text-blue-600" />
            Notifications
          </h3>
          <div className="space-y-3">
            <SettingToggle
              label="Email Notifications"
              value={settings.emailNotifications}
              onChange={() => handleToggle("emailNotifications")}
            />
            <SettingToggle
              label="Push Notifications"
              value={settings.pushNotifications}
              onChange={() => handleToggle("pushNotifications")}
            />
            <SettingToggle
              label="SMS Alerts"
              value={settings.smsAlerts}
              onChange={() => handleToggle("smsAlerts")}
            />
            <SettingToggle
              label="Sound Alerts"
              value={settings.soundAlerts}
              onChange={() => handleToggle("soundAlerts")}
            />
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <label className="block text-gray-700 text-sm mb-2">
                Alert Sensitivity
              </label>
              <select
                value={settings.alertSensitivity}
                onChange={(e) =>
                  handleSelectChange("alertSensitivity", e.target.value)
                }
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-gray-800 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5 text-red-600" />
            Security
          </h3>
          <div className="space-y-3">
            <SettingToggle
              label="Security Lock"
              value={settings.securityLock}
              onChange={() => handleToggle("securityLock")}
            />
            <SettingToggle
              label="Two-Factor Authentication"
              value={settings.twoFactorAuth}
              onChange={() => handleToggle("twoFactorAuth")}
            />
            <button className="w-full p-3 bg-gray-50 hover:bg-gray-100 rounded text-gray-700 text-sm transition-colors">
              Change Password
            </button>
            <button className="w-full p-3 bg-gray-50 hover:bg-gray-100 rounded text-gray-700 text-sm transition-colors">
              Manage API Keys
            </button>
            <button className="w-full p-3 bg-gray-50 hover:bg-gray-100 rounded text-gray-700 text-sm transition-colors">
              View Login History
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-600" />
            Data & Storage
          </h3>
          <div className="space-y-3">
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <label className="block text-gray-700 text-sm mb-2">
                Backup Frequency
              </label>
              <select
                value={settings.backupFrequency}
                onChange={(e) =>
                  handleSelectChange("backupFrequency", e.target.value)
                }
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-gray-800 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="hourly">Hourly</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <label className="block text-gray-700 text-sm mb-2">
                Data Retention Period
              </label>
              <select
                value={settings.retentionPeriod}
                onChange={(e) =>
                  handleSelectChange("retentionPeriod", e.target.value)
                }
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-gray-800 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="30days">30 Days</option>
                <option value="60days">60 Days</option>
                <option value="90days">90 Days</option>
                <option value="1year">1 Year</option>
              </select>
            </div>
            <button className="w-full p-3 bg-gray-50 hover:bg-gray-100 rounded text-gray-700 text-sm transition-colors">
              Run Backup Now
            </button>
            <button className="w-full p-3 bg-gray-50 hover:bg-gray-100 rounded text-gray-700 text-sm transition-colors">
              Database Status
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Palette className="w-5 h-5 text-purple-600" />
            Preferences
          </h3>
          <div className="space-y-3">
            <SettingToggle
              label="Dark Mode"
              value={settings.darkMode}
              onChange={() => handleToggle("darkMode")}
            />
            <SettingToggle
              label="Auto Refresh"
              value={settings.autoRefresh}
              onChange={() => handleToggle("autoRefresh")}
            />
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <label className="block text-gray-700 text-sm mb-2">
                Timezone
              </label>
              <select
                value={settings.timezone}
                onChange={(e) => handleSelectChange("timezone", e.target.value)}
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-gray-800 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="UTC">UTC</option>
                <option value="EST">Eastern (EST)</option>
                <option value="CST">Central (CST)</option>
                <option value="PST">Pacific (PST)</option>
              </select>
            </div>
            <button className="w-full p-3 bg-gray-50 hover:bg-gray-100 rounded text-gray-700 text-sm transition-colors">
              Reset to Defaults
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-bold text-gray-800 mb-4">
          System Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-gray-500 text-sm">Version</p>
            <p className="text-gray-800 font-semibold">2.0.1</p>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-gray-500 text-sm">Last Update</p>
            <p className="text-gray-800 font-semibold">2025-12-29 14:00</p>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-gray-500 text-sm">Server Status</p>
            <p className="text-green-600 font-semibold">Online</p>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-gray-500 text-sm">Database</p>
            <p className="text-gray-800 font-semibold">Connected</p>
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-3">
        <button className="px-6 py-2.5 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded transition-colors">
          Cancel
        </button>
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
        >
          <Save className="w-4 h-4" />
          Save Settings
        </button>
      </div>
    </div>
  );
};

export default SettingsPage;
// import React, { useState } from "react";
// import {
//   Settings,
//   Bell,
//   Lock,
//   Database,
//   Palette,
//   Save,
//   ToggleRight,
//   ToggleLeft,
// } from "lucide-react";

// const SettingsPage = () => {
//   const [settings, setSettings] = useState({
//     emailNotifications: true,
//     pushNotifications: true,
//     smsAlerts: false,
//     darkMode: true,
//     autoRefresh: true,
//     soundAlerts: true,
//     securityLock: true,
//     twoFactorAuth: true,
//     backupFrequency: "daily",
//     retentionPeriod: "90days",
//     alertSensitivity: "medium",
//     timezone: "UTC",
//   });

//   const [savedMessage, setSavedMessage] = useState(false);

//   const handleToggle = (key) => {
//     setSettings((prev) => ({
//       ...prev,
//       [key]: !prev[key],
//     }));
//   };

//   const handleSelectChange = (key, value) => {
//     setSettings((prev) => ({
//       ...prev,
//       [key]: value,
//     }));
//   };

//   const handleSave = () => {
//     setSavedMessage(true);
//     setTimeout(() => setSavedMessage(false), 3000);
//   };

//   const SettingToggle = ({ label, value, onChange }) => {
//     return (
//       <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded">
//         <span className="text-slate-300">{label}</span>
//         <button onClick={onChange} className="focus:outline-none">
//           {value ? (
//             <ToggleRight className="w-6 h-6 text-green-500" />
//           ) : (
//             <ToggleLeft className="w-6 h-6 text-slate-500" />
//           )}
//         </button>
//       </div>
//     );
//   };

//   return (
//     <div className="space-y-6">
//       <div className="flex items-center justify-between">
//         <div>
//           <h2 className="text-2xl font-bold text-white">
//             Settings & Configuration
//           </h2>
//           <p className="text-slate-400 text-sm mt-1">
//             Manage system preferences and security settings
//           </p>
//         </div>
//         {savedMessage && (
//           <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 rounded border border-green-500/30">
//             <span className="text-green-500 text-sm font-medium">
//               Settings saved successfully
//             </span>
//           </div>
//         )}
//       </div>

//       <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
//         <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
//           <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
//             <Bell className="w-5 h-5 text-blue-500" />
//             Notifications
//           </h3>
//           <div className="space-y-3">
//             <SettingToggle
//               label="Email Notifications"
//               value={settings.emailNotifications}
//               onChange={() => handleToggle("emailNotifications")}
//             />
//             <SettingToggle
//               label="Push Notifications"
//               value={settings.pushNotifications}
//               onChange={() => handleToggle("pushNotifications")}
//             />
//             <SettingToggle
//               label="SMS Alerts"
//               value={settings.smsAlerts}
//               onChange={() => handleToggle("smsAlerts")}
//             />
//             <SettingToggle
//               label="Sound Alerts"
//               value={settings.soundAlerts}
//               onChange={() => handleToggle("soundAlerts")}
//             />
//             <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
//               <label className="block text-slate-300 text-sm mb-2">
//                 Alert Sensitivity
//               </label>
//               <select
//                 value={settings.alertSensitivity}
//                 onChange={(e) =>
//                   handleSelectChange("alertSensitivity", e.target.value)
//                 }
//                 className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white text-sm focus:outline-none focus:border-blue-500"
//               >
//                 <option value="low">Low</option>
//                 <option value="medium">Medium</option>
//                 <option value="high">High</option>
//               </select>
//             </div>
//           </div>
//         </div>

//         <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
//           <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
//             <Lock className="w-5 h-5 text-red-500" />
//             Security
//           </h3>
//           <div className="space-y-3">
//             <SettingToggle
//               label="Security Lock"
//               value={settings.securityLock}
//               onChange={() => handleToggle("securityLock")}
//             />
//             <SettingToggle
//               label="Two-Factor Authentication"
//               value={settings.twoFactorAuth}
//               onChange={() => handleToggle("twoFactorAuth")}
//             />
//             <button className="w-full p-3 bg-slate-700/50 hover:bg-slate-700 rounded text-slate-300 text-sm transition-colors">
//               Change Password
//             </button>
//             <button className="w-full p-3 bg-slate-700/50 hover:bg-slate-700 rounded text-slate-300 text-sm transition-colors">
//               Manage API Keys
//             </button>
//             <button className="w-full p-3 bg-slate-700/50 hover:bg-slate-700 rounded text-slate-300 text-sm transition-colors">
//               View Login History
//             </button>
//           </div>
//         </div>

//         <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
//           <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
//             <Database className="w-5 h-5 text-emerald-500" />
//             Data & Storage
//           </h3>
//           <div className="space-y-3">
//             <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
//               <label className="block text-slate-300 text-sm mb-2">
//                 Backup Frequency
//               </label>
//               <select
//                 value={settings.backupFrequency}
//                 onChange={(e) =>
//                   handleSelectChange("backupFrequency", e.target.value)
//                 }
//                 className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white text-sm focus:outline-none focus:border-blue-500"
//               >
//                 <option value="hourly">Hourly</option>
//                 <option value="daily">Daily</option>
//                 <option value="weekly">Weekly</option>
//                 <option value="monthly">Monthly</option>
//               </select>
//             </div>
//             <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
//               <label className="block text-slate-300 text-sm mb-2">
//                 Data Retention Period
//               </label>
//               <select
//                 value={settings.retentionPeriod}
//                 onChange={(e) =>
//                   handleSelectChange("retentionPeriod", e.target.value)
//                 }
//                 className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white text-sm focus:outline-none focus:border-blue-500"
//               >
//                 <option value="30days">30 Days</option>
//                 <option value="60days">60 Days</option>
//                 <option value="90days">90 Days</option>
//                 <option value="1year">1 Year</option>
//               </select>
//             </div>
//             <button className="w-full p-3 bg-slate-700/50 hover:bg-slate-700 rounded text-slate-300 text-sm transition-colors">
//               Run Backup Now
//             </button>
//             <button className="w-full p-3 bg-slate-700/50 hover:bg-slate-700 rounded text-slate-300 text-sm transition-colors">
//               Database Status
//             </button>
//           </div>
//         </div>

//         <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
//           <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
//             <Palette className="w-5 h-5 text-purple-500" />
//             Preferences
//           </h3>
//           <div className="space-y-3">
//             <SettingToggle
//               label="Dark Mode"
//               value={settings.darkMode}
//               onChange={() => handleToggle("darkMode")}
//             />
//             <SettingToggle
//               label="Auto Refresh"
//               value={settings.autoRefresh}
//               onChange={() => handleToggle("autoRefresh")}
//             />
//             <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
//               <label className="block text-slate-300 text-sm mb-2">
//                 Timezone
//               </label>
//               <select
//                 value={settings.timezone}
//                 onChange={(e) => handleSelectChange("timezone", e.target.value)}
//                 className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white text-sm focus:outline-none focus:border-blue-500"
//               >
//                 <option value="UTC">UTC</option>
//                 <option value="EST">Eastern (EST)</option>
//                 <option value="CST">Central (CST)</option>
//                 <option value="PST">Pacific (PST)</option>
//               </select>
//             </div>
//             <button className="w-full p-3 bg-slate-700/50 hover:bg-slate-700 rounded text-slate-300 text-sm transition-colors">
//               Reset to Defaults
//             </button>
//           </div>
//         </div>
//       </div>

//       <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
//         <h3 className="text-lg font-bold text-white mb-4">
//           System Information
//         </h3>
//         <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
//           <div className="p-3 bg-slate-700/50 rounded">
//             <p className="text-slate-400 text-sm">Version</p>
//             <p className="text-white font-semibold">2.0.1</p>
//           </div>
//           <div className="p-3 bg-slate-700/50 rounded">
//             <p className="text-slate-400 text-sm">Last Update</p>
//             <p className="text-white font-semibold">2025-12-29 14:00</p>
//           </div>
//           <div className="p-3 bg-slate-700/50 rounded">
//             <p className="text-slate-400 text-sm">Server Status</p>
//             <p className="text-green-500 font-semibold">Online</p>
//           </div>
//           <div className="p-3 bg-slate-700/50 rounded">
//             <p className="text-slate-400 text-sm">Database</p>
//             <p className="text-white font-semibold">Connected</p>
//           </div>
//         </div>
//       </div>

//       <div className="flex justify-end gap-3">
//         <button className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded transition-colors">
//           Cancel
//         </button>
//         <button
//           onClick={handleSave}
//           className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
//         >
//           <Save className="w-4 h-4" />
//           Save Settings
//         </button>
//       </div>
//     </div>
//   );
// };

// export default SettingsPage;
