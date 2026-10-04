# DATA_READINESS_6J.md — Japanese Yen futures (CME 6J) data-readiness dossier

Lane **FX-JA-READINESS**, round FUTURES-SIX-READINESS-20261004. Worktree
`prep` @ base `d7fc6231`. Generated 2026-10-04 UTC. Companion machine
artifact: `fx_ja/fx_ja_readiness.json` (schema `fx_ja_readiness@1`).

**Law: data-ready ≠ scored-authorized.** Missing evidence = NOT_RUN, never
inferred PASS. Every load-bearing number below is either re-measured from raw
local data this lane (script + output cited) or cited to its artifact of
record. No PnL anywhere. Labels binding on every cost number: **MODELED COST /
UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN**; BBO **NOT_RUN** (D5 law).

Baseline evidence of record: `dossiers_v2/6J_DEEP_v2.md` (incl. §8 ERRATUM
M-5 cease-guard law) at base d7fc6231, plus `hypo/6j_6a/jpy_aud_hypotheses.json`
(FUTURES-OVERNIGHT-PREP-20261003) and the sibling P3 round (read-only cites,
re-verified where load-bearing).

---

## Dim 1 — Identity / tick / orientation — PASS (orientation PROVEN)

- **Tick = 5e-07 USD/JPY = $6.25/contract; multiplier = 12,500,000 JPY.**
  Measured, not assumed (`6j_identity.json`): `AV1T-definition-ALL10` carries
  `min_price_increment` = 500 int-nano (5e-7) **unique across all 72** 6J
  symbol-definition rows (2023-10+); observed minute close-to-close increment
  **GCD = 500 int-nano in all three sampled eras** (2020-03 backfill, 2023-01,
  2026-07); the coarser 1e-6 grid FAILS (≤50% of closes on-grid) — so the
  dispatch's tentative 1e-7/$1.25 alternative and any 1e-4/$12.50 legacy are
  **rejected on data**. Multiplier measured twice: definitions
  `unit_of_measure_qty` = 12500000000000000 int-nano = **12,500,000 JPY
  decoded**, and `S1_IDENTITY.json` (sha256 d217ab9d… rehashed this lane,
  match).
- **Quote orientation = USD per JPY; 6J UP = yen strengthens.** Re-proven from
  a RAW-parquet slice (own data, not the cache; `6j_orientation_recheck.json`):
  2024-07-11 MOF op day, front = 6JU4: session open 0.0062485 → close
  0.0063565 (**+1.73%** in the dossier's CT-trade-date convention; day range
  0.0062415–0.0064140) while implied USDJPY fell 160.04 → 157.32 — yen
  STRONGER, 6J price UP. No inversion.
- **Burst minute exact**: 12:41→12:42 UTC close 0.0062800 → 0.0063325 =
  **+105 ticks in one minute**, front 12:42Z volume **17,448 lots** — both
  bit-identical to `6J_DEEP_v2.md` §5 and the sibling P3 re-proof.
- **Sibling-number framing note (contradiction disclosed, not smoothed)**: the
  P3 check's "415,392 lots / close 0.0063775 / +2.056%" are **UTC-calendar-day
  aggregates** (re-measured: UTC-day volume 415,392, close 0.0063775,
  +2.07%). The dossier's CT-session convention gives 364,917 lots / +1.73%.
  Both framings prove the same law; the P3 check's session framing was
  mislabeled, nothing else changes.
- Residual: the legacy 1e-4 "JY" (TradingCharts) tick stays unadjudicated vs
  the CME rulebook (BLOCKED_TRANSPORT) — moot on this corpus (zero support).

## Dim 2 — O1M coverage + holes — PASS

- Panel of record: 2,843,938 outright 1m bars, 2020-01-01 → 2026-10-01
  (AV1B BACKFILL2 2020-22 + AV1R BACKFILL 2022-26 + AV1T 2026; era row counts
  in `6J_DEEP_v2.md` §8, cited; slices re-read from the same raw chunks this
  lane).
- **6J 2023 holes, measured** (`session_holes_2023.json`): exactly **2 missing
  weekdays in 2023** — 2023-01-02 (New Year) and 2023-12-25 (Christmas). Both
  exchange holidays. No unexplained 2023 hole.
- 2022-09-20: the vendor PANEL has 1,466 6J rows that day (exchange open);
  the hole is chain-attribution only (Dim 3).
- Caveats carried: volume-definition gap 0.455× (shares/ratios only, never
  absolute levels); 2026-10-01 partial tail (~2h); 1 stray break-window bar in
  2.84M.

## Dim 3 — Roll / expiry — PARTIAL

- **Cease-guard law (6J_DEEP_v2.md §8 / ERRATUM M-5): PASS — re-proven
  element-by-element from raw** (`6j_cease_guard_2022.json`):
  - 2022-09-20 exchange OPEN: 1,466 6J rows across 4 symbols; **Z2 traded
    125,303 lots over 1,357 bars** (exact); official corroboration — Q5
    capture row J1U27 "First Trade 2022-09-20" (a new contract year BEGAN
    trading that day; hash-verified capture, own parser).
  - k=5 still held **ceased U2** on 09-20: stale trailing-5 mean **92,857.8**
    vs Z2 ramp **88,234.0** (U2 had zero bars; its stale mean still won).
  - Switch to Z2 on **2022-09-21**; U2's final session **2022-09-19 with
    97 bars** (exact); baseline held-MAP keeps a 09-20 row (held=U2) but the
    BAR-level chain drops the session — 1,745 sessions confirmed on the
    baseline parquet.
