"""EVENT-MECHANISMS-V1 engine — frozen constants (G3_FREEZE + addenda r1/r2).

Every constant here is fixed a priori by the freeze documents; nothing is
tuned. Sources cited per constant.
"""
from __future__ import annotations

import os

# ---------------------------------------------------------------- paths ----
WORKTREE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../.."))
# engine/emv1/config.py -> up 5 = research/control/EVENT-MECHANISMS-V1/engine/../..
# Worktree root resolved from module location:
# engine/emv1/config.py = <wt>/research/control/EVENT-MECHANISMS-V1/engine/emv1/config.py
WT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
ENGINE_DIR = os.path.join(WT, "research", "control", "EVENT-MECHANISMS-V1", "engine")
EVIDENCE_DIR = os.path.join(ENGINE_DIR, "evidence")
DRYRUN_DIR = os.path.join(ENGINE_DIR, "dryrun")
STAGING = os.path.join(WT, ".staging_eventmech")
PANEL_DIR = os.path.join(STAGING, "integration", "data_raw", "stocks_ng6_eod")
STREAM_PATH = os.path.join(STAGING, "integration", ".staging_sec_v13", "form4_stream.jsonl")
DIV_DIR = os.path.join(STAGING, "integration", ".staging_sec_v13", "eodhd_div")
SPLIT_DIR = os.path.join(STAGING, "integration", ".staging_sec_v13", "eodhd_splits")
XML_DIR = os.path.join(STAGING, "integration", ".staging_sec_v13", "form4_xml")
A1_EVENTS_PATH = os.path.join(STAGING, "a1_events.jsonl")
N4_MAP_PATH = os.path.join(STAGING, "n4_map_v1.jsonl")
SUBMISSIONS_DIR = os.path.join(STAGING, "submissions")
PANEL_DIGEST_PATH = os.path.join(STAGING, "ng6_panel_digest.txt")
SUBSTRATE_MANIFEST_PATH = os.path.join(
    STAGING, "integration", "research", "control", "stocks_free_v13_run",
    "substrate_manifest.json",
)
STAGED_SUMS_PATH = os.path.join(STAGING, "SHA256SUMS.staged.txt")

# ------------------------------------------------------------- digests ----
# Pinned by lane S (G2 pins / SHA256SUMS.staged.txt). Fail-closed at load.
PIN_A1_EVENTS_SHA256 = "a6a5bb6eb39981685f2caf9b3dc1ce5e0c683926facbe2d778014e14ec979401"
PIN_A1_EVENTS_ROWS = 54941
PIN_FORM4_STREAM_SHA256 = "6ac2cd5bdd62566efe106b46de715030e9a8a940cb90f5a991df5f05ba6742b2"
PIN_FORM4_STREAM_ROWS = 546039
PIN_N4_MAP_SHA256 = "537cd5afe67dd5a280b377213a69f77747df6ff0b8f55329038bbf105b665fd8"

# ----------------------------------------------------------- identity ----
CYCLE_ID = "EVENT-MECHANISMS-V1"
FAMILY_A1 = "EMV1-A1-FILINGFLOW-ACC"
FAMILY_A2 = "EMV1-A2-INSIDERFLOW-ACC"

# ------------------------------------------------------------- window ----
WINDOW_START = "2015-01-05"
WINDOW_END = "2026-06-30"

# Folds (G3_FREEZE: F1 2015-2018, F2 2018-2021, F3 2021-2023, F4 2023-2026H1;
# half-open [start, end) convention — verified against lane S populations).
FOLDS = (
    ("F1", "2015-01-01", "2018-01-01"),
    ("F2", "2018-01-01", "2021-01-01"),
    ("F3", "2021-01-01", "2023-01-01"),
    ("F4", "2023-01-01", "2026-07-01"),
)

# ------------------------------------------------------------- floors ----
FLOOR_EVENTS_PER_FOLD = 100
FLOOR_EVENTS_TOTAL_PER_ANCHOR = 400
CONTAMINATION_EXCLUSION_FRACTION = 0.40  # R2-2: >40% of a fold => CONTAMINATION_HIGH
RHO_BAR = 0.20  # immovable ancestry/representation bar

