"""End-to-end fixtures for sprint_eval --schema v5 (PLAN 31.5, owner A3).

Each test plays the role of the diagnostic RERUNNER: it writes real input
artifacts into a ``*-DIAG-V5`` directory and hashes them LAST, then invokes
:func:`evaluate_diagnostic_v5` as the EVALUATOR and asserts:

* canonical metrics carry NO fake expectancy-R;
* gates are measured (ledger counting / directory verification);
* artifact_hashes.json is finalized last and later in-process writes RAISE;
* the registry row has kind DIAGNOSTIC_RECALC linking the source trial.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from contracts.protocol import GateVerdict
from research.protocol.registry import load_all
from research.reconciliation import (
    HASHES_FILENAME,
    finalize_directory_hashes,
    verify_experiment_dir,
)
import research.sprint_eval as sprint_eval
from research.sprint_eval import (
    V5_DEFAULT_OUTPUT_ROOT,
    HashesFinalViolation,
    evaluate_diagnostic_v5,
    guarded_write_json,
    guarded_write_text,
)

DAY = 86_400_000_000_000


def _jw(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _jl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


def _build_diag_dir(exp_dir: Path, *, n_legs=120) -> dict:
    """Runner-style inputs whose numbers reconcile exactly."""
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    # PnL split: three equal positive books (1/3 share each <= 0.40 cap),
    # SOL carries a small negative book
    sol_pnl = -250.0
    per_positive = (9_000.0 + sol_pnl) / 3
    per_symbol = {
        "BTCUSDT": per_positive,
        "ETHUSDT": per_positive,
        "XRPUSDT": per_positive,
        "SOLUSDT": sol_pnl,
    }
    total = sum(per_symbol.values())

    positions = []
    legs_per_symbol = n_legs // len(symbols)
    for sym in symbols:
        for _ in range(legs_per_symbol):
            positions.append({
                "symbol": sym,
                "canonical_pnl": round(per_symbol[sym] / legs_per_symbol, 10),
            })
    drift = round(total - sum(r["canonical_pnl"] for r in positions), 10)
    positions[0]["canonical_pnl"] += drift  # make parts sum EXACTLY

    funding = [{"funding_net": -12.5}, {"funding_net": 2.5}]
    costs = [{"commission": 8.0, "modeled_slippage": 4.0}]

    fold_returns = [
        [0.002, 0.002],   # +0.40%
        [0.002, 0.002],   # +0.40% (equal -> top fold share exactly 0.50)
        [-0.02, 0.005],   # negative fold
    ]
    accounting = {
        "positions_total_pnl": round(sum(r["canonical_pnl"] for r in positions), 10),
        "funding_total": -10.0,
        "commission_total": 8.0,
        "slippage_total": 4.0,
    }
    ledger_rows = [
        {"signal_ts": i * DAY, "fill_ts": i * DAY + 900_000_000}
        for i in range(n_legs)
    ]

    _jw(exp_dir / "cell.json", {
        "experiment_id": exp_dir.name,
        "source_trial_experiment_id": "V4-XSECT-MOM-7D-001",
        "hypothesis_id": "H-XSECT-MOM-v1",
        "strategy_type": "xsect_mom",
        "symbol": "BTCUSDT",
        "window_actual": {"start_utc": "2026-01-01T00:00:00Z",
                          "end_utc": "2026-04-01T00:00:00Z"},
        "universe": symbols,
        "declared_symbols": symbols,
        "rebalances_scored": 36,
        "warmup_boundaries": {"warmup_start": "w", "scored_start": "s",
                              "scored_end": "e"},
        "folds": [
            {"fold_id": f"f{k+1}", "start_equity": 100_000.0}
            for k in range(len(fold_returns))
        ],
    })
    _jl(exp_dir / "execution_ledger.jsonl", ledger_rows)
    _jw(exp_dir / "transforms.json", {})
    _jl(exp_dir / "positions.jsonl", positions)
    _jl(exp_dir / "funding_cashflows.jsonl", funding)
    _jl(exp_dir / "costs.jsonl", costs)
    _jw(exp_dir / "accounting_reconciliation.json", accounting)
    _jw(exp_dir / "fold_returns.json", fold_returns)
    # Runner-side hashes LAST
    finalize_directory_hashes(exp_dir)
    return accounting


@pytest.fixture(autouse=True)
def _reset_finalized_locks():
    sprint_eval._FINALIZED_DIRS.clear()
    yield
    sprint_eval._FINALIZED_DIRS.clear()


def _run(tmp_path, monkeypatch, name="V4-XSECT-MOM-7D-001-DIAG-V5"):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / V5_DEFAULT_OUTPUT_ROOT
    _build_diag_dir(root / name)
    registry_path = tmp_path / "registry" / "experiments.jsonl"
    payload = evaluate_diagnostic_v5(root, registry_path=registry_path)
    entries = load_all(registry_path)
    return payload, entries, root / name


def test_happy_path_diagnostic_eval_measures_everything(tmp_path, monkeypatch):
    payload, entries, exp_dir = _run(tmp_path, monkeypatch)
    assert payload["evaluated"] == 1
    row = entries[-1]
    assert row["kind"] == "DIAGNOSTIC_RECALC"
    assert row["source_trial_experiment_id"] == "V4-XSECT-MOM-7D-001"

    metrics = json.loads((exp_dir / "canonical_metrics.json").read_text())
    # F07: no fake expectancy-R anywhere in the v5 canonical metrics
    assert metrics["expectancy_r"] == {
        "value": None, "reason": "MISSING_R_NORMALIZATION"
    }
    assert metrics["daily_sharpe"]["estimator_id"] == "DAILY_SHARPE_RF0_V1"
    assert metrics["daily_sharpe"]["rf"] == 0.0
    assert metrics["median_fold_return"]["value"] > 0
    assert metrics["chained_wfa_mdd"]["estimator_id"] == "CHAINED_FOLD_RETURNS_MDD_V1"
    assert metrics["positive_folds"] == 2 and metrics["outer_folds"] == 3
    # F02: measured share over the canonical population, never silently 0
    # (three equal positive books -> 1/3 each)
    assert metrics["top_symbol_contribution"]["share"] == pytest.approx(1 / 3)

    gate_doc = json.loads((exp_dir / "gate_result.json").read_text())
    rows = {r["gate"]: r for r in gate_doc["rows"]}
    # F16: XG1 counted from the actual ledger rows -> clean PASS here
    assert rows["XG1_POINT_IN_TIME"]["verdict"] == GateVerdict.PASS.value
    assert rows["XG2A_ARTIFACT_INTEGRITY"]["verdict"] == GateVerdict.PASS.value
    assert rows["XG3_STAGE_A_PORTFOLIO"]["verdict"] == GateVerdict.PASS.value
    assert gate_doc["xg2a_evidence"]["measured_before_evaluation"] is True
    assert payload["pass"] == 1 and payload["protocol_fail"] == 0


def test_hashes_finalized_last_and_later_writes_raise(tmp_path, monkeypatch):
    _payload, _entries, exp_dir = _run(tmp_path, monkeypatch)
    flag = exp_dir / ".hashes_final"
    assert flag.is_file()
    hashes = exp_dir / HASHES_FILENAME
    hashes_mtime_ns = hashes.stat().st_mtime_ns
    listed = set(json.loads(hashes.read_text())["files"])
    on_disk = {
        str(p.relative_to(exp_dir))
        for p in exp_dir.rglob("*")
        if p.is_file() and p.name not in (HASHES_FILENAME, ".hashes_final")
    }
    assert listed == on_disk
    for rel in listed:
        assert (exp_dir / rel).stat().st_mtime_ns <= hashes_mtime_ns

    with pytest.raises(HashesFinalViolation):
        guarded_write_json(exp_dir / "sneaky.json", {"nope": True})
    with pytest.raises(HashesFinalViolation):
        guarded_write_text(exp_dir / "run.log", "tamper\n")


def test_tampered_runner_inputs_fail_protocol_via_measured_xg2a(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / V5_DEFAULT_OUTPUT_ROOT
    exp_dir = root / "TAMPER-V4-MOM-001-DIAG-V5"
    _build_diag_dir(exp_dir)
    time.sleep(0.01)
    # Tamper BEFORE the evaluator ever sees the directory
    rows = (exp_dir / "positions.jsonl").read_text().splitlines()
    doc = json.loads(rows[0])
    doc["canonical_pnl"] += 50_000.0
    rows[0] = json.dumps(doc)
    (exp_dir / "positions.jsonl").write_text("\n".join(rows) + "\n")

    registry_path = tmp_path / "registry" / "experiments.jsonl"
    payload = evaluate_diagnostic_v5(root, registry_path=registry_path)
    row = payload["rows"][0]
    assert row["verdict"] == "UNRANKED_PROTOCOL_FAIL"
    assert row["xg2a"] == GateVerdict.FAIL.value
    assert any("artifact_hash" in r or "accounting" in r for r in row["reasons"])
    gate_doc = json.loads((exp_dir / "gate_result.json").read_text())
    assert any(
        r.startswith("artifact_hash") for r in gate_doc["xg2a_evidence"]["reasons"]
    ) or any(
        r.startswith("accounting_reconcile_fail")
        for r in gate_doc["xg2a_evidence"]["reasons"]
    )


def test_ordering_violation_in_ledger_fails_xg1(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / V5_DEFAULT_OUTPUT_ROOT
    exp_dir = root / "VIOLATION-V4-MOM-001-DIAG-V5"
    _build_diag_dir(exp_dir)
    # Sneak one fill-before-signal row in, then re-hash (so ONLY xg1 fails)
    ledger = [
        {"signal_ts": 0, "fill_ts": 900_000_000},
        {"signal_ts": DAY, "fill_ts": DAY - 1},  # violation!
    ] + [
        {"signal_ts": i * DAY, "fill_ts": i * DAY + 900_000_000}
        for i in range(2, 20)
    ]
    _jl(exp_dir / "execution_ledger.jsonl", ledger)
    time.sleep(0.01)
    finalize_directory_hashes(exp_dir)

    registry_path = tmp_path / "registry" / "experiments.jsonl"
    payload = evaluate_diagnostic_v5(root, registry_path=registry_path)
    row = payload["rows"][0]
    assert row["xg1"] == GateVerdict.FAIL.value
    assert row["verdict"] == "UNRANKED_PROTOCOL_FAIL"


def test_missing_ledger_is_inconclusive_never_pass(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / V5_DEFAULT_OUTPUT_ROOT
    exp_dir = root / "NOLEDGER-V4-MOM-001-DIAG-V5"
    _build_diag_dir(exp_dir)
    (exp_dir / "execution_ledger.jsonl").unlink()
    time.sleep(0.01)
    finalize_directory_hashes(exp_dir)
    registry_path = tmp_path / "registry" / "experiments.jsonl"
    payload = evaluate_diagnostic_v5(root, registry_path=registry_path)
    gate_doc = json.loads((exp_dir / "gate_result.json").read_text())
    xg1 = next(r for r in gate_doc["rows"] if r["gate"] == "XG1_POINT_IN_TIME")
    assert xg1["verdict"] == GateVerdict.INCONCLUSIVE.value
    assert "evidence_missing" in xg1["reasons"]
    # XG1 not PASS => the recalc can never claim MATCH_PASS
    assert payload["rows"][0]["verdict"] == "INCONCLUSIVE"


def test_post_finalize_integrity_recorded_clean(tmp_path, monkeypatch):
    _payload, entries, exp_dir = _run(tmp_path, monkeypatch)
    result = verify_experiment_dir(exp_dir)
    assert result.verdict() is GateVerdict.PASS
    row = entries[-1]
    assert row["post_finalize_integrity"]["verdict"] == GateVerdict.PASS.value