"""
GitHub Contribution Heatmap SVG Generator.

Reads contribution data from JSON, renders a responsive dark-themed SVG contribution heatmap
with GitHub green cells (#161b22, #0e4429, #006d32, #26a641, #39d353), left-to-right ripple animation,
deduplicated month labels, terminal aesthetics, and live stats.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_INPUT_PATH = Path("data/contributions.json")
DEFAULT_OUTPUT_PATH = Path("assets/contrib-heatmap.svg")

# Color Palette: Cybersecurity Black Card + GitHub Green Cells
COLOR_BG = "#050505"
COLOR_CARD_BG = "#111111"
COLOR_BORDER = "#222222"
COLOR_TEXT_WHITE = "#f5f5f5"
COLOR_TEXT_MUTED = "#8b949e"

# GitHub Green palette for contribution levels
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


def load_contribution_data(input_path: Path = DEFAULT_INPUT_PATH) -> Dict[str, Any]:
    """Load contribution metrics and daily records from JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Contribution data file not found at {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info("Loaded contribution data for user '%s'", data.get("username", "unknown"))
    return data


def format_date_human(date_str: str) -> str:
    """Convert YYYY-MM-DD to human readable format e.g. 'Jul 19, 2026'."""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return date_str


def get_deduplicated_month_labels(contributions: List[Dict[str, Any]]) -> List[Tuple[int, str]]:
    """Extract deduplicated month labels aligned with their first week column.

    Args:
        contributions: List of daily contribution dicts.

    Returns:
        List of tuples (col_index, month_name).
    """
    month_labels: List[Tuple[int, str]] = []
    seen_months: set[str] = set()

    num_weeks = len(contributions) // 7

    for col in range(num_weeks):
        sun_item = contributions[col * 7]
        dt = datetime.strptime(sun_item["date"], "%Y-%m-%d")
        m_name = MONTH_NAMES[dt.month - 1]

        # Ignore partial first month if it has less than 2 weeks room at start
        if m_name not in seen_months:
            if col >= 1 or m_name != "Jul":
                month_labels.append((col, m_name))
                seen_months.add(m_name)

    return month_labels


def build_svg(data: Dict[str, Any]) -> str:
    """Generate responsive SVG markup for the contribution heatmap.

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

    # Uniform GitHub Grid Parameters
    cell_size = 11
    cell_gap = 3.5
    step = cell_size + cell_gap

    grid_x = 55
    grid_y = 90
    
    view_width = 890
    view_height = 230

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&amp;display=swap');
        
        .bg-canvas {{ fill: {COLOR_BG}; rx: 12px; }}
        .card-panel {{ fill: {COLOR_CARD_BG}; stroke: {COLOR_BORDER}; stroke-width: 1px; rx: 10px; }}
        .terminal-header {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 14px; font-weight: 700; fill: {COLOR_LEVEL_4}; }}
        .terminal-sub {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 11px; fill: {COLOR_TEXT_MUTED}; }}
        .stat-val {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 15px; font-weight: 700; fill: {COLOR_LEVEL_4}; }}
        .stat-lbl {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 10px; fill: {COLOR_TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.5px; }}
        .axis-lbl {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 9.5px; fill: {COLOR_TEXT_MUTED}; }}
        .legend-lbl {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 9.5px; fill: {COLOR_TEXT_MUTED}; }}
        
        .sq {{
            rx: 2.2px;
            ry: 2.2px;
            transform-box: fill-box;
            transform-origin: center;
            opacity: 0;
            animation: colScanRipple 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }}
        
        @keyframes colScanRipple {{
            0% {{
                opacity: 0;
                transform: scale(0.2);
            }}
            65% {{
                opacity: 0.95;
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
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_width} {view_height}" width="100%" height="100%" role="img" aria-label="{username}\'s Contribution Heatmap">',
        css,
        f'<rect class="bg-canvas" x="0" y="0" width="{view_width}" height="{view_height}" />',
        f'<rect class="card-panel" x="8" y="8" width="{view_width - 16}" height="{view_height - 16}" />',
    ]

    # Terminal Header
    svg_parts.append(f'<text x="28" y="34" class="terminal-header">$ github_activity_monitor</text>')
    svg_parts.append(f'<text x="28" y="52" class="terminal-sub">User: {username} | Status: ONLINE</text>')

    # Stats Summary (Top Right)
    stats_x_base = 430
    
    # Stat 1: Total Contributions
    svg_parts.append(f'<text x="{stats_x_base}" y="34" class="stat-val">{total_yearly:,}</text>')
    svg_parts.append(f'<text x="{stats_x_base}" y="50" class="stat-lbl">TOTAL CONTRIBS</text>')

    # Stat 2: Current Streak
    svg_parts.append(f'<text x="{stats_x_base + 150}" y="34" class="stat-val">{current_streak} Days</text>')
    svg_parts.append(f'<text x="{stats_x_base + 150}" y="50" class="stat-lbl">CURRENT STREAK</text>')

    # Stat 3: Longest Streak
    svg_parts.append(f'<text x="{stats_x_base + 290}" y="34" class="stat-val">{longest_streak} Days</text>')
    svg_parts.append(f'<text x="{stats_x_base + 290}" y="50" class="stat-lbl">LONGEST STREAK</text>')

    # Header Separator Line
    svg_parts.append(f'<line x1="28" y1="64" x2="{view_width - 28}" y2="64" stroke="#222222" stroke-width="1" />')

    # Weekday labels on left (Mon, Wed, Fri)
    day_indices = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    for row_idx, day_name in day_indices:
        label_y = grid_y + row_idx * step + cell_size - 1
        svg_parts.append(f'<text x="26" y="{label_y:.1f}" class="axis-lbl">{day_name}</text>')

    # Deduplicated Month Labels (Above grid)
    month_labels = get_deduplicated_month_labels(contributions)
    for col_idx, m_name in month_labels:
        m_x = grid_x + col_idx * step
        svg_parts.append(f'<text x="{m_x:.1f}" y="{grid_y - 10}" class="axis-lbl">{m_name}</text>')

    # Render Grid Cells with left-to-right ripple delay
    for idx, item in enumerate(contributions):
        col = idx // 7
        row = idx % 7

        date_str = item["date"]
        count = item["count"]
        level = item.get("level", 0)
        fill_color = LEVEL_COLORS.get(level, COLOR_LEVEL_0)

        x_pos = grid_x + col * step
        y_pos = grid_y + row * step

        # Animation delay based on column index (Left to Right ripple)
        delay_sec = col * 0.022

        human_date = format_date_human(date_str)
        tooltip_text = f"{count} contribution{'s' if count != 1 else ''} on {human_date}"

        rect_elem = (
            f'<rect class="sq" x="{x_pos:.1f}" y="{y_pos:.1f}" width="{cell_size}" height="{cell_size}" '
            f'fill="{fill_color}" style="animation-delay: {delay_sec:.3f}s;">'
            f'<title>{tooltip_text}</title></rect>'
        )
        svg_parts.append(rect_elem)

    # Bottom Legend Section
    legend_y = grid_y + 7 * step + 16
    legend_x = grid_x

    svg_parts.append(f'<text x="{legend_x}" y="{legend_y + 8}" class="legend-lbl">Less</text>')

    palette_colors = [COLOR_LEVEL_0, COLOR_LEVEL_1, COLOR_LEVEL_2, COLOR_LEVEL_3, COLOR_LEVEL_4]
    box_start_x = legend_x + 32
    for i, pcolor in enumerate(palette_colors):
        bx = box_start_x + i * 15
        svg_parts.append(
            f'<rect x="{bx}" y="{legend_y}" width="{cell_size}" height="{cell_size}" '
            f'rx="2" ry="2" fill="{pcolor}" />'
        )

    svg_parts.append(
        f'<text x="{box_start_x + len(palette_colors) * 15 + 6}" y="{legend_y + 8}" class="legend-lbl">More</text>'
    )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def render_heatmap(input_path: Path = DEFAULT_INPUT_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    """Load JSON data, render SVG, and write to output path."""
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
