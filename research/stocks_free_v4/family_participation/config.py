"""Frozen arm configuration for family SFV4-A5-H1-PARTICIPATION-SHIFT (A8).

Implements the executable contract in
``research/control/stocks_free_v4_run/selection_freeze.json``
(``selected_families[0]``) from the mechanism source
``research/control/stocks_free_v4_run/proposals/a5_h1.json`` (sections
"universe_and_schedule", "anchor", "neighbour", "causal_negative_control",
"factor_alpha_test", "costs_and_turnover") and the frozen conventions in
``research/control/stocks_free_v4_run/baseline_invariants.json``.

This module is CONFIGURATION ONLY: no schedule construction, no data access,
no disk writes, no network, no PnL.

The three frozen arms (identical book form, clock, costs, risk-match scale;
ONLY the shock-ratio window membership differs):

* ``SFV4-A5-H1-A`` (anchor)    — shock21 = mean(DV, t-20..t)      / mean(DV, t-251..t-21);
* ``SFV4-A5-H1-N`` (neighbour) — shock63 = mean(DV, t-62..t)      / mean(DV, t-251..t-63);
* ``SFV4-A5-H1-C`` (causal negative control) — fully stale by one holding
  period: mean(DV, t-83..t-63) / mean(DV, t-251..t-84); the most recent
  quarter (t-62..t) is deliberately unused so the rank cannot see the
  contemporaneous participation state.

where ``DV_s(u) = close_s(u) * volume_s(u)`` is a declared price-level feature
on the authorized RAW (``_none``) path — the raw close x raw volume pair is the
only internally consistent price-times-quantity pair; the ``_all`` volume field
is back-adjustment-distorted and is NEVER read, and the ``_all`` adjusted close
is used ONLY for leg/benchmark total returns (never for DV).

Book form (identical for all arms): rank the eligible sector ETFs by the arm's
shock ratio descending (ties broken by ticker alphabetical ascending); long the
3 highest at +1/6 each, short the 3 lowest at -1/6 each; gross 1.0, net 0.0,
CASH the explicit residual leg (never tradable, never in turnover).  Clock:
63-session decision clock anchored byte-exact to the S0 start 2018-04-04
(decisions at index multiples of 63 from the anchor, per the A9-F recommendation
frozen in selection_freeze.json); decision computed on that session's PIT close;
fill at the NEXT allowed session; 63-session holding (weights fixed between
decision slots); force-flat at every fold boundary.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from research.assets.common.contracts import canonical_json, require_token
from research.assets.stocks.factory import CASH_SYMBOL

#: Family identity as frozen in selection_freeze.json selected_families[0].
FAMILY_ID = "SFV4-A5-H1-PARTICIPATION-SHIFT"

#: Schema token for every payload this family emits.
FAMILY_SCHEMA = "stocks_free_v4/family_participation@1"

#: Hypothesis id from the frozen proposal.
HYPOTHESIS_ID = "SFV4-A5-H1"

# --------------------------------------------------------------------------- #
# frozen universe (proposal authorized_pit_inputs / universe_and_schedule)
# --------------------------------------------------------------------------- #
#: The 11 sector ETFs ranked at each decision, in frozen order.
SECTOR_SYMBOLS = (
    "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY",
)

#: SPY is the benchmark context denominator ONLY: never held, never a feature.
BENCHMARK_SYMBOL = "SPY"

# --------------------------------------------------------------------------- #
# frozen clock (selection freeze condition: byte-exact anchor pinning)
# --------------------------------------------------------------------------- #
#: The decision clock anchor: the S0 start session (A9-F byte-exact pin).
ANCHOR_SESSION = "2018-04-04"

#: Sessions between decision slots (quarterly cadence on the session calendar).
CLOCK_PERIOD_SESSIONS = 63

#: Holding period; weights are fixed between decision slots.
HOLDING_SESSIONS = 63

#: Total shock lookback (21 + 231, 63 + 189, or stale 21 + 168 within 252).
WARMUP_SESSIONS = 252

#: Fill clock: decision at PIT close of t fills at the next allowed session.
DECISION_LAG_SESSIONS = 1

# --------------------------------------------------------------------------- #
# frozen book form (proposal anchor paragraph)
# --------------------------------------------------------------------------- #
LONG_LEGS = 3
SHORT_LEGS = 3
LEG_WEIGHT = 1.0 / 6.0
BOOK_GROSS = 1.0
BOOK_NET = 0.0

#: Minimum eligible rank set for the 3v3 book to be constructible (fail-closed
#: below this; the real schedule shows 10 or 11 eligible at every decision).
MIN_RANK_SET = LONG_LEGS + SHORT_LEGS

# --------------------------------------------------------------------------- #
# frozen data sources (proposal authorized_pit_inputs, verbatim semantics)
# --------------------------------------------------------------------------- #
DV_SOURCE = (
    "{SYM}_none_p1.json fields datetime, close, volume (raw as-traded); "
    "DV_s(u) = close_s(u) * volume_s(u) is a declared price-level feature on "
    "the authorized raw path; the volume field of the _all files is NOT used "
    "(back-adjustment distorts it)"
)
RETURN_SOURCE = (
    "{SYM}_all_p1.json field datetime, close (split+dividend adjusted) for leg "
    "and spread total returns; its volume field is never read"
)
BENCHMARK_SOURCE = (
    "SPY_all_p1.json field datetime, close (adjusted) used only as the "
    "benchmark context denominator; SPY is never held and never a feature"
)

# --------------------------------------------------------------------------- #
# frozen costs / turnover / factor-alpha (baseline_invariants.json)
# --------------------------------------------------------------------------- #
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0
TURNOVER_CEILING_TWO_WAY_PER_YEAR = 6.0

#: This arm's declared frozen risk-match scale (proposal factor_alpha_test):
#: the long-leg gross exposure of the dollar-neutral book, applied ex ante to
#: the SPY total-return path; realized arm volatility is never substituted.
RISK_MATCH_SCALE = 0.5

# --------------------------------------------------------------------------- #
# frozen folds (baseline_invariants.json, verbatim)
# --------------------------------------------------------------------------- #
S0_START = "2018-04-04"
S0_END = "2025-07-31"          # screening window end; max scored date


@dataclass(frozen=True)
class Fold:
    """One frozen S0 fold window (baseline_invariants.json folds)."""

    fold_id: str
    start: str
    end: str

    def to_payload(self) -> dict[str, Any]:
        return {"fold_id": self.fold_id, "start": self.start, "end": self.end}


FOLDS: tuple[Fold, ...] = (
    Fold("S0_FOLD_1", "2018-04-04", "2020-09-01"),
    Fold("S0_FOLD_2", "2020-09-10", "2023-02-09"),
    Fold("S0_FOLD_3", "2023-02-17", "2025-07-24"),
)

# --------------------------------------------------------------------------- #
# arm roles and keys
# --------------------------------------------------------------------------- #
ROLE_ANCHOR = "anchor"
ROLE_NEIGHBOUR = "neighbour"
ROLE_CONTROL = "causal_negative_control"

ARM_KEY_ANCHOR = "A"
ARM_KEY_NEIGHBOUR = "N"
ARM_KEY_CONTROL = "C"

CASH_SEMANTICS = "EXPLICIT_RESIDUAL_LEG_NEVER_TRADABLE"
FILL_SEMANTICS = "DECISION_PIT_CLOSE_T_FILL_NEXT_ALLOWED_SESSION"
CLOCK_SEMANTICS = "ANCHORED_63_SESSION_CLOCK_DECISIONS_AT_ANCHOR_INDEX_MULTIPLES_OF_63"


class ArmConfigError(ValueError):
    """Raised when an arm configuration violates the frozen contract."""


#: Frozen arm ids, keyed by arm key (selection_freeze.json arms[].arm_id).
ARM_IDS: dict[str, str] = {
    ARM_KEY_ANCHOR: "SFV4-A5-H1-A",
    ARM_KEY_NEIGHBOUR: "SFV4-A5-H1-N",
    ARM_KEY_CONTROL: "SFV4-A5-H1-C",
}

#: Frozen roles, keyed by arm key.
ARM_ROLES: dict[str, str] = {
    ARM_KEY_ANCHOR: ROLE_ANCHOR,
    ARM_KEY_NEIGHBOUR: ROLE_NEIGHBOUR,
    ARM_KEY_CONTROL: ROLE_CONTROL,
}


@dataclass(frozen=True)
class ShockWindows:
    """Closed index windows of one arm's shock ratio.

    Offsets are counted BACK from the decision session index ``t`` on the
    master session calendar: ``mean(DV[t - start_back .. t - end_back])``
    (both ends inclusive).  ``end_back == 0`` means the window reaches the
    decision session itself (PIT-completed data only); the causal control
    uses ``end_back == 63`` so its freshest input is one full holding period
    old.  Structural PIT guarantee: the deepest read is ``t - start_back``
    and the shallowest is ``t - end_back <= t`` — no future index can be
    addressed.
    """

    num_start_back: int
    num_end_back: int
    den_start_back: int
    den_end_back: int

    def __post_init__(self) -> None:
        ints = (self.num_start_back, self.num_end_back,
                self.den_start_back, self.den_end_back)
        if any(isinstance(v, bool) or not isinstance(v, int) for v in ints):
            raise ArmConfigError(f"window offsets must be ints, got {ints!r}")
        if min(ints) < 0:
            raise ArmConfigError(f"window offsets must be non-negative, got {ints!r}")
        if self.num_end_back > self.num_start_back or self.den_end_back > self.den_start_back:
            raise ArmConfigError(
                "end_back must not exceed start_back (windows grow backwards "
                f"from t); got {ints!r}"
            )
        lookback = self.total_lookback
        if lookback != WARMUP_SESSIONS:
            raise ArmConfigError(
                f"total lookback must be the frozen {WARMUP_SESSIONS} sessions, "
                f"got {lookback}"
            )

    @property
    def numerator_sessions(self) -> int:
        return self.num_start_back - self.num_end_back + 1

    @property
    def denominator_sessions(self) -> int:
        return self.den_start_back - self.den_end_back + 1

    @property
    def total_lookback(self) -> int:
        """Deepest session read, counted back from t (frozen 252)."""
        return max(self.num_start_back, self.den_start_back) + 1

    def to_payload(self) -> dict[str, Any]:
        return {
            "numerator": {"start_back": self.num_start_back,
                          "end_back": self.num_end_back,
                          "sessions": self.numerator_sessions},
            "denominator": {"start_back": self.den_start_back,
                            "end_back": self.den_end_back,
                            "sessions": self.denominator_sessions},
            "total_lookback_sessions": self.total_lookback,
        }


#: Frozen shock-ratio windows (proposal anchor / neighbour / control, verbatim).
SHOCK_WINDOWS: dict[str, ShockWindows] = {
    ARM_KEY_ANCHOR: ShockWindows(num_start_back=20, num_end_back=0,
                                 den_start_back=251, den_end_back=21),
    ARM_KEY_NEIGHBOUR: ShockWindows(num_start_back=62, num_end_back=0,
                                    den_start_back=251, den_end_back=63),
    ARM_KEY_CONTROL: ShockWindows(num_start_back=83, num_end_back=63,
                                  den_start_back=251, den_end_back=84),
}


@dataclass(frozen=True)
class ArmConfig:
    """One frozen arm head: complete, digest-pinned, immutable.

    Every field that can influence a scored run is in :meth:`to_payload`, so
    the sha256 :attr:`digest` pins the arm exactly; two configs with equal
    digests are the same arm by construction.
    """

    arm_key: str
    arm_id: str
    role: str
    windows: ShockWindows
    symbols: tuple[str, ...] = SECTOR_SYMBOLS
    benchmark_symbol: str = BENCHMARK_SYMBOL
    anchor_session: str = ANCHOR_SESSION
    clock_period_sessions: int = CLOCK_PERIOD_SESSIONS
    holding_sessions: int = HOLDING_SESSIONS
    long_legs: int = LONG_LEGS
    short_legs: int = SHORT_LEGS
    leg_weight: float = LEG_WEIGHT
    min_rank_set: int = MIN_RANK_SET
    warmup_sessions: int = WARMUP_SESSIONS
    decision_lag_sessions: int = DECISION_LAG_SESSIONS
    base_cost_bps: float = BASE_COST_BPS
    stress_cost_bps: float = STRESS_COST_BPS
    risk_match_scale: float = RISK_MATCH_SCALE
    dv_source: str = DV_SOURCE
    return_source: str = RETURN_SOURCE
    benchmark_source: str = BENCHMARK_SOURCE
    cash_semantics: str = CASH_SEMANTICS
    fill_semantics: str = FILL_SEMANTICS
    clock_semantics: str = CLOCK_SEMANTICS

    def __post_init__(self) -> None:
        require_token(self.arm_key, "arm_key")
        require_token(self.arm_id, "arm_id")
        require_token(self.role, "role")
        if self.arm_id != ARM_IDS.get(self.arm_key) or \
                self.role != ARM_ROLES.get(self.arm_key):
            raise ArmConfigError(
                f"arm_id/role {self.arm_id!r}/{self.role!r} do not match the "
                f"frozen head for arm key {self.arm_key!r} "
                f"({ARM_IDS.get(self.arm_key)!r}/{ARM_ROLES.get(self.arm_key)!r})"
            )
        if tuple(self.symbols) != SECTOR_SYMBOLS:
            raise ArmConfigError(
                "the participation universe is exactly the frozen 11 sector "
                "ETFs in frozen order; got a different symbol tuple"
            )
        if self.benchmark_symbol in self.symbols:
            raise ArmConfigError("the benchmark must never be a tradable leg")
        if self.windows is not SHOCK_WINDOWS[self.arm_key]:
            raise ArmConfigError(
                f"arm {self.arm_key!r} must carry its frozen ShockWindows"
            )
        if (self.long_legs, self.short_legs) != (LONG_LEGS, SHORT_LEGS):
            raise ArmConfigError("book form is frozen at 3 long / 3 short legs")
        if self.leg_weight != LEG_WEIGHT:
            raise ArmConfigError(f"leg weight is frozen at {LEG_WEIGHT!r}")
        if abs(self.long_legs * self.leg_weight
               + self.short_legs * (-self.leg_weight)) > 1e-12:
            raise ArmConfigError("book net must be 0 by construction")
        if abs((self.long_legs + self.short_legs) * self.leg_weight
               - BOOK_GROSS) > 1e-12:
            raise ArmConfigError("6 legs x 1/6 must equal the frozen gross 1.0")
        if self.min_rank_set != MIN_RANK_SET:
            raise ArmConfigError(f"min_rank_set is frozen at {MIN_RANK_SET}")
        if self.clock_period_sessions != CLOCK_PERIOD_SESSIONS or \
                self.holding_sessions != HOLDING_SESSIONS or \
                self.anchor_session != ANCHOR_SESSION or \
                self.warmup_sessions != WARMUP_SESSIONS:
            raise ArmConfigError("clock/holding/warmup constants are frozen")
        if self.decision_lag_sessions != DECISION_LAG_SESSIONS:
            raise ArmConfigError("fill clock is frozen at next allowed session")
        if (self.base_cost_bps, self.stress_cost_bps) != (BASE_COST_BPS, STRESS_COST_BPS):
            raise ArmConfigError("arm costs must equal the shared contract costs")
        if self.risk_match_scale != RISK_MATCH_SCALE:
            raise ArmConfigError(f"risk-match scale is frozen at {RISK_MATCH_SCALE!r}")

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": FAMILY_SCHEMA,
            "family_id": FAMILY_ID,
            "hypothesis_id": HYPOTHESIS_ID,
            "arm_id": self.arm_id,
            "arm_key": self.arm_key,
            "role": self.role,
            "universe": {
                "symbols": list(self.symbols),
                "benchmark_symbol": self.benchmark_symbol,
                "benchmark_never_held_never_feature": True,
            },
            "book": {
                "long_legs": self.long_legs,
                "short_legs": self.short_legs,
                "leg_weight": self.leg_weight,
                "gross": BOOK_GROSS,
                "net": BOOK_NET,
                "min_rank_set": self.min_rank_set,
                "cash_semantics": self.cash_semantics,
                "tie_break": "TICKER_ALPHABETICAL_ASCENDING",
                "rank_direction": "SHOCK_DESCENDING",
            },
            "shock_windows": self.windows.to_payload(),
            "clock": {
                "semantics": self.clock_semantics,
                "anchor_session": self.anchor_session,
                "period_sessions": self.clock_period_sessions,
                "holding_sessions": self.holding_sessions,
                "warmup_sessions": self.warmup_sessions,
                "decision_lag_sessions": self.decision_lag_sessions,
                "fill_semantics": self.fill_semantics,
            },
            "risk_matched_rule": {
                "benchmark": "SPY_total_return_adjusted",
                "scale": self.risk_match_scale,
                "note": "frozen ex ante; realized arm volatility never substituted",
            },
            "costs": {
                "base_bps_per_side": self.base_cost_bps,
                "stress_bps_per_side": self.stress_cost_bps,
            },
            "authorized_pit_inputs": {
                "dollar_volume": self.dv_source,
                "returns": self.return_source,
                "benchmark": self.benchmark_source,
            },
        }

    @property
    def digest(self) -> str:
        """sha256 over the canonical JSON of the frozen config payload."""
        return hashlib.sha256(canonical_json(self.to_payload()).encode("utf-8")).hexdigest()


def build_arm_configs() -> dict[str, ArmConfig]:
    """The three frozen arm heads A/N/C, keyed by arm key."""
    specs = {
        ARM_KEY_ANCHOR: ("SFV4-A5-H1-A", ROLE_ANCHOR),
        ARM_KEY_NEIGHBOUR: ("SFV4-A5-H1-N", ROLE_NEIGHBOUR),
        ARM_KEY_CONTROL: ("SFV4-A5-H1-C", ROLE_CONTROL),
    }
    return {
        key: ArmConfig(arm_key=key, arm_id=arm_id, role=role,
                       windows=SHOCK_WINDOWS[key])
        for key, (arm_id, role) in specs.items()
    }


def arm_config_digests() -> dict[str, str]:
    """sha256 config digests of the three frozen arms, keyed by arm key."""
    return {key: cfg.digest for key, cfg in sorted(build_arm_configs().items())}


__all__ = [
    "ANCHOR_SESSION",
    "ARM_KEY_ANCHOR",
    "ARM_KEY_CONTROL",
    "ARM_KEY_NEIGHBOUR",
    "BASE_COST_BPS",
    "BENCHMARK_SOURCE",
    "BENCHMARK_SYMBOL",
    "BOOK_GROSS",
    "BOOK_NET",
    "CASH_SYMBOL",
    "CASH_SEMANTICS",
    "CLOCK_PERIOD_SESSIONS",
    "CLOCK_SEMANTICS",
    "DECISION_LAG_SESSIONS",
    "DV_SOURCE",
    "FAMILY_ID",
    "FAMILY_SCHEMA",
    "FILL_SEMANTICS",
    "FOLDS",
    "Fold",
    "HOLDING_SESSIONS",
    "HYPOTHESIS_ID",
    "LEG_WEIGHT",
    "LONG_LEGS",
    "MIN_RANK_SET",
    "RETURN_SOURCE",
    "RISK_MATCH_SCALE",
    "ROLE_ANCHOR",
    "ROLE_CONTROL",
    "ROLE_NEIGHBOUR",
    "SECTOR_SYMBOLS",
    "SHORT_LEGS",
    "SHOCK_WINDOWS",
    "S0_END",
    "S0_START",
    "STRESS_COST_BPS",
    "TURNOVER_CEILING_TWO_WAY_PER_YEAR",
    "WARMUP_SESSIONS",
    "ArmConfig",
    "ArmConfigError",
    "ShockWindows",
    "arm_config_digests",
    "build_arm_configs",
]
