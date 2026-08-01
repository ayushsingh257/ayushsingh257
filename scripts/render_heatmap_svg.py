"""
GitHub Contribution Heatmap SVG Generator (Cybersecurity SOC Terminal Theme).

Reads contribution data from JSON, renders a black & orange SOC-terminal themed
SVG contribution heatmap with horizontal column scanning animation, month spacing,
terminal styling, and live stats.
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

# Cybersecurity Black & Orange Palette
COLOR_BG = "#050505"
COLOR_CARD_BG = "#111111"
COLOR_BORDER = "#222222"
COLOR_ACCENT_ORANGE = "#ff6600"
COLOR_ACCENT_LIGHT_ORANGE = "#ff9900"
COLOR_TEXT_WHITE = "#f5f5f5"
COLOR_TEXT_MUTED = "#888888"

COLOR_LEVEL_0 = "#161616"
COLOR_LEVEL_1 = "#3d1600"
COLOR_LEVEL_2 = "#7a2e00"
COLOR_LEVEL_3 = "#c24100"
COLOR_LEVEL_4 = "#ff6600"

LEVEL_COLORS = {
    0: COLOR_LEVEL_0,
    1: COLOR_LEVEL_1,
    2: COLOR_LEVEL_2,
    3: COLOR_LEVEL_3,
    4: COLOR_LEVEL_4,
}

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_contribution_data(input_path: Path = DEFAULT_INPUT_PATH) -> Dict[str, Any]:
    """Load contribution metrics and daily records from JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        Dict containing summary stats and daily contribution records.

    Raises:
        FileNotFoundError: If input file doesn't exist.
    """
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


def build_svg(data: Dict[str, Any]) -> str:
    """Generate SVG markup for the cybersecurity terminal contribution heatmap.

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

    # Layout Parameters
    width = 910
    height = 240
    grid_x = 55
    grid_y = 95
    cell_size = 10
    cell_gap = 3.2
    step = cell_size + cell_gap
    month_gap = 14  # Extra gap between months to fulfill spacing requirement

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&amp;display=swap');
        
        .bg-canvas {{ fill: {COLOR_BG}; rx: 12px; }}
        .card-panel {{ fill: {COLOR_CARD_BG}; stroke: {COLOR_BORDER}; stroke-width: 1px; rx: 10px; }}
        .terminal-header {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 14px; font-weight: 700; fill: {COLOR_ACCENT_ORANGE}; }}
        .terminal-sub {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 11px; fill: {COLOR_TEXT_MUTED}; }}
        .stat-val {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 15px; font-weight: 700; fill: {COLOR_ACCENT_LIGHT_ORANGE}; }}
        .stat-lbl {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 10px; fill: {COLOR_TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.5px; }}
        .axis-lbl {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 9.5px; fill: {COLOR_TEXT_MUTED}; }}
        .legend-lbl {{ font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 9.5px; fill: {COLOR_TEXT_MUTED}; }}
        
        .sq {{
            rx: 2px;
            ry: 2px;
            stroke: #202020;
            stroke-width: 0.4px;
            transform-box: fill-box;
            transform-origin: center;
            opacity: 0;
            animation: colScanRipple 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }}
        
        @keyframes colScanRipple {{
            0% {{
                opacity: 0;
                transform: scale(0.2) translateY(-4px);
                filter: drop-shadow(0 0 0px transparent);
            }}
            60% {{
                opacity: 0.9;
                transform: scale(1.15);
                filter: drop-shadow(0 0 4px {COLOR_ACCENT_ORANGE});
            }}
            100% {{
                opacity: 1;
                transform: scale(1) translateY(0);
                filter: drop-shadow(0 0 0px transparent);
            }}
        }}
    </style>
    """

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{username}\'s SOC Contribution Heatmap">',
        css,
        f'<rect class="bg-canvas" x="0" y="0" width="{width}" height="{height}" />',
        f'<rect class="card-panel" x="8" y="8" width="{width - 16}" height="{height - 16}" />',
    ]

    # Header section: Terminal prompt & Username
    svg_parts.append(f'<text x="28" y="34" class="terminal-header">$ github_activity_monitor</text>')
    svg_parts.append(f'<text x="28" y="52" class="terminal-sub">User: {username} | Target: SOC_CORE_GRID</text>')

    # Stat Cards on top right
    stats_x_base = 450
    
    # Stat 1: Total Contributions
    svg_parts.append(f'<text x="{stats_x_base}" y="34" class="stat-val">{total_yearly:,}</text>')
    svg_parts.append(f'<text x="{stats_x_base}" y="50" class="stat-lbl">TOTAL CONTRIBS</text>')

    # Stat 2: Current Streak
    svg_parts.append(f'<text x="{stats_x_base + 150}" y="34" class="stat-val">{current_streak} Days</text>')
    svg_parts.append(f'<text x="{stats_x_base + 150}" y="50" class="stat-lbl">CURRENT STREAK</text>')

    # Stat 3: Longest Streak
    svg_parts.append(f'<text x="{stats_x_base + 290}" y="34" class="stat-val">{longest_streak} Days</text>')
    svg_parts.append(f'<text x="{stats_x_base + 290}" y="50" class="stat-lbl">LONGEST STREAK</text>')

    # Divider accent line
    svg_parts.append(f'<line x1="28" y1="64" x2="{width - 28}" y2="64" stroke="#222222" stroke-width="1" />')

    # Weekday labels on left
    day_indices = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    for row_idx, day_name in day_indices:
        label_y = grid_y + row_idx * step + cell_size - 1
        svg_parts.append(f'<text x="26" y="{label_y:.1f}" class="axis-lbl">{day_name}</text>')

    # Month offset calculation and grid positioning
    month_labels: List[Tuple[float, str]] = []
    month_gap_count = 0
    prev_month_str = ""

    for idx, item in enumerate(contributions):
        col = idx // 7
        row = idx % 7

        date_str = item["date"]
        count = item["count"]
        level = item.get("level", 0)
        fill_color = LEVEL_COLORS.get(level, COLOR_LEVEL_0)

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month_str = dt.strftime("%Y-%m")
        month_abbr = MONTH_NAMES[dt.month - 1]

        # Calculate month gaps at start of week (row == 0)
        if row == 0:
            if col > 0 and month_str != prev_month_str:
                month_gap_count += 1
                prev_month_str = month_str

            if col == 0:
                prev_month_str = month_str

            col_x = grid_x + col * step + month_gap_count * month_gap
            
            # Place month label if not overlapping
            if not month_labels or (col_x - month_labels[-1][0] >= 32):
                month_labels.append((col_x, month_abbr))

        x_pos = grid_x + col * step + month_gap_count * month_gap
        y_pos = grid_y + row * step

        # Animation delay based on column index (Horizontal scan ripple)
        # Delay increases from left (col 0) to right (col 52)
        delay_sec = col * 0.022

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
        svg_parts.append(f'<text x="{m_x:.1f}" y="{grid_y - 10}" class="axis-lbl">{m_name}</text>')

    # Bottom Legend Section
    legend_y = grid_y + 7 * step + 18
    legend_x = grid_x

    svg_parts.append(f'<text x="{legend_x}" y="{legend_y + 8}" class="legend-lbl">Less</text>')

    palette_colors = [COLOR_LEVEL_0, COLOR_LEVEL_1, COLOR_LEVEL_2, COLOR_LEVEL_3, COLOR_LEVEL_4]
    box_start_x = legend_x + 32
    for i, pcolor in enumerate(palette_colors):
        bx = box_start_x + i * 14
        svg_parts.append(
            f'<rect x="{bx}" y="{legend_y}" width="{cell_size}" height="{cell_size}" '
            f'rx="2" ry="2" fill="{pcolor}" stroke="#202020" stroke-width="0.4" />'
        )

    svg_parts.append(
        f'<text x="{box_start_x + len(palette_colors) * 14 + 6}" y="{legend_y + 8}" class="legend-lbl">More</text>'
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

    logger.info("Successfully generated cybersecurity heatmap SVG at %s", output_path)


def main() -> None:
    """CLI entry point for rendering heatmap SVG."""
    render_heatmap(DEFAULT_INPUT_PATH, DEFAULT_OUTPUT_PATH)


if __name__ == "__main__":
    main()
