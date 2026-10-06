# FXEB_K6_GATES — lane FXEB-K6, round FUTURES-K6GATE-PREP-20261004

- Lane: **FXEB-K6**. Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep`,
  branch `prep/futures-k6gate-20261004`, HEAD at start `05e5493971116eec8db5ea49e30c06930e8cc6bc`
  (= dispatch_sha, verified once via `git rev-parse HEAD`; `git status --porcelain` taken at
  start and again at end; no other git actions; nothing staged/committed by this lane).
- Class: **pre-registered 0-cost anatomy gates + diagnostics on committed data. UNCONDITIONAL
  descriptive statistics only: NO PnL, NO conditional-on-signal measurement, NO parameter or
  family changes. PB2 HOLD stands — these gates never schedule anything.**
- PREDECLARATION LAW: §0 below was written BEFORE any panel computation (only read-only
  inspection of file schemas and owning docs preceded it). Every gate/diagnostic quotes its
  owning doc's definition verbatim (file + section) and names the statistic, window,
  day-classes and thresholds; `[OPERATIONALIZED]` marks choices the owning docs left open —
  declared before compute, never tuned after results.
- Zero-fetch disclosure: **zero network fetches performed by this lane.** All inputs are
  committed files read read-only from the worktree. Root `.venv` python used read-only.
  Heavy-job lock inspected (`FREE_PROVEN`) before the heaviest single reads.
- Fees: all cost citations are the corrected tier-1 law **2.46 USD/side (FEES_CORRECTED §2,
  FX all-in tier-1)**; the 1.386-class glue numbers appear nowhere. No cost number is
  recomputed by this lane (no gate below adjudicates cost).

---

## 0. PREDECLARATION (written before compute)

### 0.1 Common session law (all missions)

- Panels (read-only): `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_cache/6e_annotated_1m.parquet`
  (3,054,311 rows) and `.../6B_cache/6b_annotated_1m.parquet` (2,549,633 rows). These carry the
  baseline lanes' DST-correct annotations: `session_date` (America/Chicago trade date, session =
  17:00 CT on D-1 → 16:00 CT on D, 60-min maintenance break) and `minute_of_day`/`minute_ct`
  (CT minute of the bar's own day), plus `segment` per each lib's declared segment table.
- Held chain: `6E_cache/held_calendar.parquet` / `6B_cache/held_calendar.parquet` — 1,746
  sessions each, `session_date` + `held` contract label. A bar belongs to a census session iff
  its `session_date` is in the held chain **and the bar is printed by that session's held
  contract** (`raw_symbol == held_calendar.held` label prefix). `[OPERATIONALIZED,
  executed as declared; see §0.7 execution note]` — the held-contract restriction is the
  owning docs' own "held chain" meaning (all baseline anatomy is computed on the held series).
- Era split [OPERATIONALIZED, pre-declared]: era-1 = session_date ≤ 2022-12-31; era-2 =
  session_date ≥ 2023-01-01 (the owning docs' K5 split, FX_HYPOTHESES §1.9/§4.9). Per-year
  rows also reported.
- Day-classes: all held sessions; Sunday-open stratum = sessions whose reopen (17:00 CT bar)
  falls on a Sunday CT calendar day (session_date is a Monday); weekday reopens = all others.
  DST-mismatch split available for 6E (`dst_mismatch` column), reported as anatomy only.

### 0.2 M1 — FX-F1 London-Range trigger census

Owning definitions, quoted verbatim:

- PB2_ANCESTRY_COURT_DRAFT.md §c2 ("Expected trigger counts — census NOT_RUN, bounds stated"):
  "**Trigger = first 1m close strictly outside R_lon in 11:00–15:30 London.** Design cap: 1
  trigger/session (first-touch; re-arm policy unspecified [PROVISIONAL]) ⇒ upper bound =
  evaluable sessions ≈ 1,573/1,572." and "**Pre-commit a minimum-census gate (suggested ≥500
  triggers/symbol [PROVISIONAL]) BEFORE any scored design is frozen** — the PB3/K0
  kill-by-thinness lesson applied prospectively."
- Same file §b1.2: "**Trigger census** (§c): the dead families' trade counts are known
  (11,459 / 3,830 anchor trades); the futures trigger density at 1m is NOT_RUN and must be
  censused first."
- Same file §b1: "PB2-H-C (London-morning range 08:00–11:00 local, 1m-close trigger
  11:00–15:30 local, hold to 16:00 CT)" — R_lon is the London 08:00–11:00 range.
- FX_HYPOTHESES.md §1.5: "**trigger = first 1m close strictly outside R_lon during 11:00–15:30
  London**; fill = open next 1m; **mandatory delay variants +1 bar and +30m**; base-EXCLUDE
  ECB GC (6E) / MPC (6B) / FOMC days, INCLUDE = sensitivity leg only; London-morning coverage
  <80% EXCLUDE (load-bearing on 6B thin k=5 windows); warmup 60d".
- FX_HYPOTHESES.md §1.7: "Census gate ≥500 triggers/symbol [PROVISIONAL] BEFORE any scored
  spec."
- FX_HYPOTHESES.md §1.4 (clock law): "LOCAL-CLOCK LAW: all bucketing Europe/London local
  (DST-proven both symbols; BoE anchor minute-720 stable)."
- FX_HYPOTHESES.md §1.9 (era law): "K5 rolling 2020-22 vs 2023-26 sign stability."

Statistic / window / day-classes / thresholds:

- R_lon per held session = `[min(low), max(high)]` of 1m bars with Europe/London local
  bar-open time in **[08:00, 11:00)** of that session's London calendar day (London date ==
  session_date). `[OPERATIONALIZED]` (docs say "range" without naming high/low aggregation;
  the strict-outside trigger makes the envelope the only reading that never under-counts).
- Trigger condition: exists a 1m bar in the same session with London local bar-open time in
  **[11:00, 15:30)** whose `close` is **strictly** > R_lon.high or **strictly** < R_lon.low.
  **Census count = number of census-eligible sessions with ≥1 such bar** (court first-touch
  cap: 1 trigger/session). Uncapped count of qualifying 1m bars also reported (NOT the gate).
- Census-eligible session (base stand-aside law, all pre-declared):
  1. session in held chain, session_date ≥ warmup end. **Warmup = first 60 held sessions
     excluded** `[OPERATIONALIZED]` (court §c1's arithmetic 1,746 − 60 − 55 − 58 = 1,573
     implies 60 *held sessions*, not 60 calendar days).
  2. NOT a base-excluded event day: 6E excludes ECB GC ∪ FOMC; 6B excludes BoE MPC ∪ FOMC.
     Date sets consumed read-only from the baseline lanes' pinned sources: ECB GC 55 dates
     (`6E_deep_lib.ECB_GC`, provenance documented there); MPC 56 in-panel dates
     (`6B_deep_lib.load_mpc_calendar()`); FOMC 58 in-panel dates (`6E_deep_lib.load_fomc()`,
     archived federalreserve.gov HTML with in-file release-time proof).
     `[OPERATIONALIZED]` FOMC set identical for both symbols; each symbol's own primary
     overlay per §1.5 wording.
  3. London-morning coverage ≥ 80%: (bars present in Europe/London 08:00–12:00) / 240 ≥ 0.80
     `[OPERATIONALIZED]` (docs say "coverage" without a denominator; 240 = 4h × 60m).
  4. Range and trigger windows each contain ≥ 1 bar (else a no-trigger session, not dropped).
- Also reported (pre-declared, descriptive): census WITHOUT event-day exclusion (quantifies
  K1's excluded days); census WITHOUT the coverage filter (reconciles to court §c1's
  ≈1,573/1,572 population). The GATE NUMBER is the base census (all four stand-asides).
- Gate verdict rule: **≥500 base triggers/symbol ⇒ census gate PASS; <500 ⇒ FAIL; session-set
  unbuildable ⇒ NOT_RUN.** The court marked ≥500 [PROVISIONAL]; exactly that number is
  adjudicated and no other.

### 0.3 M2 — FX-F4 Reopen-Gap trigger census + 6B gap-std anatomy gate

Owning definitions, quoted verbatim:

- FX_HYPOTHESES.md §4.5: "**signal = sign of (reopen first trade/close vs prior 16:00 CT
  close)** beyond a minimum-gap threshold [PROVISIONAL, e.g. ≥1×ATR(20d,1m-bar) fraction —
  exact value a registered-cycle decision, NOT tuned here]"; stand-asides: "(i) roll sessions
  and the session after a roll EXCLUDE; (ii) holiday/early-close-adjacent sessions with
  uncertain 2024-2025 schedules EXCLUDE/NOT_RUN; (iii) Sunday opens are a separate stratum
  (1.9% volume, distinct liquidity), base = weekday reopens".
- FX_HYPOTHESES.md §4.1 (baseline this gate relates to): "**reopen-gap vol is large relative
  to the day: gap std 0.3778% vs full-day return std 0.4695% (ratio 0.805, n=1,739, measured
  directly on the 23h venue — replacing v1's RTH-only proxy 0.79)**
  [`6E_a2_sessions.json: v1_gap_remeasure`]" and "6B: ... **6B gap-std anatomy NOT_RUN**
  (declared hole)."
- FX_HYPOTHESES.md §4.6 family-specific negative (c): "6B gap-std NOT_RUN ⇒ the 6B leg of
  this family carries an explicit anatomy-first gate: **measure 6B gap std before any 6B
  spec is frozen (descriptive, prep-legal)**."
- FX_HYPOTHESES.md §4.7: "Power [DERIVED, court §c3]: n ≈ 1,573/1,572 minus threshold
  thinning — if thresholding leaves n≈500 → MDE 5.80/6.88 bp ... unthresholded n→full gives
  3.27/3.88 bp."
- FX_HYPOTHESES.md §9 NOT_RUN item 2: "6B reopen-gap std anatomy (F4 6B leg) — NOT_RUN;
  anatomy-first gate declared."
- DATA_READINESS_6B.md §4: "Holiday/deviation grid: NOT_OBTAINED 0/42 windows." §10: "F4-6B
  leg gated on gap-std anatomy NOT_RUN." Dispatch law: "6B holiday grid 0/42 NOT_OBTAINED
  stands (holiday-adjacent fail-closed)."

Statistic / window / day-classes / thresholds:

- **Gap definition** `[OPERATIONALIZED]` (1m panel has no trade prints): gap_t =
  `close(reopen bar of session t) / close(last bar of held session t−1) − 1`; reopen bar =
  session's first held-chain 1m bar (17:00 CT on D-1); t−1 = immediately preceding held
  session. Sessions lacking either side are NOT_RUN cells (counted).
- **F4 census (unconditional)**: evaluable reopen events by stratum — base = weekday reopens
  excluding roll sessions AND the session after each roll (27 switches/symbol; switch dates =
  `cost_roll_events_fxeb.json → roll_remeasure.<SYM>.switches.first_session_on_new_contract`);
  Sunday stratum separate; holiday layer below. No minimum-gap threshold applied anywhere
  (§4.5 makes it a registered-cycle decision; thresholding = conditional counting).
  Census n mapped onto court §4.7 power rows descriptively — no invented pass/fail.
- **6B gap-std anatomy gate**: statistic = std of gap_t (% , sample std) over base 6B
  reopens, full + era + per-year; companion ratio gap_std / day_ret_std (day_ret = session
  close-to-close over the same evaluable set) `[OPERATIONALIZED]` replicating the 6E
  v1_gap_remeasure construction for comparability. **Verdict rule**: the owning docs declare
  NO numeric pass/fail — the pre-declared condition is *measurement itself* (anatomy-first).
  Verdict = **MEASURED** (NOT_RUN entry closes) with the holiday-grid hole carried; **no
  size threshold is invented here.** Gap SIGNS are anatomy, never direction claims.
- **Holiday layer, fail-closed** `[OPERATIONALIZED]`:
  - 6E: evidence-based exclusion from the id-58 (`6E`) schedule captures of
    `holiday_deviation_6e_6b.json` OBTAINED_DEVIATION windows: a held session is excluded iff
    its tradingDate carries an open event at ≠17:00 or a closed event at ≠16:00. Windows
    whose captures are absent from the committed tree, and INCONCLUSIVE_AGED_OUT windows:
    held sessions in [window_first_event_date, +3 calendar days] are **fail-closed NOT_RUN
    cells** (excluded from the clean set, counted in the register).
  - 6B: grid 0/42 NOT_OBTAINED ⇒ **no holiday-adjacent exclusion is implementable**; the 6B
    census/std measured with this standing hole declared. Any future 6B spec's holiday
    stand-aside stays blocked on the grid — restated in the verdict.
- Figures reported twice: with the holiday layer (gate number for 6E) and without
  (transparency). For 6B only the roll-excluded set exists (hole declared).

### 0.4 M3 — 1m anatomy for 6E/6B (session-segment structure)

Owning definitions, quoted verbatim:

- Court §c3 (the power statements this refreshes): "Method: two-sided α=0.05, power 80%
  (z = 2.80); **dispersion proxy = daily return std — 6E 0.463% (46.3 bp) [OBSERVED,
  `6E_a1_regimes.json`], 6B 0.549% (54.9 bp) [OBSERVED, 6B_v2 §1]**. The trade horizon
  (entry → 16:00 CT same day) is shorter than a full session day, so daily σ is an
  **upper-bound** dispersion proxy ⇒ tabulated MDEs are conservative (upper bounds). True
  per-trade dispersion: NOT_RUN (would require the census + descriptive per-trade return
  distribution — court input)."
- Anatomy anchors refreshed: `6E_a2_sessions.json: rv_share_by_segment` (london_morning
  16.60% of RV), `6B_a2_sessions.json: london_morning_share_07_12` (28.7% → 23.7%).
- Session-mark law: FX_HYPOTHESES §1.4 "LOCAL-CLOCK LAW: all bucketing Europe/London local";
  baseline lib: "Session/segment logic is DST-correct (America/Chicago + Europe/London via
  zoneinfo)". Sessions in America/Chicago trade dates (held chain).

Statistic / window / day-classes / thresholds:

- Per **session-segment** (each panel's annotated `segment` column — 6E = `6E_deep_lib.SEGMENTS`
  CT-minute disjoint partition; 6B = `6B_deep_lib.CITY_SEGMENTS` tz-aware labels), per year +
  2020-22/2023-26 + full: |1m close-to-close return| (count, mean/median/p90/std, bp), volume
  (mean/median/sum), bar count, bars-per-session (and nominal active share for 6E's exhaustive
  partition). Returns within held sessions from consecutive held-contract bars only.
- **London-local overlay rows** (DST law, both symbols): Europe/London-bucketed 08:00–11:00
  (F1 range), 11:00–15:30 (F1 trigger), 08:00–12:00 (coverage window) — same statistics.
- **Daily-σ refresh (deltas only, overwrite nothing)**: session close-to-close return std (%),
  full + era + per-year, compared as DELTAS to the court's recorded inputs (6E 0.4639% =
  `6E_a1_regimes.json daily_ret.std_pct`; 6B 0.5486% = `6B_a1_regimes.json
  chain_calendar.std`, the "6B_v2 §1 0.549%" input). Baseline JSONs read-only.
- Machine output: `session_anatomy_6e6b.json` (schema inside the file). No threshold, no
  gate verdict: M3's only check is the reproduction/delta of the cited inputs.

### 0.5 M4 — 6E/6B tick constancy at 2020-11-23 (R2 diagnostic D-2 step iii)

Owning definitions, quoted verbatim:

- HYPOTHESES_R2.md §5 D-2 row: "**D-2 | TICK-ERA AUDIT |** 6A era-aware cost-law audit: (i)
  recompute the 6A RT cost surface for era-1 at $10.00/tick ...; (ii) spread-proxy step test
  at 2020-11-23 on 6A vs the same-date 6J placebo; **(iii) tick-constancy checks for 6E/6B at
  the boundary (currently NOT_RUN — closes AF4's secondary control)**. Feeds every 6A
  family's cost field; prep-legal descriptive pass."
- HYPOTHESES_R2.md §3 field 6 (AF4): "**secondary negative = 6E/6B once D-2 proves their
  constancy (NOT_RUN today, declared)**." §3.10: "6E/6B tick-era constancy NOT_RUN (D-2)".
  §9 item 3: "6E/6B tick-constancy at 2020-11-23 (AF4 secondary control, D-2 step iii) —
  NOT_RUN."
- Method precedent `fx_ja/6j_identity.json → measured_increment_windows`: per sampled window —
  nonzero 1m close-to-close diffs → `min_observed_increment_int_nano`, `gcd_increments_int_nano`,
  `share_of_diffs_equal_to_min`, close-on-grid shares for candidate grids; windows used there:
  "2020-03-09..13 (AV1B backfill2)", "2023-01-09..13 (AV1R backfill)", "2026-07-06..10 (AV1T)".
- Prices are int-nano fixed point (price × 1e9; `6E_deep_lib`: "Price fixed point 1e-9").
  Declared ticks: 6E minTick 5e-05 = **50,000 int-nano** ($6.25/tick); 6B minTick 1e-04 =
  **100,000 int-nano** ($6.25/tick) (DATA_READINESS_6E/6B §1).

Statistic / windows / day-classes / thresholds:

- Sampled windows (America/Chicago trade dates, held-chain held-contract sessions): era
  samples per the 6j precedent — 2020-03-09..13, 2023-01-09..13, 2026-07-06..10 — plus the
  boundary pair **2020-11-16..20 (pre) and 2020-11-23..27 (post)**. ≥3 held sessions per
  window required, else that window is NOT_RUN (listed, never dropped silently).
- Per symbol per window: nonzero consecutive **same-session** 1m close diffs (int-nano) →
  n_diffs, min |diff|, GCD, share == GCD; close-on-grid shares for candidates (6E: 50,000 /
  25,000 / 100,000 / 10,000 int-nano; 6B: 100,000 / 50,000 / 1,000,000 / 10,000).
  `[OPERATIONALIZED]` diffs bounded within held sessions (6j precedent did not state
  session-bounding; bounding avoids roll/overnight artifacts — declared here).
- **Verdict rule (pre-declared)**: per symbol **CONSTANT at 2020-11-23** iff every sampled
  window's GCD equals the declared tick int-nano (pre == post == era samples == declared);
  **CHANGED** if pre ≠ post or any GCD ≠ declared; window-set unbuildable ⇒ NOT_RUN.
  Adjudicates D-2 step (iii) only — steps (i)/(ii) are 6A/6J lanes, not this lane's scope.

### 0.6 Standing prohibitions (binding on every section)

1. NO PnL, no expectancy, no conditional-on-signal return measurement (trigger census counts
   bars; gap statistics unconditional; M3/M4 dispersion/identity only).
2. Gap/trigger SIGNS are anatomy; no direction claim is made or implied.
3. No parameter/family changes; PB2 HOLD, F4-6B gating law and all NOT_RUNs stand unless a
   pre-declared condition above is adjudicated — and no gate here schedules anything.
4. Missing evidence = NOT_RUN, never inferred PASS; every considered-but-not-run measurement
   recorded in §6 (anti-cherry-pick).
5. Zero network fetches; fees cited only per FEES_CORRECTED (2.46 tier-1 FX); 1.386-class
   glue numbers appear nowhere.

### 0.7 Execution note (disclosed, anti-cherry-pick)

The first compute pass ran on held-session membership only and was **superseded within this
lane** when the held-contract restriction (§0.1) was applied: 1,282,448 of 3,054,311 6E rows
(469,545-of-2,549,633 for 6B) share a timestamp with a different contract, which mixed
contracts inside sessions and inflated dispersion (6E |1m ret| p90 45.8bp → 1.9bp held-only;
6E 08:30 RTH-open gap 0.4621% → 0.3773% held-only). The held-contract pass reproduces the
recorded baseline (`v1_gap_remeasure` 0.3778% vs re-derived 0.3773%, both n=1,739) and the
recorded daily σ (§3), so it is the faithful panel reading. First-pass numbers (6E trig
1,447 / 6B 1,510; 6E gap-std 0.2078% / 6B 0.0873%) are recorded here for completeness and
are NOT used by any verdict; every reported number below is from the held-contract pass.

---

## 1. M1 results — FX-F1 London-Range trigger census

Event-day sets (in-panel): 6E excluded 113 union dates (ECB 55 + FOMC 58, no overlap);
6B excluded 112 union dates (MPC 56 + FOMC 58, 2 overlap). Warmup end 2020-03-25 (first 60
held sessions). Note on the court's arithmetic: court §c1's ≈1,573/1,572 double-counts the
warmup∩event-day overlap (6 dates/symbol sit in both sets) and omits the coverage filter;
exact populations are reported below — the discrepancy is disclosed, not reconciled away.

| census variant | 6E eligible | 6E triggered (capped) | 6E uncapped bars | 6B eligible | 6B triggered (capped) | 6B uncapped bars |
|---|---|---|---|---|---|---|
| **BASE (all stand-asides) — GATE NUMBER** | **1,484** | **1,362** | 148,501 | **1,440** | **1,342** | 147,343 |
| without event-day exclusion | 1,588 | 1,459 | 160,343 | 1,546 | 1,444 | 160,759 |
| without coverage filter | 1,579 | 1,453 | 156,315 | 1,580 | 1,473 | 156,305 |
| warmup only | 1,686 | 1,553 | 168,479 | 1,686 | 1,575 | 169,721 |

Base per-era (triggered, capped): 6E 565 (2020-22) / 797 (2023-26); 6B 567 / 775.
Base per-year (eligible/triggered): 6E 2020 175/160, 2021 229/206, 2022 224/199, 2023 224/213,
2024 231/217, 2025 228/210, 2026 173/157. 6B 2020 171/157, 2021 224/203, 2022 221/207,
2023 219/202, 2024 222/213, 2025 219/203, 2026 164/157. (Full machine table:
`fx_f1_f4_census.json`.)

Diagnostics: sessions with empty range window 2 (each symbol); empty trigger window 1;
coverage <80% sessions 6E 102 / 6B 146 (the coverage stand-aside binds on 6B as the owning
docs predicted — "load-bearing on 6B thin k=5 windows"); median coverage 1.00 both;
min R_lon width 6E 7.0e-4 int-px (0.0007) / 6B 5.0e-4; stray rows (not held-session or not
held-contract) 6E 802,223 / 6B 470,728.

Court-power mapping [DERIVED from the court's own §c3 formula, descriptive only]: at
n=1,362 (6E), MDE = 2.80 × 46.3bp/√1,362 ≈ **3.5 bp/trade**; at n=1,342 (6B), 2.80 ×
54.9/√1,342 ≈ **4.2 bp/trade** — versus the court's thin-census warning threshold ("if
first-touch frequency < ~1/3 of sessions (n < ~500/symbol), per-symbol MDE rises above
~6 bp ... the court is underpowered by thinness"). Neither symbol triggers the thinness
condition. Cost reading [descriptive, court §b4/FEES tier-1 2.46 USD/side corrected]:
6E MDE ≈3.5bp sits at/below the modeled RT 3.6–6.3bp; 6B ≈4.2bp sits below the modeled RT
6.3–11.2bp — the court's own "power floor and cost floor coincide" finding is the frame;
no profitability inference is drawn here.

## 2. M2 results — FX-F4 reopen-gap census + 6B gap-std gate

**F4 reopen-gap census (§4.5 definition: 17:00 CT reopen close vs prior 16:00 CT close;
roll + after-roll excluded; holiday layer per §0.3):**

| stratum | 6E n | 6E gap std | 6B n | 6B gap std |
|---|---|---|---|---|
| BASE weekday reopens (gate population) | 1,282 | **0.0304%** | 1,283 | **0.0400%** |
| BASE Sunday stratum | 317 | 0.1545% | 317 | 0.1616% |
| BASE all pairs | 1,599 | 0.0741% | 1,600 | 0.0804% |
| no-exclusions all pairs (transparency) | 1,745 | — | 1,745 | — |

Base by era (weekday): 6E 0.0281% (2020-22) / 0.0322% (2023-26); 6B 0.0486% / 0.0306% —
6B's weekday reopen-gap dispersion roughly **fell by a third** across eras while 6E's rose
slightly (anatomy only). Weekday gap distribution (6E): p05 −0.034%, p50 0.000%, p95
+0.031%, min −0.541%, max +0.241%; 6B: p05 −0.045%, p50 0.000%, p95 +0.044%, min −0.420%,
max +0.281%. Gap SIGNS are anatomy, not direction claims. Sunday sessions in the held
chain: 348 (both symbols — matches the owning docs' 348); the base keeps 317 after the
§4.5 roll/holiday stand-asides (31 Monday sessions excluded, register §6).

Companion day-return std over the same evaluable set: 6E 0.4637%, 6B 0.5513% ⇒ **ratio
gap_std/day_ret_std = 0.160 (6E) / 0.146 (6B)** — versus the court-cited baseline ratio
0.805 (see finding below).

**6B gap-std anatomy gate verdict: MEASURED.** The pre-declared condition (§0.3) was the
measurement itself — no numeric pass/fail exists in any owning doc and none is invented.
6B reopen-gap std: weekday base 0.0400% (n=1,283; era 0.0486% → 0.0306%), all-pairs
0.0804% (n=1,600). The FX_HYPOTHESES §9 NOT_RUN item 2 ("6B reopen-gap std anatomy ...
NOT_RUN") closes at the measurement level; the **6B holiday-grid hole (0/42 NOT_OBTAINED)
stands** — holiday-adjacent exclusions are not implementable for 6B, so any future 6B F4
spec's stand-aside (ii) remains blocked on that grid, and the 6B leg remains gated exactly
as before at the spec level. PB2/PB3 HOLD unaffected.

**Baseline-labeling finding (recorded, nothing overwritten):** FX_HYPOTHESES §4.1 presents
"gap std 0.3778% vs full-day return std 0.4695% (ratio 0.805, n=1,739)" as the *reopen-gap*
baseline citing `6E_a2_sessions.json: v1_gap_remeasure`, but the generating script
(`6E_a2_sessions.py`) computes `rth_open_gap` = **first 08:30-CT bar close vs prior session
close** — the RTH-open gap, not F4's 17:00-CT reopen gap. Re-derived here per the exact
baseline method on the held-contract chain: **0.3773% (n=1,739)** 6E — reproduces the
recorded 0.3778% (n=1,739) to the 4th decimal; 6B same method 0.4286% (n=1,695; no 6B
baseline was recorded). Consequence: **the true F4 17:00-reopen gap (6E 0.0741% all-pairs,
ratio 0.16) is 2.3–5× smaller than the number the owning docs carried as the reopen-gap
anatomy, and the "gap vol is large relative to the day" statement (ratio 0.805) does not
carry over to the actual F4 gap.** This is anatomy, not a family verdict — no §4 refutation
condition is adjudicated by this lane (they are return-conditional and out of scope).

NOT_RUN cells (holiday layer, 6E): 1 evidence-based deviation session excluded
(2023-11-24 early close — the only committed id-58 OBTAINED capture showing deviant held
hours); 93 fail-closed neighborhood cells excluded across 37 windows (5 OBTAINED windows
have committed captures — 2023-09-03, 2023-11-22, 2023-12-24, 2023-12-31, 2025-08-31 —
the other 29 OBTAINED + 8 aged-out windows' captures are absent from the committed tree ⇒
their deviant-session identification is NOT_RUN here, neighborhoods fail-closed excluded).
6B: zero exclusions possible (0/42) — hole declared, not cells.

## 3. M3 results — 1m session-segment anatomy

Machine artifact: `session_anatomy_6e6b.json` (full per-segment × per-year × era tables for
both symbols + London-local overlays — the table the future D5/power tables consume).
Headlines (full era, held-contract chain):

- Daily-σ refresh (deltas only): 6E session close-to-close std **0.4685%** vs court input
  0.4639% (**Δ +0.46bp, +1.0%**); 6B **0.5454%** vs court input 0.5486% (**Δ −0.32bp,
  −0.6%**). Per-year and era rows in the JSON. Nothing overwritten; the court's MDE table
  remains computable from its recorded inputs within ~1%.
- London-local 08:00–11:00 (F1 range window), full era: 6E n_bars 304,846, |1m ret| mean
  1.046bp / median 0.853 / p90 2.294 / std 1.096, vol mean 148.5; 6B n_bars 295,632, mean
  1.246bp / median 0.793 / p90 2.862 / std 1.345, vol mean 80.6. London 11:00–15:30 and
  08:00–12:00 rows in the JSON.
- Segment structure, full era, |1m ret| mean bp / volume mean (valid returns only; NaN
  session-start bars reported per segment in the JSON: 6E evening_open 1,744, asia_evening 1;
  6B asia_early 1,739, asia_core 6). 6E CT partition: evening_open 0.534/31.8;
  asia_evening 0.586/37.3; asia_morning 0.772/75.2; london_morning 1.049/148.3;
  london_midday 0.896/116.4; ecb_usdata_window 1.217/213.8; pre_rth 1.320/237.6;
  rth_first_hour 1.446/295.7; us_morning_late 1.081/203.1; us_midday 0.787/104.8;
  fomc_window 0.767/119.5; afternoon_close 0.593/66.1. 6B tz-aware segments:
  asia_early 0.677/18.4; asia_core 0.723/20.6; lon_pre_boe 1.216/77.3;
  lon_us_overlap 1.363/104.1; us_rth 1.138/92.8; us_close 0.673/27.5;
  other 1.075/54.2. (The annotated 6B `segment` column carries no separate `boe_release`
  label — those minutes fall where the baseline annotation placed them; the JSON reports
  what exists, nothing is re-segmented.) Per-year and era splits: see JSON. (These refresh,not replace, the
  baseline `rv_share_by_segment` views — the baseline files are untouched.)
- London-local trigger window 11:00–15:30 (F1 trigger window), full era: 6E n_bars 460,774,
  |1m ret| mean 1.179bp / p90 2.582, vol mean 204.2; 6B n_bars 447,453, mean 1.378bp /
  p90 3.070, vol mean 106.6.

## 4. M4 results — tick constancy at 2020-11-23 (D-2 step iii)

Machine artifact: `tick_constancy_6e6b.json`. All five sampled windows had 5 held sessions
each (≥3 required). Increment GCD per window (int-nano, price × 1e9):

| window | 6E GCD | 6E min diff | 6B GCD | 6B min diff |
|---|---|---|---|---|
| 2020-03-09..13 (era sample) | 50,000 | 50,000 | 100,000 | 100,000 |
| 2020-11-16..20 (pre-boundary) | 50,000 | 50,000 | 100,000 | 100,000 |
| 2020-11-23..27 (post-boundary) | 50,000 | 50,000 | 100,000 | 100,000 |
| 2023-01-09..13 (era sample) | 50,000 | 50,000 | 100,000 | 100,000 |
| 2026-07-06..10 (era sample) | 50,000 | 50,000 | 100,000 | 100,000 |

- 6E n_diffs per window 4,764–5,886; 6B 3,820–5,044. Close-on-grid shares (declared grid)
  1.0 in every window for both symbols; alternative-grid shares in the JSON (e.g. 6E 2.5e-05
  grid ≈50% fails, mirroring the 6J precedent's rejected alternatives).
- **Verdict: 6E CONSTANT; 6B CONSTANT at 2020-11-23.** GCD == min-observed-increment ==
  declared tick in every sampled set on both sides of the boundary and across all three era
  samples. This **closes R2 §9 NOT_RUN item 3 / D-2 step (iii)** and proves AF4's secondary
  negative control: 6E and 6B are unchanged-tick placebo legs for the 6A tick regime — the
  2020-11-23 grid change is 6A-specific on the FX complex, consistent with the 6J same-date
  placebo framing. D-2 steps (i)/(ii) remain NOT_RUN (6A/6J lanes).

## 5. Verdict table

| # | gate / diagnostic (owning definition) | pre-declared condition | 6E | 6B | verdict |
|---|---|---|---|---|---|
| M1 | FX-F1 trigger census (court §c2 + FX_HYP §1.5/1.7) | ≥500 base triggers/symbol [PROVISIONAL] | 1,362 (eligible 1,484) | 1,342 (eligible 1,440) | **PASS both** — thinness condition (n<500) not triggered; schedules nothing; PB2 HOLD stands |
| M2a | FX-F4 reopen-gap census (FX_HYP §4.5) | unconditional count, no threshold | weekday base n=1,282; Sunday 317 | weekday base n=1,283; Sunday 317 | **MEASURED** — n lands in the court §4.7 "full-n" MDE class (3.27/3.88bp row) before any threshold thinning; threshold thinning NOT_RUN |
| M2b | 6B gap-std anatomy-first gate (FX_HYP §4.6c, §9 item 2) | measurement itself (no numeric threshold exists; none invented) | gap std weekday 0.0304% / all 0.0741% | gap std weekday 0.0400% / all 0.0804%; ratio 0.146 | **6B MEASURED** (NOT_RUN register closes at measurement level); 6B holiday-grid hole 0/42 stands — spec-level gating unchanged |
| M2c | baseline reconciliation (FX_HYP §4.1 cite vs its generator) | descriptive reproduction | re-derived 0.3773% (n=1,739) vs recorded 0.3778% (n=1,739) — reproduces | 0.4286% (n=1,695), no baseline recorded | **FINDING**: the recorded "reopen-gap" baseline is the 08:30-CT RTH-open gap; the true 17:00-reopen gap std is 2.3–5× smaller (ratio 0.16 vs cited 0.805) |
| M3 | 1m session-segment anatomy (court §c3 dispersion inputs) | reproduce/delta the cited inputs, overwrite nothing | daily σ 0.4685% (Δ +0.0046pp vs 0.4639%) | daily σ 0.5454% (Δ −0.0032pp vs 0.5486%) | **DELIVERED** (machine JSON emitted); court MDE inputs reproduce within ~1% |
| M4 | 6E/6B tick constancy 2020-11-23 (R2 §5 D-2 iii, AF4 field 6) | GCD == declared tick on both sides + era samples | GCD 50,000 int-nano all 5 windows | GCD 100,000 int-nano all 5 windows | **CONSTANT both** — D-2 step (iii) closed; AF4 secondary control proved (6A-only boundary confirmed) |

Every verdict above adjudicates ONLY its pre-declared condition. No gate here lifts PB2/PB3
HOLD, registers, scores, schedules, or changes any family or parameter.

## 6. NOT_RUN register + considered-and-not-run (anti-cherry-pick)

1. **Court §b1.1 1m trigger-time anatomy** (volume / |1m ret| / RV at trigger minutes vs
   matched non-trigger minutes) — considered, NOT_RUN: not in this lane's dispatch; it is
   conditional-on-trigger-minute measurement (borderline the unconditional-only law) and was
   not pre-declared. Remains the court's next census input.
2. **Per-trade dispersion for F1/F4** (court §c3 "true per-trade dispersion ... court
   input") — considered, NOT_RUN: requires conditional-on-trigger returns; forbidden here.
3. **F4 threshold-thinned census** (§4.5 minimum-gap threshold × ATR(20d)) — considered,
   NOT_RUN: threshold is a registered-cycle decision by the owning text; thresholding would
   make the census conditional.
4. **D-2 steps (i)/(ii)** (6A era-1 cost table at $10.00/tick; 6A-vs-6J spread-proxy step
   test) — NOT_RUN: 6A/6J lanes' scope, not FXEB-K6.
5. **6B holiday-adjacent exclusion** — NOT_OBTAINED (grid 0/42); carried as the standing 6B
   hole (unchanged by this lane).
6. **6E deviant-session identification for 29 of 34 OBTAINED holiday windows** — NOT_RUN:
   their id-58 capture files are absent from the committed tree; neighborhoods fail-closed
   excluded instead (93 cells), never counted as clean.
7. **FX official holiday times 2024-2025** — inherited NOT_OBTAINED (FXCAL §2); unchanged.
8. **F1/F4 INCLUDE-sensitivity legs as gates** — event-day-included census counts ARE
   reported descriptively (§1 table) but adjudicate nothing (base = EXCLUDE per §1.5).
9. **F1 co-occurrence diagnostic (court §b1.3), exit-horizon decomposition (§b1.4), F4
   DST-mismatch and 2022-Monday-halt strata as verdicts** — considered, NOT_RUN: not in this
   lane's dispatch; anatomy columns to support them are in the machine JSONs.
10. **BBO / execution realism; fee account verification (A7)** — inherited NOT_RUN
    everywhere (D5); untouched. All costs remain MODELED / UNDER REVIEW; FEES_CORRECTED
    tier-1 2.46 USD/side is the only fee number cited.
11. **6E ECU26/ECZ26 expiry cells; 6B 2023Q1–2024Q2 expiry cells** — inherited
    NOT_OBTAINED; no M above touches expiry timing.

## 7. Zero-PnL statement

Every statistic in this document and its machine mirrors is an unconditional descriptive
measure of committed data: bar counts, trigger-session counts, unconditional gap
distributions, |1m return| dispersion, volume, and price-increment GCDs. **No PnL, no
expectancy, no return conditional on any signal/threshold/sign was computed anywhere; no
position, order, parameter, family, trial, registration or schedule was created or changed;
no network was touched; no ledger/registry was written; PB2 HOLD and PB3 PARK stand; all
fees cited are MODELED per FEES_CORRECTED (tier-1 2.46 USD/side) and UNDER REVIEW until a
new A7.** Missing evidence is NOT_RUN, never inferred PASS.

— End FXEB_K6_GATES. Lane FXEB-K6, 2026-10-04.
