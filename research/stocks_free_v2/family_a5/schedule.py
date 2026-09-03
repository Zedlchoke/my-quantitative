"""Decision schedule engine for the A5-SFV2-TREND-DEFENSIVE family (Z5/A8).

SCHEDULE-ONLY: this module produces deterministic per-arm target books
(decision date, notional target weights, explicit cash weight, two-way
turnover vs the previous book) plus a schedule summary (decision counts per
fold, annualized two-way turnover vs the frozen 6.0x feasibility ceiling).
It NEVER computes strategy returns, PnL, profit factor or any scored metric —
scoring belongs to the Z8 lane.

Single shared code path parameterized by the frozen per-arm configs
(``ArmConfig`` / ``ARM_CONFIGS``), implementing the three preregistered arms
of ``research/proposals/stocks_free_v2/a5_family_manifest.json``:

* ARM1 anchor  ``A5-SFV2-ARM1-TSM12-VOLTARGET``: 252-session TSMOM sign gate
  (eligible iff 12m TR return > 0), MONTHLY clock.
* ARM2 neighbour ``A5-SFV2-ARM2-SMA200-WEEKLY``: 200-session SMA filter
  (eligible iff TR above its 200-session mean), WEEKLY clock.
* ARM3 control ``A5-SFV2-ARM3-TSM12-INVERTED-CONTROL``: exact sign inversion
  of the anchor (eligible iff 12m TR return < 0), MONTHLY clock; every other
  parameter identical.

Clocks and fills (spec section 5):
* MONTHLY — decision at the month's last completed regular session.
* WEEKLY  — decision at the ISO week's last completed regular session
  (ISO grouping derived from the injected frozen calendar sessions).
* Fill: NEXT regular session on RAW closes, one-event delay mandatory; the
  decision never sees the fill session.  Targets are notional-based so raw
  split halvings change share counts only, never weights.
* Ramp-in: a decision is allowed only once EVERY cohort member has enough
  completed TR sessions from coverage start through t; earlier clock events
  are suppressed to 100% cash with no trades (unscored).
* Folds: fills only on sessions <= the fold's scored_end; the book is
  FORCE-FLAT (100% cash) at each fold's scored_end close; no executions
  during the 5-session purge; each fold starts flat.

Data access is INJECTED ONLY: TR chains (raw closes x split factors +
distributions), raw closes, the session calendar and the partition folds.
No real-data IO, no network, no keys.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import date
from typing import Mapping, Sequence

try:  # package import (available after the integration merge)
    from research.stocks_free_v2.family_a5 import portfolio as _portfolio
    from research.stocks_free_v2.family_a5 import signals as _signals
except ImportError:  # flat file-path import used by the Z5 lane tests
    import portfolio as _portfolio
    import signals as _signals

# --------------------------------------------------------------------------- #
# Frozen family constants (spec/selection-freeze authority; not tuned here).  #
# --------------------------------------------------------------------------- #

FAMILY_ID = "A5-SFV2-TREND-DEFENSIVE"

#: Frozen investable cohort (a5_family_manifest.json cohort_usage; census digest
#: c9d4e88a33c53448120e79138057bcb0d100abecc1d33fbec92bd3d9c541bc96).
COHORT_SYMBOLS = ("SPY", "XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE")

#: Frozen turnover feasibility ceiling, A7 objective-O1 fix:
#: "A5_turnover_feasibility_ceiling": "6.0x two-way per year (schedule-only,
#: measured at Z6; matches declared neighbour upper bound)".
TURNOVER_CEILING_TWO_WAY_ANNUAL = 6.0

#: sha256 of each frozen spec file, recorded in a5_family_manifest.json
#: (the manifest is the digest authority; byte-exact reproduction required).
SPEC_FILE_SHA256 = {
    "a5_family_manifest.json": "d69fb046b9b148f36747ce8968b332b071420f7836fc74a830b242dec3b4a3c8",
    "a5_arm1_tsm12_ivol.json": "6c301db551c8e5faa68bb923411137c28581d5aa9816984d076e3cbf603cfc57",
    "a5_arm2_sma200_weekly.json": "8c65c0d7ea7582b70df0c216c42b202f5ca23788a06945ec2e9676837e69c4c1",
    "a5_arm3_tsm12_inverted_control.json": "5f3d93ba85241d22bde44978efa0bc98d3c5fbdb9cbee6f2d8881d313db39527",
}


@dataclass(frozen=True)
class ArmConfig:
    """One frozen arm configuration — the ONLY knobs the shared code path reads.

    Every value below is copied from the authoritative spec JSONs; nothing is
    chosen at implementation time (no grid, no tuning).
    """

    arm_id: str
    arm_role: str
    spec_filename: str
    gate: str  # "TSMOM_SIGN" (arms 1/3) or "SMA_ABOVE" (arm 2)
    lookback_sessions: int  # 252 (arms 1/3) or 200 (arm 2)
    inverted_sign: bool  # arm 3 only (exact sign inversion of the anchor)
    clock: str  # "MONTHLY" (arms 1/3) or "WEEKLY" (arm 2)
    vol_window_sessions: int = _signals.VOL_WINDOW_SESSIONS  # 63, ddof 1
    target_vol_annual: float = _portfolio.TARGET_VOL_ANNUAL  # 0.10
    per_etf_cap: float = _portfolio.PER_ETF_CAP  # 0.35
    annualization_sessions: float = _signals.ANNUALIZATION_SESSIONS  # 252.0

    def digest_payload(self) -> dict:
        """Canonical JSON-serializable form of every frozen field."""
        return {
            "schema": "stocks_free_v2/a5_arm_config@1",
            "family_id": FAMILY_ID,
            "arm_id": self.arm_id,
            "arm_role": self.arm_role,
            "spec_filename": self.spec_filename,
            "spec_file_sha256": SPEC_FILE_SHA256[self.spec_filename],
            "gate": self.gate,
            "lookback_sessions": self.lookback_sessions,
            "inverted_sign": self.inverted_sign,
            "clock": self.clock,
            "vol_window_sessions": self.vol_window_sessions,
            "target_vol_annual": self.target_vol_annual,
            "per_etf_cap": self.per_etf_cap,
            "annualization_sessions": self.annualization_sessions,
        }


#: Anchor: 252-session TSMOM sign gate, monthly clock (a5_arm1_tsm12_ivol.json).
ARM_CONFIG_ANCHOR = ArmConfig(
    arm_id="A5-SFV2-ARM1-TSM12-VOLTARGET",
    arm_role="ANCHOR_LITERATURE_BACKED",
    spec_filename="a5_arm1_tsm12_ivol.json",
    gate="TSMOM_SIGN",
    lookback_sessions=252,
    inverted_sign=False,
    clock="MONTHLY",
)

#: Neighbour: 200-session SMA filter, weekly clock (a5_arm2_sma200_weekly.json).
ARM_CONFIG_NEIGHBOUR = ArmConfig(
    arm_id="A5-SFV2-ARM2-SMA200-WEEKLY",
    arm_role="NEIGHBOUR_THEORETICALLY_JUSTIFIED",
    spec_filename="a5_arm2_sma200_weekly.json",
    gate="SMA_ABOVE",
    lookback_sessions=200,
    inverted_sign=False,
    clock="WEEKLY",
)

#: Causal negative control: exact sign inversion of the anchor, everything else
#: identical (a5_arm3_tsm12_inverted_control.json).
ARM_CONFIG_CONTROL = ArmConfig(
    arm_id="A5-SFV2-ARM3-TSM12-INVERTED-CONTROL",
    arm_role="CAUSAL_NEGATIVE_CONTROL",
    spec_filename="a5_arm3_tsm12_inverted_control.json",
    gate="TSMOM_SIGN",
    lookback_sessions=252,
    inverted_sign=True,
    clock="MONTHLY",
)

ARM_CONFIGS = {
    ARM_CONFIG_ANCHOR.arm_id: ARM_CONFIG_ANCHOR,
    ARM_CONFIG_NEIGHBOUR.arm_id: ARM_CONFIG_NEIGHBOUR,
    ARM_CONFIG_CONTROL.arm_id: ARM_CONFIG_CONTROL,
}


def arm_config_digest(config: ArmConfig) -> str:
    """Stable sha256 over the canonical JSON of the frozen arm config."""
    payload = json.dumps(config.digest_payload(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def spec_file_digest_matches(path, expected_sha256: str) -> bool:
    """Byte-exact sha256 check of a frozen spec file (read-only)."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest == expected_sha256


