import React, { useEffect } from "react";

export default function Toast({ type = "success", message = "", onClose }) {
  useEffect(() => {
    if (!message) return;
    const t = setTimeout(() => onClose?.(), 2500); // ✅ 2.5 seconds
    return () => clearTimeout(t);
  }, [message, onClose]);

  if (!message) return null;

  const bg = type === "error" ? "rgba(227,27,35,0.14)" : "rgba(34,197,94,0.16)";
  const border =
    type === "error" ? "rgba(227,27,35,0.35)" : "rgba(34,197,94,0.35)";

  return (
    <div
      style={{
        position: "fixed",
        top: 18,
        right: 18,
        zIndex: 9999,
        padding: "12px 14px",
        borderRadius: 14,
        background: bg,
        border: `1px solid ${border}`,
        color: "rgba(255,255,255,0.95)",
        fontWeight: 800,
        backdropFilter: "blur(8px)",
      }}
    >
      {message}
    </div>
  );
}
