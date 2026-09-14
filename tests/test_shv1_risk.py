"""Frozen risk caps applied before fills, driven by the real identity
manifest (plan G6). Caps are never hard-coded: they are parsed from
research/control/prospective_shadow_v1/identity/identity_recovery.json
verbatim parameters (read-only, in-repo).
"""

import json
import os

import pytest

from research.shadow_v1.risk import (
    RiskConfigError,
    caps_from_identity_params,
    check_and_apply,
)

IDENTITY_PATH = os.path.join(
    "research", "control", "prospective_shadow_v1", "identity", "identity_recovery.json"
)


def _params_by_family():
    with open(IDENTITY_PATH, "r", encoding="utf-8") as fh:
        identity = json.load(fh)
    return {f["family_id"]: f["score_affecting_parameters"] for f in identity["families"]}


def test_carry_caps_from_verbatim_identity_lines():
    caps = caps_from_identity_params(
        "XSECT-FUND-CARRY-7D", _params_by_family()["XSECT-FUND-CARRY-7D"]
    )
    assert caps.target_gross == 0.80
    assert caps.hard_gross_cap == 1.00
    assert caps.hard_abs_net_cap == 0.10
    assert caps.max_abs_weight == 0.20


def test_premfade_caps_weight_bounds_from_spec():
    caps = caps_from_identity_params(
        "BASISLV-PREMFADE-28D", _params_by_family()["BASISLV-PREMFADE-28D"]
    )
    assert caps.hard_gross_cap == 1.0
    assert caps.min_abs_weight == 0.125
    assert caps.max_abs_weight == 0.30
    assert caps.dollar_neutral is True


def test_cap_violation_blocks_event_and_records_pre_post():
    caps = caps_from_identity_params(
        "XSECT-FUND-CARRY-7D", _params_by_family()["XSECT-FUND-CARRY-7D"]
    )
    approved, block = check_and_apply(
        {"ETHUSDT": 0.25, "SOLUSDT": -0.25}, caps
    )
    assert approved == {}
    assert block.blocked is True
    assert block.pre_target == {"ETHUSDT": 0.25, "SOLUSDT": -0.25}
    assert block.post_target == {}  # nothing may fill after a block
    assert any("max_abs_weight[ETHUSDT]" in v for v in block.violations)
    # net |0.10| is AT the hard cap: allowed (inclusive)
    approved2, block2 = check_and_apply(
        {"ETHUSDT": 0.20, "SOLUSDT": -0.20}, caps
    )
    assert approved2 == {"ETHUSDT": 0.20, "SOLUSDT": -0.20}
    assert block2.blocked is False


def test_illiq_requires_numeric_config_fail_closed():
    params = _params_by_family()["ILLIQ-AMIHUD-28D-W"]
    # identity pins the qualitative dollar/beta-neutral rule without numbers
    with pytest.raises(RiskConfigError):
        caps_from_identity_params("ILLIQ-AMIHUD-28D-W", params)
    # the numeric tolerances must be explicitly supplied by the cycle config
    cfg = dict(params)
    cfg.update(
        {
            "target_gross": 1.0,
            "hard_gross_cap": 1.0,
            "hard_abs_net_cap": 0.0,
            "max_abs_symbol_weight": 0.20,
            "btc_beta_tolerance": 1e-9,
        }
    )
    caps = caps_from_identity_params("ILLIQ-AMIHUD-28D-W", cfg)
    assert caps.dollar_neutral and caps.btc_beta_neutral
    approved, block = check_and_apply(
        {"AAAUSDT": 0.1}, caps, symbol_betas={"AAAUSDT": 0.5}
    )
    assert block.blocked and any("btc_beta" in v for v in block.violations)


def test_unknown_family_refuses():
    with pytest.raises(RiskConfigError):
        caps_from_identity_params("NOT-A-FAMILY", {})
