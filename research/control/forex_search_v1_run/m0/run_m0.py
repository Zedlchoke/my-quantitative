"""M0 runner (FOREX-SEARCH-V1): executes the inherited golden suite
BYTE-EXACT, then the plan-§9-required extension, and writes the M0 verdict
artifact.  Exit 0 == M0 PASS (gate before D1).

Plan §9 M0 row (plans/PLAN_forex_search_v1.md): "methodology golden suite
(G1-G10 + G4N = 11/11, NG5/NG6/NG7 lineage) re-inherited BYTE-EXACT + the
dual-books degenerate fixture (the uniform-charge financed book must not
invert sign vs price-only on any fixture arm) — re-run under
research/control/forex_search_v1_run/m0/; PASS required before D1".

Mapping (F-3 remediation, A7 a7_prelaunch_forex_search_v1.json):
  * G1-G10  -> test_m0_golden.py (inherited core, BYTE-EXACT: file digests
               verified against the pre-remediation frozen values)
  * G4N     -> test_m0_extension.py (verdict-purity negative control)
  * fixture -> test_m0_extension.py (dual-books degenerate fixture)

Run:  .venv/bin/python research/control/forex_search_v1_run/m0/run_m0.py
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("m0_contract", HERE / "m0_contract.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

CONTRACT_PATH = HERE / "contract_frozen.json"
VERDICT_PATH = HERE / "m0_verdict.json"

# The inherited core's frozen digests, as recorded by the predecessor cycle's
# M0 verdict (FOREX-NG6, pre-remediation m0_verdict.json @ commit 256efe12,
# cited by audits/a7_prelaunch_forex_search_v1.json "m0" row). Byte-exact
# inheritance means THESE digests still hold on the current files.
INHERITED_CONTRACT_SHA256 = (
    "dad5de33316c01486deea57d1f97a26bb9dc8a0d61fe975f885edf378be327eb")
INHERITED_GOLDEN_SHA256 = (
    "ba3991bd170b3720494a4c738d60fcb434d79d2cd5896970d9f83e98fb2c1624")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_suite(test_file: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(test_file)], capture_output=True, text=True
    )


def main() -> int:
    contract_sha = M.freeze_contract(CONTRACT_PATH)
    contract = M.load_contract(CONTRACT_PATH, contract_sha)  # G8+G9 live check
    golden_file = HERE / "test_m0_golden.py"
    ext_file = HERE / "test_m0_extension.py"
    module_sha = sha256_file(HERE / "m0_contract.py")
    golden_sha = sha256_file(golden_file)
    ext_sha = sha256_file(ext_file)
    proc = run_suite(golden_file)
    proc_ext = run_suite(ext_file)
    byte_exact = (module_sha == INHERITED_CONTRACT_SHA256 and
                  golden_sha == INHERITED_GOLDEN_SHA256)
    core_ok = proc.returncode == 0
    ext_ok = proc_ext.returncode == 0
    verdict = {
        "schema": "m0_verdict@1",
        "cycle_id": "FOREX-SEARCH-V1",
        "gate": "M0 (plans/PLAN_forex_search_v1.md §9)",
        "inherited_from": (
            "FOREX-NG6 / FOREX-NG5 lineage (plans/PLAN_forex_ng6.md §3); "
            "the golden core is re-inherited BYTE-EXACT — the file digests "
            "below equal the predecessor cycle's frozen values, and the "
            "plan-required extension (G4N + dual-books degenerate fixture) "
            "is APPENDED in a separate file (test_m0_extension.py) without "
            "touching any inherited byte"),
        "inherited_core_byte_exact": {
            "byte_exact": byte_exact,
            "m0_contract_sha256": module_sha,
            "m0_contract_sha256_expected": INHERITED_CONTRACT_SHA256,
            "test_m0_golden_sha256": golden_sha,
            "test_m0_golden_sha256_expected": INHERITED_GOLDEN_SHA256,
        },
        "contract": dict(M.CONTRACT_FIELDS),
        "contract_sha256": contract_sha,
        "m0_contract_sha256_frozen_field": module_sha,
        "golden_suite_sha256": golden_sha,
        "golden_suite_exit_code": proc.returncode,
        "golden_suite_output": proc.stdout.strip().splitlines(),
        "extension": {
            "file": "research/control/forex_search_v1_run/m0/"
                    "test_m0_extension.py",
            "sha256": ext_sha,
            "exit_code": proc_ext.returncode,
            "output": proc_ext.stdout.strip().splitlines(),
            "content": ("G4N (verdict-purity negative control: no "
                        "payoff-correlation primary normalization; "
                        "shared-instrument normalization identity) + the "
                        "dual-books degenerate fixture (hand-computed "
                        "uniform-charge arms; financed book never inverts "
                        "sign, differs from the price book, inversion and "
                        "pnl-adding charges flagged)"),
        },
        "plan_required_total": (
            "G1-G10 + G4N = 11/11 + dual-books degenerate fixture "
            "(plans/PLAN_forex_search_v1.md §9 M0)"),
        "verdict": "PASS" if (core_ok and ext_ok and byte_exact) else "FAIL",
        "law": "M0 FAIL => BLOCKED_METHOD_CONTRACT, D1 never opens, budget "
               "stays 0/3",
    }
    VERDICT_PATH.write_text(json.dumps(verdict, indent=1, sort_keys=True) + "\n")
    print(proc.stdout.strip())
    print(proc_ext.stdout.strip())
    print(f"contract_sha256={contract_sha}")
    print(f"inherited core byte-exact: {byte_exact}")
    print(f"verdict artifact: {VERDICT_PATH}")
    return 0 if (core_ok and ext_ok and byte_exact) else 1


if __name__ == "__main__":
    sys.exit(main())
