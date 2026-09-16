"""FOREX-NG7 M0 golden suite — pytest surface (plans/PLAN_forex_ng7.md §3).

Verbatim re-inheritance of the shared D2-methodology law (G1-G10 + G4N =
11/11; NG5/NG6 lineage) plus the plan-mandated dual-books ordering fixture
(G11).  The gate bodies live verbatim in
research/control/forex_ng7_run/m0/test_m0_golden.py — the same module the
M0 verdict runner (run_m0.py) executes — so this pytest adapter duplicates
no gate logic: import-path + cycle-id adaptations only, no gate weakened
or added here.  Exit-0 of run_m0.py (m0_verdict.json == PASS) is the M0
gate artifact; this file is the per-gate pytest view of the same gates.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M0_DIR = ROOT / "research" / "control" / "forex_ng7_run" / "m0"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T = _load_module("forex_ng7_m0_golden_gates", M0_DIR / "test_m0_golden.py")


def test_g1_same_family_detection():
    T.g1()


def test_g2_sign_inversion_same_mechanism_different_direction():
    T.g2()


def test_g3_shared_payoff_trap_does_not_merge():
    T.g3()


def test_g4_no_outcome_argument_verdict_purity():
    T.g4()


def test_g4n_negative_payoff_contamination_fails_fixture():
    T.g4n()


def test_g5_primary_comparisons_hand_computed():
    T.g5()


def test_g6_same_instant_clustering():
    T.g6()


def test_g7_price_only_controls_classed_e_falsification():
    T.g7()


def test_g8_frozen_contract_refuses_tampering():
    T.g8()


def test_g9_program_bar_immovable():
    T.g9()


def test_g10_wrong_signal_x_return_kernel_caught():
    T.g10()


def test_g11_dual_books_ordering_inversion_rejected_before_merge():
    T.g11()
