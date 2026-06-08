# Review Iteration 1: Layout and Float Order

## Findings

- `paper/main.pdf` compiled, but the wide token-usage table floated to a final page after the references.
- The cost figure also appeared too late relative to the token-cost discussion.
- The final LaTeX log had no undefined citations or overfull boxes, so the issue was presentation order rather than compilation correctness.

## Changes Applied

- Converted the step-level token table from `table*` to a compact single-column `table` with shorter headers.
- Added a `\clearpage` after the token-cost result block so cost artifacts are flushed before Discussion and References.

## Verification

- Recompile required after this patch.
