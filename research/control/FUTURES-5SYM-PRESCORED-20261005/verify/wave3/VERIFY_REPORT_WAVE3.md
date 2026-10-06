# VERIFY_REPORT_WAVE3 — FUTURES-5SYM-PRESCORED-20261005

Auditor: LANE-VERIFY-WAVE3 (independent; built none of what it audits)
Audit SHA: `aa5a4bf78e4e5e8d766559fc44c964c79a3a2c40` (verified: `git rev-parse HEAD` ==
audit SHA at start and end; `git status --porcelain` clean at start, clean at end)
Wave-3 commits audited: `b2d086ca` (erratum+manifest) → `8e03e0bd` (CONTRACTS+MEAS-FX+MEAS-NQ)
→ `ccf0835a` (ADAPT-NQ+ADAPT-FXEB) → `2aea1d7a` (ADAPT-FXJA) → `890fbfa6` (FREEZE-WIRING +
symbol_contracts corrections) → `aa5a4bf7` (synth v2).
Writes confined to `verify/wave3/` + `dispatch/handoff_VERIFY-WAVE3.json`. No commits, no
network, no S1/GO/registration. Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.

## Overall verdict: **VERIFIED_WITH_NOTES**

Finding counts: **CRITICAL 0 · MAJOR 0 · MINOR 5 · NOTE 6**.

Every load-bearing wave-3 number recomputed by this auditor from committed bytes reproduced
EXACT (m1 rho pair + 1/27 flip; m4 MDE cell + r-ratios; NQ 285/285 + parquet hashes + 30-session
median deltas; CONTRACTS 24/24 evidence hashes + 3 MATCH cells + exactly-4 PENDING; the
symbol_contracts diff is exactly 4+/3- and its rth value matches CALENDAR_PIT_POLICY_NQ §1).
All six test suites re-run at the audit SHA pass. The three audited adapters are genuine
family-law implementations with fail-closed raise-not-log guards; the placeholder predicate
survives only inside the UNMODIFIED runner as the compiler's target. Sandbox isolation proven
byte-identical around all verifier runs. The "0 A-items remaining" claim stands per
WORK_QUEUE_V2's own definitions.

The 5 MINORs are handoff-metadata hygiene (one non-git `dispatch_sha`, tests[]-field gaps in
4/7 handoffs, 1 SELF placeholder, 1 missing `authority_claims`, 4/7 dispatch≠start SHA drift) —
none touches evidence: all 217 output entries resolved and 216 real digests re-hashed MATCH
(217th is the SELF entry).

## 1. Handoff schema audit (checklist 1)

Parsed all 7 wave-3 handoffs (`dispatch/handoff_{CONTRACTS,MEAS-FX,MEAS-NQ,ADAPT-NQ,
ADAPT-FXEB,ADAPT-FXJA,FREEZE-WIRING}.json`), schema `zcode_orch_v3_handoff@1` on all.

- Required fields: present 6/7; **ADAPT-FXJA lacks `authority_claims`** (V-W3-4).
- tests[]: 3/7 fully conformant (CONTRACTS, ADAPT-FXEB, FREEZE-WIRING: command/exit_code/
  verdict∈{PASS,FAIL,NOT_RUN,BLOCKED}/log_digest). Gaps: MEAS-FX (no log_digest ×9), MEAS-NQ
  (free-text `result` instead of verdict-enum ×8, no log_digest), ADAPT-NQ (no verdict, no
  log_digest ×1), ADAPT-FXJA (`status` instead of `verdict` ×15, no log_digest) (V-W3-2).
- outputs[]: **217 entries total; 216 real digests re-hashed from file bytes at HEAD — all
  216 MATCH, 0 mismatches. 1 SELF placeholder** (`ADAPT-NQ` outputs[46] = its own handoff,
  `"SELF-NO-HASH"`) (V-W3-3). Paths: all worktree-root-relative, consistent across 7/7.
