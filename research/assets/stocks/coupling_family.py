"""V5 family-1 implementation: SFV5-A6-H2-CROSS-SECTOR-COUPLING (A8).

Implements the preregistered family frozen in
``research/control/stocks_free_v5_run/proposals/a6_h2.json`` (selected by
``research/control/stocks_free_v5_run/selection_freeze.json``) under the
frozen conventions of
``research/control/stocks_free_v5_run/baseline_invariants.json``.

Three arms (identical surface form; ONLY the ranking key differs):

* ``SFV5-A6-H2-A``  COUPLE63-BN-L3S3-42 (anchor): rank eligible sector ETFs
  ASCENDING by the mean trailing 63-session pairwise Pearson return
  correlation with the other eligible sectors; long the 3 lowest-coupling at
  +1/6, short the 3 highest at -1/6;
* ``SFV5-A6-H2-N``  COUPLE21-BN-L3S3-42 (neighbour): identical except the
  correlation window is 21 sessions;
* ``SFV5-A6-H2-C``  NOMPRICE42-BN-L3S3 (causal negative control): identical
  surface form but the key is the nominal RAW as-traded close LEVEL at the
  decision session (long the 3 lowest-priced, short the 3 highest) — a pure
  per-share scaling artifact that shares no mathematical component with the
  coupling key (Pearson correlation is invariant to any positive rescaling of
  a sector's price path; the control key is a function of exactly that
  rescaling).

Shared construction (all arms): 42-session decision grid anchored at the S0
start 2018-04-04 (global grid, S0 offset 0); decision computed PIT at the
decision close; fill at the NEXT allowed session (never same-session);
weights held 42 sessions between decisions; book forced flat at every fold
boundary; SPY hedge leg ``w_SPY = -sum(w_i * beta_i)`` from 252-session OLS
betas of adjusted close-to-close returns on SPY, truncated to [-0.25, +0.25];
CASH absorbs the residual (``cash = 1 - net``); frozen gross cap 1.25;
eligibility is the fixed availability rule ">= 252 sessions of adjusted
history through d" (9-11 sectors; XLC joins in-sample; SPY never ranked);
anchor refinement: a pair whose Pearson is undefined (either window variance
< 1e-12) is excluded from BOTH sum and count, and a sector with fewer than 5
defined pairs is not rankable at that decision; fewer than 6 eligible sectors
at d means the decision is skipped and not scored.

Data-path discipline (frozen in the proposal ``fields_used``):

* the ADJUSTED (``_all``) close is the ONLY return/benchmark input — it feeds
  the coupling key, the betas, and any portfolio return computation;
* the RAW (``_none``) close enters ONLY the nominal-price control key and is
  structurally unreachable from the anchor/neighbour code paths.

Discipline of this module: deterministic feature/book/schedule arithmetic
over caller-supplied series.  No data access, no disk writes, no network, and
NO PnL of any kind — no return aggregation, no expectancy, no profit factor
exists anywhere below.  The master-calendar validator fails closed on any
calendar extending past the S0 screening end 2025-07-31, so no S1 session can
be addressed through this module.
"""

from __future__ import annotations

import hashlib
import math
from bisect import bisect_right
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from research.assets.common.contracts import canonical_json, require_token
from research.assets.stocks.factory import CASH_SYMBOL

# --------------------------------------------------------------------------- #
# frozen identity (proposal a6_h2.json + selection_freeze.json)
# --------------------------------------------------------------------------- #
#: Family identity as frozen in selection_freeze.json selected_families[0].
FAMILY_ID = "SFV5-A6-H2-CROSS-SECTOR-COUPLING"

#: Schema token for every payload this family emits.
FAMILY_SCHEMA = "stocks_free_v5/family_coupling@1"

#: Hypothesis id from the frozen proposal.
HYPOTHESIS_ID = "SFV5-A6-H2"

#: The 11 sector ETFs of the frozen cohort, frozen order (never reselected).
SECTOR_SYMBOLS = (
    "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY",
)

#: SPY: hedge instrument and benchmark context ONLY — never ranked, never a
#: sector leg, and its own series is never rescaled by any feature.
BENCHMARK_SYMBOL = "SPY"

# --------------------------------------------------------------------------- #
# frozen clock / windows (proposal universe_warmup_clock_holding_fills)
# --------------------------------------------------------------------------- #
#: The decision-clock anchor: the S0 start session (first decision).
ANCHOR_SESSION = "2018-04-04"

#: Sessions between decision slots ("every 42nd SPY-calendar session within
#: S0"; global grid from S0 offset 0 — A9-F measured 44 slots, 15/15/14).
CLOCK_PERIOD_SESSIONS = 42

#: Holding period; weights fixed between decision slots.
HOLDING_SESSIONS = 42

#: Eligibility/beta warmup: a sector needs >= 252 sessions of adjusted
#: history through d; the beta window is the last 252 sessions through d.
WARMUP_SESSIONS = 252

#: Return observations inside the 252-session beta window of closes
#: (close-to-close returns within the window; see implementation notes).
BETA_RETURN_OBSERVATIONS = WARMUP_SESSIONS - 1

#: Correlation windows: anchor 63 sessions of returns, neighbour 21.
CORR_WINDOW_ANCHOR = 63
CORR_WINDOW_NEIGHBOUR = 21

#: Fill clock: decision at PIT close of t fills at the next allowed session.
DECISION_LAG_SESSIONS = 1

#: S0 screening window end: NO session after this date is ever read or
#: scored; the calendar validator fails closed beyond it.
S0_END = "2025-07-31"

# --------------------------------------------------------------------------- #
# frozen book form (proposal anchor steps 3-6)
# --------------------------------------------------------------------------- #
LONG_LEGS = 3
SHORT_LEGS = 3
LEG_WEIGHT = 1.0 / 6.0

#: Hedge leg truncation band and the frozen gross cap it implies.
HEDGE_ABS_CAP = 0.25
GROSS_CAP = 1.25

#: Frozen skip rule: fewer than 6 eligible sectors at d -> decision skipped,
#: not scored (census arithmetic makes this measure-zero on the snapshot).
MIN_ELIGIBLE = 6

#: Frozen pair-definition floor: a Pearson pair is undefined when either
#: 63-session return-window variance is < 1e-12 (excluded from sum AND
#: count); a sector with fewer than 5 defined pairs is not rankable.
VARIANCE_FLOOR = 1e-12
MIN_DEFINED_PAIRS = 5

# --------------------------------------------------------------------------- #
# frozen costs / turnover (baseline_invariants.json, verbatim)
# --------------------------------------------------------------------------- #
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0
TURNOVER_CEILING_TWO_WAY_PER_YEAR = 6.0

#: Sessions per year used ONLY for the schedule-only annualized turnover
#: estimate (structural churn arithmetic; never a return statistic).
SESSIONS_PER_YEAR = 252.0

# --------------------------------------------------------------------------- #
# frozen folds (baseline_invariants.json folds, verbatim)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Fold:
    """One frozen S0 fold window (baseline_invariants.json)."""

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
# arm heads (proposal anchor / neighbour / causal_negative_control)
# --------------------------------------------------------------------------- #
ROLE_ANCHOR = "anchor"
ROLE_NEIGHBOUR = "neighbour"
ROLE_CONTROL = "causal_negative_control"

ARM_KEY_ANCHOR = "A"
ARM_KEY_NEIGHBOUR = "N"
ARM_KEY_CONTROL = "C"

