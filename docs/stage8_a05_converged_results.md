# Stage 8 converged alpha=0.5 mechanism confirmation: verified results

## Audit status

- Formal cells: 15/15 complete (five train/partition seeds by three distance rules).
- Each cell contains all 300 epochs, a completion marker, a resolved configuration, and exactly 15,000 unique client-round rows.
- Manifest SHA-256: `da6828980e1fd8075fc68388ca95c32ad21184746153d19687df99def13373f7`.
- Both `src/analyze_stage8_converged.py` and the separately implemented `src/verify_stage8_independent.py` passed on 2026-08-28.
- All 15 convergence gates passed. Final test accuracy ranged from 0.6986 to 0.7596; every final-50-round slope exceeded the frozen -0.0015-per-round threshold.

Raw logs remain immutable evidence under `results/raw/stage8_a05_converged_5seed`. Derived tables and file-level SHA-256 hashes are under `results/processed/stage8_a05_converged_5seed`.

## Primary seed-level result

The estimand is the Multi-Krum selection-rate difference between straggler and strong clients in percentage points. Seed, not client-round, is the replication unit.

| Window | Euclidean mean (95% CI) | Normalized minus Euclidean (95% CI) | Cosine minus Euclidean (95% CI) |
|---|---:|---:|---:|
| 2--29 | +14.43 [5.62, 23.23] | -12.93 [-31.05, 5.19] | -15.43 [-35.86, 5.01] |
| 30--99 | +10.11 [-3.86, 24.09] | -7.43 [-20.94, 6.09] | -5.57 [-16.84, 5.69] |
| 100--199 | +12.28 [-10.95, 35.51] | -10.42 [-29.19, 8.35] | -11.02 [-26.37, 4.33] |
| 200--299 | +12.28 [-14.04, 38.60] | -13.44 [-36.37, 9.49] | -10.80 [-31.93, 10.33] |

Euclidean distance produced positive straggler attraction in all five seeds in rounds 2--29 and in four of five seeds in each later window. In the final window, normalized Euclidean and cosine each reduced the Euclidean disparity in four of five paired seeds. The mean effect therefore survives the converged budget and is not confined to an unconverged pilot. However, late-window confidence intervals are wide and include zero. This is evidence for a reproducible direction with substantial seed sensitivity, not a universal or attack-robust result.

## Frozen decision

Stage 8 satisfies the conditional dual-mechanism continuation rule: the Euclidean scale-sensitive pattern persists after convergence, and both scale-removing controls reduce its average magnitude. It does **not** yet justify attack expansion, because one train seed reverses the late Euclidean disparity and only one system seed (`91001`) has been used.

The next experiment is therefore a crossed system-seed confirmation before lag-dose, attacks, or a new dataset:

1. retain the exact Stage 8 data/model/training/cardinality/distance configuration;
2. use the first three pre-specified train/partition seeds (2026--2028), not outcome-selected seeds;
3. cross them with system seeds 91001--91003;
4. reuse the nine already complete 91001 cells by verified artifact identity and run only the 18 new cells;
5. estimate train-seed, system-seed, and residual variation from seed-level window disparities;
6. proceed to a frozen lag-dose grid only if the Euclidean direction and scale-removing contrast are not driven by one system seed.

This ordering isolates scheduler randomness efficiently and prevents attacks or cross-dataset complexity from being added before the basic mechanism is stable.
