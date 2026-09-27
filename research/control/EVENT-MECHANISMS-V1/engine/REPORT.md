# LANE I REPORT — EVENT-MECHANISMS-V1 engine (2026-09-27)

Lane: I (implementation). Worktree
`.worktrees/event-mechanisms-v1/integration`, branch
`orca/event-mechanisms-v1-integration`, parent commit `f1fc2bd3` (verified:
`f1fc2bd33acfb235f711eb8c9c5853d0eb24410f`). Python:
root `.venv` (3.12.14, pandas 3.0.5 / numpy 2.5.2 / pytest 9.1.1; scipy NOT
installed — Spearman implemented in numpy with average ranks + tie handling).
Pre-GO computation boundary (R2-6) enforced throughout: decision records,
prices, cost bands, populations, rhos, dry-run IDs only. **Zero
expectancy/PF/PnL/drawdown aggregates computed anywhere** (machine-checked,
see E8).

## E1 — Loaders (fail-closed digests): PASS

Recomputed (never trusted), all EXACT vs pins:

| Artifact | sha256 (prefix) | vs authority | rows |
|---|---|---|---|
| a1_events.jsonl | `a6a5bb6e…9401` | SHA256SUMS.staged.txt EXACT | 54,941 (pin 54,941) |
| form4_stream.jsonl | `6ac2cd5b…742b2` | G2 pin EXACT | 546,039 (pin 546,039) |
| n4_map_v1.jsonl | `537cd5af…5fd8` | staged sums EXACT | 2,178 |
| NG6 panel (2,169 files) | per-file manifest | 2,169 OK / 0 bad / 0 missing / 0 extra | — |
| eodhd_div (2,168 files) | substrate_manifest | 2,168 OK / 0 bad | — |
| eodhd_splits (2,168 files) | substrate_manifest | 2,168 OK / 0 bad | — |

- a1_events measured from bytes: forms EXACTLY `10-Q` (40,926) / `10-K`
  (14,015); (cik, acceptance_utc, accession) unique = 54,941 → 0 duplicate
  identity, 0 non-exact form; acceptance range 2015-01-05..2026-06-29 (inside
  the dev window). Fold convention `[start, end)`.
- **R2-1 enforcement**: panel reader (`emv1/panel.load_name_bars`) is the
  single reader of panel bytes; explicit column allowlist
  {date, open, high, low, close, volume}; requesting `adjusted_close` raises
  `ForbiddenColumnError` (test-failable); the key is dropped at parse time and
  never enters any structure. Enforced by tests
  (`test_adjusted_close_request_raises`,
  `test_adjusted_close_never_extracted_even_with_full_allowlist`) + the
  recursive key scanner over outputs.
- Panel guard counters (raw load): 2,143/2,169 names produce series
  (26 files empty/all-guard-failed); rows skipped nonpositive/nonfinite
  2,134; volume-0 bars (B2) 160,673; extreme-print bars (B1) 751.

## E2 — A1 book (EMV1-A1-FILINGFLOW-ACC): PASS

Rules implemented per G3_FREEZE + R2-2/R2-3/R2-4: ET strata via
zoneinfo (S1 [00:00,09:30), S2 [09:30,16:00), S3 [16:00,20:00),
S4 [20:00,24:00), weekend bucket SEPARATE); direction = sign of RAW
(close−open) of the direction session (first session whose 16:00-ET close is
strictly after acceptance); entry = next session raw open; anchor H=5,
N1 H=10, N2 = anchor rule restricted to weekday S2. Fold-boundary force-flat
(never cross the fold end; if no in-fold window exists → excluded+counted);
delisting exits kept and flagged; R2-2 window exclusions; X1/X2 + B1
bar-feasibility; frozen DVmed60 eligibility floor.

**Populations (records per arm per fold):**

| arm | F1 | F2 | F3 | F4 | TOTAL |
|---|---|---|---|---|---|
| A1-ANCHOR | 3,690 | 4,018 | 2,550 | 3,851 | **14,109** |
| A1-N1 | 3,411 | 3,678 | 2,315 | 3,406 | 12,810 |
| A1-N2 | 4,883 | 4,787 | 2,634 | 2,273 | 14,577 |

Floors: A1-ANCHOR ≥100/fold **PASS**, ≥400 total **PASS**.

**Unique-event exclusion census** (pipeline-ordered first reason per event;
candidates = bookable ∪ excluded unique events):

