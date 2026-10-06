"""Production canonical-integration wrapper — the execution layer a future
REGISTERED FUTURES-5SYM-PRESCORED cycle calls (LANE-CANONICAL-CODE, wave 4,
round FUTURES-5SYM-PRESCORED-20261005).

This module is the CODE counterpart of freeze_wiring/CANONICAL_INTEGRATION.md
(that file is documentation-only; ERRATUM 2 narrowed the wave-3 claim
"canonical integration" to exactly this gap). It WRAPS the repo's canonical
governance APIs — it never reimplements them:

- heavy lock      : research/governance/heavy_lock.py (machine-wide
                    fcntl.flock + single RUNNING-row registry). acquire,
                    inspect, release, process_start_token all come from the
                    canonical module.
- cycle registry  : research/governance/cycle_registry.py +
                    governance.atomic_io (validate -> tmp -> fsync -> rename
                    -> read-back, CAS on prev content sha256, append-only
                    journal, deterministic projection).

Sandbox isolation law (how tests run the SAME code): the canonical heavy-lock
module derives its runtime internally and callers cannot select a path. The
ONE sanctioned redirection for tests is the module-level runtime constant.
When the environment override ``F5SYM_GOVERNANCE_DIR`` (or the explicit
``target_root=`` argument) names a SANDBOX governance directory, this wrapper
patches ``heavy_lock.RUNTIME_DIRNAME`` around each canonical call — the
flock/registry/journal semantics remain 100% heavy_lock's own code operating
on the sandbox copy. When no sandbox target is given, or the target resolves
to the REAL governance dir / REAL registry, this PREP build REFUSES before
any real write (hard-compiled, the same law as exec/scored_runner_v2.py's
dead ``--allow-real-governance`` flag).

Codes raised:
  AuthorityError            REGISTRY_UNREADABLE | REGISTRY_ROW_MISSING |
                            HEAD_MISMATCH | BRANCH_MISMATCH |
                            LIFECYCLE_NOT_EXECUTABLE | GO_MISSING |
                            GO_CYCLE_MISMATCH | GO_PHRASE_MISMATCH |
                            TWO_KEY_INCOMPLETE
  CanonicalRefusal          REAL_LOCK_ACQUIRE_REFUSED_PREP |
                            REGISTRY_WRITE_REAL_REFUSED | CAS_MISMATCH |
                            CONTROL_STATE_DRIFT | LOCK_POSTACQUIRE_DRIFT
  CanonicalLockBusy         verdict NOT_RUN_RESOURCE_CONFLICT (exit 75)

Final-status statuses: FINISHED (exit 0) | FAILED (exit 3, BUG1/BUG2 class)
| REFUSED (exit 2) | NOT_RUN_RESOURCE_CONFLICT (exit 75). FINAL_STATUS.json
is machine-readable and written on EVERY terminal path, success or not.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# import the CANONICAL governance modules from THIS repo tree (same module
# researchctl.py uses — sys.path insertion mirrors researchctl's own pattern)
# ---------------------------------------------------------------------------

import sys

_THIS = Path(__file__).resolve()
_CYCLE_DIR = _THIS.parents[1]           # .../research/control/<CYCLE_ID>
_REPO = _THIS.parents[4]                # repo root (research/control/CYCLE -> research -> root)
_RESEARCH_DIR = _REPO / "research"

if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

from governance import atomic_io, cycle_registry, heavy_lock  # noqa: E402

CYCLE_DIR = _CYCLE_DIR

# --- real-root authority paths: hard-refused targets (PREP build) ----------
REAL_ROOT_REGISTRY = "/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json"
REAL_PLANS_DIR = os.path.dirname(REAL_ROOT_REGISTRY)
REAL_GOVERNANCE_DIR = os.path.expanduser("~/.my-quantitative-governance")
REAL_HEAVY_RUNTIME = os.path.join(REAL_GOVERNANCE_DIR, "heavy_runtime")

SANDBOX_ENV_VAR = "F5SYM_GOVERNANCE_DIR"

# Hard-compiled PREP law: real governance writes are refused in this build.
# TODO(owner-authorization): flipping PREP_BUILD to False requires an explicit
# owner instruction naming this wrapper (production canonical integration),
# a REGISTERED cycle row in plans/CYCLE_REGISTRY.json whose lifecycle is
# ACTIVE_HEAVY, and a typed owner GO at the cycle's own gate (P-8). Until
# then every real-mode write/acquire fails closed (see
# canonical/CANONICAL_INTEGRATION_V2.md NOT_RUN table).
PREP_BUILD = True

EXIT_OK, EXIT_REFUSED, EXIT_FAILED, EXIT_CONFLICT = 0, 2, 3, 75

NOT_RUN_RESOURCE_CONFLICT = heavy_lock.NOT_RUN_RESOURCE_CONFLICT
CONTROL_STATE_DRIFT = heavy_lock.CONTROL_STATE_DRIFT

# lifecycles from which a production step may actually execute
EXECUTABLE_LIFECYCLES = ("ACTIVE_LIGHT", "ACTIVE_HEAVY")
UNMEASURED_HEAD = cycle_registry.UNMEASURED_HEAD

# named test faults (same production-code fault-seam pattern as
# exec/scored_runner_v2.py KNOWN_FAULTS / --test-fault)
KNOWN_FAULTS = {"post_acquire_foreign_row", "fail_handoff_write", "fail_release"}

FINAL_STATUS_SCHEMA = "canonical_final_status@1"
HANDOFF_SCHEMA = "canonical_handoff@1"


# ------------------------------------------------------------------- errors

class AuthorityError(RuntimeError):
    """Cycle authority verification failed (pre-lock, fail closed)."""

    def __init__(self, code: str, detail: dict | None = None):
        super().__init__(code)
        self.code = code
        self.detail = dict(detail or {})


class CanonicalRefusal(RuntimeError):
    """Wrapper-level refusal before/around a canonical surface mutation."""

    exit_code = EXIT_REFUSED

    def __init__(self, code: str, detail: dict | None = None):
        super().__init__(code)
        self.code = code
        self.detail = dict(detail or {})


class CanonicalLockBusy(RuntimeError):
    """The canonical machine-wide heavy lock is held elsewhere."""

    exit_code = EXIT_CONFLICT
    verdict = NOT_RUN_RESOURCE_CONFLICT

    def __init__(self, detail: dict | None = None):
        super().__init__(NOT_RUN_RESOURCE_CONFLICT)
        self.detail = dict(detail or {})


# ------------------------------------------------------------------ helpers

def canonical_go_phrase(cycle_id: str) -> str:
    """Byte-exact GO phrase law (verbatim equality, no trim, no case-fold)."""
    return f"GO {cycle_id} SCORED EXECUTION"


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _atomic_write_json(path: os.PathLike | str, payload: dict) -> str:
    """Small artifact writer (tmp + fsync + replace + read-back). Governance
    files go through governance.atomic_io instead; this is for run artifacts
    (FINAL_STATUS.json, handoff) owned by this step."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    tmp = p.with_name(f"{p.name}.tmp.{os.getpid()}")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, p)
    if p.read_bytes() != data:
        raise CanonicalRefusal("ARTIFACT_READBACK_MISMATCH", {"path": str(p)})
    return hashlib.sha256(data).hexdigest()


