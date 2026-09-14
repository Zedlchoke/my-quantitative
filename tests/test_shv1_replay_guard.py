"""Tests for research/shadow_v1/start_guard.py (condition C2).

The forward-only rule must be CODE-ENFORCED: a decision before
SHADOW_START_UTC is refused in the PROSPECTIVE namespace (the default),
a missing SHADOW_START_UTC refuses everything in PROSPECTIVE, and the
same pre-start decision is allowed ONLY with the explicit
REPLAY_NOT_PROSPECTIVE namespace — whose bytes land ONLY under
``<runtime_root>/replay_not_prospective/`` while prospective bytes land
ONLY under ``<runtime_root>/ledgers/``. Mixing attempts fail closed.
"""

import datetime as dt
import os
from pathlib import Path

import pytest

from research.shadow_v1 import events, ledger, risk, scheduler, start_guard
from research.shadow_v1 import executor as executor_module
from tests.test_shv1_executor import InMemoryFeed, ScriptedAdapter

D1 = "2026-06-01T00:00:00Z"
D2 = "2026-06-08T00:00:00Z"
FAMILY_ID = ScriptedAdapter.FAMILY_ID


def iso(moment):
    return moment.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def shift(stamp, **kwargs):
    d = dt.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=dt.timezone.utc
    )
    return iso(d + dt.timedelta(**kwargs))


def make_feed():
    feed = InMemoryFeed()
    import datetime as _dt

    start_open = _dt.datetime(2026, 5, 28, tzinfo=_dt.timezone.utc)
    end_open = _dt.datetime(2026, 6, 8, 2, 0, tzinfo=_dt.timezone.utc)
    count = int((end_open - start_open).total_seconds() // 900) + 8
    feed.add_bar_series("BTCUSDT", start_open, count, 50_000.0)
    return feed


def make_config(script, namespace=None):
    cfg = {
        "code_freeze_sha": "shv1-replay-guard-tests-code-freeze",
        "tick_size": 0.01,
        "cost_books": {
            "LINEAGE_COST": {"fee_rate": 0.0004, "slippage_ticks": 1.0},
            "CURRENT_CONSERVATIVE_COST": {"fee_rate": 0.0005, "slippage_ticks": 1.0},
        },
        "caps": risk.FamilyRiskCaps(
            family_id=FAMILY_ID,
            target_gross=0.9,
            hard_gross_cap=1.5,
            hard_abs_net_cap=1.0,
        ),
        "snapshot_spec": {
            "bars": {
                "symbols": ["BTCUSDT"],
                "interval": "15m",
                "lookback_seconds": 2 * 86400,
            }
        },
        "feature_cutoff_offset_seconds": 900.0,
        "schedule": scheduler.SCHEDULE_WEEKLY_MONDAY_0000Z,
        "adapter": ScriptedAdapter(script),
    }
    if namespace is not None:
        cfg["namespace"] = namespace
    return cfg


# ----------------------------------------------------------------------
# assert_forward unit semantics
# ----------------------------------------------------------------------
def test_decision_before_shadow_start_refused_in_prospective():
    with pytest.raises(start_guard.StartGuardError):
        start_guard.assert_forward(D1, D2, start_guard.NAMESPACE_PROSPECTIVE)


def test_decision_before_shadow_start_refused_by_default_namespace():
    # PROSPECTIVE is the default: silence must never mean replay
    with pytest.raises(start_guard.StartGuardError):
        start_guard.assert_forward(D1, D2)


def test_missing_shadow_start_refused_in_prospective():
    with pytest.raises(start_guard.StartGuardError):
        start_guard.assert_forward(D2, None, start_guard.NAMESPACE_PROSPECTIVE)


def test_same_decision_allowed_only_with_explicit_replay_namespace():
    start_guard.assert_forward(D1, D2, start_guard.NAMESPACE_REPLAY)  # no raise
    with pytest.raises(start_guard.StartGuardError):
        start_guard.assert_forward(D1, D2, "SOME_OTHER_NAMESPACE")


def test_unknown_namespace_refused_fail_closed():
    with pytest.raises(start_guard.StartGuardError):
        start_guard.assert_forward(D1, D2, "SNEAKY_REPLAY")


def test_boundary_decision_equal_to_shadow_start_allowed():
    start_guard.assert_forward(D2, D2, start_guard.NAMESPACE_PROSPECTIVE)


def test_assert_forward_accepts_aware_datetimes():
    moment = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)
    start = dt.datetime(2026, 6, 8, tzinfo=dt.timezone.utc)
    with pytest.raises(start_guard.StartGuardError):
        start_guard.assert_forward(moment, start, start_guard.NAMESPACE_PROSPECTIVE)
    start_guard.assert_forward(start, start, start_guard.NAMESPACE_PROSPECTIVE)


def test_naive_datetime_refused():
    naive = dt.datetime(2026, 6, 1)
    with pytest.raises(start_guard.StartGuardError):
        start_guard.assert_forward(naive, D2, start_guard.NAMESPACE_PROSPECTIVE)


