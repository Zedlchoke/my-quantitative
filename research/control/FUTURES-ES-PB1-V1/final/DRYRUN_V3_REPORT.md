# DRYRUN-V3 REPORT — cycle FUTURES-ES-PB1-V1, lane FREEZE-V3-MACHINERY

**QUARANTINED DESCRIPTIVE-ONLY — NOT SCORED — ZERO DENOMINATOR CONSUMPTION —
pre-GO rehearsal per registered plan §4 gate 4. Every number in this report
and in `final/quarantine/**` + `final/quarantine_rerun/**` +
`final/dryrun_v3_digest.json` is QUARANTINED descriptive-only. Budget counters
untouched. Zero scored cells. Zero denominator consumption. NO GO exists or is
implied by this lane.**

- Lane: FREEZE-V3-MACHINERY · Round: FUTURES-ES-PB1-V1 combined corrected
  final state — freeze v3 (2016/2020/2021 fail-closed additions) + machinery
  implementing the SPEC §4 FLAG-BASED donor law (correcting FAIL record
  D-V2-2) + gate-4 dry-run (third adjudication) on that state · Generated:
  2026-10-05
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
- Measured start HEAD: `a855dab809be73c4b6eef60ab8c41566532febcd` (matches the
  dispatch packet; single bare `rev-parse` at lane start; `git status
  --porcelain` clean at start)
- Operative freeze (NEW, this lane): `final/selection_freeze_v3.json` →
  `final/exclude_list_v3.json` (append-only supersession of
  `repair/selection_freeze_v2.json` + `repair/exclude_list_v2.json`, which are
  HISTORY — unchanged, read-only). `freezegen/**`, `dryrun/**`, `dryrun_v2/**`,
  `dryrun_v2_1/**` are HISTORY — not modified, not executed (the v2.1
  quarantine is READ as the criterion-(d) baseline; the v1 label column is
  READ as the carryover baseline).

## 1. Heavy-lock record

| Check | Verdict | Evidence |
|---|---|---|
| Lane start | **FREE_PROVEN** | `researchctl.py locks inspect`: no registry row, lock file not flocked (`flock_state: free`) |
| Immediately before each panel pass | **FREE_PROVEN** (×3 launches, §8) | re-inspected in the same shell invocation that launched the builder; verdict passed to the builder as `lock_record` and embedded in `dryrun_v3_digest.json` (`lock_record.pre_panel_pass = "FREE_PROVEN \| free"`) |
| During runs | no conflict | single-shot per launch; no lock taken; no foreign worker touched; zero `NOT_RUN_RESOURCE_CONFLICT` |

## 2. D-V2-2 correction statement (the law this lane implements)

`repair/FAIL_DONOR_VIOLATION.md` (FAIL record **D-V2-2**, append-only) found
that both prior donor laws violate the frozen SPEC §4
[ERRATUM A7-SPEC-M5] — "SL = 1.0 × median của 20 range RTH session liền trước
(strict past; close marks era-correct; **loại session short/flagged**)":

1. builder v2.1's carryover law kept **2015-07-02 donor-admitted** although
   the current freeze flags it `HOLIDAY_PDF_EQUITY_2011_2015` — a flagged
   session ⇒ must be donor-excluded;
2. builder v2's label-based 3-class list donor-admitted the 35 relabeled
   flagged sessions (139 → 104) — same violation class.

**Correction law (per frozen SPEC, NOT chosen to preserve any prior output):**
donor-excluded = every session flagged short OR bearing ANY exclusion/flag
class in the CURRENT freeze, evaluated on the current freeze's flags; the
count is machine-derived, never asserted. Impact discipline: SL distances and
trade paths DO change on affected dates; quarantined rehearsal outputs of ALL
prior states stand as history; NO choice was justified by keeping/restoring
any prior PnL path. `repair/DONOR_LAW_CARRYOVER.md` is WITHDRAWN as law by
D-V2-2 (its sha and supersession are recorded in
`final/selection_freeze_v3.json` § `donor_law.supersedes`).

