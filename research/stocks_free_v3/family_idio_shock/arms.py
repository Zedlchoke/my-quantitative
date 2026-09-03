"""The three stable frozen arm config heads A1/N1/C1 with config digests.

Each head pins the EXACT constants of ``selection_freeze.json``
families[0] ``arms`` (nothing else exists — no thresholds, lookbacks or grids
anywhere in the family).  The config digest is sha256 over the canonical JSON
of the complete frozen payload (``research.assets.common.contracts
.canonical_json``), so a trial identity can pin the exact bytes of the arm
definition.  The digests cover the ADJ-1-EXEC-CLOCK close-fill clocks.

Roles and predicted mechanism signs (recorded as static claims; this module
never scores anything):

* A1 anchor — z <= -3.0, smallest z, hold 5, 0.5 gross + 0.5 explicit CASH;
  claim: negative idio shocks revert (positive expected idio recovery over
  the hold);
* N1 neighbour — identical to A1 except hold 10 (liquidity-provision
  compensation accrues over days-to-weeks; expected same sign as A1);
* C1 causal negative control — z >= +3.0, largest z, otherwise identical to
  A1; mechanism-derived prediction: non-positive incremental alpha
  (a long book on a POSITIVE idio overshoot buys the transitory premium that
  must revert); positive control alpha comparable to A1's falsifies the
  mechanism.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Mapping

from research.assets.common.contracts import canonical_json, require_finite_float, require_token
from research.stocks_free_v3.authority import BENCHMARK_SYMBOL, SECTOR_SYMBOLS
from research.stocks_free_v3.family_idio_shock.features import (
    BETA_LOOKBACK_SESSIONS,
    RESIDUAL_DDOF,
)

FAMILY_ID = "SFV3-A5-IDIO-SHOCK-REVERSAL"

TRIGGER_NEGATIVE = "Z_LE_NEG_THRESHOLD"   # A1 / N1: z <= -3.0, select smallest z
TRIGGER_POSITIVE = "Z_GE_POS_THRESHOLD"   # C1:      z >= +3.0, select largest z

SELECTION_MIN_Z = "MIN_Z"   # smallest z wins; exact tie -> alphabetically first symbol
SELECTION_MAX_Z = "MAX_Z"   # largest z wins;  exact tie -> alphabetically first symbol

#: ADJ-1-EXEC-CLOCK (selection_freeze.json adjudications[0]): decision at the
#: close of completed session t; fills at the CLOSE of session t+1; holds are
#: close-to-close (exit fill at close of entry+hold); a trigger at close of t
#: may switch at close of t+1 when an exit also lands there (both decided at
#: earlier closes; PIT-clean).
CLOCK_DECISION = "CLOSE_OF_COMPLETED_SESSION_T"
CLOCK_FILL = "CLOSE_OF_SESSION_T_PLUS_1"
CLOCK_EXIT = "CLOSE_OF_ENTRY_PLUS_HOLD_SESSIONS"
ADJUDICATION = "ADJ-1-EXEC-CLOCK"

#: Episode-budget constants (frozen for all three arms).
BUDGET_MAX_ENTRIES = 5
BUDGET_WINDOW_SESSIONS = 252
CONCURRENCY = 1

#: The verbatim vol_scaling_rule payloads of the freeze (``target_daily_vol``
#: is null and ``min_gross == max_gross``: a CONSTANT scale equal to the
#: arm's expected average gross).  Recorded verbatim; never re-derived.
VOL_SCALING_A1_C1 = {
    "lookback_sessions": 63,
    "target_daily_vol": None,
    "min_gross": 0.025,
    "max_gross": 0.025,
}
VOL_SCALING_N1 = {
    "lookback_sessions": 63,
    "target_daily_vol": None,
    "min_gross": 0.05,
    "max_gross": 0.05,
}


@dataclass(frozen=True)
class FrozenArmConfig:
    """One frozen arm head.  Every field is a frozen constant."""

    arm_id: str
    role: str
    trigger: str
    z_threshold: float
    selection: str
    hold_sessions: int
    gross: float
    cash_weight: float
    episode_budget_max_entries: int
    episode_budget_window_sessions: int
    concurrency: int
    beta_lookback_sessions: int
    residual_ddof: int
    vol_scaling_rule: Mapping[str, object] = field(default_factory=dict)
    universe: tuple[str, ...] = SECTOR_SYMBOLS
    benchmark_symbol: str = BENCHMARK_SYMBOL

    def __post_init__(self) -> None:
        require_token(self.arm_id, "arm_id")
        require_token(self.role, "role")
        if self.trigger not in (TRIGGER_NEGATIVE, TRIGGER_POSITIVE):
            raise ValueError(f"unknown trigger {self.trigger!r}")
        require_finite_float(self.z_threshold, "z_threshold")
        if self.trigger == TRIGGER_NEGATIVE and self.z_threshold >= 0.0:
            raise ValueError("the negative-shock trigger requires a negative threshold")
        if self.trigger == TRIGGER_POSITIVE and self.z_threshold <= 0.0:
            raise ValueError("the positive-shock trigger requires a positive threshold")
        if self.selection not in (SELECTION_MIN_Z, SELECTION_MAX_Z):
            raise ValueError(f"unknown selection {self.selection!r}")
        if (self.trigger == TRIGGER_NEGATIVE) != (self.selection == SELECTION_MIN_Z):
            raise ValueError("trigger sign and selection direction must agree (frozen pairing)")
        if isinstance(self.hold_sessions, bool) or not isinstance(self.hold_sessions, int) \
                or self.hold_sessions < 1:
            raise ValueError("hold_sessions must be a positive int")
        require_finite_float(self.gross, "gross", positive=True)
        require_finite_float(self.cash_weight, "cash_weight")
        if abs(self.gross + self.cash_weight - 1.0) > 1e-12:
            raise ValueError("gross + cash_weight must equal 1.0")
        for name in ("episode_budget_max_entries", "episode_budget_window_sessions",
                     "concurrency", "beta_lookback_sessions"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive int")
        if self.residual_ddof != RESIDUAL_DDOF:
            raise ValueError(f"residual_ddof is frozen at {RESIDUAL_DDOF}")
        if self.beta_lookback_sessions != BETA_LOOKBACK_SESSIONS:
            raise ValueError(f"beta_lookback_sessions is frozen at {BETA_LOOKBACK_SESSIONS}")
        if self.benchmark_symbol in self.universe:
            raise ValueError("the benchmark symbol must not be in the trigger universe")
        rule = dict(self.vol_scaling_rule)
        if rule.get("min_gross") != rule.get("max_gross"):
            raise ValueError("the frozen constant-scale rule requires min_gross == max_gross")

    # -- selection direction helpers ----------------------------------------- #
    @property
    def selects_extreme_low(self) -> bool:
        return self.selection == SELECTION_MIN_Z

    def breaches(self, z: float) -> bool:
        """True when z breaches this arm's frozen trigger threshold."""
        if self.trigger == TRIGGER_NEGATIVE:
            return z <= self.z_threshold
        return z >= self.z_threshold

    # -- identity ------------------------------------------------------------- #
    def to_payload(self) -> dict:
        """The complete frozen config payload the digest is taken over."""
        return {
            "schema": "stocks_free_v3/family_idio_shock/arm@1",
            "family_id": FAMILY_ID,
            "arm_id": self.arm_id,
            "role": self.role,
            "universe": sorted(self.universe),
            "benchmark_symbol": self.benchmark_symbol,
            "trigger": self.trigger,
            "z_threshold": self.z_threshold,
            "selection": self.selection,
            "tie_break": "ALPHABETICALLY_FIRST_SYMBOL",
            "hold_sessions": self.hold_sessions,
            "gross": self.gross,
            "cash_weight": self.cash_weight,
            "episode_budget": {
                "max_new_entries": self.episode_budget_max_entries,
                "rolling_window_sessions": self.episode_budget_window_sessions,
                "concurrency": self.concurrency,
                "chronological": True,
            },
            "beta": {
                "estimator": "OLS_SLOPE_VS_SPY_ISSUER_TR",
                "lookback_sessions": self.beta_lookback_sessions,
                "window": "TRAILING_INCLUSIVE_OF_T",
            },
            "residual": {"ddof": self.residual_ddof},
            "clocks": {
                "decision": CLOCK_DECISION,
                "entry_fill": CLOCK_FILL,
                "exit_fill": CLOCK_EXIT,
                "same_close_switch": True,
                "adjudication": ADJUDICATION,
            },
            "vol_scaling_rule": dict(self.vol_scaling_rule),
        }

    @property
    def config_digest(self) -> str:
        """sha256 over the canonical JSON of the complete frozen payload."""
        return hashlib.sha256(canonical_json(self.to_payload()).encode("utf-8")).hexdigest()


