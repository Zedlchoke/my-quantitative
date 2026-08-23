"""Sprint V3 launch-provenance + LeakageEvidence tests (owner A3).

Covers the D1/D2 runner flow WITHOUT the Nautilus engine: fake walk-forward
payloads, real frozen snapshots, real RunLaunchManifest build/write/validate,
real LeakageEvidence emission -- including the fail-closed paths
(manifest invalid => cell aborted BEFORE engine; missing ledger timestamps =>
EVIDENCE_MISSING).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

import research.matrix_runner as mr
import research.protocol.manifest as manifest_mod
from contracts.protocol import SCORED_EXECUTION_MODE


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    registry_dir = tmp_path / "registry"
    monkeypatch.setattr(manifest_mod, "DEFAULT_REGISTRY_DIR", registry_dir)
    contract = tmp_path / "data_contract_v2.json"
    contract.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
    monkeypatch.setattr(mr, "_DATA_MANIFEST_CACHE", None)
    monkeypatch.setattr(mr, "_data_manifest_source", lambda: contract)
    return tmp_path


def _fake_walk_forward(rows=None):
    def _run(plan):
        return {
            "window_actual": {
                "start_utc": "2025-08-21T14:30:00+00:00",
                "end_utc": "2026-08-21T00:00:00+00:00",
            },
            "data_bounds": {"first_bar_utc": "a", "last_bar_utc": "b"},
            "snapshot_id": "snap",
            "total_trades": len(rows or []),
            "positive_folds": 1,
            "total_pnl": 1.0,
            "pnl_after_funding": 0.9,
            "expectancy_after_funding": 0.45,
            "positions_stats": {
                "trades": len(rows or []),
                "gross_profit": 1.0, "gross_loss": 0.1, "net_pnl": 0.9,
                "profit_factor": 10.0, "pf_reason": None,
            },
            "positions_digest": "0" * 64,
            "positions_rows": rows if rows is not None else [],
            "observations": [],
            "folds": [
                {
                    "fold": i,
                    "start_utc": "2025-08-21T14:30:00+00:00",
                    "end_utc": "2026-08-21T00:00:00+00:00",
                    "bars_incl_warmup": 1000 + i,
                    "scored_bars": 900,
                }
                for i in range(3)
            ],
        }

    return _run


def _ctx(tmp_path, experiment_id="EXP-V3TEST-0001", strategy_type=None):
    return mr.CellLaunchContext(
        experiment_id=experiment_id,
        matrix_id="v3_test",
        stage_a_root=tmp_path / "stage_a_v3",
        batch_launch_utc=mr.utc_now_iso(),
        declared_variants_by_type={
            strategy_type or "ema_atr": 1,
            mr.VOLCOMP_STRATEGY_TYPE: 4,
            mr.FUNDCROWD_STRATEGY_TYPE: 3,
        },
    )


def _plan(strategy_type="ema_atr", variant="base"):
    return mr.make_plan(
        strategy_type,
        "SOLUSDT",
        tier=1,
        folds=3,
        window_start=pd.Timestamp("2025-08-21T14:30Z"),
        window_end=pd.Timestamp("2026-08-21T00:00Z"),
        param_variant=variant,
    )


# ------------------------------ D1 ------------------------------------------- #
def test_existing_strategy_cell_writes_validated_launch_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "execute_cell", _fake_walk_forward())
    ctx = _ctx(tmp_path)
    out = mr.execute_cell_scored(_plan(), ctx)

    manifest_path = Path(out["provenance"]["launch_manifest_path"])
    assert manifest_path.is_file()
    raw = yaml.safe_load(manifest_path.read_text())
    assert raw["schema_version"] == 3
    assert raw["hypothesis_id"] == "H-EXISTING-ema_atr-v1"
    assert raw["owner_agent"] == "A2"
    assert raw["validator_agent"] == "A3"
    assert raw["execution_mode"] == SCORED_EXECUTION_MODE.value == "NEXT_BAR_EVENT_BASELINE"
    assert raw["candidate_locked_at_utc"] <= raw["backtest_run_started_utc"]
    assert raw["backtest_run_finished_utc"] is not None
    # Runtime config (YAML file) and candidate spec (generated doc) differ.
    assert raw["runtime_config_sha256"] != raw["candidate_spec_sha256"]
    frozen = Path(raw["runtime_config_path"])
    assert (manifest_path.parent / frozen).is_file()
    assert mr.read_launch_manifest(manifest_path).experiment_id == ctx.experiment_id


def test_hypothesis_cell_uses_candidate_yaml_identity_and_owner_a4(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "execute_cell", _fake_walk_forward())
    ctx = _ctx(tmp_path, strategy_type=mr.VOLCOMP_STRATEGY_TYPE)
    out = mr.execute_cell_scored(_plan(mr.VOLCOMP_STRATEGY_TYPE, "v0"), ctx)

    prov = out["provenance"]
    assert prov["hypothesis_id"] == "H-VOLCOMP-BRKOUT-v1"
    assert prov["candidate_version"] == 1
    assert prov["owner_agent"] == "A4"
    assert prov["declared_family_trials"] == 4
    # executed_family_trials recorded at LAUNCH time (before this run): 0.
    assert prov["executed_family_trials"] == 0
    # The shared batch counter increments after completion.
    assert ctx.family_counters["H-VOLCOMP-BRKOUT-v1"] == 1
    raw = yaml.safe_load(Path(prov["launch_manifest_path"]).read_text())
    assert raw["runtime_config_sha256"] != raw["candidate_spec_sha256"]
    candidate = yaml.safe_load(
        (Path(prov["launch_manifest_path"]).parent / "frozen/candidate.yaml").read_text()
    )
    assert candidate["hypothesis_id"] == "H-VOLCOMP-BRKOUT-v1"


def test_manifest_invalid_aborts_cell_before_engine_run(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        mr, "execute_cell", lambda plan: calls.append(plan) or (_ for _ in ()).throw(AssertionError("must not run"))
    )
    # funding_crowding's frozen lock stamp (2026-08-24T03:30Z) is AFTER any
    # launch time before then -> validate() must fail with lock_not_before_run.
    ctx = _ctx(tmp_path, strategy_type=mr.FUNDCROWD_STRATEGY_TYPE)
    with pytest.raises(mr.LaunchManifestInvalid) as excinfo:
        mr.execute_cell_scored(_plan(mr.FUNDCROWD_STRATEGY_TYPE, "v0"), ctx)
    assert excinfo.value.reasons == ["lock_not_before_run"]
    assert calls == []  # engine NEVER ran


def test_same_source_runtime_and_candidate_rejected(tmp_path):
    runtime = tmp_path / "config.yaml"
    runtime.write_text("strategy_type: ema_atr\n", encoding="utf-8")
    with pytest.raises(ValueError, match="config_candidate_same_source"):
        mr.snapshot_frozen_v3(
            tmp_path / "exp",
            runtime_config_source=runtime,
            candidate_source=runtime,
            universe_symbols=["SOLUSDT"],
            window_start="2025-08-21T14:30Z",
            window_end="2026-08-21T00:00Z",
            data_manifest_source=mr._data_manifest_source(),
        )


def test_snapshot_hashes_match_written_bytes(tmp_path):
    runtime = tmp_path / "config.yaml"
    payload = b"strategy_type: ema_atr\n"
    runtime.write_bytes(payload)
    snapshot = mr.snapshot_frozen_v3(
        tmp_path / "exp",
        runtime_config_source=runtime,
        candidate_bytes=b"spec_kind: existing_strategy_generated\n",
        universe_symbols=["SOLUSDT"],
        window_start="2025-08-21T14:30Z",
        window_end="2026-08-21T00:00Z",
        data_manifest_source=mr._data_manifest_source(),
    )
    from contracts.protocol import sha256_file

    exp = tmp_path / "exp"
    assert sha256_file(exp / "frozen/runtime_config.yaml") == snapshot["runtime_config_sha256"]
    assert sha256_file(exp / "frozen/candidate.yaml") == snapshot["candidate_spec_sha256"]
    assert sha256_file(exp / "frozen/data_manifest.json") == snapshot["data_manifest_sha256"]
    assert sha256_file(exp / "frozen/universe.json") == snapshot["universe_sha256"]
    universe = json.loads((exp / "frozen/universe.json").read_text())
    assert universe["symbols"] == ["SOLUSDT"]
    assert universe["scored_window"]["start_utc"].startswith("2025-08-21T14:30")


def test_family_counters_increment_across_batch(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "execute_cell", _fake_walk_forward())
    ctx = _ctx(tmp_path, strategy_type=mr.VOLCOMP_STRATEGY_TYPE)
    for i in range(2):
        mr.execute_cell_scored(_plan(mr.VOLCOMP_STRATEGY_TYPE, f"v{i}"), ctx)
    assert ctx.family_counters["H-VOLCOMP-BRKOUT-v1"] == 2


# ------------------------------ D2 ------------------------------------------- #
def test_leakage_evidence_complete_when_ledger_has_timestamps(tmp_path, monkeypatch):
    rows = [
        {
            "signal_ts": "2025-12-01T00:00:00+00:00",
            "submit_ts": "2025-12-01T00:05:00+00:00",
            "fill_ts": "2025-12-01T00:15:00+00:00",
            "execution_mode": "NEXT_BAR_EVENT_BASELINE",
            "pnl_after_funding": 1.0,
        },
        {
            "signal_ts": "2026-02-01T00:00:00+00:00",
            "submit_ts": "2026-02-01T00:05:00+00:00",
            "fill_ts": "2026-02-01T00:15:00+00:00",
            "execution_mode": "NEXT_BAR_EVENT_BASELINE",
            "pnl_after_funding": -0.1,
        },
    ]
    monkeypatch.setattr(mr, "execute_cell", _fake_walk_forward(rows))
    out = mr.execute_cell_scored(_plan(), _ctx(tmp_path))
    evidence = out["leakage_evidence"]
    ordering = evidence.execution_ordering
    assert ordering["evidence_class"] == "EXECUTION_EVIDENCE_COMPLETE"
    assert ordering["entries"] == 2
    assert ordering["violations"] == 0
    assert evidence.transform_evidence["status"] == "NOT_APPLICABLE"
    assert "no learned transform" in evidence.transform_evidence["reason"]
    assert evidence.universe_freeze["universe_sha256"]
    assert evidence.warmup_boundaries["warmup_start"] < evidence.warmup_boundaries["scored_start"]
    execution_evidence = json.loads(
        (ctx_exp_dir(tmp_path) / "execution_evidence.json").read_text()
    )
    assert execution_evidence["leakage_evidence"]["split_policy_declared"] is True


def ctx_exp_dir(tmp_path):
    return tmp_path / "stage_a_v3" / "EXP-V3TEST-0001"


def test_leakage_evidence_missing_when_ledger_lacks_timestamps(tmp_path, monkeypatch):
    rows = [{"pnl_after_funding": 1.0, "signal_ts": None, "fill_ts": None}]
    monkeypatch.setattr(mr, "execute_cell", _fake_walk_forward(rows))
    out = mr.execute_cell_scored(_plan(), _ctx(tmp_path))
    ordering = out["leakage_evidence"].execution_ordering
    assert ordering["evidence_class"] == "EVIDENCE_MISSING"
    assert ordering["missing_timestamp_rows"] == 1


def test_leakage_evidence_missing_for_empty_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "execute_cell", _fake_walk_forward([]))
    out = mr.execute_cell_scored(_plan(), _ctx(tmp_path))
    assert (
        out["leakage_evidence"].execution_ordering["evidence_class"]
        == "EVIDENCE_MISSING"
    )


def test_ordering_violation_detected_on_backwards_timestamps(tmp_path, monkeypatch):
    rows = [
        {
            "signal_ts": "2025-12-01T00:20:00+00:00",
            "fill_ts": "2025-12-01T00:15:00+00:00",  # filled BEFORE signal!
        }
    ]
    ordering = mr.evaluate_execution_ordering(rows)
    assert ordering["violations"] == 1
    assert ordering["evidence_class"] == "ORDERING_VIOLATION_DETECTED"


# --------------------- inventory rebuild identity ---------------------------- #
def test_load_inventory_plans_preserves_frozen_identities(tmp_path):
    inventory = {
        "schema_version": 1,
        "declared_cells": 1,
        "cells": [
            {
                "identity_key": None,
                "identity": {
                    "strategy_type": "reclaim_mr",
                    "symbol": "ADAUSDT",
                    "param_variant": "base",
                    "config_sha256": None,
                    "data_snapshot_id": None,
                    "split_policy": None,
                    "fee_model": "maker_taker",
                    "slippage_model": "one_tick_slippage",
                    "seed": 42,
                },
            }
        ],
    }
    plan = mr.make_plan(
        "reclaim_mr", "ADAUSDT", tier=1, folds=3,
        window_start=pd.Timestamp("2025-08-21T14:30Z"),
        window_end=pd.Timestamp("2026-08-21T00:00Z"),
    )
    ident = plan.identity(
        fee_model="maker_taker", slippage_model="one_tick_slippage", seed=42,
        snapshot_id=mr.data_snapshot_id(
            "./catalog_live_crypto", "ADAUSDT",
            pd.Timestamp("2025-08-21T14:30Z"), pd.Timestamp("2026-08-21T00:00Z"),
        ),
    )
    inventory["cells"][0]["identity_key"] = plan.identity_key(ident)
    inventory["cells"][0]["identity"]["config_sha256"] = plan.config_sha256
    inventory["cells"][0]["identity"]["data_snapshot_id"] = ident["data_snapshot_id"]
    inventory["cells"][0]["identity"]["split_policy"] = plan.split_policy
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(inventory), encoding="utf-8")

    plans, variants = mr.load_inventory_plans(
        path,
        tier=1,
        folds=3,
        window_start=pd.Timestamp("2025-08-21T14:30Z"),
        window_end=pd.Timestamp("2026-08-21T00:00Z"),
    )
    assert len(plans) == 1
    assert variants == {"reclaim_mr": 1}
    rebuilt = plans[0].identity_key(plans[0].identity(
        fee_model="maker_taker", slippage_model="one_tick_slippage", seed=42,
        snapshot_id=ident["data_snapshot_id"],
    ))
    assert rebuilt == inventory["cells"][0]["identity_key"]


def test_inventory_identity_drift_raises(tmp_path):
    plan = mr.make_plan(
        "reclaim_mr", "ADAUSDT", tier=1, folds=3,
        window_start=pd.Timestamp("2025-08-21T14:30Z"),
        window_end=pd.Timestamp("2026-08-21T00:00Z"),
    )
    inventory = {
        "schema_version": 1,
        "declared_cells": 1,
        "cells": [
            {
                "identity_key": plan.identity_key(plan.identity(
                    fee_model="maker_taker", slippage_model="one_tick_slippage",
                    seed=43, snapshot_id="WRONG",
                )),
                "identity": {"strategy_type": "reclaim_mr", "symbol": "ADAUSDT",
                             "param_variant": "base",
                             "fee_model": "maker_taker",
                             "slippage_model": "one_tick_slippage",
                             "seed": 43,
                             "config_sha256": "f" * 64,
                             "data_snapshot_id": "WRONG",
                             "split_policy": "x"},
            }
        ],
    }
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(inventory), encoding="utf-8")
    with pytest.raises(ValueError, match="identity drift"):
        mr.load_inventory_plans(
            path, tier=1, folds=3,
            window_start=pd.Timestamp("2025-08-21T14:30Z"),
            window_end=pd.Timestamp("2026-08-21T00:00Z"),
        )