- k=5 chain: 27 rolls 2020-2026 (baseline `held_volume_k5.parquet`
  cross-checked).
- **Expiry pointers: 58/68** = 52 official (FXCAL 2010-2022) + 6 from the
  Q5 capture (2024Q3..2025Q4). Missing 10 cells: 2023Q1-Q4, 2024Q1-Q2,
  2026Q1-Q4 — **NOT_OBTAINED, derivation forbidden** (dispatch's 58/68
  reproduced: `q5_independent_verify/verify_q5_captures.json`). All 16
  extracted official lastTrade dates ≥ observed last-bar session (identity
  cross-check clean).

## Dim 4 — Session / holiday — PARTIAL

23h CT continuous template (17:00→16:00, 1380 min, median 1,357 bars/session;
dossier §8). 2023: 2 holiday weekdays (measured). **NOT_OBTAINED**: FX holiday
session TIMES (early-close minutes) 2024-25 — and the in-corpus FXCAL times
2017-2023 remain per-family inputs (JF1/JF3 f4 restated). Holiday-shortened
sessions are excluded by bar-count in the family specs.

## Dim 5 — Event PIT — PARTIAL

- **BoJ: PARTIAL (unchanged, restated — NOT fixed).** 156 statement files
  2011-01-25..2026-09-18 (30 dated decisions 2023-2026) + 17 mpmdeci index
  files 2010-2026. Dates only — **no intraday timestamps in corpus**. Per
  matrix: BoJ stamps = owner decision. JF1's 12:00-15:30 JST anchor stays a
  declared convention with its K3 anchor-robustness law
  (`ja_event_pit.json`).
- **MOF**: 386 daily ops 1991-05-13..2026-05-06 on disk
  (SOURCE_TIDY_RESOLVED; ERRATUM M-1 upheld — cited, not re-litigated).
  Publish-lag law: no same-day PIT signal exists or is claimed.
- **US-side (DFF)**: 16 vintage files (year-end 2010-2024 + 2026-09-30; **no
  2025 vintage**) + latest snapshot (1954-07-01..2026-09-30). Vintage law
  restated: available_time = vintage as-of the decision date; current-calendar
  inference FORBIDDEN.
- **RBA** (cross-asset conditioning): 395 dated decisions 1990-08-02..
  2026-09-30 (2023:11 / 2024:8 / 2025:8 / 2026:6), as-published, dates only.

## Dim 6 — Fee / spread / slippage / BBO — MODELED + NOT_RUN

- Fees (FEES_CORRECTED, P0-VERIFY upheld; FX fee-group mapping PARTIAL):
  all-in **T1 2.46 / T2 2.26 / T3 2.06 / T4 1.86 USD/side** — MODELED COST /
  UNDER REVIEW / **VERIFIED_VS_ACCOUNT=NOT_RUN**.
- Notional arithmetic re-pinned: **12,500,000 × price**; representative price
  0.006383 re-measured from the raw 2026 tail (last bar 2026-09-30 23:59Z)
  → **$79,787.50**.
- **RT T1 / 1-tick = 2 × (2.46 + 25.00 + 6.25) = $67.42 = 8.4499 bp** of
  $79,787.50; tier range 8.30-12.10 bp (full table in
  `6j_orientation_recheck.json`; spread = $25 close-proxy 4 ticks,
  high-biased; slippage tiers {1,2,3} ticks × $6.25). Every input pinned.
- **BBO NOT_RUN stands** — single-level BBOMsg cannot prove fill/queue (D5
  law). True spread, queue, fill probability, slippage: NOT_RUN. Conservative
  fill law binds. Book facts (measured, dossier §3): BoJ decision window
  median 1m vol 34 vs 53 full-day; tokyo_am 59 vs ny_am 120.

## Dim 7 — Trial budget — RESTATED (no new trials)

6J minimal ≈ **29-36** (JF1 11 + JF2 7/host + JF3 11; full-grid 96) per
`synth/CENSUS_FINAL.md`; conventions: 6J6A counts its 3 controls inside
minimal. **No 6J cap defined — explicit owner ceiling required** before any
registration. Families JF1/JF2/JF3 specs unchanged (`jpy_aud_hypotheses.json`).
This lane opened no trial and touched no registry/ledger.

## Dim 8 — Reproduction / A7 — PARTIAL

- This lane's scripts (all under `fx_ja/`, interpreter
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`):
  `fx_ja_lib.py`, `measure_6j.py` (tasks 1-3), `measure_6a_tick.py`,
  `6a_roll_measure.py`, `measure_events.py`, `session_holes_2023.py`,
  `q5_independent_verify/verify_q5_captures.py`. Each JSON output names its
  inputs (absolute paths) and windows; raw parquets are read read-only.
- A7 fee re-verification packet: pending (VERIFY-A7READY lane this round,
  PREPARE ONLY). Account verification NOT_RUN.

---

## Closing line

**Data-ready ≠ scored-authorized.** 6J data is measured, reconciled and
reproducible across identity/tick, coverage, roll mechanics, event dates and
modeled costs — but scored use is **blocked** by: (1) fee
VERIFIED_VS_ACCOUNT=NOT_RUN (A7 + owner-authorized account verification);
(2) BoJ intraday decision stamps NOT_IN_CORPUS (owner decision; JF1 anchor
stays conventional); (3) BBO/fill/queue NOT_RUN (D5 — conservative fill law
binds); (4) official expiries 2023+2026 quarters and FX holiday session times
2024-25 NOT_OBTAINED; (5) volume usable as shares/ratios only (0.455 law).
None of these may be inferred PASS.
