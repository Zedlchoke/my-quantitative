"""Point-in-time security master, universe membership and S0 floors (owner: A3).

Contracts implemented here (PLAN_stocks.md section 7 A3):

* stable ``security_id`` with an effective-dated ticker history, listing and
  delisting dates and a primary-exchange identity;
* rebalance snapshots that retain ACCEPTED **and** REJECTED rows, each with a
  mandatory reason;
* a STRUCTURAL ban on current-index-membership backfill: membership rows must
  carry effective ranges, and the membership table exposes only ``as_of``
  queries — there is no "current members" accessor to project into history;
* S0 floors as validators: >= 8 years of daily history across the common
  eligible population, >= 30 eligible liquid names per cross-sectional
  decision, delisted observations retained through their final valid event,
  and S0 ending at least 12 months before the latest complete date;
* a sealed-window helper: S0 bounds are usable, the S1 window is SEALED and
  its accessor fails closed with :class:`SealedWindowError`.
"""

from __future__ import annotations

import calendar as _calendar
from dataclasses import dataclass
from datetime import date
from typing import Callable, Mapping, Sequence

from research.assets.common.contracts import canonical_json, require_token, sha256_text

#: One day after a closed effective range (ranges are inclusive on both ends).
_UNIVERSE_SCHEMA_VERSION = 1


class UniverseError(Exception):
    """Base error for security-master/universe violations."""


class SecurityMasterError(UniverseError):
    """Invalid security master construction or lookup."""


class MembershipBackfillError(UniverseError):
    """An attempt to express or use non-effective-dated membership."""


class S0FloorViolation(UniverseError):
    """At least one S0 floor is violated (aggregated messages)."""


class SealedWindowError(UniverseError):
    """The sealed S1 window was accessed — always an error in this sprint."""


def _day_after(day: date) -> date:
    return date.fromordinal(day.toordinal() + 1)


def _add_months(day: date, months: int) -> date:
    """Shift ``day`` by ``months`` clamping to the target month end."""
    index = day.month - 1 + months
    year = day.year + index // 12
    month = index % 12 + 1
    last_day = _calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))


def _require_date(value: object, field_name: str) -> date:
    if not isinstance(value, date) or isinstance(value, type(date)):
        raise ValueError(f"{field_name} must be a datetime.date, got {value!r}")
    return value


# --- security master ---------------------------------------------------------- #
@dataclass(frozen=True)
class TickerRecord:
    """One ticker assignment over an inclusive effective range.

    ``effective_to is None`` only for the open-ended (still listed) last row.
    """

    ticker: str
    effective_from: date
    effective_to: date | None = None

    def __post_init__(self) -> None:
        require_token(self.ticker, "ticker")
        _require_date(self.effective_from, "effective_from")
        if self.effective_to is not None:
            _require_date(self.effective_to, "effective_to")
            if self.effective_to < self.effective_from:
                raise ValueError(
                    f"ticker {self.ticker!r}: effective_to precedes effective_from"
                )

    def covers(self, as_of: date) -> bool:
        if as_of < self.effective_from:
            return False
        return self.effective_to is None or as_of <= self.effective_to


@dataclass(frozen=True)
class SecurityRecord:
    """One security: stable id, listing identity, ticker history."""

    security_id: str
    primary_exchange: str
    listed_date: date
    ticker_history: tuple[TickerRecord, ...]
    delisted_date: date | None = None
    #: Final valid event (e.g. last trade date) for delisted names; observation
    #: retention is validated through this date.
    last_valid_event: date | None = None

    @property
    def is_delisted(self) -> bool:
        return self.delisted_date is not None

    @property
    def final_event_date(self) -> date:
        """Last date the security could legitimately produce observations."""
        if self.last_valid_event is not None:
            return self.last_valid_event
        if self.delisted_date is not None:
            return self.delisted_date
        raise SecurityMasterError(
            f"security {self.security_id!r} is listed; it has no final event date"
        )


