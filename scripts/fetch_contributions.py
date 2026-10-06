#!/usr/bin/env python3
"""Fetch a user's public GitHub contribution calendar without an API token."""
from pathlib import Path
from datetime import datetime, timezone, timedelta, date
import json, re, sys, time
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "lymonDa"
URL = f"https://github.com/users/{USERNAME}/contributions"
DATA_DIR = ROOT / "data"
OUT = DATA_DIR / "contributions.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"https://github.com/{USERNAME}",
}

def parse_count(text: str) -> int:
    """Extract contribution count from text like '5 contributions on Oct 5'."""
    if not text:
        return 0
    m = re.search(r"([\d,]+)\s+contribution", text, flags=re.I)
    if m:
        return int(m.group(1).replace(",", ""))
    m_no = re.search(r"no\s+contribution", text, flags=re.I)
    if m_no:
        return 0
    return 0

def generate_fallback_calendar(days_count: int = 371) -> list:
    """Generate a valid zero-contribution calendar for the past ~53 weeks."""
    today = date.today()
    days = []
    start = today - timedelta(days=days_count - 1)
    for i in range(days_count):
        cur = start + timedelta(days=i)
        days.append({
            "date": cur.isoformat(),
            "count": 0,
            "level": 0,
        })
    return days

def validate_days(days: list) -> bool:
    """Validate that days list has expected schema and minimum length."""
    if not isinstance(days, list) or len(days) < 350:
        return False
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for d in days:
        if not isinstance(d, dict):
            return False
        if not date_regex.match(d.get("date", "")):
            return False
        level = d.get("level")
        if not isinstance(level, int) or level < 0 or level > 4:
            return False
        count = d.get("count")
        if not isinstance(count, int) or count < 0:
            return False
    return True

def fetch_with_retry(max_retries: int = 5) -> str:
    """Fetch contribution HTML with exponential backoff retry."""
    last_err = None
    session = requests.Session()
    for attempt in range(1, max_retries + 1):
        try:
            r = session.get(URL, headers=HEADERS, timeout=15)
            r.raise_for_status()
            if r.status_code == 200 and len(r.text) > 1000:
                return r.text
        except Exception as e:
            last_err = e
            print(f"[warn] Fetch attempt {attempt}/{max_retries} failed: {e}", file=sys.stderr)
            if attempt < max_retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to fetch contributions from GitHub after {max_retries} attempts: {last_err}")

def parse_contributions(html_text: str) -> list:
    """Parse contribution cells from GitHub HTML."""
    soup = BeautifulSoup(html_text, "html.parser")

    # Try multiple selector strategies for GitHub's evolving HTML
    cells = soup.select("table.ContributionCalendar-grid td.ContributionCalendar-day[data-date]")
    if not cells:
        cells = soup.select(".ContributionCalendar-day[data-date]")
    if not cells:
        cells = soup.select("td[data-date][data-level]")
    if not cells:
        cells = soup.select("[data-date][data-level]")
    if not cells:
        cells = soup.select("td[data-date]")

    if not cells:
        raise ValueError("No contribution cells found in GitHub HTML.")

    # Parse tooltips which carry exact counts: id -> count
    tooltip_counts = {}
    for tip in soup.find_all(["tool-tip", "div"], attrs={"for": True}):
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
            # Check cell text or aria-label
            cell_text = cell.get("aria-label") or cell.get_text(" ", strip=True)
            count = parse_count(cell_text)

        # Fallback: if level > 0 and count is 0, estimate minimum count
        if level > 0 and count == 0:
            count = level

        days.append({"date": d, "count": count, "level": level})

    # Deduplicate and sort chronologically
    unique = {x["date"]: x for x in days}
    sorted_days = [unique[k] for k in sorted(unique)]
    return sorted_days

def compute_metrics(days: list) -> dict:
    """Compute total, streaks, and best day."""
    counts = [d["count"] for d in days]
    total = sum(counts)

    # Current streak (working backwards from last day)
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # Longest streak & best day
    longest_streak = 0
    run = 0
    best_day = {"date": None, "count": 0}
    for d in days:
        if d["count"] > 0:
            run += 1
            longest_streak = max(longest_streak, run)
        else:
            run = 0
        if d["count"] > best_day["count"]:
            best_day = {"date": d["date"], "count": d["count"]}

    return {
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
    }

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    days = None
    fetch_failed = False

    try:
        html_text = fetch_with_retry(max_retries=5)
        parsed_days = parse_contributions(html_text)
        if validate_days(parsed_days):
            days = parsed_days
        else:
            print(f"[warn] Parsed {len(parsed_days)} days, which is less than expected minimum 350.", file=sys.stderr)
            fetch_failed = True
    except Exception as exc:
        print(f"[warn] GitHub contribution fetch failed: {exc}", file=sys.stderr)
        fetch_failed = True

    if days is None:
        # Check if existing contributions.json is valid
        if OUT.exists():
            try:
                existing = json.loads(OUT.read_text(encoding="utf-8"))
                if validate_days(existing.get("days", [])):
                    print(f"[info] Preserving existing valid contributions.json ({len(existing['days'])} days).")
                    return
            except Exception:
                pass
        # Fallback to empty 53-week calendar
        print("[info] Using baseline level-0 contribution calendar as fallback.")
        days = generate_fallback_calendar(371)

    metrics = compute_metrics(days)
    payload = {
        "username": USERNAME,
        "source": URL,
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        **metrics,
        "days": days,
    }

    # Atomic write
    tmp_out = OUT.with_suffix(".tmp")
    tmp_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_out.replace(OUT)
    print(f"Fetched {len(days)} days / {metrics['total_last_year']} contributions for {USERNAME}.")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
