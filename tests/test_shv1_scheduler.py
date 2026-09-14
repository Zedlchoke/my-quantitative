"""Scheduler clock exactness + restart/idempotency safety (plan G5)."""

import json

import pytest

from research.shadow_v1 import events, ledger, no_order, scheduler
from research.shadow_v1.data_feed import DataBlocked

WEEKLY = "ILLIQ-AMIHUD-28D-W"
DAILY = "XSECT-FUND-CARRY-7D"

CODE_SHA = "code-freeze-sha-1"
CONFIG_DIGEST = "config-digest-1"
COST_DIGEST = "ab524d0ef974ef3ee23236ec89ba1df50ba52c37d5de973429349291aef44d65"


def make_executor(calls, fail_before=None):
    """Executor returning a valid plan section 8 record per decision."""

    def executor(family_id, scheduled_decision_utc, event_id):
        if fail_before is not None and scheduled_decision_utc < fail_before:
            raise DataBlocked("required 15m bars not yet available")
        calls.append(scheduled_decision_utc)
        return events.build_event(
            family_id=family_id,
            arm_id=family_id,
            scheduled_decision_utc=scheduled_decision_utc,
            observed_at_utc=scheduled_decision_utc,
            feature_cutoff_utc=scheduled_decision_utc,
            data_snapshot_digest="snap-" + scheduled_decision_utc,
            code_freeze_sha=CODE_SHA,
            config_digest=CONFIG_DIGEST,
            cost_regime_digest=COST_DIGEST,
            eligible_symbols=["ETHUSDT"],
            rejected_symbols_with_reason={},
            signal_values={"ETHUSDT": 0.001},
            target_weights={"ETHUSDT": 0.1},
            previous_weights={},
            virtual_fill_events=[],
            fee=0.0,
            slippage=0.0,
            funding_cashflow=0.0,
            price_pnl=0.0,
            total_pnl=0.0,
            cash=100_000.0,
            equity=100_000.0,
            gross=0.0,
            net=0.0,
            btc_beta=0.0,
            no_order_proof={
                "emitted_action_types": ["TARGET_INTENT"],
                "scan_digest": no_order.package_scan_digest("research/shadow_v1"),
            },
        )

    return executor


def test_weekly_monday_clock_exact():
    got = scheduler.pending_decisions(WEEKLY, "2026-01-01T00:00:00Z", "2026-01-20T00:00:00Z")
    assert got == [
        "2026-01-05T00:00:00Z",
        "2026-01-12T00:00:00Z",
        "2026-01-19T00:00:00Z",
    ]
    # from exactly on a Monday 00:00Z includes it; to excludes the boundary
    got2 = scheduler.pending_decisions(WEEKLY, "2026-01-05T00:00:00Z", "2026-01-12T00:00:00Z")
    assert got2 == ["2026-01-05T00:00:00Z"]
    # 2026-12-28 is a Monday; year boundary handled
    got3 = scheduler.pending_decisions(WEEKLY, "2026-12-28T00:00:00Z", "2027-01-11T00:00:00Z")
    assert got3 == ["2026-12-28T00:00:00Z", "2027-01-04T00:00:00Z"]


def test_daily_clock_exact_and_premade_families():
    got = scheduler.pending_decisions(DAILY, "2026-01-01T00:00:00Z", "2026-01-04T00:00:00Z")
    assert got == [
        "2026-01-01T00:00:00Z",
        "2026-01-02T00:00:00Z",
        "2026-01-03T00:00:00Z",
    ]
    assert scheduler.schedule_for("BASISLV-PREMFADE-28D") == "weekly_monday_0000z"
    with pytest.raises(scheduler.SchedulerError):
        scheduler.pending_decisions("NOT-A-FAMILY", "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")


def test_month_end_weekend_boundaries():
    # Feb 2026: Mondays are 2, 9, 16, 23
    got = scheduler.pending_decisions(WEEKLY, "2026-02-01T00:00:00Z", "2026-03-01T00:00:00Z")
    assert got == [
        "2026-02-02T00:00:00Z",
        "2026-02-09T00:00:00Z",
        "2026-02-16T00:00:00Z",
        "2026-02-23T00:00:00Z",
    ]


def test_duplicate_launch_zero_new_events_byte_identical(tmp_path):
    root = str(tmp_path)
    calls = []
    executor = make_executor(calls)
    first = scheduler.run_once(
        WEEKLY, "2026-01-20T00:00:00Z", executor, root,
        from_utc="2026-01-01T00:00:00Z", to_utc="2026-01-20T00:00:00Z",
    )
    assert first["emitted"] == 3 and first["skipped_existing"] == 0
    path = ledger.ledger_path(root, WEEKLY)
    digest = ledger.ledger_digest(path)
    size = ledger.byte_count(path)

    second = scheduler.run_once(
        WEEKLY, "2026-01-20T00:00:00Z", executor, root,
        from_utc="2026-01-01T00:00:00Z", to_utc="2026-01-20T00:00:00Z",
    )
    assert second["emitted"] == 0
    assert second["skipped_existing"] == 3
    assert ledger.ledger_digest(path) == digest
    assert ledger.byte_count(path) == size
    assert len(calls) == 3  # executor not re-invoked for committed events
    ids = ledger.event_ids(path)
    assert len(ids) == 3