# --------------------------------------------------------------- A1 ------
A1_FORMS = ("10-Q", "10-K")  # exact match only (R2-3); amendment forms excluded
A1_HOLD_ANCHOR = 5   # sessions
A1_HOLD_N1 = 10      # sessions
# N2 = anchor rule restricted to monitored S2 (same H as anchor)

# --------------------------------------------------------------- A2 ------
A2_CODE = "P"              # open-market purchase transaction code
A2_MIN_BUY_VALUE_USD = 100_000.0
A2_HOLD_ANCHOR = 10   # sessions
A2_HOLD_N1 = 20       # sessions
A2_CLUSTER_MIN_INSIDERS = 2   # N2 = cluster-conditioned (same anchor rule)

# ------------------------------------------------------- strata (R2-4) ---
# ET session clock [09:30,16:00) regular; strata by acceptance clock:
#   S1 pre-open [00:00,09:30)  S2 in-session [09:30,16:00)
#   S3 after-close [16:00,20:00)  S4 late [20:00,24:00)
# Weekend acceptances bucket SEPARATELY (never collapsed into weekday strata).
STRATA_BOUNDS = (("S1", 0, 570), ("S2", 570, 960), ("S3", 960, 1200), ("S4", 1200, 1440))
ET_TZ = "America/New_York"
SESSION_CLOSE_MIN = 960   # 16:00 ET in minutes-from-midnight

# --------------------------------------------------------- control seeds --
SEED_PERMUTE = 20260927
PERMUTE_DRAWS = 3
SEED_CLOCK_SHADOW = 20260927
SEED_VALUE_DATE_PLACEBO = 20260927
SEED_TRUNCATION_SAMPLE = 7
TRUNCATION_SAMPLE_N = 300

# ------------------------------------------- frozen cost contract (E7) ----
# Source: branch orca/stocks-amihud-retest-v1-integration,
#   research/control/stocks_amihud_retest_v1/d1/cost_contract.json
#   blob sha256 b7d4464e8aa91588eb01adf39d48da32e96b8fa9b4d1c14554683f5a918b8593
#   frozen_utc 2026-09-23T06:40:00Z; engine constants cross-checked in
#   impl/samv1r/engine.py (BANDS/DV_FLOOR/CAP_FRAC/STRESS_MULT verbatim).
COST_BANDS = ((50_000_000.0, 10.0), (10_000_000.0, 15.0), (2_000_000.0, 25.0))  # (DVmed60 >=, bps/fill)
DV_FLOOR = 2_000_000.0
DV_WINDOW = 60
DV_MIN_PRESENT = 30
CAP_FRAC = 0.15
STRESS_MULT = 2.0
COST_STRESS_POWERS = (1.0, 1.5, 2.0)
# Q-2 conditional law (research/wayfinder/LESSONS.md Q-2, branch-pinned):
# at the open, per-minute movement ran 3.33x midday and measured spread 3.35x
# midday; open-crossing entries priced at the EXPENSIVE band (3.35x).
OPEN_BAND_MULT = 3.35   # entry side (fills at session open)
MIDDAY_BAND_MULT = 1.0  # exit side (fills at session close ~= midday basis)
COST_CONTRACT_SHA256 = "b7d4464e8aa91588eb01adf39d48da32e96b8fa9b4d1c14554683f5a918b8593"

# B1 both-direction extreme-print law (impl/samv1r/panel.py verbatim, raw basis
# substituted per R2-1): |log(p_t / p_{t-1})| >= log(10) => bar unfillable.
EXTREME_PRINT_LOG = 2.302585092994046  # math.log(10.0)

# --------------------------------------------------------- forbidden keys --
# R2-6 / G3 §19.2: no expectancy/PF/PnL/drawdown aggregate anywhere pre-GO.
NOPNL_FORBIDDEN_KEY_SUBSTRINGS = (
    "pnl", "profit_factor", "expectancy", "drawdown", "sharpe",
    "net_return", "gross_return", "return", "_ret", "ret_", "pnr",
    "win_rate", "hit_rate", "avg_trade", "per_trade",
)
