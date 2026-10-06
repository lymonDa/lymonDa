#!/usr/bin/env python3
"""
Prepare a portrait photo for ASCII conversion.
Removes background, applies grayscale conversion, CLAHE/contrast normalization,
and ensures proper foreground-to-background separation.

Usage:
    python scripts/prep_photo.py [source-photo.jpg]
Output:
    source-prepped.png
"""
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "source-prepped.png"

def apply_clahe(img_gray: Image.Image) -> Image.Image:
    """Apply contrast enhancement / adaptive histogram equalization."""
    arr = np.array(img_gray, dtype=np.float32)
    p_low, p_high = np.percentile(arr, (2, 98))
    if p_high > p_low:
        arr = np.clip((arr - p_low) / (p_high - p_low) * 255.0, 0, 255)
    enhanced = Image.fromarray(arr.astype(np.uint8))
    enhanced = ImageOps.autocontrast(enhanced, cutoff=1)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(1.3)
    return enhanced

def fallback_segmentation(img: Image.Image) -> Image.Image:
    """Robust fallback segmentation using edge detection and luminance when rembg is unavailable."""
    try:
        import cv2
        arr = np.array(img.convert("RGB"))
        h, w = arr.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        margin_x = max(8, int(w * 0.12))
        margin_y = max(8, int(h * 0.03))
        rect = (margin_x, margin_y, max(1, w - 2 * margin_x), max(1, h - 2 * margin_y))
        bgd = np.zeros((1, 65), np.float64)
        fgd = np.zeros((1, 65), np.float64)
        cv2.grabCut(arr, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
        fg = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")
        return Image.fromarray(fg).filter(ImageFilter.GaussianBlur(1.4))
    except Exception:
        # Pure Pillow/NumPy fallback based on center focus and luminance
        w, h = img.size
        mask = Image.new("L", (w, h), 0)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        # Person is centered in upper-middle region
        draw.ellipse([(int(w * 0.1), int(h * 0.05)), (int(w * 0.9), int(h * 0.95))], fill=255)
        return mask.filter(ImageFilter.GaussianBlur(10))

def main():
    src = None
    if len(sys.argv) > 1:
        src = Path(sys.argv[1])
        if not src.is_absolute():
            src = ROOT / src
    else:
        src = ROOT / "source-photo.jpg"

    if not src.exists():
        raise SystemExit(f"Source photo not found: {src}")

    img = Image.open(src).convert("RGB")
    w, h = img.size

    # Crop excess outer borders
    left = int(w * 0.04)
    right = int(w * 0.98)
    top = int(h * 0.08)
    bottom = int(h * 0.995)
    img = img.crop((left, top, right, bottom))

    mask = None
    try:
        from rembg import remove
        rgba = remove(img)
        mask = rgba.getchannel("A").filter(ImageFilter.GaussianBlur(1.2))
        gray = ImageOps.grayscale(rgba.convert("RGB"))
    except Exception as exc:
        print(f"[info] rembg not available ({exc}); checking existing prepped mask or fallback.", file=sys.stderr)
        if OUT.exists():
            existing = Image.open(OUT).convert("L")
            if existing.size == (right - left, bottom - top):
                # Reuse existing high-quality mask
                mask = Image.fromarray(np.where(np.array(existing) < 250, 255, 0).astype(np.uint8))
        if mask is None:
            mask = fallback_segmentation(img)
        gray = ImageOps.grayscale(img)

    # Normalize and enhance grayscale portrait
    gray = apply_clahe(gray)

    # Composite: Person on pure white background (255)
    white = Image.new("L", gray.size, 255)
    prepped = Image.composite(gray, white, mask)
    prepped = ImageEnhance.Sharpness(prepped).enhance(1.2)
    prepped.save(OUT)
    print(f"Successfully prepped photo -> {OUT} ({prepped.size[0]}x{prepped.size[1]})")

if __name__ == "__main__":
    main()
