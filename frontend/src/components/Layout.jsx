// Layout.jsx - LIGHT THEME (Search & Refresh Removed)
import React, { useState, useEffect } from "react";
import { Bell, Clock } from "lucide-react";
import Sidebar from "./Sidebar";

const Layout = ({
  children,
  title,
  activeAlerts,
  onPageChange,
  currentPage,
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date) =>
    date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });

  const formatDate = (date) =>
    date.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar
        activeAlerts={activeAlerts}
        onPageChange={onPageChange}
        currentPage={currentPage}
      />

      {/* right side */}
      <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
        {/* topbar */}
        <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
                <p className="text-gray-600 text-sm mt-1">
                  {formatDate(currentTime)}
                </p>
              </div>

              <div className="flex items-center gap-3">
                {/* time */}
                <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-100 rounded-lg">
                  <Clock className="w-4 h-4 text-blue-500" />
                  <span className="text-blue-700 font-mono font-semibold text-sm">
                    {formatTime(currentTime)}
                  </span>
                </div>

                {/* bell */}
                <button className="relative p-2 bg-blue-50 hover:bg-blue-100 border border-blue-100 rounded-lg transition-colors">
                  <Bell className="w-5 h-5 text-blue-600" />
                  {activeAlerts > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                      {activeAlerts}
                    </span>
                  )}
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* content */}
        <main className="flex-1 overflow-y-auto p-6 bg-gray-50">
          {children}
        </main>

        {/* footer */}
        <footer className="bg-white border-t border-gray-200 px-6 py-4 shadow-inner">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <p>Airtel Platform v1.0.1</p>
            <p>{formatTime(currentTime)}</p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Layout;

// // Layout.jsx - CHANGED TO LIGHT THEME
// import React, { useState, useEffect } from "react";
// import { Bell, Clock, RefreshCw, Search } from "lucide-react";
// import Sidebar from "./Sidebar";

// const Layout = ({
//   children,
//   title,
//   activeAlerts,
//   onPageChange,
//   currentPage,
// }) => {
//   const [currentTime, setCurrentTime] = useState(new Date());
//   const [lastRefresh, setLastRefresh] = useState(new Date());
//   const [searchQuery, setSearchQuery] = useState("");

//   useEffect(() => {
//     const timer = setInterval(() => setCurrentTime(new Date()), 1000);
//     return () => clearInterval(timer);
//   }, []);

//   const handleRefresh = () => setLastRefresh(new Date());

//   const formatTime = (date) =>
//     date.toLocaleTimeString("en-US", {
//       hour: "2-digit",
//       minute: "2-digit",
//       second: "2-digit",
//     });

//   const formatDate = (date) =>
//     date.toLocaleDateString("en-US", {
//       weekday: "long",
//       year: "numeric",
//       month: "long",
//       day: "numeric",
//     });

//   return (
//     <div className="flex h-screen bg-gray-50 overflow-hidden">
//       <Sidebar
//         activeAlerts={activeAlerts}
//         onPageChange={onPageChange}
//         currentPage={currentPage}
//       />

//       {/* right side */}
//       <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
//         {/* topbar */}
//         <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
//           <div className="px-6 py-4">
//             <div className="flex items-center justify-between">
//               <div>
//                 <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
//                 <p className="text-gray-600 text-sm mt-1">
//                   {formatDate(currentTime)}
//                 </p>
//               </div>

//               <div className="flex items-center gap-3">
//                 {/* search */}
//                 <div className="relative hidden md:block">
//                   <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
//                   <input
//                     type="text"
//                     placeholder="Search..."
//                     value={searchQuery}
//                     onChange={(e) => setSearchQuery(e.target.value)}
//                     className="pl-10 pr-4 py-2 bg-gray-50 border border-gray-300 rounded-lg text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all w-64"
//                   />
//                 </div>

//                 {/* time */}
//                 <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-100 rounded-lg">
//                   <Clock className="w-4 h-4 text-blue-500" />
//                   <span className="text-blue-700 font-mono font-semibold text-sm">
//                     {formatTime(currentTime)}
//                   </span>
//                 </div>

//                 {/* refresh */}
//                 <button
//                   onClick={handleRefresh}
//                   className="flex items-center gap-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 border border-blue-100 text-blue-700 rounded-lg transition-colors"
//                 >
//                   <RefreshCw className="w-4 h-4" />
//                   <span className="text-sm hidden sm:inline">Refresh</span>
//                 </button>

//                 {/* bell */}
//                 <button className="relative p-2 bg-blue-50 hover:bg-blue-100 border border-blue-100 rounded-lg transition-colors">
//                   <Bell className="w-5 h-5 text-blue-600" />
//                   {activeAlerts > 0 && (
//                     <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
//                       {activeAlerts}
//                     </span>
//                   )}
//                 </button>
//               </div>
//             </div>
//           </div>
//         </header>

//         {/* only this scrolls */}
//         <main className="flex-1 overflow-y-auto p-6 bg-gray-50">
//           {children}
//         </main>

//         {/* footer */}
//         <footer className="bg-white border-t border-gray-200 px-6 py-4 shadow-inner">
//           <div className="flex items-center justify-between text-sm text-gray-600">
//             <p>Airtel Platform v1.0.1</p>
//             <p>Last Updated: {formatTime(lastRefresh)}</p>
//           </div>
//         </footer>
//       </div>
//     </div>
//   );
// };

// export default Layout;
