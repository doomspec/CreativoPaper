"""Standalone HTML+SVG figures and the headless-Chrome PNG renderer."""

from __future__ import annotations

import html
import math
import shutil
import subprocess
from pathlib import Path


def html_page(title: str, subtitle: str, svg: str, width: int = 1200, height: int = 760) -> str:
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
  html, body {{
    margin: 0;
    width: {width}px;
    height: {height}px;
    background: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    color: #17202a;
  }}
  .frame {{
    width: {width}px;
    height: {height}px;
    box-sizing: border-box;
    padding: 34px 40px 28px;
    display: flex;
    flex-direction: column;
  }}
  h1 {{
    margin: 0;
    font-size: 30px;
    font-weight: 760;
    letter-spacing: 0;
  }}
  .subtitle {{
    margin-top: 6px;
    font-size: 16px;
    color: #44546a;
  }}
  svg {{
    margin-top: 22px;
    width: 100%;
    flex: 1 1 auto;
    min-height: 0;
    display: block;
  }}
</style>
</head>
<body>
<div class="frame">
  <h1>{html.escape(title)}</h1>
  <div class="subtitle">{html.escape(subtitle)}</div>
  {svg}
</div>
</body>
</html>
"""


def axis_ticks(y_min: float, y_max: float, count: int = 5) -> list[float]:
    step = (y_max - y_min) / (count - 1)
    return [y_min + i * step for i in range(count)]


def bar_chart_svg(
    series: list[dict],
    *,
    width: int = 1120,
    height: int = 560,
    y_min: float = 850,
    y_max: float = 1100,
    ylabel: str = "Mean Elo",
    legend: bool = True,
) -> str:
    left, right, top, bottom = 72, 28, 32, 92
    plot_w = width - left - right
    plot_h = height - top - bottom
    groups = []
    for datum in series:
        if datum["group"] not in groups:
            groups.append(datum["group"])
    colors = {
        "LLM-only": "#2f80ed",
        "Graph": "#27ae60",
        "Oral anchor": "#7f8c8d",
        "Oral": "#27ae60",
        "Poster": "#c0392b",
    }

    def y(v: float) -> float:
        return top + (y_max - v) / (y_max - y_min) * plot_h

    parts = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    parts.append('<rect width="100%" height="100%" fill="#fff"/>')
    for tick in axis_ticks(y_min, y_max):
        yy = y(tick)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" stroke="#d9dee7" stroke-width="1"/>')
        parts.append(f'<text x="{left-12}" y="{yy+4:.1f}" text-anchor="end" font-size="13" fill="#52616f">{tick:.0f}</text>')
    parts.append(f'<text x="20" y="{top + plot_h/2}" transform="rotate(-90 20 {top + plot_h/2})" font-size="14" fill="#52616f">{html.escape(ylabel)}</text>')

    group_w = plot_w / len(groups)
    label_order = {
        "LLM-only": 0,
        "Poster": 1,
        "Oral anchor": 1,
        "Oral": 2,
        "Graph": 2,
    }
    for gi, group in enumerate(groups):
        entries = [d for d in series if d["group"] == group]
        entries.sort(key=lambda d: (label_order.get(d["label"], 99), d["label"]))
        bar_gap = 8
        bar_w = min(74, (group_w - 56) / len(entries) - bar_gap)
        start = left + gi * group_w + (group_w - (bar_w + bar_gap) * len(entries) + bar_gap) / 2
        for ei, d in enumerate(entries):
            x = start + ei * (bar_w + bar_gap)
            yy = y(d["value"])
            hh = top + plot_h - yy
            color = colors.get(d["label"], "#556b8e")
            parts.append(f'<rect x="{x:.1f}" y="{yy:.1f}" width="{bar_w:.1f}" height="{hh:.1f}" rx="4" fill="{color}"/>')
            parts.append(f'<text x="{x+bar_w/2:.1f}" y="{yy-8:.1f}" text-anchor="middle" font-size="13" font-weight="700" fill="#17202a">{d["value"]:.1f}</text>')
            if "ci95" in d:
                lo, hi = d["ci95"]
                ylo, yhi = y(lo), y(hi)
                cx = x + bar_w / 2
                parts.append(f'<line x1="{cx:.1f}" y1="{yhi:.1f}" x2="{cx:.1f}" y2="{ylo:.1f}" stroke="#17202a" stroke-width="2"/>')
                parts.append(f'<line x1="{cx-9:.1f}" y1="{yhi:.1f}" x2="{cx+9:.1f}" y2="{yhi:.1f}" stroke="#17202a" stroke-width="2"/>')
                parts.append(f'<line x1="{cx-9:.1f}" y1="{ylo:.1f}" x2="{cx+9:.1f}" y2="{ylo:.1f}" stroke="#17202a" stroke-width="2"/>')
        parts.append(f'<text x="{left + gi*group_w + group_w/2:.1f}" y="{height-44}" text-anchor="middle" font-size="16" font-weight="650" fill="#17202a">{html.escape(group)}</text>')

    if legend:
        labels = []
        for d in series:
            if d["label"] not in labels:
                labels.append(d["label"])
        lx = left
        ly = height - 18
        for label in labels:
            color = colors.get(label, "#556b8e")
            parts.append(f'<rect x="{lx}" y="{ly-12}" width="14" height="14" rx="3" fill="{color}"/>')
            parts.append(f'<text x="{lx+20}" y="{ly}" font-size="14" fill="#34495e">{html.escape(label)}</text>')
            lx += 120 if len(label) < 7 else 160
    parts.append("</svg>")
    return "".join(parts)


def diversity_cost_svg(results: dict, width: int = 1180, height: int = 560) -> str:
    """Three-arm diversity vs cost figure (LLM-only / Abstracts agent / ReprNet agent)."""
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img">',
             '<rect width="100%" height="100%" fill="#fff"/>']

    C_PROMPT = "#2f80ed"
    C_FLAT = "#e67e22"
    C_GRAPH = "#27ae60"
    C_AXIS = "#52616f"
    C_GRID = "#e4e8f0"
    C_TXT = "#17202a"
    C_SUB = "#52616f"

    # Three settings * three arms = nine bars per panel. Values are pulled
    # from the per-arm similarity and token-usage outputs.
    settings = ["random10", "random20", "mixed"]
    setting_labels = ["random10", "random20", "Nature+ICLR mixed"]

    diversity = {
        "random10": {"LLM-only": 4.28, "Abstracts agent": 4.75, "ReprNet agent": 5.62},
        "random20": {"LLM-only": 6.31, "Abstracts agent": 6.58, "ReprNet agent": 6.85},
        "mixed":    {"LLM-only": 4.37, "Abstracts agent": 5.09, "ReprNet agent": 6.38},
    }
    cost = {  # per-idea generation tokens
        "random10": {"LLM-only":  2974, "Abstracts agent": 476094, "ReprNet agent": 282750},
        "random20": {"LLM-only":  5362, "Abstracts agent": 490480, "ReprNet agent": 380433},
        "mixed":    {"LLM-only":  6316, "Abstracts agent": 486055, "ReprNet agent": 271767},
    }

    arm_colors = {"LLM-only": C_PROMPT, "Abstracts agent": C_FLAT, "ReprNet agent": C_GRAPH}
    arm_order = ["LLM-only", "Abstracts agent", "ReprNet agent"]

    # ── Panel headers ─────────────────────────────────────────────
    parts.append(f'<text x="20" y="30" font-size="20" font-weight="750" '
                 f'fill="{C_TXT}">Diversity (higher is better)</text>')
    parts.append(f'<text x="640" y="30" font-size="20" font-weight="750" '
                 f'fill="{C_TXT}">Generation-token cost per idea</text>')

    # ── Left panel: diversity ─────────────────────────────────────
    lx0, ly0, lplot_h, lplot_w = 60, 70, 340, 540
    max_div = 7.5
    # gridlines
    for i in range(0, 9):
        yy = ly0 + lplot_h - (i / max_div) * lplot_h
        parts.append(f'<line x1="{lx0}" y1="{yy:.1f}" x2="{lx0+lplot_w}" '
                     f'y2="{yy:.1f}" stroke="{C_GRID}"/>')
        parts.append(f'<text x="{lx0-10}" y="{yy+4:.1f}" text-anchor="end" '
                     f'font-size="12" fill="{C_AXIS}">{i}</text>')

    group_w = (lplot_w - 40) / 3.0
    bar_w = 48
    bar_gap = 4
    arms_block_w = bar_w * 3 + bar_gap * 2
    for gi, setting in enumerate(settings):
        gx0 = lx0 + 20 + gi * group_w
        block_x = gx0 + (group_w - arms_block_w) / 2.0
        for ai, arm in enumerate(arm_order):
            val = diversity[setting][arm]
            x = block_x + ai * (bar_w + bar_gap)
            h = val / max_div * lplot_h
            y = ly0 + lplot_h - h
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" '
                f'rx="4" fill="{arm_colors[arm]}"/>'
            )
            parts.append(
                f'<text x="{x+bar_w/2:.1f}" y="{y-8:.1f}" text-anchor="middle" '
                f'font-size="12" font-weight="700" fill="{C_TXT}">{val:.2f}</text>'
            )
        # setting label
        parts.append(
            f'<text x="{gx0 + group_w/2:.1f}" y="{ly0 + lplot_h + 30}" '
            f'text-anchor="middle" font-size="14" font-weight="700" '
            f'fill="{C_TXT}">{html.escape(setting_labels[gi])}</text>'
        )

    # ── Right panel: cost (log scale) ─────────────────────────────
    rx0, ry0, rplot_h, rplot_w = 660, 70, 340, 490
    log_min, log_max = 3.0, 6.0
    for tick in [1e3, 1e4, 1e5, 1e6]:
        yy = ry0 + rplot_h - ((math.log10(tick) - log_min) /
                              (log_max - log_min)) * rplot_h
        parts.append(f'<line x1="{rx0}" y1="{yy:.1f}" x2="{rx0+rplot_w}" '
                     f'y2="{yy:.1f}" stroke="{C_GRID}"/>')
        parts.append(f'<text x="{rx0-10}" y="{yy+4:.1f}" text-anchor="end" '
                     f'font-size="12" fill="{C_AXIS}">{int(tick):,}</text>')

    cgroup_w = (rplot_w - 40) / 3.0
    cbar_w = 44
    cbar_gap = 4
    carms_block_w = cbar_w * 3 + cbar_gap * 2
    for gi, setting in enumerate(settings):
        gx0 = rx0 + 20 + gi * cgroup_w
        block_x = gx0 + (cgroup_w - carms_block_w) / 2.0
        for ai, arm in enumerate(arm_order):
            val = cost[setting][arm]
            x = block_x + ai * (cbar_w + cbar_gap)
            h = (math.log10(val) - log_min) / (log_max - log_min) * rplot_h
            y = ry0 + rplot_h - h
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cbar_w}" height="{h:.1f}" '
                f'rx="4" fill="{arm_colors[arm]}"/>'
            )
            label = (f"{val/1000:.0f}k" if val >= 1000 else f"{val}")
            parts.append(
                f'<text x="{x+cbar_w/2:.1f}" y="{y-8:.1f}" text-anchor="middle" '
                f'font-size="11" font-weight="700" fill="{C_TXT}">{label}</text>'
            )
        parts.append(
            f'<text x="{gx0 + cgroup_w/2:.1f}" y="{ry0 + rplot_h + 30}" '
            f'text-anchor="middle" font-size="14" font-weight="700" '
            f'fill="{C_TXT}">{html.escape(setting_labels[gi])}</text>'
        )

    # ── Shared legend (bottom) ────────────────────────────────────
    legend_y = ly0 + lplot_h + 70
    lx = lx0 + 10
    for arm in arm_order:
        parts.append(
            f'<rect x="{lx}" y="{legend_y-12}" width="14" height="14" rx="3" '
            f'fill="{arm_colors[arm]}"/>'
        )
        parts.append(
            f'<text x="{lx+22}" y="{legend_y}" font-size="13" fill="{C_TXT}">'
            f'{html.escape(arm)}</text>'
        )
        lx += 170

    # ── Footnotes ─────────────────────────────────────────────────
    parts.append(
        f'<text x="20" y="{height-14}" font-size="13" fill="{C_SUB}">'
        f'Diversity = 10 - average top-5% nearest-neighbor LLM similarity '
        f'(higher = less locally redundant).</text>'
    )
    parts.append(
        f'<text x="640" y="{height-14}" font-size="13" fill="{C_SUB}">'
        f'Log scale; the Abstracts agent costs 1.29-1.79x more tokens per '
        f'idea than the ReprNet agent at matched quality.</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def pipeline_svg(width: int = 1180, height: int = 540) -> str:
    """Three-arm matched-source pipeline figure for the paper.

    Layout:
        left column   - matched source-paper groups (3 benchmarks),
        middle column - three arms in a matched-budget box
                        (LLM-only, ReprNet agent, Abstracts agent),
        right column  - three evaluators (Elo, Diversity, Cost),
        bottom band   - fairness and reproducibility invariants.
    """

    # Colours for the three arms, matched to the violin plot palette.
    C_PROMPT = "#2f80ed"
    C_GRAPH = "#27ae60"
    C_FLAT = "#e67e22"
    C_EVAL = "#7f8c8d"
    C_BORDER = "#b9c6d8"
    C_FILL = "#f5f8fb"
    C_TXT = "#17202a"
    C_SUB = "#44546a"

    parts = [f'<svg viewBox="0 0 {width} {height}" role="img">',
             '<rect width="100%" height="100%" fill="#fff"/>']

    # Arrow marker.
    parts.append(
        '<defs>'
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="9" '
        'refY="3" orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L0,6 L9,3 z" fill="#6b7c93"/>'
        '</marker>'
        '</defs>'
    )

    def box(x, y, w, h, title, sub, *, fill=C_FILL, stroke=C_BORDER,
            title_color=C_TXT, sub_color=C_SUB, stroke_width=2):
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
        )
        parts.append(
            f'<text x="{x+14}" y="{y+28}" font-size="16" font-weight="750" '
            f'fill="{title_color}">{html.escape(title)}</text>'
        )
        if sub:
            parts.append(
                f'<text x="{x+14}" y="{y+50}" font-size="12" '
                f'fill="{sub_color}">{html.escape(sub)}</text>'
            )

    def arrow(x1, y1, x2, y2):
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#6b7c93" stroke-width="2.5" marker-end="url(#arrow)"/>'
        )

    # ── Section labels (column headers) ───────────────────────────
    parts.append(f'<text x="60" y="32" font-size="13" font-weight="700" fill="{C_SUB}">SOURCE GROUPS</text>')
    parts.append(f'<text x="430" y="32" font-size="13" font-weight="700" fill="{C_SUB}">IDEATION ARMS (matched LLM, schema, budget)</text>')
    parts.append(f'<text x="945" y="32" font-size="13" font-weight="700" fill="{C_SUB}">EVALUATION</text>')

    # ── Left column: source groups ─────────────────────────────────
    box(40, 60, 280, 56, "random10 ICLR", "20 groups, 10 papers each (200 total)")
    box(40, 128, 280, 56, "random20 ICLR", "10 groups, 20 papers each (200 total)")
    box(40, 196, 280, 56, "Nature+ICLR mixed", "9 groups, 10 ICLR + 5 Nature (135)")

    # Calibration anchor.
    box(40, 286, 280, 56, "ICLR 2026 oral anchor", "100 ideas, used only as Elo anchor",
        fill="#eef2f7", stroke=C_EVAL)

    # Hugging Face dataset note.
    parts.append(
        f'<text x="40" y="372" font-size="12" font-weight="700" fill="{C_TXT}">'
        f'» published as a Hugging Face dataset</text>'
    )
    parts.append(
        f'<text x="40" y="390" font-size="11" fill="{C_SUB}">'
        f'39 groups in total, schema + protocol in the dataset card</text>'
    )

    # ── Middle column: matched-budget wrapper + three arms ─────────
    wrap_x, wrap_y, wrap_w, wrap_h = 360, 50, 480, 300
    parts.append(
        f'<rect x="{wrap_x}" y="{wrap_y}" width="{wrap_w}" height="{wrap_h}" '
        f'rx="14" fill="none" stroke="#cad6e3" stroke-dasharray="6 4" '
        f'stroke-width="1.5"/>'
    )
    parts.append(
        f'<text x="{wrap_x + 14}" y="{wrap_y + 22}" font-size="12" '
        f'font-weight="700" fill="{C_SUB}">SAME LLM, IdeaProposal schema, 50 tool calls, 70 requests</text>'
    )

    # Arm 1: shuffled LLM-only baseline.
    box(wrap_x + 18, 90, wrap_w - 36, 60,
        "Shuffled LLM-only baseline",
        "one-shot prompt; per-idea deterministic abstract shuffle",
        fill="#ecf3ff", stroke=C_PROMPT)
    # Arm 2: ReprNet agent (El Agente Creativo).
    box(wrap_x + 18, 162, wrap_w - 36, 60,
        "ReprNet agent (El Agente Creativo)",
        "agentic loop over a Repr/Transform network (read-only)",
        fill="#eaf7ee", stroke=C_GRAPH)
    # Arm 3: Abstracts agent.
    box(wrap_x + 18, 234, wrap_w - 36, 60,
        "Abstracts agent (no graph)",
        "agentic loop over the flat abstract corpus",
        fill="#fdf1e1", stroke=C_FLAT)

    # ── Right column: three evaluators ─────────────────────────────
    box(890, 60, 250, 70,
        "Calibrated Elo tournament",
        "Swiss N-way judge, ICLR 2026 anchor",
        fill="#f3f5f7", stroke=C_EVAL)
    box(890, 144, 250, 70,
        "Local diversity",
        "D = 10 - top-5% LLM similarity",
        fill="#f3f5f7", stroke=C_EVAL)
    box(890, 228, 250, 70,
        "Token observability",
        "per-call input/output/requests",
        fill="#f3f5f7", stroke=C_EVAL)

    # Calibration band note.
    box(890, 312, 250, 38,
        "ICLR oral-vs-poster calibration",
        "66.0 / 35.1 Elo reference gaps",
        fill="#eef2f7", stroke=C_EVAL)

    # ── Arrows: sources -> arms ───────────────────────────────────
    for src_y in (88, 156, 224):
        arrow(320, src_y, 378, src_y)

    # ── Arrows: arms -> evaluators ────────────────────────────────
    # Each arm gets a single clean arrow into the EVALUATION column;
    # the arrows fan into a vertical bar that all three evaluators
    # read from, so the visual story is "ideas -> shared eval suite".
    bar_x = 866
    parts.append(
        f'<line x1="{bar_x}" y1="76" x2="{bar_x}" y2="306" '
        f'stroke="#cad6e3" stroke-width="3"/>'
    )
    for ax_y, ax_color in [(120, C_PROMPT), (192, C_GRAPH), (264, C_FLAT)]:
        parts.append(
            f'<line x1="840" y1="{ax_y}" x2="{bar_x}" y2="{ax_y}" '
            f'stroke="{ax_color}" stroke-width="2.5"/>'
        )
    for ey in (95, 179, 263):
        arrow(bar_x, ey, 890, ey)

    # ── Bottom band: invariants ────────────────────────────────────
    parts.append(
        f'<text x="40" y="446" font-size="13" font-weight="800" fill="{C_TXT}">'
        f'EXPERIMENTAL INVARIANTS</text>'
    )
    invariants = [
        ("Matched source", "all three arms ingest the same paper IDs per group; abstract order is controlled per idea."),
        ("Read-only graph", "prior experiment graphs are duplicated into experiment-scoped namespaces and verified by SHA-256."),
        ("Common-scale Elo", "for each benchmark, all arms enter one tournament so per-idea Elo values share a single scale."),
    ]
    for i, (label, body) in enumerate(invariants):
        y = 470 + i * 22
        parts.append(
            f'<text x="40" y="{y}" font-size="12" font-weight="700" '
            f'fill="{C_TXT}">{html.escape(label)}.</text>'
        )
        parts.append(
            f'<text x="174" y="{y}" font-size="12" fill="{C_SUB}">'
            f'{html.escape(body)}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


def write_figure(path: Path, title: str, subtitle: str, svg: str) -> None:
    path.write_text(html_page(title, subtitle, svg), encoding="utf-8")


def _find_chrome() -> str | None:
    candidates = [
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    ]
    for name in candidates:
        found = shutil.which(name)
        if found:
            return found
    # Common macOS application bundles, which are not on PATH.
    mac_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for path in mac_paths:
        if Path(path).exists():
            return path
    return None


def render_png(html_path: Path, png_path: Path) -> None:
    chrome = _find_chrome()
    if not chrome:
        print(f"WARNING: no Chrome/Chromium found; cannot render {html_path.name}")
        return
    subprocess.run(
        [
            chrome,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--hide-scrollbars",
            "--window-size=1200,760",
            f"--screenshot={png_path}",
            html_path.resolve().as_uri(),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
