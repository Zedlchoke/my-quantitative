"""Pre-return ETF cohort eligibility rule and census builder (owner: A3).

PLAN_stocks_free.md section 3.1: this cycle studies a **frozen cohort of
long-lived, liquid US-listed ETFs**.  No ticker is admitted because its
historical return looked attractive: eligibility is decided by the RULE
frozen in this module BEFORE any return is computed.  This module is a
data-rule authority only; it never computes, ranks or inspects strategy
returns.

Rule ``STOCKS_FREE_V1_COHORT_RULE_V1`` (all checks mandatory, no early
exit, every rejected row carries mandatory machine-readable reasons):

C1 ``IDENTIFIER_EVIDENCE``
    Exchange-listed ETF with stable identifier evidence: a non-empty
    ticker equal to the candidate symbol, a non-empty listing exchange
    and a non-empty issuer/vendor record.  (PLAN 3.1 bullet 1.)
C2 ``INCEPTION_BEFORE_WARMED_S0_START``
    Fund inception date is strictly before the S0 start pushed back by
    ``warmup_sessions`` regular sessions.  (PLAN 3.1 bullet 2; the S0
    warmup itself is frozen in
    :mod:`research.stocks_free_v1.partition`.)
C3 ``RAW_BARS_COMPLETE``
    Complete daily raw OHLCV inputs: exactly one sane bar per regular
    session over the declared common window, no duplicates, no
    manufactured bars (overnight/holiday gaps are returns, never filled).
    (PLAN 3.1 bullet 3.)
C4 ``TR_INPUTS_COMPLETE``
    Complete daily total-return inputs over the same common window: a
    positive total-return index point per regular session, backed by
    declared distribution/split provenance (kept outside this rule;
    per PLAN 4.1 conflicts block affected instruments).
C5 ``DOLLAR_VOLUME_FLOOR``
    Median daily dollar volume (raw close x raw volume) over the common
    window is at least ``DOLLAR_VOLUME_FLOOR_USD`` (predeclared here,
    never tuned after looking at returns).  (PLAN 3.1 bullet 4.)
C6 ``NO_UNRESOLVED_EVENTS``
    No unresolved ticker change, liquidation, split or distribution
    event anywhere in the evaluation scope.  (PLAN 3.1 bullet 5.)
C7 ``NEXT_SESSION_EXECUTABLE``
    Next-session executable raw-price semantics: for every session in
    the common window the shared calendar resolves a next regular
    session, and that next session carries a positive raw close
    (executable price) for every window session except the final one,
    whose next session may lie beyond the window horizon.  Fills never
    happen on the signal close.  (PLAN 3.1 bullet 6 and 3.2.)

Census builder
--------------
:func:`build_census` evaluates every candidate of the documentation-only
seed list against the rule and produces ACCEPTED and REJECTED rows plus a
canonical sha256 cohort digest over the accepted cohort, rule id, window
and rule parameters.  The seed list is documentation, NOT selection:
every candidate is decided by the same frozen checks.

Cohort limitation (PLAN 3.1): see ``CURRENT_SURVIVOR_LIMITATION``.  The
cycle may not generalize results to delisted ETFs or all US equities.

Import contract: this lane owns no ``__init__.py`` (A2 owns it); import
this module directly by file path (importlib/sys.path) until integration
merges the package.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Mapping, Protocol, Sequence, runtime_checkable

try:  # normal package import (available after A2/integration merge)
    from research.assets.stocks.calendar import (
        CALENDAR_TABLE_START,
        ET_ZONE,
        USEquityRegularCalendar,
    )
except ImportError:  # direct file-path import in the A3 lane worktree
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from research.assets.stocks.calendar import (
        CALENDAR_TABLE_START,
        ET_ZONE,
        USEquityRegularCalendar,
    )

COHORT_RULE_ID = "STOCKS_FREE_V1_COHORT_RULE_V1"
COHORT_DIGEST_SCHEMA = "stocks_free_v1/cohort_digest@1"

# Predeclared liquidity floor: median daily dollar volume (raw close x raw
# volume) over the declared common window.  Frozen before any return exists;
# changing it after scoring starts is a scientific-threshold change.
DOLLAR_VOLUME_FLOOR_USD = 10_000_000.0

# Required warmup (in regular sessions) between fund inception and the S0
# start; inception must sit strictly before the warmed S0 start.
WARMUP_SESSIONS = 63

# Documentation-only candidate seed list (PLAN 3.1).  Eligibility is decided
# by the RULE; membership in this list is not acceptance and observed returns
# play no part in it.
CANDIDATE_SEEDS: tuple[tuple[str, str], ...] = (
    ("SPY", "BROAD_US_EQUITY_BENCHMARK"),
    ("XLK", "SECTOR_TECHNOLOGY"),
    ("XLE", "SECTOR_ENERGY"),
    ("XLF", "SECTOR_FINANCIALS"),
    ("XLV", "SECTOR_HEALTH_CARE"),
    ("XLI", "SECTOR_INDUSTRIALS"),
    ("XLP", "SECTOR_CONSUMER_STAPLES"),
    ("XLY", "SECTOR_CONSUMER_DISCRETIONARY"),
    ("XLU", "SECTOR_UTILITIES"),
    ("XLB", "SECTOR_MATERIALS"),
    ("XLRE", "SECTOR_REAL_ESTATE"),
    ("XLC", "SECTOR_COMMUNICATION_SERVICES"),
    ("TLT", "DEFENSIVE_TREASURY"),
    ("GLD", "DEFENSIVE_GOLD"),
)

CURRENT_SURVIVOR_LIMITATION = (
    "COHORT LIMITATION (PLAN_stocks_free.md 3.1): the candidate seed list is a "
    "current-survivor list of long-lived US-listed ETFs. The frozen cohort is "
    "NOT survivorship-free: ETFs delisted before the evaluation window were "
    "never candidates. All inference is limited to the actual frozen ETF "
    "cohort; results may not be generalized to delisted ETFs, to the "
    "historical US stock market, or to all US equities."
)

ACCEPTED = "ACCEPTED"
REJECTED = "REJECTED"

# Mandatory machine-readable reason codes.  A rejected row's reasons are
# the codes of its FAILED checks (so a reason always maps 1:1 to a check);
# accepted rows carry ALL_CHECKS_PASSED.
ALL_CHECKS_PASSED = "ALL_CHECKS_PASSED"
REJECT_IDENTIFIER_EVIDENCE = "IDENTIFIER_EVIDENCE"
REJECT_INCEPTION_TOO_LATE = "INCEPTION_BEFORE_WARMED_S0_START"
REJECT_INCOMPLETE_RAW_BARS = "RAW_BARS_INCOMPLETE"
REJECT_INVALID_RAW_BARS = "RAW_BARS_INVALID"
REJECT_INCOMPLETE_TR_INPUTS = "TR_INPUTS_INCOMPLETE"
REJECT_VOLUME_FLOOR = "DOLLAR_VOLUME_FLOOR"
REJECT_UNRESOLVED_EVENTS = "NO_UNRESOLVED_EVENTS"
REJECT_NEXT_SESSION_NOT_EXECUTABLE = "NEXT_SESSION_EXECUTABLE"

_CHECK_IDENTIFIER = REJECT_IDENTIFIER_EVIDENCE
_CHECK_INCEPTION = REJECT_INCEPTION_TOO_LATE
_CHECK_RAW_BARS_INCOMPLETE = REJECT_INCOMPLETE_RAW_BARS
_CHECK_RAW_BARS_INVALID = REJECT_INVALID_RAW_BARS
_CHECK_TR_INPUTS = REJECT_INCOMPLETE_TR_INPUTS
_CHECK_DOLLAR_VOLUME = REJECT_VOLUME_FLOOR
_CHECK_NO_UNRESOLVED = REJECT_UNRESOLVED_EVENTS
_CHECK_NEXT_SESSION = REJECT_NEXT_SESSION_NOT_EXECUTABLE


@dataclass(frozen=True)
class RawBar:
    """One daily raw OHLCV bar at regular-session granularity."""

    session_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class TrPoint:
    """One daily total-return index point (dividends reinvested)."""

    session_date: date
    tr_level: float


@dataclass(frozen=True)
class UnresolvedEvent:
    """An unresolved ticker/liquidation/split/distribution event record."""

    symbol: str
    kind: str  # e.g. TICKER_CHANGE | LIQUIDATION | SPLIT | DISTRIBUTION
    event_date: date
    description: str


@runtime_checkable
class CohortDataSource(Protocol):
    """Minimal loader protocol A3 needs (A2's adapter implements it).

    Deliberately return-shaped rather than store-shaped: integration can
    wrap any A2 lane store without this module seeing the data lane.
    """

    def identifier_evidence(self, symbol: str) -> Mapping[str, object] | None:
        """Issuer/vendor record: ticker, exchange, issuer/vendor identity."""
        ...

    def inception_date(self, symbol: str) -> date | None:
        """Fund inception (first listing) date, or None when unknown."""
        ...

    def raw_bars(self, symbol: str) -> Sequence[RawBar]:
        """Daily raw OHLCV bars (never adjusted, never filled)."""
        ...

    def tr_index(self, symbol: str) -> Sequence[TrPoint]:
        """Daily total-return index points over the fund's history."""
        ...

    def unresolved_events(self, symbol: str) -> Sequence[UnresolvedEvent]:
        """Unresolved ticker/liquidation/split/distribution events."""
        ...


@dataclass(frozen=True)
class CheckResult:
    """One frozen rule check with mandatory detail."""

    code: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class CensusRow:
    """One candidate's rule verdict with mandatory reasons."""

    symbol: str
    role: str
    decision: str  # ACCEPTED | REJECTED
    reasons: tuple[str, ...]
    checks: tuple[CheckResult, ...]
    inception_date: date | None = None

    @property
    def accepted(self) -> bool:
        return self.decision == ACCEPTED


@dataclass(frozen=True)
class Census:
    """ACCEPTED + REJECTED census rows and the canonical cohort digest."""

    rows: tuple[CensusRow, ...]
    cohort_digest: str
    window_start: date
    window_end: date
    warmup_sessions: int
    dollar_volume_floor_usd: float
    rule_id: str = COHORT_RULE_ID
    limitation: str = field(default=CURRENT_SURVIVOR_LIMITATION)

    @property
    def accepted_symbols(self) -> tuple[str, ...]:
        return tuple(row.symbol for row in self.rows if row.accepted)

    @property
    def rejected_rows(self) -> tuple[CensusRow, ...]:
        return tuple(row for row in self.rows if not row.accepted)


# --- internal helpers ------------------------------------------------------- #


def _require_date(value: object, name: str) -> date:
    """Fail closed: accept only real dates (never datetime, never None)."""
    if isinstance(value, datetime) or not isinstance(value, date):
        raise ValueError(
            f"{name} must be a datetime.date, got {type(value).__name__}"
        )
    return value


def _session_dates(
    calendar: USEquityRegularCalendar, start: date, end: date
) -> list[date]:
    return [
        session.start_utc.astimezone(ET_ZONE).date()
        for session in calendar.sessions_in_range(start, end)
    ]


def _warmed_s0_start(
    calendar: USEquityRegularCalendar, s0_start: date, warmup_sessions: int
) -> date | None:
    """The session ``warmup_sessions`` regular sessions before ``s0_start``.

    Returns None when the computation would leave the frozen calendar table
    (fail closed, no guessing).
    """
    if warmup_sessions < 1:
        raise ValueError("warmup_sessions must be >= 1")
    from datetime import timedelta

    probe = s0_start - timedelta(days=warmup_sessions * 3 + 20)
    if probe < CALENDAR_TABLE_START:
        return None
    prior = _session_dates(calendar, probe, s0_start)
    # `prior` ends with s0_start itself.
    idx = len(prior) - 1 - warmup_sessions
    if idx < 0:
        return None
    return prior[idx]


def _check_identifier(
    symbol: str, evidence: Mapping[str, object] | None
) -> CheckResult:
    if not isinstance(evidence, Mapping) or not evidence:
        return CheckResult(
            _CHECK_IDENTIFIER, False, "no stable identifier evidence record"
        )
    ticker = str(evidence.get("ticker", "") or "").strip()
    exchange = str(evidence.get("exchange", "") or "").strip()
    issuer = str(evidence.get("issuer", evidence.get("vendor", "")) or "").strip()
    problems: list[str] = []
    if ticker != symbol:
        problems.append(
            f"ticker mismatch: evidence {ticker!r} != candidate {symbol!r}"
        )
    if not exchange:
        problems.append("missing listing exchange")
    if not issuer:
        problems.append("missing issuer/vendor record")
    if problems:
        return CheckResult(_CHECK_IDENTIFIER, False, "; ".join(problems))
    return CheckResult(
        _CHECK_IDENTIFIER, True, f"ticker {ticker} on {exchange} per {issuer}"
    )


def _check_inception(
    inception: date | None, warmed_start: date | None
) -> CheckResult:
    if inception is None:
        return CheckResult(
            _CHECK_INCEPTION, False, "inception date unknown; fail closed"
        )
    if warmed_start is None:
        return CheckResult(
            _CHECK_INCEPTION,
            False,
            "warmed S0 start outside frozen calendar table; fail closed",
        )
    if inception >= warmed_start:
        return CheckResult(
            _CHECK_INCEPTION,
            False,
            f"inception {inception.isoformat()} not before warmed S0 start "
            f"{warmed_start.isoformat()}",
        )
    return CheckResult(
        _CHECK_INCEPTION,
        True,
        f"inception {inception.isoformat()} < warmed S0 start "
        f"{warmed_start.isoformat()}",
    )


def _check_raw_bars(
    bars: Sequence[RawBar], sessions: Sequence[date]
) -> CheckResult:
    by_date: dict[date, RawBar] = {}
    duplicates: list[str] = []
    invalid: list[str] = []
    for bar in bars:
        if bar.session_date in by_date:
            duplicates.append(bar.session_date.isoformat())
            continue
        by_date[bar.session_date] = bar
        ok = (
            bar.open > 0.0
            and bar.low > 0.0
            and bar.close > 0.0
            and bar.volume >= 0.0
            and bar.high >= bar.low
            and bar.high >= max(bar.open, bar.close)
            and bar.low <= min(bar.open, bar.close)
        )
        if not ok:
            invalid.append(bar.session_date.isoformat())
    session_set = set(sessions)
    bar_set = set(by_date)
    missing = sorted(session_set - bar_set)
    extra = sorted(bar_set - session_set)
    problems: list[str] = []
    if missing:
        shown = ", ".join(d.isoformat() for d in missing[:5])
        problems.append(
            f"{len(missing)} regular session(s) without a raw bar "
            f"(first: {shown}); gaps are returns, never fabricated bars"
        )
    if extra:
        shown = ", ".join(d.isoformat() for d in extra[:5])
        problems.append(
            f"{len(extra)} bar(s) on non-session dates (first: {shown})"
        )
    if duplicates:
        shown = ", ".join(duplicates[:5])
        problems.append(f"{len(duplicates)} duplicate bar date(s) (first: {shown})")
    if invalid:
        shown = ", ".join(invalid[:5])
        problems.append(f"{len(invalid)} insane bar(s) (first: {shown})")
    if problems:
        coverage_problems = [p for p in problems if "insane bar" not in p]
        code = (
            _CHECK_RAW_BARS_INCOMPLETE
            if coverage_problems
            else _CHECK_RAW_BARS_INVALID
        )
        return CheckResult(code, False, "; ".join(problems))
    return CheckResult(
        _CHECK_RAW_BARS_INCOMPLETE,
        True,
        f"{len(sessions)} regular sessions fully covered by sane raw bars",
    )


def _check_tr_inputs(
    tr_points: Sequence[TrPoint], sessions: Sequence[date]
) -> CheckResult:
    by_date: dict[date, TrPoint] = {}
    duplicates = 0
    for point in tr_points:
        if point.session_date in by_date:
            duplicates += 1
            continue
        by_date[point.session_date] = point
    session_set = set(sessions)
    tr_set = set(by_date)
    missing = sorted(session_set - tr_set)
    extra = sorted(tr_set - session_set)
    nonpositive = sorted(
        d.isoformat() for d, p in by_date.items() if p.tr_level <= 0
    )
    problems: list[str] = []
    if missing:
        shown = ", ".join(d.isoformat() for d in missing[:5])
        problems.append(
            f"{len(missing)} regular session(s) without a total-return point "
            f"(first: {shown})"
        )
    if extra:
        shown = ", ".join(d.isoformat() for d in extra[:5])
        problems.append(
            f"{len(extra)} total-return point(s) on non-session dates "
            f"(first: {shown})"
        )
    if duplicates:
        problems.append(f"{duplicates} duplicate total-return date(s)")
    if nonpositive:
        shown = ", ".join(nonpositive[:5])
        problems.append(
            f"{len(nonpositive)} non-positive TR point(s) (first: {shown})"
        )
    if problems:
        return CheckResult(_CHECK_TR_INPUTS, False, "; ".join(problems))
    return CheckResult(
        _CHECK_TR_INPUTS,
        True,
        f"{len(sessions)} regular sessions fully covered by positive TR points",
    )


def _check_dollar_volume(bars: Sequence[RawBar], floor: float) -> CheckResult:
    dv = sorted(bar.close * bar.volume for bar in bars)
    if not dv:
        return CheckResult(_CHECK_DOLLAR_VOLUME, False, "no bars to evaluate")
    median_dv = statistics.median(dv)
    if median_dv < floor:
        return CheckResult(
            _CHECK_DOLLAR_VOLUME,
            False,
            f"median daily dollar volume {median_dv:,.0f} USD < floor "
            f"{floor:,.0f} USD (predeclared)",
        )
    return CheckResult(
        _CHECK_DOLLAR_VOLUME,
        True,
        f"median daily dollar volume {median_dv:,.0f} USD >= floor "
        f"{floor:,.0f} USD (predeclared)",
    )


def _check_unresolved_events(events: Sequence[UnresolvedEvent]) -> CheckResult:
    if events:
        described = "; ".join(
            f"{e.kind}@{e.event_date.isoformat()}: {e.description}"
            for e in events[:5]
        )
        return CheckResult(
            _CHECK_NO_UNRESOLVED,
            False,
            f"{len(events)} unresolved event(s): {described}",
        )
    return CheckResult(
        _CHECK_NO_UNRESOLVED, True, "no unresolved events recorded"
    )


def _check_next_session(
    calendar: USEquityRegularCalendar,
    bars_by_date: Mapping[date, RawBar],
    sessions: Sequence[date],
) -> CheckResult:
    problems: list[str] = []
    for i, day in enumerate(sessions):
        try:
            nxt = calendar.next_session(day)
        except ValueError as exc:
            problems.append(f"no next session after {day.isoformat()}: {exc}")
            continue
        next_date = nxt.start_utc.astimezone(ET_ZONE).date()
        is_last = i == len(sessions) - 1
        if is_last:
            # The next event may be beyond the common window; it only has to
            # resolve within the frozen calendar horizon.
            continue
        bar = bars_by_date.get(next_date)
        if bar is None:
            problems.append(
                f"no raw bar on next session {next_date.isoformat()} after "
                f"{day.isoformat()}"
            )
        elif bar.close <= 0.0:
            problems.append(
                f"non-positive raw close on next session {next_date.isoformat()}"
            )
    if problems:
        return CheckResult(_CHECK_NEXT_SESSION, False, "; ".join(problems[:5]))
    return CheckResult(
        _CHECK_NEXT_SESSION,
        True,
        "every window session resolves a next regular session with a positive "
        "raw executable close (final session: calendar resolution only)",
    )


# --- public rule API -------------------------------------------------------- #


def evaluate_candidate(
    symbol: str,
    *,
    source: CohortDataSource,
    calendar: USEquityRegularCalendar,
    window_start: date,
    window_end: date,
    s0_start: date,
    warmup_sessions: int = WARMUP_SESSIONS,
    dollar_volume_floor: float = DOLLAR_VOLUME_FLOOR_USD,
) -> CensusRow:
    """Apply every frozen check to one candidate; never short-circuits."""
    window_start = _require_date(window_start, "window_start")
    window_end = _require_date(window_end, "window_end")
    s0_start = _require_date(s0_start, "s0_start")
    if window_end < window_start:
        raise ValueError("window_end precedes window_start")

    sessions = _session_dates(calendar, window_start, window_end)
    evidence = source.identifier_evidence(symbol)
    inception = source.inception_date(symbol)
    bars = list(source.raw_bars(symbol))
    tr_points = list(source.tr_index(symbol))
    unresolved = list(source.unresolved_events(symbol))

    checks: list[CheckResult] = [
        _check_identifier(symbol, evidence),
        _check_inception(
            inception, _warmed_s0_start(calendar, s0_start, warmup_sessions)
        ),
        _check_raw_bars(bars, sessions),
        _check_tr_inputs(tr_points, sessions),
        _check_dollar_volume(bars, dollar_volume_floor),
        _check_unresolved_events(unresolved),
    ]
    bars_by_date = {bar.session_date: bar for bar in bars}
    checks.append(_check_next_session(calendar, bars_by_date, sessions))

    failed = [check for check in checks if not check.passed]
    decision = REJECTED if failed else ACCEPTED
    reasons = (
        tuple(check.code for check in failed) if failed else (ALL_CHECKS_PASSED,)
    )
    return CensusRow(
        symbol=symbol,
        role=_role_for(symbol),
        decision=decision,
        reasons=reasons,
        checks=tuple(checks),
        inception_date=inception,
    )


def _role_for(symbol: str) -> str:
    for seed_symbol, role in CANDIDATE_SEEDS:
        if seed_symbol == symbol:
            return role
    return "UNLISTED_CANDIDATE"


def canonical_cohort_digest(
    rows: Sequence[CensusRow],
    *,
    window_start: date,
    window_end: date,
    warmup_sessions: int,
    dollar_volume_floor: float,
) -> str:
    """sha256 over the canonical accepted-cohort manifest (rule id, window,
    predeclared parameters, sorted accepted rows)."""
    accepted = sorted(
        (
            {
                "symbol": row.symbol,
                "role": row.role,
                "inception": row.inception_date.isoformat()
                if row.inception_date
                else None,
            }
            for row in rows
            if row.accepted
        ),
        key=lambda item: item["symbol"],
    )
    payload = {
        "schema": COHORT_DIGEST_SCHEMA,
        "rule_id": COHORT_RULE_ID,
        "window": [window_start.isoformat(), window_end.isoformat()],
        "warmup_sessions": warmup_sessions,
        "dollar_volume_floor_usd": dollar_volume_floor,
        "accepted": accepted,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_census(
    candidates: Sequence[tuple[str, str]],
    *,
    source: CohortDataSource,
    calendar: USEquityRegularCalendar,
    window_start: date,
    window_end: date,
    s0_start: date,
    warmup_sessions: int = WARMUP_SESSIONS,
    dollar_volume_floor: float = DOLLAR_VOLUME_FLOOR_USD,
) -> Census:
    """Evaluate the whole candidate list; ACCEPTED/REJECTED rows + digest.

    ``candidates`` are (symbol, role) pairs supplied by the documentation
    seed list; the role is carried through for disclosure only and plays no
    part in acceptance.
    """
    rows: list[CensusRow] = []
    for symbol, role in candidates:
        row = evaluate_candidate(
            symbol,
            source=source,
            calendar=calendar,
            window_start=window_start,
            window_end=window_end,
            s0_start=s0_start,
            warmup_sessions=warmup_sessions,
            dollar_volume_floor=dollar_volume_floor,
        )
        if role and row.role == "UNLISTED_CANDIDATE":
            row = CensusRow(
                symbol=row.symbol,
                role=role,
                decision=row.decision,
                reasons=row.reasons,
                checks=row.checks,
                inception_date=row.inception_date,
            )
        rows.append(row)
    digest = canonical_cohort_digest(
        rows,
        window_start=window_start,
        window_end=window_end,
        warmup_sessions=warmup_sessions,
        dollar_volume_floor=dollar_volume_floor,
    )
    return Census(
        rows=tuple(rows),
        cohort_digest=digest,
        window_start=window_start,
        window_end=window_end,
        warmup_sessions=warmup_sessions,
        dollar_volume_floor_usd=dollar_volume_floor,
    )


__all__ = [
    "ACCEPTED",
    "ALL_CHECKS_PASSED",
    "CANDIDATE_SEEDS",
    "COHORT_DIGEST_SCHEMA",
    "COHORT_RULE_ID",
    "CURRENT_SURVIVOR_LIMITATION",
    "Census",
    "CensusRow",
    "CheckResult",
    "CohortDataSource",
    "DOLLAR_VOLUME_FLOOR_USD",
    "RawBar",
    "REJECTED",
    "REJECT_IDENTIFIER_EVIDENCE",
    "REJECT_INCOMPLETE_RAW_BARS",
    "REJECT_INCOMPLETE_TR_INPUTS",
    "REJECT_INCEPTION_TOO_LATE",
    "REJECT_INVALID_RAW_BARS",
    "REJECT_NEXT_SESSION_NOT_EXECUTABLE",
    "REJECT_UNRESOLVED_EVENTS",
    "REJECT_VOLUME_FLOOR",
    "TrPoint",
    "UnresolvedEvent",
    "WARMUP_SESSIONS",
    "build_census",
    "canonical_cohort_digest",
    "evaluate_candidate",
]
