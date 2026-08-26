"""V10 authoritative worker controller (sprint V9H H01/H02/H03/H04).

One Python controller owns every research worker: dedicated process group,
atomic heartbeat, exact-group timeout escalation, identity-based resume and
fail-closed completion truth.

Terminal states are EXACTLY (H02):
    COMPLETED | FAILED_INCOMPLETE | TIMED_OUT | SIGNALLED |
    CONTROLLER_LOST | UNKNOWN_EXTERNAL_KILL | PARTIAL_PRE_SCORE

Completion truth: exit 0 alone is never COMPLETED.  COMPLETED requires
exit==0 AND a caller-supplied artifact verifier returning a positive verdict
AND the terminal marker file written LAST, after verification.  Missing or
failing verification is FAILED_INCOMPLETE.

Classification of abnormal deaths (waitpid status vs our own sent signals):
* we escalated after frozen timeout            -> TIMED_OUT
* controller stop() killed the worker          -> SIGNALLED (we caused it)
* unexplained SIGKILL we did NOT send          -> UNKNOWN_EXTERNAL_KILL
  (never labelled "OOM"; memory pressure is only ever an evidence-backed
  inference field, recorded as None unless a real probe supplied it)
* other signal deaths                          -> SIGNALLED
* died after BASE marker, before STRESS marker -> PARTIAL_PRE_SCORE
  (base execution ending is not pipeline completion)
* controller crash/restart, no terminal record -> CONTROLLER_LOST

No pgrep/pkill/name matching anywhere.  Identity is
(pid, posix start identity `ps -o lstart=`, sha256 of exact argv, worktree).
Resume matches the full identity; PID alone is insufficient.

Every subprocess is spawned with ``start_new_session=True`` (own PGID) and a
NON-NULL frozen timeout.  stdout/stderr are streamed by reader threads into
timestamped log files under ``<output_dir>/logs/``, updating
``last_log_at_utc``; logs rotate at 50 MB keeping a tail.  All JSON writes
(worker record, heartbeat, terminal marker) are tmp + fsync + os.replace.
"""

from __future__ import annotations

import argparse
import datetime as dt
import errno
import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

try:  # pragma: no cover - trivial import guard
    import resource
except ImportError:  # pragma: no cover - non-posix
    resource = None  # type: ignore[assignment]

TERMINAL_STATES: Tuple[str, ...] = (
    "COMPLETED",
    "FAILED_INCOMPLETE",
    "TIMED_OUT",
    "SIGNALLED",
    "CONTROLLER_LOST",
    "UNKNOWN_EXTERNAL_KILL",
    "PARTIAL_PRE_SCORE",
)
ACTIVE_STATE = "RUNNING"

PHASES: Tuple[str, ...] = ("PREPARE", "BASE", "STRESS", "FINALIZE", "REPRODUCE")

DEFAULT_HEARTBEAT_INTERVAL_S = 15.0
DEFAULT_POLL_INTERVAL_S = 1.0
DEFAULT_TERM_GRACE_S = 30.0
STALE_HEARTBEAT_THRESHOLD_S = 45.0
STDERR_TAIL_BYTES = 8192
IDENTITY_PROBE_TIMEOUT_S = 5.0
LOG_ROTATE_BYTES = 50 * 1024 * 1024
LOG_TAIL_KEEP_BYTES = 5 * 1024 * 1024
PUMP_JOIN_TIMEOUT_S = 10.0

VerifierResult = Union[bool, Dict[str, Any]]
ArtifactVerifier = Callable[[Dict[str, Any]], VerifierResult]
MarkerCheck = Union[str, Path, Callable[[], bool], None]

_VERIFIER_KEY_OK = "ok"


class ControllerError(RuntimeError):
    """Base error for controller misuse."""


class IdentityMismatchError(ControllerError):
    """Resume/match rejected because recorded identity fields disagree."""

    def __init__(self, trial_id: str, mismatches: Dict[str, Tuple[Any, Any]]) -> None:
        detail = ", ".join(
            f"{field}: recorded={want!r} given={got!r}"
            for field, (want, got) in sorted(mismatches.items())
        )
        super().__init__(f"identity mismatch for trial {trial_id!r}: {detail}")
        self.trial_id = trial_id
        self.mismatches = mismatches


class UnknownTrialError(ControllerError):
    """No record for the requested trial id in the state dir."""


def utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())


def _parse_utc(stamp: str) -> Optional[dt.datetime]:
    try:
        parsed = dt.datetime.fromisoformat(str(stamp))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write JSON atomically: tmp file -> fsync -> os.replace -> fsync dir.

    An interrupted write leaves the previous file intact and parseable: the
    payload lands in a fresh uniquely-named tmp file first and the visible
    path is only ever swapped by os.replace (atomic on POSIX).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp_path, path)
    _fsync_dir(path.parent)


def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Parse a JSON file; corrupt/partial files are ignored safely (None)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def command_hash(argv: Sequence[str]) -> str:
    joined = b"\x00".join(arg.encode("utf-8") for arg in argv)
    return hashlib.sha256(joined).hexdigest()


def ps_identity(pid: int) -> Optional[Tuple[str, int]]:
    """Return (lstart string, pgid) for pid via ps, else None.

    This is the /proc-equivalent identity probe on macOS; both values must
    match the recorded ones for a live-process match.  Exact-pid probing
    only -- broad/name matching is forbidden (H01).
    """
    try:
        proc = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart=", "-o", "pgid="],
            capture_output=True,
            text=True,
            timeout=IDENTITY_PROBE_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    # e.g. "Wed Aug 26 19:33:01 2026     4242" -> lstart is every token but
    # the last; the final token is the pgid.
    fields = proc.stdout.split()
    if len(fields) < 6:
        return None
    try:
        pgid = int(fields[-1])
    except ValueError:
        return None
    lstart = " ".join(fields[:-1])
    return lstart, pgid


