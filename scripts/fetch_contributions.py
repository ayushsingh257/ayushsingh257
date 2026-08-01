"""
GitHub Contribution Scraper and Metrics Generator.

Fetches GitHub user contribution calendar data by parsing HTML output,
extracts daily contribution counts and levels, and calculates statistics
including total yearly contributions, current streak, longest streak, best day,
and monthly totals.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_USERNAME = "ayushsingh257"
DEFAULT_OUTPUT_PATH = Path("data/contributions.json")
BASE_URL = "https://github.com/users/{username}/contributions"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_contributions_html(username: str = DEFAULT_USERNAME) -> str:
    """Download the GitHub contributions HTML for the given username.

    Args:
        username: GitHub username.

    Returns:
        HTML string content of the contributions page.

    Raises:
        requests.HTTPError: If the HTTP request fails.
    """
    url = BASE_URL.format(username=username)
    logger.info("Fetching contributions HTML from %s", url)
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def parse_tooltip_count(text: str) -> int:
    """Extract integer contribution count from tooltip text.

    Examples:
        - "No contributions on July 27th." -> 0
        - "1 contribution on June 29th." -> 1
        - "26 contributions on July 19th." -> 26

    Args:
        text: Raw text content of the tooltip.

    Returns:
        Integer number of contributions.
    """
    if not text:
        return 0

    text_clean = text.strip()
    if re.search(r"\bNo\s+contributions?\b", text_clean, re.IGNORECASE):
        return 0

    match = re.search(r"(\d+)\s+contributions?", text_clean, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return 0


def parse_contributions(html: str) -> List[Dict[str, Any]]:
    """Parse HTML content and extract daily contribution records.

    Args:
        html: Raw HTML string of GitHub contributions calendar.

    Returns:
        List of dicts containing date, count, and level for each day.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Map tooltip IDs to their text content
    tooltips: Dict[str, str] = {}
    for tooltip in soup.find_all("tool-tip"):
        if tooltip.has_attr("for"):
            tooltips[tooltip["for"]] = tooltip.get_text(strip=True)

    cells = soup.find_all("td", class_="ContributionCalendar-day")
    logger.info("Found %d contribution calendar cells", len(cells))

    records: List[Dict[str, Any]] = []

    for cell in cells:
        date_str = cell.get("data-date")
        if not date_str:
            continue

        level_str = cell.get("data-level", "0")
        try:
            level = int(level_str)
        except ValueError:
            level = 0

        cell_id = cell.get("id", "")
        tooltip_text = tooltips.get(cell_id, "")
        
        # Fallback if tooltip not in mapping: check aria-label or title attribute
        if not tooltip_text:
            tooltip_text = cell.get("aria-label") or cell.get("title") or ""

        count = parse_tooltip_count(tooltip_text)

        records.append({
            "date": date_str,
            "count": count,
            "level": level
        })

    # Sort chronologically by date
    records.sort(key=lambda item: item["date"])
    return records


def calculate_streaks(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Calculate current and longest active streaks.

    Args:
        records: List of daily contribution dicts sorted by date ascending.

    Returns:
        Tuple of (current_streak, longest_streak).
    """
    if not records:
        return 0, 0

    longest_streak = 0
    temp_streak = 0

    for item in records:
        if item["count"] > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    # Calculate current streak ending at latest date or yesterday
    current_streak = 0
    idx = len(records) - 1

    # If today has 0 contributions, check yesterday to allow maintaining streak today
    if records[idx]["count"] == 0 and idx > 0:
        idx -= 1

    while idx >= 0 and records[idx]["count"] > 0:
        current_streak += 1
        idx -= 1

    return current_streak, longest_streak


def calculate_best_day(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find the single day with the maximum contribution count.

    Args:
        records: List of daily contribution dicts.

    Returns:
        Dict with "date" and "count" of the best day.
    """
    if not records:
        return {"date": "", "count": 0}

    best = max(records, key=lambda item: item["count"])
    return {"date": best["date"], "count": best["count"]}


def calculate_monthly_totals(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Sum contribution counts per month (YYYY-MM).

    Args:
        records: List of daily contribution dicts.

    Returns:
        Dict mapping "YYYY-MM" string to total count for that month.
    """
    monthly: Dict[str, int] = {}
    for item in records:
        month_key = item["date"][:7]  # YYYY-MM
        monthly[month_key] = monthly.get(month_key, 0) + item["count"]
    return monthly


def process_contributions(username: str = DEFAULT_USERNAME) -> Dict[str, Any]:
    """Main workflow to fetch, parse, and aggregate GitHub contribution data.

    Args:
        username: GitHub username.

    Returns:
        Dictionary containing all structured data and calculated metrics.
    """
    html = fetch_contributions_html(username)
    records = parse_contributions(html)

    if not records:
        logger.warning("No contribution records parsed!")

    total_yearly = sum(item["count"] for item in records)
    current_streak, longest_streak = calculate_streaks(records)
    best_day = calculate_best_day(records)
    monthly_totals = calculate_monthly_totals(records)

    summary = {
        "username": username,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_yearly_contributions": total_yearly,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": monthly_totals,
        "contributions": records
    }

    return summary


def save_contributions(data: Dict[str, Any], output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    """Save structured contribution data to JSON file.

    Args:
        data: Dictionary of summary data and records.
        output_path: Path where JSON file will be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Successfully wrote contribution data to %s", output_path)


def main() -> None:
    """CLI entry point for contribution fetching."""
    data = process_contributions(DEFAULT_USERNAME)
    save_contributions(data, DEFAULT_OUTPUT_PATH)
    logger.info(
        "Summary: %d total contributions, current streak %d days, longest streak %d days",
        data["total_yearly_contributions"],
        data["current_streak"],
        data["longest_streak"]
    )


if __name__ == "__main__":
    main()