#: Frozen arm ids and rule names (proposal ``name`` fields, verbatim).
ARM_IDS: dict[str, str] = {
    ARM_KEY_ANCHOR: "SFV5-A6-H2-A",
    ARM_KEY_NEIGHBOUR: "SFV5-A6-H2-N",
    ARM_KEY_CONTROL: "SFV5-A6-H2-C",
}
ARM_RULE_NAMES: dict[str, str] = {
    ARM_KEY_ANCHOR: "COUPLE63-BN-L3S3-42",
    ARM_KEY_NEIGHBOUR: "COUPLE21-BN-L3S3-42",
    ARM_KEY_CONTROL: "NOMPRICE42-BN-L3S3",
}
ARM_ROLES: dict[str, str] = {
    ARM_KEY_ANCHOR: ROLE_ANCHOR,
    ARM_KEY_NEIGHBOUR: ROLE_NEIGHBOUR,
    ARM_KEY_CONTROL: ROLE_CONTROL,
}

#: Ranking-key kinds.  COUPLE keys read the ADJUSTED return panel only;
#: NOMPRICE reads the RAW close level only.  The hedge beta map is adjusted
#: returns for every arm including the control ("same 252-session beta
#: hedge", proposal causal_negative_control).
KEY_COUPLE = "COUPLE"
KEY_NOMPRICE = "NOMPRICE"

#: Ranking direction, verbatim semantics: ASCENDING by the key (anchor step
#: 3: long the 3 LOWEST, short the 3 HIGHEST); ties break ticker A-Z.
RANK_DIRECTION = "KEY_ASCENDING_TIE_TICKER_ALPHABETICAL_ASC"

#: Frozen data-path declarations (proposal fields_used, verbatim semantics).
ADJUSTED_SOURCE = (
    "{SYM}_all_p1.json close (split+dividend adjusted): the ONLY return/"
    "benchmark input — coupling key, betas, and portfolio returns"
)
RAW_SOURCE = (
    "{SYM}_none_p1.json close (raw as-traded): nominal-price PLACEBO CONTROL "
    "key ONLY; never used for returns, for the anchor key, or for the "
    "neighbour"
)
BENCHMARK_SOURCE = (
    "SPY_all_p1.json close (adjusted): hedge-instrument beta and the "
    "risk-matched SPY benchmark context; SPY never ranked"
)
RISK_MATCH_DECLARATION = (
    "ZERO SPY-context multiple declared ex ante: the construction zeroes net "
    "SPY beta by rule via the hedge leg; realized arm volatility or realized "
    "beta is never substituted post hoc"
)

CASH_SEMANTICS = "EXPLICIT_RESIDUAL_LEG_NEVER_TRADABLE"
FILL_SEMANTICS = "DECISION_PIT_CLOSE_T_FILLS_NEXT_ALLOWED_SESSION_NO_SAME_SESSION_FILL"
CLOCK_SEMANTICS = "GLOBAL_42_SESSION_GRID_FROM_S0_OFFSET_0_ANCHORED_AT_2018_04_04"


class FamilyError(ValueError):
    """Raised when a call violates the frozen family contract."""


class ArmConfigError(ValueError):
    """Raised when an arm head does not match the frozen proposal."""


@dataclass(frozen=True)
class ArmConfig:
    """One frozen arm head: complete, digest-pinned, immutable.

    Every field that can influence a scored run appears in
    :meth:`to_payload`; the sha256 :attr:`digest` pins the arm exactly.
    """

    arm_key: str
    arm_id: str
    role: str
    rule_name: str
    key_kind: str
    corr_window_sessions: int | None  # None for the nominal-price control

    def __post_init__(self) -> None:
        require_token(self.arm_key, "arm_key")
        require_token(self.arm_id, "arm_id")
        require_token(self.role, "role")
        require_token(self.rule_name, "rule_name")
        if ARM_IDS.get(self.arm_key) != self.arm_id or \
                ARM_ROLES.get(self.arm_key) != self.role or \
                ARM_RULE_NAMES.get(self.arm_key) != self.rule_name:
            raise ArmConfigError(
                f"arm head {self.arm_id!r}/{self.role!r}/{self.rule_name!r} "
                f"does not match the frozen head for key {self.arm_key!r}"
            )
        if self.key_kind not in (KEY_COUPLE, KEY_NOMPRICE):
            raise ArmConfigError(f"unknown key kind {self.key_kind!r}")
        if self.key_kind == KEY_COUPLE:
            if self.corr_window_sessions not in (CORR_WINDOW_ANCHOR,
                                                 CORR_WINDOW_NEIGHBOUR):
                raise ArmConfigError(
                    "coupling window is frozen at "
                    f"{CORR_WINDOW_ANCHOR} (anchor) or "
                    f"{CORR_WINDOW_NEIGHBOUR} (neighbour); got "
                    f"{self.corr_window_sessions!r}"
                )
            expected = (CORR_WINDOW_ANCHOR if self.arm_key == ARM_KEY_ANCHOR
                        else CORR_WINDOW_NEIGHBOUR)
            if self.corr_window_sessions != expected:
                raise ArmConfigError(
                    f"arm {self.arm_key!r} must carry the "
                    f"{expected}-session window"
                )
        elif self.corr_window_sessions is not None:
            raise ArmConfigError(
                "the nominal-price control carries no correlation window"
            )
        if (self.role == ROLE_CONTROL) != (self.key_kind == KEY_NOMPRICE):
            raise ArmConfigError(
                "only the causal negative control may rank the nominal price"
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": FAMILY_SCHEMA,
            "family_id": FAMILY_ID,
            "hypothesis_id": HYPOTHESIS_ID,
            "arm_id": self.arm_id,
            "arm_key": self.arm_key,
            "role": self.role,
            "rule_name": self.rule_name,
            "key": {
                "kind": self.key_kind,
                "corr_window_sessions": self.corr_window_sessions,
                "rank_direction": RANK_DIRECTION,
                "adjusted_source": ADJUSTED_SOURCE,
                "raw_source": RAW_SOURCE if self.key_kind == KEY_NOMPRICE
                else "RAW PATH UNREAD BY THIS ARM (structural)",
            },
            "universe": {
                "symbols": list(SECTOR_SYMBOLS),
                "benchmark_symbol": BENCHMARK_SYMBOL,
                "benchmark_never_ranked": True,
                "eligibility_rule": (
                    ">= 252 sessions of adjusted history through d; "
                    "anchor refinement: >= 5 defined correlation pairs "
                    "(undefined pair: either window variance < 1e-12)"
                ),
                "skip_rule": f"fewer than {MIN_ELIGIBLE} eligible at d -> "
                             "decision skipped, not scored",
            },
            "book": {
                "long_legs": LONG_LEGS,
                "short_legs": SHORT_LEGS,
                "leg_weight": LEG_WEIGHT,
                "hedge": (
                    "w_SPY = -sum(w_i * beta_i), beta = 252-session OLS of "
                    "adjusted returns on SPY adjusted returns, truncated to "
                    "[-0.25, +0.25]"
                ),
                "gross_cap": GROSS_CAP,
                "cash_semantics": CASH_SEMANTICS,
            },
            "clock": {
                "semantics": CLOCK_SEMANTICS,
                "anchor_session": ANCHOR_SESSION,
                "period_sessions": CLOCK_PERIOD_SESSIONS,
                "holding_sessions": HOLDING_SESSIONS,
                "warmup_sessions": WARMUP_SESSIONS,
                "decision_lag_sessions": DECISION_LAG_SESSIONS,
                "fill_semantics": FILL_SEMANTICS,
            },
            "risk_matched_rule": {
                "benchmark": "SPY_total_return_adjusted",
                "declaration": RISK_MATCH_DECLARATION,
            },
            "costs": {
                "base_bps_per_side": BASE_COST_BPS,
                "stress_bps_per_side": STRESS_COST_BPS,
                "charged_exactly_once_per_fill": True,
            },
            "turnover": {
                "convention": "ADJ-5: sum(abs(delta_weight)) non-CASH",
                "ceiling_two_way_per_year": TURNOVER_CEILING_TWO_WAY_PER_YEAR,
            },
        }

    @property
    def digest(self) -> str:
        """sha256 over the canonical JSON of the frozen config payload."""
        return hashlib.sha256(
            canonical_json(self.to_payload()).encode("utf-8")).hexdigest()


