# Scientific reproducibility bundle specification

## Scope

The scientific bundle is generated only after Stage 10 reaches an audited terminal state and the terminal manuscript candidate passes the independent claim verifier. It is not the publisher submission ZIP and does not infer author metadata, declarations, reviewer suggestions, or a public-data release policy.

## Included evidence

- Frozen Stage 8--10 protocols, manifests, and configurations.
- Main and independent analyzers, semantic verifiers, figure generators, queue runners, and manuscript-audit programs.
- Audited processed tables and JSON decisions for Stage 8, Stage 9, and Stage 10.
- Candidate manuscript and supplement, bibliography, generated Stage 10 insert, and provenance sidecars.
- Publication figures for the mechanism, crossed-seed, trajectory, directional, and transfer analyses.
- The exact framework files implementing distance-based aggregation and logical system heterogeneity.
- A generated README, file inventory, source and bundled SHA-256 hashes, and a ZIP archive.
- An independently implemented post-build verifier recomputes source, directory, inventory, checksum-file, ZIP-entry, closure, isolation, and private-path checks.

## Exclusions and privacy gates

- `results/raw`, `results/smoke`, partial cells, caches, credentials, and unrelated projects are never collected.
- Raw logs remain subject to the author-confirmed release policy and are not silently added.
- Text files are copied with the project root and user-home prefix replaced by portable placeholders. Any remaining Windows absolute path causes the build to fail.
- Existing bundle directories or ZIP files are not overwritten automatically.
- Author placeholders may remain because this bundle proves scientific closure, not publisher metadata completion.

## Terminal preconditions

1. `scientific_closure.json` reports `scientific_closure_generated` and 27 complete cells.
2. Numeric and semantic independent verifiers report `passed`.
3. The generated manuscript candidate reports a non-pending terminal state and `passed`.
4. Candidate and closure ledger hashes match the files on disk.
5. Every selected source remains within the project root and outside forbidden raw/smoke paths.
