"""
Facial Emotion Recognition using DeepFace.

Analyzes each frame for faces and classifies emotions:
angry, disgust, fear, happy, sad, surprise, neutral.
"""
from typing import List, Dict, Any

# Lazy-load DeepFace to avoid import overhead at startup
_deepface = None


def _get_deepface():
    global _deepface
    if _deepface is None:
        from deepface import DeepFace
        _deepface = DeepFace
    return _deepface


def analyze_emotions(frame_path: str) -> List[Dict[str, Any]]:
    """
    Detect faces in a frame and classify their emotions.

    Args:
        frame_path: Path to the frame image file.

    Returns:
        List of dicts: [{"face": 1, "emotion": "angry", "confidence": 0.78}, ...]
        Returns empty list if no faces detected or on error.
    """
    try:
        DeepFace = _get_deepface()
        results = DeepFace.analyze(
            img_path=frame_path,
            actions=["emotion"],
            enforce_detection=True,  # Strictly require a face to prevent hallucinated detections
            silent=True,
        )

        # DeepFace returns a list of face analyses
        if not isinstance(results, list):
            results = [results]

        emotions = []
        for idx, face in enumerate(results):
            emotion_scores = face.get("emotion", {})
            if not emotion_scores:
                continue

            # Get dominant emotion and its confidence
            dominant = face.get("dominant_emotion", "neutral")
            confidence = round(float(emotion_scores.get(dominant, 0)) / 100.0, 4)

            # Only include if confidence is reasonable
            if confidence > 0.3:
                emotions.append({
                    "face": idx + 1,
                    "emotion": dominant,
                    "confidence": confidence,
                })

        return emotions

    except Exception as e:
        # Silently return empty — no face is a valid result
        return []