class SecurityMaster:
    """Immutable point-in-time security master.

    Construction validates the whole master: unique stable ids, ticker
    histories contiguous from the listing date, ranges inside the listing
    window, and delisting consistency.  All lookups are ``as_of`` based —
    there is deliberately no "current ticker" accessor.
    """

    def __init__(self, records: Sequence[SecurityRecord]) -> None:
        if not records:
            raise SecurityMasterError("security master requires at least one record")
        by_id: dict[str, SecurityRecord] = {}
        ticker_owners: dict[str, list[tuple[date, date | None, str]]] = {}
        for record in records:
            if not isinstance(record, SecurityRecord):
                raise SecurityMasterError("records must be SecurityRecord instances")
            require_token(record.security_id, "security_id")
            require_token(record.primary_exchange, "primary_exchange")
            _require_date(record.listed_date, "listed_date")
            if record.security_id in by_id:
                raise SecurityMasterError(
                    f"duplicate security_id {record.security_id!r}: ids are stable "
                    "and unique"
                )
            if record.delisted_date is not None:
                _require_date(record.delisted_date, "delisted_date")
                if record.delisted_date < record.listed_date:
                    raise SecurityMasterError(
                        f"security {record.security_id!r}: delisted_date precedes "
                        "listed_date"
                    )
                if record.last_valid_event is not None:
                    _require_date(record.last_valid_event, "last_valid_event")
                    if record.last_valid_event > record.delisted_date:
                        raise SecurityMasterError(
                            f"security {record.security_id!r}: last_valid_event is "
                            "after delisted_date"
                        )
            elif record.last_valid_event is not None:
                raise SecurityMasterError(
                    f"security {record.security_id!r}: last_valid_event requires a "
                    "delisted_date"
                )
            if not record.ticker_history:
                raise SecurityMasterError(
                    f"security {record.security_id!r}: empty ticker_history"
                )
            ordered = sorted(record.ticker_history, key=lambda t: t.effective_from)
            if ordered[0].effective_from != record.listed_date:
                raise SecurityMasterError(
                    f"security {record.security_id!r}: first ticker range must start "
                    "on the listing date"
                )
            for previous, current in zip(ordered, ordered[1:]):
                if previous.effective_to is None:
                    raise SecurityMasterError(
                        f"security {record.security_id!r}: only the last ticker "
                        "range may be open-ended"
                    )
                if _day_after(previous.effective_to) != current.effective_from:
                    raise SecurityMasterError(
                        f"security {record.security_id!r}: ticker history is not "
                        f"contiguous at {current.ticker!r}"
                    )
            if record.delisted_date is not None:
                if ordered[-1].effective_to is None:
                    raise SecurityMasterError(
                        f"security {record.security_id!r}: a delisted security must "
                        "close its last ticker range"
                    )
                if ordered[-1].effective_to != record.delisted_date:
                    raise SecurityMasterError(
                        f"security {record.security_id!r}: last ticker range must "
                        "end on the delisting date"
                    )
            else:
                if ordered[-1].effective_to is not None:
                    raise SecurityMasterError(
                        f"security {record.security_id!r}: a listed security must "
                        "end with an open-ended ticker range"
                    )
            for ticker_record in ordered:
                ticker_owners.setdefault(ticker_record.ticker, []).append(
                    (ticker_record.effective_from, ticker_record.effective_to,
                     record.security_id)
                )
            by_id[record.security_id] = SecurityRecord(
                security_id=record.security_id,
                primary_exchange=record.primary_exchange,
                listed_date=record.listed_date,
                ticker_history=tuple(ordered),
                delisted_date=record.delisted_date,
                last_valid_event=record.last_valid_event,
            )
        for ticker, owners in ticker_owners.items():
            ordered_owners = sorted(owners, key=lambda o: o[0])
            for left, right in zip(ordered_owners, ordered_owners[1:]):
                left_end = left[1]
                if left_end is None or right[0] <= left_end:
                    raise SecurityMasterError(
                        f"ticker {ticker!r} is assigned to overlapping securities "
                        f"{left[2]!r} and {right[2]!r}"
                    )
        self._by_id = by_id

    def security_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_id))

    def get(self, security_id: str) -> SecurityRecord:
        try:
            return self._by_id[security_id]
        except KeyError as exc:
            raise SecurityMasterError(f"unknown security_id {security_id!r}") from exc

    def __len__(self) -> int:
        return len(self._by_id)

    def ticker_as_of(self, security_id: str, as_of: date) -> str | None:
        """Ticker effective on ``as_of`` (point-in-time; None when not yet listed)."""
        _require_date(as_of, "as_of")
        record = self.get(security_id)
        for ticker_record in record.ticker_history:
            if ticker_record.covers(as_of):
                return ticker_record.ticker
        return None

    def resolve_security_id(self, ticker: str, as_of: date) -> str | None:
        """Point-in-time ticker -> security id (None when not effective)."""
        _require_date(as_of, "as_of")
        matches = []
        for security_id in self.security_ids():
            for ticker_record in self.get(security_id).ticker_history:
                if ticker_record.ticker == ticker and ticker_record.covers(as_of):
                    matches.append(security_id)
        if not matches:
            return None
        if len(matches) > 1:
            raise SecurityMasterError(
                f"ticker {ticker!r} resolves ambiguously on {as_of}: {matches}"
            )
        return matches[0]

    def members_as_of(self, as_of: date) -> tuple[str, ...]:
        """Security ids listed on ``as_of`` and not yet delisted (PIT)."""
        _require_date(as_of, "as_of")
        members = []
        for security_id in self.security_ids():
            record = self._by_id[security_id]
            if record.listed_date > as_of:
                continue
            if record.delisted_date is not None and record.delisted_date < as_of:
                continue
            members.append(security_id)
        return tuple(members)