# --------------------------------------------------------------------------- #
# Output types (deterministic; dicts serialize with sorted keys).             #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class FoldWindow:
    """One S0 fold from the frozen partition (partition.json authority)."""

    fold_id: str
    start: date
    scored_end: date
    purge_sessions: int = 5


@dataclass(frozen=True)
class TargetBook:
    """Deterministic decision/target book for one event (schedule-only)."""

    arm_id: str
    fold_id: str
    decision_date: date
    fill_date: date  # next regular session (one-event delay); == decision_date for force-flat
    kind: str  # "DECISION" | "RAMP_CASH" | "FORCE_FLAT"
    scored: bool
    targets: Mapping[str, float]  # notional weights incl. explicit "CASH"
    cash_weight: float
    gross: float
    turnover_two_way: float  # vs previous book within the arm schedule
    eligible: tuple = ()
    arena_sigma: float = 0.0
    gross_scalar: float = 1.0

    def to_dict(self) -> dict:
        return {
            "arm_id": self.arm_id,
            "fold_id": self.fold_id,
            "decision_date": self.decision_date.isoformat(),
            "fill_date": self.fill_date.isoformat(),
            "kind": self.kind,
            "scored": self.scored,
            "targets": {k: self.targets[k] for k in sorted(self.targets)},
            "cash_weight": self.cash_weight,
            "gross": self.gross,
            "turnover_two_way": self.turnover_two_way,
            "eligible": list(self.eligible),
            "arena_sigma": self.arena_sigma,
            "gross_scalar": self.gross_scalar,
        }


