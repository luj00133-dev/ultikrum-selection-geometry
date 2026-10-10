# Stage 9 secondary analysis: training-stage decay

## Status and purpose

This protocol was frozen after the Stage 9 system-seed gate failed and before inspecting fine-grained trajectories. It is a transparent secondary analysis of the already verified 27-cell Stage 8/9 crossed design. It launches no training and does not alter raw artifacts.

The purpose is to quantify the supported claim boundary: the Euclidean selection disparity and its attenuation by scale-removing distances are stable early in training but are not system-seed invariant after convergence.

## Frozen trajectory construction

- Exclude rounds 0--1 as staleness warm-up, matching the Stage 8/9 primary windows.
- Use one initial bin 2--9 and fixed non-overlapping 10-round bins 10--19 through 290--299.
- For every train seed x system seed x distance cell and bin, compute straggler-minus-strong differences in selection rate, mean `norm_ratio`, and mean `aggregator_score`.
- Client-rounds remain observations. The crossed train/system seed cell is the unit used for margins; no row-level p-value is reported.
- Report each system-seed margin across the three train seeds, and the overall descriptive margin across all nine crossed cells.
- Compute paired normalized-minus-Euclidean and cosine-minus-Euclidean disparity trajectories within each train/system seed cell.

## Frozen decay summaries

For each system seed and distance, report:

1. OLS trajectory slope in percentage points per 100 rounds over bins 10--99 and 100--299;
2. the first 10-round bin after which every remaining bin has absolute marginal disparity <=5 pp, if such a bin exists;
3. early (2--29) and late (200--299) weighted means as consistency checks against Stage 9.

The 5 pp threshold is a descriptive practical-equivalence threshold, not a hypothesis-test boundary. A missing stabilization bin is reported as missing rather than imputed.

## Geometry diagnostics

Within each Euclidean cell, compute Spearman correlations across the 30 bins between selection disparity and:

- negative straggler-minus-strong `norm_ratio` gap; and
- negative straggler-minus-strong score gap.

These correlations diagnose whether smaller stale-update norms and lower Krum scores co-move with selection disparity. They are temporally confounded descriptive quantities and cannot establish mediation or causality.

## Output and interpretation

The analysis writes auditable CSV/JSON tables, SHA-256 hashes, and publication-style trajectory figures under ignored derived-artifact directories. A separate standard-library verifier recomputes all 810 cell-bin rows from raw CSV files and compares them numerically with the main output.

This secondary analysis cannot rescue the failed late persistence gate. It may support a training-stage-dependent mechanism claim and determine whether a separately frozen cross-dataset experiment should target the early phenomenon. Lag-dose and attack expansion remain stopped.
