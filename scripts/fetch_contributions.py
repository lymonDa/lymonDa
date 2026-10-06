#!/usr/bin/env python3
"""Fetch a user's public GitHub contribution calendar without a token."""
from pathlib import Path
from datetime import date, datetime, timedelta
import json, re, sys
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "lymonDa"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = ROOT / "data" / "contributions.json"

HEADERS = {
    "User-Agent": "lymonDa-profile-art/1.0",
    "Accept": "text/html,application/xhtml+xml",
    "Referer": f"https://github.com/{USERNAME}",
}

def parse_count(text):
    m = re.search(r"([\d,]+)\s+contribution", text, flags=re.I)
    return int(m.group(1).replace(",", "")) if m else 0

def fetch():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    cells = soup.select(".ContributionCalendar-day[data-date]")
    if not cells:
        cells = soup.select("[data-date][data-level]")
    if not cells:
        raise RuntimeError("GitHub contribution cells were not found; GitHub may have changed its HTML.")

    # Tooltips carry exact counts. Build id -> count map first.
    tooltip_counts = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if target:
            tooltip_counts[target] = parse_count(tip.get_text(" ", strip=True))

    days = []
    for cell in cells:
        d = cell.get("data-date")
        if not d:
            continue
        try:
            level = max(0, min(4, int(cell.get("data-level", "0"))))
        except ValueError:
            level = 0
        count = tooltip_counts.get(cell.get("id"))
        if count is None:
            count = parse_count(cell.get_text(" ", strip=True))
        days.append({"date": d, "count": count, "level": level})

    # Deduplicate and sort.
    unique = {x["date"]: x for x in days}
    days = [unique[k] for k in sorted(unique)]
    if len(days) < 300:
        raise RuntimeError(f"Only {len(days)} contribution days parsed; refusing to publish incomplete data.")

    counts = [d["count"] for d in days]
    total = sum(counts)

    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break

    longest = best = 0
    run = 0
    best_day = {"date": None, "count": 0}
    for d in days:
        if d["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
        if d["count"] > best_day["count"]:
            best_day = {"date": d["date"], "count": d["count"]}

    payload = {
        "username": USERNAME,
        "source": URL,
        "fetched_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "total_last_year": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best_day,
        "days": days,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Fetched {len(days)} days / {total} contributions for {USERNAME}.")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    fetch()