#: Frozen arm heads, keyed by arm key.
FROZEN_ARMS: dict[str, ArmConfig] = {
    ARM_KEY_ANCHOR: ArmConfig(
        arm_key=ARM_KEY_ANCHOR, arm_id=ARM_IDS[ARM_KEY_ANCHOR],
        role=ARM_ROLES[ARM_KEY_ANCHOR], rule_name=ARM_RULE_NAMES[ARM_KEY_ANCHOR],
        key_kind=KEY_COUPLE, corr_window_sessions=CORR_WINDOW_ANCHOR),
    ARM_KEY_NEIGHBOUR: ArmConfig(
        arm_key=ARM_KEY_NEIGHBOUR, arm_id=ARM_IDS[ARM_KEY_NEIGHBOUR],
        role=ARM_ROLES[ARM_KEY_NEIGHBOUR],
        rule_name=ARM_RULE_NAMES[ARM_KEY_NEIGHBOUR], key_kind=KEY_COUPLE,
        corr_window_sessions=CORR_WINDOW_NEIGHBOUR),
    ARM_KEY_CONTROL: ArmConfig(
        arm_key=ARM_KEY_CONTROL, arm_id=ARM_IDS[ARM_KEY_CONTROL],
        role=ARM_ROLES[ARM_KEY_CONTROL], rule_name=ARM_RULE_NAMES[ARM_KEY_CONTROL],
        key_kind=KEY_NOMPRICE, corr_window_sessions=None),
}


def build_arm_configs() -> dict[str, ArmConfig]:
    """The three frozen arm heads A/N/C, keyed by arm key (fresh copies)."""
    return dict(FROZEN_ARMS)


def arm_config_digests() -> dict[str, str]:
    """sha256 config digests of the three frozen arms, keyed by arm key."""
    return {key: arm.digest for key, arm in sorted(FROZEN_ARMS.items())}


# --------------------------------------------------------------------------- #
# master calendar (fail-closed, S0-bounded)
# --------------------------------------------------------------------------- #
def validate_master_dates(dates: Sequence[str]) -> tuple[str, ...]:
    """Fail-closed calendar validation; returns the tuple form.

    Sorted ascending, unique, ISO session strings, and — the S1 guard —
    never extending past the S0 screening end (no session after 2025-07-31
    can be addressed through this module).
    """
    if not dates:
        raise FamilyError("master calendar must be non-empty")
    if list(dates) != sorted(set(dates)):
        raise FamilyError("master calendar must be sorted ascending and unique")
    for d in dates:
        if not isinstance(d, str) or len(d) != 10 or d[4] != "-" or d[7] != "-":
            raise FamilyError(f"non-ISO session string {d!r}")
    if dates[-1] > S0_END:
        raise FamilyError(
            f"master calendar extends past the S0 screening end {S0_END!r} "
            f"(last session {dates[-1]!r}); S1 data must never be read"
        )
    return tuple(dates)


def anchor_index(dates: Sequence[str],
                 anchor_session: str = ANCHOR_SESSION) -> int:
    """Index of the frozen clock anchor session (fail-closed if absent)."""
    try:
        return list(dates).index(anchor_session)
    except ValueError as exc:
        raise FamilyError(
            f"clock anchor session {anchor_session!r} not on the master "
            "calendar") from exc


def fold_of(session: str, folds: Sequence[Fold] = FOLDS) -> str | None:
    """The fold containing ``session`` (None = fold gap; ISO compare)."""
    for fold in folds:
        if fold.start <= session <= fold.end:
            return fold.fold_id
    return None


# --------------------------------------------------------------------------- #
# schedule (dates + counts ONLY — no feature values, no PnL)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DecisionSlot:
    """One 42-grid decision slot with its fold assignment and fill."""

    k: int                    # clock tick number (anchor tick is k=0)
    session: str              # decision session (PIT close)
    index: int                # index in the master calendar
    fold_id: str | None       # containing fold (None = voided, in a fold gap)
    fill_session: str | None  # next allowed session (None only when voided)

    def to_payload(self) -> dict[str, Any]:
        return {"k": self.k, "session": self.session, "index": self.index,
                "fold_id": self.fold_id, "fill_session": self.fill_session}


@dataclass(frozen=True)
class ForceFlat:
    """One fold-boundary force-flat fill (at the fold end session)."""

    fold_id: str
    session: str

    def to_payload(self) -> dict[str, Any]:
        return {"fold_id": self.fold_id, "session": self.session}


@dataclass(frozen=True)
class ArmSchedule:
    """One arm's deterministic 42-grid schedule (dates + counts only)."""

    arm_id: str
    arm_key: str
    rule_name: str
    role: str
    config_digest: str
    decisions: tuple[DecisionSlot, ...]
    voided: tuple[DecisionSlot, ...]
    force_flats: tuple[ForceFlat, ...]
    master_sessions_total: int
    master_first: str
    master_last: str
    anchor_index_value: int

    @property
    def decided(self) -> tuple[DecisionSlot, ...]:
        """Decision slots inside folds (never voided), frozen order."""
        return tuple(d for d in self.decisions if d.fold_id is not None)

    def decisions_in_fold(self, fold_id: str) -> tuple[DecisionSlot, ...]:
        return tuple(d for d in self.decided if d.fold_id == fold_id)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": FAMILY_SCHEMA,
            "family_id": FAMILY_ID,
            "hypothesis_id": HYPOTHESIS_ID,
            "arm_id": self.arm_id,
            "arm_key": self.arm_key,
            "rule_name": self.rule_name,
            "role": self.role,
            "config_digest": self.config_digest,
            "clock": {
                "semantics": CLOCK_SEMANTICS,
                "anchor_session": ANCHOR_SESSION,
                "period_sessions": CLOCK_PERIOD_SESSIONS,
                "anchor_index": self.anchor_index_value,
                "decision_lag_sessions": DECISION_LAG_SESSIONS,
                "master_sessions_total": self.master_sessions_total,
                "master_first": self.master_first,
                "master_last": self.master_last,
            },
            "decisions": [d.to_payload() for d in self.decisions],
            "voided_ticks": [v.to_payload() for v in self.voided],
            "force_flats": [f.to_payload() for f in self.force_flats],
            "counts": {
                "decisions": len(self.decided),
                "voided": len(self.voided),
                "force_flats": len(self.force_flats),
            },
        }

    def canonical_json(self) -> str:
        """Byte-stable canonical JSON of the whole schedule."""
        return canonical_json(self.to_payload())

    @property
    def schedule_digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def clock_slots(dates: Sequence[str],
                anchor_session: str = ANCHOR_SESSION,
                period: int = CLOCK_PERIOD_SESSIONS,
                folds: Sequence[Fold] = FOLDS) -> tuple[DecisionSlot, ...]:
    """All 42-grid ticks through the last fold end (filled or voided).

    Tick ``k`` sits at master index ``anchor_index + period*k`` (global grid
    from S0 offset 0).  A tick whose session falls in a fold gap is VOIDED
    and recorded — per the frozen sample-size discipline a voided slot is
    never re-timed.  A tick with no next master session cannot fill and is
    refused (fail-closed) rather than silently dropped.
    """
    dates_t = validate_master_dates(dates)
    a = anchor_index(dates_t, anchor_session)
    last_fold_end = folds[-1].end
    slots: list[DecisionSlot] = []
    k = 0
    while True:
        i = a + period * k
        if i >= len(dates_t) or dates_t[i] > last_fold_end:
            break
        session = dates_t[i]
        fill = dates_t[i + 1] if i + 1 < len(dates_t) else None
        if fill is None:
            raise FamilyError(
                f"clock tick k={k} at {session!r} has no next allowed "
                "session on the master calendar; refusing to re-time"
            )
        slots.append(DecisionSlot(k=k, session=session, index=i,
                                  fold_id=fold_of(session, folds),
                                  fill_session=fill))
        k += 1
    if not slots:
        raise FamilyError("no clock ticks before the last fold end")
    return tuple(slots)


