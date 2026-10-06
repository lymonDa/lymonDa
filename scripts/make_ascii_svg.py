#!/usr/bin/env python3
"""Convert source-prepped.png into an animated, README-safe SVG."""
from pathlib import Path
from PIL import Image
import html
import os

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "source-prepped.png"
OUTPUT = ROOT / "avi-ascii.svg"

RAMP = " .`:-=+*cs#%@"
WIDTH = 100
SVG_WIDTH = 900
LEFT = 18

def main():
    if not INPUT.exists():
        raise SystemExit("source-prepped.png not found. Run prep_photo.py first.")
    image = Image.open(INPUT).convert("L")
    aspect = image.height / image.width
    rows = max(35, int(WIDTH * aspect * 0.50))
    small = image.resize((WIDTH, rows), Image.Resampling.LANCZOS)

    cell_h = 13.0
    font_size = 13.0
    height = int(rows * cell_h + 34)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{height}" viewBox="0 0 {SVG_WIDTH} {height}" role="img" aria-label="Animated ASCII portrait">',
        "<defs>",
        '<style>',
        f'.ascii{{font-family:"SFMono-Regular","Cascadia Code","Roboto Mono","DejaVu Sans Mono",monospace;font-size:{font_size}px;fill:#e7e3d8;letter-spacing:0;}}',
        '@keyframes rowReveal{from{opacity:0;transform:translateX(-16px)}to{opacity:1;transform:translateX(0)}}',
        '.row{animation:rowReveal .62s cubic-bezier(.2,.7,.2,1) both}',
        '</style>',
        '</defs>',
        '<rect width="100%" height="100%" rx="18" fill="#0b0d0c"/>',
    ]

    px = small.load()
    for y in range(rows):
        chars = []
        for x in range(WIDTH):
            value = px[x, y]
            idx = int((255 - value) / 255 * (len(RAMP) - 1))
            chars.append(RAMP[idx])
        text = html.escape("".join(chars))
        delay = y * 0.028
        baseline = 20 + (y + 1) * cell_h
        out.append(
            f'<text class="ascii row" x="{LEFT}" y="{baseline:.1f}" '
            f'style="animation-delay:{delay:.3f}s;white-space:pre">{text}</text>'
        )

    out.append("</svg>")
    OUTPUT.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {OUTPUT}")

if __name__ == "__main__":
    main()
