"""Frozen arm configuration heads for family SFV3-A6-TOM-SETTLE (A9).

Implements the executable contract in
``research/control/stocks_free_v3_run/selection_freeze.json`` (``families[1]``)
from the mechanism source
``research/proposals/stocks_free_v3/a6_family_SFV3-A6-TOM-SETTLE.md``
(sections 4, 5, 8, 9).  This module is CONFIGURATION ONLY: no schedule
construction, no data access, no disk writes, no network, no PnL.

The three frozen arms (identical books, gross values, clocks, costs and
risk-matched rule; ONLY the window membership differs):

* ``SFV3-A6-TOM-SETTLE-A`` (anchor)      — window = last 3 regular sessions of
  month M plus the first 2 of M+1 (5 sessions);
* ``SFV3-A6-TOM-SETTLE-N`` (neighbour)   — window = first 3 regular sessions of
  month M only (Ogden's settlement channel isolated);
* ``SFV3-A6-TOM-SETTLE-C`` (causal negative control) — window = regular-session
  ordinals 8-12 of each month (mid-month; disjoint from the anchor window for
  every month length with at least 15 sessions — every real US equity month
  has 19-23 sessions).

Two frozen books and no other states (proposal section 5): the TOM book holds
each of the 11 cohort ETFs at ``TOM_GROSS / 11`` (gross 0.50); the BASE book
holds each at ``BASE_GROSS / 11`` (gross 0.30); CASH is the residual to 1.0
and is never a tradable leg.  Clock: decision at the close of completed
session T determines the book for the fill at the close of T+1 (canonical
close-fill; the fill day earns no same-day return on the new weights).
24 transitions/yr; windows straddling fold/purge boundaries lose those scored
sessions, no compensation trades.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from research.assets.common.contracts import canonical_json, require_finite_float, require_token
from research.assets.stocks.calendar import CALENDAR_ID
from research.assets.stocks.factory import CASH_SYMBOL
from research.stocks_free_v3.authority import COHORT_SYMBOLS
from research.stocks_free_v3.benchmarks import VolScalingRule

#: Family identity as frozen in selection_freeze.json families[1].
FAMILY_ID = "SFV3-A6-TOM-SETTLE"

#: Schema token for every payload this family emits.
FAMILY_SCHEMA = "stocks_free_v3/family_tom_settle@1"

#: Number of sessions between the decision close and the fill close (T -> T+1).
DECISION_LAG_SESSIONS = 1

#: Frozen book gross values (proposal section 5; reasoned constants, no grid).
TOM_GROSS = 0.50
BASE_GROSS = 0.30

#: Shared contract costs (selection_freeze.json shared_contract.costs).
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0

#: The ex-ante gross/vol rule every arm declares for the RISK_MATCHED_SPY_CONTEXT
#: builder (proposal section 9): target 0.5% daily vol (half of SPY's long-run
#: ~1% daily vol, a literature-level constant), 63-session lookback, clip band
#: equal to the arm's own designed gross range [0.30, 0.50].
FROZEN_VOL_SCALING_RULE = VolScalingRule(
    lookback_sessions=63,
    target_daily_vol=0.005,
    min_gross=0.30,
    max_gross=0.50,
)

#: Frozen schedule expectations (proposal sections 4 and 6; checked by
#: :mod:`research.stocks_free_v3.family_tom_settle.schedule`, never assumed).
EXPECTED_TRANSITIONS_PER_YEAR = 24
#: 24 transitions x |delta gross| 0.20, the proposal's own arithmetic, reported
#: before any scoring (schedule-only turnover gate: <= 6.0 two-way per year).
EXPECTED_TWO_WAY_TURNOVER_PER_YEAR = 4.80
TURNOVER_CEILING_TWO_WAY_PER_YEAR = 6.0

#: Minimum regular sessions per calendar month accepted by the schedule
#: builder.  Real US equity months have 19-23 sessions (measured range on the
#: frozen US_EQUITY_REGULAR_V1 table over S0); the floor only rejects
#: synthetic misuse that would make the mid-month control window (ordinals
#: 8-12) empty.  Fail-closed, never guessed around.
MIN_MONTH_SESSIONS = 8

#: Anchor/control disjointness needs the control's last ordinal (12) strictly
#: below an anchor tail ordinal (month_length - 2), i.e. month_length >= 15.
MIN_MONTH_SESSIONS_ANCHOR_CONTROL_DISJOINT = 15

ROLE_ANCHOR = "anchor"
ROLE_NEIGHBOUR = "neighbour"
ROLE_CONTROL = "causal_negative_control"

ARM_KEY_ANCHOR = "A"
ARM_KEY_NEIGHBOUR = "N"
ARM_KEY_CONTROL = "C"

#: CASH semantics string pinned in every config payload.
CASH_SEMANTICS = "EXPLICIT_RESIDUAL_LEG_NEVER_TRADABLE"

#: Clock semantics string pinned in every config payload.
CLOCK_SEMANTICS = "DECISION_CLOSE_T_FILL_CLOSE_T_PLUS_1_CANONICAL_CLOSE_FILL"


class ArmConfigError(ValueError):
    """Raised when an arm configuration violates the frozen contract."""


@dataclass(frozen=True)
class WindowRule:
    """One arm's frozen window membership rule on month ordinals.

    Ordinals are counted on the REGULAR-SESSION calendar within a calendar
    month (never on calendar dates), so holiday-thinned months need no special
    cases.  Exactly one of the three kinds may be non-empty:

    * ``first_ordinals`` — ordinals from the month start (neighbour: 1..3;
      anchor head: 1..2);
    * ``last_ordinals``  — ordinal DISTANCES from the month end, 1 = last
      session (anchor tail: 1..3);
    * ``explicit_ordinals`` — literal ordinals (control: 8..12), clipped to
      the month length when a month is shorter than the largest ordinal
      (never happens on real US months; deterministic by construction).

    ``window_ordinals(month_length)`` returns the sorted ordinal list; the
    schedule layer maps ordinals to sessions through
    :func:`research.stocks_free_v3.family_tom_settle.schedule.month_ordinals`.
    """

    rule_kind: str          # ANCHOR_TOM | NEIGHBOUR_MONTH_START | CONTROL_MID_MONTH
    first_ordinals: tuple[int, ...] = ()
    last_ordinals: tuple[int, ...] = ()
    explicit_ordinals: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.rule_kind not in (
            "ANCHOR_TOM", "NEIGHBOUR_MONTH_START", "CONTROL_MID_MONTH"
        ):
            raise ArmConfigError(f"unknown window rule kind {self.rule_kind!r}")
        for name in ("first_ordinals", "last_ordinals", "explicit_ordinals"):
            value = tuple(getattr(self, name))
            if any(isinstance(o, bool) or not isinstance(o, int) or o < 1 for o in value):
                raise ArmConfigError(f"{name} must be positive ints, got {value!r}")
            if list(value) != sorted(set(value)):
                raise ArmConfigError(f"{name} must be strictly increasing, got {value!r}")
        kinds = (
            bool(self.first_ordinals),
            bool(self.last_ordinals),
            bool(self.explicit_ordinals),
        )
        if self.rule_kind == "ANCHOR_TOM":
            if not (kinds[0] and kinds[1]) or kinds[2]:
                raise ArmConfigError(
                    "ANCHOR_TOM needs first_ordinals (month-start head) and "
                    "last_ordinals (month-end tail) and nothing else"
                )
        elif self.rule_kind == "NEIGHBOUR_MONTH_START":
            if not (kinds[0] and not kinds[1] and not kinds[2]):
                raise ArmConfigError(
                    "NEIGHBOUR_MONTH_START needs only first_ordinals"
                )
        else:
            if not (kinds[2] and not kinds[0] and not kinds[1]):
                raise ArmConfigError("CONTROL_MID_MONTH needs only explicit_ordinals")
        if self.first_ordinals != tuple(range(1, len(self.first_ordinals) + 1)):
            raise ArmConfigError(
                "first_ordinals must be contiguous from ordinal 1 "
                f"(month-start head), got {self.first_ordinals!r}"
            )
        if self.last_ordinals != tuple(range(1, len(self.last_ordinals) + 1)):
            raise ArmConfigError(
                "last_ordinals must be contiguous distances from 1 (month end), "
                f"got {self.last_ordinals!r}"
            )
        # The three window SHAPES are frozen constants of the contract
        # (selection_freeze.json families[1].arms[].window): anything else is
        # a different family and is rejected, not approximated.
        frozen_shapes = {
            "ANCHOR_TOM": {"first_ordinals": (1, 2), "last_ordinals": (1, 2, 3)},
            "NEIGHBOUR_MONTH_START": {"first_ordinals": (1, 2, 3)},
            "CONTROL_MID_MONTH": {"explicit_ordinals": (8, 9, 10, 11, 12)},
        }
        for field, frozen in frozen_shapes[self.rule_kind].items():
            if tuple(getattr(self, field)) != frozen:
                raise ArmConfigError(
                    f"{self.rule_kind}.{field} is frozen to {frozen}, got "
                    f"{getattr(self, field)!r}; window reshapes are not permitted"
                )

    @property
    def max_ordinal(self) -> int:
        """Largest literal ordinal the rule can name (tail distances aside).

        Tail ordinals resolve from the month end, so their ordinal value
        depends on month length; this property covers only the ordinals that
        are known without a month length (head + explicit windows).
        """
        return max(self.first_ordinals + self.explicit_ordinals, default=0)

    def window_ordinals(self, month_length: int) -> tuple[int, ...]:
        """Sorted window ordinals for one month of ``month_length`` sessions.

        The control window is the intersection of its explicit ordinals with
        ``1..month_length`` (deterministic clip); anchor and neighbour
        ordinals are always <= month_length for any month accepted by the
        schedule builder.  Tail ordinals are resolved from the month end:
        distance 1 = ordinal ``month_length``.
        """
        if month_length < MIN_MONTH_SESSIONS:
            raise ArmConfigError(
                f"month_length {month_length} < frozen minimum "
                f"{MIN_MONTH_SESSIONS}; the schedule builder fails closed"
            )
        head = set(self.first_ordinals)
        tail = {month_length + 1 - d for d in self.last_ordinals}
        explicit = {o for o in self.explicit_ordinals if o <= month_length}
        return tuple(sorted(head | tail | explicit))

    def to_payload(self) -> dict[str, Any]:
        return {
            "rule_kind": self.rule_kind,
            "first_ordinals": list(self.first_ordinals),
            "last_ordinals": list(self.last_ordinals),
            "explicit_ordinals": list(self.explicit_ordinals),
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(canonical_json(self.to_payload()).encode("utf-8")).hexdigest()


#: Frozen window rules (selection_freeze.json families[1].arms[].window).
WINDOW_RULES: dict[str, WindowRule] = {
    ARM_KEY_ANCHOR: WindowRule(
        rule_kind="ANCHOR_TOM",
        first_ordinals=(1, 2),
        last_ordinals=(1, 2, 3),
    ),
    ARM_KEY_NEIGHBOUR: WindowRule(
        rule_kind="NEIGHBOUR_MONTH_START",
        first_ordinals=(1, 2, 3),
    ),
    ARM_KEY_CONTROL: WindowRule(
        rule_kind="CONTROL_MID_MONTH",
        explicit_ordinals=(8, 9, 10, 11, 12),
    ),
}

#: Book names emitted in ``ScheduledFill.book``.
BOOK_TOM = "TOM"
BOOK_BASE = "BASE"


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
    window: WindowRule
    symbols: tuple[str, ...]
    tom_gross: float
    base_gross: float
    vol_scaling_rule: VolScalingRule
    decision_lag_sessions: int
    calendar_id: str
    base_cost_bps: float
    stress_cost_bps: float
    cash_semantics: str = CASH_SEMANTICS
    clock_semantics: str = CLOCK_SEMANTICS
    expected_transitions_per_year: int = EXPECTED_TRANSITIONS_PER_YEAR
    expected_two_way_turnover_per_year: float = EXPECTED_TWO_WAY_TURNOVER_PER_YEAR
    _extra: dict = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        require_token(self.arm_key, "arm_key")
        require_token(self.arm_id, "arm_id")
        require_token(self.role, "role")
        if not self.arm_id.startswith(FAMILY_ID + "-"):
            raise ArmConfigError(
                f"arm_id {self.arm_id!r} must be prefixed by the family id"
            )
        if self.role not in (ROLE_ANCHOR, ROLE_NEIGHBOUR, ROLE_CONTROL):
            raise ArmConfigError(f"unknown arm role {self.role!r}")
        if tuple(self.symbols) != tuple(COHORT_SYMBOLS):
            raise ArmConfigError(
                "the TOM-SETTLE universe is exactly the frozen 11-ETF cohort "
                "in frozen order; got a different symbol tuple"
            )
        require_finite_float(self.tom_gross, "tom_gross", positive=True)
        require_finite_float(self.base_gross, "base_gross", positive=True)
        if self.tom_gross <= self.base_gross:
            raise ArmConfigError("tom_gross must exceed base_gross (window enters at higher gross)")
        if not isinstance(self.vol_scaling_rule, VolScalingRule):
            raise ArmConfigError("vol_scaling_rule must be the frozen VolScalingRule type")
        if isinstance(self.decision_lag_sessions, bool) or \
                self.decision_lag_sessions != DECISION_LAG_SESSIONS:
            raise ArmConfigError(
                f"decision_lag_sessions must be {DECISION_LAG_SESSIONS} "
                "(canonical close-fill clock T -> T+1)"
            )
        if self.calendar_id != CALENDAR_ID:
            raise ArmConfigError(
                f"calendar_id must be the frozen {CALENDAR_ID}, got {self.calendar_id!r}"
            )
        if (self.base_cost_bps, self.stress_cost_bps) != (BASE_COST_BPS, STRESS_COST_BPS):
            raise ArmConfigError("arm costs must equal the shared contract costs")

    @property
    def window_key(self) -> str:
        return self.arm_key

    def leg_weight(self, book: str) -> float:
        """Equal weight per ETF leg of one book (gross / 11 legs)."""
        gross = self.tom_gross if book == BOOK_TOM else self.base_gross
        if book not in (BOOK_TOM, BOOK_BASE):
            raise ArmConfigError(f"unknown book {book!r}")
        return gross / len(self.symbols)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": FAMILY_SCHEMA,
            "family_id": FAMILY_ID,
            "arm_id": self.arm_id,
            "arm_key": self.arm_key,
            "role": self.role,
            "universe": {"symbols": list(self.symbols), "basket": "EQUAL_WEIGHT_ALL_LEGS"},
            "books": {
                "tom": {"gross": self.tom_gross,
                        "leg_weight": self.leg_weight(BOOK_TOM),
                        "legs": len(self.symbols)},
                "base": {"gross": self.base_gross,
                         "leg_weight": self.leg_weight(BOOK_BASE),
                         "legs": len(self.symbols)},
                "cash_semantics": self.cash_semantics,
                "intra_window_re_equalization": "NEVER",
            },
            "window": self.window.to_payload(),
            "clock": {
                "semantics": self.clock_semantics,
                "decision_lag_sessions": self.decision_lag_sessions,
                "expected_transitions_per_year": self.expected_transitions_per_year,
                "expected_two_way_turnover_per_year":
                    self.expected_two_way_turnover_per_year,
            },
            "risk_matched_rule": self.vol_scaling_rule.to_payload(),
            "costs": {
                "base_bps_per_side": self.base_cost_bps,
                "stress_bps_per_side": self.stress_cost_bps,
            },
            "calendar_id": self.calendar_id,
        }

    @property
    def digest(self) -> str:
        """sha256 over the canonical JSON of the frozen config payload."""
        return hashlib.sha256(canonical_json(self.to_payload()).encode("utf-8")).hexdigest()


def build_arm_configs() -> dict[str, ArmConfig]:
    """The three frozen arm heads A/N/C, keyed by arm key."""
    specs = {
        ARM_KEY_ANCHOR: ("SFV3-A6-TOM-SETTLE-A", ROLE_ANCHOR),
        ARM_KEY_NEIGHBOUR: ("SFV3-A6-TOM-SETTLE-N", ROLE_NEIGHBOUR),
        ARM_KEY_CONTROL: ("SFV3-A6-TOM-SETTLE-C", ROLE_CONTROL),
    }
    return {
        key: ArmConfig(
            arm_key=key,
            arm_id=arm_id,
            role=role,
            window=WINDOW_RULES[key],
            symbols=tuple(COHORT_SYMBOLS),
            tom_gross=TOM_GROSS,
            base_gross=BASE_GROSS,
            vol_scaling_rule=FROZEN_VOL_SCALING_RULE,
            decision_lag_sessions=DECISION_LAG_SESSIONS,
            calendar_id=CALENDAR_ID,
            base_cost_bps=BASE_COST_BPS,
            stress_cost_bps=STRESS_COST_BPS,
        )
        for key, (arm_id, role) in specs.items()
    }


def arm_config_digests() -> dict[str, str]:
    """sha256 config digests of the three frozen arms, keyed by arm key."""
    return {key: cfg.digest for key, cfg in sorted(build_arm_configs().items())}


__all__ = [
    "ARM_KEY_ANCHOR",
    "ARM_KEY_CONTROL",
    "ARM_KEY_NEIGHBOUR",
    "BASE_COST_BPS",
    "BASE_GROSS",
    "BOOK_BASE",
    "BOOK_TOM",
    "CASH_SEMANTICS",
    "CASH_SYMBOL",
    "CLOCK_SEMANTICS",
    "DECISION_LAG_SESSIONS",
    "EXPECTED_TRANSITIONS_PER_YEAR",
    "EXPECTED_TWO_WAY_TURNOVER_PER_YEAR",
    "FAMILY_ID",
    "FAMILY_SCHEMA",
    "FROZEN_VOL_SCALING_RULE",
    "MIN_MONTH_SESSIONS",
    "MIN_MONTH_SESSIONS_ANCHOR_CONTROL_DISJOINT",
    "ROLE_ANCHOR",
    "ROLE_CONTROL",
    "ROLE_NEIGHBOUR",
    "STRESS_COST_BPS",
    "TOM_GROSS",
    "TURNOVER_CEILING_TWO_WAY_PER_YEAR",
    "WINDOW_RULES",
    "ArmConfig",
    "ArmConfigError",
    "WindowRule",
    "arm_config_digests",
    "build_arm_configs",
]