- vs wave-2 verify findings:
  - V-2 (tests[] fields, all 7 nonconformant) → **improved, unresolved** (3/7 clean).
  - V-3 (SELF placeholders, 3 handoffs) → **improved, unresolved** (1 handoff).
  - V-4 (round-dir-relative paths) → **resolved** (uniform worktree-root-relative).
  - V-5 (dispatch_sha ≠ actual_start_sha, disclosed) → persists in 4/7 (V-W3-5).
  - V-6 (commit_sha null ×7) → unchanged NOTE (V-W3-7).

## 2. Test-suite re-runs at the audit SHA (checklist 2)

| # | suite | exact summary | exit |
|---|-------|---------------|------|
| a | exec `pytest test_runner_v2 -q` | `42 passed in 3.87s` (first run 3.82s) | 0 |
| b | adapt_nq `pytest . -q` | `65 passed in 0.32s` (first 0.41s) | 0 |
| c | adapt_fx_eb `pytest . -q` | `86 passed in 0.51s` (first 0.62s) | 0 |
| d | adapt_fx_ja `pytest . -q` | `90 passed in 1.22s` (first 1.33s) | 0 |
| e | freeze_wiring `pytest . -q` | `21 passed in 5.17s` (first 5.38s) | 0 |
| f | meas_nq harness `--selfcheck` | `SELFCHECK PASS: 39 checks` | 0 |
| f' | meas_nq harness `--real` refusal | `REFUSED_D9_UNSIGNED: no --d9-ratification supplied` | 20 |

**Any failure at audit SHA: none.** 65+86+90+21 = 262 exactly as claimed; +42 exec +39 checks.
Log sha256s recorded in `verify_findings_wave3.json`. Side effect: the freeze_wiring suite's own
conftest appends 2 lock records per run to `tests/LOCKS_LOG.jsonl`; disclosed and reverted after
each run (V-W3-8).

## 3. Placeholder-substitution audit (checklist 3)

Read in full: `adapt_nq/f1_fomc_era/adapter.py`, `adapt_fx_eb/f2_policy_decision/adapter.py`,
`adapt_fx_ja/jf1_boj_mpm/adapter.py` (+ their `*_common` modules).

- **NQ-F1**: 14:00-ET timed-statement universe; 13:00-CT anchor; `UNTIMED_DAY_LEVEL_ONLY` /
  `EMERGENCY_TIMING` strata; era-correct close via `era_close_ct`; CONT/REV/ALW/SHDW arms;
  PIT `asof` with decision_time = anchor+1 bar; ATR20 warmup gate; same-bar SL-priority.
- **FX-F2**: one family, two legs — 6E anchor fixed minute 780 CT; 6B anchor = the bar whose
  **Europe/London wall time is 12:00 via zoneinfo** (the CT-clock DST bug class is explicitly
  tested); first-5m window; T+60s fill (anchor+6); EMERGENCY/ECB/MPC-change/DOUBLE_EVENT
  strata; BBO NOT_RUN stamped (P5-FXEB-OD8); PB2-conditional labels everywhere.
- **JF1**: BoJ MPM 12:00–15:30 JST declared window (intraday stamps NOT_IN_CORPUS; consuming
  one refuses); decision at window close; **6J UP = yen STRONG quote-direction law in every
  sign**; DRIFT/REV + PLA/ALW/CLK; +1-tick Tokyo entry floor declared PROVISIONAL, never a
  fill claim.

None is a generic bar-up/bar-down evaluator. The generic predicate exists **only** in
`exec/scored_runner_v2.py` (last commit `fe250465`, wave-1 — `git log --follow` confirms no
wave-2/wave-3 commit touches it). `freeze_wiring/wiring/spec_compiler.py` routes
adapter-derived packets: C1 positional encoding, C2 price-grid refusal (exit 42), C3 era cost
refusal (41), **C4 direction ±1 → the runner's two legal arms with every non-signal bar
price-NEUTRAL** so the predicate fires exactly at adapter-declared positions, C5 no-trade
refusal (43), C6 era-label refusal (45); "RUNNER INVARIANCE LAW: this module NEVER modifies
exec/ runner files" — verified. `adapter_binding.PENDING_WIRING = []` (19 adapters wired).