def _realpath(p: os.PathLike | str) -> str:
    return os.path.realpath(str(p))


def is_real_governance_target(p: os.PathLike | str) -> bool:
    """True when p IS the real registry, or resolves inside the real plans
    dir, or inside the real governance dir (the runner's R-GOV law)."""
    rp = _realpath(p)
    if rp == _realpath(REAL_ROOT_REGISTRY):
        return True
    if rp == _realpath(REAL_GOVERNANCE_DIR) or rp.startswith(_realpath(REAL_GOVERNANCE_DIR) + os.sep):
        return True
    return rp.startswith(_realpath(REAL_PLANS_DIR) + os.sep)


def _sha256_file(path: os.PathLike | str) -> Optional[str]:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def artifacts_digest(expected_artifacts: list[str]) -> str:
    """Content digest of the expected-artifacts list (order-independent)."""
    return hashlib.sha256(
        json.dumps(sorted(str(a) for a in expected_artifacts), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# --------------------------------------------- sandbox runtime redirection

@contextlib.contextmanager
def _sandbox_runtime(gov_root: os.PathLike | str):
    """Point governance.heavy_lock at the SANDBOX governance dir for the
    duration of ONE canonical call. This is the sanctioned redirection: the
    same heavy_lock code path runs, only its internally-derived runtime
    directory constant is aimed at the sandbox copy. Real state is never
    touched (acquire/inspect/cleanup_stale all read machine_runtime_dir())."""
    saved = heavy_lock.RUNTIME_DIRNAME
    heavy_lock.RUNTIME_DIRNAME = Path(gov_root) / "heavy_runtime"
    try:
        yield heavy_lock.RUNTIME_DIRNAME
    finally:
        heavy_lock.RUNTIME_DIRNAME = saved


def resolve_sandbox_root(target_root: os.PathLike | str | None) -> Optional[Path]:
    """Sandbox governance root from the explicit arg, else the env override,
    else None (= real mode => refused in this PREP build)."""
    raw = target_root if target_root is not None else os.environ.get(SANDBOX_ENV_VAR)
    if raw is None or str(raw).strip() == "":
        return None
    return Path(str(raw)).expanduser()


# ------------------------------------------------------------ (a) authority

def read_authority(
    registry_path: os.PathLike | str,
    cycle_id: str,
    *,
    worktree: str | None = None,
    measured_head: str | None = None,
    measured_branch: str | None = None,
    go_artifact: os.PathLike | str | None = None,
) -> dict:
    """Parse the REAL registry format and verify the cycle's execution
    authority. Returns the cycle row. Raises AuthorityError (pre-lock,
    fail closed) on any gap:

    - REGISTRY_UNREADABLE / malformed         (cycle_registry strict loader)
    - REGISTRY_ROW_MISSING                    cycle-id absent
    - HEAD_MISMATCH                           row.head != measured HEAD
                                              (incl. unmeasured placeholder)
    - BRANCH_MISMATCH                         row.branch != measured branch
    - LIFECYCLE_NOT_EXECUTABLE                not ACTIVE_LIGHT/ACTIVE_HEAVY
    - GO_MISSING / GO_CYCLE_MISMATCH /        GO_RECORDED.json verification
      GO_PHRASE_MISMATCH / TWO_KEY_INCOMPLETE (cycle BEFORE phrase; byte-
                                              exact phrase; two-key complete)

    Measurement law: when worktree is given and measured_* are not, HEAD and
    branch are MEASURED via git in that worktree — never guessed; a git
    failure raises HEAD_MISMATCH(kind=unmeasurable) rather than passing.
    """
    registry_path = str(registry_path)
    try:
        reg = cycle_registry.load(registry_path)
    except atomic_io.ControlStateDrift as exc:
        raise AuthorityError("REGISTRY_UNREADABLE",
                             {"registry": registry_path, "error": str(exc)}) from exc

    try:
        row = cycle_registry.resolve(reg, cycle_id)
    except cycle_registry.CycleNotFound:
        raise AuthorityError("REGISTRY_ROW_MISSING",
                             {"registry": registry_path, "cycle_id": cycle_id,
                              "registered": len(reg["cycles"])}) from None

    # ---- measured HEAD / branch (compare-against-measured, never assume) ---
    if measured_head is None and worktree:
        proc = subprocess.run(["git", "-C", str(worktree), "rev-parse", "HEAD"],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            raise AuthorityError("HEAD_MISMATCH", {
                "cycle_id": cycle_id, "kind": "unmeasurable",
                "worktree": str(worktree), "error": proc.stderr.strip()})
        measured_head = proc.stdout.strip()
    if measured_branch is None and worktree:
        proc = subprocess.run(["git", "-C", str(worktree), "rev-parse", "--abbrev-ref", "HEAD"],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            raise AuthorityError("BRANCH_MISMATCH", {
                "cycle_id": cycle_id, "kind": "unmeasurable",
                "worktree": str(worktree), "error": proc.stderr.strip()})
        measured_branch = proc.stdout.strip()

    if measured_head is not None:
        if row.get("head") == UNMEASURED_HEAD:
            raise AuthorityError("HEAD_MISMATCH", {
                "cycle_id": cycle_id, "kind": "unmeasured_placeholder",
                "row_head": row.get("head"), "measured_head": measured_head})
        if row.get("head") != measured_head:
            raise AuthorityError("HEAD_MISMATCH", {
                "cycle_id": cycle_id, "kind": "stale",
                "row_head": row.get("head"), "measured_head": measured_head})
    if measured_branch is not None and row.get("branch") != measured_branch:
        raise AuthorityError("BRANCH_MISMATCH", {
            "cycle_id": cycle_id, "row_branch": row.get("branch"),
            "measured_branch": measured_branch})

    if row.get("lifecycle") not in EXECUTABLE_LIFECYCLES:
        raise AuthorityError("LIFECYCLE_NOT_EXECUTABLE", {
            "cycle_id": cycle_id, "lifecycle": row.get("lifecycle"),
            "executable": list(EXECUTABLE_LIFECYCLES)})

    # ---- GO artifact (real convention: research/control/<CYCLE>/auth/) -----
    go_path = Path(go_artifact) if go_artifact is not None else (
        _CYCLE_DIR / "auth" / "GO_RECORDED.json")
    _verify_go_artifact(go_path, cycle_id, registered_phrase=row.get("go_phrase") or "")
    return row


def _verify_go_artifact(go_path: Path, cycle_id: str, *, registered_phrase: str) -> None:
    """GO verification per the real GO_RECORDED.json convention observed in
    research/control/<CYCLE>/auth/ (schema dev1_go_auth@1): cycle match is
    checked BEFORE the phrase; the typed phrase must be BYTE-equal to the
    canonical phrase (and to the registered phrase when the row carries one);
    the two_key object must carry BOTH key_1_a7 and key_2_owner_go."""
    if not go_path.is_file():
        raise AuthorityError("GO_MISSING", {"artifact": str(go_path),
                                            "cycle_id": cycle_id})
    try:
        go = json.loads(go_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AuthorityError("GO_MISSING", {
            "artifact": str(go_path), "error": f"unreadable/unparseable ({exc})"}) from exc
    if not isinstance(go, dict):
        raise AuthorityError("GO_MISSING", {"artifact": str(go_path),
                                            "error": "not a JSON object"})

    # cycle identity FIRST (a GO for another cycle must never leak its phrase)
    if go.get("cycle") != cycle_id and go.get("cycle_id") != cycle_id:
        raise AuthorityError("GO_CYCLE_MISMATCH", {
            "artifact": str(go_path),
            "go_cycle": go.get("cycle", go.get("cycle_id")),
            "expected": cycle_id})

    typed = go.get("go_phrase_typed")
    registered_in_go = go.get("go_phrase_registered")
    want = canonical_go_phrase(cycle_id)
    if typed != want:  # byte equality: no trim, no case-fold
        raise AuthorityError("GO_PHRASE_MISMATCH", {
            "artifact": str(go_path), "got": typed, "expected": want,
            "note": "paraphrase/alias dies unconsumed (byte-exact law)"})
    if registered_phrase and registered_phrase != want:
        raise AuthorityError("GO_PHRASE_MISMATCH", {
            "artifact": str(go_path), "registered_phrase": registered_phrase,
            "expected": want, "note": "registry row phrase contradicts canonical phrase"})
    if registered_in_go is not None and registered_in_go != typed:
        raise AuthorityError("GO_PHRASE_MISMATCH", {
            "artifact": str(go_path), "go_phrase_registered": registered_in_go,
            "go_phrase_typed": typed, "note": "GO artifact registered!=typed (match law)"})

    two_key = go.get("two_key")
    if not isinstance(two_key, dict):
        raise AuthorityError("TWO_KEY_INCOMPLETE", {
            "artifact": str(go_path), "error": "missing two_key object"})
    missing = [k for k in ("key_1_a7", "key_2_owner_go")
               if not two_key.get(k)]
    if missing:
        raise AuthorityError("TWO_KEY_INCOMPLETE", {
            "artifact": str(go_path), "missing": missing})


# ------------------------------------------------------- (b) canonical lock

@dataclass
class GuardedCanonicalLock:
    """Our hold on the canonical heavy lock. Delegates every operation to
    governance.heavy_lock (never reimplements flock)."""

    handle: heavy_lock.HeavyLockHandle
    cycle_id: str
    role: str
    runtime_dir: Path
    _abandoned: bool = False

    # -- post-acquire TOCTOU recheck (fresh read; every field must be ours) --
    def recheck(self) -> dict:
        with _sandbox_runtime(self.runtime_dir.parent):
            report = heavy_lock.inspect()
            row, err = heavy_lock._load_registry(self.handle.registry_path)
        expected = {
            "cycle_id": self.cycle_id,
            "role": self.role,
            "pid": os.getpid(),
            "process_start_token": heavy_lock.process_start_token(os.getpid()),
        }
        problems: list[str] = []
        if report["verdict"] != heavy_lock.VERDICT_HELD_PROVEN:
            problems.append(f"inspect verdict {report['verdict']} != HELD_PROVEN")
        if err is not None:
            problems.append(f"registry unreadable: {err}")
        elif row is None:
            problems.append("registry row vanished after acquire")
        else:
            for k, want in expected.items():
                if row.get(k) != want:
                    problems.append(f"registry field {k}={row.get(k)!r} != ours {want!r}")
        if problems:
            # drift abort: evidence preserved, never deleted; we give back
            # ONLY the OS flock we hold (the row bytes stay for inspection)
            self.abandon_preserving_row()
            raise CanonicalRefusal("LOCK_POSTACQUIRE_DRIFT", {
                "problems": problems, "row": row,
                "inspect_verdict": report["verdict"],
                "note": "post-acquire TOCTOU recheck failed; row preserved, "
                        "flock returned, never reclaimed by the worker"})
        return {"verdict": report["verdict"], "row": row}

    def abandon_preserving_row(self) -> None:
        """Release ONLY the OS flock; leave the registry row bytes untouched
        (drift evidence is preserved, never archived/rewritten by us)."""
        if self._abandoned:
            return
        import fcntl
        fcntl.flock(self.handle.fd, fcntl.LOCK_UN)
        os.close(self.handle.fd)
        self._abandoned = True

    def heartbeat(self, extra: dict | None = None) -> None:
        self.handle.heartbeat(extra)

    def release(self, status: str = "FINISHED", note: str = "") -> None:
        """Canonical release (registry terminal row + append-only history +
        unlink + flock unlock) — heavy_lock's own code."""
        if self._abandoned:
            raise heavy_lock.HeavyLockError("release after drift-abandon")
        self.handle.release(status=status, note=note)

    @property
    def released(self) -> bool:
        return self.handle._released

    @property
    def owner_row(self) -> dict:
        return dict(self.handle.owner)


def acquire_canonical_lock(
    cycle_id: str,
    role: str,
    worktree: str,
    command: list[str],
    expected_artifacts: list[str],
    *,
    target_root: os.PathLike | str | None = None,
    faults: set[str] | None = None,
) -> GuardedCanonicalLock:
    """Acquire the repo's canonical machine-wide heavy lock THROUGH
    governance.heavy_lock (imported — not reimplemented).

    Sandbox law: with F5SYM_GOVERNANCE_DIR (or target_root=) naming a sandbox
    governance dir, the SAME heavy_lock code path operates on the sandbox
    copy (scoped RUNTIME_DIRNAME redirection). Real mode is REFUSED in this
    PREP build before any real write/lock.

    Sequence: pre-inspect (FREE_PROVEN or refuse; HELD -> NOT_RUN_RESOURCE_
    CONFLICT) -> heavy_lock.acquire (its own TOCTOU under flock; busy ->
    LockBusyError; stale-proven row -> reclaim per canonical law) ->
    post-acquire recheck (fresh inspect HELD_PROVEN + every registry field
    ours; drift -> evidence preserved, flock returned, LOCK_POSTACQUIRE_DRIFT).
    """
    faults = set(faults or set())
    unknown = faults - KNOWN_FAULTS
    if unknown:
        raise CanonicalRefusal("BAD_FAULT_NAMES", {"unknown": sorted(unknown),
                                                   "known": sorted(KNOWN_FAULTS)})
    sandbox_root = resolve_sandbox_root(target_root)
    if sandbox_root is None:
        raise CanonicalRefusal("REAL_LOCK_ACQUIRE_REFUSED_PREP", {
            "cycle_id": cycle_id, "role": role,
            "real_runtime": REAL_HEAVY_RUNTIME,
            "todo": "owner authorization required: explicit owner instruction "
                    "naming this wrapper + a registered cycle row with typed GO "
                    "(see canonical/CANONICAL_INTEGRATION_V2.md NOT_RUN table)",
            "note": "PREP_BUILD hard-compiled refusal; no real lock was touched"})
    if is_real_governance_target(sandbox_root):
        raise CanonicalRefusal("REAL_LOCK_ACQUIRE_REFUSED_PREP", {
            "cycle_id": cycle_id, "role": role,
            "target_root": str(sandbox_root),
            "note": "target resolves to the real governance dir — refused "
                    "before any real write"})
    runtime = sandbox_root / "heavy_runtime"
    runtime.mkdir(parents=True, exist_ok=True)

    # 0. pre-check (refuse early, before any work is compiled)
    with _sandbox_runtime(sandbox_root):
        pre = heavy_lock.inspect()
    if pre["verdict"] == heavy_lock.VERDICT_DRIFT:
        raise CanonicalRefusal("CONTROL_STATE_DRIFT", {
            "phase": "pre_acquire", "evidence": pre["evidence"],
            "reason": pre.get("reason")})
    # HELD_PROVEN falls through to acquire() which raises LockBusyError with
    # the canonical holder detail — the authority stays heavy_lock's own.

    # 1. canonical acquire (flock + registry row written by heavy_lock)
    try:
        with _sandbox_runtime(sandbox_root):
            handle = heavy_lock.acquire(
                cycle_id=cycle_id, role=role, worktree=str(worktree),
                command=list(command), expected_artifacts=list(expected_artifacts))
    except heavy_lock.LockBusyError as exc:
        raise CanonicalLockBusy({
            "cycle_id": cycle_id, "role": role,
            "holder_detail": str(exc), "verdict": NOT_RUN_RESOURCE_CONFLICT}) from exc
    # HeavyLockError (canonical drift inside acquire) propagates as-is:
    # the canonical module's own fail-closed semantics, row preserved there.

    guard = GuardedCanonicalLock(handle=handle, cycle_id=cycle_id, role=role,
                                 runtime_dir=runtime)

    # test fault: inject a foreign RUNNING row after acquire, before recheck
    if "post_acquire_foreign_row" in faults:
        foreign = dict(handle.owner)
        foreign["cycle_id"] = "FOREIGN-CYCLE-INJECTED"
        foreign["role"] = "FOREIGN-ROLE"
        heavy_lock._atomic_write_json(handle.registry_path, foreign)

    # 2. post-acquire recheck (TOCTOU closure)
    guard.recheck()
    return guard


# ---------------------------------------------------- (c) guarded execution

def write_terminal_handoff(handoff_path: os.PathLike | str, payload: dict) -> str:
    body = dict(payload)
    body.setdefault("schema", HANDOFF_SCHEMA)
    return _atomic_write_json(handoff_path, body)


def execute_cycle_step(
    *,
    cycle_id: str,
    step_name: str,
    step_callable: Callable[[], dict],
    lock: GuardedCanonicalLock,
    expected_artifacts: list[str],
    final_status_path: os.PathLike | str,
    handoff_path: os.PathLike | str | None = None,
    handoff_payload: dict | None = None,
    ledger_paths: list[str] | None = None,
    faults: set[str] | None = None,
) -> dict:
    """One production cycle step INSIDE the canonical critical section.

    Laws enforced here (BUG1/BUG2 class, per freeze_wiring/CANONICAL_
    INTEGRATION.md §3 and the round's freeze_law):
    - the caller-supplied ``step_callable`` runs inside the lock;
    - an exception in the step => the lock release is ALWAYS attempted, the
      ledger must be untouched, terminal status FAILED non-zero;
    - the terminal handoff is written INSIDE the guarded path (before
      release); a raised handoff write => FAILED, no success token;
    - a raised RELEASE => FAILED non-zero even when the step completed
      (BUG1: a release failure is a finalization failure, never a success);
    - FINAL_STATUS.json is machine-readable and written on EVERY terminal
      path.

    Returns the outcome dict (also persisted to final_status_path).
    """
    faults = set(faults or set())
    started = _utcnow()
    digest = artifacts_digest(expected_artifacts)
    ledger_paths = list(ledger_paths or [])
    ledger_before = {p: _sha256_file(p) for p in ledger_paths}

    errors: list[dict] = []
    step_error: dict | None = None
    step_result: dict | None = None
    handoff_sha: str | None = None
    handoff_error: dict | None = None
    released = False
    release_error: dict | None = None
    abandoned = False

    try:
        step_result = step_callable()
    except Exception as exc:  # noqa: BLE001 — production wrapper records, never swallows
        step_error = {"type": type(exc).__name__, "message": str(exc)}
        errors.append({"phase": "step", **step_error})

    if step_error is None and handoff_path is not None:
        if "fail_handoff_write" in faults:
            handoff_error = {"type": "InjectedFault", "message": "fail_handoff_write"}
            errors.append({"phase": "handoff", **handoff_error})
        else:
            try:
                handoff_sha = write_terminal_handoff(handoff_path, dict(
                    handoff_payload or {},
                    cycle_id=cycle_id, step=step_name, status="FINISHED",
                    step_artifacts_digest=digest, written_utc=_utcnow()))
            except Exception as exc:  # noqa: BLE001
                handoff_error = {"type": type(exc).__name__, "message": str(exc)}
                errors.append({"phase": "handoff", **handoff_error})

    # release ALWAYS attempted (success, failure, or exception path)
    try:
        if "fail_release" in faults:
            raise heavy_lock.HeavyLockError("injected fail_release (BUG1-class proof)")
        lock.release(status="FINISHED" if not errors else "FAILED",
                     note=f"{step_name} step")
        released = True
    except Exception as exc:  # noqa: BLE001
        release_error = {"type": type(exc).__name__, "message": str(exc)}
        errors.append({"phase": "release", **release_error})

    ledger_after = {p: _sha256_file(p) for p in ledger_paths}
    ledger_drift = [p for p in ledger_paths if ledger_before[p] != ledger_after[p]]

    if errors or ledger_drift:
        status, exit_code = "FAILED", EXIT_FAILED
    else:
        status, exit_code = "FINISHED", EXIT_OK
    success = status == "FINISHED" and released and handoff_error is None

    outcome = {
        "schema": FINAL_STATUS_SCHEMA,
        "cycle_id": cycle_id,
        "step": step_name,
        "status": status,
        "exit_code": exit_code,
        "success": success,                      # the ONLY success token
        "step_artifacts_digest": digest,
        "expected_artifacts": list(expected_artifacts),
        "handoff": ({"path": str(handoff_path), "sha256": handoff_sha}
                    if handoff_sha else None),
        "released": released,
        "release_error": release_error,
        "step_error": step_error,
        "handoff_error": handoff_error,
        "step_result": step_result,
        "ledger_untouched": not ledger_drift,
        "ledger_drift": ledger_drift,
        "errors": errors,
        "started_utc": started,
        "finished_utc": _utcnow(),
    }
    _atomic_write_json(final_status_path, outcome)
    return outcome


# ---------------------------------------------------- (d) registry CAS write

def registry_cas_update(
    *,
    registry_path: os.PathLike | str,
    cycle_id: str,
    prev_sha: str,
    head: str | None = None,
    lifecycle: str | None = None,
    phase: str | None = None,
    workers: int | None = None,
    active_heavy: bool | None = None,
    reason: str = "canonical step update",
) -> dict:
    """Measured-HEAD / lifecycle update through the CANONICAL CAS writer
    (governance.cycle_registry.update_cycle: validate -> CAS on prev sha ->
    journal events -> projection regeneration).

    Real mode is REFUSED in this PREP build (REGISTRY_WRITE_REAL_REFUSED,
    hard-compiled) BEFORE any read-modify-write of the real file. Sandbox
    registries (same cycle_registry@1 schema) go through the identical code
    path. A concurrent writer fails closed as CAS_MISMATCH with no partial
    write (governance.atomic_io CAS law).
    """
    if is_real_governance_target(registry_path):
        raise CanonicalRefusal("REGISTRY_WRITE_REAL_REFUSED", {
            "registry": str(registry_path), "cycle_id": cycle_id,
            "prep_build": PREP_BUILD,
            "todo": "owner authorization required: explicit owner instruction "
                    "lifting the PREP build law + a registered cycle row with "
                    "typed GO (see canonical/CANONICAL_INTEGRATION_V2.md NOT_RUN)",
            "note": "refused before any read-modify-write; real registry untouched"})
    try:
        reg = cycle_registry.load(registry_path)
    except atomic_io.ControlStateDrift as exc:
        raise CanonicalRefusal("REGISTRY_UNREADABLE", {
            "registry": str(registry_path), "error": str(exc)}) from exc
    try:
        changes, new_sha = cycle_registry.update_cycle(
            registry_path, reg, prev_sha=prev_sha, cycle_id=cycle_id,
            head=head, lifecycle=lifecycle, phase=phase, workers=workers,
            active_heavy=active_heavy, reason=reason)
    except atomic_io.ControlStateDrift as exc:
        raise CanonicalRefusal("CAS_MISMATCH", {
            "registry": str(registry_path), "cycle_id": cycle_id,
            "error": str(exc), "note": "concurrent writer detected — no partial "
                                       "write (atomic_io CAS law)"}) from exc
    return {"changes": changes, "registry_sha256": new_sha,
            "registry": str(registry_path), "cycle_id": cycle_id}


# --------------------------------------------------------- convenience run

def run_protected_step(
    *,
    registry_path: os.PathLike | str,
    cycle_id: str,
    role: str,
    worktree: str,
    command: list[str],
    expected_artifacts: list[str],
    step_callable: Callable[[], dict],
    final_status_path: os.PathLike | str,
    handoff_path: os.PathLike | str | None = None,
    handoff_payload: dict | None = None,
    ledger_paths: list[str] | None = None,
    measured_head: str | None = None,
    measured_branch: str | None = None,
    go_artifact: os.PathLike | str | None = None,
    target_root: os.PathLike | str | None = None,
    faults: set[str] | None = None,
) -> dict:
    """The exact production sequence of CANONICAL_INTEGRATION §3 as one call:
    authority -> acquire -> post-acquire recheck -> guarded step -> CAS
    registry update. Refusals return machine-readable outcomes (and write
    FINAL_STATUS.json — machine-readable on EVERY terminal path) with the
    canonical exit codes (0/2/3/75); they never raise past this function."""
    started = _utcnow()

    def _refusal(status_label: str, exit_code: int, code: str, detail: dict) -> dict:
        outcome = {
            "schema": FINAL_STATUS_SCHEMA,
            "cycle_id": cycle_id, "step": "cycle_step",
            "status": status_label, "exit_code": exit_code, "success": False,
            "code": code, "detail": detail, "errors": [{"phase": "preflight",
                                                        "code": code}],
            "started_utc": started, "finished_utc": _utcnow(),
        }
        _atomic_write_json(final_status_path, outcome)
        return outcome

    try:
        row = read_authority(registry_path, cycle_id, worktree=worktree,
                             measured_head=measured_head,
                             measured_branch=measured_branch,
                             go_artifact=go_artifact)
    except AuthorityError as exc:
        return _refusal("REFUSED", EXIT_REFUSED, exc.code, exc.detail)
    try:
        guard = acquire_canonical_lock(cycle_id, role, worktree, command,
                                       expected_artifacts, target_root=target_root,
                                       faults=faults)
    except CanonicalLockBusy as exc:
        return _refusal(NOT_RUN_RESOURCE_CONFLICT, EXIT_CONFLICT, exc.verdict, exc.detail)
    except CanonicalRefusal as exc:
        return _refusal("REFUSED", EXIT_REFUSED, exc.code, exc.detail)

    outcome = execute_cycle_step(
        cycle_id=cycle_id, step_name="cycle_step", step_callable=step_callable,
        lock=guard, expected_artifacts=expected_artifacts,
        final_status_path=final_status_path, handoff_path=handoff_path,
        handoff_payload=handoff_payload, ledger_paths=ledger_paths, faults=faults)

    if outcome["success"]:
        try:
            prev_sha = _sha256_file(registry_path)
            cas = registry_cas_update(
                registry_path=registry_path, cycle_id=cycle_id, prev_sha=prev_sha or "",
                phase="step executed under canonical lock",
                reason="canonical step completion")
            outcome["registry_cas"] = cas
        except CanonicalRefusal as exc:
            # a failed post-step registry update is a finalization failure:
            # the run is FAILED non-zero even though the step itself completed
            outcome["status"], outcome["exit_code"], outcome["success"] = "FAILED", EXIT_FAILED, False
            outcome["errors"].append({"phase": "registry_cas", "code": exc.code,
                                      "detail": exc.detail})
            _atomic_write_json(final_status_path, outcome)
    outcome["authority_row_lifecycle"] = row.get("lifecycle")
    return outcome
