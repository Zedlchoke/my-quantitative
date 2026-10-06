# FXJA_K6_GATES — lane FXJA-K6, round FUTURES-K6GATE-PREP-20261004

- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep`
  @ HEAD `05e5493971116eec8db5ea49e30c06930e8cc6bc` (== dispatch base_sha, the
  one permitted `git rev-parse HEAD`), branch `prep/futures-k6gate-20261004`.
- Class: **unconditional descriptive statistics + cost arithmetic ONLY.** No
  PnL, no conditional-on-signal measurement, no parameter/family changes, no
  registration, no scored runs, no network (zero fetches, disclosed).
- Cost law binding every dollar figure: **FEES_CORRECTED** (FX tier T1 2.46 /
  T2 2.26 / T3 2.06 / T4 1.86 USD/side; MODELED_COST /
  VERIFIED_VS_ACCOUNT=NOT_RUN) as corrected by **COST_FREEZE_ERRATUM**
  (correction of record; 1.386-class glue never consumable; no silent D3
  default). Forbidden words "measured cost", "complete cost" enforced by scan.
- **PB3 (6A) PARK stands** (contingency only, gates never schedule). **D8
  unratified**: the 6A tick-era boundary stays a PROVISIONAL data-side label
  (`6a_tick_adjudication.json`, official rulebook BLOCKED_TRANSPORT); the D-2
  audit below FEEDS the D8 decision and decides nothing. **D9 unratified.**
- Interpreter: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`
  (read-only). Parquet discipline: single-shot reads, aggregate then release.
  Machine-wide one-heavy-job law: lock-free FX work (no NQ rebuild this lane);
  `researchctl.py locks inspect` consulted before the largest read.

---

## §0 PREDECLARATION (written BEFORE compute; owning definitions quoted verbatim)

This section was fully written and saved before the first statistic was
computed. Every verdict below adjudicates ONLY these pre-declared conditions.

### §0.1 Sources of record consumed (read-only)

| file | role |
|---|---|
| `FUTURES-OVERNIGHT-PREP-20261003/hypo/6j_6a/JPY_AUD_HYPOTHESES.md` | JF1 (M1 owning doc: fields 3, 5, 7-K3) |
| `FUTURES-SIX-ADOPT-PREP-20261004/hypo/HYPOTHESES_R2.md` | RMM §2 (field 3 mode law) + §5 D-1, D-2 (M2/M3 owning doc) |
| `FUTURES-SIX-READINESS-20261004/fx_ja/` | `6a_roll_measured.json`, `6a_tick_adjudication.json`, `6j_identity.json`, `6j_cease_guard_2022.json`, `ja_event_pit.json`, `DATA_READINESS_6J/6A.md` |
| `FUTURES-SIX-READINESS-20261004/fx_eb/cost_roll_events/cost_roll_events_fxeb.json` | `roll_remeasure.6E/6B` committed switch tables (M2 cross-check) |
| `FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/source/FEES_CORRECTED.md` | fee tier table §2 |
| `FUTURES-SIX-SCORED-GATE-PREP-20261004/synth/COST_FREEZE_ERRATUM.md` | cost correction of record |
| `FUTURES-DATACONTRACT-QUAL-V1/DATACONTRACT_QUALIFICATION.md` §1.7 | cost authority table (spread close-proxy 20d USD: 6E/6B 18.75/18.75, 6A 20, 6J 25; BBO NOT_RUN) |
| `FUTURES-DEEPRESEARCH-V2-20261003/analysis/` (sibling prep worktree, read-only; the exact paths `cost_roll_events_fxeb.json` itself cites) | `6J_cache/{6j_annotated_1m.parquet, held_volume_k5.parquet, contract_registry.json}`, `6E_cache/{6e_annotated_1m.parquet, contract_registry.json}`, `6B_cache/{6b_annotated_1m.parquet}`, `6A_cache/registry.parquet`, `6J_a4_events.json` (54 MPM dates), `6J_a2_sessions.json`, `6A_a2_sessions.json` |
| raw vendor panels `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/{AV1B-O1M-6A-BACKFILL2, AV1R-O1M-6A-BACKFILL, AV1T-O1M-6A}` | 6A 1m panel (no annotated 6A cache exists) |

