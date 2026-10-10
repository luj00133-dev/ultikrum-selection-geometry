# Verified Stage 10 manuscript insert

**Terminal state:** `pass`

**Abstract sentence:** On CIFAR-10/simpleCNN, the frozen transfer grid independently reproduces the early effect and both metric-control contrasts across all three assignments.

## Methods-status sentence

All 27 CIFAR-10/simpleCNN cells completed the frozen 60-round crossed grid, passed exact artifact and client-round coverage checks, and were recomputed by the independent verifier.

## Results

The crossed early Euclidean straggler-minus-strong disparity was +14.84 pp. System-seed margins and paired control contrasts are shown below.

| System seed | Euclidean disparity (pp) | Normalized minus Euclidean (pp) | Cosine minus Euclidean (pp) |
|---:|---:|---:|---:|
| 91001 | +11.19 | -1.19 | -1.67 |
| 91002 | +15.36 | -12.50 | -15.36 |
| 91003 | +17.98 | -21.31 | -17.86 |

The frozen transfer gate **passes**. This supports cross-dataset/model transfer of the early scale-sensitive selection effect, but not converged persistence, attacks, physical-device behavior, or a deployable defense.

## Audit statement

The minimum final-10-round accuracy was 0.1973, and the minimum final-minus-first-10-round gain was +0.0707. The independent verifier covered 27 cells and 54 cell windows; its maximum absolute numerical disagreement was 6.395e-14.

## Gate ledger

| Frozen condition | Result |
|---|---|
| All 27 learning guards pass | Pass |
| Crossed Euclidean disparity is at least +5 pp | Pass |
| Euclidean margin is positive for every system seed | Pass |
| Both control contrasts are negative for every system seed | Pass |

This generated insert must be reviewed before copying into the manuscript; it does not replace author confirmation of declarations.
