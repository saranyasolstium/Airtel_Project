// src/pages/TrafficFlowPage.jsx
import React, { useEffect, useMemo, useState } from "react";
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

import {
  listTrafficFlowVehicles,
  exportTrafficFlowCSV,
} from "../api/trafficFlow";
import "../styles/traffic.css";

/* ================= helpers ================= */
const pad2 = (n) => String(n).padStart(2, "0");
const toInputDate = (d) =>
  `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;

// ✅ RULES YOU ASKED
// < 2 hours => INFO
// >= 2 hours => WARNING
// >= 10 hours => CRITICAL
const computeSeverity = (dwellSeconds) => {
  const s = Number(dwellSeconds || 0);
  if (s >= 10 * 3600) return "CRITICAL";
  if (s >= 2 * 3600) return "WARNING";
  return "INFO";
};

/* ======= Severity mapping (for your glass theme) ======= */
const severityClass = (severity) => {
  const s = (severity || "").toLowerCase();
  if (s === "critical") return "tCard tCritical";
  if (s === "warning") return "tCard tWarning";
  return "tCard tInfo";
};

/* ================= Card ================= */
const DwellAlertCard = ({ alert }) => {
  const sev = alert.severity || "INFO";

  return (
    <div className={severityClass(sev)}>
      <div className="tCardRow">
        <div className="tIconWrap">
          <AlertTriangle size={18} />
        </div>

        <div className="tCardBody">
          <div className="tPills">
            <span className="tPill">{sev.toUpperCase()}</span>
          </div>

          <div className="tCardTitle">
            <b>{alert.plate_text || "-"}</b> exceeded dwell time limit
          </div>

          <div className="tMeta">
            <div className="tMetaItem">
              <MapPin size={14} />
              <span>{alert.location_text || "-"}</span>
            </div>

            <div className="tMetaItem">
              <Clock size={14} />
              <span>{alert.dwell_text || "-"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ================= Page ================= */
export default function TrafficFlowPage() {
  const [selectedDate, setSelectedDate] = useState(toInputDate(new Date()));
  const [limit, setLimit] = useState(10);
  const [page, setPage] = useState(1);

  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
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
        dwell_limit_seconds: 7200, // just for display “limit” label
      });

      const rows = res?.data || res?.items || [];

      // ✅ Force severity rules in frontend (even if backend returns wrong)
      const fixed = rows.map((r) => ({
        ...r,
        severity: computeSeverity(r?.dwell_seconds),
      }));

      setAlerts(fixed);
      setTotal(Number(res?.total || 0));
    } catch (e) {
      console.error(e);
      setAlerts([]);
      setTotal(0);
      setErr(e?.message || "Failed to load alerts");
    } finally {
      setLoading(false);
    }
  };

  // ✅ Backend CSV Export (BEST)
  const exportCSV = async () => {
    setExporting(true);
    setErr("");
    try {
      const res = await exportTrafficFlowCSV({
        date: selectedDate,
        dwell_limit_seconds: 7200,
      });

      const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);

      // try filename from headers
      const cd = res.headers?.["content-disposition"] || "";
      const match = cd.match(/filename="([^"]+)"/);
      const filename = match?.[1] || `traffic_flow_${selectedDate}.csv`;

      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      setErr(e?.message || "Export failed");
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    loadAlerts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate, limit, page]);

  const showingText = useMemo(() => {
    if (total === 0) return "Showing 0 - 0 of 0";
    const from = offset + 1;
    const to = Math.min(offset + limit, total);
    return `Showing ${from} - ${to} of ${total}`;
  }, [offset, limit, total]);

  return (
    <div className="tPage">
      <div className="tTop">
        <div>
          <div className="tHeading">Traffic Flow</div>
          <div className="tSubheading">
            Dwell time alerts for vehicles exceeding allowed limits
          </div>
        </div>
      </div>

      <div className="tPanel">
        <div className="tPanelHeader">
          <div>
            <div className="tTitle">Dwell Time Alerts</div>
            <div className="tSub">Filter by date and export alerts</div>
          </div>

          <div className="tHeaderRight">
            <button
              className="tBtn tBtnGhost"
              onClick={loadAlerts}
              disabled={loading}
              title="Refresh"
            >
              <RefreshCw size={16} className={loading ? "tSpin" : ""} />
              Refresh
            </button>

            <button
              className="tBtn tBtnPrimary"
              type="button"
              onClick={exportCSV}
              disabled={exporting}
              title="Export CSV"
            >
              <Download size={16} />
              {exporting ? "Exporting..." : "Export Report"}
            </button>
          </div>
        </div>

        <div className="tFilters">
          <div className="tField">
            <div className="tLabel">Date</div>
            <div className="tInputIcon">
              <CalendarDays size={16} />
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => {
                  setPage(1);
                  setSelectedDate(e.target.value);
                }}
              />
            </div>
          </div>

          <div className="tField">
            <div className="tLabel">Rows</div>
            <div className="tInputIcon">
              <Filter size={16} />
              <select
                value={limit}
                onChange={(e) => {
                  setPage(1);
                  setLimit(Number(e.target.value));
                }}
              >
                <option value={5}>5 / page</option>
                <option value={10}>10 / page</option>
                <option value={20}>20 / page</option>
              </select>
            </div>
          </div>
        </div>

        {err ? <div className="tError">{err}</div> : null}

        {loading ? (
          <div className="tEmpty">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="tEmpty">
            <div className="tEmptyIcon">
              <AlertTriangle size={20} />
            </div>
            <div className="tEmptyTitle">No dwell time alerts</div>
            <div className="tEmptySub">Try selecting a different date</div>
          </div>
        ) : (
          <div className="tList">
            {alerts.map((a) => (
              <DwellAlertCard
                key={a.id ?? `${a.plate_text}-${a.dwell_seconds}`}
                alert={a}
              />
            ))}
          </div>
        )}

        <div className="tFooter">
          <div className="tFooterLeft">{showingText}</div>

          <div className="tFooterRight">
            <button
              className="tBtn tBtnGhost"
              disabled={page <= 1 || loading}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft size={16} />
              Prev
            </button>

            <div className="tPageInfo">
              Page <b>{page}</b> / <b>{totalPages}</b>
            </div>

            <button
              className="tBtn tBtnGhost"
              disabled={page >= totalPages || loading}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
