"""V13 I lane -- frozen identity, schedule and fold-contract tests for OITD.

Pins the frozen identity of family ``A13-V13-A8-OITD`` (selection freeze
``research/control/v13_run/selection_freeze_v13.json`` + mechanism
``research/proposals/v13/a8/OITD.md``/``.json``) exactly as the V12 lanes
pinned theirs:

* exactly three arms -- anchor ``OITD-28D``, neighbour ``OITD-56D``,
  causal negative control ``CTL-FLOW-ONLY`` -- with the frozen roles;
* per-arm ``arm_config_digest`` recomputed from the frozen identity via
  the frozen ``research.v11.publication_identity`` function equals the
  recorded constant, and the three digests are pairwise distinct;
* the weekly Monday 00:00:00Z decision clock (52 stamps, first
  2025-08-25, last 2026-08-17) and the pinned F0/F1/F2 fold calendar with
  the 1-stamp purge and force-flat boundaries;
* the plugin carries the frozen identity, the 19-name tradeable universe
  (benchmark excluded, context-only), the frozen V10 cost floors and the
  pinned fill-availability convention string;
* the causal control is constructed WITHOUT the OI/mark bundles and its
  signal layer refuses them outright (the numerator is deleted by
  construction, fail-closed).

No real data is required and no scored metric is computed.
"""

from __future__ import annotations

import pytest

from tests.v13i_oitd_world import (
    T1_DAY,
    T1_NS,
    SYMBOLS,
    bars_by_symbol,
    world_b,
)

from research.adapter_v10.protocol import ContractViolation, StressSpec
from research.contract_v10 import (
    ADVERSE_TICKS_SLIPPAGE_FLOOR_V10,
    TAKER_FEE_FLOOR_BPS_V10,
)
from research.v13.families.oitd.audits import (
    fold_end_instants,
    tradeable_universe_symbols,
)
from research.v13.families.oitd.plugin import OitdPlugin
from research.v13.families.oitd.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    ARM_ROLES,
    BENCHMARK_SYMBOL,
    CONTROL_ARM,
    FAMILY_ID,
    FOLD_WINDOWS,
    FROZEN_ARM_CONFIG_DIGESTS,
    NEIGHBOUR_ARM,
    PURGE_DAYS,
    STRATEGY_ID,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    arm_signal_spec,
    fold_assignments,
    frozen_arm_digest_report,
    frozen_identity,
    next_allowed_fill,
    purge_fold_members,
    stamp_calendar,
)
from research.v12.data_contract import REQUIRED_SYMBOLS

DAY_NS = 86_400_000_000_000


# --------------------------------------------------------------------- #
# Frozen identity vs the selection freeze
# --------------------------------------------------------------------- #
def test_family_and_arms_match_the_selection_freeze() -> None:
    assert FAMILY_ID == "A13-V13-A8-OITD"
    assert ARM_ROLES == {
        ANCHOR_ARM: "anchor",
        NEIGHBOUR_ARM: "neighbour",
        CONTROL_ARM: "causal_negative_control",
    }
    assert ARM_IDS == ("CTL-FLOW-ONLY", "OITD-28D", "OITD-56D")
    # exactly three arms: no post-hoc fourth arm exists
    assert len(ARM_IDS) == 3


def test_arm_signal_semantics_match_the_frozen_mechanism() -> None:
    # anchor: D = OI7 x MK / TO(28d), ranked ASCENDING (long lowest-D tercile)
    assert arm_signal_spec(ANCHOR_ARM) == ("unwind_duration", 28, True)
    # neighbour: identical construction with the 56d denominator
    assert arm_signal_spec(NEIGHBOUR_ARM) == ("unwind_duration", 56, True)
    # control: 28d turnover ALONE, DESCENDING (long highest-turnover tercile)
    assert arm_signal_spec(CONTROL_ARM) == ("turnover_only", 28, False)


def test_identity_fields_pinned_per_arm() -> None:
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        assert identity.strategy_id == STRATEGY_ID == "hyp_a13_v13_a8_oitd"
        assert identity.family_id == FAMILY_ID
        assert identity.direction == "long_short"
        assert identity.window_start_iso == WINDOW_START_ISO == "2025-08-22T00:00:00Z"
        assert identity.window_end_iso == WINDOW_END_ISO == "2026-08-21T00:00:00Z"
        assert identity.benchmark_symbols_excluded == ("BTCUSDT",)
        assert identity.funding_sign_convention == "LONG_PAYS_POSITIVE_RATE"
        assert identity.matrix_cohort_hint == "v13"
        assert identity.arm_id == arm_id
    assert frozen_identity(ANCHOR_ARM).arm_config_id == "28D"
    assert frozen_identity(NEIGHBOUR_ARM).arm_config_id == "56D"
    assert frozen_identity(CONTROL_ARM).arm_config_id == "FLOW-ONLY"
    with pytest.raises(ContractViolation):
        frozen_identity("NOT-AN-ARM")


