"""Frozen arm-config identity, digest stability and byte-exact spec digests."""

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

ARM_IDS = (
    "A5-SFV2-ARM1-TSM12-VOLTARGET",
    "A5-SFV2-ARM2-SMA200-WEEKLY",
    "A5-SFV2-ARM3-TSM12-INVERTED-CONTROL",
)


def test_three_registered_arms(a5):
    assert tuple(a5.schedule.ARM_CONFIGS) == ARM_IDS


def test_anchor_frozen_fields(a5):
    c = a5.schedule.ARM_CONFIG_ANCHOR
    # a5_arm1_tsm12_ivol.json: 252-session sign gate m>0, monthly clock.
    assert c.gate == "TSMOM_SIGN"
    assert c.lookback_sessions == 252
    assert c.inverted_sign is False
    assert c.clock == "MONTHLY"
    assert c.vol_window_sessions == 63
    assert c.target_vol_annual == 0.10
    assert c.per_etf_cap == 0.35
    assert c.annualization_sessions == 252.0


def test_neighbour_frozen_fields(a5):
    c = a5.schedule.ARM_CONFIG_NEIGHBOUR
    # a5_arm2_sma200_weekly.json: SMA200 price-above gate, weekly clock,
    # defensive mapping IDENTICAL to anchor (only estimator + clock change).
    assert c.gate == "SMA_ABOVE"
    assert c.lookback_sessions == 200
    assert c.inverted_sign is False
    assert c.clock == "WEEKLY"
    assert c.vol_window_sessions == 63
    assert c.target_vol_annual == 0.10
    assert c.per_etf_cap == 0.35


def test_control_is_pure_sign_mutation_of_anchor(a5):
    s = a5.schedule
    anchor, control = s.ARM_CONFIG_ANCHOR, s.ARM_CONFIG_CONTROL
    # Spec: "Eligibility sign INVERTED ... everything_else: IDENTICAL to the anchor".
    assert control.gate == "TSMOM_SIGN"
    assert control.inverted_sign is True
    assert control.clock == "MONTHLY"
    assert s.control_is_pure_sign_mutation(anchor, control) is True
    # The neighbour is NOT a sign mutation of the anchor (estimator + clock differ).
    assert s.control_is_pure_sign_mutation(anchor, s.ARM_CONFIG_NEIGHBOUR) is False


def test_spec_files_reproduce_manifest_sha256_byte_exactly(a5):
    # Spec section 14: "manifest arm sha256s above must reproduce byte-exactly".
    spec_dir = a5.repo_root / "research" / "proposals" / "stocks_free_v2"
    for name, expected in a5.schedule.SPEC_FILE_SHA256.items():
        path = spec_dir / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == expected, name
        assert a5.schedule.spec_file_digest_matches(path, expected) is True


def test_arm_config_digest_stability_and_sensitivity(a5):
    s = a5.schedule
    anchor = s.ARM_CONFIG_ANCHOR
    # stable across repeated derivation
    assert s.arm_config_digest(anchor) == s.arm_config_digest(anchor)
    # every frozen field is digest-load-bearing: touching ANY of them moves it
    sensitive = {}
    for f in dataclasses.fields(anchor):
        if f.name in ("arm_id", "arm_role", "spec_filename"):
            continue  # identity fields are exercised by the control/neighbour cases
        bumped = dataclasses.replace(anchor, **{f.name: _bump(getattr(anchor, f.name))})
        sensitive[f.name] = s.arm_config_digest(bumped)
    base = s.arm_config_digest(anchor)
    for name, digest in sensitive.items():
        assert digest != base, name
    # distinct registered arms carry distinct digests
    digests = {s.arm_config_digest(c) for c in s.ARM_CONFIGS.values()}
    assert len(digests) == 3


def _bump(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, float):
        return value * 1.5
    if isinstance(value, int):
        return value + 1
    if isinstance(value, str):
        return value + "_X"
    raise AssertionError(value)


def test_digest_is_sha256_of_canonical_payload(a5):
    s = a5.schedule
    payload = json.dumps(s.ARM_CONFIG_ANCHOR.digest_payload(), sort_keys=True, separators=(",", ":"))
    assert s.arm_config_digest(s.ARM_CONFIG_ANCHOR) == hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert len(s.arm_config_digest(s.ARM_CONFIG_ANCHOR)) == 64


def test_cohort_matches_frozen_census(a5):
    census = json.loads(
        (a5.repo_root / "research" / "control" / "stocks_free_v2_run" / "cohort_census.json").read_text()
    )
    accepted = [row["symbol"] for row in census["rows"] if row["decision"] == "ACCEPTED"]
    assert a5.schedule.COHORT_SYMBOLS == tuple(accepted)
    assert len(a5.schedule.COHORT_SYMBOLS) == 11
    # TLT/GLD excluded pre-census: defensiveness is CASH only.
    assert "TLT" not in a5.schedule.COHORT_SYMBOLS
    assert "GLD" not in a5.schedule.COHORT_SYMBOLS


def test_turnover_ceiling_is_frozen_o1_fix(a5):
    # selection_freeze.json objective-O1 fix: 6.0x two-way per year (schedule-only).
    assert a5.schedule.TURNOVER_CEILING_TWO_WAY_ANNUAL == 6.0


def test_family_id_matches_manifest(a5):
    manifest = json.loads(
        (a5.repo_root / "research" / "proposals" / "stocks_free_v2" / "a5_family_manifest.json").read_text()
    )
    assert a5.schedule.FAMILY_ID == manifest["family_id"] == "A5-SFV2-TREND-DEFENSIVE"
