"""V5 reason-semantics fixtures (PLAN 31.2 items 6-8 / F08, owner A3).

Absent evidence must emit ``not_tested`` -- NEVER ``<name>_negative``.
Only an EXECUTED-and-negative stress earns its negative reason code.
"""

from __future__ import annotations

import pytest

from contracts.protocol import REASON_CODES, GateVerdict
from research.protocol.gates import (
    METRIC_MISSING,
    NOT_TESTED,
    STRESS_NEGATIVE,
    ReasonSemantics,
    SurvivorInput,
    XGateInputs,
    XRobustnessInput,
    evaluate_gates,
    evaluate_xg4,
    evaluate_xgates,
)
from research.protocol.gates import GateInputs  # re-exported for symmetry


STRESS_NEGATIVE_CODES = (
    "fee_stress_negative",
    "slippage_stress_negative",
    "delay_stress_negative",
)


# --------------------------- helper contracts ------------------------------- #
def test_reason_semantics_values_are_frozen():
    assert ReasonSemantics.NOT_TESTED.value == "not_tested"
    assert ReasonSemantics.METRIC_MISSING.value == "metric_missing"
    assert NOT_TESTED == "not_tested" and METRIC_MISSING == "metric_missing"


def test_stress_negative_reason_builder():
    assert STRESS_NEGATIVE("fee_stress") == "fee_stress_negative"
    assert ReasonSemantics.stress_negative("delay_stress") == "delay_stress_negative"
    with pytest.raises(ValueError):
        STRESS_NEGATIVE("   ")


def test_v5_reason_codes_registered():
    for code in ("not_tested", "metric_missing", "evidence_missing",
                 "not_applicable_with_reason", "median_fold_return_nonpositive"):
        assert code in REASON_CODES


# ------------------------------ G4 (legacy row) ----------------------------- #
def test_g4_absent_fee_and_delay_stress_emit_not_tested_never_negative():
    result = evaluate_gates(GateInputs(survivor=SurvivorInput()))[5]
    assert result.verdict in (
        GateVerdict.NOT_IMPLEMENTED, GateVerdict.INCONCLUSIVE
    )
    assert NOT_TESTED in result.reasons
    for code in STRESS_NEGATIVE_CODES:
        assert code not in result.reasons


def test_g4_delay_unsupported_absence_is_not_tested_not_negative():
    survivor = SurvivorInput(
        fee_stress_positive=True,
        delay_stress_positive=None,       # never executed
        delay_stress_supported=True,      # support exists -> absence is explicit
        neighborhood_spike_detected=False,
        dropone_signflip_detected=False,
    )
    result = evaluate_gates(GateInputs(survivor=survivor))[5]
    assert result.verdict is GateVerdict.NOT_IMPLEMENTED
    assert NOT_TESTED in result.reasons
    assert "delay_stress_negative" not in result.reasons


def test_g4_executed_negative_stress_keeps_negative_code():
    survivor = SurvivorInput(
        fee_stress_positive=False,        # EXECUTED and negative
        delay_stress_positive=True,
        delay_stress_supported=True,
        neighborhood_spike_detected=False,
        dropone_signflip_detected=False,
    )
    result = evaluate_gates(GateInputs(survivor=survivor))[5]
    assert result.verdict is GateVerdict.FAIL
    assert "fee_stress_negative" in result.reasons
    assert NOT_TESTED not in result.reasons


# ------------------------------ XG4 ------------------------------------------ #
def _robust(**overrides):
    base = dict(
        fee50_exp_r=0.02,
        twotick_exp_r=0.01,
        extradelay_exp_r=0.01,
        dropone_symbol_clean=True,
        dropone_fold_clean=True,
        turnover_budget_exceeded=False,
    )
    base.update(overrides)
    return XRobustnessInput(**base)


def test_xg4_all_stresses_absent_emits_not_tested_only():
    result = evaluate_xg4(XRobustnessInput())
    assert result.verdict is GateVerdict.INCONCLUSIVE
    # reasons are de-duplicated; one not_tested stands for every absent check
    assert NOT_TESTED in result.reasons
    for code in STRESS_NEGATIVE_CODES:
        assert code not in result.reasons


def test_xg4_mixed_executed_and_absent_stresses_split_semantics():
    section = _robust(fee50_exp_r=-0.01)  # executed-negative; others absent
    result = evaluate_xg4(section)
    assert result.verdict is GateVerdict.FAIL
    assert "fee_stress_negative" in result.reasons
    assert NOT_TESTED in result.reasons  # the two unexecuted stresses
    assert "slippage_stress_negative" not in result.reasons
    assert "delay_stress_negative" not in result.reasons


def test_xg4_executed_negative_via_evaluate_xgates_row():
    rows = evaluate_xgates(XGateInputs(robustness=_robust(twotick_exp_r=0.0)))
    xg4 = rows[5]
    assert xg4.verdict is GateVerdict.FAIL
    assert "slippage_stress_negative" in xg4.reasons


def test_xg4_dropone_absence_keeps_its_own_pending_code():
    # drop-one checks are detection checks, not cost stresses: their absence
    # stays "dropone_signflip"-pending and is NOT renamed to not_tested.
    section = _robust(dropone_symbol_clean=None, dropone_fold_clean=None)
    result = evaluate_xg4(section)
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert "dropone_signflip" in result.reasons