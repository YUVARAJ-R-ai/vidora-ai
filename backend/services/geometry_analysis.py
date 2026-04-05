import math
from typing import Optional

def estimate_distance_to_object(
    box_width_px: float,
    box_height_px: float,
    frame_width_px: int,
    assumed_physical_size_m: float,
    camera_fov_degrees: float = 60.0
) -> Optional[float]:
    """
    Estimates distance to an object using simple geometry (pinhole camera model).
    
    Args:
        box_width_px: Bounding box width in pixels.
        box_height_px: Bounding box height in pixels.
        frame_width_px: Total width of the video frame.
        assumed_physical_size_m: Estimated real world size in meters (width or height, whichever is larger).
        camera_fov_degrees: Assumed Field of View of the camera.
        
    Returns:
        Estimated distance in meters.
    """
    # Use the maximum dimension for the most accurate angle estimation
    max_px = max(box_width_px, box_height_px)
    if max_px <= 0:
        return None
        
    # Calculate focal length in pixels based on FOV
    # FOV is usually horizontal, so we use frame_width_px
    focal_length_px = (frame_width_px / 2) / math.tan(math.radians(camera_fov_degrees / 2))
    
    # distance = (real_size * focal_length_px) / object_size_px
    distance = (assumed_physical_size_m * focal_length_px) / max_px
    
    return round(distance, 2)

def calculate_altitude_from_ground_object(
    distance_to_object_m: float,
    pitch_angle_degrees: float = 90.0
) -> float:
    """
    Calculate the actual altitude of a drone given the distance to an object on the ground
    and the angle of the camera relative to the horizon.
    
    Args:
        pitch_angle_degrees: 90 is looking straight down, 0 is looking forward.
    """
    altitude = distance_to_object_m * math.sin(math.radians(pitch_angle_degrees))
    return round(altitude, 2)
