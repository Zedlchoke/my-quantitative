"""Exact decision clocks + idempotent run loop (plan sections E, G5).

Frozen decision clocks (from the identity manifest decision_clock
parameters):
- weekly Monday 00:00:00Z : ILLIQ-AMIHUD-28D-W, BASISLV-PREMFADE-28D
- daily 00:00:00Z         : XSECT-FUND-CARRY-7D

``pending_decisions`` is a pure function. ``run_once`` derives due
decisions, skips ones already in the ledger (by deterministic
event_id), executes the rest in order and appends records atomically.
A second identical run over the same window produces ZERO new events
and a byte-identical ledger. ``DataBlocked`` from an executor records a
DATA_BLOCKED event under the SAME deterministic event_id (no price is
synthesized; a retry cannot duplicate the decision).

``heartbeat`` returns {last_scheduled_event, last_completed_event,
ledger_byte_count}.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import events, ledger

FAMILY_ILLIQ = "ILLIQ-AMIHUD-28D-W"
FAMILY_PREMFADE = "BASISLV-PREMFADE-28D"
FAMILY_CARRY = "XSECT-FUND-CARRY-7D"

SCHEDULE_WEEKLY_MONDAY_0000Z = "weekly_monday_0000z"
SCHEDULE_DAILY_0000Z = "daily_0000z"

#: Frozen decision clocks per identity manifest / dispatch packet.
FAMILY_SCHEDULES: Dict[str, str] = {
    FAMILY_ILLIQ: SCHEDULE_WEEKLY_MONDAY_0000Z,
    FAMILY_PREMFADE: SCHEDULE_WEEKLY_MONDAY_0000Z,
    FAMILY_CARRY: SCHEDULE_DAILY_0000Z,
}

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
_WEEK = dt.timedelta(days=7)
_DAY = dt.timedelta(days=1)

HeartbeatExecutor = Callable[[str, str, str], Dict[str, Any]]


class SchedulerError(RuntimeError):
    """Scheduler misconfiguration or contract violation."""


def schedule_for(family_id: str) -> str:
    if family_id not in FAMILY_SCHEDULES:
        raise SchedulerError(f"unknown family {family_id!r}; no frozen schedule")
    return FAMILY_SCHEDULES[family_id]


def to_iso_z(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).strftime(ISO_FMT)


def parse_iso_z(text: str) -> dt.datetime:
    return dt.datetime.strptime(text, ISO_FMT).replace(tzinfo=dt.timezone.utc)


def _first_decision_at_or_after(schedule: str, from_utc: dt.datetime) -> dt.datetime:
    day = from_utc.astimezone(dt.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    if schedule == SCHEDULE_DAILY_0000Z:
        if day < from_utc:
            day += _DAY
        return day
    if schedule == SCHEDULE_WEEKLY_MONDAY_0000Z:
        # Monday == weekday 0
        days_ahead = (0 - day.weekday()) % 7
        day += _DAY * days_ahead
        if day < from_utc:
            day += _WEEK
        return day
    raise SchedulerError(f"unknown schedule {schedule!r}")


def pending_decisions(family_id: str, from_utc: str, to_utc: str) -> List[str]:
    """Pure: exact decision timestamps with from inclusive, to exclusive."""
    schedule = schedule_for(family_id)
    start = parse_iso_z(from_utc)
    end = parse_iso_z(to_utc)
    if end < start:
        raise SchedulerError("to_utc earlier than from_utc")
    out: List[str] = []
    step = _DAY if schedule == SCHEDULE_DAILY_0000Z else _WEEK
    cursor = _first_decision_at_or_after(schedule, start)
    while cursor < end:
        out.append(to_iso_z(cursor))
        cursor += step
    return out


def run_once(
    family_id: str,
    now_utc: str,
    executor: HeartbeatExecutor,
    runtime_root: str,
    *,
    arm_id: Optional[str] = None,
    from_utc: Optional[str] = None,
    to_utc: Optional[str] = None,
    blocked_event_builder: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Idempotency loop over one family's ledger.

    ``executor(family_id, scheduled_decision_utc, event_id)`` returns a
    full plan section 8 record or raises ``data_feed.DataBlocked`` (or
    any exception with ``data_blocked = True`` semantics handled by the
    caller-supplied ``blocked_event_builder``).
    """
    if arm_id is None:
        arm_id = family_id
    path = ledger.ledger_path(runtime_root, family_id)
    existing_records = ledger.scan_events(path)
    existing_ids = {rec["event_id"] for rec in existing_records}

    window_end = to_utc if to_utc is not None else now_utc
    if from_utc is None:
        if existing_records:
            from_utc = max(rec["scheduled_decision_utc"] for rec in existing_records)
        else:
            from_utc = window_end  # nothing scheduled yet

    due = pending_decisions(family_id, from_utc, window_end)
    emitted = 0
    skipped = 0
    blocked = 0
    last_event_id: Optional[str] = None

    for scheduled_utc in due:  # chronological order
        event_id = events.compute_event_id(family_id, arm_id, scheduled_utc)
        if event_id in existing_ids:
            skipped += 1
            continue
        from_blocked_exception = False
        try:
            record = executor(family_id, scheduled_utc, event_id)
        except Exception as exc:  # noqa: BLE001 - fail-closed conversion below
            if not getattr(exc, "data_blocked", False):
                raise
            builder = blocked_event_builder
            if builder is None:
                builder = _default_blocked_builder(getattr(exc, "context", {}))
            record = builder(
                family_id=family_id,
                arm_id=arm_id,
                scheduled_decision_utc=scheduled_utc,
                blocked_reason=str(getattr(exc, "reason", exc)),
            )
            from_blocked_exception = True
            blocked += 1
        events.validate_event_record(record)
        if record["event_id"] != event_id:
            raise SchedulerError(
                f"executor returned event_id {record['event_id']!r}, "
                f"expected deterministic {event_id!r}"
            )
        ledger.append_event(path, record)
        existing_ids.add(event_id)
        last_event_id = event_id
        if from_blocked_exception:
            pass  # already counted as blocked
        elif record["data_status"] == events.DATA_STATUS_BLOCKED:
            blocked += 1
        else:
            emitted += 1

    return {
        "family_id": family_id,
        "emitted": emitted,
        "skipped_existing": skipped,
        "blocked": blocked,
        "last_event_id": last_event_id,
        "ledger_digest": ledger.ledger_digest(path),
    }


