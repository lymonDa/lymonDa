#!/usr/bin/env python3
"""Generate the animated terminal/neofetch-style profile info card as a self-contained SVG."""
from pathlib import Path
import html

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "info-card.svg"

W, H = 490, 520

def main():
    rows = [
        # (label, value, is_header_or_sub)
        ("Now", "Software Engineer & Product Builder", False),
        ("Prev", "Front-End → Full-Stack Development", False),
        ("Stack", "TypeScript · JavaScript · Python · Dart", False),
        ("", "React · Next.js · Angular · Flutter", True),
        ("", "Node.js · Express · Fastify", True),
        ("", "PostgreSQL · MongoDB · Supabase", True),
        ("", "REST APIs · System Design", True),
        ("", "Docker · CI/CD · GitHub Actions · DevOps", True),
        ("Focus", "Clean Code · SOLID · Design Patterns", False),
        ("Build", "Web · Mobile · SaaS · Product Engineering", False),
    ]

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="LymonDa profile information card">',
        "<defs>",
        '<linearGradient id="card-border" x1="0" y1="0" x2="1" y2="1">',
        '  <stop offset="0%" stop-color="#2b332e"/>',
        '  <stop offset="100%" stop-color="#8f7a4a"/>',
        '</linearGradient>',
        "<style>",
        '.mono{font-family:"SFMono-Regular","Cascadia Code","Roboto Mono","DejaVu Sans Mono",monospace}',
        '@keyframes fadeSlide{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}',
        '.line{animation:fadeSlide 0.4s ease-out forwards}',
        "</style>",
        "</defs>",
        f'<rect width="100%" height="100%" rx="16" fill="#0b0d0c" stroke="url(#card-border)" stroke-width="1.8"/>',
        # Top terminal bar
        f'<rect x="1" y="1" width="{W - 2}" height="32" rx="15" fill="#111513"/>',
        '<circle cx="18" cy="16" r="4.5" fill="#8f7a4a"/>',
        '<circle cx="32" cy="16" r="4.5" fill="#5f7f69"/>',
        '<circle cx="46" cy="16" r="4.5" fill="#d4d0c5"/>',
        f'<text class="mono" x="65" y="20" fill="#e7e3d8" font-size="11">lymon@github — profile</text>',
        # Header block
        '<g class="line" opacity="0">',
        '  <animate attributeName="opacity" from="0" to="1" dur="0.35s" begin="0.1s" fill="freeze"/>',
        '  <text class="mono" x="24" y="62" fill="#69f0a0" font-size="13" font-weight="600">╭─ whoami</text>',
        '  <text class="mono" x="24" y="86" fill="#e7e3d8" font-size="17" font-weight="700">Abdulsattar Mohamed (lymonDa)</text>',
        '  <text class="mono" x="24" y="107" fill="#a8ada7" font-size="12.5">Software Engineer &amp; Product Builder</text>',
        f'  <line x1="24" y1="122" x2="{W - 24}" y2="122" stroke="#252b27" stroke-width="1"/>',
        '</g>',
    ]

    base_y = 148
    line_spacing = 26
    start_delay = 0.30

    for i, (label, val, is_sub) in enumerate(rows):
        y = base_y + i * line_spacing
        delay = start_delay + i * 0.08
        val_escaped = html.escape(val)

        svg.append(f'<g class="line" opacity="0">')
        svg.append(f'  <animate attributeName="opacity" from="0" to="1" dur="0.35s" begin="{delay:.2f}s" fill="freeze"/>')
        svg.append(f'  <animateTransform attributeName="transform" type="translate" from="0 6" to="0 0" dur="0.35s" begin="{delay:.2f}s" fill="freeze"/>')

        if label:
            label_escaped = html.escape(f"{label:<6}")
            svg.append(f'  <text class="mono" x="24" y="{y}" fill="#69f0a0" font-size="12.5" font-weight="600">{label_escaped}</text>')
            svg.append(f'  <text class="mono" x="88" y="{y}" fill="#e7e3d8" font-size="12.5">{val_escaped}</text>')
        else:
            svg.append(f'  <text class="mono" x="88" y="{y}" fill="#c5c9c3" font-size="12.5">{val_escaped}</text>')

        svg.append('</g>')

    # Footer status
    status_delay = start_delay + len(rows) * 0.08 + 0.1
    status_y = H - 24
    svg += [
        f'<g class="line" opacity="0">',
        f'  <animate attributeName="opacity" from="0" to="1" dur="0.35s" begin="{status_delay:.2f}s" fill="freeze"/>',
        f'  <line x1="24" y1="{status_y - 20}" x2="{W - 24}" y2="{status_y - 20}" stroke="#252b27" stroke-width="1"/>',
        f'  <text class="mono" x="24" y="{status_y}" fill="#8f7a4a" font-size="11.5">status</text>',
        f'  <text class="mono" x="78" y="{status_y}" fill="#a8ada7" font-size="11.5">building useful products, one system at a time</text>',
        f'</g>',
        "</svg>"
    ]

    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"Generated info card -> {OUTPUT} ({W}x{H})")

if __name__ == "__main__":
    main()
