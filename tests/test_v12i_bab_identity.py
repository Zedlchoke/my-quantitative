"""Frozen-identity equality tests for A12-V12-BAB-LOWBETA (V12 I lane).

The binding contract is the selection-freeze V2 identity reissue
(integration commit ``39fc8821a5c8dbe9c2fd998edc3956ad6a02ec8f``: publish
full identity contract -- arm_config_id / direction / strategy_id -- and
reproducible digests; v1 digests superseded pre-score, 0 scored metrics
exist).  This worktree's copy of ``research/control/v12_run/selection_freeze.json``
still carries the SUPERSEDED v1 rows, so the v2 digest constants are
hard-coded below with that provenance and pinned STRICTLY (no xfail): the
plugin identities must reproduce them EXACTLY.  A mismatch means THIS
implementation's payload drifted -- the freeze is never touched.

The per-arm ``config`` dicts are unchanged between freeze v1 and v2, so they
are verified verbatim against the spec rows in
``research/control/v12_run/selection_freeze_specs/A12-V12-BAB-LOWBETA.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.adapter_v10.protocol import StrategyIdentity
from research.v12.families.bab_lowbeta.plugin import (
    BabLowBetaPlugin,
    frozen_identity,
)
from research.v12.families.bab_lowbeta.strategy import (
    ARM_IDS,
    BENCHMARK_SYMBOL_EXCLUDED,
    FAMILY_ID,
    FROZEN_ARM_CONFIG_DIGESTS,
    STRATEGY_ID,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    build_frozen_identity,
    frozen_arm_config_digest,
    frozen_arm_ids,
)
from research.v11.publication_identity import arm_config_digest

REPO = Path(__file__).resolve().parents[1]
SPEC_PATH = (
    REPO / "research" / "control" / "v12_run" / "selection_freeze_specs"
    / "A12-V12-BAB-LOWBETA.json"
)

# --------------------------------------------------------------------------- #
# FROZEN V2 IDENTITY CONTRACT (hard-coded; provenance: freeze v2 reissue,
# integration commit 39fc8821a5c8dbe9c2fd998edc3956ad6a02ec8f, frozen_cells
# rows for family A12-V12-BAB-LOWBETA).
# --------------------------------------------------------------------------- #
FROZEN_V2_DIRECTION = "long_short_beta_neutral"
FROZEN_V2_ARM_CONFIG_IDS = {
    "BAB-90D-W": "90D-BETA",
    "BAB-DOWNCORR-90D-W": "90D-DOWNCORR",
    "BAB-90D-W-INV": "90D-BETA-INV",
}
FROZEN_V2_DIGESTS = {
    "BAB-90D-W": (
        "7a233cf4672d279408a64b84d0b5e9924323329cf246f1b582fe0eb869c0db60"
    ),
    "BAB-DOWNCORR-90D-W": (
        "c1c2ed26da54090e1c08c35a36209e0afff99540701669fa99623b45f71881ee"
    ),
    "BAB-90D-W-INV": (
        "fabeb43aa89fcbfb915bbda488b07e272f188b2da06fc648e2f3ddc021072423"
    ),
}


def _spec_configs() -> dict[str, dict]:
    """Per-arm config dicts from the spec file (verbatim, v1 == v2)."""
    doc = json.loads(SPEC_PATH.read_text())
    return {
        arm["arm_id"]: arm["config"]
        for arm in doc["arms"]
        if arm["family"] == FAMILY_ID
    }


def test_frozen_digest_equality_all_three_arms() -> None:
    """STRICT: the v2 digests reproduce 3/3 from the frozen identity."""
    assert set(FROZEN_V2_DIGESTS) == set(ARM_IDS)
    for arm_id in ARM_IDS:
        identity = build_frozen_identity(arm_id)
        assert identity.arm_id == arm_id
        assert identity.strategy_id == STRATEGY_ID
        assert identity.family_id == FAMILY_ID
        assert identity.arm_config_id == FROZEN_V2_ARM_CONFIG_IDS[arm_id]
        # freeze v2: ONE direction shared by every arm
        assert identity.direction == FROZEN_V2_DIRECTION
        assert identity.window_start_iso == WINDOW_START_ISO
        assert identity.window_end_iso == WINDOW_END_ISO
        assert identity.benchmark_symbols_excluded == (BENCHMARK_SYMBOL_EXCLUDED,)
        assert identity.funding_sign_convention == "LONG_PAYS_POSITIVE_RATE"
        assert identity.matrix_cohort_hint == "v12"
        digest = arm_config_digest(identity, arm_id=arm_id)
        assert digest == FROZEN_V2_DIGESTS[arm_id], (
            f"{arm_id}: digest drifted from the frozen v2 contract "
            f"({digest} != {FROZEN_V2_DIGESTS[arm_id]}); fix the payload, "
            "never the freeze"
        )


def test_module_digest_literals_equal_the_v2_freeze_constants() -> None:
    """The module's pinned digest literals equal the hard-coded v2 rows."""
    assert dict(FROZEN_ARM_CONFIG_DIGESTS) == FROZEN_V2_DIGESTS
    for arm_id in ARM_IDS:
        assert frozen_arm_config_digest(arm_id) == FROZEN_V2_DIGESTS[arm_id]


