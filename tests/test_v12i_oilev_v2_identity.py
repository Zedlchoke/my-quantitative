"""V12 I lane -- frozen-identity tests for OILEV-V2 (deliverable 3/7).

Pins every identity field of the FREEZE V2 identity contract
(``selection_freeze.json`` v2; integration commit
``39fc8821a5c8dbe9c2fd998edc3956ad6a02ec8f``, reissued by A1 before any
scored metric exists): family/strategy ids, direction
(``long_short_beta_neutral`` on all three arms), the digest-bearing
``arm_config_id`` (``28D-FLOW`` / ``56D-STOCK`` / ``28D-FLOW-INV``),
benchmark exclusion, funding sign convention, matrix cohort hint, window,
and the per-arm ``config`` dicts (verbatim against the recorded freeze
cells -- unchanged between v1 and v2).

Root cause of the previously documented 0/3 mismatch: freeze V1 recorded
``arm_config_digest`` WITHOUT the identity fields (arm_config_id /
direction / strategy_id), so no published payload could reproduce it.
V2 publishes the full identity contract;
``test_arm_config_digest_reproduces_freeze`` is a STRICT assertion and
passes 3/3 against the hard-coded v2 digests (the worktree's local copy
of ``selection_freeze.json`` is still v1 and is deliberately left
untouched; A1's integration carries v2).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.v12.families.oilev_v2.plugin import OilevV2Plugin
from research.v12.families.oilev_v2.strategy import (
    ANCHOR_ARM,
    ARM_CONFIG_IDS,
    ARM_IDS,
    ARM_ROLES,
    BENCHMARK_SYMBOL,
    CONTROL_ARM,
    FAMILY_ID,
    FROZEN_ARM_CONFIG_DIGESTS,
    MATRIX_COHORT_HINT,
    NEIGHBOUR_ARM,
    STRATEGY_ID,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    frozen_arm_config,
    frozen_arm_digest_report,
    frozen_identity,
    iso_utc,
    stamp_calendar,
)
from research.v11.publication_identity import arm_config_digest

FREEZE_PATH = Path("research/control/v12_run/selection_freeze.json")
SPEC_PATH = Path(
    "research/control/v12_run/selection_freeze_specs/"
    "A12-V12-OILEVER-V2-DELEV.json"
)

#: FREEZE V2 identity contract (hard-coded frozen constants; provenance:
#: selection_freeze.json v2 / integration commit
#: 39fc8821a5c8dbe9c2fd998edc3956ad6a02ec8f, reissued by A1 before any
#: scored metric exists; this worktree's local freeze copy is still v1 and
#: is deliberately left untouched).
V2_ARM_CONFIG_IDS: dict[str, str] = {
    "OILEV-V2-28D-FLOW-W": "28D-FLOW",
    "OILEV-V2-56D-STOCK-W": "56D-STOCK",
    "OILEV-V2-28D-FLOW-W-INV": "28D-FLOW-INV",
}
V2_ARM_CONFIG_DIGESTS: dict[str, str] = {
    "OILEV-V2-28D-FLOW-W": (
        "2d9c56443e3e7eff62b1013c373f738a2eb2a2f8be1b34de83e6d1fd37af8454"
    ),
    "OILEV-V2-56D-STOCK-W": (
        "0ba51b43a8b4adeb683f4eaf9ddfc3a107de9bee9f6f1af9a93862a7f6f55562"
    ),
    "OILEV-V2-28D-FLOW-W-INV": (
        "e57b26fe1110da8bf82ddc00feb038087bed8f72baeb81c910a7c065a1f8de37"
    ),
}
V2_DIRECTION = "long_short_beta_neutral"  # all three arms


def _freeze_family_cells() -> dict[str, dict]:
    with open(FREEZE_PATH, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    cells = [c for c in doc["frozen_cells"] if c["family"] == FAMILY_ID]
    assert len(cells) == 3
    return {c["arm_id"]: c for c in cells}


def test_identity_fields_pinned_per_arm() -> None:
    cells = _freeze_family_cells()
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        cell = cells[arm_id]
        assert identity.family_id == FAMILY_ID
        assert identity.strategy_id == STRATEGY_ID
        # freeze v2: the digest-bearing arm_config_id (NOT the v1 role)
        assert identity.arm_config_id == V2_ARM_CONFIG_IDS[arm_id]
        assert identity.arm_config_id == ARM_CONFIG_IDS[arm_id]
        assert ARM_ROLES[arm_id] == cell["role"]  # descriptive role, v1 record
        assert identity.arm_id == arm_id
        assert identity.benchmark_symbols_excluded == (BENCHMARK_SYMBOL,)
        assert identity.funding_sign_convention == "LONG_PAYS_POSITIVE_RATE"
        assert identity.matrix_cohort_hint == MATRIX_COHORT_HINT == "v12"
        assert identity.window_start_iso == WINDOW_START_ISO
        assert identity.window_end_iso == WINDOW_END_ISO
        assert identity.window_start_iso == "2025-08-22T00:00:00Z"
        assert identity.window_end_iso == "2026-08-21T00:00:00Z"


def test_direction_pinned_on_all_three_arms() -> None:
    from research.v11.families.oilever_delev.strategy import DIRECTION as V11_DIRECTION

    for arm_id in ARM_IDS:
        assert frozen_identity(arm_id).direction == V2_DIRECTION
        assert frozen_identity(arm_id).direction == V11_DIRECTION
        assert frozen_identity(arm_id).direction == "long_short_beta_neutral"


def test_arm_configs_match_freeze_json_verbatim() -> None:
    cells = _freeze_family_cells()
    for arm_id in ARM_IDS:
        assert frozen_arm_config(arm_id) == cells[arm_id]["config"]
        assert frozen_identity(arm_id).config == cells[arm_id]["config"]
    # the recorded per-arm keys are exactly the frozen contract vocabulary
    expected_keys = {
        "book",
        "weight_cap_abs",
        "min_eligible",
        "leg_names",
        "beta_hedge",
        "scale_rule",
        "window",
        "feature",
        "formation_days",
    }
    assert set(frozen_arm_config(ANCHOR_ARM)) == expected_keys
    assert set(frozen_arm_config(NEIGHBOUR_ARM)) == expected_keys
    assert set(frozen_arm_config(CONTROL_ARM)) == expected_keys | {"sign"}


def test_arm_feature_semantics_match_the_freeze() -> None:
    from research.v12.families.oilev_v2.strategy import arm_feature_spec

    assert arm_feature_spec(ANCHOR_ARM) == ("oi_flow", 28, False)
    assert arm_feature_spec(NEIGHBOUR_ARM) == ("oi_stock", 56, False)
    assert arm_feature_spec(CONTROL_ARM) == ("oi_flow", 28, True)


def test_recorded_digests_are_the_v2_frozen_constants() -> None:
    """The module's freeze digests are exactly the hard-coded v2 constants.

    The worktree's local ``selection_freeze.json`` is still V1 (its digests
    were computed without the identity fields and are irreproducible); the
    binding record is V2 (integration commit 39fc8821), pinned here as
    hard-coded constants with the module constants cross-checked against
    them so silent edits fail this test.
    """
    assert dict(FROZEN_ARM_CONFIG_DIGESTS) == dict(V2_ARM_CONFIG_DIGESTS)
    assert dict(ARM_CONFIG_IDS) == dict(V2_ARM_CONFIG_IDS)


def test_arm_digests_pairwise_distinct() -> None:
    report = frozen_arm_digest_report()
    computed = [report[arm]["computed_from_identity"] for arm in ARM_IDS]
    recorded = [report[arm]["recorded_in_freeze"] for arm in ARM_IDS]
    assert len(set(computed)) == 3, "computed arm digests must be pairwise distinct"
    assert len(set(recorded)) == 3, "recorded freeze digests must be pairwise distinct"
    # changing any score-affecting identity field must move the digest
    base = frozen_identity(ANCHOR_ARM)
    tweaked_config = dict(base.config)
    tweaked_config["formation_days"] = 29
    from research.adapter_v10.protocol import StrategyIdentity

    tweaked = StrategyIdentity(
        strategy_id=base.strategy_id,
        family_id=base.family_id,
        arm_config_id=base.arm_config_id,
        direction=base.direction,
        window_start_iso=base.window_start_iso,
        window_end_iso=base.window_end_iso,
        benchmark_symbols_excluded=base.benchmark_symbols_excluded,
        funding_sign_convention=base.funding_sign_convention,
        arm_id=base.arm_id,
        config=tweaked_config,
    )
    assert arm_config_digest(tweaked, arm_id=ANCHOR_ARM) != report[ANCHOR_ARM][
        "computed_from_identity"
    ]


def test_arm_config_digest_reproduces_freeze_v2() -> None:
    """STRICT: recomputed arm_config_digest equals the freeze-v2 digest 3/3.

    ``arm_config_digest(StrategyIdentity(strategy_id, family_id,
    arm_config_id, direction, window, benchmark exclusion, funding sign,
    matrix_cohort_hint, config=<recorded config verbatim>, arm_id),
    arm_id=...)`` must equal the v2 recorded digest for every arm.
    """
    report = frozen_arm_digest_report()
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        computed = arm_config_digest(identity, arm_id=arm_id)
        assert computed == V2_ARM_CONFIG_DIGESTS[arm_id], arm_id
        assert report[arm_id]["match"] is True, arm_id


def test_schedule_is_52_weekly_monday_stamps() -> None:
    stamps = stamp_calendar()
    assert len(stamps) == 52
    from datetime import datetime, timezone

    first = datetime.fromtimestamp(stamps[0] / 1e9, tz=timezone.utc)
    assert first.weekday() == 0
    assert iso_utc(stamps[0]) == "2025-08-25T00:00:00Z"
    assert iso_utc(stamps[-1]) == "2026-08-17T00:00:00Z"
    assert all(
        stamps[i + 1] - stamps[i] == 7 * 86_400_000_000_000 for i in range(51)
    )


def test_first_stamp_warmup_bound_is_2025_08_25() -> None:
    stamps = stamp_calendar()
    from research.v12.families.oilev_v2.strategy import (
        FIRST_STAMP_ISO,
        parse_iso_utc,
    )

    assert iso_utc(stamps[0]) == FIRST_STAMP_ISO == "2025-08-25T00:00:00Z"
    assert stamps[0] == parse_iso_utc(FIRST_STAMP_ISO)


def _tiny_plugin(arm_id: str) -> OilevV2Plugin:
    from research.v11.families.oilever_delev.strategy import Bar

    day = 86_400_000_000_000
    base = 1_750_368_000_000_000_000  # 2025-06-20T00:00:00Z (ns)
    oi = {
        f"SYM{i:02d}": tuple(
            (base + d * day + 23 * 3600 * 10**9, 1_000_000.0 + i * 100.0 + d)
            for d in range(120)
        )
        for i in range(12)
    }
    stamp = stamp_calendar()[0]
    bars = {
        sym: (
            Bar(
                ts_event_ns=stamp + 900_000_000_000,
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
            ),
            Bar(
                ts_event_ns=stamp + 1_800_000_000_000,
                open=100.5,
                high=101.5,
                low=100.0,
                close=101.0,
            ),
        )
        for sym in oi
    }
    bars["BTCUSDT"] = bars["SYM00"]
    return OilevV2Plugin(
        arm_id=arm_id, oi_by_symbol=oi, bars_by_symbol=bars
    )


def test_plugin_carries_the_frozen_identity() -> None:
    for arm_id in ARM_IDS:
        plugin = _tiny_plugin(arm_id)
        assert plugin.identity() == frozen_identity(arm_id)
        assert plugin.identity().matrix_cohort_hint == "v12"


def test_plugin_universe_excludes_benchmark_and_floors_breadth() -> None:
    plugin = _tiny_plugin(ANCHOR_ARM)
    universe = plugin.tradeable_universe()
    assert "BTCUSDT" not in universe
    assert "BTCUSDT" in plugin.benchmark_context_symbols()
    assert len(universe) == 12
    assert plugin.minimum_tradeable_names() == 9
    baseline = plugin.baseline_stress()
    assert baseline.is_baseline
    assert len(plugin.universe(baseline)) == 12
    from research.adapter_v10.protocol import StressSpec

    drop_eleven = StressSpec(name="drop_too_many", drop_symbols=tuple(sorted(universe)[:4]))
    with pytest.raises(Exception):
        # 12 - 4 = 8 survivors < frozen min_eligible(9) must fail closed
        plugin.universe(drop_eleven)


def test_plugin_folds_pinned_labels_and_dropped_fold_probe() -> None:
    plugin = _tiny_plugin(ANCHOR_ARM)
    baseline = plugin.baseline_stress()
    instants = list(plugin.schedule().instants)
    folds = plugin.folds(stress=baseline, instants=instants)
    assert [f.label for f in folds] == ["F0", "F1", "F2"]
    assert all(f.purge_days == 1 for f in folds)
    assert all(not f.dropped for f in folds)
    covered = [i for f in folds for i in f.instants]
    assert sorted(covered) == sorted(set(covered))  # no overlap
    from research.adapter_v10.protocol import StressSpec

    probed = plugin.folds(
        stress=StressSpec(name="drop_one_fold", dropped_fold_index=0),
        instants=instants,
    )
    assert probed[0].dropped and not probed[1].dropped and not probed[2].dropped


def test_plugin_cost_model_uses_frozen_v10_floors() -> None:
    from research.v12.families.oilev_v2.strategy import (
        ADVERSE_TICK_SLIP_FLOOR,
        TAKER_FEE_FLOOR_BPS,
    )

    plugin = _tiny_plugin(ANCHOR_ARM)
    model = plugin.cost_model()
    assert model.taker_fee_bps == TAKER_FEE_FLOOR_BPS == 5.0
    assert model.adverse_tick_slip_floor == ADVERSE_TICK_SLIP_FLOOR == 1