#: A1 anchor: z <= -3.0, smallest z, hold 5, 0.5 + 0.5 explicit CASH.
ARM_A1 = FrozenArmConfig(
    arm_id=f"{FAMILY_ID}-A1",
    role="anchor",
    trigger=TRIGGER_NEGATIVE,
    z_threshold=-3.0,
    selection=SELECTION_MIN_Z,
    hold_sessions=5,
    gross=0.5,
    cash_weight=0.5,
    episode_budget_max_entries=BUDGET_MAX_ENTRIES,
    episode_budget_window_sessions=BUDGET_WINDOW_SESSIONS,
    concurrency=CONCURRENCY,
    beta_lookback_sessions=BETA_LOOKBACK_SESSIONS,
    residual_ddof=RESIDUAL_DDOF,
    vol_scaling_rule=VOL_SCALING_A1_C1,
)

#: N1 neighbour: identical to A1 except hold 10 sessions.
ARM_N1 = FrozenArmConfig(
    arm_id=f"{FAMILY_ID}-N1",
    role="neighbour",
    trigger=TRIGGER_NEGATIVE,
    z_threshold=-3.0,
    selection=SELECTION_MIN_Z,
    hold_sessions=10,
    gross=0.5,
    cash_weight=0.5,
    episode_budget_max_entries=BUDGET_MAX_ENTRIES,
    episode_budget_window_sessions=BUDGET_WINDOW_SESSIONS,
    concurrency=CONCURRENCY,
    beta_lookback_sessions=BETA_LOOKBACK_SESSIONS,
    residual_ddof=RESIDUAL_DDOF,
    vol_scaling_rule=VOL_SCALING_N1,
)

