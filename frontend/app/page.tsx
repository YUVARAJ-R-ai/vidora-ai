"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const router = useRouter();

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
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      
      if (data.video_id) {
        // Add a slight delay for buttery transition
        setTimeout(() => {
          router.push(`/video/${data.video_id}`);
        }, 600);
      }
    } catch (error) {
      console.error("Upload failed", error);
      alert("Failed to connect to the analysis backend. Make sure docker is running!");
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <h1 className="title">
          Know Your Video <br/><span className="title-accent">Instantly.</span>
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "1.25rem", margin: "1.5rem 0 3rem 0", maxWidth: "600px", lineHeight: 1.6 }}>
          Upload your media and let our Hybrid AI engine detect scenes, tag objects, and answer any questions you have.
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
        <label htmlFor="file-upload" style={{ cursor: "pointer", display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
          
          <motion.div 
            animate={{ y: [0, -10, 0] }} 
            transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
            style={{ fontSize: "4.5rem", marginBottom: "1rem" }}
          >
            {file ? "🎬" : "☁️"}
          </motion.div>
          
          <h2 style={{ margin: 0, fontSize: "1.75rem", fontWeight: 600 }}>
            {file ? <span className="title-accent">{file.name}</span> : "Drag & Drop Video Here"}
          </h2>
          <p style={{ color: "var(--text-muted)", margin: 0, fontSize: "1.1rem" }}>
            {file ? `Ready to analyze ${(file.size / 1024 / 1024).toFixed(1)} MB` : "Or click to browse files (MP4, MOV, MKV)"}
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
                <span className="dot"></span><span className="dot"></span><span className="dot"></span>
              </div>
            ) : "Analyze Intelligence ✨"}
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}
