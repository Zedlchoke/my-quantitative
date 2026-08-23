"""Sprint V2 evaluation bridge tests (owner A3): engine-free, hand-built
matrix artifacts -> frozen provenance -> gates -> artifacts -> comparison."""

from __future__ import annotations

import hashlib
import json

import pytest
import yaml

import research.protocol.manifest as manifest_mod
import research.protocol.registry as registry_mod
from contracts.protocol import GateId, GateVerdict, canonical_json, sha256_text
from research.sprint_eval import evaluate_matrix_v2


WINDOW_START = "2025-08-21T00:00:00+00:00"
WINDOW_END = "2026-08-21T00:00:00+00:00"


def _positions(trades_per_fold: int, winners: int):
    """rows for one fold: ``winners`` x +1.0 then rest x -1.0."""
    rows = []
    for i in range(trades_per_fold):
        pnl = 1.0 if i < winners else -1.0
        rows.append(
            {
                "instrument_id": "SOLUSDT-PERP.BINANCE",
                "side": "LONG",
                "qty": 0.01,
                "entry_ts": WINDOW_START,
                "exit_ts": f"2026-01-01T00:00:{i:02d}+00:00",
                "realized_pnl_gross": pnl,
                "commission": None,
                "funding_net": 0.0,
                "pnl_after_funding": pnl,
            }
        )
    return rows


def _cell_document(tmp_path, *, symbol="SOLUSDT", trades_per_fold=10, winners=7):
    folds_rows = []
    folds_payload = []
    for fold in range(3):
        rows = [
            {**row, "exit_ts": f"2026-0{fold + 1}-01T00:00:{i:02d}+00:00"}
            for i, row in enumerate(_positions(trades_per_fold, winners))
        ]
        folds_rows.extend(rows)
        fold_net = sum(r["pnl_after_funding"] for r in rows)
        gp = sum(r["pnl_after_funding"] for r in rows if r["pnl_after_funding"] > 0)
        gl = abs(sum(r["pnl_after_funding"] for r in rows if r["pnl_after_funding"] < 0))
        folds_payload.append(
            {
                "fold": fold,
                "bars_incl_warmup": 12640,
                "scored_bars": 11680,
                "trades": trades_per_fold,
                "pnl": fold_net,
                "expectancy": fold_net / trades_per_fold,
                "profit_factor": gp / gl if gl else None,
                "win_rate": winners / trades_per_fold,
                "funding_available": True,
                "reason_codes": [],
                "trades_after_funding": trades_per_fold,
                "pnl_after_funding": fold_net,
                "expectancy_after_funding": fold_net / trades_per_fold,
                "profit_factor_after_funding": gp / gl if gl else None,
                "positions_stats": {
                    "trades": trades_per_fold,
                    "gross_profit": gp,
                    "gross_loss": gl,
                    "net_pnl": fold_net,
                    "profit_factor": gp / gl if gl else None,
                    "pf_reason": None if gl else "no_losing_positions",
                },
            }
        )
    total_trades = len(folds_rows)
    gp = sum(r["pnl_after_funding"] for r in folds_rows if r["pnl_after_funding"] > 0)
    gl = abs(sum(r["pnl_after_funding"] for r in folds_rows if r["pnl_after_funding"] < 0))
    net = sum(r["pnl_after_funding"] for r in folds_rows)
    config_path = tmp_path / "research.yaml"
    config_path.write_text("strategy_type: ema_atr\n", encoding="utf-8")
    return {
        "document": {
            "schema_version": 1,
            "generated_at_utc": "2026-08-23T00:00:00+00:00",
            "tier": 1,
            "identity": {
                "strategy_type": "ema_atr",
                "symbol": symbol,
                "param_variant": "base",
                "config_sha256": "f" * 64,
                "data_snapshot_id": "catalog|SYM|20250821|20260821",
                "split_policy": "chrono_wf3fold",
                "fee_model": "maker_taker",
                "slippage_model": "one_tick_slippage",
                "seed": 42,
            },
            "cell_result": {"status": "COMPLETED"},
            "plan": {
                "config_path": str(config_path),
                "config_sha256": "f" * 64,
                "catalog_path": "./catalog_live_crypto",
                "funding_path": "funding_data/scan_2026",
                "folds": 3,
                "warmup_days": 10,
                "window_declared": {"start_utc": WINDOW_START, "end_utc": WINDOW_END},
                "split_policy": "chrono_wf3fold_warmup10d_20250821-20260821",
            },
            "window_actual": {"start_utc": WINDOW_START, "end_utc": WINDOW_END},
            "total_trades": total_trades,
            "positive_folds": 3,
            "total_pnl": net,
            "pnl_after_funding": round(net, 6),
            "expectancy_after_funding": net / total_trades if total_trades else None,
            "positions_stats": {
                "trades": total_trades,
                "gross_profit": gp,
                "gross_loss": gl,
                "net_pnl": net,
                "profit_factor": gp / gl if gl else None,
                "pf_reason": None if gl else "no_losing_positions",
            },
            "positions_digest": sha256_text(canonical_json(folds_rows)),
            "observations": [],
            "folds": folds_payload,
        },
        "positions": folds_rows,
    }