#: C1 causal negative control: z >= +3.0, largest z, otherwise identical to A1.
ARM_C1 = FrozenArmConfig(
    arm_id=f"{FAMILY_ID}-C1",
    role="causal_negative_control",
    trigger=TRIGGER_POSITIVE,
    z_threshold=3.0,
    selection=SELECTION_MAX_Z,
    hold_sessions=5,
    gross=0.5,
    cash_weight=0.5,
    episode_budget_max_entries=BUDGET_MAX_ENTRIES,
    episode_budget_window_sessions=BUDGET_WINDOW_SESSIONS,
    concurrency=CONCURRENCY,
    beta_lookback_sessions=BETA_LOOKBACK_SESSIONS,
    residual_ddof=RESIDUAL_DDOF,
    vol_scaling_rule=VOL_SCALING_A1_C1,
)

#: Static expected mechanism directions (claims, never scored here).
EXPECTED_MECHANISM_SIGN = {
    ARM_A1.arm_id: "POSITIVE_EXPECTED_IDIO_RECOVERY_OVER_HOLD",
    ARM_N1.arm_id: "POSITIVE_EXPECTED_IDIO_RECOVERY_OVER_HOLD",
    ARM_C1.arm_id: "NON_POSITIVE_EXPECTED_ALPHA_FALSIFICATION_CONTROL",
}

FROZEN_ARMS: tuple[FrozenArmConfig, ...] = (ARM_A1, ARM_N1, ARM_C1)

__all__ = [
    "ADJUDICATION",
    "ARM_A1",
    "ARM_C1",
    "ARM_N1",
    "BUDGET_MAX_ENTRIES",
    "BUDGET_WINDOW_SESSIONS",
    "CONCURRENCY",
    "CLOCK_DECISION",
    "CLOCK_EXIT",
    "CLOCK_FILL",
    "EXPECTED_MECHANISM_SIGN",
    "FAMILY_ID",
    "FROZEN_ARMS",
    "FrozenArmConfig",
    "SELECTION_MAX_Z",
    "SELECTION_MIN_Z",
    "TRIGGER_NEGATIVE",
    "TRIGGER_POSITIVE",
    "VOL_SCALING_A1_C1",
    "VOL_SCALING_N1",
]
