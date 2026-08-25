"""A4 V7 machine finalizer tests -- golden synthetic trial + fail-closed paths.

The golden fixture is fully hand-checkable:

* closed legs give top POSITIVE-pnl fold share 100/230 ~= 0.4348 (<= 0.50)
  and top symbol share 85/230 ~= 0.3696 (<= 0.40);
* a dominance variant concentrates 100/150 = 2/3 of positive PnL in one
  fold AND one symbol -> FG3 must fail with those exact numbers;
* DSR/PBO run on honest synthetic inputs vs literal fail-closed sentinels.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.v7_finalizer import (
    DSR_UNAVAILABLE,
    PBO_UNAVAILABLE,
    FINALIZER_SCHEMA_VERSION,
    build_reproduction_report,
    build_stress_manifest,
    finalize_trial,
)

DAY_NS = 86_400_000_000_000


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


CONTRACT = {
    "schema_version": 1,
    "experiment_id": "V7-PD-3D",
    "strategy_kind": "funding_price_divergence",
    "direction": "normal",
    "price_lookback_days": 3,
    "funding_lookback_days": 3,
    "thresholds": {
        "min_profit_factor": 1.10,
        "max_drawdown": 0.10,
        "max_top_fold_share": 0.50,
        "max_top_symbol_share": 0.40,
        "min_adjacent_positive_lookbacks": 2,
        "max_gross_exposure": 1.0,
        "max_net_abs_exposure": 0.10,
        "max_fold_return_dispersion": 0.05,
        "dsr_min": 0.5,
        "pbo_max": 0.5,
    },
}

GOLDEN_LEGS = [
    # experiment_fold, symbol, canonical_pnl  (positives total 230)
    {"experiment_fold": "F1", "symbol": "AUSDT", "canonical_pnl": 40.0},
    {"experiment_fold": "F1", "symbol": "BUSDT", "canonical_pnl": 35.0},
    {"experiment_fold": "F1", "symbol": "CUSDT", "canonical_pnl": 25.0},
    {"experiment_fold": "F2", "symbol": "AUSDT", "canonical_pnl": 30.0},
    {"experiment_fold": "F2", "symbol": "BUSDT", "canonical_pnl": 32.0},
    {"experiment_fold": "F2", "symbol": "CUSDT", "canonical_pnl": 28.0},
    {"experiment_fold": "F3", "symbol": "AUSDT", "canonical_pnl": 15.0},
    {"experiment_fold": "F3", "symbol": "BUSDT", "canonical_pnl": 13.0},
    {"experiment_fold": "F3", "symbol": "CUSDT", "canonical_pnl": 12.0},
    {"experiment_fold": "F3", "symbol": "DUSDT", "canonical_pnl": -10.0},
]

GOLDEN_SIBLINGS = [
    {"experiment_id": "V7-PD-1D", "is_control": False, "price_lookback_days": 1,
     "net_pnl": 3000.0, "profit_factor": 1.20, "mechanism_pass": True,
     "fold_pnls": {"F1": 1500.0, "F2": 1500.0}},
    {"experiment_id": "V7-PD-7D", "is_control": False, "price_lookback_days": 7,
     "net_pnl": 2100.0, "profit_factor": 1.15, "mechanism_pass": True,
     "fold_pnls": {"F1": 1100.0, "F2": 1000.0}},
    {"experiment_id": "V7-REVERSE-3D", "is_control": True, "price_lookback_days": 3,
     "net_pnl": -4000.0, "profit_factor": 0.85, "mechanism_pass": False,
     "fold_pnls": {"F1": -2000.0, "F2": -2000.0}},
]

GOLDEN_STRESS_VARIANTS = {
    "fee_x1_5": {"executed": True, "canonical_pnl": 3000.0},
    "adverse_two_ticks": {"executed": True, "canonical_pnl": 2800.0},
    "extra_one_event_delay": {"executed": True, "canonical_pnl": 2600.0},
    "drop_one_symbol:AUSDT": {"executed": True, "canonical_pnl": 2200.0},
    "drop_one_symbol:BUSDT": {"executed": True, "canonical_pnl": 2100.0},
    "drop_one_symbol:CUSDT": {"executed": True, "canonical_pnl": 2000.0},
    "drop_one_symbol:DUSDT": {"executed": True, "canonical_pnl": 2400.0},
    "drop_one_fold:F1": {"executed": True, "canonical_pnl": 1900.0},
    "drop_one_fold:F2": {"executed": True, "canonical_pnl": 1700.0},
    "drop_one_fold:F3": {"executed": True, "canonical_pnl": 1500.0},
}


def _golden_equity() -> tuple[list[dict], float]:
    """30 days of gently-varying positive-drift equity (nonzero variance)."""
    rows, equity = [], 100_000.0
    for day in range(30):
        rows.append({"ts": 1_700_000_000_000_000_000 + day * DAY_NS,
                     "equity": round(equity, 6),
                     "experiment_fold": f"F{min(day // 10 + 1, 3)}"})
        equity += [160.0, 210.0, 185.0][day % 3]
    return rows, equity


def make_golden_trial(tmp_path: Path) -> Path:
    exp_dir = Path(tmp_path) / "trial-golden"
    exp_dir.mkdir(parents=True)
    ledger, final_equity = _golden_equity()
    _write_jsonl(exp_dir / "portfolio_ledger.jsonl", ledger)
    _write_jsonl(exp_dir / "positions.jsonl", GOLDEN_LEGS)
    _write_jsonl(exp_dir / "funding_cashflows.jsonl",
                 [{"cashflow": 500.0}, {"cashflow": 500.0}, {"cashflow": 500.0}])
    (exp_dir / "canonical_metrics.json").write_text(json.dumps({
        "total_pnl": 5000.0,
        "pf_position_level": {"profit_factor": 1.25, "trades": 9},
        "fold_pnls": {"F1": 2000.0, "F2": 1800.0, "F3": 1200.0},
        "fold_returns": {"F1": 0.02, "F2": 0.018, "F3": 0.012},
        "max_drawdown_fraction": 0.03,
        "margin_breach_rows": 0,
        "gross_max": 0.9,
        "net_abs_max": 0.08,
    }), encoding="utf-8")
    (exp_dir / "stress_report.json").write_text(json.dumps({
        "schema_version": 4, "baseline": {"canonical_pnl": 3300.0},
        "variants": GOLDEN_STRESS_VARIANTS,
    }), encoding="utf-8")
    (exp_dir / "accounting_reconciliation.json").write_text("{}\n", encoding="utf-8")
    (exp_dir / "commission_slippage.json").write_text("{}\n", encoding="utf-8")
    hashes = {name: _sha(exp_dir / name) for name in (
        "canonical_metrics.json", "portfolio_ledger.jsonl", "positions.jsonl",
        "funding_cashflows.jsonl", "accounting_reconciliation.json",
        "commission_slippage.json", "stress_report.json")}
    (exp_dir / "artifact_hashes.json").write_text(
        json.dumps({"schema_version": 4, "hashes": hashes}), encoding="utf-8")
    return exp_dir


def _comparison_file(tmp_path: Path, name: str, all_match: bool) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps({
        "schema_version": 4, "all_match": all_match,
        "checks": {"pnl_match": all_match, "mdd_match": all_match},
    }), encoding="utf-8")
    return path


def _pbo_matrix(n_configs: int = 8, n_points: int = 24) -> dict[str, list[float]]:
    return {f"cfg{i}": [(i + 1) * (1.0 + 0.01 * b) for b in range(n_points)]
            for i in range(n_configs)}


def _finalize_golden(tmp_path: Path, **overrides):
    exp_dir = make_golden_trial(tmp_path)
    kwargs = dict(
        resolved_contract=CONTRACT,
        sibling_trials=GOLDEN_SIBLINGS,
        effective_n_trials=8,
        trial_sharpes=[0.05, 0.06, 0.07, 0.08],
        pbo_returns_matrix=_pbo_matrix(),
        comparison_paths=[_comparison_file(tmp_path, "cmp_ok.json", True)],
        a7_audit={"unresolved_high": 0, "unresolved_critical": 0},
    )
    kwargs.update(overrides)
    summary = finalize_trial(exp_dir, **kwargs)
    docs = {}
    for name in summary["artifacts_written"]:
        docs[name] = json.loads((exp_dir / name).read_text(encoding="utf-8"))
    return exp_dir, summary, docs


# --------------------------------------------------------------------------- #
# golden synthetic trial
# --------------------------------------------------------------------------- #
def test_golden_trial_writes_all_six_artifacts_and_lock_eligible(tmp_path):
    exp_dir, summary, docs = _finalize_golden(tmp_path)
    assert sorted(docs) == sorted([
        "final_gate_result.json", "final_scorecard.json",
        "concentration_report.json", "stress_manifest.json",
        "statistical_haircut.json", "reproduction_report.json"])
    assert summary["verdict"] == "LOCK_ELIGIBLE"
    assert summary["all_hard_gates_pass"] is True
    assert all(status == "PASS" for status in summary["gate_statuses"].values())


def test_golden_gate_rows_fg0_to_fg7_with_measured_threshold_operator(tmp_path):
    _, _, docs = _finalize_golden(tmp_path)
    gates = {g["gate"]: g for g in docs["final_gate_result.json"]["gates"]}
    assert list(gates) == ["FG0", "FG1", "FG2", "FG3", "FG4", "FG5", "FG6", "FG7"]
    fg2 = {c["check"]: c for c in gates["FG2"]["criteria"]}
    assert fg2["net_pnl_positive"] == {
        "check": "net_pnl_positive", "measured_value": 5000.0, "threshold": 0.0,
        "operator": ">", "pass": True, "status": "PASS", "reason": None}
    assert fg2["profit_factor_at_least_minimum"]["measured_value"] == pytest.approx(1.25)
    assert fg2["profit_factor_at_least_minimum"]["operator"] == ">="
    assert fg2["profit_factor_at_least_minimum"]["threshold"] == pytest.approx(1.10)
    assert fg2["no_negative_fold"]["measured_value"] == 0.0
    fg3 = {c["check"]: c for c in gates["FG3"]["criteria"]}
    assert fg3["net_funding_positive"]["measured_value"] == pytest.approx(1500.0)
    assert fg3["adjacent_positive_lookbacks"]["measured_value"] == 2.0
    assert fg3["adjacent_positive_lookbacks"]["operator"] == ">="
    assert fg3["top_positive_fold_share_within_limit"]["operator"] == "<="
    assert gates["FG7"]["status"] == "PASS"


def test_golden_concentration_math_hand_checked(tmp_path):
    _, _, docs = _finalize_golden(tmp_path)
    conc = docs["concentration_report.json"]
    assert conc["input_status"] == "OK"
    assert conc["legs_used"] == 10  # incl. one negative leg
    by_fold = conc["by_experiment_fold"]
    assert by_fold["shares"]["F1"] == pytest.approx(100.0 / 230.0)
    assert by_fold["shares"]["F2"] == pytest.approx(90.0 / 230.0)
    assert by_fold["shares"]["F3"] == pytest.approx(40.0 / 230.0)
    assert by_fold["top"] == "F1"
    assert by_fold["top_share"] == pytest.approx(100.0 / 230.0)
    by_symbol = conc["by_symbol"]
    assert by_symbol["shares"]["AUSDT"] == pytest.approx(85.0 / 230.0)
    assert by_symbol["shares"]["BUSDT"] == pytest.approx(80.0 / 230.0)
    assert by_symbol["shares"]["CUSDT"] == pytest.approx(65.0 / 230.0)
    assert "DUSDT" not in by_symbol["shares"]  # negative leg excluded entirely
    assert by_symbol["top_share"] == pytest.approx(85.0 / 230.0)


def test_golden_statistical_haircut_computed_not_sentinel(tmp_path):
    _, _, docs = _finalize_golden(tmp_path)
    haircut = docs["statistical_haircut.json"]
    assert haircut["observed_daily_sharpe"] > 0
    assert haircut["sample_len"] == 29  # 30 equity days -> 29 returns
    assert haircut["effective_n_trials"] == 8
    assert haircut["skew_kurtosis_estimator_id"]
    dsr_block = haircut["dsr"]
    assert dsr_block["dsr"] != DSR_UNAVAILABLE
    assert 0.0 <= dsr_block["dsr"] <= 1.0
    assert dsr_block["sr0"] is not None
    pbo_block = haircut["pbo"]
    assert pbo_block["pbo"] == 0.0  # consistently ranked matrix
    assert pbo_block["n_combinations"] == 70  # C(8,4)
    assert pbo_block["rank_rule"] and pbo_block["tie_rule"]


def test_golden_scorecard_full_marks_and_operator_serialization(tmp_path):
    _, summary, docs = _finalize_golden(tmp_path)
    card = docs["final_scorecard.json"]
    assert card["total_possible"] == 100.0
    assert card["score_meaningful"] is True
    assert summary["score_total"] == pytest.approx(100.0)
    assert card["band"] == "STRONG_LOCK_ELIGIBLE_STILL_NEEDS_A7_SIGNATURE"
    groups = card["groups"]
    assert [groups[g]["points_max"] for g in
            ("integrity", "robustness", "risk_adjusted", "costs", "breadth",
             "statistical")] == [20, 20, 20, 15, 15, 10]
    serialized = []
    for group in groups.values():
        for item in group["items"]:
            serialized.append(item)
            assert {"item", "points_max", "awarded", "raw_value", "threshold",
                    "operator", "earned"} <= set(item)
            json.dumps(item)  # operator/threshold survive serialization
    pf_item = next(i for i in serialized if i["item"] == "profit_factor")
    assert pf_item["operator"] == ">=" and pf_item["earned"] is True
    assert pf_item["raw_value"] == pytest.approx(1.25)
    mdd_item = next(i for i in serialized if i["item"] == "max_drawdown")
    assert mdd_item["operator"] == "<=" and mdd_item["raw_value"] == pytest.approx(0.03)
    dsr_item = next(i for i in serialized if i["item"] == "deflated_sharpe_ratio")
    assert dsr_item["awarded"] == 5.0
    assert 0 <= dsr_item["raw_value"] <= 1


def test_golden_stress_manifest_lists_required_families_executed(tmp_path):
    _, _, docs = _finalize_golden(tmp_path)
    manifest = docs["stress_manifest.json"]
    families = {row["family"]: row for row in manifest["variants"]}
    for fixed in ("fee_x1_5", "adverse_two_ticks", "extra_one_event_delay"):
        assert families[fixed]["executed"] is True
        assert families[fixed]["present"] is True
    assert families["drop_one_symbol_AUSDT"]["executed"] is True
    assert families["drop_one_fold_F1"]["executed"] is True
    assert manifest["all_required_executed"] is True
    assert manifest["missing_or_not_executed"] == []


def test_every_writer_embeds_schema_generated_at_and_source_hashes(tmp_path):
    _, _, docs = _finalize_golden(tmp_path)
    for name, doc in docs.items():
        assert doc["schema_version"] == FINALIZER_SCHEMA_VERSION
        assert doc["generated_at_utc"].endswith("Z")
        if name != "final_scorecard.json":
            assert doc.get("source_hashes"), name
    hashes = docs["concentration_report.json"]["source_hashes"]
    assert set(hashes) == {"positions.jsonl"}


# --------------------------------------------------------------------------- #
# fail-closed paths
# --------------------------------------------------------------------------- #
def test_concentration_dominance_fails_fg3_with_exact_hand_math(tmp_path):
    exp_dir = make_golden_trial(tmp_path)
    dominant = [
        {"experiment_fold": "F1", "symbol": "AUSDT", "canonical_pnl": 100.0},
        {"experiment_fold": "F2", "symbol": "BUSDT", "canonical_pnl": 50.0},
    ]
    (exp_dir / "positions.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in dominant), encoding="utf-8")
    hashes_doc = json.loads((exp_dir / "artifact_hashes.json").read_text())
    hashes_doc["hashes"]["positions.jsonl"] = _sha(exp_dir / "positions.jsonl")
    (exp_dir / "artifact_hashes.json").write_text(json.dumps(hashes_doc))
    docs = {}
    summary = finalize_trial(
        exp_dir, resolved_contract=CONTRACT, sibling_trials=GOLDEN_SIBLINGS,
        effective_n_trials=8, trial_sharpes=[0.05, 0.06],
        pbo_returns_matrix=_pbo_matrix(),
        comparison_paths=[_comparison_file(tmp_path, "cmp_ok2.json", True)],
        a7_audit={"unresolved_high": 0, "unresolved_critical": 0})
    for name in summary["artifacts_written"]:
        docs[name] = json.loads((exp_dir / name).read_text(encoding="utf-8"))
    conc = docs["concentration_report.json"]
    assert conc["by_experiment_fold"]["top_share"] == pytest.approx(2.0 / 3.0)
    assert conc["by_symbol"]["top_share"] == pytest.approx(2.0 / 3.0)
    gates = {g["gate"]: g for g in docs["final_gate_result.json"]["gates"]}
    fg3 = {c["check"]: c for c in gates["FG3"]["criteria"]}
    assert fg3["top_positive_fold_share_within_limit"]["pass"] is False
    assert fg3["top_positive_fold_share_within_limit"]["measured_value"] \
        == pytest.approx(2.0 / 3.0)
    assert fg3["top_positive_symbol_share_within_limit"]["pass"] is False
    assert gates["FG3"]["pass"] is False
    assert summary["verdict"] == "NOT_ELIGIBLE"
    assert summary["score_meaningful"] is False
    assert docs["final_scorecard.json"]["band"] is None
    breadth = docs["final_scorecard.json"]["groups"]["breadth"]
    fold_share = next(i for i in breadth["items"] if i["item"] == "top_fold_share")
    assert fold_share["earned"] is False and fold_share["awarded"] == 0.0


def test_dsr_fail_closed_without_dispersion_or_ledger(tmp_path):
    exp_dir = make_golden_trial(tmp_path)
    result = finalize_trial(exp_dir, resolved_contract=CONTRACT,
                            effective_n_trials=8,  # no trial_sharpes
                            pbo_returns_matrix=_pbo_matrix(),
                            comparison_paths=[_comparison_file(tmp_path, "c.json", True)],
                            a7_audit={"unresolved_high": 0, "unresolved_critical": 0})
    haircut = json.loads(
        (exp_dir / "statistical_haircut.json").read_text(encoding="utf-8"))
    assert haircut["dsr"]["dsr"] == DSR_UNAVAILABLE
    assert haircut["dsr"]["reason"] == "trial_sharpe_dispersion_missing"
    assert haircut["pbo"]["pbo"] == 0.0

    empty_dir = tmp_path / "empty-trial"
    empty_dir.mkdir()
    finalize_trial(empty_dir, resolved_contract=CONTRACT)
    haircut_empty = json.loads(
        (empty_dir / "statistical_haircut.json").read_text(encoding="utf-8"))
    assert haircut_empty["dsr"]["dsr"] == DSR_UNAVAILABLE
    assert haircut_empty["dsr"]["reason"] == "portfolio_ledger_missing_or_unreadable"
    gates = {g["gate"]: g for g in json.loads(
        (empty_dir / "final_gate_result.json").read_text(encoding="utf-8"))["gates"]}
    assert gates["FG0"]["pass"] is False
    assert all(gate["pass"] is False for gate in gates.values())
    assert gates["FG2"]["status"] == "FAIL"
    assert all(c["status"] == "NOT_TESTED" for c in gates["FG2"]["criteria"])


def test_pbo_fail_closed_below_eight_configs_or_misaligned(tmp_path):
    exp_dir = make_golden_trial(tmp_path)
    seven = _pbo_matrix(n_configs=7)
    finalize_trial(exp_dir, resolved_contract=CONTRACT,
                   effective_n_trials=8, trial_sharpes=[0.05, 0.06],
                   pbo_returns_matrix=seven,
                   comparison_paths=[_comparison_file(tmp_path, "c2.json", True)],
                   a7_audit={"unresolved_high": 0, "unresolved_critical": 0})
    haircut = json.loads(
        (exp_dir / "statistical_haircut.json").read_text(encoding="utf-8"))
    assert haircut["pbo"]["pbo"] == PBO_UNAVAILABLE
    assert haircut["pbo"]["reason"] == "insufficient_configurations"

    # misaligned matrix on a fresh dir
    exp_dir3 = make_golden_trial(tmp_path / "misaligned")
    ragged = _pbo_matrix()
    ragged["cfg0"] = ragged["cfg0"][:-1]
    finalize_trial(exp_dir3, resolved_contract=CONTRACT,
                   effective_n_trials=8, trial_sharpes=[0.05, 0.06],
                   pbo_returns_matrix=ragged,
                   comparison_paths=[_comparison_file(tmp_path, "c3.json", True)],
                   a7_audit={"unresolved_high": 0, "unresolved_critical": 0})
    haircut_ragged = json.loads(
        (exp_dir3 / "statistical_haircut.json").read_text(encoding="utf-8"))
    assert haircut_ragged["pbo"]["pbo"] == PBO_UNAVAILABLE
    assert haircut_ragged["pbo"]["reason"] == "misaligned_matrix"


def test_missing_inputs_degrade_gates_never_pass(tmp_path):
    exp_dir = make_golden_trial(tmp_path)
    (exp_dir / "canonical_metrics.json").unlink()
    (exp_dir / "stress_report.json").unlink()
    result = finalize_trial(
        exp_dir, resolved_contract=CONTRACT,
        comparison_paths=[],  # no reproduction evidence
        a7_audit=None)
    assert result["verdict"] == "NOT_ELIGIBLE"
    statuses = result["gate_statuses"]
    assert statuses["FG0"] == "FAIL"
    assert statuses["FG2"] == "FAIL"
    assert statuses["FG4"] == "FAIL"
    assert statuses["FG5"] == "FAIL"
    assert statuses["FG6"] == "FAIL"
    assert statuses["FG7"] == "FAIL"
    gates_doc = json.loads(
        (exp_dir / "final_gate_result.json").read_text(encoding="utf-8"))
    gates = {g["gate"]: g for g in gates_doc["gates"]}
    assert any("missing_artifacts" in note for note in gates_doc["notes"])
    fg0 = {c["check"]: c for c in gates["FG0"]["criteria"]}
    assert fg0["required_artifacts_complete"]["pass"] is False
    assert fg0["required_artifacts_complete"]["status"] == "FAIL"
    # six artifacts still written despite failures
    for name in ("final_gate_result.json", "final_scorecard.json",
                 "concentration_report.json", "stress_manifest.json",
                 "statistical_haircut.json", "reproduction_report.json"):
        assert (exp_dir / name).is_file()


def test_hash_mismatch_fails_fg0_and_scores_zero_integrity_items(tmp_path):
    exp_dir = make_golden_trial(tmp_path)
    (exp_dir / "canonical_metrics.json").write_text(
        json.dumps({"total_pnl": 999999.0}), encoding="utf-8")  # tamper post-hash
    result = finalize_trial(
        exp_dir, resolved_contract=CONTRACT,
        sibling_trials=GOLDEN_SIBLINGS, effective_n_trials=8,
        trial_sharpes=[0.05, 0.06], pbo_returns_matrix=_pbo_matrix(),
        comparison_paths=[_comparison_file(tmp_path, "cmp_h.json", True)],
        a7_audit={"unresolved_high": 0, "unresolved_critical": 0})
    assert result["verdict"] == "NOT_ELIGIBLE"
    gates_doc = json.loads(
        (exp_dir / "final_gate_result.json").read_text(encoding="utf-8"))
    gates = {g["gate"]: g for g in gates_doc["gates"]}
    assert gates["FG0"]["pass"] is False
    assert any("hash_mismatch:canonical_metrics.json" in note
               for note in gates_doc["notes"])
    integrity = json.loads(
        (exp_dir / "final_scorecard.json").read_text())["groups"]["integrity"]
    hash_items = {i["item"]: i for i in integrity["items"]}
    assert hash_items["deterministic_artifacts_hash_recompute"]["earned"] is False


def test_stress_manifest_detects_missing_variant_and_blocks_fg5(tmp_path):
    exp_dir = make_golden_trial(tmp_path)
    report = json.loads((exp_dir / "stress_report.json").read_text())
    del report["variants"]["fee_x1_5"]
    (exp_dir / "stress_report.json").write_text(json.dumps(report))
    hashes_doc = json.loads((exp_dir / "artifact_hashes.json").read_text())
    hashes_doc["hashes"]["stress_report.json"] = _sha(exp_dir / "stress_report.json")
    (exp_dir / "artifact_hashes.json").write_text(json.dumps(hashes_doc))
    result = finalize_trial(
        exp_dir, resolved_contract=CONTRACT, sibling_trials=GOLDEN_SIBLINGS,
        effective_n_trials=8, trial_sharpes=[0.05, 0.06],
        pbo_returns_matrix=_pbo_matrix(),
        comparison_paths=[_comparison_file(tmp_path, "cm.json", True)],
        a7_audit={"unresolved_high": 0, "unresolved_critical": 0})
    assert result["verdict"] == "NOT_ELIGIBLE"
    manifest = json.loads(
        (exp_dir / "stress_manifest.json").read_text(encoding="utf-8"))
    families = {row["family"]: row for row in manifest["variants"]}
    assert families["fee_x1_5"]["executed"] is False
    assert families["fee_x1_5"]["present"] is False
    assert "fee_x1_5" in manifest["missing_or_not_executed"]
    assert manifest["all_required_executed"] is False
    gates_doc = json.loads(
        (exp_dir / "final_gate_result.json").read_text(encoding="utf-8"))
    fg5 = next(g for g in gates_doc["gates"] if g["gate"] == "FG5")
    assert fg5["pass"] is False
    costs = json.loads(
        (exp_dir / "final_scorecard.json").read_text())["groups"]["costs"]
    fee_item = next(i for i in costs["items"] if i["item"] == "fee_x1_5_survival")
    assert fee_item["reason"] == "stress_variant_not_executed"
    assert fee_item["awarded"] == 0.0


# --------------------------------------------------------------------------- #
# reproduction report builder
# --------------------------------------------------------------------------- #
def test_reproduction_report_passes_only_when_all_entries_match(tmp_path):
    ok1 = _comparison_file(tmp_path, "r1.json", True)
    ok2 = _comparison_file(tmp_path, "r2.json", True)
    bad = _comparison_file(tmp_path, "bad.json", False)
    good = build_reproduction_report([ok1, ok2])
    assert good["pass"] is True and good["reason"] is None
    mixed = build_reproduction_report([ok1, bad])
    assert mixed["pass"] is False
    entry_bad = next(e for e in mixed["entries"] if e["path"].endswith("bad.json"))
    assert entry_bad["failed_checks"] == ["mdd_match", "pnl_match"]
    empty = build_reproduction_report([])
    assert empty["pass"] is False
    assert empty["reason"] == "no_comparisons_provided"
    missing = build_reproduction_report([tmp_path / "ghost.json"])
    assert missing["pass"] is False
    assert missing["entries"][0]["status"] == "MISSING_OR_UNREADABLE_FAIL_CLOSED"


def test_adjacency_requires_distinct_passing_lookbacks(tmp_path):
    exp_dir = make_golden_trial(tmp_path)
    weak_siblings = [
        {"experiment_id": "V7-PD-1D", "is_control": False,
         "price_lookback_days": 1, "net_pnl": -5.0, "profit_factor": 0.9,
         "mechanism_pass": False},
        {"experiment_id": "V7-PD-3D-DUP", "is_control": False,
         "price_lookback_days": 3, "net_pnl": 900.0, "profit_factor": 1.4,
         "mechanism_pass": True},
    ]
    result = finalize_trial(
        exp_dir, resolved_contract=CONTRACT, sibling_trials=weak_siblings,
        effective_n_trials=8, trial_sharpes=[0.05, 0.06],
        pbo_returns_matrix=_pbo_matrix(),
        comparison_paths=[_comparison_file(tmp_path, "ca.json", True)],
        a7_audit={"unresolved_high": 0, "unresolved_critical": 0})
    assert result["verdict"] == "NOT_ELIGIBLE"
    gates_doc = json.loads(
        (exp_dir / "final_gate_result.json").read_text(encoding="utf-8"))
    fg3 = next(g for g in gates_doc["gates"] if g["gate"] == "FG3")
    adjacency = next(c for c in fg3["criteria"]
                     if c["check"] == "adjacent_positive_lookbacks")
    assert adjacency["measured_value"] == 0.0
    assert adjacency["pass"] is False
