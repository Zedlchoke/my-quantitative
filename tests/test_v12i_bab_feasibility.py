"""Schedule-only feasibility tests for A12-V12-BAB-LOWBETA (no PnL).

Real-stamp books of every frozen arm are validated through the frozen
validator :mod:`research.v12.feasibility` (breadth, frozen 4+4 leg identity,
weight cap) and the exact-arm dummy dry-run publishes DUMMY finite metrics
through :mod:`research.v12.accounting` into a temporary EMPTY ledger
(zero-position REFUSED, replay idempotent) -- synthetic frame only, never a
real scored metric.

The committed artifacts under ``research/audits/v12i/bab_lowbeta/`` carry
the full evidence; these tests re-derive the core verdicts in-suite.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from research.v12.accounting import (
    REFUSED_ZERO_POSITIONS,
    STAGE_IDEMPOTENT_REPLAY,
    STAGE_PUBLISHED,
    STAGE_REFUSED,
    freeze_family_cell_contract,
    publish_v12_cell,
    read_v12_ledger,
    v12_denominator_view,
)
from research.v12.families.bab_lowbeta.audits import (
    _dummy_metrics_for,
    build_beta_ranking_frame,
    build_schedule_feasibility,
    make_plugin,
)
from research.v12.families.bab_lowbeta.plugin import ROLE_BY_ARM
from research.v12.families.bab_lowbeta.strategy import (
    CAP,
    FAMILY_ID,
    LEGS_PER_SIDE,
    MIN_ELIGIBLE,
    STRATEGY_ID,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    frozen_arm_config_digest,
    frozen_arm_ids,
    weekly_monday_stamps,
)
from research.v12.feasibility import validate_stamp_schedule
from research.adapter_v10.stress import derive_family_stress_matrix
from research.adapter_v10.runner import run_strategy

AUDIT_DIR = Path(__file__).resolve().parents[1] / "research" / "audits" / "v12i" / "bab_lowbeta"


# --------------------------------------------------------------------------- #
# Committed real-data artifacts (produced by audits.main(); read here)
# --------------------------------------------------------------------------- #
def test_committed_schedule_feasibility_artifact_passes():
    path = AUDIT_DIR / "schedule_feasibility.json"
    assert path.exists(), "run research.v12.families.bab_lowbeta.audits.main() first"
    doc = json.loads(path.read_text())
    assert doc["family_id"] == FAMILY_ID
    assert doc["verdict"] == "PASS"
    assert len(doc["per_arm"]) == 3
    for arm_id, arm in doc["per_arm"].items():
        assert arm["n_stamps"] == 52
        assert arm["n_skip_stamps"] == 0
        assert arm["feasibility_verdict"] == "PASS"
        assert arm["legs_4v4_all_book_stamps"] is True
        assert arm["max_abs_weight_over_book_stamps"] <= CAP + 1e-9
        assert arm["n_book_stamps"] == 50  # 52 - 2 fold-boundary force-flats


def test_committed_c1_artifact_passes():
    path = AUDIT_DIR / "c1_fields.json"
    assert path.exists()
    doc = json.loads(path.read_text())
    assert doc["verdict"] == "PASS"
    assert doc["close_decode_crosscheck"]["verdict"] == "PASS"
    assert doc["pit_beta_proof_verdict"] == "PASS"
    assert all(
        p["truncated_bars_identical_to_full"] for p in doc["pit_beta_proof_at_stamps"]
    )


def test_committed_double_generation_and_drop_one_artifacts_pass():
    double = json.loads((AUDIT_DIR / "double_generation.json").read_text())
    assert double["verdict"] == "PASS"
    assert all(a["byte_identical"] for a in double["per_arm"].values())
    drop_one = json.loads((AUDIT_DIR / "drop_one.json").read_text())
    assert drop_one["verdict"] == "PASS"
    assert drop_one["survived"] is True
    assert drop_one["dropped_symbol_absent_from_reduced_book"] is True
    assert drop_one["reduced_legs"] == {
        "n_long": LEGS_PER_SIDE,
        "n_short": LEGS_PER_SIDE,
    }


# --------------------------------------------------------------------------- #
# In-suite stamp validation (synthetic closed-form frame)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def beta_bars():
    bars, _design = build_beta_ranking_frame()
    return bars


def test_every_stamp_book_passes_the_frozen_validator(beta_bars):
    plugin = make_plugin("BAB-90D-W", beta_bars)
    universe = plugin.universe(plugin.baseline_stress())
    stamps = list(plugin.schedule().instants)
    boundary = {
        int(members[-1])
        for members in plugin.fold_instants().values()
        if int(members[-1]) != int(stamps[-1])
    }
    records = []
    for stamp in stamps:
        book = plugin.targets_at(int(stamp), universe=universe, stress=plugin.baseline_stress())
        records.append({"decision_ns": int(stamp), "weights": dict(book["weights"])})
    verdict = validate_stamp_schedule(records, require_non_empty=False)
    assert verdict["verdict"] == "PASS"
    assert verdict["n_stamps"] == 52
    # non-boundary stamps carry the frozen 4+4 book within the cap
    n_books = 0
    for record, stamp in zip(records, stamps):
        weights = record["weights"]
        if not weights:
            assert int(stamp) in boundary or int(stamp) == int(stamps[-1])
            continue
        n_books += 1
        n_long = sum(1 for w in weights.values() if w > 0.0)
        n_short = sum(1 for w in weights.values() if w < 0.0)
        assert n_long == LEGS_PER_SIDE and n_short == LEGS_PER_SIDE
        assert all(abs(w) <= CAP + 1e-9 for w in weights.values())
    assert n_books == 50


def test_fold_layout_matches_the_frozen_folds(beta_bars):
    plugin = make_plugin("BAB-90D-W", beta_bars)
    fold_members = plugin.fold_instants()
    assert sorted(fold_members) == ["F0", "F1", "F2"]
    assert [len(fold_members[k]) for k in ("F0", "F1", "F2")] == [17, 18, 17]
    total = sum(len(v) for v in fold_members.values())
    assert total == 52
    # folds() must place every schedule instant into exactly one fold
    specs = plugin.folds(
        stress=plugin.baseline_stress(), instants=list(plugin.schedule().instants)
    )
    assert [spec.label for spec in specs] == ["F0", "F1", "F2"]
    assert sum(len(spec.instants) for spec in specs) == 52
    assert all(not spec.dropped for spec in specs)


def test_family_stress_matrix_derives_from_frozen_folds(beta_bars):
    """L-V11-1: the per-family cell list derives from the folds contract."""
    plugin = make_plugin("BAB-90D-W", beta_bars)
    universe = plugin.universe(plugin.baseline_stress())
    derivation = derive_family_stress_matrix(
        strategy_baseline=plugin.baseline_stress(),
        droppable_symbols=universe,
        folds=plugin.folds,
        instants=list(plugin.schedule().instants),
    )
    names = [cell.name for cell in derivation.cells]
    assert names[0] == "baseline"
    assert "drop_one_fold" in names
    assert derivation.record["folds_contract_probe_accepts_drop_one_fold"] is True
    contract = freeze_family_cell_contract(
        FAMILY_ID, [cell.spec for cell in derivation.cells]
    )
    assert len(contract) == len(names)
    # the baseline cell must be inside the derived contract
    from research.v12.accounting import canonical_cell_key

    assert canonical_cell_key(plugin.baseline_stress()) in contract


# --------------------------------------------------------------------------- #
# Exact-arm dummy dry-run via research.v12.accounting (synthetic only)
# --------------------------------------------------------------------------- #
def test_dryrun_publish_replay_and_zero_position_refusal(beta_bars):
    with tempfile.TemporaryDirectory(prefix="v12i_bab_feas_") as tmp:
        ledger_path = Path(tmp) / "dryrun_v12i_bab_lowbeta.jsonl"
        # identity-only trial keys: the zero-position refusal probe of the
        # same trial must run on its OWN empty scratch ledger
        refusal_ledger_path = Path(tmp) / "dryrun_v12i_bab_zero.jsonl"
        for arm_id in frozen_arm_ids():
            plugin = make_plugin(arm_id, beta_bars)
            result = run_strategy(plugin, write_artifact_file=False)
            assert result["scored"] is False
            assert len(result["positions"]) > 0
            derivation = derive_family_stress_matrix(
                strategy_baseline=plugin.baseline_stress(),
                droppable_symbols=result["universe"],
                folds=plugin.folds,
                instants=list(plugin.schedule().instants),
            )
            contract = freeze_family_cell_contract(
                FAMILY_ID, [cell.spec for cell in derivation.cells]
            )
            dummy = _dummy_metrics_for(
                arm_id, result, list(plugin.schedule().instants)
            )
            first = publish_v12_cell(
                strategy_id=STRATEGY_ID,
                family=FAMILY_ID,
                arm_id=arm_id,
                arm_config_digest=frozen_arm_config_digest(arm_id),
                stress_signature=plugin.baseline_stress().signature(),
                window_start_iso=WINDOW_START_ISO,
                window_end_iso=WINDOW_END_ISO,
                scored_metrics=dummy,
                result_sha256=str(result["hashes"]["result_sha256"]),
                ledger_path=ledger_path,
                family_contract_cells=contract,
                producer_head_sha="V12I_BAB_TEST_NO_REAL_HEAD",
            )
            assert first["stage"] == STAGE_PUBLISHED
            assert first["published_delta"] == 1
            replay = publish_v12_cell(
                strategy_id=STRATEGY_ID,
                family=FAMILY_ID,
                arm_id=arm_id,
                arm_config_digest=frozen_arm_config_digest(arm_id),
                stress_signature=plugin.baseline_stress().signature(),
                window_start_iso=WINDOW_START_ISO,
                window_end_iso=WINDOW_END_ISO,
                scored_metrics=dummy,
                result_sha256=str(result["hashes"]["result_sha256"]),
                ledger_path=ledger_path,
                family_contract_cells=contract,
                producer_head_sha="V12I_BAB_TEST_NO_REAL_HEAD",
            )
            assert replay["stage"] == STAGE_IDEMPOTENT_REPLAY
            assert replay["published_delta"] == 0
            zero = dict(dummy)
            zero["n_positions"] = 0
            zero["decisions"] = []
            zero["fills"] = []
            refusal = publish_v12_cell(
                strategy_id=STRATEGY_ID,
                family=FAMILY_ID,
                arm_id=arm_id,
                arm_config_digest=frozen_arm_config_digest(arm_id),
                stress_signature=plugin.baseline_stress().signature(),
                window_start_iso=WINDOW_START_ISO,
                window_end_iso=WINDOW_END_ISO,
                scored_metrics=zero,
                result_sha256=str(result["hashes"]["result_sha256"]),
                ledger_path=refusal_ledger_path,
                family_contract_cells=contract,
                producer_head_sha="V12I_BAB_TEST_NO_REAL_HEAD",
            )
            assert refusal["stage"] == STAGE_REFUSED
            assert any(
                str(r).startswith(REFUSED_ZERO_POSITIONS) for r in refusal["reasons"]
            )
        view = v12_denominator_view(ledger_path)
        assert view["published"] == 3
        assert view["observed"] == 0
        refusal_view = v12_denominator_view(refusal_ledger_path)
        assert refusal_view["published"] == 0
        assert refusal_view["observed"] == 3
        state = read_v12_ledger(ledger_path)
        assert state["count"] == 3
        keys = [row["trial_key"] for row in state["rows"]]
        assert len(set(keys)) == 3  # exactly-once per trial


def test_committed_dryrun_artifact_passes():
    path = AUDIT_DIR / "dryrun.json"
    assert path.exists()
    doc = json.loads(path.read_text())
    assert doc["verdict"] == "PASS"
    assert doc["no_real_pnl_attestation"]["real_pnl"] is False
    for arm_id, arm in doc["arms"].items():
        assert arm["publish_stage"] == "PUBLISHED"
        assert arm["replay_stage"] == "IDEMPOTENT_REPLAY_SKIPPED"
        assert arm["zero_position_stage"] == "REFUSED"
        assert any(r.startswith("REFUSED_ZERO_POSITIONS") for r in arm["zero_position_reasons"])
        assert arm["adapter_run"]["scored"] is False