Guards: `P5-` occurrences — adapt_nq 60, adapt_fx_eb 96, adapt_fx_ja 112, freeze_wiring 15.
Eight refusals sample-traced by reading code — **all raise, none log-and-continue**:
P5-NQ1 (`require_synthetic` raise), P5-NQ3 (Variant-B cost raise), P5-FXEB-OD1 (raise),
P5-FXEB-OD5 (RMM Role-B raise), P5-FXEB-OD6 (consumable-cost raise, incl. basis-A DERIVED),
P5-FXJA-D1 (6J raise), P5-FXJA-D5 (6A chain raise), freeze_builder `gate0` per-gate
`GateRefusal` exits 21/22/23/24/25/26/29/30/31.

## 4. Spot-recompute from committed bytes (checklist 4)

- **MEAS-FX m1** (from `FUTURES-DEEPRESEARCH-V2-20261003/audit/a7_6e/a7_6e_recompute.json`
  `rolls_cip.rows`, 27 rows): Pearson latest = **+0.9097001094** (claim +0.9097 ✓; artifact
  committed_check agrees to 1e-15), vintage-as-of = **−0.1068290453** (claim −0.1068 ✓);
  Spearman 0.8999/0.0153 EXACT; sign agreement 27/27 and 26/27 EXACT; **flip = 1/27 at
  2022-12-01** under the artifact's own definition ✓. rho-bar 0.20: latest PASSES, as-of
  FAILS → "vintage-dependent" verified.
- **MEAS-FX m4**, 6E Reading B weekday cell end-to-end: σ=0.030381680286489826 % ×100 =
  3.0381680286489825 bp; MDE = 2.80σ/√1282 = **0.2375887146358199 bp == artifact EXACT**.
  r-claims: 3.6–6.3/0.2375887 = 15.15–26.52 ("15.2–26.5" ✓); 6B: 6.3–11.2/0.3126023 =
  20.15–35.83 ("20.2–35.8" ✓). p95 3.10/4.40 below RT floors present.
- **MEAS-NQ m1**: 3 parquet inputs re-hashed MATCH (e233da66…, b7bd830a…, 30bc1ec3…);
  285/285 structure = 19 blocks × 15 measures, all `MEASUREMENT_IDENTICAL` delta 0.0;
  30-session sample (committed K6GATE per-session parquet 4219 rows vs rederived 4219 rows):
  **median |delta| = 0.0 on all 7 measures**; headline σ 112.2983830675262 → same, Δ 0.0.
- **CONTRACTS**: evidence_hash_index **24/24 re-hashed MATCH** (incl. the disclosed ROOT
  absolute path S6_FRONT_SPREADS.json, hash 3724a633… MATCH). 3 MATCH cells re-verified from
  the cited evidence files: NQ tick 0.25; 6J direction (long_base_sign=1 vs orientation
  recheck PROVEN law); 6A era rows (0.0001 / $10.00 era-1 / 100,000 mult vs
  6a_tick_adjudication.json). **Exactly 4 field-level PENDING** — all `session_mask_spec.rth`
  on 6E/6B/6J/6A; no other PENDING verdict exists (raw-text hits are enum/totals strings).
- **symbol_contracts.json diff at 890fbfa6**: `git diff 890fbfa6^ 890fbfa6` = **exactly
  4 insertions / 3 deletions, 1 file**; touches only NQ `session_mask_spec` (rth, note, new
  `evidence`) + NQ `verification` annotation; no other symbol/number field. New rth value =
  "08:30-16:15 CT (era-A close, through 2015-09-18) / 08:30-16:00 CT (era-B close, from
  2015-09-21 SESSION_SWITCH_DATE)" — matches `nq/CALENDAR_PIT_POLICY_NQ.md` §1 verbatim in
  law content (era-A 16:15 through 2015-09-18; era-B 16:00 from 2015-09-21
  SESSION_SWITCH_DATE; RTH span 08:30 CT → era-correct close; Friday 15:15 handled
  per-session, never asserted).

## 5. Wiring proofs (checklist 5)

`freeze_wiring/tests/` contains and asserts exactly what the lane claims:
- **PIT two-layer**: `test_nq_f1_pit_asof_truncation_byte_identical` (adapter) +
  `test_compiled_pit_truncation_identical_trades_up_to_T` (compiled layer).
