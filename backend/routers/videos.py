import os
import uuid

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from models import User, Video, Detection
from schemas import (
    VideoUploadResponse,
    VideoStatusResponse,
    VideoResultsResponse,
    DetectionItem,
    VideoListItem,
)
from auth import get_current_user
from services.video_processor import process_video_pipeline

router = APIRouter(prefix="/videos", tags=["Videos"])

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video_id = str(uuid.uuid4())
    safe_filename = f"{video_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    db_video = Video(
        id=video_id,
        user_id=current_user.id,
        filename=file.filename,
        filepath=file_path,
        status="processing",
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)

    background_tasks.add_task(process_video_pipeline, video_id, file_path)

    return {"video_id": video_id, "status": "processing"}


@router.get("/status/{video_id}", response_model=VideoStatusResponse)
def get_video_status(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.user_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"video_id": video.id, "status": video.status}


@router.get("/results/{video_id}", response_model=VideoResultsResponse)
def get_video_results(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.user_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    detections = (
        db.query(Detection).filter(Detection.video_id == video_id).all()
    )
    return {
        "video_id": video.id,
        "status": video.status,
        "detections": [
            DetectionItem(
                id=d.id,
                timestamp_sec=d.timestamp_sec,
                objects_json=d.objects_json,
            )
            for d in detections
        ],
    }


@router.get("/my-videos", response_model=list[VideoListItem])
def list_my_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    videos = (
        db.query(Video)
        .filter(Video.user_id == current_user.id)
        .order_by(Video.created_at.desc())
        .all()
    )
    return videos


@router.get("/stream/{video_id}")
def stream_video(
    video_id: str,
    token: str,
    db: Session = Depends(get_db),
):
    """Serve the uploaded video file for playback safely via query token auth."""
    from auth import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.user_id == user_id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if not os.path.exists(video.filepath):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    return FileResponse(
        video.filepath,
        media_type="video/mp4",
        filename=video.filename,
    )


@router.post("/cancel/{video_id}", response_model=VideoStatusResponse)
def cancel_video_processing(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.user_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.status in ("processing", "pending"):
        video.status = "cancelled"
        db.commit()

    return {"video_id": video.id, "status": video.status}