def _coverage(symbol="SOLUSDT", gaps=0):
    entry = {
        "instrument_metadata_present": True,
        "bars": {
            "duplicate_timestamps": 0,
            "gaps_over_interval": gaps,
            "gap_details": (
                [{
                    "after_ts_utc": "2025-08-21T02:00:00+00:00",
                    "before_ts_utc": "2025-08-21T09:00:00+00:00",
                    "gap_minutes": 420.0,
                }] if gaps else []
            ),
        },
        "funding": {
            "bundle_present": True,
            "covers_declared_window": True,
            "coverage_ratio": 1.0,
        },
    }
    return {"schema_version": 1, "symbols": {symbol: entry}}


@pytest.fixture()
def env(tmp_path, monkeypatch):
    registry_dir = tmp_path / "registry"
    monkeypatch.setattr(manifest_mod, "DEFAULT_REGISTRY_DIR", registry_dir)
    monkeypatch.setattr(
        registry_mod, "DEFAULT_REGISTRY_DIR", registry_dir
    )
    monkeypatch.setattr(
        registry_mod, "DEFAULT_REGISTRY_PATH", registry_dir / "experiments.jsonl"
    )
    return tmp_path


def _write_matrix(tmp_path, name, docs):
    cells_dir = tmp_path / name / "cells"
    cells_dir.mkdir(parents=True)
    index_cells = {}
    for strategy, symbol, variant, bundle in docs:
        stem = f"{strategy}__{symbol}__{variant}"
        artifact = cells_dir / f"{stem}.json"
        artifact.write_text(json.dumps(bundle["document"]), encoding="utf-8")
        ledger = cells_dir / f"{stem}.positions.jsonl"
        ledger.write_text(
            "".join(json.dumps(r) + "\n" for r in bundle["positions"]), encoding="utf-8"
        )
        index_cells[stem] = {
            "artifact_path": str(artifact),
            "status": "COMPLETED",
            "identity": bundle["document"]["identity"],
        }
    (tmp_path / name / "index.json").write_text(
        json.dumps({"schema_version": 1, "cells": index_cells}), encoding="utf-8"
    )
    (tmp_path / name / "report.json").write_text(
        json.dumps({"matrix_id": name, "declared_cells": len(docs)}), encoding="utf-8"
    )


def test_v2_eval_full_pipeline_pass(env):
    tmp_path = env
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps(_coverage()), encoding="utf-8")
    _write_matrix(tmp_path, "m_v2", [("ema_atr", "SOLUSDT", "base", _cell_document(tmp_path))])

    payload = evaluate_matrix_v2(
        str(tmp_path / "m_v2"),
        output_root=str(tmp_path / "stage_a_v2"),
        coverage_path=str(coverage_file),
    )
    assert payload["evaluated"] == 1 and payload["pass"] == 1
    row = payload["rows"][0]
    assert row["verdict"] == "CANDIDATE_PASS"
    # Position-level PF: 21 wins / 9 losses across 30 trades.
    assert row["pf_position_level"] == pytest.approx(21.0 / 9.0)
    assert row["exp_after_cost"] == pytest.approx(12.0 / 30.0)

    exp_dir = tmp_path / "stage_a_v2" / row["experiment_id"]
    for name in (
        "manifest.yaml", "canonical_metrics.json", "gate_result.json",
        "scorecard.json", "artifact_hashes.json", "run.log",
        "positions.jsonl", "frozen/config.yaml", "frozen/candidate.yaml",
        "frozen/universe.json", "frozen/data_manifest.json",
    ):
        assert (exp_dir / name).exists(), name

    manifest = yaml.safe_load((exp_dir / "manifest.yaml").read_text())
    assert manifest["schema_version"] == 2
    assert manifest["parameter_lock_utc"] < manifest["run_started_utc"]
    assert manifest["hypothesis_id"] == "H-EXISTING-ema_atr-v1"

    gates = {g["gate"]: g for g in json.loads((exp_dir / "gate_result.json").read_text())}
    assert gates[GateId.G0_DATA.value]["verdict"] == GateVerdict.PASS.value
    assert gates[GateId.G1_LEAKAGE.value]["verdict"] == GateVerdict.PASS.value
    assert gates["G2A_ARTIFACT_INTEGRITY"]["verdict"] == GateVerdict.PASS.value
    assert gates["G2B_INDEPENDENT_REPRODUCIBILITY"]["verdict"] == GateVerdict.PASS.value
    assert gates[GateId.G3_STAGE_A.value]["verdict"] == GateVerdict.PASS.value

    scorecard = json.loads((exp_dir / "scorecard.json").read_text())
    assert scorecard["diagnostic"] is False  # G0..G3 all PASS

    hashes = json.loads((exp_dir / "artifact_hashes.json").read_text())["files"]
    assert set(hashes) == {
        "manifest.yaml", "canonical_metrics.json", "gate_result.json",
        "scorecard.json", "run.log", "positions.jsonl",
        "frozen/config.yaml", "frozen/candidate.yaml",
        "frozen/universe.json", "frozen/data_manifest.json",
    }

    entries = registry_mod.load_all()
    assert len(entries) == 1
    assert entries[0]["verdict"] == "CANDIDATE_PASS"
    assert entries[0]["canonical"]["trades"] == 30
    assert entries[0]["pf_position_level"] == pytest.approx(21.0 / 9.0)


