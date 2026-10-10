# Supplementary Material for “When Staleness Attracts”

**Authors:** [AUTHOR NAMES TO CONFIRM]

This supplement records the parameter conventions, artifact gates, crossed summaries, and claim-audit rules for the accompanying manuscript. Stage 10 content remains provisional until all 27 CIFAR-10 cells pass their frozen integrity and learning guards and the main and independent analyses agree.

## S1. Parameter-explicit experimental configuration

### S1.1 FashionMNIST/LeNet confirmation

| Item | Frozen value |
|---|---|
| Dataset / model | FashionMNIST / LeNet |
| Federated algorithm | FedSGD |
| Clients | 50, all participating in every round |
| Global rounds | 300 |
| Local epochs | 1 |
| Batch size | 128 |
| Optimizer | SGD, learning rate 0.01, momentum 0.9, weight decay 0.0001 |
| Data partition | Dirichlet label partition, \(\alpha=0.5\), uncached for formal seed changes |
| Train/partition seeds | 2026, 2027, 2028; partition seed equals train seed |
| System seeds | 91001, 91002, 91003 |
| Threat model | NoAttack |
| Aggregation output | 38 of 50 clients (`avg_percentage=0.76`) |
| Score neighbors | 39 (`num_score_neighbors=39`) |
| Feasibility check | Disabled to preserve the frozen convention |
| Distance controls | Euclidean, normalized Euclidean, cosine |
| Formal cells | 3 train seeds × 3 system seeds × 3 distances = 27 |

### S1.2 Four-tier logical-staleness profile

| Resource label | Client count | Requested model-version lag |
|---|---:|---:|
| Strong | 10 | 0 |
| Medium | 15 | 0 |
| Weak | 15 | 1 |
| Straggler | 10 | 2 |

The system seed shuffles these labels over the 50 client identifiers. Assignments remain fixed within a cell. For each client, the emulator stores its current update in a history and supplies the update at the requested lag, clipped by available history. Thus effective lag ramps up during the first two rounds. The primary analysis excludes rounds 0--1.

The profile is a deterministic logical model-version intervention. It does not emulate wall-clock scheduling, CPU throughput, wireless transmission, packet loss, energy, deadline failures, or physical devices. Resource labels should not be interpreted as hardware measurements.

### S1.3 Krum-score and selection implementation

For each update, the implementation computes pairwise Euclidean L2 distances, Euclidean L2 distances after row-wise normalization, or cosine distances. The L2 distances are not squared. It sums the 39 smallest distances to other clients to form the score, orders all 50 clients by score, retains the first `int(0.76 × 50)=38`, and averages their supplied updates. Per-client logs record the score, selected indicator, and selection rank. The 39-neighbor and 38-output conventions are reported separately because they control different parts of Multi-Krum.

Row-wise normalization uses an epsilon of \(10^{-12}\). A vector at or below that norm is represented by the zero vector for normalized Euclidean distance; cosine distance involving such a vector is set to 1.0. These implementation conventions are reported for reproducibility and are not additional tunable controls in the formal grid.

## S2. Raw-log schema and integrity controls

Every formal system log contains the following fields:

- round and client identifier;
- resource group, requested staleness, and effective staleness;
- current-update norm, effective-update norm, and their ratio;
- current and effective cosine alignment to the current-update mean;
- norm of the stale-minus-current difference;
- aggregator score, selected indicator, and selection rank.

For each FashionMNIST cell, the runner and analyzers require:

1. exactly one occurrence of each round from 0 through 299 in the training log;
2. the expected completion marker;
3. a resolved configuration matching dataset, model, seeds, heterogeneity, attack, defense, and client count;
4. exactly 15,000 system-log rows;
5. exactly 50 unique clients in each round;
6. final accuracy at least 0.60; and
7. final-50-round accuracy slope at least -0.0015.

Files are hashed with SHA-256. A cell interrupted without a completion marker is not counted, even if it contains many usable-looking rows. The unchanged runner may rerun an incomplete cell from the beginning; it may skip only cells that pass the full audit.

## S3. Estimands and replication structure

For each train-seed/system-seed/distance cell and round window, selection rates are computed for each resource group. The principal estimand is 100 times the straggler selection rate minus the strong-client selection rate, in percentage points. Positive values indicate relative attraction; negative values indicate relative exclusion.

Normalized-minus-Euclidean and cosine-minus-Euclidean contrasts are paired within the same train/system seed before taking margins. This preserves the crossed randomization structure. Client-round rows and time bins are observations used to construct each cell summary; they are not independent replicates and do not enter row-level significance tests.

The main report includes:

- all 3 × 3 train/system cell disparities for each distance;
- system-seed margins over the three train seeds;
- train-seed margins over the three system seeds;
- finite-level train, system, and interaction sums-of-squares shares;
- leave-one-system-seed-out summaries; and
- pre-specified early and converged-late windows.

## S4. Stage 9 confirmatory and secondary analyses

### S4.1 Confirmatory windows and decision

The early window is rounds 2--29 and the converged late window is rounds 200--299. The lag-dose continuation gate requires, in both windows, a positive Euclidean system-seed margin for every system seed and at least one scale-removing control with a negative paired contrast for every system seed.

The early window passes: the Euclidean margins are +17.26, +12.98, and +20.71 pp, and both controls attenuate the disparity for every system seed. The late window fails because the Euclidean margins are +23.13, -0.27, and +0.87 pp and no control attenuates every system-seed margin. Therefore lag-dose and attack expansion stop under the frozen rule.