## 3. M1 — freeze v3 (deterministic merge)

`final/build_freeze_v3.py` (sha `b8adbd67…`) merges
`repair/exclude_list_v2.json` (1,318 entries) with the 11 recorded additions
of `y2016/exclude_2016_failclosed.json` (sha `1b846b17…`, class
`HOLIDAY_2016_UNPROVEN_FAILCLOSED`): **4 new set members appended**
(2016-07-01, 2020-07-02, 2021-07-02, 2021-12-31), **7 evidence relabels**
(2016-01-18, 2016-02-15, 2016-05-30, 2016-07-04, 2016-09-05, 2016-11-24,
2016-11-25 — each replacing its `COVERAGE_LT60` entry; the replaced candidate
class is preserved in `overlaps_before_precedence`, mirroring the v2
treatment of the 2011 relabels). `reason_class_priority` gains the new class
at position 4; `priority_rank` renumbered class-purely (1,112 rows of
UNCERTAIN/COVERAGE/WARMUP — rank never affects the exclude SET, which is the
union either way). v2 arithmetic was reproduced EXACTLY first: eval
375/949/711/890 = 2,925, base excl 38/75/72/85. Machine asserts (all PASS):

- **eval surface == 2,921** (F1 375 / F2 948 / F3 708 / F4 890), bounds ==
  EVAL_V3 (F3 eval-last 2021-12-31 → 2021-12-30); WARMUP positional law intact
  (first 252 post-EXCLUDE sessions per fold head);
- v3 date set superset of v2: **+4 / −0**; exactly 11 recorded additions;
  no duplicate dates;
- sha round-trip: `selection_freeze_v3.exclude_list.sha256` ==
  sha256(`exclude_list_v3.json`) = `b101f5c7490f9a182ef6be6d188322ce368fe79476c3f3f46f37bca7cdc5b4aa`.

`final/selection_freeze_v3.json` (sha `a992baac…`, schema `selection_freeze@3`,
**no self-hash**): v2 freeze structure + v3 exclusion sha + the **donor-law
row** (SPEC §4 ERRATUM A7-SPEC-M5 quote verbatim + SPEC sha `445f7499…` +
`repair/FAIL_DONOR_VIOLATION.md` sha `2f06de66…` + carryover withdrawal) + the
**y2016 evidence row** (EVAL_V3.md `6342b65f…`, eval_v3.json `fad3c35a…`,
exclude_2016_failclosed `1b846b17…`, sweep `2953c5ca…`) + pins-as-law carried
verbatim (`owner_ratified_pins_law`, `pins_manifest`, `cost_contract`,
`identity_table`, `laws`, `registered_plan`).

## 4. M2 — machinery v2.2 (the FLAG-BASED donor law)

`final/make_builder_v3.py` (sha `cf0fd897…`) derives
`final/dryrun_builder_v3.py` (sha `5a08c9fd…`) from
`dryrun_v2_1/dryrun_builder_v2_1.py` via exact-marker replacement with a
**REVERSE-APPLY PROOF**: reverting all 18 recorded hunks byte-reproduces the
v2.1 source — the files differ ONLY inside the declared hunks. **Exactly ONE
hunk touches simulation logic (H4, correction C2, in `load_inputs`)**:

```diff
-    short_flagged = classes_v1 and {
-        d for d, cs in classes_v1.items()
-        if cs & {"HOLIDAY_FACT_EARLYCLOSE", "HOLIDAY_UNCERTAIN", "COVERAGE_LT60"}
-    }
-    (v1-label asserts: count == 139; 2015-07-02 donor-admitted; XOR == 35)
+    prev_short_flagged = {v1-label 3-class set}          # 139, carryover
+    donor_family_v3 = {HOLIDAY_FACT_EARLYCLOSE,
+                       HOLIDAY_PDF_EQUITY_2011_2015,
+                       HOLIDAY_2016_UNPROVEN_FAILCLOSED,
+                       HOLIDAY_UNCERTAIN, COVERAGE_LT60}
+    sf_flags = {d for d, cs in classes.items()          # classes = v3 labels
+                if cs & donor_family_v3}
+    short_flagged = sf_flags | prev_short_flagged       # THE C2 LAW
+    (delta evidence derived and reported; count NOT asserted)
```

