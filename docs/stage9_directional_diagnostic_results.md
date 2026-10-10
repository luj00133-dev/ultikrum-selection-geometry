# Stage 9 directional-mechanism boundary diagnostic: verified results

## Audit status

- Reused exactly the 27 independently verified Stage 8/9 crossed cells; no new training was launched.
- Verified 15,000 client-round rows, rounds 0--299, and 50 unique clients per round in every cell.
- Derived 54 cell-window rows and 810 non-overlapping cell-bin rows.
- The standard-library verifier independently recomputed every cell-window quantity and agreed with the main analyzer to a maximum absolute error of `5.551115123125783e-17`.
- Raw system-log SHA-256 hashes are recorded in `results/processed/stage9_directional_diagnostic/raw_sha256.csv`.

## Early-window directional result

Values are system-seed margins across the three train/partition seeds in rounds 2--29. Directional shift is `effective cosine - current cosine`; negative values indicate that logical staleness reduces alignment relative to the update computed at the current model state.

| System seed | Euclidean straggler directional shift | Euclidean effective-cosine gap, straggler - strong | Cosine selection disparity (pp) |
|---:|---:|---:|---:|
| 91001 | -0.00359 | +0.00571 | +6.31 |
| 91002 | -0.00309 | -0.00814 | -11.55 |
| 91003 | -0.00332 | -0.00209 | -2.62 |

The first component is stable: the straggler directional shift is negative for every system seed. However, the absolute effective-cosine ordering is not stable. Under system seed 91001, stragglers begin with a positive current-cosine advantage (+0.00930), and the stale shift is not large enough to erase it; their effective-cosine gap remains +0.00571. Consistently, cosine-distance Multi-Krum still favors stragglers by +6.31 pp for that system seed. System seeds 91002 and 91003 show the opposite ordering and negative cosine-selection disparities.

The frozen conservative support rule therefore fails two of its three components:

- Euclidean straggler shift negative for every system seed: **yes**;
- Euclidean effective-cosine gap negative for every system seed: **no**;
- cosine selection disparity negative for every system seed: **no**.

## Time-bin association

Across the nine Euclidean crossed cells, the median within-cell Spearman association between selection disparity and the straggler-minus-strong effective-cosine gap is `rho = -0.144`. Individual values range from -0.702 to +0.252. This heterogeneous and slightly negative median does not support a stable descriptive relationship in which greater relative directional alignment consistently improves selection over training time.

The correlations are temporally confounded and are not treated as independent inferential tests.

## Claim decision

The converged non-IID evidence does **not** support a stable opposing direction-drift exclusion mechanism. The defensible finding is narrower:

> Logical staleness produces a small, consistently negative within-straggler directional shift, but whether stragglers become less aligned than strong clients and whether direction-only metrics exclude them depends on resource assignment and the underlying current-update geometry.

Accordingly:

- remove "verified dual mechanism" from the main contribution and title;
- retain direction drift as a measured competing factor and boundary result;
- make the reproducible main contribution the early, scale-sensitive Euclidean selection attraction and its training-stage/system-seed dependence;
- describe the 30-round IID direction-exclusion pattern as prior conditional evidence, not converged non-IID confirmation;
- do not add lag-dose or attacks to repair the failed directional claim.

## Artifacts

- `results/processed/stage9_directional_diagnostic/analysis.json`
- `results/processed/stage9_directional_diagnostic/independent_verification.json`
- `results/processed/stage9_directional_diagnostic/cell_window_metrics.csv`
- `results/processed/stage9_directional_diagnostic/system_seed_margins.csv`
- `results/processed/stage9_directional_diagnostic/euclidean_direction_associations.csv`
- `artifacts/figures/stage9_directional_diagnostic/early_directional_diagnostic.{png,pdf,svg}`
