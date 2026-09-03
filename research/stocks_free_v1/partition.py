"""S0/warmup/S1 partition freeze and S1 access isolation (owner: A3).

PLAN_stocks_free.md 4.2 — after accepted coverage is known (coverage is an
INPUT of :func:`freeze_partition`; this module never fabricates dates):

* ``S1``: the most recent NON-OVERLAPPING twelve COMPLETE calendar months
  of the coverage, SEALED.  If a valid sealed S1 cannot be formed the
  caller closes ``STOCKS_FREE_V1_BLOCKED_S1_ISOLATION`` — this module
  raises :class:`PartitionError` with ``S1_CANNOT_BE_FORMED``.
* ``warmup``: precedes S0, may NOT contribute scored trades.
* ``S0``: historical screening window, at least six complete years where
  possible (when fewer complete years exist, that fact is recorded in
  ``s0_complete_years`` / warnings — never silently accepted).
* three CHRONOLOGICAL S0 folds with force-flat boundaries and a declared
  purge: each fold's scored region ends ``purge_sessions`` before the
  fold's end, so no position can carry across a fold boundary or into S1.

Access isolation: :class:`SealedPathFilter` is the research-process
allowlist — paths under sealed roots, or data files whose embedded date
falls inside the sealed S1 range, raise :class:`SealedWindowError`.
Staging/hashing layers may see the complete delivery; research processes
cannot open S1 paths through this filter (PLAN 4.2, gate FD7).
"""

from __future__ import annotations

import calendar as _calendar
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Sequence

try:  # normal package import (available after A2/integration merge)
    from research.assets.stocks.calendar import (
        CALENDAR_TABLE_END,
        CALENDAR_TABLE_START,
        ET_ZONE,
        USEquityRegularCalendar,
        US_EQUITY_REGULAR_V1,
    )
except ImportError:  # direct file-path import in the A3 lane worktree
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from research.assets.stocks.calendar import (
        CALENDAR_TABLE_END,
        CALENDAR_TABLE_START,
        ET_ZONE,
        USEquityRegularCalendar,
        US_EQUITY_REGULAR_V1,
    )

PARTITION_SCHEMA = "stocks_free_v1/partition@1"
PARTITION_RULE_ID = "STOCKS_FREE_V1_S0_S1_PARTITION_V1"

S1_COMPLETE_MONTHS = 12
S0_MIN_COMPLETE_YEARS = 6
S0_FOLDS = 3
# Declared purge (regular sessions) forced flat at every fold boundary and
# before the S1 boundary; no scored trade may span a purge.
DEFAULT_PURGE_SESSIONS = 5
DEFAULT_WARMUP_SESSIONS = 63

BLOCKED_S1_ISOLATION = "STOCKS_FREE_V1_BLOCKED_S1_ISOLATION"


class PartitionError(ValueError):
    """Raised when a valid partition cannot be formed (fail closed)."""


class SealedWindowError(PermissionError):
    """Raised when a research process touches a sealed S1 path."""


@dataclass(frozen=True)
class Fold:
    """One chronological S0 fold with a force-flat, purged scored region.

    ``scored_end`` is the last session that may carry an OPEN position:
    ``purge_sessions`` before the fold end.  The purged tail sessions
    belong to no scored region of this fold.
    """

    fold_id: str
    start: date
    end: date
    scored_end: date
    purge_sessions: int

    @property
    def force_flat_sessions(self) -> tuple[date, ...]:
        return (self.scored_end,)


