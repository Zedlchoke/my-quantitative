"""reason_codes@1 registry — frozen verbatim from architecture_freeze.json.

Freeze authority: research/control/market_data_plane_v1_run/architecture_freeze.json
(sha256 7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02),
section "reason_codes@1".  Lanes never improve a frozen spec; the codes, the
three classes and the semantics below are copied exactly as frozen.

Class semantics
---------------
``reject_to_quarantine``
    Any of these codes makes the event INVALID.  Callers (A3's quarantine
    store) decide the physical quarantine move; this module only classifies.
``flag_suspect``
    Any of these codes makes the event SUSPECT (unless a rejection code is
    also present, in which case the event is INVALID).
``bookkeeping``
    Recorded on the event but does not, by itself, degrade quality_status
    (final status rule: INVALID if any rejection code, else SUSPECT if any
    suspect code, else VALID).

This module imports nothing outside the standard library.
"""

from __future__ import annotations

# --- frozen code list (order exactly as frozen) -----------------------------
CODES: tuple[str, ...] = (
    "MALFORMED_SHAPE",
    "MISSING_REQUIRED_FIELD",
    "UNKNOWN_EVENT_TYPE",
    "TIMEZONE_NAIVE_REJECTED",
    "NON_FINITE_PRICE",
    "PRECISION_LOSS",
    "NEGATIVE_PRICE",
    "NEGATIVE_SIZE",
    "CROSSED_QUOTE",
    "STALE_QUOTE",
    "IMPOSSIBLE_TIME_ORDER",
    "OUT_OF_ORDER_DELIVERY",
    "SEQUENCE_GAP",
    "SEQUENCE_RESET",
    "DUPLICATE_EVENT",
    "SOURCE_RESET_UNEVIDENCED",
    "UNKNOWN_INSTRUMENT",
    "MANIFEST_MISMATCH",
    "STATISTICAL_ANOMALY",
    "QUARANTINE_ORPHAN",
    "HASH_DISAGREEMENT",
)

# --- frozen classes ---------------------------------------------------------
REJECT_TO_QUARANTINE: tuple[str, ...] = (
    "MALFORMED_SHAPE",
    "MISSING_REQUIRED_FIELD",
    "UNKNOWN_EVENT_TYPE",
    "TIMEZONE_NAIVE_REJECTED",
    "NON_FINITE_PRICE",
    "PRECISION_LOSS",
    "NEGATIVE_PRICE",
    "NEGATIVE_SIZE",
    "CROSSED_QUOTE",
    "IMPOSSIBLE_TIME_ORDER",
    "SOURCE_RESET_UNEVIDENCED",
    "UNKNOWN_INSTRUMENT",
    "MANIFEST_MISMATCH",
    "HASH_DISAGREEMENT",
    "QUARANTINE_ORPHAN",
)

FLAG_SUSPECT: tuple[str, ...] = (
    "STALE_QUOTE",
    "OUT_OF_ORDER_DELIVERY",
    "SEQUENCE_GAP",
    "SEQUENCE_RESET",
    "STATISTICAL_ANOMALY",
)

BOOKKEEPING: tuple[str, ...] = (
    "DUPLICATE_EVENT",
)

_REJECT_SET = frozenset(REJECT_TO_QUARANTINE)
_SUSPECT_SET = frozenset(FLAG_SUSPECT)
_BOOKKEEPING_SET = frozenset(BOOKKEEPING)
_ALL_SET = frozenset(CODES)

# --- frozen semantics (docstrings exactly as frozen) ------------------------
SEMANTICS: dict[str, str] = {
    "SEQUENCE_GAP": (
        "raised only when the chunk manifest declares sequence_semantics=CONTIGUOUS; "
        "with sequence_semantics=NONE a jump is not missing data"
    ),
    "OUT_OF_ORDER_DELIVERY": (
        "flagged only when manifest declares ordered_delivery=true; replay sorting is "
        "deterministic and never deletes"
    ),
    "CROSSED_QUOTE": (
        "bid_price >= ask_price inside ONE venue+instrument quote; cross-venue price "
        "disagreement is recorded by consolidated BBO contributors, never coded "
        "CROSSED_QUOTE"
    ),
    "STATISTICAL_ANOMALY": (
        "diagnostic only, never silent deletion; default rule set flags |z|>6 on log "
        "price change within instrument and event class"
    ),
    "STALE_QUOTE": (
        "quote whose exchange_time is older than the staleness threshold parameter at "
        "evaluation time; threshold is always an explicit input"
    ),
}


def is_known(code: str) -> bool:
    """True when *code* is a member of the frozen reason_codes@1 registry."""
    return code in _ALL_SET


def is_rejection(code: str) -> bool:
    """True when *code* is in the frozen ``reject_to_quarantine`` class."""
    return code in _REJECT_SET


def is_suspect(code: str) -> bool:
    """True when *code* is in the frozen ``flag_suspect`` class."""
    return code in _SUSPECT_SET


def is_bookkeeping(code: str) -> bool:
    """True when *code* is in the frozen ``bookkeeping`` class."""
    return code in _BOOKKEEPING_SET


def final_status_for(codes) -> str:
    """Frozen final-status rule over a collection of reason codes.

    INVALID if any rejection code is present, else SUSPECT if any suspect code
    is present, else VALID.  Bookkeeping codes (DUPLICATE_EVENT) never raise
    the status by themselves.
    """
    for code in codes:
        if code in _REJECT_SET:
            return "INVALID"
    for code in codes:
        if code in _SUSPECT_SET:
            return "SUSPECT"
    return "VALID"