- **Cease-guard divergence**: `test_cease_guard_chain_diverges_exactly_at_guard_date` —
  naive keeps the dead contract on 2020-11-20; guarded switches exactly there.
- **Era boundary**: `test_6a_era_boundary_through_runner` — era-1 0.0001/$10.00 vs era-2
  0.00005/$5.00 bound to ENTRY era; costs **57.00 / 30.75** asserted EXACT; era-1 cost model
  on an era-2 arm refused (exit 41, separate test).
- **6J sign**: `test_6j_direction_sign_through_real_adapter_and_runner` — yen-strengthening
  up-move through the real JF1 + compiled runner: DRIFT-UP net > 0, REV-UP net < 0.
- **Runner untouched**: `git log --follow exec/scored_runner_v2.py` → last commit `fe250465`
  (wave-1); HEAD blob == wave-1 committed blob. spec_compiler drives the unmodified runner
  via subprocess on compiled inputs; never writes runner files.

## 6. Sandbox isolation (checklist 6)

- `/Users/hoangminhlong/.my-quantitative-governance`: 37-file sha256 snapshot **byte-identical
  before/after** all verifier suite re-runs.
- `plans/CYCLE_REGISTRY.json`: sha256 `f6a52cb9…` identical before/after; **0 FUTURES-5SYM
  entries** (grep count 0).
- **No GO_RECORDED.json** anywhere under the round dir.
- Verifier side effect (disclosed): two LOCKS_LOG.jsonl appends from the mandated freeze_wiring
  re-runs, reverted to committed bytes after each; tree clean at end.

## 7. Synth v2 consistency (checklist 7)

