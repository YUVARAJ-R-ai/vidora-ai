# Vidora AI - Architecture & Debugging Guide

When working with modern multi-modal AI systems embedded inside Docker, it can get difficult to isolate where exactly an error is occurring. Vidora AI is split into four distinct container services inside your `docker-compose.yml`. Use this guide to systematically isolate, diagnose, and solve issues.

---

## 🏗️ 1. Global Diagnosis (The Orchestration Layer)

Before isolating a single container, look at the health of the entire Docker cluster.

### Useful Commands:
- **See what is actively running:**
  ```bash
  docker-compose ps
  ```
  *If a container says `Restarting` or `Exited`, that container is causing your crash.*

- **View global logs (Live filtering):**
  ```bash
  # Watch all logs live, but only from the last 50 lines to avoid spam
  docker-compose logs -f --tail=50
  ```

- **Rebuild from scratch (Clears Cache):**
  ```bash
  docker-compose down -v  # Destroys containers AND Database volume (Use carefully!)
  docker-compose build --no-cache
  docker-compose up -d
  ```

---

## 🧠 2. Backend Container (`backend`)
*This is the heart of the system. It handles Python, GPU/CPU tensor calculations, YOLOv8, Transformers, and the REST API.*

**Why it usually fails:**
1. Heavy dependencies like `torch`, `transformers`, or `opencv-python` failed to install during the Docker Build phase (Timeout or OOM).
2. Missing environment variables (`GEMINI_API_KEY`, `GROQ_API_KEY`).
3. Out of Memory (OOM) Killed during video processing because the MiDaS depth model or optical flow required too much RAM.

### How to Debug:
- **Tail the backend logs specifically:**
  ```bash
  docker-compose logs -f --tail=100 backend
  ```
- **Drop directly into the running container's shell session:**
  ```bash
  docker exec -it vidora-ai-backend-1 /bin/bash
  ```
  *(Once inside, you can run `top` or `htop` to see if Python is eating all the RAM).*
- **Manually run the Python server to see raw error traces:**
  ```bash
  docker exec -it vidora-ai-backend-1 /bin/bash
  # Then inside the container:
  uvicorn main:app --host 0.0.0.0 --port 8000
  ```

---

## 🖥️ 3. Frontend Container (`frontend`)
*The Next.js React user interface. Handles user interaction, rendering telemetry, and communicating with the Backend REST API.*

**Why it usually fails:**
1. Node packages are missing (requiring `npm install`).
2. Cannot reach the backend because `NEXT_PUBLIC_API_URL` is configured to `localhost:8000` but you are deploying it on a network machine.
3. TypeScript errors breaking the `npm run build` process during Docker initialization.

### How to Debug:
- **Check the specific Next.js Server logs:**
  ```bash
  docker-compose logs -f --tail=50 frontend
  ```
- **Error:** *"Make sure the backend is running!"*
  * This happens when the Frontend Javascript tries to GET/POST to `http://localhost:8000` but the Backend Docker container has either crashed or is still building its Image. (Check the backend logs!)

---

## 🗄️ 4. PostgreSQL Database (`db`)
*Your persistent memory. We recently upgraded this to run `pgvector/pgvector:pg15` to support RAG embeddings.*

**Why it usually fails:**
1. You originally created the volume with standard PostgreSQL, and Docker is confused now that you switched the image to `pgvector`.
2. Wrong password credentials.
3. The `main.py` SQLAlchemy script failed to run `CREATE EXTENSION vector`.

### How to Debug:
- **Check DB initialization logs:**
  ```bash
  docker-compose logs db
  ```
- **Enter the raw SQL shell to manually test functionality:**
  ```bash
  docker exec -it vidora-ai-db-1 psql -U vidora -d vidora
  
  # Then run:
  \dx  # This will list all extensions. Ensure "vector" is in this list!
  ```
- **Nuke and restart the database (WARNING: DELETES ALL DATA):**
  ```bash
  docker-compose down
  docker volume rm vidora-ai_postgres_data
  docker-compose up -d
  ```

---

## 🤖 5. Local LLM Service (`ollama`)
*Handles offline models running directly on your host.*

**Why it usually fails:**
1. **Port conflicts (Address already in use):** You have Ollama installed natively as a system service on Linux (which runs automatically on port 11434). Docker tries to map its internal Ollama to `11434` and crashes.
   - *Fix:* Change the `docker-compose.yml` port map to `"11435:11434"`.

### How to Debug:
- **Stop native host Ollama if it conflicts:**
  ```bash
  sudo systemctl stop ollama
  ```
- **Log check:**
  ```bash
  docker-compose logs ollama
  ```

---

# 🚀 The Ultimate Developer Iteration Loop
If you are developing complex features (like modifying `page.tsx` or `video_processor.py`), **do not** wait 5 minutes for Docker to rebuild every time you make a change. Docker Compose maps your local folders (`./backend:/app` and `./frontend:/app`) into the containers.

**Therefore, any changes you save in VS Code will instantly update inside Docker via hot-reloading!**
Only run `docker-compose build` when you add entirely new dependencies to `requirements.txt` or `package.json`.
