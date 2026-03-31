from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import datetime


# ── User schemas ──────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# ── Video schemas ─────────────────────────────────────────────

class VideoUploadResponse(BaseModel):
    video_id: str
    status: str


class VideoStatusResponse(BaseModel):
    video_id: str
    status: str


class DetectionItem(BaseModel):
    id: str
    timestamp_sec: float
    objects_json: Any

    class Config:
        from_attributes = True


class VideoResultsResponse(BaseModel):
    video_id: str
    status: str
    detections: List[DetectionItem]


class VideoListItem(BaseModel):
    id: str
    filename: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Query schemas ─────────────────────────────────────────────

class QueryRequest(BaseModel):
    video_id: str
    query: str


class QueryResponse(BaseModel):
    response: str
    model_used: str


# ── Health ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
