#!/usr/bin/env python3
"""Build paper data summaries and figures.

Entry point that ties together the split modules:
    paths         - shared output locations
    data_io       - read experiment outputs, assemble results.json
    violin_plots  - matplotlib calibration/quality violins (direct PNG)
    svg_assets    - standalone HTML+SVG figures rendered to PNG via Chrome
"""

from __future__ import annotations

import json

from paths import DATA, FIGURES
from data_io import load_results
from svg_assets import diversity_cost_svg, pipeline_svg, render_png, write_figure
from violin_plots import build_calibration_violin, build_quality_violin


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    results = load_results()
    (DATA / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    build_calibration_violin(results, FIGURES / "fig_calibration.png")
    build_quality_violin(results, FIGURES / "fig_quality.png")

    write_figure(
        FIGURES / "fig_diversity_cost.html",
        "ReprNet agent wins diversity at lower per-idea cost than the Abstracts agent",
        "Diversity uses top-5% nearest-neighbor LLM similarity; token costs are per generated idea (log scale).",
        diversity_cost_svg(results),
    )

    write_figure(
        FIGURES / "fig_pipeline.html",
        "El Agente Creativo: experiment pipeline",
        "Matched source-paper groups feed three ideation arms (LLM-only, ReprNet agent, Abstracts agent) into a common-scale evaluation suite.",
        pipeline_svg(),
    )

    # Remove stale HTML for figures now produced directly via matplotlib.
    for stale in ["fig_calibration.html", "fig_quality.html"]:
        stale_path = FIGURES / stale
        if stale_path.exists():
            stale_path.unlink()

    manifest = [
        {"html": None, "png": "fig_calibration.png"},
        {"html": None, "png": "fig_quality.png"},
    ]
    for html_path in sorted(FIGURES.glob("fig_*.html")):
        png_path = html_path.with_suffix(".png")
        render_png(html_path, png_path)
        manifest.append({"html": html_path.name, "png": png_path.name})
    (FIGURES / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {DATA / 'results.json'}")
    print(f"Wrote {len(manifest)} figure(s) to {FIGURES}")


if __name__ == "__main__":
    main()
