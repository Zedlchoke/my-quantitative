"""jrv1 — Python core for cycle JEV-REGIME-ROUTER-V1 (S0 research only).

Frozen-spec implementation. No live surface of any kind: this package never
sends anything anywhere, never holds credentials, and refuses S1 paths.
Deterministic pure python + numpy; pyarrow only inside the parquet reader.
"""

__version__ = "0.1.0"

CYCLE_ID = "JEV-REGIME-ROUTER-V1"

LABELS = (
    "ACCUMULATION",
    "UPTREND",
    "DISTRIBUTION",
    "DOWNTREND",
    "TRANSITION_UNKNOWN",
)

# Label codes used for autocorrelation / association statistics (arm F Q-11).
LABEL_CODES = {
    "ACCUMULATION": 1,
    "UPTREND": 2,
    "DISTRIBUTION": 3,
    "DOWNTREND": 4,
    "TRANSITION_UNKNOWN": 5,
}

DECISION_IO_SCHEMA = "jrv1_decision_io@1"
