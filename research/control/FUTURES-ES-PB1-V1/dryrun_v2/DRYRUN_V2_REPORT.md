# DRYRUN-V2 REPORT — cycle FUTURES-ES-PB1-V1, gate 4 re-run on the repaired v2 freeze

**QUARANTINED DESCRIPTIVE-ONLY — NOT SCORED — ZERO DENOMINATOR CONSUMPTION —
pre-GO rehearsal per registered plan §4 gate 4. Every number in this report and
in `dryrun_v2/quarantine/**` + `dryrun_v2/dryrun_v2_digest.json` is QUARANTINED
descriptive-only. Budget counters untouched. Zero scored cells. Zero denominator
consumption. NO GO exists or is implied by this lane.**

- Lane: DRYRUN-V2 · Round: FUTURES-ES-PB1-V1 pre-GO repair wave · Generated: 2026-10-05
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
- Measured start HEAD: `436d8cf82eb57a84b0aa4a82c17ee0fd2d0d72d9` (matches dispatch packet; `git status --porcelain` clean at start)
- Authority for the v2 surface: `auth/PREGO_REPAIR_RECORDED.json` (decisions
  HOLIDAY-REPAIR-AUTH + PINS-D-A1-A2-A3, recorded 2026-10-04) → pins D-A1/D-A2/D-A3
  are LAW; `repair/exclude_list_v2.json` + `repair/selection_freeze_v2.json` are the
  operative freeze (append-only supersession; v1 `freezegen/**` + `dryrun/**` are
  HISTORY and were not modified or executed).

## 1. Heavy-lock record

| Check | Verdict | Evidence |
|---|---|---|
| Lane start | **FREE_PROVEN** | `researchctl.py locks inspect`: no registry row, lock file not flocked (`flock_state: free`) |
| Immediately before the panel pass | **FREE_PROVEN** | re-inspected in the same shell invocation that launched the builder; verdict passed to the builder as `lock_record` and embedded in `dryrun_v2_digest.json` |
| During run | no conflict | single-shot; no lock taken; no foreign worker touched; zero `NOT_RUN_RESOURCE_CONFLICT` |

## 2. Machinery provenance (M1: exact v1 machinery, shim-only)

`dryrun_v2/dryrun_builder_v2.py` is a byte-copy of the A7-v2-verified v1 builder
(`dryrun/dryrun_builder.py`) produced by 11 exact-string anchor replacements
(each applied with count==1 enforcement; code-line diff vs v1 shows ONLY):

- **S1** input paths → `repair/selection_freeze_v2.json` + `repair/exclude_list_v2.json` (schema asserts `selection_freeze@2` / `exclude_list@2`; measured-sha keys renamed);
- **S2** output root → `dryrun_v2/` (`quarantine/` + `quarantine_rerun/`);
- **S3** digest head_sha = `436d8cf8…`, lane `DRYRUN-V2`, schema `dryrun_v2_digest@1`, digest filename `dryrun_v2_digest.json`;
- **S4** `GENERATED_UTC` fixed `"2026-10-05"` (determinism law unchanged);
- **S5** post-hoc criteria (d)/(e) checks added in `main()` only — `load_inputs` / `build_sessions` / `derive_state` / `simulate` / `run_pass` logic byte-identical to v1;
- **S6** `main(lock_record)` records the pre-panel-pass lock verdict (argv[1]).

No other divergence exists. Extending the builder's SL-donor filter to the new
exclude class was considered and **NOT done**: it would be a logic divergence
beyond the two permitted shims (see §5 CRITICAL finding).

Input gate (pre-run, aborts pre-write): SPEC sha `445f7499…`, panel sha
`7ae6de2d…`, chain sha `7b6179d2…` all matched pins; freeze↔exclude sha
round-trip matched (`selection_freeze_v2.exclude_list.sha256` ==
sha256(`exclude_list_v2.json`)); Variant-A cost-contract arithmetic asserts and
retired-value ban (1.386/21.006/33.506/46.006) passed.

## 3. Surface actually run

- Eval sessions **2,925** reproduced exactly: F1 375 (2011-06-10..2012-12-31) ·
  **F2 949** (2014-01-17..2017-12-29) · F3 711 (2019-01-18..2021-12-31) ·
  F4 890 (2023-01-18..2026-09-30) — matches `selection_freeze_v2.fold_structure`
  (v1 was 2,926 / F2 950; delta = −1 = 2015-07-02, as frozen by the repair).
- FOMCIN session set 104; C3 FLAT session set 0. Panel: 7,825,657 rows read
  once per pass; 0 dash rows; 1,834,852 RTH rows kept (held chain only).
