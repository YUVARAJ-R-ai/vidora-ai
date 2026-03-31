from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, Video, Detection, Query
from schemas import QueryRequest, QueryResponse
from auth import get_current_user
from services.ai_router import route_query

router = APIRouter(prefix="/query", tags=["Query"])


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

    # Gather detection context
    detections = (
        db.query(Detection)
        .filter(Detection.video_id == payload.video_id)
        .order_by(Detection.timestamp_sec)
        .limit(50)
        .all()
    )

    # Build context string
    context_lines = []
    for det in detections:
        objects = det.objects_json.get("objects", []) if isinstance(det.objects_json, dict) else []
        context_lines.append(f"At {det.timestamp_sec}s: {', '.join(objects)}")
    context = "\n".join(context_lines)

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
