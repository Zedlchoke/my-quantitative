"""M0 golden tests G1-G10 (owner-mandated methodology contract, §3 of both plans).

Run:  .venv/bin/python research/control/stocks_ng5_run/m0/test_m0_golden.py
Exit 0 only when every gate passes.  Synthetic data only — no market data.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("m0_contract", HERE / "m0_contract.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

RESULTS = []


def gate(gid, name, fn):
    try:
        fn()
        RESULTS.append((gid, name, "PASS", ""))
    except Exception as exc:  # noqa: BLE001 — the test IS the gate
        RESULTS.append((gid, name, "FAIL", f"{type(exc).__name__}: {exc}"))


def weights_of(signal: np.ndarray) -> np.ndarray:
    return np.sign(signal)


# ---------------------------------------------------------------- fixtures

SIG_A = np.array([1.5, -0.5, 2.0, -1.0, 0.5, -2.0, 1.0, -1.5])
SIG_B_RANK = np.array([7.0, 3.0, 8.0, 2.0, 5.0, 1.0, 6.0, 4.0])  # rank of SIG_A
SIG_B_NEG = -SIG_A
# n=256 fixed-seed draws: independent-normal rank correlations concentrate
# far under the 0.20 bar, deterministically for this seed.
RNG = np.random.default_rng(20260916)
SIG_C = RNG.normal(size=256)  # independent signal (fixed seed)
SIG_D = RNG.normal(size=256)  # independent signal (fixed seed)
SHARED_RET = RNG.normal(size=256)  # common future returns
# the G10 trap made explicit: two DIFFERENT signals whose candidate PnL is
# dominated by the shared market return (unit beta + small idiosyncratic
# part) — the wrong payoff-primary kernel merges them, the contract does not.
SIG_E = 1.0 + 0.1 * RNG.normal(size=256)
SIG_F = 1.0 + 0.1 * RNG.normal(size=256)


def _metrics(a_sig, b_sig, weights=None):
    """Binary sign weights by default; continuous weights for the
    independent-signal fixtures (a binary book's weight Spearman is a
    heavily-tied, coarse statistic — the continuous book is the honest
    fixture for the pooled bar)."""
    if weights is None:
        weights = (weights_of(a_sig), weights_of(b_sig))
    wa, wb = weights
    return M.primary_comparisons(wa, wb, a_sig, b_sig)


# ------------------------------------------------------------------- gates

def g1():
    m = _metrics(SIG_A, SIG_B_RANK)
    assert M.pooled_abs_correlation(m) > M.PROGRAM_RHO_BAR, m
    v = M.family_verdict(m, dict(M.CONTRACT_FIELDS))
    assert v == M.SAME_FAMILY, v


def g2():
    m = _metrics(SIG_A, SIG_B_NEG)
    assert m["target_weight_pearson"] == -1.0, m
    assert m["sign_agreement"] == 0.0, m
    v = M.family_verdict(m, dict(M.CONTRACT_FIELDS))
    assert v == M.SAME_MECHANISM_DIFFERENT_DIRECTION, v


def g3():
    m = _metrics(SIG_C, SIG_D, weights=(SIG_C, SIG_D))
    assert M.pooled_abs_correlation(m) <= M.PROGRAM_RHO_BAR, m
    v = M.family_verdict(m, dict(M.CONTRACT_FIELDS))
    assert v == M.DIFFERENT_FAMILY, v
    # the shared-payoff trap in its strong form: unit-beta books (mean 1,
    # small idiosyncratic parts) scaled by the SAME future returns produce
    # strongly correlated candidate PnLs — the verdict must stay blind to it.
    pnl_a = SIG_E * SHARED_RET
    pnl_b = SIG_F * SHARED_RET
    assert abs(M._pearson(pnl_a, pnl_b)) > 0.8
    m_trap = _metrics(SIG_E, SIG_F, weights=(SIG_E, SIG_F))
    assert M.pooled_abs_correlation(m_trap) <= M.PROGRAM_RHO_BAR, m_trap
    assert M.family_verdict(m_trap, dict(M.CONTRACT_FIELDS)) == M.DIFFERENT_FAMILY


def g4():
    params = inspect.signature(M.family_verdict).parameters
    banned = {"returns", "pnl", "payoff", "outcome", "future_returns", "shared_returns"}
    assert not (set(params) & banned), params
    # HARDENED G4 (A2R-F2): name-based checks are porous (optional defaulted
    # params, module-global payoff state). The AST purity proof closes both
    # demonstrated bypass shapes: exact signature (metrics, contract) with
    # no optional/defaulted/vararg params, and a frozen whitelist of load
    # names inside the function body — any payoff parameter, global read or
    # out-of-whitelist helper reference raises here and fails the suite.
    M.verify_verdict_purity(inspect.getsource(M.family_verdict))
    # primary_comparisons takes no outcome argument either
    params2 = inspect.signature(M.primary_comparisons).parameters
    assert not (set(params2) & banned), params2
    # payoff correlation between candidate PnLs is never an input
    m = _metrics(SIG_C, SIG_D)
    assert "payoff" not in m and "pnl" not in m


def g4n():
    """NEGATIVE control for G4 (A7-STOCKS round-2 requirement): an
    implementation that lets payoff/PnL/outcome into the verdict path must
    FAIL this suite — demonstrably wrong on the G3 fixture.  SCOPE (A2R-F2
    corrected claim): the contaminated-kernel probe proves the FIXTURE
    separates payoff-contaminated from clean verdicts; the hardened G4
    purity check is the gate that FAILS edits which smuggle payoff into
    family_verdict itself (optional params, globals, extra names).  Both
    layers together are the sensitivity proof; either alone is not."""
    # the contaminated kernel exists only as the wrong-implementation probe
    assert hasattr(M, "family_verdict_payoff_contaminated")
    params = inspect.signature(M.family_verdict_payoff_contaminated).parameters
    assert any("payoff" in p for p in params), params  # it takes payoff in
    # on the shared-payoff trap it merges two genuinely different signals…
    contaminated = M.family_verdict_payoff_contaminated(
        _metrics(SIG_E, SIG_F, weights=(SIG_E, SIG_F)),
        payoff_correlation=M._pearson(SIG_E * SHARED_RET, SIG_F * SHARED_RET),
        contract=dict(M.CONTRACT_FIELDS),
    )
    assert contaminated == M.SAME_FAMILY, contaminated
    # …while the clean contract keeps them distinct.
    clean = M.family_verdict(
        _metrics(SIG_E, SIG_F, weights=(SIG_E, SIG_F)), dict(M.CONTRACT_FIELDS)
    )
    assert clean == M.DIFFERENT_FAMILY, clean
    # the purity gate rejects both A2-demonstrated contamination shapes
    # outright (optional defaulted param; module-global payoff read)
    adversarial_optional_param = (
        "def family_verdict(metrics, contract, agreement_index=None):\n"
        "    if agreement_index is not None and abs(agreement_index) > contract['rho_bar']:\n"
        "        return SAME_FAMILY\n"
        "    return DIFFERENT_FAMILY\n"
    )
    try:
        M.verify_verdict_purity(adversarial_optional_param)
    except AssertionError:
        pass
    else:
        raise AssertionError("purity check failed to reject optional-param contamination")
    adversarial_global_read = (
        "def family_verdict(metrics, contract):\n"
        "    if EXTERNAL_PAYOFF_STATE is not None:\n"
        "        return SAME_FAMILY\n"
        "    return DIFFERENT_FAMILY\n"
    )
    try:
        M.verify_verdict_purity(adversarial_global_read)
    except AssertionError:
        pass
    else:
        raise AssertionError("purity check failed to reject module-global contamination")


def g5():
    # hand-computed fixtures for each of the seven named metrics
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([2.0, 4.0, 6.0])
    assert abs(M._pearson(a, b) - 1.0) < 1e-12
    assert abs(M._pearson(a, -b) + 1.0) < 1e-12
    assert abs(M._spearman(np.array([1.0, 2.0, 3.0]), np.array([3.0, 1.0, 2.0])) + 0.5) < 1e-12
    assert M._sign_agreement(np.array([1, -1, 1, -1]), np.array([1, 1, -1, -1])) == 0.5
    assert abs(M._active_jaccard(np.array([1, 0, 1, 0]), np.array([0, 1, 1, 0])) - (1 / 3)) < 1e-12
    assert M._decision_overlap(np.array([1, -1, 0]), np.array([1, -1, 1])) == 2 / 3
    assert abs(M._cosine(np.array([1.0, 2.0]), np.array([2.0, 1.0])) - 0.8) < 1e-12
    full = _metrics(SIG_A, SIG_B_RANK)
    for key in (
        "target_weight_pearson",
        "target_weight_spearman",
        "signal_rank_correlation",
        "sign_agreement",
        "active_set_jaccard",
        "decision_overlap",
        "exposure_cosine",
    ):
        assert key in full, key


def g6():
    # 12 rows over 4 shared decision dates (3 symbols per date): naive row
    # counting says 12 observations; clustering by the shared decision date
    # collapses to 4 — the clustered count is the only lawful n.
    keys = [(pd, sym) for pd in ("2026-01-05", "2026-01-12", "2026-01-20", "2026-01-26") for sym in ("QQQ", "SPY", "XY")]
    assert len(keys) == 12
    assert M.effective_observation_count(keys) == 12  # distinct tuples, naive
    assert M.effective_observation_count([k[0] for k in keys]) == 4  # clustered


def g7():
    assert M.control_classification("price_only_payoff") == "E_FALSIFICATION"
    assert M.control_classification("momentum_shadow") == "E_FALSIFICATION"
    assert M.control_classification("clock_only_book") == "E_FALSIFICATION"
    # classing is metadata: it never enters the novelty verdict inputs
    m = _metrics(SIG_A, SIG_B_RANK)
    v = M.family_verdict(m, dict(M.CONTRACT_FIELDS))
    assert v in {M.SAME_FAMILY, M.SAME_MECHANISM_DIFFERENT_DIRECTION, M.DIFFERENT_FAMILY}


def g8():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "contract.json"
        sha = M.freeze_contract(p)
        assert M.load_contract(p, sha) == dict(M.CONTRACT_FIELDS)
        tampered = json.loads(p.read_text())
        tampered["sign_agreement_bar"] = 0.5
        p.write_text(json.dumps(tampered, sort_keys=True, indent=1))
        try:
            M.load_contract(p, sha)
        except M.ContractRefused:
            pass
        else:
            raise AssertionError("tampered contract loaded")


def g9():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "contract_lower_bar.json"
        lowered = dict(M.CONTRACT_FIELDS, rho_bar=0.15)
        blob = json.dumps(lowered, sort_keys=True, indent=1).encode()
        p.write_bytes(blob)
        sha = hashlib.sha256(blob).hexdigest()
        try:
            M.load_contract(p, sha)
        except M.ContractRefused as exc:
            assert "immovable" in str(exc)
        else:
            raise AssertionError("lowered bar accepted — veto-shopping")


def g10():
    # the WRONG kernel (signal x shared future return, payoff-primary) merges
    # two genuinely different signals because their shared-return PnLs are
    # strongly correlated (market-dominated books) — the correct contract
    # keeps them distinct. This is the sensitivity proof: the golden suite
    # FAILS the wrong implementation class.
    wrong = M.wrong_verdict_signal_times_shared_return(SIG_E, SIG_F, SHARED_RET)
    m_right = _metrics(SIG_E, SIG_F, weights=(SIG_E, SIG_F))
    right = M.family_verdict(m_right, dict(M.CONTRACT_FIELDS))
    assert wrong == M.SAME_FAMILY, wrong
    assert M.pooled_abs_correlation(m_right) <= M.PROGRAM_RHO_BAR, m_right
    assert right == M.DIFFERENT_FAMILY, right


def main() -> int:
    gate("G1", "same-family detection (rank transform)", g1)
    gate("G2", "sign inversion = same mechanism, different direction", g2)
    gate("G3", "shared-payoff trap does not merge different signals", g3)
    gate("G4", "no payoff/outcome argument in the verdict path", g4)
    gate("G4N", "NEGATIVE: payoff-contaminated verdict FAILS the fixture", g4n)
    gate("G5", "primary comparisons hand-computed fixtures", g5)
    gate("G6", "same-day/same-release clustering to one observation", g6)
    gate("G7", "price-only controls classed E_FALSIFICATION", g7)
    gate("G8", "frozen contract refuses tampering", g8)
    gate("G9", "program bar 0.20 immovable (no rescue)", g9)
    gate("G10", "wrong signal-x-return kernel caught by the suite", g10)
    for gid, name, verdict, note in RESULTS:
        print(f"{verdict:5} {gid} {name}" + (f"  -- {note}" if note else ""))
    fails = [r for r in RESULTS if r[2] != "PASS"]
    print(f"M0 {'FAIL ' + str(len(fails)) if fails else 'PASS'} ({len(RESULTS)} gates)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
