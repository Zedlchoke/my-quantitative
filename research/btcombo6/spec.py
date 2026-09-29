"""Frozen constants for BTC-COMBO6-SCORED-V1 — single source of truth.

Everything here is pinned by the plan (plans/PLAN_btc_combo6_scored_v1.md)
and the A1 dispatch packet. No CLI overrides exist for any of these values.
"""
from __future__ import annotations

import pandas as pd

CYCLE_ID = "BTC-COMBO6-SCORED-V1"
ENGINE_VERSION = "btcombo6-engine@1"

# ---------------------------------------------------------------------------
# Fold calendar.
#
# FOLD ERRATUM 2026-09-29: plan §4 prose said "F10 ends 2025-12-26"; correct
# Monday-aligned 10x26w end is 2025-12-29 (DATA-VERIFY measured delta
# 1817d = 259w+4d). 2021-01-04T00:00Z is a Monday; +260 weeks = 260*7d =
# 1820d later = 2025-12-29T00:00:00Z (Monday), NOT 2025-12-26. The
# programmatic calendar below is authoritative; A1 lands the plan erratum
# before code freeze (dispatch amendment 2026-09-29).
# ---------------------------------------------------------------------------
F1_START = pd.Timestamp("2021-01-04T00:00:00Z")
N_FOLDS = 10
FOLD_WEEKS = 26
FOLD_TD = pd.Timedelta(weeks=FOLD_WEEKS)
FOLD_STARTS = [F1_START + i * FOLD_TD for i in range(N_FOLDS)]
EVAL_END = F1_START + N_FOLDS * FOLD_TD          # 2025-12-29T00:00:00Z
SEALED_TAIL_START = EVAL_END                     # loaded+digested, NEVER evaluated

FOLDS = [
    {"fold": f"F{i + 1}", "i": i, "start": FOLD_STARTS[i],
     "end": FOLD_STARTS[i] + FOLD_TD}
    for i in range(N_FOLDS)
]
FOLD_NAMES = [f["fold"] for f in FOLDS]

# ---------------------------------------------------------------------------
# Legs (owner screenshots, verbatim transcription; plan §1 table).
# SMA windows are TIME windows in 5m bars on the 5m close master
# (min_periods=window; NaN -> signal ineligible).
# RSI periods are bar-counts on the emitted (complete-bucket) 15m close series.
# ---------------------------------------------------------------------------
LEGS = {
    "LEG-1": {
        "leg": "LEG-1", "name": "MOM4H-1PCT", "family": "MOM4H-1PCT",
        "clock": "5m", "rule": "momentum_state_change",
        "mom_bars": 48, "mom_threshold": 0.01,
        "tp": 0.010, "sl": 0.010,
    },
    "LEG-2": {
        "leg": "LEG-2", "name": "MAS-4H24H-TURN", "family": "MAS-4H24H-TURN",
        "clock": "4h", "rule": "sma_spread_cross",
        "fast_bars": 48, "slow_bars": 288,
        "tp": 0.080, "sl": 0.030,
    },
    "LEG-3": {
        "leg": "LEG-3", "name": "MAS-12H72H-TURN", "family": "MAS-12H72H-TURN",
        "clock": "4h", "rule": "sma_spread_cross",
        "fast_bars": 144, "slow_bars": 864,
        "tp": 0.080, "sl": 0.040,
    },
    "LEG-4": {
        "leg": "LEG-4", "name": "MAC-2H8H", "family": "MAC-2H8H",
        "clock": "15m", "rule": "sma_spread_cross",
        "fast_bars": 24, "slow_bars": 96,
        "tp": 0.080, "sl": 0.030,
    },
    "LEG-5": {
        "leg": "LEG-5", "name": "RSI-20-55", "family": "RSI-20-55",
        "clock": "15m", "rule": "rsi_cross",
        "rsi_fast": 20, "rsi_slow": 55,
        "tp": 0.080, "sl": 0.030,
    },
    "LEG-6": {
        "leg": "LEG-6", "name": "MAT-2H12H", "family": "MAT-2H12H",
        "clock": "1h", "rule": "sma_spread_cross",
        "fast_bars": 24, "slow_bars": 144,
        "tp": 0.080, "sl": 0.040,
    },
}
LEG_IDS = list(LEGS)

