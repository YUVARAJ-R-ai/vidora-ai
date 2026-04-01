from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, Video, Detection, Query
from schemas import QueryRequest, QueryResponse
from auth import get_current_user
from services.ai_router import route_query

router = APIRouter(prefix="/query", tags=["Query"])


def _build_rich_context(detections) -> str:
    """
    Build a multi-modal context string from enriched detection records.

    Separates visual detections (objects, emotions, captions) from
    audio detections (transcripts, loudness) for clarity.
    """
    visual_lines = []
    audio_lines = []

    for det in detections:
        data = det.objects_json if isinstance(det.objects_json, dict) else {}
        ts = det.timestamp_sec

        # Check if this is an audio detection
        audio = data.get("audio")
        if audio:
            loud_tag = "[LOUD] " if audio.get("is_loud") else ""
            end_sec = audio.get("end_sec", ts)
            transcript = audio.get("transcript", "")
            audio_lines.append(
                f"Audio {ts}s-{end_sec}s: {loud_tag}\"{transcript}\""
            )
            continue

        # Visual detection — build a rich line
        parts = []

        # Objects
        objects = data.get("objects", [])
        if objects:
            parts.append(f"Objects: {', '.join(objects)}")

        # Emotions
        emotions = data.get("emotions", [])
        if emotions:
            emo_strs = [
                f"{e['emotion']} ({e['confidence']:.0%})"
                for e in emotions
            ]
            parts.append(f"Emotions: {', '.join(emo_strs)}")

        # Scene caption
        caption = data.get("scene_caption")
        if caption:
            parts.append(f"Scene: \"{caption}\"")

        if parts:
            visual_lines.append(f"At {ts}s: {' | '.join(parts)}")

    # Combine visual and audio context
    sections = []
    if visual_lines:
        sections.append("Visual analysis:\n" + "\n".join(visual_lines))
    if audio_lines:
        sections.append("Audio analysis:\n" + "\n".join(audio_lines))

    return "\n\n".join(sections) if sections else "No detection data available."


@router.post("/", response_model=QueryResponse)
def ask_query(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure the video belongs to the current user
    video = (
        db.query(Video)
        .filter(Video.id == payload.video_id, Video.user_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.status != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Video is not ready yet. Current status: {video.status}",
        )

    # Gather ALL detection context (visual + audio), capped at 50
    detections = (
        db.query(Detection)
        .filter(Detection.video_id == payload.video_id)
        .order_by(Detection.timestamp_sec)
        .limit(50)
        .all()
    )

    # Build rich multi-modal context
    context = _build_rich_context(detections)

    # Route the query through AI
    response_text, model_used = route_query(payload.query, context)

    # Persist query
    db_query = Query(
        video_id=payload.video_id,
        query_text=payload.query,
        response_json={"response": response_text},
        model_used=model_used,
    )
    db.add(db_query)
    db.commit()

    return {"response": response_text, "model_used": model_used}
