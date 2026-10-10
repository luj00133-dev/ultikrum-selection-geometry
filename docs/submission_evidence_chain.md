# Submission evidence chain and claim audit

## Purpose

This living audit maps every intended paper claim to immutable protocol, raw evidence, independent verification, and an explicit boundary. A claim is manuscript-ready only when all four are present. Pilot findings and smoke outputs are excluded from confirmatory evidence.

The related-work collision audit is recorded in `docs/literature_collision_audit_2026-08-29.md`; it was refreshed through 2026-08-30 and must be checked again if submission is materially delayed.

## Evidence ledger

| Evidence block | Frozen protocol / manifest | Raw scope | Main analysis | Independent check | Decision |
|---|---|---:|---|---|---|
| Stage 8 converged alpha=0.5 mechanism confirmation | `docs/stage8_a05_converged_protocol.md` | 15 cells; 5 train seeds × 3 distances; 300 rounds | `src/analyze_stage8_converged.py` | `src/verify_stage8_independent.py` | Passed convergence and mechanism gate |
| Stage 9 converged crossed system-seed confirmation | `docs/stage9_system_seed_converged_protocol.md`; manifest SHA-256 `d8956ad2db8d095b318f735acc7306dd8801c26a157eddd4a272bb863a2e5990` | 27 cells; 3 train × 3 system × 3 distances; 300 rounds | `src/analyze_stage9_system_seed.py` | `src/verify_stage9_independent.py` | Early gate passed; late gate failed; lag-dose and attacks stopped |
| Stage 9 time-resolved secondary analysis | `docs/stage9_time_resolved_protocol.md` | Existing 27 cells; 810 non-overlapping cell-bin rows | `src/analyze_stage9_trajectory.py` | `src/verify_stage9_trajectory_independent.py`; max error `5.68e-14` | Supports training-stage dependence, not late persistence |
| Stage 9 directional boundary diagnostic | `docs/stage9_directional_diagnostic_protocol.md` | Existing 27 cells; 54 cell-window and 810 binned rows | `src/analyze_stage9_directional.py` | `src/verify_stage9_directional_independent.py`; max error `5.55e-17` | Stable direction-exclusion mechanism not supported |
| Stage 10 CIFAR-10/simplecnn transfer test | `docs/stage10_cifar10_early_replication_protocol.md`; formal manifest SHA-256 `bcfa8cc9204d537756dbddb25fb8feaf48154d707f06f8f256b1f92d11724f8a` | 27 complete cells; 3 train × 3 system × 3 distances; 60 rounds | `src/analyze_stage10_cifar10.py` | `src/verify_stage10_independent.py`; `src/verify_stage10_semantics_independent.py` | Transfer gate passed; 27/27 learning-valid and independently verified |

## Claim-to-evidence map

### C1. Euclidean Multi-Krum can favor logically stale honest clients early in training

- Required evidence: positive straggler-minus-strong selection disparity under Euclidean distance across pre-specified seeds and early windows.
- Current support: Stage 9 system-seed margins in rounds 2--29 are +17.26, +12.98, and +20.71 pp.
- Audit: all 27 Stage 8/9 cells have complete logs, resolved configurations, 15,000 client-round rows, and independent recomputation.
- Boundary: FashionMNIST/LeNet, Dirichlet `alpha=0.5`, FedSGD, four-tier logical staleness, NoAttack. This is selection attraction, not proof that slow hardware is preferred.
- Transfer evidence: Stage 10 passed its frozen CIFAR-10 gate, supporting a bounded cross-dataset/model early-stage effect.

### C2. Update scale contributes materially to the early selection disparity

- Required evidence: paired normalized-Euclidean-minus-Euclidean and cosine-minus-Euclidean contrasts are negative across every pre-specified system-seed margin, together with norm/score co-movement.
- Current support: both controls attenuate or reverse the early disparity for all three Stage 9 system seeds; median within-cell Spearman associations are 0.510 for negative norm-ratio gap and 0.615 for negative score gap.
- Audit: paired contrasts are formed within each train/system cell; no client-round pseudo-replication or row-level p-value is used.
- Boundary: distance controls alter the metric and neighbor ranking. They diagnose scale sensitivity but do not establish a unique causal mediator or a new fair/robust defense.