@dataclass(frozen=True)
class FoldScheduleSummary:
    """Per-fold schedule summary (counts + turnover vs the frozen 6.0x ceiling)."""

    fold_id: str
    decision_events: int  # clock events with fills landing inside the fold
    scored_events: int  # decision events executed after the ramp (incl. 100%-cash states)
    suppressed_events: int  # pre-ramp 100%-cash events (unscored, no trades)
    force_flat_events: int
    total_two_way_turnover: float
    scored_window_sessions: int  # sessions in [fold.start, scored_end]
    years: float  # scored_window_sessions / 252
    turnover_per_year: float
    within_turnover_ceiling: bool  # turnover_per_year <= 6.0x two-way

    def to_dict(self) -> dict:
        return {
            "fold_id": self.fold_id,
            "decision_events": self.decision_events,
            "scored_events": self.scored_events,
            "suppressed_events": self.suppressed_events,
            "force_flat_events": self.force_flat_events,
            "total_two_way_turnover": self.total_two_way_turnover,
            "scored_window_sessions": self.scored_window_sessions,
            "years": self.years,
            "turnover_per_year": self.turnover_per_year,
            "turnover_ceiling_two_way_annual": TURNOVER_CEILING_TWO_WAY_ANNUAL,
            "within_turnover_ceiling": self.within_turnover_ceiling,
        }


@dataclass(frozen=True)
class ArmScheduleResult:
    """Full schedule-only result for one arm."""

    arm_id: str
    config_digest: str
    books: tuple = ()
    fold_summaries: tuple = ()
    total_two_way_turnover: float = 0.0

    def to_dict(self) -> dict:
        return {
            "arm_id": self.arm_id,
            "config_digest": self.config_digest,
            "total_two_way_turnover": self.total_two_way_turnover,
            "fold_summaries": [s.to_dict() for s in self.fold_summaries],
            "books": [b.to_dict() for b in self.books],
        }


# --------------------------------------------------------------------------- #
# Clocks (derived from injected frozen-calendar sessions; never guessed).     #
# --------------------------------------------------------------------------- #


def decision_dates_monthly(sessions: Sequence[date]) -> list:
    """Last completed regular session of each calendar month (MONTHLY clock)."""
    last_by_month: dict = {}
    for s in sessions:
        last_by_month[(s.year, s.month)] = s
    return [last_by_month[key] for key in sorted(last_by_month)]


def decision_dates_weekly(sessions: Sequence[date]) -> list:
    """Last completed regular session of each ISO week (WEEKLY clock)."""
    last_by_week: dict = {}
    for s in sessions:
        iso_year, iso_week, _ = s.isocalendar()
        last_by_week[(iso_year, iso_week)] = s
    return [last_by_week[key] for key in sorted(last_by_week)]


