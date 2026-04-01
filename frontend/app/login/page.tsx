"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { loginUser, registerUser } from "../lib/api";
import { useAuth } from "../lib/auth";

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  const { refreshAuth } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isLogin) {
        await loginUser(email, password);
        refreshAuth();
        router.push("/");
      } else {
        await registerUser(email, password);
        // Auto-login after registration
        await loginUser(email, password);
        refreshAuth();
        router.push("/");
      }
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      {/* Animated background orbs */}
      <div className="bg-orb orb-1" />
      <div className="bg-orb orb-2" />
      <div className="bg-orb orb-3" />

      <motion.div
        className="login-card glass-panel"
        initial={{ opacity: 0, y: 40, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        {/* Logo */}
        <div className="login-logo">
          <motion.span
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
            style={{ display: "inline-block", fontSize: "2.5rem" }}
          >
            🎬
          </motion.span>
          <h1 className="login-title">
            Vidora <span className="title-accent">AI</span>
          </h1>
          <p className="login-subtitle">Intelligent Video Analysis Platform</p>
        </div>

        {/* Mode Toggle */}
        <div className="auth-toggle">
          <button
            className={`toggle-btn ${isLogin ? "active" : ""}`}
            onClick={() => { setIsLogin(true); setError(""); }}
          >
            Sign In
          </button>
          <button
            className={`toggle-btn ${!isLogin ? "active" : ""}`}
            onClick={() => { setIsLogin(false); setError(""); }}
          >
            Register
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label className="input-label">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="login-input"
              required
            />
          </div>

          <div className="input-group">
            <label className="input-label">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="login-input"
              required
              minLength={6}
            />
          </div>

          <AnimatePresence>
            {error && (
              <motion.div
                className="login-error"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
              >
                ⚠️ {error}
              </motion.div>
            )}
          </AnimatePresence>

          <motion.button
            type="submit"
            className="login-submit"
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {loading ? (
              <div className="dots-loader">
                <span className="dot" /><span className="dot" /><span className="dot" />
              </div>
            ) : isLogin ? "Sign In →" : "Create Account →"}
          </motion.button>
        </form>
      </motion.div>
    </div>
  );
}
