# 6A_TICK_ERA_LAW — era-aware tick/cost law for 6A (AUD/USD futures)

Round: FUTURES-SIX-ADOPT-PREP-20261004 · Lane ADOPT · 2026-10-04

**Label: PROPOSED — pending owner decision D8. Nothing here freezes a cost spec; until the owner
rules, the fail-closed default in §4 applies.**

## 1. Era table (the law)

6A's traded tick size is NOT constant over the corpus. The measured law:

| Era | Sessions | Tick (USD per AUD) | Tick value per contract | Basis |
|-----|----------|--------------------|--------------------------|-------|
| **Era 1** | **2020-01-02 .. 2020-11-20** (231 sessions) | **1e-04** (0.0001) | **$10.00** (multiplier 100,000 AUD) | every observed increment on the 1e-04 grid; min observed increment = 1e-04; **zero** odd 5e-05 prints across 327k+ closes |
| **Era 2** | **2020-11-23 .. corpus end (2026-09-30)** | **5e-05** (0.00005) | **$5.00** | odd 5e-05 prints in ~49% of closes; era-wide increment GCD = 5e-05; matches vendor `min_price_increment` in every definition row 2023-10+ |

Boundary: the **weekend 2020-11-20 → 2020-11-23** (the CME FX tick-halving window). Locator:
`last_pure_1e4_session = 2020-11-20`, `first_5e5_session = 2020-11-23`
(`fx_ja/6a_tick_adjudication.json tick_break_locator`). Both legacy candidates from the v2 conflict
(6A_DEEP_v2.md defects item 8) are therefore REAL — just in different eras. The baseline's
"$5 throughout" is correct from 2020-11-23 onward only and **wrong for the 2020 sub-era**.

Domain of validity: the av1trim 6A corpus (2020-01-02 onward). Pre-2020 6A tick is NOT measured by
this corpus and is out of scope; any pre-2020 6A cost work needs its own measurement first.

## 2. Measurement basis (how the eras were established)

* **Method**: GCD of non-zero minute-close increments on the integer-nano grid + share of closes on
  the 5e-05 / 1e-04 grids; window probes at 8 stress points including the COVID week
  2020-03-09..13 (GCD 1e-04, share-at-min 0.397) and cease-guard week 2022-09-19..23 (GCD 5e-05).
  File: `FUTURES-SIX-READINESS-20261004/fx_ja/6a_tick_adjudication.json`; measured from raw parquets
  (`measure_6a_tick.py`); independently reproduced by the VERIFY lane from raw with its own code
  (`verify/fxja_crosscheck.json`: 3 pre-break sessions GCD 100,000 int-nano, 3 post-break sessions
  GCD 50,000 — break reproduces exactly at the 2020-11-20→23 weekend).
* **Era-wide chunks (4)**: BF2_2020_2021 (791,090 rows / 575,805 increments), BF1A_2022_2023
  (800,059 / 646,919), BF1B_2024_2025 (814,686 / 606,103), TRIM_2026 (194,379 / 139,089) — all
  `close_on_5e5_grid_share = 1.0`, all GCD 5e-05; per-era `first_session_with_odd_5e5_print`
  = 2020-11-23 / 2022-01-03 / 2024-01-02 / 2026-04-01 (first session of each chunk's coverage).
  `non_5e5_grid_closes_whole_corpus = 0`.
* **Vendor definition consistency**: definitions 2023-10+ — 72 6A symbols, single distinct
  `min_price_increment` (5e-05 USD/AUD), single unit-of-measure (100,000 AUD) — consistent with
  era 2 only, which is exactly why the vendor field could not adjudicate era 1.
* **Status of the official source**: the CME rulebook page for the tick change remains
  **BLOCKED_TRANSPORT**; the break is DATED FROM DATA. Labels stay descriptive-measurement; no
  cost/PnL claim is made by the measurement itself.

## 3. Cost implication (era-aware slippage)

With multiplier 100,000 AUD: one tick = 1e-04 × 100,000 = **$10.00** (era 1) vs 5e-05 × 100,000 =
**$5.00** (era 2).

* **Per side**: a 1-tick slippage assumption costs **$10.00/side in era 1** vs $5.00/side in era 2 —
  the era-1 slip is **2×** the era-2 slip.
* **Round-turn**: a 1-tick-per-side model costs **$20.00/RT in era 1** vs **$10.00/RT in era 2** —
  a delta of **+$10.00/RT per contract (+100% of the slip component)** for any 2020-era window
  modeled with the flat $5 tick. Commission components are unaffected; the understatement is exactly
  $10.00/RT regardless of the modeled RT total.
* Any historical 6A evaluation touching 2020-01-02..2020-11-20 with a flat-$5 spec understates
  execution cost by that $10.00/RT and must not be consumed as-is (blocked by the §4 default).
* Session-level application: the era boundary is a SESSION-date lookup (2020-11-20/23 weekend), so
  era assignment is deterministic per bar/decision date and introduces no lookback.

## 4. What a future 6A cost spec MUST contain

1. **Explicit era table** with the session-date boundary (last 1e-04 session 2020-11-20; first
   5e-05 session 2020-11-23) — a flat tick field is a spec defect.
2. **Tick value per era** ($10.00 / $5.00 per contract) with the multiplier (100,000 AUD) and quote
   orientation (USD per AUD; 6A UP = AUD stronger) stated.
3. **Slippage in ticks, priced era-aware** (tick value resolved per decision session).
4. **Separately itemized commissions** (not entangled with slip), still MODELED /
   VERIFIED_VS_ACCOUNT=NOT_RUN until fee D2/D3 authorization.
5. **Provenance status line**: data-derived boundary; official rulebook source BLOCKED_TRANSPORT;
   measurement file pointer (`fx_ja/6a_tick_adjudication.json`) + verifier pointer
   (`verify/fxja_crosscheck.json`).
6. **Domain statement**: corpus coverage 2020-01-02 onward; pre-2020 windows NOT covered by this
   law.

## 5. Fail-closed default (until D8 is ruled)

**Era-2-only cost models may not back-cast into 2020-era windows.** A 6A cost spec that lacks the
era table is invalid for any window overlapping 2020-01-02..2020-11-20; if the owner rules Option B
(vendor document before freezing), the measured boundary stays PROVISIONAL and 2020-era 6A cost work
stays blocked on that document.

— PROPOSED, pending owner D8. Not frozen.
