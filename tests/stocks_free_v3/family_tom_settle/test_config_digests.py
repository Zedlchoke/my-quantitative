"""Frozen arm configuration heads: three stable identities, complete digests.

Deliverable 1c: three stable arm config heads A/N/C with complete sha256
config digests over the canonical JSON of the frozen config.  The pinned
digest literals below are part of the handoff evidence — any change to a
frozen constant changes them and MUST break this test.
"""

from __future__ import annotations

import hashlib

import pytest

from research.assets.common.contracts import canonical_json
from research.assets.stocks.calendar import CALENDAR_ID
from research.stocks_free_v3.authority import COHORT_SYMBOLS
from research.stocks_free_v3.family_tom_settle import (
    BASE_COST_BPS,
    BASE_GROSS,
    DECISION_LAG_SESSIONS,
    FAMILY_ID,
    FROZEN_VOL_SCALING_RULE,
    STRESS_COST_BPS,
    TOM_GROSS,
    ArmConfigError,
    WindowRule,
    arm_config_digests,
    build_arm_configs,
)

#: Pinned sha256 digests of the three frozen arm configs (A9 handoff).
PINNED_DIGESTS = {
    "A": "e8e5b5c0f1b44360b36790bf3a7a04358ba1c7943f3824c534da07ed4513ee6f",
    "N": "e0afac4ab7c615319e2a6943380eaea4a38efb3cd4255fe0630442bc93c7a5f4",
    "C": "f57b5580d2699a84c3ed9afbc888c7abea6f70d8ef4602a95f59660691e1bd58",
}


def test_three_heads_with_frozen_identities():
    cfgs = build_arm_configs()
    assert set(cfgs) == {"A", "N", "C"}
    assert cfgs["A"].arm_id == "SFV3-A6-TOM-SETTLE-A"
    assert cfgs["N"].arm_id == "SFV3-A6-TOM-SETTLE-N"
    assert cfgs["C"].arm_id == "SFV3-A6-TOM-SETTLE-C"
    assert cfgs["A"].role == "anchor"
    assert cfgs["N"].role == "neighbour"
    assert cfgs["C"].role == "causal_negative_control"
    assert cfgs["A"].window.rule_kind == "ANCHOR_TOM"
    assert cfgs["N"].window.rule_kind == "NEIGHBOUR_MONTH_START"
    assert cfgs["C"].window.rule_kind == "CONTROL_MID_MONTH"


def test_heads_share_everything_but_the_window():
    cfgs = build_arm_configs()
    payloads = {k: cfg.to_payload() for k, cfg in cfgs.items()}
    identity_fields = {"window", "arm_id", "arm_key", "role"}
    for key in ("N", "C"):
        other = {k: v for k, v in payloads[key].items() if k not in identity_fields}
        anchor = {k: v for k, v in payloads["A"].items() if k not in identity_fields}
        assert other == anchor


def test_frozen_constants_inside_every_payload():
    for cfg in build_arm_configs().values():
        payload = cfg.to_payload()
        assert payload["family_id"] == FAMILY_ID
        assert payload["books"]["tom"]["gross"] == TOM_GROSS == 0.50
        assert payload["books"]["base"]["gross"] == BASE_GROSS == 0.30
        assert payload["books"]["tom"]["legs"] == 11
        assert payload["books"]["cash_semantics"] == "EXPLICIT_RESIDUAL_LEG_NEVER_TRADABLE"
        assert payload["books"]["intra_window_re_equalization"] == "NEVER"
        assert payload["clock"]["semantics"] == "DECISION_CLOSE_T_FILL_CLOSE_T_PLUS_1_CANONICAL_CLOSE_FILL"
        assert payload["clock"]["decision_lag_sessions"] == DECISION_LAG_SESSIONS == 1
        assert payload["clock"]["expected_transitions_per_year"] == 24
        assert payload["clock"]["expected_two_way_turnover_per_year"] == 4.80
        assert payload["risk_matched_rule"] == {
            "kind": "EX_ANTE_GROSS_VOL_CLIP_DD0",
            "lookback_sessions": 63,
            "target_daily_vol": 0.005,
            "min_gross": 0.30,
            "max_gross": 0.50,
            "insufficient_history": "MIN_GROSS",
        }
        assert payload["costs"] == {
            "base_bps_per_side": BASE_COST_BPS,
            "stress_bps_per_side": STRESS_COST_BPS,
        }
        assert payload["calendar_id"] == CALENDAR_ID == "US_EQUITY_REGULAR_V1"
        assert payload["universe"]["symbols"] == list(COHORT_SYMBOLS)


def test_digests_match_pinned_literals():
    assert arm_config_digests() == PINNED_DIGESTS


