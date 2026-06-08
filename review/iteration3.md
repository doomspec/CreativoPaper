# Review Iteration 3: Claims and Evidence

## Findings

- The main graph-vs-prompt effect was reported as mean Elo gaps, but the text did not explicitly state the bootstrap interval separation.
- The paper said graph arms exceed the oral anchor, which needs a stronger caveat because the benchmark uses LLM judges rather than human acceptance decisions.
- Two BibTeX entries for foundational LLM work were present but not cited.

## Changes Applied

- Added bootstrap confidence interval ranges for random10, random20, and mixed graph-vs-prompt comparisons.
- Added an explicit limitation that exceeding the oral anchor is a relative LLM-judge preference signal, not an acceptance claim.
- Cited the transformer and large-scale pretraining references in the introduction.

## Verification

- Recompile required after this patch.