i.e. donor-excluded := {in-panel sessions bearing ANY short/flag-family class
in `exclude_list_v3`} ∪ {prev short-flagged sessions — the v2.1 carryover 139
(v1 labels), carried so the correction can never re-admit a previously
donor-excluded session}. FOMC_STATEMENT_DAY (full session, statement-risk
only) and WARMUP (positional fold-head label) are NOT short/flag classes and
remain donor-admitted exactly as in every prior state. Everything downstream
(`build_sessions` / `derive_state` / `simulate` / `run_pass`) is byte-identical
to v2.1. The other 17 hunks are documentation/paths/digest/finding metadata
plus the criterion-(d) CHECKER rewrite (S5' — post-hoc check, not simulation
logic; the v2.1 lane rewrote it identically when its baseline moved
v1 → v2; here it moves v2.1 → v3 and becomes EXPECTED-CHANGE-TOLERANT per
mission M3d). Behavior-preservation cross-checks (machine-verified, in-digest):

- FOMCIN 4-class overlap filter == 6-class filter on the v3 surface (no FOMC
  day carries `HOLIDAY_PDF_EQUITY_2011_2015` or the new class); FOMCIN
  set = 104 sessions, unchanged;
- the checker's independently recomputed v3 donor series == the builder
  state's `sldist` (asserted in the checker).

## 5. Surface actually run (final recorded run)

- Eval sessions **2,921** reproduced exactly (builder assert vs
  `selection_freeze_v3.fold_structure`): F1 375 · F2 948 · F3 708
  (eval-last 2021-12-30) · F4 890; `n_sessions_in_set` = 2,921 for every
  trading identity; FOMCIN set 104; C3 FLAT 0.
- Panel: 7,825,657 rows read once per pass; 0 dash rows; 1,834,852 RTH rows
  kept (held chain only). Era validation identical to v2.1 (close 4,142/
  4,204; RTH-open 4,193/4,204 — evaluation view only).
