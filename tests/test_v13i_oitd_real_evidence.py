"""V13 I lane -- real-snapshot schedule-only evidence for OITD (h, i, j).

Run against the READ-ONLY workspace snapshot (skipped when the data roots
are absent); SCOPE BOUNDARY: NO PnL, no returns and no scored metric is
computed anywhere in this module -- every assertion is about counts,
breadth, weights, timestamps, turnover estimates, cost-drag floors and
ledger row types.

* (h) schedule-only feasibility on the REAL snapshot for all three frozen
  arms: 52 stamped schedule, pinned F0/F1/F2 folds (>= 15 retained
  decisions each), hysteresis book validation, cap/gross/cash invariants,
  honest signal availability, and the frozen
  ``research.v11.cost_feasibility`` gate (base <= 8%/yr, stressed
  <= 12%/yr, decisions/365d <= 60, median intended holding >= 3d, max
  symbol turnover share <= 25%) with the fold-terminal force-flat
  artifacts recorded per the frozen A3 vocabulary;
* (h, continued) deterministic double generation on the real snapshot:
  the full 49-stamp chained book schedule per arm computed twice from
  independent plugin instances is byte-identical (canonical-JSON sha256);
* (i) non-vacuous drop-one: at every retained stamp the dropped symbol IS
  the HELD max-|weight| symbol (tie-break ascending name), was actually
  held at that stamp, the remaining weights are UNCHANGED (no post-score
  renormalisation), and a zero-position book is refused;
* (j) the dummy publication dry-run into a TEMPORARY namespaced ledger:
  adapter traversal per arm, zero-position DUMMY payload REFUSED
  (OBSERVATION row), an out-of-contract cell REFUSED against the frozen
  family cell matrix, one DUMMY CELL_RESULT published per arm, and the
  exact replay of every row is an idempotent skip with ZERO counter
  delta.  The metrics are fixed synthetic constants (kind
  ``DUMMY_DRYRUN_METRICS``) -- zero scored metrics exist in this lane.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from research.v12.accounting import (
    ROW_TYPE_CELL_RESULT,
    ROW_TYPE_OBSERVATION,
    STAGE_IDEMPOTENT_REPLAY,
    STAGE_PUBLISHED,
    STAGE_REFUSED,
    read_v12_ledger,
    v12_denominator_view,
)
from research.v12.data_contract import BARS_ROOT, OI_CONSOLIDATED_ROOT
from research.v13.families.oitd.audits import (
    DRYRUN_DUMMY_METRICS_KIND,
    evidence_drop_one,
    evidence_schedule_only_real,
    evidence_identity,
    load_snapshot_data,
    require_temporary_ledger,
    run_dummy_dryrun,
)
from research.v13.families.oitd.plugin import OitdPlugin
from research.v13.families.oitd.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    CONTROL_ARM,
    NEIGHBOUR_ARM,
)

_DATA_PRESENT = Path(BARS_ROOT).is_dir() and Path(OI_CONSOLIDATED_ROOT).is_dir()

_requires_data = pytest.mark.skipif(
    not _DATA_PRESENT, reason="read-only workspace data absent"
)


@pytest.fixture(scope="module")
def snapshot():
    return load_snapshot_data()


# --------------------------------------------------------------------- #
# (h) schedule-only feasibility on the REAL snapshot
# --------------------------------------------------------------------- #
@_requires_data
def test_schedule_only_feasibility_on_the_real_snapshot(snapshot) -> None:
    payload = evidence_schedule_only_real(data=snapshot)
    assert payload["scored"] is False
    assert payload["real_pnl"] is False
    assert payload["universe_size"] == 19
    assert payload["window"] == [
        "2025-08-22T00:00:00Z",
        "2026-08-21T00:00:00Z",
    ]
    for arm_id, arm in payload["arms"].items():
        assert arm["n_schedule_stamps"] == 52, arm_id
        # the purge strips exactly one stamp per fold: 52 - 3 = 49 retained
        assert arm["n_retained_decisions"] == 49, arm_id
        # pinned folds: F0/F1/F2, >= 15 retained decisions each
        folds = arm["folds"]
        assert [f["label"] for f in folds] == ["F0", "F1", "F2"]
        assert all(f["retained"] >= 15 for f in folds), arm_id
        assert all(f["purge_days"] == 1 for f in folds)
        assert sum(f["retained"] for f in folds) == 49
        assert sum(f["declared"] for f in folds) == 52
        # breadth and side membership floors on the real data
        assert arm["n_eligible_min"] >= 12, arm_id
        assert arm["min_side_members_observed"] >= 4, arm_id
        # cap / gross invariants hold at every real stamp
        assert arm["max_abs_weight_observed"] <= 0.30 + 1e-12, arm_id
        assert arm["max_gross_observed"] <= 1.0 + 1e-9, arm_id
        # the frozen availability floor: a computable book at >= 95% of the
        # retained stamps (here 100%); per-symbol coverage never drops below
        # 18/19 = 0.947 (one fail-closed data-gap symbol at the first stamp)
        assert arm["stamps_with_book_ratio"] >= 0.95, arm_id
        assert arm["stamps_with_book_ratio"] == 1.0, arm_id
        assert arm["signal_availability_ratio_min"] >= 18.0 / 19.0 - 1e-12, arm_id
        # every book passes the frozen validator
        assert arm["book_validation"] == {
            "verdict": "PASS",
            "n_pass": 49,
            "n_fail": 0,
        }
        # turnover / holding estimates exist (schedule-only quantities)
        diag = arm["schedule_diagnostics"]
        assert diag["decision_count"] == 49
        assert diag["one_way_turnover_total"] > 0.0
        assert diag["n_held_spans"] > 0
        assert diag["funding_events_while_held"] > 0
        # the frozen A3 cost-feasibility gate PASSES, incl. the three
        # fold-terminal FORCED_FLAT boundary actions recorded separately
        gate = arm["cost_gate"]
        assert gate["verdict"] == "PASS", arm_id
        assert gate["forced_flat_decisions"] == 3
        assert gate["one_way_turnover_forced_flat"] > 0.0
        floors = gate["floors"]
        assert floors["max_base_cost_drag_frac_of_gross"]["status"] == "PASS"
        assert floors["max_base_cost_drag_frac_of_gross"]["observed"] <= 0.08
        assert floors["max_stressed_cost_drag_frac_of_gross"]["status"] == "PASS"
        assert floors["max_stressed_cost_drag_frac_of_gross"]["observed"] <= 0.12
        assert floors["max_discretionary_decisions_per_365d"]["status"] == "PASS"
        assert floors["min_median_intended_holding_days"]["status"] == "PASS"
        assert floors["min_median_intended_holding_days"]["observed"] >= 3.0
        assert floors["max_symbol_turnover_share"]["status"] == "PASS"
        assert floors["max_symbol_turnover_share"]["observed"] <= 0.25


@_requires_data
def test_real_books_reconcile_cash_and_side_budgets(snapshot) -> None:
    """Cap/gross/cash invariants re-verified from the raw chained books."""
    from research.v13.families.oitd.audits import (
        build_plugins,
        tradeable_universe_symbols,
    )

    universe = tradeable_universe_symbols()
    plugins = build_plugins(data=snapshot, symbols=universe)
    import math

    for arm_id in ARM_IDS:
        plugin = plugins[arm_id]
        stress = plugin.baseline_stress()
        retained = plugin.decision_instants(stress=stress)
        for stamp in retained:
            payload = plugin.targets_at(stamp, universe=universe, stress=stress)
            weights = {sym: float(w) for sym, w in payload["weights"]}
            assert weights, (arm_id, stamp)
            gross = math.fsum(abs(w) for w in weights.values())
            assert max(abs(w) for w in weights.values()) <= 0.30 + 1e-12
            assert gross <= 1.0 + 1e-9
            assert 1.0 - gross >= -1e-9  # cash reconciles, never negative
            longs = math.fsum(w for w in weights.values() if w > 0.0)
            shorts = math.fsum(-w for w in weights.values() if w < 0.0)
            assert longs == pytest.approx(0.5, abs=1e-9), (arm_id, stamp)
            assert shorts == pytest.approx(0.5, abs=1e-9), (arm_id, stamp)


@_requires_data
def test_real_double_generation_byte_identical_all_arms(snapshot) -> None:
    """(d, real) full 49-stamp schedules per arm, two independent runs."""
    import hashlib
    import json

    from research.v13.families.oitd.audits import (
        build_plugins,
        tradeable_universe_symbols,
    )

    universe = tradeable_universe_symbols()
    digests = {}
    for arm_id in ARM_IDS:
        texts = []
        for _run in range(2):
            plugin = OitdPlugin(
                arm_id=arm_id,
                day_turnover_by_symbol=dict(snapshot.day_turnover_by_symbol),
                bars_by_symbol=dict(snapshot.bars_by_symbol),
                oi_by_symbol=None if arm_id == CONTROL_ARM else dict(snapshot.oi_by_symbol),
                mark_by_symbol=None if arm_id == CONTROL_ARM else dict(snapshot.mark_by_symbol),
                settlements_by_symbol=dict(snapshot.settlements_by_symbol),
                tick_sizes=dict(snapshot.tick_sizes),
            )
            stress = plugin.baseline_stress()
            retained = plugin.decision_instants(stress=stress)
            payloads = [
                plugin.targets_at(int(stamp), universe=universe, stress=stress)
                for stamp in retained
            ]
            texts.append(
                json.dumps(payloads, sort_keys=True, separators=(",", ":"), default=str)
            )
        assert texts[0] == texts[1], arm_id
        digests[arm_id] = hashlib.sha256(texts[0].encode("utf-8")).hexdigest()
    # the three arms schedule DIFFERENT books (anchor != control on real data)
    assert digests[ANCHOR_ARM] != digests[CONTROL_ARM]
    assert digests[ANCHOR_ARM] != digests[NEIGHBOUR_ARM]
    assert digests[NEIGHBOUR_ARM] != digests[CONTROL_ARM]


# --------------------------------------------------------------------- #
# (i) non-vacuous drop-one on the REAL snapshot
# --------------------------------------------------------------------- #
@_requires_data
def test_drop_one_selects_a_held_maximum_abs_weight_symbol(snapshot) -> None:
    payload = evidence_drop_one(data=snapshot)
    assert payload["scored"] is False
    assert payload["all_match"] is True
    assert payload["any_zero_held"] is False
    for arm_id, arm in payload["arms"].items():
        assert arm["n_stamps"] == 49, arm_id
        assert arm["n_held_at"] == 49, arm_id  # never a vacuous selection
        for check in arm["checks"]:
            assert check["selected"] is not None
            assert check["held"] is True  # the dropped symbol WAS held
            assert check["unheld_never_selected"] is True
            assert check["zero_held_book_refused"] is False  # never zero-held
            assert check["dropped_book_weights_unchanged"] is True


@_requires_data
def test_drop_one_book_differs_and_refuses_zero_position(snapshot) -> None:
    from research.v13.families.oitd.audits import (
        build_plugins,
        tradeable_universe_symbols,
    )
    from research.v13.families.oitd.book import (
        EligibilityShortfall,
        drop_one_book,
        held_max_abs_weight_symbol,
    )

    universe = tradeable_universe_symbols()
    plugins = {
        arm_id: OitdPlugin(
            arm_id=arm_id,
            day_turnover_by_symbol=dict(snapshot.day_turnover_by_symbol),
            bars_by_symbol=dict(snapshot.bars_by_symbol),
            oi_by_symbol=None if arm_id == CONTROL_ARM else dict(snapshot.oi_by_symbol),
            mark_by_symbol=None if arm_id == CONTROL_ARM else dict(snapshot.mark_by_symbol),
            settlements_by_symbol=dict(snapshot.settlements_by_symbol),
            tick_sizes=dict(snapshot.tick_sizes),
        )
        for arm_id in (ANCHOR_ARM,)
    }
    plugin = plugins[ANCHOR_ARM]
    stress = plugin.baseline_stress()
    first_stamp = plugin.decision_instants(stress=stress)[0]
    book = plugin.targets_at(first_stamp, universe=universe, stress=stress)
    weights = {sym: float(w) for sym, w in book["weights"]}
    target = held_max_abs_weight_symbol(weights)
    assert target is not None and target in weights  # actually HELD
    dropped = drop_one_book(weights)
    assert dropped["dropped_symbol"] == target
    remaining = {sym: w for sym, w in dropped["weights"]}
    assert target not in remaining
    for sym, w in weights.items():
        if sym != target:
            assert remaining[sym] == weights[sym]  # UNCHANGED, no renorm
    with pytest.raises(EligibilityShortfall):
        drop_one_book({})  # zero-position books are refused


# --------------------------------------------------------------------- #
# (j) dummy publication dry-run into a TEMPORARY ledger
# --------------------------------------------------------------------- #
def test_require_temporary_ledger_refuses_non_temp_paths(tmp_path) -> None:
    with pytest.raises(Exception):
        require_temporary_ledger(None)
    with pytest.raises(Exception):
        require_temporary_ledger(tmp_path / "wrong_name.jsonl")
    with pytest.raises(Exception):
        require_temporary_ledger(tmp_path / "dryrun_wrong_ext.json")
    ok = require_temporary_ledger(tmp_path / "dryrun_ok.jsonl")
    assert ok.name == "dryrun_ok.jsonl"


@_requires_data
def test_dummy_dryrun_publish_refusals_and_zero_delta_replay(tmp_path, snapshot) -> None:
    ledger = tmp_path / "dryrun_oitd.jsonl"
    payload = run_dummy_dryrun(ledger_path=ledger, data=snapshot)
    assert payload["scored"] is False
    assert payload["real_pnl"] is False
    assert payload["ledger_path"] == str(ledger)
    assert payload["ok"] is True
    assert payload["ledger_denominators"]["published"] == 3
    assert payload["ledger_denominators"]["observed"] == 4
    for arm_id, arm in payload["arms"].items():
        traversal = arm["adapter_traversal"]
        assert traversal["strategy_id"] == "hyp_a13_v13_a8_oitd"
        assert traversal["n_universe"] == 19
        assert traversal["n_schedule_instants"] == 52
        assert traversal["n_retained_decisions"] == 49
        assert traversal["n_folds"] == 3
        assert traversal["fold_labels"] == ["F0", "F1", "F2"]
        assert traversal["dropped_fold_accepted"] is True
        assert traversal["n_fills_applied"] == 19
        assert traversal["first_stamp_mark_finite"] is True
        assert traversal["n_funding_cashflows_probe_span"] > 0
        assert traversal["funding_sign_convention"] == "LONG_PAYS_POSITIVE_RATE"
        assert traversal["declared_execution_lag"].startswith(
            "orders release at decision + 15m"
        )
        # zero-position DUMMY payload -> REFUSED (observation row)
        assert arm["zero_position_stage"] == STAGE_REFUSED
        assert arm["zero_position_refused"] is True
        assert arm["zero_position_replay_stage"] == STAGE_IDEMPOTENT_REPLAY
        # the out-of-contract probe is exercised once, on the anchor arm
        if arm_id == ANCHOR_ARM:
            assert arm["out_of_contract_stage"] == STAGE_REFUSED
            assert arm["out_of_contract_refused"] is True
            assert "REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT" in arm["out_of_contract_reason"]
        else:
            assert arm["out_of_contract_stage"] == "NOT_PROBED_ANCHOR_ONLY"
        # one DUMMY publish per arm; exact replay is an idempotent skip
        assert arm["dummy_publish_stage"] in (STAGE_PUBLISHED, STAGE_IDEMPOTENT_REPLAY)
        assert arm["replay_stage"] == STAGE_IDEMPOTENT_REPLAY
        assert arm["replay_idempotent"] is True
        assert arm["counter_delta_on_replay"] == {"published": 0, "observed": 0}
        assert arm["dummy_metrics_kind"] == DRYRUN_DUMMY_METRICS_KIND
    state = read_v12_ledger(ledger)
    row_types = [str(row["row_type"]) for row in state["rows"]]
    assert row_types.count(ROW_TYPE_CELL_RESULT) == 3
    assert row_types.count(ROW_TYPE_OBSERVATION) == 4
    # ZERO scored metrics: the ledger holds only DUMMY-dryrun rows for this
    # family -- CELL_RESULT rows carry digests (never metric values) and the
    # frozen family id; OBSERVATION rows carry a documented refusal reason.
    from research.v13.families.oitd.strategy import FAMILY_ID

    for row in state["rows"]:
        if row["row_type"] == ROW_TYPE_CELL_RESULT:
            assert str(row["family"]) == FAMILY_ID
            assert len(str(row["result_sha256"])) == 64
            assert len(str(row["arm_config_digest"])) == 64
            assert str(row["arm_id"]) in payload["arms"]
        else:
            assert str(row.get("reason", "")).strip()
    assert state["count"] == 7


@_requires_data
def test_dummy_dryrun_replay_is_idempotent_on_rerun(tmp_path, snapshot) -> None:
    """Re-running the whole dry-run on the SAME ledger adds no rows."""
    ledger = tmp_path / "dryrun_oitd.jsonl"
    first = run_dummy_dryrun(ledger_path=ledger, data=snapshot)
    assert first["ok"] is True
    before = v12_denominator_view(ledger)
    second = run_dummy_dryrun(ledger_path=ledger, data=snapshot)
    after = v12_denominator_view(ledger)
    assert before == after
    assert after["published"] == 3 and after["observed"] == 4
    for _arm_id, arm in second["arms"].items():
        assert arm["zero_position_replay_stage"] == STAGE_IDEMPOTENT_REPLAY
        assert arm["replay_idempotent"] is True


@_requires_data
def test_identity_evidence_digest_report_matches(snapshot) -> None:
    payload = evidence_identity()
    assert payload["artifact"] == "identity"
    assert set(payload["arms"]) == set(ARM_IDS)
    for arm_id in ARM_IDS:
        assert payload["digest_report"][arm_id]["match"] is True
        assert payload["recorded_digests"][arm_id] == (
            payload["digest_report"][arm_id]["computed_from_identity"]
        )
