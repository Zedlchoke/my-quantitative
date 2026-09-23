"""jrv2 — Python core for cycle JEV-REGIME-ROUTER-V2 (S0 research only).

FORCED-CHOICE design (owner law, PLAN §1): the provider NEVER abstains —
TRANSITION_UNKNOWN does not exist as a provider option. Abstention is
code-owned ONLY (safety layer). No live surface of any kind: this package
never sends anything anywhere, never holds credentials, refuses S1 paths and
refuses any V1 runtime path (V1 isolation). Deterministic pure python +
numpy; pyarrow only inside the parquet reader.

Fully isolated v2 namespace: no cache, no decisions, no state shared with
V1; state_id salts are namespaced JRV2 (sha256('JRV2'||asset||data_sha)).
"""

from __future__ import annotations

__version__ = "0.1.0"

CYCLE_ID = "JEV-REGIME-ROUTER-V2"

# Forced-choice answer sets (question_contract.json). There is NO fifth
# phase option: TRANSITION_UNKNOWN is code-owned, never a provider choice.
PHASES = ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND")
STRUCTURES = ("TREND", "RANGE")
DIRECTIONS = ("UP", "DOWN", "NEUTRAL")

# Effective labels: the four phases plus the code-owned abstention label.
LABELS = PHASES + ("TRANSITION_UNKNOWN",)

LABEL_CODES = {
    "ACCUMULATION": 1,
    "UPTREND": 2,
    "DISTRIBUTION": 3,
    "DOWNTREND": 4,
    "TRANSITION_UNKNOWN": 5,
}

QUESTION_IO_SCHEMA = "jrv2_question_io@1"

# Cells (fold_contract.json): asset x regime clock. exec clock is 15m for
# BTC cells, D1 for SPY.
CELLS = {
    "BTC_H1": {"asset": "btcusdt", "regime_clock": "H1", "exec_clock": "15m"},
    "BTC_H4": {"asset": "btcusdt", "regime_clock": "H4", "exec_clock": "15m"},
    "SPY_D1": {"asset": "spy", "regime_clock": "D1", "exec_clock": "D1"},
}