def decision_dates_for(config: ArmConfig, sessions: Sequence[date]) -> list:
    if config.clock == "MONTHLY":
        return decision_dates_monthly(sessions)
    if config.clock == "WEEKLY":
        return decision_dates_weekly(sessions)
    raise ValueError(f"unknown clock {config.clock!r}")


# --------------------------------------------------------------------------- #
# Shared schedule engine.                                                     #
# --------------------------------------------------------------------------- #


def _flat_book(cohort: Sequence[str]) -> dict:
    return {**{s: 0.0 for s in cohort}, _portfolio.CASH_SYMBOL: 1.0}


def _eligible_set(config: ArmConfig, tr_by_symbol, sessions, decision_date, cohort) -> tuple:
    """Gate evaluation on TR chains through the decision date (no lookahead)."""
    eligible = []
    for symbol in cohort:
        tr_map = tr_by_symbol[symbol]
        if config.gate == "TSMOM_SIGN":
            if _signals.tsmom_eligible(
                tr_map,
                sessions,
                symbol,
                decision_date,
                lookback_sessions=config.lookback_sessions,
                inverted_sign=config.inverted_sign,
            ):
                eligible.append(symbol)
        elif config.gate == "SMA_ABOVE":
            if config.inverted_sign:  # structural guard: no inverted SMA arm is registered
                raise ValueError("inverted sign is defined only for the TSMOM gate")
            if _signals.sma_eligible(
                tr_map,
                sessions,
                symbol,
                decision_date,
                window_sessions=config.lookback_sessions,
            ):
                eligible.append(symbol)
        else:
            raise ValueError(f"unknown gate {config.gate!r}")
    return tuple(eligible)