def test_arm_config_digests_recompute_and_are_pairwise_distinct() -> None:
    report = frozen_arm_digest_report()
    assert len(report) == 3
    for arm_id in ARM_IDS:
        entry = report[arm_id]
        assert entry["match"] is True, arm_id
        assert entry["computed_from_identity"] == FROZEN_ARM_CONFIG_DIGESTS[arm_id]
    assert len(set(FROZEN_ARM_CONFIG_DIGESTS.values())) == 3


def test_universe_is_the_frozen_required_symbols_minus_btcusdt() -> None:
    universe = tradeable_universe_symbols()
    assert len(universe) == 19
    assert BENCHMARK_SYMBOL not in universe
    assert set(universe) == set(REQUIRED_SYMBOLS) - {BENCHMARK_SYMBOL}


# --------------------------------------------------------------------- #
# Decision clock and fold contract
# --------------------------------------------------------------------- #
def test_schedule_is_52_weekly_monday_midnight_stamps() -> None:
    calendar = stamp_calendar()
    assert len(calendar) == 52
    assert calendar[0] == T1_NS  # 2025-08-25T00:00:00Z
    assert len(set(calendar)) == 52
    assert calendar == tuple(sorted(calendar))
    week = 7 * DAY_NS
    assert all(b - a == week for a, b in zip(calendar, calendar[1:]))
    # last stamp 2026-08-17T00:00:00Z
    from research.v12.data_contract import ns_to_iso_utc

    assert ns_to_iso_utc(calendar[-1]) == "2026-08-17T00:00:00Z"


def test_fold_calendar_is_pinned_f0_f1_f2_with_one_stamp_purge() -> None:
    assert FOLD_WINDOWS == (
        ("F0", "2025-08-22", "2025-12-21"),
        ("F1", "2025-12-22", "2026-04-21"),
        ("F2", "2026-04-22", "2026-08-21"),
    )
    calendar = list(stamp_calendar())
    assignments = fold_assignments(calendar)
    assert [(label, len(members)) for _i, label, members in assignments] == [
        ("F0", 17),
        ("F1", 18),
        ("F2", 17),
    ]
    purged = purge_fold_members(assignments, purge_days=PURGE_DAYS)
    retained_total = 0
    for index, label, members, gaps in purged:
        assert label == f"F{index}"
        assert len(gaps) == PURGE_DAYS == 1
        # the purge strips exactly each fold's TRAILING stamp
        assert members == assignments[index][2][:-1]
        assert len(members) >= 15  # the frozen per-fold decision floor
        retained_total += len(members)
    assert retained_total == 52 - 3


def test_force_flat_boundaries_close_every_in_fold_book_before_the_next_fold() -> None:
    """Force-flat at fold boundaries: no book can straddle a boundary.

    The purge strips each fold's trailing stamp, so a book opened at the
    last retained stamp of a fold realises within one holding week -- at
    or before the fold's boundary instant, where the family force-flats.
    """
    purged = purge_fold_members(fold_assignments(list(stamp_calendar())))
    boundaries = fold_end_instants()
    assert [len(boundaries)] == [3]
    for boundary, (_index, label, members, _gaps) in zip(boundaries, purged):
        assert boundary % DAY_NS == 0  # midnight grid instant
        # the last retained stamp's one-week holding span ends at/before
        # the boundary: the force-flat there can never straddle folds
        assert members[-1] + 7 * DAY_NS <= boundary


def test_fold_end_instants_are_the_pinned_window_ends() -> None:
    from research.v13.families.oitd.strategy import parse_iso_utc

    assert fold_end_instants() == [
        int(parse_iso_utc("2025-12-21T00:00:00Z")),
        int(parse_iso_utc("2026-04-21T00:00:00Z")),
        int(parse_iso_utc("2026-08-21T00:00:00Z")),
    ]


# --------------------------------------------------------------------- #
# Plugin wiring
# --------------------------------------------------------------------- #
def test_plugin_carries_the_frozen_identity_and_universe() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    plugin = OitdPlugin(
        arm_id=ANCHOR_ARM,
        day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
        bars_by_symbol=bars_by_symbol(SYMBOLS, T1_NS),
        oi_by_symbol=dict(world["oi_by_symbol"]),
        mark_by_symbol=dict(world["mark_by_symbol"]),
    )
    identity = plugin.identity()
    assert identity == frozen_identity(ANCHOR_ARM)
    assert plugin.tradeable_universe() == tuple(sorted(SYMBOLS))
    assert plugin.minimum_tradeable_names() == 12
    assert set(plugin.benchmark_context_symbols()) == set(SYMBOLS) | {
        BENCHMARK_SYMBOL,
    }
    assert BENCHMARK_SYMBOL not in plugin.tradeable_universe()
    assert plugin.fold_count() == 3
    assert plugin.purge_days() == 1
    assert plugin.fold_label(0) == "F0"
    assert plugin.declared_execution_lag().startswith(
        "orders release at decision + 15m"
    )


