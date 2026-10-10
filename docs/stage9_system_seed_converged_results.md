# Stage 9 converged system-seed confirmation: verified results

## Audit status

- New Stage 9 cells: 18/18 complete.
- Combined crossed design: 27/27 cells (three train/partition seeds x three system seeds x three distance rules).
- Every cell contains epochs 0--299, a completion marker, a frozen resolved configuration, and exactly 15,000 client-round rows with 50 unique clients in every round.
- All 27 convergence gates passed.
- The primary analyzer and the separately implemented standard-library verifier both passed on 2026-08-29.
- Stage 9 manifest SHA-256: `d8956ad2db8d095b318f735acc7306dd8801c26a157eddd4a272bb863a2e5990`.

The last new cell was interrupted after epoch 77 without a completion marker. It was never counted as complete. The unchanged formal runner subsequently verified and skipped the other 17 complete cells and reran only that incomplete cell from the beginning; the replacement then passed the same full checks. No partial rows entered analysis.

## Pre-specified gate results

Values below are system-seed marginal means across the three pre-specified train seeds. Disparity is straggler minus strong Multi-Krum selection rate in percentage points. Control contrasts are control minus Euclidean disparity, so negative values indicate attenuation.

### Early window, rounds 2--29

| System seed | Euclidean disparity | Normalized minus Euclidean | Cosine minus Euclidean |
|---:|---:|---:|---:|
| 91001 | +17.26 | -8.21 | -10.95 |
| 91002 | +12.98 | -23.69 | -24.52 |
| 91003 | +20.71 | -23.93 | -23.33 |

The early-window gate passed: Euclidean disparity was positive for every system seed, and both scale-removing controls attenuated it for every system seed.

### Converged late window, rounds 200--299

| System seed | Euclidean disparity | Normalized minus Euclidean | Cosine minus Euclidean |
|---:|---:|---:|---:|
| 91001 | +23.13 | -22.80 | -19.10 |
| 91002 | -0.27 | +3.30 | -0.20 |
| 91003 | +0.87 | +1.17 | +1.60 |

The late-window gate failed. Euclidean disparity was not positive for all system seeds, and neither control attenuated it for all system seeds. Therefore the frozen overall lag-dose gate is **No-Go**.

Leave-one-system-seed-out analysis reinforces this interpretation. Omitting 91001 leaves a late Euclidean mean of only +0.30 pp, while normalized and cosine contrasts become +2.23 and +0.70 pp. In contrast, omitting either 91002 or 91003 retains an approximately +11.4 to +12.0 pp Euclidean mean and negative control contrasts. Thus the apparent persistent late effect is strongly dependent on system seed 91001 in this finite crossed design.

Finite-level sums-of-squares decomposition also shows substantial system-seed dependence in the late window: the system factor accounts for 48.2% of Euclidean disparity variation, 62.0% of normalized-minus-Euclidean contrast variation, and 42.1% of cosine-minus-Euclidean contrast variation. These are descriptive shares for the frozen factor levels, not population variance estimates.

## Decision and claim boundary

Stage 9 supports a robust **early training-stage selection-geometry effect** under logical staleness: Euclidean Multi-Krum systematically favors straggler clients relative to strong clients, and scale-removing distances consistently suppress or reverse that disparity across all three system seeds. It does not support a system-seed-invariant claim that this mechanism persists after convergence.

Under the pre-specified protocol:

- do not start the lag-dose grid;
- do not expand to attacks;
- do not use Stage 6's 30-round results as converged evidence;
- do not claim physical-device, bandwidth, deadline, or Byzantine robustness effects;
- reframe the next analysis around training-stage dependence and the decay of selection bias, using the already verified 27-cell trajectories before considering any further GPU expansion.

The next evidence step is a read-only time-resolved analysis of the existing Stage 8/9 system logs: estimate per-cell disparity trajectories, decay summaries, and their association with update-norm ratio and score geometry. Any later cross-dataset experiment must be separately frozen to test the early-stage phenomenon, not presented as validation of a late persistent effect.
