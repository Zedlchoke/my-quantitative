# DRYRUN-V2-1 REPORT — cycle FUTURES-ES-PB1-V1, gate 4 re-run after the D-V2-1 defect correction

**QUARANTINED DESCRIPTIVE-ONLY — NOT SCORED — ZERO DENOMINATOR CONSUMPTION —
pre-GO rehearsal per registered plan §4 gate 4. Every number in this report and
in `dryrun_v2_1/quarantine/**` + `dryrun_v2_1/dryrun_v2_1_digest.json` +
`dryrun_v2_1/trade_level_delta_vs_v1.json` is QUARANTINED descriptive-only.
Budget counters untouched. Zero scored cells. Zero denominator consumption.
NO GO exists or is implied by this lane.**

- Lane: DRYRUN-V2-1 · Round: FUTURES-ES-PB1-V1 gate-4 re-run after defect
  correction · Generated: 2026-10-05
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
- Measured start HEAD: `148a7bf52b4e4351ae156e4f704a7e7e22c87f0a` (matches
  dispatch packet; `git status --porcelain` clean at start)
- Operative freeze (unchanged from DRYRUN-V2): `auth/PREGO_REPAIR_RECORDED.json`
  → `repair/exclude_list_v2.json` + `repair/selection_freeze_v2.json`
  (append-only supersession). v1 `freezegen/**` + `dryrun/**` and v2
  `dryrun_v2/**` are HISTORY — read-only baselines, not modified, not executed.

## 1. Heavy-lock record

| Check | Verdict | Evidence |
|---|---|---|
| Lane start | **FREE_PROVEN** | `researchctl.py locks inspect`: no registry row, lock file not flocked (`flock_state: free`) |
| Immediately before the panel pass | **FREE_PROVEN** | re-inspected in the same shell invocation that launched the builder; verdict passed to the builder as `lock_record` and embedded in `dryrun_v2_1_digest.json` |
| During run | no conflict | single-shot; no lock taken; no foreign worker touched; zero `NOT_RUN_RESOURCE_CONFLICT` |

## 2. D-V2-1 correction statement (the law this lane implements)

DRYRUN-V2 (dryrun_v2/DRYRUN_V2_REPORT.md §5) caught defect **D-V2-1**: the v1
machinery's SL-donor filter (pin D-A4, the SPEC §4 "short/flagged" set) is
LABEL-based `{HOLIDAY_FACT_EARLYCLOSE, HOLIDAY_UNCERTAIN, COVERAGE_LT60}`; the
repair's 35 `COVERAGE_LT60 → HOLIDAY_PDF_EQUITY_2011_2015` relabels (exclude
SET unchanged) therefore silently re-admitted those sessions as donors
(139 → 104 donor-excluded), changing `sl_distance_pts` on 244 eval dates and
177 exits.

**Correction law (conservative-intent carryover, within the owner's repair
authorization for the conservative holiday repair): the SL-donor EXCLUSION
session set must be IDENTICAL to v1's 139 sessions — the relabel is evidentiary
metadata only and must not alter donor statistics.** This is a defect
correction restoring frozen v1 behavior under relabeling, NOT a new design
choice; admitting PDF sessions as donors would be a new amendment requiring its
own owner adjudication. Concretely verified from the v1 label column
(`freezegen/exclude_list.json`, read-only):

- donor-excluded under v1 labels: **139** (== v1); under v2 labels: 104;
- the diff is EXACTLY the 35 relabeled sessions (2011-01-17 … 2015-12-24,
  v1 `COVERAGE_LT60` → v2 `HOLIDAY_PDF_EQUITY_2011_2015`); zero sessions newly
  excluded; the v2-only class therefore adds NOTHING to the donor law;
- **2015-07-02 has NO v1 exclusion label at all** → donor-ADMITTED in v1 and
  kept donor-admitted here (the repair changes EVAL membership only, not donor
  law); it is the one `HOLIDAY_PDF_EQUITY` session not covered by the v1 label
  rule.

## 3. Machinery provenance (M1: corrected builder v2.1)

`dryrun_v2_1/dryrun_builder_v2_1.py` is an exact copy of
`dryrun_v2/dryrun_builder_v2.py` (the shim-only v2 rehearsal machinery) with
EXACTLY ONE additional logic change, applied via exact-string replacement with
count==1 enforcement. **The one-line diff (effective logic):**

```diff
-    short_flagged = classes and {
-        d for d, cs in classes.items()
-        if cs & {"HOLIDAY_FACT_EARLYCLOSE", "HOLIDAY_UNCERTAIN", "COVERAGE_LT60"}
-    }
+    # (C1) donor exclusion set = v1's exact 139-session set, evaluated on the
+    # V1 class labels (freezegen/exclude_list.json, read-only; the 3-class
+    # filter unchanged); + mandated asserts: donor-excluded count == 139 == v1;
+    # 2015-07-02 donor-admitted; XOR vs the v2-label set == exactly the 35
+    # relabeled sessions (v1 COVERAGE_LT60 -> v2 HOLIDAY_PDF_EQUITY_2011_2015).
+    excl_v1 = json.load(open(WT + "/.../freezegen/exclude_list.json"))
+    classes_v1 = {in-panel session -> v1 reason_class set}   # same fold as v1
+    short_flagged = classes_v1 and {d for d, cs in classes_v1.items() if cs & {…3 classes…}}
```

