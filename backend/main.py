from fastapi import FastAPI, UploadFile, File
import time

app = FastAPI(title="Vidora AI Backend API")

@app.get("/")
def read_root():
    return {"message": "Vidora AI Backend API is running"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    # TODO: Save the file, kickoff background task
    video_id = f"vid_{int(time.time())}"
    return {"video_id": video_id, "status": "Upload successful"}

@app.get("/status/{video_id}")
def get_status(video_id: str):
    # TODO: Poll database for actual status
    return {"video_id": video_id, "status": "processing", "progress": 25}

@app.post("/query")
def process_query(video_id: str, query: str):
    # TODO: Search SQLite DB, route to Gemini or Ollama
    return {
         "timestamps": [12, 45, 78],
         "objects": ["person", "car"],
         "confidence": 0.92,
         "response": "Based on my analysis, a person appears with a car at around 12 seconds."
    }
