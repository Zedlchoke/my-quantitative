"""Sprint V2 provenance tests (owner A3): immutable input snapshots.

Hand-verifiable, engine-free: freeze -> hash equality, tamper detection,
ManifestV2Spec validation incl. ``lock_not_before_run`` fail-closed path.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
import yaml

from contracts.protocol import ManifestV2Spec
from research.provenance import (
    SNAPSHOT_FILES,
    build_manifest_v2,
    snapshot_experiment_inputs,
    verify_frozen_snapshots,
)


@pytest.fixture()
def inputs(tmp_path):
    config = tmp_path / "research.yaml"
    config.write_text("strategy_type: ema_atr\nbacktest:\n  random_seed: 7\n", encoding="utf-8")
    candidate = tmp_path / "candidate.yaml"
    candidate.write_text("hypothesis_id: H-TEST-v1\n", encoding="utf-8")
    manifest = tmp_path / "coverage.json"
    manifest.write_text(json.dumps({"symbols": {"SOLUSDT": {"bars": {}}}}), encoding="utf-8")
    return config, candidate, manifest


def _snapshot(tmp_path, inputs, lock=None):
    config, candidate, manifest = inputs
    lock = lock or datetime.now(timezone.utc).isoformat()
    return snapshot_experiment_inputs(
        tmp_path / "EXP-TEST",
        config_path=config,
        candidate_path=candidate,
        universe_symbols=["SOLUSDT", "ETHUSDT"],
        requested_window=(datetime(2025, 8, 21, tzinfo=timezone.utc),
                          datetime(2026, 8, 21, tzinfo=timezone.utc)),
        data_manifest_path=manifest,
        parameter_lock_utc=lock,
        git_repo=tmp_path,
    )


def test_snapshot_freezes_bytes_and_hashes_match(inputs, tmp_path):
    snapshot = _snapshot(tmp_path, inputs)
    exp_dir = tmp_path / "EXP-TEST"
    frozen = exp_dir / "frozen"
    assert sorted(p.name for p in frozen.iterdir()) == [
        "candidate.yaml", "config.yaml", "data_manifest.json", "universe.json",
    ]
    # Frozen copies are byte-identical to the sources.
    config, candidate, manifest = inputs
    assert (frozen / "config.yaml").read_bytes() == config.read_bytes()
    assert (frozen / "candidate.yaml").read_bytes() == candidate.read_bytes()
    assert (frozen / "data_manifest.json").read_bytes() == manifest.read_bytes()

    from contracts.protocol import sha256_file

    assert snapshot["frozen_config_sha256"] == sha256_file(frozen / "config.yaml")
    assert snapshot["frozen_candidate_sha256"] == sha256_file(frozen / "candidate.yaml")
    assert snapshot["data_manifest_sha256"] == sha256_file(frozen / "data_manifest.json")
    assert snapshot["universe_snapshot_sha256"] == sha256_file(frozen / "universe.json")

    universe = json.loads((frozen / "universe.json").read_text(encoding="utf-8"))
    assert universe["symbols"] == ["SOLUSDT", "ETHUSDT"]
    assert universe["requested_window"]["start_utc"].startswith("2025-08-21T00:00:00")


def test_snapshot_captures_git_argv_and_timestamp_order(inputs, tmp_path):
    snapshot = _snapshot(tmp_path, inputs)
    assert set(snapshot["exact_argv"]) and all(
        isinstance(arg, str) for arg in snapshot["exact_argv"]
    )
    assert isinstance(snapshot["dirty_worktree_at_launch"], bool)
    # Lock timestamp must be strictly before run start.
    assert snapshot["parameter_lock_utc"] < snapshot["run_started_utc"]
    # Artifact-local frozen paths per PLAN section 7.
    assert snapshot["frozen_config_path"] == SNAPSHOT_FILES["frozen_config"]
    assert verify_frozen_snapshots(snapshot, tmp_path / "EXP-TEST") == []


def test_verify_detects_tampered_frozen_byte(inputs, tmp_path):
    snapshot = _snapshot(tmp_path, inputs)
    assert verify_frozen_snapshots(snapshot, tmp_path / "EXP-TEST") == []
    target = tmp_path / "EXP-TEST" / SNAPSHOT_FILES["frozen_candidate"]
    raw = target.read_bytes()
    target.write_bytes(raw.replace(b"H-TEST", b"H-TESX"))
    assert verify_frozen_snapshots(snapshot, tmp_path / "EXP-TEST") == ["hash_mismatch"]
    # Deleting a frozen file is also fail-closed.
    target.unlink()
    reasons = verify_frozen_snapshots(snapshot, tmp_path / "EXP-TEST")
    assert "manifest_missing_field" in reasons


def test_missing_source_is_fail_closed(inputs, tmp_path):
    config, candidate, manifest = inputs
    with pytest.raises(FileNotFoundError):
        snapshot_experiment_inputs(
            tmp_path / "E",
            config_path=tmp_path / "does_not_exist.yaml",
            candidate_path=candidate,
            universe_symbols=["SOLUSDT"],
            requested_window=("2025-08-21T00:00:00+00:00", "2026-08-21T00:00:00+00:00"),
            data_manifest_path=manifest,
            parameter_lock_utc=datetime.now(timezone.utc).isoformat(),
            git_repo=tmp_path,
        )


def _spec_fields(snapshot, **overrides):
    run_started = datetime.fromisoformat(snapshot["run_started_utc"])
    fields = {
        "experiment_id": "EXP-20260823-9999",
        "matrix_id": "MATRIX-V2-TEST",
        "hypothesis_id": "H-EXISTING-ema_atr-v1",
        "candidate_version": 1,
        "strategy_type": "ema_atr",
        "owner_agent": "A2",
        "validator_agent": "A3",
        "actual_start_utc": snapshot["requested_start_utc"],
        "actual_end_utc": snapshot["requested_end_utc"],
        "continuous_clean_intersection": None,
        "split_policy": "chrono_wf3fold_warmup10d_20250821-20260821",
        "warmup_bars": 960,
        "purge_bars": 0,
        "embargo_bars": 0,
        "outer_folds": 3,
        "declared_parameter_combinations": 1,
        "executed_parameter_combinations": 1,
        "prior_family_trials": 0,
        "fee_model": "maker_taker",
        "slippage_model": "one_tick_slippage",
        "funding_mode": "audited-post-trade",
        "random_seed": 7,
    }
    fields.update(overrides)
    return build_manifest_v2(snapshot, **fields)


def test_manifest_v2_spec_validates_from_snapshot(inputs, tmp_path):
    snapshot = _snapshot(tmp_path, inputs)
    spec = _spec_fields(snapshot)
    assert isinstance(spec, ManifestV2Spec)
    assert spec.schema_version == 2
    assert spec.validate() == []
    payload = spec.to_dict()
    assert payload["git_commit_at_launch"] == snapshot["git_commit_at_launch"]
    assert payload["exact_argv"] == tuple(snapshot["exact_argv"])
    # YAML round-trip keeps the lock ordering check meaningful.
    restored = yaml.safe_load(yaml.safe_dump(payload))
    assert restored["parameter_lock_utc"] < restored["run_started_utc"]


@pytest.mark.parametrize("offset_seconds", [0, 1])
def test_lock_not_before_run_is_rejected(inputs, tmp_path, offset_seconds):
    snapshot = _snapshot(tmp_path, inputs)
    run_started = datetime.fromisoformat(snapshot["run_started_utc"])
    bad_lock = (run_started + timedelta(seconds=offset_seconds)).isoformat()
    spec = _spec_fields(snapshot, parameter_lock_utc=bad_lock)
    assert spec.validate() == ["lock_not_before_run"]


def test_lock_one_second_before_run_is_accepted(inputs, tmp_path):
    snapshot = _snapshot(tmp_path, inputs)
    run_started = datetime.fromisoformat(snapshot["run_started_utc"])
    good_lock = (run_started - timedelta(seconds=1)).isoformat()
    spec = _spec_fields(snapshot, parameter_lock_utc=good_lock)
    assert spec.validate() == []
