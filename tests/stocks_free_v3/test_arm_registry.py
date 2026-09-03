"""A1 central wiring tests: the six-arm registry (PLAN_stocks.md section 13).

Wiring must bind exactly the frozen selection, with six distinct trial
identities, before any QA or scored dispatch is possible.
"""
from research.stocks_free_v3.arm_registry import (
    EXECUTION_ORDER,
    build_registry,
    build_arm_schedule,
)

FAMILY_ARM_CONFIG_DIGESTS = {
    # pinned from the A8/A9 implementation handoffs (verbatim frozen configs)
    "SFV3-A5-IDIO-SHOCK-REVERSAL-A1":
        "c4c38f87c4b2cee68d88a9f949b4c2ed064b550a92e89d49d13a5b9a77e5f64c",
    "SFV3-A5-IDIO-SHOCK-REVERSAL-N1":
        "a8265f8c1572cf39b0ccf7683737c0ee9979a723d424af91451374923144cc2f",
    "SFV3-A5-IDIO-SHOCK-REVERSAL-C1":
        "5a07f804fbccadf98065e3084c662f8f9eabb2e52f9b68a5fd729a6e6fef1617",
    "SFV3-A6-TOM-SETTLE-A":
        "e8e5b5c0f1b44360b36790bf3a7a04358ba1c7943f3824c534da07ed4513ee6f",
    "SFV3-A6-TOM-SETTLE-N":
        "e0afac4ab7c615319e2a6943380eaea4a38efb3cd4255fe0630442bc93c7a5f4",
    "SFV3-A6-TOM-SETTLE-C":
        "f57b5580d2699a84c3ed9afbc888c7abea6f70d8ef4602a95f59660691e1bd58",
}


def test_registry_binds_exactly_six_frozen_arms():
    reg = build_registry()
    assert set(reg) == set(EXECUTION_ORDER)
    assert len(reg) == 6


def test_family_module_digests_match_implementation_handoffs():
    reg = build_registry()
    for arm_id, expected in FAMILY_ARM_CONFIG_DIGESTS.items():
        assert reg[arm_id].config_digest == expected, arm_id


def test_six_distinct_trial_identities():
    reg = build_registry()
    digests = {reg[a].trial_identity_digest for a in EXECUTION_ORDER}
    assert len(digests) == 6


def test_constant_scale_rules_resolved_adj4():
    reg = build_registry()
    for arm_id in ("SFV3-A5-IDIO-SHOCK-REVERSAL-A1",
                   "SFV3-A5-IDIO-SHOCK-REVERSAL-C1"):
        rule = reg[arm_id].vol_scaling_rule
        assert rule.min_gross == rule.max_gross == 0.025
        assert rule.target_daily_vol == 0.01  # ADJ-4 pin; scale constant
        assert rule.scale([0.02] * 63) == 0.025
    rule = reg["SFV3-A5-IDIO-SHOCK-REVERSAL-N1"].vol_scaling_rule
    assert rule.min_gross == rule.max_gross == 0.05
    assert rule.scale([0.02] * 63) == 0.05
    for arm_id in ("SFV3-A6-TOM-SETTLE-A", "SFV3-A6-TOM-SETTLE-N",
                   "SFV3-A6-TOM-SETTLE-C"):
        rule = reg[arm_id].vol_scaling_rule
        assert (rule.target_daily_vol, rule.min_gross, rule.max_gross) == (
            0.005, 0.30, 0.50)


def test_roles_and_family_split():
    reg = build_registry()
    assert reg["SFV3-A5-IDIO-SHOCK-REVERSAL-A1"].role == "anchor"
    assert reg["SFV3-A5-IDIO-SHOCK-REVERSAL-N1"].role == "neighbour"
    assert reg["SFV3-A5-IDIO-SHOCK-REVERSAL-C1"].role == (
        "causal_negative_control")
    assert reg["SFV3-A6-TOM-SETTLE-C"].role == "causal_negative_control"
    assert sum(1 for b in reg.values()
               if b.role == "causal_negative_control") == 2


def test_schedule_dispatch_smoke_synthetic_idio():
    """The registry dispatch reaches the family module on synthetic input
    (no real data; no scored metric)."""
    sessions = [f"2021-01-{d:02d}" for d in range(4, 20)]
    returns = {s: {"SPY": 0.0, "XLK": 0.0} for s in sessions}
    inputs = type("I", (), {"sessions": tuple(sessions),
                            "issuer_tr_returns": returns})()
    from research.stocks_free_v3.arm_registry import ArmInputs
    inputs = ArmInputs(sessions=tuple(sessions), raw_close={}, distributions={},
                       split_factors={}, issuer_tr_returns=returns)
    result = build_arm_schedule("SFV3-A5-IDIO-SHOCK-REVERSAL-A1", inputs)
    assert result is not None
