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
  RefreshCw,
} from "lucide-react";

import { listVehicleLogs } from "../api/vehicleLogs";
import "../styles/vehicles.css";

/* ========================= Helpers ========================= */
const prettyDT = (s) => (s ? String(s).replace("T", " ") : "-");

const todayYYYYMMDD = () => {
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
};

const toImageSrc = (capture_image) => {
  if (!capture_image) return "";
  const s = String(capture_image);
  if (s.startsWith("data:image/")) return s;
  return `data:image/jpeg;base64,${s}`;
};

const StatusPill = ({ exited }) => (
  <span className={`v-pill ${exited ? "v-pillExited" : "v-pillOnsite"}`}>
    {exited ? "Exited" : "On-Site"}
  </span>
);

/* ========================= Modal ========================= */
const ImagePreviewModal = ({ open, onClose, imageUrl, title }) => {
  if (!open) return null;

  return (
    <div
      className="vModalOverlay"
      onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}
    >
      <div className="vModal">
        <div className="vModalHeader">
          <div className="vModalTitle">{title}</div>
          <button className="vIconBtn" onClick={onClose} title="Close">
            <X size={18} />
          </button>
        </div>

        <div className="vModalBody">
          <div className="vModalFrame">
            {imageUrl ? (
              <img src={imageUrl} alt="capture" className="vModalImg" />
            ) : (
              <div className="vModalEmpty">No image</div>
            )}
          </div>
        </div>

        <div className="vModalFooter">
          <button className="vBtn vBtnGhost" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

/* ========================= Page ========================= */
export default function VehiclesPage() {
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState(todayYYYYMMDD());
  const [dateTo, setDateTo] = useState(todayYYYYMMDD());

  const [limit, setLimit] = useState(10);
  const [offset, setOffset] = useState(0);

  const [total, setTotal] = useState(0);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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

  useEffect(() => {
    fetchLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, dateFrom, dateTo, limit, offset]);

  const totalVehiclesLogged = total;
  const onSiteCount = useMemo(
    () => logs.filter((v) => !v.exit_time).length,
    [logs],
  );

  return (
    <div className="vPage">
      {/* Page Heading */}
      <div className="vHero">
        <h1 className="vHeroTitle">Vehicle Management</h1>
        <p className="vHeroSub">
          Track vehicle entries, exits, dwell time and capture history
        </p>
      </div>

      {/* Stats */}
      <div className="vStats">
        <div className="vStatCard">
          <div className="vStatLabel">Total Vehicles Logged</div>
          <div className="vStatValue">{totalVehiclesLogged}</div>
        </div>

        <div className="vStatCard">
          <div className="vStatLabel">Currently On-Site (Page)</div>
          <div className="vStatValue vBlue">{onSiteCount}</div>
        </div>

        <div className="vStatCard">
          <div className="vStatLabel">Avg Dwell Time</div>
          <div className="vStatValue">—</div>
        </div>
      </div>

      {/* Panel */}
      <div className="vPanel">
        {/* Header */}
        <div className="vPanelHeader">
          <div>
            <div className="vTitle">Vehicle Logs</div>
            <div className="vSub">Filter by date range and search plates</div>
          </div>

          <div className="vHeaderRight">
            <button
              onClick={fetchLogs}
              className="vBtn vBtnGhost"
              disabled={loading}
            >
              <RefreshCw size={16} className={loading ? "vSpin" : ""} />
              Refresh
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="vFilters">
          <div className="vField">
            <div className="vFieldLabel">From</div>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => {
                const nextFrom = e.target.value || todayYYYYMMDD();
                setOffset(0);
                setDateFrom(nextFrom);
                if (dateTo && dateTo < nextFrom) setDateTo(nextFrom);
              }}
              className="vInput"
            />
          </div>

          <div className="vField">
            <div className="vFieldLabel">To</div>
            <input
              type="date"
              value={dateTo}
              min={dateFrom}
              onChange={(e) => {
                setOffset(0);
                setDateTo(e.target.value || dateFrom);
              }}
              className="vInput"
            />
          </div>

          <div className="vSearch">
            <Search size={16} />
            <input
              value={search}
              onChange={(e) => {
                setOffset(0);
                setSearch(e.target.value);
              }}
              placeholder="Search plate / location..."
            />
          </div>
        </div>

        {/* Error */}
        {error ? <div className="vError">{error}</div> : null}

        {/* Table */}
        <div className="vTableWrap">
          <table className="vTable">
            <thead>
              <tr>
                <th style={{ width: 210 }}>Capture</th>
                <th style={{ width: 140 }}>Plate</th>
                <th style={{ width: 240, textAlign: "center" }}>Entry</th>
                <th style={{ width: 240, textAlign: "center" }}>Exit</th>
                <th style={{ width: 120, textAlign: "center" }}>Dwell</th>
                <th>Location</th>
                <th style={{ width: 140, textAlign: "center" }}>Status</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="vEmptyRow">
                    Loading...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="vEmptyRow">
                    No records for this date range.
                  </td>
                </tr>
              ) : (
                logs.map((row) => {
                  const exited = Boolean(row.exit_time);
                  const imgSrc = toImageSrc(row.capture_image);

                  return (
                    <tr key={row.id}>
                      {/* Capture */}
                      <td>
                        <div className="vCaptureCell">
                          <div className="vThumb">
                            {imgSrc ? (
                              <img src={imgSrc} alt="" className="vThumbImg" />
                            ) : (
                              <Car size={18} />
                            )}
                          </div>

                          <button
                            className="vMiniBtn"
                            onClick={() =>
                              setPreview({
                                open: true,
                                imageUrl: imgSrc,
                                title: `Capture - ${row.plate_text || ""}`,
                              })
                            }
                          >
                            <Eye size={14} />
                            View
                          </button>
                        </div>
                      </td>

                      {/* Plate */}
                      <td className="vPlate">{row.plate_text || "-"}</td>

                      {/* Entry */}
                      <td style={{ textAlign: "center" }}>
                        <div className="vDT">
                          <Clock size={16} />
                          {prettyDT(row.entry_time)}
                        </div>
                      </td>

                      {/* Exit */}
                      <td style={{ textAlign: "center" }}>
                        {prettyDT(row.exit_time)}
                      </td>

                      {/* Dwell */}
                      <td style={{ textAlign: "center" }}>
                        {row.dwell_time || "-"}
                      </td>

                      {/* Location */}
                      <td>
                        <div className="vLoc">
                          <MapPin size={16} />
                          {row.location || "-"}
                        </div>
                      </td>

                      {/* Status */}
                      <td style={{ textAlign: "center" }}>
                        <StatusPill exited={exited} />
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="vPager">
          <div className="vPagerLeft">
            Showing <b>{total === 0 ? 0 : offset + 1}</b> -{" "}
            <b>{Math.min(offset + limit, total)}</b> of <b>{total}</b>
          </div>

          <div className="vPagerRight">
            <div className="vRows">
              <span>Rows</span>
              <select
                value={limit}
                onChange={(e) => {
                  setOffset(0);
                  setLimit(Number(e.target.value));
                }}
                className="vSelect"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>

            <button
              className="vBtn vBtnGhost"
              disabled={!canPrev || loading}
              onClick={() => setOffset((o) => Math.max(0, o - limit))}
            >
              <ChevronLeft size={16} />
              Prev
            </button>

            <div className="vPageInfo">
              Page <b>{page}</b> / <b>{totalPages}</b>
            </div>

            <button
              className="vBtn vBtnGhost"
              disabled={!canNext || loading}
              onClick={() => setOffset((o) => o + limit)}
            >
              Next
              <ChevronRight size={16} />
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
}
