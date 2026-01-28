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
  Bike,
  Bus,
  Truck,
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

const toImageSrc = (img) => {
  if (!img) return "";
  const s = String(img);
  if (s.startsWith("data:image/")) return s;
  return `data:image/jpeg;base64,${s}`;
};

const StatusPill = ({ exited }) => (
  <span className={`v-pill ${exited ? "v-pillExited" : "v-pillOnsite"}`}>
    {exited ? "Exited" : "On-Site"}
  </span>
);

const WhitelistPill = ({ status }) => {
  const s = (status || "not_found").toLowerCase();

  const label =
    s === "approved"
      ? "Approved"
      : s === "blocked"
        ? "Blocked"
        : s === "expired"
          ? "Expired"
          : "Not Found";

  return <span className={`wl-pill wl-${s}`}>{label}</span>;
};

/* ✅ Avg dwell formatter */
function formatAvg(seconds) {
  const s = Number(seconds || 0);
  if (!s || s <= 0) return "—";

  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);

  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

/* ✅ Vehicle type badge */
const normalizeType = (t) =>
  String(t || "car")
    .trim()
    .toLowerCase();

const VehicleTypeBadge = ({ type }) => {
  const t = normalizeType(type);

  const meta =
    t === "bike" || t === "motorcycle"
      ? { label: "Bike", Icon: Bike, cls: "vt-bike" }
      : t === "bus"
        ? { label: "Bus", Icon: Bus, cls: "vt-bus" }
        : t === "truck"
          ? { label: "Truck", Icon: Truck, cls: "vt-truck" }
          : { label: "Car", Icon: Car, cls: "vt-car" };

  const IconComp = meta.Icon;

  return (
    <span className={`vtBadge ${meta.cls}`}>
      <IconComp size={14} />
      {meta.label}
    </span>
  );
};

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

  /* ✅ AVG DWELL: exited vehicles only */
  const avgDwellSecondsExited = useMemo(() => {
    const rows = logs.filter((r) => {
      const exited = Boolean(r.exit_time);
      const ds = Number(r?.dwell_seconds || 0);
      return exited && ds > 0;
    });
    if (!rows.length) return 0;
    const sum = rows.reduce((acc, r) => acc + Number(r.dwell_seconds || 0), 0);
    return Math.round(sum / rows.length);
  }, [logs]);

  const avgDwellText = useMemo(
    () => formatAvg(avgDwellSecondsExited),
    [avgDwellSecondsExited],
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
          <div className="vStatLabel">Avg Dwell Time (Exited)</div>
          <div className="vStatValue">{avgDwellText}</div>
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

            <div className="vInputIcon">
              <Clock size={16} />
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => {
                  const nextFrom = e.target.value || todayYYYYMMDD();
                  setOffset(0);
                  setDateFrom(nextFrom);
                  if (dateTo && dateTo < nextFrom) setDateTo(nextFrom);
                }}
              />
            </div>
          </div>

          <div className="vField">
            <div className="vFieldLabel">To</div>

            <div className="vInputIcon">
              <Clock size={16} />
              <input
                type="date"
                value={dateTo}
                min={dateFrom}
                onChange={(e) => {
                  setOffset(0);
                  setDateTo(e.target.value || dateFrom);
                }}
              />
            </div>
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
                <th style={{ width: 140, textAlign: "center" }}>Type</th>
                <th style={{ width: 140 }}>Plate</th>
                <th style={{ width: 160, textAlign: "center" }}>Whitelist</th>
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
                  <td colSpan={9} className="vEmptyRow">
                    Loading...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={9} className="vEmptyRow">
                    No records for this date range.
                  </td>
                </tr>
              ) : (
                logs.map((row) => {
                  const exited = Boolean(row.exit_time);

                  const entryImgSrc = toImageSrc(
                    row.capture_image_entry || row.capture_image,
                  );
                  const exitImgSrc = toImageSrc(row.capture_image_exit);
                  const thumbSrc = entryImgSrc || exitImgSrc;

                  const vType = row.type || row.event_type; // ✅ supports both

                  return (
                    <tr key={row.id}>
                      <td>
                        <div className="vCaptureCell">
                          <div className="vThumb">
                            {thumbSrc ? (
                              <img
                                src={thumbSrc}
                                alt=""
                                className="vThumbImg"
                              />
                            ) : (
                              <Car size={18} />
                            )}
                          </div>

                          <div style={{ display: "flex", gap: 8 }}>
                            <button
                              className="vMiniBtn"
                              disabled={!entryImgSrc}
                              onClick={() =>
                                setPreview({
                                  open: true,
                                  imageUrl: entryImgSrc,
                                  title: `Entry Capture - ${row.plate_text || ""}`,
                                })
                              }
                            >
                              <Eye size={14} />
                              Entry
                            </button>

                            <button
                              className="vMiniBtn"
                              disabled={!exitImgSrc}
                              onClick={() =>
                                setPreview({
                                  open: true,
                                  imageUrl: exitImgSrc,
                                  title: `Exit Capture - ${row.plate_text || ""}`,
                                })
                              }
                            >
                              <Eye size={14} />
                              Exit
                            </button>
                          </div>
                        </div>
                      </td>

                      <td style={{ textAlign: "center" }}>
                        <VehicleTypeBadge type={vType} />
                      </td>

                      <td className="vPlate">{row.plate_text || "-"}</td>

                      <td style={{ textAlign: "center" }}>
                        <WhitelistPill status={row.whitelist_status} />
                      </td>

                      <td style={{ textAlign: "center" }}>
                        <div className="vDT">
                          <Clock size={16} />
                          {prettyDT(row.entry_time)}
                        </div>
                      </td>

                      <td style={{ textAlign: "center" }}>
                        {prettyDT(row.exit_time)}
                      </td>

                      <td style={{ textAlign: "center" }}>
                        {row.dwell_time || "-"}
                      </td>

                      <td>
                        <div className="vLoc">
                          <MapPin size={16} />
                          {row.location || "-"}
                        </div>
                      </td>

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