### §0.2 M1 — JF1 K3 anchor-robustness anatomy (6J)

Owning definition, quoted verbatim (JPY_AUD_HYPOTHESES.md, PART I §1 JF1,
field 7, third bullet):

> **K3 (window-artifact)**: if the effect vanishes when the anchor moves ±45
> min within the 12:00–15:30 JST window (no minute-stamped release exists —
> the anchor-robustness test is the substitute), it is a bucketing artifact.

and field 3 (anchor nature):

> The 12:00–15:30 JST "decision window" is a **window convention** — the
> Tokyo-afternoon block where decisions are known to land, measured via
> range-share concentration (13.4% vs 10.3%), NOT a minute-anchored release
> like FOMC's "For release at".

Pre-declared measurement (anatomy only; the K3 *kill* itself requires the
conditional scored effect and is explicitly NOT computable here):

- Panel: `6j_annotated_1m.parquet` (2,843,938 rows = the panel of record,
  DATA_READINESS_6J Dim 2), held chain = `6J_cache/held_volume_k5.parquet`
  (baseline k=5 chain of record, 1,746 sessions; disclosed: on 2022-09-20 the
  baseline chain holds ceased U2 with zero bars — that session enters no
  within-session statistic; cease-guard chain is RMM's chain, not this
  anatomy's).
- Window clock: **Asia/Tokyo local time via zoneinfo** (JF1 field 4 local-
  clock law), half-open interval [start, end) by time-of-day, mapped to the
  CT `session_date` of the bars (Tokyo afternoon D lands wholly inside CT
  session D).
- Variants: **primary** W−45 = 11:15–14:45, W0 = 12:00–15:30 (convention),
  W+45 = 12:45–16:15 (the K3 ±45-min law); **secondary ladder, all reported,
  none selectable**: −30, −15, +15, +30 min shifts of the convention (same
  210-min length).
- Strata: (a) the **54 BoJ MPM dates** (`6J_a4_events.json:boj_mpm_days`,
  dates FACT from the in-corpus statement archive — stamps NOT_IN_CORPUS,
  stamps NOT_IN_CORPUS stands, no BoJ-stamp inference); (b) **all sessions**
  with ≥1 convention-window bar.
- Statistics per (variant × stratum): n sessions; median/mean/p90 of
  within-window 1m |close-to-close ret| in bp (held contract, within-session
  pairs); window volume share of session (%); window range share of session
  (%) = (window high − window low)/(session high − session low) on the held
  contract; median window bars/session. Baseline convention values on record
  for delta: mpm range-share median 13.43% vs all-days 10.35% (JPY_AUD f1;
  `6J_a4_events.json:boj_mpm_vs_alldays`).
- **Verdict condition [pre-declared]**: this lane DELIVERS the K3 anatomy
  material and reports ALL variants (anti-cherry-pick). The descriptive K3
  observation adjudicates exactly one condition — **K3-ANATOMY: the
  convention window's concentration lead over its ±45-min neighbors**
  (range-share and volume-share medians, W0 vs max(W−45, W+45), on MPM days
  and on all sessions). If W0's lead over both ±45 shifts is < 0.5 pp on MPM
  days, the convention's concentration is anchor-insensitive at ±45 min
  (reported as `ANCHOR_INSENSITIVE_AT_45MIN`); if ≥ 0.5 pp,
  `ANCHOR_SENSITIVE_AT_45MIN`. **No vanishing-effect claim is possible here**
  (the "effect" is the scored conditional; its K3 kill remains with the
  scored cycle — recorded NOT_RUN, never inferred).

### §0.3 M2 — RMM D-1 mode ledger (6E/6B/6J; 6A cited)

Owning definitions, quoted verbatim:

HYPOTHESES_R2.md §2 RMM field 3:

> mode label = strict-past classification from the measured old-contract
> last-bars session vs the k=5 crossover trigger, decided at close t,
> effective t+1

HYPOTHESES_R2.md §5 D-1 (design):

> Cross-symbol migration-mode synchronization: derive per-roll mode (abrupt=
> cease-guard-triggered vs gradual=crossover) for all five measured roll sets
> (6E/6B/6J/6A 27 each + NQ 66 v3) from committed switch tables; test whether
> abrupt mode clusters on the same calendar weeks across symbols
> (market-wide liquidity events, e.g. crisis-adjacent quarters) vs
> symbol-local contract-specific OI dynamics. Placebo: block-shuffled mode
> calendars ≥100 seeds; null = symbol-local.

Pre-declared operationalization [OPERATIONALIZED choices marked]:

- Per symbol 6E/6B/6J: build the wide session×contract volume table from the
  committed annotated 1m caches (contract identity via each cache's
  `contract_registry.json` instrument_ids map; 6B quarterly map from
  `6b_annotated_1m.parquet` non-null (instrument_id, contract) pairs — 32
  quarterly iids; coverage disclosed). Then run BOTH committed algorithms
  verbatim (as in `6a_roll_measure.py`): (a) `fx_ja_lib.k5_chain` baseline
  k=5; (b) the explicit cease-guard variant whose per-roll `trigger` is
  `cease_guard_no_bars` (→ mode **abrupt**) or `k5_crossover` (→ mode
  **gradual**).
- Cross-check (pre-declared validity condition): derived baseline switch
  dates must equal the committed switch tables — 6E/6B vs
  `cost_roll_events_fxeb.json:roll_remeasure.<sym>.switches[]
  .first_session_on_new_contract` (27 each); 6J vs `6J_cache/
  held_volume_k5.parquet` held-chain transitions (27; the 2022-09-20
  cease-guard exemplar per `6j_cease_guard_2022.json` must reproduce as
  abrupt). ANY divergence is itemized in the ledger, never normalized.
- 6A: **cited, not redone** — `6a_roll_measured.json:
  k5_cease_guard_variant.rolls[].trigger` (21 cease_guard_no_bars / 6
  k5_crossover of 27).
- Deliverable: `rmm_mode_ledger.json` — per symbol per roll: switch_session,
  from/to contracts, trigger, mode label, evidence citations.
- **CEASE-SYNC descriptive pass [pre-declared boundary]**: ISO-week
  (Monday-based) of each abrupt switch; observed cross-symbol coincidence
  table — number of ISO weeks with k symbols in abrupt state simultaneously
  (k = 1..4), the member lists of every ≥2-symbol week, plus a ±1-ISO-week
  tolerance variant. 6A enters from its committed ledger. **Descriptive
  ONLY: the block-shuffle placebo (≥100 seeds) is a FUTURE scored-side
  control — NOT_RUN here; no clustering-vs-symbol-local verdict is issued
  from this lane** (that null test is pre-registered to the scored cycle).
- **NQ leg**: considered and NOT_RUN here — the dispatch assigns this lane
  6E/6B/6J (+6A cited); NQ 66-roll v3 mode derivation belongs to the NQ
  lane (recorded in the NOT_RUN register, anti-cherry-pick).

### §0.4 M3 — 6A D-2 tick-era audit (steps i + ii; iii is the FXEB lane's)

Owning definition, quoted verbatim (HYPOTHESES_R2.md §5 D-2):

> 6A era-aware cost-law audit: (i) recompute the 6A RT cost surface for
> era-1 at $10.00/tick (spread proxy and tick components double; deliver the
> corrected table so no 6A spec ever pools across the boundary silently);
> (ii) spread-proxy step test at 2020-11-23 on 6A vs the same-date 6J
> placebo; (iii) tick-constancy checks for 6E/6B at the boundary (currently
> NOT_RUN — closes AF4's secondary control).

Era law (quoted from `6a_tick_adjudication.json:adjudication`): era-1
2020-01-02..2020-11-20 traded grid 1e-04 = **$10.00/tick**; era-2 from
2020-11-23 grid 5e-05 = **$5.00/tick**; label stays data-side PROVISIONAL
(D8 unratified).

**(i) Era-1 MODELED cost surface** — pure arithmetic from named inputs:

- fee tiers T1 2.46 / T2 2.26 / T3 2.06 / T4 1.86 USD/side
  (FEES_CORRECTED §2, FX row);
- spread close-proxy era-2 $20.00/side = 4 ticks × $5.00 (DC §1.7 6A
  column); era-1 equivalent [OPERATIONALIZED per the D-2 text "spread proxy
  and tick components double"] = 4 ticks × $10.00 = **$40.00/side**;
- slippage tiers {1, 2, 3} ticks/side: era-1 $10.00 / $20.00 / $30.00 per
  side (vs era-2 $5 / $10 / $15);
- RT = 2 × (fee + spread + slippage); bp = RT / notional × 10⁴;
  notional = 100,000 AUD × representative price. Era-2 reference of record:
  RT T1 1-tick $54.92 = 8.2 bp @ 0.6696 (DATA_READINESS_6A Dim 6).
- Representative era-1 price [OPERATIONALIZED]: median of held-chain session
  closes over era-1 (primary), plus the final era-1 session close
  (sensitivity) — both measured from the 6A panel.
- Labels on every cell: **MODELED COST / UNDER REVIEW /
  VERIFIED_VS_ACCOUNT=NOT_RUN**. The words "measured cost" and "complete
  cost" are FORBIDDEN and scanned-for. No D3 default language anywhere.

**(ii) Spread-proxy step test at 2020-11-23** [OPERATIONALIZED]:

- Per session, on each symbol's held chain (6A: cease-guard chain re-derived
  and cross-checked against `6a_roll_measured.json` — both variants' 27
  switch dates must reproduce exactly; 6J: baseline k=5 chain of record):
  **proxy_s = median over within-session consecutive 1m bar pairs of
  |Δclose| (USD price units)**, the unconditional close-to-close micro
  measure, reported raw and in ticks of the prevailing grid (÷10⁻⁴ era-1
  6A, ÷5×10⁻⁵ era-2 6A, ÷5×10⁻⁷ 6J).
- Boundary window: the 10 held sessions immediately before the boundary
  (ending 2020-11-20) and the 10 immediately after (starting 2020-11-23) —
  same calendar dates for 6A and 6J (same-date placebo law, AF4 field 6:
  "the same-date anatomy continuity on unchanged-tick 6J"); additionally the
  20-session trailing medians through 2020-12-31 shown as a series.
- Step statistic [pre-declared]: ratio (post-10 median proxy_s)/(pre-10
  median proxy_s) in USD, for 6A and 6J; plus the same ratio in TICK units.
  Descriptive comparison only — **no directional claims, no significance
  test** (n=10 vs 10; a test would be theater at this n and is NOT_RUN by
  construction).
- Step (iii) 6E/6B tick constancy: **NOT RUN — FXEB lane's** (recorded
  considered-and-not-run here; no duplication).

### §0.5 M4 — 6J/6A session dispersion refresh (unconditional)

- Statistic per held-chain session (held contract bars only, within-session
  close-to-close 1m pairs): n_bars, held volume sum, session close, median /
  mean / p90 of |1m ret| (bp), std of 1m ret (bp, the D5/power feed),
  session |ret| sum (bp). Panel-wide (all-contract) session volume recorded
  as a secondary field (6J 0.455× volume-definition gap law: shares/ratios
  only, never absolute levels).
- 6J: full committed panel (2,843,938 bars; baseline k=5 chain of record;
  2022-09-20 enters no held-bar statistic — disclosed). 6A: full committed
  panel, **era-aware split mandatory**: era-1 = sessions ≤ 2020-11-20
  (231 sessions, **descriptive-only stratum per the K3-thin law** — JF1 f7
  n-honesty: "any fold structure ... will fail a ≥5-per-fold floor —
  pre-declared, the subset may only ever be a descriptive view"), era-2 =
  sessions ≥ 2020-11-23. 6A held chain = cease-guard variant (0 violations;
  the chain the RMM field-4 law binds), re-derived + cross-checked.
- Prior committed dispersion inputs cited and delta-compared where a
  directly comparable statistic exists: `6A_a2_sessions.json:
  mean_abs_1m_ret_by_ct_hour_bp` (era buckets 2020-2021 / 2022-2023 /
  2024-2026-09) and `6J_a2_sessions.json` (eras/boj_decision_window blocks).
  Deltas are reported; **nothing overwritten** (all outputs are new files in
  this round's fx_ja/).
- Machine output: `session_dispersion_6j6a.json` (per-symbol per-era
  per-session rows + era aggregates) — the D5/power-consumable table.

### §0.6 Anti-cherry-pick / NOT_RUN law

Every measurement considered and not run is recorded with its reason in §4
(NOT_RUN register) of this file. All computed results are reported including
unfavorable/inconclusive ones. No result may create, kill, or re-parameterize
a family; verdicts adjudicate only the §0.2–§0.5 pre-declared conditions.

### §0.7 Zero-PnL statement

Every statistic in this lane is an unconditional descriptive of price
dispersion, volume, bar counts, roll mechanics, or arithmetic on named cost
inputs. No signal is defined, no position is constructed, no conditional
return is measured, no expectancy/PnL number exists in any output.

---

## §1 M1 — JF1 K3 anchor-robustness anatomy (6J)

Artifact: `jf1_k3_anchor.json` (schema `jf1_k3_anchor@1`). All seven variants
reported (anti-cherry-pick; primary = ±45 per the K3 law, secondary ladder =
±30/±15, none selected).

Median per-variant anatomy, **MPM days (n=54)** | **all sessions** (held k=5
chain; range share = window range / session range, held contract):

| variant (JST) | range% MPM | vol% MPM | median |1m ret| bp MPM | bars MPM | range% ALL | vol% ALL | |1m ret| bp ALL |
|---|---|---|---|---|---|---|---|
| W−45 11:15–14:45 | 44.45 | 12.67 | 0.77 | 209 | 26.89 | 7.92 | 0.70 |
| W−30 11:30–15:00 | 44.71 | 13.57 | 0.77 | 209 | 26.95 | 8.02 | 0.70 |
| W−15 11:45–15:15 | 43.31 | 13.59 | 0.77 | 209 | 28.12 | 8.50 | 0.70 |
| **W0 12:00–15:30 (convention)** | **34.66** | **10.84** | **0.77** | **210** | **28.57** | **8.70** | **0.71** |
| W+15 12:15–15:45 | 37.71 | 13.05 | 0.78 | 210 | 29.36 | 9.03 | 0.71 |
| W+30 12:30–16:00 | 38.39 | 13.85 | 0.78 | 210 | 29.91 | 9.30 | 0.71 |
| W+45 12:45–16:15 | 41.03 | 14.82 | 0.78 | 210 | 32.06 | 10.18 | 0.71 |

Pre-declared K3-ANATOMY condition (§0.2): W0 lead over best(±45) on MPM-day
range share = 34.66 − 44.45 = **−9.78 pp** (< 0.5 pp threshold) →
**ANCHOR_INSENSITIVE_AT_45MIN**. Companion leads: MPM volume share −3.99 pp;
all-sessions range −3.48 pp; all-sessions volume −1.48 pp. Median in-window
|1m ret| is flat across all seven variants (0.77–0.78 bp MPM; 0.70–0.71 bp
ALL). The Tokyo-afternoon concentration is a BLOCK property, not a property
of the convention's exact bounds — no 210-min slice of that afternoon is
anatomically special.

**Level reconciliation (disclosed)**: this lane's W0 medians (34.66 / 28.57)
do NOT reproduce the on-record a4-lane convention levels (13.43 / 10.35,
JPY_AUD f1 citing `6J_a4_events.json:boj_mpm_vs_alldays`). Probe 2020-01-21:
this lane 18.18% range / 8.77% vol under [12:00,15:30) held-chain bars; a4
stores 9.60% / 7.87%; the cache `w_tokyo_pm` flag [12:30,15:00) gives
16.88% / 5.30% — neither reproduces a4. a4's exact per-day window/session
convention was not reverse-engineered (considered, NOT_RUN — recorded §4).
The K3 variant comparison is unaffected: every variant uses the identical
statistic on identical bars.

**Verdict (per §0.2)**: K3 anatomy material **DELIVERED**; descriptive
condition **ANCHOR_INSENSITIVE_AT_45MIN**; the K3 *kill* itself (vanishing of
the scored conditional effect under shifted anchors) is **NOT_RUN** — it
requires conditional-on-signal measurement, forbidden this round. BoJ stamps
NOT_IN_CORPUS stands; no stamp inference was made.

## §2 M2 — RMM D-1 mode ledger (6E/6B/6J) + CEASE-SYNC descriptive pass

Artifact: `rmm_mode_ledger.json` (schema `rmm_mode_ledger@1`).

**Mode split (Role-A construction ledger, 27 rolls each)**:

| symbol | abrupt (cease_guard_no_bars) | gradual (k5_crossover) | source |
|---|---|---|---|
| 6E | 22 | 5 | derived (this lane) |
| 6B | 23 | 4 | derived (this lane) |
| 6J | 19 | 8 | derived (this lane) |
| 6A | 21 | 6 | CITED (`6a_roll_measured.json`), reproduction verified |

This closes the RMM register line "mode classification NOT_RUN on 6E/6B/6J"
(mechanical derivation, prep-legal, per dispatch).

**Cross-checks (all in `rmm_mode_ledger.json:crosscheck`)**:
- 6J: derived baseline chain == committed `6J_cache/held_volume_k5.parquet`
  transitions, 27/27 dates and pairs; the 2022-09-20 cease-guard exemplar
  reproduces as abrupt (trigger `cease_guard_no_bars`, switch 2022-09-20,
  consistent with `6j_cease_guard_2022.json` where the k5 baseline switched
  09-21 and the cease-guard law switches at the no-bars session).
- 6A verification: re-derived baseline dates == committed (27/27) AND
  cease-guard dates+triggers == committed (27/27), 0 unmapped rows — the
  cited 21/6 split is bit-reproduced from raw.
- 6E/6B: old→new pairs match the committed switch tables 27/27; **switch
  DATES diverge by design** — the committed `cost_roll_events_fxeb.json`
  tables (and their `held_calendar.parquet`/`chain_calendar.parquet` chains)
  roll on the DECLARED CALENDAR rule (programmatically verified: chain
  transitions == committed switch dates, e.g. 2020-03-02/06-01/09-01), while
  the RMM mode ledger is derived on the k5 + explicit cease-guard MEASURED
  family (RMM field-4 event clock). Per K6(c) law the divergence is itemized
  per roll in `rmm_mode_ledger.json:declared_vs_measured_rule_divergence`
  (27 rows/symbol, calendar-day deltas) and never normalized. Identity
  coverage: 0 unmapped rows on 6E/6J; 84,339 6B rows are non-quarterly
  month-code bars that never enter the quarterly chain by construction.

**CEASE-SYNC descriptive pass (pre-declared boundary: descriptive ONLY; the
block-shuffle placebo ≥100 seeds is a FUTURE scored-side control — NOT_RUN;
no clustering-vs-symbol-local verdict is issued)**: 24 distinct ISO weeks
contain ≥1 abrupt roll. Observed simultaneity (exact week; ±1-week tolerance
gives identical counts): **18 weeks with all 4 symbols abrupt, 3 weeks with
3 symbols, 1 week with 2, 2 weeks with 1** (85 abrupt rolls total).
Every ≥2-symbol week is listed with members in the JSON. The four FX
contracts share the CME quarterly cycle, so mid-March/Jun/Sep/Dec
coincidence is the expected geometry; whether abrupt MODE adds
cross-symbol timing beyond the calendar is exactly what the scored-side
placebo must adjudicate.

**Verdict (per §0.3)**: Role-A construction ledger **DELIVERED**;
validity condition **PASS** (6J/6A exact reproduction; 6E/6B pairs exact
with the rule divergence itemized, not normalized); CEASE-SYNC table
**DELIVERED, descriptive only**.

## §3 M3 — 6A D-2 tick-era audit (steps i + ii)

Artifact: `aud_d2_tickera.json` (schema `aud_d2_tickera@1`).

**Era counts**: era-1 (≤2020-11-20) = **231 held sessions** (== the
`tick_break_locator` count), era-2 (≥2020-11-23) = **1,515** (== AF4 f10's
"≈1,515"). Boundary label stays data-side PROVISIONAL (D8 unratified).

**(i) Era-1 MODELED cost surface at $10.00/tick** — every cell MODELED COST /
UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN; fee layer per FEES_CORRECTED §2
(uniform across tiers); spread proxy = 4 ticks × prevailing tick ($40.00
era-1 vs $20.00 era-2); slippage {1,2,3} ticks ($10/$20/$30 vs $5/$10/$15).

Era-1 reference prices (measured): median held-session close **0.6912**
USD/AUD; final era-1 session (2020-11-20) close 0.7306. Full T1–T4 × {1,2,3}
tables for both price bases in the JSON. Headline (T1, 1-tick, median px):

| | era-1 ($10/tick) | era-2 reference ($5/tick @0.6696) | delta |
|---|---|---|---|
| RT USD | **$104.92** | $54.92 (recomputed exactly; on-record bp 8.2 vs recomputed 8.2019 — validation PASS) | +$50.00 |
| RT bp of notional ($69,120) | **15.18** | 8.20 | ≈ ×1.85 (not ×2: the fee layer is tick-invariant) |

The tick-denominated components double in era-1; the fee layer does not —
so era-1 RT is 1.85–1.91× era-2 in bp depending on the representative price.
No 6A spec may pool across the boundary silently (the delivered tables are
the wired-in correction AF4 f8 required).

**(ii) Spread-proxy step test at 2020-11-23 (same-date 6J placebo)** —
pre-10 vs post-10 held sessions (identical date sets verified across both
symbols; descriptive only, no significance test at n=10 vs 10, no
directional claims):

| | pre-10 median \|Δclose\| | post-10 median | step USD | step ticks |
|---|---|---|---|---|
| 6A | 0.00010 (1 old tick) | 0.00005 (1 new tick) | **0.50×** | **1.00×** |
| 6J (placebo) | 0.0000005 (1 tick) | 0.0000005 (1 tick) | **1.00×** | **1.00×** |

The unconditional close-to-close micro-structure halves in USD exactly at
the boundary on 6A and is exactly tick-invariant; unchanged-grid 6J is flat
in both units on the same dates. Descriptive reading (pre-declared
non-claim): the measured micro-increment is grid-bound on 6A and
date-stable on 6J — the 2020 COVID confound does not move the 6J placebo.
This is the AF4 K2 substrate delivered; no AF4/6A verdict is issued.

Step (iii) 6E/6B constancy: **NOT RUN — FXEB lane's** (dispatch boundary;
recorded §4).

**Verdict (per §0.4)**: steps (i)+(ii) **DELIVERED**; era-2 reference
validation PASS; all cost cells carry MODELED/NOT_RUN labels; D8 remains
unratified and untouched.

## §3b M4 — 6J/6A session dispersion refresh

Artifact: `session_dispersion_6j6a.json` (schema `session_dispersion_6j6a@1`;
per-session machine rows for D5/power consumption).

| block | sessions (with bars) | held bars | median session median\|ret\| bp | median session std bp | held volume |
|---|---|---|---|---|---|
| 6J full 2020–2026 | 1,745 | **2,309,778** | 0.7241 | 1.2745 | 221,915,493 |
| 6A era-1 (≤2020-11-20; descriptive-only stratum) | 231 | 299,445 | 1.4358 | 1.9511 | 20,530,888 |
| 6A era-2 (≥2020-11-23) | 1,515 | 2,003,233 | 0.7558 | 1.6024 | 129,478,595 |

- **6J reproduces the prior committed input exactly**: `6J_a2_sessions.json`
  panel = 2,309,778 bars / 1,745 sessions — this lane's refresh is
  bar-identical at panel level (delta zero); per-session rows are NEW output
  (nothing overwritten).
- 6A era split sums to the full panel (231 + 1,515 = 1,746 held sessions);
  era-1 remains a descriptive-only stratum (K3-thin law — no fold structure
  ever).
- Delta vs prior committed 6A a2 (`mean_abs_1m_ret_by_ct_hour_bp`, 2020-2021
  bucket, on the declared-calendar chain): max |Δ| = 0.114 bp, mean Δ =
  −0.027 bp across the 24 CT hours — attributable to the chain difference
  (declared calendar vs cease-guard), disclosed, not normalized.
- 6J volume-law honored: volume fields are shares/ratios inputs only
  (0.455× gap law), never absolute-level claims.

**Verdict (per §0.5)**: **DELIVERED** — era-aware tables + machine rows;
prior inputs cited; deltas shown; nothing overwritten.

## §4 NOT_RUN register (every considered-and-not-run measurement, anti-cherry-pick)

1. **K3 kill decision** (JF1): requires the scored conditional effect under
   shifted anchors — conditional-on-signal measurement is forbidden this
   round. Only the §1 anatomy material was deliverable.
2. **D-1 block-shuffle placebo** (≥100 seeds, block-shuffled mode
   calendars): pre-registered FUTURE scored-side control; not run here; the
   observed coincidence table carries no cluster/null verdict.
3. **NQ 66-roll mode ledger** (D-1's fifth roll set): out of this lane's
   dispatch scope (NQ-K6 lane owns NQ); considered, not run.
4. **D-2 step (iii)** 6E/6B tick constancy at 2020-11-23: the FXEB lane's;
   not duplicated here.
5. **a4 level-convention reverse-engineering** (the 13.43/10.35 per-day
   range-share convention): probed on 2020-01-21 (two candidate window
   definitions, neither reproduces); not pursued further — disclosed as
   LEVEL_NON_IDENTITY in `jf1_k3_anchor.json`; does not affect the variant
   comparison.
6. **Fee account verification (A7)** — VERIFIED_VS_ACCOUNT=NOT_RUN
   (standing law; no account data touched).
7. **BBO/true spread/fill/queue** — NOT_RUN everywhere (D5 law; standing).
8. **BoJ intraday decision stamps** — NOT_IN_CORPUS (standing; no stamp
   inference in M1).
9. **Significance testing on the step test** (n=10 vs 10) — not run by
   pre-declared construction (§0.4); descriptive ratios only.
10. **Era-1 fold structures** on 6A — forbidden by the K3-thin law
    (≥5-per-fold floor fails at 231 sessions); era-1 remains a
    descriptive-only stratum forever unless the owner extends the panel.
11. **Registration / trial creation / registry or ledger writes** — none
    (round absolutes); PB3 (6A) PARK stands; D8/D9 unratified; ES cap 24
    FROZEN untouched.

## §5 Verdict table

| mission | deliverable | verdict (adjudicates only the §0 pre-declared condition) |
|---|---|---|
| M1 JF1 K3 | `jf1_k3_anchor.json` | **DELIVERED**; descriptive K3-ANATOMY: **ANCHOR_INSENSITIVE_AT_45MIN** (W0 lead −9.78 pp < 0.5 pp on MPM range share); K3 kill NOT_RUN (scored-side) |
| M2 RMM D-1 | `rmm_mode_ledger.json` | **DELIVERED / PASS-with-disclosed-divergence**: splits 6E 22/5, 6B 23/4, 6J 19/8 (derived; 6J chain exact, 6E/6B pairs 27/27 with the declared-vs-measured rule divergence itemized per K6(c)), 6A 21/6 cited + bit-reproduced; CEASE-SYNC descriptive table delivered (18 four-symbol weeks of 24), no cluster verdict (placebo NOT_RUN) |
| M3 D-2 (i+ii) | `aud_d2_tickera.json` | **DELIVERED**: era-1 cost surface delivered (T1 1-tick RT $104.92 = 15.18 bp @0.6912; era-2 reference validation exact at $54.92 / 8.20 bp); step test 6A USD ×0.50 / ticks ×1.00 vs 6J ×1.00/×1.00 on identical dates — descriptive only; D8 untouched |
| M4 dispersion refresh | `session_dispersion_6j6a.json` | **DELIVERED**: 6J refresh bar-identical to the prior committed a2 panel (2,309,778); 6A 231/1,515 era split matches the locator; deltas disclosed; nothing overwritten |

**Zero-PnL statement**: every number in this lane is an unconditional
descriptive of dispersion/volume/bar-count/range/roll mechanics or MODELED
cost arithmetic on named inputs. No signal, no position, no conditional
return, no expectancy, no PnL exists in any artifact. Zero network fetches.
One `git rev-parse HEAD` + `git status --porcelain` (start/end) only; no
commit, no stage, no push.