# --- effective-dated universe membership (no backfill, structurally) ---------- #
@dataclass(frozen=True)
class MembershipRecord:
    """Effective-dated membership of one security in one universe.

    ``effective_from`` is mandatory: a membership row WITHOUT effective dating
    cannot even be constructed, which is the structural ban on
    current-index-membership backfill.
    """

    security_id: str
    universe_id: str
    effective_from: date
    effective_to: date | None = None

    def __post_init__(self) -> None:
        require_token(self.security_id, "security_id")
        require_token(self.universe_id, "universe_id")
        _require_date(self.effective_from, "effective_from")
        if self.effective_to is not None:
            _require_date(self.effective_to, "effective_to")
            if self.effective_to < self.effective_from:
                raise MembershipBackfillError(
                    f"membership {self.security_id!r}/{self.universe_id!r}: "
                    "effective_to precedes effective_from"
                )

    def covers(self, as_of: date) -> bool:
        if as_of < self.effective_from:
            return False
        return self.effective_to is None or as_of <= self.effective_to


class MembershipTable:
    """Effective-dated membership rows with as-of queries ONLY.

    There is deliberately NO ``members()`` / ``current_members()`` accessor:
    "who is in the index today" must never be projected backwards into
    history.  The table's sole read API is :meth:`members_as_of`.
    """

    def __init__(self, records: Sequence[MembershipRecord]) -> None:
        ordered = sorted(records, key=lambda r: (r.universe_id, r.security_id, r.effective_from))
        seen: set[tuple[str, str]] = set()
        for record in ordered:
            if not isinstance(record, MembershipRecord):
                raise MembershipBackfillError(
                    "membership rows must be MembershipRecord instances"
                )
            key = (record.universe_id, record.security_id)
            if key in seen and record.effective_to is None:
                raise MembershipBackfillError(
                    f"overlapping open-ended membership rows for {key}"
                )
            seen.add(key)
        for left, right in zip(ordered, ordered[1:]):
            if (
                left.universe_id == right.universe_id
                and left.security_id == right.security_id
                and left.effective_to is not None
                and right.effective_from <= left.effective_to
            ):
                raise MembershipBackfillError(
                    f"overlapping membership ranges for {left.security_id!r} in "
                    f"{left.universe_id!r}"
                )
        self._records = tuple(ordered)

    def members_as_of(self, as_of: date, *, universe_id: str | None = None) -> tuple[str, ...]:
        """Members effective on ``as_of`` (optionally scoped to one universe)."""
        _require_date(as_of, "as_of")
        members = []
        for record in self._records:
            if universe_id is not None and record.universe_id != universe_id:
                continue
            if record.covers(as_of):
                members.append(record.security_id)
        return tuple(sorted(set(members)))


