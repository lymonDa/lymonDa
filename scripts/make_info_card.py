#!/usr/bin/env python3
"""Generate the animated terminal/neofetch-style profile card."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "info-card.svg"
STATIC = os.getenv("STATIC") == "1"

rows = [
    ("Now", "Software Engineer & Product Builder"),
    ("Prev", "Front-End → Full-Stack Development"),
    ("Stack", "TypeScript · JavaScript · Python"),
    ("", "React · Next.js · Angular · Flutter"),
    ("", "Node.js · Express · Fastify"),
    ("", "REST APIs · Supabase · PostgreSQL · MongoDB"),
    ("", "Docker · CI/CD · GitHub Actions"),
    ("", "Cloud · Deployment · DevOps"),
    ("Focus", "Clean Code · SOLID · Design Patterns"),
    ("", "System Design · API Design · Testing"),
    ("Build", "Web Apps · Mobile Apps · SaaS · Product Development"),
]

W, H = 980, 590
out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="LymonDa profile information card">',
    "<defs>",
    "<linearGradient id=\"border\" x1=\"0\" x2=\"1\"><stop offset=\"0\" stop-color=\"#2b332e\"/><stop offset=\"1\" stop-color=\"#8f7a4a\"/></linearGradient>",
    "<style>",
    '.mono{font-family:"SFMono-Regular","Cascadia Code","Roboto Mono","DejaVu Sans Mono",monospace}',
    '@keyframes fadeUp{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}',
    '.line{animation:fadeUp .55s ease both}',
    '</style>',
    "</defs>",
    '<rect width="100%" height="100%" rx="18" fill="#0b0d0c" stroke="url(#border)" stroke-width="2"/>',
    '<rect x="1" y="1" width="978" height="58" rx="17" fill="#111513"/>',
    '<circle cx="27" cy="30" r="7" fill="#8f7a4a"/>',
    '<circle cx="51" cy="30" r="7" fill="#5f7f69"/>',
    '<circle cx="75" cy="30" r="7" fill="#d4d0c5"/>',
    '<text class="mono" x="105" y="37" fill="#e7e3d8" font-size="21">lymon@github — profile</text>',
    '<text class="mono" x="28" y="91" fill="#69f0a0" font-size="18">╭─ whoami</text>',
    '<text class="mono" x="28" y="119" fill="#e7e3d8" font-size="22">Abdulsattar Mohamed (lymonDa)</text>',
    '<text class="mono" x="28" y="145" fill="#a8ada7" font-size="16">Software Engineer &amp; Product Builder</text>',
]
y=184
for i,(key,val) in enumerate(rows):
    delay = 0 if STATIC else 0.65 + i*0.055
    fill = "#69f0a0" if key else "#a8ada7"
    xkey = 28
    xval = 148 if key else 28
    if key:
        out.append(f'<text class="mono line" style="animation-delay:{delay:.2f}s" x="{xkey}" y="{y}" fill="{fill}" font-size="16">{key:7}</text>')
        out.append(f'<text class="mono line" style="animation-delay:{delay:.2f}s" x="{xval}" y="{y}" fill="#e7e3d8" font-size="16">{val}</text>')
    else:
        out.append(f'<text class="mono line" style="animation-delay:{delay:.2f}s" x="{xval}" y="{y}" fill="#e7e3d8" font-size="16">{val}</text>')
    y += 29

out += [
    '<text class="mono" x="28" y="552" fill="#8f7a4a" font-size="15">status</text>',
    '<text class="mono" x="94" y="552" fill="#a8ada7" font-size="15">building useful products, one system at a time</text>',
    "</svg>"
]
OUTPUT.write_text("\n".join(out), encoding="utf-8")
print(f"Wrote {OUTPUT}")
