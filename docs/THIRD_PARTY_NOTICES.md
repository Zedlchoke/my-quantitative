# Third-party notices (MDP-V1)

## MDRAP — selective adaptation upstream

- Repository: https://github.com/Aryan-20-04/mdrap, pinned at
  `7bc831ccde5b3d97dd784aeeb51e2d17982771c3` (MIT License,
  Copyright (c) 2026 MDRAP Platform Contributors; LICENSE SHA-256
  `33f80e45669593c83a0a6761021a9a016bb79d2962fa4b5f2db3569c615eb406`).
- MDP-V1 adapts IDEAS from the allowed set (canonical raw/canonical
  separation, quality status/reason codes, quarantine lineage,
  deterministic archive/replay, BBO/depth/TCA, watchdog/operator
  presentation) as clean-room implementations against the frozen
  `architecture_freeze.json` contracts. Per-file hash evidence:
  `research/control/market_data_plane_v1_run/upstream_manifest.json`.
- MDRAP is NOT a runtime dependency; its setup scripts, DLL/C fast
  path, demo keys, live endpoints, strategy/execution/RBAC stack were
  never executed, loaded, or imported. Full upstream test success is
  not claimed.
- Should any future file be copied or materially derived from MDRAP,
  it must carry MIT attribution in its header and this notice.

## Adopted supporting OSS (pinned, license-verified from installed bytes)

| Project | Version | License (measured) | Boundary |
|---|---|---|---|
| DVC | 3.67.1 | Apache-2.0 | local transport POC only; never data authority; no `dvc exp` ranking/sweeps |
| Hypothesis | 6.168.0 | MPL-2.0 (measured from installed LICENSE.txt — corrects the common Apache assumption) | test-only property testing; never production logic; never sole reproduction evidence |
| Pandera | 0.33.1 | MIT | boundary spike only; final decision `PANDERA_EVALUATED_NOT_ADOPTED` (frozen criteria); not imported by production modules |

Dependency lock (93 packages, per-artifact SHA-256):
`research/control/market_data_plane_v1_run/oss/dependency_freeze.json`.

## Data Fusion

Adopted from this repository's own audited cycle at exact commit
`c6a0576ef98dd4392e90805c8ba33821da62eabc` (branch
`orca/data-fusion-v1-a7-audit`), with two MDP-versioned semantic fixes
(G3 gate record). No external upstream involved.

## Deferred / not adopted (no install, no import in MDP-V1)

RD-Agent, skfolio, Dagster, Qlib, OpenLineage (deferred behind binding
triggers, plan §4.8); MLflow, Great Expectations, ArcticDB (not
adopted). See `oss/adoption_matrix.json`.
