// src/pages/VehiclesPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import {
  Car,
  Clock,
  MapPin,
  Search,
  Eye,
  X,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import { listVehicleLogs } from "../api/vehicleLogs";

/* ========================= Modal ========================= */
const ImagePreviewModal = ({ open, onClose, imageUrl, title }) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-3xl rounded-xl border shadow-xl overflow-hidden">
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="text-lg font-bold">{title}</h3>
          <button onClick={onClose} className="p-2 rounded hover:bg-gray-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 bg-gray-50">
          <div className="aspect-video bg-white border rounded flex items-center justify-center overflow-hidden">
            {imageUrl ? (
              <img
                src={imageUrl}
                alt="capture"
                className="w-full h-full object-contain"
              />
            ) : (
              <span className="text-gray-500 text-sm">No image</span>
            )}
          </div>
        </div>

        <div className="p-4 border-t text-right">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 border"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

/* ========================= Helpers ========================= */
const prettyDT = (s) => (s ? String(s).replace("T", " ") : "-");

const StatusPill = ({ exited }) =>
  exited ? (
    <span className="px-3 py-1 rounded-full text-xs bg-gray-100 text-gray-700 border">
      Exited
    </span>
  ) : (
    <span className="px-3 py-1 rounded-full text-xs bg-emerald-100 text-emerald-700 border">
      On-Site
    </span>
  );

const todayYYYYMMDD = () => {
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
};

const toImageSrc = (capture_image) => {
  if (!capture_image) return "";
  const s = String(capture_image);
  if (s.startsWith("data:image/")) return s; // already full data url
  // assume base64 only (no header)
  return `data:image/jpeg;base64,${s}`;
};

