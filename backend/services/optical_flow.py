import cv2
import numpy as np
from typing import Tuple

def calculate_average_speed_metrics(
    video_path: str,
    sample_rate: int = 15,
    max_frames_to_process: int = 150
) -> Tuple[float, float]:
    """
    Analyzes a video using Dense Optical Flow to determine 
    the average absolute velocity of pixels across the screen.
    
    This is extremely useful for estimating camera speed or the speed of dominant
    objects in the frame without AI overhead.
    
    Args:
        video_path: Path to the video file.
        sample_rate: Process every Nth frame to save CPU (Optical Flow is intensive).
        max_frames_to_process: Safety bound to prevent infinite calculation.
        
    Returns:
        (avg_magnitude, max_magnitude) representing relative speed indices.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.0, 0.0

    ret, frame1 = cap.read()
    if not ret:
        cap.release()
        return 0.0, 0.0

    # Resize to something manageable so the CPU isn't overwhelmed
    width, height = 640, 360
    frame1 = cv2.resize(frame1, (width, height))
    prvs = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    
    total_magnitudes = []
    max_mag = 0.0
    processed_count = 0
    
    while True:
        # Skip frames
        for _ in range(sample_rate - 1):
            cap.read()
            
        ret, frame2 = cap.read()
        if not ret:
            break
            
        frame2_resized = cv2.resize(frame2, (width, height))
        next_gray = cv2.cvtColor(frame2_resized, cv2.COLOR_BGR2GRAY)

        # Dense Optical Flow (Farneback)
        flow = cv2.calcOpticalFlowFarneback(
            prvs, next_gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        
        # Compute magnitude of the vectors
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        
        # Calculate mean magnitude of this frame (how fast the whole screen shifted)
        avg_frame_mag = float(np.mean(mag))
        total_magnitudes.append(avg_frame_mag)
        
        if avg_frame_mag > max_mag:
            max_mag = avg_frame_mag
            
        prvs = next_gray
        processed_count += 1
        
        if processed_count >= max_frames_to_process:
            break

    cap.release()
    
    if not total_magnitudes:
        return 0.0, 0.0
        
    avg_mag = float(np.mean(total_magnitudes))
    return round(avg_mag, 2), round(max_mag, 2)
