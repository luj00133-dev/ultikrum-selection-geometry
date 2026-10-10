# Stage 10 execution and interruption log

## Purpose

This log records non-scientific execution events for the frozen Stage 10 CIFAR-10 grid. It does not alter the protocol, analysis, learning guards, transfer gate, or cell definitions. Times use Asia/Shanghai unless otherwise stated.

## Frozen identifiers

- Protocol implementation commit: `9c61e9c`.
- Main analyzer freeze commit: `925c196`.
- Formal manifest SHA-256: `bcfa8cc9204d537756dbddb25fb8feaf48154d707f06f8f256b1f92d11724f8a`.
- Formal grid: 27 cells, each requiring 60 rounds and 3,000 client-round rows.
- Runner: `scripts/run_stage10_cifar10_early_replication.ps1 -Run`.

## Event 1 — initial formal queue

- The single-GPU formal queue started on 2026-08-29 at approximately 15:03.
- The runner used its full-cell completeness checks before skipping any existing cell.
- Smoke artifacts remained in the dedicated ignored `results/smoke` tree and were never included in the formal manifest or progress counts.

## Event 2 — unexpected queue termination

- At the last live observation before interruption, seven formal cells were complete and `stage10_cifar10_a05_r60_multikrum_normalized_s2026_sys91003` was incomplete.
- The incomplete cell's last formal writes occurred at approximately 15:51. Its log lacked the required 60-round coverage and completion marker.
- At 19:31, process inspection found no Stage 10 runner or training process. The progress auditor reported:
  - complete: 7;
  - partial: 1;
  - missing: 19;
  - invalid complete cells: 0; and
  - failed learning cells among complete cells: 0.
- The incomplete cell was not promoted, hashed as a complete artifact, or used in any analysis.

## Event 3 — protocol-preserving recovery

- After confirming that no duplicate GPU process existed, the same frozen runner was restarted at approximately 19:31.
- The runner independently verified and skipped exactly the seven complete cells.
- It selected the incomplete normalized-Euclidean cell as the next run and restarted that cell from round 0 under the unchanged configuration. It did not append to or salvage the partial trajectory.
- The new process used the same dataset, model, train/partition seed 2026, system seed 91003, distance rule, 60-round budget, logical-staleness profile, and Multi-Krum parameters.
- Subsequent audits showed the recovered queue advancing normally. The rerun cell later became complete and the queue proceeded to later cells.

## Integrity consequence

This interruption changes wall-clock completion time only. It does not create an additional replicate, modify the formal grid, or permit partial-row reuse. The terminal Stage 10 analysis must still require all 27 cells and recompute hashes from the final on-disk artifacts. Any future interruption is handled by the same rule: verify complete cells, never count a partial cell, and rerun only the incomplete cell from the beginning under the unchanged runner.

## Current status

This section is updated only at meaningful milestones. As of the post-recovery audit that motivated this log, 11/27 cells were complete, one cell was running, 15 were not yet started, and no complete cell had failed integrity or learning guards. The authoritative live count remains `src/audit_stage10_progress.py`, not this narrative snapshot.
