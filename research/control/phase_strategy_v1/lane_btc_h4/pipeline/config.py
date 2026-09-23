"""PSV1 lane_btc_h4 frozen configuration.

EVERY constant in this file was fixed BEFORE any history-wide measurement
(plan §5.3: round domain-standard constants fixed before scoring; no PnL
exists anywhere in this lane). This file is the single source of truth for
the phase rule, eras/folds, floors, proposal constants and the cost model.

Cell: BTC_H4 — BTCUSDT-PERP, 4-hour UTC buckets, derived from Binance Vision
1h klines (aggregated-from-1h is the SCORED representation; native Vision 4h
zips are a shadow cross-check only).

Outcome-blindness (plan §7.3): census = counts/occupancy/dwell/transition
statistics ONLY; feasibility = signal-event counting ONLY. No strategy
returns/equity/PnL path exists in this lane. 'return' appears below only as
Python statements and price rel-diff observables, never as strategy results.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------
CELL = "BTC_H4"
LANE = "L2_BTC_H4"
CYCLE_ID = "PHASE-STRATEGY-V1"
TASK_ID = "psv1-l2-btc-h4"
SYMBOL = "BTCUSDT"
INSTRUMENT_IDENTITY = "BTCUSDT-PERP.BINANCE (USDT-M perpetual, matches V2 catalog instrument)"
CLOCK = "UTC"
DISPATCH_SHA = "6e6ffa3bb1c6ad82fb1771b99abdecfb0bedf849"

# ---------------------------------------------------------------------------
# Data gate (plan §9.1) — Binance Vision keyless USDT-M klines
# ---------------------------------------------------------------------------
BASE_URL = "https://data.binance.vision/data/futures/um"
FIRST_MONTH = "2020-01"           # probe confirmed HTTP 200 from 2020-01; 2019-12 monthly is 404
DATA_RETRIEVED_AT = "2026-09-23"  # retrospective exchange snapshots; no per-bar publication timestamps

PIT_CONVENTION = (
    "Vision klines are retrospective exchange snapshots (retrieved 2026-09, "
    "no per-bar publication timestamps). Frozen convention: a bar is knowable "
    "at its close; first executable fill at the NEXT H4 bucket open."
)

H4_MS = 4 * 3600 * 1000
H1_MS = 3600 * 1000

# Integrity law (fail-closed)
GAP_TOLERANCE_FRAC = 0.0005          # interior missing 1h slots <= 0.05% of calendar
GAP_MAX_RUN_H1 = 4                   # any interior missing run > 4 consecutive 1h slots => BLOCKED
PRICE_ATOL = 1e-8                    # OHLC sanity tolerance (relative 0; prices are decimal strings)

# Frozen 15m catalog cross-check (read-only reuse; digest verified 2026-09-23)
CATALOG_PARQUET = (
    "/Users/hoangminhlong/my-quantitative/catalog/data/binance_bar/"
    "BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL/"
    "2025-08-20T02-34-14-475394000Z_2026-08-20T02-34-14-475394000Z.parquet"
)
CATALOG_SHA256 = "81d4f147c6bc6a8e03275140a65ac06a63c2e644f449f1c48d8758b187fc8321"
CATALOG_CHECK_ATOL_PRICE = 1e-6
CATALOG_CHECK_RTOL_VOL = 1e-6

# 4h native shadow cross-check tolerance: OHLC relative tolerance, volume tolerance
SHADOW_PRICE_RTOL = 1e-9
SHADOW_VOL_RTOL = 1e-9

# Deterministic re-retrieval verification sample (fixed before download)
RERETRIEVAL_SAMPLE = 3

# ---------------------------------------------------------------------------
# Phase rule (plan §5) — frozen BEFORE any history-wide measurement
# ---------------------------------------------------------------------------
# Observables on H4 close series (UTC), all causal (bars with close <= t):
#   sma_t   = SMA(close, N_SMA)
#   slope_t = sma_t / sma_{t-M_SLOPE} - 1
#   side_t  = close_t / sma_t - 1
# Quadrants (both dead-bands clear):
#   slope>0, side<0  -> ACCUMULATION   (price below rising average: recovery from decline)
#   slope>0, side>0  -> UPTREND
#   slope<0, side>0  -> DISTRIBUTION   (price above falling average: late-stage advance fading)
#   slope<0, side<0  -> DOWNTREND
# Uncertainty (explicit, code-owned; never model abstention):
#   U1 warmup incomplete; U2 |slope| < DEADBAND_SLOPE; U3 |side| < DEADBAND_SIDE;
#   U4 confirmation: raw state must repeat CONFIRM consecutive bars, else TRANSITION_UNKNOWN.
N_SMA = 120            # H4 bars (20 days)
M_SLOPE = 30           # H4 bars (5 days)
DEADBAND_SLOPE = 0.01  # 1% over 30 bars
DEADBAND_SIDE = 0.01   # 1% close vs SMA
CONFIRM = 3            # consecutive identical raw states
WARMUP = N_SMA + M_SLOPE + CONFIRM  # = 153 H4 bars

PHASES = ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND", "TRANSITION_UNKNOWN"]
TRADED_PHASES = ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"]

# +-1 notch ladder (reported as label-agreement sensitivity, NEVER optimized)
NOTCH_LADDER = {
    "N_SMA": [N_SMA - 10, N_SMA, N_SMA + 10],
    "M_SLOPE": [M_SLOPE - 5, M_SLOPE, M_SLOPE + 5],
    "DEADBAND_SLOPE": [DEADBAND_SLOPE - 0.005, DEADBAND_SLOPE, DEADBAND_SLOPE + 0.005],
    "DEADBAND_SIDE": [DEADBAND_SIDE - 0.005, DEADBAND_SIDE, DEADBAND_SIDE + 0.005],
    "CONFIRM": [CONFIRM - 1, CONFIRM, CONFIRM + 1],
}

# ---------------------------------------------------------------------------
# Eras and folds (plan §4.1 — public calendar anchors, NEVER moved)
# ---------------------------------------------------------------------------
ERAS = [
    {"era": "ERA-B1", "label": "post-halving expansion I", "start": "2020-01-01", "end": "2021-04-30"},
    {"era": "ERA-B2", "label": "contraction I", "start": "2021-05-01", "end": "2022-12-31"},
    {"era": "ERA-B3", "label": "post-halving expansion II", "start": "2023-01-01", "end": "2024-12-31"},
    {"era": "ERA-B4", "label": "current regime", "start": "2025-01-01", "end": None},  # end = data_end
]
# 4 eras => fold boundaries land on era boundaries (plan §4.3)
FOLD_LAW = "F_i = ERA-Bi (post-warmup); fold ends force-flat for signal segmentation."

# ---------------------------------------------------------------------------
# Floors (immutable, plan §4.3)
# ---------------------------------------------------------------------------
FLOOR_EPISODES_CELL = 20   # >= independent episodes / phase / cell total
FLOOR_EPISODES_FOLD = 3    # >= independent episodes / phase / fold
FLOOR_DECISIONS_FOLD = 100 # >= eligible decisions / phase / fold

# ---------------------------------------------------------------------------
# Proposal constants (frozen BEFORE any history-wide measurement)
# ---------------------------------------------------------------------------
EXIT_BUFFER_BARS = 6    # phase-gate hysteresis: episode ends after 6 consecutive non-phase bars
MIN_HOLD_BARS = 12      # 2 days: churn law (>= phase-rule dwell margin CONFIRM=3)
MAX_HOLD_BARS = 450     # 75 days: safety force-exit
DONCH_ENTRY = 30        # H4 bars: entry channel (close > max of prior 30 closes) — UPTREND only
DONCH_STOP = 15         # H4 bars: exit channel (close < min of prior 15 closes) — UPTREND only

SIZING_FRACTION = 1.0   # V2 accounting
EXECUTION_LAW = "decision at H4 close, fill at NEXT H4 bucket open, no mid-bar fills"

# ---------------------------------------------------------------------------
# Cost model (BTC; frozen; synthetic unit fixtures in tests_py)
# ---------------------------------------------------------------------------
TAKER_FEE_BPS = 5.0
SLIPPAGE_BPS = 1.0
COST_PER_SIDE_BPS = TAKER_FEE_BPS + SLIPPAGE_BPS      # 6 bps
COST_ROUND_TRIP_BPS = 2 * COST_PER_SIDE_BPS           # 12 bps
FUNDING_PER_8H = 1.377e-5                             # fraction of notional, signed by position
FUNDING_INTERVAL_H = 8
COST_TIERS = [1.0, 1.5, 2.0]                          # multiplier applies to the FULL stack

# Feasibility ceiling (plan §11): cadence-based arithmetic, no strategy PnL
PLAUSIBLE_EDGE_BPS = 100.0  # preregistered plausible gross edge bound per trade for an
                            # H4-cadence phase book; cadence whose 1.5x per-trade cost
                            # exceeds this is STRUCK_BY_CEILING

# ---------------------------------------------------------------------------
# Ancestry (plan §7) — dead shadows for crypto/BTC
# ---------------------------------------------------------------------------
RHO_BAR = 0.20
SHADOW_WINDOWS = {
    "close_displace_fade": {"disp": 6, "z": 60},   # z-scored 24h displacement, sign-faded
    "rev24_leg": {"disp": 6},                      # 24h (6xH4) reversal per-leg, sign-flipped
    "run_imbalance": {"win": 12},                  # signed bar-run imbalance, 12-bar window
    "amihud_illiq": {"win": 60},                   # |ret|/quote-volume level, z-scored
}
SHADOW_NOT_MEASURED = {
    "OI_level": "open interest is not in the kline cell data (price/volume only); mechanism class: derivatives positioning flow, not reconstructible from this cell",
    "OI_share_stoch": "open interest share/stoch needs OI + price cross-sections; not in cell data",
    "generic_dvol_shock": "DVOL (Deribit implied vol index) is a cross-venue observable; not in cell data",
    "pair_spread_trend": "requires a second instrument; this cell is single-instrument BTCUSDT-PERP",
}
