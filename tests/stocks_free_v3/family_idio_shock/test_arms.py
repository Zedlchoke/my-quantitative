"""Frozen arm config heads: constants, digests, validation, expected signs."""

from __future__ import annotations

import hashlib

import pytest

from research.assets.common.contracts import canonical_json
from research.stocks_free_v3.authority import SECTOR_SYMBOLS
from research.stocks_free_v3.family_idio_shock.arms import (
    ADJUDICATION,
    ARM_A1,
    ARM_C1,
    ARM_N1,
    EXPECTED_MECHANISM_SIGN,
    FAMILY_ID,
    FROZEN_ARMS,
    FrozenArmConfig,
    VOL_SCALING_A1_C1,
    VOL_SCALING_N1,
)


def test_universe_is_the_frozen_ten_sector_etfs():
    assert set(SECTOR_SYMBOLS) == {
        "XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE"}
    assert "SPY" not in SECTOR_SYMBOLS


def test_frozen_constants_match_selection_freeze():
    for arm in FROZEN_ARMS:
        assert arm.gross == 0.5 and arm.cash_weight == 0.5
        assert arm.episode_budget_max_entries == 5
        assert arm.episode_budget_window_sessions == 252
        assert arm.concurrency == 1
        assert arm.beta_lookback_sessions == 60
        assert arm.residual_ddof == 0
        assert arm.universe == tuple(SECTOR_SYMBOLS)
    assert ARM_A1.role == "anchor"
    assert ARM_A1.hold_sessions == 5
    assert ARM_A1.z_threshold == -3.0
    assert ARM_N1.hold_sessions == 10  # neighbour differs ONLY in the hold
    assert ARM_N1.z_threshold == ARM_A1.z_threshold
    assert ARM_N1.trigger == ARM_A1.trigger
    assert ARM_C1.role == "causal_negative_control"
    assert ARM_C1.hold_sessions == 5
    assert ARM_C1.z_threshold == +3.0
    # the constant-scale vol rules, verbatim from the freeze
    assert VOL_SCALING_A1_C1 == {"lookback_sessions": 63, "target_daily_vol": None,
                                 "min_gross": 0.025, "max_gross": 0.025}
    assert VOL_SCALING_N1 == {"lookback_sessions": 63, "target_daily_vol": None,
                              "min_gross": 0.05, "max_gross": 0.05}
    assert ADJUDICATION == "ADJ-1-EXEC-CLOCK"


def test_config_digest_is_sha256_over_canonical_payload():
    for arm in FROZEN_ARMS:
        expected = hashlib.sha256(
            canonical_json(arm.to_payload()).encode("utf-8")).hexdigest()
        assert arm.config_digest == expected
        assert len(arm.config_digest) == 64
    # payload determinism: digest independent of dict insertion order
    payload = ARM_A1.to_payload()
    reordered = dict(reversed(list(payload.items())))
    assert canonical_json(payload) == canonical_json(reordered)
    # the three arms are distinct identities
    assert len({a.config_digest for a in FROZEN_ARMS}) == 3


def test_expected_mechanism_signs_are_recorded():
    assert EXPECTED_MECHANISM_SIGN[ARM_A1.arm_id].startswith("POSITIVE")
    assert EXPECTED_MECHANISM_SIGN[ARM_N1.arm_id].startswith("POSITIVE")
    assert EXPECTED_MECHANISM_SIGN[ARM_C1.arm_id].startswith("NON_POSITIVE")


def test_trigger_breach_and_selection_direction():
    assert ARM_A1.breaches(-3.0) and ARM_A1.breaches(-7.8)
    assert not ARM_A1.breaches(-2.999) and not ARM_A1.breaches(+5.0)
    assert ARM_C1.breaches(3.0) and ARM_C1.breaches(7.8)
    assert not ARM_C1.breaches(2.999) and not ARM_C1.breaches(-5.0)
    assert ARM_A1.selects_extreme_low and ARM_N1.selects_extreme_low
    assert not ARM_C1.selects_extreme_low


def _mutated(**overrides) -> FrozenArmConfig:
    fields = {f.name: getattr(ARM_A1, f.name) for f in ARM_A1.__dataclass_fields__.values()}
    fields.update(overrides)
    return FrozenArmConfig(**fields)


def test_config_validation_fails_closed():
    with pytest.raises(ValueError, match="gross \\+ cash_weight"):
        _mutated(gross=0.6)
    with pytest.raises(ValueError, match="negative threshold"):
        _mutated(z_threshold=3.0)
    with pytest.raises(ValueError, match="trigger sign and selection direction"):
        _mutated(selection="MAX_Z")
    with pytest.raises(ValueError, match="min_gross == max_gross"):
        _mutated(vol_scaling_rule={"lookback_sessions": 63,
                                   "target_daily_vol": None,
                                   "min_gross": 0.01, "max_gross": 0.02})
    with pytest.raises(ValueError, match="residual_ddof is frozen"):
        _mutated(residual_ddof=1)
    with pytest.raises(ValueError, match="beta_lookback_sessions is frozen"):
        _mutated(beta_lookback_sessions=63)
    with pytest.raises(ValueError, match="must not be in the trigger universe"):
        _mutated(universe=tuple(list(SECTOR_SYMBOLS) + ["SPY"]))
    with pytest.raises(ValueError, match="hold_sessions must be"):
        _mutated(hold_sessions=0)
    with pytest.raises(ValueError, match="episode_budget_window_sessions must be"):
        _mutated(episode_budget_window_sessions=0)
    with pytest.raises(ValueError, match="concurrency must be"):
        _mutated(concurrency=0)


def test_arm_ids_follow_the_freeze_naming():
    assert ARM_A1.arm_id == f"{FAMILY_ID}-A1"
    assert ARM_N1.arm_id == f"{FAMILY_ID}-N1"
    assert ARM_C1.arm_id == f"{FAMILY_ID}-C1"
    assert FAMILY_ID == "SFV3-A5-IDIO-SHOCK-REVERSAL"
