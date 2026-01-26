import React, { useEffect, useMemo, useState } from "react";
import {
  ShieldCheck,
  Plus,
  RefreshCw,
  Search,
  CalendarDays,
  User,
  Car,
  ClipboardList,
  Edit2,
  X,
  ChevronUp,
  ChevronDown,
  ArrowUpDown,
} from "lucide-react";

import {
  listWhitelist,
  createWhitelist,
  setWhitelistStatus,
  updateWhitelist,
} from "../api/vehicleWhitelist";

import "../styles/whitelist.css";

const pad2 = (n) => String(n).padStart(2, "0");
const toInputDate = (d) =>
  `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;

const today = () => toInputDate(new Date());

const StatusPill = ({ status }) => {
  const s = (status || "").toLowerCase();
  const approved = s === "approved";
  return (
    <span className={`wPill ${approved ? "wPillOk" : "wPillBad"}`}>
      {approved ? "Approved" : "Blocked"}
    </span>
  );
};

function Modal({ open, title, onClose, children }) {
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev || "auto";
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="wModalOverlay" onMouseDown={onClose}>
      <div className="wModal" onMouseDown={(e) => e.stopPropagation()}>
        <div className="wModalHeader">
          <div className="wModalTitle">{title}</div>
          <button className="wIconBtn" onClick={onClose} type="button">
            <X size={18} />
          </button>
        </div>
        <div className="wModalBody">{children}</div>
      </div>
    </div>
  );
}

export default function WhitelistPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  // modal
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("add"); // add | edit
  const [editRow, setEditRow] = useState(null);

  // form
  const [name, setName] = useState("");
  const [vehicleNumber, setVehicleNumber] = useState("");
  const [vehicleType, setVehicleType] = useState("Car");
  const [purpose, setPurpose] = useState("");
  const [fromDate, setFromDate] = useState(today());
  const [toDate, setToDate] = useState(today());

  // list filter
  const [search, setSearch] = useState("");

  // sorting
  const [sortKey, setSortKey] = useState("name");
  const [sortDir, setSortDir] = useState("asc"); // asc | desc

  // pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const load = async () => {
    setLoading(true);
    setErr("");
    try {
      const data = await listWhitelist();
      setRows(Array.isArray(data) ? data : []);
    } catch (e) {
      setRows([]);
      setErr(e?.message || "Failed to load whitelist");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    setPage(1);
  }, [search]);

  const SORTABLE = {
    name: (r) => String(r?.name || "").toLowerCase(),
    vehicle_number: (r) => String(r?.vehicle_number || "").toLowerCase(),
    vehicle_type: (r) => String(r?.vehicle_type || "").toLowerCase(),
    purpose: (r) => String(r?.purpose || "").toLowerCase(),
    from_date: (r) => String(r?.from_date || ""),
    to_date: (r) => String(r?.to_date || ""),
    status: (r) => String(r?.status || "").toLowerCase(),
  };

  const onSort = (key) => {
    setPage(1);
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const SortIcon = ({ col }) => {
    if (sortKey !== col) return <ArrowUpDown size={14} className="wSortIdle" />;
    return sortDir === "asc" ? (
      <ChevronUp size={16} className="wSortOn" />
    ) : (
      <ChevronDown size={16} className="wSortOn" />
    );
  };

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => {
      return (
        String(r?.vehicle_number || "")
          .toLowerCase()
          .includes(q) ||
        String(r?.name || "")
          .toLowerCase()
          .includes(q) ||
        String(r?.vehicle_type || "")
          .toLowerCase()
          .includes(q) ||
        String(r?.purpose || "")
          .toLowerCase()
          .includes(q) ||
        String(r?.status || "")
          .toLowerCase()
          .includes(q)
      );
    });
  }, [rows, search]);

  const filteredSorted = useMemo(() => {
    const getter = SORTABLE[sortKey] || SORTABLE.name;
    const dir = sortDir === "asc" ? 1 : -1;

    return [...filtered].sort((a, b) => {
      const va = getter(a);
      const vb = getter(b);
      if (va < vb) return -1 * dir;
      if (va > vb) return 1 * dir;
      return 0;
    });
  }, [filtered, sortKey, sortDir]);

  const total = filteredSorted.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(page, totalPages);

  const pageRows = useMemo(() => {
    const start = (safePage - 1) * pageSize;
    return filteredSorted.slice(start, start + pageSize);
  }, [filteredSorted, safePage, pageSize]);

  useEffect(() => {
    if (page !== safePage) setPage(safePage);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [totalPages]);

  const resetForm = () => {
    setName("");
    setVehicleNumber("");
    setVehicleType("Car");
    setPurpose("");
    setFromDate(today());
    setToDate(today());
  };

  const openAdd = () => {
    setErr("");
    setMode("add");
    setEditRow(null);
    resetForm();
    setOpen(true);
  };

  const openEdit = (row) => {
    setErr("");
    setMode("edit");
    setEditRow(row);

    setName(row?.name || "");
    setVehicleNumber(row?.vehicle_number || "");
    setVehicleType(row?.vehicle_type || "Car");
    setPurpose(row?.purpose || "");
    setFromDate(row?.from_date || today());
    setToDate(row?.to_date || row?.from_date || today());

    setOpen(true);
  };

  const closeModal = () => {
    setOpen(false);
    setEditRow(null);
    setErr("");
  };

  const save = async () => {
    setErr("");

    const vn = vehicleNumber.trim().toUpperCase();
    if (!name.trim()) return setErr("Name is required");
    if (!vn) return setErr("Vehicle number is required");
    if (!fromDate || !toDate) return setErr("From/To dates are required");
    if (toDate < fromDate) return setErr("to_date must be >= from_date");

    try {
      setLoading(true);

      const basePayload = {
        name: name.trim(),
        vehicle_number: vn,
        vehicle_type: vehicleType,
        purpose: purpose.trim() || null,
        from_date: fromDate,
        to_date: toDate,
      };

      if (mode === "add") {
        await createWhitelist({ ...basePayload, status: "approved" });
      } else {
        await updateWhitelist(editRow.id, basePayload);
      }

      closeModal();
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Save failed");
    } finally {
      setLoading(false);
    }
  };

  const toggle = async (row) => {
    setErr("");
    try {
      setLoading(true);
      const next = row.status === "approved" ? "blocked" : "approved";
      await setWhitelistStatus(row.id, next);
      await load();
    } catch (e) {
      setErr(e?.message || "Update failed");
    } finally {
      setLoading(false);
    }
  };

  const quickExtend7Days = async (row) => {
    setErr("");
    try {
      setLoading(true);
      const d = new Date(row.to_date);
      d.setDate(d.getDate() + 7);
      const nextTo = toInputDate(d);
      await updateWhitelist(row.id, { to_date: nextTo });
      await load();
    } catch (e) {
      setErr(e?.message || "Extend failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="wPage">
      <div className="wPanel">
        <div className="wPanelHeader">
          <div>
            <div className="wTitle">Whitelist Management</div>
            <div className="wSub">
              Add vehicles + update status live from security
            </div>
          </div>

          <div className="wHeaderRight">
            <button
              className="wBtn wBtnGhost"
              onClick={load}
              disabled={loading}
              title="Refresh"
              type="button"
            >
              <RefreshCw size={16} className={loading ? "wSpin" : ""} />
              Refresh
            </button>

            <button
              className="wBtn wBtnPrimary"
              type="button"
              onClick={openAdd}
              disabled={loading}
            >
              <Plus size={16} />
              Add Vehicle
            </button>
          </div>
        </div>

        <div className="wSearchRow">
          <div className="wSearch">
            <Search size={16} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name / vehicle / type / status..."
            />
          </div>
          <div className="wCount">
            Total: <b>{total}</b>
          </div>
        </div>

        {err ? <div className="wTopError">{err}</div> : null}

        {/* TABLE */}
        <div className="wTableWrap">
          <table className="wTable">
            <thead>
              <tr>
                <th style={{ width: 180 }}>
                  <button
                    className="wThBtn"
                    onClick={() => onSort("name")}
                    type="button"
                  >
                    Name <SortIcon col="name" />
                  </button>
                </th>

                <th style={{ width: 140 }}>
                  <button
                    className="wThBtn"
                    onClick={() => onSort("vehicle_number")}
                    type="button"
                  >
                    Vehicle No <SortIcon col="vehicle_number" />
                  </button>
                </th>

                <th style={{ width: 120 }}>
                  <button
                    className="wThBtn"
                    onClick={() => onSort("vehicle_type")}
                    type="button"
                  >
                    Type <SortIcon col="vehicle_type" />
                  </button>
                </th>

                <th>
                  <button
                    className="wThBtn"
                    onClick={() => onSort("purpose")}
                    type="button"
                  >
                    Purpose <SortIcon col="purpose" />
                  </button>
                </th>

                <th style={{ width: 130, textAlign: "center" }}>
                  <button
                    className="wThBtn center"
                    onClick={() => onSort("from_date")}
                    type="button"
                  >
                    From <SortIcon col="from_date" />
                  </button>
                </th>

                <th style={{ width: 130, textAlign: "center" }}>
                  <button
                    className="wThBtn center"
                    onClick={() => onSort("to_date")}
                    type="button"
                  >
                    To <SortIcon col="to_date" />
                  </button>
                </th>

                {/* ✅ REMOVED STATUS COLUMN */}

                <th style={{ width: 280, textAlign: "center" }}>Actions</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td className="wEmptyRow" colSpan={7}>
                    Loading...
                  </td>
                </tr>
              ) : pageRows.length === 0 ? (
                <tr>
                  <td className="wEmptyRow" colSpan={7}>
                    No whitelist records
                  </td>
                </tr>
              ) : (
                pageRows.map((r) => (
                  <tr key={r.id}>
                    <td className="wStrong">{r.name}</td>
                    <td className="wMono">{r.vehicle_number}</td>
                    <td>{r.vehicle_type}</td>
                    <td className="wMuted">{r.purpose || "-"}</td>
                    <td style={{ textAlign: "center" }}>{r.from_date}</td>
                    <td style={{ textAlign: "center" }}>{r.to_date}</td>

                    {/* ✅ REMOVED STATUS CELL */}

                    <td style={{ textAlign: "center" }}>
                      <div className="wToggleRow">
                        <button
                          className={`wToggle ${r.status === "approved" ? "on" : "off"}`}
                          onClick={() => toggle(r)}
                          type="button"
                          title="Toggle Approved/Blocked"
                        >
                          <span className="dot" />
                          <span className="txt">
                            {r.status === "approved" ? "Approved" : "Blocked"}
                          </span>
                        </button>

                        <button
                          className="wBtnMini"
                          type="button"
                          onClick={() => quickExtend7Days(r)}
                          title="Extend +7 days"
                        >
                          +7d
                        </button>

                        <button
                          className="wIconBtnMini"
                          type="button"
                          onClick={() => openEdit(r)}
                          title="Edit"
                        >
                          <Edit2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="wPager">
          <div className="wPagerLeft">
            Rows:
            <select
              className="wPagerSelect"
              value={pageSize}
              onChange={(e) => {
                setPage(1);
                setPageSize(Number(e.target.value));
              }}
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
            <span className="wPagerMeta">
              Showing <b>{total === 0 ? 0 : (safePage - 1) * pageSize + 1}</b>-
              <b>{Math.min(safePage * pageSize, total)}</b> of <b>{total}</b>
            </span>
          </div>

          <div className="wPagerRight">
            <button
              className="wBtnMini"
              onClick={() => setPage(1)}
              disabled={safePage <= 1}
              type="button"
            >
              First
            </button>
            <button
              className="wBtnMini"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={safePage <= 1}
              type="button"
            >
              Prev
            </button>

            <div className="wPagerPage">
              Page <b>{safePage}</b> / <b>{totalPages}</b>
            </div>

            <button
              className="wBtnMini"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={safePage >= totalPages}
              type="button"
            >
              Next
            </button>
            <button
              className="wBtnMini"
              onClick={() => setPage(totalPages)}
              disabled={safePage >= totalPages}
              type="button"
            >
              Last
            </button>
          </div>
        </div>

        <div className="wHint">
          Tip: Approved = whitelisted, Blocked = blacklisted. Validity is
          checked using from_date/to_date.
        </div>
      </div>

      <Modal
        open={open}
        title={
          mode === "add" ? "Add Whitelist Vehicle" : "Edit Whitelist Vehicle"
        }
        onClose={() => {
          if (!loading) closeModal();
        }}
      >
        <div className="wFormGrid wFormGridModal">
          <div className="wField">
            <div className="wLabel">Name</div>
            <div className="wInputIcon">
              <User size={16} />
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Vendor Driver"
              />
            </div>
          </div>

          <div className="wField">
            <div className="wLabel">Vehicle Number</div>
            <div className="wInputIcon">
              <Car size={16} />
              <input
                value={vehicleNumber}
                onChange={(e) => setVehicleNumber(e.target.value)}
                placeholder="e.g., TN48SD9156"
              />
            </div>
          </div>

          <div className="wField">
            <div className="wLabel">Vehicle Type</div>
            <div className="wInputIcon">
              <ClipboardList size={16} />
              <select
                className="wSelect"
                value={vehicleType}
                onChange={(e) => setVehicleType(e.target.value)}
              >
                <option value="Car">Car</option>
                <option value="Bike">Bike</option>
                <option value="Truck">Truck</option>
                <option value="Van">Van</option>
                <option value="Bus">Bus</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div className="wField">
            <div className="wLabel">Purpose (optional)</div>
            <div className="wInputIcon">
              <ShieldCheck size={16} />
              <input
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="e.g., Delivery / Staff / Visitor"
              />
            </div>
          </div>

          <div className="wField">
            <div className="wLabel">Valid From</div>
            <div className="wInputIcon">
              <CalendarDays size={16} />
              <input
                type="date"
                value={fromDate}
                onChange={(e) => {
                  const v = e.target.value || today();
                  setFromDate(v);
                  if (toDate < v) setToDate(v);
                }}
              />
            </div>
          </div>

          <div className="wField">
            <div className="wLabel">Valid To</div>
            <div className="wInputIcon">
              <CalendarDays size={16} />
              <input
                type="date"
                min={fromDate}
                value={toDate}
                onChange={(e) => setToDate(e.target.value || fromDate)}
              />
            </div>
          </div>
        </div>

        {err ? (
          <div className="wError" style={{ marginTop: 12 }}>
            {err}
          </div>
        ) : null}

        <div className="wModalActions">
          <button
            className="wBtn"
            type="button"
            onClick={closeModal}
            disabled={loading}
          >
            Cancel
          </button>

          <button
            className="wBtn wBtnPrimary"
            type="button"
            onClick={save}
            disabled={loading}
          >
            <Plus size={16} />
            {mode === "add" ? "Add Vehicle" : "Save Changes"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
