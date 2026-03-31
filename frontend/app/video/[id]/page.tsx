"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

interface Detection {
  timestamp: number;
  objects: { label: string; confidence: number }[];
}

export default function VideoDashboard() {
  const params = useParams();
  const videoId = params.id as string;
  const [status, setStatus] = useState("processing");
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<Detection[]>([]);
  const [chatLog, setChatLog] = useState<{ role: string; content: string }[]>([]);
  const [query, setQuery] = useState("");
  const [querying, setQuerying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog, querying]);

  useEffect(() => {
    const pollStatus = setInterval(async () => {
      if (status === "completed" || status === "failed") {
        clearInterval(pollStatus);
        if (status === "completed") {
          fetchResults();
        }
        return;
      }
      try {
        const res = await fetch(`http://localhost:8000/status/${videoId}`);
        if (!res.ok) return;
        const data = await res.json();
        setStatus(data.status);
        setProgress(data.progress || 0);
      } catch (err) {
        console.error("Poll error", err);
      }
    }, 2000);
    return () => clearInterval(pollStatus);
  }, [videoId, status]);

  const fetchResults = async () => {
    try {
      const res = await fetch(`http://localhost:8000/results/${videoId}`);
      if (!res.ok) return;
      const data = await res.json();
      setResults(data.results || []);
      setChatLog([{ role: "ai", content: "Analysis complete! How can I help you understand this video today? ✨" }]);
    } catch (e) {
      console.error(e);
      setChatLog([{ role: "ai", content: "Analysis complete, but I couldn't load the object tracking data." }]);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;
    const userMsg = query;
    setChatLog((prev) => [...prev, { role: "user", content: userMsg }]);
    setQuery("");
    setQuerying(true);

    try {
      const res = await fetch(`http://localhost:8000/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_id: videoId, query: userMsg }),
      });
      if (!res.ok) throw new Error("API returned an error");
      const data = await res.json();
      
      setChatLog((prev) => [...prev, { role: "ai", content: data.response }]);
    } catch (err) {
      setChatLog((prev) => [...prev, { role: "ai", content: "Sorry, I had trouble processing that query. Please make sure the AI endpoint is alive." }]);
    } finally {
      setQuerying(false);
    }
  };

  const seekTo = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play().catch(e => console.log(e));
    }
  };

  if (status === "processing" || status === "pending") {
    return (
      <div className="upload-container">
        <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} transition={{ duration: 0.5 }}>
          <h2 className="title" style={{ fontSize: "2.5rem" }}>Analyzing Intelligence <span className="title-accent">...</span></h2>
          <div style={{ width: "600px", maxWidth: "90vw", background: "var(--bg-surface)", height: "24px", borderRadius: "12px", overflow: "hidden", border: "1px solid var(--border)", position: 'relative' }}>
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ ease: "easeOut", duration: 0.8 }}
              style={{ background: "linear-gradient(90deg, var(--primary), var(--accent))", height: "100%", position: 'relative' }}
            >
               <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)', filter: 'blur(4px)', opacity: 0.5, transform: 'translateX(-100%)', animation: 'shimmer 2s infinite' }} />
            </motion.div>
          </div>
          <p style={{ marginTop: "1.5rem", fontSize: "1.2rem", color: "var(--text-muted)", letterSpacing: "2px" }}>
            {progress}% EXTRACTED
          </p>
        </motion.div>
      </div>
    );
  }

  const duration = videoRef.current ? videoRef.current.duration : 100;

  return (
    <div className="dashboard-layout">
      {/* LEFT SECTION */}
      <div className="player-section">
        <h1 className="title" style={{ fontSize: "2.5rem", margin: 0 }}>
          Video <span className="title-accent">Dashboard</span>
        </h1>
        
        <div className="video-glass-wrapper">
          <video 
            ref={videoRef} 
            controls 
            src={`http://localhost:8000/static/${videoId}_${videoId.slice(4)}.mp4`} 
            onError={(e) => {
              // Fallback to simpler filename if it doesn't match the new UUID format
              const v = e.target as HTMLVideoElement;
              if (v.src.includes(".mp4")) v.src = `http://localhost:8000/static/${videoId}.mp4`;
            }}
          />
        </div>

        <h3 style={{ margin: "1rem 0 0 0", fontWeight: 600 }}>Object Timeline</h3>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", margin: "0 0 1rem 0" }}>Click a marker to jump to scene</p>
        
        <div className="timeline-container glass-panel" style={{ height: "40px", border: "1px solid var(--border)" }}>
          {results.map((r, i) => {
            const leftPerc = duration && !isNaN(duration) && duration > 0 ? (r.timestamp / duration) * 100 : Math.min(r.timestamp, 95);
            return (
              <div 
                key={i} 
                className="timeline-marker"
                style={{ left: `${leftPerc}%` }}
                onClick={() => seekTo(r.timestamp)}
                title={`Detected: ${r.objects.map((o) => o.label).join(", ")}`}
              />
            );
          })}
        </div>

        <h3 style={{ margin: "1rem 0 0 0", fontWeight: 600 }}>Detected Scenes</h3>
        {results.length === 0 ? (
           <p style={{ color: "var(--text-muted)" }}>No objects were detected securely. (PyTorch loaded locally)</p>
        ) : (
          <div className="scene-cards">
            {results.map((r, i) => (
              <div 
                key={i}
                onClick={() => seekTo(r.timestamp)}
                className="scene-card"
              >
                <p style={{ color: "var(--accent)", fontWeight: "bold", margin: "0 0 0.25rem 0", fontSize: "1.1rem" }}>{r.timestamp}s</p>
                <p style={{ fontSize: "0.85rem", margin: 0, color: "var(--text-muted)", textTransform: "capitalize" }}>
                  {r.objects.map((o) => o.label).join(", ")}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* RIGHT SECTION (CHAT) */}
      <div className="chat-section glass-panel">
        <div className="chat-header">
          <div className="status-dot" />
          Neural Assistant
        </div>
        
        <div className="chat-messages">
          <AnimatePresence>
            {chatLog.map((log, i) => (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                key={i} 
                className={`message ${log.role === 'user' ? 'msg-user' : 'msg-ai'}`}
              >
                {log.content}
              </motion.div>
            ))}
            {querying && (
               <motion.div 
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} 
                  className="message msg-ai dots-loader"
               >
                  <span className="dot"></span><span className="dot"></span><span className="dot"></span>
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
              onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
              placeholder="Ask anything about the video..."
              disabled={querying}
            />
            <button className="chat-send" onClick={handleQuery} disabled={querying}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z" fill="currentColor"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <style jsx global>{`
        @keyframes shimmer {
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
}
