"""ZCODE-ORCHESTRATION-V3 P2: stdio MCP server protocol tests (gate Z3-G2).

The server is spawned exactly as ZCode would run it (JSON-RPC lines on stdio).
State goes to a hermetic runtime dir via ZCODE_ORCH_RUNTIME_DIR; governance
imports stay bound to the real repository (read-only).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SERVER = REPO / "plugins" / "quant-research-orchestrator" / "scripts" / "mcp_server.py"
PY = sys.executable


class McpClient:
    def __init__(self, tmp_path):
        env = dict(os.environ)
        env["ZCODE_ORCH_RUNTIME_DIR"] = str(tmp_path / "rt")
        self.proc = subprocess.Popen(
            [PY, str(SERVER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=env, cwd=str(tmp_path))

    def send(self, msg: dict, timeout: float = 20.0) -> dict | None:
        import select
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        if "method" in msg and str(msg["method"]).startswith("notifications/"):
            return None  # notifications never produce a response frame
        ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
        if not ready:
            self.proc.kill()
            raise AssertionError(f"MCP server did not respond within {timeout}s")
        line = self.proc.stdout.readline()
        return json.loads(line) if line.strip() else None

    def call(self, name: str, arguments: dict, mid=1):
        return self.send({"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                          "params": {"name": name, "arguments": arguments}})

    def result(self, resp: dict):
        assert resp is not None and "result" in resp, resp
        return json.loads(resp["result"]["content"][0]["text"])

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=10)


@pytest.fixture()
def client(tmp_path):
    c = McpClient(tmp_path)
    yield c
    c.close()


def test_initialize_and_tools_list(client):
    resp = client.send({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                        "params": {}})
    assert resp["result"]["serverInfo"]["name"] == "quant-research-orchestrator"
    resp = client.send({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {t["name"] for t in resp["result"]["tools"]}
    assert {"orchestrator_intake", "orchestrator_register_task",
            "orchestrator_list_ready", "orchestrator_mark_dispatched",
            "orchestrator_heartbeat", "orchestrator_publish_handoff",
            "orchestrator_validate_handoff", "orchestrator_mark_integrated",
            "orchestrator_record_blocker", "orchestrator_waiting_summary",
            "orchestrator_terminal_check"} <= names
    # notifications produce no response frame
    client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})


def test_full_lifecycle_through_mcp(client):
    r = client.result(client.call("orchestrator_intake", {}, mid=1))
    assert r["schema"] == "zcode_orch_v3_tasks@1"
    r = client.result(client.call("orchestrator_register_task", {
        "task_id": "m1", "role": "quant-explorer", "objective": "mcp fixture",
        "base_sha": "a" * 40, "branch": "orca/fixture",
        "absolute_worktree": "/tmp/fixture",
        "allowed_paths": ["/tmp/fixture"]}, mid=2))
    assert r["status"] == "REGISTERED"
    r = client.result(client.call("orchestrator_list_ready", {}, mid=3))
    assert [t["task_id"] for t in r["ready"]] == ["m1"]
    r = client.result(client.call("orchestrator_mark_dispatched",
                                  {"task_id": "m1", "invocation_id": "inv-1"}, mid=4))
    assert r["status"] == "DISPATCHED"
    r = client.result(client.call("orchestrator_heartbeat",
                                  {"task_id": "m1", "pid": 4242}, mid=5))
    assert r["status"] == "RUNNING"  # live heartbeat materializes DISPATCHED->RUNNING
    handoff = {"task_id": "m1", "cycle_id": "ZCODE-ORCHESTRATION-V3",
               "role": "quant-explorer", "lane": "fixture",
               "dispatch_sha": "b" * 40, "actual_start_sha": "b" * 40,
               "commit_sha": "c" * 40, "changed_paths": [],
               "tests": [{"command": "true", "exit_code": 0, "verdict": "PASS"}],
               "authority_claims": [], "known_limitations": [], "incidents": [],
               "tree_status": "clean", "workers": 0, "outputs": [],
               "recommended_next_action": "integrate"}
    r = client.result(client.call("orchestrator_publish_handoff",
                                  {"task_id": "m1", "handoff": handoff}, mid=6))
    assert r["status"] == "HANDOFF_READY"
    r = client.result(client.call("orchestrator_validate_handoff",
                                  {"task_id": "m1"}, mid=7))
    assert r["status"] == "VALIDATING"
    r = client.result(client.call("orchestrator_mark_integrated",
                                  {"task_id": "m1", "commit_sha": "c" * 40}, mid=8))
    assert r["status"] == "INTEGRATED"
    r = client.result(client.call("orchestrator_terminal_check", {}, mid=9))
    assert r["non_terminal_tasks"] == ["m1"] and not r["all_terminal"]


def test_illegal_transition_is_tool_error(client):
    client.result(client.call("orchestrator_intake", {}))
    client.result(client.call("orchestrator_register_task", {
        "task_id": "m2", "role": "quant-explorer", "objective": "x"}, mid=1))
    resp = client.call("orchestrator_mark_integrated", {"task_id": "m2"}, mid=2)
    assert resp["result"]["isError"] is True
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["kind"] == "IllegalTransition"


def test_missing_state_is_drift_not_empty(client, tmp_path):
    # no intake: read paths must surface CONTROL_STATE_DRIFT, not an empty list
    resp = client.call("orchestrator_waiting_summary", {}, mid=1)
    assert resp["result"]["isError"] is True
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["kind"] == "CONTROL_STATE_DRIFT"


def test_unknown_task_is_tool_error(client):
    client.result(client.call("orchestrator_intake", {}))
    resp = client.call("orchestrator_validate_handoff", {"task_id": "ghost"}, mid=1)
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["kind"] == "TaskNotFound"


def test_unknown_method_is_rpc_error(client):
    resp = client.send({"jsonrpc": "2.0", "id": 5, "method": "bogus/method"})
    assert resp["error"]["code"] == -32601