| reason | TOTAL |
|---|---|
| BELOW_DV_FLOOR_AT_DECISION | 12,972 |
| ZERO_DIRECTION_SESSION_MOVE | 5,504 |
| NO_SESSION_AFTER_ACCEPTANCE | 3,278 |
| CORP_ACTION_IN_WINDOW | 3,618 |
| FOLD_BOUNDARY_NO_WINDOW | 801 |
| NO_PANEL_FOR_TICKER | 606 |
| ENTRY_BAR_UNFILLABLE_B1B2 | 373 |
| EXIT_BAR_UNFILLABLE_B1B2 | 359 |
| NO_ENTRY_SESSION | 44 |
| candidates unique per fold | F1 17,732 / F2 16,972 / F3 10,588 / F4 9,649 |

R2-2 contamination check: corp-action exclusions / candidates per fold =
5.87% / 5.90% / 5.90% / 9.85% → **contamination_high = False** (bar 40%).

## E3 — A2 book (EMV1-A2-INSIDERFLOW-ACC): PASS with measured limitations

**Schema measurements from bytes (all recorded, per R2-3 ambiguity law):**

1. form4_stream rows carry EXACTLY 11 keys (all 546,039 rows): `cik,
   accession, acceptance, filing_date, transaction_date, transaction_code,
   direction, shares, owner_cik, owner_name, table`.
2. **Amendment distinguishability**: NO form-type field in the stream →
   join `accession` → EDGAR submissions shards (staged by lane S) `form`
   field; form `'4'` = original (KEEP), `'4/A'` = amendment (DROP),
   missing = fail-closed DROP (`AMENDMENT_UNKNOWN`).
3. **Officer/director roles**: NOT in the stream → read from the staged
   Form-4 XML estate (`reportingOwnerRelationship` fields `isDirector`,
   `isOfficer`, `isTenPercentOwner`, `officerTitle`; booleans encoded
   `'1'/'0'` in X030x vintages, `'true'/'false'` in newer). Law applied:
   isDirector OR isOfficer; 10%-owner-only filers dropped+counted.
4. **Price/value**: NOT in the stream → `transactionShares/value` ×
   `transactionPricePerShare/value` from the XML (transactions live under
   `<nonDerivativeTransaction>`, amounts under `<transactionAmounts>`).
   Unpriced rows dropped+counted.
5. **Declared-plan flag**: NOT in the stream → measured `<aff10b5One>` in
   the XML (exists only on post-2023-schema forms; pre-2023 = 0 by
   construction). Used for the E5 cadence proxy only.
