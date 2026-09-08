"""Compatibility tests: historical crypto manifests parse identically.

Gate M0 (PLAN_stocks.md section 15): old manifests (exactly as produced by
``research/protocol/manifest.py``) convert through the migration adapter
with every historical value preserved; the roundtrip is byte-identical.
No tracked crypto artifact is read or written here — fixtures are built in
``tmp_path`` only.
"""

from __future__ import annotations

import hashlib

import pytest
import yaml

from contracts.protocol import ManifestSpec
from research.assets.common.crypto_compat import (
    CRYPTO_PERP_ASSET_CLASS,
    derive_cost_model_id,
    legacy_payload,
    normalize_legacy_manifest,
    to_asset_contract,
    verify_roundtrip,
    yaml_bytes,
)
from research.protocol.manifest import build_manifest, read_manifest, write_manifest

CONFIG_SHA = hashlib.sha256(b"frozen-config").hexdigest()
DATA_SHA = hashlib.sha256(b"frozen-data-manifest").hexdigest()

VENUE = "BINANCE"
CALENDAR_ID = "TEST_ONLY_DUMMY_SOLAR_24X7"


def _manifest_kwargs(**overrides) -> dict:
    base = {name: "x" for name in (
        "hypothesis_id", "strategy_type", "owner_agent", "validator_agent",
        "git_commit", "config_path", "data_snapshot_id", "universe_snapshot",
        "actual_start_utc", "actual_end_utc", "common_intersection",
        "split_policy", "fee_model", "slippage_model", "funding_mode",
        "parameter_lock_utc", "command", "experiment_id",
    )}
    kwargs = {
        **base,
        "candidate_version": 1,
        "dirty_worktree": False,
        "warmup_bars": 0,
        "purge_bars": 0,
        "embargo_bars": 0,
        "outer_folds": 3,
        "parameter_combinations": 1,
        "prior_family_trials": 0,
        "random_seed": 42,
        "config_sha256": CONFIG_SHA,
        "data_manifest_sha256": DATA_SHA,
        "fee_model": "taker_fee_bnb_v1",
        "slippage_model": "two_tick_v1",
        "funding_mode": "bundled_pit_v2",
        "hypothesis_id": "HYP_VOL_MR",
        "strategy_type": "vol_compression_mr",
        "experiment_id": "EXP-20260902-0007",
    }
    kwargs.update(overrides)
    return kwargs


def _manifest(**overrides) -> ManifestSpec:
    return build_manifest(**_manifest_kwargs(**overrides))


# --- adapter output ----------------------------------------------------------- #
def test_old_crypto_manifest_yields_asset_neutral_contract():
    manifest = _manifest()
    result = to_asset_contract(manifest, venue=VENUE, calendar_id=CALENDAR_ID)
    contract = result.contract
    assert contract.asset_class == CRYPTO_PERP_ASSET_CLASS == "CRYPTO_PERP"
    assert contract.venue == VENUE
    assert contract.calendar_id == CALENDAR_ID
    assert contract.experiment_id == manifest.experiment_id
    assert contract.family_id == manifest.hypothesis_id
    assert contract.arm_id == f"{manifest.strategy_type}@v{manifest.candidate_version}"
    assert contract.arm_config_digest == manifest.config_sha256
    assert contract.cost_model_id == (
        "CRYPTO_COMPAT::taker_fee_bnb_v1::two_tick_v1::bundled_pit_v2"
    )
    assert contract.provider_schema_digest == hashlib.sha256(
        manifest.data_manifest_sha256.encode()
    ).hexdigest()


def test_adapter_uses_historical_validation_and_requires_venue_calendar():
    # venue / calendar_id have NO defaults: they must be named explicitly.
    with pytest.raises(TypeError):
        to_asset_contract(_manifest(), venue=VENUE)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        to_asset_contract(_manifest(), calendar_id=CALENDAR_ID)  # type: ignore[call-arg]
    # A payload the historical validator rejects is rejected identically.
    bad = _manifest_kwargs()
    del bad["git_commit"]
    with pytest.raises(ValueError, match="manifest_missing_field"):
        to_asset_contract(bad, venue=VENUE, calendar_id=CALENDAR_ID)


def test_dict_payload_and_object_produce_identical_contracts():
    manifest = _manifest()
    from_object = to_asset_contract(manifest, venue=VENUE, calendar_id=CALENDAR_ID)
    from_dict = to_asset_contract(
        manifest.to_dict(), venue=VENUE, calendar_id=CALENDAR_ID
    )
    assert from_object.contract.canonical_json() == from_dict.contract.canonical_json()
    assert from_object.legacy_manifest == from_dict.legacy_manifest


def test_null_seed_manifest_keeps_seed_unavailable_reason():
    manifest = _manifest(random_seed=None)
    result = to_asset_contract(manifest, venue=VENUE, calendar_id=CALENDAR_ID)
    assert result.legacy_payload["random_seed"] is None
    assert result.legacy_payload["random_seed_reason"] == "seed_unavailable"
    assert verify_roundtrip(result, manifest) == []
    rebuilt = normalize_legacy_manifest(result.legacy_payload)
    assert isinstance(rebuilt, ManifestSpec) and rebuilt.random_seed is None


def test_derived_cost_model_id_embeds_historical_values_verbatim():
    manifest = _manifest()
    cost_model_id = derive_cost_model_id(manifest)
    for value in (manifest.fee_model, manifest.slippage_model, manifest.funding_mode):
        assert value in cost_model_id
    other = to_asset_contract(
        _manifest(fee_model="maker_rebate_v1"), venue=VENUE, calendar_id=CALENDAR_ID
    )
    assert other.contract.cost_model_id != cost_model_id


# --- roundtrip identity through the real manifest IO -------------------------- #
def test_yaml_roundtrip_through_historical_io_is_identical(tmp_path):
    manifest = _manifest()
    result = to_asset_contract(manifest, venue=VENUE, calendar_id=CALENDAR_ID)

    # Write through the HISTORICAL writer, read back through the HISTORICAL
    # reader, and convert the reloaded payload again.
    path = write_manifest(manifest, tmp_path / "registry" / "manifest.yaml")
    reloaded = read_manifest(path)
    assert reloaded == manifest
    reconverted = to_asset_contract(reloaded, venue=VENUE, calendar_id=CALENDAR_ID)
    assert reconverted.contract.canonical_json() == result.contract.canonical_json()
    assert verify_roundtrip(reconverted, manifest) == []

    # The adapter's YAML bytes equal the historical writer's file bytes.
    assert yaml_bytes(result.legacy_payload) == path.read_text()


def test_roundtrip_preserves_every_historical_value(tmp_path):
    manifest = _manifest()
    result = to_asset_contract(manifest, venue=VENUE, calendar_id=CALENDAR_ID)
    assert verify_roundtrip(result, manifest) == []

    payload = legacy_payload(result.legacy_manifest)
    assert yaml.safe_load(yaml.safe_dump(payload)) == payload
    for field_name in ManifestSpec.REQUIRED_FIELDS:
        assert payload[field_name] == getattr(manifest, field_name), field_name

    # Double serialization determinism of the converted contract.
    once = result.contract.canonical_json()
    twice = to_asset_contract(
        normalize_legacy_manifest(result.legacy_payload),
        venue=VENUE,
        calendar_id=CALENDAR_ID,
    ).contract.canonical_json()
    assert once == twice