# --- rebalance snapshots -------------------------------------------------------- #
ACCEPTED = "ACCEPTED"
REJECTED = "REJECTED"


@dataclass(frozen=True)
class EligibilityInput:
    """Per-security facts a rule may inspect for one rebalance decision."""

    security_id: str
    ticker: str
    decision_date: date
    history_days: int
    median_dollar_volume: float
    last_obs: date


EligibilityRule = Callable[[EligibilityInput], tuple[bool, str]]


@dataclass(frozen=True)
class UniverseRow:
    """One decision row; ACCEPTED and REJECTED rows are both retained."""

    security_id: str
    ticker: str
    decision_date: date
    status: str
    reason: str
    history_days: int | None = None
    median_dollar_volume: float | None = None
    last_obs: date | None = None

    def __post_init__(self) -> None:
        require_token(self.security_id, "security_id")
        require_token(self.ticker, "ticker")
        _require_date(self.decision_date, "decision_date")
        if self.status not in (ACCEPTED, REJECTED):
            raise UniverseError(f"status must be ACCEPTED or REJECTED, got {self.status!r}")
        if not isinstance(self.reason, str) or not self.reason.strip():
            # A reason is mandatory for BOTH outcomes: rejections must be
            # explainable and acceptances must cite the rule that admitted them.
            raise UniverseError(
                f"row {self.security_id!r}: a non-empty reason is required for "
                f"{self.status} rows"
            )


@dataclass(frozen=True)
class UniverseSnapshot:
    """One rebalance snapshot (immutable, digest-able)."""

    universe_id: str
    decision_date: date
    rows: tuple[UniverseRow, ...]

    def __post_init__(self) -> None:
        require_token(self.universe_id, "universe_id")
        _require_date(self.decision_date, "decision_date")
        if not self.rows:
            raise UniverseError("a rebalance snapshot needs at least one row")
        ids = [row.security_id for row in self.rows]
        if len(set(ids)) != len(ids):
            raise UniverseError("duplicate security_id rows in one snapshot")

    def accepted(self) -> tuple[UniverseRow, ...]:
        return tuple(row for row in self.rows if row.status == ACCEPTED)

    def rejected(self) -> tuple[UniverseRow, ...]:
        return tuple(row for row in self.rows if row.status == REJECTED)

    def status_counts(self) -> dict[str, int]:
        return {
            ACCEPTED: len(self.accepted()),
            REJECTED: len(self.rejected()),
        }

    def digest(self) -> str:
        """Canonical sha256 over the snapshot (rows sorted by security_id)."""
        payload = {
            "schema": "universe_snapshot",
            "version": _UNIVERSE_SCHEMA_VERSION,
            "universe_id": self.universe_id,
            "decision_date": self.decision_date.isoformat(),
            "rows": [
                {
                    "security_id": row.security_id,
                    "ticker": row.ticker,
                    "status": row.status,
                    "reason": row.reason,
                    "history_days": row.history_days,
                    "median_dollar_volume": row.median_dollar_volume,
                    "last_obs": (
                        row.last_obs.isoformat() if row.last_obs is not None else None
                    ),
                }
                for row in sorted(self.rows, key=lambda r: r.security_id)
            ],
        }
        return sha256_text(canonical_json(payload))