@dataclass(frozen=True)
class Partition:
    """Frozen S0/warmup/S1 window layout (UTC calendar dates)."""

    coverage_start: date
    coverage_end: date
    warmup_start: date
    warmup_end: date
    s0_start: date
    s0_end: date
    s1_start: date
    s1_end: date
    folds: tuple[Fold, ...]
    purge_sessions: int
    warmup_sessions: int
    s0_complete_years: int
    s0_minimum_years_met: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)
    schema: str = PARTITION_SCHEMA
    rule_id: str = PARTITION_RULE_ID

    @property
    def digest(self) -> str:
        payload = {
            "schema": self.schema,
            "rule_id": self.rule_id,
            "coverage": [self.coverage_start.isoformat(), self.coverage_end.isoformat()],
            "warmup": [self.warmup_start.isoformat(), self.warmup_end.isoformat()],
            "s0": [self.s0_start.isoformat(), self.s0_end.isoformat()],
            "s1": [self.s1_start.isoformat(), self.s1_end.isoformat()],
            "folds": [
                {
                    "fold_id": f.fold_id,
                    "start": f.start.isoformat(),
                    "end": f.end.isoformat(),
                    "scored_end": f.scored_end.isoformat(),
                    "purge_sessions": f.purge_sessions,
                }
                for f in self.folds
            ],
            "purge_sessions": self.purge_sessions,
            "warmup_sessions": self.warmup_sessions,
            "s0_complete_years": self.s0_complete_years,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def as_manifest(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "rule_id": self.rule_id,
            "partition_digest": self.digest,
            "coverage": [self.coverage_start.isoformat(), self.coverage_end.isoformat()],
            "warmup": [self.warmup_start.isoformat(), self.warmup_end.isoformat()],
            "warmup_may_contribute_scored_trades": False,
            "s0": [self.s0_start.isoformat(), self.s0_end.isoformat()],
            "s0_complete_years": self.s0_complete_years,
            "s0_minimum_years_met": self.s0_minimum_years_met,
            "s1": [self.s1_start.isoformat(), self.s1_end.isoformat()],
            "s1_status": "SEALED_NO_RESEARCH_READ",
            "folds": [
                {
                    "fold_id": f.fold_id,
                    "start": f.start.isoformat(),
                    "end": f.end.isoformat(),
                    "scored_end": f.scored_end.isoformat(),
                    "purge_sessions": f.purge_sessions,
                }
                for f in self.folds
            ],
            "purge_sessions": self.purge_sessions,
            "warnings": list(self.warnings),
        }


# --- month helpers ------------------------------------------------------------ #


def _month_end(year: int, month: int) -> date:
    return date(year, month, _calendar.monthrange(year, month)[1])


def _shift_months(day: date, months: int) -> date:
    month_index = day.year * 12 + (day.month - 1) + months
    year, month = divmod(month_index, 12)
    month += 1
    end_of_month = _month_end(year, month)
    return min(date(year, month, min(day.day, end_of_month.day)), end_of_month)


def _session_dates(
    calendar: USEquityRegularCalendar, start: date, end: date
) -> list[date]:
    return [
        session.start_utc.astimezone(ET_ZONE).date()
        for session in calendar.sessions_in_range(start, end)
    ]


# --- partition freeze ---------------------------------------------------------- #


def freeze_partition(
    *,
    coverage_start: date,
    coverage_end: date,
    calendar: USEquityRegularCalendar = US_EQUITY_REGULAR_V1,
    warmup_sessions: int = DEFAULT_WARMUP_SESSIONS,
    purge_sessions: int = DEFAULT_PURGE_SESSIONS,
    s1_complete_months: int = S1_COMPLETE_MONTHS,
    s0_min_complete_years: int = S0_MIN_COMPLETE_YEARS,
    n_folds: int = S0_FOLDS,
) -> Partition:
    """Freeze warmup/S0/folds/S1 from KNOWN coverage dates (input, never
    fabricated).  Fails closed when the sealed S1 or the S0 folds cannot be
    formed."""
    coverage_start = _require_date(coverage_start, "coverage_start")
    coverage_end = _require_date(coverage_end, "coverage_end")
    if coverage_end < coverage_start:
        raise PartitionError("coverage_end precedes coverage_start")
    if coverage_start < CALENDAR_TABLE_START or coverage_end > CALENDAR_TABLE_END:
        raise PartitionError(
            f"coverage [{coverage_start.isoformat()}, {coverage_end.isoformat()}] "
            f"leaves the frozen calendar table horizon "
            f"[{CALENDAR_TABLE_START.isoformat()}, {CALENDAR_TABLE_END.isoformat()}]"
        )
    if warmup_sessions < 0 or purge_sessions < 0:
        raise PartitionError("warmup/purge must be non-negative")
    if n_folds < 1:
        raise PartitionError("n_folds must be >= 1")

    warnings: list[str] = []

    # --- sealed S1: the most recent s1_complete_months COMPLETE months --- #
    last_complete_month_end = (
        _month_end(coverage_end.year, coverage_end.month)
        if coverage_end == _month_end(coverage_end.year, coverage_end.month)
        else _month_end(*_previous_month(coverage_end))
    )
    s1_end = last_complete_month_end
    s1_start = _shift_months(s1_end, -(s1_complete_months - 1)).replace(day=1)
    if s1_start <= coverage_start:
        raise PartitionError(
            f"S1_CANNOT_BE_FORMED: {s1_complete_months} complete months do not "
            f"fit in coverage [{coverage_start.isoformat()}, "
            f"{coverage_end.isoformat()}]; close {BLOCKED_S1_ISOLATION}"
        )

    # --- warmup precedes S0; warmup may not contribute scored trades ----- #
    sessions = _session_dates(calendar, coverage_start, coverage_end)
    if len(sessions) <= warmup_sessions + 2 * n_folds:
        raise PartitionError(
            "S0_CANNOT_BE_FORMED: too few sessions in coverage for warmup "
            f"+ {n_folds} folds"
        )
    warmup_start = sessions[0]
    warmup_end = sessions[warmup_sessions - 1] if warmup_sessions else warmup_start - timedelta(days=1)
    # S0 sits BETWEEN the warmup and the sealed S1 tail: its sessions are
    # every post-warmup session strictly before s1_start.
    s0_sessions = [day for day in sessions[warmup_sessions:] if day < s1_start]
    if len(s0_sessions) <= 2 * n_folds:
        raise PartitionError(
            "S0_CANNOT_BE_FORMED: too few sessions between warmup and the "
            f"sealed S1 for {n_folds} folds; fail closed"
        )
    s0_start = s0_sessions[0]
    s0_end = s0_sessions[-1]
    # S0 must end strictly before the sealed S1 begins.
    if s0_end >= s1_start:
        raise PartitionError(
            "S0 overlaps the sealed S1; fail closed "
            f"(s0_end {s0_end.isoformat()} >= s1_start {s1_start.isoformat()})"
        )

    # --- S0 completeness (recorded, never silently accepted) ------------- #
    s0_complete_years = _complete_years_inside(s0_start, s0_end)
    s0_minimum_years_met = s0_complete_years >= s0_min_complete_years
    if not s0_minimum_years_met:
        warnings.append(
            f"S0 has only {s0_complete_years} complete calendar year(s) "
            f"(minimum {s0_min_complete_years} NOT met); PLAN 4.2 permits "
            "'where possible' but this must be recorded and acknowledged"
        )

    # --- three chronological folds with force-flat purged boundaries ----- #
    folds = _build_folds(s0_sessions, n_folds, purge_sessions)

    return Partition(
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        warmup_start=warmup_start,
        warmup_end=warmup_end,
        s0_start=s0_start,
        s0_end=s0_end,
        s1_start=s1_start,
        s1_end=s1_end,
        folds=folds,
        purge_sessions=purge_sessions,
        warmup_sessions=warmup_sessions,
        s0_complete_years=s0_complete_years,
        s0_minimum_years_met=s0_minimum_years_met,
        warnings=tuple(warnings),
    )


def _previous_month(day: date) -> tuple[int, int]:
    year, month = day.year, day.month
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _complete_years_inside(start: date, end: date) -> int:
    """Complete calendar years (Jan 1..Dec 31) fully inside [start, end]."""
    count = 0
    for year in range(start.year, end.year + 1):
        if date(year, 1, 1) >= start and date(year, 12, 31) <= end:
            count += 1
    return count


def _build_folds(
    s0_sessions: Sequence[date], n_folds: int, purge_sessions: int
) -> tuple[Fold, ...]:
    """Contiguous chronological folds; each fold's scored region is purged
    (force-flat) ``purge_sessions`` before its end."""
    total = len(s0_sessions)
    base = total // n_folds
    remainder = total % n_folds
    folds: list[Fold] = []
    index = 0
    for fold_number in range(1, n_folds + 1):
        size = base + (1 if fold_number <= remainder else 0)
        start = s0_sessions[index]
        end_index = index + size - 1
        end = s0_sessions[end_index]
        scored_index = end_index - purge_sessions
        if scored_index < index:
            raise PartitionError(
                f"FOLD_CANNOT_BE_FORMED: fold {fold_number} smaller than its "
                f"purge ({purge_sessions} sessions); fail closed"
            )
        folds.append(
            Fold(
                fold_id=f"S0_FOLD_{fold_number}",
                start=start,
                end=end,
                scored_end=s0_sessions[scored_index],
                purge_sessions=purge_sessions,
            )
        )
        index += size
    return tuple(folds)


def _require_date(value: object, name: str) -> date:
    if isinstance(value, datetime) or not isinstance(value, date):
        raise ValueError(
            f"{name} must be a datetime.date, got {type(value).__name__}"
        )
    return value


# --- S1 filesystem isolation --------------------------------------------------- #

_DATE_TOKEN_PATTERNS = (
    re.compile(r"(?<!\d)(\d{4})-?(\d{2})-?(\d{2})(?!\d)"),  # 2025-03-14 / 20250314
)


def _dates_in_name(name: str) -> list[date]:
    found: list[date] = []
    for pattern in _DATE_TOKEN_PATTERNS:
        for match in pattern.finditer(name):
            try:
                found.append(date(int(match.group(1)), int(match.group(2)), int(match.group(3))))
            except ValueError:
                continue
    return found


@dataclass(frozen=True)
class SealedPathFilter:
    """Research-process allowlist: S1 paths are UNREADABLE through it.

    ``allowed_roots``: the only prefixes a research process may touch.
    ``sealed_roots``: prefixes that are sealed outright (e.g. an S1 data
    directory staged by the operator).
    ``sealed_date_range``: half-open-closed inclusive UTC-date range
    (``s1_start``, ``s1_end``); any path whose name embeds a date in this
    range is sealed even when the root itself is allowed (per-file date
    partition layouts).
    """

    allowed_roots: tuple[str, ...]
    sealed_roots: tuple[str, ...] = ()
    sealed_date_range: tuple[date, date] | None = None

    def __post_init__(self) -> None:
        if not self.allowed_roots:
            raise ValueError("SealedPathFilter requires at least one allowed root")

    # -- classification ---------------------------------------------------- #
    def reason_denied(self, path: str | Path) -> str | None:
        """Denial reason, or None when the path is readable."""
        candidate = str(path)
        normalized = candidate.replace("\\", "/")
        for sealed in self.sealed_roots:
            sealed_norm = str(sealed).replace("\\", "/").rstrip("/")
            if normalized == sealed_norm or normalized.startswith(sealed_norm + "/"):
                return f"path under sealed root {sealed}"
        if self.sealed_date_range is not None:
            s1_start, s1_end = self.sealed_date_range
            for name in (PurePosixPath(normalized).name, str(normalized)):
                for found in _dates_in_name(name):
                    if s1_start <= found <= s1_end:
                        return (
                            f"embedded date {found.isoformat()} is inside the "
                            f"sealed S1 range "
                            f"[{s1_start.isoformat()}, {s1_end.isoformat()}]"
                        )
        for root in self.allowed_roots:
            root_norm = str(root).replace("\\", "/").rstrip("/")
            if normalized == root_norm or normalized.startswith(root_norm + "/"):
                return None
        return f"path outside every allowed root {list(self.allowed_roots)}"

    def check(self, path: str | Path) -> Path:
        """Return the resolved path or raise :class:`SealedWindowError`."""
        reason = self.reason_denied(path)
        if reason is not None:
            raise SealedWindowError(
                f"SEALED_WINDOW denial for {path}: {reason} "
                "(S1 is sealed; research processes cannot read it)"
            )
        return Path(path)

    def open(self, path: str | Path, mode: str = "rb", **kwargs):
        """``open`` with S1 sealing enforced; write modes are rejected."""
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            raise SealedWindowError(
                f"SEALED_WINDOW denial for {path}: research processes get "
                "read-only access through the allowlist"
            )
        return open(self.check(path), mode, **kwargs)

    def is_readable(self, path: str | Path) -> bool:
        return self.reason_denied(path) is None


def build_research_allowlist(
    partition: Partition,
    *,
    data_root: str | Path,
) -> SealedPathFilter:
    """Allowlist for research processes over an A2 staged data root.

    The complete delivery may be hashed by staging layers; research
    processes get the data root MINUS anything dated inside the sealed S1.
    """
    return SealedPathFilter(
        allowed_roots=(str(data_root),),
        sealed_date_range=(partition.s1_start, partition.s1_end),
    )


__all__ = [
    "BLOCKED_S1_ISOLATION",
    "DEFAULT_PURGE_SESSIONS",
    "DEFAULT_WARMUP_SESSIONS",
    "Fold",
    "Partition",
    "PartitionError",
    "PARTITION_RULE_ID",
    "PARTITION_SCHEMA",
    "S0_FOLDS",
    "S0_MIN_COMPLETE_YEARS",
    "S1_COMPLETE_MONTHS",
    "SealedPathFilter",
    "SealedWindowError",
    "build_research_allowlist",
    "freeze_partition",
]
