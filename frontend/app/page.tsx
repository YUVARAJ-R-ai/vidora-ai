"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { uploadVideo, getToken } from "./lib/api";
import { useAuth } from "./lib/auth";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const router = useRouter();
  const { isAuthenticated, userEmail, logout } = useAuth();

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
    }
  }, []);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);

    try {
      const data = await uploadVideo(file);
      if (data.video_id) {
        setTimeout(() => {
          router.push(`/video/${data.video_id}`);
        }, 600);
      }
    } catch (error) {
      console.error("Upload failed", error);
      alert("Failed to upload. Make sure the backend is running!");
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      {/* Top bar */}
      <div className="top-bar">
        <div className="top-bar-brand">
          🎬 <span className="title-accent">Vidora AI</span>
        </div>
        <div className="top-bar-actions">
          <button className="nav-link" onClick={() => router.push("/videos")}>
            My Videos
          </button>
          {isAuthenticated && (
            <button className="nav-link logout-btn" onClick={logout}>
              Logout
            </button>
          )}
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <h1 className="title">
          Know Your Video <br />
          <span className="title-accent">Instantly.</span>
        </h1>
        <p
          style={{
            color: "var(--text-muted)",
            fontSize: "1.25rem",
            margin: "1.5rem 0 3rem 0",
            maxWidth: "600px",
            lineHeight: 1.6,
          }}
        >
          Upload your media and let our multi-modal AI detect emotions, transcribe
          speech, caption scenes, and answer any questions you have.
        </p>
      </motion.div>

      <motion.div
        className="upload-box glass-panel"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept="video/*"
          onChange={handleFile}
          style={{ display: "none" }}
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          style={{
            cursor: "pointer",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "1rem",
          }}
        >
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
            style={{ fontSize: "4.5rem", marginBottom: "1rem" }}
          >
            {file ? "🎬" : "☁️"}
          </motion.div>

          <h2 style={{ margin: 0, fontSize: "1.75rem", fontWeight: 600 }}>
            {file ? (
              <span className="title-accent">{file.name}</span>
            ) : (
              "Drag & Drop Video Here"
            )}
          </h2>
          <p
            style={{
              color: "var(--text-muted)",
              margin: 0,
              fontSize: "1.1rem",
            }}
          >
            {file
              ? `Ready to analyze ${(file.size / 1024 / 1024).toFixed(1)} MB`
              : "Or click to browse files (MP4, MOV, MKV)"}
          </p>
        </label>
      </motion.div>

      <AnimatePresence>
        {file && (
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="upload-btn"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? (
              <div className="dots-loader" style={{ padding: "0 1.5rem" }}>
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            ) : (
              "Analyze Intelligence ✨"
            )}
          </motion.button>
        )}
      </AnimatePresence>

      {/* Quick link */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        style={{
          marginTop: "2rem",
          color: "var(--text-muted)",
          fontSize: "0.95rem",
        }}
      >
        Or{" "}
        <span
          className="title-accent"
          style={{ cursor: "pointer" }}
          onClick={() => router.push("/videos")}
        >
          view your previous analyses →
        </span>
      </motion.p>
    </div>
  );
}
