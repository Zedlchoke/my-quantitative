# SPEC_6E — Euro FX futures (6E) PRE-SCORED packet draft, load-bearing laws

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **FXEB**, 2026-10-05.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`,
  branch `prep/futures-5sym-prescored-20261005`, HEAD `ffed828f73fa19fa0ff4aee3ac1b441909a43940`
  (= dispatch `base_sha`, measured once at lane start). No commits by this lane.
- Class: PREP-only draft. **0 PnL, 0 scored runs, 0 conditional-on-signal statistics.**
  Every number below is cited to a committed artifact (sha256 recorded in this lane's
  handoff outputs and in the cited files themselves). Missing evidence = `NOT_RUN`,
  never inferred PASS.
- **CONDITIONAL-ON-PB2-LIFT DRAFT. PB2 remains HOLD by Co-Owner ruling
  (PLAYBOOKS_DRAFT r5 §2; PB2_ANCESTRY_COURT_DRAFT §d "renders NO reopening verdict";
  `FUTURES-SIX-READINESS-20261004/fx_eb/pb2/PB2_HOLD_RESTATE.md`, sha256
  `88386aa3443ac8713a1dc33eba628910d04c088cc2a9d64fce8238c9d9d5a75b`). NOTHING in this
  spec is executable today. Every gate, identity and cost number binds ONLY if, and
  after, the owner lifts PB2 — which this lane does NOT treat as given and does not
  ask for.** The 6B sibling spec is `SPEC_6B.md`; no cell is shared silently.

## 1. Instrument identity (6E)

| field | value | status | source |
|---|---|---|---|
| Product | CME Euro FX futures, Globex code `6E` (chain label prefix `6E`, e.g. `6EH0_2020`) | FACT (baseline restate) | `DATA_READINESS_6E.md` §1 (`FUTURES-SIX-READINESS-20261004/fx_eb/`, sha256 `c7ea807b…cd05`); machine twin `fx_eb_readiness.json` sha256 `adc15c67…52eb`, `6E.dims.1_identity_tick` |
| Contract size | **EUR 125,000** vs USD | PASS_BASELINE_RESTATE | same rows; baseline `dossiers_v2/6E_DEEP_v2.md` header pin recorded in `fx_eb_readiness.json.artifact_pins` |
| Quotation | **USD per EUR** (implied USD quote currency) | PASS_BASELINE_RESTATE | same rows ("125000 EUR, USD quote") |
| Min tick | **0.00005 = $6.25/tick** | PASS_BASELINE_RESTATE | same rows, `tick: "0.00005", tick_value_usd: 6.25` |
| Tick in data fixed-point | **50,000 int-nano** (price × 1e-9) | MEASURED | `FXEB_K6_GATES.md` §0.5 + §4 (`FUTURES-K6GATE-PREP-20261004/fx_eb/`, sha256 `861a04bd…0841`); machine mirror `tick_constancy_6e6b.json` sha256 `b6b9927e…fca2` |
| Tick constancy at 2020-11-23 | **CONSTANT** — GCD == min-increment == 50,000 int-nano in all 5 sampled windows (2020-03, pre/post boundary pair, 2023-01, 2026-07); close-on-grid share 1.0 | MEASURED (D-2 step iii CLOSED) | `FXEB_K6_GATES.md` §4 verdict table; `tick_constancy_6e6b.json` |
| Orientation | standard (no inverse-quote flag measured); orientation PROVEN carried at family level by dossier v2 + `FX_HYPOTHESES.md` §1.4 "0 violations on 3.05M bars" | carried | `FX_HYPOTHESES.md` (sha256 `f8403a0f…4b861`) §1.4 |

Anything not in the table above (e.g. margin levels, delivery terms verbatim text):
**NOT_RUN for this packet** — margin is a sizing fact, not an edge (court §b4); no
verbatim 6E weekly-hours spec capture exists (§3 below).

## 2. Data / panel contract (6E)

- Outright 1m panel: **3,054,311 bars, 2020-01 → 2026-09-30**, three eras (AV1B
  backfill2 886,127 / AV1R backfill 1,823,090 / AV1T 345,094); era butts verified
  no-overlap [FACT, `DATA_READINESS_6E.md` §2].
- Files re-hashed by THIS lane in THIS worktree (read-only single-shot; locks
  FREE_PROVEN before/after):
  - `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_cache/6e_annotated_1m.parquet`
    — 3,054,311 rows per K6GATE §0.1; sha256 `13ae3cd657bb140a05e73986838069d6e5ae197757ecfc1328c987305499077e`, 83,827,281 bytes.
  - `…/6E_cache/6e_outright_1m.parquet` — sha256 `fc9ca2a1f6e8a9b61f4b3352bfcd988738e65d808d9d7f28d71cdd0e989a70e2`, 79,396,559 bytes.
  - `…/6E_cache/held_calendar.parquet` — 1,746 sessions 2020-01-02..2026-10-01;
    sha256 `35aa5d0bb4e7943a7cc2a9a6a2fd2c4c89c71e412c4745b34f7d7f557a7a0231` (equals the
    pin in `cost_roll_events_fxeb.json`), 11,369 bytes.
  - `…/6E_cache/contract_registry.json` — sha256 `0d5c577a21cd0b90ff63affa473d22e96ea703044443583525f9918c006148b6` (6E-only artifact; no 6B registry exists — disclosed).
- Schema law: D5 fixed-point 1e-9; `ts_event` = bar START; `raw_symbol` containing `-`
  (calendar spreads) excluded by design; serial months dead (0.34% of 6E volume); strays
  (`6JZ7`/`SIJ5` filtered; GCQ4 quarantined) per `FX_HYPOTHESES.md` §1.10.
- **Held-contract restriction is load-bearing** [MEASURED, K6GATE §0.7]: 1,282,448 of
  3,054,311 rows share a timestamp with a different contract; mixing contracts inside
  sessions inflates dispersion (|1m ret| p90 45.8bp → 1.9bp held-only). All anatomy,
  triggers and any future scored fill MUST be computed held-contract-only.
- 0 OHLC/zero-vol/duplicate violations on 3.05M bars [carried, `FX_HYPOTHESES.md` §1.10].

## 3. Session law + DST (6E)

- Template: **Globex ~23h; session = 17:00 CT (D-1) → 16:00 CT (D), 60-min maintenance
  break** [MEASURED on venue; `FX_HYPOTHESES.md` §4.1/§4.3; K6GATE §0.1 session
  annotations]. 348/1,746 Sunday-evening opens (1.9% of front volume).
- **No verbatim weekly-hours spec capture for 6E exists** (archived spec-service captures
  are ES/NQ-only) — stated honestly [FACT, `DATA_READINESS_6E.md` §4]. The session law
  therefore rests on the measured template + holiday deviation grids, not on a spec page.
- DST: session/segment logic America/Chicago + Europe/London via zoneinfo, DST-correct;
  DST-mismatch weeks shift the 6E volume profile by exactly one CT hour (159,982 bars;
  h+02 6.79→4.71, h+03 5.64→6.80) [MEASURED, `6E_a2_sessions.json:dst_mismatch_effect`
  cited in `FX_HYPOTHESES.md` §1.1]. DST-mismatch sign flip = clock-law bug (K4-analog).
- Segment partition for masks/ anatomy: `6E_deep_lib.SEGMENTS` CT-minute disjoint
  partition (evening_open / asia_evening / asia_morning / london_morning / london_midday /
  ecb_usdata_window / pre_rth / rth_first_hour / us_morning_late / us_midday / fomc_window /
  afternoon_close) [K6GATE §0.4/§3].

## 4. Calendar / roll law (6E) — details in CALENDAR_PIT_POLICY_6E_6B.md

- Expiry 2023-2026 official cells: **14/16 OBTAINED**; cumulative 2010-2026 grid
  **66/68** (missing ECU26/ECZ26, proven-absent chain). ECH26 2026-03-16 and ECM26
  2026-06-15 recovered this cycle-family; every cell carries file+sha256 provenance
  [FACT, `fx_eb_expiry_2023_2026.json` sha256 `cf07d4e2…1ef07`].
- Roll: **27 switches over 1,746 sessions, 28 contracts; last-held-session lead before
  expiry 13–19 days** where cells obtained [MEASURED, `cost_roll_events_fxeb.json`
  sha256 `a99a6983…40052`]. What SIX-READINESS measured: the observed switch pattern
  (dates + leads) from the existing held chain. What remains **law-pending**: binding a
  PIT roll rule (k=5 + cease-guard class) to official expiry dates, and the treatment of
  the 2 NOT_OBTAINED quarters (fail-closed per D12 posture). The baseline 6B-style "PIT
  k=5 + cease-guard" rule exists for 6B (`FX_HYPOTHESES.md` §1.4); **the equivalent 6E
  freeze-law wording is NOT YET ADJUDICATED — DRAFT here, binding only at a PB2-lifted
  freeze**: roll at the close of the session T-5 sessions before official last-trade
  date, with cease-guard (never roll into a dead contract; reconcile naive vs guarded
  switch on cease-guard event days per CYCLE_LAUNCH_DRAFT §5).
- Holidays: **34/42 archived windows OBTAINED** with id-58 deviation grids (first
  per-product 6E tabulation; 8 aged-out INCONCLUSIVE never counted). Early-close/
  holiday exclusions **fail-closed** with exact lists in `CALENDAR_PIT_POLICY_6E_6B.md` §3.

## 5. Event PIT law (6E)

- **FOMC (6E primary overlay family FX-F2 base)**: 30 rate-decision statements
  2023→2026-09-30 (8/8/8/6 by year); the 31st statement (2025-08-22) is the
  framework-review statement, not a decision. In-panel 2020-2026: 58 statements with
  in-file release-time proof (53 at 13:00 CT; 2020 emergency timings disclosed and
  EXCLUDED from any base). Anchor minute 13:00 CT (minute 780); volume ×17.24 vs control
  Wednesdays; re-amplification ×8.81 at 13:40 CT [MEASURED, `6E_a4_events.json:fomc`
  cited `FX_HYPOTHESES.md` §2.1; `DATA_READINESS_6E.md` §5].
- **ECB GC (6E secondary stratum)**: 55/55 meetings 2020–2026.9, decision 14:15
  CET/CEST [carried, `6E_a4_events.json:ecb`; decision-minute volume ×1.73 — a different
  intensity class, the F2 family-specific negative].
- **BLS 08:30 ET (FX-F3 base days)**: CPI/EMPSIT schedules 204/204 rows 2010-2026 all
  @08:30 ET, vintage law BLSV §5 mandatory (2025: 11 CPI / 10 EMPSIT actual prints;
  canceled-expected days are negative-control strata) [FACT, `bls_dates.json` +
  `BLS_VINTAGE_INVESTIGATION.md` cited `FX_HYPOTHESES.md` §3.3].
- Vintage law: event calendars keyed to vintage as-of decision date; current-calendar
  inference FORBIDDEN. Surprise/consensus vintages NOT_RUN — F2 conditions on event +
  realized first-5m sign only.

## 6. Cost contract (6E) — full derivation in COST_CONTRACT_6E_6B.md

Tier-1 all-in **2.46 USD/side MODELED** (0.85 + 1.60 + 0.01; FX alias mapping PARTIAL —
generic CME "Forex Futures" row, 6E never verbatim); dual-variant reg-basis law applied
to the FX tier: A7 §8 tabulates the A/B dual variant for ES/NQ only, so the FX Variant-A
composition (0.85+1.60+0.02 = 2.47) is **DERIVED, not tabulated** — owner ruling
required. Modeled RT ladder **3.6–6.3 bp** across S1/S2/S3 ×1.0 (spread close-proxy
$18.75/side high-biased; slippage {1,2,3} ticks/side × $6.25). **BBO NOT_RUN stands
(D5); VERIFIED_VS_ACCOUNT=NOT_RUN; UNDER REVIEW until a clean fee A7 + basis ruling.
The words "measured cost"/"complete cost" are forbidden on any output.**

## 7. Folds, warmup, K-views (6E) — DRAFT law, binding only post-lift

- Folds (ES-precedent 4-fold mapped to the 6E measured span 2020-01..2026-09, folds
  respect era seams as views not cuts; boundaries fixed at any future registration
  freeze): **F1 2020-01..2021-12 · F2 2022-01..2023-12 · F3 2024-01..2025-06 ·
  F4 2025-07..2026-09**. S1 = SEALED_UNTOUCHED. Folds multiply evaluation, never
  identities (SPEC_PB1_ES §7 precedent).
- Warmup: **60 held sessions** excluded at each fold head (FX family law
  `FX_HYPOTHESES.md` §1.5; K6GATE §0.2 operationalized as held sessions). The six-adopt
  packet's ES-precedent 252-session warmup is an alternative — owner choice at the
  CONV-D signature (P5-OD11).
- Declared K-views (evaluation views, never folds): K5 era sign stability 2020-22 vs
  2023-26; DST-mismatch-week split; 2022 Monday-halt regime change (pre-2022 reopen
  structure differs); BLS vintage regime 2025; fee epoch windows (none measured for FX
  inside 2020+; e.3 epoch-binding ruling carried).

## 8. Baselines / controls (6E, CONV-D per family per leg)

Per family per leg (CONV-D, requires owner convention signature): **8 minimal-core S2
identities (2 arms × 2 tails × 2 delays @ tier S2) + 3 scored controls** = 11:
- C1-class **clock-only shadow**: single-seed/single-delay placebo per PB1 C1 law
  (SPEC_PB1_ES §6: seed 20261002, publication-limit framing, no permutation-robustness
  claim); the clock-shadow reading (a) (shadow is 1 of the 3 controls) vs (b) (additive)
  is an owner signature (IDENTITY_TABLES §2.1).
- **C2 always-on** (signal ignored; arm must beat C2 after cost ⇒ else "no conditioning
  information"); **C3 anchor** (FLAT-class accounting floor). C4 dose-response stays a
  full-grid/sensitivity class, not in the CONV-D 11.
- Family-specific negatives carried per family: F2-6E negative = ECB stratum (×1.73
  vs ×17.24 intensity ordering is itself the falsifiable claim); F3-6E negatives =
  weekday-matched non-event clock + expected-but-canceled 2025 days + weaker
  unclassified-8:30 stratum; F1-6E = 6E/6B trigger co-occurrence + C2; F4-6E =
  zero/minimum-gap-day placebo + DST-mismatch split.

## 9. Verdict criteria + power honesty (6E)

- Gates (G-series, ES precedent): after-cost expectancy > 0 at declared tier; PF ≥ 1.10;
  ≥2/4 folds positive; era-sign stability (K-views); delay sign-stability within family;
  crash-window concentration cap (K3); arm beats C2 and C1 after cost; repro byte-match;
  A7 0 HIGH/CRITICAL. Family kill: both competing arms below floor ⇒ family dead, no
  re-tparam (K2).
- **Power honesty (6E numbers)**: F1 census n=1,362 base triggers ⇒ MDE-at-n
  ≈ **3.5 bp/trade** (court §c3 method: 2.80 × 46.3bp/√1,362) vs modeled RT 3.6–6.3 bp —
  the power floor and the cost floor essentially coincide [MEASURED+DERIVED,
  `FXEB_K6_GATES.md` §1]. F2 n=58 FOMC days ⇒ MDE ≈ 17.0 bp vs RT 3.6–6.3 bp —
  detectable only at tail-event scale. F3 known-type n≈165 ⇒ MDE ≈ 10.1 bp. F4 weekday
  reopens n=1,282 (gap std 0.0304%, Sunday 317 separate stratum) ⇒ MDE-class 3.3–5.8 bp
  before threshold thinning (threshold itself a registered-cycle decision, NOT_RUN).
- **The court finding binds (PB2_ANCESTRY_COURT_DRAFT §c3, restated in IDENTITY_TABLES
  §6): at program-feasible n≈300–900 the power floor and the cost floor coincide. A null
  returned at that n is the PRE-REGISTERED DEATH of the family — it is NOT evidence of
  absence of an edge smaller than cost.** Every 6E verdict must be written in those terms.
- Census gate ≥500 triggers/symbol: **6E PASS (1,362 ≥ 500)** [MEASURED, K6GATE §5 M1] —
  this closes the census gate's measurement precondition ONLY; it schedules nothing and
  does not lift PB2. The court's b1.1 1m trigger-time anatomy (required BEFORE any scored
  registration per court §b1.1) remains **NOT_RUN**.

## 10. NOT_RUN register (6E, carried + this lane)

1. BBO / execution realism — NOT_RUN (D5 law; conservative fills bind).
2. Fee account verification (A7 against account) — NOT_RUN; fee layer UNDER REVIEW.
3. FX Variant-A reg composition on the FX tier — DERIVED (not in A7 §8 tables); owner
   ruling P5-OD7 required.
4. ECU26/ECZ26 official expiry cells — NOT_OBTAINED (proven-absent chain).
5. 7 aged-out 2023-H1 + 2025-01-05 holiday windows — INCONCLUSIVE_AGED_OUT (never cells).
6. Deviant-session identification for 29/34 OBTAINED holiday windows (captures absent
   from committed tree) — NOT_RUN; neighborhoods fail-closed (93 cells, K6GATE §2).
7. 1m trigger-time anatomy (court §b1.1) — NOT_RUN; precondition for any scored F1 spec.
8. Per-trade dispersion (court §c3 court-input) — NOT_RUN (conditional-on-signal class).
9. F4 minimum-gap threshold value — NOT_RUN (registered-cycle decision by §4.5 law).
10. F5 CIP-vintage quantification + real-time SOFR source decision — NOT_RUN (owner-gated).
11. Surprise/consensus vintages (ECB/FOMC/BLS content) — NOT_RUN.
12. ATR(20d) numeric SL levels — NOT_RUN (computed at freeze, never before).
13. Weekly-hours verbatim spec capture for 6E — NOT_OBTAINED (structural; session law is
    measured-template-based).

— End SPEC_6E.md. Conditional-on-PB2-lift draft; nothing herein registers, schedules,
scores, or reopens any standing ruling.