### C3. The effect is training-stage and system-seed dependent

- Required evidence: pre-specified late window plus time-resolved trajectories and leave-one-system-seed-out sensitivity.
- Current support: late Euclidean margins are +23.13, -0.27, and +0.87 pp. Omitting system seed 91001 leaves +0.30 pp; seeds 91002 and 91003 reach sustained ±5 pp neutrality at rounds 220 and 250.
- Audit: fixed windows, fixed 10-round bins, and a strict sustained-equivalence criterion were frozen before fine-grained inspection.
- Boundary: a system-seed-invariant converged-persistence claim is not supported under the frozen design. The crossed mean must not be presented without the three system-seed trajectories.

### C3b. Direction drift is a measured but non-stable competing factor

- Required evidence for a stable exclusion mechanism: negative straggler directional shift, negative straggler-minus-strong effective-cosine gap, and negative cosine-distance selection disparity for every system-seed margin.
- Current result: only the first condition passes. The effective-cosine ordering and cosine-selection sign fail for system seed 91001; the median Euclidean time-bin association is `rho = -0.144`.
- Audit: 54 cell-window quantities were independently recomputed with maximum error `5.55e-17`.
- Boundary: this is a negative claim audit. Direction drift may compete with scale in particular cells, but a stable converged non-IID direction-exclusion contribution is not supported.

### C4. Cross-dataset/model replication

- Required evidence: all 27 Stage 10 cells pass integrity and learning guards; crossed early Euclidean disparity is at least +5 pp; every system-seed Euclidean margin is positive; both control contrasts are negative for every system seed.
- Current support: 27/27 cells passed; crossed Euclidean disparity is +14.84 pp; system-seed margins are +11.19, +15.36, and +17.98 pp; both paired controls are negative for every system seed.
- Audit: the numeric verifier independently recomputed 54 cell windows with maximum absolute disagreement `6.395e-14`; the semantic verifier checked 81,000 rows, 1,620 rounds, lag semantics, group assignments, and 38-of-50 selection cardinality.
- Decision: the frozen cross-dataset/model replication gate passed.
- Boundary: CIFAR-10/simplecnn is a second controlled simulation, not physical-device or Byzantine validation.

## Claims explicitly ruled out by current gates

- A system-seed-invariant selection disparity after convergence.
- A lag-dose response, because the pre-specified Stage 9 gate was No-Go.
- Byzantine or backdoor robustness, because the confirmed design is `NoAttack`.
- Real-device, bandwidth, deadline, energy, or network effects.
- A fairness guarantee or a deployable defense supplied by normalized/cosine controls.
- A confirmed, system-seed-stable "dual opposing mechanisms" claim under converged non-IID training.
- Population-level inferential certainty from client-round or time-bin pseudo-replication.

## Submission assembly gate

Stage 10 reached the audited **Transfer pass** terminal state. Manuscript assembly therefore uses C1--C4 with all boundaries below:

1. Use C1--C4 and frame the contribution as a reproducible, training-stage-dependent selection-geometry diagnosis.
2. Retain the negative late-persistence and directional-mechanism results; do not reopen lag-dose or attack experiments to strengthen the narrative.

The complete-Fail and Invalid branches remain archived counterfactual rules; neither was entered. No cell was dropped and no threshold changed after inspection.

## Pre-transfer manuscript assembly audit

