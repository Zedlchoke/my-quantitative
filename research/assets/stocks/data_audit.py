"""Point-in-time data audit (owner: A3).

Composes the loader and the security master into an audit report with
verdicts PASS / FAIL / NOT_RUN only:

* ``checksum_and_partitions`` — every security's full window loads through the
  checksum-verified loader (missing/tampered/unmanifested partitions FAIL);
* ``pit_timestamps`` — both exchange and ingest timestamps exist, are
  tz-aware, and ingest >= exchange on every row;
* ``regular_session_gaps_explained`` — every missing day between a security's
  first and last observation that the INJECTED session predicate declares a
  regular session is an unexplained gap (FAIL).  The predicate is a required
  parameter of type ``Callable[[date], bool]`` supplied by the caller; the
  official calendar is owned by another lane, so when no predicate is
  injected the check is NOT_RUN — never a silent pass, never a locally
  implemented calendar;
* ``delisting_retention`` — delisted securities keep observations through
  their final valid event.

The audit performs NO writes: it returns an immutable report whose canonical
JSON can back gate evidence (``SD0_DATA_PIT_PASS``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Mapping

from research.assets.common.contracts import canonical_json
from research.assets.stocks.loader import (
    BarLoader,
    LoaderError,
    SchemaError,
    SessionPredicate,
)
from research.assets.stocks.universe import (
    HistorySpan,
    SecurityMaster,
    UniverseError,
    evaluate_delisting_retention,
)

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_NOT_RUN = "NOT_RUN"

#: Report detail caps (evidence stays bounded, findings are counted fully).
_MAX_FINDINGS_IN_DETAIL = 20


@dataclass(frozen=True)
class AuditCheck:
    """One audit check: name, PASS/FAIL/NOT_RUN verdict, bounded detail."""

    name: str
    verdict: str
    detail: str

    def __post_init__(self) -> None:
        if self.verdict not in (VERDICT_PASS, VERDICT_FAIL, VERDICT_NOT_RUN):
            raise ValueError(
                f"verdict must be PASS/FAIL/NOT_RUN, got {self.verdict!r}"
            )
        if not isinstance(self.detail, str) or not self.detail.strip():
            raise ValueError(f"check {self.name!r}: detail is mandatory")


@dataclass(frozen=True)
class PitAuditReport:
    """Immutable PIT audit report (overall verdict + per-check verdicts)."""

    root: str
    checks: tuple[AuditCheck, ...]

    def __post_init__(self) -> None:
        if not self.checks:
            raise ValueError("a PIT audit report requires at least one check")
        names = [check.name for check in self.checks]
        if len(set(names)) != len(names):
            raise ValueError("duplicate check names in report")

    @property
    def verdict(self) -> str:
        """FAIL if any check failed, else NOT_RUN if any check did not run."""
        verdicts = {check.verdict for check in self.checks}
        if VERDICT_FAIL in verdicts:
            return VERDICT_FAIL
        if VERDICT_NOT_RUN in verdicts:
            return VERDICT_NOT_RUN
        return VERDICT_PASS

    def check(self, name: str) -> AuditCheck:
        for candidate in self.checks:
            if candidate.name == name:
                return candidate
        raise KeyError(f"no check named {name!r}")

    def to_payload(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "verdict": self.verdict,
            "checks": [
                {"name": c.name, "verdict": c.verdict, "detail": c.detail}
                for c in self.checks
            ],
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_payload())

    def gate_evidence(self, gate_id: str = "SD0_DATA_PIT_PASS") -> dict[str, Any]:
        """Payload for the gate evidence file (integration writes the JSON)."""
        return {
            "gate": gate_id,
            "verdict": self.verdict,
            "report": self.to_payload(),
        }


def run_pit_audit(
    *,
    root: Path,
    master: SecurityMaster,
    latest_complete_date: date,
    session_predicate: SessionPredicate | None = None,
    manifest_path: Path | None = None,
    gap_tolerance_days: int = 0,
) -> PitAuditReport:
    """Run every PIT data check over the prepared dataset at ``root``.

    ``session_predicate`` must be injected by the caller (the official
    session calendar is owned by the calendar lane).  Without it the
    regular-session gap check is NOT_RUN.  ``gap_tolerance_days`` is the
    declared loader tolerance; the audit itself reports ANY unexplained
    regular-session gap regardless of tolerance.
    """
    root = Path(root)
    # The audit must report gaps, not crash on them: load with gap
    # enforcement off and analyze per-date coverage here.
    loader = BarLoader(
        root,
        manifest_path=manifest_path,
        gap_tolerance_days=gap_tolerance_days,
        session_predicate=session_predicate,
        enforce_gaps=False,
    )
    integrity_findings: list[str] = []
    pit_findings: list[str] = []
    gap_findings: list[str] = []
    last_obs_by_security: dict[str, date] = {}
    loaded: dict[str, Any] = {}
    for security_id in master.security_ids():
        record = master.get(security_id)
        try:
            end = record.final_event_date if record.is_delisted else latest_complete_date
            frame = loader.load(
                security_id,
                start=record.listed_date,
                end=max(end, record.listed_date),
                allow_duplicate_timestamps=False,
            )
        except SchemaError as exc:
            pit_findings.append(f"{security_id}: {exc}")
            continue
        except LoaderError as exc:
            integrity_findings.append(f"{security_id}: {exc}")
            continue
        loaded[security_id] = frame
        observed = sorted(set(frame["ts_exchange"].dt.date))
        last_obs_by_security[security_id] = observed[-1]
        # Unexplained regular-session gaps: a day the predicate declares a
        # session, between first and last observation, with no bar.
        if session_predicate is not None:
            for previous, following in zip(observed, observed[1:]):
                for offset in range(1, (following - previous).days):
                    day = date.fromordinal(previous.toordinal() + offset)
                    if session_predicate(day):
                        gap_findings.append(
                            f"{security_id}: no observation on regular session day "
                            f"{day.isoformat()} (between {previous.isoformat()} and "
                            f"{following.isoformat()})"
                        )
    checksum_check = AuditCheck(
        name="checksum_and_partitions",
        verdict=VERDICT_FAIL if integrity_findings else VERDICT_PASS,
        detail=(
            "; ".join(integrity_findings[:_MAX_FINDINGS_IN_DETAIL])
            if integrity_findings
            else f"all {len(master)} securities load through the verified manifest"
        ),
    )
    pit_check = AuditCheck(
        name="pit_timestamps",
        verdict=VERDICT_FAIL if pit_findings else VERDICT_PASS,
        detail=(
            "; ".join(pit_findings[:_MAX_FINDINGS_IN_DETAIL])
            if pit_findings
            else (
                "ts_exchange + ts_ingest present, tz-aware, ingest >= exchange "
                f"for {len(loaded)}/{len(master)} securities"
            )
        ),
    )
    if session_predicate is None:
        gap_check = AuditCheck(
            name="regular_session_gaps_explained",
            verdict=VERDICT_NOT_RUN,
            detail=(
                "no session predicate injected; the official calendar is owned "
                "by the calendar lane and cannot be assumed or reimplemented here"
            ),
        )
    else:
        gap_check = AuditCheck(
            name="regular_session_gaps_explained",
            verdict=VERDICT_FAIL if gap_findings else VERDICT_PASS,
            detail=(
                "; ".join(gap_findings[:_MAX_FINDINGS_IN_DETAIL])
                if gap_findings
                else f"no unexplained regular-session gaps across "
                f"{len(loaded)}/{len(master)} securities"
            ),
        )
    retention_problems = evaluate_delisting_retention(master, last_obs_by_security)
    retention_check = AuditCheck(
        name="delisting_retention",
        verdict=VERDICT_FAIL if retention_problems else VERDICT_PASS,
        detail=(
            "; ".join(retention_problems[:_MAX_FINDINGS_IN_DETAIL])
            if retention_problems
            else "delisted observations retained through their final valid event"
        ),
    )
    return PitAuditReport(
        root=str(root),
        checks=(checksum_check, pit_check, gap_check, retention_check),
    )


def summarize_histories(
    master: SecurityMaster,
    last_obs_by_security: Mapping[str, date],
    *,
    eligibility: Callable[[str], bool] | None = None,
) -> dict[str, HistorySpan]:
    """Convenience: build :class:`HistorySpan` metadata from loaded coverage.

    ``first_obs`` uses the listing date (the earliest possible observation);
    the audit-level floors then run on the same vocabulary as
    :func:`research.assets.stocks.universe.evaluate_s0_floors`.
    """
    spans: dict[str, HistorySpan] = {}
    for security_id in master.security_ids():
        record = master.get(security_id)
        last_obs = last_obs_by_security.get(
            security_id,
            record.final_event_date if record.is_delisted else record.listed_date,
        )
        spans[security_id] = HistorySpan(
            security_id=security_id,
            first_obs=record.listed_date,
            last_obs=last_obs,
            eligible=eligibility(security_id) if eligibility else True,
        )
    return spans


__all__ = [
    "VERDICT_FAIL",
    "VERDICT_NOT_RUN",
    "VERDICT_PASS",
    "AuditCheck",
    "PitAuditReport",
    "UniverseError",
    "run_pit_audit",
    "summarize_histories",
]