- 24/24 identities ran at ×1.0 Variant-A declared costs; total trades 13,185
  (v1: 13,188; delta = −3, see §5).

## 4. PASS criteria (gate law; never PnL quality)

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| a | Enumeration: exactly the frozen 24 identities, byte-exact ids vs `repair/selection_freeze_v2.json` embedded table | **PASS** | 24/24 byte-exact, set and order equal, zero extras/missing (digest `pass_criteria.a_enumeration`) |
| b | Cost recompute: 20 sampled trades vs Variant-A pinned table | **PASS** | 20/20 exact; includes 4 NFA-window rows (e.g. S2 window RT 66.98 @ 2017-08-29 vs standard 67.00); gross = dir×(exit−entry)×50 verified; retired values absent (digest `pass_criteria.b_cost_recompute`) |
| c | Determinism: two full passes byte-identical | **PASS** | trades-index sha256 `db19098704df0d446709e2ff26000e9bb1720a468b5c74271082df1d28c08909` identical across passes; all 24 per-identity JSONs byte-identical (`quarantine/` vs `quarantine_rerun/`) |
| d | Surface delta vs v1 quarantine index: ONLY 2015-07-02 effects | **FAIL — CRITICAL finding D-V2-1** | 2015-07-02 removal is exactly as expected (§5.2), but 18 TP/SL identities additionally show exit-level changes caused by the repair's class relabels interacting with the v1 SL-donor filter (§5.3). Per mission law, any difference beyond 2015-07-02 effects = CRITICAL. |
| e | FOMCIN warmup-defect regression (v1 D-F1 class) | **PASS** | 13,185 trades scanned across all 24 identities: zero trades ≤ any fold `warmup_carve_out.last`, zero trades on WARMUP-labelled sessions (digest `pass_criteria.e_warmup_regression`) |

**Gate-4 v2 verdict (machinery output, `dryrun_v2_digest.json`): FAIL — driven
solely by criterion (d); (a)/(b)/(c)/(e) are clean.** This is a rehearsal
machinery-vs-freeze interaction finding, not a PnL result.

## 5. CRITICAL finding D-V2-1 — SL-donor window drift from the repair's class relabels

### 5.1 What changed vs v1 (and what did not)

Expected and confirmed clean:
- Session universe, chain, panel, pins: unchanged (same sha-pinned inputs).
- Eval surface: −1 session exactly (2015-07-02 out of F2). Every identity's
  `n_sessions_in_set` = 2,925 (104 FOMCIN, 0 FLAT).
- q80 signal path: **zero** `q80_threshold` changes on all 13,185 common trades.
- Entry path: entry_price / fill_bar_utc / signal_bar_utc / direction byte-identical
  on all 13,185 common trades.
- Identity membership of trades: identical except the single expected removals (§5.2).

### 5.2 Expected effect of the freeze change — exactly as predicted

Trades dated 2015-07-02 removed: exactly 3, one each in FBES1-ALW-D0-S2,
FBES1-PLA-D0-S2, FBES1-DOSE-D0-S2 (the three identities that traded that session
in v1; no primary arm traded it). 13,188 → 13,185 trades.

### 5.3 Unexpected effect — mechanism, isolated end-to-end

The v2 repair relabelled **35 in-panel sessions** from `COVERAGE_LT60` to
`HOLIDAY_PDF_EQUITY_2011_2015` (priority rank 2 beats rank 4; exclude SET
unchanged — union law). The v1 machinery's SL-donor filter (implementation pin
D-A4, "the short/flagged set of SPEC §4") is label-set-based:
`{HOLIDAY_FACT_EARLYCLOSE, HOLIDAY_UNCERTAIN, COVERAGE_LT60}` — it does not
contain the new class. Therefore those **35 sessions silently re-entered the
trailing-20 SL-donor window** in the v2 run:

- donor-excluded sessions: v1 139 → v2 104; the diff is EXACTLY the 35
  label-changed sessions (2011-01-17 … 2015-12-24); zero sessions newly excluded;
- `sl_distance_pts` changed on **244** eval dates (2011-06-10 .. 2016-01-21 —
  entirely inside the relabel span plus one trailing-20 window reach into F2);
- every exit-changed trade sits on one of those 244 dates (0 violations);
- control isolation: FBES1-ALW-D0-S2 (C2 — no TP/SL mechanics) shows **zero**
  extra changes vs v1-modulo-2015-07-02; only the 18 TP/SL-mechanics identities
  are affected.

