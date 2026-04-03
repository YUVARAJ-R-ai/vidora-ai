"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { uploadVideo, getMyVideos, getToken, deleteVideo } from "./lib/api";
import { useAuth } from "./lib/auth";

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
  cancelled: { emoji: "🚫", color: "#ef4444", label: "Cancelled" },
};

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [yoloModel, setYoloModel] = useState<string>("yolov8n");
  
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loadingVideos, setLoadingVideos] = useState(true);

  const router = useRouter();
  const { isAuthenticated, logout } = useAuth();

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
        setLoadingVideos(false);
      }
    };
    fetchVideos();
  }, [router]);

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
      const data = await uploadVideo(file, yoloModel);
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
    <div className="dashboard-main-page" style={{ minHeight: "100vh", paddingTop: "5rem", paddingBottom: "4rem" }}>
      {/* Top bar */}
      <div className="top-bar">
        <div className="top-bar-brand">
          🎬 <span className="title-accent">Vidora AI</span>
        </div>
        <div className="top-bar-actions">
          {isAuthenticated && (
            <button className="nav-link logout-btn" onClick={logout}>
              Logout
            </button>
          )}
        </div>
      </div>

      <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "0 2rem" }}>
        {/* Upload Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          style={{ marginBottom: "4rem" }}
        >
          <div style={{ textAlign: "center", marginBottom: "2rem" }}>
            <h1 className="title" style={{ fontSize: "2.5rem" }}>
              Welcome to your <span className="title-accent">Dashboard</span>
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: "1.1rem" }}>
              Upload new media or review your previous multi-modal analyses.
            </p>
          </div>

          <motion.div
            className="upload-box glass-panel"
            whileHover={{ scale: 1.01 }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            style={{ padding: "3rem 2rem", maxWidth: "800px", margin: "0 auto" }}
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
                animate={{ y: [0, -5, 0] }}
                transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
                style={{ fontSize: "3rem", marginBottom: "0.5rem" }}
              >
                {file ? "🎬" : "☁️"}
              </motion.div>

              <h2 style={{ margin: 0, fontSize: "1.4rem", fontWeight: 600 }}>
                {file ? (
                  <span className="title-accent">{file.name}</span>
                ) : (
                  "Drag & Drop Video to Analyze"
                )}
              </h2>
              <p
                style={{
                  color: "var(--text-muted)",
                  margin: 0,
                  fontSize: "0.95rem",
                }}
              >
                {file
                  ? `Ready to process ${(file.size / 1024 / 1024).toFixed(1)} MB`
                  : "Or click to browse files (MP4, MOV, MKV)"}
              </p>
            </label>
          </motion.div>

          <AnimatePresence>
            {file && (
              <div style={{ textAlign: "center" }}>
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  style={{ display: "flex", justifyContent: "center", gap: "2rem", marginTop: "1.5rem" }}
                >
                   <label style={{display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontSize: "0.95rem"}}>
                       <input type="radio" name="model" checked={yoloModel === 'yolov8n'} onChange={() => setYoloModel('yolov8n')} style={{ accentColor: "var(--accent)" }} />
                       <span style={{color: yoloModel === 'yolov8n' ? "var(--accent)" : "var(--text-muted)", fontWeight: yoloModel === 'yolov8n' ? 600 : 400}}>⚡ Fast (YOLOv8n)</span>
                   </label>
                   <label style={{display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontSize: "0.95rem"}}>
                       <input type="radio" name="model" checked={yoloModel === 'yolov8s'} onChange={() => setYoloModel('yolov8s')} style={{ accentColor: "var(--accent)" }} />
                       <span style={{color: yoloModel === 'yolov8s' ? "var(--accent)" : "var(--text-muted)", fontWeight: yoloModel === 'yolov8s' ? 600 : 400}}>🎯 Studio (YOLOv8s)</span>
                   </label>
                </motion.div>
                <motion.button
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 15 }}
                  className="upload-btn"
                  onClick={handleUpload}
                  disabled={uploading}
                  style={{ marginTop: "1.5rem", padding: "0.8rem 2.5rem" }}
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
              </div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* My Videos Section */}
        <motion.div
           initial={{ opacity: 0 }}
           animate={{ opacity: 1 }}
           transition={{ duration: 0.8, delay: 0.2 }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", borderBottom: "1px solid var(--border)", paddingBottom: "1rem", marginBottom: "1.5rem" }}>
            <h2 className="title" style={{ fontSize: "1.8rem", margin: 0 }}>Recent <span className="title-accent">Analyses</span></h2>
            <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>{videos.length} videos</span>
          </div>

          {loadingVideos ? (
            <div className="videos-grid">
              {[1, 2, 3].map((i) => (
                <div key={i} className="video-card glass-panel skeleton" style={{ height: "90px" }} />
              ))}
            </div>
          ) : videos.length === 0 ? (
            <div className="empty-state glass-panel" style={{ padding: "3rem", border: "1px dashed var(--border)", background: "transparent", color: "var(--text-muted)" }}>
              No videos processed yet. Upload your first one above!
            </div>
          ) : (
            <div className="videos-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))", gap: "1rem" }}>
              {videos.map((v, i) => {
                const config = STATUS_CONFIG[v.status] || STATUS_CONFIG.pending;
                const date = new Date(v.created_at);
                return (
                  <motion.div
                    key={v.id}
                    className="video-card glass-panel"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    onClick={() => router.push(`/video/${v.id}`)}
                    whileHover={{ scale: 1.02, y: -2 }}
                    style={{ background: "rgba(20,20,28,0.6)", position: "relative" }}
                  >
                   <button 
                     onClick={async (e) => {
                       e.stopPropagation();
                       if (confirm("Delete this video analysis permanently?")) {
                         try {
                           await deleteVideo(v.id);
                           setVideos((prev) => prev.filter(vid => vid.id !== v.id));
                         } catch(err) {
                           alert("Failed to delete video. Is backend running?");
                         }
                       }
                     }}
                     style={{ position: "absolute", top: "12px", right: "12px", background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: "50%", width: "32px", height: "32px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", transition: "all 0.2s z-index 10" }}
                     onMouseOver={(e) => { e.currentTarget.style.background = "rgba(239, 68, 68, 0.4)"; e.currentTarget.style.transform = "scale(1.1)"; }}
                     onMouseOut={(e) => { e.currentTarget.style.background = "rgba(239, 68, 68, 0.15)"; e.currentTarget.style.transform = "scale(1)"; }}
                     title="Delete Video"
                   >
                     🗑️
                   </button>
                    <div className="video-card-icon" style={{ fontSize: "1.5rem" }}>🎬</div>
                    <div className="video-card-info">
                      <h3 className="video-card-name" style={{ fontSize: "0.95rem" }}>{v.filename}</h3>
                      <p className="video-card-date" style={{ fontSize: "0.75rem" }}>
                        {date.toLocaleDateString()} · {date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </p>
                    </div>
                    <div
                      className="video-card-status"
                      style={{ color: config.color, fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "0.3rem" }}
                    >
                      {config.emoji} {config.label}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
