# MDP-V1 third-party decision record

Cycle: MARKET-DATA-PLANE-V1 · Authority: `plans/PLAN_market_data_plane_v1.md` §4–§5 · Generated 2026-09-09 (A1)

## 1. MDRAP (selective adaptation upstream)

- **Pin:** https://github.com/Aryan-20-04/mdrap @ `7bc831ccde5b3d97dd784aeeb51e2d17982771c3`
  (remote HEAD observed equal to the pin at intake — `upstream_manifest.json`).
- **License:** MIT, `Copyright (c) 2026 MDRAP Platform Contributors`;
  LICENSE SHA-256 `33f80e45669593c83a0a6761021a9a016bb79d2962fa4b5f2db3569c615eb406`.
- **Mode:** read-only clone into a disposable staging directory outside every git
  worktree. Setup scripts were never executed; the DLL/C fast path was never
  loaded; no upstream endpoint was contacted; MDRAP is **not** a runtime
  dependency of this repository.
- **Adaptation set (ideas only, prefer clean implementation):** canonical
  raw/canonical separation, quality status + reason codes, quarantine with
  lineage, deterministic archive/replay, venue/consolidated BBO, optional
  depth views, research TCA, observable watchdog states, operator presentation.
  See the per-file map in `upstream_manifest.json`.
- **Forbidden (inventory recorded, never imported):** strategy SDK, paper
  executor, broker/live adapters, shared-memory/SBE/multicast/C-fast-path,
  Excel export, RBAC/security defaults, demo keys, benchmarks.
- **Provenance obligation:** any copied or materially derived code carries MIT
  attribution in the file header and `docs/THIRD_PARTY_NOTICES.md`. Provenance
  is mandatory even for small derivations.
- **Full upstream test success is NOT claimed** (planning audit found missing
  optional dependencies and targeted failures; upstream tests were not run).

## 2. Adopted supporting OSS (installed, pinned)

| Project | Version | License (measured from installed bytes) | Role boundary |
|---|---|---|---|
| DVC | 3.67.1 | Apache-2.0 | local transport/cache POC only; never a data authority, trial tracker, or manifest replacement; `dvc exp` ranking/sweeps forbidden |
| Hypothesis | 6.168.0 | **MPL-2.0** (measured — corrects the common Apache assumption) | test-only property testing with frozen profiles; never production logic; never the only reproduction evidence |
| Pandera | 0.33.1 | MIT | batch-boundary compatibility spike under frozen acceptance criteria; production adoption only if every criterion passes; else `PANDERA_EVALUATED_NOT_ADOPTED` |

Dependency lock: 93 resolved packages with SHA-256 per artifact
(`oss/dependency_freeze.json`); installed versions verified equal to pins.
Licenses hashed from installed dist-info (`oss/adoption_matrix.json`).

## 3. Deferred (design-only; NOT installed, NOT imported)

RD-Agent (MIT, design-only until MDP-V1 pass + one reboot asset cycle),
skfolio (BSD-3, until two independent survivors), Dagster (Apache-2.0, until
2 hosts / 10 recurring jobs / 2 evidenced scheduler failures), Qlib (MIT,
offline conformance reference only), OpenLineage (Apache-2.0, schema reference
only). Activation triggers are binding and recorded in
`oss/adoption_matrix.json` §4.8 of the plan.

## 4. Not adopted in MDP-V1

MLflow (duplicate ledger), Great Expectations (duplicate validation platform),
ArcticDB (license-ambiguous storage dependency). Reconsider only under a
separate owner plan.

## 5. Secret posture

No credential, demo key, or example secret is accepted anywhere in this cycle;
the recursive scan at P5/P5A covers tracked files, the dependency tree and the
git history range of this branch. Violations fail the G8/G8D gate.
