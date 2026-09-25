# FALSIFIER_REPORT — ERP1-TRACKA-COHORT-1 — tracka1-falsifier (GO-1 battery)

Lane: FALSIFIER (PRE-PnL battery to completion; freeze artifact + ledger
seed). GO-1 consumed; **GO-2 NOT given — no scored row exists anywhere**.
Worktree: `.worktrees/erp1-tracka-cohort-1/integration`, branch
`orca/erp1-tracka-cohort-1-integration`, dispatch SHA
`2682422a62e64edd25cca42b6a51fdffdfba4d14` (verified: pwd/branch/HEAD at
lane start). Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.

**HARD LAW HELD:** no PnL / expectancy / PF / win-rate of any arm exists
in this lane or its artifacts. The schedule-only executor
(`tracka_lib.schedule_only`) emits entry/exit/direction/hold ONLY — the
engine's price/pips code path is never entered. The only magnitude
arithmetic is F-5 declared-band arithmetic on COSTS (spread pips) and the
§9.4 seam constants (`c_rt` from the cost book; `N_diff` from schedules).
The seam law's `S` is recorded `NOT_COMPUTABLE_PRE_PNL`. The holdout
window 2026-01-01..2026-06-30 was never read (one-look law).

Mandatory class labels on every verdict and ledger row:
`SINGLE_SOURCE_PANEL`, `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`,
`PAPER_TIER`. Wording bans honored (taker PAYS the spread; no
maker/queue claims; no live-readiness wording).

---

## 1. Verdict lines (headline)

```
Task 0  PLANE PIN        PINNED  ancestry close-column-HIGH/true-LOW = SIGNAL
                         plane; port true-H/L = COST plane; spreads identical
F-5  M3 (USDCAD)         NOT_SCORED_FALSIFIED   stress RT 4.8 pips >= 2.0 kill line
                         (margin +2.8 pips; base-book RT 2.4 > 1.5 hypothesis);
                         V-1, T-1, T-2, T-3 MOOT (explicitly recorded, not run)
F-5  M1 (both pairs)     REPORT_ONLY_F5_NO_DECLARED_BAND (no kill invented)
F-PIT-1 M-1 AUDUSD/USDCAD  PASS  (pure index shift == independent impl, arrays equal)
F-PIT-1 M-2 AUDUSD/USDCAD  PASS  22.99% / 20.38% in-session dev bars differ (gate >= 2%,
                           margins +20.99pp / +18.38pp)
F-PIT-1 M-3 AUDUSD/USDCAD  DISCLOSED_SEAM (bar disagreement vs R-ORIG 16.7% / 19.6%;
                           day mode-flip rate 43.0% / 63.4%; orig-active-daemon-flat
                           278 / 564 days; reverse 0; midday daemon mode changes
                           520 / 772 days) — never a kill
F-PIT-1 M-4               FIXTURE COMMITTED (self-test blindness is structural)
F-PIT-1 M-5 AUDUSD/USDCAD  R-ORIG LEAK_PROVEN (truncated replay differs on 936/1298 =
                           72.1% and 973/1298 = 75.0% of days); R-ANCHOR
                           PIT_CLEAN_AS_EXECUTED (0 differing days)
F-1  AUDUSD               pooled |rho| 0.1352 (<= 0.20); max 0.3276 (PDHLOC buf=0)
F-1  USDCAD               pooled |rho| 0.1214 (<= 0.20); max 0.2827 (PDHLOC buf=0)
                           (gate is Task-2-binding; for M1 = ancestry disclosure;
                           RANGEEXP family: 0.1905 AUDUSD / 0.2522 USDCAD)
F-3  clock-placebo        NOT CONSTRUCTIBLE AS PINDED: occupancy predicate FAILS
                           (placebo 65.8% / 65.7% vs 10-40% band; the anchor's own
                           in-session occupancy is 49.8% / 48.2%) => causal control
                           must be REBUILT before scoring (plan 8 F-3 remedy) —
                           scored-phase prerequisite, NOT an arm kill
F-3  mode-sham            PASS_NON_VACUOUS 41.8% / 39.1% of day labels changed
                           (seed 20260925); bar disagreement vs anchor 22.8% / 20.9%
F-6  populations          ALL non-FLAT arms meet smoke 30 / adjudication 100 /
                           promote 236 on the dev union AND smoke 30 on the last-6
                           window (anchor: AUDUSD 923 dev / 100 last6; USDCAD 962 / 97;
                           FLAT = 0 by design). COUNTS ONLY.
F-7                       DECLARED_PRE_PNL (stats + exclusion-zone fields frozen)
STOP CONDITIONS           none fired (no M-1/M-5 failure; plane ambiguity resolved;
                          no net-return arithmetic anywhere)
```

