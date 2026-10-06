# DATA_READINESS_6A.md — Australian Dollar futures (CME 6A) data-readiness dossier

Lane **FX-JA-READINESS**, round FUTURES-SIX-READINESS-20261004. Worktree
`prep` @ base `d7fc6231`. Generated 2026-10-04 UTC. Companion machine
artifact: `fx_ja/fx_ja_readiness.json` (schema `fx_ja_readiness@1`).

**Law: data-ready ≠ scored-authorized.** Missing evidence = NOT_RUN, never
inferred PASS. **PB3 (6A) stays PARK — restated here, never reopened**; the
census below is contingency-only. No PnL anywhere. Labels binding on every
cost number: **MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN**;
BBO **NOT_RUN** (D5 law).

Baseline evidence of record: `dossiers_v2/6A_DEEP_v2.md` (incl. defects
register item 8, the tick conflict) at base d7fc6231, plus
`hypo/6j_6a/jpy_aud_hypotheses.json` (AF1 f4: "k=5 on 6A NOT measured
(ERRATUM A7-DC-F3)"; "tick 5e-05 vendor, 1e-4 conflict UNADJUDICATED") and the
sibling P3 round (read-only cites).

---

## Dim 1 — Identity / tick — PASS, CONFLICT ADJUDICATED PER ERA (measured)

- **Legacy tick conflict RESOLVED from data** (`6a_tick_adjudication.json`).
  The dossier's item-8 claim ("0.00005-vs-0.0001 legacy conflict remains
  unadjudicated") is closed as a **dated two-regime fact**:
  - **Era 1 — 2020-01-02..2020-11-20 (231 sessions)**: traded grid
    **1e-04 USD/AUD = $10.00/tick** at 100,000 AUD. Evidence: zero odd
    5e-05-multiple closes anywhere in 327k+ closes (odd share 0.000 in every
    month Jan-Oct 2020); era-1 increment GCD = 100,000 int-nano; min observed
    increment = 1e-4.
  - **Era 2 — 2020-11-23..2026-09-30**: grid **5e-05 USD/AUD = $5.00/tick**.
    Evidence: odd 5e-05 multiples in ~49% of closes (coin-flip fine-grained
    book) in every era-wide chunk (2020-21 backfill included: first odd print
    session **2020-11-23**); era-wide increment GCD = 50,000 int-nano in all
    four vendor chunks; vendor `min_price_increment` = 5e-05 in all 72
    definition rows 2023-10+ (consistent with era 2).
  - Every close in the corpus lies on the 5e-5 grid (the 1e-4 grid is a
    subset) — no pricing inconsistency; the BREAK sits in the weekend of
    **2020-11-20 → 2020-11-23** (CME FX tick-halving window; official
    rulebook page remains BLOCKED_TRANSPORT — the adjudication is data-side
    and the official-source label is unchanged).
- **Multiplier = 100,000 AUD** (definitions `unit_of_measure_qty` decoded +
  S1_IDENTITY '100000'). **Quote = USD per AUD; 6A UP = AUD stronger.**
- **Consequence (cost-bearing, disclosed)**: the baseline's "5e-05 used
  throughout = $5.00/tick" is correct only from 2020-11-23; in the 2020
  sub-era a tick is $10.00, so tick-denominated cost/spread models must be
  era-aware (the baseline 4-tick close-proxy = $20 is a post-break number).

## Dim 2 — O1M coverage + holes — PASS

Panel of record: 2,703,211 outright bars 2020-01 → 2026-10-01 on 86
contracts; 1,584 `6BU5` vendor-contaminant bars excluded; 0 outright negative
prices; 171,473 calendar-spread bars kept strictly separate
(`6A_DEEP_v2.md` §7 / `build_report.json`, cited). **Mar/Jun 2023 measured
this lane** (`session_holes_2023.json`): **zero missing weekdays** — March
2023 has 23 traded weekday sessions, June 2023 has 22. The "6A Mar/Jun 2023"
gap is an **expiry-pointer** cell (Dim 3), not a data hole. Caveats: 2020-21
identity by instrument_id + delivery-frame (definitions begin 2023-10);
2026-10-01 partial tail.

## Dim 3 — Roll / expiry — MEASURED (was BLOCKED), NOT_OBTAINED cells remain

- **k=5 roll MEASURED, not extrapolated** (`6a_roll_measure.py` →
  `6a_roll_measured.json`; chain built from the raw parquets with the baseline
  algorithm family cited from `6J_deep_lib.py`/`NQ_deep_lib.py`; identity via
  the 6A registry's instrument_id map):
  - **27 rolls**, span **2020-03-17 (6AH0→6AM0) .. 2026-09-14
    (6AU6→6AZ6)**, 1,746 held sessions, 32 quarterly contracts.
  - **Cease-guard violations (baseline-code k=5): 2 vanished sessions** —
    **2024-12-17** (held dead 6AZ4 while 6AH5 traded 55,675 lots) and
    **2026-06-16** (held dead 6AM6 while 6AU6 traded 55,533 lots) — the exact
    6J-2022-09-20 pathology, on 6A, twice. Exchange was open both days.
  - **Explicit cease-guard variant** (hard switch at last-bars date): 27
    rolls, **0 violations**, identical switch dates except the two above land
    1 session earlier (2024-12-17, 2026-06-16). 21 of 27 rolls fire the
    cease-guard trigger; 6 fire the volume crossover.
  - Calendar-rule cross-reference: declared calendar rule = 27 rolls
    (`6A_a3_term.json`); k=5 crossover dates land ~2 weeks later than the
    declared roll dates (consistent with §3.1's 9-15d crossover lag) — roll
    rule choice is material to timing, disclosed.
  - The matrix's BLOCKED reason "k=5 extrapolation" is **discharged**; owner
    updates the matrix cell (not this lane).
- **Expiry pointers: 62/68** = 52 official (FXCAL 2010-2022) + 10 from the Q5
  capture (2023Q3..2025Q4). Missing 6 cells: **2023Q1 (Mar), 2023Q2 (Jun),
  2026Q1-Q4** — NOT_OBTAINED, derivation forbidden. The dispatch's 62/68 is
  reproduced (`q5_independent_verify/verify_q5_captures.json`); all 10
  extracted official lastTrade dates ≥ observed last-bar session.

## Dim 4 — Session / holiday — PARTIAL

17:00 CT Sun → 16:00 CT Fri template, 60-min break honored 2020-2026 (dossier
§7). Mar/Jun 2023 clean (measured). **NOT_IN_CORPUS**: CME holiday session
TIMES (early-close minutes) for every year incl. 2024-25 — same open cell as
6J.

## Dim 5 — Event PIT — PARTIAL (RBA PASS at date granularity)

- **RBA**: `rba/cash_rate_gate.html` (sha-verified this lane) carries **395
  dated decisions 1990-08-02..2026-09-30**; 2023-2026: **33 dated decisions
  (11/8/8/6), 12 changes**. PASS_EVIDENCED at date granularity; decision TIME
  not carried by the file — the 14:30-Sydney anchor stays the declared
  convention of `6A_DEEP_v2.md` §4.1.
- **DFF (US side)**: 16 year-end vintages (2010-2024 + 2026-09-30; **no 2025
  vintage**) + latest snapshot. Vintage law restated: available_time = the
  vintage as-of the decision date; current-calendar inference FORBIDDEN.
  NOT a dense PIT series — AF2's declared caveat stands.
- **NOT_RUN** (unchanged): ABS CPI/Labour-Force historical release dates; China
  Caixin/NBS calendars; RBA surprise classification.

## Dim 6 — Fee / spread / slippage / BBO — MODELED + NOT_RUN

Same corrected fee tier table as 6J (FX group; mapping PARTIAL) — MODELED
COST / **VERIFIED_VS_ACCOUNT=NOT_RUN**. Baseline RT 1-tick T1 **$54.92 =
8.2 bp** (spread proxy $20 = 4 × $5 post-break tick; multiplier 100,000).
**Era caveat: that RT is NOT valid in the 2020 sub-era** ($10/tick there);
era-aware recomputation is required before any use. **BBO NOT_RUN** (D5).

## Dim 7 — Trial budget — PB3 PARK RESTATED (no new trials)

AF1 11 + AF2 0 + AF3 11 minimal (full-grid 48) per `synth/CENSUS_FINAL.md`.
**PB3 PARK stands**: 6A is PREP only — no registration, no budget; the census
is CONTINGENCY ONLY; nothing in this lane reopens it. AF1's two f4 gates that
this round could close are closed: k=5 MEASURED (Dim 3), tick conflict
RESOLVED_PER_ERA (Dim 1) — recorded for the owner's matrix update.

## Dim 8 — Reproduction / A7 — PARTIAL

Same lane scripts as the 6J dossier (`fx_ja/`, interpreter pinned). A7 fee
re-verification packet pending (VERIFY-A7READY, PREPARE ONLY); account
verification NOT_RUN.

---

## Closing line

**Data-ready ≠ scored-authorized.** 6A's two long-standing blockers that data
could close are now closed by measurement (tick adjudicated per era; k=5 roll
measured with the cease-guard pathology quantified), but scored use remains
**blocked** by: (1) **PB3 PARK** (owner ruling — contingency-only regardless
of readiness); (2) fee VERIFIED_VS_ACCOUNT=NOT_RUN (A7); (3) the 2020
sub-era $10/tick fact not yet wired into any frozen cost spec; (4) BBO/fill/
queue NOT_RUN (D5); (5) official expiries 2023Q1/Q2 + 2026 NOT_OBTAINED and
holiday session times NOT_IN_CORPUS; (6) ABS/China calendars NOT_RUN (AF3's
own K4 kills its base spec without a China calendar). None of these may be
inferred PASS.
