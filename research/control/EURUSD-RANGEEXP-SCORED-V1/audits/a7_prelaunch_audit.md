# A7 PRELAUNCH AUDIT — EURUSD-RANGEEXP-SCORED-V1

- Auditor: A7 (independent, fresh context — no prior involvement in this cycle)
- Measured (UTC): 2026-09-23T20:53:49Z
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/eurusd-rangeexp-scored-v1/integration`
- Branch / HEAD: `orca/eurusd-rangeexp-scored-v1-integration` @ `c5987372382f3a425c358406f238893c93b25693`
- Scope: prelaunch gate BEFORE any scored cell runs (two-key law; owner verbatim GO is key 2)
- Method: every claim recomputed from bytes/commands in this session; nothing trusted from prose.

## VERDICT: REFUSED

One BLOCKING finding (F1, governance/registry). All technical checks — freeze chain,
engine byte-identity, data plane, independent dry-run reproduction, cell/config
definitions, boundaries — PASS. The blocker is administrative and remediable: the
cycle has NO row in the canonical registry `plans/CYCLE_REGISTRY.json`, so there is
no registered lifecycle (ACTIVE_LIGHT/PLANNED), no registered budget cap (6), and no
machine-anchored `go_phrase`. Per the mission invariant, missing evidence is
NOT_RUN, never inferred PASS: the gate cannot issue AUTHORIZED on an unregistered
cycle identity.

## Fresh-context declaration

A7 declares: this audit was produced in a single fresh session with zero prior
context in EURUSD-RANGEEXP-SCORED-V1; no state was inherited from any prior audit,
lane worker, or dispatch packet beyond the audit charter itself; all checks below
were independently recomputed (git patch-ids, sha256 digests, parquet re-read,
dry-run execution, registry queries) and no artifact other than this audit pair
(`a7_prelaunch_audit.md` + `a7_prelaunch_audit.json`) was created or modified.

## Checks

| # | Check | Result | Evidence (measured this session) |
|---|-------|--------|----------------------------------|
| 1 | Plan commit on main | PASS | `a846e2b869929dd5…` is tip of `main`; adds `plans/PLAN_eurusd_rangeexp_scored_v1.md` (80 lines) only |
| 2 | Cherry-pick onto lane branch | PASS | Branch commit `9352abef2f8d…` has identical `git patch-id --stable` = `55ab043a351c92e9a9f0c63aedab573bba6d0add`; plan file diff between the two commits = 0 lines; branch parent chain `c5987372 → 9352abef → 86668a5f` (V2 terminal anchor) |
| 3 | Freeze commit contents | PASS | `c5987372382f…` adds `code_freeze.json`, `scripts/scored_cells.py` (167 ln), `scripts/engine.py` (464 ln), `v2_lib.py`, `v2_campaign.py`, `build_bars.py`, `duka_lib.py`, `.gitignore` (1672 insertions); exists only on the lane branch |
| 4 | Engine sha + byte identity | PASS | sha256(`scripts/engine.py`) = `cc868402e63db2f6b487fc544fe0799889db4c5e0e0df3f3689693f0871cb491` = `code_freeze.json.engine_sha256`, prefix `cc868402e63d`; `cmp` byte-identical to `research/control/EURUSD-OPEN-SEARCH-V2/scripts/engine.py` in the SAME worktree; `v2_lib.py` sha `efb87e37…` matches freeze; `m1_manifest.json` sha `ef154574…` matches freeze and census |
| 5 | M1 manifest | PASS | schema `eosv1.m1_manifest@1`, 4014 files, `complete: true`, `missing: 0` |
| 6 | Raw-file sample hashes | PASS | 12/12 files verified (sha256 + byte size), 2 per year 2021..2026 alternating ASK/BID (first and mid entries per year), 0 mismatches, on-disk path `data_local/duka/M1/<key>` |
| 7 | bars1h.parquet | PASS | Re-read with pandas: exactly 30,550 rows; cols `b_o,b_h,b_l,b_c,a_o,a_c`; ts 2021-01-03T23:00Z .. 2026-06-30T20:00Z |
| 8 | Census | PASS | `verdict: BUILD_PASS`; all 3 gates true; `bars15_valid: 130,911`; `data_manifest.bars1h_rows: 30550`; manifest sha matches freeze |
| 9 | Independent dry-run | PASS | Ran `.venv/bin/python research/control/EURUSD-RANGEEXP-SCORED-V1/scripts/scored_cells.py --dry-run` from the worktree root myself: printed 12/12 `reconciled: true` (C3/C4 × DEV/HOLDOUT × k∈{1.0,1.5,2.0}), final line "DRY_RUN: S1 all reconciled; no PnL printed"; zero PnL numbers in output |
| 10 | Dry-run side effects | PASS | `outcomes/` empty before and after (no `scored_cells.json`); `git status --porcelain` clean |
| 11 | Cells S1..S6 implemented | PASS WITH FINDINGS | S1 (12 reconciliation checks), S2–S5 leg decompositions, S6 drift flags present; no computation beyond plan §2 machinery exists. Findings F2 (S1 compares 3 of 5 preregistered metrics), F3 (per-leg PF omitted), F4 (baseline set reduced to SHORT_ALWAYS) |
| 12 | S6 drift rule | PASS | Code: `short_net > 0 AND total_net != 0 AND abs(short_net) >= 0.5*abs(total_net) AND SHORT_ALWAYS_net(k=1.0, same window) > 0` → `DRIFT_DEPENDED` else `NO_DRIFT_FLAG`. Matches the charter phrasing (`|total|`); see note F5 on the plan's literal text |
| 13 | Candidate configs | PASS | `cfg_of`: C3 → `FX2-RANGEEXP.configs[2]` = `{lo_q 0.3, hi_q 0.7, use_breakout false}` (fade); C4 → `configs[3]` = `{0.25, 0.75, false}`. Equals `candidates_frozen_v2.json` (config_index 2/3, digests `020e645dbfec2cdc` / `548bb8606af4beae`) and `code_freeze.json.candidates_immutable`; V2 committed dev numbers (C3 7147.1/6822.1 PF 1.7287; C4 6561.1/6235.35 PF 1.6497) present as reconciliation refs |
| 14 | No config selection/alteration | PASS | `CANDS` hardcoded; only CLI switch is `--dry-run`; configs never assigned/mutated; plane slices are shallow copies with every array attribute replaced (source plane untouched); single write surface `outcomes/scored_cells.json` (full mode only) |
| 15 | No orders/paper/live; no secrets | PASS | Scored path (scored_cells → v2_campaign → v2_lib → engine) imports no network code; the only HTTPS client is `duka_lib.py` (Dukascopy fetcher), not imported by the scored path; grep found no credentials/tokens/order surfaces |
| 16 | go_phrase in plan | PASS | Plan §0: `go_phrase  GO EURUSD RANGEEXP SCORED V1` ("typed verbatim by the owner at this cycle's own gate after A7 prelaunch") |
| 17 | Registry row (lifecycle/budget/GO state) | **FAIL — BLOCKING** | Canonical `plans/CYCLE_REGISTRY.json` (main repo, the only authority researchctl reads) has 59 cycles, ZERO matching `RANGEEXP`; `researchctl.py cycle list | grep RANGEEXP-SCORED` prints nothing; worktree's stale registry copy (54 cycles) also has none. Therefore: lifecycle is neither ACTIVE_LIGHT nor PLANNED, budget max 6 is not machine-registered, `go_phrase_state` not anchored. Charter requirement unmet |
| 18 | Heavy lock / foreign workers | PASS (note F6) | `locks inspect`: `flock_state: free`; the only registry row is a FOREIGN cycle (`CRYPTO-HISTORICAL-REPLICATION-3F-V1`) whose pid is dead (verdict `CONTROL_STATE_DRIFT`, stale registry, reclaim is round-2 discipline — not this audit's action). No contention for this light compute (plan §4: seconds of vectorized work) |
| 19 | Budget max 6 | FAIL (consequence of #17) | Declared in plan §0 ("6 scored cells MAX") but not registered in the machine registry; unverifiable as an enforced cap |

## Independent reproduction (audit-strength, reproduction-class only)

The shipped dry-run reconciles only {trades, net_pips, pf} (finding F2). To make
the F2 finding decidable, A7 independently recomputed all 12 arm×window×k books
with the FULL preregistered metric set — including `hit` and `maxdd_pips` using the
equity curve returned by `run_strategy` (which `scored_cells.py` discards). Result:
**12/12 byte-exact on all five metrics** vs `campaign_dev_v2.jsonl` +
`holdout_check_v2.json` (e.g. C3 DEV k1: 1000 trades / 7147.1 / 1.7287 / 0.619 /
288.9; C4 HOLDOUT k2: 87 / 161.5 / 1.1718 / 0.5862 / 392.9). This was strictly
reproduction-class work — no S2–S6 cells were computed by the auditor, so the
scored budget (S1..S6) remains untouched.

## Findings

| ID | Severity | Blocking | Finding |
|----|----------|----------|---------|
| F1 | HIGH | **YES** | Cycle absent from canonical `plans/CYCLE_REGISTRY.json`: no lifecycle (required ACTIVE_LIGHT/PLANNED), no budget max 6, no machine-anchored `go_phrase_state`. `cycle list | grep RANGEEXP-SCORED` is empty. Two-key gate key 1 cannot attach to an unregistered cycle identity. Remedy: owner/lead registers the row (e.g. `researchctl.py cycle register … --lifecycle … ` with budget max 6 and go_phrase `GO EURUSD RANGEEXP SCORED V1`) via a registry commit; a delta re-audit of checks 17/19 alone can then flip this verdict. |
| F2 | MEDIUM | no | S1 gate narrower than preregistered: `scored_cells.py` reconciles only {trades, net_pips, pf}; plan §2 S1 requires "every metric"; `hit` and `maxdd_pips` are not compared and the equity curve from `run_strategy` is discarded (zeros passed to `metrics`), making maxdd reconciliation impossible as written. Mitigated: A7's independent all-5-metric reconciliation passes 12/12 byte-exact, so widening the gate would still pass. Recommend widening before the scored run or recording an owner-accepted deviation. |
| F3 | MEDIUM | no | S2–S5 leg decomposition omits per-leg PF; plan §2 lists "long-leg vs short-leg net pips, trades, hit, PF". Under-computation only; recommend adding PF per leg or an owner waiver. |
| F4 | MEDIUM | no | Plan §2 baseline paragraph ("Baselines recomputed identically per cell window: CASH, LONG_ALWAYS, SHORT_ALWAYS, RANDOM_MATCHED(seed 20260923)") is only partially implemented: the script recomputes SHORT_ALWAYS per window (k=1.0) only. Recommend completing the baseline set or an owner waiver before GO. |
| F5 | LOW | no | Interpretation note: script's S6 uses `abs(total_net)` (with a `total_net != 0` guard) where the plan's literal text reads `|short_leg_net| >= 0.5 * total_net` (unsigned RHS would be vacuous for negative totals). Script matches the charter's canonical phrasing (`|total|`) and is the conservative reading; identical outcome for any positive-total book. Record in the terminal report. |
| F6 | LOW | no | `locks inspect` verdict `CONTROL_STATE_DRIFT`: stale foreign registry row (CRYPTO-HISTORICAL-REPLICATION-3F-V1, pid dead, `flock_state: free`). No contention for this light compute; reclaim belongs to round-2 discipline, not to this audit. |

## Gate arithmetic

- Technical readiness: PASS (checks 1–16, 18).
- Governance readiness: FAIL (check 17, and 19 as consequence).
- Verdict = **REFUSED** until F1 is remedied and re-audited (delta scope: checks
  17/19). F2–F4 are non-blocking but should be resolved (code fix or recorded
  owner waiver) before the owner's verbatim GO is consumed.

## Artifact pair

- `audits/a7_prelaunch_audit.md` (this file)
- `audits/a7_prelaunch_audit.json` (machine-readable same content)

---

# ROUND 2 — DELTA RE-AUDIT (A7, same fresh-session discipline, audit-only)

- Measured (UTC): 2026-09-23T21:00:41Z
- Remediation commit under audit: `8110dd26a693d17ad3d35b5212f51c03e260aa3e` on `orca/eurusd-rangeexp-scored-v1-integration` (touches ONLY `scripts/scored_cells.py`, +33/−8; verified via `git show --stat`)
- Registry commit: `d7c9d2d345b3…` on `main` ("registry: EURUSD-RANGEEXP-SCORED-V1 ACTIVE_LIGHT @c5987372 budget 0/6 …")

## ROUND-2 VERDICT: AUTHORIZED

## Delta scope results (charter round-2 items 1–4)

| # | Item | Result | Evidence (measured this round) |
|---|------|--------|-------------------------------|
| 1 | F1 registry row | **RESOLVED — PASS** | `cycle list` now prints `EURUSD-RANGEEXP-SCORED-V1  ACTIVE_LIGHT  0/6  c598737  orca/eurusd-rangeexp-scored-v1-integration`. Full row: `lifecycle: ACTIVE_LIGHT`, `budget {used:0, max:6}`, `head: c5987372382f…` (the freeze commit), `go_phrase: "GO EURUSD RANGEEXP SCORED V1"`, `go_phrase_state: "REGISTERED_NOT_CONSUMED"`, `phase: REGISTERED`, `s1: SEALED_UNTOUCHED`, `workers: 0`, `active_heavy: false`, plan path `plans/PLAN_eurusd_rangeexp_scored_v1.md`. Commit `d7c9d2d3` verified on `main`. |
| 2 | Five-metric S1 gate + sanitized dry-run | **RESOLVED — PASS** | Diff replaces `np.zeros` equity with the real `equity` from `run_strategy` and the `ok` conjunction now covers all five metrics: trades (exact), net_pips (≤1e-6), pf (None-ness + ≤1e-6), hit (None-ness + ≤1e-9), maxdd_pips (≤1e-6). I re-ran `scored_cells.py --dry-run` from the worktree root twice: 12/12 `reconciled: true` (C3/C4 × DEV/HOLDOUT × k∈{1.0,1.5,2.0}); parsed output programmatically — per-check fields are only {arm, k, window, reconciled}, zero PnL tokens (`net_pips/pips/pf/maxdd/hit`) anywhere in stdout; tail line "DRY_RUN: S1 all reconciled; no PnL printed"; assert guard intact. |
| 3 | F3/F4/F5 diffs vs plan text | **RESOLVED — PASS** | F3: `legs()` now emits `long_pf`/`short_pf` via `leg_pf` (gross win/gross loss, round 4, None when no losses/empty leg) — plan §2 "…, hit, PF" satisfied. F4: full baseline set per window at k=1.0 — CASH=0.0, LONG_ALWAYS (ones), SHORT_ALWAYS (−ones), RANDOM_MATCHED(seed=20260923) (`np.random.default_rng(20260923)`, `integers(-1,2,size=n)`) recorded in `rec['baselines']` as `DEV_k1`/`HOLDOUT_k1`; construction byte-matches V2's `v2_holdout.py` recipe ("recomputed identically"). F5: S6 now `short_net > 0 AND total_net != 0 AND short_net >= 0.5 * total_net AND SHORT_ALWAYS(k=1.0, same window) > 0` — the plan §2 literal, exactly as the round-2 charter requested. Diff contains NOTHING beyond these hunks; configs (CANDS/cfg_of), refs, slices, and boundaries unchanged. |
| 4 | No scored run before GO | **PASS** | `outcomes/` still empty (no `scored_cells.json`) before and after my dry-runs; `git status --porcelain` clean except this audit's untracked `audits/` pair. |

## Unchanged-check spot re-verification (remediation-adjacent)

- Engine chain intact: sha256(`engine.py`) still `cc8402…/cc868402e63db2f6b487fc544fe0799889db4c5e0e0df3f3689693f0871cb491`, `cmp` byte-identical to V2's engine in the same worktree. Data plane untouched by 8110dd26 (commit stat: 1 file).
- Heavy lock: still no contention (row CRYPTO-HISTORICAL-REPLICATION-3F-V1 is that cycle's governance; flock free; light compute per plan §4) — round-1 F6 stands as recorded, no action.

## Round-2 findings (all non-blocking)

| ID | Severity | Blocking | Finding |
|----|----------|----------|---------|
| F7 | LOW | no | Registry row `head` (c5987372) is one commit behind the measured branch tip (8110dd26) — the tip advanced by this remediation commit one minute after registration. Benign (the freeze commit — the sha that anchors engine/data/candidates — is unchanged and was independently re-verified this round); recommend refreshing `head` at the next registry touch to avoid the stale-head adapter-warning pattern seen on terminal cycles. |
| F8 | LOW | no | Cosmetic: `scored_cells.py` module docstring still says "tolerance 1e-9 abs on pips" while the code uses TOL=1e-6 on net_pips/maxdd and 1e-9 on hit only; dead no-op lines (`if name == "DEV" or not dry_run: pass`). No behavior impact. |
| F9 | LOW | no | Informational: with the plan-literal F5 form, a hypothetical negative-total book would satisfy `short_net >= 0.5 * total_net` vacuously once `short_net > 0`; for the actual books (C3/C4 totals positive on both windows per V2 refs) the flag outcome is identical to the round-1 `abs(total)` form. Recorded per remediation intent; no action. |

Round-1 F1–F5: CLOSED (verified above). Round-1 F2–F4 waivers no longer needed — remediated in code. Round-1 F6: stands as recorded, foreign-cycle governance.

## Gate arithmetic (round 2)

- Technical readiness: PASS (delta + spot re-verification).
- Governance readiness: PASS (F1 resolved, row verified from the registry JSON itself).
- Verdict = **AUTHORIZED** for the scored run of cells S1–S6 under plan
  `plans/PLAN_eurusd_rangeexp_scored_v1.md`, budget cap 6, contingent on the
  owner's verbatim key-2 GO phrase `GO EURUSD RANGEEXP SCORED V1` at this
  cycle's own gate (two-key law; this authorization is key 1 only and is NOT
  the GO).

## Artifact pair (round 2)

- `audits/a7_prelaunch_audit.md` (this file, round-2 section appended)
- `audits/a7_prelaunch_audit_r2.json` (machine-readable round-2 delta)
