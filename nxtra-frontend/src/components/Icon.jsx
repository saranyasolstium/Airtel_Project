import React from "react";

export default function Icon({ name, size = 18 }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg",
    style: { color: "rgba(255,255,255,0.85)" },
  };

  switch (name) {
    case "mail":
      return (
        <svg {...common}>
          <path d="M4 6h16v12H4V6Z" stroke="currentColor" strokeWidth="1.8" />
          <path
            d="m4 7 8 6 8-6"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "lock":
      return (
        <svg {...common}>
          <path
            d="M7 11V8.8A5 5 0 0 1 12 4a5 5 0 0 1 5 4.8V11"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M7 11h10v9H7v-9Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "eye":
      return (
        <svg {...common}>
          <path
            d="M2.5 12s3.5-7 9.5-7 9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7Z"
            stroke="currentColor"
            strokeWidth="1.8"
          />
          <path
            d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
            stroke="currentColor"
            strokeWidth="1.8"
          />
        </svg>
      );
    case "eyeOff":
      return (
        <svg {...common}>
          <path
            d="M3 3l18 18"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M2.5 12s3.5-7 9.5-7c2 0 3.7.6 5.1 1.5M21.5 12s-3.5 7-9.5 7c-2 0-3.7-.6-5.1-1.5"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M10.5 10.5a2.5 2.5 0 0 0 3 3"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      );
    case "user":
      return (
        <svg {...common}>
          <path
            d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Z"
            stroke="currentColor"
            strokeWidth="1.8"
          />
          <path
            d="M4.5 20c1.7-3.3 5-5 7.5-5s5.8 1.7 7.5 5"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      );

    default:
      return null;
  }
}
