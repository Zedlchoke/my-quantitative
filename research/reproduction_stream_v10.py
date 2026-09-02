"""A4 streamed reproduction runner (PLAN.md section 6, H04 -- streaming logs).

Replaces buffered whole-child output retention with a line-streaming
subprocess runner for reproduction workers:

* the child is spawned with its OWN process group/session
  (``start_new_session=True``), so timeouts kill the EXACT group (child +
  grandchildren) and never unrelated workers;
* stdout and stderr are streamed line-by-line by dedicated reader threads
  into timestamped phase-aware log files
  ``<log_dir>/<UTC>__<phase>.out.log`` / ``.err.log``; every persisted line
  is prefixed with an ISO-8601 UTC stamp so partial evidence survives even
  when the child dies mid-line;
* a liveness state JSON next to the logs is rewritten ATOMICALLY
  (tmp file + fsync + ``os.replace``) with ``last_log_at_utc``,
  ``lines_seen``, ``bytes_written``, ``phase``, ``pid``/``pgid``,
  ``started_at`` and terminal fields, so an external reader observes
  progress BEFORE completion;
* ``timeout_s`` is REQUIRED and non-null (H03/H08-11): on deadline the
  exact process group gets SIGTERM, then after ``term_grace_s`` (default
  30s per contract) SIGKILL; the child is reaped and structured timeout
  evidence is recorded in the state JSON and the result;
* large logs are bounded: each stream rotates at ``max_log_bytes``
  (default 100 MB) keeping at most ``MAX_ROTATIONS = 2`` rotations
  (``.log.1``/``.log.2``); :func:`tail` reads only the last k bytes of a
  file efficiently for bounded terminal-report excerpts.

The runner NEVER buffers whole-child output in memory: there is no whole-
stream capture anywhere in this module -- child output flows to disk as it
is produced, and only the bounded stderr tail (``TAIL_EXCERPT_BYTES``)
travels into terminal reports.

Stdlib only; no network; no engine imports.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

__all__ = [
    "DEFAULT_MAX_LOG_BYTES",
    "DEFAULT_STATE_MIN_INTERVAL_S",
    "MAX_ROTATIONS",
    "RUNNING",
    "TAIL_EXCERPT_BYTES",
    "TERM_GRACE_S",
    "RunResult",
    "read_state",
    "run_streamed",
    "tail",
]

#: Default per-stream rotation threshold (100 MB).
DEFAULT_MAX_LOG_BYTES: int = 100 * 1024 * 1024
#: Rotated generations kept per stream (`.log.1` .. `.log.N`).
MAX_ROTATIONS: int = 2
#: Upper bound of the stderr tail excerpt carried into terminal reports.
TAIL_EXCERPT_BYTES: int = 8 * 1024
#: Contract grace between SIGTERM and SIGKILL for the timed-out group.
TERM_GRACE_S: float = 30.0
#: Minimum wall-clock spacing between liveness state rewrites (per stream);
#: keeps state observable while bounding disk churn for chatty children.
DEFAULT_STATE_MIN_INTERVAL_S: float = 0.1

TERMINAL_RUNNING = "RUNNING"
TERMINAL_EXITED = "EXITED"
TERMINAL_TIMED_OUT = "TIMED_OUT"

_STATE_SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    """Current UTC time as ISO-8601 with explicit offset."""
    return datetime.now(timezone.utc).isoformat()


def _sanitize_phase(label: str) -> str:
    """Filename-safe phase token (non-allowlist chars -> '-')."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(label)).strip("-")
    return cleaned or "phase"


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomic JSON write: unique tmp sibling -> fsync -> os.replace."""
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}-{threading.get_ident()}")
    data = (json.dumps(dict(payload), indent=2, sort_keys=True, default=str)
            + "\n").encode("utf-8")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def read_state(path: str | Path) -> dict[str, Any] | None:
    """Tolerant state-JSON reader: parsed dict or None (never raises)."""
    try:
        parsed = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def tail(path: str | Path, k_bytes: int) -> bytes:
    """Last ``k_bytes`` bytes of a file, reading ONLY that window.

    Seeks from EOF instead of loading the file; returns the whole content
    when the file is smaller than the window.
    """
    if k_bytes <= 0:
        return b""
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        if size > k_bytes:
            fh.seek(-k_bytes, os.SEEK_END)
        return fh.read()


class _RotatingLogWriter:
    """Append-only binary line writer with size-bounded rotation.

    When the active file would exceed ``max_log_bytes`` (and is non-empty),
    generations shift ``current -> .1 -> .2`` and at most ``MAX_ROTATIONS``
    rotated generations are kept; older ones are displaced by ``os.replace``
    (overwrite semantics), so the on-disk footprint stays bounded.
    """

    def __init__(self, path: Path, max_log_bytes: int) -> int:
        self.path = Path(path)
        self.max_log_bytes = int(max_log_bytes)
        if self.max_log_bytes <= 0:
            raise ValueError("max_log_bytes must be positive")
        self.total_bytes_written = 0
        self._fh = open(self.path, "ab")

    def write_line(self, stamp_utc: str, raw_line: bytes) -> int:
        payload = stamp_utc.encode("utf-8") + b" " + raw_line
        if not payload.endswith(b"\n"):
            payload += b"\n"
        try:
            current_size = self._fh.tell()
        except OSError:
            current_size = self.path.stat().st_size
        if 0 < current_size and current_size + len(payload) > self.max_log_bytes:
            self._rotate()
        self._fh.write(payload)
        self._fh.flush()
        self.total_bytes_written += len(payload)
        return len(payload)

    def _rotate(self) -> None:
        self._fh.close()
        for idx in range(MAX_ROTATIONS - 1, 0, -1):
            src = self.path.with_name(f"{self.path.name}.{idx}")
            dst = self.path.with_name(f"{self.path.name}.{idx + 1}")
            if src.exists():
                os.replace(src, dst)
        os.replace(self.path, self.path.with_name(f"{self.path.name}.1"))
        self._fh = open(self.path, "wb")

    def close(self) -> None:
        try:
            self._fh.close()
        except OSError:
            pass


@dataclass(frozen=True)
class RunResult:
    """Terminal outcome of one streamed run (evidence-carrying)."""

    exit_code: int | None
    duration_s: float
    timed_out: bool
    log_paths: dict[str, str]
    tail_excerpt: str
    last_log_at_utc: str | None
    lines_seen: int
    bytes_written: int
    state_path: str
    pid: int
    pgid: int
    terminal_state: str
    timeout_evidence: dict[str, Any]


class _StreamCounters:
    """Lock-guarded counters shared between reader threads and the writer."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.lines_seen = 0
        self.bytes_written = 0
        self.last_log_at_utc: str | None = None

    def record(self, lines: int, byte_count: int, stamp: str | None) -> None:
        with self.lock:
            self.lines_seen += lines
            self.bytes_written += byte_count
            if stamp is not None:
                self.last_log_at_utc = stamp

    def snapshot(self) -> tuple[int, int, str | None]:
        with self.lock:
            return self.lines_seen, self.bytes_written, self.last_log_at_utc


