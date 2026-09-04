"""V13 Phase P1 -- accounting/publication regression (five-property proof).

Closes the V13-P1 gaps of ``PLAN_crypto_v13.md`` section 6 (P1) on top of the
inherited V11/V12 suites; every test here is OFFLINE and SYNTHETIC (tmp_path
ledgers only, no real data files, no network) and NO frozen V11/V12 science,
loader, driver, ledger or control byte is touched.

The five plan properties and where each is proven:

1. zero-position / out-of-contract refusal (L-V11-4)
     COVERED by the inherited suites
     (tests/test_v12p_a2_publication.py::test_zero_position_baseline_is_refused_and_cannot_publish,
     ::test_missing_or_invalid_position_evidence_fails_closed,
     ::test_family_contract_superset_refusal,
     ::test_legacy_global_ledger_path_gets_the_guard_only_when_opted_in;
     tests/test_v12r_driver.py::test_oilev_end_to_end_publish_replay_refusal).
     This module adds only the untested refusal-precedence pin: the
     family-contract gate fires BEFORE the position-evidence gate.
2. drop-one non-vacuousness (L-V11-7) -- the drop-one convention must PROVE
   the dropped symbol held positions in the anchor or neighbour book
     selection-side COVERED by tests/test_v12p_a4_feasibility.py
     (::test_drop_one_selects_largest_held_weight_not_lexicographic_first,
     ::test_drop_one_cannot_select_unheld_or_foreign_symbol,
     ::test_derivation_drop_one_honours_realized_weights); the cross-arm
     "held in anchor OR neighbour" non-vacuousness verdict is CLOSED here.
3. observed counter increments exactly once; exact replays move ZERO counters
     COVERED by tests/test_v12p_a2_publication.py
     (::test_refusal_observed_exactly_once_and_replay_adds_no_row,
     ::test_exact_replay_of_published_trial_is_fully_idempotent,
     ::test_concurrent_writers_append_serialized_rows_without_corruption)
     and tests/test_v11p_a2_publication.py
     (::test_compute_once_counts_observed_even_when_publication_refused,
     ::test_true_idempotent_replay_moves_neither_counter).  Referenced, not
     rewritten.
4. append-only corrections leave counters untouched
     historical-byte preservation COVERED
     (tests/test_v11p_a2_publication.py::test_historical_v1_ledger_bytes_are_never_rewritten,
     ::test_m01_reconciliation_is_append_only_119_published_120_observed;
     tests/test_v12p_a2_publication.py::test_exact_replay_of_published_trial_is_fully_idempotent).
     The V12-ledger chain property -- sequential OBSERVATION corrections
     never rewrite a prior byte and never move the PUBLISHED counter -- is
     CLOSED here.
5. simultaneous writers cannot both append: appends go through A1
   serialization (the process-local ``_V12_LEDGER_LOCK`` critical section in
   research/v12/accounting.py)
     outcome-level COVERED (tests/test_v12p_a2_publication.py
     ::test_concurrent_writers_append_serialized_rows_without_corruption;
     tests/test_v11p_a2_publication.py::test_concurrent_publish_of_one_trial_appends_exactly_once,
     ::test_concurrent_distinct_arms_append_without_corruption).
     The direct BLOCKING proof -- a second writer provably cannot complete an
     append while the lock is held, plus the same-key race on the raw
     ``append_v12_row`` primitive -- is CLOSED here.

Serialization scope (honest, no retrofit): ``_V12_LEDGER_LOCK`` is a
process-local ``threading.RLock``; cross-PROCESS writers to ONE ledger file
are excluded by factory policy (one writer per worktree ledger, documented in
research/v12/accounting.py).  These tests prove the in-process A1
serialization contract that the code actually provides.
"""

from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
from pathlib import Path

import pytest