def test_v2_eval_g0_gap_symbol_is_protocol_fail(env):
    tmp_path = env
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps(_coverage(symbol="ETHUSDT", gaps=1)), encoding="utf-8")
    _write_matrix(
        tmp_path, "m_gap",
        [("ema_atr", "ETHUSDT", "base", _cell_document(tmp_path, symbol="ETHUSDT"))],
    )
    payload = evaluate_matrix_v2(
        str(tmp_path / "m_gap"),
        output_root=str(tmp_path / "out"),
        coverage_path=str(coverage_file),
    )
    row = payload["rows"][0]
    assert payload["protocol_fail"] == 1
    assert row["verdict"] == "UNRANKED_PROTOCOL_FAIL"
    assert "unexplained_gap" in row["reasons"]
    scorecard = json.loads(
        (tmp_path / "out" / row["experiment_id"] / "scorecard.json").read_text()
    )
    assert scorecard["diagnostic"] is True


def test_v2_eval_low_trades_is_inconclusive_and_pf_recorded(env):
    tmp_path = env
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps(_coverage()), encoding="utf-8")
    bundle = _cell_document(tmp_path, trades_per_fold=6, winners=4)  # 18 trades < 20
    _write_matrix(tmp_path, "m_small", [("ema_atr", "SOLUSDT", "base", bundle)])
    payload = evaluate_matrix_v2(
        str(tmp_path / "m_small"),
        output_root=str(tmp_path / "out"),
        coverage_path=str(coverage_file),
    )
    assert payload["rows"][0]["verdict"] == "INCONCLUSIVE"
    assert "trades_below_min" in payload["rows"][0]["reasons"]


def test_v1_v2_comparison_written_into_matrix_dir(env):
    tmp_path = env
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps(_coverage()), encoding="utf-8")
    v1_dir = tmp_path / "v1_summaries"
    v1_dir.mkdir()
    (v1_dir / "sprint_summary_20260823T000000Z.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "experiment_id": "EXP-V1-0001",
                        "strategy_type": "ema_atr",
                        "symbol": "SOLUSDT",
                        "variant": "base",
                        "verdict": "CANDIDATE_FAIL",
                        "pf_after_cost": float("inf"),  # V1 fold-net pathology
                        "exp_after_cost": 0.011228,
                        "trades": 379,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    _write_matrix(tmp_path, "m_cmp", [("ema_atr", "SOLUSDT", "base", _cell_document(tmp_path))])
    evaluate_matrix_v2(
        str(tmp_path / "m_cmp"),
        output_root=str(tmp_path / "out"),
        coverage_path=str(coverage_file),
        v1_summary_dir=str(v1_dir),
    )
    comparison = json.loads(
        (tmp_path / "m_cmp" / "v1_v2_comparison.json").read_text()
    )
    assert comparison["matched"] == 1
    row = comparison["rows"][0]
    assert row["verdict_old"] == "CANDIDATE_FAIL"
    assert row["verdict_new"] == "CANDIDATE_PASS"
    assert row["verdict_changed"] is True
    # Non-finite V1 PF is sanitized to null (strict JSON, honest dPF).
    assert row["pf_old_fold_net"] is None
    assert row["d_pf"] is None
    assert comparison["top_pf_shifts"] == []
