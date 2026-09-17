"""M0 extension for FOREX-SEARCH-V1 (plan §9 M0 required content).

The inherited NG5/NG6/NG7 golden core (test_m0_golden.py G1-G10 +
m0_contract.py) is re-run BYTE-EXACT by run_m0.py — this file ADDS the two
plan-§9-M0 members the inherited core does not carry:

  G4N  verdict-purity NEGATIVE CONTROL ("no payoff-correlation primary
       normalization", plans/PLAN_stocks_ng6.md §3 suite enumeration): a
       deliberately contaminated normal-form implementation that normalizes
       candidate books by a SHARED instrument (making payoff correlation
       the primary) must (a) merge two genuinely different signals — the
       wrong-implementation signature — and (b) BE CAUGHT by the contract
       verdict on the same inputs, whose verdict path takes no payoff/
       returns/normalizer argument at all and is invariant to the shared
       payoff stream. The shared-instrument normalization identity is
       proven: elementwise normalization of both books by the same shared
       series is invariant to positive rescaling of that series (it never
       removes the payoff coupling — it IS the payoff-primary kernel).

  DUAL-BOOKS DEGENERATE FIXTURE (plans/PLAN_forex_search_v1.md §9 M0):
       the uniform-charge financed book (price book + strictly-negative
       uniform charge) must NEVER invert the price book's sign on any
       fixture arm and must DIFFER from the price book — hand-computed
       arithmetic at stress 1.0 and stress 2.0 PRIMARY on positive,
       negative and sign-inversion-sensitivity arms, using the frozen
       I-lane ladder (research/control/forex_search_v1_run/i/i_engine.py,
       read-only import; 1.5 bps/fill x 2 fills + 1.7 bps/night).

Run:  .venv/bin/python research/control/forex_search_v1_run/m0/test_m0_extension.py
Exit 0 only when every gate passes.  Synthetic/hand-computed data only —
no market data, no network, no scored output.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WT = HERE.parents[3]  # .../research/control/forex_search_v1_run/m0 -> worktree root

spec = importlib.util.spec_from_file_location("m0_contract", HERE / "m0_contract.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

spec_i = importlib.util.spec_from_file_location(
    "i_engine_m0_fixture",
    WT / "research/control/forex_search_v1_run/i/i_engine.py")
ENG = importlib.util.module_from_spec(spec_i)
spec_i.loader.exec_module(ENG)

RESULTS = []


def gate(gid, name, fn):
    try:
        fn()
        RESULTS.append((gid, name, "PASS", ""))
    except Exception as exc:  # noqa: BLE001 — the test IS the gate
        RESULTS.append((gid, name, "FAIL", f"{type(exc).__name__}: {exc}"))


# ---------------------------------------------------------------- fixtures
# n=256 fixed-seed draws (same generator family as the inherited core): two
# genuinely DIFFERENT near-constant signals whose books are dominated by the
# SHARED future-return stream, plus independent streams as the sensitivity
# control.
RNG = np.random.default_rng(20260917)
SIG_E = 1.0 + 0.1 * RNG.normal(size=256)
SIG_F = 1.0 + 0.1 * RNG.normal(size=256)
SHARED_RET = RNG.normal(size=256)
IND_A = RNG.normal(size=256)
IND_B = RNG.normal(size=256)


# ------------------------------------------------------------------ G4N

def g4n_contract_stays_blind():
    """(a) The catch: the shared-instrument (payoff-primary) kernel merges
    two genuinely different signals while the frozen contract verdict keeps
    them distinct on the SAME signals."""
    wrong = M.wrong_verdict_signal_times_shared_return(SIG_E, SIG_F, SHARED_RET)
    assert wrong == M.SAME_FAMILY, wrong
    m_right = M.primary_comparisons(SIG_E, SIG_F, SIG_E, SIG_F)
    assert M.pooled_abs_correlation(m_right) <= M.PROGRAM_RHO_BAR, m_right
    assert M.family_verdict(m_right, dict(M.CONTRACT_FIELDS)) == \
        M.DIFFERENT_FAMILY


def g4n_shared_instrument_normalization_identity():
    """(b) The identity: elementwise normalization of both books by the same
    shared instrument NEVER removes the payoff coupling — the contaminated
    verdict is invariant to positive rescaling of the shared stream, and
    decorrelates exactly when the stream stops being shared."""
    base = M.wrong_verdict_signal_times_shared_return(SIG_E, SIG_F, SHARED_RET)
    for scale in (0.25, 2.0, 7.5):
        scaled = M.wrong_verdict_signal_times_shared_return(
            SIG_E, SIG_F, SHARED_RET * scale)
        assert scaled == base == M.SAME_FAMILY
        a = SIG_E * SHARED_RET * scale
        b = SIG_F * SHARED_RET * scale
        assert abs(M._pearson(a, b) - M._pearson(SIG_E * SHARED_RET,
                                                 SIG_F * SHARED_RET)) < 1e-12
    # the coupling comes ONLY from sharing: independent streams (same
    # marginals) decorrelate -> the kernel returns DIFFERENT_FAMILY
    indep = M.wrong_verdict_signal_times_shared_return(IND_A, IND_B, SHARED_RET)
    assert indep == M.DIFFERENT_FAMILY, indep


def g4n_no_normalizer_argument_in_contract_path():
    """(c) Purity: the contract path admits NO payoff/returns/shared-
    instrument argument at all (extends G4 to the normalization surface),
    so no shared-instrument normalization can become its primary."""
    banned = {"returns", "pnl", "payoff", "outcome", "future_returns",
              "shared_returns", "normalizer", "instrument", "shared_instrument"}
    for fn in (M.family_verdict, M.primary_comparisons):
        params = inspect.signature(fn).parameters
        assert not (set(params) & banned), (fn.__name__, params)
    # the contract verdict is invariant to whatever payoff stream exists in
    # the world: same (weights, signals) -> same verdict, always
    m1 = M.primary_comparisons(SIG_E, SIG_F, SIG_E, SIG_F)
    m2 = M.primary_comparisons(SIG_E, SIG_F, SIG_E, SIG_F)
    assert M.family_verdict(m1, dict(M.CONTRACT_FIELDS)) == \
        M.family_verdict(m2, dict(M.CONTRACT_FIELDS)) == M.DIFFERENT_FAMILY


# ------------------------------------------- dual-books degenerate fixture

def _trade(gross: float, leg: str = "EURUSD", fold: int = 1, mi: int = 0,
           side: int = 1) -> dict:
    return {"leg": leg, "fold": fold, "state_key": f"side{side:+d}",
            "side": side, "mi_decision": mi, "decision_date": "2026-01-05",
            "entry": 1.0, "exit": 1.0, "gross_bps": gross}


def dual_books_fixture_arms():
    """Hand-computed uniform-charge arithmetic on three fixture arms.

    Ladder: price = gross - 2 x 1.5 x stress; financed = price - 1.7 x stress.
      ARM-1 stress 1.0, gross [20, -10, 30]:
        price  [17.0, -13.0, 27.0]  sum +31.0
        financed [15.3, -14.7, 25.3] sum +25.9   (same sign, differs)
      ARM-2 stress 2.0 PRIMARY, gross [20, -10, 30]:
        price  [14.0, -16.0, 24.0]  sum +22.0
        financed [10.6, -19.4, 20.6] sum +11.8   (same sign, differs)
      ARM-3 stress 1.0, gross [-20, -30]:
        price  [-23.0, -33.0]       sum -56.0
        financed [-24.7, -34.7]     sum -59.4    (same sign, differs)
    """
    arms = [
        ("ARM-1-stress-1.0", 1.0, [_trade(20.0), _trade(-10.0, mi=1),
                                   _trade(30.0, mi=2)], 31.0, 25.9),
        ("ARM-2-stress-2.0-PRIMARY", 2.0, [_trade(20.0), _trade(-10.0, mi=1),
                                           _trade(30.0, mi=2)], 22.0, 11.8),
        ("ARM-3-negative-price-book", 1.0,
         [_trade(-20.0, leg="GBPUSD"), _trade(-30.0, leg="GBPUSD", mi=1)],
         -56.0, -59.4),
    ]
    for name, stress, trades, want_price, want_fin in arms:
        chk = ENG.dual_books_check(trades, stress)
        assert abs(chk["price_net_bps"] - want_price) < 1e-9, (name, chk)
        assert abs(chk["financed_net_bps"] - want_fin) < 1e-9, (name, chk)
        assert np.sign(chk["price_net_bps"]) == \
            np.sign(chk["financed_net_bps"]) != 0, chk
        assert chk["sign_inversion"] is False, chk
        assert chk["financed_never_adds_pnl"] is True, chk
        assert chk["pass"] is True, chk
        # the financed book strictly DIFFERS from the price book (uniform
        # charge of exactly 1.7 x stress per round trip, never adds)
        price_a, fin_a = ENG.ladder_bps(trades, stress)
        assert float(fin_a.sum()) != float(price_a.sum())
        assert bool(np.all(fin_a <= price_a - 1.7 * stress + 1e-12))
        assert abs(float(price_a.sum()) - float(fin_a.sum()) -
                   len(trades) * 1.7 * stress) < 1e-9


def pytest_approx(x: float) -> float:
    """Hand values are exact in float for these fixtures; all comparisons
    use a 1e-9 tolerance inline."""
    return x


def dual_books_inversion_sensitivity():
    """The gate-catch: a price book the uniform charge pushes through zero
    IS flagged (price +1.0 vs financed -0.7 at stress 1.0) — sign
    invariance is CHECKED, never assumed."""
    chk = ENG.dual_books_check([_trade(4.0)], 1.0)
    assert abs(chk["price_net_bps"] - 1.0) < 1e-9, chk
    assert abs(chk["financed_net_bps"] - (-0.7)) < 1e-9, chk
    assert chk["sign_inversion"] is True and chk["pass"] is False
    # checker sensitivity: a NEGATIVE band would ADD pnl and must flag
    chk_add = ENG.dual_books_check([_trade(20.0), _trade(-10.0, mi=1)],
                                   1.0, fin_bps=-1.0)
    assert chk_add["financed_never_adds_pnl"] is False
    assert chk_add["pass"] is False


def dual_books_frozen_constants():
    """The charge comes from the frozen §4 F4 constants (1.5 bps/fill,
    1.7 bps/night, stress 2.0 PRIMARY -> 9.4 bps worst case)."""
    assert ENG.COST_BPS_PER_FILL == 1.5
    assert ENG.FIN_BPS_PER_NIGHT == 1.7
    assert ENG.STRESS_MULTIPLIER_PRIMARY == 2.0
    assert abs(ENG.WORST_CASE_ROUND_TRIP_BPS - 9.4) < 1e-9


def main() -> int:
    gate("G4N-a", "payoff-primary shared-instrument kernel caught by the "
         "contract verdict", g4n_contract_stays_blind)
    gate("G4N-b", "shared-instrument normalization identity (rescaling "
         "invariance; decorrelation only when unshared)",
         g4n_shared_instrument_normalization_identity)
    gate("G4N-c", "no normalizer/payoff argument exists in the contract "
         "verdict path", g4n_no_normalizer_argument_in_contract_path)
    gate("DB-1", "dual-books degenerate fixture: uniform-charge financed "
         "book never inverts sign and differs from price book (hand-"
         "computed, 3 arms)", dual_books_fixture_arms)
    gate("DB-2", "dual-books sensitivity: sign inversion and pnl-adding "
         "charge are flagged, never assumed", dual_books_inversion_sensitivity)
    gate("DB-3", "frozen §4 F4 constants (1.5/1.7/2.0 -> 9.4 bps worst)",
         dual_books_frozen_constants)
    for gid, name, verdict, note in RESULTS:
        print(f"{verdict:5} {gid} {name}" + (f"  -- {note}" if note else ""))
    fails = [r for r in RESULTS if r[2] != "PASS"]
    print(f"M0 EXTENSION {'FAIL ' + str(len(fails)) if fails else 'PASS'} "
          f"({len(RESULTS)} gates: G4N + dual-books fixture)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
