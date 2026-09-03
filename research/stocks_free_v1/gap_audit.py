"""Missing/duplicate/out-of-order/price/gap audit for stocks-free-v1 (A2, Z1).

Implements PLAN_stocks_free.md section 4.1 items 5 and 11 philosophy:
coverage is loader-resolved (the audit runs on OBSERVED series, never on file
presence) and the session convention is INJECTED as a predicate callable —
this module never implements a calendar itself (the frozen calendar lives in
``research/assets/stocks/calendar.py`` and is read-only reuse).

Findings are fail-closed: an empty series is itself a finding.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence

FINDING_KINDS = frozenset(
    {
        "EMPTY_SERIES",
        "DUPLICATE_DATE",
        "OUT_OF_ORDER",
        "NON_POSITIVE_PRICE",
        "MISSING_SESSION",
        "GAP_BEYOND_TOLERANCE",
        "MISSING_VALUE",
    }
)


@dataclass(frozen=True)
class GapFinding:
    kind: str
    detail: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GapReport:
    n_observations: int
    n_unique_dates: int
    span_days: Optional[int]
    findings: List[GapFinding] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict:
        return {
            "n_observations": self.n_observations,
            "n_unique_dates": self.n_unique_dates,
            "span_days": self.span_days,
            "is_clean": self.is_clean,
            "findings": [f.to_dict() for f in self.findings],
        }


def audit_series(
    dates: Sequence[dt.date],
    session_predicate: Callable[[dt.date], bool],
    values: Optional[Sequence[Optional[float]]] = None,
    max_gap_calendar_days: Optional[int] = 14,
    detect_missing_sessions: bool = True,
) -> GapReport:
    """Audit one observed series.

    Parameters
    ----------
    dates:
        Observed dates in provider order (duplicates and disorder allowed —
        they are findings, not exceptions).
    session_predicate:
        Injected callable returning True when a calendar date is an expected
        trading session (e.g. ``calendar.is_session``). Never implemented
        here.
    values:
        Optional parallel value list (closes/NAVs). ``None`` or non-finite
        positive checks produce ``MISSING_VALUE``/``NON_POSITIVE_PRICE``.
    max_gap_calendar_days:
        Declared tolerance: two consecutive observed sessions more than this
        many calendar days apart raise ``GAP_BEYOND_TOLERANCE`` even when the
        predicate claims no missing session (catches a wrong/incomplete
        calendar instead of failing open).
    detect_missing_sessions:
        When True, sessions per the predicate between two observed dates but
        absent from the series raise ``MISSING_SESSION`` findings.
    """
    findings: List[GapFinding] = []
    n = len(dates)
    if values is not None and len(values) != n:
        raise ValueError("dates and values lengths differ")
    if n == 0:
        return GapReport(0, 0, None, [GapFinding("EMPTY_SERIES", "no observations")])

    seen: Dict[dt.date, int] = {}
    for i, d in enumerate(dates):
        seen[d] = seen.get(d, 0) + 1
        if values is not None:
            v = values[i]
            if v is None:
                findings.append(
                    GapFinding("MISSING_VALUE", f"{d.isoformat()}: value is None")
                )
            elif v <= 0:
                findings.append(
                    GapFinding(
                        "NON_POSITIVE_PRICE", f"{d.isoformat()}: value {v!r} <= 0"
                    )
                )
    for d, count in sorted(seen.items()):
        if count > 1:
            findings.append(
                GapFinding("DUPLICATE_DATE", f"{d.isoformat()} appears {count}x")
            )

    for i in range(1, n):
        if dates[i] < dates[i - 1]:
            findings.append(
                GapFinding(
                    "OUT_OF_ORDER",
                    f"dates[{i}] {dates[i].isoformat()} < dates[{i - 1}] "
                    f"{dates[i - 1].isoformat()}",
                )
            )

    ordered = sorted(seen)
    span = (ordered[-1] - ordered[0]).days
    unique = set(seen)
    for a, b in zip(ordered, ordered[1:]):
        gap_days = (b - a).days
        if max_gap_calendar_days is not None and gap_days > max_gap_calendar_days:
            findings.append(
                GapFinding(
                    "GAP_BEYOND_TOLERANCE",
                    f"{a.isoformat()} -> {b.isoformat()} spans {gap_days} "
                    f"calendar days > declared {max_gap_calendar_days}",
                )
            )
        if detect_missing_sessions:
            cursor = a + dt.timedelta(days=1)
            while cursor < b:
                if session_predicate(cursor) and cursor not in unique:
                    findings.append(
                        GapFinding(
                            "MISSING_SESSION",
                            f"{cursor.isoformat()} expected by session "
                            "predicate but absent from series",
                        )
                    )
                cursor += dt.timedelta(days=1)

    return GapReport(n, len(seen), span, findings)


def summarize_reports(reports: Iterable[tuple]) -> dict:
    """Aggregate per-instrument reports into a compact audit summary."""
    summary: dict = {"instruments": {}, "total_findings": 0, "clean": True}
    for name, report in reports:
        summary["instruments"][name] = report.to_dict()
        summary["total_findings"] += len(report.findings)
        summary["clean"] = summary["clean"] and report.is_clean
    return summary
