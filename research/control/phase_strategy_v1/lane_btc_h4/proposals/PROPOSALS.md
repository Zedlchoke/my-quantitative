# PROPOSALS — PSV1 / L2_BTC_H4

Cycle `PHASE-STRATEGY-V1`, cell **BTC_H4**. Companion artifacts:
`proposals.json` (authoritative freeze), `ancestry_selfcheck.json`,
`../feasibility/ceiling.json`, `../census/CENSUS.md`.

Proposal law (plan §6): at most ONE strategy per data-sufficient phase, chosen
by economic mechanism — never by scanning results, none of which exist in this
lane. No strategy returns were computed anywhere in this lane (plan §7.3).

## 1. Phase disposition summary

| Phase | Floors | Disposition | Slot |
|---|---|---|---|
| ACCUMULATION | NOT_RUN_THIN_PHASE (F4 decisions 71 < 100, margin −29) | NO_ELIGIBLE_PROPOSAL | FLAT |
| UPTREND | DATA_SUFFICIENT (worst fold +15 eps / +595 dec) | **ONE PROPOSAL** (below) | candidate, pending E1–E6 at integration |
| DISTRIBUTION | NOT_RUN_THIN_PHASE (F1 66, F4 53 < 100) | NO_ELIGIBLE_PROPOSAL (the plan's stricter DISTRIBUTION default would independently force FLAT) | FLAT |
| DOWNTREND | DATA_SUFFICIENT | NO_ELIGIBLE_PROPOSAL (mechanism distance, §3) | FLAT |
| TRANSITION_UNKNOWN | gate state | never traded | FLAT |

Budget: exactly **1 scored cell** consumed if this candidate runs post-GO
(max 15 cycle-wide).

## 2. UPTREND proposal — `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION`

**Mechanism (who is forced to trade, and why it can survive costs).**
The book trades discrete forced-liquidity events inside a confirmed uptrend
phase. (1) *Mechanical covering:* stop-losses and fade entries of sellers rest
just above the trailing 30-bar (5-day) close channel; an H4 close beyond that
channel forces rule-driven buying that is not opinion-driven. (2) *Staged,
late capital:* allocation- and on-ramp-driven flow deploys into confirmed
strength rather than anticipating it, so continuation legs persist after the
break. Cost survival is structural: the book is event-based (~13 round trips
per year), so the 12 bps round-trip stack is paid rarely, and both effects
operate on multi-day horizons (median hold 23 H4 bars ≈ 3.8 days).

**Why it is not a forbidden ancestor (plan §7).**
Not a phase-gated variant of any §7.1 specialist: `UP_TREND_SLOW_LONG` was a
*continuous* hold; this book is in the market only after discrete channel
events (measured exposure ≈ 14% of bars) with a structural channel stop.
Not `ACC_FLAT_BREAKOUT_WAIT` (different phase, and that class *waits* — this
book trades the event). Not any §7.2 dead mechanism: measured signal-series
rho (daily-sampled, V2 D2 convention, pre-PnL) against every
price-reconstructible BTC dead shadow is within the 0.20 bar —

| Dead shadow | rho | n days | Verdict |
|---|---|---|---|
| close_displace_fade | −0.017 | 2,447 | WITHIN_BAR |
| rev24_leg | −0.149 | 2,456 | WITHIN_BAR |
| run_imbalance | +0.168 | 2,456 | WITHIN_BAR (worst case) |
| amihud_illiq | −0.081 | 2,447 | WITHIN_BAR |
| OI_level / OI_share_stoch / generic_dvol_shock / pair_spread_trend | `NOT_MEASURED_WITH_REASON` | — | observables do not exist in this cell (price/volume only; single instrument); mechanism-class distance documented in `pipeline/config.py` |

**Frozen contract (full detail in `proposals.json`).**

- Direction long only, sizing fraction 1.0, BTCUSDT-PERP.
- Entry: at H4 close t — UPTREND gate ON (phase label within last 6 bars),
  flat, and `close_t > max(close[t−30..t−1])` → fill next H4 open; entries
  whose fill would cross a fold boundary are skipped.
- Exit (first of): DONCHIAN_STOP `close_t < min(close[t−15..t−1])`;
  GATE_INACTIVE (6 consecutive bars without a UPTREND label); MAX_HOLD 450
  bars; fold end force-flat. Min-dwell 12 bars (2 days) suppresses all exit
  triggers — *including the stop* — before 12 bars held; that risk window is
  disclosed and frozen as implemented.
- Execution: decision at H4 close, fill next H4 open, no mid-bar fills;
  PIT convention (retrospective Vision snapshots, knowable at close, next-open
  fill) disclosed in every artifact.
- Churn law: no-op law structurally enforced — same-direction label noise
  inside the 6-bar gate buffer produces ZERO fills (exit requires 6
  consecutive non-phase bars; re-entry requires a fresh entry event; fixture
  tested). Counters: switches per phase transition 0.95 (≤ 1 by construction);
  re-entries within one gate-buffer of an exit: 8 (genuine episode relapses,
  disclosed — not noise fills).
- Costs: taker 5 + slippage 1 = 6 bps/side, 12 bps round trip; funding
  1.377e-5 per 8h signed by position (median 11 boundaries/trade); tier
  multipliers 1.0/1.5/2.0 on the FULL stack. Measured cadence: per-trade cost
  at 1.5x ≈ 20.4 bps vs the 100 bps preregistered plausible-edge bound —
  `PASS_WITHIN_CEILING` (~5x headroom). Capacity: deepest crypto perp venue,
  1.0 notional, ~14% time-in-market — no capacity constraint at research scale.
- **Preregistered falsification control (semantics fixed before any scored
  result):** phase-shuffled matched control — permute the UPTREND gate labels
  within each fold in non-overlapping 30-H4-bar blocks (preserves occupancy,
  destroys phase↔break timing), re-run the identical Donchian book on real
  prices. Q-11 movement validation: control must produce ≥50% of the
  candidate's entry count, else the control is invalid (disclosed; null rests
  on G1–G5). Control out-earning the candidate at 1.0x ⇒ KILL (G6).