def force_flats(dates: Sequence[str],
                folds: Sequence[Fold] = FOLDS) -> tuple[ForceFlat, ...]:
    """Force-flat fill at every fold end session (fail-closed if absent)."""
    dates_t = validate_master_dates(dates)
    out = []
    for fold in folds:
        if fold.end not in dates_t:
            raise FamilyError(
                f"fold {fold.fold_id} end {fold.end!r} is not a master "
                "session; the force-flat boundary cannot be placed"
            )
        out.append(ForceFlat(fold.fold_id, fold.end))
    return tuple(out)


def _assemble(arm: ArmConfig, dates: Sequence[str],
              slots: Sequence[DecisionSlot],
              flats: Sequence[ForceFlat],
              folds: Sequence[Fold] = FOLDS) -> ArmSchedule:
    """Shared validation + payload assembly for both generation paths."""
    dates_t = validate_master_dates(dates)
    if len(slots) != len(set((s.k, s.session) for s in slots)):
        raise FamilyError("duplicate clock ticks in slot list")
    decided = tuple(s for s in slots if s.fold_id is not None)
    voided = tuple(s for s in slots if s.fold_id is None)
    flat_sessions = {f.session for f in flats}
    fold_spans = {f.fold_id: (f.start, f.end) for f in folds}
    for s in decided:
        start, end = fold_spans[s.fold_id]
        if not (start <= s.session <= end):
            raise FamilyError(
                f"decision {s.session!r} assigned to {s.fold_id} outside span")
        if not (start <= s.fill_session <= end):
            raise FamilyError(
                f"decision {s.session!r} fill {s.fill_session!r} escapes fold "
                f"{s.fold_id} span [{start}, {end}] (force-flat discipline)")
        if s.fill_session == s.session:
            raise FamilyError(f"same-session fill at {s.session!r}")
        if s.fill_session in flat_sessions:
            raise FamilyError(
                f"decision fill {s.fill_session!r} collides with a fold-end "
                "force-flat")
    for flat in flats:
        fold_fills = [s.fill_session for s in decided
                      if s.fold_id == flat.fold_id]
        if any(f >= flat.session for f in fold_fills):
            raise FamilyError(
                f"force-flat {flat.session!r} not after all "
                f"{flat.fold_id} fills")
    return ArmSchedule(
        arm_id=arm.arm_id, arm_key=arm.arm_key, rule_name=arm.rule_name,
        role=arm.role, config_digest=arm.digest,
        decisions=tuple(slots), voided=voided, force_flats=tuple(flats),
        master_sessions_total=len(dates_t), master_first=dates_t[0],
        master_last=dates_t[-1], anchor_index_value=anchor_index(dates_t))


def build_arm_schedule_walk(arm: ArmConfig, dates: Sequence[str],
                            folds: Sequence[Fold] = FOLDS) -> ArmSchedule:
    """Path 1 — sequential clock walk appending ticks, then fold flats."""
    validate_master_dates(dates)
    return _assemble(arm, dates, clock_slots(dates, folds=folds),
                     force_flats(dates, folds), folds)


def build_arm_schedule_blockwise(arm: ArmConfig, dates: Sequence[str],
                                 folds: Sequence[Fold] = FOLDS) -> ArmSchedule:
    """Path 2 — fold blocks first, then merge (must equal path 1 byte-exact).

    Groups the ticks per fold in frozen FOLDS order, re-inserts the voided
    ticks at their clock position (k order), and merges the force-flats;
    the assembled schedule MUST be canonical-JSON-identical to
    :func:`build_arm_schedule_walk` (pinned — including calendars where a
    tick lands in a fold gap).
    """
    validate_master_dates(dates)
    slots = clock_slots(dates, folds=folds)
    flats = force_flats(dates, folds)
    by_fold: dict[str, list[DecisionSlot]] = {f.fold_id: [] for f in folds}
    ordered: list[DecisionSlot] = []
    voided: list[DecisionSlot] = []
    for s in slots:
        if s.fold_id is None:
            voided.append(s)
        else:
            by_fold[s.fold_id].append(s)
    for fold in folds:  # frozen fold order == k order on the global grid
        ordered.extend(by_fold[fold.fold_id])
    # both lists are k-ascending: a k-merge restores the walk order exactly
    merged = sorted(ordered + voided, key=lambda s: s.k)
    return _assemble(arm, dates, merged, flats, folds)


def schedules_equal(a: ArmSchedule, b: ArmSchedule) -> bool:
    """Byte-level equality of two schedules' canonical JSON payloads."""
    return a.canonical_json() == b.canonical_json()


# --------------------------------------------------------------------------- #
# feature primitives (adjusted path ONLY for returns; raw ONLY for control)
# --------------------------------------------------------------------------- #
def align_close_series(close: Mapping[str, float],
                       dates: Sequence[str]) -> list[float | None]:
    """Align a ``{iso_date: close}`` map onto the master calendar.

    ``None`` marks a master session the symbol has no close for (XLC before
    its 2018-06-19 inception).  Fails closed on non-finite closes.
    """
    out: list[float | None] = []
    for d in dates:
        c = close.get(d)
        if c is not None and not math.isfinite(c):
            raise FamilyError(f"non-finite close at {d!r}")
        out.append(c)
    return out


def return_series(closes: Sequence[float | None]) -> list[float | None]:
    """Close-to-close returns of an aligned close series.

    ``r[i] = c[i] / c[i-1] - 1`` when both closes exist; ``None`` otherwise
    (series start or missing session).  The input MUST be the ADJUSTED
    (``_all``) close — split+dividend adjusted closes make the ratio the
    holding-period total return by construction.  The raw path is
    structurally unreachable from here: this function takes one series and
    no second source exists in the signature.
    """
    out: list[float | None] = [None] * len(closes)
    prev: float | None = None
    for i, c in enumerate(closes):
        if c is not None and prev is not None and prev != 0.0:
            out[i] = c / prev - 1.0
        if c is not None:
            prev = c
    return out


def window_returns(returns: Sequence[float | None], t: int,
                   n_returns: int) -> list[float]:
    """The ``n_returns`` completed returns ending at index ``t``.

    Returns indices ``[t - n_returns + 1, t]`` (closed window, PIT-complete:
    the deepest read is strictly in the past).  Fail-closed when the window
    reaches before the series start or any observation inside is missing.
    """
    if n_returns <= 0:
        raise FamilyError(f"window length must be positive, got {n_returns!r}")
    if t < 0 or t >= len(returns):
        raise FamilyError(f"decision index {t} outside series of len {len(returns)}")
    lo = t - n_returns + 1
    if lo < 0:
        raise FamilyError(
            f"return window t-{n_returns - 1}..t reaches before the series "
            f"start (index {lo} < 0): warmup incomplete at t={t}"
        )
    window = returns[lo:t + 1]
    if any(v is None for v in window):
        raise FamilyError(
            f"missing return inside window t-{n_returns - 1}..t at t={t}: "
            "warmup incomplete"
        )
    return [float(v) for v in window]


