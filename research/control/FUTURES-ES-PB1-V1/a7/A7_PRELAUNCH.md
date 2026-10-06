# A7_PRELAUNCH — FUTURES-ES-PB1-V1 (gate 3, key 1 of 2) — independent fresh-context audit

- Auditor: prelaunch A7 lane (fresh context; audit only — repairs nothing,
  rules nothing on outcomes, does NOT type or endorse any GO).
- Measured at: worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`, HEAD **`a33978b75bb0e4228a8346c44a568166414c2c8f`**
  (single `rev-parse` at start; equals the dispatch SHA; `git status --porcelain` EMPTY at start).
- Program: registered plan `plans/PLAN_futures_es_pb1_v1.md` §4 gate 3 + `PRELAUNCH_A7_SPEC.md`
  (FUTURES-ES-PB1-REGPREP-20261004/synth/), both read fresh at this session.
- R2 non-inheritance: **no prior pass inherited.** Every hash, enumeration,
  arithmetic identity, and set-equality below was recomputed by this lane at
  this SHA in this session; no earlier verifier verdict is relied on as
  evidence (prior verdicts are cited only as history, never as measurement).

## VERDICT: AUTHORIZED_WITH_FINDINGS

- 0 CRITICAL, 0 HIGH unresolved. 1 MEDIUM (sustained, non-blocking,
  adjudicated lawful with zero empirical exposure at this SHA — F-A1),
  4 NOTEs (F-N1..F-N4). All findings disclosed with severity, file, evidence.
- This verdict authorizes NOTHING by itself: it is key 1 of the two-key law.
  Gates 4 (exact-arm dry-run) and 5 (typed owner GO, owner only, never
  delegated) remain outstanding; gate 6 (scored) runs only after both keys.

---

## Check 1 — Freeze integrity (PASS)

### 1a. The 34 pins of `freeze/freeze_pins_v2.json` re-hashed at HEAD a33978b7

Result: **34/34 MATCH, 0 mismatch** (`pin_count=34`, array len 34). Manifest
self-reference law holds (no pin hashes the manifest itself). Manifest own
sha256 `f7e1b580071c09526f13915523a287094ed56a530d2196adc4de0c85907b469a`
equals `selection_freeze.pins_manifest.sha256_at_head`. Representative pins
re-verified byte-exact:

| pin (artifact) | path | sha256 (v2) | result |
|---|---|---|---|
| SPEC_PB1_ES r3 | FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md | 445f7499…6b7073 | MATCH |
| D3_RECORDED (final state) | REGPREP/auth/D3_RECORDED.json | f54610eb…1e355 | MATCH |
| ES_fomc_stats.json | DEEPRESEARCH-V2/analysis/ES_fomc_stats.json | 228fe2d4…18f213 | MATCH |
| es_session_holiday.json | SIX-READINESS/es/es_session_holiday.json | 8885d5de…71391 | MATCH |
| calendar_close_delta.json | SIX-SCORED-GATE-PREP/cal_close/… | 626deccc…df8bb | MATCH |
| es_1m_outright.parquet | DEEPRESEARCH-V2/analysis/ES_cache/… | 7ae6de2d…27b95 | MATCH |
| es_expiry_recheck.json | SIX-READINESS/es/es_expiry_recheck.json | 2b065d5b…34fa94b | MATCH |
| (all other 27 pins) | … | … | MATCH |

### 1b. Gate-2's own declared input hashes re-hashed vs disk

| input | declared sha | measured | result |
|---|---|---|---|
| D3_RECORDED.json (cost_contract.source_sha256) | f54610eb… | f54610eb… | MATCH |
| identity_table_24.json (identity_table.source_sha256) | 6e391980… | 6e391980… | MATCH |
| exclude_list.json (exclude_list.sha256) | bc8a41b6… | bc8a41b6… | MATCH |
| pit_exclude_set.json (laws.source_sha256) | f504c731… | f504c731… | MATCH |
| PLAN_futures_es_pb1_v1.md (registered_plan.sha256, root, read-only) | e29b3d2f… | e29b3d2f… | MATCH |
| session_universe source session_dispersion_es.json | e56c4a53… | e56c4a53… | MATCH |

All 16 artifact shas embedded in `selection_freeze.laws.components[]` also
re-hash MATCH. Embedded identity table == identity_table_24.json
(parsed-equal); embedded cost table == D3_RECORDED interpretation table
(parsed-equal); decision quote `tôi chọn 2.25$` identical in both. Gate-2
output bytes equal the lane handoff output pins (selection_freeze e2b9934a…,
exclude_list bc8a41b6…, REPRODUCE d0960020…, builder 9b94372d…) — the
committed state is exactly what the lane produced.

## Check 2 — Identity enumeration (PASS, byte-exact)

This lane independently expanded the SPEC_PB1_ES §6 patterns (read at this
SHA; header "A-r4 đúng 24"): P-A `FBES1-PB1-{CONT,REV}-{UP,DN}-{D0,D30}-S2`
→ 8; P-B `FBES1-PB1-{CONT,REV}-{UP,DN}-D0-{S1,S3}` → 8; FOMC
`FBES1-PB1-{CONT,REV}-{UP,DN}-D0-S2-FOMCIN` → 4; C1 `FBES1-PLA-D0-S2`,
C2 `FBES1-ALW-D0-S2`, C3 `FBES1-FLAT`, C4 `FBES1-DOSE-D0-S2` → 4. Total 24.

| property | result |
|---|---|
| A7 transcription count | 24 (composition P-A 8 + P-B 8 + FOMC 4 + C1-C4 4) |
| vs freeze/identity_table_24.json | same-set TRUE, same-order TRUE |
| vs selection_freeze embedded identities | same-set TRUE, same-order TRUE |
| duplicates / provisional markers | 0 / none (both artifacts) |
| negative control (8 absent D30×{S1,S3} cells) | 0 leaked into transcription |
| count == registered budget | 24 == 24 (registry `budget.max=24`) |

## Check 3 — Cost arithmetic (PASS)

Recomputed from components with exact decimal arithmetic:

| quantity | recomputation | frozen value | result |
|---|---|---|---|
| fees/side (Variant A) | 0.85+1.38+0.02 | 2.25 | MATCH |
| all-in/side S1/S2/S3 | 2.25+6.25+{12.50,25.00,37.50} | 21.00/33.50/46.00 | MATCH |
| round-trip | all-in ×2 | 42.00/67.00/92.00 | MATCH |
| window fees/side (NFA 0.01, 2014-10-01→2017-12-31) | 0.85+1.38+0.01 | 2.24 | MATCH |
| window all-in/side | 2.24+6.25+slip | 20.99/33.49/45.99 | MATCH |

Cross-artifact: selection_freeze embedded table == D3_RECORDED table ==
registered plan §2 literals (21.00/33.50/46.00; RT 42/67/92; window
20.99/33.49/45.99; exchange 1.38; reg 0.02/0.01; spread 6.25; slippage
12.50/25.00/37.50). Labels present and identical in both artifacts:
`MODELED COST`; `VERIFIED_VS_ACCOUNT = NOT_RUN` (never inferred);
`documentation-A7 clean (AUTHORIZED_WITH_FINDINGS, 0 HIGH/CRITICAL)`.
Forbidden-value use-as-value scan (1.386 / 21.006 / 33.506 / 46.006):
**0 numeric hits** in selection_freeze cost contract, D3 interpretation, or
exclude_list; the only string occurrences are inside the
`forbidden_values_law` retirement text itself (lawful — the law names what
it forbids). Stale SPEC §5 prints remain only in the pinned SPEC, which the
v2 pin role and COST_FREEZE_ERRATUM supersede by reference (see F-N4).

## Check 4 — PIT / exclude coverage (PASS; MEDIUM adjudicated F-A1)

Universe: 4,204 sessions 2010-06-07..2026-10-01 (session_dispersion_es.json,
sha MATCH). Exclusion accounting reconciles exactly: 1,297 array entries =
1,278 in-panel + 19 law-dates-with-no-panel-session; +8 out-of-chain-span =
1,305 total; per-class splits exact (in-panel: FOMC 131, HOLIDAY_FACT 10,
HOLIDAY_UNCERTAIN 60, COVERAGE_LT60 69, WARMUP 1008).

### 4a. FOMC 132-statement day-exclude law

- The **entire** exclude-list FOMC set (131 dates) is set-equal to
  `ES_fomc_stats.json per_event_day_level` dates (stronger than spot-check).
- Deterministic 10-date spot-check (first 3 + seeded middle 4 + last 3,
  seed 7): 10/10 OK (2011-01-26, 2011-03-15, 2011-04-27, 2016-07-27,
  2025-12-10, 2013-10-30, 2017-09-20, 2026-06-17, 2026-07-29, 2026-09-16).
- 132-law arithmetic consistent: 132 statements − 1 (2020-03-15, Sunday,
  no session) = 131 in-data rows; 2020-03-15 correctly absent from the list.

### 4b. Holiday-fact days (5-date spot-check vs cited sources)

| date | cited source | verified in source | result |
|---|---|---|---|
| 2010-07-05 | es_session_holiday.json year_2010_product_level_reference (2010 official PDF, per-day) | yes | OK |
| 2010-09-06 | same | yes | OK |
| 2026-01-19 | 2026 holiday_dates_for_legality + MLK FACT window (calendar_close_delta, capture sha 5184b760…) | yes | OK |
| 2026-04-03 | 2026 legality list + Good-Friday FACT window (capture sha cdba0a65…) | yes | OK |
| 2026-07-03 | 2026 legality list + July-4 FACT window (capture sha 6fbf2904…) | yes | OK |

Full-set equality additionally verified: 2010 legality list (9 dates) ==
exclude-list 2010 HOLIDAY_FACT dates (9); 2026 legality list (11 dates) ==
exclude-list 2026 HOLIDAY_FACT dates (11). `in_panel=false` flags reconcile
(2010-12-24, 2026-01-01 are genuinely absent from the session universe).

### 4c. Coverage rule vs K6 excluded_dates (builder's bit-exact claim re-derived)

- This lane re-derived the rule `rth_core_coverage < 0.60` over the pinned
  session rows: **139 dates — bit-exact vs K6 `excluded_dates` (order
  included)**, confirming the builder's claim [exclude_list tests 15-17].
- All 139 are excluded in exclude_list: 69 labelled COVERAGE_LT60 + 70
  re-labelled by declared priority (10 HOLIDAY_FACT_EARLYCLOSE + 60
  HOLIDAY_UNCERTAIN) — exclude SET is the union either way; 0 priority-law
  violations found.
- Deterministic 20-date re-derivation spot-check (first 5 + seeded middle 10
  + last 5, seed 11): 20/20 OK (coverage < 0.60 in K6 rows AND excluded
  under some class in the list).
- Coverage margin matches exactly: max-below 0.5795 / min-at-or-above 0.9641.

### 4d. D5 pin + BLS vintage + roll/expiry

- D5 pin present in pinned calendar_close_delta.json:
  `D5_bls_cpi_jan2026_pin: NOT_OBTAINED -> OBTAINED (2026-02-13 08:30 ET
  embargo)` with the verbatim BLS schedule-table quote. BLS vintage artifacts
  (BLS_VINTAGE_INVESTIGATION.md, bls_vintage_evidence.json) pin MATCH (in
  the 34).
- E2 roll/expiry law: es_expiry_recheck 68/68 expiry union re-derived,
  66/66 data-side match, Juneteenth exceptions 2026-06 only; quarter-level
  excludes = 0. The artifact's `all_machine_checks_pass=false` is fully
  explained by the disclosed capture-byte legs NOT_RUN_IN_WORKTREE (verdict
  `CONFIRMED_68_68_WITH_RESIDUALS`; carried in selection_freeze
  not_run_register) — see F-N2.

### 4e. ADJUDICATION of the lane's MEDIUM flag (X-A5): 2011-2016 per-day holiday enumeration NOT_RUN

**Verdict: LAWFUL — fail-closed-pending handling is excluded-or-pending,
never silently narrower. Severity MEDIUM SUSTAINED (non-blocking).**

Grounds:
1. Disclosure is present in BOTH gate-2 artifacts (exclude_list
   `.not_run_elements` + selection_freeze `.not_run_register.added_by_this_gate`)
   and in REPRODUCE.md — the freeze nowhere claims 2011-2016 holiday
   completeness; the class is registered as PENDING, not verified-absent.
   This satisfies the mission invariant (missing evidence is NOT_RUN, never
   inferred PASS) and the fail-closed law.
2. No provable exclusion was dropped: in 2011-2016 every partial session is
   excluded anyway — band census (from the pinned session rows): cov=0 → 4/4
   excluded; 0<cov<0.60 → 40/40 excluded; 0.60≤cov<1.0 → 0 sessions exist;
   cov=1.0 → 1,084 survive as full sessions. FOMC days remain excluded via
   FOMC_STATEMENT_DAY. The include set is never silently narrower.
3. NEW A7 evidence — the pending class has **zero empirical exposure in the
   committed panel**: there is not a single 2011-2016 session in the
   [0.60, 1.0) coverage band, so the hypothetical unproven survivor
   population is empty at this SHA. The gap is a law-side enumeration gap,
   not a data-side effect on this freeze.
4. Severity stays MEDIUM (not downgraded, not raised): the enumeration
   itself is genuinely NOT_RUN vs the SPEC §2-E1 fail-closed text; it is
   non-blocking because gates 4-6 consume THIS freeze at THIS SHA where the
   exposure is empty, and the standing obligation (resolve before scored
   execution / before any data refresh that could add 2011-2016
   partial-coverage sessions) is already written into REPRODUCE.md and the
   lane handoff.

## Check 5 — Budget accounting (PASS)

- 24 identities == registry `budget.max` 24; registry `budget.used = 0`
  (nothing scored; dry-run/quarantined passes would not count per plan §6).
- Zero unregistered cells: every `FBES1-*` token in the entire gate-2
  surface (selection_freeze, exclude_list, REPRODUCE.md, builder script)
  belongs to the 24. The single extra token (`FBES1-PB1`) is the verbatim
  SPEC §6 pattern prefix whose brace-expansion lies inside the 24 — not a
  cell. exclude_list contains zero identity tokens by construction.
- Composition law intact: D30×{S1,S3} and all combinations outside the two
  P families are explicitly absent (negative control in Check 2).

## Check 6 — Language scan (PASS)

Scanned the cycle's frozen surface (selection_freeze, exclude_list,
REPRODUCE.md, builder, lane handoff, freeze_pins_v2, identity_table_24,
pit_exclude_set, D3_RECORDED):

- `expectancy` / positive-PnL / `measured cost` / `profitable` / `profit` /
  edge-proven: **0 hits**.
- "scored execution": 2 hits, both conditional gate-dependency language
  ("must be resolved … before scored execution") — reinforcement of
  non-authorization, not a claim of it.
- Typed GO: **absent everywhere** in the frozen surface. The canonical
  phrase `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` appears only in the ROOT
  registry/plan as `REGISTERED_NOT_CONSUMED` — never consumed, never typed
  by any lane. This A7 does not type or endorse it.

## Check 7 — Registry consistency (PASS, read-only)

`/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json` row
FUTURES-ES-PB1-V1 (root read-only; never written):

| field | registry | measured/expected | result |
|---|---|---|---|
| plan | plans/PLAN_futures_es_pb1_v1.md | file exists (read this session) | OK |
| branch | prep/futures-es-reg-20261004 | == audit worktree branch | OK |
| head | e7fc1d8d…8ff361 | == direct parent of gate-2 HEAD a33978b7 (lineage holds; freeze-authority commit per plan) | OK |
| go_phrase | `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` | exact string, no aliases; state REGISTERED_NOT_CONSUMED | OK |
| budget | max 24, used 0 | == 24-identity table; nothing scored | OK |
| s0 / s1 | OPEN / SEALED_UNTOUCHED | consistent with plan §6 | OK |

---

## Findings ledger

| id | severity | file(s) | finding | disposition |
|---|---|---|---|---|
| F-A1 | MEDIUM (sustained, non-blocking) | FUTURES-ES-PB1-V1/freezegen/exclude_list.json `.not_run_elements`; freezegen/selection_freeze.json `.not_run_register.added_by_this_gate`; freezegen/REPRODUCE.md | 2011-2016 per-day holiday enumeration NOT_RUN; HOLIDAY_UNCERTAIN fail-closed-pending for that span | ADJUDICATED LAWFUL (excluded-or-pending, never silently narrower; disclosed in both artifacts; zero empirical exposure at this SHA — 0 sessions in [0.60,1.0) band 2011-2016; 44 partial/zero-coverage 2011-2016 sessions all excluded). Standing obligation already on record: resolve before scored execution and before any data refresh touching 2011-2016. |
| F-N1 | NOTE | freeze/freeze_pins_v2.json `.deltas[0]`; auth/D3_RECORDED.json `._corrections_log` | v1→v2 pin delta on D3_RECORDED (disclosed controller correction wave; decision content byte-verified unchanged by prior verifiers; this lane re-verified decision tables parsed-equal across artifacts) | No action; disclosure chain complete. |
| F-N2 | NOTE | SIX-READINESS/es/es_expiry_recheck.json `verdict`; selection_freeze `.not_run_register` | `all_machine_checks_pass=false` solely from capture-byte spot legs NOT_RUN_IN_WORKTREE (bytes absent); count/data-side legs 68/68 + 66/66 verified true by this lane's read | No action; residual honestly labelled. |
| F-N3 | NOTE | freeze/identity_table_24.json `source_artifact.note` | SPEC section header says "A-r4 đúng 24" while the document is FREEZE-READY r3 | No action; disclosed at extraction; transcription byte-exact regardless. |
| F-N4 | NOTE | FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md §5 | Stale cost prints (1.386/21.006/33.506/46.006) remain in the pinned SPEC text | No action; superseded by COST_FREEZE_ERRATUM per the pin role and retired by the forbidden-values law; this lane verified 0 use-as-value in operative contracts. |

Unresolved HIGH/CRITICAL count: **0**.

## Boundary compliance

- ONE `git rev-parse HEAD` at start (= a33978b7…, recorded); start
  `git status --porcelain` EMPTY; end status re-checked below; no
  commit/stage/push; no other git mutation. Read-only `git show -s --format`
  used twice for lineage (a33978b7 parent = e7fc1d8d).
- Writes confined to `research/control/FUTURES-ES-PB1-V1/a7/**` and
  `research/control/FUTURES-ES-PB1-V1/dispatch/handoff_A7-PRELAUNCH.json`.
- Root repo read-only (registry + plan read, never written). Zero network.
  Zero PnL/signal computation (hashing, JSON equality, set/count arithmetic,
  and coverage-flag comparison only; no price series consumed beyond flag
  fields in committed JSON).
- This artifact is key 1 of 2 only. It is NOT a GO and does not endorse one.

— End A7_PRELAUNCH (FUTURES-ES-PB1-V1).