# ----------------------------------------------------------------------
# ledger root separation
# ----------------------------------------------------------------------
def test_ledger_roots_visibly_separated(tmp_path):
    root = str(tmp_path)
    pro = start_guard.prospective_ledger_root(root)
    rep = start_guard.replay_ledger_root(root)
    assert pro == os.path.join(root, "ledgers")
    assert rep == os.path.join(root, "replay_not_prospective")
    assert pro != rep
    # neither root may contain the other
    start_guard.assert_roots_disjoint(pro, rep)
    assert not rep.startswith(pro.rstrip(os.sep) + os.sep)
    assert not pro.startswith(rep.rstrip(os.sep) + os.sep)


def test_ledger_root_unknown_namespace_refused(tmp_path):
    with pytest.raises(start_guard.StartGuardError):
        start_guard.ledger_root(str(tmp_path), "NOT_A_NAMESPACE")


# ----------------------------------------------------------------------
# end-to-end: replay bytes land ONLY under replay_not_prospective/
# ----------------------------------------------------------------------
def test_replay_executor_writes_only_under_replay_root(tmp_path):
    exec_ = executor_module.ForwardExecutor(
        FAMILY_ID,
        make_config({D1: {"BTCUSDT": 0.9}}, namespace=start_guard.NAMESPACE_REPLAY),
        str(tmp_path),
        make_feed(),
        D2,  # replay may declare a start too, but it is not binding
    )
    result = exec_.run_due(shift(D1, minutes=16), from_utc=D1)
    assert result["emitted"] == 1
    replay_file = os.path.join(
        start_guard.replay_ledger_root(str(tmp_path)),
        f"{FAMILY_ID}{ledger.LEDGER_SUFFIX}",
    )
    assert os.path.exists(replay_file)
    records = ledger.scan_events(replay_file)
    assert len(records) == 1
    assert records[0]["event_id"] == events.compute_event_id(
        FAMILY_ID, ScriptedAdapter.ARM_ID, D1
    )
    # the prospective ledger directory was never created / never written
    assert not os.path.exists(start_guard.prospective_ledger_root(str(tmp_path)))


def test_replay_namespace_runs_pre_start_without_shadow_start(tmp_path):
    exec_ = executor_module.ForwardExecutor(
        FAMILY_ID,
        make_config({D1: {"BTCUSDT": 0.9}}, namespace=start_guard.NAMESPACE_REPLAY),
        str(tmp_path),
        make_feed(),
        None,  # no SHADOW_START_UTC at all: fine for an explicit replay
    )
    result = exec_.run_due(shift(D1, minutes=16), from_utc=D1)
    assert result["emitted"] == 1


def test_replay_requires_explicit_from_utc_fail_closed(tmp_path):
    exec_ = executor_module.ForwardExecutor(
        FAMILY_ID,
        make_config({D1: {"BTCUSDT": 0.9}}, namespace=start_guard.NAMESPACE_REPLAY),
        str(tmp_path),
        make_feed(),
        None,
    )
    with pytest.raises(executor_module.ExecutorError):
        exec_.run_due(shift(D1, minutes=16))


def test_prospective_and_replay_bytes_never_mix(tmp_path):
    pro_exec = executor_module.ForwardExecutor(
        FAMILY_ID,
        make_config({D2: {"BTCUSDT": 0.5}}),
        str(tmp_path),
        make_feed(),
        D2,
    )
    rep_exec = executor_module.ForwardExecutor(
        FAMILY_ID,
        make_config({D1: {"BTCUSDT": 0.9}}, namespace=start_guard.NAMESPACE_REPLAY),
        str(tmp_path),
        make_feed(),
        D2,
    )
    rep_result = rep_exec.run_due(shift(D1, minutes=16), from_utc=D1)
    pro_result = pro_exec.run_due(shift(D2, minutes=16))
    assert rep_result["emitted"] == 1
    assert pro_result["emitted"] == 1

    replay_ids = {
        r["event_id"]
        for r in ledger.scan_events(
            os.path.join(
                start_guard.replay_ledger_root(str(tmp_path)),
                f"{FAMILY_ID}{ledger.LEDGER_SUFFIX}",
            )
        )
    }
    pro_path = os.path.join(
        start_guard.prospective_ledger_root(str(tmp_path)),
        f"{FAMILY_ID}{ledger.LEDGER_SUFFIX}",
    )
    pro_ids = {r["event_id"] for r in ledger.scan_events(pro_path)}
    assert len(replay_ids) == 1 and len(pro_ids) == 1
    assert replay_ids.isdisjoint(pro_ids)
    # the dashboard-facing prospective root contains NO replay bytes
    root_dir = start_guard.prospective_ledger_root(str(tmp_path))
    for name in os.listdir(root_dir):
        assert not name.startswith("replay")
    start_guard.assert_roots_disjoint(
        start_guard.prospective_ledger_root(str(tmp_path)),
        start_guard.replay_ledger_root(str(tmp_path)),
    )


def test_prospective_executor_refuses_pre_start_and_writes_nothing(tmp_path):
    exec_ = executor_module.ForwardExecutor(
        FAMILY_ID,
        make_config({D1: {"BTCUSDT": 0.9}}),
        str(tmp_path),
        make_feed(),
        D2,
    )
    with pytest.raises(start_guard.StartGuardError):
        exec_.run_due(shift(D2, minutes=16), from_utc=D1)
    pro_root = start_guard.prospective_ledger_root(str(tmp_path))
    if os.path.exists(pro_root):
        assert os.listdir(pro_root) == []