def test_arm_digests_are_pairwise_distinct_and_replay_stable() -> None:
    digests = {arm: frozen_arm_config_digest(arm) for arm in ARM_IDS}
    assert len(set(digests.values())) == 3
    replay = {arm: frozen_arm_config_digest(arm) for arm in ARM_IDS}
    assert digests == replay


def test_arm_configs_match_the_spec_config_dicts() -> None:
    """The per-arm config mappings equal the spec file's ``config`` rows."""
    spec_configs = _spec_configs()
    assert set(spec_configs) == set(ARM_IDS)
    for arm_id in ARM_IDS:
        assert dict(build_frozen_identity(arm_id).config) == spec_configs[arm_id]


def test_any_config_drift_moves_the_digest() -> None:
    """A one-character config change must move the digest (fail closed)."""
    base = build_frozen_identity("BAB-90D-W")
    payload = dict(base.config)
    payload["formation_days"] = 56
    mutated = StrategyIdentity(
        strategy_id=base.strategy_id,
        family_id=base.family_id,
        arm_config_id=base.arm_config_id,
        direction=base.direction,
        window_start_iso=base.window_start_iso,
        window_end_iso=base.window_end_iso,
        benchmark_symbols_excluded=base.benchmark_symbols_excluded,
        arm_id=base.arm_id,
        config=payload,
    )
    assert arm_config_digest(mutated, arm_id=base.arm_id) != arm_config_digest(
        base, arm_id=base.arm_id
    )


def test_any_direction_drift_moves_the_digest() -> None:
    """A direction change must move the digest (freeze v2 pins direction)."""
    base = build_frozen_identity("BAB-90D-W")
    mutated = StrategyIdentity(
        strategy_id=base.strategy_id,
        family_id=base.family_id,
        arm_config_id=base.arm_config_id,
        direction="long_low_beta_short_high_beta",  # superseded v1-style text
        window_start_iso=base.window_start_iso,
        window_end_iso=base.window_end_iso,
        benchmark_symbols_excluded=base.benchmark_symbols_excluded,
        arm_id=base.arm_id,
        config=dict(base.config),
    )
    assert arm_config_digest(mutated, arm_id=base.arm_id) != arm_config_digest(
        base, arm_id=base.arm_id
    )


def test_unknown_arm_refused() -> None:
    with pytest.raises(Exception):
        build_frozen_identity("NOT-A-FROZEN-ARM")


def test_plugin_identity_matches_freeze() -> None:
    """The plugin's own identity() reproduces the frozen v2 digests 3/3."""

    class _StubBar:
        __slots__ = ("ts_event_ns", "open", "close")

        def __init__(self) -> None:
            self.ts_event_ns = 1
            self.open = 1.0
            self.close = 1.0

    bars = {
        BENCHMARK_SYMBOL_EXCLUDED: [_StubBar()],
        "SOLUSDT": [_StubBar()],
    }
    for arm_id in ARM_IDS:
        plugin = BabLowBetaPlugin(bars_by_symbol=bars, arm_id=arm_id)
        identity = plugin.identity()
        assert identity.arm_id == arm_id
        assert arm_config_digest(identity, arm_id=arm_id) == FROZEN_V2_DIGESTS[arm_id]


def test_frozen_identity_helper_is_the_plugin_identity() -> None:
    assert frozen_identity is build_frozen_identity
