# Reproducibility archive — When Logical Staleness Attracts

Audited processed evidence, resolved configurations and analysis code for the
study *"When Logical Staleness Attracts: Training-stage and Assignment-dependent
Selection Geometry of Multi-Krum under Non-IID Federated Learning."*

Frozen terminal state: **pass**.

---

## What this archive contains

| Path | Contents |
|---|---|
| `configs/` | Resolved frozen configurations for every formal experiment (Stage 8 / 9 / 10). |
| `src/` | Main analyzers and the independently implemented verifiers. |
| `scripts/` | Orchestration entry points. |
| `results/manifests/` | Per-experiment manifests (identifiers, hashes, status). |
| `results/processed/` | Processed tables and per-cell summaries used in the paper. |
| `artifacts/` | Figures and rendered evidence blocks. |
| `docs/` | Protocols, result note, literature-collision audit, evidence chain, and this release's scope notes. |
| `manuscript/` | Manuscript candidates and the reference list used at build time. |
| `vendor/FLPoison/` | Modified subset of the FLPoison framework needed to run the audited aggregators. |
| `inventory.json` | Per-file inventory with bundled SHA-256 values (141 entries). |
| `SHA256SUMS.txt` | Flat checksum list for the same files. |

**Excluded by design:** raw training logs, smoke runs, partial or cached
artifacts, and anything not part of the formal evidence chain. The reported
analyses rest on the 15 Stage 8, 18 Stage 9 and 27 Stage 10 formal runs.

## De-identification

`${PROJECT_ROOT}` and `${USER_HOME}` appear in place of absolute paths. Author
identities and declarations were deliberately not inferred from the artifacts.

## Integrity

`inventory.json` records, for each file, its bundled SHA-256 and (where the file
originated upstream) the source SHA-256. `SHA256SUMS.txt` is the flat
counterpart. These were produced by the frozen build, not edited afterwards.

## Requirements

Python 3.9+ with NumPy, pandas and Matplotlib. See `configs/` and
`docs/*_protocol.md` for the exact model, optimiser and heterogeneity settings of
each experiment. The audited framework expects a CUDA device for the Stage 10
CIFAR-10 grid; the Stage 8/9 FashionMNIST grids run on CPU.

## Reproducing the reported tables

1. Read the relevant `docs/stage*_protocol.md` for the frozen protocol and gates.
2. Read the matching `configs/*.json` for the resolved parameters.
3. Run the analyzer listed in `docs/submission_evidence_chain.md`; each analyzer
   validates manifest fields, row coverage and learning guards before computing
   summaries.
4. Compare against the independent verifier for the same stage. The verifiers use
   separate code paths and standard-library parsing where practical; their
   maximum numerical disagreement is printed rather than rounded away.

## Licensing

This archive mixes original and third-party work and is **not** covered by one
licence. See [`LICENSING.md`](LICENSING.md):

- original code — **MIT** (`LICENSE`)
- original data and documentation — **CC BY 4.0**
- `vendor/FLPoison/` (modified) — **GPL-2.0** (`LICENSE-GPL-2.0.txt`)

## Citing

See [`CITATION.cff`](CITATION.cff). A DOI for this archive can be added there
after the first Zenodo release.

## Contact

Corresponding author: Lu Jiang, School of Electronic and Optical Engineering,
Nanjing University of Science and Technology, Nanjing, Jiangsu 210094, China.