def _default_blocked_builder(context: Dict[str, Any]) -> Callable[..., Dict[str, Any]]:
    def builder(
        *,
        family_id: str,
        arm_id: str,
        scheduled_decision_utc: str,
        blocked_reason: str,
    ) -> Dict[str, Any]:
        return events.build_data_blocked_event(
            family_id=family_id,
            arm_id=arm_id,
            scheduled_decision_utc=scheduled_decision_utc,
            observed_at_utc=scheduled_decision_utc,
            feature_cutoff_utc=scheduled_decision_utc,
            code_freeze_sha=str(context.get("code_freeze_sha", "UNKNOWN")),
            config_digest=str(context.get("config_digest", "UNKNOWN")),
            cost_regime_digest=str(context.get("cost_regime_digest", "UNKNOWN")),
            blocked_reason=blocked_reason,
        )

    return builder


def heartbeat(
    runtime_root: str,
    family_ids: Tuple[str, ...],
    now_utc: str,
    *,
    lookback_from_utc: str = "2020-01-01T00:00:00Z",
) -> Dict[str, Any]:
    """G5 heartbeat: last scheduled event, last completed event, bytes."""
    last_scheduled: Optional[Dict[str, str]] = None
    last_completed: Optional[Dict[str, str]] = None
    total_bytes = 0
    per_family: Dict[str, Dict[str, Any]] = {}

    for family_id in family_ids:
        schedule_for(family_id)
        path = ledger.ledger_path(runtime_root, family_id)
        records = ledger.scan_events(path)
        size = ledger.byte_count(path)
        total_bytes += size
        family_last_scheduled: Optional[str] = None
        if pending_decisions(family_id, lookback_from_utc, now_utc):
            family_last_scheduled = pending_decisions(family_id, lookback_from_utc, now_utc)[-1]
        if family_last_scheduled is not None and (
            last_scheduled is None or family_last_scheduled > last_scheduled["scheduled_decision_utc"]
        ):
            last_scheduled = {
                "family_id": family_id,
                "scheduled_decision_utc": family_last_scheduled,
            }
        if records:
            latest = max(records, key=lambda r: r["scheduled_decision_utc"])
            if last_completed is None or latest["scheduled_decision_utc"] > last_completed["scheduled_decision_utc"]:
                last_completed = {
                    "family_id": family_id,
                    "event_id": latest["event_id"],
                    "scheduled_decision_utc": latest["scheduled_decision_utc"],
                    "data_status": latest.get("data_status"),
                }
        per_family[family_id] = {
            "ledger_path": path,
            "record_count": len(records),
            "bytes": size,
            "digest": ledger.ledger_digest(path),
        }

    return {
        "now_utc": now_utc,
        "last_scheduled_event": last_scheduled,
        "last_completed_event": last_completed,
        "ledger_byte_count": total_bytes,
        "per_family": per_family,
    }