def generate_arm_schedule(
    config: ArmConfig,
    *,
    tr_by_symbol: Mapping[str, Mapping],
    sessions: Sequence[date],
    calendar,  # injected frozen calendar; only .next_session(after) is used
    folds: Sequence[FoldWindow],
    coverage_start: date,
) -> ArmScheduleResult:
    """Generate the deterministic schedule-only target books for one arm.

    ``tr_by_symbol`` maps each cohort symbol to its issuer-reconstructed TR
    chain (raw closes x split factors + distributions) keyed by session date.
    ``sessions`` are the partition's regular sessions (from the frozen
    calendar).  ``calendar`` resolves the one-event-delay fill session.
    """
    if sessions and min(sessions) < coverage_start:
        # partition dates are injected, never fabricated or back-extended
        raise ValueError(
            f"session {min(sessions).isoformat()} precedes coverage_start {coverage_start.isoformat()}"
        )
    cohort = sorted(tr_by_symbol)
    ramp_requirement = _signals.feature_requirement_sessions(config.gate, config.lookback_sessions)
    books: list = []
    summaries: list = []
    total_turnover = 0.0

    for fold in folds:
        previous = _flat_book(cohort)  # each fold starts flat (terminal rule)
        fold_turnover = 0.0
        fold_decision_events = 0
        fold_scored_events = 0
        fold_suppressed_events = 0

        clock_dates = [
            d
            for d in decision_dates_for(config, sessions)
            if fold.start <= d <= fold.scored_end
        ]
        for decision_date in clock_dates:
            fill_session = calendar.next_session(decision_date)
            fill_date = fill_session.start_utc.date()
            if fill_date > fold.scored_end:
                # "A decision executes fills only on sessions <= its fold's
                # scored_end."  The event cannot execute inside the fold; drop it.
                continue
            fold_decision_events += 1

            # Ramp-in: every cohort member needs the feature requirement of
            # completed TR sessions through the decision date; earlier events
            # are suppressed to 100% cash with NO trades (unscored).
            counts = {
                s: _signals.completed_session_count(tr_by_symbol[s], sessions, decision_date)
                for s in cohort
            }
            if min(counts.values()) < ramp_requirement:
                book = TargetBook(
                    arm_id=config.arm_id,
                    fold_id=fold.fold_id,
                    decision_date=decision_date,
                    fill_date=fill_date,
                    kind="RAMP_CASH",
                    scored=False,
                    targets=_flat_book(cohort),
                    cash_weight=1.0,
                    gross=0.0,
                    turnover_two_way=0.0,
                    eligible=(),
                    arena_sigma=0.0,
                    gross_scalar=1.0,
                )
                fold_suppressed_events += 1
            else:
                eligible = _eligible_set(config, tr_by_symbol, sessions, decision_date, cohort)
                sigmas = {
                    s: _signals.realized_vol_annualized(
                        [
                            tr_by_symbol[s][x]
                            for x in sessions
                            if x <= decision_date and x in tr_by_symbol[s]
                        ],
                        window_sessions=config.vol_window_sessions,
                        annualization_sessions=config.annualization_sessions,
                    )
                    for s in eligible
                }
                arena = _signals.arena_volatility(sigmas)
                scalar = _portfolio.gross_scalar(arena, config.target_vol_annual)
                weights = _portfolio.defensive_target_weights(
                    eligible, arena, config.target_vol_annual, config.per_etf_cap
                )
                for symbol in cohort:  # every cohort member carries an explicit weight
                    weights.setdefault(symbol, 0.0)
                turnover = _portfolio.two_way_turnover(previous, weights)
                book = TargetBook(
                    arm_id=config.arm_id,
                    fold_id=fold.fold_id,
                    decision_date=decision_date,
                    fill_date=fill_date,
                    kind="DECISION",
                    scored=True,
                    targets=weights,
                    cash_weight=weights[_portfolio.CASH_SYMBOL],
                    gross=_portfolio.book_gross(weights),
                    turnover_two_way=turnover,
                    eligible=eligible,
                    arena_sigma=arena,
                    gross_scalar=scalar,
                )
                previous = weights
                fold_scored_events += 1

            books.append(book)
            fold_turnover += book.turnover_two_way

        # Terminal rule: force-flat (100% cash) at the fold's scored_end close;
        # no executions during the purge; the next fold starts flat.
        flat = _flat_book(cohort)
        liquidation = _portfolio.two_way_turnover(previous, flat)
        books.append(
            TargetBook(
                arm_id=config.arm_id,
                fold_id=fold.fold_id,
                decision_date=fold.scored_end,
                fill_date=fold.scored_end,
                kind="FORCE_FLAT",
                scored=True,
                targets=flat,
                cash_weight=1.0,
                gross=0.0,
                turnover_two_way=liquidation,
                eligible=(),
                arena_sigma=0.0,
                gross_scalar=0.0,
            )
        )
        fold_turnover += liquidation

        window_sessions = sum(1 for s in sessions if fold.start <= s <= fold.scored_end)
        years = window_sessions / _signals.ANNUALIZATION_SESSIONS
        per_year = fold_turnover / years if years > 0 else 0.0
        summaries.append(
            FoldScheduleSummary(
                fold_id=fold.fold_id,
                decision_events=fold_decision_events,
                scored_events=fold_scored_events,
                suppressed_events=fold_suppressed_events,
                force_flat_events=1,
                total_two_way_turnover=fold_turnover,
                scored_window_sessions=window_sessions,
                years=years,
                turnover_per_year=per_year,
                within_turnover_ceiling=per_year <= TURNOVER_CEILING_TWO_WAY_ANNUAL,
            )
        )
        total_turnover += fold_turnover

    return ArmScheduleResult(
        arm_id=config.arm_id,
        config_digest=arm_config_digest(config),
        books=tuple(books),
        fold_summaries=tuple(summaries),
        total_two_way_turnover=total_turnover,
    )


def control_is_pure_sign_mutation(anchor: ArmConfig, control: ArmConfig) -> bool:
    """Structural check: control == anchor except arm identity and sign.

    Spec authority (a5_arm3_tsm12_inverted_control.json, control_mutation):
    "Eligibility sign INVERTED ... everything_else: IDENTICAL to the anchor".
    """
    identity = {"arm_id", "arm_role", "spec_filename", "spec_file_sha256"}
    mutated = replace(
        control,
        arm_id=anchor.arm_id,
        arm_role=anchor.arm_role,
        spec_filename=anchor.spec_filename,
        inverted_sign=anchor.inverted_sign,
    )
    same_machinery = mutated == anchor
    sign_differs = control.inverted_sign != anchor.inverted_sign
    fields_identity_only = {
        k for k in anchor.digest_payload() if anchor.digest_payload()[k] != control.digest_payload()[k]
    } <= identity | {"inverted_sign"}
    return same_machinery and sign_differs and fields_identity_only
