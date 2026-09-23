# CENSUS — cell BTC_H1 (lane L1, cycle PHASE-STRATEGY-V1)

Deterministic, PIT, code-owned phase census on Binance Vision BTCUSDT-PERP
1h bars (2020-01-01T00:00Z → 2026-09-22T23:00Z open; last complete hour
closes 2026-09-23T00:00Z). 58,968 bars retrieved; **zero** interior gaps,
zero duplicate timestamps, zero OHLC sanity violations, 1 zero-volume bar.
Rule and folds as frozen in `freezes/phase_rule_freeze.json` and
`freezes/era_fold_freeze.json` (both written before any history-wide
computation). Machine-readable twin: `census.json`.

> **PIT disclosure**: Vision klines are retrospective exchange snapshots
> (retrieved 2026-09-23; no per-bar publication timestamps). A bar is
> knowable at its close; the first executable fill is at the NEXT bar open.
> Every label uses only bars closed at or before decision time. This is S0
> discovery (`DISCOVERY_ON_NEVER_COMPUTED_HISTORY`), not OOS. No strategy
> PnL exists anywhere in this lane.

> **INCIDENT XCHECK-FAIL (disclosed in full in `data/manifest.json`)**: the
> mandatory cross-check of the frozen 15m catalog (sha
> `81d4f147…8321`, verified) resampled to 1h vs the Vision 1h series FAILED
> at the pre-declared tolerance. Forensics prove the comparison is correctly
> aligned (shift-scan optimum at 0h; close correlation 0.999969; both volume
> fields decode sanely via VWAP-in-range) and that the catalog itself is not
> a complete/consistent trade record of the instrument over the overlap
> (per-hour volume differs ~12x at the median; per-day ratios 0.01–32x;
> close diffs reach ±6,800). No smoothing, no tolerance relaxation. The
> plan-prescribed scored source (Vision, integrity PASS) proceeds; A1 must
> adjudicate this incident at integration.

## Phase rule (frozen)

Wilder ADX(14)/±DI(14) + SMA720(close) on the UTC hourly grid, raw-label
total partition → 24-bar persistence state machine (hysteresis):

- warmup (< 720 bars) → TRANSITION_UNKNOWN (insufficient evidence)
- ADX in (18, 22) → TRANSITION_UNKNOWN (explicit margin)
- ADX ≥ 22: DI+ ≥ DI− → UPTREND (tie→UP), DI− > DI+ → DOWNTREND
- ADX ≤ 18: close ≥ SMA720 → DISTRIBUTION (tie→DIST), else ACCUMULATION

## Eras / folds (frozen; fold k = era k)

Post-warmup window starts 2020-01-31T00:00Z (bar index 720).
F1 = 2020-01-31→2021-05-01 (10,944 bars) · F2 = 2021-05→2023-01 (14,640) ·
F3 = 2023-01→2025-01 (17,544) · F4 = 2025-01→data end (15,120).
Fold ends force-flat. F4 contains 2025-08→2026-08 which overlaps the frozen
V2 15m catalog (outcome-observed corpus) — disclosed; no V2 artifact read.

## Census headline (post-warmup, 58,248 bars)

| phase | episodes | margin vs 20 | decisions | share | dec/fold min | dwell p25/med/p75/max (bars) | floors |
|---|---|---|---|---|---|---|---|
| ACCUMULATION | 69 | +49 | 6,458 | 11.1% | 604 | 47 / 66 / 104 / 391 | PASS |
| UPTREND | 172 | +152 | 20,411 | 35.0% | 3,812 | 60 / 95.5 / 152.5 / 551 | PASS |
| DISTRIBUTION | 75 | +55 | 6,295 | 10.8% | 731 | 45 / 67 / 111 / 294 | PASS |
| DOWNTREND | 190 | +170 | 24,913 | 42.8% | 5,109 | 63 / 104 / 172.75 / 473 | PASS |
| TRANSITION_UNKNOWN | 3 | **−17** | 171 | 0.3% | 0 | 43.5 / 63 / 73.5 / 84 | **THIN** |

- Episode floors per fold (≥3): all four market phases pass in every fold
  (min: DISTRIBUTION F2 = 10; ACC F1 = 8; UP min 33; DOWN min 39).
- Decision floors per fold (≥100): all four phases pass with large margins
  (min: DISTRIBUTION F2 = 731).
- TRANSITION_UNKNOWN is NOT_RUN_THIN_PHASE (3 episodes; margin −17; F3 has
  zero UNKNOWN bars). With the frozen margin band (18–22) sub-24-bar
  uncertainty excursions are absorbed by the state machine by design; the
  sustained-uncertainty state is genuinely rare on this cell. Slot = FLAT.
  This is a valid result, reported with margin, not pooled with anything.
- Occupancy by fold (ACC/UP/DIST/DOWN/UNK): F1 5.5/34.8/12.2/46.7/0.8% ·
  F2 13.2/36.7/5.0/44.9/0.2% · F3 10.2/34.7/15.3/39.8/0.0% ·
  F4 14.0/33.9/10.3/41.3/0.4%.
- State-label transitions (all types): 505. Longest UNKNOWN run: 84 bars
  (F1); longest-run-per-fold 84/24/0/63.
- 15 truncated episodes at fold edges (counted, flagged, not merged).

## ±1-notch label-agreement table (one-shot, reported not iterated)

Post-warmup state-label agreement with the frozen base:

| variant | agreement |
|---|---|
| adx_threshold 19.0 | 90.8% |
| adx_threshold 21.0 | 93.5% |
| adx_margin 1.0 | 93.2% |
| adx_margin 3.0 | 89.1% |
| transition_buffer 12 | 63.7% |
| transition_buffer 48 | 50.9% |

Decision-knob notches (threshold/margin) preserve ≥89% of labels — the
partition is stable. The buffer notch moves labels more (50–64%) because it
changes state-machine memory, mostly re-timing adoptions rather than
re-classifying regimes. Reported once; no parameter was re-chosen after
seeing this table (freeze law).

## Ancestry self-check (plan §7; one-shot, signal-level, no PnL)

Position-book series of each frozen candidate vs reconstructible dead
shadows (Pearson rho on the common grid; shadows reconstructed by name
assumptions documented in `code/ancestry.py`):

| candidate | rev24_reversal | close_displace_fade | amihud_illiquidity |
|---|---|---|---|
| UPTREND-BREAKOUT_CONT | −0.076 | −0.048 | −0.053 |
| ACC-FLOOR_PROVISION | −0.007 | −0.001 | −0.066 |
| DOWNTREND-BREAKDOWN_CONT | −0.047 | −0.027 | −0.082 |

All |rho| ≤ 0.082 — comfortably distinct under the E3 reading of the 0.20
bar (|rho| ≤ 0.20 ⇒ distinct; the plan §7.2 parenthetical states the bar
inversely; the ambiguity is recorded in `census.json.ancestry.bar_reading`
for A1 adjudication). NOT measured, with reason + mechanism-class distance:
run_imbalance (needs trade-direction data), OI-level/OI-share/stoch (needs
open interest), generic DVOL shock (needs DVOL), pair-spread-trend
composites (needs a second asset). No candidate is a §7.1 RSM-V1 specialist
or a phase-gated variant of one (argument per proposal in
`proposals/PROPOSALS.md`); no V2 Jev label was read.
