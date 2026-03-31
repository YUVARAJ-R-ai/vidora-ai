📄 Product Requirements Document (PRD)
🧠 Product Name

Vidora AI – Intelligent Video Analysis Platform

🎯 Objective

Build a web-based video analysis system that allows users to:

Upload videos
Automatically extract insights (objects, scenes, events)
Interactively query the video
Navigate via a smart, visual timeline
🚀 Key Value Proposition

“Search and understand videos like Google — instantly.”

👥 Target Users
Students / researchers
Content creators
Security / surveillance analysis
Developers experimenting with AI
🧩 Core Features
1. 🎥 Video Upload & Processing
Drag-and-drop upload
Real-time processing status
Progress visualization
2. 🧠 AI Video Understanding
Object detection (person, car, phone, etc.)
Scene segmentation
Event tagging
3. 🔍 Smart Video Search
Natural language queries:
“When does a person appear?”
“Find scenes with vehicles”
Returns:
Timestamps
Scene previews
4. 🎬 Interactive Timeline (Core UX)
Visual markers for detected objects
Click → jump to timestamp
Hover → preview frame
5. 💬 AI Chat Assistant
Ask questions about video
Summarization
Context-aware responses
6. 📊 Scene Cards & Highlights
Auto-generated scenes
Key moments extraction
Scrollable preview cards
🏗️ System Architecture
Frontend (Next.js)
        ↓
FastAPI Backend
        ↓
Video Processing Pipeline
   ├── FFmpeg (frame extraction)
   ├── YOLO (object detection)
   ├── Hybrid AI Layer
   │     ├── Local LLM (Ollama)
   │     └── Cloud API (Gemini / TwelveLabs)
        ↓
Storage (JSON / DB)
        ↓
Frontend UI (timeline + chat)
🧠 Hybrid AI Strategy (KEY INNOVATION)
🔹 Local LLM (Offline / Cheap)

Using Ollama

Responsibilities:
Basic Q&A
Object-based queries
Simple summaries
Benefits:
No API cost
Works offline
Faster for small tasks
🔹 Cloud API (Advanced Reasoning)

Using:

Gemini 1.5
or TwelveLabs
Responsibilities:
Deep video understanding
Complex queries
Semantic reasoning
🔀 Routing Logic (Smart Switching)
User Query
   ↓
Simple? → Local LLM
Complex? → Cloud API
Example:
Query	Model Used
“When does a car appear?”	Local LLM
“Explain the story of this video”	Cloud API
“What is the person doing emotionally?”	Cloud API
⚙️ Functional Requirements
🎥 Video Processing
Extract frames at configurable FPS
Resize frames for optimization
Map frames → timestamps
🧠 Detection Engine
Detect objects using YOLO
Store results in structured format
🔍 Query Engine
Parse user query
Match against indexed data
Route to appropriate AI model
📊 Data Storage
Store:
Frame metadata
Object detections
Scene summaries
📡 API Endpoints
POST   /upload
GET    /status/{video_id}
GET    /results/{video_id}
POST   /query
Example Query Request
{
  "video_id": "abc123",
  "query": "Find all scenes with a person"
}
Example Response
{
  "timestamps": [12, 45, 78],
  "objects": ["person"],
  "confidence": 0.92
}
🎨 Frontend Requirements

Using Next.js

UI Components
Video Player
Timeline with markers
Chat interface
Upload component
Scene cards
UX Features (Important for grading)
Smooth animations (Framer Motion)
AI thinking states
Interactive timeline
Hover previews
Click-to-seek
⚡ Performance Requirements
Frame extraction ≤ 1 FPS
Processing time:
Short videos (<1 min): < 30s
Async processing (non-blocking UI)
🔐 Constraints
Must run on CPU-based system
Limited memory (16GB)
Minimal API cost
🧪 Success Metrics
Query response time < 3 sec
Accurate timestamp detection
Smooth UI interactions
User can navigate video efficiently
🚀 Future Enhancements
Real-time video analysis
Multi-video comparison
Emotion detection
Speech-to-text integration
Export reports
🏆 Unique Selling Points (Highlight this in viva)
🔥 Hybrid AI (Local + Cloud)
🎬 Cinematic timeline UI
🔍 Searchable video system
⚡ Optimized for low-resource devices