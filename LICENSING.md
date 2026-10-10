# Licensing of this archive

This archive is **not** covered by a single licence. It mixes original work with
third-party code, and the two carry different terms.

## 1. Original code — MIT

Everything authored for this study is released under the MIT Licence
(see `LICENSE`). This covers:

- `src/` — analysis, orchestration, verification and figure-generation code
- `scripts/`
- `configs/`
- `docs/`
- `manuscript/`
- `results/`

## 2. Original data, documentation and processed tables — CC BY 4.0

The de-identified formal evidence and the processed tables derived from it are
released under the Creative Commons Attribution 4.0 International Licence
(CC BY 4.0), https://creativecommons.org/licenses/by/4.0/

## 3. Third-party code — GPL-2.0 (retained)

`vendor/FLPoison/` contains a **modified subset** of the FLPoison framework,
which is distributed under the GNU General Public Licence, version 2. The three
files bundled here are:

- `vendor/FLPoison/global_args.py`
- `vendor/FLPoison/system_heterogeneity.py`
- `vendor/FLPoison/aggregators/aggregator_utils.py`

They were modified for this study (the distance functions used by the audited
selection rules were added to `aggregator_utils.py`). Because they are derivative
works of GPL-2.0 code, **they remain under GPL-2.0**; the full licence text is in
`LICENSE-GPL-2.0.txt`. The MIT Licence in `LICENSE` does **not** apply to them.

Upstream project and the citation its maintainers request:

- FLPoison software artifact, https://github.com/vio1etus/FLPoison
- Heyi Zhang, Yule Liu, Xinlei He, Jun Wu, Tianshuo Cong, Xinyi Huang,
  "SoK: Benchmarking Poisoning Attacks and Defenses in Federated Learning,"
  arXiv:2502.03801 (2025). https://doi.org/10.48550/arXiv.2502.03801

If you redistribute this archive or a derivative of it, keep
`LICENSE-GPL-2.0.txt` alongside the `vendor/` directory.

## 4. Scope note

No raw training logs are included; see `README.md` and `S8` of the supplementary
material for what the archive does and does not contain. `${PROJECT_ROOT}` and
`${USER_HOME}` are portable placeholders substituted during de-identification.
