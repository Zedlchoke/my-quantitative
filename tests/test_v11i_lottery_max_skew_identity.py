"""Frozen-identity equality tests for V11-SEED-LOTTERY-MAX-SKEW (I-family-1).

The digests in ``research/control/v11_run/selection_freeze.json``
(``frozen_cells``) are the frozen contract: the plugin identities must
reproduce them EXACTLY.  A mismatch means THIS implementation's payload
drifted -- the freeze is never touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.adapter_v10.protocol import ContractViolation
from research.v11.families.lottery_max_skew.plugin import (
    ANCHOR_ARM,
    ARM_IDS,
    CONTROL_ARM,
    FAMILY_ID,
    NEIGHBOUR_ARM,
    frozen_identity,
)
from research.v11.publication_identity import arm_config_digest

REPO = Path(__file__).resolve().parents[1]
FREEZE_PATH = REPO / "research" / "control" / "v11_run" / "selection_freeze.json"


def _frozen_digests() -> dict[str, str]:
    doc = json.loads(FREEZE_PATH.read_text())
    return {
        cell["arm_id"]: cell["arm_config_digest"]
        for cell in doc["frozen_cells"]
        if cell["family"] == FAMILY_ID
    }


def test_frozen_digest_equality_all_three_arms() -> None:
    frozen = _frozen_digests()
    assert set(frozen) == set(ARM_IDS)
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        assert identity.arm_id == arm_id
        assert identity.window_start_iso == "2025-08-22T00:00:00Z"
        assert identity.window_end_iso == "2026-08-21T00:00:00Z"
        assert identity.benchmark_symbols_excluded == ("BTCUSDT",)
        digest = arm_config_digest(identity, arm_id=arm_id)
        assert digest == frozen[arm_id], (
            f"{arm_id}: digest drifted from the frozen contract "
            f"({digest} != {frozen[arm_id]}); fix the payload, never the freeze"
        )


def test_anchor_digest_matches_freeze_value() -> None:
    frozen = _frozen_digests()
    assert frozen[ANCHOR_ARM] == (
        "810ee5023dd2e3d124d59aaf67a0a8abb296960f6c48cf0a5c9d0f4c0087362e"
    )
    assert frozen[NEIGHBOUR_ARM] == (
        "2ad45a4b08dddd48974aa8cfdfcd29e2d375923f0bd174b75143849eef5732d5"
    )
    assert frozen[CONTROL_ARM] == (
        "2429b50cd7d3ec098a2aa211ed4465da495dd061319b520c32859e76208e352d"
    )


def test_arm_digests_are_pairwise_distinct_and_replay_stable() -> None:
    digests = {
        arm: arm_config_digest(frozen_identity(arm), arm_id=arm) for arm in ARM_IDS
    }
    assert len(set(digests.values())) == 3
    replay = {
        arm: arm_config_digest(frozen_identity(arm), arm_id=arm) for arm in ARM_IDS
    }
    assert digests == replay


def test_any_config_drift_moves_the_digest() -> None:
    """A one-character config change must move the digest (fail closed)."""
    base = frozen_identity(ANCHOR_ARM)
    payload = dict(base.config)
    payload["formation_days"] = 8
    drifted = ContractViolation  # noqa: F841 - documentation only
    mutated = type(base)(
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


def test_unknown_arm_refused() -> None:
    with pytest.raises(ContractViolation):
        frozen_identity("NOT-A-FROZEN-ARM")
