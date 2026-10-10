# Stage 10: frozen CIFAR-10 early-stage replication protocol

## Status and rationale

This protocol is frozen after the verified Stage 9 time-resolved analysis and before any Stage 10 smoke or formal output is inspected. Stage 9 failed its converged late-persistence gate but supported an early training-stage selection-geometry effect for every system-seed margin. Stage 10 tests whether that limited early effect transfers from FashionMNIST/LeNet to a color-image dataset and a different model family.

Stage 10 is not a test of converged persistence, lag dose, attacks, physical devices, bandwidth, or deadlines. No Stage 10 result may be used to rescue those claims.

## Frozen design

- Dataset/model: CIFAR-10 with `simplecnn` (RGB input; different dataset and architecture from FashionMNIST/LeNet).
- Federated optimizer: FedSGD, 60 rounds, 50 clients, one local epoch, batch size 128, learning rate 0.01.
- Data heterogeneity: uncached Dirichlet label partition with `alpha = 0.5`.
- System heterogeneity: the unchanged four-tier logical-staleness profile.
- Train/partition seeds: 2026, 2027, 2028; partition seed equals train seed by design and is not a second replicate.
- System/resource-assignment seeds: 91001, 91002, 91003.
- Aggregation controls: Euclidean Multi-Krum, normalized-Euclidean Multi-Krum, and cosine Multi-Krum.
- Fixed Multi-Krum parameters: `avg_percentage = 0.76`, `num_score_neighbors = 39`, and `enable_check = false`.
- Threat model: `NoAttack` only.

The formal grid contains 3 train/partition seeds × 3 system seeds × 3 distances = 27 cells. Every cell must contain exactly 60 sequential epochs and 3,000 client-round rows with 50 unique clients in every round. Failed or partial cells are never counted and are rerun from the beginning under the unchanged configuration.

## Frozen estimands and windows

Rounds 0--1 are excluded as scheduler warm-up. The primary window is rounds 2--29, matching the supported Stage 9 early claim. Rounds 30--59 are secondary and descriptive.

The primary estimand is the straggler-minus-strong Multi-Krum selection-rate difference in percentage points. For each system seed, average over the three train seeds. Compute normalized-minus-Euclidean and cosine-minus-Euclidean paired contrasts within every train-seed/system-seed cell before taking margins. Report the full 3 × 3 crossed matrix; client-rounds are observations, not independent replicates.

## Frozen integrity and learning gates

All 27 formal cells and their raw logs, system logs, resolved configurations, completion markers, and hashes are required. Each cell must satisfy both descriptive learning checks:

1. mean test accuracy over rounds 50--59 is at least 0.15; and
2. mean test accuracy over rounds 50--59 exceeds the mean over rounds 0--9 by at least 0.03.

These are malfunction guards, not claims of convergence or competitive CIFAR-10 accuracy. If any cell fails, Stage 10 is invalid for transfer claims until the pre-specified grid is completed under a newly frozen calibration; thresholds are not changed after inspection.

## Frozen transfer gate

Stage 10 passes only if all of the following hold in rounds 2--29:

1. the crossed Euclidean disparity across all nine train/system cells is at least +5 pp;
2. the Euclidean disparity is positive for each of the three system-seed margins; and
3. both normalized-minus-Euclidean and cosine-minus-Euclidean contrasts are negative for each system-seed margin.

No row-level p-value is permitted. Finite-level train, system, and interaction sums-of-squares shares and leave-one-system-seed-out summaries are descriptive sensitivity analyses.

## Decision rules

- **Pass:** support a cross-dataset/model early-stage selection-geometry claim and proceed to manuscript assembly. Attack and lag-dose grids remain stopped.
- **Complete but fail:** report a boundary/negative transfer result and do not broaden the claim.
- **Integrity or learning failure:** stop; do not interpret the transfer gate and do not silently remove, replace, or retune cells.

Smoke outputs use a dedicated ignored directory, are never merged into the formal manifest, and cannot contribute to any result.

## Frozen result-to-manuscript handling

Before the formal grid completed, `src/render_stage10_manuscript_insert.py` was frozen to prevent outcome-dependent prose selection. It accepts only terminal `analysis.json` and `independent_verification.json` files that agree on all learning and transfer gates and cover all 27 cells and 54 cell windows. It emits one of three fixed branches:

- transfer Pass: report cross-dataset/model early-effect support with the original scope limits;
- complete, learning-valid Fail: report a negative-transfer boundary and prohibit claim broadening; or
- learning Invalid: omit a transfer effect, retain every cell, and require a separately frozen calibration before any rerun.

The renderer writes a reviewable insert and input/output hashes; it never edits the manuscript or author declarations automatically.

## Independent semantic audit

`src/verify_stage10_semantics_independent.py` was added while the formal queue was incomplete and does not modify either frozen scientific analyzer. After the main and numeric independent checks pass, it must separately verify all 27 final artifacts for:

- the complete resolved hyperparameter tuple and exact defense parameters;
- formal-root path containment and exclusion of smoke artifacts;
- system metadata, fixed 10/15/15/10 group counts, and client-to-group stability;
- requested lags 0/0/1/2 and effective lag `min(requested_lag, round)`;
- exactly 38 selected clients and ranks 0--37 in every round;
- finite scores, norms, cosine values, stale deltas, and recomputed norm ratios; and
- equality with the main analyzer's final artifact hashes.

Failure of this semantic audit is an integrity failure and stops transfer interpretation even if the numerical gate signs appear favorable.
