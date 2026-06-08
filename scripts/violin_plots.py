"""Matplotlib violin figures for calibration and quality results."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from data_io import source_values

VIOLIN_COLORS = {
    "LLM-only": "#2f80ed",
    "ReprNet agent": "#27ae60",
    "Abstracts agent": "#e67e22",
    "Oral anchor": "#7f8c8d",
    "Oral": "#3a7ebf",
    "Poster": "#d9823b",
}


def render_elo_violin(
    png_path: Path,
    entries: list[dict],
    *,
    title: str,
    subtitle: str | None = None,
    figsize: tuple[float, float] = (10.0, 5.6),
) -> None:
    """Render a violin plot of per-idea Elo distributions.

    Each entry: {"label": "LLM-only"|"ReprNet agent"|..., "group": "random10"|...,
                  "values": [floats]}.  Entries appear in the supplied order.
    Group labels are placed under each violin cluster, individual labels
    above the x-axis.
    """
    arrays = [np.asarray(e["values"], dtype=float) for e in entries]
    labels = [e["label"] for e in entries]
    groups = [e["group"] for e in entries]
    colors = [VIOLIN_COLORS.get(lab, "#556b8e") for lab in labels]
    positions = list(range(1, len(entries) + 1))

    fig, ax = plt.subplots(figsize=figsize)
    parts = ax.violinplot(
        arrays,
        positions=positions,
        widths=0.8,
        showmeans=False,
        showmedians=False,
        showextrema=False,
    )
    for pc, c in zip(parts["bodies"], colors):
        pc.set_facecolor(c)
        pc.set_edgecolor("black")
        pc.set_alpha(0.55)

    rng = np.random.default_rng(20260513)
    for pos, arr, c in zip(positions, arrays, colors):
        if arr.size == 0:
            continue
        x = rng.normal(loc=pos, scale=0.05, size=arr.size)
        ax.scatter(
            x, arr, s=10, color=c, edgecolor="black",
            linewidths=0.3, alpha=0.6, zorder=3,
        )

    for pos, arr in zip(positions, arrays):
        if arr.size == 0:
            continue
        m = float(arr.mean())
        sem = float(arr.std(ddof=1) / np.sqrt(arr.size)) if arr.size > 1 else 0.0
        ax.hlines(m, pos - 0.28, pos + 0.28, colors="black", linewidth=2, zorder=4)
        ax.errorbar(
            pos, m, yerr=1.96 * sem, fmt="none", ecolor="black",
            elinewidth=1.5, capsize=6, zorder=4,
        )
        ax.text(
            pos + 0.32, m, f"{m:.1f}\n±{1.96*sem:.1f}",
            va="center", ha="left", fontsize=8,
        )

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Elo rating", fontsize=11)

    # Group annotation underneath the per-violin labels.
    group_runs: list[tuple[str, int, int]] = []
    for i, g in enumerate(groups):
        if group_runs and group_runs[-1][0] == g:
            group_runs[-1] = (g, group_runs[-1][1], i)
        else:
            group_runs.append((g, i, i))
    # Group labels are placed beneath the plot, below the per-violin tick
    # labels, using axis-fraction y so they sit outside the data area.
    xtrans = ax.get_xaxis_transform()
    label_yf = -0.12
    for g, lo, hi in group_runs:
        center = (positions[lo] + positions[hi]) / 2.0
        ax.text(
            center, label_yf, g,
            transform=xtrans, ha="center", va="top",
            fontsize=11, fontweight="bold", clip_on=False,
        )

    # Separator lines between groups.
    for i in range(len(group_runs) - 1):
        right = positions[group_runs[i][2]]
        left = positions[group_runs[i + 1][1]]
        ax.axvline((right + left) / 2.0, color="#dde2eb", linewidth=1.0, zorder=0)

    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=28)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.22, top=0.86)
    fig.savefig(png_path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def build_calibration_violin(results: dict, png_path: Path) -> None:
    cal_files = {
        "ICLR 2025": Path(results["_elo_files"]["calibration_iclr2025"]),
        "ICLR 2026": Path(results["_elo_files"]["calibration_iclr2026"]),
    }
    entries: list[dict] = []
    for group, path in cal_files.items():
        per = source_values(path)
        oral_key = next(k for k in per if "oral" in k)
        poster_key = next(k for k in per if "poster" in k)
        entries.append({"group": group, "label": "Oral", "values": per[oral_key]})
        entries.append({"group": group, "label": "Poster", "values": per[poster_key]})
    render_elo_violin(
        png_path,
        entries,
        title="Elo calibration recovers oral-vs-poster preference",
        subtitle="Per-idea Elo distributions from two independent ICLR tournaments; bars show 95% CI of the mean.",
        figsize=(9.0, 5.4),
    )


def build_quality_violin(results: dict, png_path: Path) -> None:
    entries: list[dict] = []
    for group_label, key in [("random10", "random10"), ("random20", "random20")]:
        per = source_values(Path(results["_elo_files"][key]))
        group_entries = [
            {"group": group_label, "label": "LLM-only",
             "values": per[f"{key}_group_prompt_all"]},
            {"group": group_label, "label": "Oral anchor",
             "values": per["iclr2026_oral_random100_ideas"]},
            {"group": group_label, "label": "ReprNet agent",
             "values": per[f"{key}_group_graph_all"]},
        ]
        # The Abstracts agent currently only has a random20 ablation pool.
        # When the random20 Elo file is its 4-way tournament, append an
        # Abstracts-agent violin to the random20 group so all four arms
        # show under a single mutually-comparable rating scale.
        flat_key = f"{key}_group_flatagent_all"
        if flat_key in per:
            group_entries.append({
                "group": group_label, "label": "Abstracts agent",
                "values": per[flat_key],
            })
        entries.extend(group_entries)
    inter_per = source_values(Path(results["_elo_files"]["interdisciplinary"]))
    mixed_entries = [
        {"group": "mixed", "label": "LLM-only",
         "values": inter_per["mixed_prompt_all"]},
        {"group": "mixed", "label": "ReprNet agent",
         "values": inter_per["mixed_graph_augmented_all"]},
    ]
    if "mixed_flatagent_all" in inter_per:
        mixed_entries.append({
            "group": "mixed", "label": "Abstracts agent",
            "values": inter_per["mixed_flatagent_all"],
        })
    entries.extend(mixed_entries)
    render_elo_violin(
        png_path,
        entries,
        title="Agentic ideation ties on quality; ReprNet and Abstracts agents differ on diversity and cost",
        subtitle="Per-idea Elo distributions from unified tournaments; bars show 95% CI of the mean."
                 " The ReprNet and Abstracts agents are tied within tournament noise at every setting.",
        figsize=(14.0, 5.8),
    )