6. XML directory layout measured: `form4_xml/CIK##########/<accession
   without dashes>/*.`xml`. Targeted parse: 20,065 unique P-row accessions
   (ALL 37,305 P rows are in-cohort issuers; 1,417 CIKs), 0 XML missing.

A2 pipeline drops (row-level unless noted): ROLE_NOT_OFFICER_DIRECTOR 8,263;
UNPRICED 294; issuer-days BELOW_VALUE_FLOOR (<$100k) 6,331. Net: **5,606
qualifying issuer-day events** (net open-market BUY value ≥ $100,000,
officer/director, original filings), issuer-day = (issuer, UTC acceptance
date), event instant = earliest qualifying acceptance, cluster = ≥2 distinct
insiders (distinct owner_cik/name) same issuer-day.

**Populations:**

| arm | F1 | F2 | F3 | F4 | TOTAL |
|---|---|---|---|---|---|
| A2-ANCHOR (H=10) | 0 | 1,628 | 661 | 632 | **2,921** |
| A2-N1 (H=20) | 0 | 1,482 | 590 | 542 | 2,614 |
| A2-N2 (cluster, H=10) | 0 | 334 | 105 | 93 | 532 |

Floors: A2-ANCHOR ≥400 total **PASS** (2,921); **F1 = 0 → floor FAIL for
F1** — DATA-COVERAGE fact, not selection: the pinned form4_stream substrate
coverage measured **2018-01..2025** (P rows by year: 2018 8,463 … 2025
1,048; no 2015–2017 rows exist in the staged bytes). Recorded as
NOT_RUN_THIN-risk for A2 on F1; requires A1/owner adjudication whether the
freeze floor applies to folds without substrate coverage.

A2 unique-event exclusions: BELOW_DV_FLOOR 1,493; CORP_ACTION_IN_WINDOW 889;
NO_SESSION_AFTER_ACCEPTANCE 391; FOLD_BOUNDARY_NO_WINDOW 88; ENTRY/EXIT
UNFILLABLE 40/41; NO_PANEL 46; candidates per fold F2 3,151 / F3 1,450 /
F4 1,005. Contamination fractions 0% / 15.26% / 11.59% / 23.88% →
**contamination_high = False**.

## E4 — Controls machinery (re-evaluations, no PnL): PASS

| control | construction | populations |
|---|---|---|
| date-only A1 | filing_date 00:00 ET clock, strata removed; ANCHOR H=5 / N1 H=10 | 28,768 / 26,358 (F1 8,587/7,991, F2 8,829/8,175, F3 5,192/4,768, F4 6,160/5,424) |
| date-only A2 | issuer-day filing_date clock, H=10 | 2,920 (F2 1,622 / F3 665 / F4 633) |
| permuted-acceptance ×3 | stamps shuffled within issuer×form×year, seed 20260927, anchor rule | 42,327 anchor-equivalent records (F1 11,070 / F2 12,054 / F3 7,650 / F4 11,553) |
| clock-only shadow | (issuer, session) sampled uniformly at per-bucket event rates, seed 20260927, anchor rule | 10,399 (F1 3,326 / F2 3,344 / F3 1,951 / F4 1,778) |
| value/date-matched placebo A2 | random issuer-days, A2 issuer cohort × A2 date-range, same count, same rule, seed 20260927 | 5,606 (= A2 event count; F2 2,603 / F3 1,762 / F4 1,241) |

All control outputs are decision records with prices + cost bands only
(R2-6).

## E5 — ancestry rho battery (bar 0.20 immovable): PASS — no breach

Identity stream = signed decision indicator (+1 LONG / −1 SHORT / 0 none)
at (name, entry_session). Proxy constructions (documented):
reversal_kd = −sign(raw k-session return) on bars t−1, t−1−k
(unfinished-window safe); momentum_60d = +sign same basis; amihud_kd =
mean(|ret_1d|/dollar-volume) trailing k closed sessions, cross-sectional
percentile rank scaled [−1,1]; declared_plan_cadence_180d = per-issuer count
of aff10b5One='1' P-accessions in trailing 180 calendar days (universe =
A2 parsed accession set — measured limitation; pre-2023 = 0 by schema
vintage).

Spearman (Pearson in evidence file `rho_evidence.json`), pooled + per fold:

| proxy | A1 pooled | A2 pooled | max abs ANY scope (row) |
|---|---|---|---|
| reversal_5d | +0.0240 | −0.0082 | 0.0257 (A1 F4) |
| reversal_20d | +0.0151 | −0.0176 | 0.0194 (A1 F4) |
| momentum_60d | −0.0099 | +0.0213 | 0.0213 (A2 pooled) |
| amihud_28d | −0.0005 | +0.0022 | 0.0112 (A2 F4, abs) |
| amihud_63d | −0.0007 | +0.0008 | 0.0111 (A2 F4, abs) |
| declared_plan_cadence_180d | +0.0005 | +0.0530 | **0.1142 (A2 F4)** |

**Any rho > 0.20: NO** (0 rows over bar across pooled + F1–F4, both
identities). Max margin: A2 × declared-plan-cadence F4 = 0.114 vs bar 0.20
(margin 0.086) — below bar, but the thinnest cell (recorded, not
adjudicated).

A1-vs-A2 stream rho (merge condition, **RECORD ONLY**): pooled Spearman
0.000028 (n 1,292,583 grid points; A1-active 9,616; A2-active 2,690;
overlap points 18) — far below 0.20; collapse condition NOT triggered by
this measurement (adjudication stays with A1).

## E6 — G4 test battery: PASS (22/22)

- (a) **S7 fixtures 3/3 exact** — reproduced from code with synthetic
  weekday panels: fixture a (S3, offset −4, dir 06-11, entry 06-12, exit
  06-18), fixture b (S1, −4, dir 06-10, entry 06-11, exit 06-17), fixture c
  (S3 + weekend bucket, offset **−5 EST**, dir 2025-11-03, entry 11-04).
- (b) **9 hand fixtures** (≥6 required):
  1. close-boundary instant (16:00:00 ET acceptance → direction = NEXT
     session; 1s earlier → same-date session);
  2. no-lookahead shift mutation (event instant shifted one session →
     direction/entry/exit shift exactly one session; byte-compared);
  3. DST spring-forward (2025-03-09 22:30Z = 18:30 EDT −04:00, S3+weekend);
  4. fold-boundary force-flat (F3 event, H=10 → exit 2022-12-30,
     forced_flat=True, never crosses 2023-01-01);
  5. cost applied exactly once per side (entry = base×3.35, exit =
     base×1.0; RT(x) = entry+exit scaled once; class-B check);
  6. volume-0 entry bar → EXCLUDED `ENTRY_BAR_UNFILLABLE_B1B2`;
  7. delisting exit (panel ends mid-window → exit at last bar,
     delisting_exit=True, event kept);
  8. window exclusion on a synthetic split inside the hold (excluded;
     outside the window → bookable);
  9. zero-direction session (close==open → excluded+counted);
  + B1 extreme-print bar (100× jump → unfillable, both directions law).
- (c) **Unfinished-window guard**: `guard.assert_readable` raises
  `LookaheadRead` on any bar whose 16:00-ET close is after the decision
  instant; planted-future-bars invariance (dvmed60 unchanged with 1e12
  closes planted beyond the decision); fail-closed on short history
  (< DV_MIN_PRESENT → None).
- (d) **Panel-truncation replay: 318/318 byte-identical** (300 random
  events seed 7 + 18 fold-boundary events = 3 nearest each side of all 3
  boundaries). V1 entry-instant truncation: decision prefix
  (direction_session/direction/entry_session/entry_price) 318/318. V2
  fold-context truncation (cutoff = fold end + H_max buffer so the
  forced_flat/delisting_exit panel-extent flags are well-defined): FULL
  builder record byte-identical 318/318. Evidence
  `evidence/truncation_replay.json`.
- (e) **Determinism**: small rebuild byte-identical (pytest) + full-chain
  double run: 15/15 evidence files byte-identical
  (`evidence/determinism_full_run.json`).

## E7 — cost ceiling (G6 paper, PREREGISTERED arithmetic only): COMPLETE

Frozen constants + sources:

| constant | value | source |
|---|---|---|
| band schedule | A/B/C = 10/15/25 bps per fill at DVmed60 ≥ $50M / ≥ $10M / ≥ $2M | `research/control/stocks_amihud_retest_v1/d1/cost_contract.json` @ branch `orca/stocks-amihud-retest-v1-integration`, blob sha256 `b7d4464e8aa91588eb01adf39d48da32e96b8fa9b4d1c14554683f5a918b8593`, frozen 2026-09-23T06:40:00Z |
| engine constants cross-check | DV_FLOOR 2e6, DV_WINDOW 60, DV_MIN_PRESENT 30, CAP_FRAC 0.15, STRESS 2.0, band_bps fails closed at 25 | `impl/samv1r/engine.py` (same branch) verbatim |
| cost debit law | exactly once per fill; entry and exit separate fills | cost_contract.json |
| frozen stress/ceiling | ×2.0 PRIMARY; ceiling 100 bps round trip = 25 bps × 2 fills × 2.0 | cost_contract.json |
| Q-2 conditional law | open = 3.33× midday (per-minute movement) / 3.35× midday (measured spread); open-crossing entries priced at the EXPENSIVE band | `research/wayfinder/LESSONS.md` Q-2 (same branch, lines 389–401) |
| band-C 13.8% | measured band-C fraction of the STOCKS-NG6 fired population ("NOT majority") | `plans/CYCLE_REGISTRY.json` STOCKS-NG6 terminal entry + `research/wayfinder/HYPOTHESIS_LEDGER.md` STOCKS-NG6 row |

Per-event cost bands recorded on every decision record:
`cost_entry_bps_x1 = class_bps × 3.35`, `cost_exit_bps_x1 = class_bps ×
1.0`; round trip = sum × {1.0, 1.5, 2.0}. Band-C bound round trip =
108.75 bps at ×1.0 → 163.13 at ×1.5 → 217.50 at ×2.0; midday-basis band-C =
50 → 75 → 100 bps. Ceiling grid template (required per-event gross
expectancy vs event count per arm, ×1.0/×1.5/×2.0) in
`evidence/cost_evidence.json` — 18 rows (6 arms × 3 powers), TEMPLATE ONLY,
no expectancy computed. Measured band mix per arm (e.g. A2-N1: A 1,323 /
B 747 / C 544) in the same file.

## E8 — exact-arm dry-run: PASS

`dryrun/dryrun_manifest.json` + `dryrun/placeholder_ledger.jsonl`
(engine-owned; canonical trial ledger NOT touched — A1 owns it):

- 6 arms recorded: A1-ANCHOR 14,109 / A1-N1 12,810 / A1-N2 14,577 /
  A2-ANCHOR 2,921 / A2-N1 2,614 / A2-N2 532 (fold splits above).
- `arms_scored: false`; `real_money: false`;
  `record_kind: DECISION_RECORDS_ONLY_PRICES_AND_COST_BANDS`.
- **Pairwise-distinct record IDs: TRUE** (all 15 arm pairs, 0
  intersections; IDs are prefixed `{arm_id}:{event identity}`).
- **Recursive no-forbidden-field scan: CLEAN** — every JSON/JSONL output at
  every depth (16 files) scanned for the forbidden key substrings
  {pnl, profit_factor, expectancy, drawdown, sharpe, return, _ret, ret_,
  net_return, gross_return, win_rate, hit_rate, avg_trade, per_trade, pnr}:
  0 violations. Combined with the builder field whitelist
  (`book.DECISION_KEYS`: prices, cost bands, flags only) this is the R2-6
  boundary proof. No exit-minus-entry return exists in any artifact and no
  aggregate was computed at any depth.

## E9 — targeted tests: PASS

`pytest tests/` (root .venv): **22 passed, 0 failed, 8.06s**. Files:
`tests/test_s7_fixtures.py` (3), `tests/test_hand_fixtures.py` (10),
`tests/test_unfinished_window.py` (3), `tests/test_engine_guards.py` (6:
digests fail-closed, allowlist enforcement ×2, scanner, scanner-over-
outputs, determinism).

## Incidents / heavy-candidate notes

1. I-H1 (fixed in-lane): first pytest run took 12:54 — a test-side O(n²)
   expression (re-sorting a 54,941-element set inside a comprehension)
   dominated; `sample(1)` of the spinning process + hoisting the expression
   fixed it. Engine build stages themselves are light: full build ~40 s,
   controls ~60 s, rho ~50 s, truncation replay ~90 s (all well inside the
   heavy boundary; no step exceeded 10 min CPU after the fix).
2. I-H2 (fixed in-lane): force-flat vs delisting clamp order initially
   mislabeled delisting exits as fold force-flats; corrected to a
   calendar-based fold test (force-flat only when the name has bars past
   the fold end) with a dedicated fixture (test_4/test_7 pair).
3. I-H3 (schema, recorded — not a defect): form4_stream carries NO
   form-type/amendment marker, NO role field, NO price, NO declared-plan
   flag (11 keys measured). Amendment drop, role filter, buy value and the
   10b5-1 cadence proxy all read the staged Form-4 XML estate / submissions
   shards; every drop counted (E3). Any change to these mappings returns to
   A1 per the ambiguity law.
4. A2-F1 = 0 (stream substrate begins 2018-01) — freeze-floor FAIL on F1
   for A2, flagged for adjudication; NOT silently normalized.

## Known limitations for Lane X / G-gates

1. A2 fold coverage is F2–F4 only (substrate coverage); date-only A2 and
   the A2 placebo inherit the same support.
2. 26/2,169 panel names produce no series (all bars guard-failed or empty);
   their events are excluded+counted (`NO_PANEL_FOR_TICKER`: A1 606 unique).
3. Pre-2023 Form-4 XMLs predate the `aff10b5One` field: declared-plan
   cadence is structurally 0 before 2023 (schema vintage, not absence of
   plans).
4. Proxy planes are PROXY-PRIOR (stocks cost plane 0/10 measured) — carried
   label, unchanged.
5. Issuer-day keying uses the UTC acceptance date and the earliest
   qualifying acceptance instant as the event clock (recorded choice);
   cluster counts distinct owner_cik (fallback owner_name).

## Outputs

- Engine: `research/control/EVENT-MECHANISMS-V1/engine/`
  (`emv1/` 9 modules, `run/` 6 runners, `tests/` 4 files + conftest).
- Evidence: `engine/evidence/` (a1/a2 decisions+exclusions, a2 issuer-day
  table, build/controls/rho/cost/truncation/determinism json). Record
  tables committed gzip-compressed (8.5 MB total; deterministic jsonl —
  G5 comparison is on the decompressed bytes; a rerun regenerates raw
  .jsonl alongside).
- Dry-run: `engine/dryrun/` (manifest + placeholder ledger).
- One clean commit on `orca/event-mechanisms-v1-integration` (pathspec-
  staged; nothing else touched).

---

# DELTA r3 — 2026-09-27 (task delta-r3, remediation + re-run lane; append-only)

Binding authority: `G3_FREEZE_ADDENDUM_r3.md` (A1 court adjudication of the
pre-r3 G5 comparison). Both implementations rebuilt to the r3 canonical
reading; re-comparison record-only (R2-6 held; zero PnL at any depth).

## Delta changes (this engine)

1. **D-1 (r3 defect)**: A2 entry = FIRST session whose 09:30 ET open is
   strictly after the acceptance instant (`resolve_entry_open_anchored`);
   A2 records carry `direction_session = null`. The pre-delta A2 path
   reused the A1 close-anchored sequencing — non-spec for ~55% of A2
   acceptances (S1/S4).
2. **D-2 (r3 defect)**: `load_corp_actions` resolves div/split stems
   CASE-INSENSITIVELY (the 79 case-differing files are now matched);
   collisions deterministic + counted; loader census: 4,336 files, 0
   collisions. CA window is now a CALENDAR-interval compare (r3 AMB-15;
   ex-dates on non-session days inside [entry..exit] contaminate), checked
   on the FINAL window after the exit roll (r3 AMB-13).
3. **AMB-1**: weekend acceptances are anchor members, stratum label `WKND`
   (S1∪S3∪S4∪WKND). Production weekend candidates: 0 (measured, unchanged).
4. **AMB-7**: unfillable EXIT bars ROLL FORWARD to the next clean bar
   (notes `EXIT_ROLLED_B1X1`); exhaustion = last permissible bar +
   `delisting_exit` + `EXIT_ROLL_EXHAUSTED_AT_LAST_BAR`. The
   `EXIT_BAR_UNFILLABLE_B1B2` exclusion is retired (412 pre-delta
   exclusion rows leave the census; the roll may extend or exhaust).
5. **AMB-9**: fold assignment by ET-LOCAL acceptance date
   (`clock.fold_of_et`); fold labels move for post-midnight-UTC
   acceptances (bookkeeping only).
6. `parse_acceptance_utc` accepts ISO-offset stamps too (control machinery
   shadow/placebo records feed ET-offset instants; production stamps
   unchanged). AMB-10/11/14/16 and AMB-2/3/4/5/6/8/12 were already
   canonical here — now pinned by regression tests.

## Populations (r3-canonical rebuild; floors unchanged)

| arm | F1 | F2 | F3 | F4 | total |
|---|---|---|---|---|---|
| A1-ANCHOR | 3,679 | 4,013 | 2,553 | 3,851 | **14,096** |
| A1-N1 | 3,392 | 3,665 | 2,319 | 3,407 | 12,783 |
| A1-N2 | 4,873 | 4,778 | 2,633 | 2,281 | 14,565 |
| A2-ANCHOR | 0 | 1,606 | 664 | 633 | **2,903** |

Floors: A1-ANCHOR ≥100/fold PASS, ≥400 total PASS (A1-N2 also PASS).
A2 F1 = 0 (substrate fact) → **NOT_RUN_THIN stands** per F-ADJ-1; the
frozen floor is not relaxed.

A1 exclusion census deltas vs pre-delta: CORP_ACTION_IN_WINDOW 4,935 →
5,049 (D-2 case-fix + AMB-15 interval); EXIT_BAR_UNFILLABLE 412 → 0
(AMB-7 roll); ENTRY fill 498 → 602 (entry laws now precede window
clamping — reason precedence only). Contamination: no fold >40%
(max 9.81% F4) → CONTAMINATION_HIGH none.

## Re-run proofs (this engine)

- pytest: **35/35 PASS** (`evidence/pytest_run.txt`; 13 new r3-delta tests
  in `tests/test_r3_delta.py`).
- Truncation replay (seed 7; 300-event sample + 18 fold-boundary): **318/
  318** V1 prefix + **318/318** V2 full-record byte-identical
  (`evidence/truncation_replay.json`).
- Full-chain determinism double-run: **10/10 files byte-identical**
  (`evidence/determinism_full_run.json`).
- Dry-run proofs: pairwise-distinct IDs TRUE; recursive no-PnL scan CLEAN.

## Re-comparison outcome (records only)

See `../G5_VERDICT.md` and `../reconciliation/comparison_results.json`.
A1-N2 key sets IDENTICAL (14,565 = 14,565); A1 anchor 4 key diffs /
3 field diffs, all the fold force-flat convention (unruled at r3); A2
field diffs 14 on the 2,271 secondary-matched instants, all force-flat.
**Zero DEFECT, zero unattributed** after 1 fix iteration (lane X
exhaustion-exit semantics). Final G5 verdict:
**G5_PASS_RESIDUALS_CLASSIFIED**.