def pearson(x: Sequence[float], y: Sequence[float],
            variance_floor: float = VARIANCE_FLOOR) -> float | None:
    """Pearson correlation, or None when either variance is below the floor.

    The frozen pair rule (anchor step 2): a pair whose correlation is
    undefined (either window variance < 1e-12) is excluded from BOTH the sum
    and the count.  Location- and scale-invariant by construction (adding a
    constant to or rescaling either input never moves the value beyond float
    noise) — the mathematical walls that keep the coupling key free of
    return-level, trend, and volatility-LEVEL content.
    """
    if len(x) != len(y):
        raise FamilyError("pearson inputs must be aligned")
    n = len(x)
    if n < 2:
        return None
    mx = math.fsum(x) / n
    my = math.fsum(y) / n
    dx = [v - mx for v in x]
    dy = [v - my for v in y]
    sxy = math.fsum(a * b for a, b in zip(dx, dy))
    sxx = math.fsum(a * a for a in dx)
    syy = math.fsum(b * b for b in dy)
    if sxx < variance_floor or syy < variance_floor:
        return None
    return sxy / math.sqrt(sxx * syy)


def eligibility(dates: Sequence[str], t: int,
                presence: Mapping[str, Sequence[str] | set[str] | tuple],
                warmup: int = WARMUP_SESSIONS,
                symbols: Sequence[str] = SECTOR_SYMBOLS) -> list[str]:
    """Sector ETFs with >= ``warmup`` sessions of adjusted history through d.

    Fixed availability rule (proposal, NOT performance-based): a sector is
    eligible at decision index ``t`` iff its own session history contains at
    least ``warmup`` sessions dated <= ``dates[t]``.  ``presence[s]`` is the
    symbol's sorted session dates (dates/universe facts only — no feature
    values, no closes).  SPY is never in ``symbols``: the hedge instrument
    and benchmark context are never ranked.

    Implementation reading (recorded in the evidence file): the proposal
    prose "9 sectors eligible from S0 start (XLC and XLRE join at ~2019-06)"
    contradicts its own written rule, which the A9-F audit measured to give
    10 sectors from S0 start (all but XLC; XLRE's 252nd session precedes S0)
    and 11 from XLC's 252nd session.  The WRITTEN rule is implemented, per
    the audit's "the prose must not be implemented literally".
    """
    dates_t = validate_master_dates(dates)
    if t < 0 or t >= len(dates_t):
        raise FamilyError(f"decision index {t} outside calendar of len {len(dates_t)}")
    if BENCHMARK_SYMBOL in symbols:
        raise FamilyError("the benchmark must never be an eligible/ranked symbol")
    d = dates_t[t]
    out = []
    for s in symbols:
        have = presence.get(s)
        if not have:
            continue
        if isinstance(have, (set, frozenset)):
            count = sum(1 for x in have if x <= d)
        else:
            count = bisect_right(sorted(have), d)
        if count >= warmup:
            out.append(s)
    return out


def ols_slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    """OLS slope of ``ys`` on ``xs`` (``cov / var_x``), fail-closed when the
    x-variance is below the frozen floor (a degenerate regressor is a data
    defect, never a zero beta).  Exact for identical inputs (1.0) and for
    dyadic rescalings — pinned by the hand goldens."""
    if len(xs) != len(ys) or not xs:
        raise FamilyError("ols_slope inputs must be non-empty and aligned")
    n = len(xs)
    mx = math.fsum(xs) / n
    my = math.fsum(ys) / n
    sxx = math.fsum((x - mx) ** 2 for x in xs)
    if sxx < VARIANCE_FLOOR:
        raise FamilyError(
            f"regressor variance {sxx!r} below the floor {VARIANCE_FLOOR!r}: "
            "slope undefined")
    return math.fsum((y - my) * (x - mx)
                     for x, y in zip(xs, ys)) / sxx


def beta_map(spy_returns: Sequence[float | None],
             sector_returns: Mapping[str, Sequence[float | None]],
             t: int, symbols: Sequence[str]) -> dict[str, float]:
    """252-session OLS betas of adjusted sector returns on SPY returns.

    The beta window is the LAST ``WARMUP_SESSIONS`` master sessions through
    the decision close ``t``; the regression uses the close-to-close returns
    INSIDE that window (``BETA_RETURN_OBSERVATIONS`` observations, indices
    ``[t - BETA_RETURN_OBSERVATIONS + 1, t]``).  Implementation reading
    (recorded): "OLS ... over the last 252 sessions through d" is read as
    the 252-session close window whose interior returns feed the OLS — the
    reading consistent with the frozen "warmup <= 252 sessions" bound and
    the declared first-decision window; a 252-RETURN reading would read one
    session before that window.
    """
    xs = window_returns(spy_returns, t, BETA_RETURN_OBSERVATIONS)
    mx = math.fsum(xs) / len(xs)
    if math.fsum((x - mx) ** 2 for x in xs) < VARIANCE_FLOOR:
        raise FamilyError(
            f"SPY beta-window variance below the floor at t={t}: betas "
            "undefined, hedge not constructible")
    if BENCHMARK_SYMBOL in symbols:
        raise FamilyError("the benchmark is never a beta leg")
    return {s: ols_slope(xs, window_returns(sector_returns[s], t,
                                            BETA_RETURN_OBSERVATIONS))
            for s in symbols}


def hedge_weight(leg_weights: Mapping[str, float],
                 betas: Mapping[str, float]) -> float:
    """Hedge leg ``w_SPY = -sum(w_i * beta_i)`` truncated to [-0.25, +0.25].

    Anchor step 5, verbatim; the truncation is the declared gross-cap
    enforcement (6 legs x 1/6 + |hedge| <= 1.0 + 0.25 = the frozen 1.25).
    """
    raw = -math.fsum(float(w) * float(betas.get(s, 0.0))
                     for s, w in leg_weights.items() if s != CASH_SYMBOL)
    return max(-HEDGE_ABS_CAP, min(HEDGE_ABS_CAP, raw))


def build_targets(ranked: Sequence[str], betas: Mapping[str, float],
                  long_legs: int = LONG_LEGS, short_legs: int = SHORT_LEGS,
                  leg_weight: float = LEG_WEIGHT) -> dict[str, float]:
    """Frozen book: long-3 at +1/6, short-3 at -1/6, SPY hedge, CASH residual.

    ``ranked`` is the ASCENDING key order (anchor step 3-4: long the 3
    lowest keys, short the 3 highest).  The 6 sector legs are dollar-neutral
    by construction (sum 0); ``net = w_SPY``; ``CASH = 1 - net``.  Fail-closed
    unless at least ``MIN_ELIGIBLE`` symbols are ranked (the frozen skip
    rule) and the 3v3 baskets are disjoint.
    """
    if len(ranked) < MIN_ELIGIBLE:
        raise FamilyError(
            f"rank set {len(ranked)} below the frozen minimum "
            f"{MIN_ELIGIBLE}: decision must be SKIPPED, not scored")
    longs = list(ranked[:long_legs])
    shorts = list(ranked[len(ranked) - short_legs:])
    if len(longs) != long_legs or len(shorts) != short_legs:
        raise FamilyError("degenerate basket split")
    overlap = set(longs) & set(shorts)
    if overlap or len(set(longs)) != long_legs or len(set(shorts)) != short_legs:
        raise FamilyError(
            f"degenerate 3v3 book: longs {longs!r} shorts {shorts!r} "
            f"overlap {sorted(overlap)!r}")
    targets: dict[str, float] = {}
    for s in longs:
        targets[s] = leg_weight
    for s in shorts:
        targets[s] = -leg_weight
    w_spy = hedge_weight(targets, betas)
    targets[BENCHMARK_SYMBOL] = w_spy
    targets[CASH_SYMBOL] = 1.0 - math.fsum(targets.values())
    return targets


