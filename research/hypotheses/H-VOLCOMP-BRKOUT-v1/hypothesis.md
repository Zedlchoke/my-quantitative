# H-VOLCOMP-BRKOUT-v1 — Volatility compression → breakout

**Family:** `volatility_compression_breakout` · **State:** `SPEC_DRAFT` (PLAN §6) ·
**Owner:** A4 · **Candidate version:** 1 · **Split policy:** `S0_chrono3fold`

## Motivation (from negative results, not a resurrection)

Scan matrix 2026-08-23 (`results/scan_matrix/20260823T051806Z/`) produced
**0/60 PASS under strict gates**: 58 testable combos, all q=1.0 after BH-FDR.
The near-winners are mean-reversion/pullback shapes (`NEAR reclaim_mr`,
`BOME trend_pullback`, `ADA markdown`) — i.e. the current inventory is entirely
*fade* shaped; there is no expansion-leg strategy in the frozen inventory that
buys squeeze resolution. NOTES §15.2 already flags "markup onset" as a phase
where chasing is dangerous *without* a coil precondition — this hypothesis adds
exactly that precondition and is pre-registered as a NEW candidate before any
scored run.

## Economic mechanism

A Bollinger band-width percentile at the bottom of its trailing distribution is
the canonical signature of consensus/deleveraging: volatility sellers dominate,
range stops accumulate just outside the coil. When price closes above the
96-bar high with an expansion-volume burst, the marginal buyer is a stop order
or a late chaser; the strategy buys from the sellers exhausted during the coil.
The counterparty is the breakout chaser who pays the post-expansion spread.

## Rules summary (frozen; see candidate.yaml for exact text)

1. **Compression gate** — range-normalized rank (0..100; 0 = tightest edge of
   the window, tie-robust under coiled markets) of the previous closed bar's
   bandwidth ≤ 25 within its full trailing `squeeze_lookback` window ({96,192}).
2. **Trigger** — close > max(high of previous 96 bars).
3. **Confirm** — bar volume ≥ {1.5, 2.0} × SMA20(volume).
4. **Risk house style** — stop = 1.5×ATR at fill, TP = 2R; exit also on close
   back below the Bollinger basis; engine daily-loss/cooldown limits apply.
5. Long-only; S0 seven symbols; 15m closed bars only (no lookahead: trailing
   structures exclude the trigger bar).

## Pre-registered trial budget (frozen NOW, before any run)

| knob | values |
|---|---|
| `squeeze_lookback` | 96, 192 |
| `volume_min_ratio` | 1.5, 2.0 |

→ exactly **4 combinations MAX**, plus fixed params (bb 20/2.0, pct ≤ 25,
Donchian 96, vol-SMA 20, ATR 14, stop 1.5×ATR, TP 2R). Any spec change creates
`H-VOLCOMP-BRKOUT-v2`; v1 parameters are never edited silently.

## Invalidating evidence

- Edge disappears at +50% fee stress while baseline positive → reject as cost artifact.
- Positive folds < 2/3 under `S0_chrono3fold`.
- Aggregate PF < 1.10, any fold PF < 0.80 with ≥5 trades, or >50% single-fold PnL concentration.
- Positive result driven by one symbol only (universe artifact, not mechanism).

## Data / feasibility

- 15m bars for the S0 seven in `catalog_live_crypto` (common intersection ~1y
  multi-symbol; per-symbol 2024-08 → 2026-08). Warmup ≥ 200 bars declared (320).
- No funding/OI dependency → not blocked by the ~30d OI overlay limit.

## Explicitly out of scope

No short side, no regime gate beyond the pre-registered compression definition,
no per-symbol parameters. Near-winners from the scan are cited as motivation
only and stay labeled **EXPLORATORY**.