def build_rebalance_snapshot(
    master: SecurityMaster,
    *,
    universe_id: str,
    decision_date: date,
    metrics: Mapping[str, EligibilityInput],
    rule: EligibilityRule,
) -> UniverseSnapshot:
    """Evaluate one rebalance, retaining ACCEPTED and REJECTED rows with reasons.

    Fail-closed: a member as of the decision date without metrics is an error,
    never a silent drop.
    """
    _require_date(decision_date, "decision_date")
    rows: list[UniverseRow] = []
    for security_id in master.members_as_of(decision_date):
        metric = metrics.get(security_id)
        if metric is None:
            raise UniverseError(
                f"no observations/metrics for member {security_id!r} on "
                f"{decision_date.isoformat()}; refusing to decide without data"
            )
        ticker = master.ticker_as_of(security_id, decision_date)
        if ticker is None:  # pragma: no cover - members_as_of guarantees coverage
            raise UniverseError(
                f"member {security_id!r} has no effective ticker on {decision_date}"
            )
        if metric.security_id != security_id or metric.ticker != ticker:
            raise UniverseError(
                f"metrics identity mismatch for {security_id!r} on "
                f"{decision_date.isoformat()}"
            )
        accepted, reason = rule(metric)
        if not isinstance(accepted, bool):
            raise UniverseError(f"rule for {security_id!r} must return (bool, str)")
        if not isinstance(reason, str) or not reason.strip():
            raise UniverseError(
                f"rule for {security_id!r} returned no reason; a reason is "
                "mandatory for ACCEPTED and REJECTED rows alike"
            )
        rows.append(
            UniverseRow(
                security_id=security_id,
                ticker=ticker,
                decision_date=decision_date,
                status=ACCEPTED if accepted else REJECTED,
                reason=reason,
                history_days=metric.history_days,
                median_dollar_volume=metric.median_dollar_volume,
                last_obs=metric.last_obs,
            )
        )
    if not rows:
        raise UniverseError(
            f"rebalance on {decision_date.isoformat()} produced no rows"
        )
    return UniverseSnapshot(
        universe_id=universe_id,
        decision_date=decision_date,
        rows=tuple(sorted(rows, key=lambda r: r.security_id)),
    )


# --- S0 floors (validators) ----------------------------------------------------- #
@dataclass(frozen=True)
class HistorySpan:
    """Observed coverage of one security (metadata-level; no bars needed)."""

    security_id: str
    first_obs: date
    last_obs: date
    eligible: bool = True


def evaluate_delisting_retention(
    master: SecurityMaster,
    last_obs_by_security: Mapping[str, date],
) -> tuple[str, ...]:
    """Delisted names must keep observations through their final valid event."""
    problems: list[str] = []
    for security_id in master.security_ids():
        record = master.get(security_id)
        if not record.is_delisted:
            continue
        last_obs = last_obs_by_security.get(security_id)
        if last_obs is None:
            problems.append(
                f"{security_id}: delisted security has NO retained observations "
                f"(final valid event {record.final_event_date.isoformat()})"
            )
        elif last_obs < record.final_event_date:
            problems.append(
                f"{security_id}: observations truncated {last_obs.isoformat()} < "
                f"final valid event {record.final_event_date.isoformat()}"
            )
    return tuple(problems)


def evaluate_s0_floors(
    *,
    histories: Mapping[str, HistorySpan],
    eligible_counts_by_decision: Mapping[date, int],
    latest_complete_date: date,
    s0_end: date,
    master: SecurityMaster | None = None,
    min_history_years: float = 8.0,
    min_eligible_names: int = 30,
    s0_buffer_months: int = 12,
) -> tuple[str, ...]:
    """Validate every initial S0 floor; returns violation messages (empty = ok).

    Floors (PLAN_stocks.md section 7 A3):

    * the common eligible population has >= ``min_history_years`` of daily
      history (joint window: max first_obs .. min last_obs over ELIGIBLE names);
    * every cross-sectional decision has >= ``min_eligible_names`` eligible
      liquid names;
    * delisted observations are retained through their final valid event —
      enforced when ``master`` is supplied (spans' ``last_obs`` vs the
      security's ``final_event_date``; see
      :func:`evaluate_delisting_retention`);
    * S0 ends >= ``s0_buffer_months`` before ``latest_complete_date``.
    """
    problems: list[str] = []
    eligible = [span for span in histories.values() if span.eligible]
    if not eligible:
        problems.append("history_floor: no eligible securities at all")
    else:
        common_start = max(span.first_obs for span in eligible)
        common_end = min(span.last_obs for span in eligible)
        days = (common_end - common_start).days
        years = days / 365.25
        if years < min_history_years:
            problems.append(
                f"history_floor: common eligible population covers {years:.2f}y "
                f"({common_start.isoformat()}..{common_end.isoformat()}) < "
                f"{min_history_years}y"
            )
    for decision_date, count in sorted(eligible_counts_by_decision.items()):
        if count < min_eligible_names:
            problems.append(
                f"eligible_names_floor: decision {decision_date.isoformat()} has "
                f"{count} eligible names < {min_eligible_names}"
            )
    if master is not None:
        last_obs_by_security = {
            span.security_id: span.last_obs
            for span in histories.values()
            if span.security_id in master.security_ids()
        }
        problems.extend(evaluate_delisting_retention(master, last_obs_by_security))
    shift = _add_months(latest_complete_date, -s0_buffer_months)
    if s0_end > shift:
        problems.append(
            f"s0_separation_floor: S0 ends {s0_end.isoformat()} which is less "
            f"than {s0_buffer_months} months before the latest complete date "
            f"{latest_complete_date.isoformat()} (must end on or before "
            f"{shift.isoformat()})"
        )
    return tuple(problems)


