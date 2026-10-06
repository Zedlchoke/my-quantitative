"""Verifier driver: run the SAME boundary-fault repro pattern as
fix2/repro_finalization_bugs.py against the PRE-FIX executor bytes
(git show c17ab2bf:...scored_executor.py). Only the import order differs
(pre-fix module imported first so sys.modules binds it)."""
import hashlib, json, sys, tempfile
from pathlib import Path
from unittest import mock
TMPD = Path(__file__).resolve().parent
RUNNER_DIR = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep/research/control/FUTURES-ES-PB1-V1/gate6/runner")
SB = RUNNER_DIR / "scratch/synthetic/sandbox"
sys.path.insert(0, str(TMPD))
import scored_executor as SE   # PRE-FIX bytes
print("MODULE_UNDER_TEST", SE.__file__, file=sys.stderr)
print("MODULE_SHA256", hashlib.sha256(Path(SE.__file__).read_bytes()).hexdigest(), file=sys.stderr)
sys.path.insert(0, str(RUNNER_DIR))
import test_execution_path as T
import governance.heavy_lock as HL

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

out = {"module_sha256": hashlib.sha256(Path(SE.__file__).read_bytes()).hexdigest()}
with tempfile.TemporaryDirectory() as td:
    cfg = base_cfg(td, "b1")
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
