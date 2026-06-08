"""Read experiment outputs and assemble the paper results summary."""

from __future__ import annotations

import json
import random
from pathlib import Path
from statistics import mean

from paths import ROOT


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def summary_row(path: Path) -> dict:
    for row in read_jsonl(path):
        if row.get("_summary"):
            return row
    raise ValueError(f"No summary row in {path}")


def non_summary_rows(path: Path) -> list[dict]:
    return [row for row in read_jsonl(path) if not row.get("_summary")]


def bootstrap_ci(values: list[float], reps: int = 5000, seed: int = 20260513) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(values)
    samples = []
    for _ in range(reps):
        samples.append(mean(values[rng.randrange(n)] for _ in range(n)))
    samples.sort()
    lo = samples[int(0.025 * reps)]
    hi = samples[int(0.975 * reps)]
    return (round(lo, 2), round(hi, 2))


def source_values(path: Path) -> dict[str, list[float]]:
    rows = non_summary_rows(path)
    by_source: dict[str, list[float]] = {}
    for row in rows:
        by_source.setdefault(row["source"], []).append(float(row["elo"]))
    return by_source


def source_stats(path: Path) -> dict[str, dict]:
    out = {}
    for source, values in source_values(path).items():
        lo, hi = bootstrap_ci(values)
        out[source] = {
            "n": len(values),
            "mean": round(mean(values), 2),
            "ci95": [lo, hi],
        }
    return out


def load_results() -> dict:
    v2 = ROOT / "experiments" / "2026-05-12_iclr2025_random_fair_benchmark_v2"
    inter = ROOT / "experiments" / "2026-05-12_interdisciplinary_nature_iclr_graph_effect"
    flat_r20 = ROOT / "experiments" / "2026-05-13_flatagent_baseline_random20"
    flat_r10 = ROOT / "experiments" / "2026-05-22_flatagent_random10"
    flat_mix = ROOT / "experiments" / "2026-05-22_flatagent_nature_mixed"
    cal25 = ROOT / "iclr2025_oral_vs_poster"
    cal26 = ROOT / "iclr2026_oral_vs_poster"

    # We prefer the Abstracts-agent multi-way tournament files in each
    # setting because they put the LLM-only, ReprNet-agent, Abstracts-agent,
    # and (where applicable) ICLR 2026 oral anchor pools on a single
    # common Elo scale.
    def _prefer(candidate: Path, fallback: Path) -> Path:
        return candidate if candidate.exists() else fallback

    random10_elo_file = _prefer(
        flat_r10 / "outputs" / "random10_four_way_elo.jsonl",
        v2 / "outputs" / "random10_group_elo_vs_iclr2026_oral100.jsonl",
    )
    random20_elo_file = _prefer(
        flat_r20 / "outputs" / "random20_three_way_elo.jsonl",
        v2 / "outputs" / "random20_group_elo_vs_iclr2026_oral100.jsonl",
    )
    interdisciplinary_elo_file = _prefer(
        flat_mix / "outputs" / "mixed_three_way_elo.jsonl",
        inter / "outputs" / "mixed_elo_prompt_vs_graph.jsonl",
    )

    results = {
        "_elo_files": {
            "calibration_iclr2025": str(cal25 / "elo_oral_vs_poster.jsonl"),
            "calibration_iclr2026": str(cal26 / "elo_oral_vs_poster.jsonl"),
            "random10": str(random10_elo_file),
            "random20": str(random20_elo_file),
            "interdisciplinary": str(interdisciplinary_elo_file),
        },
        "calibration": {
            "iclr2025": {
                "elo_summary": summary_row(cal25 / "elo_oral_vs_poster.jsonl"),
                "elo_stats": source_stats(cal25 / "elo_oral_vs_poster.jsonl"),
                "oral_diversity": summary_row(cal25 / "similarity_top5_oral.jsonl"),
                "poster_diversity": summary_row(cal25 / "similarity_top5_poster.jsonl"),
            },
            "iclr2026": {
                "elo_summary": summary_row(cal26 / "elo_oral_vs_poster.jsonl"),
                "elo_stats": source_stats(cal26 / "elo_oral_vs_poster.jsonl"),
                "oral_diversity": summary_row(cal26 / "similarity_top5_oral.jsonl"),
                "poster_diversity": summary_row(cal26 / "similarity_top5_poster.jsonl"),
            },
        },
        "random_v2": {
            "random10": {
                "elo_summary": summary_row(v2 / "outputs" / "random10_group_elo_vs_iclr2026_oral100.jsonl"),
                "elo_stats": source_stats(v2 / "outputs" / "random10_group_elo_vs_iclr2026_oral100.jsonl"),
                "prompt_diversity": summary_row(v2 / "outputs" / "similarity_top5_random10_group_prompt_all_top240.jsonl"),
                "graph_diversity": summary_row(v2 / "outputs" / "similarity_top5_random10_group_graph_all_top240.jsonl"),
            },
            "random20": {
                "elo_summary": summary_row(v2 / "outputs" / "random20_group_elo_vs_iclr2026_oral100.jsonl"),
                "elo_stats": source_stats(v2 / "outputs" / "random20_group_elo_vs_iclr2026_oral100.jsonl"),
                "prompt_diversity": summary_row(v2 / "outputs" / "similarity_top5_random20_group_prompt_all_top240.jsonl"),
                "graph_diversity": summary_row(v2 / "outputs" / "similarity_top5_random20_group_graph_all_top240.jsonl"),
            },
            "token_summary": json.loads((v2 / "outputs" / "token_usage_summary.json").read_text(encoding="utf-8")),
        },
        "interdisciplinary": {
            "elo_summary": summary_row(inter / "outputs" / "mixed_elo_prompt_vs_graph.jsonl"),
            "elo_stats": source_stats(inter / "outputs" / "mixed_elo_prompt_vs_graph.jsonl"),
            "prompt_diversity": summary_row(inter / "outputs" / "similarity_top5_mixed_prompt_top360.jsonl"),
            "graph_diversity": summary_row(inter / "outputs" / "similarity_top5_mixed_graph_augmented_top360.jsonl"),
            "rubric": summary_row(inter / "outputs" / "interdisciplinarity_rubric.jsonl"),
            "token_summary": json.loads((inter / "outputs" / "token_usage_summary.json").read_text(encoding="utf-8")),
        },
    }
    return results


def fmt(x: float) -> str:
    return f"{x:.2f}"
