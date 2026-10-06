"""Reproduce the two finalization false-success bugs through the REAL
scored_executor.run_scored_execution over the synthetic sandbox (faults
injected at the boundary like the independent audit did; no real
lock/ledger/GO/panel touched)."""
import json, sys, tempfile
from pathlib import Path
from unittest import mock
RUNNER_DIR = Path.cwd()
sys.path.insert(0, str(RUNNER_DIR))
SB = RUNNER_DIR / "scratch/synthetic/sandbox"
sys.path.insert(0, str(RUNNER_DIR))
import test_execution_path as T
import scored_executor as SE

def base_cfg(td, tag):
    return {
        "cycle_id": T.CYCLE_ID, "sandbox_root": str(SB),
        "worktree": T.WORKTREE, "contract_path": T.CONTRACT_IN_SB,
        "builder_path": str(SB / "research/control/FUTURES-ES-PB1-V1/final/dryrun_builder_v3.py"),
        "builder_pin_sha": "5a08c9fd8a94948cc61762933f77e5fe7db660ade43e1f2d140d2c628e164906", "builder_overrides": None,
        "identity_ids": T.identity_ids(),
        "ledger_path": f"{td}/{tag}_ledger.jsonl",
        "lock_runtime_dir": str(SB / "heavy_runtime"),
        "run_root": f"{td}/{tag}_run",
        "command": [tag], "fault": None,
        "reverify_authority": lambda: [],
    }

out = {}
# BUG 1: handle.release() raises after a full successful computation
with tempfile.TemporaryDirectory() as td:
    cfg = base_cfg(td, "b1")
    import governance.heavy_lock as HL
    with mock.patch.object(HL, "acquire") as acq:
        h = mock.MagicMock()
        h.release.side_effect = RuntimeError("INJECTED release failure")
        acq.return_value = h
        rc, term = SE.run_scored_execution(cfg)
    out["BUG1_release_raises"] = {
        "exit_code": rc,
        "terminal_state": term.get("terminal_state"),
        "lock_released_status": term.get("lock_released_status"),
        "lock_release_error": term.get("lock_release_error"),
        "handoff_claimed": "terminal_handoff_path" in term,
        "verdict_success_reported": (rc == 0 and term.get("terminal_state") == "EXECUTION_COMPLETE"),
    }
# BUG 2: terminal_handoff.json write raises OSError
with tempfile.TemporaryDirectory() as td:
    cfg = base_cfg(td, "b2")
    real = SE._write_atomic
    def boom(p, d):
        if "terminal_handoff" in str(p): raise OSError("INJECTED handoff write failure")
        return real(p, d)
    with mock.patch.object(SE, "_write_atomic", boom):
        rc, term = SE.run_scored_execution(cfg)
    out["BUG2_handoff_raises"] = {
        "exit_code": rc,
        "terminal_state": term.get("terminal_state"),
        "terminal_handoff_error": term.get("terminal_handoff_error"),
        "handoff_path_claimed": "terminal_handoff_path" in term,
        "verdict_success_reported": (rc == 0 and term.get("terminal_state") == "EXECUTION_COMPLETE"),
    }
print(json.dumps(out, indent=1))
