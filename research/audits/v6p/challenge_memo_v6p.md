# A7 Post-Freeze Adversarial Audit Memo — V6P

- **Auditor:** A7 (independent; wrote only this file + `scientific_audit_v6p.json`)
- **Audit HEAD:** `a65a7c4d5412bc93b8cff0692009417307d3faac` (frozen population on disk, `results/` gitignored by repo convention)
- **Created:** 2026-08-25T02:50:44+00:00 · **Protocol:** `research/audits/v6p/a7_challenge_protocol.md` (40 items)
- **Census discipline:** 100% of every mandated population (3/3 experiments, all 37,862-row ledgers, all exposure events, all 13/13+8/8 stress variants, all hash entries, all reproductions, all 20 gates, all 15 findings). No population exceeded 100,000 rows ⇒ **seeded sampling never invoked** (registered seed `20260824`, unused).

## A. Pre-launch recheck (final HEAD)

| Item | Result | Note |
|---|---|---|
| P-A-1 clean tree | PASS_WITH_EXEMPTION | 5 dirty files, all inside `allowed_uncommitted_at_launch` declared in the **committed pre-launch blob** (`git show a43d2f0:…`, verified) |
| P-A-2 HEAD vs baseline | PASS_ANCESTOR_RULE | HEAD `a65a7c4`; baseline `launch_head a43d2f0`; ancestor rule holds. RETRY1/REVERSE launched exactly at `a43d2f0`; GOLDEN at descendant `9edfb89` — intermediate commits touch only registry contract + hash-verifier skip list (**no engine/math code**, diff inspected). Finding F-02 |
| P-A-3 external root | PASS | `baseline_self_hash_violations == []`; regex hits none; the `source_files_sha256` self-entry pins the **committed pre-freeze blob** `d7503e…` (recomputed from git object = match), current bytes anchored externally by attestation hash `93ba1f…` |
| P-A-4 attestation | PASS | verdict PASS, all checks true, `baseline_sha256` matches independently recomputed digest |
| P-A-5 precedence | PASS_ON_DECLARED_POPULATION | Attestation 00:55:21.702 and baseline creation 00:55:21.607 strictly precede RETRY1 01:06:24 / REVERSE 01:06:29 / GOLDEN 01:23:27. The earlier SENTINEL attempt (00:43:49, pre-baseline) was **voided** (`ABORTED.json`: scored=false, unregistered, byte-preserved). Finding F-04 |

## C. Post-freeze census highlights

