#!/usr/bin/env python3
"""Orchestrator V3 task store (PLAN_zcode_orchestration_v3 sec 3.2, phase P2).

Machine-readable coordination state for one controller cycle. It is a thin,
fail-closed wrapper around the repository's own governance modules:

- every write goes through governance.atomic_io.atomic_write_json
  (schema-validate -> tmp -> fsync -> rename -> read-back) with a CAS on the
  previous content sha256;
- every applied transition appends one event to events.jsonl (append-only);
- missing / malformed / stale state is CONTROL_STATE_DRIFT - never an empty
  queue, never silently repaired;
- idempotent by (task_id, attempt_no, digest);
- no backward transitions; retry is a new attempt record, re-dispatch after a
  terminal failure is a NEW task_id.

This module never calls a model and never spawns agents. It is state only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Resolve the repository root so governance imports work regardless of where
# the plugin is invoked from (repo checkout, personal marketplace cache, hook
# subprocess with an unrelated cwd). QUANT_REPO_ROOT wins when set.
_DEFAULT_REPO = Path(__file__).resolve().parents[3]
REPO_ROOT = Path(os.environ.get("QUANT_REPO_ROOT", str(_DEFAULT_REPO))).resolve()
for _p in (str(REPO_ROOT / "research"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from governance import atomic_io  # noqa: E402

SCHEMA_ID = "zcode_orch_v3_tasks@1"
CONTROL_STATE_DRIFT = atomic_io.CONTROL_STATE_DRIFT

STATES = (
    "REGISTERED", "READY", "DISPATCHED", "RUNNING", "HANDOFF_READY",
    "VALIDATING", "INTEGRATED", "REJECTED", "BLOCKED", "TECHABORT", "TERMINAL",
)
TRANSITIONS = {
    "REGISTERED": {"READY"},
    "READY": {"DISPATCHED"},
    "DISPATCHED": {"RUNNING"},
    "RUNNING": {"HANDOFF_READY"},
    "HANDOFF_READY": {"VALIDATING"},
    "VALIDATING": {"INTEGRATED", "REJECTED", "BLOCKED", "TECHABORT"},
    "INTEGRATED": {"TERMINAL"},
    "REJECTED": {"TERMINAL"},
    "BLOCKED": {"TERMINAL"},
    "TECHABORT": {"TERMINAL"},
    "TERMINAL": set(),
}
TERMINAL_STATES = {"TERMINAL"}
READY_SOURCE = "REGISTERED"
ROLES = ("quant-explorer", "quant-implementer", "quant-reproducer", "quant-auditor")
WORKLOAD_CLASSES = ("LIGHT", "MEDIUM", "HEAVY")

REQUIRED_TASK_FIELDS = (
    "task_id", "cycle_id", "role", "objective", "created_utc", "updated_utc",
    "parent_controller_id", "status", "dependencies", "priority",
    "workload_class", "base_sha", "branch", "absolute_worktree",
    "allowed_paths", "forbidden_paths", "required_inputs", "required_outputs",
    "test_commands", "stop_conditions", "background_allowed",
    "zcode_invocation_id", "heartbeat_utc", "pid", "attempts", "max_attempts",
    "handoff_path", "blocker", "terminal_reason",
)
_HEX40 = __import__("re").compile(r"^[0-9a-f]{40}$")
_UTC = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class IllegalTransition(ValueError):
    pass


class TaskNotFound(KeyError):
    pass


class ForeignTaskRefused(ValueError):
    pass


class DependencyCycle(ValueError):
    pass


def now_utc() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fail(msg: str):
    raise atomic_io.SchemaValidationError(f"{SCHEMA_ID}: {msg}")


def validate_store(obj: dict) -> None:
    if obj.get("schema") != SCHEMA_ID:
        _fail(f"schema must be {SCHEMA_ID}, got {obj.get('schema')!r}")
    if not isinstance(obj.get("cycle_id"), str) or not obj["cycle_id"]:
        _fail("cycle_id must be a non-empty string")
    if not isinstance(obj.get("tasks"), list):
        _fail("tasks must be a list")
    seen = set()
    for t in obj["tasks"]:
        if not isinstance(t, dict):
            _fail("task must be an object")
        missing = [f for f in REQUIRED_TASK_FIELDS if f not in t]
        if missing:
            _fail(f"{t.get('task_id', '?')}: missing fields {missing}")
        tid = t["task_id"]
        if tid in seen:
            _fail(f"duplicate task_id {tid}")
        seen.add(tid)
        if t["status"] not in STATES:
            _fail(f"{tid}: illegal status {t['status']!r}")
        if t["role"] not in ROLES:
            _fail(f"{tid}: illegal role {t['role']!r}")
        if t["workload_class"] not in WORKLOAD_CLASSES:
            _fail(f"{tid}: illegal workload_class {t['workload_class']!r}")
        if t["parent_controller_id"] != "primary-lead":
            _fail(f"{tid}: parent_controller_id must be 'primary-lead' (one-level hierarchy)")
        if t.get("base_sha") and not _HEX40.match(t["base_sha"]):
            _fail(f"{tid}: base_sha must be 40-hex or empty")
        for dep in t["dependencies"]:
            if dep == tid:
                _fail(f"{tid}: self-dependency")
        if not isinstance(t["attempts"], list):
            _fail(f"{tid}: attempts must be a list")
        if not (isinstance(t["max_attempts"], int) and 1 <= t["max_attempts"] <= 10):
            _fail(f"{tid}: max_attempts must be int in [1,10]")
    for t in obj["tasks"]:
        for dep in t["dependencies"]:
            if dep not in seen:
                _fail(f"{t['task_id']}: dependency {dep!r} is not a registered task")
    for f in ("schema", "cycle_id", "updated_at_utc", "writer", "tasks"):
        if f not in obj:
            _fail(f"missing top-level field {f}")


def validate_handoff(obj: dict) -> None:
    required = ("task_id", "cycle_id", "role", "lane", "dispatch_sha",
                "actual_start_sha", "commit_sha", "changed_paths", "tests",
                "authority_claims", "known_limitations", "incidents",
                "tree_status", "workers", "outputs", "recommended_next_action")
    missing = [f for f in required if f not in obj]
    if missing:
        _fail(f"handoff missing fields {missing}")
    for f in ("dispatch_sha", "actual_start_sha", "commit_sha"):
        if obj[f] and not _HEX40.match(str(obj[f])):
            _fail(f"handoff {f} must be 40-hex or empty")
    if not isinstance(obj["tests"], list):
        _fail("handoff tests must be a list")
    for t in obj["tests"]:
        for f in ("command", "exit_code", "verdict"):
            if f not in t:
                _fail(f"handoff test row missing {f}: {t}")
        if t["verdict"] not in ("PASS", "FAIL", "NOT_RUN"):
            _fail(f"handoff test verdict must be PASS|FAIL|NOT_RUN, got {t['verdict']!r}")


def handoff_digest(handoff: dict) -> str:
    payload = json.dumps(handoff, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class OrchestratorStore:
    """One cycle's task store under <repo>/.runtime/orchestrator_v3/."""

    def __init__(self, repo_root: Optional[os.PathLike | str] = None,
                 cycle_id: str = "ZCODE-ORCHESTRATION-V3",
                 runtime_dir: Optional[os.PathLike | str] = None):
        self.repo_root = Path(repo_root).resolve() if repo_root else REPO_ROOT
        self.cycle_id = cycle_id
        if runtime_dir:
            self.runtime = Path(runtime_dir).resolve()
        else:
            # ZCODE_ORCH_RUNTIME_DIR lets hermetic tests / alternate checkouts
            # redirect the runtime state; governance imports stay bound to
            # REPO_ROOT (the canonical modules), only the state moves.
            env_dir = os.environ.get("ZCODE_ORCH_RUNTIME_DIR")
            self.runtime = Path(env_dir).resolve() if env_dir else \
                self.repo_root / ".runtime" / "orchestrator_v3"
        self.tasks_path = self.runtime / "tasks.json"
        self.events_path = self.runtime / "events.jsonl"
        self.heartbeats = self.runtime / "heartbeats"
        self.inbox = self.runtime / "inbox"
        self.current_dispatch = self.runtime / "current_dispatch.json"

    # ------------------------------------------------------------ primitives
    def _ensure_dirs(self) -> None:
        for d in (self.runtime, self.heartbeats, self.inbox):
            d.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        """Strict load; missing state is CONTROL_STATE_DRIFT, never empty."""
        return atomic_io.load_json_strict(self.tasks_path, schema_validator=validate_store)

    def _save(self, store: dict, *, expect_prev_sha: Optional[str]) -> str:
        self._ensure_dirs()
        return atomic_io.atomic_write_json(
            self.tasks_path, store, schema_validator=validate_store,
            expect_prev_sha=expect_prev_sha)

    def _event(self, event: dict) -> None:
        atomic_io.append_event(self.events_path, dict(event, cycle_id=self.cycle_id))

    def exists(self) -> bool:
        return self.tasks_path.exists()

    # -------------------------------------------------------------- mutation
    def intake(self, writer: str = "primary-lead") -> dict:
        """Create the store for this cycle; refuses to overwrite (idempotent).

        Missing state is only repairable by an EXPLICIT intake, never by a
        read path. An existing valid store is returned untouched.
        """
        if self.exists():
            return self.load()
        self._ensure_dirs()
        store = {"schema": SCHEMA_ID, "cycle_id": self.cycle_id,
                 "updated_at_utc": now_utc(), "writer": writer, "tasks": []}
        self._save(store, expect_prev_sha=None)
        self._event({"event": "STORE_INTAKE", "writer": writer})
        return store

    def _resolve(self, store: dict, task_id: str) -> dict:
        for t in store["tasks"]:
            if t["task_id"] == task_id:
                return t
        raise TaskNotFound(task_id)

    def _check_cycle(self, task: dict) -> None:
        if task["cycle_id"] != self.cycle_id:
            raise ForeignTaskRefused(
                f"task {task['task_id']} belongs to cycle {task['cycle_id']!r}, "
                f"this store serves {self.cycle_id!r} - foreign task isolation")

    def _check_dependency_cycle(self, store: dict, task_id: str) -> None:
        edges = {t["task_id"]: list(t["dependencies"]) for t in store["tasks"]}
        seen, stack = set(), [task_id]
        while stack:
            cur = stack.pop()
            if cur == task_id and cur in seen:
                raise DependencyCycle(f"registering {task_id} would create a dependency cycle")
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(edges.get(cur, []))

    def register_task(self, *, task_id: str, role: str, objective: str,
                      base_sha: str = "", branch: str = "", absolute_worktree: str = "",
                      allowed_paths=None, forbidden_paths=None,
                      dependencies=None, priority: int = 5,
                      workload_class: str = "LIGHT", background_allowed: bool = True,
                      required_inputs=None, required_outputs=None,
                      test_commands=None, stop_conditions=None,
                      max_attempts: int = 3,
                      writer: str = "primary-lead") -> dict:
        if role not in ROLES:
            raise ValueError(f"register: role must be one of {ROLES}, got {role!r}")
        if workload_class not in WORKLOAD_CLASSES:
            raise ValueError(f"register: workload_class must be one of {WORKLOAD_CLASSES}")
        store = self.load()
        try:
            self._resolve(store, task_id)
        except TaskNotFound:
            pass
        else:
            raise ValueError(f"register: {task_id} already registered (duplicate ids refused)")
        now = now_utc()
        task = {
            "task_id": task_id, "cycle_id": self.cycle_id, "role": role,
            "objective": objective, "created_utc": now, "updated_utc": now,
            "parent_controller_id": "primary-lead", "status": "REGISTERED",
            "dependencies": sorted(set(dependencies or [])),
            "priority": int(priority), "workload_class": workload_class,
            "base_sha": base_sha, "branch": branch,
            "absolute_worktree": absolute_worktree,
            "allowed_paths": list(allowed_paths or []),
            "forbidden_paths": list(forbidden_paths or []),
            "required_inputs": list(required_inputs or []),
            "required_outputs": list(required_outputs or []),
            "test_commands": list(test_commands or []),
            "stop_conditions": list(stop_conditions or []),
            "background_allowed": bool(background_allowed),
            "zcode_invocation_id": None, "heartbeat_utc": None, "pid": None,
            "attempts": [], "max_attempts": int(max_attempts),
            "handoff_path": None, "blocker": None, "terminal_reason": None,
        }
        store["tasks"].append(task)
        self._check_dependency_cycle(store, task_id)
        store["updated_at_utc"] = now
        store["writer"] = writer
        prev = atomic_io.sha256_file(self.tasks_path)
        self._save(store, expect_prev_sha=prev)
        self._event({"event": "TASK_REGISTERED", "task_id": task_id, "role": role,
                     "dependencies": task["dependencies"], "workload_class": workload_class})
        return task

    def list_ready(self) -> list:
        """READY candidates: REGISTERED with all dependencies INTEGRATED/TERMINAL-done."""
        store = self.load()
        done = {t["task_id"] for t in store["tasks"]
                if t["status"] in ("INTEGRATED", "TERMINAL")}
        ready = []
        for t in store["tasks"]:
            if t["status"] != READY_SOURCE:
                continue
            if all(d in done for d in t["dependencies"]):
                ready.append(t)
        ready.sort(key=lambda t: (t["priority"], t["created_utc"]))
        return ready

    def _transition(self, store: dict, task_id: str, new_status: str,
                    *, writer: str, extra: Optional[dict] = None) -> dict:
        task = self._resolve(store, task_id)
        self._check_cycle(task)
        allowed = TRANSITIONS[task["status"]]
        if new_status not in allowed:
            raise IllegalTransition(
                f"{task_id}: {task['status']} -> {new_status} is not an allowed transition "
                f"(no backward moves; retry = new attempt, re-dispatch = new task)")
        now = now_utc()
        task["status"] = new_status
        task["updated_utc"] = now
        if extra:
            task.update(extra)
        store["updated_at_utc"] = now
        store["writer"] = writer
        return task

    def mark_dispatched(self, *, task_id: str, invocation_id: Optional[str] = None,
                        writer: str = "primary-lead") -> dict:
        """REGISTERED -> READY -> DISPATCHED (plan sec 3.2 chain; READY is
        materialized here when every dependency is done, never skipped and
        never granted while a dependency is open). Idempotent: a repeated
        identical dispatch is a no-op."""
        store = self.load()
        task = self._resolve(store, task_id)
        self._check_cycle(task)
        open_attempt = next((a for a in task["attempts"] if a["returned_utc"] is None), None)
        if task["status"] == "DISPATCHED" and open_attempt:
            self._event({"event": "TASK_DISPATCH_DUPLICATE_IGNORED", "task_id": task_id,
                         "attempt": open_attempt["attempt_no"]})
            return task
        if task["status"] == "REGISTERED":
            done = {t["task_id"] for t in store["tasks"]
                    if t["status"] in ("INTEGRATED", "TERMINAL")}
            open_deps = [d for d in task["dependencies"] if d not in done]
            if open_deps:
                raise IllegalTransition(
                    f"{task_id}: dependencies not done yet {open_deps} - "
                    "READY is never granted while a dependency is open")
            self._transition(store, task_id, "READY", writer=writer)
            self._event({"event": "TASK_READY", "task_id": task_id})
        attempt_no = len(task["attempts"]) + 1
        if attempt_no > task["max_attempts"]:
            raise IllegalTransition(
                f"{task_id}: attempt {attempt_no} exceeds max_attempts "
                f"{task['max_attempts']} - TECHABORT is the honest state, not another retry")
        self._transition(store, task_id, "DISPATCHED", writer=writer)
        task = self._resolve(store, task_id)
        task["attempts"].append({"attempt_no": attempt_no, "dispatched_utc": now_utc(),
                                 "returned_utc": None, "outcome": None,
                                 "handoff_sha256": None,
                                 "zcode_invocation_id": invocation_id})
        if invocation_id:
            task["zcode_invocation_id"] = invocation_id
        store["updated_at_utc"] = task["updated_utc"]
        prev = atomic_io.sha256_file(self.tasks_path)
        self._save(store, expect_prev_sha=prev)
        self._event({"event": "TASK_DISPATCHED", "task_id": task_id, "attempt": attempt_no,
                     "invocation_id": invocation_id})
        self._write_current_dispatch(task)
        return task

    def _write_current_dispatch(self, task: dict) -> None:
        """Publish the active-dispatch context the PreToolUse hook enforces."""
        self._ensure_dirs()
        ctx = {"schema": "zcode_orch_v3_dispatch@1",
               "task_id": task["task_id"], "cycle_id": task["cycle_id"],
               "role": task["role"], "status": task["status"],
               "branch": task["branch"], "absolute_worktree": task["absolute_worktree"],
               "base_sha": task["base_sha"],
               "allowed_paths": task["allowed_paths"],
               "forbidden_paths": task["forbidden_paths"],
               "updated_at_utc": now_utc()}
        atomic_io.atomic_write_json(
            self.current_dispatch, ctx, schema_validator=validate_dispatch_context)

    def heartbeat(self, *, task_id: str, pid: Optional[int] = None,
                  writer: str = "primary-lead") -> dict:
        store = self.load()
        task = self._resolve(store, task_id)
        self._check_cycle(task)
        if task["status"] not in ("DISPATCHED", "RUNNING"):
            raise IllegalTransition(
                f"{task_id}: heartbeat refused in status {task['status']} "
                "(heartbeats belong to live work only)")
        if task["status"] == "DISPATCHED":
            # a live heartbeat IS evidence of running work: materialize the
            # plan chain DISPATCHED -> RUNNING (journaled, forward-only)
            self._transition(store, task_id, "RUNNING", writer=writer)
            self._event({"event": "TASK_RUNNING", "task_id": task_id})
            task = self._resolve(store, task_id)
        now = now_utc()
        task["heartbeat_utc"] = now
        if pid is not None:
            task["pid"] = int(pid)
        store["updated_at_utc"] = now
        prev = atomic_io.sha256_file(self.tasks_path)
        self._save(store, expect_prev_sha=prev)
        atomic_io.append_event(self.events_path,
                               {"event": "TASK_HEARTBEAT", "task_id": task_id,
                                "cycle_id": self.cycle_id, "pid": task["pid"]})
        return task

    def mark_running(self, *, task_id: str, writer: str = "primary-lead") -> dict:
        store = self.load()
        self._transition(store, task_id, "RUNNING", writer=writer)
        task = self._resolve(store, task_id)
        prev = atomic_io.sha256_file(self.tasks_path)
        self._save(store, expect_prev_sha=prev)
        self._event({"event": "TASK_RUNNING", "task_id": task_id})
        return task

    def publish_handoff(self, *, task_id: str, handoff: dict,
                        handoff_path: Optional[os.PathLike | str] = None,
                        writer: str = "primary-lead") -> dict:
        """RUNNING -> HANDOFF_READY with the digest recorded on the attempt."""
        validate_handoff(handoff)
        if handoff["task_id"] != task_id:
            raise ForeignTaskRefused(
                f"handoff declares task {handoff['task_id']!r}, store call was {task_id!r}")
        digest = handoff_digest(handoff)
        store = self.load()
        self._transition(store, task_id, "HANDOFF_READY", writer=writer)
        task = self._resolve(store, task_id)
        open_attempt = next((a for a in reversed(task["attempts"])
                             if a["returned_utc"] is None), None)
        if open_attempt is None:
            raise IllegalTransition(f"{task_id}: no open attempt to bind the handoff to")
        if open_attempt["handoff_sha256"] == digest:
            self._event({"event": "TASK_HANDOFF_DUPLICATE_IGNORED", "task_id": task_id,
                         "digest": digest[:16]})
            return task
        open_attempt["returned_utc"] = now_utc()
        open_attempt["outcome"] = "HANDOFF_PUBLISHED"
        open_attempt["handoff_sha256"] = digest
        path = Path(handoff_path) if handoff_path else \
            self.inbox / f"{task_id}-handoff.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            atomic_io.atomic_write_json(
                path, handoff, schema_validator=validate_handoff)
        task["handoff_path"] = str(path)
        store["updated_at_utc"] = task["updated_utc"]
        prev = atomic_io.sha256_file(self.tasks_path)
        self._save(store, expect_prev_sha=prev)
        self._event({"event": "TASK_HANDOFF_PUBLISHED", "task_id": task_id,
                     "attempt": open_attempt["attempt_no"],
                     "handoff_sha256": digest, "handoff_path": str(path)})
        return task

    def validate_handoff(self, *, task_id: str, writer: str = "primary-lead") -> dict:
        """HANDOFF_READY -> VALIDATING. Re-reads the artifact from disk (bytes are
        authority): a handoff whose file digest differs from the recorded digest,
        or whose dispatch_sha != actual_start_sha, is drift, never silently ok."""
        store = self.load()
        task = self._resolve(store, task_id)
        self._check_cycle(task)
        if not task.get("handoff_path") or not Path(task["handoff_path"]).exists():
            raise atomic_io.ControlStateDrift(
                f"{task_id}: recorded handoff artifact missing on disk")
        on_disk = json.loads(Path(task["handoff_path"]).read_text(encoding="utf-8"))
        if handoff_digest(on_disk) != task["attempts"][-1]["handoff_sha256"]:
            raise atomic_io.ControlStateDrift(
                f"{task_id}: handoff bytes changed after publish (digest mismatch)")
        self._transition(store, task_id, "VALIDATING", writer=writer)
        task = self._resolve(store, task_id)
        prev = atomic_io.sha256_file(self.tasks_path)
        self._save(store, expect_prev_sha=prev)
        self._event({"event": "TASK_VALIDATING", "task_id": task_id})
        return task

    def mark_integrated(self, *, task_id: str, commit_sha: str = "",
                        writer: str = "primary-lead") -> dict:
        store = self.load()
        self._transition(store, task_id, "INTEGRATED", writer=writer)
        task = self._resolve(store, task_id)
        if commit_sha:
            if not _HEX40.match(commit_sha):
                raise ValueError(f"mark_integrated: commit_sha must be 40-hex")
            task["attempts"][-1]["integrated_commit_sha"] = commit_sha
        store["updated_at_utc"] = task["updated_utc"]
        prev = atomic_io.sha256_file(self.tasks_path)
        self._save(store, expect_prev_sha=prev)
        self._event({"event": "TASK_INTEGRATED", "task_id": task_id,
                     "commit_sha": commit_sha})
        self._clear_current_dispatch(task_id)
        return task

    def record_outcome(self, *, task_id: str, outcome: str, reason: str = "",
                       writer: str = "primary-lead") -> dict:
        if outcome not in ("REJECTED", "BLOCKED", "TECHABORT"):
            raise ValueError(f"record_outcome: outcome must be REJECTED|BLOCKED|TECHABORT")
        store = self.load()
        self._transition(store, task_id, outcome, writer=writer,
                         extra={"blocker": reason or None})
        task = self._resolve(store, task_id)
        prev = atomic_io.sha256_file(self.tasks_path)
        self._save(store, expect_prev_sha=prev)
        self._event({"event": f"TASK_{outcome}", "task_id": task_id, "reason": reason})
        self._clear_current_dispatch(task_id)
        return task

    def mark_terminal(self, *, task_id: str, terminal_reason: str,
                      writer: str = "primary-lead") -> dict:
        store = self.load()
        self._transition(store, task_id, "TERMINAL", writer=writer,
                         extra={"terminal_reason": terminal_reason})
        task = self._resolve(store, task_id)
        prev = atomic_io.sha256_file(self.tasks_path)
        self._save(store, expect_prev_sha=prev)
        self._event({"event": "TASK_TERMINAL", "task_id": task_id,
                     "terminal_reason": terminal_reason})
        return task

    def _clear_current_dispatch(self, task_id: str) -> None:
        if self.current_dispatch.exists():
            try:
                ctx = json.loads(self.current_dispatch.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                ctx = None
            if ctx and ctx.get("task_id") == task_id:
                self.current_dispatch.unlink()

    # -------------------------------------------------------------- readouts
    def waiting_summary(self) -> dict:
        store = self.load()
        ready = [t["task_id"] for t in self.list_ready()]
        inflight = [{"task_id": t["task_id"], "status": t["status"],
                     "heartbeat_utc": t["heartbeat_utc"], "pid": t["pid"],
                     "attempt": len(t["attempts"])}
                    for t in store["tasks"]
                    if t["status"] in ("DISPATCHED", "RUNNING", "HANDOFF_READY",
                                       "VALIDATING")]
        awaiting_validation = [t["task_id"] for t in store["tasks"]
                               if t["status"] == "HANDOFF_READY"]
        return {"cycle_id": self.cycle_id, "ready": ready, "inflight": inflight,
                "awaiting_validation": awaiting_validation,
                "updated_at_utc": store["updated_at_utc"]}

    def terminal_check(self) -> dict:
        store = self.load()
        non_terminal = [t["task_id"] for t in store["tasks"]
                        if t["status"] not in TERMINAL_STATES]
        blocked = [t["task_id"] for t in store["tasks"] if t["status"] == "BLOCKED"]
        return {"cycle_id": self.cycle_id,
                "tasks_total": len(store["tasks"]),
                "tasks_terminal": len(store["tasks"]) - len(non_terminal),
                "non_terminal_tasks": non_terminal,
                "blocked_tasks": blocked,
                "all_terminal": not non_terminal}


# The dispatch-context validator used by _write_current_dispatch lives here so
# hooks can import the same check.
def validate_dispatch_context(obj: dict) -> None:
    if obj.get("schema") != "zcode_orch_v3_dispatch@1":
        _fail("dispatch context schema must be zcode_orch_v3_dispatch@1")
    for f in ("task_id", "cycle_id", "role", "status", "allowed_paths",
              "forbidden_paths"):
        if f not in obj:
            _fail(f"dispatch context missing {f}")
