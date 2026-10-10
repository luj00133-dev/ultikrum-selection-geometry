# Stage 10 CIFAR-10 early-effect replication: terminal results

## Frozen scope and integrity

- Grid: 3 train/partition seeds × 3 system-assignment seeds × 3 distance rules = 27 cells.
- Training: CIFAR-10/simpleCNN, FedSGD, 50 clients, Dirichlet alpha = 0.5, NoAttack, 60 rounds.
- Primary window: rounds 2--29; secondary window: rounds 30--59.
- Formal manifest SHA-256: `bcfa8cc9204d537756dbddb25fb8feaf48154d707f06f8f256b1f92d11724f8a`.
- Numeric verifier: `passed`, 27 cells, 54 windows, maximum error 6.395e-14.
- Semantic verifier: `passed`, 81,000 client-round rows and 61,560 selected rows.
- Minimum final-10-round accuracy: 0.1973; minimum final-minus-first-10 gain: +0.0707.

## Terminal decision

Terminal state: **pass**.

Crossed early Euclidean straggler-minus-strong selection disparity: **+14.84 pp**.

| System seed | Euclidean disparity (pp) | Normalized minus Euclidean (pp) | Cosine minus Euclidean (pp) |
|---:|---:|---:|---:|
| 91001 | +11.19 | -1.19 | -1.67 |
| 91002 | +15.36 | -12.50 | -15.36 |
| 91003 | +17.98 | -21.31 | -17.86 |

### Frozen gate ledger

| Gate | Result |
|---|---|
| All 27 learning guards pass | Pass |
| Crossed Euclidean disparity is at least +5 pp | Pass |
| Euclidean margin is positive for every system seed | Pass |
| Both controls are negative for every system seed | Pass |

## Consequence

The frozen transfer gate passes. The early scale-sensitive selection effect has bounded cross-dataset/model support. Stage 9 nevertheless ruled out assignment-stable converged persistence, so lag-dose and attack expansion remain No-Go.

## Claim boundary

This experiment does not establish Byzantine/backdoor robustness, physical-device behavior, asynchronous-network performance, a fairness guarantee, a new defense, or a system-seed-invariant converged dual mechanism.
