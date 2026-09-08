"""Corporate-actions engine: splits, dividends, earnings timing (owner: A4).

Applies splits and cash dividends at the ex/effective timestamp, computes
adjustment factors under an EXPLICIT declared price-adjustment policy
(``RAW`` fill path vs ``TOTAL_RETURN`` research path — the policy is a
required constructor argument and is never implicit), reconciles the two
paths, and classifies earnings timestamps BTO/AMC with fail-closed
``UNKNOWN`` semantics, using the :mod:`research.assets.stocks.calendar`
session calendar.

Conventions (frozen here, consumed by accounting/execution lanes):

* An action is applied exactly once, at its ex/effective timestamp: the
  first moment the security trades on the post-event basis.  By default
  that is the ex-date regular-session open (09:30 ET); an explicit
  ``effective_at_utc`` must be tz-aware and fall on the ex-date
  (America/New_York), otherwise construction fails.
* Split ``split_ratio`` is shares-new per share-old (2.0 = 2:1).  At the
  effective moment raw prices divide by the ratio and share counts
  multiply by it; position market value is preserved.
* Cash dividends carry ``cash_amount`` per share (pre-adjustment dollars);
  the proportional adjustment factor for the total-return path is
  ``1 - amount / previous_close`` applied to prices strictly before the
  ex/effective moment (previous close = last raw close strictly before
  the effective moment; missing previous close fails closed).
* RAW policy: prices pass through untouched; fills always use raw prices.
  TOTAL_RETURN policy: research-path prices are back-adjusted.  Using raw
  prices for total-return signals, or adjusted prices for fills, without
  the declared transformation is exactly what this module prevents.
* Earnings timestamps: ``BTO`` before the session open of their ET date,
  ``AMC`` at/after the session close of their ET date, ``UNKNOWN``
  (fail closed, with a reason) inside the regular session or on a
  non-session ET date — a provider timestamp there is ambiguous and must
  never be silently reclassified.
* ``corporate_action_manifest_digest`` is a canonical sha256 over the
  sorted, immutable action records; input order never matters.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo

from research.assets.stocks.calendar import ET_ZONE

ACTION_SPLIT = "SPLIT"
ACTION_CASH_DIVIDEND = "CASH_DIVIDEND"
ACTION_TYPES = (ACTION_SPLIT, ACTION_CASH_DIVIDEND)

POLICY_RAW = "RAW"
POLICY_TOTAL_RETURN = "TOTAL_RETURN"
PRICE_ADJUSTMENT_POLICIES = (POLICY_RAW, POLICY_TOTAL_RETURN)

EARNINGS_BTO = "BTO"
EARNINGS_AMC = "AMC"
EARNINGS_UNKNOWN = "UNKNOWN"

_SPLIT_FILL_TOLERANCE = 1e-12


def _require_date(value: object, name: str) -> date:
    if isinstance(value, datetime):
        raise ValueError(f"{name} must be a datetime.date, not a datetime")
    if not isinstance(value, date):
        raise ValueError(f"{name} must be a datetime.date, got {type(value).__name__}")
    return value


def _require_utc(value: object, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{name} must be a tz-aware datetime")
    return value.astimezone(timezone.utc)


def _require_finite(value: object, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a real number, got {value!r}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite, got {value!r}")
    if positive and number <= 0:
        raise ValueError(f"{name} must be > 0, got {value!r}")
    return number


@dataclass(frozen=True)
class CorporateAction:
    """One immutable corporate-action record.

    Exactly one of ``split_ratio`` (``SPLIT``) / ``cash_amount``
    (``CASH_DIVIDEND``) must be set, driven by ``action_type``; anything
    else is a construction error.  ``ex_date`` is the first session day
    trading on the post-event basis; ``effective_at_utc`` defaults to the
    ex-date open via :func:`resolve_effective_at`.
    """

    security_id: str
    action_type: str
    ex_date: date
    split_ratio: float | None = None
    cash_amount: float | None = None
    effective_at_utc: datetime | None = None
    declared_date: date | None = None
    record_date: date | None = None
    payment_date: date | None = None
    action_id: str = ""
    label: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.security_id, str) or not self.security_id.strip():
            raise ValueError("security_id must be a non-empty string")
        if self.action_type not in ACTION_TYPES:
            raise ValueError(
                f"action_type must be one of {ACTION_TYPES}, got {self.action_type!r}"
            )
        object.__setattr__(self, "ex_date", _require_date(self.ex_date, "ex_date"))
        for name in ("declared_date", "record_date", "payment_date"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _require_date(value, name))
        if self.effective_at_utc is not None:
            effective = _require_utc(self.effective_at_utc, "effective_at_utc")
            object.__setattr__(self, "effective_at_utc", effective)
            if effective.astimezone(ET_ZONE).date() != self.ex_date:
                raise ValueError(
                    f"effective_at_utc ET date {effective.astimezone(ET_ZONE).date()} "
                    f"must equal ex_date {self.ex_date}"
                )
        if self.action_type == ACTION_SPLIT:
            if self.cash_amount is not None:
                raise ValueError("SPLIT must not carry cash_amount")
            ratio = _require_finite(self.split_ratio, "split_ratio", positive=True)
            if abs(ratio - 1.0) <= _SPLIT_FILL_TOLERANCE:
                raise ValueError("split_ratio of 1.0 is a no-op; reject")
            object.__setattr__(self, "split_ratio", ratio)
        else:
            if self.split_ratio is not None:
                raise ValueError("CASH_DIVIDEND must not carry split_ratio")
            amount = _require_finite(self.cash_amount, "cash_amount", positive=True)
            object.__setattr__(self, "cash_amount", amount)

    def with_effective_at(self, effective_at_utc: datetime) -> "CorporateAction":
        """Immutable copy with an explicit effective instant (same ex_date)."""
        return replace(self, effective_at_utc=effective_at_utc)

    def canonical_payload(self) -> dict[str, str]:
        """Deterministic, JSON-safe payload (dates/times as ISO strings)."""
        effective = self.effective_at_utc
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "cash_amount": repr(self.cash_amount) if self.cash_amount is not None else "",
            "declared_date": self.declared_date.isoformat() if self.declared_date else "",
            "effective_at_utc": effective.isoformat() if effective else "",
            "ex_date": self.ex_date.isoformat(),
            "label": self.label,
            "payment_date": self.payment_date.isoformat() if self.payment_date else "",
            "record_date": self.record_date.isoformat() if self.record_date else "",
            "security_id": self.security_id,
            "split_ratio": repr(self.split_ratio) if self.split_ratio is not None else "",
        }


def resolve_effective_at(action: CorporateAction, calendar) -> datetime:
    """Effective instant of ``action``: explicit value or ex-date session open."""
    if action.effective_at_utc is not None:
        return action.effective_at_utc
    session = calendar.session_bounds(action.ex_date)
    if session is None:
        raise ValueError(
            f"{action.security_id} {action.action_type} ex_date "
            f"{action.ex_date.isoformat()} is not a session day; fail closed"
        )
    return session.start_utc


def sort_actions(actions: Iterable[CorporateAction]) -> tuple[CorporateAction, ...]:
    """Deterministic record ordering: (security, ex_date, type, action_id)."""
    return tuple(
        sorted(
            actions,
            key=lambda a: (
                a.security_id,
                a.ex_date.isoformat(),
                a.action_type,
                a.action_id,
            ),
        )
    )


def corporate_action_manifest_digest(
    actions: Iterable[CorporateAction],
) -> str:
    """Canonical sha256 over sorted immutable action records.

    Input order never matters; any field change changes the digest.
    """
    records = [action.canonical_payload() for action in sort_actions(actions)]
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def require_price_adjustment_policy(policy: object) -> str:
    """Fail closed: the policy is explicit, never implicit, never defaulted."""
    if policy is None:
        raise ValueError(
            "price_adjustment_policy is required and never implicit; pass "
            f"POLICY_RAW ({POLICY_RAW}) or POLICY_TOTAL_RETURN ({POLICY_TOTAL_RETURN})"
        )
    if policy not in PRICE_ADJUSTMENT_POLICIES:
        raise ValueError(
            f"price_adjustment_policy must be one of {PRICE_ADJUSTMENT_POLICIES}, "
            f"got {policy!r}"
        )
    return policy


@dataclass(frozen=True)
class PricePoint:
    """One raw daily close (UTC instant + raw price)."""

    ts_utc: datetime
    raw_close: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "ts_utc", _require_utc(self.ts_utc, "ts_utc"))
        object.__setattr__(
            self, "raw_close", _require_finite(self.raw_close, "raw_close", positive=True)
        )


@dataclass(frozen=True)
class AdjustedPricePoint:
    ts_utc: datetime
    raw_close: float
    adjusted_close: float
    cumulative_factor: float


@dataclass(frozen=True)
class AppliedEvent:
    action: CorporateAction
    effective_at_utc: datetime
    split_ratio: float | None
    cash_amount: float | None
    shares_before: float
    shares_after: float
    reference_price_before: float
    reference_price_after: float
    cash_to_position: float


@dataclass(frozen=True)
class PositionApplication:
    security_id: str
    at_utc: datetime
    shares_before: float
    shares_after: float
    value_before: float
    value_after: float
    cash_events: tuple[AppliedEvent, ...] = field(default=())


@dataclass(frozen=True)
class ReconciliationRecord:
    ex_date: date
    security_id: str
    action_type: str
    boundary_prev_utc: datetime | None
    boundary_next_utc: datetime | None
    raw_return: float | None
    total_return: float | None
    price_factor: float | None
    dividend_yield: float | None
    explained: bool
    note: str


class CorporateActionEngine:
    """Applies actions at ex/effective timestamps under an explicit policy."""

    def __init__(
        self,
        actions: Iterable[CorporateAction] = (),
        *,
        calendar,
        price_adjustment_policy,
    ) -> None:
        require_price_adjustment_policy(price_adjustment_policy)
        if calendar is None:
            raise ValueError("calendar is required (session calendar, never defaulted)")
        self.calendar = calendar
        self.price_adjustment_policy = price_adjustment_policy
        self._actions = sort_actions(actions)
        self._by_security: dict[str, tuple[CorporateAction, ...]] = {}
        groups: dict[str, list[CorporateAction]] = {}
        for action in self._actions:
            groups.setdefault(action.security_id, []).append(action)
        for key, group in groups.items():
            self._by_security[key] = tuple(
                sorted(
                    group,
                    key=lambda a: (
                        a.ex_date.isoformat(),
                        a.action_type,
                        a.action_id,
                    ),
                )
            )
        self._manifest_digest: str | None = None

    # --- records ------------------------------------------------------------ #
    @property
    def actions(self) -> tuple[CorporateAction, ...]:
        return self._actions

    def actions_for(self, security_id: str) -> tuple[CorporateAction, ...]:
        return self._by_security.get(security_id, ())

    def effective_moment(self, action: CorporateAction) -> datetime:
        return resolve_effective_at(action, self.calendar)

    def corporate_action_manifest_digest(self, security_id: str | None = None) -> str:
        if self._manifest_digest is None:
            self._manifest_digest = corporate_action_manifest_digest(self._actions)
        if security_id is None:
            return self._manifest_digest
        return corporate_action_manifest_digest(self.actions_for(security_id))

    # --- factors ------------------------------------------------------------ #
    def events_between(
        self, security_id: str, start_utc: datetime, end_utc: datetime
    ) -> tuple[CorporateAction, ...]:
        start = _require_utc(start_utc, "start_utc")
        end = _require_utc(end_utc, "end_utc")
        return tuple(
            action
            for action in self.actions_for(security_id)
            if start < self.effective_moment(action) <= end
        )

    def share_multiplier_between(
        self, security_id: str, start_utc: datetime, end_utc: datetime
    ) -> float:
        """Share-count multiplier from ``start_utc`` to ``end_utc``."""
        multiplier = 1.0
        for action in self.events_between(security_id, start_utc, end_utc):
            if action.action_type == ACTION_SPLIT:
                assert action.split_ratio is not None
                multiplier *= action.split_ratio
        return multiplier

    def price_adjustment_factor_between(
        self, security_id: str, start_utc: datetime, end_utc: datetime
    ) -> float:
        """Raw-price multiplier from ``start_utc`` to ``end_utc`` (splits only)."""
        return 1.0 / self.share_multiplier_between(security_id, start_utc, end_utc)

    # --- application at the ex/effective timestamp --------------------------- #
    def apply_to_position(
        self,
        security_id: str,
        shares: float,
        raw_price_per_share: float,
        at_utc: datetime,
    ) -> PositionApplication:
        """Apply every action effective exactly at ``at_utc``.

        Splits multiply shares and divide the raw reference price (value
        preserved).  Cash dividends accrue ``cash_amount`` per share held
        after any same-moment split (dividends are quoted post-split at
        ex).  Nothing mutates the caller's inputs; the returned record is
        immutable.  No action at ``at_utc`` is an error (fail closed).
        """
        moment = _require_utc(at_utc, "at_utc")
        shares_f = _require_finite(shares, "shares")
        price_f = _require_finite(raw_price_per_share, "raw_price_per_share", positive=True)
        events = tuple(
            action
            for action in self.actions_for(security_id)
            if self.effective_moment(action) == moment
        )
        if not events:
            raise ValueError(
                f"no {security_id} action is effective exactly at {moment.isoformat()}; "
                "fail closed rather than guessing"
            )
        applied: list[AppliedEvent] = []
        cur_shares, cur_price = shares_f, price_f
        value_before = cur_shares * cur_price
        for action in events:  # sorted by (ex_date, type, id)
            if action.action_type == ACTION_SPLIT:
                assert action.split_ratio is not None
                new_shares = cur_shares * action.split_ratio
                new_price = cur_price / action.split_ratio
                applied.append(
                    AppliedEvent(
                        action=action,
                        effective_at_utc=moment,
                        split_ratio=action.split_ratio,
                        cash_amount=None,
                        shares_before=cur_shares,
                        shares_after=new_shares,
                        reference_price_before=cur_price,
                        reference_price_after=new_price,
                        cash_to_position=0.0,
                    )
                )
                cur_shares, cur_price = new_shares, new_price
            else:
                assert action.cash_amount is not None
                cash = cur_shares * action.cash_amount
                applied.append(
                    AppliedEvent(
                        action=action,
                        effective_at_utc=moment,
                        split_ratio=None,
                        cash_amount=action.cash_amount,
                        shares_before=cur_shares,
                        shares_after=cur_shares,
                        reference_price_before=cur_price,
                        reference_price_after=cur_price,
                        cash_to_position=cash,
                    )
                )
        return PositionApplication(
            security_id=security_id,
            at_utc=moment,
            shares_before=shares_f,
            shares_after=cur_shares,
            value_before=value_before,
            value_after=cur_shares * cur_price,
            cash_events=tuple(applied),
        )

    # --- price paths --------------------------------------------------------- #
    def price_path(
        self, security_id: str, points: Sequence[PricePoint]
    ) -> tuple[AdjustedPricePoint, ...]:
        """Research/fill price path under the declared adjustment policy.

        ``RAW`` returns raw prices untouched (the fill path).  Under
        ``TOTAL_RETURN`` prices strictly before each ex/effective moment
        are multiplied by the event factor (``1/ratio`` for splits,
        ``1 - amount/previous_close`` for dividends); the previous close
        is the last raw point strictly before the effective moment and a
        missing one fails closed.
        """
        require_price_adjustment_policy(self.price_adjustment_policy)
        ordered = tuple(sorted(points, key=lambda p: p.ts_utc))
        if self.price_adjustment_policy == POLICY_RAW:
            return tuple(
                AdjustedPricePoint(
                    ts_utc=p.ts_utc,
                    raw_close=p.raw_close,
                    adjusted_close=p.raw_close,
                    cumulative_factor=1.0,
                )
                for p in ordered
            )
        events = sorted(
            self.actions_for(security_id), key=self.effective_moment, reverse=True
        )
        factors: list[float] = [1.0] * len(ordered)
        for action in events:
            moment = self.effective_moment(action)
            if action.action_type == ACTION_SPLIT:
                assert action.split_ratio is not None
                factor = 1.0 / action.split_ratio
            else:
                assert action.cash_amount is not None
                prev = next((p for p in reversed(ordered) if p.ts_utc < moment), None)
                if prev is None:
                    raise ValueError(
                        f"total-return adjustment for {security_id} "
                        f"{action.action_type} ex {action.ex_date.isoformat()} "
                        "requires a raw close strictly before the effective "
                        "moment; fail closed"
                    )
                factor = 1.0 - action.cash_amount / prev.raw_close
            for idx, point in enumerate(ordered):
                if point.ts_utc < moment:
                    factors[idx] *= factor
        return tuple(
            AdjustedPricePoint(
                ts_utc=point.ts_utc,
                raw_close=point.raw_close,
                adjusted_close=point.raw_close * factors[idx],
                cumulative_factor=factors[idx],
            )
            for idx, point in enumerate(ordered)
        )

    # --- raw fill path vs total-return research path reconciliation ---------- #
    def reconcile_raw_vs_total_return(
        self,
        security_id: str,
        points: Sequence[PricePoint],
        *,
        tolerance: float = 1e-9,
    ) -> tuple[ReconciliationRecord, ...]:
        """One reconciliation record per action across its ex boundary.

        For the last raw point strictly before the effective moment (P)
        and the first point at/after it (C): raw return ``C/P - 1``,
        total-return return ``adjC/adjP - 1``, and the expected
        total-return return ``(1 + raw_return) * (cumC/cumP) - 1``.
        ``explained`` is true only when the boundary exists and the
        identity closes within ``tolerance``; anything else fails closed
        with a note instead of a silent pass.
        """
        try:
            path = self.price_path(security_id, points)
        except ValueError as exc:
            # The price path itself failed closed (e.g. a dividend with no
            # previous close).  Report one explicit fail-closed record per
            # action instead of raising, so nothing is silently skipped.
            return tuple(
                ReconciliationRecord(
                    ex_date=action.ex_date,
                    security_id=security_id,
                    action_type=action.action_type,
                    boundary_prev_utc=None,
                    boundary_next_utc=None,
                    raw_return=None,
                    total_return=None,
                    price_factor=None,
                    dividend_yield=None,
                    explained=False,
                    note=str(exc),
                )
                for action in self.actions_for(security_id)
            )
        records: list[ReconciliationRecord] = []
        for action in self.actions_for(security_id):
            moment = self.effective_moment(action)
            prev = next((p for p in reversed(path) if p.ts_utc < moment), None)
            nxt = next((p for p in path if p.ts_utc >= moment), None)
            if prev is None or nxt is None:
                records.append(
                    ReconciliationRecord(
                        ex_date=action.ex_date,
                        security_id=security_id,
                        action_type=action.action_type,
                        boundary_prev_utc=prev.ts_utc if prev else None,
                        boundary_next_utc=nxt.ts_utc if nxt else None,
                        raw_return=None,
                        total_return=None,
                        price_factor=None,
                        dividend_yield=None,
                        explained=False,
                        note="missing boundary point; fail closed",
                    )
                )
                continue
            factor = nxt.cumulative_factor / prev.cumulative_factor
            raw_return = nxt.raw_close / prev.raw_close - 1.0
            total_return = nxt.adjusted_close / prev.adjusted_close - 1.0
            # adjC/adjP = (rawC/rawP) * (cumC/cumP)
            expected_total = (1.0 + raw_return) * factor - 1.0
            if action.action_type == ACTION_CASH_DIVIDEND:
                assert action.cash_amount is not None
                dividend_yield = action.cash_amount / prev.raw_close
            else:
                dividend_yield = None
            explained = abs(total_return - expected_total) <= tolerance
            note = (
                "total-return identity closes within tolerance"
                if explained
                else f"identity residual {total_return - expected_total:.3e} "
                "exceeds tolerance; fail closed"
            )
            records.append(
                ReconciliationRecord(
                    ex_date=action.ex_date,
                    security_id=security_id,
                    action_type=action.action_type,
                    boundary_prev_utc=prev.ts_utc,
                    boundary_next_utc=nxt.ts_utc,
                    raw_return=raw_return,
                    total_return=total_return,
                    price_factor=factor,
                    dividend_yield=dividend_yield,
                    explained=explained,
                    note=note,
                )
            )
        return tuple(records)

    # --- earnings timing ------------------------------------------------------ #
    def classify_earnings(self, ts_utc: datetime) -> "EarningsTiming":
        return classify_earnings_timestamp(ts_utc, self.calendar)


@dataclass(frozen=True)
class EarningsTiming:
    """BTO/AMC classification or fail-closed UNKNOWN with a reason."""

    value: str
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.value not in (EARNINGS_BTO, EARNINGS_AMC, EARNINGS_UNKNOWN):
            raise ValueError(
                f"earnings timing must be one of "
                f"({EARNINGS_BTO}, {EARNINGS_AMC}, {EARNINGS_UNKNOWN}), "
                f"got {self.value!r}"
            )
        if self.value == EARNINGS_UNKNOWN:
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError("UNKNOWN earnings timing requires a non-empty reason")
        elif self.reason is not None:
            raise ValueError("classified earnings timing must not carry a reason")

    @property
    def is_classified(self) -> bool:
        return self.value != EARNINGS_UNKNOWN

    def require_classified(self) -> str:
        """Fail closed: raise when UNKNOWN, else return BTO/AMC."""
        if not self.is_classified:
            raise ValueError(f"earnings timing unclassified: {self.reason}")
        return self.value


def classify_earnings_timestamp(ts_utc: datetime, calendar) -> EarningsTiming:
    """Classify an earnings release instant against the session calendar.

    ``BTO`` strictly before the session open of its America/New_York date,
    ``AMC`` at/after that session's close, ``UNKNOWN`` (fail closed, with
    a reason) inside the regular session or on a non-session ET date.
    """
    moment = _require_utc(ts_utc, "ts_utc")
    et_day = moment.astimezone(ET_ZONE).date()
    session = calendar.session_bounds(et_day)
    if session is None:
        return EarningsTiming(
            EARNINGS_UNKNOWN,
            reason=(
                f"{moment.isoformat()} falls on non-session ET date "
                f"{et_day.isoformat()} (weekend/holiday/unscheduled closure); "
                "fail closed"
            ),
        )
    if moment < session.start_utc:
        return EarningsTiming(EARNINGS_BTO)
    if moment >= session.end_utc:
        return EarningsTiming(EARNINGS_AMC)
    return EarningsTiming(
        EARNINGS_UNKNOWN,
        reason=(
            f"{moment.isoformat()} falls inside the regular session "
            f"[{session.start_utc.isoformat()}, {session.end_utc.isoformat()}); "
            "provider timestamps there are ambiguous; fail closed"
        ),
    )


__all__ = [
    "ACTION_CASH_DIVIDEND",
    "ACTION_SPLIT",
    "ACTION_TYPES",
    "AdjustedPricePoint",
    "AppliedEvent",
    "CorporateAction",
    "CorporateActionEngine",
    "EARNINGS_AMC",
    "EARNINGS_BTO",
    "EARNINGS_UNKNOWN",
    "EarningsTiming",
    "POLICY_RAW",
    "POLICY_TOTAL_RETURN",
    "PRICE_ADJUSTMENT_POLICIES",
    "PositionApplication",
    "PricePoint",
    "ReconciliationRecord",
    "classify_earnings_timestamp",
    "corporate_action_manifest_digest",
    "require_price_adjustment_policy",
    "resolve_effective_at",
    "sort_actions",
]