Seam constants frozen (§9.4; exact formulas in §3.4 below): `c_rt` =
2.0 pips (AUDUSD), 2.4 pips (USDCAD), base book, R-ANCHOR and R-ORIG
alike; `N_diff` = 728 (AUDUSD) / 665 (USDCAD); `S` NOT computable (PnL) —
limbs (i)/(ii) evaluate in the scored phase; limb (iii) machinery frozen
(matched pairs 337 / 306 ≥ floor 20 ⇒ evaluable, pairing rule pinned).

---

## 2. Task 0 — PLANE SEMANTICS PIN (LINEAGE-NOTE-1 resolved)

Decision rule (frozen by A1): the ANCESTRY convention is the SIGNAL plane
of ALL arms (R-ORIG stays a faithful ancestor instantiation); the port's
true-H/L bars remain the COST plane (spread charging unchanged).

Exact ancestor convention (re-derived from ancestry
`build_bars.py` under the verified `(sec,o,c,l,h,v)` decode): 15m `b_h` =
**max of the CLOSE column**, 15m `b_l` = **min of the LOW column**; H1 =
max/min over the four valid 15m bars. LINEAGE-NOTE-1 precision fix: only
the HIGH is close-column — the ancestor's LOW was already the true low.

Verification (rebuild from raw M1 bytes under the heavy lock, diff vs the
port's planes; `data_local/derived/plane_diff_{SYM}.json`):

| Metric | AUDUSD | USDCAD |
|---|---|---|
| 15m rows / ts sets equal | 130,160 / yes | 130,102 / yes |
| 15m `b_h`: anc < port / equal / anc > port | 118,910 / 11,250 / **0** | 120,409 / 9,693 / **0** |
| 15m `b_h` mean gap (pips) / max abs diff | 0.63 / 0.00831 | 0.75 / 0.00720 |
| 15m `b_l` differing bars / max diff | **0 / 0.0** | **0 / 0.0** |
| H1 rows / ts sets equal | 30,420 / yes | 30,386 / yes |
| H1 `b_h` anc < port / equal / mean gap pips | 28,402 / 2,018 / 0.67 | 28,797 / 1,589 / 0.81 |
| H1 `b_l` differing bars | **0** | **0** |
| `s_open`/`s_close` max abs diff (15m & H1) | **0.0 / 0.0** | **0.0 / 0.0** |

Consequence (structural, as predicted): ancestor ranges are narrower on
the top than true ranges (max-close ≤ true high, never above). The cost
plane is bit-identical across conventions. Recorded in the freeze
artifact (`plane_semantics_pin`).

## 3. Task 1 — F-5 declared-band arithmetic on COSTS

Formula (pinned): `stress_RT = 2 crossings × k × s_cond`, `s_cond` =
n-weighted mean of bucket OPEN p50s over the break-window buckets the
07–18 UTC window actually fills in (`london_07_12`, `ny_overlap_12_16`,
`ny_late_16_21`), from the committed censuses (`tracka_census@2`).

### M3 (USDCAD home pair) — KILLED pre-PnL

- `s_cond` = 1.2 pips (all three buckets p50 = 1.2; n = 28,390 / 22,787 /
  27,811 — the weighted mean is 1.2 exactly; the max-bucket robustness
  variant is identical).
- Measured stress RT = 2 × 2.0 × 1.2 = **4.8 pips ≥ 2.0 kill line ⇒
  `NOT_SCORED_FALSIFIED`, falsifier_id F-5, mechanism M3** (margin to
  kill line +2.8 pips). The declared hypothesis band was ≤ 1.5 pips
  round trip; even the BASE book (k = 1.0) RT = 2.4 pips exceeds it.
- **All M3-only conditions are MOOT and explicitly recorded as not-run:**
  V-1 fixture, T-1 session-collapse tripwire, T-2 just-closed-bar PIT
  fixture, T-3 mutation non-vacuity. No M3 arm, schedule or rho fixture
  was computed.

### M1 (both pairs) — REPORT-ONLY (no declared premium band exists in the freeze; no kill invented)

| Pair | s_cond p50 | RT @k=1.0 | RT @k=1.5 | RT @k=2.0 | overall p50 | rollover p50 |
|---|---|---|---|---|---|---|
| AUDUSD | 1.0 | 2.0 | 3.0 | 4.0 | 1.0 | 2.0 |
| USDCAD | 1.2 | 2.4 | 3.6 | 4.8 | 1.2 | 2.3 |

Context for the scored phase: the anchor's measured `c_rt` (below)
equals the census conditional floor on both pairs — median fills sit in
the 1.0/1.2-pip regime.

## 4. Task 2 — F-PIT-1 (M-1..M-5) + seam constants + mode-sham

Dev window 2021-01-01..2025-12-31, warmup = first 61 traded days
(AUDUSD/USDCAD: warmup ends inside 2021-03; 1,237 post-warmup traded
days; in-session = 07–18 UTC tradable bars post-warmup = 14,567 /
14,640). All signal machinery on the ANCESTRY-convention H1 plane.

- **M-1 shift-equivalence: PASS both pairs.** Implementation A (pure
  usage-index shift of the ancestor function — same `pct` dict, index
  shifted at consumption, guard `pct[d−1] > 0`) and implementation B
  (independent from-scratch percentile of `ranges[d−1][0]` vs history
  strictly before d−1, numpy window slices) produce **integer-identical
  target arrays** on both pairs. `NOT_RUN_ARMS_REDERIVED` did not fire.
- **M-2 non-vacuity: PASS both pairs.** tgt(R-ANCHOR) ≠ tgt(R-ORIG) on
  3,349/14,567 = **22.99%** (AUDUSD) and 2,983/14,640 = **20.38%**
  (USDCAD) of in-session dev bars — margins +20.99pp / +18.38pp over the
  2% `KILL_VACUOUS_MUTATION` gate. Mechanism: the day-mode label changes
  on 501/1,237 (40.5%) and 441/1,237 (35.7%) of post-warmup days; the
  marginal label distributions are identical (flat 25/27, fade
  867/858, follow 345/352) — the shift moves WHICH days, not how many.
- **M-3 daemon seam: DISCLOSED_SEAM (logged, not a kill).** Pinned
  emulation semantics (in the freeze artifact): at each signal bar the
  mode is the searchsorted-left percentile of the PARTIAL day range up to
  and including that bar vs the trailing-60 full prior-day ranges; the
  state machine consumes the current bar's mode; pos persists within the
  day; pd_h/pd_l = prior day's full hi/lo. Measurements (vs R-ORIG):
  bar-level disagreement 6,784 bars = 16.7% (AUDUSD) / 6,739 = 19.6%
  (USDCAD); day-level mode-flip rate 43.0% / 63.4%; days where R-ORIG is
  active but the daemon's first in-session mode is flat: 278 / 564
  (early-silenced); reverse: 0 / 0 (structurally sensible); the daemon's
  mode CHANGES mid-day on 520 / 772 days — the third-law signature.
- **M-4 self-test blindness: fixture committed**
  (`tests/test_tracka_lib.py::test_m4_self_test_blindness_fixture`): a
  synthetic panel where the daemon law and R-ORIG produce different
  arrays while the shipped same-panel self-test construction (same
  function, same panel) trivially returns PASS. Structural blindness,
  proven by construction.
- **M-5 panel-truncation PIT proof: both arms behave as the law
  requires.** Definition (pinned): truncated replay = the day-stat layer
  computed on the prefix panel strictly BEFORE the day's first bar; the
  bar-walk then runs over the day's bars using that frozen stat layer
  (T0 = strict day start; T1 = first-bar-closed prefix, disclosed).
  R-ORIG differs from its full-panel replay on 936/1,298 (72.1%) days
  (AUDUSD) and 973/1,298 (75.0%) (USDCAD) at T0 — **the leak is proven
  end-to-end**; R-ANCHOR is **identical on every day (0 differing
  days)** on both pairs — PIT-clean as executed, not just as specified.
- **Seam-law constants (frozen; formulas stated):**
  - `c_rt` = median over the arm's dev-window closed round trips of
    [s_open(entry fill bar) + s_open(exit bar) for signal exits /
    s_close(day-close bar) for force-flat exits] × pip_mult, base book
    k = 1.0, in pips. Measured: **AUDUSD 2.0 pips; USDCAD 2.4 pips**
    (R-ANCHOR and R-ORIG alike). The bar spreads reconcile to the census
    p50s exactly (data-gate reconcile gate = 0.0 diff), so this is the
    per-session spread curve evaluated at the arm's actual fill bars.
  - `N_diff` = round trips whose (entry_ts, direction) differ between
    R-ANCHOR and R-ORIG: **728** (AUDUSD: 362 anchor-only + 366
    orig-only) and **665** (USDCAD: 330 + 335).
  - `S` = **NOT_COMPUTABLE_PRE_PNL** (limbs (i)/(ii) evaluate in the
    scored phase; this lane freezes the constants and machinery only).
  - Limb (iii) machinery: nearest-in-time unmatched R-ANCHOR-only trip
    within the same UTC day, equidistant → EARLIER entry_ts (rule
    frozen); matched pairs 337 (AUDUSD) / 306 (USDCAD) ≥ floor 20 ⇒
    **evaluable** in the scored phase (pin (v)).
- **Mode-sham (F-3 extension): PASS_NON_VACUOUS both pairs.** Seed 2026-
  0925 (pin (i)); the anchor's day-level FADE/FOLLOW labels permuted
  among active days (marginal frequency preserved; flat stays flat;
  pd_h/pd_l stay with their days). Labels changed: 542/1,263 active days
  = 41.8% of all dev days (AUDUSD), 508/1,262 = 39.1% (USDCAD) — both
  ≥ 2%. Bar-level disagreement vs R-ANCHOR: 22.8% / 20.9% of in-session
  bars. Internal check: rebuilding R-ANCHOR from its own (unpermuted)
  labels equals the arm-A implementation — true on both pairs.
  Outcome vocabulary per freeze pin (iii): this is a diagnostic-only
  record, never a positive input.

## 5. Task 3 — F-1 ancestry rho (skeptic representation law)

Frozen variant set = the **12 census family functions ported from
ancestry v2_lib** (GAP, PDHLOC, DOW, ASIAFADE, SESSMA, H1TSMOM, H1DONCH,
DAYMOM, RANGEEXP, STOCH, ROUNDNUM, HOURREV) × 2 lane-pinned variants
each = 24 variants (full table frozen in the freeze artifact
`f1_frozen_variant_set`; pip-parametrized). Representation = the EXACT
scored target array over post-warmup dev bars (in-session-only rho also
logged). Spearman via average-tie ranks.

| Pair | pooled |rho| (gate ≤ 0.20) | max |rho| | max variant | RANGEEXP C3 | RANGEEXP breakout |
|---|---|---|---|---|---|
| AUDUSD | **0.1352** | 0.3276 | PDHLOC buf=0, opp-exit | 0.1905 | 0.2481 |
| USDCAD | **0.1214** | 0.2827 | PDHLOC buf=0, opp-exit | 0.2522 | 0.2060 |

Reading (recorded honestly): the **pooled** |rho| — the gated statistic
per plan §3.4/§8 — sits under 0.20 on both pairs. The **max** single
variant exceeds 0.20 on both pairs and is PDHLOC, the family that shares
the prev-day-break execution machinery with this one. For M1 this whole
table is **DISCLOSURE of declared ancestry, not a gate**: M1 is the
Task-1 replication of the RANGEEXP family itself (plan §3.5) and cannot
be vetoed for being related to its own ancestry; the F-1
`VETO_NOVELTY_RENAME` class binds Task-2 proposals only. M3's armed V-1
fixture is **MOOT** (M3 killed at F-5). No kill fired.

## 6. Task 4 — F-3 clock-placebo constructibility + mode-sham

Pinned recipe (in the freeze artifact): entries/day = round(anchor avg
entries per traded day); entry hour = round(anchor avg entry hour)
clamped [7,17]; direction alternates by traded-day index; exit after
round(anchor avg hold) bars or day close.

| Predicate | AUDUSD | USDCAD |
|---|---|---|
| anchor avg entries/day, entry hour, hold bars | 0.71, 10.7, 7.0 | 0.74, 11.2, 6.5 |
| placebo trips (dev) | 1,286 | 1,240 |
| **occupancy 10–40%** | **FAIL — 65.8%** | **FAIL — 65.7%** |
| both directions present | PASS | PASS |
| ≥90% round trips differ from anchor | PASS (97.7%) | PASS (98.6%) |
| non-constant series | PASS | PASS |

**Verdict: the causal control is NOT constructible under the pinned
recipe — the occupancy predicate fails on both pairs** (margin −25.8pp /
−25.7pp below the 40% ceiling), and the anchor's own in-session
occupancy (49.8% / 48.2%) already sits above the band, so no
clock-matched clone can satisfy it. Per plan §8 F-3's own remedy the
control **must be REBUILT before scoring**; recorded as a scored-phase
prerequisite (the scored phase may not run a causal-control cell until a
rebuilt recipe satisfies all four predicates). This is NOT an arm kill
and NOT an arm-set re-derivation. Mode-sham: see §4 (PASS_NON_VACUOUS).

## 7. Task 5 — F-6 populations (COUNTS ONLY)

Floors: smoke 30, adjudication 100, promote 236 (dev union). Fold table
(pinned, 6 × 10-month chronological, force-flat at boundaries is the
scored executor's law): F1 2021-01..10, F2 2021-11..2022-08, F3
2022-09..2023-06, F4 2023-07..2024-04, F5 2024-05..2025-02, F6
2025-03..12; last-6 feasibility window 2025-07-01..2025-12-31.

| Arm | pair | per-fold F1..F6 | dev union | last-6 | smoke | adjud | promote |
|---|---|---|---|---|---|---|---|
| R-ANCHOR | AUDUSD | 113/172/156/167/157/158 | **923** | **100** | Y | Y | Y |
| R-ORIG | AUDUSD | 117/172/156/169/156/157 | 927 | 101 | Y | Y | Y |
| R-NEIGH | AUDUSD | 113/172/156/167/157/158 | 923 | 100 | Y | Y | Y |
| INVERTED | AUDUSD | 113/172/156/167/157/158 | 923 | 100 | Y | Y | Y |
| SHORT/LONG_ALWAYS | AUDUSD | 169/221/219/219/227/221 | 1,276 | 135 | Y | Y | Y |
| R-ANCHOR | USDCAD | 110/184/171/167/166/164 | **962** | **97** | Y | Y | Y |
| R-ORIG | USDCAD | 115/181/168/171/164/168 | 967 | 100 | Y | Y | Y |
| R-NEIGH | USDCAD | 110/184/171/167/166/166 | 964 | 97 | Y | Y | Y |
| INVERTED | USDCAD | 110/184/171/167/166/164 | 962 | 97 | Y | Y | Y |
| SHORT/LONG_ALWAYS | USDCAD | 160/219/219/222/221/217 | 1,258 | 131 | Y | Y | Y |
| FLAT | both | 0/0/0/0/0/0 | 0 (by design) | 0 | n/a | n/a | n/a |

No population floor is at risk: every non-FLAT arm clears even the
promote floor on the dev union, and the last-6 window clears smoke.
(Whether the arms deserve those counts is the scored phase's question —
these are schedule counts, not outcomes.)

## 8. Task 6 — F-7 concentration pre-check (declared, pre-PnL)

Declared statistics the scored phase MUST emit, at cost books k=1.0 and
k=2.0, folds F1..F6 (dev) only:
- **Fold level:** top-fold share = max over folds of (positive net in
  fold)/(total positive net); gate G6 ≤ 0.50.
- **Trade level:** top-5-trades share = sum of the 5 largest positive
  trade pips / total positive net; gate G7 ≤ 0.50 (top-single-trade
  share also logged).
- **Session-hour level:** top single session-hour share = max over UTC
  hours of (positive net in hour)/(total positive net); gate G8 ≤ 0.50.
- Exclusion-zone log fields (frozen): `level(fold|trade|hour)`, `id`,
  `share`, `threshold`, `cost_tier k`, `arm_id`, `pair`,
  `fold_or_holdout_tag`.

## 9. Freeze artifact and ledger seed

- **`freeze/GO1_freeze_artifact.json`** (schema `tracka_go1_freeze@1`)
  carries the five mandatory pins: (i) bootstrap seed **20260925** +
  mode-sham seed **20260925** + storage path (pins written to
  `freeze/freeze_pins.json` BEFORE any consuming computation; measured
  constants merged before the single commit — no scored computation
  exists in this cycle segment); (ii) §9.1 holdout-pass membership
  (per pair: anchor R-ANCHOR + companions CAUSAL-PLACEBO, INVERTED,
  BASELINE-SET incl. the inverted companion and the beta-matched books
  AUDUSD→SHORT_ALWAYS / USDCAD→LONG_ALWAYS; never-selectable: R-ORIG,
  R-NEIGH, R-DAEMON, mode-sham, M2, M3) with sha256
  `3135b11dfe83de49…`; (iii) mode-sham outcome vocabulary verbatim per
  plan §10; (iv) two-pair identical UTC close semantics statement; (v)
  seam limb (iii) minimum-N floor 20 ⇒ NOT_RUN fail-closed. PLUS:
  plane-semantics pin with the measured diff tables, c_rt/N_diff actual
  numbers, the F-1 frozen variant set, the 16-entry arm registry with
  `arm_config_digest` hashes, dev/holdout window strings, fold table,
  cost-book tiers + census sha256s, F-5 verdicts, F-7 declaration,
  placebo recipe pin, code sha chain.
- **`trial_ledger.jsonl`** — 25 seed rows, every row labeled
  `SINGLE_SOURCE_PANEL`, `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`,
  `PAPER_TIER`; `net_pnl`/`gross_pnl` null everywhere; **no scored
  rows**. Rows: 2 data-gate (BUILD_PASS), 1 F-5 M3 kill
  (`NOT_SCORED_FALSIFIED`), 2 F-5 M1 report-only, 2 F-PIT-1
  (`PASS_PIT`), 2 F-1 disclosure, 2 mode-sham, 14 F-6 population rows.
  The seed is written exactly-once (idempotent regeneration until
  commit; the append-only law governs post-commit rows).

## 10. Tests, commands, reproduction

Test suite (32 passed, incl. the 12 new falsifier fixtures):
```
cd <worktree>/research/control/ERP1-TRACKA-COHORT-1
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/ -q
# 32 passed in ~0.8s
```
New fixtures: M-1 shift-equivalence (3 synthetic seeds), M-5 truncation
PIT, R-DAEMON hand-built panel with hand-computed partial-range
percentiles (including a genuine daemon/R-ORIG divergence case), M-4
blindness, schedule-only force-flat + no-PnL-field law, trip-cost
linearity in k, N_diff/limb3 machinery, Spearman sanity, mode-sham
marginal-preservation, family smoke, plane convention, plane semantics.

Exact commands (in execution order):
```
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/ -q
/Users/hoangminhlong/my-quantitative/.venv/bin/python scripts/build_signal_plane.py AUDUSD   # heavy-lock role falsifier-plane
/Users/hoangminhlong/my-quantitative/.venv/bin/python scripts/build_signal_plane.py USDCAD   # heavy-lock role falsifier-plane
/Users/hoangminhlong/my-quantitative/.venv/bin/python scripts/falsifier_run.py              # writes falsifier_results.json,
                                                            # freeze/GO1_freeze_artifact.json, trial_ledger.jsonl
```
Locks: two heavy-lock acquisitions (role `falsifier-plane`, one per
pair), both released FINISHED; `researchctl.py locks inspect` was
`FREE_PROVEN` at lane start.

## 11. Incidents and known limitations

Incidents:
1. **Band-index defect caught and fixed pre-freeze (self-caught).** The
   first battery run had R-ANCHOR/R-DAEMON consume the fade band from
   `ranges[d−1]` (two trading days back); plan §4.2 pins the ONE delta to
   the mode percentile index ONLY, so the band must stay
   `ranges[d][1]/[2]` (the previous day's hi/lo). Fixed in all four
   consumers (shift impl, independent impl, day-labels/truncation probe,
   daemon); the M-1 double implementation could not catch this class
   (both legs shared the misreading) — the plan-text re-read did. Battery
   re-run; all numbers in this report are post-fix.
2. **Ledger seed duplication during the development re-run** (25 rows
   appended twice): writer made exactly-once/idempotent before commit;
   the committed seed is 25 unique rows. No committed ledger existed, so
   no append-only law was violated.
3. Heavy-lock note: `build_signal_plane.py` reuses the data-gate census
   build under role `falsifier-plane`; both acquisitions released
   FINISHED, no contention.

Known limitations (all disclosed on the artifacts):
- `SINGLE_SOURCE_PANEL` (Dukascopy-only), `PAPER_TIER` ceiling,
  `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` — on every verdict/row.
- The F-1 variant set is lane-pinned (the V2 census config tables live
  in `v2_campaign.py`, outside this lane's allowed read set); 2 variants
  per family were pinned and frozen BEFORE the rho computation.
- R-DAEMON is an EMULATION pinned by this lane per the dispatch
  definition; the shadow daemon source was never read (outside the
  allowed set) and no shadow artifact is cited.
- M-5's truncated-replay definition (T0 strict day start; T1
  first-bar-closed disclosed) is pinned in the freeze artifact.
- The HOURREV family port keeps the ancestor's negative-index wrap at
  `d_i == win_days` byte-faithfully (1 day per window affected);
  disclosed in the variant set.
- The causal control rebuild (F-3 occupancy) is a scored-phase
  prerequisite — the rebuilt recipe must satisfy ALL four predicates
  before any causal-control cell runs.
- M-2's in-session denominator (07–18 UTC tradable bars, post-warmup) is
  the pinned reading of "in-session dev bars".
