# V12 I lane — OILEV-V2 family implementation evidence

Worktree `.worktrees/crypto/v12/i-oilever-v2`, branch `orca/v12i-oilever-v2`,
bootstrap `ec4b59fe80d601471343d6feb38687c6ef4cd981` (verified before any
write; porcelain empty). Producer role `I-OILEV`. Scope: family module/plugin
+ evidence + tests. **No scored PnL on real data** — synthetic fixtures and
schedule-only diagnostics only.

## BLOCKER (surfaced, not papered over): frozen `arm_config_digest` mismatch

`research/v11.publication_identity.arm_config_digest(StrategyIdentity(...),
arm_id=...)` does NOT reproduce the digests recorded in
`research/control/v12_run/selection_freeze.json` for any of the three frozen
OILEV-V2 arms (0/3). Exhaustive search documented in
`identity_digest_report.json`: every defensible reading of the frozen
contract was tried — `arm_config_id` ∈ {recorded role, arm_id, variants},
direction over the full repo vocabulary plus a generated mechanism
vocabulary (>50k candidates), strategy_id pinned/convention variants
(`hyp_a12_v12_oilever_v2_delev`, `A12-V12-OILEVER-V2-DELEV.v1`, …), config
shapes (verbatim / window-less / date-form / dict-form / epoch / sign- and
role-augmented), funding-sign and benchmark-case variants, arm_id argument
variants. The SAME function reproduces the V11 freeze digests exactly
(verified in-run). Conclusion: the V12 freeze record must be re-issued by
A1 with the identity contract published (or its digests recomputed from the
recorded cells). Until then the identity module pins the coordinator-specified
contract (family/strategy ids, benchmark exclusion, funding sign, matrix
cohort hint `v12`, window, recorded role as `arm_config_id`, recorded config
verbatim, V11-inherited direction `long_short_beta_neutral`), and
`tests/test_v12i_oilev_v2_identity.py::test_arm_config_digest_reproduces_freeze`
is a STRICT xfail: the suite stays green while the mismatch stays visible and
turns RED the moment identity and freeze record agree.

## Evidence artifacts (this directory)

| file | verdict |
|---|---|
| `identity_digest_report.json` | recomputed vs recorded digests — 0/3 match (BLOCKER above) |
| `c1_field_verification.json` | PASS — first/mid/last real stamps × 19 symbols: consumed OI row strictly before stamp, ≤48h fresh, positive, equals the loader-selected parquet row; execution bars loader-selected completed 15m bars (close boundary exact slot), fill open ≥ decision instant, close decode `raw i128 / 1e16` verified within float64 ULP |
| `feasibility_52_stamps.json` | **PASS 52/52 × 3 arms** — eligible 19–19 per stamp (≥9 required), exact 4+4 legs, max abs weight 0.125 ≤ 0.30, uniform scale never triggered (A4 parity) |
| `funding_events_while_held.json` | **A4 open item RESOLVED** — native `funding_data/scan_2026` settlements counted per held span: anchor/control 6612 events / 90 spans, neighbour 5437 / 103 spans (schedule-only counts, never PnL) |
| `double_generation_determinism.json` | PASS — all 3 arms × 52 stamps generated twice, canonical-JSON sha256 byte-identical |
| `drop_one_diagnostic.json` | PASS — repaired stress layer (`research.adapter_v10.stress.select_drop_one_symbol`) drops exactly the held max-|weight| symbol; unheld cohort symbols never selected; zero-held book refused |
| `exact_arm_dummy_dryrun.json` | PASS — adapter primitives traversed per arm on the staged snapshot (universe 19, schedule 52, folds F0/F1/F2 accepting a dropped fold, fills/marks finite, native settlements, LONG_PAYS_POSITIVE_RATE accrual verified); zero-position DUMMY payload REFUSED (`REFUSED_ZERO_POSITIONS` → OBSERVATION row), held-position DUMMY payload published (CELL_RESULT row), exact replay idempotent; temp ledger 3+3 rows |

## Tests

`tests/test_v12i_oilev_v2_{identity,pit,causal,determinism,feasibility}.py` —
41 passed + 1 strict xfailed (the digest blocker). Golden fixtures
(`research/v12/families/oilev_v2/golden/`) are committed, sha256-pinned in
the determinism tests, and never written by the suite (tracked files
unchanged after a run).

## Data

Read-only absolute-path reads of the staged V11 S0 snapshot
(`oi_data/consolidated` 20/20 daily OI parquets, `catalog_live_crypto/data`
bars decoded `raw i128 / 1e16`, `funding_data/scan_2026` native
settlements). Nothing copied or committed. Bars injected to the plugin are
the loader-selected completed bars around the frozen schedule's instants —
consumed strictly as execution events, never as decision inputs.
