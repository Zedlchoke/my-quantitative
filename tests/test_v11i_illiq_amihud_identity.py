"""Frozen-digest equality + identity tests for A8-V11-ILLIQ-AMIHUD.

The selection freeze (``research/control/v11_run/selection_freeze.json``)
pins one ``arm_config_digest`` per arm.  These tests assert EXACT equality
against the freeze file: a mismatch is a bug in THIS family package, never a
reason to touch the freeze.
"""

import json
from pathlib import Path

import pytest

from research.adapter_v10.protocol import StrategyIdentity
from research.v11.families.illiq_amihud import (
    ARMS,
    BENCHMARK_SYMBOL_EXCLUDED,
    FAMILY_ID,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    build_frozen_identity,
    frozen_arm_config_digest,
    frozen_arm_ids,
)
from research.v11.publication_identity import arm_config_digest

REPO_ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = (
    REPO_ROOT / "research" / "control" / "v11_run" / "selection_freeze.json"
)
SPEC_PATH = (
    REPO_ROOT
    / "research"
    / "control"
    / "v11_run"
    / "selection_freeze_specs"
    / "A8-V11-ILLIQ-AMIHUD.json"
)

FROZEN_DIGESTS = {
    "ILLIQ-AMIHUD-28D-W": (
        "76729187a8a94980c08c30ae741a1ae0dd0e4da3d682037012ed7c04016fa8e0"
    ),
    "ILLIQ-AMIHUD-56D-W": (
        "286cef34b8b520843608737e45f0a3175719dde5099724f33c299c14eaf44571"
    ),
    "ILLIQ-AMIHUD-28D-W-INV": (
        "d4d32ed62153ae5c9cee69230fc35de92bed64fe560e80f1902cc90f505fc913"
    ),
}


def _frozen_cells() -> dict[str, dict]:
    with open(FREEZE_PATH, "r", encoding="utf-8") as handle:
        freeze = json.load(handle)
    cells = {
        cell["arm_id"]: cell
        for cell in freeze["frozen_cells"]
        if cell["family"] == FAMILY_ID
    }
    assert set(cells) == set(frozen_arm_ids())
    return cells


def test_frozen_digest_equality_against_freeze_file():
    """Digest equality x3 against the committed selection freeze."""
    cells = _frozen_cells()
    for arm_id in frozen_arm_ids():
        digest = frozen_arm_config_digest(arm_id)
        assert digest == cells[arm_id]["arm_config_digest"], arm_id


def test_frozen_digest_equality_against_hard_pinned_values():
    """Digest equality x3 against the freeze-time pinned hex values."""
    for arm_id in frozen_arm_ids():
        assert frozen_arm_config_digest(arm_id) == FROZEN_DIGESTS[arm_id]


def test_digest_is_stable_under_identity_replay():
    for arm_id in frozen_arm_ids():
        identity = build_frozen_identity(arm_id)
        replay = arm_config_digest(
            StrategyIdentity(
                strategy_id=identity.strategy_id,
                family_id=identity.family_id,
                arm_config_id=identity.arm_config_id,
                direction=identity.direction,
                window_start_iso=identity.window_start_iso,
                window_end_iso=identity.window_end_iso,
                benchmark_symbols_excluded=identity.benchmark_symbols_excluded,
                funding_sign_convention=identity.funding_sign_convention,
                arm_id=identity.arm_id,
                config=dict(identity.config),
            ),
            arm_id=arm_id,
        )
        assert replay == frozen_arm_config_digest(arm_id)


def test_identity_fields_are_frozen():
    cells = _frozen_cells()
    with open(SPEC_PATH, "r", encoding="utf-8") as handle:
        spec = json.load(handle)
    anchor = next(a for a in spec["arms"].values() if a["role"] == "anchor")
    for arm_id in frozen_arm_ids():
        identity = build_frozen_identity(arm_id)
        assert identity.strategy_id == f"{FAMILY_ID}.v1"
        assert identity.family_id == FAMILY_ID
        assert identity.arm_config_id == cells[arm_id]["role"]
        assert identity.direction == "long_short_beta_neutral"
        assert identity.window_start_iso == WINDOW_START_ISO
        assert identity.window_end_iso == WINDOW_END_ISO
        assert identity.benchmark_symbols_excluded == (BENCHMARK_SYMBOL_EXCLUDED,)
        assert identity.funding_sign_convention == "LONG_PAYS_POSITIVE_RATE"
        assert identity.arm_id == arm_id


def test_identity_config_carries_exactly_the_frozen_values():
    """The config mapping is exactly the frozen feature/book/clock/cost set."""
    with open(SPEC_PATH, "r", encoding="utf-8") as handle:
        spec = json.load(handle)
    arms_spec = spec["arms"]
    anchor = next(a for a in arms_spec.values() if a["role"] == "anchor")
    for arm_id in frozen_arm_ids():
        arm_spec = arms_spec[arm_id]
        identity = build_frozen_identity(arm_id)
        config = dict(identity.config)
        assert set(config) == {
            "feature",
            "book",
            "formation_days",
            "holding_days",
            "decision_clock",
            "costs",
            "falsification",
        }
        expected_feature = (
            anchor["feature"]
            if "same as anchor" in arm_spec["feature"]
            else arm_spec["feature"]
        )
        assert config["feature"] == expected_feature
        assert config["book"] == arm_spec["book"]
        assert config["formation_days"] == arm_spec.get(
            "formation_days", anchor["formation_days"]
        )
        assert config["holding_days"] == arm_spec.get(
            "holding_days", anchor["holding_days"]
        )
        assert config["decision_clock"] == spec["common"]["decision_clock"]
        assert config["costs"] == spec["common"]["costs"]
        assert config["falsification"] == arm_spec.get("falsification", "")


def test_arm_digests_are_pairwise_distinct():
    digests = {arm_id: frozen_arm_config_digest(arm_id) for arm_id in frozen_arm_ids()}
    assert len(set(digests.values())) == 3
    assert set(ARMS) == set(frozen_arm_ids())
