# Stage 9: converged system-seed crossed confirmation

## Frozen question and design

Stage 9 tests whether the converged alpha=0.5 distance effect from Stage 8 is robust to the resource-assignment seed. It changes no data, model, optimizer, attack, cardinality, neighbor-count, lag profile, or convergence threshold.

- FashionMNIST / LeNet / FedSGD / NoAttack, Dirichlet alpha=0.5;
- 300 rounds, 50 clients, four-tier logical staleness;
- train/partition seeds 2026--2028, selected as the first three pre-specified Stage 8 seeds rather than by outcomes;
- system seeds 91001--91003;
- MultiKrum Euclidean, normalized Euclidean, and cosine; output cardinality 38 and 39 score neighbors;
- 3 train seeds x 3 system seeds x 3 distances = 27 crossed cells.

The nine `system_seed=91001` cells are immutable Stage 8 artifacts. Stage 9 generates only the 18 cells for 91002 and 91003 in a separate directory. Existing cells may enter the combined analysis only after full log, resolved-config, row-coverage, and SHA-256 verification. No copying or synthesized compatibility rows are permitted.

## Completion and convergence gates

Every new cell must have epochs 0--299 exactly once, `Training finished on`, the frozen resolved configuration, and exactly 15,000 system rows covering 50 unique clients in every round. All 27 combined cells must have final accuracy >=0.60 and final-50-round slope >=-0.0015. A failed or interrupted cell stops analysis and is never silently removed.

The replication structure is crossed. Client-rounds are observations, not replicates; system seeds do not increase the number of independent training seeds. For every distance and time window, analysis reports the 3x3 cell matrix, train-seed and system-seed margins, and finite-level sums-of-squares shares for train, system, and interaction. The same crossed summaries are computed for normalized-minus-Euclidean and cosine-minus-Euclidean paired disparities.

## Pre-specified decision rule

Continue to a lag-dose experiment only if both conditions hold in the early (2--29) and converged late (200--299) windows:

1. the Euclidean straggler-minus-strong marginal disparity is positive for every system seed; and
2. at least one scale-removing control has a negative control-minus-Euclidean marginal contrast for every system seed.

The analyzer also reports leave-one-system-seed-out means. Failure of either condition stops attack expansion and triggers a system-seed-dependent reframe or a larger seed confirmation. Even a pass supports only logical-staleness mechanism claims, not physical-device, network, deadline, or Byzantine-security claims.

## Execution

The runner defaults to read-only DryRun and requires explicit `-Run` for formal execution. It executes one GPU cell at a time and skips a cell only after checking all artifacts, frozen resolved fields, exact epoch coverage, and exact client-round coverage.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_stage9_system_seed_converged.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_stage9_system_seed_converged.ps1 -Run -ProjectRoot ${PROJECT_ROOT}
```
