"""DT100 — DAYTRADER-100-V1 frozen configuration.

All constants here are FROZEN at G3 (plan sec 3.1/4, AMENDMENT_r1). Any change
after scored PnL is visible is a new identity (no in-place rescue).
"""
from __future__ import annotations

# ---------------------------------------------------------------- disclosure
DISCLOSURE = (
    "ANCESTRY_RELAXED_BY_OWNER_ORDER_2026-09-28: this program re-scores families "
    "already falsified by this program, on the owner's explicit order. Trials are "
    "NOT independent of their ancestors' kills; any positive must pass the "
    "decorrelation court (pooled |rho| <= 0.20 vs its dead ancestor) before any "
    "label stronger than OWNER_ORDERED_RESCORE_POSITIVE."
)

# ---------------------------------------------------------------- calendars
# Crypto (Binance Vision 1m/1h, 2020-09-01 .. 2026-08-31)
CRYPTO_WARMUP = ("2020-09-01", "2021-03-31")          # no decisions scored
CRYPTO_FOLDS = [
    ("GĐ1", "2021-04-01", "2022-06-30"),
    ("GĐ2", "2022-07-01", "2023-09-30"),
    ("GĐ3", "2023-10-01", "2024-12-31"),
    ("GĐ4", "2025-01-01", "2026-08-31"),
]
# FX (Dukascopy M1, 2021-01-01 .. 2026-09-23)
FX_WARMUP = ("2021-01-01", "2021-03-31")
FX_FOLDS = [
    ("P1", "2021-04-01", "2022-06-30"),
    ("P2", "2022-07-01", "2023-09-30"),
    ("P3", "2023-10-01", "2024-12-31"),
    ("P4", "2025-01-01", "2026-09-23"),
]

# ---------------------------------------------------------------- costs
# Q-8 disclosure: crypto taker fee is the exchange CONTRACT constant (5.0 bps),
# not tape-measured; half-spread frozen from the program's measured census
# (SOL p50 0.469 bps -> 0.5; BTC conservative 1.0). Stress x1.0/x1.5/x2.0.
CRYPTO_COSTS = {
    "BTCUSDT": {"taker_bps": 5.0, "half_spread_bps": 1.0},
    "SOLUSDT": {"taker_bps": 5.0, "half_spread_bps": 0.5},
    "ETHUSDT": {"taker_bps": 5.0, "half_spread_bps": 1.0},
    "XRPUSDT": {"taker_bps": 5.0, "half_spread_bps": 1.5},
}
STRESS_MULTIPLIERS = [1.0, 1.5, 2.0]
# FX: cost is the MEASURED per-bar half-spread from the M1 bid/ask itself
# (bps of mid at the fill bar); stress multiplies it. No taker leg (spot).
FX_MIN_HALF_SPREAD_BPS = 0.05   # floor vs zero-spread bars (data artifact guard)

# ---------------------------------------------------------------- floors
FLOORS = {
    "pf_bar_x1.0": 1.10,
    "min_trades_per_fold": 100,
    "min_trades_total": 400,
    "fired_rate_band": (0.02, 0.10),        # decisions per bar-leg-day (sanity)
    "top_fold_contribution_max": 0.50,
    "weekday_share_max": 0.35,
    "folds_positive_min": 2,                # of 4 chronological folds
}

# ---------------------------------------------------------------- paths
WT = "/Users/hoangminhlong/my-quantitative/.worktrees/daytrader-100-v1/integration"
SRC = {
    "btc1m": "/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/integration/research/control/DTP-CX-SOLUSDT-C1/data_local/vision/klines_um_BTCUSDT_1m",
    "sol1m": "/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/integration/research/control/DTP-CX-SOLUSDT-C1/data_local/vision/klines_um_SOLUSDT_1m",
    "eth1h": "/Users/hoangminhlong/my-quantitative/.worktrees/ethusdt-open-search-v2/integration/research/control/ethusdt_open_search_v2/data_local/vision/klines_um_ETHUSDT_1h",
    "sol1h": "/Users/hoangminhlong/my-quantitative/.worktrees/ethusdt-open-search-v2/integration/research/control/ethusdt_open_search_v2/data_local/vision/klines_um_SOLUSDT_1h",
    "xrp1h": "/Users/hoangminhlong/my-quantitative/.worktrees/ethusdt-open-search-v2/integration/research/control/ethusdt_open_search_v2/data_local/vision/klines_um_XRPUSDT_1h",
    "eur_m1_bid": "/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/M1/BID",
    "eur_m1_ask": "/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/M1/ASK",
    "gbp_m1_bid": "/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/GBPUSD/M1/BID",
    "gbp_m1_ask": "/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/GBPUSD/M1/ASK",
    "jpy_m1_bid": "/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/USDJPY/M1/BID",
    "jpy_m1_ask": "/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/USDJPY/M1/ASK",
    "premium_btc": WT + "/research/control/DAYTRADER-100-V1/data_staging/premium/BTCUSDT",
    "premium_sol": WT + "/research/control/DAYTRADER-100-V1/data_staging/premium/SOLUSDT",
    "funding_btc": WT + "/research/control/DAYTRADER-100-V1/data_staging/funding/BTCUSDT",
    "funding_sol": WT + "/research/control/DAYTRADER-100-V1/data_staging/funding/SOLUSDT",
    "spot_btc": WT + "/research/control/DAYTRADER-100-V1/data_staging/spot/BTCUSDT",
    "spot_sol": WT + "/research/control/DAYTRADER-100-V1/data_staging/spot/SOLUSDT",
    "quarterly_btc": WT + "/research/control/DAYTRADER-100-V1/data_staging/quarterly/BTCUSDT",
}

# Dukascopy integer-point scales (duka_lib.py verified layout)
FX_SCALES = {"eur": 1e5, "gbp": 1e5, "jpy": 1e3}

CONTROLS = ["clock_shadow", "sign_flip", "stale_lag"]   # re-evaluations, zero cells
CONTROL_SEED = 20260928
