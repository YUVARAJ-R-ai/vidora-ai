import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    videos = relationship("Video", back_populates="owner")


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, done, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="videos")
    detections = relationship("Detection", back_populates="video", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="video", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(String, primary_key=True, default=generate_uuid)
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    timestamp_sec = Column(Float, nullable=False)
    objects_json = Column(JSON, nullable=False)  # {"objects": [...], "confidence": 0.92}

    video = relationship("Video", back_populates="detections")


class Query(Base):
    __tablename__ = "queries"

    id = Column(String, primary_key=True, default=generate_uuid)
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    response_json = Column(JSON, nullable=True)
    model_used = Column(String, nullable=True)  # "local" or "cloud"

    video = relationship("Video", back_populates="queries")

class VideoSummary(Base):
    __tablename__ = "video_summaries"

    id = Column(String, primary_key=True, default=generate_uuid)
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    summary_text = Column(Text, nullable=False)
    embedding = Column(Vector(768)) # Gemini default embedding is 768 dims
    
    video = relationship("Video")
