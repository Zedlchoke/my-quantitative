"""Frozen strategy primitives for the A12-V12-OILEVER-V2-DELEV family.

This module implements the FROZEN contract pinned by
``research/control/v12_run/selection_freeze.json`` +
``research/control/v12_run/selection_freeze_specs/
A12-V12-OILEVER-V2-DELEV.json`` (bootstrap ``ec4b59f``) verbatim -- no
tuning, no grids, no parameter changes.  It is a pure, data-injected
library: every observable (daily OI snapshot series, completed 15m bars,
funding settlements, tick sizes) is supplied by the caller, so the same
primitives run on synthetic fixtures and on the read-only workspace
snapshot.  Nothing here reads the catalog, computes a scored outcome, or
persists anything.

Frozen contract (V12 selection freeze, verbatim semantics):

* anchor ``OILEV-V2-28D-FLOW-W`` -- 28d OI-flow feature (``oi_flow``);
* neighbour ``OILEV-V2-56D-STOCK-W`` -- 56d OI-stock feature
  (``oi_stock``);
* control ``OILEV-V2-28D-FLOW-W-INV`` -- the anchor feature/book
  sign-inverted end-to-end (causal negative control;
  falsification: a positive after-cost spread destroys the mechanism).

FEATURE DEFINITIONS ARE INHERITED UNCHANGED from
``research.v11.families.oilever_delev.strategy`` (the V11 OILEV family):
the 28d log OI-growth, the 56d OI level percentile of the symbol's own
history, and the frozen PIT staleness gate (last COMPLETED daily OI row
STRICTLY BEFORE the stamp, staleness <= 48h, positive value; a symbol
that fails the gate is simply INELIGIBLE at the stamp -- fail closed,
never guessed).  This module imports those primitives; it does not
re-implement them.  The V11 momentum residualisation and the V11
DV-median eligibility filter are deliberately NOT inherited (the A1
oilever_v2_brief freezes the raw OI feature ranking and the
min-eligible-9 breadth rule instead).

BOOK: :func:`research.v12.oilev_v2_book.build_oilev_v2_book` -- when >= 9
names are eligible, the four lowest feature scores are the long leg and
the four highest the short leg, equal weight per leg, the frozen BTC beta
hedge applied as a CONTEXT semantic only (BTCUSDT is benchmark-excluded
and can never appear as a position), then a uniform WHOLE-BOOK scale when
needed so every final absolute weight <= 0.30.  Individual names are
never clipped and never renormalised.  Below 9 eligible names the stamp
raises :class:`research.v12.oilev_v2_book.EligibilityShortfall`
(fail closed): a stamp without sufficient breadth has NO book.

SCHEDULE: weekly Monday 00:00:00Z decision stamps over the frozen window
2025-08-22T00:00:00Z..2026-08-21T00:00:00Z (52 stamps; first stamp
2025-08-25, whose warmup is satisfied from pre-window OI history).  The
one declared execution lag fills at the open of the 15m bar covering the
decision instant (the first allowed execution event after availability).
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import (
    ContractViolation,
    StrategyIdentity,
)
from research.contract_v10 import (
    ADVERSE_TICKS_SLIPPAGE_FLOOR_V10,
    FILL_CLOCK_V10,
    TAKER_FEE_FLOOR_BPS_V10,
)
from research.v11.families.oilever_delev.strategy import (
    Bar,
    FORMATION_DAYS_ANCHOR,
    FORMATION_DAYS_NEIGHBOUR,
    HOUR_NS,
    OI_MAX_STALENESS_HOURS,
    oi_flow_growth,
    oi_stock_percentile,
    parse_iso_utc,
    iso_utc,
    weekly_mondays,
)
from research.v11.publication_identity import arm_config_digest
from research.v12.oilev_v2_book import (
    EligibilityShortfall,
    build_oilev_v2_book,
)

# --------------------------------------------------------------------------- #
# Frozen identity (fields pinned by the V12 selection freeze / lane contract)
# --------------------------------------------------------------------------- #
FAMILY_ID = "A12-V12-OILEVER-V2-DELEV"
STRATEGY_ID = "hyp_a12_v12_oilever_v2_delev"
#: V11 family semantics carried forward: long/short book with the BTC beta
#: hedge as a CONTEXT-only semantic (the hedge never alters leg weights).
DIRECTION = "long_short_beta_neutral"
BENCHMARK_SYMBOL = "BTCUSDT"
MATRIX_COHORT_HINT = "v12"

WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-21T00:00:00Z"

FUNDING_SIGN_CONVENTION = "LONG_PAYS_POSITIVE_RATE"

#: Arm id -> frozen role (``arm_config_id``), exactly as recorded in
#: ``selection_freeze.json`` ``frozen_cells`` (``role`` field).
ARM_ROLES: dict[str, str] = {
    "OILEV-V2-28D-FLOW-W": "anchor",
    "OILEV-V2-56D-STOCK-W": "neighbour",
    "OILEV-V2-28D-FLOW-W-INV": "causal_negative_control",
}
ARM_IDS: tuple[str, ...] = tuple(sorted(ARM_ROLES))
ANCHOR_ARM = "OILEV-V2-28D-FLOW-W"
NEIGHBOUR_ARM = "OILEV-V2-56D-STOCK-W"
CONTROL_ARM = "OILEV-V2-28D-FLOW-W-INV"

#: The ``arm_config_digest`` values RECORDED in selection_freeze.json
#: (binding freeze record).  ``frozen_arm_digest_report`` compares them to
#: the digests recomputed from this module's identities.
FROZEN_ARM_CONFIG_DIGESTS: dict[str, str] = {
    ANCHOR_ARM: "04982abb77932aeaa1f7a337c7970e8ba97f72afcbf867f84b85faeb9bd0ca3b",
    NEIGHBOUR_ARM: "05b9fb40e187dd8af12688ef95d7c4efb68271314d83a1f60089904d64ee463e",
    CONTROL_ARM: "4e04a01a4111c4d6961cf604efe73ec06edda0b5cff6c65f08b9dfeadf7cfb8b",
}

#: Frozen per-arm feature/book mapping (spec ``arms.config``, verbatim
#: semantics): feature kind, formation days, and whether the whole book is
#: sign-inverted end-to-end.
_ARM_FEATURE: dict[str, tuple[str, int, bool]] = {
    ANCHOR_ARM: ("oi_flow", FORMATION_DAYS_ANCHOR, False),
    NEIGHBOUR_ARM: ("oi_stock", FORMATION_DAYS_NEIGHBOUR, False),
    CONTROL_ARM: ("oi_flow", FORMATION_DAYS_ANCHOR, True),
}

#: Frozen config payloads per arm -- the recorded ``config`` dicts of
#: ``selection_freeze.json`` ``frozen_cells``, verbatim (key order is
#: irrelevant to the digest, which canonicalises sorted).
_FROZEN_CONFIGS: dict[str, dict] = {
    ANCHOR_ARM: {
        "book": "oilev_v2_diversified_4v4",
        "weight_cap_abs": 0.3,
        "min_eligible": 9,
        "leg_names": 4,
        "beta_hedge": "frozen_90d_btc",
        "scale_rule": "uniform_whole_book",
        "window": ["2025-08-22T00:00:00Z", "2026-08-21T00:00:00Z"],
        "feature": "oi_flow",
        "formation_days": 28,
    },
    NEIGHBOUR_ARM: {
        "book": "oilev_v2_diversified_4v4",
        "weight_cap_abs": 0.3,
        "min_eligible": 9,
        "leg_names": 4,
        "beta_hedge": "frozen_90d_btc",
        "scale_rule": "uniform_whole_book",
        "window": ["2025-08-22T00:00:00Z", "2026-08-21T00:00:00Z"],
        "feature": "oi_stock",
        "formation_days": 56,
    },
    CONTROL_ARM: {
        "book": "oilev_v2_diversified_4v4",
        "weight_cap_abs": 0.3,
        "min_eligible": 9,
        "leg_names": 4,
        "beta_hedge": "frozen_90d_btc",
        "scale_rule": "uniform_whole_book",
        "window": ["2025-08-22T00:00:00Z", "2026-08-21T00:00:00Z"],
        "feature": "oi_flow",
        "formation_days": 28,
        "sign": "inverted",
    },
}

#: Frozen schedule / folds strings (freeze ``common_frozen``, verbatim).
DECISION_CLOCK = (
    "Mondays 00:00:00Z; features from completed 15m bars + last completed OI "
    "row strictly before stamp; one declared execution lag"
)
FOLDS_CONTRACT = (
    "chronological 3-fold force-flat per V11 convention "
    "(F0 2025-08-22..2025-12-21, F1 2025-12-22..2026-04-21, "
    "F2 2026-04-22..2026-08-21); per-family cell matrices derived from the "
    "family's frozen folds contract (L-V11-1)"
)
CLOSE_DECODE = "bar close = raw i128 / 1e16 (A9-F F7, binding for all lanes)"

#: Declared cost floors (contract_v10; identical to the V11 OILEV family).
TAKER_FEE_FLOOR_BPS = float(TAKER_FEE_FLOOR_BPS_V10)
ADVERSE_TICK_SLIP_FLOOR = int(ADVERSE_TICKS_SLIPPAGE_FLOOR_V10)
FILL_CLOCK = FILL_CLOCK_V10

#: Frozen book constants (mirrored from the A4 builder; asserted equal there).
CAP_MAX = 0.30
MIN_ELIGIBLE = 9
LEG_NAMES = 4
GROSS_TARGET = 1.0

#: Pinned folds (freeze ``common_folds``; the plugin realises force-flat at
#: fold boundaries through the adapter's purge/carry accounting).
FOLD_WINDOWS: tuple[tuple[str, str, str], ...] = (
    ("F0", "2025-08-22", "2025-12-21"),
    ("F1", "2025-12-22", "2026-04-21"),
    ("F2", "2026-04-22", "2026-08-21"),
)
PURGE_DAYS = 1
MIN_FOLDS = 3

#: The first decision stamp of the frozen window (2025-08-25 is a Monday);
#: the first-stamp warmup must be satisfiable from PRE-WINDOW data.
FIRST_STAMP_ISO = "2025-08-25T00:00:00Z"

STATUS_OK = "OK"

def frozen_arm_config(arm_id: str) -> dict:
    """The exact frozen ``config`` payload of one arm (digest input)."""
    arm_id = str(arm_id)
    if arm_id not in _FROZEN_CONFIGS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return dict(_FROZEN_CONFIGS[arm_id])


def frozen_identity(arm_id: str) -> StrategyIdentity:
    """The frozen V12 identity of one arm (digest equality is test-pinned)."""
    arm_id = str(arm_id)
    if arm_id not in ARM_ROLES:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return StrategyIdentity(
        strategy_id=STRATEGY_ID,
        family_id=FAMILY_ID,
        arm_config_id=ARM_ROLES[arm_id],
        direction=DIRECTION,
        window_start_iso=WINDOW_START_ISO,
        window_end_iso=WINDOW_END_ISO,
        benchmark_symbols_excluded=(BENCHMARK_SYMBOL,),
        funding_sign_convention=FUNDING_SIGN_CONVENTION,
        matrix_cohort_hint=MATRIX_COHORT_HINT,
        arm_id=arm_id,
        config=frozen_arm_config(arm_id),
    )


def frozen_arm_digest_report() -> dict[str, dict[str, Any]]:
    """Recomputed vs recorded ``arm_config_digest`` per arm (honest report).

    The freeze record is binding; this lane MUST surface any mismatch
    instead of papering over it.  Each entry carries the digest recomputed
    from :func:`frozen_identity` via
    ``research.v11.publication_identity.arm_config_digest`` and the digest
    recorded in ``selection_freeze.json``.
    """
    report: dict[str, dict[str, Any]] = {}
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        computed = arm_config_digest(identity, arm_id=arm_id)
        recorded = FROZEN_ARM_CONFIG_DIGESTS[arm_id]
        report[arm_id] = {
            "computed_from_identity": computed,
            "recorded_in_freeze": recorded,
            "match": bool(computed == recorded),
        }
    return report


def arm_feature_spec(arm_id: str) -> tuple[str, int, bool]:
    """``(feature_kind, formation_days, invert)`` of one frozen arm."""
    arm_id = str(arm_id)
    if arm_id not in _ARM_FEATURE:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return _ARM_FEATURE[arm_id]


# --------------------------------------------------------------------------- #
# PIT ranking feature (inherited UNCHANGED from the V11 OILEV strategy)
# --------------------------------------------------------------------------- #
def signal_scores_at(
    arm_id: str,
    *,
    oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
    stamp_ns: int,
    universe: Sequence[str],
) -> dict[str, float]:
    """PIT feature scores of one arm at one Monday 00:00:00Z stamp.

    ``oi_flow``: 28d log OI-growth from the daily-last anchor.
    ``oi_stock``: percentile of the current OI level within its own
    trailing window.  Both inherited UNCHANGED from
    ``research.v11.families.oilever_delev.strategy`` (last completed daily
    OI row strictly before the stamp, staleness <= 48h, positive; a symbol
    whose anchor or feature is unavailable is simply INELIGIBLE -- fail
    closed, never guessed).  The pinned benchmark leg is refused outright.
    """
    arm_id = str(arm_id)
    if arm_id not in _ARM_FEATURE:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    feature_kind, formation_days, _invert = _ARM_FEATURE[arm_id]
    if BENCHMARK_SYMBOL in set(str(s) for s in universe):
        raise ContractViolation(
            "the pinned benchmark leg can never enter the tradeable universe"
        )
    stamp = int(stamp_ns)
    scores: dict[str, float] = {}
    for sym in sorted(str(s) for s in universe):
        series = oi_by_symbol.get(sym) or ()
        if feature_kind == "oi_flow":
            value: Optional[float] = oi_flow_growth(
                series, stamp, formation_days=int(formation_days)
            )
        else:
            value = oi_stock_percentile(series, stamp, window_days=int(formation_days))
        if value is None:
            continue  # INELIGIBLE at this stamp (stale/non-positive/uncomputable)
        scores[sym] = float(value)
    return scores


# --------------------------------------------------------------------------- #
# Per-stamp target book (delegates to the frozen A4 book builder)
# --------------------------------------------------------------------------- #
def compute_targets_at(
    arm_id: str,
    *,
    oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
    stamp_ns: int,
    universe: Sequence[str],
    gross: float = GROSS_TARGET,
) -> dict[str, Any]:
    """Frozen target book of one arm at one Monday 00:00:00Z stamp.

    Ranks the eligible universe by the inherited PIT feature and delegates
    to :func:`research.v12.oilev_v2_book.build_oilev_v2_book` (>= 9
    eligible -> 4 lowest + 4 highest, equal weight per leg, context-only
    BTC beta hedge, uniform whole-book scale, cap <= 0.30 by
    construction).  Fewer than 9 eligible names raises
    :class:`EligibilityShortfall` (fail closed).  No PnL is computed.
    """
    arm_id = str(arm_id)
    if arm_id not in _ARM_FEATURE:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    feature_kind, formation_days, invert = _ARM_FEATURE[arm_id]
    stamp = int(stamp_ns)
    scores = signal_scores_at(
        arm_id, oi_by_symbol=oi_by_symbol, stamp_ns=stamp, universe=universe
    )
    book = build_oilev_v2_book(scores, invert=invert, gross=float(gross))
    final_weights = {str(sym): float(w) for sym, w in book["weights"]}
    weights = {sym: final_weights[sym] for sym in sorted(final_weights)}
    return {
        "schema": "v12i.oilev_v2.targets.v1",
        "family_id": FAMILY_ID,
        "arm_id": arm_id,
        "status": STATUS_OK,
        "weights": [[sym, weights[sym]] for sym in sorted(weights)],
        "longs": [[sym, round(final_weights[sym], 12)] for sym in book["longs"]],
        "shorts": [[sym, round(final_weights[sym], 12)] for sym in book["shorts"]],
        "carried_forward": False,
        "decision_ns": stamp,
        "diagnostics": {
            "stamp_ns": stamp,
            "stamp_iso": iso_utc(stamp),
            "n_eligible": int(book["n_eligible"]),
            "n_longs": int(book["n_longs"]),
            "n_shorts": int(book["n_shorts"]),
            "feature_kind": feature_kind,
            "formation_days": int(formation_days),
            "invert": bool(invert),
            "scale_applied": book["scale_applied"],
            "max_abs_weight": book["max_abs_weight"],
            "per_name_weight_before_scale": book["per_name_weight_before_scale"],
            "gross_after_scale": book["gross_after_scale"],
            "reason_code": None,
        },
    }


# --------------------------------------------------------------------------- #
# Schedule / folds (frozen clocks; calendar reuse is V11-exact)
# --------------------------------------------------------------------------- #
def stamp_calendar() -> tuple[int, ...]:
    """Weekly Monday 00:00:00Z decision stamps over the frozen window."""
    return weekly_mondays(
        window_start_iso=WINDOW_START_ISO, window_end_iso=WINDOW_END_ISO
    )


def fold_assignments(instants: Sequence[int]) -> list[tuple[int, str, list[int]]]:
    """Assign decision stamps to the PINNED F0/F1/F2 calendar windows.

    Delegates to the V11 strategy's identical pinned-window helper.
    """
    from research.v11.families.oilever_delev.strategy import fold_assignments as _assign

    return _assign(list(instants))


def purge_fold_members(
    assignments: Sequence[tuple[int, str, list[int]]],
    *,
    purge_days: int = PURGE_DAYS,
) -> list[tuple[int, str, list[int], list[int]]]:
    """Strip the trailing ``purge_days`` instants of each fold (purge gaps).

    Delegates to the V11 strategy's identical pinned helper; a book opened
    inside a fold therefore always realises inside that fold (force-flat
    at fold boundaries under the adapter's accounting).
    """
    from research.v11.families.oilever_delev.strategy import (
        purge_fold_members as _purge,
    )

    return _purge(list(assignments), purge_days=int(purge_days))


def window_start_ns() -> int:
    return parse_iso_utc(WINDOW_START_ISO)


def window_end_ns() -> int:
    return parse_iso_utc(WINDOW_END_ISO)


__all__ = [
    "ADVERSE_TICK_SLIP_FLOOR",
    "ANCHOR_ARM",
    "ARM_IDS",
    "ARM_ROLES",
    "Bar",
    "BENCHMARK_SYMBOL",
    "CAP_MAX",
    "CLOSE_DECODE",
    "CONTROL_ARM",
    "DECISION_CLOCK",
    "DIRECTION",
    "FILL_CLOCK",
    "FIRST_STAMP_ISO",
    "FOLD_WINDOWS",
    "FOLDS_CONTRACT",
    "FORMATION_DAYS_ANCHOR",
    "FORMATION_DAYS_NEIGHBOUR",
    "FAMILY_ID",
    "GROSS_TARGET",
    "HOUR_NS",
    "LEG_NAMES",
    "MATRIX_COHORT_HINT",
    "MIN_ELIGIBLE",
    "MIN_FOLDS",
    "NEIGHBOUR_ARM",
    "OI_MAX_STALENESS_HOURS",
    "PURGE_DAYS",
    "STATUS_OK",
    "STRATEGY_ID",
    "TAKER_FEE_FLOOR_BPS",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "EligibilityShortfall",
    "arm_feature_spec",
    "build_oilev_v2_book",
    "compute_targets_at",
    "fold_assignments",
    "frozen_arm_config",
    "frozen_arm_digest_report",
    "frozen_identity",
    "iso_utc",
    "oi_flow_growth",
    "oi_stock_percentile",
    "parse_iso_utc",
    "purge_fold_members",
    "signal_scores_at",
    "stamp_calendar",
    "window_end_ns",
    "window_start_ns",
]
