#!/usr/bin/env python3
"""Render data/contributions.json as a self-contained animated SVG with guaranteed grid visibility."""
from pathlib import Path
from datetime import datetime, date, timedelta
import json, html, sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

# Distinct GitHub contribution palette with crisp level-0 stroke
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
STROKES = ["#252d38", "#195e3a", "#0e8542", "#2ec850", "#48e864"]

W, H = 860, 220
LEFT, TOP = 40, 48
CELL, GAP = 11.5, 3.2
COLS, ROWS = 53, 7

def validate_and_load_data() -> dict:
    """Load and validate data/contributions.json with fallback."""
    if not DATA.exists():
        print(f"[warn] {DATA} does not exist. Creating default zero-contribution grid.", file=sys.stderr)
        return {"days": [], "total_last_year": 0, "current_streak": 0, "longest_streak": 0}

    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        if not isinstance(data.get("days"), list) or len(data["days"]) == 0:
            print(f"[warn] {DATA} contains no days list. Rendering level-0 grid.", file=sys.stderr)
            data["days"] = []
        return data
    except Exception as e:
        print(f"[error] Failed to parse {DATA}: {e}", file=sys.stderr)
        return {"days": [], "total_last_year": 0, "current_streak": 0, "longest_streak": 0}

def main():
    data = validate_and_load_data()
    days_list = data.get("days", [])
    by_date = {x["date"]: x for x in days_list if "date" in x}

    if days_list:
        try:
            start_d = datetime.strptime(days_list[0]["date"], "%Y-%m-%d").date()
            end_d = datetime.strptime(days_list[-1]["date"], "%Y-%m-%d").date()
        except Exception:
            end_d = date.today()
            start_d = end_d - timedelta(days=364)
    else:
        end_d = date.today()
        start_d = end_d - timedelta(days=364)

    # In GitHub calendar: Sunday is row 0, Saturday is row 6.
    # Python weekday(): Monday is 0 ... Sunday is 6.
    # Convert to Sunday=0: (weekday() + 1) % 7
    start_sun = start_d - timedelta(days=(start_d.weekday() + 1) % 7)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub contribution heatmap">',
        "<defs>",
        "<style>",
        '.mono{font-family:"SFMono-Regular","Cascadia Code","Roboto Mono","DejaVu Sans Mono",monospace}',
        '@keyframes popIn{from{opacity:0;transform:scale(0.8)}to{opacity:1;transform:scale(1)}}',
        '.cell{animation:popIn 0.3s ease-out forwards;transform-origin:center;transform-box:fill-box}',
        "</style>",
        "</defs>",
        f'<rect width="100%" height="100%" rx="16" fill="#0b0d0c" stroke="#252b27" stroke-width="1.5"/>',
        '<text class="mono" x="40" y="28" fill="#e7e3d8" font-size="14" font-weight="600">lymon@github ~ $ ./contributions.sh</text>',
    ]

    total_cells = 0
    for col in range(COLS):
        for row in range(ROWS):
            cell_date = start_sun + timedelta(days=col * 7 + row)
            x = LEFT + col * (CELL + GAP)
            y = TOP + row * (CELL + GAP)
            delay = (col + row) * 0.012

            date_str = cell_date.isoformat()
            if cell_date > end_d:
                # Future day in current week: render faint dashed placeholder
                continue

            day_info = by_date.get(date_str)
            if day_info is not None:
                level = min(4, max(0, int(day_info.get("level", 0))))
                count = int(day_info.get("count", 0))
            else:
                level = 0
                count = 0

            fill = PALETTE[level]
            stroke = STROKES[level]
            title = html.escape(f"{count} contributions on {date_str}")
            total_cells += 1

            svg.append(
                f'<g class="cell" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" dur="0.25s" begin="{delay:.3f}s" fill="freeze"/>'
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2.5" fill="{fill}" stroke="{stroke}" stroke-width="0.7">'
                f'<title>{title}</title>'
                f'</rect>'
                f'</g>'
            )

    total = int(data.get("total_last_year", 0))
    current_streak = int(data.get("current_streak", 0))
    longest_streak = int(data.get("longest_streak", 0))
    best_day = data.get("best_day", {})
    best_count = int(best_day.get("count", 0)) if isinstance(best_day, dict) else 0

    if data.get("fetched_at"):
        footer = f"{total:,} contributions in the last year"
    else:
        footer = "Zero contributions recorded or awaiting sync"

    svg += [
        f'<text class="mono" x="40" y="174" fill="#a8ada7" font-size="13">{html.escape(footer)}</text>',
        '<text class="mono" x="40" y="198" fill="#8f7a4a" font-size="12">Less</text>',
    ]

    lx = 76
    for i, (color, strk) in enumerate(zip(PALETTE, STROKES)):
        svg.append(f'<rect x="{lx + i * 18}" y="188" width="12" height="12" rx="2.5" fill="{color}" stroke="{strk}" stroke-width="0.7"/>')

    svg += [
        f'<text class="mono" x="{lx + 5 * 18 + 8}" y="198" fill="#8f7a4a" font-size="12">More</text>',
        f'<text class="mono" x="510" y="198" fill="#5f7f69" font-size="12">streak {current_streak}d · longest {longest_streak}d · best {best_count}</text>',
        "</svg>"
    ]

    OUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"Rendered {total_cells} contribution cells to {OUT}")

if __name__ == "__main__":
    main()
