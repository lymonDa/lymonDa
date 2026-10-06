#!/usr/bin/env python3
"""
Prepare a portrait for ASCII conversion.

Usage:
    python scripts/prep_photo.py source-photo.jpg
Output:
    source-prepped.png
"""
from pathlib import Path
import sys
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "source-prepped.png"

def grabcut_fallback(img):
    import numpy as np
    import cv2
    arr = np.array(img.convert("RGB"))
    h, w = arr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    margin_x = max(8, int(w * 0.12))
    margin_y = max(8, int(h * 0.03))
    rect = (margin_x, margin_y, max(1, w - 2*margin_x), max(1, h - 2*margin_y))
    bgd = np.zeros((1,65), np.float64)
    fgd = np.zeros((1,65), np.float64)
    cv2.grabCut(arr, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")
    return Image.fromarray(fg).filter(ImageFilter.GaussianBlur(1.4))

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/prep_photo.py source-photo.jpg")
    src = Path(sys.argv[1])
    if not src.is_absolute():
        src = ROOT / src
    if not src.exists():
        raise SystemExit(f"Photo not found: {src}")

    img = Image.open(src).convert("RGB")

    # Keep the portrait readable by cropping away excessive empty background.
    w, h = img.size
    left = int(w * 0.04)
    right = int(w * 0.98)
    top = int(h * 0.12)
    bottom = int(h * 0.995)
    img = img.crop((left, top, right, bottom))

    try:
        from rembg import remove
        rgba = remove(img)
        alpha = rgba.getchannel("A")
        gray = ImageOps.grayscale(rgba.convert("RGB"))
        white = Image.new("L", gray.size, 255)
        mask = alpha.filter(ImageFilter.GaussianBlur(1.2))
        prepped = Image.composite(gray, white, mask)
    except Exception as exc:
        print(f"[warn] rembg unavailable/failed ({exc}); using OpenCV GrabCut fallback.")
        mask = grabcut_fallback(img)
        gray = ImageOps.grayscale(img)
        white = Image.new("L", gray.size, 255)
        prepped = Image.composite(gray, white, mask)

    prepped = ImageEnhance.Contrast(prepped).enhance(1.55)
    prepped = ImageEnhance.Sharpness(prepped).enhance(1.15)
    prepped.save(OUT)
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
