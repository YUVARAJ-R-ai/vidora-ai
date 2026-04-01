"""
Enhanced Video Processing Pipeline.

1. FFmpeg frame extraction (0.5 FPS, 480p)
2. Per-frame analysis:
   a. YOLOv8n object detection
   b. DeepFace facial emotion recognition
   c. BLIP scene captioning (every 2nd frame)
3. Audio analysis:
   a. FFmpeg audio extraction
   b. Whisper tiny transcription
   c. Amplitude-based shouting detection
4. Persist enriched Detection records to DB
5. Update Video status
"""
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
BLIP_EVERY_N = 2  # Caption every 2nd frame to save time


def process_video_pipeline(video_id: str, file_path: str):
    """
    Full multi-modal processing pipeline.
    Runs as a FastAPI BackgroundTask with its own DB session.
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
            "-y",
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

        frame_files = sorted(
            f for f in os.listdir(frames_dir) if f.endswith(".jpg")
        )

        if not frame_files:
            print(f"No frames extracted for {video_id}")
            video.status = "failed"
            db.commit()
            return

        # ── Step 2: Per-frame analysis ────────────────────────
        print(f"[{video_id}] Processing {len(frame_files)} frames...")

        # Lazy-import analysis services (heavy dependencies)
        from services.emotion_analyzer import analyze_emotions
        from services.scene_captioner import caption_frame

        for idx, fname in enumerate(frame_files):
            db.refresh(video)
            if video.status in ("cancelled", "failed"):
                print(f"[{video_id}] Processing aborted by user.")
                break

            frame_path = os.path.join(frames_dir, fname)
            frame_number = idx + 1
            timestamp_sec = round(frame_number / FPS, 2)

            # ── 2a. YOLO object detection ─────────────────────
            detected_labels = []
            confidences = []

            if yolo_model is not None:
                results = yolo_model(frame_path, verbose=False)
                for res in results:
                    for box in res.boxes:
                        conf = float(box.conf[0])
                        if conf > 0.4:
                            cls_id = int(box.cls[0])
                            label = yolo_model.names[cls_id]
                            detected_labels.append(label)
                            confidences.append(conf)

            # ── 2b. DeepFace emotion analysis ─────────────────
            emotions = analyze_emotions(frame_path)

            # ── 2c. BLIP scene captioning (every Nth frame) ───
            scene_caption = None
            if frame_number % BLIP_EVERY_N == 0 or frame_number == 1:
                scene_caption = caption_frame(frame_path)

            # ── Build enriched detection record ───────────────
            # Save if we have ANY data (objects, emotions, or caption)
            if detected_labels or emotions or scene_caption:
                mean_conf = round(
                    sum(confidences) / len(confidences), 4
                ) if confidences else 0.0

                objects_json = {
                    "objects": detected_labels,
                    "confidence": mean_conf,
                }

                if emotions:
                    objects_json["emotions"] = emotions

                if scene_caption:
                    objects_json["scene_caption"] = scene_caption

                detection = Detection(
                    video_id=video_id,
                    timestamp_sec=timestamp_sec,
                    objects_json=objects_json,
                )
                db.add(detection)
                db.commit()

            print(f"  Frame {frame_number}/{len(frame_files)} done "
                  f"(objects={len(detected_labels)}, emotions={len(emotions)}, "
                  f"caption={'yes' if scene_caption else 'no'})")

        db.refresh(video)
        if video.status in ("cancelled", "failed"):
            print(f"[{video_id}] Audio processing skipped due to cancellation.")
            return

        # ── Step 3: Audio analysis ────────────────────────────
        print(f"[{video_id}] Starting audio analysis...")
        try:
            from services.audio_analyzer import analyze_audio

            audio_segments = analyze_audio(file_path, frames_dir)

            for seg in audio_segments:
                audio_detection = Detection(
                    video_id=video_id,
                    timestamp_sec=seg["start"],
                    objects_json={
                        "objects": [],
                        "confidence": 0.0,
                        "audio": {
                            "transcript": seg["text"],
                            "is_loud": seg.get("is_loud", False),
                            "amplitude_db": seg.get("amplitude_db", 0.0),
                            "end_sec": seg["end"],
                        }
                    },
                )
                db.add(audio_detection)

            if audio_segments:
                db.commit()
                print(f"  Audio: {len(audio_segments)} segments transcribed")
            else:
                print(f"  Audio: no audio track or no speech detected")

        except Exception as e:
            print(f"  Audio analysis failed (non-fatal): {e}")

        # ── Step 4: Mark video as done ────────────────────────
        db.refresh(video)
        if video.status not in ("cancelled", "failed"):
            video.status = "done"
            db.commit()
            print(f"[{video_id}] Processing complete!")

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
