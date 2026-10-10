# Stage 8: converged alpha=0.5 mechanism confirmation

## Purpose

Stage 8 tests whether the Stage 3/4 non-IID selection pattern survives a training budget that passed the convergence calibration. It does not overwrite prior stages and does not introduce attacks or new algorithms.

## Frozen design

- FashionMNIST + LeNet, FedSGD, NoAttack;
- Dirichlet alpha=0.5 and four-tier logical staleness;
- 300 rounds, 50 clients, seeds 2026--2030, system seed 91001;
- MultiKrum, MultiKrumNormalized, and MultiKrumCosine;
- output cardinality 38, score-neighbor count 39, no runtime check substitution.

The run grid contains exactly 15 cells. Each complete cell must contain a main log with `Training finished on`, a parseable resolved config, and a system CSV with exactly 15,000 client-round rows. Missing or interrupted cells are not included in analysis.

## Primary gate

All five seeds for each distance control must be complete. A cell is convergence-valid only if final test accuracy is at least 0.60 and the final-50-round accuracy slope is at least -0.0015 per round. Seed is the replication unit.

The primary estimand is straggler minus strong Multi-Krum selection rate, reported by seed and training window. The mechanism contrast is normalized/cosine minus Euclidean disparity within the same seed. Client-round rows are never treated as independent replicates.

## Decision rule

- Continue the dual-mechanism paper if Euclidean straggler attraction persists across converged seeds and at least one scale-removing control consistently reduces or reverses it.
- Reframe as a training-stage-dependent transient if the effect is concentrated in early rounds or disappears after convergence.
- Stop attack expansion if the five-seed direction is unstable or convergence gates fail.

This stage remains logical-staleness emulation and cannot support claims about physical devices, bandwidth, packet loss, deadlines, or Byzantine security.