def test_plugin_cost_model_uses_the_frozen_v10_floors() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    plugin = OitdPlugin(
        arm_id=ANCHOR_ARM,
        day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
        bars_by_symbol=bars_by_symbol(SYMBOLS, T1_NS),
        oi_by_symbol=dict(world["oi_by_symbol"]),
        mark_by_symbol=dict(world["mark_by_symbol"]),
        tick_sizes={sym: 0.01 for sym in SYMBOLS},
    )
    model = plugin.cost_model()
    assert float(model.taker_fee_bps) == float(TAKER_FEE_FLOOR_BPS_V10)
    assert int(model.adverse_tick_slip_floor) == int(ADVERSE_TICKS_SLIPPAGE_FLOOR_V10)
    baseline = plugin.baseline_stress()
    assert isinstance(baseline, StressSpec)
    assert baseline.name == "baseline"
    assert float(baseline.fee_multiplier) == 1.0


def test_plugin_folds_accept_a_dropped_fold_probe() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    plugin = OitdPlugin(
        arm_id=ANCHOR_ARM,
        day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
        bars_by_symbol=bars_by_symbol(SYMBOLS, T1_NS),
        oi_by_symbol=dict(world["oi_by_symbol"]),
        mark_by_symbol=dict(world["mark_by_symbol"]),
    )
    calendar = list(stamp_calendar())
    folds = plugin.folds(stress=plugin.baseline_stress(), instants=calendar)
    assert [f.label for f in folds] == ["F0", "F1", "F2"]
    assert all(not f.dropped for f in folds)
    probe = StressSpec(name="drop_one_fold", dropped_fold_index=0)
    dropped_folds = plugin.folds(stress=probe, instants=calendar)
    assert [f.dropped for f in dropped_folds] == [True, False, False]
    retained = plugin.decision_instants(stress=probe)
    assert not (set(retained) & set(dropped_folds[0].instants))
    assert len(retained) == sum(
        len(f.instants) for f in dropped_folds if not f.dropped
    )


# --------------------------------------------------------------------- #
# Causal control deletion (fail-closed)
# --------------------------------------------------------------------- #
def test_control_arm_refuses_oi_and_mark_bundles_at_construction() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    with pytest.raises(ContractViolation):
        OitdPlugin(
            arm_id=CONTROL_ARM,
            day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
            bars_by_symbol=bars_by_symbol(SYMBOLS, T1_NS),
            oi_by_symbol=dict(world["oi_by_symbol"]),
        )
    with pytest.raises(ContractViolation):
        OitdPlugin(
            arm_id=CONTROL_ARM,
            day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
            bars_by_symbol=bars_by_symbol(SYMBOLS, T1_NS),
            mark_by_symbol=dict(world["mark_by_symbol"]),
        )


def test_control_signal_refuses_oi_and_mark_inputs() -> None:
    from research.v13.families.oitd.strategy import signal_scores_at

    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    with pytest.raises(ContractViolation):
        signal_scores_at(
            CONTROL_ARM,
            day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
            stamp_ns=T1_NS,
            universe=world["universe"],
            oi_by_symbol=dict(world["oi_by_symbol"]),
        )
    with pytest.raises(ContractViolation):
        signal_scores_at(
            CONTROL_ARM,
            day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
            stamp_ns=T1_NS,
            universe=world["universe"],
            mark_by_symbol=dict(world["mark_by_symbol"]),
        )


def test_unknown_arm_ids_are_refused_everywhere() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    with pytest.raises(ContractViolation):
        OitdPlugin(
            arm_id="OITD-84D",
            day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
            bars_by_symbol=bars_by_symbol(SYMBOLS, T1_NS),
        )


def test_pinned_benchmark_never_enters_the_tradeable_universe() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    with pytest.raises(ContractViolation):
        OitdPlugin(
            arm_id=ANCHOR_ARM,
            day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
            bars_by_symbol=bars_by_symbol(SYMBOLS, T1_NS),
            oi_by_symbol=dict(world["oi_by_symbol"]),
            mark_by_symbol=dict(world["mark_by_symbol"]),
            benchmark_symbol="SYM00",  # the pinned leg is BTCUSDT, never else
        )


def test_next_allowed_fill_refuses_non_grid_and_negative_delays() -> None:
    from tests.v13i_oitd_world import execution_bars

    bars = execution_bars(T1_NS)
    with pytest.raises(ContractViolation):
        next_allowed_fill(bars, "SYM00", decision_ns=T1_NS + 60_000_000_000)
    with pytest.raises(ContractViolation):
        next_allowed_fill(bars, "SYM00", decision_ns=T1_NS, event_delay_events=-1)
