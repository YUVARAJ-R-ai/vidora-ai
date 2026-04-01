"use client";

import { useEffect, useState, useRef, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import {
  getVideoResults,
  queryVideo,
  getToken,
  getVideoStreamUrl,
  cancelVideoProcessing,
} from "../../lib/api";
import { useAuth } from "../../lib/auth";

// ── Types ─────────────────────────────────────────────────────
interface DetectionData {
  id: string;
  timestamp_sec: number;
  objects_json: {
    objects?: string[];
    confidence?: number;
    emotions?: { face: number; emotion: string; confidence: number }[];
    scene_caption?: string;
    audio?: {
      transcript: string;
      is_loud: boolean;
      amplitude_db: number;
      end_sec: number;
    };
  };
}

interface ChatMsg {
  role: "user" | "ai";
  content: string;
  model?: string;
}

// ── Emotion config ────────────────────────────────────────────
const EMOTION_COLORS: Record<string, string> = {
  angry: "#ef4444",
  happy: "#facc15",
  sad: "#3b82f6",
  neutral: "#94a3b8",
  fear: "#a855f7",
  surprise: "#f97316",
  disgust: "#22c55e",
};

const EMOTION_EMOJIS: Record<string, string> = {
  angry: "😡",
  happy: "😊",
  sad: "😢",
  neutral: "😐",
  fear: "😨",
  surprise: "😮",
  disgust: "🤢",
};

const QUICK_QUERIES = [
  "What emotions are shown?",
  "Is anyone shouting?",
  "Describe what is happening",
  "Summarize the video",
];

// ── Component ─────────────────────────────────────────────────
export default function VideoDashboard() {
  const params = useParams();
  const router = useRouter();
  const videoId = params.id as string;

  const [status, setStatus] = useState("loading");
  const [detections, setDetections] = useState<DetectionData[]>([]);
  const [chatLog, setChatLog] = useState<ChatMsg[]>([]);
  const [query, setQuery] = useState("");
  const [querying, setQuerying] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { logout } = useAuth();

  // Auth guard
  useEffect(() => {
    if (!getToken()) router.push("/login");
  }, [router]);

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog, querying]);

  // Poll for live results during processing
  useEffect(() => {
    if (status === "done" || status === "failed" || status === "cancelled") {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const data = await getVideoResults(videoId);
        if (data) {
          setStatus(data.status);
          setDetections(data.detections || []);
          
          if (data.status === "done" && chatLog.length === 0) {
            setChatLog([
              {
                role: "ai",
                content: "✨ Multi-modal analysis complete! I've detected objects, emotions, scenes, and audio. Ask me anything about this video!",
              },
            ]);
            clearInterval(interval);
          } else if (data.status === "failed" || data.status === "cancelled") {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.error("Poll error", err);
      }
    }, 2000);

    // Initial fetch
    getVideoResults(videoId).then(data => {
        if(data) {
            setStatus(data.status);
            setDetections(data.detections || []);
            if(data.status === "done" && chatLog.length === 0) {
               setChatLog([{ role: "ai", content: "✨ Multi-modal analysis complete! Ask me anything about this video!" }]);
            }
        }
    });

    return () => clearInterval(interval);
  }, [videoId, status, chatLog.length]);


  // ── Derived data ────────────────────────────────────────────
  const visualDetections = useMemo(
    () => detections.filter((d) => !d.objects_json.audio),
    [detections]
  );

  const audioSegments = useMemo(
    () =>
      detections
        .filter((d) => d.objects_json.audio)
        .map((d) => ({
          start: d.timestamp_sec,
          end: d.objects_json.audio!.end_sec,
          text: d.objects_json.audio!.transcript,
          isLoud: d.objects_json.audio!.is_loud,
          db: d.objects_json.audio!.amplitude_db,
        })),
    [detections]
  );

  const emotionStats = useMemo(() => {
    const counts: Record<string, number> = {};
    visualDetections.forEach((d) => {
      d.objects_json.emotions?.forEach((e) => {
        counts[e.emotion] = (counts[e.emotion] || 0) + 1;
      });
    });
    return Object.entries(counts)
      .map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
        color: EMOTION_COLORS[name] || "#64748b",
        emoji: EMOTION_EMOJIS[name] || "❓",
      }))
      .sort((a, b) => b.value - a.value);
  }, [visualDetections]);

  // ── Handlers ────────────────────────────────────────────────
  const seekTo = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play().catch(() => {});
    }
  };

  const handleQuery = async (q?: string) => {
    const text = q || query;
    if (!text.trim()) return;
    setChatLog((prev) => [...prev, { role: "user", content: text }]);
    setQuery("");
    setQuerying(true);

    try {
      const data = await queryVideo(videoId, text);
      setChatLog((prev) => [
        ...prev,
        { role: "ai", content: data.response, model: data.model_used },
      ]);
    } catch {
      setChatLog((prev) => [
        ...prev,
        { role: "ai", content: "Sorry, I had trouble processing that. Try again?" },
      ]);
    } finally {
      setQuerying(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel the analysis?")) return;
    try {
      await cancelVideoProcessing(videoId);
      setStatus("cancelled");
      router.push("/");
    } catch (e) {
      console.error(e);
      alert("Failed to cancel.");
    }
  };

  const duration = videoRef.current?.duration || 100;

  // ── Loading State ───────────────────────────────────────────
  if (status === "loading") {
      return <div className="dashboard-page" style={{paddingTop: "5rem", textAlign: "center", color: "var(--text-muted)"}}>Loading data...</div>
  }

  // ── Cancelled / Failed State ────────────────────────────────
  if (status === "cancelled" || status === "failed") {
    return (
       <div className="dashboard-page" style={{ paddingTop: "8rem", textAlign: "center" }}>
          <div style={{fontSize: "4rem", marginBottom: "1rem"}}>🚫</div>
          <h2 className="title" style={{ fontSize: "2rem" }}>Analysis <span className="title-accent" style={{color: "#ef4444"}}>{status.toUpperCase()}</span></h2>
          <p style={{ color: "var(--text-muted)", marginTop: "1rem" }}>This video process was {status}. Partial data may be saved.</p>
          <button onClick={() => router.push("/")} className="upload-btn" style={{marginTop: "2rem"}}>Return to Dashboard</button>
       </div>
    );
  }

  // ── Processing State (Live UI) ──────────────────────────────
  if (status === "processing" || status === "pending") {
    return (
      <div className="dashboard-page flex flex-col" style={{ minHeight: "100vh", paddingBottom: "3rem" }}>
         <div className="top-bar">
          <div className="top-bar-brand" onClick={() => router.push("/")} style={{ cursor: "pointer" }}>
            🎬 <span className="title-accent">Vidora AI</span>
          </div>
          <div className="top-bar-actions">
            <button className="nav-link" onClick={() => router.push("/")}>Dashboard</button>
          </div>
        </div>
        
        <div style={{ maxWidth: "800px", margin: "5rem auto 3rem", textAlign: "center" }}>
          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 4, ease: "linear" }} style={{ fontSize: "3rem", display: "inline-block" }}>⚙️</motion.div>
          <h2 className="title" style={{ fontSize: "2rem", marginTop: "1rem" }}>Analyzing <span className="title-accent">Intelligence</span></h2>
          <p style={{ color: "var(--text-muted)" }}>Running DeepFace, Salesforce BLIP, and YOLOv8 models in the background...</p>
          
          <button onClick={handleCancel} className="upload-btn" style={{ background: "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)", marginTop: "2rem", boxShadow: "0 0 20px rgba(239, 68, 68, 0.3)" }}>
            🚫 Cancel Analysis
          </button>
        </div>

        <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "0 2rem", flexGrow: 1, width: "100%" }}>
           <h3 style={{ marginBottom: "1.5rem", color: "var(--text-muted)", display: "flex", gap: "10px", alignItems: "center", fontSize: "1.2rem", fontWeight: 500 }}>
             <div className="live-indicator" style={{width: "10px", height: "10px", background: "#ef4444", borderRadius: "50%", boxShadow: "0 0 10px #ef4444"}}></div>
             Live Frame Stream ({visualDetections.length} recorded)
           </h3>
           
           {visualDetections.length === 0 ? (
               <div className="glass-panel" style={{padding: "3rem", textAlign: "center", color: "var(--text-muted)", borderStyle: "dashed", opacity: 0.7}}>
                   Waiting for first frame to be analyzed... (This might take a few minutes if downloading AI models for the first time).
               </div>
           ) : (
               <div className="scene-cards" style={{ display: "grid", gap: "1rem", maxHeight: "400px", overflowY: "auto", paddingRight: "10px", paddingBottom: "20px" }}>
                {visualDetections.slice().reverse().map((d, i) => {
                  const mainEmotion = d.objects_json.emotions?.[0];
                  return (
                    <motion.div key={d.id} className="scene-card glass-panel" initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{duration: 0.3}} style={{margin: 0, background: "rgba(20,20,30,0.8)"}}>
                      <div className="scene-card-header">
                        <span className="scene-time" style={{ color: "var(--accent)" }}>{d.timestamp_sec}s</span>
                        {mainEmotion && (
                          <span className="scene-emotion-badge" style={{ background: EMOTION_COLORS[mainEmotion.emotion] + "30", color: EMOTION_COLORS[mainEmotion.emotion] }}>
                            {EMOTION_EMOJIS[mainEmotion.emotion]} {mainEmotion.emotion}
                          </span>
                        )}
                      </div>
                      <p className="scene-objects" style={{ margin: "5px 0" }}>{d.objects_json.objects?.join(", ") || "—"}</p>
                      {d.objects_json.scene_caption && <p className="scene-caption" style={{ color: "var(--text-muted)" }}>"{d.objects_json.scene_caption}"</p>}
                    </motion.div>
                  );
                })}
               </div>
           )}
        </div>
      </div>
    );
  }

  // ── Dashboard Layout (Done) ─────────────────────────────────
  return (
    <div className="dashboard-page">
      {/* Top bar */}
      <div className="top-bar">
        <div className="top-bar-brand" onClick={() => router.push("/")} style={{ cursor: "pointer" }}>
          🎬 <span className="title-accent">Vidora AI</span>
        </div>
        <div className="top-bar-actions">
          <button className="nav-link" onClick={() => router.push("/")}>
            Dashboard
          </button>
          <button className="nav-link logout-btn" onClick={logout}>
            Logout
          </button>
        </div>
      </div>

      <div className="dashboard-layout">
        {/* ── LEFT: Video + Analysis ────────────────────────── */}
        <div className="player-section">
          {/* Video Player & overlay */}
          <div className="video-glass-wrapper" style={{ position: "relative" }}>
            <video preload="auto" crossOrigin="anonymous" ref={videoRef} controls src={getVideoStreamUrl(videoId)} />
            
            {duration > 0 && (
              <div className="emoji-timeline-overlay">
                <div className="timeline-track" />
                {visualDetections.map((d, i) => {
                  const leftPerc =
                    duration > 0 ? (d.timestamp_sec / duration) * 100 : i * 5;
                  const mainEmotion = d.objects_json.emotions?.[0];
                  const emoji = mainEmotion
                    ? EMOTION_EMOJIS[mainEmotion.emotion] || "📍"
                    : "📍";
                  return (
                    <motion.div
                      key={d.id}
                      className="emoji-marker"
                      style={{ left: `${Math.min(leftPerc, 96)}%` }}
                      onClick={() => seekTo(d.timestamp_sec)}
                      whileHover={{ scale: 1.4 }}
                      title={`${d.timestamp_sec}s — ${
                        mainEmotion ? mainEmotion.emotion : d.objects_json.objects?.join(", ")
                      }`}
                    >
                      {emoji}
                    </motion.div>
                  );
                })}
                {/* Audio markers */}
                {audioSegments.map((seg, i) => {
                  const leftPerc =
                    duration > 0 ? (seg.start / duration) * 100 : 0;
                  return (
                    <motion.div
                      key={`audio-${i}`}
                      className={`emoji-marker ${seg.isLoud ? "loud-marker" : ""}`}
                      style={{ left: `${Math.min(leftPerc, 96)}%`, top: "28px" }}
                      onClick={() => seekTo(seg.start)}
                      whileHover={{ scale: 1.4 }}
                      title={`${seg.start}s — ${seg.isLoud ? "📢 LOUD: " : "🗣️ "}${seg.text}`}
                    >
                      {seg.isLoud ? "📢" : "🗣️"}
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Stats Row: Emotion Chart + Audio Transcript */}
          <div className="stats-row">
            {/* Emotion Distribution */}
            <div className="section-card glass-panel emotion-chart-card">
              <h3 className="section-title">😊 Emotion Distribution</h3>
              {emotionStats.length === 0 ? (
                <p className="section-desc">No emotions detected</p>
              ) : (
                <div className="chart-wrapper">
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={emotionStats}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={3}
                        dataKey="value"
                        animationBegin={0}
                        animationDuration={800}
                      >
                        {emotionStats.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          background: "rgba(20,20,25,0.9)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "8px",
                          color: "#fff",
                        }}
                        formatter={(val: number, name: string) => [val, name]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="emotion-legend">
                    {emotionStats.map((e) => (
                      <div key={e.name} className="legend-item">
                        <span className="legend-dot" style={{ background: e.color }} />
                        {e.emoji} {e.name} ({e.value})
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Audio Transcript */}
            <div className="section-card glass-panel audio-card">
              <h3 className="section-title">🎙️ Audio Transcript</h3>
              {audioSegments.length === 0 ? (
                <p className="section-desc">No speech detected in this video</p>
              ) : (
                <div className="audio-transcript">
                  {audioSegments.map((seg, i) => (
                    <div
                      key={i}
                      className={`audio-bubble ${seg.isLoud ? "audio-loud" : ""}`}
                      onClick={() => seekTo(seg.start)}
                    >
                      <span className="audio-time">
                        {seg.isLoud ? "📢" : "🗣️"} {seg.start}s–{seg.end}s
                      </span>
                      <span className="audio-text">{seg.text}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Scene Detection Cards */}
          <div className="section-card glass-panel">
            <h3 className="section-title">🎬 Scene Detections</h3>
            {visualDetections.length === 0 ? (
              <p className="section-desc">No detections found</p>
            ) : (
              <div className="scene-cards">
                {visualDetections.map((d, i) => {
                  const mainEmotion = d.objects_json.emotions?.[0];
                  return (
                    <motion.div
                      key={d.id}
                      className="scene-card"
                      onClick={() => seekTo(d.timestamp_sec)}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <div className="scene-card-header">
                        <span className="scene-time">{d.timestamp_sec}s</span>
                        {mainEmotion && (
                          <span
                            className="scene-emotion-badge"
                            style={{
                              background: EMOTION_COLORS[mainEmotion.emotion] + "30",
                              color: EMOTION_COLORS[mainEmotion.emotion],
                            }}
                          >
                            {EMOTION_EMOJIS[mainEmotion.emotion]} {mainEmotion.emotion}
                          </span>
                        )}
                      </div>
                      <p className="scene-objects">
                        {d.objects_json.objects?.join(", ") || "—"}
                      </p>
                      {d.objects_json.scene_caption && (
                        <p className="scene-caption">
                          "{d.objects_json.scene_caption}"
                        </p>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* ── RIGHT: AI Chat ────────────────────────────────── */}
        <div className="chat-section glass-panel">
          <div className="chat-header">
            <div className="status-dot" />
            Neural Assistant
          </div>

          <div className="chat-messages">
            {/* Quick query chips */}
            {chatLog.length <= 1 && (
              <div className="quick-chips">
                {QUICK_QUERIES.map((q) => (
                  <motion.button
                    key={q}
                    className="chip"
                    onClick={() => handleQuery(q)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {q}
                  </motion.button>
                ))}
              </div>
            )}

            <AnimatePresence>
              {chatLog.map((log, i) => (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  key={i}
                  className={`message ${log.role === "user" ? "msg-user" : "msg-ai"}`}
                >
                  {log.content}
                  {log.model && (
                    <span className="model-badge">
                      {log.model === "cloud" ? "☁️ Cloud" : "🟢 Local"}
                    </span>
                  )}
                </motion.div>
              ))}
              {querying && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="message msg-ai dots-loader"
                >
                  <span className="dot" />
                  <span className="dot" />
                  <span className="dot" />
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </AnimatePresence>
          </div>

          <div className="chat-input-wrapper">
            <div className="chat-input-inner">
              <input
                className="chat-input"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleQuery()}
                placeholder="Ask anything about the video..."
                disabled={querying}
              />
              <button
                className="chat-send"
                onClick={() => handleQuery()}
                disabled={querying}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M22 2L11 13"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path d="M22 2L15 22L11 13L2 9L22 2Z" fill="currentColor" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
