# Submission package plan and readiness gates

## Current state

The frozen 27-cell Stage 10 replication grid is complete. All 27 cells passed the artifact, learning, numerical, and semantic checks, and the pre-specified replication gate passed. The closure wrapper generated and independently verified the terminal report, Stage 10 manuscript insert, main and supplementary manuscript candidates, scientific closure ledger, and de-identified reproducibility bundle. The paper is scientifically closed for the frozen Stage 8--10 scope. Journal-neutral DOCX/LaTeX/PDF conversion, seven-figure packaging, accessibility audits, and page-level visual QA are complete under `artifacts/submission/journal_neutral`; author-confirmed metadata and target-journal formatting remain before submission.

The recommended primary target is **The Journal of Supercomputing**, Original Paper, using the subscription route (no APC). The target decision and official-source checks are recorded in `docs/target_journal_decision_2026-08-30.md`; a target-specific 137-word/6-keyword technical candidate is under `artifacts/submission/the_journal_of_supercomputing`. Author-identifying metadata is independently pending in `manuscript/author_confirmation_form.md`. Scientific completion must not be conflated with author confirmation.

## Scientific terminal branches

### Branch A — transfer Pass

1. Run `src/analyze_stage10_cifar10.py` only after the auditor reports 27/27 complete and zero invalid cells.
2. Run `src/verify_stage10_independent.py` and require 27 cells, 54 windows, matching gate decisions, and reported maximum disagreement.
3. Run `src/verify_stage10_semantics_independent.py` and require all configuration, lag, rank, geometry, and path-isolation checks to pass.
4. Run `src/render_stage10_manuscript_insert.py`; accept only its `pass` branch.
5. Add the cross-dataset/model early-effect contribution, exact system margins, control contrasts, learning range, matrix figure, and scope boundary.
6. Keep lag-dose, attacks, physical-device claims, and converged persistence as No-Go.

### Branch B — complete, learning-valid transfer Fail

1. Complete the same main and independent checks; no cell may be removed.
2. Accept only the renderer's `fail` branch.
3. Report the failed transfer gate as a negative generalization boundary.
4. Retain the FashionMNIST mechanism diagnosis but remove all cross-dataset replication wording.
5. Reassess journal scope without launching outcome-repair experiments.

### Branch C — integrity or learning Invalid

1. Stop scientific interpretation of Stage 10.
2. Retain every artifact and report the failed guard.
3. Do not evaluate or report the transfer-effect signs as evidence.
4. Freeze a separate calibration protocol before any rerun; do not alter thresholds or replace cells.

## Required source package

| Item | Source / generator | Current gate |
|---|---|---|
| Main manuscript | `manuscript/manuscript_stage10_candidate.md` | Terminal Pass candidate generated and independently verified |
| Supplement | `manuscript/supplementary_stage10_candidate.md` | Terminal Pass candidate generated and independently verified; publication copy still needs author metadata |
| Bibliography | Frozen `manuscript/references.bib`; submission-only `artifacts/submission/journal_neutral/journal_references.bib` | Frozen key set verified; collision search refreshed through 2026-08-30 |
| Evidence chain | `docs/submission_evidence_chain.md` | Living and current |
| Stage 9 claim audit | `src/verify_manuscript_stage9_claims.py` | Passing |
| Stage 10 result insert | `src/render_stage10_manuscript_insert.py` | Pass branch rendered with hashed terminal inputs |
| Main figures | `artifacts/figures/manuscript` and verified Stage 9/10 figure folders | Seven current figures; Stage 10 matrix and trajectory present |
| Journal-neutral package | `src/build_journal_neutral_submission.py`; `src/audit_journal_neutral_submission.py` | DOCX/LaTeX/PDF and seven figures generated; 13+5 PDF pages inspected; audit status is blocked only on author confirmation and target journal |
| JOS target package | `src/build_jos_submission_candidate.py`; `src/audit_jos_submission_candidate.py` | Original Paper technical candidate; 137-word abstract; six keywords; flat LaTeX references; 7 PNG + 7 vector PDF figures; 13+5 pages rendered and inspected; subscription/no-APC route recorded |
| Author metadata | `manuscript/author_confirmation_form.md` | Author confirmation pending |

## Final deliverables after scientific closure

1. Journal-neutral clean manuscript DOCX.
2. Journal-neutral LaTeX source with bibliography and figure files.
3. Main manuscript PDF rendered from the final source.
4. Supplementary DOCX/PDF.
5. Individual publication-quality PDF/SVG/PNG figures with matching captions.
6. Title page, highlights if required, cover letter, declarations, and reviewer suggestions.
7. Reproducibility archive containing frozen configs, manifests, analyzers, independent verifiers, processed tables, figure scripts, hashes, and a README; raw logs included according to the author-confirmed release policy.
8. Submission ZIP with a machine-generated inventory and SHA-256 checksums.

## Final mechanical quality gates

- No `[[STAGE10...]]`, `[AUTHOR TO CONFIRM]`, or caption placeholders remain in deliverable files.
- Abstract respects the target journal's word limit after inserting the terminal Stage 10 sentence.
- Every citation key resolves and every bibliography item is cited.
- Every displayed numerical value is checked against terminal JSON/CSV artifacts.
- All figures exist in vector and high-resolution raster forms and match their audit hashes.
- DOCX and PDF are rendered page by page; no clipped equations, tables, captions, references, or blank spill pages remain.
- The submission archive inventory matches the actual files and contains no smoke data, partial cells, cached credentials, private paths, or unrelated G-drive project results.
- Author declarations are copied only from the signed-off confirmation form.

The terminal scientific sequence is wrapped by `scripts/finalize_stage10_scientific.ps1`. It audits the complete 27-cell grid before doing any analysis, refuses partial/missing/invalid coverage, then runs the frozen main analysis, numeric verifier, semantic verifier, fixed manuscript-insert renderer, and candidate assembler in order. It never starts training and never overwrites the pre-transfer sources. The assembler writes separate `manuscript_stage10_candidate.md` and `supplementary_stage10_candidate.md` files with a hash audit. Its `scientific_closure.json` records the terminal decision and hashes of the required outputs; human review and author confirmation remain separate gates.

After scientific closure, the same wrapper invokes `src/build_scientific_reproducibility_bundle.py` to create a separate de-identified evidence bundle under `artifacts/submission`. Its allowlist and gates are frozen in `docs/reproducibility_bundle_spec.md`, and its audit records the exact scientific-closure hash. Raw and smoke logs are excluded by default; adding raw data remains an explicit author release decision.