### S4.2 Time-resolved analysis

The time-resolved protocol was frozen before detailed trajectories were inspected. It uses rounds 2--9 as the first bin and then non-overlapping 10-round bins. Across 27 cells this produces 810 cell-bin rows. Sustained practical neutrality begins at the first bin whose disparity and all later bins remain within ±5 pp.

Euclidean system seeds 91002 and 91003 reach sustained neutrality at rounds 220 and 250. Seed 91001 never does. The independent verifier reconstructs all 810 rows from raw CSV files with maximum absolute disagreement \(5.684341886080802\times10^{-14}\).

### S4.3 Directional boundary audit

The directional protocol was also frozen before its detailed summaries were inspected. A stable direction-exclusion mechanism requires, for every system seed, a negative within-straggler effective-minus-current cosine shift, a negative straggler-minus-strong effective-cosine gap, and a negative cosine-distance selection disparity.

Only the first component passes. System seed 91001 retains a positive effective-cosine gap and positive cosine-selection disparity; the other two system seeds show negative values. The independent verifier reconstructs 54 cell-window and 810 binned quantities, with maximum absolute cell-window disagreement \(5.551115123125783\times10^{-17}\). The manuscript consequently treats direction drift as a conditional competing factor rather than a verified second mechanism.

## S5. Reproducibility ledger

| Evidence block | Formal cells | Raw rows per cell | Main analyzer | Independent verifier | Terminal status |
|---|---:|---:|---|---|---|
| Stage 8 converged mechanism confirmation | 15 | 15,000 | `src/analyze_stage8_converged.py` | `src/verify_stage8_independent.py` | Passed |
| Stage 9 crossed system-seed confirmation | 27 combined | 15,000 | `src/analyze_stage9_system_seed.py` | `src/verify_stage9_independent.py` | Early pass; late fail |
| Stage 9 time-resolved analysis | Reuses 27 | 15,000 | `src/analyze_stage9_trajectory.py` | `src/verify_stage9_trajectory_independent.py` | Passed |
| Stage 9 directional boundary | Reuses 27 | 15,000 | `src/analyze_stage9_directional.py` | `src/verify_stage9_directional_independent.py` | Stable exclusion rejected |
| Stage 10 CIFAR-10 transfer | Frozen at 27 | 3,000 | `src/analyze_stage10_cifar10.py` | `src/verify_stage10_independent.py` | Pass; 27/27 complete, learning-valid, numerically and semantically verified |

The Stage 9 manifest SHA-256 is `d8956ad2db8d095b318f735acc7306dd8801c26a157eddd4a272bb863a2e5990`. The frozen Stage 10 manifest SHA-256 is `bcfa8cc9204d537756dbddb25fb8feaf48154d707f06f8f256b1f92d11724f8a`.

## S6. Frozen Stage 10 transfer rules

The Stage 10 grid uses CIFAR-10, a simple CNN, 60 rounds, batch size 128, the same 50 clients, \(\alpha=0.5\), three train seeds, three system seeds, and three distances. Every cell must contain exactly 60 rounds and 3,000 system rows. Its final-10-round mean accuracy must be at least 0.15 and exceed its first-10-round mean by at least 0.03. These are malfunction guards, not competitive-accuracy claims.

Only after all 27 cells pass may the transfer gate be evaluated. It requires a crossed early Euclidean disparity of at least +5 pp, a positive Euclidean margin for every system seed, and negative normalized and cosine paired contrasts for every system seed. A complete gate failure is reported as a generalization boundary. An integrity or learning failure stops interpretation and cannot be repaired by dropping a cell or changing a threshold.

All 27 cells passed learning and integrity guards. The minimum final-10-round accuracy was 0.1973, the minimum final-minus-first-10-round gain was +0.0707, and the independent maximum absolute disagreement was 6.395e-14.

Crossed early Euclidean disparity: +14.84 pp.

| System seed | Euclidean disparity (pp) | Normalized minus Euclidean (pp) | Cosine minus Euclidean (pp) |
|---:|---:|---:|---:|
| 91001 | +11.19 | -1.19 | -1.67 |
| 91002 | +15.36 | -12.50 | -15.36 |
| 91003 | +17.98 | -21.31 | -17.86 |

The frozen transfer gate **passes**. This supports cross-dataset/model transfer of the early scale-sensitive selection effect, but not converged persistence, attack robustness, physical-device behavior, or a deployable defense.

## S7. Claim-control checklist

- Do not claim first discovery of Krum selection bias under non-IID data.
- Do not describe logical lag as measured hardware or network heterogeneity.
- Do not call normalized or cosine Multi-Krum a validated defense.
- Do not infer Byzantine or backdoor robustness from NoAttack experiments.
- Do not pool client-round rows as independent replicates.
- Do not hide system seed 91001 or report only the crossed late mean.
- Do not describe the directional evidence as a stable dual mechanism.
- Do not start lag-dose or attack grids after the frozen Stage 9 No-Go.
- Do not insert Stage 10 claims before exact completion, learning, and independent-verification checks pass.

## S8. Availability statements requiring author confirmation

The final supplement must replace the following placeholders using author-confirmed information only:

- public or anonymized code/archive URL;
- which raw logs can be deposited and under what license;
- funding and conflict-of-interest declarations;
- author names, affiliations, and CRediT roles; and
- target-journal-specific ethics and data-availability wording.