- **WORK_QUEUE_V2**: 8 rows sampled (#1, #3, #8, #9, #10, #11, #12, #14) — every CLOSED-A /
  PARTIAL-A status matches its cited artifacts: contract_verification 67/1/4 over 72; m1 rho
  pair + 1/27 flip; m2 4/4 fixtures pass with real run NOT_RUN owner-gated; m3 "0 of the 16
  material rolls" + machinery; m1-NQ 285/285 + decomposition; m4 r-claims + p95; harness
  39/39 + exit-20 refusal; 19 adapters with 65/86/90/21.
- **OWNER_DECISION_PACKET_P5_V2**: 262 = 65+86+90+21 ✓ (matches REPORT_VI and the verifier's
  own re-runs); 39 harness checks ✓; recommendation grounds traceable (NQ-B 29 → F1/F2 11/11;
  J-A 29; D3 Variant A; PB2 two-sided evidence) — except the 6B MDE quoted **"4.2bp" vs
  artifact 4.31bp** (mis-rounding; verdict-invariant; V-W3-6; the m4 md table also prints
  "4.313" vs json 4.3094 — typo).
- **REPORT_VI wave-3 section**: 67/1/4; 19 adapters; 262 tests; 39/39; rho pair; per-symbol
  matrix 65/86/86/90/90; refusal exit codes 21/23/26/24→25→21/27/30/31; SHA chain — all
  match handoffs and verifier measurements.
- **"0 mục [A] còn chưa làm"**: accurate per WORK_QUEUE_V2's own definitions. Every CLOSED-A/
  PARTIAL-A row's evidence exists and contains what is claimed; the only open-form [A] row is
  #2, which **is** the wave-3 verify that the same document schedules ("sau commit synth này"),
  and its pointer exists in-tree. Not a MAJOR; nuance recorded (V-W3-10).

## 8. Language / outcome-blind (checklist 8)

- Stale-cost tokens `21.006 / 33.506 / 46.006 / 1.386` in wave-3 dirs appear **only** as
  labeled refusal/ban context ("retired-value ban", "stale-print refusal", "Never-consumable
  list", "stale 21.006-prints never consumable"). Zero use-as-value.
- No positive PnL/profitability/expectancy claims in any wave-3 dir; only negative statements
  ("Zero profitability claims anywhere", "No PnL exists here", "no scored cells").
- All adapter real-data paths refuse unsigned: P5-NQ1 / P5-FXEB-OD1 / P5-FXJA-D1 / P5-FXJA-D5
  (raise), meas_nq REFUSED_D9_UNSIGNED exit 20 (reproduced), freeze_builder GATE-0 dedicated
  exit codes (reproduced by its own suite, refusal demos read in code).

## Per-lane verdicts

| lane | verdict | basis |
|------|---------|-------|
| CONTRACTS | VERIFIED | 3/3 outputs re-hash; 24/24 evidence hashes MATCH; 3 MATCH cells + exactly-4 PENDING re-verified; diff law confirmed by CALENDAR §1 |
| MEAS-FX | VERIFIED_WITH_NOTES | m1/m4 recomputations EXACT; MINORs V-W3-2 (tests[] fields), V-W3-5 (dispatch≠start, undisclosed) |
| MEAS-NQ | VERIFIED_WITH_NOTES | 285/285 + parquet hashes + exit-20 reproduced; MINOR V-W3-2 (`result` field, no log_digest) |
| ADAPT-NQ | VERIFIED_WITH_NOTES | 65/65 re-run; adapter genuine; guards raise; MINORs V-W3-1 (non-git dispatch_sha), V-W3-2, V-W3-3 (SELF) |
| ADAPT-FXEB | VERIFIED | 86/86 re-run; adapter genuine; tests[] fully conformant; 57/57 outputs re-hash |
| ADAPT-FXJA | VERIFIED_WITH_NOTES | 90/90 re-run; adapter genuine; MINORs V-W3-4 (no authority_claims), V-W3-2 (`status` field) |
| FREEZE-WIRING | VERIFIED_WITH_NOTES | 21/21 re-run; runner untouched; 4 named proofs assert the claims; diff 4+/3- exact; MINOR V-W3-5 (dispatch≠start, checkpoint class) |
| synth v2 | VERIFIED_WITH_NOTES | all numbers reconcile; NOTE V-W3-6 (4.2bp quote) |

## Findings register

- **V-W3-1 MINOR** ADAPT-NQ `dispatch_sha` is a 64-hex non-git digest (`git cat-file -t`
  fails), undisclosed; same class as wave-2 V-1 but without the stale-draft evidence defect
  (all 46 real digests MATCH; actual_start_sha valid) — graded MINOR with controller
  normalization recommended at integration.
- **V-W3-2 MINOR** tests[] field gaps in 4/7 handoffs (details §1); 3/7 fully conformant
  (wave-2: 0/7). All cited exit codes reproduced by this auditor.
- **V-W3-3 MINOR** ADAPT-NQ outputs[46] `"SELF-NO-HASH"`; real digest available
  (be61b600c863…). Stamp or drop at integration.
- **V-W3-4 MINOR** ADAPT-FXJA handoff missing `authority_claims`.
- **V-W3-5 MINOR** dispatch_sha ≠ actual_start_sha in 4/7 (1 disclosed); benign checkpoint
  class; record at integration.
- **V-W3-6 NOTE** packet "6B MDE 4.2bp" vs artifact 4.31bp; m4 md "4.313" vs json 4.3094 —
  mis-rounding/typo, verdict-invariant.
- **V-W3-7 NOTE** commit_sha null ×7 (wave-2 V-6 unchanged).
- **V-W3-8 NOTE** verifier LOCKS_LOG appends, disclosed + reverted.
- **V-W3-9 NOTE** CONTRACTS ROOT absolute evidence path — disclosed by the lane, hash MATCH.
- **V-W3-10 NOTE** "0 A-items" claim nuance (row #2 is the verify itself).
- **V-W3-11 NOTE** placeholder predicate reused as compilation target (accurate-but-nuanced
  reading of REPORT_VI's "no placeholder in the production path").
- **V-W3-12 NOTE** NQ rth MISMATCH→correction staged across 8e03e0bd→890fbfa6 as designed.

## Recommended disposition

No lane work required. Controller at integration: normalize the 5 MINORs (stamp git
dispatch_sha for ADAPT-NQ; add verdict/log_digest or accept recorded equivalence; stamp or
drop the ADAPT-NQ SELF entry; add ADAPT-FXJA authority_claims; note dispatch≠start), then the
round stands as PREP-complete within scope. 0 scored cells / 0 PnL / 0 GO / 0 registration
anywhere in wave-3.