def rank_ascending(keys: Mapping[str, float]) -> list[str]:
    """Ascending key order; ties break ticker alphabetical ascending."""
    return sorted(keys, key=lambda s: (keys[s], s))


# --------------------------------------------------------------------------- #
# decisions (anchor / neighbour / control)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Panel:
    """Aligned input panel for one decision set.

    ``adjusted_closes``: ``{SYM: {iso_date: adjusted close}}`` from the
    ``_all`` path for the 11 sectors and SPY — the ONLY return source.
    ``raw_closes``: ``{SYM: {iso_date: raw close}}`` from the ``_none``
    path — reachable ONLY by the nominal-price control key (the anchor and
    neighbour code paths never receive it: :meth:`coupling_ranks` takes no
    raw argument).
    """

    adjusted_closes: Mapping[str, Mapping[str, float]]
    raw_closes: Mapping[str, Mapping[str, float]] | None = None

    def adjusted(self, symbol: str) -> Mapping[str, float]:
        series = self.adjusted_closes.get(symbol)
        if series is None:
            raise FamilyError(f"missing adjusted close panel for {symbol!r}")
        return series

    def raw(self, symbol: str) -> Mapping[str, float]:
        if self.raw_closes is None:
            raise FamilyError(
                "no raw panel supplied: the nominal-price control requires "
                "the raw (_none) close; the anchor/neighbour never read it")
        series = self.raw_closes.get(symbol)
        if series is None:
            raise FamilyError(f"missing raw close panel for {symbol!r}")
        return series


def coupling_ranks(panel: Panel, dates: Sequence[str], t: int,
                   corr_window: int,
                   eligible: Sequence[str],
                   ) -> tuple[dict[str, float], dict[str, int], list[str]]:
    """Mean trailing pairwise coupling per sector at decision index ``t``.

    For every eligible sector ``i``: the mean of Pearson correlations
    between the last ``corr_window`` completed adjusted returns of ``i`` and
    of each eligible peer ``j != i``; an undefined pair (either window
    variance < 1e-12) is excluded from BOTH sum and count; a sector with
    fewer than ``MIN_DEFINED_PAIRS`` defined pairs is NOT rankable at this
    decision (frozen rule, no substitution).  Returns
    ``(scores, defined_counts, ranked_ascending)`` over the rankable set.

    Scale invariance (the audit's argument): rescaling any one sector's
    price path by a positive constant rescales its returns; Pearson is
    invariant, so no transformation of price levels can move this ranking —
    the structural wall between anchor and NOMPRICE control.
    """
    if corr_window <= 0:
        raise FamilyError("correlation window must be positive")
    rets = {s: return_series(align_close_series(panel.adjusted(s), dates))
            for s in eligible}
    scores: dict[str, float] = {}
    counts: dict[str, int] = {}
    for i in eligible:
        xs = window_returns(rets[i], t, corr_window)
        pairs: list[float] = []
        for j in eligible:
            if j == i:
                continue
            ys = window_returns(rets[j], t, corr_window)
            r = pearson(xs, ys)
            if r is not None:
                pairs.append(r)
        counts[i] = len(pairs)
        if len(pairs) >= MIN_DEFINED_PAIRS:
            scores[i] = math.fsum(pairs) / len(pairs)
    ranked = rank_ascending(scores)
    return scores, counts, ranked


def nomprice_ranks(panel: Panel, dates: Sequence[str], t: int,
                   eligible: Sequence[str]) -> tuple[dict[str, float], list[str]]:
    """Nominal RAW price-level keys at ``t`` (causal negative control ONLY).

    The key is the raw as-traded close LEVEL of each eligible sector at the
    decision session — no returns, no co-movement, no volume, no variance:
    a pure per-share scaling artifact of issuer share bookkeeping.  Long
    the 3 lowest-priced, short the 3 highest-priced (same ascending order
    convention).  THIS is the only function in this module that reads the
    raw path.
    """
    d = validate_master_dates(dates)[t]
    levels = {s: float(panel.raw(s)[d]) for s in eligible}
    if any(not math.isfinite(v) or v <= 0.0 for v in levels.values()):
        raise FamilyError(f"non-finite/non-positive raw price level at {d!r}")
    return levels, rank_ascending(levels)


def decide_at(arm: ArmConfig, panel: Panel, dates: Sequence[str], t: int,
              presence: Mapping[str, Sequence[str] | set[str] | tuple],
              ) -> dict[str, Any]:
    """One full decision for ``arm`` at decision index ``t``.

    Eligibility (252-session rule) -> key -> ascending rank -> 3v3 baskets
    -> 252-session OLS SPY hedge (truncated) -> CASH residual.  A decision
    whose rankable set falls below ``MIN_ELIGIBLE`` is SKIPPED: the payload
    carries ``"scored": False`` and no targets (the book carries its prior
    weights; nothing is filled for the skipped slot).
    """
    dates_t = validate_master_dates(dates)
    eligible = eligibility(dates_t, t, presence)
    if arm.key_kind == KEY_COUPLE:
        scores, counts, ranked = coupling_ranks(
            panel, dates_t, t, arm.corr_window_sessions, eligible)
        key_payload: dict[str, Any] = {
            "coupling_scores": scores,
            "defined_pair_counts": counts,
        }
    else:
        levels, ranked = nomprice_ranks(panel, dates_t, t, eligible)
        scores, counts = levels, {s: 0 for s in eligible}
        key_payload = {"nominal_price_levels": levels}
    payload: dict[str, Any] = {
        "schema": FAMILY_SCHEMA,
        "family_id": FAMILY_ID,
        "arm_id": arm.arm_id,
        "t": t,
        "session": dates_t[t],
        "eligible": list(eligible),
        "ranked": ranked,
        "scored": len(ranked) >= MIN_ELIGIBLE,
        **key_payload,
    }
    if not payload["scored"]:
        payload["skip_reason"] = (
            f"rankable set {len(ranked)} < frozen minimum {MIN_ELIGIBLE}")
        return payload
    spy_rets = return_series(align_close_series(panel.adjusted(BENCHMARK_SYMBOL),
                                                dates_t))
    rets = {s: return_series(align_close_series(panel.adjusted(s), dates_t))
            for s in eligible}
    betas = beta_map(spy_rets, rets, t, ranked)
    targets = build_targets(ranked, betas)
    payload.update({
        "betas": betas,
        "targets": targets,
        "gross": math.fsum(abs(v) for k, v in targets.items()
                           if k != CASH_SYMBOL),
        "net": math.fsum(v for k, v in targets.items() if k != CASH_SYMBOL),
    })
    return payload


def rebuild_targets_excluding(
        arm: ArmConfig, panel: Panel, dates: Sequence[str], t: int,
        presence: Mapping[str, Sequence[str] | set[str] | tuple],
        excluded: str) -> dict[str, float]:
    """Drop-one rebuild: re-rank from scratch under the identical rule minus
    one sector (book still 3v3 + hedge; membership may change), so survival
    requires the ordering, not one leg.  Fail-closed if the excluded symbol
    is not eligible or the remaining rankable set falls below the minimum.
    """
    dates_t = validate_master_dates(dates)
    eligible = eligibility(dates_t, t, presence)
    if excluded not in eligible:
        raise FamilyError(f"drop-one refused: {excluded!r} is not eligible")
    remaining = [s for s in eligible if s != excluded]
    if arm.key_kind == KEY_COUPLE:
        _, _, ranked = coupling_ranks(panel, dates_t, t,
                                      arm.corr_window_sessions, remaining)
    else:
        _, ranked = nomprice_ranks(panel, dates_t, t, remaining)
    spy_rets = return_series(align_close_series(panel.adjusted(BENCHMARK_SYMBOL),
                                                dates_t))
    rets = {s: return_series(align_close_series(panel.adjusted(s), dates_t))
            for s in remaining}
    betas = beta_map(spy_rets, rets, t, ranked)
    return build_targets(ranked, betas)