from research.adapter_v10.protocol import ContractViolation, StressSpec
from research.adapter_v10.stress import (
    HELD_WEIGHT_TOL,
    derive_family_stress_matrix,
    select_drop_one_symbol,
)
from research.v12.accounting import (
    REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT,
    REFUSED_TRIAL_KEY_ALREADY_PRESENT,
    REFUSED_ZERO_POSITIONS,
    ROW_TYPE_CELL_RESULT,
    ROW_TYPE_OBSERVATION,
    STAGE_PUBLISHED,
    STAGE_REFUSED,
    _V12_LEDGER_LOCK,
    append_v12_row,
    freeze_family_cell_contract,
    publish_v12_cell,
    read_v12_ledger,
    v12_denominator_view,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The launch-1 incident shape (L-V11-4): score_valid=true over all-zero
#: finite metrics for a book that held NO positions.
ZERO_POSITION_METRICS = {
    "score_valid": True,
    "net_return_sum": 0.0,
    "expectancy_per_day": 0.0,
    "max_drawdown": 0.0,
    "n_positions": 0,
    "n_decisions": 0,
    "n_fills": 0,
}

#: Synthetic realized books for the drop-one non-vacuousness proof: the
#: lexicographically-first candidate (AAAUSDT) is UNHELD in the anchor book,
#: so the frozen legacy fallback would make the cell vacuous.
ANCHOR_BOOK = {"AAAUSDT": 0.0, "BBBUSDT": 0.25, "CCCUSDT": 0.10}
NEIGHBOUR_BOOK = {"AAAUSDT": 0.20, "BBBUSDT": 0.0, "CCCUSDT": 0.41}
DROPPABLE = ("AAAUSDT", "BBBUSDT", "CCCUSDT")

BASELINE_CELL = StressSpec(name="baseline")
OUT_OF_CONTRACT_CELL = StressSpec(name="drop_one_fold", dropped_fold_index=0)
HEAD = "0" * 40


# --------------------------------------------------------------------------- #
# Property -> coverage map (the executable V13-P1 gate record)
# --------------------------------------------------------------------------- #
COVERAGE_MAP = {
    "P1_zero_position_and_out_of_contract_refusal": {
        "lesson": "L-V11-4",
        "status": "COVERED",
        "cited": [
            "tests/test_v12p_a2_publication.py::test_zero_position_baseline_is_refused_and_cannot_publish",
            "tests/test_v12p_a2_publication.py::test_missing_or_invalid_position_evidence_fails_closed",
            "tests/test_v12p_a2_publication.py::test_family_contract_superset_refusal",
            "tests/test_v12r_driver.py::test_oilev_end_to_end_publish_replay_refusal",
        ],
        "closed_by": [
            "test_v13p_refusal_first_hit_wins_zero_position_and_out_of_contract",
        ],
    },
    "P2_drop_one_non_vacuousness": {
        "lesson": "L-V11-7",
        "status": "CLOSED",
        "cited": [
            "tests/test_v12p_a4_feasibility.py::test_drop_one_selects_largest_held_weight_not_lexicographic_first",
            "tests/test_v12p_a4_feasibility.py::test_drop_one_cannot_select_unheld_or_foreign_symbol",
            "tests/test_v12p_a4_feasibility.py::test_derivation_drop_one_honours_realized_weights",
        ],
        "closed_by": [
            "test_v13p_drop_one_cell_proves_held_symbol_from_arm_book",
            "test_v13p_drop_one_vacuous_shape_detected_and_unconstructable",
        ],
    },
    "P3_observed_increments_once_replays_never": {
        "lesson": "L-V11-4",
        "status": "COVERED",
        "cited": [
            "tests/test_v12p_a2_publication.py::test_refusal_observed_exactly_once_and_replay_adds_no_row",
            "tests/test_v12p_a2_publication.py::test_exact_replay_of_published_trial_is_fully_idempotent",
            "tests/test_v11p_a2_publication.py::test_compute_once_counts_observed_even_when_publication_refused",
            "tests/test_v11p_a2_publication.py::test_true_idempotent_replay_moves_neither_counter",
        ],
    },
    "P4_append_only_corrections_leave_counters_untouched": {
        "lesson": "L-V11-5",
        "status": "CLOSED",
        "cited": [
            "tests/test_v11p_a2_publication.py::test_historical_v1_ledger_bytes_are_never_rewritten",
            "tests/test_v11p_a2_publication.py::test_m01_reconciliation_is_append_only_119_published_120_observed",
        ],
        "closed_by": [
            "test_v13p_append_only_corrections_preserve_bytes_and_published_counter",
        ],
    },
    "P5_simultaneous_writers_serialized_by_a1_lock": {
        "lesson": "L-V11-5",
        "status": "CLOSED",
        "cited": [
            "tests/test_v12p_a2_publication.py::test_concurrent_writers_append_serialized_rows_without_corruption",
            "tests/test_v11p_a2_publication.py::test_concurrent_publish_of_one_trial_appends_exactly_once",
        ],
        "closed_by": [
            "test_v13p_ledger_lock_blocks_second_writer_until_first_append_completes",
            "test_v13p_same_trial_concurrent_appends_via_primitive_land_exactly_once",
        ],
    },
}


def test_v13p_coverage_map_pins_all_five_properties():
    """The gate record names every plan property and only existing tests."""
    assert set(COVERAGE_MAP) == {
        "P1_zero_position_and_out_of_contract_refusal",
        "P2_drop_one_non_vacuousness",
        "P3_observed_increments_once_replays_never",
        "P4_append_only_corrections_leave_counters_untouched",
        "P5_simultaneous_writers_serialized_by_a1_lock",
    }
    module = sys.modules[__name__]
    for entry in COVERAGE_MAP.values():
        assert entry["status"] in ("COVERED", "CLOSED")
        for citation in entry.get("cited", []):
            assert (REPO_ROOT / citation.split("::")[0]).is_file(), citation
        for name in entry.get("closed_by", []):
            assert callable(getattr(module, name, None)), name


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _cell_result_row(trial_key: str, arm_id: str) -> dict:
    """One schema-valid CELL_RESULT row (all frozen required fields set)."""
    return {
        "row_type": ROW_TYPE_CELL_RESULT,
        "trial_key": trial_key,
        "arm_id": arm_id,
        "arm_config_digest": "5" * 64,
        "family": "v13-p1-regression",
        "cell": {"name": "baseline"},
        "result_sha256": "6" * 64,
        "published_utc": "2026-09-04T00:00:00Z",
        "producer_head_sha": HEAD,
    }


def _publish_kwargs(
    tmp_path: Path,
    *,
    arm_id: str,
    cell: StressSpec = BASELINE_CELL,
    scored_metrics=None,
    family_contract_cells=None,
    ledger_name: str = "v13p.jsonl",
) -> dict:
    return dict(
        strategy_id="strat-v13p",
        family="v13-p1-regression",
        arm_id=arm_id,
        arm_config_digest=hashlib.sha256(arm_id.encode()).hexdigest(),
        stress_signature=cell,
        window_start_iso="2026-01-01T00:00:00Z",
        window_end_iso="2026-07-01T00:00:00Z",
        scored_metrics=dict(
            scored_metrics
            if scored_metrics is not None
            else {
                "score_valid": True,
                "net_return_sum": 0.0123,
                "expectancy_per_day": 0.0004,
                "max_drawdown": 0.0031,
                "n_positions": 12,
                "n_decisions": 34,
                "n_fills": 30,
            }
        ),
        result_sha256="c" * 64,
        ledger_path=tmp_path / ledger_name,
        family_contract_cells=family_contract_cells,
        producer_head_sha=HEAD,
    )


def _read_rows(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _drop_one_nonvacuousness_verdict(
    drop_symbols, *books
) -> dict:
    """L-V11-7 verdict: does EVERY dropped symbol provably hold a position
    (|w| > HELD_WEIGHT_TOL) in at least one supplied arm book (anchor or
    neighbour)?  A dropped symbol absent from, or flushed-to-zero in, every
    supplied book makes the diagnostic VACUOUS."""
    held_in = [
        sym
        for sym in drop_symbols
        if any(
            abs(float(book.get(sym, 0.0))) > HELD_WEIGHT_TOL for book in books
        )
    ]
    return {
        "non_vacuous": bool(drop_symbols) and len(held_in) == len(drop_symbols),
        "held_in": held_in,
    }


# --------------------------------------------------------------------------- #
# P1 -- refusal (gate-order pin; per-reason coverage inherited)
# --------------------------------------------------------------------------- #
def test_v13p_refusal_first_hit_wins_zero_position_and_out_of_contract(tmp_path):
    contract = freeze_family_cell_contract(
        "v13-p1-regression", [BASELINE_CELL]
    )
    ledger = tmp_path / "order.jsonl"

    # Out-of-contract cell AND zero-position metrics: the family-contract
    # gate is gate 2 and the position gate is gate 4 -- first hit wins.
    result = publish_v12_cell(
        **_publish_kwargs(
            tmp_path,
            arm_id="oor-zero",
            cell=OUT_OF_CONTRACT_CELL,
            scored_metrics=ZERO_POSITION_METRICS,
            family_contract_cells=contract,
            ledger_name="order.jsonl",
        )
    )
    assert result["published"] is False
    assert result["stage"] == STAGE_REFUSED
    assert result["reasons"][0].startswith(REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT)
    rows = _read_rows(ledger)
    assert len(rows) == 1 and rows[0]["row_type"] == ROW_TYPE_OBSERVATION

    # The same zero-position payload inside the contract is refused with the
    # position-evidence reason (L-V11-4) and can never publish.
    result2 = publish_v12_cell(
        **_publish_kwargs(
            tmp_path,
            arm_id="in-contract-zero",
            scored_metrics=ZERO_POSITION_METRICS,
            family_contract_cells=contract,
            ledger_name="order.jsonl",
        )
    )
    assert result2["published"] is False
    assert result2["reasons"][0] == REFUSED_ZERO_POSITIONS

    view = v12_denominator_view(ledger)
    assert view == {"published": 0, "observed": 2, "observed_total": 2, "rows": 2}


# --------------------------------------------------------------------------- #
# P2 -- drop-one non-vacuousness (L-V11-7): held in anchor OR neighbour
# --------------------------------------------------------------------------- #
def test_v13p_drop_one_cell_proves_held_symbol_from_arm_book():
    for label, book, expected in (
        ("anchor", ANCHOR_BOOK, "BBBUSDT"),
        ("neighbour", NEIGHBOUR_BOOK, "CCCUSDT"),
    ):
        derivation = derive_family_stress_matrix(
            strategy_baseline=BASELINE_CELL,
            droppable_symbols=DROPPABLE,
            realized_weights=book,
            supported_cells=("drop_one_symbol",),
        )
        assert derivation.cells[0].name == "baseline"
        assert derivation.record["drop_one_symbol_uses_realized_weights"] is True
        by_name = {cell.name: cell.spec for cell in derivation.cells}
        # The lexicographically-first candidate (AAAUSDT) is unheld in the
        # anchor book -- the cell must drop the largest-|w| HELD symbol.
        assert by_name["drop_one_symbol"].drop_symbols == (expected,), label

        verdict = _drop_one_nonvacuousness_verdict(
            by_name["drop_one_symbol"].drop_symbols, ANCHOR_BOOK, NEIGHBOUR_BOOK
        )
        assert verdict["non_vacuous"] is True, label
        assert expected in verdict["held_in"]

    # The "anchor OR neighbour" clause: a cell dropped for a book where the
    # symbol is flushed to zero stays non-vacuous when the OTHER arm book
    # proves the position (union across arms, per L-V11-7).
    split_book = {"AAAUSDT": 0.0, "BBBUSDT": 0.30, "CCCUSDT": 0.0}
    dropped, = select_drop_one_symbol(
        droppable_symbols=DROPPABLE, realized_weights=split_book
    )
    assert dropped == "BBBUSDT"
    anchor_only_zero = {"AAAUSDT": 0.0, "BBBUSDT": 0.0, "CCCUSDT": 0.10}
    neighbour_holds = {"AAAUSDT": 0.15, "BBBUSDT": 0.20, "CCCUSDT": 0.0}
    verdict = _drop_one_nonvacuousness_verdict(
        (dropped,), anchor_only_zero, neighbour_holds
    )
    assert verdict["non_vacuous"] is True
    assert verdict["held_in"] == ["BBBUSDT"] and neighbour_holds["BBBUSDT"] > HELD_WEIGHT_TOL


def test_v13p_drop_one_vacuous_shape_detected_and_unconstructable():
    # A dropped symbol flushed to zero in BOTH arm books is VACUOUS.
    vacuous = _drop_one_nonvacuousness_verdict(
        ("AAAUSDT",),
        {"AAAUSDT": 0.0, "BBBUSDT": 0.30},
        {"AAAUSDT": 0.0, "BBBUSDT": 0.40},
    )
    assert vacuous["non_vacuous"] is False and vacuous["held_in"] == []
    # ...and so is a symbol absent from every book.
    absent = _drop_one_nonvacuousness_verdict(
        ("ZZZUSDT",), ANCHOR_BOOK, NEIGHBOUR_BOOK
    )
    assert absent["non_vacuous"] is False

    # The convention can never CONSTRUCT those shapes from a realized book:
    # a fully-flushed book is refused outright (no held symbol to drop)...
    with pytest.raises(ContractViolation):
        select_drop_one_symbol(
            droppable_symbols=DROPPABLE,
            realized_weights={"AAAUSDT": 0.0, "BBBUSDT": 0.0, "CCCUSDT": 0.0},
        )
    # ...and for every arm book the selected symbol is HELD in that book.
    for book in (ANCHOR_BOOK, NEIGHBOUR_BOOK):
        dropped, = select_drop_one_symbol(
            droppable_symbols=DROPPABLE, realized_weights=book
        )
        assert abs(book[dropped]) > HELD_WEIGHT_TOL


# --------------------------------------------------------------------------- #
# P4 -- append-only corrections: bytes preserved, published counter untouched
# --------------------------------------------------------------------------- #
def test_v13p_append_only_corrections_preserve_bytes_and_published_counter(tmp_path):
    ledger = tmp_path / "corrections.jsonl"
    contract = freeze_family_cell_contract(
        "v13-p1-regression", [BASELINE_CELL]
    )

    # Seed: one genuine publication.
    first = publish_v12_cell(
        **_publish_kwargs(
            tmp_path, arm_id="seed", family_contract_cells=contract,
            ledger_name="corrections.jsonl",
        )
    )
    assert first["stage"] == STAGE_PUBLISHED
    seed_view = v12_denominator_view(ledger)
    assert seed_view["published"] == 1 and seed_view["observed"] == 0
    seed_bytes = ledger.read_bytes()
    seed_rows = _read_rows(ledger)

    # Correction 1: a refused (zero-position) compute appends an OBSERVATION.
    publish_v12_cell(
        **_publish_kwargs(
            tmp_path, arm_id="corr-zero",
            scored_metrics=ZERO_POSITION_METRICS,
            family_contract_cells=contract,
            ledger_name="corrections.jsonl",
        )
    )
    after_first_correction = ledger.read_bytes()

    # Correction 2: an out-of-contract compute appends another OBSERVATION.
    publish_v12_cell(
        **_publish_kwargs(
            tmp_path, arm_id="corr-oor", cell=OUT_OF_CONTRACT_CELL,
            family_contract_cells=contract,
            ledger_name="corrections.jsonl",
        )
    )
    after_second_correction = ledger.read_bytes()

    # Append-only chain: every later state starts with every earlier state,
    # byte for byte; no row is rewritten, reordered or deleted.
    assert after_first_correction.startswith(seed_bytes)
    assert after_second_correction.startswith(after_first_correction)

    # The earlier rows survive re-reads dict-identical (no in-place mutation).
    rows = _read_rows(ledger)
    assert rows[0] == seed_rows[0]
    assert [r["row_type"] for r in rows] == [
        ROW_TYPE_CELL_RESULT,
        ROW_TYPE_OBSERVATION,
        ROW_TYPE_OBSERVATION,
    ]
    # Corrections carry no publication fields at all.
    for row in rows[1:]:
        assert "result_sha256" not in row and "published_utc" not in row

    # The corrections moved ONLY the observed counter; published is untouched.
    view = v12_denominator_view(ledger)
    assert view == {"published": 1, "observed": 2, "observed_total": 3, "rows": 3}
    # A re-read verifies every frozen invariant (unique keys, schemas) holds.
    assert read_v12_ledger(ledger)["count"] == 3


# --------------------------------------------------------------------------- #
# P5 -- A1 serialization: the lock BLOCKS a second concurrent append
# --------------------------------------------------------------------------- #
def test_v13p_ledger_lock_blocks_second_writer_until_first_append_completes(tmp_path):
    ledger = tmp_path / "serial.jsonl"
    assert append_v12_row(
        _cell_result_row("a" * 64, "seed"), ledger
    )["appended"] is True
    seeded_bytes = ledger.read_bytes()

    reached_append = threading.Event()   # writer two is at the append attempt
    finished = threading.Event()         # writer two completed its append
    outcome: dict = {}

    def second_writer() -> None:
        reached_append.set()
        outcome["append"] = append_v12_row(
            _cell_result_row("b" * 64, "second"), ledger
        )
        finished.set()

    # A1 holds the ledger lock; a second writer must be BLOCKED -- it can
    # attempt the append but can never complete one while the lock is held.
    with _V12_LEDGER_LOCK:
        thread = threading.Thread(target=second_writer, daemon=True)
        thread.start()
        assert reached_append.wait(timeout=10)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            assert not finished.is_set(), (
                "second writer completed an append while the A1 lock was held"
            )
            assert ledger.read_bytes() == seeded_bytes  # no second row landed
            time.sleep(0.05)
    # Lock released: the blocked writer now proceeds -- exactly once.
    assert finished.wait(timeout=10)
    thread.join(timeout=10)
    assert outcome["append"]["attempted"] is True
    assert outcome["append"]["appended"] is True
    assert ledger.read_bytes().startswith(seeded_bytes)  # append-only growth
    assert read_v12_ledger(ledger)["count"] == 2
    assert v12_denominator_view(ledger)["published"] == 2


def test_v13p_same_trial_concurrent_appends_via_primitive_land_exactly_once(tmp_path):
    ledger = tmp_path / "race_primitive.jsonl"
    row = _cell_result_row("c" * 64, "race")
    results: list = [None] * 8
    start = threading.Barrier(len(results))

    def attempt(index: int) -> None:
        start.wait(timeout=30)
        results[index] = append_v12_row(row, ledger)

    threads = [
        threading.Thread(target=attempt, args=(i,), daemon=True)
        for i in range(len(results))
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)

    assert all(r is not None for r in results)
    appended = [r for r in results if r["appended"]]
    refused = [r for r in results if not r["appended"]]
    assert len(appended) == 1  # two writers can never BOTH append
    assert all(r["attempted"] is True for r in results)
    assert all(
        r["reasons"] == [REFUSED_TRIAL_KEY_ALREADY_PRESENT] for r in refused
    )
    # The raw-primitive race leaves a clean single-row ledger: the frozen
    # read verifies uniqueness, schemas and append-only integrity.
    state = read_v12_ledger(ledger)
    assert state["count"] == 1
    assert state["rows"][0]["trial_key"] == "c" * 64
    assert v12_denominator_view(ledger) == {
        "published": 1, "observed": 0, "observed_total": 1, "rows": 1,
    }
