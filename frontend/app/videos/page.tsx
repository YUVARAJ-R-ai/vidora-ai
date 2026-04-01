"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { getMyVideos, getToken } from "../lib/api";
import { useAuth } from "../lib/auth";

interface VideoItem {
  id: string;
  filename: string;
  status: string;
  created_at: string;
}

const STATUS_CONFIG: Record<string, { emoji: string; color: string; label: string }> = {
  pending: { emoji: "⏳", color: "#f59e0b", label: "Pending" },
  processing: { emoji: "⚙️", color: "#3b82f6", label: "Processing" },
  done: { emoji: "✅", color: "#10b981", label: "Complete" },
  failed: { emoji: "❌", color: "#ef4444", label: "Failed" },
};

export default function VideosPage() {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { logout } = useAuth();

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }

    const fetchVideos = async () => {
      try {
        const data = await getMyVideos();
        setVideos(data);
      } catch (err) {
        console.error("Failed to fetch videos", err);
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, []);

  return (
    <div className="videos-page">
      {/* Top bar */}
      <div className="top-bar">
        <div className="top-bar-brand" onClick={() => router.push("/")} style={{ cursor: "pointer" }}>
          🎬 <span className="title-accent">Vidora AI</span>
        </div>
        <div className="top-bar-actions">
          <button className="nav-link" onClick={() => router.push("/")}>
            Upload
          </button>
          <button className="nav-link logout-btn" onClick={logout}>
            Logout
          </button>
        </div>
      </div>

      <div className="videos-content">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="title" style={{ fontSize: "2.5rem" }}>
            My <span className="title-accent">Videos</span>
          </h1>
          <p style={{ color: "var(--text-muted)", marginBottom: "2rem" }}>
            {videos.length} video{videos.length !== 1 ? "s" : ""} analyzed
          </p>
        </motion.div>

        {loading ? (
          <div className="videos-grid">
            {[1, 2, 3].map((i) => (
              <div key={i} className="video-card glass-panel skeleton" />
            ))}
          </div>
        ) : videos.length === 0 ? (
          <motion.div
            className="empty-state"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <motion.div
              animate={{ y: [0, -15, 0] }}
              transition={{ repeat: Infinity, duration: 3 }}
              style={{ fontSize: "4rem" }}
            >
              📹
            </motion.div>
            <h2 style={{ margin: "1rem 0 0.5rem" }}>No videos yet</h2>
            <p style={{ color: "var(--text-muted)" }}>
              Upload your first video to get started
            </p>
            <button className="upload-btn" onClick={() => router.push("/")} style={{ marginTop: "1.5rem" }}>
              Upload Video ✨
            </button>
          </motion.div>
        ) : (
          <div className="videos-grid">
            {videos.map((v, i) => {
              const config = STATUS_CONFIG[v.status] || STATUS_CONFIG.pending;
              const date = new Date(v.created_at);
              return (
                <motion.div
                  key={v.id}
                  className="video-card glass-panel"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                  onClick={() => router.push(`/video/${v.id}`)}
                  whileHover={{ scale: 1.03, y: -4 }}
                >
                  <div className="video-card-icon">🎬</div>
                  <div className="video-card-info">
                    <h3 className="video-card-name">{v.filename}</h3>
                    <p className="video-card-date">
                      {date.toLocaleDateString()} · {date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                  <div
                    className="video-card-status"
                    style={{ color: config.color }}
                  >
                    {config.emoji} {config.label}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