Everything downstream is untouched: `build_sessions` / `derive_state` /
`simulate` / `run_pass` and the criteria checks are byte-identical to the v2
builder (line-diff hunks: header docstring, determinism comment date, output
root `dryrun_v2_1/`, the C1 block, digest metadata/lane/head-sha/filename,
donor-correction evidence plumbing, D-V2-1-FIX finding — 9 hunks, of which
only the C1 block touches logic). Remaining lane shims inherited from v2:
S1 v2 freeze/exclude inputs (schema @2), S4 `GENERATED_UTC` fixed
`"2026-10-05"`, S5 post-hoc criteria (d)/(e), S6 `main(lock_record)`.

Input gate (pre-run, aborts pre-write): SPEC sha `445f7499…`, panel sha
`7ae6de2d…`, chain sha `7b6179d2…` all matched pins;
`selection_freeze_v2.exclude_list.sha256` == sha256(`exclude_list_v2.json`);
Variant-A cost-contract arithmetic asserts and retired-value ban
(1.386/21.006/33.506/46.006) passed.

## 4. Surface actually run

- Eval sessions **2,925** reproduced exactly (builder assert vs
  `selection_freeze_v2.fold_structure`): F1 375 · **F2 949** (2014-01-17…
  2017-12-29) · F3 711 · F4 890 — the v2 eval surface; `n_sessions_in_set` =
  2,925 for every trading identity, FOMCIN set 104, C3 FLAT 0.
- Panel: 7,825,657 rows read once per pass; 0 dash rows; 1,834,852 RTH rows
  kept (held chain only).
- 24/24 identities ran at ×1.0 Variant-A declared costs; total trades
  **13,185** (= v1's 13,188 − exactly the 3 trades dated 2015-07-02).

## 5. PASS criteria (gate law; never PnL quality)

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| a | Enumeration: exactly the frozen 24 identities, byte-exact ids vs `repair/selection_freeze_v2.json` embedded table | **PASS** | 24/24 byte-exact, set and order equal, zero extras/missing (digest `pass_criteria.a_enumeration`) |
| b | Cost recompute: 20 sampled trades vs Variant-A pinned table | **PASS** | 20/20 exact, incl. 4 NFA-window rows (fees 2.24 vs 2.25); gross = dir×(exit−entry)×50 verified; retired values absent (digest `pass_criteria.b_cost_recompute`) |
| c | Determinism: two full passes byte-identical | **PASS** | trades-index sha256 `eaae8b6b13453db7ef0666bb1ac15a5111898ea01019ebbd0c974a505e6df4a8` identical across passes; all 24 per-identity JSONs byte-identical (`quarantine/` vs `quarantine_rerun/`, independently re-verified) |
| d | Surface delta vs v1 quarantine: ONLY the 2015-07-02 removal (3 trades); donor-set restored ⇒ zero other changes | **PASS** | index check: every identity's list == v1 minus its 2015-07-02 rows (3 removed: ALW/PLA/DOSE D0-S2); DEEP trade-level check (`trade_level_delta_vs_v1.json`): all **13,185** common trades value-identical to v1 canonical trade dicts, **0** `sl_distance_pts` differences — SL distances byte-identical to v1 |
| e | FOMCIN warmup-defect regression (v1 D-F1 class) | **PASS** | 13,185 trades scanned across all 24 identities: zero trades ≤ any fold `warmup_carve_out.last`, zero trades on WARMUP-labelled sessions (digest `pass_criteria.e_warmup_regression`) |

**Gate-4 v2.1 verdict (machinery output, `dryrun_v2_1_digest.json`): PASS —
all five criteria clean.** The D-V2-1 surface contamination is gone: with the
donor set restored to v1's 139 sessions, the ONLY surface difference vs v1 is
exactly the frozen eval-surface change (session 2015-07-02 removed from F2 →
its 3 trades gone). This is a rehearsal machinery-vs-freeze reconciliation, not
a PnL result.

## 6. Zero-denominator statement

No ledger, counter, registry, budget or trial write anywhere in this lane; the
observed denominator was NOT incremented; zero scored cells; all numerics
remain QUARANTINED descriptive-only under `dryrun_v2_1/quarantine/` +
`dryrun_v2_1/quarantine_rerun/` with the quarantine header on every artifact.
S1 SEALED_UNTOUCHED; zero network; root read-only; Python = root `.venv`;
v1 `dryrun/` + `freezegen/` and v2 `dryrun_v2/` HISTORY untouched (the v1 label
column was READ, never written). NO GO exists or is implied.

## 7. Files produced by this lane (write boundary honored)

| Path | Role |
|---|---|
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/dryrun_builder_v2_1.py` | corrected machinery copy (one C1 logic change; diff-proven, count==1 anchors) |
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/quarantine/**` | pass-1 outputs: 24 per-identity JSONs + `summary.json` + `trades_index.json` (index sha `eaae8b6b…`) |
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/quarantine_rerun/**` | pass-2 outputs, byte-identical (criterion c) |
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/trade_level_delta_vs_v1.json` | deep M2(d) trade-level delta vs v1 quarantine (13,185 common trades identical; 0 SL-distance diffs; verdict PASS) |
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/verify_trade_level_delta_vs_v1.py` | the deep-check script (post-hoc, read-only on v1/v2 artifacts) |
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/dryrun_v2_1_digest.json` | machinery digest: criteria a–e, donor_correction evidence, lock record; gate4 verdict PASS |
| `research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/DRYRUN_V2_1_REPORT.md` | this report |
| `research/control/FUTURES-ES-PB1-V1/dispatch/handoff_DRYRUN-V2-1.json` | structured handoff `zcode_orch_v3_handoff@1` |
