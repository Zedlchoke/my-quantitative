"""Pytest mirror of the STOCKS-NG6 M0 golden suite (plans/PLAN_stocks_ng6.md §3).

Re-inherited BYTE-EXACT from the NG5 M0 machinery
(research/control/stocks_ng6_run/m0/ — law and fixtures identical to
research/control/stocks_ng5_run/m0/).  This file only exposes each frozen
gate function as a pytest test; it adds NO gates, skips NO gates and
weakens NO assertions.  G1-G10 + G4N = 11 tests.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
M0_DIR = HERE.parent / "research" / "control" / "stocks_ng6_run" / "m0"

_spec = importlib.util.spec_from_file_location("ng6_m0_golden", M0_DIR / "test_m0_golden.py")
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)


def test_g1_same_family_detection():
    G.g1()


def test_g2_sign_inversion_same_mechanism():
    G.g2()


def test_g3_shared_payoff_trap_blind():
    G.g3()


def test_g4_no_payoff_argument_in_verdict():
    G.g4()


def test_g4n_negative_contaminated_verdict_fails():
    G.g4n()


def test_g5_primary_comparisons_fixtures():
    G.g5()


def test_g6_same_instant_clustering():
    G.g6()


def test_g7_price_only_controls_classed():
    G.g7()


def test_g8_frozen_contract_refuses_tampering():
    G.g8()


def test_g9_program_bar_immovable():
    G.g9()


def test_g10_wrong_kernel_caught():
    G.g10()
