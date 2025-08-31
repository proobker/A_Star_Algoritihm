import numpy as np
from PIL import Image

MAX_DIM = 1024

def load_image_as_array(path: str) -> np.ndarray:
    """Load image as grayscale numpy array (uint8)."""
    img = Image.open(path).convert("L")
    w, h = img.size
    scale = min(MAX_DIM / max(w, h), 1.0)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS) # type: ignore
    return np.asarray(img, dtype=np.uint8)

def make_walkable_mask(gray: np.ndarray, invert: bool, auto_threshold: bool, thresh: int) -> np.ndarray:
    """Create a boolean walkability mask from grayscale image."""
    if auto_threshold:
        t = int(np.percentile(gray, 60))
    else:
        t = int(np.clip(thresh, 0, 255))
    return gray > t if not invert else gray < t