# --------------------------------------------------------------------------- #
# books (FILL entries at slot fills + FORCE_FLAT at fold ends)
# --------------------------------------------------------------------------- #
def book_entries_walk(arm: ArmConfig, panel: Panel, dates: Sequence[str],
                      schedule: ArmSchedule,
                      presence: Mapping[str, Sequence[str] | set[str] | tuple],
                      ) -> list[dict[str, Any]]:
    """Path 1 — decisions in schedule order, then the fold force-flats.

    One FILL entry per SCORED DECIDED slot (at its next-allowed-session
    fill, targets carrying the explicit CASH residual leg); voided ticks
    (fold gaps) and skipped decisions fill nothing; a FORCE_FLAT entry at
    every fold end closes each fold (baseline force-flat rule — no
    cross-fold carry).
    """
    validate_master_dates(dates)
    entries: list[dict[str, Any]] = []
    for slot in schedule.decided:
        dec = decide_at(arm, panel, dates, slot.index, presence)
        if dec["scored"]:
            entries.append({"entry_type": "FILL",
                            "fill_date": slot.fill_session,
                            "decision_session": slot.session,
                            "targets": dict(dec["targets"])})
    entries.extend({"entry_type": "FORCE_FLAT", "fill_date": f.session,
                    "fold_id": f.fold_id}
                   for f in schedule.force_flats)
    entries.sort(key=lambda e: (e["fill_date"], 0 if e["entry_type"] == "FILL"
                                else 1))
    validate_book(entries)
    return entries


def book_entries_blockwise(arm: ArmConfig, panel: Panel, dates: Sequence[str],
                           schedule: ArmSchedule,
                           presence: Mapping[str, Sequence[str] | set[str] | tuple],
                           ) -> list[dict[str, Any]]:
    """Path 2 — per-fold blocks (fills then the fold flat), merged.

    MUST be canonical-JSON-identical to :func:`book_entries_walk` (pinned).
    """
    validate_master_dates(dates)
    entries: list[dict[str, Any]] = []
    for fold in FOLDS:
        for slot in schedule.decisions_in_fold(fold.fold_id):
            dec = decide_at(arm, panel, dates, slot.index, presence)
            if dec["scored"]:
                entries.append({"entry_type": "FILL",
                                "fill_date": slot.fill_session,
                                "decision_session": slot.session,
                                "targets": dict(dec["targets"])})
        flat = next(f for f in schedule.force_flats
                    if f.fold_id == fold.fold_id)
        entries.append({"entry_type": "FORCE_FLAT", "fill_date": flat.session,
                        "fold_id": fold.fold_id})
    entries.sort(key=lambda e: (e["fill_date"], 0 if e["entry_type"] == "FILL"
                                else 1))
    validate_book(entries)
    return entries


def validate_book(entries: Sequence[Mapping[str, Any]]) -> None:
    """Fail-closed book validation: chronology, force-flat discipline, and
    the cap/gross/net/cash invariants on every entry (no returns, no PnL).
    """
    last = ""
    for e in entries:
        d = e["fill_date"]
        if d < last:
            raise FamilyError(f"book entries out of order at {d!r}")
        last = d
        if e["entry_type"] == "FORCE_FLAT":
            continue
        targets = {s: float(w) for s, w in e["targets"].items()}
        cash = targets.pop(CASH_SYMBOL)
        if abs(math.fsum(targets.values()) + cash - 1.0) > 1e-9:
            raise FamilyError(f"weights do not reconcile to 1.0 at {d!r}")
        sector_net = math.fsum(v for s, v in targets.items()
                               if s != BENCHMARK_SYMBOL)
        if abs(sector_net) > 1e-9:
            raise FamilyError(
                f"3v3 sector book not dollar-neutral at {d!r}: {sector_net!r}")
        gross = math.fsum(abs(v) for v in targets.values())
        if gross > GROSS_CAP + 1e-9:
            raise FamilyError(
                f"gross {gross!r} exceeds the frozen cap {GROSS_CAP!r} "
                f"at {d!r}")


def book_digest(entries: Sequence[Mapping[str, Any]]) -> str:
    """sha256 over the canonical JSON of the book's structure ONLY.

    Dates and weights (sorted, canonical) — no returns, no PnL, no metric:
    the published structural fingerprint of a dry-run book.
    """
    payload = [
        {"entry_type": e["entry_type"],
         "fill_date": e["fill_date"],
         **({"targets": {s: float(w) for s, w in sorted(e["targets"].items())}}
            if "targets" in e else {}),
         **({"fold_id": e["fold_id"]} if "fold_id" in e else {})}
        for e in entries
    ]
    return hashlib.sha256(
        canonical_json({"schema": FAMILY_SCHEMA, "book": payload})
        .encode("utf-8")).hexdigest()


