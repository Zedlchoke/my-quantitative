# A7 AUDIT R2 — FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (round 2, fresh-context)

- **Lane:** A7-AUDIT-R2 (independent fresh-context auditor; READ-ONLY except `audit/a7_r2/` + `dispatch/handoff_A7_R2.json`; nothing fixed by this lane).
- **Audit date:** 2026-10-02 (UTC). Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep`, branch `prep/futures-behavior-10syms-20261002`.
- **Commits audited:** base `eae8c3d2d8282f89fb3547ed5572ffe1f88fabc7` (reproduction, via a throwaway detached worktree under /tmp, removed after) and HEAD `60bbb48b9690897c43487a7dd2f11a9edc2a469c` (verification; HEAD verified, tree clean before/after apart from `audit/a7_r2/`).
- **Auditor scripts (all fresh, no lane test code imported):** `audit/a7_r2/repro_exec.py` (R1–R4), `repro_r5_walkforward.py` (R5), `repro_r6_handoffs.py` (R6), `adv_d1_margin_roll.py`, `adv_d2_d3_bars_costs.py`, `adv_d4_d5_dbn_wf.py` (adversarial regressions). Raw outputs: `*_BASE.json` / `*_HEAD.json` / `*_OUT.json` alongside.

## Verdict

**PASS for the WAITING_DATABENTO_DATA gate question** ("is everything
implementable-without-vendor-data actually implemented + tested and honestly
typed, with remaining blockers truthfully typed?").

All 6 co-owner findings (R1–R6) were independently REPRODUCED at `eae8c3d2`
with the exact claimed numbers, and all 6 fixes VERIFIED at `60bbb48b` with
the exact claimed behavior numbers. The 4 round-2 deliverables check out
(DBN layouts spot-verified against the official databento/dbn reference;
configs map 50/50 to dossier §5; probes fail-safe without a key; portfolio
laws pinned by tests AND by my own adversarial runs). Full suite **417/417
OK**. No BLOCKER, no MAJOR. **Counts: BLOCKER 0 · MAJOR 0 · MINOR 3 · NOTE 5.**

---

## A. Reproduction of the 6 co-owner findings at eae8c3d2 (all REPRODUCED)

| # | Finding | Observed at eae8c3d2 (my own scripts) | Status |
|---|---|---|---|
| R1 | commission drops quantity; missing-fee zeroing; cost_incomplete blind to slippage | ES qty3 entry fill cost **$2.24/side** (record total **$4.48 roundtrip**) vs required $6.72/$13.44 (`commission_cash_usd(1)` hardcoded at engine.py:254); CL with missing exchange+reg fee charged **$0.00/side** despite known $0.85 broker fee (`cash = 0.0 if comm["missing"]`); ES record `cost_incomplete=False` while slippage is NOT_RUN in the book | **REPRODUCED** |
| R2 | roll old-leg gross missing from journal | es_universe scenario: ledger realized gross **700**, journal record gross **425**, net **416.04** vs ledger final implying **691.04** — exactly 275 (the roll old-leg segment) missing | **REPRODUCED** |
| R3 | roll ran before intraday barriers; old stop rebased onto new contract | exit on **ESM6 (conid 102) at 184.75** — outside the new bar's [198,205] entirely — after 1 roll executed; stop level derived from the OLD bar's low against a gap-rebased level | **REPRODUCED** |
| R4 | gap-stop fill at the barrier outside the bar | long SL95 vs bar O80/H90/L70/C85 → filled **94.75** (above the whole bar); gross −275 | **REPRODUCED** |
| R5 | fold test windows not enforced | calendar 2026-01-01..06-30 (129 sessions), 4 folds, train_frac .7, horizon 2: fold1 planned test [2026-05-08..2026-05-20] but emitted **37 test cells through 2026-06-30** — **29 sessions past test_end**, **31 label-immature cells kept**, and every fold pair overlaps (fold1∩fold2 = 28 emitted sessions; the "38 cells" co-owner count = the window from test_start incl. the embargo-dropped May-8 cell — same defect under either convention) | **REPRODUCED** |
| R6 | 14 non-canonical handoffs | my schema checker (keys per `plugins/quant-research-orchestrator/skills/structured-handoff/SKILL.md`) on the 14 committed `dispatch/handoff_*.json` at eae8c3d2: **14/14 non-canonical**, each missing 15 of the 17 required keys (only schema/task_id/summary/outputs-ish present; no dispatch_sha/actual_start_sha/tests-with-verdicts/tree_status/…) | **REPRODUCED** |

## B. Fix verification at 60bbb48b (all VERIFIED)

| # | Claimed fixed behavior | Observed at HEAD (my own scripts) | Status |
|---|---|---|---|
| R1 | qty3 $13.44 rt; incomplete-cost law; refusal | entry/exit cost **$6.72/side, $13.44 roundtrip** for qty3; CL known $0.85/side charged with `cost_incomplete=True` + missing `[exchange_plus_regulatory, slippage]`; ES-slippage-NOT_RUN record `cost_incomplete=True`, missing-component status = **NULL value + provenance NOT_RUN + expected source class** (never 0, never MEASURED); `allow_incomplete_costs=False` on an incomplete book → **PolicyError at construction** (refusal message names the components) | **VERIFIED** |
| R2 | journal=ledger 700/691.04 + independent reconciliation | journal gross **700 = ledger**, net **691.04**; `gross_segments = [roll_leg_old_contract 275 (ESH6, 2026-02-27), exit 425 (ESM6, 2026-03-04)]`; `independent_reconciliation`: reconciled=true, journal_gross 700, journal_costs 8.96 (4 legs × $2.24), cash_final identity exact, **per_bar_checks=129** (every replayed session), ledger_cost_outflow 8.96 — roll gap borne once, never double-counted | **VERIFIED** |
| R3 | barrier on OLD contract first; stopped ⇒ no roll | exit **SL on ESH6 (conid 101) at 94.75** — inside the old bar [90,115] — with **0 rolls**; single MAE/MFE segment on conid 101 with mae −512.5/mfe +737.5 (old-bar extrema only; no ~−5600 cross-frame number) | **VERIFIED** |
| R4 | gap-stop open-adverse fill | long SL95 into O80/H90/L70/C85 → **79.75** (= open 80 − 0.25 adverse shift), inside the bar; same-bar TP+SL still **AMBIGUOUS_ORDER** with net=None and gap-aware scenario bounds (preserved from base, now with gap-aware bounds) | **VERIFIED** |
| R5 | fold1 exactly 7 cells + LABEL_CENSORED + disjoint + producer-prefix PIT | embargo-0 co-owner case: fold1 emits **exactly 7 cells [2026-05-08..2026-05-18]**, drops = 1 PURGE + **2 LABEL_CENSORED** (May 19/20) + **29 POST_TEST_WINDOW**; all four folds' emitted sets **pairwise disjoint** (my run also clean with embargo=1: 6 cells, 0 outside, 0 immature). Producer-prefix PIT tests exist with counter-lookahead teeth (`test_wf_pit_prefix.py`: leaky bar/roll-table/metadata/selection readers each detected; roll table REBUILT from truncated bars, not static) | **VERIFIED** |
| R6 | 14 canonical replacements + verbatim archive + validator + honest shas | 14/14 replacements carry the full schema (my checker: 2 fully canonical, 12 conforming with honest `NOT_RUN`/null-digest entries for archived tests — key present, value null, never promoted to PASS); **archive_attempt1 originals byte-identical to eae8c3d2 blobs (my own `git show`+`cmp`: 14/14 IDENTICAL)**; `cycle_id=UNREGISTERED_PREP` honest, dispatch_sha=actual_start_sha=eae8c3d2 (real commit) in all; **no fabricated cycle/sha**; MCP-validator NOT_RUN disclosed (HANDOFF-RESEARCH known_limitations + validator banner). Lane validator re-run by me at HEAD: exits 1 honestly with findings — see MINOR m2 | **VERIFIED** (with m2 residuals) |

## C. Round-2 work audit

### C1. DBN-ADAPTER — VERIFIED
- **Layouts vs official reference** (github.com/databento/dbn `main`, `rust/dbn/src/record.rs` + `compat.rs`, fetched 2026-10-02 by this auditor): **OhlcvMsg 56 B** (hd + open/high/low/close i64 + volume u64), **BboMsg 80 B** (price, size, _reserved1, side, flags, _reserved2, ts_recv, _reserved3[4], sequence, BidAskPair — identical order incl. reserved bytes and encode_orders), **StatMsg 80 B** (ts_recv, ts_ref, price, quantity, sequence, ts_in_delta, stat_type, channel_id, update_action, stat_flags, _reserved[18]), **InstrumentDefMsg 520 B** (all 70 fields in exact declaration order; 16+120+76+12+263+16+17 = 520 exact; `_mk` self-asserts layout==size). Official v3 constants `SYMBOL_CSTR_LEN=71`, `ASSET_CSTR_LEN=11` (compat.rs) match spec.py. My independent byte recount confirms every size.
- **Fail-closed unknown rtype:** `UnknownRecordTypeError` raised at decode and pack; verified behaviorally in D4 below; 3 lane test sites.
- **Synthetic-only fixtures:** `futbt/dbn/fixtures.py` has no file/env/network access; docstring declares all-fabricated arithmetic patterns; ingest takes caller-supplied paths only. 144 DBN tests run offline OK (1.66 s).

### C2. STRATEGY-CONFIGS — VERIFIED (one stale pin, m1)
- 10 symbol configs, **50 hypotheses (5×10)**; every config's hypothesis ID set **matches its dossier §5 header set 1:1** (checked all 10 programmatically); ES-H1 deep-read maps mechanism/T-5/Juneteenth/invalidation/counter-hypothesis verbatim; parameters the dossiers leave unset appear as **PARAM-GAP registers** (57 total), none invented.
- Pilot: `total_declared_trials = 79` = 72 primary (2 sym × 1 rule × 2 roll × 3 stress × 2 slippage × 3 delay) + 5 baselines + 2 ablations; budget NOT_RUN; multiplicity families disclosed; master seed 20261002 with stable enumeration order.
- Coverage cross-check: 16 RUNNABLE_NOW / 30 WAIT_DATA / 4 BLOCKED_NONDATA — matches claim; "no hypothesis has been run" confirmed (no run artifacts anywhere).
- **m1:** `analysis/strategy_lane/validate_configs.py` **FAILS (exit 1) at HEAD**: `configs/symbols/6A.yaml` pins `dossier_sha256 4628eaea…` but the committed `dossiers/6A_DOSSIER.md` (with the Lead's HG-not-in-corpus erratum) hashes `85956ee6…`. The "validator exit 0" claim held only pre-erratum. One-line re-pin fixes it. (Process note: running the validator rewrites `validate_configs_report.json` as a side effect; I restored that file via git checkout.)

### C3. REQUEST-PACKET — VERIFIED
- `request_manifest.json`: **15 lines** (PILOT-01..06, EXP-01..09), each with `hypothesis_ids`, `schemas`, `date_spec`, `need`, `phase`, `engine_or_qa_note`; EXP-06..08 honestly NOT_ENUMERATED.
- Probes run by me with no key: `--dry-run` → exit 0, "**DRY-RUN COMPLETE: 0 network calls**" (46 billable-size + 1 unit-price request enumerated); real run without key → **exit 2 FATAL before any network code path** (key check precedes urlopen; key from env only, never argv; output redacted).
- No price numbers presented as real: grep for `$`/USD figures in manifest + packet returns only NOT_RUN_NO_CALL context ("every price NOT_RUN_NO_CALL until list_unit_prices actually returns it").

### C4. MULTIASSET-WIRING — VERIFIED
- **62 tests** (risk_caps 20 + wiring 21 + composition 21); laws read in source: veto-never-clips (`test_per_sleeve_cap_blocks_without_clipping` preserves requested qty; `test_caps_never_touch_filled_quantities` asserts no journal qty ever differs from requested; concurrency blocks new sleeve with `held_unchanged`), leave-one-leg **full-path** harness with genuine non-additivity, frozen-marks no-lookahead (`test_future_view_trap_raises_inside_portfolio`, `test_future_mutation_invariance_portfolio_wide`, `test_prefix_determinism_full_vs_cutoff`, `test_gate_audit_never_runs_ahead_of_the_calendar`).
- Claimed EXEC-FIX defect fix (censored-with-roll broke journal-cash reconciliation) has the pinning test: `test_portfolio_composition.py::test_single_symbol_censored_after_executed_roll` asserts right_censored + 1 executed roll + `independent_reconciliation.journal_gross_usd == ledger_realize_usd`.
- Independently re-proven by my adversarial D1 below (margin veto + same-session roll).

## D. Adversarial regressions (new, mine; scripts in audit/a7_r2/) — 5/5 PASS

1. **D1 margin-cap veto + same-session roll** (`adv_d1_margin_roll.py`, exit 0): 3-symbol portfolio, ES fill attempted at the 2026-02-27 open — the same session CL rolls — with equity 21,049.10. ES blocked `BLOCKED_MARGIN_INITIAL`, **qty 2 preserved, zero entry fills**; veto math exact: per-symbol 3,080.00 (6J) / 8,823.20 (CL) / 57,263.30 (ES×2) = MARGINS.initial×qty, required **69,166.50**, shortfall **48,117.40 = required − equity**, breach⇔required>equity; **CL roll executed on schedule 2026-02-27** with journal gross = ledger (−3,940.00) — another symbol's block disturbs nothing; no qty clipped anywhere.
2. **D2 zero-range bar H==L** (`adv_d2_d3_bars_costs.py`): long TP150/SL50 and short TP50/SL150 facing O=H=L=C=100 (real volume) — **no crash, no barrier fill invented**; both exit TIME on a later bar at a real price; a fully zero-range universe still resolves TIME legally.
3. **D3 missing exchange fee in a 2-symbol portfolio** (same script): CL fee NOT_RUN → `cost_incomplete=True`, missing `[exchange_plus_regulatory, slippage]`, component status **value NULL (not 0) + provenance NOT_RUN + expected class PUBLISHED**, known $0.85/side still charged; ES with declared slippage stamps `cost_incomplete=False`; per-symbol cash identity (final = initial + gross − costs) exact on both.
4. **D4 unknown rtype mid-stream** (`adv_d4_d5_dbn_wf.py`): legal DBN v3 file with valid–unknown(0x0a MBP-10)–valid records → **`UnknownRecordTypeError` reporting rtype 10**, nothing silently skipped; the clean control file decodes 2 records.
5. **D5 walkforward horizon 5 / 3 folds / 60 sessions** (same script): emitted test sets **pairwise disjoint**, **0 label-immature emitted, 0 outside test_end**; honest heavy censoring (LABEL_CENSORED 5/fold, POST_TEST_WINDOW audited, fold3 emits 0 cells — window too short for horizon 5; no suppression).

## E. Full suite + hygiene

- **`python -m unittest discover -s tests -t .` → Ran 417 tests in 4.272s — OK** (claim: 417 OK; exact). Count reconciles: 147 base + 35 EXEC-FIX + 29 WF-PIT-FIX + 62 portfolio + 144 DBN = 417.
- **No real-data strategy evaluation artifacts:** greps for sharpe/sortino/win-rate/profit-factor/CAGR/drawdown/PnL across `analysis/`, `configs/`, `data/`, dossiers and control docs hit only disclaimers, laws and synthetic-test references; `analysis/strategy_lane/` + `research_lane/` contain only configs/coverage/manifest tooling, no run outputs.
- **No credentials:** key-shaped greps hit only env-only-key documentation and disclaimers; probes verified fail-safe without a key (C3).
- **Git status:** HEAD 60bbb48b; only expected untracked `audit/a7_r2/` (one side-effect write by the configs validator was restored; disclosed above).
- **Locks:** `researchctl.py locks inspect` → **FREE_PROVEN** (no registry row, flock free). No heavy jobs run; no subagents; no push/merge/ledger writes; raw data untouched.

## Findings (new, this round)

### BLOCKER — none. ### MAJOR — none.

### MINOR
**m1 — stale dossier-hash pin breaks the configs validator at HEAD.**
`configs/symbols/6A.yaml` `dossier_sha256: 4628eaea…` ≠ committed
`dossiers/6A_DOSSIER.md` `85956ee6…` (the Lead's post-config HG erratum landed
after STRATEGY-CONFIGS pinned the hash). `validate_configs.py` at HEAD: FAIL,
exit 1 ("dossier_sha256 mismatch for 6A"). The failure mode is honest (the
validator caught real drift) and the fix is a one-line re-pin, but the
deliverable's own gate is red at the audited commit. (Same root cause as the
EXEC-FIX/HANDOFF-RESEARCH output-digest drift in m2.)

**m2 — handoff canonicity/drift residuals at HEAD (validator re-run by me:
14/21 PASS, 7 files with findings, exit 1).** (a) 5 round-2 handoffs
(DBN-ADAPTER, MULTIASSET-WIRING, REQUEST-PACKET, STRATEGY-CONFIGS, WF-PIT-FIX)
leave `commit_sha` null WITHOUT the explicit known_limitations disclosure the
round rule requires (EXEC-FIX and HANDOFF-RESEARCH disclose properly);
(b) recorded output sha256s drifted where later lanes/Lead edited shared
files (EXEC-FIX: engine.py/accounting.py/README; HANDOFF-RESEARCH:
INTEGRATION_SUMMARY.md/6A_DOSSIER.md) — digests are handoff-time snapshots,
correct at publish, stale at HEAD, and the validator flags them (control-
state-drift by design, but the Lead should re-anchor digests at integration);
(c) `handoff_DBN-ADAPTER.json` tests[1] claims PASS with **no `log_digest`
key at all**; (d) EXEC-FIX and WF-PIT-FIX `workers` is a dict/string, not an
integer ≥ 0. None fabricates evidence; all are canonicity/discipline gaps to
sweep when the Lead rewrites commit_shas.

**m3 — REQUEST-PACKET handoff types expected refusals as PASS.** tests[5]/[6]
record `verdict: PASS` with `exit_code: 2` (the no-key real-run refusals).
The runs themselves are exactly right (fail-safe exit 2, no network) — but a
PASS verdict on a nonzero exit is internally inconsistent typing; record
them as expected-refusal with the exit code in the note, or a distinct
verdict.

### NOTE
**n1 —** DBN record layouts independently spot-verified against the official
databento/dbn reference on github (record.rs/compat.rs @main, fetched
2026-10-02): sizes 56/80/80/520 and field order match exactly for
OhlcvMsg/BboMsg/StatMsg/InstrumentDefMsg, including reserved bytes and
encode_orders; official v3 string constants (71/11) match spec.py.

**n2 —** Archive integrity proven independently: all 14 archived attempt-1
handoffs byte-identical to the eae8c3d2 committed blobs (`git show` + `cmp`);
`ORIGINAL_SHA256SUMS.txt` present. MCP validator NOT_RUN is disclosed in the
right places (not silently claimed).

**n3 —** R5 counting conventions reconcile: the co-owner "38 cells" counts
the fold1 test window from test_start (incl. the embargo-dropped 2026-05-08
cell); my emitted-set measurement is 37 cells / 29 excess / 28-session fold1∩
fold2 overlap — identical defect, consistent under either convention.

**n4 —** The fix-round behavior numbers claimed in lane handoffs reproduce
exactly under my own independent fixtures (all of §B) — no evidence of
test-to-claim coupling or overfitting to the co-owner examples.

**n5 —** Probe scripts are the correct security posture for the vendor round:
env-only key, redacted output, dry-run default evidence, exit 2 without key,
phase-0 free endpoints only, no get_range/batch/live anywhere in the code.

## Gate answer

**WAITING_DATABENTO_DATA: PASS.** Everything implementable without vendor
data is implemented and tested (417/417; my 5 adversarial regressions green;
6/6 findings fixed with exact numbers), typing is honest everywhere I
probed (NOT_RUN/NULL/PARAM-GAP/BLOCKED_* used, never fabricated values), and
the remaining blockers are truthfully typed: Databento data depth (pilot
+ expansion manifest 15 lines, probes prepared NOT_RUN), declared slippage
everywhere, exchange fees 9/10 symbols, registration for any scored run,
consensus-archive license (owner decision), HG not in corpus (erratum). The
3 MINORs are hygiene (re-pin 6A hash; sweep handoff canonicity at Lead
integration; retype 2 probe verdicts) and do not gate the packet.

## Artifacts
- `audit/a7_r2/repro_exec.py` + `repro_exec_BASE.json` + `repro_exec_HEAD.json`
- `audit/a7_r2/repro_r5_walkforward.py` + `repro_r5_BASE.json` + `repro_r5_HEAD.json`
- `audit/a7_r2/repro_r6_handoffs.py` + `repro_r6_BASE.json` + `repro_r6_CURRENT.json`
- `audit/a7_r2/adv_d1_margin_roll.py` + `_OUT.json`; `adv_d2_d3_bars_costs.py` + `_OUT.json`; `adv_d4_d5_dbn_wf.py` + `_OUT.json`
- `audit/A7_AUDIT_R2.md` (this report); `dispatch/handoff_A7_R2.json`