def ps_lstart(pid: int) -> Optional[str]:
    identity = ps_identity(pid)
    return identity[0] if identity else None


def _rss_kb_via_ps(pid: int) -> Optional[int]:
    try:
        proc = subprocess.run(
            ["ps", "-p", str(pid), "-o", "rss="],
            capture_output=True,
            text=True,
            timeout=IDENTITY_PROBE_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    text = proc.stdout.strip()
    if not text:
        return None
    try:
        return int(text.split()[0])
    except (ValueError, IndexError):
        return None


def _children_peak_rss_kb_fallback() -> Optional[int]:
    """Best-effort rusage children max-rss (darwin reports bytes here)."""
    if resource is None or not hasattr(resource, "getrusage"):
        return None
    if not hasattr(resource, "RUSAGE_CHILDREN"):
        return None
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    max_rss = ru.ru_maxrss
    if max_rss <= 0:
        return None
    if sys.platform == "darwin":
        # macOS reports bytes here; Linux reports KiB.
        return max_rss // 1024
    return int(max_rss)


def tail_file(path: Path, limit_bytes: int = STDERR_TAIL_BYTES) -> str:
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - limit_bytes))
            return handle.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def _eval_marker(marker: MarkerCheck) -> bool:
    if marker is None:
        return False
    if isinstance(marker, (str, Path)):
        return Path(str(marker)).exists()
    return bool(marker())


def _normalize_verdict(raw: VerifierResult) -> Dict[str, Any]:
    if isinstance(raw, bool):
        return {"ok": raw, "detail": {}}
    if isinstance(raw, dict):
        ok = raw.get(_VERIFIER_KEY_OK)
        if isinstance(ok, bool):
            return {"ok": ok, "detail": raw}
        return {
            "ok": False,
            "detail": {"error": "verifier dict missing boolean 'ok'", "raw": repr(raw)[:500]},
        }
    return {"ok": False, "detail": {"error": f"unsupported verifier result {type(raw).__name__}"}}


class TailRotatingLog:
    """Append-only timestamped line log bounded at ``max_bytes``.

    When the file exceeds ``max_bytes`` it is rotated IN PLACE keeping only
    the last ``keep_tail_bytes`` (tail preservation): the tail is copied to a
    tmp file, fsynced, then os.replace'd over the live path.  Only the writer
    thread touches an instance; a lock guards rotation against close().
    """

    def __init__(
        self,
        path: Union[str, Path],
        *,
        max_bytes: int = LOG_ROTATE_BYTES,
        keep_tail_bytes: int = LOG_TAIL_KEEP_BYTES,
    ) -> None:
        self.path = Path(path)
        if max_bytes <= 0 or keep_tail_bytes <= 0:
            raise ValueError("max_bytes and keep_tail_bytes must be positive")
        self.max_bytes = int(max_bytes)
        self.keep_tail_bytes = int(keep_tail_bytes)
        self.rotations = 0
        self.bytes_written = 0
        self._lock = threading.Lock()
        self._closed = False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "ab")
        self._size = self._fh.tell()

    def write_line(self, raw: bytes) -> None:
        text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
        stamped = f"{utc_now_iso()} {text}\n".encode("utf-8")
        with self._lock:
            if self._closed:
                return
            self._fh.write(stamped)
            self._fh.flush()
            self._size += len(stamped)
            self.bytes_written += len(stamped)
            if self._size >= self.max_bytes:
                self._rotate_locked()

    def _rotate_locked(self) -> None:
        self._fh.close()
        tail = b""
        try:
            with open(self.path, "rb") as src:
                src.seek(max(0, self._size - self.keep_tail_bytes))
                tail = src.read()
        except OSError:
            tail = b""
        tmp_path = self.path.with_name(f".{self.path.name}.{uuid.uuid4().hex}.tmp")
        with open(tmp_path, "wb") as dst:
            dst.write(tail)
            dst.flush()
            os.fsync(dst.fileno())
        os.replace(tmp_path, self.path)
        _fsync_dir(self.path.parent)
        self._fh = open(self.path, "ab")
        self._size = self._fh.tell()
        self.rotations += 1

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                try:
                    self._fh.flush()
                    self._fh.close()
                except OSError:
                    pass
                self._closed = True


def _pump_stream(pipe: Any, log_writer: TailRotatingLog, key: str, log_state: Dict[str, Any]) -> None:
    """Reader-thread body: stream one child pipe into its rotating log."""
    try:
        for raw in iter(pipe.readline, b""):
            log_writer.write_line(raw)
            log_state[key] = log_state.get(key, 0) + len(raw)
            log_state["last_log_at_utc"] = utc_now_iso()
    except (OSError, ValueError):
        pass
    finally:
        try:
            pipe.close()
        except OSError:
            pass