def dry_run_artifact(arm: ArmConfig, schedule: ArmSchedule,
                     entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Structural-only publication payload for a dry run: ZERO scored
    metrics (no PnL, no expectancy, no PF, no drawdown, no returns) —
    digests and counts a scorer cannot trade on.
    """
    fills = [e for e in entries if e["entry_type"] == "FILL"]
    return {
        "schema": FAMILY_SCHEMA,
        "kind": "DRY_RUN_STRUCTURE_ONLY",
        "family_id": FAMILY_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "arm_id": arm.arm_id,
        "rule_name": arm.rule_name,
        "role": arm.role,
        "config_digest": arm.digest,
        "schedule_digest": schedule.schedule_digest,
        "book_digest": book_digest(entries),
        "counts": {
            "decisions": len(schedule.decided),
            "fills": len(fills),
            "force_flats": len(schedule.force_flats),
        },
        "scored": False,
        "real_pnl": False,
    }


# --------------------------------------------------------------------------- #
# schedule-only feasibility + turnover estimate (dates/counts/universe ONLY)
# --------------------------------------------------------------------------- #
def membership_churn(ranked_by_slot: Sequence[Sequence[str]]) -> list[int]:
    """Legs REPLACED per consecutive basket transition (A9-F convention).

    The 6 sector legs (3 long + 3 short, order-free) per slot; one replaced
    leg = one leg out + one leg in, i.e. half the symmetric difference
    (always integral for equal-size baskets).  The first slot has no
    predecessor, so the series has n_slots - 1 transitions.
    """
    legs = [set(r[:LONG_LEGS]) | set(r[len(r) - SHORT_LEGS:])
            for r in ranked_by_slot]
    return [len(legs[i - 1] ^ legs[i]) // 2 for i in range(1, len(legs))]


def estimate_turnover(churn: Sequence[int], s0_sessions: int,
                      n_force_flats: int) -> dict[str, float]:
    """Schedule-only annualized two-way turnover estimate (NO returns).

    Components, per the frozen convention (proposal turnover_and_sample_floor
    and the A9-F measured-churn arithmetic):

    * rebalance component (measured churn): each changed leg moves
      1/6 -> 0 -> 1/6, i.e. ``churn * 2 * LEG_WEIGHT`` of ADJ-5
      |delta_weight| per transition; annualized over the S0 span
      (``s0_sessions / SESSIONS_PER_YEAR`` years, ``len(churn)``
      rebalances) — the A9-F comparable "mid";
    * hedge component upper bound: |dw_hedge| <= 2 * HEDGE_ABS_CAP per
      rebalance (full truncation-band flip — deliberately conservative; the
      realized hedge drift is far smaller because the band is [-0.25, +0.25]);
    * boundary component upper bound: per fold boundary a force-flat (1.0
      one-way) plus a rebuild (1.0 + full hedge band), ``n_force_flats``
      boundaries over the S0 span;
    * full-reconstitution bound: all 6 legs reconstituted every rebalance
      (the declared falsification surface, above the ceiling by design).

    Deterministic churn arithmetic over WEIGHTS only — never a return
    statistic, never a scored metric.
    """
    if s0_sessions <= 0:
        raise FamilyError("s0_sessions must be positive")
    if not churn:
        raise FamilyError("churn series must have at least one transition")
    years = s0_sessions / SESSIONS_PER_YEAR
    rebalances_per_year = len(churn) / years
    mean_churn = math.fsum(churn) / len(churn)
    mid = mean_churn * 2.0 * LEG_WEIGHT * rebalances_per_year
    hedge_bound = 2.0 * HEDGE_ABS_CAP * rebalances_per_year
    boundary_bound = (2.0 + 2.0 * HEDGE_ABS_CAP) * n_force_flats / years
    full_reconstitution = (2.0 * LONG_LEGS * 2.0 * LEG_WEIGHT
                           * rebalances_per_year)
    return {
        "years": years,
        "rebalances_per_year": rebalances_per_year,
        "mean_membership_churn_legs": mean_churn,
        "max_membership_churn_legs": float(max(churn)),
        "mid_two_way_per_year": mid,
        "hedge_upper_bound_two_way_per_year": hedge_bound,
        "boundary_upper_bound_two_way_per_year": boundary_bound,
        "upper_two_way_per_year": mid + hedge_bound + boundary_bound,
        "full_reconstitution_bound_two_way_per_year":
            full_reconstitution + hedge_bound + boundary_bound,
        "ceiling_two_way_per_year": TURNOVER_CEILING_TWO_WAY_PER_YEAR,
    }


def schedule_feasibility(arm: ArmConfig, schedule: ArmSchedule,
                         dates: Sequence[str],
                         presence: Mapping[str, Sequence[str] | set[str] | tuple],
                         folds: Sequence[Fold] = FOLDS) -> dict[str, Any]:
    """Schedule-only feasibility of one arm: dates/counts/universe ONLY.

    No feature values, no returns, no PnL — eligible-set SIZES are
    presence facts.  Every structural invariant is a named check.
    """
    dates_t = validate_master_dates(dates)
    decided = schedule.decided
    per_fold: dict[str, Any] = {}
    for fold in folds:
        slots = schedule.decisions_in_fold(fold.fold_id)
        per_fold[fold.fold_id] = {
            "span": [fold.start, fold.end],
            "decision_count": len(slots),
            "decision_sessions": [s.session for s in slots],
            "fill_sessions": [s.fill_session for s in slots],
            "eligible_set_sizes": [
                len(eligibility(dates_t, s.index, presence)) for s in slots],
        }
    flat_sessions = {f.session for f in schedule.force_flats}
    checks = {
        "all_decision_sessions_on_master_calendar": all(
            s.session in set(dates_t) for s in decided),
        "all_fills_next_allowed_session": all(
            dates_t[s.index + 1] == s.fill_session for s in decided),
        "no_same_session_fill": all(
            s.fill_session != s.session for s in decided),
        "all_decisions_inside_fold_spans": all(
            s.fold_id is not None for s in schedule.decisions),
        "force_flat_at_every_fold_end": all(
            ForceFlat(f.fold_id, f.end) in schedule.force_flats for f in folds),
        "no_fill_collides_with_force_flat": all(
            s.fill_session not in flat_sessions for s in decided),
        "master_calendar_s0_bounded": dates_t[-1] <= S0_END,
        "meets_fold_floor_ge_5": all(
            len(schedule.decisions_in_fold(f.fold_id)) >= 5 for f in folds),
        "meets_total_floor_ge_30": len(decided) >= 30,
        "skip_rule_never_triggered": all(
            n >= MIN_ELIGIBLE for fold_id in per_fold
            for n in per_fold[fold_id]["eligible_set_sizes"]),
        "double_generation_byte_identical": schedules_equal(
            build_arm_schedule_walk(arm, dates_t, folds),
            build_arm_schedule_blockwise(arm, dates_t, folds)),
        "benchmark_never_a_ranked_symbol": BENCHMARK_SYMBOL not in SECTOR_SYMBOLS,
    }
    return {
        "schema": FAMILY_SCHEMA,
        "feasibility": "SCHEDULE_ONLY_NO_PNL_NO_REAL_FEATURE_VALUES",
        "family_id": FAMILY_ID,
        "arm_id": arm.arm_id,
        "rule_name": arm.rule_name,
        "config_digest": arm.digest,
        "schedule_digest": schedule.schedule_digest,
        "master_calendar": {
            "sessions_total": schedule.master_sessions_total,
            "first": schedule.master_first,
            "last": schedule.master_last,
            "anchor_session": ANCHOR_SESSION,
            "anchor_index": schedule.anchor_index_value,
        },
        "decisions_total": len(decided),
        "voided_ticks": len(schedule.voided),
        "folds": per_fold,
        "force_flats": [f.to_payload() for f in schedule.force_flats],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


__all__ = [
    "ADJUSTED_SOURCE",
    "ANCHOR_SESSION",
    "ARM_IDS",
    "ARM_KEY_ANCHOR",
    "ARM_KEY_CONTROL",
    "ARM_KEY_NEIGHBOUR",
    "ARM_RULE_NAMES",
    "ARM_ROLES",
    "ArmConfig",
    "ArmConfigError",
    "BASE_COST_BPS",
    "BENCHMARK_SYMBOL",
    "BETA_RETURN_OBSERVATIONS",
    "book_digest",
    "book_entries_blockwise",
    "book_entries_walk",
    "build_arm_configs",
    "build_arm_schedule_blockwise",
    "build_arm_schedule_walk",
    "build_targets",
    "clock_slots",
    "CLOCK_PERIOD_SESSIONS",
    "CORR_WINDOW_ANCHOR",
    "CORR_WINDOW_NEIGHBOUR",
    "decide_at",
    "DecisionSlot",
    "dry_run_artifact",
    "eligibility",
    "estimate_turnover",
    "FAMILY_ID",
    "FAMILY_SCHEMA",
    "FamilyError",
    "Fold",
    "FOLDS",
    "force_flats",
    "FROZEN_ARMS",
    "GROSS_CAP",
    "HEDGE_ABS_CAP",
    "hedge_weight",
    "HOLDING_SESSIONS",
    "HYPOTHESIS_ID",
    "KEY_COUPLE",
    "KEY_NOMPRICE",
    "LEG_WEIGHT",
    "LONG_LEGS",
    "membership_churn",
    "MIN_DEFINED_PAIRS",
    "MIN_ELIGIBLE",
    "nomprice_ranks",
    "Panel",
    "pearson",
    "rank_ascending",
    "rebuild_targets_excluding",
    "return_series",
    "RISK_MATCH_DECLARATION",
    "S0_END",
    "schedule_feasibility",
    "schedules_equal",
    "SECTOR_SYMBOLS",
    "SHORT_LEGS",
    "STRESS_COST_BPS",
    "TURNOVER_CEILING_TWO_WAY_PER_YEAR",
    "VARIANCE_FLOOR",
    "WARMUP_SESSIONS",
    "ols_slope",
    "validate_book",
    "window_returns",
]
