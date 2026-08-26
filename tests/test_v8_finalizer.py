"""A4 V8 finalizer tests -- thin-adapter golden, family §7.2 math, ledger.

Covers the A4 V8 contract surface:

* synthetic trial dir -> six FINAL artifacts written via delegation to
  ``research.v7_finalizer.finalize_trial`` (plus FG8 augmentation);
* FG8 weekly-minimum-rebalances: evaluated when ``min_weekly_rebalances``
  is in the resolved contract; honest SKIPPED (skip-not-fail) when absent;
* family adjacent-pair verdict math over [3D,7D,14D] incl. the
  3D PASS + 7D FAIL + 14D PASS => pair exists case;
* control-beats-best detection at family level;
* global-ledger snapshot/append_verified/digest + cohort split by
  matrix_id prefix (V6/V7/V8/V8X, unmapped surfaced);
* DSR ``effective_n_trials`` passthrough with fail-closed sentinel None.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.global_ledger import (
    append_verified,
    cohort_of,
    cohort_split,
    digest,
    snapshot,
    verify_append_only,
)
from research.v7_finalizer import DSR_UNAVAILABLE
from research.v8_finalizer import (
    FAMILY_EXPLORATORY,
    FAMILY_INVALIDATED,
    FAMILY_LOCK,
    FAMILY_REJECT_ALL,
    SIX_FINAL_ARTIFACTS,
    build_family_summary,
    finalize_trial_v8,
)
from tests.test_v7_finalizer import GOLDEN_SIBLINGS, make_golden_trial

CONTROL_ID = "XSECT-WMOM-7D-CONTROL"

V8_CONTRACT = {
    "schema_version": "v8.resolved_run_contract.v1",
    "experiment_id": "XSECT-WREV-3D",
    "strategy_kind": "cross_sectional_weekly_reversal",
    "direction": "normal",
    "price_lookback_days": 3,
    "is_control": False,
    "min_weekly_rebalances": 12,
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

CFG_SPECS = {
    "trial_specs": {
        "XSECT-WREV-3D": {"price_lookback_days": 3, "is_control": False},
        "XSECT-WREV-7D": {"price_lookback_days": 7, "is_control": False},
        "XSECT-WREV-14D": {"price_lookback_days": 14, "is_control": False},
        CONTROL_ID: {"price_lookback_days": 7, "is_control": True},
    },
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _comparison_file(directory: Path, name: str = "v8_cmp_ok.json",
                     all_match: bool = True) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(json.dumps({
        "schema_version": 4, "all_match": all_match,
        "checks": {"pnl_match": all_match, "mdd_match": all_match},
    }), encoding="utf-8")
    return path


def _refresh_canonical_hash(exp_dir: Path) -> None:
    hashes_doc = json.loads(
        (exp_dir / "artifact_hashes.json").read_text(encoding="utf-8"))
    hashes_doc["hashes"]["canonical_metrics.json"] = _sha(
        exp_dir / "canonical_metrics.json")
    (exp_dir / "artifact_hashes.json").write_text(
        json.dumps(hashes_doc), encoding="utf-8")


def make_v8_trial(
    tmp_path: Path,
    *,
    experiment_id: str = "XSECT-WREV-3D",
    rebalances_scored: int | None = 30,
    total_pnl: float | None = None,
) -> Path:
    """Golden synthetic trial patched into a V8 weekly trial identity."""
    exp_dir = make_golden_trial(tmp_path / experiment_id)
    canonical = json.loads(
        (exp_dir / "canonical_metrics.json").read_text(encoding="utf-8"))
    canonical["experiment_id"] = experiment_id
    canonical["matrix_id"] = "v8_xsect_weekly_reversal"
    if rebalances_scored is not None:
        canonical["rebalances_scored"] = rebalances_scored
    if total_pnl is not None:
        canonical["total_pnl"] = total_pnl
    (exp_dir / "canonical_metrics.json").write_text(
        json.dumps(canonical), encoding="utf-8")
    _refresh_canonical_hash(exp_dir)
    return exp_dir


def _finalize_v8(exp_dir: Path, *, contract: dict | None = None,
                 effective_n_trials: int | None = 8, **overrides):
    kwargs = dict(
        resolved_contract=contract or dict(V8_CONTRACT),
        sibling_trials=GOLDEN_SIBLINGS,
        repro_comparison_path=_comparison_file(exp_dir.parent),
        a7_verdict="V8_TERMINAL_AUDIT_PASS",
        effective_n_trials=effective_n_trials,
    )
    kwargs.update(overrides)
    summary = finalize_trial_v8(exp_dir, **kwargs)
    docs = {name: json.loads((exp_dir / name).read_text(encoding="utf-8"))
            for name in SIX_FINAL_ARTIFACTS}
    return summary, docs


# --------------------------------------------------------------------------- #
# six standard artifacts via delegation + FG8 augmentation
# --------------------------------------------------------------------------- #
def test_synthetic_trial_writes_all_six_artifacts_lock_eligible(tmp_path):
    exp_dir = make_v8_trial(tmp_path)
    summary, docs = _finalize_v8(exp_dir)
    assert sorted(docs) == sorted(SIX_FINAL_ARTIFACTS)
    for name in SIX_FINAL_ARTIFACTS:
        assert (exp_dir / name).is_file()
    assert summary["all_hard_gates_pass"] is True
    assert summary["verdict"] == "LOCK_ELIGIBLE"
    assert summary["score_meaningful"] is True
    assert summary["artifact_family"] == "V8_FINALIZER_A4"
    gates = {g["gate"]: g for g in docs["final_gate_result.json"]["gates"]}
    assert list(gates)[-1] == "FG8"
    fg8 = gates["FG8"]
    assert fg8["status"] == "PASS" and fg8["skipped"] is False
    row = fg8["criteria"][0]
    assert row["check"] == "weekly_rebalances_at_least_minimum"
    assert row["measured_value"] == 30.0
    assert row["threshold"] == 12.0 and row["operator"] == ">="
    assert summary["fg8"]["measured_value"] == 30.0
    meta = docs["final_gate_result.json"]["v8_meta"]
    assert meta == {
        "experiment_id": "XSECT-WREV-3D",
        "matrix_id": "v8_xsect_weekly_reversal",
        "direction": "normal",
        "price_lookback_days": 3,
        "is_control": False,
    }


def test_fg8_skipped_honestly_when_contract_field_absent(tmp_path):
    contract = json.loads(json.dumps(V8_CONTRACT))
    del contract["min_weekly_rebalances"]
    _, docs = _finalize_v8(make_v8_trial(tmp_path), contract=contract)
    gate_doc = docs["final_gate_result.json"]
    fg8 = next(g for g in gate_doc["gates"] if g["gate"] == "FG8")
    assert fg8["status"] == "SKIPPED"
    assert fg8["skipped"] is True
    assert fg8["pass"] is None
    assert fg8["criteria"][0]["reason"] == \
        "min_weekly_rebalances_not_in_contract_skip_not_fail"
    # skip-not-fail: absence neither blocks the verdict nor fabricates a pass
    assert gate_doc["all_hard_gates_pass"] is True


def test_fg8_threshold_under_thresholds_block_also_supported(tmp_path):
    contract = json.loads(json.dumps(V8_CONTRACT))
    del contract["min_weekly_rebalances"]
    contract["thresholds"]["min_weekly_rebalances"] = 12
    _, docs = _finalize_v8(make_v8_trial(tmp_path), contract=contract)
    fg8 = next(g for g in docs["final_gate_result.json"]["gates"]
               if g["gate"] == "FG8")
    assert fg8["status"] == "PASS" and fg8["skipped"] is False


def test_fg8_fail_blocks_verdict_and_rescinds_scorecard_band(tmp_path):
    contract = json.loads(json.dumps(V8_CONTRACT))
    contract["min_weekly_rebalances"] = 50  # measured only 30
    summary, docs = _finalize_v8(make_v8_trial(tmp_path), contract=contract)
    fg8 = next(g for g in docs["final_gate_result.json"]["gates"]
               if g["gate"] == "FG8")
    assert fg8["status"] == "FAIL" and fg8["pass"] is False
    assert summary["verdict"] == "NOT_ELIGIBLE"
    assert summary["all_hard_gates_pass"] is False
    scorecard = docs["final_scorecard.json"]
    assert scorecard["score_meaningful"] is False
    assert scorecard["band"] is None
    assert "FG8" in scorecard.get("v8_note", "")


def test_fg8_unmeasurable_when_present_but_engine_count_missing(tmp_path):
    exp_dir = make_v8_trial(tmp_path, rebalances_scored=None)
    summary, _ = _finalize_v8(exp_dir)
    assert summary["fg8"]["status"] == "FAIL"
    assert summary["fg8"]["skipped"] is False
    assert summary["verdict"] == "NOT_ELIGIBLE"


def test_missing_comparison_or_a7_fails_closed(tmp_path):
    summary, _ = _finalize_v8(make_v8_trial(tmp_path),
                              repro_comparison_path=None, a7_verdict=None)
    assert summary["gate_statuses"]["FG6"] == "FAIL"
    assert summary["gate_statuses"]["FG7"] == "FAIL"
    assert summary["verdict"] == "NOT_ELIGIBLE"


def test_missing_comparison_file_fails_closed_not_crash(tmp_path):
    exp_dir = make_v8_trial(tmp_path)
    summary, _ = _finalize_v8(
        exp_dir, repro_comparison_path=tmp_path / "ghost_cmp.json")
    repro = json.loads(
        (exp_dir / "reproduction_report.json").read_text(encoding="utf-8"))
    assert repro["entries"][0]["status"] == "MISSING_OR_UNREADABLE_FAIL_CLOSED"
    assert summary["gate_statuses"]["FG6"] == "FAIL"


def test_a7_mapping_with_findings_normalizes_and_can_fail(tmp_path):
    summary, _ = _finalize_v8(
        make_v8_trial(tmp_path),
        a7_verdict={"unresolved_high": 1, "unresolved_critical": 0})
    assert summary["gate_statuses"]["FG7"] == "FAIL"


# --------------------------------------------------------------------------- #
# DSR effective_n_trials passthrough (fail closed on None)
# --------------------------------------------------------------------------- #
def test_dsr_effective_n_trials_passthrough_fail_closed_none(tmp_path):
    _, docs = _finalize_v8(make_v8_trial(tmp_path), effective_n_trials=21)
    haircut = docs["statistical_haircut.json"]
    assert haircut["effective_n_trials"] == 21

    _, docs_none = _finalize_v8(make_v8_trial(tmp_path / "none-case"),
                                effective_n_trials=None)
    haircut_none = docs_none["statistical_haircut.json"]
    assert haircut_none["effective_n_trials"] is None
    assert haircut_none["dsr"]["dsr"] == DSR_UNAVAILABLE
    assert haircut_none["dsr"]["reason"] == "effective_n_trials_missing"
    # PBO stays at its fail-closed sentinel: the comparable-cohort returns
    # matrix is a family-level input, not a per-trial one.
    assert docs_none["statistical_haircut.json"]["pbo"]["pbo"] == \
        "PBO_UNAVAILABLE_FAIL_CLOSED"


# --------------------------------------------------------------------------- #
# family summary -- §7.2 conjunction, adjacent pairs, control rule
# --------------------------------------------------------------------------- #
REVERSAL_IDS = ((3, "XSECT-WREV-3D"), (7, "XSECT-WREV-7D"),
                (14, "XSECT-WREV-14D"))


def _family_siblings(own_lookback: int) -> list[dict]:
    """Family-coherent FG1/FG3 sibling descriptors for one trial."""
    siblings = []
    for lookback, exp_id in REVERSAL_IDS:
        if lookback == own_lookback:
            continue
        siblings.append({
            "experiment_id": exp_id, "is_control": False,
            "price_lookback_days": lookback, "net_pnl": 3000.0,
            "profit_factor": 1.20, "mechanism_pass": True,
            "fold_pnls": {"F1": 1500.0, "F2": 1500.0},
        })
    siblings.append({
        "experiment_id": CONTROL_ID, "is_control": True,
        "price_lookback_days": 7, "net_pnl": -4000.0,
        "profit_factor": 0.85, "mechanism_pass": False,
        "fold_pnls": {"F1": -2000.0, "F2": -2000.0},
    })
    return siblings


def _family_dirs(tmp_path: Path, scenario: str) -> list[Path]:
    """Finalized reversal trio (+ control) for one family scenario.

    Scenarios: clean (3P/7P/14P), mid_fail (3P/7F/14P), weekly_fail
    (all FG8-fail via impossible rebalance floor), control_beats.
    """
    dirs: list[Path] = []
    for lookback, exp_id in REVERSAL_IDS:
        root = tmp_path / f"fam-{scenario}-{lookback}D"
        contract = json.loads(json.dumps(V8_CONTRACT))
        contract["experiment_id"] = exp_id
        contract["price_lookback_days"] = lookback
        if scenario == "weekly_fail":
            contract["min_weekly_rebalances"] = 99
        exp_dir = make_v8_trial(root, experiment_id=exp_id)
        if scenario == "mid_fail" and lookback == 7:
            canonical = json.loads(
                (exp_dir / "canonical_metrics.json").read_text(encoding="utf-8"))
            canonical["total_pnl"] = -1.0
            (exp_dir / "canonical_metrics.json").write_text(
                json.dumps(canonical), encoding="utf-8")
            _refresh_canonical_hash(exp_dir)
        _finalize_v8(exp_dir, contract=contract,
                     sibling_trials=_family_siblings(lookback))
        dirs.append(exp_dir)
    control_root = tmp_path / f"fam-{scenario}-{CONTROL_ID}"
    control_contract = json.loads(json.dumps(V8_CONTRACT))
    control_contract["experiment_id"] = CONTROL_ID
    control_contract["is_control"] = True
    control_contract["price_lookback_days"] = 7
    control_dir = make_v8_trial(
        control_root, experiment_id=CONTROL_ID,
        total_pnl=999999.0 if scenario == "control_beats" else 100.0)
    _finalize_v8(control_dir, contract=control_contract,
                 sibling_trials=_family_siblings(7))
    dirs.append(control_dir)
    return dirs


def test_adjacent_pair_math_3d_pass_7d_fail_14d_pass_pair_exists(tmp_path):
    dirs = _family_dirs(tmp_path, "mid_fail")
    summary = build_family_summary(dirs, dict(CFG_SPECS))
    assert [t["all_hard_gates_pass"] for t in summary["trials"]] == \
        [True, False, True, True]
    assert summary["passing_lookbacks"] == [3, 14]
    assert summary["adjacent_pairs"] == [[3, 14]]
    assert summary["pair_exists"] is True
    assert summary["control_check"] == "PASS"
    assert summary["core_hard_gate_conjunction_pass"] is True
    assert summary["family_verdict"] == FAMILY_EXPLORATORY


def test_all_three_pass_two_pairs_and_lock_requires_statistical_flags(
        tmp_path):
    dirs = _family_dirs(tmp_path, "clean")
    exploratory = build_family_summary(dirs, dict(CFG_SPECS))
    assert exploratory["adjacent_pairs"] == [[3, 7], [7, 14]]
    assert exploratory["pair_exists"] is True
    assert exploratory["family_verdict"] == FAMILY_EXPLORATORY
    assert any("lock_withheld" in r for r in exploratory["reasons"])

    locked = build_family_summary(dirs, {
        **dict(CFG_SPECS),
        "a7_terminal_pass": True,
        "pbo_comparable_cohort_valid": True})
    assert locked["family_verdict"] == FAMILY_LOCK


def test_single_passing_lookback_yields_no_pair_reject_all(tmp_path):
    dirs = _family_dirs(tmp_path, "weekly_fail")
    summary = build_family_summary(dirs, dict(CFG_SPECS))
    assert summary["passing_lookbacks"] == []
    assert summary["adjacent_pairs"] == [] and summary["pair_exists"] is False
    assert summary["core_hard_gate_conjunction_pass"] is False
    assert summary["family_verdict"] == FAMILY_REJECT_ALL


def test_control_beats_best_detection_forces_reject_all(tmp_path):
    dirs = _family_dirs(tmp_path, "control_beats")
    summary = build_family_summary(dirs, dict(CFG_SPECS))
    assert summary["pair_exists"] is True          # reversals themselves fine
    assert summary["control_check"] == "FAIL_CONTROL_BEATS_BEST"
    assert any(r.startswith("control_beats_best:") for r in summary["reasons"])
    assert summary["best_reversal_net_pnl"] == pytest.approx(5000.0)
    assert summary["control_net_pnl_worst_case"] == pytest.approx(999999.0)
    assert summary["core_hard_gate_conjunction_pass"] is False
    assert summary["family_verdict"] == FAMILY_REJECT_ALL


def test_unreadable_or_empty_family_invalidated_fail_closed(tmp_path):
    dirs = _family_dirs(tmp_path, "clean")
    (dirs[0] / "final_gate_result.json").unlink()
    summary = build_family_summary(dirs, dict(CFG_SPECS))
    assert summary["family_verdict"] == FAMILY_INVALIDATED
    assert summary["core_hard_gate_conjunction_pass"] is False
    assert summary["unreadable_trial_dirs"] == [str(dirs[0])]

    empty = build_family_summary([], dict(CFG_SPECS))
    assert empty["family_verdict"] == FAMILY_INVALIDATED
    assert empty["unreadable_trial_dirs"] == ["no_trial_dirs_provided"]


# --------------------------------------------------------------------------- #
# global ledger -- snapshot / append_verified / digest / cohort split
# --------------------------------------------------------------------------- #
def _entry(n: int, matrix_id: str) -> dict:
    return {
        "experiment_id": f"E{n}",
        "kind": "CELL_RESULT",
        "schema": "v4",
        "matrix_id": matrix_id,
        "verdict": "REJECT",
        "appended_at": f"2026-08-20T00:00:{n:02d}+00:00",
    }


def test_snapshot_count_sha_and_digest_roundtrip(tmp_path):
    path = tmp_path / "ledger.jsonl"
    rows = [_entry(1, "v7_xsect_funding_price_divergence"),
            _entry(2, "v8_xsect_weekly_reversal")]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows),
                    encoding="utf-8")
    snap = snapshot(path)
    assert snap["count"] == 2 and snap["existed"] is True
    assert snap["rows"] == rows
    assert snap["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest(snap) == digest(rows)
    mutated = [dict(r) for r in rows]
    mutated[0]["verdict"] = "PASS"
    assert digest(mutated) != digest(rows)


def test_snapshot_missing_file_is_honest_empty(tmp_path):
    snap = snapshot(tmp_path / "absent.jsonl")
    assert snap["existed"] is False
    assert snap["count"] == 0 and snap["rows"] == []
    assert snap["sha256"] is None


def test_corrupt_line_raises_fail_closed(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"ok": 1}\n{not json}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="global_ledger_corrupt_line"):
        snapshot(path)


def test_append_verified_appends_only_after_verification(tmp_path):
    path = tmp_path / "ledger.jsonl"
    append_verified(_entry(1, "v6_matrix"), path)
    append_verified(_entry(2, "v8_core"), path)
    assert snapshot(path)["count"] == 2
    assert verify_append_only(path) is True

    stored = append_verified({"experiment_id": "E3", "verdict": "REJECT"},
                             path)
    assert stored["experiment_id"] == "E3"
    assert "appended_at" in stored
    assert snapshot(path)["count"] == 3


def test_append_verified_refuses_bad_entries_and_tampered_files(tmp_path):
    path = tmp_path / "ledger.jsonl"
    with pytest.raises(ValueError, match="requires_non_null"):
        append_verified({"verdict": "X"}, path)
    with pytest.raises(ValueError, match="must_be_mapping"):
        append_verified("not-a-mapping", path)  # type: ignore[arg-type]

    good = tmp_path / "tampered.jsonl"
    good.write_text("".join(json.dumps(r) + "\n" for r in [
        _entry(5, "v6_m"),
        _entry(2, "v6_m"),           # appended_at goes backwards => tamper
    ]), encoding="utf-8")
    before = good.read_bytes()
    with pytest.raises(ValueError, match="append_only"):
        append_verified(_entry(9, "v9_future"), good)
    assert good.read_bytes() == before      # nothing written on refusal


def test_cohort_split_by_matrix_id_prefix():
    rows = [
        _entry(1, "v6_xsect_funding_price_divergence"),
        _entry(2, "v7_xsect_funding_price_divergence"),
        _entry(3, "v8_xsect_weekly_reversal"),
        _entry(4, "v8_core_second_shard"),              # case/prefix v8
        _entry(5, "v8x_breadth_crypto_1y"),             # NOT pooled into V8
        _entry(6, "v80_typo_shard"),                    # v80 is not v8
        {"experiment_id": "E7", "verdict": "REJECT"},   # no matrix_id
    ]
    split = cohort_split(rows)
    assert set(split) == {"V6", "V7", "V8", "V8X", "UNMAPPED"}
    assert [r["experiment_id"] for r in split["V6"]] == ["E1"]
    assert [r["experiment_id"] for r in split["V7"]] == ["E2"]
    assert [r["experiment_id"] for r in split["V8"]] == ["E3", "E4"]
    assert [r["experiment_id"] for r in split["V8X"]] == ["E5"]
    assert {r["experiment_id"] for r in split["UNMAPPED"]} == {"E6", "E7"}
    # partition invariant: nothing dropped silently
    assert sum(len(v) for v in split.values()) == len(rows)
    assert cohort_of({"matrix_id": "v8_x"}) == "V8"
    assert cohort_of({}) == "UNMAPPED"
