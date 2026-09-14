"""ZCODE-ORCHESTRATION-V3 P4: hook subprocess fixture tests (gate Z3-G4).

Every hook is executed exactly as ZCode would: a subprocess receiving one
JSON line on stdin. State is a fixture runtime dir via QUANT_REPO_ROOT /
ZCODE_ORCH_RUNTIME_DIR; nothing outside tmp is mutated.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "plugins" / "quant-research-orchestrator" / "scripts"
PY = sys.executable

REAL_REPO = os.environ.get("ZCODE_ORCH_REAL_REPO", str(REPO))


def run_hook(script: str, payload: dict, repo_root: str, runtime_dir: Path | None = None,
             cwd: str | None = None):
    env = dict(os.environ)
    env["QUANT_REPO_ROOT"] = repo_root
    if runtime_dir is not None:
        env["ZCODE_ORCH_RUNTIME_DIR"] = str(runtime_dir)
    proc = subprocess.run(
        [PY, str(SCRIPTS / script)], input=json.dumps(payload) + "\n",
        capture_output=True, text=True, env=env, timeout=15, cwd=cwd or repo_root)
    out = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, out


def write_dispatch(runtime: Path, **kw):
    runtime.mkdir(parents=True, exist_ok=True)
    ctx = {"schema": "zcode_orch_v3_dispatch@1", "task_id": "t9",
           "cycle_id": "ZCODE-ORCHESTRATION-V3", "role": "quant-implementer",
           "status": "DISPATCHED", "branch": "orca/fixture",
           "absolute_worktree": "/tmp/fixture", "base_sha": "a" * 40,
           "allowed_paths": ["/tmp/fixture/src"],
           "forbidden_paths": ["/tmp/fixture/other"],
           "updated_at_utc": "2026-09-11T00:00:00Z"}
    ctx.update(kw)
    (runtime / "current_dispatch.json").write_text(json.dumps(ctx), encoding="utf-8")
    return ctx


def write_tasks(runtime: Path, statuses):
    runtime.mkdir(parents=True, exist_ok=True)
    tasks = [{"task_id": f"t{i}", "status": st} for i, st in enumerate(statuses)]
    (runtime / "tasks.json").write_text(json.dumps(
        {"schema": "zcode_orch_v3_tasks@1", "cycle_id": "ZCODE-ORCHESTRATION-V3",
         "updated_at_utc": "2026-09-11T00:00:00Z", "writer": "fixture",
         "tasks": tasks}), encoding="utf-8")


# ------------------------------------------------------------------ pre_tool
def test_pre_tool_allows_root_lead_push_under_standing_delegation():
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Bash",
                        "tool_input": {"command": "git push origin main"}},
                       repo_root=REAL_REPO)
    assert rc == 0
    assert out == {}


def test_pre_tool_denies_lane_push():
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Bash",
                        "tool_input": {
                            "command": "git -C /tmp/repo/.worktrees/lane push origin lane"
                        }},
                       repo_root=REAL_REPO)
    assert rc == 0
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pre_tool_denies_hard_reset_and_env_echo():
    for cmd in ("git reset --hard HEAD~1", "cat .env", "printenv | grep SECRET"):
        rc, out = run_hook("hook_pre_tool.py",
                           {"tool_name": "Bash", "tool_input": {"command": cmd}},
                           repo_root=REAL_REPO)
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny", cmd


def test_pre_tool_denies_s1_touch():
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Bash",
                        "tool_input": {"command": "python run_s1_scored.py"}},
                       repo_root=REAL_REPO)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pre_tool_allows_ordinary_bash():
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Bash",
                        "tool_input": {"command": "pytest tests/test_atomic_io.py -q"}},
                       repo_root=REAL_REPO)
    assert rc == 0 and out == {}


def test_pre_tool_enforces_ownership_paths_when_dispatch_active(tmp_path):
    write_dispatch(tmp_path)
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Edit",
                        "tool_input": {"file_path": "/tmp/fixture/other/x.py",
                                       "old_string": "a", "new_string": "b"}},
                       repo_root=REAL_REPO, runtime_dir=tmp_path)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Write",
                        "tool_input": {"file_path": "/tmp/unrelated/x.py",
                                       "content": "x"}},
                       repo_root=REAL_REPO, runtime_dir=tmp_path)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Edit",
                        "tool_input": {"file_path": "/tmp/fixture/src/x.py",
                                       "old_string": "a", "new_string": "b"}},
                       repo_root=REAL_REPO, runtime_dir=tmp_path)
    assert rc == 0 and out == {}


def test_pre_tool_blocks_lane_registry_write_but_not_controller(tmp_path):
    write_dispatch(tmp_path)
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Write",
                        "tool_input": {"file_path":
                                       "/tmp/fixture/plans/CYCLE_REGISTRY.json",
                                       "content": "{}"}},
                       repo_root=REAL_REPO, runtime_dir=tmp_path)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    # no dispatch context anywhere (controller's own canonical write) -> allowed
    empty_runtime = tmp_path / "empty"
    empty_runtime.mkdir()
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Write",
                        "tool_input": {"file_path": "/tmp/fixture/plans/x.json",
                                       "content": "{}"}},
                       repo_root=REAL_REPO, runtime_dir=empty_runtime)
    assert rc == 0 and out == {}


def test_pre_tool_requires_dispatch_before_writable_dispatch(tmp_path):
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Agent",
                        "tool_input": {"name": "quant-implementer",
                                       "prompt": "implement the fixture lane"}},
                       repo_root=REAL_REPO, runtime_dir=tmp_path)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    write_dispatch(tmp_path)
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Agent",
                        "tool_input": {"name": "quant-implementer",
                                       "prompt": "implement the fixture lane"}},
                       repo_root=REAL_REPO, runtime_dir=tmp_path)
    assert rc == 0 and out == {}
    # read-only explorer never requires a dispatch context
    rc, out = run_hook("hook_pre_tool.py",
                       {"tool_name": "Agent",
                        "tool_input": {"name": "quant-explorer",
                                       "prompt": "explore the fixture"}},
                       repo_root=REAL_REPO, runtime_dir=tmp_path)
    assert rc == 0 and out == {}


# ---------------------------------------------------------------- post_agent
def test_post_agent_flags_missing_handoff(tmp_path):
    write_dispatch(tmp_path)
    write_tasks(tmp_path, ["DISPATCHED"])
    rc, out = run_hook("hook_post_agent.py",
                       {"tool_name": "Agent", "tool_response": {"summary": "done"}},
                       repo_root=REAL_REPO, runtime_dir=tmp_path)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "HANDOFF_INVALID" in ctx


def test_post_agent_points_to_present_handoff(tmp_path):
    write_dispatch(tmp_path)
    runtime = tmp_path
    write_tasks(runtime, ["HANDOFF_READY"])
    tasks = json.loads((runtime / "tasks.json").read_text(encoding="utf-8"))
    tasks["tasks"][0]["task_id"] = "t9"  # must match the dispatch context id
    tasks["tasks"][0]["handoff_path"] = str(runtime / "inbox" / "t9-handoff.json")
    (runtime / "inbox").mkdir(exist_ok=True)
    (runtime / "inbox" / "t9-handoff.json").write_text("{}", encoding="utf-8")
    (runtime / "tasks.json").write_text(json.dumps(tasks), encoding="utf-8")
    rc, out = run_hook("hook_post_agent.py",
                       {"tool_name": "Agent", "tool_response": {}},
                       repo_root=REAL_REPO, runtime_dir=runtime)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "Handoff artifact present" in ctx and "orchestrator_validate_handoff" in ctx


def test_post_agent_ignores_non_agent_tools(tmp_path):
    rc, out = run_hook("hook_post_agent.py",
                       {"tool_name": "Bash", "tool_response": {}},
                       repo_root=REAL_REPO, runtime_dir=tmp_path)
    assert rc == 0 and out == {}


# --------------------------------------------------------------------- stop
def test_stop_blocks_with_active_tasks_and_self_caps(tmp_path):
    write_tasks(tmp_path, ["READY", "DISPATCHED"])
    payload = {"stop_hook_active": True, "last_assistant_message": "done?"}
    rc, out = run_hook("hook_stop.py", payload, repo_root=REAL_REPO,
                       runtime_dir=tmp_path)
    assert out["decision"] == "block" and "t0" in out["reason"]
    for _ in range(2):
        rc, out = run_hook("hook_stop.py", payload, repo_root=REAL_REPO,
                           runtime_dir=tmp_path)
        assert out["decision"] == "block"
    # 4th consecutive block: hook stands down (bounded continuation)
    rc, out = run_hook("hook_stop.py", payload, repo_root=REAL_REPO,
                       runtime_dir=tmp_path)
    assert rc == 0 and out == {}


def test_stop_stays_silent_without_owned_work(tmp_path):
    write_tasks(tmp_path, ["TERMINAL", "INTEGRATED"])
    rc, out = run_hook("hook_stop.py", {"stop_hook_active": False},
                       repo_root=REAL_REPO, runtime_dir=tmp_path)
    assert rc == 0 and out == {}


def test_stop_reports_drift_on_malformed_tasks(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks.json").write_text("{broken", encoding="utf-8")
    rc, out = run_hook("hook_stop.py", {}, repo_root=REAL_REPO,
                       runtime_dir=tmp_path)
    assert out["decision"] == "block" and "CONTROL_STATE_DRIFT" in out["reason"]


# ------------------------------------------------------------ session_start
def test_session_start_injects_snapshot():
    rc, out = run_hook("hook_session_start.py", {"cwd": REAL_REPO},
                       repo_root=REAL_REPO, cwd=REAL_REPO)
    assert rc == 0
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "[orchestrator-v3 snapshot]" in ctx
    assert ("HEAD=" in ctx) and ("heavy_lock=" in ctx)


def test_session_start_failure_is_visible_not_clean(tmp_path):
    # a repo root with no registry -> snapshot must say UNAVAILABLE, never invent
    rc, out = run_hook("hook_session_start.py", {"cwd": str(tmp_path)},
                       repo_root=str(tmp_path), cwd=str(tmp_path))
    assert rc == 0
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "SNAPSHOT_UNAVAILABLE" in ctx