### 5.4 Surface-delta table (criterion d)

| Identity | v1 trades | v2 trades | 2015-07-02 removed | exit-level-changed trades | list == v1 − 2015-07-02? |
|---|---|---|---|---|---|
| FBES1-FLAT | 0 | 0 | 0 | 0 | identical |
| FBES1-ALW-D0-S2 | 2,925 | 2,924 | 1 | 0 | **identical** |
| FBES1-PLA-D0-S2 | 2,925 | 2,924 | 1 | 44 | NO (D-V2-1) |
| FBES1-DOSE-D0-S2 | 2,890 | 2,889 | 1 | 43 | NO (D-V2-1) |
| FBES1-PB1-CONT-UP-D0-S1/S2/S3 | 289 ×3 | 289 ×3 | 0 | 7 each | NO (D-V2-1) |
| FBES1-PB1-CONT-UP-D30-S2 | 289 | 289 | 0 | 7 | NO (D-V2-1) |
| FBES1-PB1-CONT-DN-D0-S1/S2/S3 | 264 ×3 | 264 ×3 | 0 | 6 each | NO (D-V2-1) |
| FBES1-PB1-CONT-DN-D30-S2 | 265 | 265 | 0 | 5 | NO (D-V2-1) |
| FBES1-PB1-REV-UP-D0-S1/S2/S3 | 289 ×3 | 289 ×3 | 0 | 6 each | NO (D-V2-1) |
| FBES1-PB1-REV-UP-D30-S2 | 289 | 289 | 0 | 3 | NO (D-V2-1) |
| FBES1-PB1-REV-DN-D0-S1/S2/S3 | 264 ×3 | 264 ×3 | 0 | 4 each | NO (D-V2-1) |
| FBES1-PB1-REV-DN-D30-S2 | 265 | 265 | 0 | 6 | NO (D-V2-1) |
| FBES1-PB1-{CONT,REV}-{UP,DN}-D0-S2-FOMCIN (4) | 9/2/9/2 | 9/2/9/2 | 0 | 0 | **identical** |
| **Total** | **13,188** | **13,185** | **3** | **177** | 6 of 24 clean |

### 5.5 Disposition (no fix applied by this lane)

Whether `HOLIDAY_PDF_EQUITY_2011_2015` belongs in the SPEC §4 "short/flagged"
SL-donor exclusion set is a **spec-level law question**: in v1 the same 35
physical sessions WERE donor-excluded (via their `COVERAGE_LT60` label); the
repair's relabel changed donor eligibility implicitly, with no explicit donor-law
change recorded in `repair/selection_freeze_v2.json`. Resolving it by lane
discretion is forbidden (mission M1: any logic divergence beyond the two shims =
CRITICAL; and the choice changes trade outcomes, so it must be adjudicated
outcome-blind by the owner/controller before any scored run). The v2 run as
executed keeps the v1 machinery verbatim — the faithful exact-machinery re-run —
and criterion (d) exists precisely to surface this interaction.

Required before gate 6: owner adjudication of the SL-donor set on the v2 surface
(extend the short/flagged filter to the new class, or keep the v1 filter verbatim
and accept the v2 donor set), recorded as law; then a dry-run re-run on the
adjudicated machinery with criterion (d) re-checked.

## 6. Zero-denominator statement

No ledger, counter, registry, budget or trial write anywhere in this lane; the
observed denominator was NOT incremented; zero scored cells; all numerics remain
QUARANTINED descriptive-only under `dryrun_v2/quarantine/` +
`dryrun_v2/quarantine_rerun/` with the quarantine header on every artifact.
S1 SEALED_UNTOUCHED; zero network; root read-only; Python = root `.venv`;
v1 `dryrun/` HISTORY untouched. NO GO exists or is implied.

## 7. Files produced by this lane (write boundary honored)

| Path | Role |
|---|---|
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2/dryrun_builder_v2.py` | machinery copy (shim-only; diff-proven) |
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2/quarantine/**` | pass-1 outputs: 24 per-identity JSONs + `summary.json` + `trades_index.json` (index sha `db190987…`) |
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2/quarantine_rerun/**` | pass-2 outputs, byte-identical (criterion c) |
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2/dryrun_v2_digest.json` | machinery digest: criteria a–e, per-identity delta rows, lock record; gate4 verdict FAIL (d) |
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2/DRYRUN_V2_REPORT.md` | this report |
| `research/control/FUTURES-ES-PB1-V1/dispatch/handoff_DRYRUN-V2.json` | structured handoff `zcode_orch_v3_handoff@1` |
