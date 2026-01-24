import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import bg from "../assets/nxtra-bg.png";
import logo from "../assets/nxtra-logo.jpg";
import TextField from "../components/TextField";
import Toast from "../components/Toast";

import { loginApi, registerApi } from "../api/auth";
import { saveAuth } from "../utils/storage";

export default function AuthPage({ defaultMode = "login" }) {
  const navigate = useNavigate();

  // mode comes from route component
  const mode = defaultMode;
  const isLogin = mode === "login";

  const [showPw, setShowPw] = useState(false);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [toast, setToast] = useState({ type: "success", message: "" });

  async function onSubmit(e) {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      const msg = "Email and password are required.";
      setError(msg);
      setToast({ type: "error", message: msg });
      return;
    }

    if (!isLogin && !fullName.trim()) {
      const msg = "Full name is required for registration.";
      setError(msg);
      setToast({ type: "error", message: msg });
      return;
    }

    try {
      setLoading(true);

      if (isLogin) {
        const data = await loginApi({ email, password });
        const token = data?.access_token || data?.token || data?.jwt || null;

        saveAuth({ token, user: data?.user || { email } });

        setToast({ type: "success", message: "Login successful ✅" });

        // go to dashboard alerts
        setTimeout(() => navigate("/dashboard-alert"), 1800);
      } else {
        await registerApi({ full_name: fullName, email, password });

        setToast({
          type: "success",
          message: "Registration successful ✅ Please login",
        });

        setTimeout(() => navigate("/login"), 800);
      }
    } catch (err) {
      const msg = err?.message || "Something went wrong";
      setError(msg);
      setToast({ type: "error", message: msg });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.root(bg)}>
      <div style={styles.overlay} />

      <Toast
        type={toast.type}
        message={toast.message}
        onClose={() => setToast({ type: "success", message: "" })}
      />

      <div style={styles.card}>
        <div style={styles.brand}>
          <img src={logo} alt="Nxtra by Airtel" style={styles.logo} />
          <div style={styles.subtitle}>
            {isLogin ? "Sign in to continue" : "Create your account"}
          </div>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={onSubmit}>
          {!isLogin && (
            <>
              <TextField
                placeholder="Full name"
                icon="user"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
              <div style={{ height: 12 }} />
            </>
          )}

          <TextField
            placeholder="Email address"
            icon="mail"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <div style={{ height: 12 }} />

          <TextField
            placeholder="Password"
            icon="lock"
            type={showPw ? "text" : "password"}
            rightIcon={showPw ? "eyeOff" : "eye"}
            onRightIconClick={() => setShowPw((s) => !s)}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <div style={styles.row}>
            <label style={styles.checkboxRow}>
              <input type="checkbox" style={styles.checkbox} />
              <span style={styles.muted}>Remember me</span>
            </label>

            {isLogin ? (
              <a href="#" style={styles.link}>
                Forgot password?
              </a>
            ) : (
              <span />
            )}
          </div>

          <button style={styles.loginBtn} disabled={loading}>
            {loading
              ? isLogin
                ? "Logging in..."
                : "Creating..."
              : isLogin
                ? "Log In"
                : "Register"}
          </button>
        </form>

        <div style={styles.switchRow}>
          <span style={styles.muted}>
            {isLogin ? "New here?" : "Already have an account?"}
          </span>

          <button
            type="button"
            style={styles.switchBtn}
            onClick={() => navigate(isLogin ? "/register" : "/login")}
          >
            {isLogin ? "Create account" : "Back to login"}
          </button>
        </div>

        <div style={styles.footer}>
          <div style={styles.footerText}>
            © 2024 Nxtra by Airtel. All rights reserved.
          </div>
          <div style={styles.footerLinks}>
            <a href="#" style={styles.footerLink}>
              Privacy Policy
            </a>
            <span style={styles.dot}>•</span>
            <a href="#" style={styles.footerLink}>
              Terms of Service
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  root: (bgUrl) => ({
    minHeight: "100vh",
    display: "grid",
    placeItems: "center",
    backgroundImage: `url(${bgUrl})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    position: "relative",
    padding: 24,
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial',
  }),

  overlay: {
    position: "absolute",
    inset: 0,
    background: "linear-gradient(180deg, rgba(0,0,0,0.20), rgba(0,0,0,0.35))",
    pointerEvents: "none",
  },

  card: {
    width: "min(560px, 92vw)",
    borderRadius: 22,
    padding: "34px 34px 26px",
    background: "var(--glass)",
    border: "1px solid var(--glass-border)",
    boxShadow: "var(--shadow)",
    backdropFilter: "blur(14px)",
    WebkitBackdropFilter: "blur(14px)",
    position: "relative",
  },

  brand: { textAlign: "center", marginBottom: 14 },
  logo: { height: 70, objectFit: "contain" },

  subtitle: {
    marginTop: 10,
    color: "rgba(255,255,255,0.75)",
    fontSize: 14,
  },

  error: {
    marginTop: 10,
    marginBottom: 12,
    padding: "10px 12px",
    borderRadius: 12,
    background: "rgba(227,27,35,0.12)",
    border: "1px solid rgba(227,27,35,0.25)",
    color: "rgba(255,255,255,0.92)",
    fontSize: 14,
  },

  row: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 14,
    marginBottom: 18,
  },

  checkboxRow: { display: "flex", gap: 10, alignItems: "center" },
  checkbox: { width: 16, height: 16, accentColor: "var(--nxtra-red)" },

  muted: { color: "var(--muted)", fontSize: 14 },
  link: { color: "var(--muted)", fontSize: 14, textDecoration: "none" },

  loginBtn: {
    width: "100%",
    border: "none",
    borderRadius: 12,
    padding: "14px 16px",
    fontSize: 18,
    fontWeight: 700,
    color: "white",
    cursor: "pointer",
    background:
      "linear-gradient(180deg, var(--nxtra-red), var(--nxtra-red-dark))",
    boxShadow: "0 12px 30px rgba(227, 27, 35, 0.28)",
  },

  switchRow: {
    marginTop: 14,
    display: "flex",
    justifyContent: "center",
    gap: 10,
  },

  switchBtn: {
    border: "none",
    background: "transparent",
    cursor: "pointer",
    color: "white",
    fontWeight: 700,
    textDecoration: "underline",
  },

  footer: { marginTop: 18, textAlign: "center" },
  footerText: { color: "rgba(255,255,255,0.7)", fontSize: 12 },

  footerLinks: {
    marginTop: 8,
    display: "flex",
    gap: 10,
    justifyContent: "center",
  },

  footerLink: { color: "rgba(255,255,255,0.72)", fontSize: 12 },
  dot: { color: "rgba(255,255,255,0.55)", fontSize: 12 },
};
