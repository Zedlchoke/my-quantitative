"""Frozen arm configuration for family SFV4-A4-H1-SEMIVARIANCE-SHARE (A9).

Implements the executable contract frozen in
``research/control/stocks_free_v4_run/selection_freeze.json``
(``selected_families[1]``, family_id ``SFV4-A4-H1-SEMIVARIANCE-SHARE``) from
the mechanism source ``research/control/stocks_free_v4_run/proposals/a4_h1.json``
and the frozen conventions in
``research/control/stocks_free_v4_run/baseline_invariants.json``.

This module is CONFIGURATION ONLY: constants, frozen arm heads and their
digests.  No schedule construction, no data access, no disk writes, no
network, and NO PnL of any kind.

The three frozen arms (identical book form, bands, weights, clock, fills,
universe, eligibility; ONLY the state window and the sort statistic differ):

* ``SFV4-A4-H1-A`` (anchor) — rank the 11 sector ETFs by the semivariance
  share ``S_i = DS_i / SS_i`` (downside / total sum of squared returns) over
  the trailing 126 sessions; long ranks 1-4, short ranks 8-11;
* ``SFV4-A4-H1-N`` (neighbour) — identical mechanism, state window 63
  sessions (the proposal's single fixed shorter window);
* ``SFV4-A4-H1-C`` (causal negative control) — identical book form, sectors
  ranked by total-variance LEVEL ``SS_i`` descending (long the 4 highest
  variance sectors, short the 4 lowest); preregistered falsification per the
  proposal (refuted if control expectancy > 0 or
  ``|control alpha| >= 0.5 x anchor alpha``).

Frozen ex-ante conditions carried verbatim from selection_freeze.json:

* KAPPA FALLBACK (frozen before any V4 return was observed):
  ``kappa_t = 1.0`` flat for scored sessions until 252 scored sessions have
  accumulated; thereafter the trailing-252 OLS slope of the arm's daily
  return on the SPY total return, clipped to [0, 2]; the fallback is never
  refit in-sample.  Implemented as the pure function
  :func:`research.stocks_free_v4.family_semivar.signals.kappa_frozen`.
* Clock anchoring pinned byte-exact: the 21-session decision clock is
  anchored to the S0 start ``2018-04-04`` (global session-count clock; see
  :mod:`research.stocks_free_v4.family_semivar.schedule`).
* Early fold-1 net-exposure stretches (9 ticks net +0.25 anchor; 15 ticks
  5 legs neighbour) are FROZEN EXPECTED BEHAVIOR of the eligibility rule
  (XLC enters the ranking only once it has a full state window of authorized
  history; incumbents are retained through the rank 5-7 hysteresis buffer).
  They are recorded, never "fixed".
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from research.assets.common.contracts import canonical_json, require_token

#: Family identity as frozen in selection_freeze.json selected_families[1].
FAMILY_ID = "SFV4-A4-H1-SEMIVARIANCE-SHARE"

#: Schema token for every payload this family emits.
FAMILY_SCHEMA = "stocks_free_v4/family_semivar@1"

#: Proposal source pin (research/control/stocks_free_v4_run/proposals/a4_h1.json).
PROPOSAL_HYPOTHESIS_ID = "SFV4-A4-H1"

# --------------------------------------------------------------------------- #
# frozen universe (proposal authorized_pit_inputs / universe_and_schedule)
# --------------------------------------------------------------------------- #
#: The 11 SPDR sector ETFs of the frozen cohort, in frozen order.  SPY is
#: NEVER a held leg (benchmark context only) and CASH is never a symbol.
SECTOR_SYMBOLS = (
    "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY",
)
BENCHMARK_SYMBOL = "SPY"

# --------------------------------------------------------------------------- #
# frozen mechanism constants (proposal anchor: single rule, no parameter menu)
# --------------------------------------------------------------------------- #
#: Anchor state window (trailing sessions of squared returns).
STATE_WINDOW_ANCHOR = 126
#: Neighbour state window (the proposal's single fixed shorter variant).
STATE_WINDOW_NEIGHBOUR = 63
#: Control uses the anchor window (identical surface form, LEVEL sort).
STATE_WINDOW_CONTROL = STATE_WINDOW_ANCHOR

#: Session-count decision clock: every 21st SPY session, anchored to S0 start.
CLOCK_STEP_SESSIONS = 21
CLOCK_ANCHOR_SESSION = "2018-04-04"

#: Hysteresis book: 4 long / 4 short capacity; entry bands rank <= 4 (long)
#: and rank >= 8 (short); ranks 5-7 are the exit buffer where incumbents are
#: retained.  Ranks are 1-based, 1 = highest feature value.
N_LONG_LEGS = 4
N_SHORT_LEGS = 4
LONG_ENTRY_RANK_MAX = 4      # rank <= 4 enters / stays LONG band
SHORT_ENTRY_RANK_MIN = 8     # rank >= 8 enters / exits into SHORT band

#: Weight per held leg (+0.25 LONG, -0.25 SHORT); gross cap 2.0.
LEG_WEIGHT = 0.25
GROSS_CAP = 2.0

#: Sort statistics (arm key -> the one statistic its ranking uses).
SORT_SEMIVARIANCE_SHARE = "SEMIVARIANCE_SHARE"   # DS/SS, anchor + neighbour
SORT_VARIANCE_LEVEL = "VARIANCE_LEVEL"           # SS descending, control

# --------------------------------------------------------------------------- #
# frozen shared-convention costs / turnover / folds (baseline_invariants.json)
# --------------------------------------------------------------------------- #
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0
TURNOVER_CEILING_TWO_WAY_PER_YEAR = 6.0

#: Frozen folds (baseline_invariants.json folds[]).
FOLD_S0_FOLD_1 = ("S0_FOLD_1", "2018-04-04", "2020-09-01")
FOLD_S0_FOLD_2 = ("S0_FOLD_2", "2020-09-10", "2023-02-09")
FOLD_S0_FOLD_3 = ("S0_FOLD_3", "2023-02-17", "2025-07-24")
FOLDS = (FOLD_S0_FOLD_1, FOLD_S0_FOLD_2, FOLD_S0_FOLD_3)

#: S0 screening window and authorized pre-S0 warmup runway (proposal
#: window_discipline: the 126-session window at the first S0 decision is
#: filled from 2010-01-04..2018-04-03, 2076 sessions; nothing after the S0
#: end is ever read).
S0_START = CLOCK_ANCHOR_SESSION
S0_END = "2025-07-31"
WARMUP_RUNWAY_START = "2010-01-04"

# --------------------------------------------------------------------------- #
# frozen kappa fallback (selection_freeze.json condition 1; proposal
# factor_alpha_test.risk_matched_incremental_alpha)
# --------------------------------------------------------------------------- #
KAPPA_FALLBACK_VALUE = 1.0
KAPPA_FALLBACK_MIN_SCORED_SESSIONS = 252
KAPPA_OLS_TRAILING_SESSIONS = 252
KAPPA_CLIP_LOW = 0.0
KAPPA_CLIP_HIGH = 2.0

ROLE_ANCHOR = "anchor"
ROLE_NEIGHBOUR = "neighbour"
ROLE_CONTROL = "causal_negative_control"

ARM_KEY_ANCHOR = "A"
ARM_KEY_NEIGHBOUR = "N"
ARM_KEY_CONTROL = "C"

#: CASH semantics (baseline invariants: CASH is never a symbol; it absorbs
#: the residual and is excluded from turnover, concentration and drop-one).
CASH_SYMBOL = "CASH"
CASH_SEMANTICS = "EXPLICIT_RESIDUAL_LEG_NEVER_TRADABLE_NEVER_A_SYMBOL"

#: Clock semantics string pinned in every config payload.
CLOCK_SEMANTICS = (
    "DECISION_ON_SESSION_T_COMPLETED_DATA_FILL_NEXT_ALLOWED_SESSION_NEVER_SAME_SESSION"
)

#: The preregistered control falsification gate (proposal
#: causal_negative_control.preregistered_falsification_rule).
CONTROL_ALPHA_ABS_RATIO_LT = 0.5

#: Frozen expected-behavior note (selection_freeze.json condition 3), recorded
#: verbatim so no implementation lane ever "fixes" it.
EARLY_FOLD1_NET_EXPOSURE_NOTE = (
    "early fold-1 net-exposure stretches (9 ticks net +0.25 anchor; 15 ticks "
    "5 legs neighbour) are expected behavior, not defects"
)

#: XLC availability rule (proposal universe_and_schedule): a sector enters the
#: ranking only when it has >= STATE_WINDOW sessions of authorized adjusted
#: close history; before that it is excluded from ranks and held FLAT — an
#: availability rule, not a selection.
XLC_AVAILABILITY_RULE = (
    "a sector enters the ranking only when it has >= state-window sessions of "
    "authorized adjusted-close history ending at the decision session; before "
    "that it is excluded from ranks and held FLAT (availability rule, not a "
    "selection); XLC incepts 2018-06-19 in the staged snapshot"
)


class ArmConfigError(ValueError):
    """Raised when an arm configuration violates the frozen contract."""


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
    sort_statistic: str
    state_window_sessions: int
    symbols: tuple[str, ...]
    benchmark_symbol: str
    leg_weight: float
    n_long_legs: int
    n_short_legs: int
    long_entry_rank_max: int
    short_entry_rank_min: int
    gross_cap: float
    clock_step_sessions: int
    clock_anchor_session: str
    decision_fill_lag_sessions: int
    kappa_fallback_value: float
    kappa_fallback_min_scored_sessions: int
    kappa_ols_trailing_sessions: int
    kappa_clip_low: float
    kappa_clip_high: float
    base_cost_bps: float
    stress_cost_bps: float
    cash_semantics: str = CASH_SEMANTICS
    clock_semantics: str = CLOCK_SEMANTICS
    control_alpha_abs_ratio_lt: float = CONTROL_ALPHA_ABS_RATIO_LT
    _extra: dict = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        require_token(self.arm_key, "arm_key")
        require_token(self.arm_id, "arm_id")
        require_token(self.role, "role")
        if not self.arm_id.startswith(PROPOSAL_HYPOTHESIS_ID + "-"):
            raise ArmConfigError(
                f"arm_id {self.arm_id!r} must be prefixed by the hypothesis id "
                f"{PROPOSAL_HYPOTHESIS_ID} (frozen arm ids: SFV4-A4-H1-A/N/C)"
            )
        if self.role not in (ROLE_ANCHOR, ROLE_NEIGHBOUR, ROLE_CONTROL):
            raise ArmConfigError(f"unknown arm role {self.role!r}")
        if self.sort_statistic not in (SORT_SEMIVARIANCE_SHARE, SORT_VARIANCE_LEVEL):
            raise ArmConfigError(
                f"unknown sort statistic {self.sort_statistic!r}"
            )
        if tuple(self.symbols) != SECTOR_SYMBOLS:
            raise ArmConfigError(
                "the SEMIVARIANCE-SHARE universe is exactly the frozen 11 "
                "sector ETFs in frozen order; got a different symbol tuple"
            )
        if self.benchmark_symbol != BENCHMARK_SYMBOL:
            raise ArmConfigError(
                f"benchmark must be {BENCHMARK_SYMBOL} (never a held leg), got "
                f"{self.benchmark_symbol!r}"
            )
        if self.arm_key == ARM_KEY_ANCHOR:
            if self.sort_statistic != SORT_SEMIVARIANCE_SHARE or \
                    self.state_window_sessions != STATE_WINDOW_ANCHOR:
                raise ArmConfigError(
                    "anchor must be the semivariance-share sort on the "
                    f"{STATE_WINDOW_ANCHOR}-session window"
                )
        if self.arm_key == ARM_KEY_NEIGHBOUR:
            if self.sort_statistic != SORT_SEMIVARIANCE_SHARE or \
                    self.state_window_sessions != STATE_WINDOW_NEIGHBOUR:
                raise ArmConfigError(
                    "neighbour must be the semivariance-share sort on the "
                    f"{STATE_WINDOW_NEIGHBOUR}-session window"
                )
        if self.arm_key == ARM_KEY_CONTROL:
            if self.sort_statistic != SORT_VARIANCE_LEVEL or \
                    self.state_window_sessions != STATE_WINDOW_CONTROL:
                raise ArmConfigError(
                    "control must be the variance-LEVEL sort on the "
                    f"{STATE_WINDOW_CONTROL}-session window"
                )
        if self.leg_weight != LEG_WEIGHT or self.gross_cap != GROSS_CAP:
            raise ArmConfigError(
                f"leg weight is frozen at {LEG_WEIGHT} and gross cap at "
                f"{GROSS_CAP}; reshaping the book is not permitted"
            )
        if (self.n_long_legs, self.n_short_legs) != (N_LONG_LEGS, N_SHORT_LEGS):
            raise ArmConfigError("the book is frozen 4 long / 4 short")
        if (self.long_entry_rank_max, self.short_entry_rank_min) != (
            LONG_ENTRY_RANK_MAX, SHORT_ENTRY_RANK_MIN
        ):
            raise ArmConfigError(
                f"entry bands are frozen rank <= {LONG_ENTRY_RANK_MAX} (long) "
                f"and rank >= {SHORT_ENTRY_RANK_MIN} (short)"
            )
        if self.clock_step_sessions != CLOCK_STEP_SESSIONS or \
                self.clock_anchor_session != CLOCK_ANCHOR_SESSION:
            raise ArmConfigError(
                f"the decision clock is frozen at {CLOCK_STEP_SESSIONS} sessions "
                f"anchored to {CLOCK_ANCHOR_SESSION} (byte-exact pin)"
            )
        if self.decision_fill_lag_sessions != 1:
            raise ArmConfigError(
                "fills happen at the NEXT allowed session after the decision "
                "(lag 1); never a same-session fill"
            )
        if (self.kappa_fallback_value, self.kappa_fallback_min_scored_sessions,
                self.kappa_ols_trailing_sessions, self.kappa_clip_low,
                self.kappa_clip_high) != (
            KAPPA_FALLBACK_VALUE, KAPPA_FALLBACK_MIN_SCORED_SESSIONS,
            KAPPA_OLS_TRAILING_SESSIONS, KAPPA_CLIP_LOW, KAPPA_CLIP_HIGH,
        ):
            raise ArmConfigError(
                "the kappa fallback rule is frozen ex ante and may not be "
                "retuned per arm"
            )
        if (self.base_cost_bps, self.stress_cost_bps) != (BASE_COST_BPS, STRESS_COST_BPS):
            raise ArmConfigError("arm costs must equal the shared contract costs")

    @property
    def max_gross(self) -> float:
        """Gross of the fully-populated 4/4 book (== GROSS_CAP by design)."""
        return self.leg_weight * (self.n_long_legs + self.n_short_legs)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": FAMILY_SCHEMA,
            "family_id": FAMILY_ID,
            "hypothesis_id": PROPOSAL_HYPOTHESIS_ID,
            "arm_id": self.arm_id,
            "arm_key": self.arm_key,
            "role": self.role,
            "sort_statistic": self.sort_statistic,
            "state_window_sessions": self.state_window_sessions,
            "universe": {
                "symbols": list(self.symbols),
                "benchmark_symbol": self.benchmark_symbol,
                "xlc_availability_rule": XLC_AVAILABILITY_RULE,
            },
            "book": {
                "leg_weight": self.leg_weight,
                "n_long_legs": self.n_long_legs,
                "n_short_legs": self.n_short_legs,
                "long_entry_rank_max": self.long_entry_rank_max,
                "short_entry_rank_min": self.short_entry_rank_min,
                "gross_cap": self.gross_cap,
                "cash_semantics": self.cash_semantics,
                "static_weights_between_decisions": True,
            },
            "clock": {
                "step_sessions": self.clock_step_sessions,
                "anchor_session": self.clock_anchor_session,
                "semantics": self.clock_semantics,
                "decision_fill_lag_sessions": self.decision_fill_lag_sessions,
            },
            "kappa_fallback": {
                "fallback_value": self.kappa_fallback_value,
                "min_scored_sessions": self.kappa_fallback_min_scored_sessions,
                "ols_trailing_sessions": self.kappa_ols_trailing_sessions,
                "clip": [self.kappa_clip_low, self.kappa_clip_high],
                "in_sample_refit": "FORBIDDEN",
            },
            "control_gate": {
                "control_alpha_abs_ratio_lt": self.control_alpha_abs_ratio_lt,
                "refuted_if": "control expectancy > 0 OR |control alpha| >= 0.5 x anchor alpha",
            },
            "costs": {
                "base_bps_per_side": self.base_cost_bps,
                "stress_bps_per_side": self.stress_cost_bps,
            },
            "expected_behavior_notes": {
                "early_fold1_net_exposure": EARLY_FOLD1_NET_EXPOSURE_NOTE,
            },
        }

    @property
    def digest(self) -> str:
        """sha256 over the canonical JSON of the frozen config payload."""
        return hashlib.sha256(
            canonical_json(self.to_payload()).encode("utf-8")
        ).hexdigest()


def build_arm_configs() -> dict[str, ArmConfig]:
    """The three frozen arm heads A/N/C, keyed by arm key."""
    specs = {
        ARM_KEY_ANCHOR: (
            "SFV4-A4-H1-A", ROLE_ANCHOR, SORT_SEMIVARIANCE_SHARE,
            STATE_WINDOW_ANCHOR,
        ),
        ARM_KEY_NEIGHBOUR: (
            "SFV4-A4-H1-N", ROLE_NEIGHBOUR, SORT_SEMIVARIANCE_SHARE,
            STATE_WINDOW_NEIGHBOUR,
        ),
        ARM_KEY_CONTROL: (
            "SFV4-A4-H1-C", ROLE_CONTROL, SORT_VARIANCE_LEVEL,
            STATE_WINDOW_CONTROL,
        ),
    }
    return {
        key: ArmConfig(
            arm_key=key,
            arm_id=arm_id,
            role=role,
            sort_statistic=sort_stat,
            state_window_sessions=window,
            symbols=SECTOR_SYMBOLS,
            benchmark_symbol=BENCHMARK_SYMBOL,
            leg_weight=LEG_WEIGHT,
            n_long_legs=N_LONG_LEGS,
            n_short_legs=N_SHORT_LEGS,
            long_entry_rank_max=LONG_ENTRY_RANK_MAX,
            short_entry_rank_min=SHORT_ENTRY_RANK_MIN,
            gross_cap=GROSS_CAP,
            clock_step_sessions=CLOCK_STEP_SESSIONS,
            clock_anchor_session=CLOCK_ANCHOR_SESSION,
            decision_fill_lag_sessions=1,
            kappa_fallback_value=KAPPA_FALLBACK_VALUE,
            kappa_fallback_min_scored_sessions=KAPPA_FALLBACK_MIN_SCORED_SESSIONS,
            kappa_ols_trailing_sessions=KAPPA_OLS_TRAILING_SESSIONS,
            kappa_clip_low=KAPPA_CLIP_LOW,
            kappa_clip_high=KAPPA_CLIP_HIGH,
            base_cost_bps=BASE_COST_BPS,
            stress_cost_bps=STRESS_COST_BPS,
        )
        for key, (arm_id, role, sort_stat, window) in specs.items()
    }


def arm_config_digests() -> dict[str, str]:
    """sha256 config digests of the three frozen arms, keyed by arm key."""
    return {key: cfg.digest for key, cfg in sorted(build_arm_configs().items())}


__all__ = [
    "ARM_KEY_ANCHOR",
    "ARM_KEY_CONTROL",
    "ARM_KEY_NEIGHBOUR",
    "BASE_COST_BPS",
    "BENCHMARK_SYMBOL",
    "CLOCK_ANCHOR_SESSION",
    "CLOCK_SEMANTICS",
    "CLOCK_STEP_SESSIONS",
    "CONTROL_ALPHA_ABS_RATIO_LT",
    "CASH_SEMANTICS",
    "CASH_SYMBOL",
    "EARLY_FOLD1_NET_EXPOSURE_NOTE",
    "FAMILY_ID",
    "FAMILY_SCHEMA",
    "FOLDS",
    "GROSS_CAP",
    "KAPPA_CLIP_HIGH",
    "KAPPA_CLIP_LOW",
    "KAPPA_FALLBACK_MIN_SCORED_SESSIONS",
    "KAPPA_FALLBACK_VALUE",
    "KAPPA_OLS_TRAILING_SESSIONS",
    "LEG_WEIGHT",
    "LONG_ENTRY_RANK_MAX",
    "N_LONG_LEGS",
    "N_SHORT_LEGS",
    "PROPOSAL_HYPOTHESIS_ID",
    "ROLE_ANCHOR",
    "ROLE_CONTROL",
    "ROLE_NEIGHBOUR",
    "SHORT_ENTRY_RANK_MIN",
    "S0_END",
    "S0_START",
    "SECTOR_SYMBOLS",
    "SORT_SEMIVARIANCE_SHARE",
    "SORT_VARIANCE_LEVEL",
    "STATE_WINDOW_ANCHOR",
    "STATE_WINDOW_CONTROL",
    "STATE_WINDOW_NEIGHBOUR",
    "STRESS_COST_BPS",
    "TURNOVER_CEILING_TWO_WAY_PER_YEAR",
    "WARMUP_RUNWAY_START",
    "XLC_AVAILABILITY_RULE",
    "ArmConfig",
    "ArmConfigError",
    "arm_config_digests",
    "build_arm_configs",
]
