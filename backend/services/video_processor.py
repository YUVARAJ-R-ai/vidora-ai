import os
import subprocess

from ultralytics import YOLO
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Video, Detection

# ── PyTorch 2.6+ unpickling fix ──────────────────────────────
try:
    import torch
    import ultralytics.nn.tasks
    torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])
except Exception:
    pass

# ── Preload YOLO model ───────────────────────────────────────
try:
    yolo_model = YOLO("yolov8n.pt")
except Exception as e:
    print(f"Warning: Could not load YOLO model: {e}")
    yolo_model = None

FRAMES_BASE_DIR = "/app/frames"
FPS = 0.5  # extract 1 frame every 2 seconds


def process_video_pipeline(video_id: str, file_path: str):
    """
    Full processing pipeline:
    1. FFmpeg frame extraction at 0.5 FPS, scaled to 480p width
    2. YOLOv8 nano detection on each frame
    3. Persist Detection records to DB
    4. Update Video status to done/failed
    """
    db: Session = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return

        video.status = "processing"
        db.commit()

        # ── Step 1: Extract frames ────────────────────────────
        frames_dir = os.path.join(FRAMES_BASE_DIR, video_id)
        os.makedirs(frames_dir, exist_ok=True)

        ffmpeg_cmd = [
            "ffmpeg", "-i", file_path,
            "-vf", f"fps={FPS},scale=480:-1",
            os.path.join(frames_dir, "frame_%04d.jpg"),
            "-y",  # overwrite
        ]

        result = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            print(f"FFmpeg error for {video_id}: {result.stderr.decode()}")
            video.status = "failed"
            db.commit()
            return

        # ── Step 2: Run YOLO on each frame ────────────────────
        frame_files = sorted(
            f for f in os.listdir(frames_dir) if f.endswith(".jpg")
        )

        if not frame_files:
            print(f"No frames extracted for {video_id}")
            video.status = "failed"
            db.commit()
            return

        for idx, fname in enumerate(frame_files):
            frame_path = os.path.join(frames_dir, fname)
            # Timestamp = frame_number / fps
            # frame_number is 1-indexed from ffmpeg naming
            frame_number = idx + 1
            timestamp_sec = frame_number / FPS

            if yolo_model is None:
                continue

            results = yolo_model(frame_path, verbose=False)
            detected_labels = []
            confidences = []

            for res in results:
                for box in res.boxes:
                    conf = float(box.conf[0])
                    if conf > 0.4:
                        cls_id = int(box.cls[0])
                        label = yolo_model.names[cls_id]
                        detected_labels.append(label)
                        confidences.append(conf)

            # Only save frames with at least one detection
            if detected_labels:
                mean_conf = round(sum(confidences) / len(confidences), 4)
                detection = Detection(
                    video_id=video_id,
                    timestamp_sec=round(timestamp_sec, 2),
                    objects_json={
                        "objects": detected_labels,
                        "confidence": mean_conf,
                    },
                )
                db.add(detection)
                db.commit()

        # ── Step 3: Mark video as done ────────────────────────
        video.status = "done"
        db.commit()
        print(f"Video {video_id} processing complete.")

    except Exception as e:
        print(f"Error processing video {video_id}: {e}")
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
