"""A3 manifest tests: build/validate, monotonic IDs, YAML roundtrip."""

from __future__ import annotations

import pytest

from contracts.protocol import ManifestSpec
from research.protocol.manifest import (
    build_manifest,
    manifest_seed_reason,
    next_experiment_id,
    read_manifest,
    write_manifest,
)


def _kwargs() -> dict:
    base = {name: "x" for name in (
        "hypothesis_id", "strategy_type", "owner_agent", "validator_agent",
        "git_commit", "config_path", "config_sha256", "data_snapshot_id",
        "data_manifest_sha256", "universe_snapshot", "actual_start_utc",
        "actual_end_utc", "common_intersection", "split_policy", "fee_model",
        "slippage_model", "funding_mode", "parameter_lock_utc", "command",
        "experiment_id",
    )}
    return {
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
    }


def test_build_manifest_valid_and_typed():
    manifest = build_manifest(**_kwargs())
    assert isinstance(manifest, ManifestSpec)
    assert manifest.random_seed == 42
    assert manifest.candidate_version == 1
    assert manifest.validate() == []


def test_build_manifest_missing_fields_raise_with_reason():
    kwargs = _kwargs()
    del kwargs["git_commit"]
    del kwargs["split_policy"]
    with pytest.raises(ValueError, match="manifest_missing_field"):
        build_manifest(**kwargs)


def test_build_manifest_unknown_field_rejected():
    with pytest.raises(ValueError, match="unknown fields"):
        build_manifest(**{**_kwargs(), "not_a_field": 1})


def test_null_seed_allowed_and_reason_recorded():
    kwargs = _kwargs()
    kwargs["random_seed"] = None
    manifest = build_manifest(**kwargs)
    assert manifest.random_seed is None
    assert manifest.validate() == []
    assert manifest_seed_reason(manifest) == "seed_unavailable"


def test_experiment_id_monotonic_counter(tmp_path):
    first = next_experiment_id(tmp_path)
    second = next_experiment_id(tmp_path)
    third = next_experiment_id(tmp_path)
    assert first.startswith("EXP-") and len(first.split("-")[-1]) == 4
    ordinals = [int(x.split("-")[-1]) for x in (first, second, third)]
    assert ordinals == sorted(ordinals) and len(set(ordinals)) == 3
    counter = (tmp_path / "counter.txt").read_text()
    assert int(counter) == 3


def test_manifest_yaml_roundtrip_preserves_types(tmp_path):
    manifest = build_manifest(**_kwargs())
    path = write_manifest(manifest, tmp_path / "nested" / "manifest.yaml")
    loaded = read_manifest(path)
    assert loaded == manifest
    assert isinstance(loaded.warmup_bars, int)
    assert isinstance(loaded.dirty_worktree, bool)
    assert loaded.random_seed == 42

    null_kwargs = _kwargs()
    null_kwargs["random_seed"] = None
    null_manifest = build_manifest(**null_kwargs)
    null_path = write_manifest(null_manifest, tmp_path / "m2.yaml")
    text = null_path.read_text()
    assert "random_seed_reason: seed_unavailable" in text
    reloaded = read_manifest(null_path)
    assert reloaded.random_seed is None


def test_read_manifest_rejects_unknown_or_missing_fields(tmp_path):
    manifest = build_manifest(**_kwargs())
    path = write_manifest(manifest, tmp_path / "manifest.yaml")
    text = path.read_text()
    (tmp_path / "bad_unknown.yaml").write_text(text + "sneaky: 1\n")
    with pytest.raises(ValueError, match="unknown fields"):
        read_manifest(tmp_path / "bad_unknown.yaml")

    stripped = "\n".join(
        line for line in text.splitlines() if not line.startswith("git_commit")
    )
    (tmp_path / "bad_missing.yaml").write_text(stripped + "\n")
    with pytest.raises(ValueError, match="manifest_missing_field"):
        read_manifest(tmp_path / "bad_missing.yaml")


def test_read_manifest_requires_seed_reason_for_null_seed(tmp_path):
    kwargs = _kwargs()
    kwargs["random_seed"] = None
    path = write_manifest(build_manifest(**kwargs), tmp_path / "seedless.yaml")
    text = path.read_text().replace("random_seed_reason: seed_unavailable\n", "")
    (tmp_path / "no_reason.yaml").write_text(text)
    with pytest.raises(ValueError, match="seed_unavailable"):
        read_manifest(tmp_path / "no_reason.yaml")