CLOCK_PANDAS_RULE = {"15m": "15min", "1h": "1h", "4h": "4h"}
CLOCK_TD = {
    "5m": pd.Timedelta(minutes=5), "15m": pd.Timedelta(minutes=15),
    "1h": pd.Timedelta(hours=1), "4h": pd.Timedelta(hours=4),
}
CLOCK_EXPECTED_5M = {"15min": 3, "1h": 12, "4h": 48}

# ---------------------------------------------------------------------------
# Common execution law.
# ---------------------------------------------------------------------------
NOTIONAL_PER_ENTRY = 10_000.0     # USD, per entry, every leg (D5)
SLEEVE_START_EQUITY = 10_000.0    # USD, per sleeve
N_SLEEVES = 6
COMBO_START_EQUITY = 60_000.0     # USD, equal-weight sum of sleeves

FEE_BPS = 5.0                     # taker, DECLARED (CHR3F frozen posture)
HALF_SPREAD_BPS = 1.0             # DECLARED_PESSIMISTIC
COST_PER_SIDE_BPS = FEE_BPS + HALF_SPREAD_BPS   # 6.0 bps/side
STRESS_TIERS = (1.0, 1.5, 2.0)    # on fee+spread only; funding unstressed


def cost_per_side(stress: float) -> float:
    """Decimal cost per side at a stress tier (fee + half-spread only)."""
    return (COST_PER_SIDE_BPS / 1e4) * float(stress)


# ---------------------------------------------------------------------------
# Non-vacuity + verdict bars (plan §4/§6).
# ---------------------------------------------------------------------------
MIN_TRADES_NON_VACUOUS = 30
PF_BAR = 1.25
NET_POSITIVE_FOLDS_BAR = 7        # of 10
MAX_DD_PCT_BAR = 0.25             # of COMBO_START_EQUITY for P4
SINGLE_FOLD_SHARE_BAR = 0.5       # P6: no single fold > 50% of combo net

# ---------------------------------------------------------------------------
# Data locations (relative to the cycle worktree root).
# ---------------------------------------------------------------------------
KLINE_DIR_REL = "research/control/bear_opportunity_recon_2026-09/killer_a4/dl5m"
FUNDING_PARQUET_REL = (
    "research/control/bear_opportunity_recon_2026-09/data_a2/funding_events.parquet"
)
CONTROL_DIR_REL = "research/control/BTC-COMBO6-SCORED-V1"
STAGING_DIR_REL = f"{CONTROL_DIR_REL}/staging"
MANIFEST_REL = f"{STAGING_DIR_REL}/data_manifest.json"
M5_CACHE_REL = f"{STAGING_DIR_REL}/m5_panel.parquet"
DRY_DIR_REL = f"{CONTROL_DIR_REL}/dry_run"
SCORED_DIR_REL = f"{CONTROL_DIR_REL}/scored"
LEDGER_REL = f"{CONTROL_DIR_REL}/TRIAL_LEDGER.jsonl"


def fold_calendar_block() -> dict:
    """Serializable fold calendar (goes into record ids and artifacts)."""
    return {
        "f1_start": F1_START.isoformat(),
        "n_folds": N_FOLDS,
        "fold_weeks": FOLD_WEEKS,
        "fold_starts": [f["start"].isoformat() for f in FOLDS],
        "fold_ends": [f["end"].isoformat() for f in FOLDS],
        "eval_end": EVAL_END.isoformat(),
        "sealed_tail_start": SEALED_TAIL_START.isoformat(),
    }


def cost_kernel_block() -> dict:
    return {
        "fee_bps": FEE_BPS,
        "half_spread_bps": HALF_SPREAD_BPS,
        "cost_per_side_bps": COST_PER_SIDE_BPS,
        "stress_tiers": list(STRESS_TIERS),
        "stress_applies_to": "fee+spread only",
        "funding": "measured events, signed, unstressed",
    }
