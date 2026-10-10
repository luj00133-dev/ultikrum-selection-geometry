# Stage 9 secondary directional-mechanism boundary diagnostic

## Status and purpose

This read-only protocol is frozen after the primary Stage 9 selection result is known but before inspecting its fine-grained current/effective cosine summaries. It is therefore a transparent secondary diagnostic, not a new confirmatory test or preregistration.

The purpose is to determine whether the manuscript may retain an opposing "direction-drift exclusion" mechanism under converged non-IID training, or whether the verified contribution must be narrowed to scale-sensitive early selection attraction. No new training is launched and no primary Stage 8/9 gate is changed.

## Frozen data and windows

- Reuse exactly the 27 independently verified Stage 8/9 crossed cells: 3 train/partition seeds × 3 system seeds × 3 distance rules.
- Primary descriptive window: rounds 2--29, matching the verified early effect.
- Converged boundary window: rounds 200--299.
- Client-rounds remain observations. Margins are formed across the three train seeds within each system seed; no row-level p-value is reported.

## Frozen directional quantities

For every client-round, define the logged directional shift

`direction_shift = effective_cosine_to_mean - current_cosine_to_mean`.

A negative value means that the effective (possibly stale) update is less aligned with the current-update mean than the update computed from the current model state. For every crossed cell and window, compute:

1. the straggler mean direction shift;
2. the straggler-minus-strong effective-cosine gap;
3. the straggler-minus-strong current-cosine gap;
4. the straggler-minus-strong selection-rate disparity.

The Euclidean cells are the primary geometry diagnostic because they retain both scale and direction. Cosine and normalized-Euclidean cells are reported as metric-control trajectories, not pooled as extra replicates.

## Frozen descriptive support rule

The converged non-IID evidence is described as supporting a stable opposing direction-exclusion mechanism only if, in the early window, all three system-seed margins satisfy all three conditions:

1. Euclidean straggler direction shift is negative;
2. Euclidean straggler-minus-strong effective-cosine gap is negative; and
3. cosine-distance straggler-minus-strong selection disparity is negative.

Because the primary selection outcome was already known before this protocol, this rule is a conservative claim-boundary audit, not an inferential hypothesis test. Failure of any component requires "partial/mixed directional evidence" or "not supported" wording. It cannot be repaired by choosing individual train seeds, rounds, or alternative windows.

## Association diagnostic

Within each Euclidean crossed cell, compute Spearman correlation across non-overlapping time bins (2--9, then 10-round bins) between selection disparity and the straggler-minus-strong effective-cosine gap. This is temporally confounded and descriptive. A positive median association is compatible with greater directional alignment improving selection but cannot establish causal mediation.

## Audit and outputs

The main analyzer must verify 15,000 rows and 50 unique clients per round in every raw system log, record SHA-256 hashes, and write crossed/window summaries and a publication-style figure. A separately implemented standard-library verifier must recompute every cell-window quantity and compare it numerically with the main output.

This analysis cannot authorize lag-dose, attacks, physical-device claims, or a new defense.
