"""CRYPTO-NG4 M0: pytest wrapper for the shared D2-methodology golden suite.

Plan authority: plans/PLAN_crypto_ng4.md §3 — the shared D2-methodology
golden suite (G1–G10 + G4N = 11/11; NG5 lineage) is re-inherited BYTE-EXACT
into research/control/crypto_ng4_run/m0/ and re-run in THIS cycle's
worktree.  This wrapper runs each gate under pytest and pins the byte-exact
re-inheritance: any edit to the law (m0_contract.py) or to the frozen
contract fails here before D1.

Run:  .venv/bin/python -m pytest tests/test_crypto_ng4_m0_golden.py -q
Synthetic data only — no market data.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parent
M0_DIR = WORKTREE / "research" / "control" / "crypto_ng4_run" / "m0"

# Byte-exact re-inheritance pins (sha256 measured on the stocks-ng5 lineage
# m0 dir — the NG5-law 11-gate version the plan §3 names):
#   m0_contract.py      2e744579c81869d0dcc90499bdaecef5cefbcfb284282f3ef6caf1d4a9aa0d91
#   contract_frozen.json 8b5ee44bf61566b879c5d656992a1789dd8161642ebac655e824002c0ceef91f
NG5_LINEAGE_SHA = {
    "m0_contract.py": "2e744579c81869d0dcc90499bdaecef5cefbcfb284282f3ef6caf1d4a9aa0d91",
    "contract_frozen.json": "8b5ee44bf61566b879c5d656992a1789dd8161642ebac655e824002c0ceef91f",
}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load("cng4_m0_contract", M0_DIR / "m0_contract.py")
G = _load("cng4_m0_golden", M0_DIR / "test_m0_golden.py")


def test_byte_exact_reinheritance_of_the_ng5_law():
    """The law and the frozen contract are BYTE-EXACT the NG5 lineage
    (plan §3: 're-inherited BYTE-EXACT').  Any silent edit — e.g. a
    weakened gate, a lowered bar, a changed sign bar — fails here."""
    for fname, expected_sha in NG5_LINEAGE_SHA.items():
        blob = (M0_DIR / fname).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == expected_sha, fname


@pytest.mark.parametrize(
    "gid,fn_name",
    [
        ("G1", "g1"),
        ("G2", "g2"),
        ("G3", "g3"),
        ("G4", "g4"),
        ("G4N", "g4n"),
        ("G5", "g5"),
        ("G6", "g6"),
        ("G7", "g7"),
        ("G8", "g8"),
        ("G9", "g9"),
        ("G10", "g10"),
    ],
)
def test_shared_golden_gate(gid, fn_name):
    """Each of the 11 shared gates, run in this cycle's worktree."""
    assert not hasattr(G, "g11")  # no gate may be silently added either
    getattr(G, fn_name)()  # the gate IS the test; a raise is a FAIL


def test_golden_suite_runs_11_of_11_pass():
    """The in-directory suite self-reports M0 PASS with EXACTLY the
    NG5-lineage gate set G1..G10 + G4N — no gate dropped, none added."""
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = G.main()
    assert rc == 0, buf.getvalue()
    ids = [gid for gid, _, verdict, _ in G.RESULTS]
    assert ids == ["G1", "G2", "G3", "G4", "G4N", "G5", "G6", "G7", "G8", "G9", "G10"], ids
    assert all(verdict == "PASS" for _, _, verdict, _ in G.RESULTS)
    assert "M0 PASS (11 gates)" in buf.getvalue()


def test_m0_verdict_artifact_pass_and_cycle_identity():
    verdict = json.loads((M0_DIR / "m0_verdict.json").read_text())
    assert verdict["schema"] == "m0_verdict@1"
    assert verdict["cycle_id"] == "CRYPTO-NG4"
    assert verdict["gate"] == "M0 (plans/PLAN_crypto_ng4.md §3)"
    assert verdict["verdict"] == "PASS"
    assert verdict["golden_suite_exit_code"] == 0
    assert verdict["contract"] == dict(M.CONTRACT_FIELDS)
    passed = [line for line in verdict["golden_suite_output"] if line.startswith("PASS")]
    assert len(passed) == 11
    assert "M0 PASS (11 gates)" in verdict["golden_suite_output"]


def test_frozen_contract_refuses_wrong_hash_live():
    """G8 live against the committed contract blob (not a temp copy)."""
    blob = (M0_DIR / "contract_frozen.json").read_bytes()
    good_sha = hashlib.sha256(blob).hexdigest()
    assert M.load_contract(M0_DIR / "contract_frozen.json", good_sha) == dict(M.CONTRACT_FIELDS)
    with pytest.raises(M.ContractRefused):
        M.load_contract(M0_DIR / "contract_frozen.json", "0" * 64)
