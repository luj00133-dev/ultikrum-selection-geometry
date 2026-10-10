# Literature collision audit: Krum selection geometry under heterogeneity and staleness

## Search cutoff and scope

Searches were last refreshed on **2026-08-30 (Asia/Shanghai)**. The discoverable literature examined includes work available online or published through 30 August 2026. Queries combined `Krum`, `Multi-Krum`, `honest client`, `selection bias`, `non-IID`, `staleness`, `straggler`, `update norm`, `cosine`, and `system heterogeneity`, with targeted checks of arXiv, OpenReview, PMLR, ACM, IEEE, Elsevier, and primary conference/project pages.

This is a collision audit, not a PRISMA systematic review. Coverage is constrained by indexing and access available on the search date. It establishes a defensible novelty boundary but must be refreshed immediately before submission.

## Closest work

| Work | What it already establishes | Collision with this project | Remaining distinction |
|---|---|---|---|
| Bao, Wu, and He, [BOBA: Byzantine-Robust Federated Learning with Label Skewness](https://proceedings.mlr.press/v238/bao24a.html), AISTATS 2024 | Under label skew, Krum and other robust AGRs can repeatedly select majority-class gradients and discard honest gradients with large outer variation, even without attacks; proposes a new robust method. | **High conceptual collision** on honest-gradient selection bias under non-IID data. | BOBA studies label/subspace variation and defense design, not logical staleness, resource-group selection disparity, scale contraction, crossed system seeds, or training-stage decay. Our paper must not claim first discovery that Krum is biased under non-IID data. |
| Karimireddy, He, and Jaggi, [Byzantine-Robust Learning on Heterogeneous Datasets via Bucketing](https://openreview.net/pdf?id=jXKKDEi5vJt), ICLR 2022 | Shows that IID-oriented robust aggregators can fail under heterogeneous data and proposes bucketing with convergence guarantees. | **Medium collision** on the broad incompatibility between classical robust aggregation and non-IID updates. | Attack/robust-optimization focus; no honest resource-group selection mechanism, stale-update norm/cosine instrumentation, or crossed scheduler analysis. |
| Liu et al., [Byzantine-Robust Learning on Heterogeneous Data via Gradient Splitting](https://proceedings.mlr.press/v202/liu23d/liu23d.pdf), ICML 2023 | Evaluates robust AGRs under heterogeneous data and explicitly measures the fraction of honest gradients participating in aggregation. | **Medium-high collision** on honest-gradient inclusion as an evaluation quantity. | Focuses on a new robust algorithm and heterogeneity/attack performance, not scale-sensitive attraction of logically stale clients or time/system-seed claim boundaries. |
| Park et al., [Handling Both Stragglers and Adversaries for Robust Federated Learning](https://fl-icml.github.io/2021/papers/FL-ICML21_paper_7.pdf), ICML FL Workshop / Sageflow line, 2021 | Jointly studies staleness/stragglers and adversaries; uses staleness-aware grouping and compares with Multi-Krum. | **High topical collision** on stragglers plus robust aggregation. | It treats straggler handling as a system/robustness design problem and attributes Multi-Krum degradation largely to effective attack ratio and waiting/grouping. It does not diagnose no-attack honest selection attraction through radius/angle geometry or report crossed system-assignment trajectories. |
| Bellachia, Bouchiha, and Ghamri-Doudane, [SoK: Understanding Backdoor Attacks & Defenses in Federated Learning](https://doi.org/10.1016/j.eswa.2026.132558), *Expert Systems with Applications* 325 (2026) 132558 | Its benchmark reports substantial false-positive rates for detect-and-filter defenses under non-IID data and explicitly links benign-update spread in L2 norm/cosine to honest-client filtering. | **High motivational collision** on collateral exclusion of honest non-IID clients and norm/cosine geometry. | It is an attack/defense SoK and benchmark. It does not report the counterintuitive no-attack attraction of stale clients, scale-removing paired controls, system-seed dependence, or sustained time-resolved neutrality. |
| Subramanian, Khan, and Islam, [Bypassing Krum: Selection-Aware Backdoor Attacks in Federated Learning](https://arxiv.org/abs/2608.06637), arXiv:2608.06637 (2026) | Optimizes malicious updates to enter geometry favored by Krum, using nearest-neighbor proxies and norm/variance constraints. | **Medium-high mechanistic collision** on the idea that Krum has favored geometric regions. | Attacker-centric and backdoor-oriented; it does not study naturally stale honest updates, resource groups, non-IID crossed factors, or attraction decay. Cite it to connect honest and adversarial selection geometry without claiming the same phenomenon. |
| [Brief Announcement: Byzantine Machine Learning, MultiKrum and an Optimal Notion of Robustness](https://doi.org/10.1145/3796701.3815914), PODC 2026 | Supplies formal robustness guarantees for Multi-Krum. | **Low-medium collision** because it changes how Multi-Krum theory should be described. | Robustness coefficients do not establish unbiased honest-client coverage under data/system heterogeneity. The manuscript must distinguish Byzantine robustness from selection neutrality. |
| FedJoint, [adaptive orchestration with staleness-aware weighting](https://doi.org/10.1016/j.infsof.2026.108177), 2026; FedGS, [asynchronous FL with stale-gradient compensation](https://doi.org/10.1016/j.future.2026.108558), 2026 | Recent systems work treats stale updates as a convergence problem and down-weights/compensates them. | **Medium topical collision** on staleness under non-IID training. | Neither work, based on the accessible descriptions, isolates Multi-Krum honest-client selection geometry or the possibility that raw Euclidean scoring favors scale-contracted stale updates. |
| Lu et al., [Modeling behavioral staleness in asynchronous federated learning (FedPSA)](https://doi.org/10.1016/j.eswa.2026.133003), *Expert Systems with Applications* 329 (2026) 133003 | Models behavioral staleness with stage-adaptive aggregation using sensitivity/cosine signals and a momentum-derived training-stage indicator. | **Medium-high topical collision** on staleness geometry and training-stage adaptation. | FedPSA is a convergence-oriented asynchronous aggregation method. It does not isolate no-attack Multi-Krum group-inclusion disparity, paired scale-removing controls, or crossed resource-assignment trajectories. |

## Collision decision

No located paper has the same complete combination of:

1. honest, no-attack clients under joint Dirichlet data heterogeneity and controlled logical staleness;
2. Multi-Krum resource-group **selection attraction**, rather than only exclusion, accuracy loss, or attack failure;
3. paired Euclidean, normalized-Euclidean, and cosine controls that diagnose radial scale contribution;
4. crossed train/partition seeds and resource-assignment/system seeds;
5. 300-round convergence checks plus a frozen time-resolved decay analysis; and
6. independent raw-artifact recomputation with an explicit negative directional result.

The broad problem is **not new**. Honest-client selection bias under non-IID data is clearly established by BOBA and reinforced by later surveys/benchmarks. Staleness-aware robust FL is also established by Sageflow and asynchronous-FL work. Therefore the paper is publishable only if positioned around the narrower empirical finding and methodology:

> Logical staleness can create a scale-sensitive early **attraction** of honest straggler updates under Euclidean Multi-Krum; this attraction is altered by scale-removing metrics, decays differently across resource assignments, and does not imply a stable opposing direction-exclusion mechanism.

## Claims that must not appear

- "First work to identify Krum selection bias under non-IID data."
- "First work to study robust federated learning with stragglers."
- "First work to show honest clients can be filtered by robust aggregation."
- "Normalized/cosine Multi-Krum solves fairness or Byzantine robustness."
- "The observed geometry is universal across training or system assignments."

## Recommended related-work organization

1. **Robust aggregation under heterogeneous data:** Krum, bucketing, BOBA, gradient splitting.
2. **Straggler/asynchronous FL:** Sageflow and stale-gradient weighting/compensation.
3. **Selection geometry and collateral filtering:** BOBA, the 2026 SoK benchmark, and Krum-Proxy.
4. **This paper's gap:** no-attack stale-client attraction, radial-control diagnosis, crossed system seeds, time-resolved claim audit, and independent recomputation.

## Risk assessment

- Broad novelty risk: **high** if the paper says only "Krum is biased under non-IID data."
- Exact-method collision risk: **low to medium** based on literature discoverable through 2026-08-30.
- Publishability risk after correct positioning: **moderate**; it depends heavily on Stage 10 cross-dataset/model transfer and concise presentation of the negative late/directional results.
