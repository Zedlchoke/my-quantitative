# H-FUNDCROWD-MR-v2 — Funding-crowding gated reclaim mean-reversion

**Family:** `funding_crowding` · **Feature:** `point_in_time_funding_percentile` ·
**State:** `SPEC_DRAFT` (A1 locks) · **Owner:** A4 · **Candidate version:** 2 ·
**Prior family trials:** 0 (v1 was spec-only, never scored) ·
**Split policy:** `S0_chrono3fold` · **Stage:** `S0_EXPLORATORY`

## Motivation

The V1 77-combo scan ended 0-PASS and the post-mortem plus the fill-timing
challenge memo showed that what survives strict gates is *fade* shaped — but
plain mean-reversion bleeds exactly when the crowd is one-sided: entries taken
into funding extremes pay carry while held and meet forced-deleveraging
air-pockets if price stalls. H-FUNDCROWD-MR-v1 proposed gating reclaim-MR with
a funding percentile but was never implemented; PLAN §11 corrected its
contract (family renamed, OI removed, budget fixed at 3). This version is that
corrected contract, implemented before any scored run.

## Economic mechanism

Funding transfers are largest when positioning is one-sided. A latest settled
rate in the upper tail of its trailing distribution marks crowded longs: they
pay elevated carry and unwind violently into adverse moves. Mean-reversion
longs entered there face negative carry plus unwind asymmetry; the same
reclaim signal taken when carry terms are neutral-to-favourable keeps the
reversion edge without the tail. Shorts mirror at the lower tail. The
counterparty is the over-leveraged crowded-side holder who must unwind, and
the late MR chaser who enters without any crowding check.

## Gate semantics (exact, pre-registered)

At `decision_ts` = **the current signal bar's CLOSE timestamp** (`bar.ts_event`,
moment of decision), query `FundingPIT.percentile_asof(decision_ts,
window_days=30)`:

| side | condition | action |
|---|---|---|
| LONG | `percentile > threshold_p/100` | BLOCKED |
| LONG | `percentile <= threshold_p/100` | allowed |
| SHORT | `percentile <= (100-threshold_p)/100` | BLOCKED |
| SHORT | `percentile > (100-threshold_p)/100` | allowed |
| any | PIT returns None / unavailable | BLOCKED both sides, fail-closed, counter incremented |

PIT-strict by construction: only settlements already published at or before
the decision timestamp can be observed (8h settlement lag respected, no
forward-fill). Boundary asymmetry (long strict `>`, short inclusive `<=`) is
intentional spec text and pinned by unit tests.

Base entry/exit stays frozen: Bollinger reclaim + RSI extreme inside the
VHF/ADX/volume range gate and phase gate; stop 1.5×ATR, TP 2×; engine
daily-loss/cooldown limits unchanged. HTF filter fixed ON for all combos.
OI never touches the signal in this version.

## Pre-registered trial budget (frozen NOW, before any run)

| knob | values |
|---|---|
| `threshold_p` | 70, 75, 80 |

→ exactly **3 combinations** (`thresholds × htf_filter=true`, `oi_overlay=false`),
plus frozen baseline params (bb 20/2.0, RSI 2 @ 15/85, VHF 28 ≤ 0.25,
ADX 14 ≤ 20, vol-SMA 20 ≤ 1.8×, stop 1.5×ATR, TP 2×, history_days 220,
warmup 320 bars). Any spec change creates v3; v2 parameters are never edited
silently.

## Quantitative invalidation (any one ⇒ REJECT this family version)

- aggregate after-cost expectancy ≤ 0 on the scored window;
- aggregate position PF < 1.10 on the scored window;
- positive folds < 2/3 on the scored window (after cost).

Supporting: fold PF < 0.80 with ≥5 trades; single-fold PnL concentration >50%;
gated variant not beating the ungated baseline on identical folds; failure
under +50% fee stress or one-bar-delayed-entry stress. Fewer than 20 closed
trades total ⇒ INCONCLUSIVE, never PASS. Allowed outcomes only: `REJECTED`,
`INCONCLUSIVE`, `STAGE_A_PASS_EXPLORATORY`, `LOCK_FOR_FUTURE_S1`.

## Implementation & feasibility

- Wrapper module `strategy_funding_crowding_mr.py`: subclasses the frozen
  `ReclaimMeanReversionStrategy`; records each bar's close ts as
  `decision_ts`, interposes the gate in front of `_submit_entry`. Baseline
  module untouched.
- Feature dependency: `research/funding_pit.py` (`FundingPIT`), injected via
  constructor arg; default lazily built from `funding_data/scan_2026`.
- Data (H14 resolved): ETH trimmed start 2025-08-21T14:30Z; continuous clean
  intersection `[2025-08-21T14:30Z, 2026-08-21T00:00Z]`; funding COMPLETE for
  all S0-seven symbols.
- Tests: `tests/test_funding_crowding_mr.py` — 16 tests (grid freeze, exact
  boundary math, fail-closed counters, no-lookahead timestamp proof, config
  factory with `allow_short=True` passthrough). Full suite green (277).

## Explicitly out of scope

No OI input (that would be a new candidate version named
`funding_oi_crowding` with publication-delay evidence); no per-symbol
parameters; no threshold outside {70,75,80}; no tuning of the frozen baseline
block; this is nested S0 exploratory selection — never S1/OOS.