- 24/24 identities at ×1.0 Variant-A declared costs; total trades **13,165**
  (= v2.1's 13,185 − exactly the 20 removed trades of §7(i)).

## 6. Gate-4 PASS criteria (gate law; never PnL quality)

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| a | Enumeration: exactly the frozen 24 identities, byte-exact vs `selection_freeze_v3` | **PASS** | 24/24 byte-exact, set and order equal, zero extras/missing |
| b | Cost recompute: 20 sampled trades vs Variant-A pinned table | **PASS** | 20/20 exact incl. 4 NFA-window rows (fees 2.25 / 2.24-in-window + spread 6.25 + slip 12.50/25.00/37.50); gross = dir×(exit−entry)×50 verified; retired values absent |
| c | Determinism: two full passes byte-identical | **PASS** | trades-index canonical sha256 `13a40f67804808121de3a8b43da4bbf9c4b9165d4402af8b4606c93737f92966` identical across passes; all 24 per-identity JSONs byte-identical (`quarantine/` vs `quarantine_rerun/`; builder check + independent re-verification) |
| d | Delta vs v2.1 quarantine = EXPECTED changes ONLY: (i) removals on the 4 newly-excluded eval dates; (ii) SL changes only on donor-window-affected dates, tabulated; (iii) NO other change | **PASS** | 20 trades removed (§7-i); 124 trades SL-changed on exactly the 59 derived SL-change dates, 21 with knock-on exit changes; **0 unexpected differences; 0 attribution breaks** (every changed trade requires an `sl_distance_pts` difference AND a recomputed donor-window-composition change at that date) |
| e | Warmup regression (v1 D-F1 class) | **PASS** | 13,165 trades scanned across all 24 identities: zero trades ≤ any fold `warmup_carve_out.last`, zero trades on WARMUP-labelled sessions |

**Gate-4 v3 verdict (machinery output, `dryrun_v3_digest.json`): PASS — all
five criteria clean.** This is a rehearsal machinery-vs-freeze reconciliation,
not a PnL result.

## 7. The correction's real cost (D-V2-2 impact — reported honestly, NOT a defect)

**Donor-excluded count (machine-derived at each epoch of the law):**

| Law epoch | Donor-excluded | Evidence |
|---|---|---|
| v1 labels, 3-class filter (v1/v2/v2.1 machinery) | **139** | carryover baseline re-proven from `freezegen/exclude_list.json` (read-only) |
| freeze v2 labels, flag-based family (D-V2-2 expectation) | **140** = 139 + 2015-07-02 | `repair/exclude_list_v2.json`, 4-family view — matches the FAIL record's stated expectation exactly |
| **freeze v3 labels, C2 flag-based law (machinery of record)** | **144** | `final/exclude_list_v3.json` family ∪ carryover 139 |

- **Delta vs 139 = exactly 5 sessions**: 2015-07-02 (`HOLIDAY_PDF_EQUITY_2011_2015`
  flag, no v1 label — the D-V2-2 case-1 session) + the 4 v3 additions
  (2016-07-01, 2020-07-02, 2021-07-02, 2021-12-31, each
  `HOLIDAY_2016_UNPROVEN_FAILCLOSED`). Per-session classes/v1-classes/reasons
  in `dryrun_v3_digest.json` § `donor_law_v3.delta_vs_139_per_session`.
- **Delta vs 140 = exactly the 4 new members.** The 7 relabels were already
  donor-excluded via the carryover 139 (v1 `COVERAGE_LT60`) — flags moved,
  donor membership unchanged for them.

**(i) Trades removed — the 11 v3 exclusions remove exactly 4 eval sessions
(the other 7 were already eval-excluded via COVERAGE_LT60):**

| Identity | Removed | Dates |
|---|---|---|
| FBES1-ALW-D0-S2 / FBES1-PLA-D0-S2 / FBES1-DOSE-D0-S2 | 4 each | 2016-07-01, 2020-07-02, 2021-07-02, 2021-12-31 |
| 8 primaries (CONT-UP ×4 tiers/delays, REV-UP ×4) | 1 each | 2020-07-02 (the only removed date where an UP-tail primary fired) |
| **Total** | **20** | 13,185 → 13,165 |

**(ii) SL-distance changes with knock-on exit changes:** 104 chain dates
(2015-07-03 .. 2022-01-31) have a changed trailing-20 donor-window
composition; on **59** of them the SL distance actually changes; 42 of those
carry trades — **124 trades** across all identities have `sl_distance_pts`
changes and **21** of them change exit (reason/bar/price). The full 42-row
per-date impact table (old→new SL distance, trades changed, exits changed,
identity lists) is in `dryrun_v3_digest.json`
§ `pass_criteria.d_surface_delta.impact_table`. Structure (exactly as the law
predicts — changes cluster in the ~20-session donor windows following each
newly donor-excluded session): 2015-07-06..07-30 (after 2015-07-02), 
2016-07-05..08-01 (after 2016-07-01), 2020-07-13..07-31 (after 2020-07-02),
2021-07-07..07-22 (after 2021-07-02), 2021-12 window tails + 2022-01 F4-warmup
dates (after 2021-12-31; the warmup ones shift state but carry no trades).
Examples: 2015-07-06 15.75→16.00 (10 trades, 5 exits), 2020-07-13
58.75→63.25 (2 trades, 2 exits), 2021-07-19 28.125→29.125 (10 trades, 3 exits).

**(iii) NO other changes:** 0 unexpected differences, 0 attribution breaks;
all common trades byte-identical on every required field (fold, direction, m,
q80, signal/fill bars, entry, cost); entry-side machinery untouched.

## 8. Launch record (honest incident note — no criterion was ever failed)

| # | Builder sha | Outcome |
|---|---|---|
| 1 | `689daa90…` | CRASHED **pre-adjudication** in the criterion-(d) checker (S5' bug: read v2.1 trade rows from the 3-column index instead of the per-identity trade dicts). Both passes had completed and written quarantine outputs; no criteria adjudicated, no digest written. Checker fixed (inside the declared S5' hunk); simulation logic untouched. |
| 2 | `baf582f8…` | Complete, gate-4 PASS; superseded ONLY because the digest's `delta_vs_140` evidence field was computed against a v3-label 4-family view (133) instead of the true v2-label baseline. Panel outputs byte-identical to #1 and #3 (index file sha `6118b061…`). |
| 3 (recorded) | `5a08c9fd…` | Final recorded run: delta-vs-140 computed on `repair/exclude_list_v2.json` v2 labels (= 140, matching the FAIL record). All §5-§7 numbers are from this run. |

**Cross-launch determinism evidence:** all three launches produced
byte-identical panel outputs — `quarantine/trades_index.json` file sha
`6118b0615b8354b41f89d1868a3d3989b803a9b7ef0bddb148dded014f9d8f62` in every
launch (and `quarantine_rerun/` identical within each). The checker/evidence
fixes never touched simulation behavior.

## 9. Zero-denominator statement

No ledger, counter, registry, budget or trial write anywhere in this lane; the
observed denominator was NOT incremented; zero scored cells; all numerics
remain QUARANTINED descriptive-only under `final/quarantine/` +
`final/quarantine_rerun/` with the quarantine header on every artifact. S1
SEALED_UNTOUCHED; zero network; root read-only outside the write boundary;
Python = root `.venv`. HISTORY artifacts (`freezegen/`, `dryrun/`,
`dryrun_v2/`, `dryrun_v2_1/`, `repair/`, `y2016/`) read-only. NO GO exists or
is implied.

## 10. Files produced by this lane (write boundary: `final/**` + handoff)

| Path | Role |
|---|---|
| `final/build_freeze_v3.py` | M1 deterministic merge machinery (asserts eval 2,921; +4/−0; 11 recorded additions) |
| `final/exclude_list_v3.json` | freeze v3 exclusion list (schema `exclude_list@3`, sha `b101f5c7…`) |
| `final/selection_freeze_v3.json` | freeze v3 selection (schema `selection_freeze@3`, sha `a992baac…`; donor-law row + y2016 evidence row + pins-as-law; no self-hash) |
| `final/make_builder_v3.py` | M2 derive script (18 hunks, reverse-apply proof) |
| `final/dryrun_builder_v3.py` | machinery of record (sha `5a08c9fd…`; ONE logic hunk = C2 flag-based donor law) |
| `final/quarantine/**` | pass-1 outputs: 24 per-identity JSONs + `summary.json` + `trades_index.json` |
| `final/quarantine_rerun/**` | pass-2 outputs, byte-identical (criterion c) |
| `final/dryrun_v3_digest.json` | machinery digest: criteria a–e, `donor_law_v3` evidence, impact table, lock record; gate-4 verdict PASS (sha `b01b6b0b…`) |
| `final/DRYRUN_V3_REPORT.md` | this report |
| `../dispatch/handoff_FREEZE-V3-MACHINERY.json` | structured handoff `zcode_orch_v3_handoff@1` |

— End DRYRUN-V3 REPORT (FUTURES-ES-PB1-V1 / FREEZE-V3-MACHINERY).
