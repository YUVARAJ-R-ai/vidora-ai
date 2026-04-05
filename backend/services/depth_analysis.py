import cv2
import numpy as np
import logging
from transformers import pipeline

# Suppress overly verbose transformers loading warnings
logging.getLogger("transformers").setLevel(logging.ERROR)

depth_pipeline = None

def get_depth_pipeline():
    """Lazy load the depth estimation pipeline to save RAM on startup."""
    global depth_pipeline
    if depth_pipeline is None:
        try:
            # Using Intel's tiny SwinV2 Depth model. It's incredibly fast and lightweight
            # and automatically caches in the huggingface_cache volume.
            depth_pipeline = pipeline("depth-estimation", model="Intel/dpt-swinv2-tiny-256")
        except Exception as e:
            print(f"Failed to load depth pipeline: {e}")
    return depth_pipeline

def estimate_depth(frame: np.ndarray) -> np.ndarray:
    """
    Takes a raw BGR cv2 video frame and returns a normalized depth map (0-255).
    Lighter pixels = closer to camera, Darker pixels = further away.
    """
    pipe = get_depth_pipeline()
    if not pipe:
        # Fallback to pure black image on error
        return np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
        
    from PIL import Image
    
    # Convert BGR to RGB format required by HuggingFace
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # Run inference
    result = pipe(img)
    depth_image = result["depth"]
    
    # Convert PIL Image back to numpy array format natively compatible with cv2
    depth_map = np.array(depth_image)
    
    # Normalizing just in case the model returns non 0-255 bounds
    depth_min = depth_map.min()
    depth_max = depth_map.max()
    if depth_max - depth_min > 0:
        depth_map = 255 * (depth_map - depth_min) / (depth_max - depth_min)
        
    return depth_map.astype(np.uint8)

def get_center_proximity(depth_map: np.ndarray) -> float:
    """
    Returns relative proximity value (0.0 to 1.0) for the center of the frame.
    Useful for warning if the drone is about to crash directly into an object.
    Higher value = Object is extremely close.
    """
    h, w = depth_map.shape
    center_region = depth_map[int(h*0.4):int(h*0.6), int(w*0.4):int(w*0.6)]
    avg_depth = np.mean(center_region)
    return float(avg_depth / 255.0)