def test_digest_is_sha256_of_canonical_payload():
    for cfg in build_arm_configs().values():
        expected = hashlib.sha256(canonical_json(cfg.to_payload()).encode("utf-8")).hexdigest()
        assert cfg.digest == expected


def test_digests_stable_across_repeated_construction():
    assert arm_config_digests() == {
        k: cfg.digest for k, cfg in build_arm_configs().items()
    }


def test_digests_distinct_across_arms():
    digests = arm_config_digests()
    assert len(set(digests.values())) == 3


def test_digest_changes_when_any_frozen_field_changes():
    base = build_arm_configs()["A"]
    for change in (
        {"tom_gross": 0.55},
        {"base_gross": 0.35},
        {"decision_lag_sessions": 2},
    ):
        kwargs = dict(
            arm_key="A", arm_id="SFV3-A6-TOM-SETTLE-A", role="anchor",
            window=base.window, symbols=tuple(COHORT_SYMBOLS),
            tom_gross=TOM_GROSS, base_gross=BASE_GROSS,
            vol_scaling_rule=FROZEN_VOL_SCALING_RULE,
            decision_lag_sessions=DECISION_LAG_SESSIONS,
            calendar_id=CALENDAR_ID, base_cost_bps=BASE_COST_BPS,
            stress_cost_bps=STRESS_COST_BPS,
        )
        kwargs.update(change)
        if change.get("decision_lag_sessions") == 2:
            with pytest.raises(ArmConfigError):
                base.__class__(**kwargs)
            continue
        mutated = base.__class__(**kwargs)
        assert mutated.digest != base.digest


def test_window_reshapes_are_rejected_frozen_shapes_only():
    """The three window SHAPES are frozen constants; anything else is rejected."""
    with pytest.raises(ArmConfigError):
        WindowRule(rule_kind="BOGUS")
    with pytest.raises(ArmConfigError):
        WindowRule(rule_kind="ANCHOR_TOM", first_ordinals=(1,), last_ordinals=(1, 2, 3))
    with pytest.raises(ArmConfigError):
        WindowRule(rule_kind="ANCHOR_TOM", first_ordinals=(1, 2), last_ordinals=(1, 2))
    with pytest.raises(ArmConfigError):
        WindowRule(rule_kind="NEIGHBOUR_MONTH_START", first_ordinals=(2, 3))
    with pytest.raises(ArmConfigError):
        WindowRule(rule_kind="NEIGHBOUR_MONTH_START", first_ordinals=(1, 2, 3, 4))
    with pytest.raises(ArmConfigError):
        WindowRule(rule_kind="CONTROL_MID_MONTH", explicit_ordinals=(8, 8, 9))
    with pytest.raises(ArmConfigError):
        WindowRule(rule_kind="CONTROL_MID_MONTH", explicit_ordinals=(8, 13))
    with pytest.raises(ArmConfigError):
        WindowRule(rule_kind="CONTROL_MID_MONTH", explicit_ordinals=(7, 8, 9, 10, 11))
    # the frozen shapes themselves construct cleanly
    assert WindowRule(rule_kind="ANCHOR_TOM", first_ordinals=(1, 2),
                      last_ordinals=(1, 2, 3)).window_ordinals(20) == (1, 2, 18, 19, 20)
    assert WindowRule(rule_kind="NEIGHBOUR_MONTH_START",
                      first_ordinals=(1, 2, 3)).window_ordinals(19) == (1, 2, 3)
    assert WindowRule(rule_kind="CONTROL_MID_MONTH",
                      explicit_ordinals=(8, 9, 10, 11, 12)).window_ordinals(19) == (8, 9, 10, 11, 12)


def test_universe_must_be_the_exact_frozen_cohort():
    cfg = build_arm_configs()["A"]
    kwargs = dict(
        arm_key="A", arm_id="SFV3-A6-TOM-SETTLE-A", role="anchor",
        window=cfg.window, symbols=tuple(COHORT_SYMBOLS),
        tom_gross=TOM_GROSS, base_gross=BASE_GROSS,
        vol_scaling_rule=FROZEN_VOL_SCALING_RULE,
        decision_lag_sessions=DECISION_LAG_SESSIONS, calendar_id=CALENDAR_ID,
        base_cost_bps=BASE_COST_BPS, stress_cost_bps=STRESS_COST_BPS,
    )
    assert cfg.__class__(**kwargs).digest == cfg.digest
    with pytest.raises(ArmConfigError):
        kwargs["symbols"] = tuple(COHORT_SYMBOLS)[:-1] + ("XLC",)
        cfg.__class__(**kwargs)
    kwargs["symbols"] = tuple(COHORT_SYMBOLS)
    with pytest.raises(ArmConfigError):
        kwargs["calendar_id"] = "MADE_UP_CALENDAR"
        cfg.__class__(**kwargs)
