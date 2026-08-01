"""
GitHub Contribution Heatmap SVG Generator.

Reads contribution data from JSON, renders a dark-themed, animated SVG contribution heatmap
with GitHub green palette, stats summary, month/day labels, legend, and diagonal cascade animation.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_INPUT_PATH = Path("data/contributions.json")
DEFAULT_OUTPUT_PATH = Path("assets/contrib-heatmap.svg")

# Palette constants as specified in requirements
COLOR_LEVEL_0 = "#161b22"
COLOR_LEVEL_1 = "#0e4429"
COLOR_LEVEL_2 = "#006d32"
COLOR_LEVEL_3 = "#26a641"
COLOR_LEVEL_4 = "#39d353"

LEVEL_COLORS = {
    0: COLOR_LEVEL_0,
    1: COLOR_LEVEL_1,
    2: COLOR_LEVEL_2,
    3: COLOR_LEVEL_3,
    4: COLOR_LEVEL_4,
}

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def load_contribution_data(input_path: Path = DEFAULT_INPUT_PATH) -> Dict[str, Any]:
    """Load contribution metrics and daily records from JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        Dict containing summary stats and daily contribution records.

    Raises:
        FileNotFoundError: If the input JSON file does not exist.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Contribution data file not found at {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info("Loaded contribution data for user '%s'", data.get("username", "unknown"))
    return data


def format_date_human(date_str: str) -> str:
    """Convert YYYY-MM-DD to a human readable format e.g. 'Jul 19, 2026'.

    Args:
        date_str: Date string in YYYY-MM-DD format.

    Returns:
        Formatted human-readable date.
    """
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return date_str


def build_svg(data: Dict[str, Any]) -> str:
    """Generate SVG markup for the contribution heatmap.

    Args:
        data: Dict containing metrics and daily records.

    Returns:
        Complete SVG string.
    """
    username = data.get("username", "ayushsingh257")
    total_yearly = data.get("total_yearly_contributions", 0)
    current_streak = data.get("current_streak", 0)
    longest_streak = data.get("longest_streak", 0)
    contributions: List[Dict[str, Any]] = data.get("contributions", [])

    # Canvas dimensions & grid parameters
    width = 890
    height = 225
    grid_x = 65
    grid_y = 85
    cell_size = 11
    cell_gap = 3.5
    step = cell_size + cell_gap

    # Generate CSS with keyframes for diagonal cascade reveal animation
    css = f"""
    <style>
        .card-bg {{ fill: #0d1117; stroke: #30363d; stroke-width: 1px; rx: 12px; }}
        .header-title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 700; fill: #c9d1d9; }}
        .header-sub {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 12px; fill: #8b949e; }}
        .stat-value {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; font-weight: 700; fill: {COLOR_LEVEL_4}; }}
        .stat-label {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 11px; fill: #8b949e; }}
        .axis-label {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 10px; fill: #8b949e; }}
        .legend-text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 10px; fill: #8b949e; }}
        .sq {{
            rx: 2.5px;
            ry: 2.5px;
            transform-box: fill-box;
            transform-origin: center;
            animation: cascadeReveal 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
        }}
        @keyframes cascadeReveal {{
            0% {{
                opacity: 0;
                transform: scale(0.15);
            }}
            65% {{
                transform: scale(1.15);
            }}
            100% {{
                opacity: 1;
                transform: scale(1);
            }}
        }}
    </style>
    """

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{username}\'s Contribution Heatmap">',
        css,
        f'<rect class="card-bg" x="0" y="0" width="{width}" height="{height}" />',
    ]

    # Header Section
    svg_parts.append(f'<text x="25" y="32" class="header-title">{username}</text>')
    svg_parts.append('<text x="25" y="50" class="header-sub">GitHub Contribution Calendar</text>')

    # Stats cards on top right
    stats_start_x = 420
    # Stat 1: Total Contributions
    svg_parts.append(f'<text x="{stats_start_x}" y="32" class="stat-value">{total_yearly:,}</text>')
    svg_parts.append(f'<text x="{stats_start_x}" y="48" class="stat-label">Yearly Contributions</text>')

    # Stat 2: Current Streak
    svg_parts.append(f'<text x="{stats_start_x + 160}" y="32" class="stat-value">{current_streak} Days</text>')
    svg_parts.append(f'<text x="{stats_start_x + 160}" y="48" class="stat-label">Current Streak</text>')

    # Stat 3: Longest Streak
    svg_parts.append(f'<text x="{stats_start_x + 310}" y="32" class="stat-value">{longest_streak} Days</text>')
    svg_parts.append(f'<text x="{stats_start_x + 310}" y="48" class="stat-label">Longest Streak</text>')

    # Day of week labels on left (Mon, Wed, Fri)
    day_indices = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    for row_idx, day_name in day_indices:
        label_y = grid_y + row_idx * step + cell_size - 2
        svg_parts.append(f'<text x="32" y="{label_y:.1f}" class="axis-label">{day_name}</text>')

    # Grid Cells & Month Labels
    month_labels: List[str] = []
    last_month_col = -10

    for idx, item in enumerate(contributions):
        col = idx // 7
        row = idx % 7

        date_str = item["date"]
        count = item["count"]
        level = item.get("level", 0)
        fill_color = LEVEL_COLORS.get(level, COLOR_LEVEL_0)

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month_abbr = MONTH_NAMES[dt.month - 1]

        # Detect month change at row 0 (start of week)
        if row == 0:
            if col - last_month_col >= 3:
                # Check if this month is different from last placed month
                last_placed_name = month_labels[-1][1] if month_labels else ""
                if month_abbr != last_placed_name:
                    month_x = grid_x + col * step
                    month_labels.append((month_x, month_abbr))
                    last_month_col = col

        x_pos = grid_x + col * step
        y_pos = grid_y + row * step

        # Animation delay calculation: diagonal cascade col + row
        diag_index = col + row
        delay_sec = diag_index * 0.012

        human_date = format_date_human(date_str)
        tooltip_text = f"{count} contribution{'s' if count != 1 else ''} on {human_date}"

        rect_elem = (
            f'<rect class="sq" x="{x_pos:.1f}" y="{y_pos:.1f}" width="{cell_size}" height="{cell_size}" '
            f'fill="{fill_color}" style="animation-delay: {delay_sec:.3f}s;">'
            f'<title>{tooltip_text}</title></rect>'
        )
        svg_parts.append(rect_elem)

    # Render Month Labels above grid
    for m_x, m_name in month_labels:
        svg_parts.append(f'<text x="{m_x:.1f}" y="{grid_y - 12}" class="axis-label">{m_name}</text>')

    # Bottom Legend Section
    legend_y = grid_y + 7 * step + 18
    legend_x = grid_x

    svg_parts.append(f'<text x="{legend_x}" y="{legend_y + 9}" class="legend-text">Less</text>')

    palette_colors = [COLOR_LEVEL_0, COLOR_LEVEL_1, COLOR_LEVEL_2, COLOR_LEVEL_3, COLOR_LEVEL_4]
    box_start_x = legend_x + 32
    for i, pcolor in enumerate(palette_colors):
        bx = box_start_x + i * 15
        svg_parts.append(
            f'<rect x="{bx}" y="{legend_y}" width="{cell_size}" height="{cell_size}" '
            f'rx="2.5" ry="2.5" fill="{pcolor}" />'
        )

    svg_parts.append(f'<text x="{box_start_x + len(palette_colors) * 15 + 6}" y="{legend_y + 9}" class="legend-text">More</text>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def render_heatmap(input_path: Path = DEFAULT_INPUT_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    """Load JSON data, render SVG, and write to output path.

    Args:
        input_path: Path to input JSON file.
        output_path: Path to output SVG file.
    """
    data = load_contribution_data(input_path)
    svg_content = build_svg(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    logger.info("Successfully generated heatmap SVG at %s", output_path)


def main() -> None:
    """CLI entry point for rendering heatmap SVG."""
    render_heatmap(DEFAULT_INPUT_PATH, DEFAULT_OUTPUT_PATH)


if __name__ == "__main__":
    main()
