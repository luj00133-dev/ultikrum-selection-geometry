# Stage 9 time-resolved secondary analysis: verified results

## Audit status

- Source design: the 27 verified Stage 8/9 cells (3 train/partition seeds × 3 system seeds × 3 distance rules).
- Raw coverage: every source cell contains 300 rounds and 50 unique clients per round; rounds 0--1 were excluded exactly as frozen.
- Derived coverage: 30 non-overlapping bins per cell and 810 cell-bin rows in total.
- The main analyzer recomputed all summaries from raw system logs and recorded SHA-256 hashes for every source file.
- A separately implemented standard-library verifier recomputed all 810 cell-bin rows. Verification passed with maximum absolute disagreement `5.684341886080802e-14`.
- Unit of interpretation: crossed train-seed/system-seed cells. Client-round rows and time bins are not treated as independent replication units.

This analysis is descriptive and secondary. It does not change the failed Stage 9 late-persistence gate and does not authorize lag-dose or attack expansion.

## Time-resolved result

The early Euclidean selection disparity is reproducible across all three system seeds, but its later trajectory is system-seed dependent.

| System seed | Distance | Early mean, rounds 2--29 (pp) | Late mean, rounds 200--299 (pp) | Slope, rounds 10--99 (pp/100 rounds) | Slope, rounds 100--299 (pp/100 rounds) | First sustained `|disparity| <= 5 pp` bin |
|---:|---|---:|---:|---:|---:|---:|
| 91001 | Euclidean | +17.26 | +23.13 | +0.78 | +4.87 | none |
| 91002 | Euclidean | +12.98 | -0.27 | -6.06 | -7.79 | 220 |
| 91003 | Euclidean | +20.71 | +0.87 | -13.89 | -5.36 | 250 |
| 91001 | Normalized Euclidean | +9.05 | +0.33 | -9.22 | -1.44 | 210 |
| 91002 | Normalized Euclidean | -10.71 | +3.03 | +19.11 | -0.06 | none |
| 91003 | Normalized Euclidean | -3.21 | +2.03 | +7.06 | +0.04 | none |
| 91001 | Cosine | +6.31 | +4.03 | -0.61 | -0.39 | none |
| 91002 | Cosine | -11.55 | -0.47 | +26.22 | +2.66 | none |
| 91003 | Cosine | -2.62 | +2.47 | +4.44 | -0.65 | 290 |

The strict stabilization criterion requires every subsequent 10-round bin to remain inside ±5 pp. A missing stabilization time therefore means that at least one later bin leaves the band; it must not be read as evidence of a persistent mean effect. In particular, several control trajectories have near-zero late means but intermittent excursions.

For Euclidean Multi-Krum, system seeds 91002 and 91003 decay to sustained practical neutrality after rounds 220 and 250, whereas seed 91001 remains strongly positive and increases during the late interval. This directly explains why averaging across system seeds would overstate late persistence. The supported statement is therefore an **early training-stage geometry effect**, not a converged invariant.

## Geometry diagnostic

Across the nine Euclidean crossed cells, the median within-cell Spearman association between selection disparity and the negative straggler-minus-strong norm-ratio gap is `rho = 0.510`; the corresponding median association with the negative score gap is `rho = 0.615`. The norm-ratio association is positive in eight of nine cells and negative in one (`train seed 2027`, `system seed 91001`); score-gap associations are positive in all nine cells but vary substantially in magnitude.

These co-movements are consistent with the proposed two-step mechanism: stale updates can differ in scale, and Euclidean Krum scores can convert that geometry into unequal selection. They are not mediation estimates. Training time affects all three quantities, so no causal or row-level inferential claim is made.

## Frozen claim boundary and next-stage decision

The verified evidence supports all of the following limited claims:

1. Under FashionMNIST/LeNet, Dirichlet `alpha = 0.5`, and the frozen four-tier logical-staleness profile, Euclidean Multi-Krum exhibits an early straggler-versus-strong selection disparity for every crossed system-seed margin.
2. Normalized Euclidean and cosine controls attenuate or reverse that early disparity for every system seed, supporting a scale-sensitive selection-geometry mechanism.
3. The disparity is not system-seed invariant after convergence; late persistence is driven mainly by system seed 91001 in this finite design.

The next-stage decision is **Go only for a separately frozen cross-dataset/model replication of the early-stage phenomenon**. Its purpose is external transfer, not rescue of the failed late claim. The experiment must retain crossed train and system seeds, include Euclidean plus both scale-removing controls, and pre-specify early windows and gates before any formal output is inspected.

The following remain **No-Go** unless new pre-specified evidence changes the decision: lag-dose expansion, Byzantine attacks, physical-device claims, deadline/network claims, and any assertion of converged system-seed-invariant bias.

## Artifacts

- `results/processed/stage9_time_resolved/analysis.json`
- `results/processed/stage9_time_resolved/independent_verification.json`
- `results/processed/stage9_time_resolved/trajectory_bins.csv`
- `results/processed/stage9_time_resolved/decay_summaries.csv`
- `results/processed/stage9_time_resolved/euclidean_geometry_associations.csv`
- `artifacts/figures/stage9_time_resolved/selection_disparity_trajectory.{png,pdf,svg}`
- `artifacts/figures/stage9_time_resolved/control_contrast_trajectory.{png,pdf,svg}`
- `artifacts/figures/stage9_time_resolved/geometry_diagnostics.{png,pdf,svg}`