/* ========================= Page ========================= */
const VehiclesPage = () => {
  const [search, setSearch] = useState("");

  // ✅ two-date range (defaults to today)
  const [dateFrom, setDateFrom] = useState(todayYYYYMMDD());
  const [dateTo, setDateTo] = useState(todayYYYYMMDD());

  // pagination
  const [limit, setLimit] = useState(10);
  const [offset, setOffset] = useState(0);

  // api state
  const [total, setTotal] = useState(0);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // modal
  const [preview, setPreview] = useState({
    open: false,
    imageUrl: "",
    title: "",
  });

  const page = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const canPrev = offset > 0;
  const canNext = offset + limit < total;

  const fetchLogs = async () => {
    setLoading(true);
    setError("");
    try {
      const json = await listVehicleLogs({
        search,
        limit,
        offset,
        date_from: dateFrom,
        date_to: dateTo,
      });

      setLogs(json.items || []);
      setTotal(Number(json.total || 0));
    } catch (e) {
      setError(e?.message || "Failed to load vehicle logs");
      setLogs([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  // ✅ refetch on any change
  useEffect(() => {
    fetchLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, dateFrom, dateTo, limit, offset]);

  // cards (based on returned total + current page)
  const totalVehiclesLogged = total;
  const onSiteCount = logs.filter((v) => !v.exit_time).length;

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border rounded-xl p-5">
          <p className="text-sm text-gray-600">Total Vehicles Logged</p>
          <p className="text-3xl font-bold mt-2">{totalVehiclesLogged}</p>
        </div>
        <div className="bg-white border rounded-xl p-5">
          <p className="text-sm text-gray-600">Currently On-Site (Page)</p>
          <p className="text-3xl font-bold text-blue-600 mt-2">{onSiteCount}</p>
        </div>
        <div className="bg-white border rounded-xl p-5">
          <p className="text-sm text-gray-600">Avg Dwell Time</p>
          <p className="text-3xl font-bold mt-2">—</p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        <div className="p-5 border-b flex flex-wrap gap-3 justify-between items-center">
          <h2 className="text-lg font-semibold">Vehicle Logs</h2>

          <div className="flex flex-wrap items-center gap-3">
            {/* From */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">From</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => {
                  const nextFrom = e.target.value || todayYYYYMMDD();
                  setOffset(0);
                  setDateFrom(nextFrom);
                  // keep to >= from
                  if (dateTo && dateTo < nextFrom) setDateTo(nextFrom);
                }}
                className="border rounded-lg px-3 py-2 text-sm"
              />
            </div>

            {/* To */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">To</span>
              <input
                type="date"
                value={dateTo}
                min={dateFrom}
                onChange={(e) => {
                  setOffset(0);
                  setDateTo(e.target.value || dateFrom);
                }}
                className="border rounded-lg px-3 py-2 text-sm"
              />
            </div>

            {/* Search */}
            <div className="relative w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={search}
                onChange={(e) => {
                  setOffset(0);
                  setSearch(e.target.value);
                }}
                placeholder="Search plate / location..."
                className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm"
              />
            </div>

            {/* Refresh */}
            <button
              onClick={() => fetchLogs()}
              className="px-4 py-2 rounded-lg border bg-white hover:bg-gray-50 text-sm"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Error */}
        {error ? (
          <div className="px-5 py-3 border-b bg-red-50 text-red-700 text-sm">
            {error}
          </div>
        ) : null}

        <div className="overflow-x-auto">
          <table className="w-full text-sm table-fixed">
            <thead className="bg-white border-b">
              <tr className="text-xs uppercase text-gray-600">
                <th className="px-5 py-3 w-[210px] text-left">Capture</th>

                {/* ✅ Reduced plate column width */}
                <th className="px-5 py-3 w-[120px] text-left">Plate</th>

                {/* ✅ Increased entry/exit widths */}
                <th className="px-5 py-3 w-[240px] text-center">Entry</th>
                <th className="px-5 py-3 w-[240px] text-center">Exit</th>

                <th className="px-5 py-3 w-[120px] text-center">Dwell</th>
                <th className="px-5 py-3 text-left">Location</th>
                <th className="px-5 py-3 w-[140px] text-center">Status</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-5 py-10 text-center text-gray-500"
                  >
                    Loading...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-5 py-10 text-center text-gray-500 font-extrabold"
                  >
                    No records for this date range.
                  </td>
                </tr>
              ) : (
                logs.map((row) => {
                  const exited = Boolean(row.exit_time);
                  const imgSrc = toImageSrc(row.capture_image);

                  return (
                    <tr key={row.id} className="border-b hover:bg-gray-50">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-14 h-10 border rounded bg-gray-100 overflow-hidden flex items-center justify-center shrink-0">
                            {imgSrc ? (
                              <img
                                src={imgSrc}
                                alt=""
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <Car className="w-5 h-5 text-gray-400" />
                            )}
                          </div>

                          <button
                            onClick={() =>
                              setPreview({
                                open: true,
                                imageUrl: imgSrc,
                                title: `Capture - ${row.plate_text || ""}`,
                              })
                            }
                            className="px-2.5 py-1.5 border rounded text-xs flex items-center gap-1"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            View
                          </button>
                        </div>
                      </td>

                      <td className="px-5 py-4 font-semibold whitespace-nowrap overflow-hidden text-ellipsis">
                        {row.plate_text || "-"}
                      </td>

                      <td className="px-5 py-4 text-center whitespace-nowrap">
                        <div className="inline-flex items-center gap-2">
                          <Clock className="w-4 h-4 text-gray-400" />
                          {prettyDT(row.entry_time)}
                        </div>
                      </td>

                      <td className="px-5 py-4 text-center whitespace-nowrap">
                        {prettyDT(row.exit_time)}
                      </td>

                      <td className="px-5 py-4 text-center whitespace-nowrap">
                        {row.dwell_time || "-"}
                      </td>

                      <td className="px-5 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <MapPin className="w-4 h-4 text-gray-400" />
                          {row.location || "-"}
                        </div>
                      </td>

                      <td className="px-5 py-4 text-center">
                        <StatusPill exited={exited} />
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls Bottom */}
        <div className="px-5 py-3 border-b bg-gray-50 flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm text-gray-600">
            Showing <b>{total === 0 ? 0 : offset + 1}</b> -{" "}
            <b>{Math.min(offset + limit, total)}</b> of <b>{total}</b>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-600">Rows</span>
              <select
                value={limit}
                onChange={(e) => {
                  setOffset(0);
                  setLimit(Number(e.target.value));
                }}
                className="border rounded-lg px-2 py-1.5"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>

            <button
              disabled={!canPrev || loading}
              onClick={() => setOffset((o) => Math.max(0, o - limit))}
              className="px-3 py-2 rounded-lg border disabled:opacity-50 flex items-center gap-1"
            >
              <ChevronLeft className="w-4 h-4" /> Prev
            </button>

            <div className="text-sm text-gray-700">
              Page <b>{page}</b> / <b>{totalPages}</b>
            </div>

            <button
              disabled={!canNext || loading}
              onClick={() => setOffset((o) => o + limit)}
              className="px-3 py-2 rounded-lg border disabled:opacity-50 flex items-center gap-1"
            >
              Next <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Modal */}
      <ImagePreviewModal
        open={preview.open}
        imageUrl={preview.imageUrl}
        title={preview.title}
        onClose={() => setPreview({ open: false, imageUrl: "", title: "" })}
      />
    </div>
  );
};

export default VehiclesPage;
