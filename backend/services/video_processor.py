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

import cv2
from database import SessionLocal
from models import Video, Detection, VideoSummary

from services.optical_flow import calculate_average_speed_metrics
from services.geometry_analysis import estimate_distance_to_object

# ── PyTorch 2.6+ unpickling fix ──────────────────────────────
try:
    import torch
    import ultralytics.nn.tasks
    torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])
except Exception:
    pass

# ── Dynamic YOLO loader ──────────────────────────────────────
global_yolo_model = None
global_yolo_name = None

def get_yolo_model(model_name: str):
    global global_yolo_model, global_yolo_name
    if global_yolo_name != model_name:
        try:
            print(f"Loading new YOLO architecture: {model_name}.pt into memory...")
            global_yolo_model = YOLO(f"{model_name}.pt")
            global_yolo_name = model_name
        except Exception as e:
            print(f"Warning: Could not load YOLO model {model_name}: {e}")
            global_yolo_model = None
            global_yolo_name = None
    return global_yolo_model

FRAMES_BASE_DIR = "/app/frames"
FPS = 0.5  # extract 1 frame every 2 seconds
BLIP_EVERY_N = 2  # Caption every 2nd frame to save time


def process_video_pipeline(video_id: str, file_path: str, yolo_model_name: str = "yolov8n"):
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

        # ── Step 1.5: Optical Flow (Speed calculation) ────────
        print(f"[{video_id}] Calculating optical flow speed...")
        avg_speed, max_speed = calculate_average_speed_metrics(file_path, sample_rate=15)
        
        speed_detection = Detection(
            video_id=video_id,
            timestamp_sec=0.0,
            objects_json={"global_metrics": {"avg_speed": avg_speed, "max_speed": max_speed}}
        )
        db.add(speed_detection)
        db.commit()

        # ── Step 2: Per-frame analysis ────────────────────────
        print(f"[{video_id}] Processing {len(frame_files)} frames...")

        # Lazy-import analysis services (heavy dependencies)
        from services.emotion_analyzer import analyze_emotions
        from services.scene_captioner import caption_frame
        from services.depth_analysis import estimate_depth, get_center_proximity

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

            current_yolo = get_yolo_model(yolo_model_name)
            object_distances = []
            
            if current_yolo is not None:
                results = current_yolo(frame_path, verbose=False)
                for res in results:
                    for box in res.boxes:
                        conf = float(box.conf[0])
                        if conf > 0.4:
                            cls_id = int(box.cls[0])
                            label = current_yolo.names[cls_id]
                            detected_labels.append(label)
                            confidences.append(conf)
                            
                            # Calculate distance/altitude
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            w, h = x2 - x1, y2 - y1
                            
                            # Extremely rough physical size mapping
                            size_m = 1.0 # default 1m
                            if label in ['car', 'truck', 'bus']: size_m = 4.5
                            elif label in ['person']: size_m = 1.7
                            elif label in ['dog', 'cat', 'animal']: size_m = 0.5
                            
                            dist = estimate_distance_to_object(w, h, 480, size_m)
                            if dist:
                                object_distances.append({f"{label}_{cls_id}": dist})

            # ── 2b. DeepFace emotion analysis ─────────────────
            emotions = analyze_emotions(frame_path)

            # ── 2c. BLIP scene captioning (every Nth frame) ───
            scene_caption = None
            if frame_number % BLIP_EVERY_N == 0 or frame_number == 1:
                scene_caption = caption_frame(frame_path)

            # ── 2d. Depth proximity analysis ──────────────────
            proximity = 0.0
            try:
                cv2_frame = cv2.imread(frame_path)
                if cv2_frame is not None:
                    d_map = estimate_depth(cv2_frame)
                    proximity = round(get_center_proximity(d_map), 2)
            except Exception as e:
                print(f"Depth analysis skipped: {e}")

            # ── Build enriched detection record ───────────────
            # Save if we have ANY data
            if detected_labels or emotions or scene_caption or proximity > 0:
                mean_conf = round(
                    sum(confidences) / len(confidences), 4
                ) if confidences else 0.0

                objects_json = {
                    "objects": detected_labels,
                    "confidence": mean_conf,
                    "proximity": proximity,
                }
                if object_distances:
                    objects_json["distances"] = object_distances

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

        # ── Step 3.5: RAG Memory Generation ───────────────────
        print(f"[{video_id}] Generating RAG memory summary and vector embedding...")
        try:
            import google.generativeai as genai
            
            # Gather all detection strings
            all_dets = db.query(Detection).filter(Detection.video_id == video_id).order_by(Detection.timestamp_sec).all()
            raw_text_events = []
            for d in all_dets:
                j = d.objects_json
                if "global_metrics" in j:
                    raw_text_events.append(f"Global Video Telemetry: speed {j['global_metrics'].get('avg_speed')} avg, {j['global_metrics'].get('max_speed')} max")
                if "scene_caption" in j:
                    raw_text_events.append(f"Timestamp {d.timestamp_sec}s: Scene shows {j['scene_caption']}")
                if "audio" in j:
                    raw_text_events.append(f"Timestamp {d.timestamp_sec}s: Spoken words: {j['audio'].get('transcript')}")
                if "objects" in j and j["objects"]:
                    raw_text_events.append(f"Timestamp {d.timestamp_sec}s: Objects detected: {', '.join(j['objects'])}")

            context_str = "\n".join(raw_text_events)

            # 1. Ask Gemini to summarize the event timeline
            model = genai.GenerativeModel("gemini-1.5-flash")
            summary_prompt = f"Summarize the following timeline of events detected in a video into a highly descriptive, comprehensive 2 to 3 sentence paragraph. Include key events, objects, overall speed, and the overall narrative. Do not say 'In this video', just provide the summary directly:\n\n{context_str}"
            response = model.generate_content(summary_prompt)
            final_summary = response.text.strip()

            # 2. Generate a vector embedding for the database
            embed_response = genai.embed_content(
                model="models/text-embedding-004",
                content=final_summary,
                task_type="retrieval_document",
            )
            vector_data = embed_response['embedding']

            # 3. Save to VideoSummary table
            vs = VideoSummary(video_id=video_id, summary_text=final_summary, embedding=vector_data)
            db.add(vs)
            db.commit()
            print(f"  RAG Memory generated successfully!")

        except Exception as e:
            print(f"  RAG memory generation and embedding failed: {e}")

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