- The bounded English source was created before Stage 10 reached a terminal result: `manuscript/manuscript_v0.md` (commit `dac91c3`). It contains explicit Stage 10 placeholders and does not infer author names, affiliations, funding, conflicts, repository availability, or CRediT roles.
- The pre-transfer abstract contains 156 words after excluding its Stage 10 placeholder, leaving room for one audited transfer sentence while preserving a 200-word target.
- Primary-source bibliographic records are stored in the frozen `manuscript/references.bib`; the candidate citation and bibliography key sets match. The journal-neutral copy adds two submission-only 2026 records in `artifacts/submission/journal_neutral/journal_references.bib`, and the collision search was refreshed through 2026-08-30.
- `src/verify_manuscript_stage9_claims.py` (commit `5d9ccf1`) independently checks manuscript table values and signs against the terminal Stage 9 JSON/CSV artifacts, verifies the time-resolved and directional boundary numbers, rejects prohibited novelty language, checks the abstract budget and citation set, and requires Stage 10 placeholders while no terminal Stage 10 analysis exists.
- `src/render_stage10_manuscript_insert.py` (commit `b4aa421`) was frozen while the Stage 10 queue was incomplete. It refuses partial or inconsistent inputs, requires 27 cells and 54 independently verified cell windows, checks the main/independent gate decisions, and renders fixed Pass, complete-Fail, or learning-Invalid wording without editing the manuscript automatically. Synthetic tests cover all three terminal branches and a decision-mismatch rejection.
- `src/plot_manuscript_stage9_crossed_matrix.py` renders the main 3-panel early crossed matrix directly from the verified 27-row Stage 9 early table. Its audit sidecar records the source CSV hash and PNG/PDF/SVG hashes; the manuscript verifier checks both the source and displayed PNG hashes.
- A source-to-manuscript method audit found and corrected two documentation-only mismatches before submission assembly: the framework uses unsquared L2 distances (not squared L2), and all 27 formal Stage 9 resolved configurations use batch size 128 (not the 64 in an unused long-template file). The current verifier reads every resolved configuration and checks the common tuple: 300 rounds, batch 128, learning rate 0.01, one local epoch, SGD, momentum 0.9, weight decay 0.0001, 50 clients, zero adversaries, uncached partitions, and zero data-loader workers.
- Submission assembly is split into scientific and author-confirmation gates in `docs/submission_package_plan.md`. Author names, order, affiliations, CRediT roles, funding, conflicts, release policy, and journal metadata remain explicitly unresolved in `manuscript/author_confirmation_form.md`; none may be inferred by the automated workflow.
- Stage 10 execution incidents are retained in `docs/stage10_execution_log.md`. The first queue termination left seven complete cells and one partial cell; after process absence and cell coverage were verified, the same runner skipped the seven complete cells and reran the incomplete cell from round 0. No partial rows entered a scientific table.
- Stage 10 also requires `src/verify_stage10_semantics_independent.py`, frozen before grid completion. This third, read-only check covers configuration fields, formal-path isolation, metadata/group assignment, logical-lag semantics, 38-of-50 selection cardinality and ranks, geometry field validity, norm-ratio recomputation, and agreement with the final artifact hash ledger. A semantic failure is treated as an integrity failure, not as a scientific transfer result.
- The manuscript verifier now has a pre-frozen terminal Stage 10 branch. Once `analysis.json` exists, it requires the numeric and semantic verifiers, the hashed generated insert, removal of all scientific Stage 10 placeholders from both main and supplement, the exact audited abstract sentence, crossed disparity, three system-margin rows, correct Pass/Fail/Invalid boundary wording, and a final abstract no longer than 200 words.
- Before Stage 10 completion, `src/assemble_stage10_manuscript_candidate.py` and `scripts/finalize_stage10_scientific.ps1` froze the terminal writing path. The assembler never overwrites the pre-transfer sources: it generates separate main and supplementary candidates from the hashed insert, suppresses all transfer-effect values and figures in the learning-invalid branch, and records candidate hashes. The closure wrapper then invokes the manuscript verifier on those exact candidate paths and retains its machine-readable result.
- `src/render_stage10_results_report.py` freezes a separate human-readable terminal report with input and output hashes. Pass and complete-Fail branches retain all frozen gate values; the learning-Invalid branch suppresses effect signs, contrasts, figures, and effect-gate outcomes and reports only integrity and learning failure.
- `src/verify_stage10_results_report_independent.py` independently checks the report branch, all displayed Stage 10 values and gate rows, every report-input hash, and the invalid-branch non-disclosure rule before the report enters the closure ledger or reproducibility bundle.
- The Stage 10 closure begins by verifying `configs/stage10_scientific_code_freeze.json`. This pre-completion ledger covers the protocol, formal manifest, runner, progress auditor, main/numeric/semantic analysis stack, and every Python/YAML implementation file under the vendored FLPoison framework. Analysis cannot start if any raw or normalized-text hash changes.
- The candidate verifier passed after Stage 10 closure on the exact hashed main and supplementary candidates. It must be rerun after every numerical manuscript edit; submission-only prose calibration is separately checked by `src/audit_journal_neutral_submission.py` and must not alter frozen numerical claims.
