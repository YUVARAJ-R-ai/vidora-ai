import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base
from schemas import HealthResponse

# Import routers
from routers.users import router as users_router
from routers.videos import router as videos_router
from routers.query import router as query_router

# ── Create database tables on startup ────────────────────────
Base.metadata.create_all(bind=engine)

# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title="Vidora AI Backend API",
    description="Intelligent video analysis platform powered by YOLOv8 and LLMs",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (uploaded videos) ───────────────────────────
os.makedirs("/app/uploads", exist_ok=True)
os.makedirs("/app/frames", exist_ok=True)
app.mount("/static", StaticFiles(directory="/app/uploads"), name="static")

# ── Register routers ─────────────────────────────────────────
app.include_router(users_router)
app.include_router(videos_router)
app.include_router(query_router)


# ── Health check ──────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return {"status": "ok"}


@app.get("/", tags=["Health"])
def root():
    return {"message": "Vidora AI Backend API is running"}