def assert_s0_floors(**kwargs: object) -> None:
    """Fail-closed variant of :func:`evaluate_s0_floors`."""
    problems = evaluate_s0_floors(**kwargs)  # type: ignore[arg-type]
    if problems:
        raise S0FloorViolation("; ".join(problems))


# --- sealed windows --------------------------------------------------------------- #
@dataclass(frozen=True)
class SealedWindows:
    """S0 research window plus a SEALED S1 window that cannot be opened.

    ``s0_end`` must sit at least ``buffer_months`` (default 12) before the
    latest complete provider date; the S1 window is the remainder and its
    accessor ALWAYS raises :class:`SealedWindowError`.
    """

    s0_start: date
    s0_end: date
    latest_complete_date: date
    buffer_months: int = 12

    def __post_init__(self) -> None:
        _require_date(self.s0_start, "s0_start")
        _require_date(self.s0_end, "s0_end")
        _require_date(self.latest_complete_date, "latest_complete_date")
        if self.s0_start >= self.s0_end:
            raise UniverseError("s0_start must precede s0_end")
        if self.buffer_months < 1:
            raise UniverseError("buffer_months must be >= 1")
        limit = _add_months(self.latest_complete_date, -self.buffer_months)
        if self.s0_end > limit:
            raise UniverseError(
                f"S0 must end no later than {self.buffer_months} months before the "
                f"latest complete date {self.latest_complete_date.isoformat()} "
                f"(latest allowed s0_end {limit.isoformat()}, got "
                f"{self.s0_end.isoformat()})"
            )

    @property
    def s1_starts_on(self) -> date:
        """First day of the sealed region (declared, never accessible as data)."""
        return _day_after(self.s0_end)

    def s0_window(self) -> tuple[date, date]:
        """Inclusive S0 research window."""
        return (self.s0_start, self.s0_end)

    def s1_window(self) -> "tuple[date, date]":
        """SEALED: always raises. S1 is never opened during this sprint."""
        raise SealedWindowError(
            "the S1 window is SEALED (PLAN_stocks.md section 7 A3); it is never "
            "opened during this sprint and no accessor may return it"
        )

    def require_within_s0(self, start: date, end: date) -> None:
        """Fail closed when a requested range touches the sealed region."""
        _require_date(start, "start")
        _require_date(end, "end")
        if end > self.s0_end:
            raise SealedWindowError(
                f"requested range {start.isoformat()}..{end.isoformat()} crosses "
                f"the S0/S1 boundary on {self.s1_starts_on.isoformat()}; the S1 "
                "window is sealed"
            )


def declare_sealed_windows(
    *,
    s0_start: date,
    s0_end: date,
    latest_complete_date: date,
    buffer_months: int = 12,
) -> SealedWindows:
    """Factory for :class:`SealedWindows` (validates the S0 separation floor)."""
    return SealedWindows(
        s0_start=s0_start,
        s0_end=s0_end,
        latest_complete_date=latest_complete_date,
        buffer_months=buffer_months,
    )
