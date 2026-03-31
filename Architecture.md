📄 Architecture Document
🧠 Product: Vidora AI
🎯 1. Overview

Vidora AI is a web-based video analysis platform that enables users to:

Upload videos
Extract structured insights (objects, scenes, events)
Query videos using natural language
Interact via a dynamic timeline + AI chat interface

The system is designed using a Dockerized microservices architecture to ensure:

Scalability
Isolation of components
Easy deployment
🏗️ 2. High-Level Architecture
[ Next.js Frontend ]
          ↓
[ API Gateway / FastAPI Backend ]
          ↓
-------------------------------------------------
|           Dockerized Services Layer            |
|-----------------------------------------------|
| 1. Video Processing Service                   |
|    - FFmpeg (frame extraction)                |
|                                               |
| 2. Detection Service                          |
|    - YOLOv8 (object detection)                |
|                                               |
| 3. AI Service (Hybrid)                        |
|    - Local LLM (Ollama)                       |
|    - Cloud API (Gemini / TwelveLabs)          |
|                                               |
| 4. Storage Service                            |
|    - JSON / SQLite / PostgreSQL               |
-------------------------------------------------
          ↓
[ Processed Data → Frontend UI ]
🐳 3. Dockerized Architecture

All components are containerized using Docker.

🧩 Services (Each runs in its own container)
1. 🌐 Frontend Service
Technology: Next.js
Responsibilities:
UI rendering
Video player + timeline
Chat interface
2. ⚙️ Backend API Service
Technology: FastAPI
Responsibilities:
Handle uploads
Manage processing pipeline
Route AI queries
Serve results
3. 🎥 Video Processing Service
Tool: FFmpeg
Responsibilities:
Extract frames from video
Resize & optimize frames
4. 🧠 Detection Service
Tool: YOLOv8
Responsibilities:
Detect objects in frames
Generate structured metadata
5. 🤖 AI Service (Hybrid)
🔹 Local LLM Container
Tool: Ollama
Handles:
Simple queries
Object-based reasoning
🔹 Cloud API Integration
APIs:
Gemini 1.5
TwelveLabs
Handles:
Complex reasoning
Semantic understanding
6. 🗄️ Storage Service
Options:
JSON (lightweight)
SQLite / PostgreSQL
Stores:
Frame metadata
Detection results
AI outputs
🔄 4. Data Flow (End-to-End)
1. User uploads video (Frontend)
2. Backend receives file
3. Video sent to Processing Service
4. FFmpeg extracts frames
5. Frames → Detection Service (YOLO)
6. Results stored in DB/JSON
7. AI Service generates summaries
8. Frontend fetches processed data
9. User queries video via chat
10. Backend routes:
      → Local LLM OR Cloud API
11. Response returned to UI
🧠 5. Hybrid AI Decision Layer
User Query
   ↓
Query Analyzer (Backend)
   ↓
-------------------------
| Simple Query → Ollama |
| Complex Query → API   |
-------------------------
Example Routing
Query	Route
“When does a car appear?”	Local LLM
“Explain the story of this video”	Cloud API
“What is happening emotionally?”	Cloud API
📡 6. API Design
POST   /upload
GET    /status/{video_id}
GET    /results/{video_id}
POST   /query
🗂️ 7. Storage Design
Example JSON Structure
{
  "video_id": "123",
  "frames": [
    { "timestamp": 1, "objects": ["person"] },
    { "timestamp": 2, "objects": ["car"] }
  ],
  "index": {
    "person": [1, 5, 10],
    "car": [2, 8]
  }
}
⚡ 8. Performance Considerations
Frame extraction: 0.5–1 FPS
Image resizing: 480p
Async processing (background tasks)
Limit concurrent jobs
🔐 9. Scalability & Deployment
Docker Benefits:
Independent scaling of services
Easy deployment across environments
Isolation of heavy components (YOLO, LLM)
Future Scaling:
Move to Kubernetes
Add message queue (Redis / RabbitMQ)
GPU-based inference (optional)
🎨 10. Frontend Interaction Layer
Interactive timeline
AI chat interface
Scene cards
Smooth animations
🏆 11. Key Highlights (for evaluation)
🐳 Fully Dockerized architecture
🤖 Hybrid AI (local + cloud)
🎬 Interactive video timeline
⚡ Optimized for low-resource systems
🔍 Searchable video intelligence
🚀 12. Conclusion

Vidora AI combines:

Efficient local processing
Advanced cloud-based reasoning
Modern interactive UI

to deliver a scalable, intelligent, and user-friendly video analysis system.

If you want next:
👉 I can generate:

docker-compose.yml
Folder structure
Deployment steps (NixOS friendly 🔥)

Just say 👍