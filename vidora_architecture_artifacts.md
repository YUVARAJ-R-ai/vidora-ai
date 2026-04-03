# Vidora AI: System Architecture Highlights
*Compiled for Final Project Presentation*

This document outlines the significant engineering hurdles and custom solutions built into the Vidora AI platform to achieve a production-grade, containerized Video Analysis platform.

## 1. The HTML5 Streaming Auth Bypass
**The Problem:** Securing a `/stream/` API endpoint with JSON Web Tokens (JWT) naturally relies on injecting custom `Authorization: Bearer <token>` Headers into HTTP requests. However, standard browser `<video src="...">` tags inherently do not support injecting Header rules. This caused our authenticated FastAPI backend to immediately reject the frontend player with a `401 Unauthorized`.
**The Solution:** We explicitly rewrote the FastAPI dependency injector (`videos.py`) to scrape the user's JWT from a dynamically injected URL query parameter instead of a Header (`/stream/{video_id}?token=...`). The Next.js frontend fetches the token from LocalStorage and crafts the URL, securely bypassing the browser limitation without exposing the backend to raw public internet access!

## 2. Dynamic Memory Allocation ("The YOLO Lazy Loader")
**The Problem:** Machine Learning models occupy massive memory pools. Initializing `yolov8n` and `yolov8s` simultaneously inside Python global variables will cause WSL Docker containers to instantly crash out of RAM space (OOM Kills).
**The Solution:** We implemented an active Memory Allocation Manager inside `video_processor.py`. When a user requests a video scan, the Background CPU checks which model is currently "hot" in cache. If the user requested the heavier `yolov8s` model, but `yolov8n` is in memory, the server gracefully purges the `yolov8n` tensors from memory, pulls the `yolov8s` architecture into RAM on-the-fly, processes the video frames, and subsequently holds that state. This strictly limits YOLO to a single model memory footprint at a time while serving user toggling requests cleanly!

## 3. Database Integrity & Object Cascading
**The Problem:** Deleting a `Video` requires deleting hundreds of JSON `Detections` corresponding to individual frame inferences, the raw `MP4` on disk, and the `extracted_frames` array to prevent zombie disk bloat.
**The Solution:** We modified the SQLAlchemy relational schema to include `cascade="all, delete-orphan"`. Firing a `DELETE /videos/{id}` now cascades the physical Object Relational mapping automatically across child tables. Following this constraint wipe, the Python backend executes standard `os.remove` and `shutil.rmtree` to permanently clear the Docker filesystem `/app/uploads` and `/app/frames` of the physical target data.

---
> [!TIP]
> **Future Roadmap Integration:** A proposed Version 2.0 update replaces the `Salesforce/blip-image-captioning-base` module with a dedicated `EasyOCR` instance applied solely to low-blur semantic frames. This would enable ground truth extraction (sign reading, document scanning) and provide extreme accuracy enhancements to the Groq Llama 3.3 LLM summarizations.