def run_streamed(argv, log_dir, phase_label, timeout_s,
                 env: Mapping[str, str] | None = None,
                 cwd: str | Path | None = None,
                 max_log_bytes: int = DEFAULT_MAX_LOG_BYTES,
                 term_grace_s: float = TERM_GRACE_S,
                 state_min_interval_s: float = DEFAULT_STATE_MIN_INTERVAL_S,
                 ) -> RunResult:
    """Spawn ``argv`` in its own process group and stream its output to disk.

    Parameters mirror the H04 contract: ``timeout_s`` is REQUIRED non-null;
    ``env=None`` inherits the full parent environment, otherwise the mapping
    is merged OVER ``os.environ`` (caller overrides win last, matching the
    reproduction-harness forwarding convention). Logs land under ``log_dir``
    as ``<UTCcompact>__<phase>.out.log`` / ``.err.log`` (+ ``.state.json``).
    """
    if timeout_s is None:
        raise ValueError(
            "run_streamed requires a non-null timeout_s "
            "(H03: production subprocess layers never wait unbounded)")
    timeout_f = float(timeout_s)
    if not timeout_f > 0:
        raise ValueError(f"timeout_s must be positive, got {timeout_s!r}")
    argv_tokens = [str(token) for token in argv]
    if not argv_tokens:
        raise ValueError("argv must be non-empty")

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    phase = _sanitize_phase(phase_label)
    base = log_dir / f"{stamp}__{phase}"
    while base.with_name(base.name + ".state.json").exists():
        base = base + "-x"
    out_path = base.with_name(base.name + ".out.log")
    err_path = base.with_name(base.name + ".err.log")
    state_path = base.with_name(base.name + ".state.json")

    popen_env: Mapping[str, str] | None = None
    if env is not None:
        merged = dict(os.environ)
        merged.update({str(k): str(v) for k, v in env.items()})
        popen_env = merged

    counters = _StreamCounters()
    started_at = utc_now_iso()
    started_mono = time.monotonic()

    proc = subprocess.Popen(
        argv_tokens,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        env=popen_env,
        cwd=(None if cwd is None else str(cwd)),
        start_new_session=True,
    )
    pgid = proc.pid  # session leader => process group id == pid

    def write_state(terminal_state: str,
                    evidence: dict[str, Any] | None = None,
                    exit_code: int | None = None,
                    duration: float | None = None) -> None:
        lines, byte_count, last_stamp = counters.snapshot()
        doc: dict[str, Any] = {
            "schema_version": _STATE_SCHEMA_VERSION,
            "artifact": "repro_stream_state_v10",
            "phase": phase,
            "phase_label_raw": str(phase_label),
            "pid": proc.pid,
            "pgid": pgid,
            "command": argv_tokens,
            "command_sha256": hashlib.sha256(
                json.dumps(argv_tokens, separators=(",", ":")).encode()).hexdigest(),
            "started_at": started_at,
            "last_log_at_utc": last_stamp,
            "lines_seen": lines,
            "bytes_written": byte_count,
            "terminal_state": terminal_state,
            "timed_out": terminal_state == TERMINAL_TIMED_OUT,
            "timeout_evidence": evidence or {},
            "exit_code": exit_code,
            "duration_s": duration,
            "generated_at_utc": utc_now_iso(),
            "log_paths": {"stdout": str(out_path), "stderr": str(err_path)},
            "max_log_bytes": int(max_log_bytes),
            "timeout_s": timeout_f,
        }
        _atomic_write_json(state_path, doc)

    writers: dict[str, _RotatingLogWriter] = {
        "stdout": _RotatingLogWriter(out_path, max_log_bytes),
        "stderr": _RotatingLogWriter(err_path, max_log_bytes),
    }

    def pump(stream_name: str, stream) -> None:
        writer = writers[stream_name]
        last_state_write = time.monotonic()
        try:
            for raw in iter(stream.readline, b""):
                line_stamp = utc_now_iso()
                written = writer.write_line(line_stamp, raw.rstrip(b"\r\n"))
                counters.record(1, written, line_stamp)
                now = time.monotonic()
                if now - last_state_write >= state_min_interval_s:
                    last_state_write = now
                    write_state(TERMINAL_RUNNING)
        finally:
            try:
                stream.close()
            except OSError:
                pass

    threads = [
        threading.Thread(target=pump, args=("stdout", proc.stdout), daemon=True),
        threading.Thread(target=pump, args=("stderr", proc.stderr), daemon=True),
    ]
    for thread in threads:
        thread.start()

    write_state(TERMINAL_RUNNING)

    timed_out = False
    evidence: dict[str, Any] = {}
    try:
        exit_code = proc.wait(timeout=timeout_f)
    except subprocess.TimeoutExpired:
        timed_out = True
        evidence = _terminate_exact_group(proc, term_grace_s)
        exit_code = proc.wait()

    for thread in threads:
        thread.join(timeout=10.0)
    if not any(thread.is_alive() for thread in threads):
        for writer in writers.values():
            writer.close()

    finished_mono = time.monotonic()
    duration = finished_mono - started_mono
    terminal_state = TERMINAL_TIMED_OUT if timed_out else TERMINAL_EXITED
    write_state(terminal_state, evidence=evidence, exit_code=exit_code,
                duration=duration)

    _, _, last_stamp = counters.snapshot()
    total_lines, total_bytes = counters.lines_seen, counters.bytes_written
    return RunResult(
        exit_code=exit_code,
        duration_s=duration,
        timed_out=timed_out,
        log_paths={"stdout": str(out_path), "stderr": str(err_path)},
        tail_excerpt=tail(err_path, TAIL_EXCERPT_BYTES).decode(
            "utf-8", errors="replace"),
        last_log_at_utc=last_stamp,
        lines_seen=total_lines,
        bytes_written=total_bytes,
        state_path=str(state_path),
        pid=proc.pid,
        pgid=pgid,
        terminal_state=terminal_state,
        timeout_evidence=evidence,
    )


def _terminate_exact_group(proc: subprocess.Popen,
                           term_grace_s: float) -> dict[str, Any]:
    """SIGTERM the exact group, grace-wait, then SIGKILL group; reap+evidence."""
    pgid = proc.pid
    evidence: dict[str, Any] = {
        "timed_out": True,
        "killed_pgid": pgid,
        "term_grace_s": term_grace_s,
        "sigterm_sent_at_utc": utc_now_iso(),
    }
    try:
        os.killpg(pgid, signal.SIGTERM)
        evidence["sigterm_result"] = "sent"
    except ProcessLookupError:
        evidence["sigterm_result"] = "group_already_gone"
    try:
        proc.wait(timeout=max(0.0, float(term_grace_s)))
        evidence["escalated_to_sigkill"] = False
    except subprocess.TimeoutExpired:
        evidence["escalated_to_sigkill"] = True
        evidence["sigkill_sent_at_utc"] = utc_now_iso()
        try:
            os.killpg(pgid, signal.SIGKILL)
            evidence["sigkill_result"] = "sent"
        except ProcessLookupError:
            evidence["sigkill_result"] = "group_already_gone"
    proc.wait()
    evidence["reaped"] = True
    evidence["final_returncode"] = proc.returncode
    return evidence
