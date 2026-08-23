"""A3 rerun-harness tests (comparison logic via injected runner — no engine)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from contracts.protocol import GateId, GateVerdict
from research.protocol.manifest import build_manifest, write_manifest
from research.protocol.reproduce import (
    digest_from_wf_summary,
    reproduce_from_manifest,
)
from research.protocol.registry import append


def _manifest_kwargs(config_path, config_sha256):
    base = {name: "x" for name in (
        "hypothesis_id", "strategy_type", "owner_agent", "validator_agent",
        "git_commit", "data_snapshot_id", "data_manifest_sha256",
        "universe_snapshot", "actual_start_utc", "actual_end_utc",
        "common_intersection", "split_policy", "fee_model", "slippage_model",
        "funding_mode", "parameter_lock_utc", "command",
    )}
    return {
        **base,
        "experiment_id": "EXP-20260823-0001",
        "strategy_type": "reclaim_mr",
        "config_path": str(config_path),
        "config_sha256": config_sha256,
        "candidate_version": 1,
        "dirty_worktree": False,
        "warmup_bars": 0,
        "purge_bars": 0,
        "embargo_bars": 0,
        "outer_folds": 1,
        "parameter_combinations": 1,
        "prior_family_trials": 0,
        "random_seed": None,
    }


def _summary(trades=5, pnl=123.456):
    return {
        "strategy_type": "reclaim_mr",
        "symbols": ["ETHUSDT"],
        "folds": 1,
        "cells": [
            {"symbol": "ETHUSDT", "fold": 0, "trades": trades,
             "pnl": pnl, "pnl_after_funding": pnl}
        ],
    }


def _setup(tmp_path, summary):
    config = tmp_path / "cfg.yaml"
    config.write_text("strategy_type: reclaim_mr\n")
    from contracts.protocol import sha256_file

    manifest = build_manifest(
        **_manifest_kwargs(config, sha256_file(config))
    )
    manifest_path = write_manifest(manifest, tmp_path / "manifest.yaml")
    registry = tmp_path / "registry.jsonl"
    entry = {
        "experiment_id": manifest.experiment_id,
        "verdict": "INCONCLUSIVE",
        "symbol": "ETHUSDT",
        "canonical": {
            "trades": summary["cells"][0]["trades"],
            "net_canonical_pnl": summary["cells"][0]["pnl_after_funding"],
            "positions_digest": digest_from_wf_summary(summary),
        },
    }
    append(entry, registry)
    return manifest_path, registry


def test_reproduce_passes_on_identical_rerun(tmp_path):
    summary = _summary()
    manifest_path, registry = _setup(tmp_path, summary)
    seen = {}

    def runner(config_path, strategy_type, symbols, folds, output):
        seen.update(symbols=symbols, folds=folds)
        Path(output).write_text(json.dumps(summary))
        return summary

    result = reproduce_from_manifest(
        manifest_path, tmp_path / "work", registry_path=registry, runner=runner
    )
    assert result.gate is GateId.G2_REPRODUCIBILITY
    assert result.verdict is GateVerdict.PASS and result.reasons == ()
    assert seen["symbols"] == ("ETHUSDT",) and seen["folds"] == 1


def test_reproduce_flags_pnl_mismatch_beyond_relative_tolerance(tmp_path):
    manifest_path, registry = _setup(tmp_path, _summary())
    drifted = _summary(pnl=123.456 * (1 + 1e-3))

    result = reproduce_from_manifest(
        manifest_path,
        tmp_path / "work",
        registry_path=registry,
        runner=lambda *args, **kw: drifted,
    )
    assert result.verdict is GateVerdict.FAIL
    assert "rerun_pnl_mismatch" in result.reasons


def test_reproduce_digest_strict_even_within_pnl_tolerance(tmp_path):
    """PnL tolerance never weakens the positions-digest equality rule."""
    manifest_path, registry = _setup(tmp_path, _summary())
    noise = _summary(pnl=123.456 * (1 + 1e-9))
    result = reproduce_from_manifest(
        manifest_path,
        tmp_path / "work",
        registry_path=registry,
        runner=lambda *args, **kw: noise,
    )
    assert result.verdict is GateVerdict.FAIL
    assert result.reasons == ("rerun_positions_mismatch",)


def test_reproduce_flags_positions_mismatch_on_trades_or_digest(tmp_path):
    manifest_path, registry = _setup(tmp_path, _summary())

    different_trades = reproduce_from_manifest(
        manifest_path,
        tmp_path / "w1",
        registry_path=registry,
        runner=lambda *a, **k: _summary(trades=7),
    )
    assert "rerun_positions_mismatch" in different_trades.reasons

    same_metrics_new_cells = {
        "strategy_type": "reclaim_mr",
        "symbols": ["ETHUSDT"],
        "folds": 1,
        "cells": [
            {"symbol": "ETHUSDT", "fold": 0, "trades": 5, "pnl": 123.456,
             "pnl_after_funding": 123.456, "bars": 99999}
        ],
    }
    different_digest = reproduce_from_manifest(
        manifest_path,
        tmp_path / "w2",
        registry_path=registry,
        runner=lambda *a, **k: same_metrics_new_cells,
    )
    assert different_digest.verdict is GateVerdict.FAIL
    assert "rerun_positions_mismatch" in different_digest.reasons


def test_reproduce_detects_config_hash_drift(tmp_path):
    manifest_path, registry = _setup(tmp_path, _summary())
    config = None
    for candidate in tmp_path.glob("cfg.yaml"):
        config = candidate
    config.write_text("strategy_type: reclaim_mr\n# tampered\n")

    result = reproduce_from_manifest(
        manifest_path,
        tmp_path / "work",
        registry_path=registry,
        runner=lambda *a, **k: _summary(),
    )
    assert result.verdict is GateVerdict.FAIL
    assert "hash_mismatch" in result.reasons


def test_reproduce_without_baseline_evidence_is_not_yet_tested(tmp_path):
    config = tmp_path / "cfg.yaml"
    config.write_text("a: 1\n")
    from contracts.protocol import sha256_file

    kwargs = _manifest_kwargs(config, sha256_file(config))
    kwargs["experiment_id"] = "EXP-20260823-9999"
    manifest_path = write_manifest(build_manifest(**kwargs), tmp_path / "m.yaml")
    empty_registry = tmp_path / "empty.jsonl"

    result = reproduce_from_manifest(
        manifest_path,
        tmp_path / "work",
        registry_path=empty_registry,
        runner=lambda *a, **k: pytest.fail("must not run without baseline"),
    )
    assert result.verdict is GateVerdict.NOT_YET_TESTED
    assert "metric_not_computed" in result.reasons