- **Population (P-C-1):** exactly 3 registered roots (registry shards `v6p_{golden,sentinel_mom,sentinel_rev}`), 7 byte-preserved abort/preflight stubs with documented reasons, 3 reproduction dirs, 2 matrix roots. Matrix indices reference exactly these; no orphans; no V5R namespace reuse.
- **Accounting identity (P-C-2):** dual recomputation — reconciler components AND independent sums from raw `orders/positions/terminal/funding` rows — agree with equity delta within tolerance for all 3 experiments, fold level and experiment level. MOM residual ≈ −4.9e−11.
- **Continuous capital (P-C-3):** `capital_reset_injection == 0` everywhere; recon fold chain exact; dense real-run ledgers satisfy first==last boundary equality to $0; GOLDEN's sparse event-ledger gaps equal **exactly** each fold's first-bar costs (30.0 / 29.98344 / 29.96544) and reconstructed-path MDD equals reported `0.0017489776` to ≤1e−9 rel; `one_pass.single_engine_call=true`.
- **MDD/fold returns:** recomputed by A7 from ledger equity series: MOM/REVERSE rel err **0.0**; GOLDEN exact via reconstruction.
- **Risk caps (P-C-4):** every ledger row: gross ≤ 0.99999954, |net| ≤ 0.09555 (caps 1.00/0.10); RISK_MODE_V1 active both runs; 2,390/2,374 deterministic `reduce_only_trim` events persisted, zero non-trimmed breaches. Symbol weight is a **target cap = 0.25** per hashed `contracts/protocol.py PORTFOLIO_CONSTRAINTS` (my protocol's “0.20” parenthetical was mis-transcribed; corrected against frozen contract — F-08). Realized intrabar weight drift to 0.269 is mark-drift between rebalances; gross/net are hard-enforced every completed bar by design.
- **Funding (P-C-7/C07):** all 4,344 cashflow rows per real run map 1:1 to canonical bundle settlements with **exact rate match** (0 unmatched, 0 rate mismatch); notional basis uses engine panel marks (documented `audited-post-trade` semantics).
- **Stress (P-C-5):** `executed_unconditionally=true` in all 3 incl. SENTINEL whose base edge FAILs; 13/13 expected families per real run, 8/8 for GOLDEN's 2-symbol fixture universe; family metrics complete; no `expectancy_r` metric anywhere (disclosure note present).
- **XG1 (P-C-6):** counters row-derived over ALL executed orders (11,597 / 11,549 / 12 entries): missing_ts=0; violations=0 on both real runs. Code path inspection: scored path always supplies `execution_ledger_rows` (`portfolio_runner.py:1394-1397`); absent rows ⇒ INCONCLUSIVE, legacy booleans non-scored only. **GOLDEN XG1 FAIL (2 same-bar fills in fixture)** = the measurement working as designed; recorded as finding F-06 for V6 spec alignment.
- **XG0:** PASS with empty reasons ×3; fail-closed semantics verified in `_evaluate_xg0` (missing payload ⇒ INCONCLUSIVE, never PASS); measured blocks evidenced by `data_manifest.funding_completeness` + my independent settlement census.
- **Hashes (P-C-8):** 21/21 entries ×3 dirs recompute clean; zero unlisted files; zero files newer than manifest (hashes-last ordering holds). Reproduction rerun artifacts: 11/11 core files **byte-identical** to source hashes.
- **Reproduction (P-C-9):** 3/3 `all_match=true`, `rerun_process_separate=true`, **21 components** (≥14 required) covering the full PLAN §6.4(9) surface incl. `artifact_hashes`, `gate_result_verdicts`, `stress_report`, `scorecard_totals`, digests.
- **Matrix/registry (P-C-10):** final `v6p_validation/reconciliation.json`: `COMPLETE`, `mismatches=[]`, `registry_append_only_verified=true`, `stage_a_root=results/validation_v6p`. Merged registry rows 503–508 appended strictly after all prior rows, zero duplicate conflicts, shard↔merged verdicts identical.
- **Gate ledger sanity:** all 18 PASS + 1 PASS_WITH_CAVEAT evidence hashes match current bytes — **zero stale hashes**.

## Findings register

| ID | Sev | Status | Summary |
|---|---|---|---|
| F-01 | MEDIUM | RESOLVED | **C03 remediation (user-mandated classification):** pre-launch attestation was provisionally *self-issued* (committed freeze copy `0b95c123` still references superseded baseline `d7503e`); genuine A7 countersign executed post-hoc 01:35:51 verifying every claim; I independently re-executed all five claims at audit time incl. full suite rerun (623 passed, exit 0). Residual: countersigned file remains uncommitted; manifests pinned an intermediate hash `9f9adb21…` not recoverable from git history. Requires commit of countersigned artifact in integration commit. Not HIGH: preflight enforcement was mechanical/env-enforced and fail-closed, and no scored result depends on the attestation's claims (all re-derived here). |
| F-02 | MEDIUM | RESOLVED | Launch-head divergence: GOLDEN at `9edfb89` ≠ baseline `a43d2f0`. Ancestor rule holds; intermediate diffs are glue-only (verified hunk-by-hunk); disclosed in attestation claim_1 and gate C04. |
| F-03 | LOW | RESOLVED | All 5 manifests record raw `dirty_worktree_at_launch: true` with exemption-aware enforced preflight PASS; fail-closed behavior proven by three preserved abort stubs. Letter deviation from N02's "false", substance honest and enforced. |
| F-04 | MEDIUM | RESOLVED | Pre-baseline SENTINEL launch (00:43:49) voided `ABORTED_INFRA`, `scored:false`, unregistered, artifacts byte-preserved. Fail-closed worked; P-A-5 holds on the declared population. |
| F-05 | LOW | OPEN_RECOMMENDATION | `results/matrix/v6p_golden/report.json` carries stale `stage_a_root: results/portfolio_v4` and `declared_cells: 4` vs 1 executed; `index.json` correct; final validation reconciliation unaffected. Regenerate during integration. |
| F-06 | MEDIUM | RESOLVED_FOR_V6P | GOLDEN XG1 FAIL from same-bar fills in synthetic fixture (2/12 entries) — demonstrates measured gate correctly fails; zero look-ahead on real runs (0/11,597 and 0/11,549). Fixture semantics vs declared NEXT_BAR alignment carried to V6 spec (already noted in gate C08). No scored impact; GOLDEN cell verdict REJECTED regardless. |
| F-07 | MEDIUM | OPEN | **N14 letter-fail:** explicit `purge_embargo` fields absent from the V6P launch-manifest schema (only warmup isolation frozen: `warmup_bars: 1344`, warmup outside scored folds, boundaries fed to XG1). PLAN.md declares `purge_embargo: 24h` but `.md` files are outside the hash-pinned source set; `contracts/protocol.py` fields unused by V6P manifest class. Feeds V6 FG1. Per verdict rules, an open MEDIUM does not block authorization. |
| F-08 | LOW | RESOLVED | Protocol-letter deviations resolved against higher authority: symbol-weight cap 0.25 per hashed contract (protocol said 0.20); `reset_folds` key replaced by stronger equivalent evidence (`capital_reset_injection=0`, chain, one_pass); exposure_control logs enforcement *events* (risk mode evidenced in canonical_metrics + engine code); XG0 payload blocks not serialized into gate_result.json (compensated by fail-closed semantics + data_manifest blocks + independent census). |

## N01–N15 status table

| Finding | Orig severity | Status | Evidence |
|---|---|---|---|
| N01 baseline attestation pending / overclaim | CRITICAL | **CLOSED** | v5r slot untouched (`PENDING_A6`); new baseline carries no pending slot; addendum records N01; countersigned attestation PASS |
| N02 dirty worktree at launch | CRITICAL | **CLOSED** (with disclosure) | Exemption-aware enforced preflight; raw flags retained; abort stubs prove enforcement; v5r contrast immutable |
| N03 self-referential baseline hash | HIGH | **CLOSED** | Validator+regex clean; self-pin = committed ancestor blob (recomputed); negative fixtures green in suite |
| N04 reset-fold outer curve | CRITICAL | **CLOSED** | Zero capital resets; fold chains exact (recon + ledger); MDD rel err 0.0; single engine call |
| N05 risk mode inactive / gross >1 | CRITICAL | **CLOSED** | RISK_MODE_V1 active; gross ≤1.00, \|net\|≤0.10 on 100% of 75,731 ledger rows; trims persisted |
| N06 missing settlement/accounting artifacts | CRITICAL | **CLOSED** | Full artifact sets present; GOLDEN `exposure_control.jsonl` empty-by-design (benign scenario, unit-test asserted); terminal flat book ×3 |
| N07 hand-built XG1 booleans | CRITICAL | **CLOSED** | Measured path wired unconditionally on scored runs; counters = order counts; fail-closed without rows |
| N08 coverage adapter None | HIGH | **CLOSED** | XG0 PASS implies measured payload (INCONCLUSIVE otherwise, by construction); data_manifest blocks measured |
| N09 benchmark/funding reason conflation | HIGH | **CLOSED** | Distinct codes enforced in gates.py; reason-semantics tests pass (53 passed) |
| N10 conditional stress + expectancy_r | HIGH | **CLOSED** | Stress unconditional incl. failing base edge; families complete; no expectancy_r metric |
| N11 shallow reproduction surface | HIGH | **CLOSED** | 21-component full-surface comparison ×3, all_match, separate process, byte-identical reruns |
| N12 append_only false / stale stage_a_root | HIGH | **CLOSED** | Final reconciliation append-only true, mismatches [], COMPLETE, correct root (golden aux report nit → F-05) |
| N13 audit incompleteness | HIGH | **CLOSED** | This audit: 15/15 findings adjudicated, 20/20 gates corroborated, 100% census, no sampling |
| N14 purge/embargo not frozen | MEDIUM | **OPEN (MEDIUM)** | Warmup isolation frozen; purge_embargo field absent from V6P manifest schema → F-07 |
| N15 stale transition timestamps/heads | MEDIUM | **PENDING_INTEGRATION** | Transition created_at set; audited/integrated slots null awaiting this audit by design; `final_head 9edfb89` is ancestor of audit HEAD; refresh required post-audit |

## Gate corroboration C01–C20

C01–C18: independently corroborated from raw evidence (hashes recomputed, identities recomputed, censuses above). C03 corroborated as PASS_WITH_CAVEAT per F-01. **C19 = PASS** (this audit, zero unresolved HIGH/CRITICAL). **C20 = PASS** (no unresolved HIGH/CRITICAL; no S1 access; live-money surface UNCHANGED_DISABLED per intake + countersign pattern scan, no config changes in working tree).

## Verdict

**AUDIT_VERDICT = PASS** — zero unresolved HIGH/CRITICAL findings. Open items: F-05/F-07 (LOW/MEDIUM, non-blocking) and N15 integration mechanics.

**Conditions on authorization flip (`V6P_PASS_V6_AUTHORIZED`):**
1. Commit the countersigned attestation + these two audit artifacts.
2. Refresh transition heads (`audited_head=a65a7c4…`, timestamps monotonic) and regenerate golden matrix report (F-05).
3. Carry F-06 fixture semantics and F-07 purge/embargo freeze into V6 FG1 scope.

*Independence: A7 owns no implementation/results; all checks executed in separate reader processes under `.venv/bin/python`; raw recomputations outrank any reported verdict strings per protocol D-2.*