class WorkerController:
    """Authoritative supervisor for research workers (one state dir)."""

    def __init__(
        self,
        state_dir: Union[str, Path],
        *,
        poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
        heartbeat_interval_s: float = DEFAULT_HEARTBEAT_INTERVAL_S,
        term_grace_s: float = DEFAULT_TERM_GRACE_S,
    ) -> None:
        if poll_interval_s <= 0 or heartbeat_interval_s <= 0:
            raise ValueError("poll_interval_s and heartbeat_interval_s must be positive")
        if term_grace_s <= 0:
            raise ValueError("term_grace_s must be positive")
        self.state_dir = Path(state_dir)
        self.records_dir = self.state_dir / "records"
        self.heartbeats_dir = self.state_dir / "heartbeats"
        self.terminal_dir = self.state_dir / "terminal"
        self.poll_interval_s = float(poll_interval_s)
        self.heartbeat_interval_s = float(heartbeat_interval_s)
        self.term_grace_s = float(term_grace_s)
        # Per-trial cooperative stop requests so the supervise loop -- the
        # single owner of the Popen -- is always the one to escalate/reap.
        self._stop_events: Dict[str, threading.Event] = {}

    def _register_stop_event(self, trial_id: str) -> threading.Event:
        event = threading.Event()
        self._stop_events[str(trial_id)] = event
        return event

    def _release_stop_event(self, trial_id: str) -> None:
        self._stop_events.pop(str(trial_id), None)

    # ------------------------------------------------------------------ paths
    def record_path(self, trial_id: str) -> Path:
        return self.records_dir / f"{trial_id}.json"

    def heartbeat_path(self, trial_id: str) -> Path:
        return self.heartbeats_dir / f"{trial_id}.json"

    def terminal_path(self, trial_id: str) -> Path:
        return self.terminal_dir / f"{trial_id}.json"

    # ------------------------------------------------------------- record I/O
    def load_record(self, trial_id: str) -> Dict[str, Any]:
        payload = load_json_safe(self.record_path(trial_id))
        if payload is None:
            raise UnknownTrialError(f"no readable record for trial {trial_id!r}")
        return payload

    def load_records(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if not self.records_dir.is_dir():
            return records
        for path in sorted(self.records_dir.glob("*.json")):
            payload = load_json_safe(path)
            if payload is not None and payload.get("trial_id"):
                records.append(payload)
        return records

    def _save_record(self, record: Dict[str, Any]) -> None:
        atomic_write_json(self.record_path(str(record["trial_id"])), record)

    @staticmethod
    def is_terminal(record: Dict[str, Any]) -> bool:
        state = record.get("terminal_state")
        return state is not None and state in TERMINAL_STATES

    # ------------------------------------------------------------ phase order
    def advance_phase(self, trial_id: str, phase: str) -> Dict[str, Any]:
        """Persist entry into ``phase`` BEFORE the caller enters it.

        Enforces the strict sequence PREPARE->BASE->STRESS->FINALIZE->
        REPRODUCE; the appended ``phases_entered`` list is what later lets the
        controller distinguish PARTIAL_PRE_SCORE from clean failures.
        """
        if phase not in PHASES:
            raise ValueError(f"phase must be one of {PHASES}, got {phase!r}")
        record = self.load_record(trial_id)
        entered = list(record.get("phases_entered", []))
        next_index = len(entered)
        want = PHASES[next_index] if next_index < len(PHASES) else None
        if want != phase:
            raise ControllerError(
                f"trial {trial_id!r} phase sequence violation: expected {want!r}, got {phase!r}"
            )
        entered.append(phase)
        record["phases_entered"] = entered
        record["phase"] = phase
        record.setdefault("markers", {})["phase_advanced_utc"] = utc_now_iso()
        self._save_record(record)
        return record

    # ------------------------------------------------------------------ spawn
    def spawn(
        self,
        cmd_argv: Sequence[str],
        *,
        trial_id: str,
        launch_sha: str,
        worktree: Union[str, Path],
        output_dir: Union[str, Path],
        timeout_s: float,
        phase: str = "PREPARE",
        artifact_verifier: Optional[ArtifactVerifier] = None,
        base_marker: MarkerCheck = None,
        stress_marker: MarkerCheck = None,
        env_extra: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Spawn cmd_argv as a dedicated process group and supervise to terminal.

        timeout_s must be non-null (H03/H08-11): production timeouts are
        frozen; ``None`` is rejected here at the API boundary.
        """
        if not cmd_argv:
            raise ValueError("cmd_argv must be non-empty")
        if phase not in PHASES:
            raise ValueError(f"phase must be one of {PHASES}, got {phase!r}")
        if timeout_s is None or float(timeout_s) <= 0:
            raise ValueError("timeout_s must be non-null and positive (frozen contract)")
        existing = load_json_safe(self.record_path(trial_id))
        if existing is not None:
            raise ControllerError(f"trial {trial_id!r} already has a record")

        out_dir = Path(output_dir)
        logs_dir = out_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        out_log = TailRotatingLog(logs_dir / "worker_stdout.log")
        err_log = TailRotatingLog(logs_dir / "worker_stderr.log")
        log_state: Dict[str, Any] = {"last_log_at_utc": None}
        env = os.environ.copy()
        if env_extra:
            env.update(env_extra)
        try:
            proc = subprocess.Popen(  # noqa: S603 - argv list form, no shell
                list(cmd_argv),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                start_new_session=True,  # dedicated PGID (H03)
                cwd=str(worktree),
                env=env,
            )
        except BaseException:
            out_log.close()
            err_log.close()
            raise
        pump_threads = [
            threading.Thread(
                target=_pump_stream, args=(proc.stdout, out_log, "stdout_bytes", log_state),
                daemon=True, name=f"pump-stdout-{trial_id}",
            ),
            threading.Thread(
                target=_pump_stream, args=(proc.stderr, err_log, "stderr_bytes", log_state),
                daemon=True, name=f"pump-stderr-{trial_id}",
            ),
        ]
        for thread in pump_threads:
            thread.start()

        spawned_iso = utc_now_iso()
        identity: Optional[Tuple[str, int]] = None
        deadline = time.monotonic() + IDENTITY_PROBE_TIMEOUT_S
        while identity is None and time.monotonic() < deadline:
            identity = ps_identity(proc.pid)
            if identity is None:
                time.sleep(0.05)
        lstart = identity[0] if identity else ""
        pgid = identity[1] if identity else proc.pid

        record: Dict[str, Any] = {
            "trial_id": trial_id,
            "pid": proc.pid,
            "pgid": pgid,
            "posix_start_identity": lstart,
            "command_hash": command_hash(cmd_argv),
            "command_argv": list(cmd_argv),
            "launch_sha": launch_sha,
            "worktree": str(worktree),
            "output_dir": str(out_dir),
            "phase": phase,
            "started_at_utc": spawned_iso,
            "last_heartbeat_utc": spawned_iso,
            "last_log_at_utc": None,
            "exit_code": None,
            "exit_signal": None,
            "peak_rss_kb": None,
            "peak_rss_bytes": None,
            "terminal_state": ACTIVE_STATE,
            "artifact_verification": {},
            "log_paths": {"stdout": str(out_log.path), "stderr": str(err_log.path)},
            "log_stats": {"rotations_stdout": 0, "rotations_stderr": 0},
            "phases_entered": [phase],
            "markers": {"base_reached": False, "stress_reached": False},
            "evidence": {},
            "supervision": {
                "controller_pid": os.getpid(),
                "started_utc": spawned_iso,
                "resumed": False,
                "last_action": "spawn",
            },
            "timestamps": {"spawned": spawned_iso, "last_heartbeat": spawned_iso},
        }
        self._save_record(record)
        started_monotonic = time.monotonic()
        stop_event = self._register_stop_event(trial_id)
        self._write_heartbeat(record, started_monotonic=started_monotonic, log_state=log_state)
        try:
            self._supervise_loop(
                record,
                proc=proc,
                timeout_s=float(timeout_s),
                artifact_verifier=artifact_verifier,
                base_marker=base_marker,
                stress_marker=stress_marker,
                started_monotonic=started_monotonic,
                log_state=log_state,
                stop_event=stop_event,
            )
        finally:
            self._release_stop_event(trial_id)
            for thread in pump_threads:
                thread.join(timeout=PUMP_JOIN_TIMEOUT_S)
            out_log.close()
            err_log.close()
            record["log_stats"] = {
                "stdout_bytes": int(log_state.get("stdout_bytes", 0)),
                "stderr_bytes": int(log_state.get("stderr_bytes", 0)),
                "rotations_stdout": out_log.rotations,
                "rotations_stderr": err_log.rotations,
            }
            record["last_log_at_utc"] = log_state.get("last_log_at_utc")
            if self.is_terminal(record):
                self._save_record(record)
        return self.load_record(trial_id)

    # ---------------------------------------------------------------- resume
    def match(
        self,
        *,
        pid: int,
        posix_start_identity: str,
        command_hash_hex: str,
        worktree: Union[str, Path],
        trial_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Match a worker record by full identity; reject mismatches explicitly.

        Every provided field must equal the recorded one.  PID alone is
        intentionally insufficient (H01): a reused PID with a different
        posix start identity or command hash raises IdentityMismatchError.
        """
        candidates: List[Dict[str, Any]] = []
        if trial_id is not None:
            candidates.append(self.load_record(trial_id))
        else:
            candidates = [r for r in self.load_records() if not self.is_terminal(r)]
        matches: List[Dict[str, Any]] = []
        mismatches_by_trial: Dict[str, Dict[str, Tuple[Any, Any]]] = {}
        for record in candidates:
            bad: Dict[str, Tuple[Any, Any]] = {}
            pairs = (
                ("pid", (record.get("pid"), pid)),
                ("posix_start_identity", (record.get("posix_start_identity"), posix_start_identity)),
                ("command_hash", (record.get("command_hash"), command_hash_hex)),
                ("worktree", (record.get("worktree"), str(worktree))),
            )
            for field, (want, got) in pairs:
                if want != got:
                    bad[field] = (want, got)
            if bad:
                mismatches_by_trial[str(record.get("trial_id"))] = bad
            else:
                matches.append(record)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            ids = sorted(str(m.get("trial_id")) for m in matches)
            raise ControllerError(f"identity matched multiple trials {ids}; refusing ambiguous adopt")
        if mismatches_by_trial:
            first_trial = sorted(mismatches_by_trial)[0]
            raise IdentityMismatchError(first_trial, mismatches_by_trial[first_trial])
        raise UnknownTrialError("no record matches the supplied identity")

    def resume(
        self,
        *,
        pid: int,
        posix_start_identity: str,
        command_hash_hex: str,
        worktree: Union[str, Path],
        timeout_s: float,
        trial_id: Optional[str] = None,
        artifact_verifier: Optional[ArtifactVerifier] = None,
        base_marker: MarkerCheck = None,
        stress_marker: MarkerCheck = None,
    ) -> Dict[str, Any]:
        """Adopt a matching live worker and supervise it to a terminal state.

        The caller re-freezes timeout_s (still non-null); identity is
        re-verified LIVE via ps before adoption.  A non-terminal record whose
        process can no longer be matched is reconciled honestly to
        CONTROLLER_LOST (supervision was interrupted; nothing else may be
        claimed about the death).
        """
        if timeout_s is None or float(timeout_s) <= 0:
            raise ValueError("timeout_s must be non-null and positive (frozen contract)")
        record = self.match(
            pid=pid,
            posix_start_identity=posix_start_identity,
            command_hash_hex=command_hash_hex,
            worktree=worktree,
            trial_id=trial_id,
        )
        if self.is_terminal(record):
            return record
        if str(record["trial_id"]) in self._stop_events:
            raise ControllerError(
                f"trial {record['trial_id']!r} is already supervised in-process; "
                "use stop() instead of resume()"
            )
        live = ps_identity(int(record["pid"]))
        if live is None or live[0] != record.get("posix_start_identity"):
            record = self._classify_unmatchable_after_restart(record)
            return self.load_record(str(record["trial_id"]))
        record["supervision"]["resumed"] = True
        record["supervision"]["controller_pid"] = os.getpid()
        record["supervision"]["last_action"] = "resume_adopt"
        record["supervision"]["resumed_utc"] = utc_now_iso()
        self._save_record(record)
        stop_event = self._register_stop_event(str(record["trial_id"]))
        try:
            self._supervise_loop(
                record,
                proc=None,
                timeout_s=float(timeout_s),
                artifact_verifier=artifact_verifier,
                base_marker=base_marker,
                stress_marker=stress_marker,
                started_monotonic=time.monotonic(),
                adopted=True,
                stop_event=stop_event,
            )
        finally:
            self._release_stop_event(str(record["trial_id"]))
        return self.load_record(str(record["trial_id"]))

    def reconcile_all(self) -> List[Dict[str, Any]]:
        """Post-crash reconciliation: every non-terminal record whose process
        cannot be identity-matched becomes CONTROLLER_LOST (no death cause is
        invented; last-heartbeat age is preserved as evidence)."""
        reconciled: List[Dict[str, Any]] = []
        for record in self.load_records():
            if self.is_terminal(record):
                continue
            if self._alive_by_identity(record):
                continue
            reconciled.append(self._classify_unmatchable_after_restart(record))
        return reconciled

    def _classify_unmatchable_after_restart(self, record: Dict[str, Any]) -> Dict[str, Any]:
        hb_age = self.heartbeat_age_s(str(record["trial_id"]), record=record)
        record["terminal_state"] = "CONTROLLER_LOST"
        record.setdefault("evidence", {}).update(
            {
                "reason": "process identity unmatchable after controller restart/reconciliation",
                "identity_probe": ps_identity(int(record.get("pid", -1))),
                "last_heartbeat_age_s": hb_age,
                "memory_pressure_evidence": None,
            }
        )
        record["exit_code"] = None
        self._save_record(record)
        atomic_write_json(self.terminal_path(str(record["trial_id"])), self._terminal_payload(record))
        return record

    # -------------------------------------------------------------- heartbeat
    def _write_heartbeat(
        self,
        record: Dict[str, Any],
        *,
        started_monotonic: float,
        log_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        alive = self._alive_by_identity(record)
        now_iso = utc_now_iso()
        elapsed = max(0.0, time.monotonic() - started_monotonic)
        if log_state is not None and log_state.get("last_log_at_utc"):
            record["last_log_at_utc"] = log_state["last_log_at_utc"]
        payload = {
            "trial_id": record["trial_id"],
            "phase": record["phase"],
            "elapsed_s": round(elapsed, 3),
            "pid_alive_by_identity": alive,
            "pid": record["pid"],
            "pgid": record["pgid"],
            "last_log_at_utc": record.get("last_log_at_utc"),
            "heartbeat_utc": now_iso,
        }
        record["timestamps"]["last_heartbeat"] = now_iso
        record["last_heartbeat_utc"] = now_iso
        record["heartbeat"] = payload
        atomic_write_json(self.heartbeat_path(str(record["trial_id"])), payload)
        self._save_record(record)

    def _alive_by_identity(self, record: Dict[str, Any]) -> bool:
        identity = ps_identity(int(record["pid"]))
        if identity is None:
            return False
        lstart, pgid = identity
        return lstart == record.get("posix_start_identity") and pgid == int(record.get("pgid", -1))

    def heartbeat_age_s(self, trial_id: str, record: Optional[Dict[str, Any]] = None) -> Optional[float]:
        rec = record if record is not None else self.load_record(trial_id)
        stamp = rec.get("last_heartbeat_utc") or rec.get("timestamps", {}).get("last_heartbeat")
        if not stamp:
            hb = load_json_safe(self.heartbeat_path(trial_id))
            stamp = hb.get("heartbeat_utc") if hb else None
        if not stamp:
            return None
        parsed = _parse_utc(stamp)
        if parsed is None:
            return None
        return max(0.0, (dt.datetime.now(dt.timezone.utc) - parsed).total_seconds())

    def last_log_age_s(self, record: Dict[str, Any]) -> Optional[float]:
        stamp = record.get("last_log_at_utc")
        if not stamp:
            return None
        parsed = _parse_utc(stamp)
        if parsed is None:
            return None
        return max(0.0, (dt.datetime.now(dt.timezone.utc) - parsed).total_seconds())

    def stale_heartbeat(
        self, trial_id: str, *, threshold_s: float = STALE_HEARTBEAT_THRESHOLD_S
    ) -> Dict[str, Any]:
        """Report staleness ONLY.  A stale heartbeat NEVER invents death."""
        record = self.load_record(trial_id)
        age = self.heartbeat_age_s(trial_id, record=record)
        stale = age is not None and age > threshold_s and not self.is_terminal(record)
        return {
            "trial_id": trial_id,
            "heartbeat_age_s": age,
            "stale": stale,
            "threshold_s": threshold_s,
            "warning": "HEARTBEAT_STALE — may be alive" if stale else None,
            "terminal_state": record.get("terminal_state"),
        }

    # ------------------------------------------------------------------- stop
    def stop(self, trial_id: str, *, reason: str = "controller_stop") -> Dict[str, Any]:
        """Graceful stop of the exact recorded group (TERM then KILL).

        When an in-process supervise loop owns this worker it performs the
        escalation itself (single owner of the Popen -- no reap races); the
        resulting death classifies as SIGNALLED because this controller sent
        it.  Cross-process stops fall back to direct ownership.
        """
        record = self.load_record(trial_id)
        if self.is_terminal(record):
            return record
        pgid = int(record["pgid"])
        if pgid <= 1:
            raise ControllerError(f"refusing suspicious pgid {pgid} for trial {trial_id!r}")
        event = self._stop_events.get(str(trial_id))
        if event is not None:
            event.set()
            deadline = time.monotonic() + max(60.0, self.term_grace_s * 2 + 10.0)
            while time.monotonic() < deadline:
                current = self.load_record(trial_id)
                if self.is_terminal(current):
                    return current
                time.sleep(0.05)
            raise ControllerError(f"supervise loop did not honour stop request for {trial_id!r}")
        # Fallback: no in-process supervisor (e.g. CLI stop after restart).
        evidence: Dict[str, Any] = {"reason": reason}
        self._escalate_and_reap(record, evidence, term_first=True)
        record["evidence"].update(evidence)
        self._finalize(
            record,
            artifact_verifier=None,
            base_marker=None,
            stress_marker=None,
            classification_basis={
                "kind": "stopped_by_controller",
                "controller_sent_signals": True,
            },
        )
        return self.load_record(trial_id)

    # ------------------------------------------------------------ supervise
    def _sample_peak_rss(self, record: Dict[str, Any], current_peak_kb: Optional[int]) -> Optional[int]:
        sample = _rss_kb_via_ps(int(record["pid"]))
        if sample is None:
            sample = _children_peak_rss_kb_fallback()
        if sample is None:
            return current_peak_kb
        return sample if current_peak_kb is None else max(current_peak_kb, sample)

    @staticmethod
    def _store_peak_rss(record: Dict[str, Any], peak_kb: Optional[int]) -> None:
        record["peak_rss_kb"] = peak_kb
        record["peak_rss_bytes"] = None if peak_kb is None else int(peak_kb) * 1024

    def _supervise_loop(
        self,
        record: Dict[str, Any],
        *,
        proc: Optional[subprocess.Popen[Any]],
        timeout_s: float,
        artifact_verifier: Optional[ArtifactVerifier],
        base_marker: MarkerCheck,
        stress_marker: MarkerCheck,
        started_monotonic: float,
        log_state: Optional[Dict[str, Any]] = None,
        adopted: bool = False,
        stop_event: Optional[threading.Event] = None,
    ) -> None:
        pid = int(record["pid"])
        timed_out = False
        stopped_by_request = False
        last_beat = time.monotonic()
        peak_rss_kb: Optional[int] = record.get("peak_rss_kb")
        status: Optional[int] = None
        echild_seen = False
        try:
            while True:
                if stop_event is not None and stop_event.is_set():
                    stopped_by_request = True
                    break
                now = time.monotonic()
                elapsed = now - started_monotonic
                if proc is not None:
                    try:
                        wait_res = proc.poll()
                    except ChildProcessError:
                        wait_res = None
                        echild_seen = True
                    if wait_res is not None:
                        status = wait_res
                        break
                else:
                    if not self._alive_by_identity(record):
                        status = None
                        break
                base_ok = _eval_marker(base_marker)
                stress_ok = _eval_marker(stress_marker)
                record["markers"]["base_reached"] = base_ok
                record["markers"]["stress_reached"] = stress_ok
                peak_rss_kb = self._sample_peak_rss(record, peak_rss_kb)
                self._store_peak_rss(record, peak_rss_kb)
                if elapsed >= timeout_s:
                    timed_out = True
                    evidence: Dict[str, Any] = {
                        "timeout_s": timeout_s,
                        "elapsed_at_timeout_s": round(elapsed, 3),
                    }
                    self._escalate_and_reap(record, evidence, term_first=True)
                    record["evidence"].update(evidence)
                    break
                if now - last_beat >= self.heartbeat_interval_s:
                    self._write_heartbeat(
                        record, started_monotonic=started_monotonic, log_state=log_state
                    )
                    last_beat = time.monotonic()
                time.sleep(min(self.poll_interval_s, max(0.0, timeout_s - elapsed)))
        except BaseException as exc:  # KeyboardInterrupt/SystemExit: controller lost
            record["terminal_state"] = "CONTROLLER_LOST"
            record["evidence"]["controller_exception"] = f"{type(exc).__name__}: {exc}"
            record["evidence"]["last_heartbeat_age_s"] = self.heartbeat_age_s(
                str(record["trial_id"]), record=record
            )
            self._save_record(record)
            atomic_write_json(self.terminal_path(str(record["trial_id"])), self._terminal_payload(record))
            raise

        if timed_out:
            record["terminal_state"] = "TIMED_OUT"
            record["artifact_verification"] = {"ok": False, "reason": "timed_out_before_verification"}
            record.setdefault("evidence", {}).update(
                {
                    "death_kind": "controller_timeout_escalation",
                    "memory_pressure_evidence": None,
                }
            )
            self._attach_stderr_tail(record)
            self._write_terminal(record)
            return

        if stopped_by_request:
            evidence = {"reason": "controller_stop"}
            self._escalate_and_reap(record, evidence, term_first=True)
            record["evidence"].update(evidence)
            self._finalize(
                record,
                artifact_verifier=None,
                base_marker=base_marker,
                stress_marker=stress_marker,
                classification_basis={
                    "kind": "stopped_by_controller",
                    "controller_sent_signals": True,
                },
            )
            return

        if proc is None:
            # Adopted supervision lost the process: not our child, so there is
            # no waitpid truth.  Fail closed to the classifier (which will
            # honour partial markers, then UNKNOWN_EXTERNAL_KILL).
            record.setdefault("evidence", {}).update(
                {
                    "reason": (
                        "adopted process vanished; this controller is not the parent "
                        "so no waitpid truth exists"
                    ),
                    "death_kind": "adopted_loss_no_exit_truth",
                    "memory_pressure_evidence": None,
                }
            )
        elif status is not None:
            # Popen.returncode convention: positive = exit code,
            # negative = killed by signal -(code).  (Raw waitpid statuses are
            # only seen inside the escalation path, which decodes them there.)
            if status < 0:
                record["exit_signal"] = -status
            else:
                record["exit_code"] = status
        elif echild_seen:
            record.setdefault("evidence", {}).update(
                {
                    "reason": "waitpid ECHILD: child no longer reapable by this controller",
                    "death_kind": "echild_no_exit_truth",
                    "memory_pressure_evidence": None,
                }
            )

        self._finalize(
            record,
            artifact_verifier=artifact_verifier,
            base_marker=base_marker,
            stress_marker=stress_marker,
            classification_basis={
                "kind": (
                    "adopted_loss_no_exit_truth"
                    if proc is None
                    else ("echild_no_exit_truth" if echild_seen and status is None else "exit_watch")
                ),
                "adopted": adopted,
                "controller_sent_signals": self._we_signaled(record),
            },
        )

    @staticmethod
    def _we_signaled(record: Dict[str, Any]) -> bool:
        evidence = record.get("evidence", {})
        if evidence.get("signals_sent"):
            return True
        return "sigterm_sent_utc" in evidence or "sigkill_sent_utc" in evidence

    # ------------------------------------------------------------ escalation
    def _escalate_and_reap(
        self,
        record: Dict[str, Any],
        evidence: Dict[str, Any],
        *,
        term_first: bool,
    ) -> None:
        """SIGTERM exact recorded group, wait grace, SIGKILL exact group, reap.

        Every step is timestamped into ``evidence``; only the recorded PGID is
        ever signalled (never a name, never a broad match).
        """
        pid = int(record["pid"])
        pgid = int(record["pgid"])
        observed_status: Optional[int] = None
        if term_first:
            evidence["sigterm_sent_utc"] = utc_now_iso()
            self._kill_group(pgid, signal.SIGTERM, evidence)
            deadline = time.monotonic() + self.term_grace_s
            while time.monotonic() < deadline:
                observed_status = self._reap_nonblocking(pid, evidence)
                if not self._group_alive(pgid):
                    break
                time.sleep(0.05)
        if self._group_alive(pgid) or self._pid_alive(pid):
            evidence["sigkill_sent_utc"] = utc_now_iso()
            self._kill_group(pgid, signal.SIGKILL, evidence)
        final_status = self._reap_blocking(pid)
        if final_status is not None:
            observed_status = final_status
        evidence["reaped"] = observed_status is not None or final_status is not None
        if observed_status is not None:
            evidence["reaped_wait_status"] = observed_status
            if os.WIFEXITED(observed_status):
                record["exit_code"] = os.WEXITSTATUS(observed_status)
            elif os.WIFSIGNALED(observed_status):
                record["exit_signal"] = os.WTERMSIG(observed_status)
        err_tail = tail_file(Path(record.get("log_paths", {}).get("stderr", "")))
        if err_tail:
            evidence["stderr_tail"] = err_tail[-STDERR_TAIL_BYTES:]

    def _kill_group(self, pgid: int, sig: int, evidence: Dict[str, Any]) -> None:
        if pgid <= 1:
            evidence[f"refused_signal_{int(sig)}_on_pgid"] = pgid
            return
        try:
            os.killpg(pgid, sig)
            evidence.setdefault("signals_sent", []).append({"pgid": pgid, "sig": int(sig)})
        except ProcessLookupError:
            evidence.setdefault("signals_sent", []).append(
                {"pgid": pgid, "sig": int(sig), "note": "already gone"}
            )
        except PermissionError as exc:
            evidence.setdefault("signals_errors", []).append(str(exc))

    @staticmethod
    def _group_alive(pgid: int) -> bool:
        try:
            os.killpg(pgid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError as exc:
            return exc.errno == errno.EPERM

    def _reap_nonblocking(self, pid: int, evidence: Dict[str, Any]) -> Optional[int]:
        try:
            done, status = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            return None
        if done == pid:
            evidence["reaped_during_grace_utc"] = utc_now_iso()
            return status
        return None

    def _reap_blocking(self, pid: int) -> Optional[int]:
        for _ in range(600):
            try:
                done, status = os.waitpid(pid, os.WNOHANG)
                if done == pid:
                    return status
            except ChildProcessError:
                # Not our child anymore (adopted session): nothing to reap.
                return None
            time.sleep(0.05)
        return None

    # ---------------------------------------------------------- finalization
    def _run_verifier(
        self,
        record: Dict[str, Any],
        artifact_verifier: Optional[ArtifactVerifier],
    ) -> Dict[str, Any]:
        if artifact_verifier is None:
            return {"ok": False, "reason": "no_verifier_injected"}
        try:
            return _normalize_verdict(artifact_verifier(dict(record)))
        except Exception as exc:  # noqa: BLE001 - verifier faults fail closed
            return {"ok": False, "reason": f"verifier_raised:{type(exc).__name__}", "detail": str(exc)}

    def _attach_stderr_tail(self, record: Dict[str, Any]) -> None:
        err_tail = tail_file(Path(record.get("log_paths", {}).get("stderr", "")))
        if err_tail:
            record.setdefault("evidence", {})["stderr_tail"] = err_tail[-STDERR_TAIL_BYTES:]

    def _finalize(
        self,
        record: Dict[str, Any],
        *,
        artifact_verifier: Optional[ArtifactVerifier],
        base_marker: MarkerCheck,
        stress_marker: MarkerCheck,
        classification_basis: Dict[str, Any],
    ) -> None:
        record["markers"]["base_reached"] = _eval_marker(base_marker)
        record["markers"]["stress_reached"] = _eval_marker(stress_marker)
        exited_zero = record.get("exit_code") == 0 and record.get("exit_signal") is None
        we_signaled = bool(classification_basis.get("controller_sent_signals")) or self._we_signaled(record)

        if exited_zero:
            verdict = self._run_verifier(record, artifact_verifier)
            record["artifact_verification"] = verdict
            record["terminal_state"] = "COMPLETED" if verdict.get("ok") else "FAILED_INCOMPLETE"
            if not verdict.get("ok"):
                record.setdefault("evidence", {})["incomplete_reason"] = verdict.get(
                    "reason", "verifier_negative"
                )
        else:
            # Exit 0 alone is never completion; signals/nonzero exits never verify.
            record["artifact_verification"] = {"ok": False, "reason": "worker_did_not_exit_zero"}
            self._attach_stderr_tail(record)
            sig = record.get("exit_signal")
            code = record.get("exit_code")
            base_ok = bool(record["markers"]["base_reached"])
            stress_ok = bool(record["markers"]["stress_reached"])
            evidence = record.setdefault("evidence", {})
            if code is not None and sig is None:
                death_kind = "nonzero_exit"
            elif sig is not None:
                death_kind = f"signal_{int(sig)}"
            else:
                death_kind = str(evidence.get("death_kind", "no_exit_truth"))
            evidence["death_kind"] = death_kind
            evidence["classification_basis"] = classification_basis
            evidence["controller_sent_signals"] = we_signaled
            if base_ok and not stress_ok:
                # A base result exists but stress/finalize never ran: the base
                # ending is NOT pipeline completion (H02).
                record["terminal_state"] = "PARTIAL_PRE_SCORE"
                evidence["partial_reason"] = "died after BASE marker before STRESS marker"
                evidence["base_only_timestamp_note"] = (
                    "base execution ending is not pipeline completion"
                )
            elif sig is not None and int(sig) == int(signal.SIGKILL) and not we_signaled:
                record["terminal_state"] = "UNKNOWN_EXTERNAL_KILL"
                evidence["unexplained_kill_reason"] = (
                    "worker died by SIGKILL this controller never sent "
                    "(external actor or kernel); no OOM claim is made"
                )
                evidence["memory_pressure_evidence"] = None
            elif sig is not None:
                record["terminal_state"] = "SIGNALLED"
            elif code is None:
                record["terminal_state"] = "UNKNOWN_EXTERNAL_KILL"
                evidence.setdefault("unexplained_kill_reason", "no waitpid truth available")
                evidence["memory_pressure_evidence"] = None
            else:
                record["terminal_state"] = "FAILED_INCOMPLETE"
        self._write_terminal(record)

    def _terminal_payload(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "trial_id": record["trial_id"],
            "terminal_state": record["terminal_state"],
            "exit_code": record.get("exit_code"),
            "exit_signal": record.get("exit_signal"),
            "artifact_verification": record.get("artifact_verification"),
            "timestamps": record.get("timestamps"),
            "finalized_utc": utc_now_iso(),
            "evidence": record.get("evidence"),
        }

    def _write_terminal(self, record: Dict[str, Any]) -> None:
        """Persist record first; terminal marker is written LAST (H02)."""
        record["timestamps"]["terminal_utc"] = utc_now_iso()
        self._save_record(record)
        atomic_write_json(self.terminal_path(str(record["trial_id"])), self._terminal_payload(record))


# ----------------------------------------------------------------------- CLI
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research.runtime_controller_v10",
        description="V10 authoritative worker controller (spawn/resume/show/stop).",
    )
    parser.add_argument("--state-dir", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    p_spawn = sub.add_parser("spawn", help="spawn a supervised worker after --")
    p_spawn.add_argument("--trial-id", required=True)
    p_spawn.add_argument("--launch-sha", default="")
    p_spawn.add_argument("--worktree", default=os.getcwd())
    p_spawn.add_argument("--output-dir", default="")
    p_spawn.add_argument("--timeout-s", type=float, required=True)
    p_spawn.add_argument("--phase", default="PREPARE", choices=list(PHASES))
    p_spawn.add_argument("--env", action="append", default=[], metavar="K=V")
    p_spawn.add_argument("argv", nargs=argparse.REMAINDER)

    p_resume = sub.add_parser("resume", help="adopt a matching live worker by full identity")
    p_resume.add_argument("--trial-id")
    p_resume.add_argument("--pid", type=int, required=True)
    p_resume.add_argument("--lstart", required=True)
    p_resume.add_argument("--command-hash", required=True)
    p_resume.add_argument("--worktree", required=True)
    p_resume.add_argument("--timeout-s", type=float, required=True)

    sub.add_parser("show", help="dump all records as JSON")
    p_stop = sub.add_parser("stop", help="graceful stop of the exact group")
    p_stop.add_argument("--trial-id", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    controller = WorkerController(args.state_dir)
    if args.command == "spawn":
        cmd = [a for a in args.argv if a != "--"]
        record = controller.spawn(
            cmd,
            trial_id=args.trial_id,
            launch_sha=args.launch_sha,
            worktree=args.worktree,
            output_dir=args.output_dir or str(Path(args.worktree) / "results" / args.trial_id),
            timeout_s=args.timeout_s,
            phase=args.phase,
            env_extra=dict(kv.split("=", 1) for kv in args.env),
        )
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0 if record.get("terminal_state") == "COMPLETED" else 1
    if args.command == "resume":
        record = controller.resume(
            pid=args.pid,
            posix_start_identity=args.lstart,
            command_hash_hex=args.command_hash,
            worktree=args.worktree,
            trial_id=args.trial_id,
            timeout_s=args.timeout_s,
        )
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0 if record.get("terminal_state") == "COMPLETED" else 1
    if args.command == "show":
        print(json.dumps(controller.load_records(), indent=2, sort_keys=True))
        return 0
    if args.command == "stop":
        record = controller.stop(args.trial_id)
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
