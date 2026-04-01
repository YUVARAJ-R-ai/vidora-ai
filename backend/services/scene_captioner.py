"""
Scene Captioning using Salesforce BLIP (base).

Generates natural-language descriptions of video frames.
Model: Salesforce/blip-image-captioning-base (~1GB, downloaded on first use).
"""
from typing import Optional

# Lazy-load to avoid slow startup
_processor = None
_model = None
_loaded = False


def _load_blip():
    global _processor, _model, _loaded
    if _loaded:
        return

    try:
        from transformers import BlipProcessor, BlipForConditionalGeneration

        model_name = "Salesforce/blip-image-captioning-base"
        print(f"Loading BLIP model: {model_name} (first run downloads ~1GB)...")

        _processor = BlipProcessor.from_pretrained(model_name)
        _model = BlipForConditionalGeneration.from_pretrained(model_name)
        _model.eval()  # Set to eval mode for inference
        _loaded = True

        print("BLIP model loaded successfully.")
    except Exception as e:
        print(f"Warning: Could not load BLIP model: {e}")
        _loaded = True  # Don't retry on failure


def caption_frame(frame_path: str) -> Optional[str]:
    """
    Generate a natural-language caption for a video frame.

    Args:
        frame_path: Path to the frame image file.

    Returns:
        Caption string, e.g. "a person standing in a kitchen with a dog"
        Returns None if captioning fails.
    """
    _load_blip()

    if _processor is None or _model is None:
        return None

    try:
        from PIL import Image
        import torch

        image = Image.open(frame_path).convert("RGB")

        # Process image for BLIP
        inputs = _processor(image, return_tensors="pt")

        # Generate caption
        with torch.no_grad():
            output = _model.generate(
                **inputs,
                max_new_tokens=50,
                num_beams=3,       # beam search for better quality
                early_stopping=True,
            )

        caption = _processor.decode(output[0], skip_special_tokens=True)

        # Clean up common BLIP artifacts
        caption = caption.strip()
        if caption.startswith("arafed "):
            caption = caption[7:]  # Remove common BLIP hallucination prefix

        return caption if caption else None

    except Exception as e:
        print(f"BLIP captioning error: {e}")
        return None
