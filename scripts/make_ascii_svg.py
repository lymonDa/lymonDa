#!/usr/bin/env python3
"""Convert source-prepped.png into a high-contrast, animated, README-safe ASCII portrait SVG."""
from pathlib import Path
from PIL import Image
import numpy as np
import html

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "source-prepped.png"
OUTPUT = ROOT / "avi-ascii.svg"

# ASCII ramp mapping bright pixels to sparse characters, dark pixels to dense characters
RAMP = " .`:-=+*cs#%@"
COLS = 52
ROWS = 38
SVG_WIDTH = 370
SVG_HEIGHT = 520
LEFT = 15
TOP = 50
ROW_HEIGHT = 12.0
FONT_SIZE = 10.8

def get_portrait_crop(img: Image.Image) -> Image.Image:
    """Find the upper-body portrait area to maximize face resolution and remove empty lower space."""
    arr = np.array(img)
    fg_mask = arr < 248
    row_counts = fg_mask.sum(axis=1)

    # Find the top of the head
    y_indices = np.where(row_counts > 5)[0]
    if len(y_indices) == 0:
        return img

    y_min = max(0, y_indices[0] - 5)

    # Check for empty gap between chest and lower torso/hands
    y_max = y_indices[-1]
    for y in range(y_min + 150, min(len(row_counts), y_max)):
        # If there is a run of rows with near-zero foreground, stop at chest
        if row_counts[y:y + 30].sum() < 10:
            y_max = y
            break

    # Find x bounds within the chosen vertical window
    sub_fg = fg_mask[y_min:y_max, :]
    col_counts = sub_fg.sum(axis=0)
    x_indices = np.where(col_counts > 2)[0]
    if len(x_indices) > 0:
        x_min = max(0, x_indices[0] - 10)
        x_max = min(img.width, x_indices[-1] + 10)
    else:
        x_min, x_max = 0, img.width

    return img.crop((x_min, y_min, x_max, y_max))

def normalize_foreground(arr: np.ndarray) -> np.ndarray:
    """Contrast-stretch foreground pixels to use full dynamic range."""
    fg = arr < 248
    if not fg.any():
        return arr

    p_low = np.percentile(arr[fg], 1.5)
    p_high = np.percentile(arr[fg], 98.5)

    norm = arr.copy().astype(float)
    if p_high > p_low:
        scaled = np.clip((arr[fg] - p_low) / (p_high - p_low) * 230.0, 0, 230)
        norm[fg] = scaled
    norm[~fg] = 255.0
    return norm.astype(np.uint8)

def main():
    if not INPUT.exists():
        raise SystemExit(f"{INPUT} not found. Run prep_photo.py first.")

    raw = Image.open(INPUT).convert("L")
    cropped = get_portrait_crop(raw)

    # Resize to character grid
    small = cropped.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    arr = normalize_foreground(np.array(small))

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" role="img" aria-label="Animated ASCII portrait of lymonDa">',
        "<defs>",
        "<style>",
        f'.mono{{font-family:"SFMono-Regular","Cascadia Code","Roboto Mono","DejaVu Sans Mono",monospace;letter-spacing:0.1px}}',
        f'.ascii{{font-family:"SFMono-Regular","Cascadia Code","Roboto Mono","DejaVu Sans Mono",monospace;font-size:{FONT_SIZE}px;fill:#1f2328;letter-spacing:0.1px;white-space:pre}}',
        '@keyframes rowIn{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}',
        '.row{animation:rowIn 0.25s ease-out forwards}',
        "</style>",
        "</defs>",
        # Clean white card background with rounded corners and border
        f'<rect width="100%" height="100%" rx="16" fill="#ffffff" stroke="#30363d" stroke-width="1.5"/>',
        # Terminal top bar
        f'<rect x="1" y="1" width="{SVG_WIDTH - 2}" height="32" rx="15" fill="#f6f8fa" stroke="#e1e4e8" stroke-width="0.5"/>',
        '<circle cx="18" cy="16" r="4.5" fill="#ff5f56"/>',
        '<circle cx="32" cy="16" r="4.5" fill="#ffbd2e"/>',
        '<circle cx="46" cy="16" r="4.5" fill="#27c93f"/>',
        f'<text class="mono" x="65" y="20" fill="#57606a" font-size="11">lymon@github — portrait</text>',
    ]

    ramp_len = len(RAMP)
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            val = arr[y, x]
            # Map bright (255) -> 0 (space), dark (0) -> max (dense character)
            idx = int((255 - val) / 255.0 * (ramp_len - 1))
            idx = max(0, min(ramp_len - 1, idx))
            chars.append(RAMP[idx])

        line_str = "".join(chars)
        text_escaped = html.escape(line_str)
        delay = y * 0.022
        baseline = TOP + (y + 1) * ROW_HEIGHT

        svg.append(
            f'<text class="ascii row" x="{LEFT}" y="{baseline:.1f}" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" dur="0.25s" begin="{delay:.3f}s" fill="freeze"/>'
            f'<animate attributeName="x" from="{LEFT - 8}" to="{LEFT}" dur="0.25s" begin="{delay:.3f}s" fill="freeze"/>'
            f'{text_escaped}'
            f'</text>'
        )

    svg.append("</svg>")
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"Generated {ROWS} rows ASCII portrait -> {OUTPUT} ({SVG_WIDTH}x{SVG_HEIGHT})")

if __name__ == "__main__":
    main()
