#!/usr/bin/env python3
"""Render data/contributions.json as a self-contained animated SVG."""
from pathlib import Path
import json, html
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
W, H = 1120, 270
LEFT, TOP = 30, 48
CELL, GAP = 14, 4
COLS, ROWS = 53, 7

def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    by_date = {x["date"]: x for x in data.get("days", [])}

    # Build columns by calendar order, oldest to newest.
    dates = sorted(by_date)
    if not dates:
        raise SystemExit("No contribution data available.")

    # Anchor the last 371 days to the 7-day grid.
    values = []
    for d in dates[-371:]:
        x = by_date[d]
        values.append((d, int(x.get("level", 0)), int(x.get("count", 0))))

    # Right-align the available days.
    while len(values) < COLS * ROWS:
        values.insert(0, ("", 0, 0))

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub contribution heatmap">',
        "<defs>",
        "<style>",
        '@keyframes reveal{from{opacity:0;transform:translate(-5px,-5px)}to{opacity:1;transform:translate(0,0)}}',
        '.cell{animation:reveal .5s cubic-bezier(.2,.7,.2,1) both}',
        '.mono{font-family:"SFMono-Regular","Cascadia Code","Roboto Mono","DejaVu Sans Mono",monospace}',
        "</style>",
        "</defs>",
        '<rect width="100%" height="100%" rx="18" fill="#0b0d0c" stroke="#252b27"/>',
        '<text class="mono" x="30" y="28" fill="#e7e3d8" font-size="16">lymon@github ~ $ ./contributions.sh</text>',
    ]

    for i,(d,level,count) in enumerate(values):
        col = i // ROWS
        row = i % ROWS
        x = LEFT + col*(CELL+GAP)
        y = TOP + row*(CELL+GAP)
        fill = PALETTE[min(4,max(0,level))]
        delay = (col + row) * 0.018
        if d:
            title = html.escape(f"{count} contributions on {d}")
            svg.append(f'<g class="cell" style="animation-delay:{delay:.3f}s"><rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="4" fill="{fill}"><title>{title}</title></rect></g>')
        else:
            svg.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="4" fill="{PALETTE[0]}"/>')

    total = int(data.get("total_last_year", 0))
    if data.get("fetched_at"):
        footer = f"{total:,} contributions in the last year"
    else:
        footer = "Awaiting first GitHub Actions sync"
    svg += [
        f'<text class="mono" x="30" y="168" fill="#a8ada7" font-size="14">{html.escape(footer)}</text>',
        '<text class="mono" x="30" y="194" fill="#8f7a4a" font-size="13">Less</text>',
    ]
    lx=72
    for i,color in enumerate(PALETTE):
        svg.append(f'<rect x="{lx+i*23}" y="183" width="15" height="15" rx="4" fill="{color}"/>')
    svg += [
        '<text class="mono" x="205" y="194" fill="#8f7a4a" font-size="13">More</text>',
        f'<text class="mono" x="30" y="232" fill="#5f7f69" font-size="13">streak {int(data.get("current_streak",0))}d</text>',
        f'<text class="mono" x="150" y="232" fill="#5f7f69" font-size="13">longest {int(data.get("longest_streak",0))}d</text>',
        f'<text class="mono" x="300" y="232" fill="#5f7f69" font-size="13">best day {int(data.get("best_day",{}).get("count",0))}</text>',
        "</svg>"
    ]
    OUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
