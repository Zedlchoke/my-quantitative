"""V12P A4 tests -- pre-score feasibility, drop-one repair, per-family stress
matrix derivation, OILEV-V2 diversified book, and the stamp calendar.

Scope guard: everything here is schedule-only (counts, durations, weights,
verdicts).  No PnL, no returns, no scored metric is computed or asserted.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

from research.adapter_v10.protocol import (
    ContractViolation,
    StressSpec,
)
from research.adapter_v10.stress import (
    BASELINE_NAME,
    STRESS_SURFACE_VARIANTS,
    build_stress_spec,
    derive_family_stress_matrix,
    probe_family_dropped_fold_support,
    select_drop_one_symbol,
    stress_matrix_cells,
)
from research.v12.feasibility import (
    REASON_EMPTY_BOOK,
    REASON_LEG_COUNT_MISMATCH,
    REASON_WEIGHT_ABOVE_CAP,
    REASON_WEIGHT_NOT_FINITE,
    schedule_diagnostics,
    validate_stamp_schedule,
    validate_target_book,
)
from research.v12.oilev_v2_book import (
    BENCHMARK_SYMBOL,
    CAP_MAX,
    EligibilityShortfall,
    build_oilev_v2_book,
)
from research.v12.oilev_v2_spec import (
    OILEV_V2_ARMS,
    provisional_oi_feature_scores,
    stamp_calendar,
)

DAY_NS = 86_400_000_000_000


def _baseline() -> StressSpec:
    return StressSpec(name=BASELINE_NAME, tick_slip_ticks=1)


# --------------------------------------------------------------------------- #
# Pre-score target-book validator
# --------------------------------------------------------------------------- #
def test_validator_passes_cap_compliant_diversified_book():
    book = build_oilev_v2_book(
        {f"S{i:02d}USDT": float(i) for i in range(10)}
    )
    check = validate_target_book(book, decision_ns=1_000, legs_per_side=4)
    assert check["status"] == "OK"
    assert check["reason_codes"] == ["OK"]
    assert check["n_longs"] == 4 and check["n_shorts"] == 4
    assert check["max_abs_weight"] == pytest.approx(0.125, abs=1e-12)
    assert check["cap_max"] == pytest.approx(0.30, abs=1e-12)


def test_validator_flags_cap_breach_and_accepts_exact_cap():
    over = {"weights": [["AAAUSDT", 0.31]], "status": "OK"}
    check = validate_target_book(over)
    assert check["status"] == "FAIL"
    assert any(code.startswith(REASON_WEIGHT_ABOVE_CAP) for code in check["reason_codes"])
    exact = {"weights": [["AAAUSDT", 0.30], ["BBBUSDT", -0.30]]}
    assert validate_target_book(exact)["status"] == "OK"


def test_validator_flags_non_finite_and_duplicate_and_shape():
    nan_book = {"weights": [["AAAUSDT", float("nan")]]}
    check = validate_target_book(nan_book)
    assert any(code.startswith(REASON_WEIGHT_NOT_FINITE) for code in check["reason_codes"])
    dup = validate_target_book({"weights": [["AAAUSDT", 0.1], ["AAAUSDT", -0.1]]})
    assert any(code.startswith("DUPLICATE_SYMBOL") for code in dup["reason_codes"])
    bad = validate_target_book({"weights": [["AAAUSDT"]]})
    assert any(code.startswith("BAD_BOOK_SHAPE") for code in bad["reason_codes"])


def test_validator_empty_book_fail_closed_only_when_contract_requires():
    empty = {"weights": []}
    check = validate_target_book(empty, require_non_empty=True)
    assert check["status"] == "FAIL"
    assert REASON_EMPTY_BOOK in check["reason_codes"]
    assert validate_target_book(empty, require_non_empty=False)["status"] == "OK"


def test_validator_leg_count_mismatch_for_oilev_v2_identity():
    book = {"weights": [[f"S{i}", 0.125] for i in range(3)] + [[f"T{i}", -0.125] for i in range(4)]}
    check = validate_target_book(book, legs_per_side=4)
    assert check["status"] == "FAIL"
    assert any(code.startswith(REASON_LEG_COUNT_MISMATCH) for code in check["reason_codes"])
    assert check["reason_codes"][-1].endswith("3L/4S")


def test_schedule_verdict_fail_closed_every_stamp():
    good = build_oilev_v2_book({f"S{i:02d}USDT": float(i) for i in range(10)})
    bad = {"weights": [["AAAUSDT", 0.9]], "status": "OK"}
    ok_verdict = validate_stamp_schedule([good, good], legs_per_side=4)
    assert ok_verdict["verdict"] == "PASS"
    assert ok_verdict["n_stamps"] == 2 and ok_verdict["n_fail"] == 0
    fail_verdict = validate_stamp_schedule([good, bad], legs_per_side=4)
    assert fail_verdict["verdict"] == "FAIL"
    assert fail_verdict["n_fail"] == 1
    assert fail_verdict["failing_stamps"][0]["index"] == 1
    unavailable = validate_stamp_schedule([])
    assert unavailable["verdict"] == "UNAVAILABLE_FAIL_CLOSED"


# --------------------------------------------------------------------------- #
# L-V11-7: drop-one-symbol repair
# --------------------------------------------------------------------------- #
def test_drop_one_selects_largest_held_weight_not_lexicographic_first():
    # Hand-built regression book: the lexicographically-first HELD symbol is
    # NOT the largest-weight holder, and an unheld symbol sits in the cohort.
    realized = {"AAAAUSDT": 0.05, "BBBBUSDT": 0.25, "CCCCUSDT": 0.0}
    dropped = select_drop_one_symbol(
        droppable_symbols=("AAAAUSDT", "BBBBUSDT", "CCCCUSDT"),
        realized_weights=realized,
    )
    assert dropped == ("BBBBUSDT",)
    # the unheld symbol can never be selected, whatever its cohort position
    for _ in range(1):
        assert "CCCCUSDT" not in dropped
    # full spec path carries the same selection
    spec = build_stress_spec(
        "drop_one_symbol",
        strategy_baseline=_baseline(),
        droppable_symbols=("AAAAUSDT", "BBBBUSDT", "CCCCUSDT"),
        realized_weights=realized,
    )
    assert spec.drop_symbols == ("BBBBUSDT",)


def test_drop_one_exact_tie_breaks_lexicographically_smallest():
    dropped = select_drop_one_symbol(
        droppable_symbols=("CCCCUSDT", "BBBBUSDT", "AAAAUSDT"),
        realized_weights={"CCCCUSDT": 0.2, "BBBBUSDT": 0.2, "AAAAUSDT": 0.1},
    )
    assert dropped == ("BBBBUSDT",)


def test_drop_one_cannot_select_unheld_or_foreign_symbol():
    with pytest.raises(ContractViolation):
        select_drop_one_symbol(
            droppable_symbols=("AAAUSDT", "BBBUSDT"),
            realized_weights={"AAAUSDT": 0.0, "BBBUSDT": 0.0},
        )
    with pytest.raises(ContractViolation):
        select_drop_one_symbol(
            droppable_symbols=("AAAUSDT",),
            realized_weights={"ZZZUSDT": 0.5},
        )


def test_drop_one_legacy_fallback_unchanged_for_frozen_driver_signature():
    # No realized book in the frozen V10/V11 call signature: sorted-first
    # fallback preserved (reproducibility of the frozen drivers).
    assert select_drop_one_symbol(droppable_symbols=("ZZZUSDT", "AAAUSDT")) == ("AAAUSDT",)
    spec = build_stress_spec(
        "drop_one_symbol",
        strategy_baseline=_baseline(),
        droppable_symbols=("AAAUSDT", "BBBUSDT"),
    )
    assert spec.drop_symbols == ("AAAUSDT",)


# --------------------------------------------------------------------------- #
# L-V11-1: per-family stress-cell matrix derivation
# --------------------------------------------------------------------------- #
def _lot_like_folds(*, stress: StressSpec, instants) -> tuple:
    """Frozen LOT posture: any dropped fold is refused."""
    if stress.dropped_fold_index is not None:
        raise ContractViolation("the frozen LOT family declares no dropped-fold stress cell")
    return tuple(("F0", int(v)) for v in instants)


def _illiq_like_folds(*, stress: StressSpec, instants) -> tuple:
    """Frozen ILLIQ/OILEV posture: dropped folds are honoured."""
    dropped = stress.dropped_fold_index is not None and stress.dropped_fold_index == 0
    return tuple(("F0", int(v), bool(dropped)) for v in instants)


def test_probe_refuses_lot_like_contract_and_keeps_oilev_like():
    instants = [1, 2, 3]
    assert probe_family_dropped_fold_support(
        baseline_stress=_baseline(), folds=_lot_like_folds, instants=instants
    ) is False
    assert probe_family_dropped_fold_support(
        baseline_stress=_baseline(), folds=_illiq_like_folds, instants=instants
    ) is True
    with pytest.raises(ContractViolation):
        probe_family_dropped_fold_support(
            baseline_stress=_baseline(), folds=_illiq_like_folds, instants=[]
        )


def test_derivation_lot_like_excludes_drop_one_fold_and_records_it():
    derivation = derive_family_stress_matrix(
        strategy_baseline=_baseline(),
        droppable_symbols=("AAAUSDT", "BBBUSDT"),
        folds=_lot_like_folds,
        instants=[1, 2, 3],
    )
    names = [cell.name for cell in derivation.cells]
    assert names[0] == BASELINE_NAME
    assert "drop_one_fold" not in names
    assert len(names) == 5
    assert derivation.record["excluded_cells"] == {
        "drop_one_fold": "NOT_IN_FAMILY_DECLARED_SUPPORTED_CELLS"
    }
    assert derivation.record["folds_contract_probe_accepts_drop_one_fold"] is False


def test_derivation_oilev_like_keeps_all_six_cells():
    derivation = derive_family_stress_matrix(
        strategy_baseline=_baseline(),
        droppable_symbols=("AAAUSDT",),
        folds=_illiq_like_folds,
        instants=[1, 2, 3],
    )
    names = [cell.name for cell in derivation.cells]
    assert names == [BASELINE_NAME, *STRESS_SURFACE_VARIANTS]
    assert derivation.record["excluded_cells"] == {}


def test_derivation_explicit_supported_cells_exclude_and_record():
    derivation = derive_family_stress_matrix(
        strategy_baseline=_baseline(),
        supported_cells=("fee_slippage_x1_5", "plus_2_ticks"),
    )
    names = [cell.name for cell in derivation.cells]
    assert names == [BASELINE_NAME, "fee_slippage_x1_5", "plus_2_ticks"]
    assert set(derivation.record["excluded_cells"]) == {
        "plus_1_event_delay",
        "drop_one_symbol",
        "drop_one_fold",
    }


def test_derivation_fail_closed_inputs():
    with pytest.raises(ContractViolation):
        derive_family_stress_matrix(strategy_baseline=_baseline())  # no contract at all
    with pytest.raises(ContractViolation):
        derive_family_stress_matrix(
            strategy_baseline=_baseline(),
            folds=_illiq_like_folds,
            instants=[1],
            supported_cells=("fee_slippage_x1_5",),
        )
    with pytest.raises(ContractViolation):
        build_stress_spec(
            "drop_one_fold",
            strategy_baseline=_baseline(),
            supported_cells=("fee_slippage_x1_5", "drop_one_symbol"),
        )


def test_legacy_six_cell_superset_still_default():
    cells = stress_matrix_cells(
        strategy_baseline=_baseline(), droppable_symbols=("AAAUSDT", "BBBUSDT")
    )
    assert [cell.name for cell in cells] == [BASELINE_NAME, *STRESS_SURFACE_VARIANTS]
    assert len(cells) == 6


def test_derivation_drop_one_honours_realized_weights():
    derivation = derive_family_stress_matrix(
        strategy_baseline=_baseline(),
        droppable_symbols=("AAAAUSDT", "BBBBUSDT", "CCCCUSDT"),
        realized_weights={"AAAAUSDT": 0.05, "BBBBUSDT": 0.25, "CCCCUSDT": 0.0},
        folds=_illiq_like_folds,
        instants=[1, 2, 3],
    )
    by_name = {cell.name: cell for cell in derivation.cells}
    assert by_name["drop_one_symbol"].spec.drop_symbols == ("BBBBUSDT",)
    assert derivation.record["drop_one_symbol_uses_realized_weights"] is True


# --------------------------------------------------------------------------- #
# OILEV-V2 diversified book
# --------------------------------------------------------------------------- #
def test_book_four_lowest_four_highest_equal_weight_under_cap():
    scores = {f"S{i:02d}USDT": float(i) for i in range(10)}
    book = build_oilev_v2_book(scores)
    assert book["n_eligible"] == 10
    assert book["longs"] == ["S00USDT", "S01USDT", "S02USDT", "S03USDT"]
    assert book["shorts"] == ["S06USDT", "S07USDT", "S08USDT", "S09USDT"]
    weights = dict(book["weights"])
    assert len(weights) == 8
    assert all(abs(abs(w) - 0.125) <= 1e-12 for w in weights.values())
    assert sum(1 for w in weights.values() if w > 0) == 4
    assert sum(1 for w in weights.values() if w < 0) == 4
    assert book["max_abs_weight"] <= CAP_MAX
    assert book["scale_applied"] == pytest.approx(1.0, abs=1e-12)


def test_book_requires_nine_eligible_fail_closed():
    scores = {f"S{i:02d}USDT": float(i) for i in range(8)}
    with pytest.raises(EligibilityShortfall):
        build_oilev_v2_book(scores)
    # non-finite entries are ineligible, never guessed
    scores_nan = {**{f"S{i:02d}USDT": float(i) for i in range(8)}, "S99USDT": float("nan")}
    with pytest.raises(EligibilityShortfall):
        build_oilev_v2_book(scores_nan)
    ok = build_oilev_v2_book({**scores, "S98USDT": 100.0, "S99USDT": float("inf")})
    assert ok["n_eligible"] == 9
    assert ok["diagnostics"]["ineligible"] == {"S99USDT": "NON_FINITE_SCORE"}


def test_book_uniform_whole_book_scale_never_clips_names():
    scores = {f"S{i:02d}USDT": float(i) for i in range(12)}
    book = build_oilev_v2_book(scores, gross=3.0)  # per-name 0.375 > cap
    weights = dict(book["weights"])
    assert book["scale_applied"] == pytest.approx(0.30 / 0.375, abs=1e-12)
    assert book["max_abs_weight"] == pytest.approx(0.30, abs=1e-12)
    assert max(abs(w) for w in weights.values()) <= 0.30
    # uniform: every name carries exactly the same scaled magnitude
    assert all(abs(abs(w) - 0.30) <= 1e-12 for w in weights.values())
    assert book["gross_after_scale"] == pytest.approx(2.4, abs=1e-9)


def test_book_invert_flips_end_to_end():
    scores = {f"S{i:02d}USDT": float(i) for i in range(10)}
    plain = build_oilev_v2_book(scores)
    flipped = build_oilev_v2_book(scores, invert=True)
    assert flipped["longs"] == plain["shorts"]
    assert flipped["shorts"] == plain["longs"]
    plain_w = dict(plain["weights"])
    for sym, weight in dict(flipped["weights"]).items():
        assert weight == pytest.approx(-plain_w[sym], abs=1e-12)


def test_book_exact_score_ties_break_lexicographically():
    scores = {f"S{i:02d}USDT": 1.0 for i in range(9)}
    book = build_oilev_v2_book(scores)
    assert book["longs"] == ["S00USDT", "S01USDT", "S02USDT", "S03USDT"]
    assert book["shorts"] == ["S05USDT", "S06USDT", "S07USDT", "S08USDT"]


def test_book_refuses_benchmark_and_records_hedge_context():
    scores = {f"S{i:02d}USDT": float(i) for i in range(9)}
    scores[BENCHMARK_SYMBOL] = 4.2
    with pytest.raises(ContractViolation):
        build_oilev_v2_book(scores)
    del scores[BENCHMARK_SYMBOL]
    book = build_oilev_v2_book(scores, beta_hedge_ratios={"S00USDT": 1.1})
    assert book["beta_hedge"]["ratios"] == {"S00USDT": 1.1}
    assert "never appear as a position" in book["beta_hedge"]["semantics"]
    # the hedge is context-only: weights are untouched by the ratios
    assert dict(book["weights"]) == dict(build_oilev_v2_book(scores)["weights"])
    with pytest.raises(ContractViolation):
        build_oilev_v2_book(scores, beta_hedge_ratios={"S00USDT": float("nan")})


# --------------------------------------------------------------------------- #
# Stamp calendar (V11 convention, reused for the calendar only)
# --------------------------------------------------------------------------- #
def test_stamp_calendar_weekly_mondays_52_stamps():
    stamps = stamp_calendar()
    assert len(stamps) == 52
    assert list(stamps) == sorted(set(stamps))
    for stamp in stamps:
        moment = datetime.fromtimestamp(stamp / 1e9, tz=timezone.utc)
        assert moment.weekday() == 0
        assert (moment.hour, moment.minute, moment.second) == (0, 0, 0)
    assert datetime.fromtimestamp(stamps[0] / 1e9, tz=timezone.utc).date().isoformat() == "2025-08-25"
    assert datetime.fromtimestamp(stamps[-1] / 1e9, tz=timezone.utc).date().isoformat() == "2026-08-17"


def test_arm_table_matches_plan_8_2():
    kinds = [(arm["feature_kind"], arm["formation_days"], arm["invert"]) for arm in OILEV_V2_ARMS]
    assert ("oi_flow", 28, False) in kinds  # anchor
    assert ("oi_stock", 56, False) in kinds  # neighbour
    assert ("oi_flow", 28, True) in kinds  # sign-inverted control
    assert len(kinds) == 3


# --------------------------------------------------------------------------- #
# End-to-end schedule pipeline (synthetic OI; schedule-only)
# --------------------------------------------------------------------------- #
def test_synthetic_oi_schedule_pipeline_52_stamps_pass():
    n_symbols = 12
    start = datetime(2025, 7, 1, 23, 55, tzinfo=timezone.utc)
    oi_by_symbol = {}
    for s in range(n_symbols):
        series = []
        for day in range(417):
            ts = int(datetime.fromtimestamp(start.timestamp() + day * 86_400, tz=timezone.utc).timestamp()) * 1_000_000_000
            value = 100.0 * math.exp(0.001 * day + 0.05 * s * math.sin(0.02 * day + s))
            series.append((ts, value))
        oi_by_symbol[f"S{s:02d}USDT"] = series
    stamps = stamp_calendar()
    records = []
    for stamp in stamps:
        scores = provisional_oi_feature_scores(
            oi_by_symbol, stamp, feature_kind="oi_flow", formation_days=28
        )
        records.append({**build_oilev_v2_book(scores), "decision_ns": stamp})
    verdict = validate_stamp_schedule(records, legs_per_side=4)
    assert verdict["verdict"] == "PASS"
    assert verdict["n_stamps"] == 52 and verdict["n_fail"] == 0
    diagnostics = schedule_diagnostics(records)
    assert diagnostics["decision_count"] == 52
    assert diagnostics["one_way_turnover"]["total"] >= 0.0
    assert diagnostics["holdings"]["status"] == "OK"
    assert diagnostics["holdings"]["n_spans"] > 0
    # weekly stamps: every realized holding span is an exact 7-day multiple
    for span in diagnostics["holdings"]["spans"]:
        assert span["duration_days"] % 7 == 0
        assert span["duration_days"] >= 7.0
    # no local funding series -> the funding metric is UNAVAILABLE, never inferred
    assert diagnostics["funding_events_while_held"]["status"] == "UNAVAILABLE"
    assert diagnostics["verdict"] == "UNAVAILABLE_FAIL_CLOSED"
    # records without nanosecond stamps degrade durations to UNAVAILABLE
    no_ns = [build_oilev_v2_book(scores) for scores in
             (provisional_oi_feature_scores(oi_by_symbol, s, feature_kind="oi_flow", formation_days=28)
              for s in stamps)]
    degraded = schedule_diagnostics(no_ns)
    assert degraded["holdings"]["status"] == "UNAVAILABLE"
    assert degraded["holdings"]["reason_code"] == "NO_DECISION_NS_IN_RECORDS"


def test_schedule_diagnostics_counts_funding_events_when_series_injected():
    stamps = [0 * DAY_NS, 7 * DAY_NS, 14 * DAY_NS]
    records = [
        {"decision_ns": stamps[0], "weights": [["AAAUSDT", 0.125], ["BBBUSDT", -0.125]]},
        {"decision_ns": stamps[1], "weights": [["AAAUSDT", 0.125], ["BBBUSDT", -0.125]]},
        {"decision_ns": stamps[2], "weights": [["CCCUSDT", 0.125]]},
    ]
    funding = {"AAAUSDT": [1 * DAY_NS, 5 * DAY_NS], "BBBUSDT": [3 * DAY_NS]}
    diagnostics = schedule_diagnostics(records, funding_events_by_symbol=funding)
    assert diagnostics["funding_events_while_held"]["status"] == "OK"
    assert diagnostics["funding_events_while_held"]["events_while_held_total"] == 3
    # one-way turnover: stamp2->stamp3 drops AAAUSDT/BBBUSDT, adds CCCUSDT
    assert diagnostics["one_way_turnover"]["per_step"][0] == pytest.approx(0.0, abs=1e-12)
    assert diagnostics["one_way_turnover"]["per_step"][1] == pytest.approx(0.375, abs=1e-12)
