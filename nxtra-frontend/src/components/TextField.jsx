import React from "react";
import Icon from "./Icon";

export default function TextField({
  icon,
  rightIcon,
  onRightIconClick,
  ...props
}) {
  return (
    <div style={styles.wrap}>
      {/* Left Icon */}
      <div style={styles.left}>
        <Icon name={icon} size={18} />
      </div>

      {/* Input */}
      <input style={styles.input} {...props} />

      {/* Right Icon Slot (always reserved) */}
      <div style={styles.rightSlot}>
        {rightIcon ? (
          <button
            type="button"
            style={styles.rightBtn}
            onClick={onRightIconClick}
            aria-label="toggle password visibility"
          >
            <Icon name={rightIcon} size={18} />
          </button>
        ) : null}
      </div>
    </div>
  );
}

const FIELD_H = 48; // ✅ fixed height for ALL fields

const styles = {
  wrap: {
    width: "100%",
    height: FIELD_H, // ✅ enforce equal height
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "0 14px", // ✅ vertical padding removed (height controls it)
    borderRadius: 14,
    background: "var(--field)",
    border: "1px solid var(--field-border)",
  },

  left: {
    width: 30,
    height: "100%", // ✅ same height as field
    display: "grid",
    placeItems: "center",
    opacity: 0.9,
    flex: "0 0 auto",
  },

  input: {
    flex: 1,
    height: "100%", // ✅ match fixed field height
    outline: "none",
    border: "none",
    background: "transparent",
    color: "var(--text)",
    fontSize: 16,
    lineHeight: `${FIELD_H}px`, // ✅ prevents vertical jitter
  },

  rightSlot: {
    width: 42,
    height: "100%",
    display: "grid",
    placeItems: "center",
    flex: "0 0 auto",
  },

  rightBtn: {
    width: 34,
    height: 34, // ✅ fixed button size
    display: "grid",
    placeItems: "center",
    border: "none",
    background: "transparent",
    cursor: "pointer",
    opacity: 0.9,
    padding: 0, // ✅ remove default button padding
  },
};