- Expected failure interpretation (preregistered): killed by control ⇒ any
  edge is phase-gating-generic, not channel-event-specific; fails G1/G2 ⇒ cost
  stack dominates; fails G4/G5 ⇒ single-era dependence (expected suspect: F1
  2020–21 expansion). Any of these is a valid terminal finding — never a
  parameter-rescue trigger.

## 3. DOWNTREND — NO_ELIGIBLE_PROPOSAL (meets floors; mechanism distance)

DOWNTREND is data-sufficient (85 episodes; all folds ≥ 12 eps / 308 dec), but
every economically natural book in this phase lands on a measured-dead or
forbidden class: shorting the phase = `DOWN_SHORT_BTC` (§7.1); stepping
aside/de-risking = `DOWN_FLAT_RISKOFF` (§7.1); buying post-cascade
stabilization = short-horizon reversal / `close-displace-fade` class (§7.2,
measured dead on this program). No remaining mechanism with a
forced-counterparty story is constructible from this cell's price/volume
observables. A phase with no testable strategy is a valid result (plan §0).
Slot FLAT.

## 4. Thin phases — NOT_RUN_THIN_PHASE

ACCUMULATION (F4 decisions 71 < 100) and DISTRIBUTION (F1 66 / F4 53 < 100)
fail the immutable per-fold decision floor; margins reported in CENSUS.md,
floors never relaxed, phases never pooled with BTC_H1 or any other cell.
A mechanism draft for ACCUMULATION (capitulation-exhaustion drift long) was
carried through event-counting only and is explicitly NOT a proposal.
DISTRIBUTION additionally carries the plan's stricter default: no explicit
evidenced forced-counterparty mechanism exists in klines observables ⇒ FLAT
regardless of floors.

## 5. Identity and lineage

- family_id `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION`, arm_id
  `…@freeze1`; arm_config_digest computed by A1 at integration from the frozen
  constants (`pipeline/config.py`) plus `proposals.json`.
- Data lineage: `data/manifest.json` (182 sha256-pinned files) →
  `data/data_gate.json` → `freezes/*` → `census/census.json` →
  `feasibility/ceiling.json` → this freeze.
- Ancestry adjudication is A1's at integration; this lane's measured rho table
  and class-distance arguments are recorded above.
