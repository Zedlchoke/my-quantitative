"""M0 runner: executes the golden suite, freezes the contract, writes the
M0 verdict artifact.  Exit 0 == M0 PASS (gate before D1).

Run:  .venv/bin/python research/control/forex_ng6_run/m0/run_m0.py
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


def main() -> int:
    contract_sha = M.freeze_contract(CONTRACT_PATH)
    contract = M.load_contract(CONTRACT_PATH, contract_sha)  # G8+G9 live check
    test_file = HERE / "test_m0_golden.py"
    proc = subprocess.run(
        [sys.executable, str(test_file)], capture_output=True, text=True
    )
    module_sha = hashlib.sha256((HERE / "m0_contract.py").read_bytes()).hexdigest()
    test_sha = hashlib.sha256(test_file.read_bytes()).hexdigest()
    verdict = {
        "schema": "m0_verdict@1",
        "cycle_id": "FOREX-NG6",
        "gate": "M0 (plans/PLAN_forex_ng6.md §3)",
        "contract": dict(M.CONTRACT_FIELDS),
        "contract_sha256": contract_sha,
        "m0_contract_sha256": module_sha,
        "golden_suite_sha256": test_sha,
        "golden_suite_exit_code": proc.returncode,
        "golden_suite_output": proc.stdout.strip().splitlines(),
        "verdict": "PASS" if proc.returncode == 0 else "FAIL",
        "law": "M0 FAIL => BLOCKED_METHOD_CONTRACT, D1 never opens, budget stays 0/3",
    }
    VERDICT_PATH.write_text(json.dumps(verdict, indent=1, sort_keys=True) + "\n")
    print(proc.stdout.strip())
    print(f"contract_sha256={contract_sha}")
    print(f"verdict artifact: {VERDICT_PATH}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