def test_late_data_emits_data_blocked_and_retry_resumes_same_event_id(tmp_path):
    root = str(tmp_path)
    calls = []
    blocking_executor = make_executor(calls, fail_before="2026-01-12T00:00:00Z")
    out = scheduler.run_once(
        WEEKLY, "2026-01-20T00:00:00Z", blocking_executor, root,
        from_utc="2026-01-05T00:00:00Z", to_utc="2026-01-20T00:00:00Z",
    )
    # first decision blocked, remaining two emitted
    assert out["blocked"] == 1 and out["emitted"] == 2
    path = ledger.ledger_path(root, WEEKLY)
    records = ledger.scan_events(path)
    by_ts = {r["scheduled_decision_utc"]: r for r in records}
    blocked_rec = by_ts["2026-01-05T00:00:00Z"]
    assert blocked_rec["data_status"] == "DATA_BLOCKED"
    assert blocked_rec["target_weights"] == {}
    assert blocked_rec["equity"] is None
    expected_id = events.compute_event_id(WEEKLY, WEEKLY, "2026-01-05T00:00:00Z")
    assert blocked_rec["event_id"] == expected_id
    assert blocked_rec["data_snapshot_digest"].startswith("DATA_BLOCKED:")

    digest = ledger.ledger_digest(path)
    # retry after "data arrives": same window, executor would now succeed
    retry = scheduler.run_once(
        WEEKLY, "2026-01-20T00:00:00Z", make_executor([]), root,
        from_utc="2026-01-05T00:00:00Z", to_utc="2026-01-20T00:00:00Z",
    )
    assert retry["emitted"] == 0 and retry["skipped_existing"] == 3
    assert ledger.ledger_digest(path) == digest
    # same event id, never duplicated
    assert sum(1 for r in ledger.scan_events(path) if r["event_id"] == expected_id) == 1


def test_heartbeat_fields(tmp_path):
    root = str(tmp_path)
    scheduler.run_once(
        WEEKLY, "2026-01-20T00:00:00Z", make_executor([]), root,
        from_utc="2026-01-05T00:00:00Z", to_utc="2026-01-20T00:00:00Z",
    )
    hb = scheduler.heartbeat(
        root, (WEEKLY, DAILY, "BASISLV-PREMFADE-28D"), "2026-01-20T00:00:00Z"
    )
    assert set(hb) >= {
        "last_scheduled_event", "last_completed_event", "ledger_byte_count"
    }
    assert hb["last_scheduled_event"]["scheduled_decision_utc"] == "2026-01-19T00:00:00Z"
    assert hb["last_completed_event"]["family_id"] == WEEKLY
    assert hb["last_completed_event"]["scheduled_decision_utc"] == "2026-01-19T00:00:00Z"
    assert hb["ledger_byte_count"] > 0
    assert hb["per_family"][WEEKLY]["record_count"] == 3
    assert hb["per_family"][DAILY]["record_count"] == 0


def test_run_once_default_window_resumes_from_last_ledger_event(tmp_path):
    root = str(tmp_path)
    calls = []
    scheduler.run_once(
        DAILY, "2026-01-03T00:00:00Z", make_executor(calls), root,
        from_utc="2026-01-01T00:00:00Z", to_utc="2026-01-03T00:00:00Z",
    )
    assert len(calls) == 2
    # a later run with no explicit window resumes from the last ledger
    # event (which is reconsidered but skipped idempotently)
    calls2 = []
    scheduler.run_once(
        DAILY, "2026-01-05T00:00:00Z", make_executor(calls2), root,
        to_utc="2026-01-05T00:00:00Z",
    )
    assert calls2 == ["2026-01-03T00:00:00Z", "2026-01-04T00:00:00Z"]


def test_scheduler_rejects_executor_event_id_mismatch(tmp_path):
    root = str(tmp_path)

    def rogue_executor(family_id, scheduled_decision_utc, event_id):
        rec = events.build_data_blocked_event(
            family_id=family_id,
            arm_id=family_id,
            scheduled_decision_utc=scheduled_decision_utc,
            observed_at_utc=scheduled_decision_utc,
            feature_cutoff_utc=scheduled_decision_utc,
            code_freeze_sha="x", config_digest="y", cost_regime_digest="z",
            blocked_reason="x",
        )
        rec["event_id"] = "f" * 32
        return rec

    with pytest.raises((scheduler.SchedulerError, events.EventContractError)):
        scheduler.run_once(
            DAILY, "2026-01-02T00:00:00Z", rogue_executor, root,
            from_utc="2026-01-01T00:00:00Z", to_utc="2026-01-02T00:00:00Z",
        )
    # nothing was committed by the rogue executor
    assert ledger.scan_events(ledger.ledger_path(root, DAILY)) == []
