# ReprNet Paper

This directory contains the full LaTeX paper and reproducible HTML-based figures.

Build everything from the repository root:

```bash
cd paper
make
```

The figure pipeline reads the local experiment artifacts, writes `data/results.json`,
generates standalone HTML/SVG figures under `figures/`, and renders PNGs with
headless Chrome for inclusion in `main.tex`.

Primary artifacts:

- `main.tex`: LaTeX paper.
- `references.bib`: BibTeX citations.
- `figures/*.html`: source figures authored in HTML with inline SVG.
- `figures/*.png`: rendered figures included by LaTeX.
- `data/results.json`: extracted numeric summaries from the experiment outputs.
- `review/`: three documented review-and-improvement iterations.
