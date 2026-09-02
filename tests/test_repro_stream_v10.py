"""A4 streamed-runner tests (PLAN.md section 6, H04 -- synthetic children only).

No real reproduction runs, no network, no engine imports. Covered:

* streaming works: a python child printing lines with sleeps produces a
  growing log WHILE it is alive, the atomic state JSON shows increasing
  ``lines_seen`` and a fresh ``last_log_at_utc`` pre-completion, and lines
  on disk carry ISO-UTC prefixes;
* the state JSON stays parseable for an external reader throughout rapid
  concurrent updates (chatty child + continuous reader loop);
* timeout escalates SIGTERM -> SIGKILL against the EXACT process group
  (child that ignores SIGTERM plus its ``sleep`` grandchild), leaves NO
  orphan, reaps, and records structured evidence;
* grep-guard: the module source contains the literal banned-buffering flag
  NOWHERE (whole-child output capture must never return) and
  ``run_streamed`` exposes no such parameter;
* rotation triggers at small ``max_log_bytes`` keeping at most
  ``MAX_ROTATIONS = 2`` generations;
* ``tail()`` reads only the last k bytes; ``tail_excerpt`` stays bounded
  at ``TAIL_EXCERPT_BYTES`` and reflects late stderr content;
* exit codes propagate verbatim; non-null positive ``timeout_s`` is
  REQUIRED (missing arg -> TypeError, None/non-positive -> ValueError);
* env/cwd forwarding works (caller env merged last over parent).
"""

from __future__ import annotations

import inspect
import json
import os
import re
import sys
import threading
import time
from pathlib import Path

import pytest

import research.reproduction_stream_v10 as rstream
from research.reproduction_stream_v10 import (
    MAX_ROTATIONS,
    TAIL_EXCERPT_BYTES,
    read_state,
    run_streamed,
    tail,
)

PY = sys.executable

#: Child: alternating stdout/stderr lines with sleeps so an external reader
#: can observe liveness while it runs.
CHILD_SLOW_PRINT = (
    "import sys, time\n"
    "for i in range(8):\n"
    "    print(f'line-{i}', flush=True)\n"
    "    print(f'err-{i}', file=sys.stderr, flush=True)\n"
    "    time.sleep(0.2)\n"
    "print('done', flush=True)\n"
)

#: Child: high-frequency output to stress atomic state writes.
CHILD_SPAM = (
    "for i in range(2000):\n"
    "    print(f'spam-{i}-' + 'x' * 40, flush=True)\n"
)

#: Child: ignores SIGTERM, announces a `sleep` grandchild in ITS OWN group
#: (inherited), then idles -- used to prove group-wide escalation.
_CHILD_IGNORE_TERM = (
    "import signal, subprocess, sys, time\n"
    "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
    "gc = subprocess.Popen(['sleep', '120'])\n"
    "print(f'GRANDCHILD {gc.pid}', flush=True)\n"
    "time.sleep(120)\n"
)

#: Child: big stderr blob to exercise bounded tails.
CHILD_BIG_STDERR = (
    "import sys\n"
    "sys.stderr.write('A' * 60000 + '\\n')\n"
    "sys.stderr.write('TAIL-MARKER-9f2c\\n')\n"
    "sys.stderr.flush()\n"
)

#: Child: exits with an arbitrary code.
_CHILD_EXIT = "import sys; print('bye'); sys.exit(7)"

#: Child: prints an env var and cwd to verify forwarding.
_CHILD_ENV_CWD = (
    "import os, sys\n"
    "print(os.environ.get('A4_STREAM_MARKER', 'MISSING'), flush=True)\n"
    "print(os.getcwd(), flush=True)\n"
)


def _write_child(tmp_path: Path, name: str, body: str) -> str:
    script = tmp_path / name
    script.write_text(body, encoding="utf-8")
    return str(script)


def _wait_for(predicate, timeout_s: float = 15.0, interval_s: float = 0.05):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval_s)
    return None


def _assert_no_orphan(pid: int) -> None:
    """Poll until the pid is gone (zombie reaped) -- fail if still alive."""
    for _ in range(100):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    raise AssertionError(f"orphan survived: pid {pid}")


# --------------------------------------------------------------------------- #
# streaming liveness
# --------------------------------------------------------------------------- #
def test_streaming_grows_log_and_state_while_child_alive(tmp_path):
    log_dir = tmp_path / "logs"
    child = _write_child(tmp_path, "slow_print.py", CHILD_SLOW_PRINT)

    samples: list[tuple[float, int, str | None]] = []
    stop = threading.Event()

    def watcher():
        while not stop.is_set():
            states = list(log_dir.glob("*.state.json"))
            if states:
                doc = read_state(states[0])
                if doc is not None:
                    samples.append((time.monotonic(),
                                    doc.get("lines_seen", -1),
                                    doc.get("last_log_at_utc")))
            time.sleep(0.05)

    watcher_thread = threading.Thread(target=watcher, daemon=True)
    watcher_thread.start()
    try:
        result = run_streamed([PY, child], log_dir, "REPRODUCE",
                              timeout_s=30)
    finally:
        stop.set()
        watcher_thread.join(timeout=5)

    assert result.exit_code == 0
    assert result.timed_out is False
    assert result.terminal_state == "EXITED"

    # observable progress BEFORE completion: alive-phase samples show
    # growing lines_seen AND at least two distinct last_log_at_utc values
    alive = [s for s in samples if s[1] >= 0 and s[1] < result.lines_seen]
    assert alive, f"no pre-completion liveness samples: {samples[-3:]}"
    distinct_last_log = {s[2] for s in alive if s[2] is not None}
    assert len(distinct_last_log) >= 2, (
        f"last_log_at_utc never updated while alive: {sorted(distinct_last_log)}")
    seen = [s[1] for s in alive]
    assert max(seen) > min(seen) >= 0, f"lines_seen never grew: {seen}"

    # logs carry ISO-UTC prefixes per line and full content
    out_text = Path(result.log_paths["stdout"]).read_text(encoding="utf-8")
    err_text = Path(result.log_paths["stderr"]).read_text(encoding="utf-8")
    out_lines = out_text.strip().splitlines()
    assert len(out_lines) == 9  # 8 numbered + done
    assert all(_ISO_LINE.match(line) for line in out_lines[:3])
    assert any(line.endswith("line-0") for line in out_lines)
    assert any("err-7" in line for line in err_text.strip().splitlines())
    assert result.last_log_at_utc is not None
    assert result.lines_seen == 17  # 9 stdout + 8 stderr


_ISO_LINE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00 \S")


def test_atomic_state_parseable_during_rapid_updates(tmp_path):
    log_dir = tmp_path / "logs"
    child = _write_child(tmp_path, "spam.py", CHILD_SPAM)

    parse_failures: list[str] = []
    parses = [0]
    done = threading.Event()

    def reader_loop():
        while not done.is_set():
            states = list(log_dir.glob("*.state.json"))
            if states:
                raw = states[0].read_text(encoding="utf-8") \
                    if states[0].exists() else ""
                if raw:
                    try:
                        doc = json.loads(raw)
                        assert isinstance(doc.get("lines_seen"), int)
                        assert doc.get("phase") == "STRESS"
                        parses[0] += 1
                    except (ValueError, AssertionError) as exc:
                        parse_failures.append(repr(exc))
            time.sleep(0.005)

    reader = threading.Thread(target=reader_loop, daemon=True)
    reader.start()
    result = run_streamed([PY, "-u", child], log_dir, "STRESS",
                          timeout_s=60, state_min_interval_s=0.0)
    done.set()
    reader.join(timeout=5)

    assert result.exit_code == 0
    assert result.lines_seen == 2000
    assert parses[0] > 20, f"reader loop barely sampled: {parses[0]}"
    assert not parse_failures, f"state JSON unparseable {len(parse_failures)}x"


# --------------------------------------------------------------------------- #
# timeout escalation / exact-group kill
# --------------------------------------------------------------------------- #
def test_timeout_escalates_and_kills_exact_group_no_orphan(tmp_path):
    log_dir = tmp_path / "logs"
    child = _write_child(tmp_path, "ignore_term.py", _CHILD_IGNORE_TERM)

    result = run_streamed([PY, child], log_dir, "BASE",
                          timeout_s=1.5, term_grace_s=1.0)

    assert result.timed_out is True
    assert result.terminal_state == "TIMED_OUT"
    evidence = result.timeout_evidence
    assert evidence.get("timed_out") is True
    assert evidence.get("sigterm_result") == "sent"
    assert evidence.get("escalated_to_sigkill") is True
    assert evidence.get("reaped") is True
    assert evidence.get("killed_pgid") == result.pgid

    grandchild_pid = _wait_for(
        lambda: _grandchild_pid(Path(result.log_paths["stdout"])),
        timeout_s=5)
    assert grandchild_pid is not None, "child never announced grandchild"

    final_state = read_state(result.state_path)
    assert final_state is not None
    assert final_state["timed_out"] is True
    assert final_state["exit_code"] != 0

    # both child and grandchild are gone: exact-group kill left no orphan
    _wait_for(lambda: _gone(result.pid), timeout_s=5)
    _assert_no_orphan(grandchild_pid)


def _grandchild_pid(out_log: Path) -> int | None:
    try:
        text = out_log.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        if "GRANDCHILD" in line:
            return int(line.rsplit(" ", 1)[1])
    return None


def _gone(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def test_normal_completion_records_exit_without_timeout_evidence(tmp_path):
    log_dir = tmp_path / "logs"
    child = _write_child(tmp_path, "quick.py", "print('ok')\n")
    result = run_streamed([PY, child], log_dir, "FINALIZE", timeout_s=30)
    assert result.timed_out is False
    assert result.exit_code == 0
    assert result.timeout_evidence == {}
    state = read_state(result.state_path)
    assert state["terminal_state"] == "EXITED"
    assert state["timed_out"] is False


# --------------------------------------------------------------------------- #
# capture ban / contract guards
# --------------------------------------------------------------------------- #
def test_module_source_contains_no_whole_stream_capture():
    source = Path(rstream.__file__).read_text(encoding="utf-8")
    assert "capture_output" not in source, (
        "H04 violation: whole-child output buffering returned to the runner")
    params = inspect.signature(rstream.run_streamed).parameters
    assert "capture_output" not in params
    assert "timeout_s" in params  # non-null contract surface exists


def test_non_null_timeout_required(tmp_path):
    child = _write_child(tmp_path, "noop.py", "pass\n")
    with pytest.raises(ValueError):
        run_streamed([PY, child], tmp_path / "l1", "REPRODUCE",
                     timeout_s=None)
    with pytest.raises(ValueError):
        run_streamed([PY, child], tmp_path / "l2", "REPRODUCE",
                     timeout_s=0)
    with pytest.raises(TypeError):
        run_streamed([PY, child], tmp_path / "l3", "REPRODUCE")


# --------------------------------------------------------------------------- #
# rotation / bounding / tails
# --------------------------------------------------------------------------- #
def test_rotation_triggers_and_keeps_at_most_two_generations(tmp_path):
    log_dir = tmp_path / "logs"
    child = _write_child(tmp_path, "chatty.py", CHILD_SPAM)
    max_bytes = 2048
    result = run_streamed([PY, "-u", child], log_dir, "ROTATE",
                          timeout_s=60, max_log_bytes=max_bytes)
    assert result.exit_code == 0

    out_current = Path(result.log_paths["stdout"])
    rotations = [out_current.with_name(f"{out_current.name}.{n}")
                 for n in (1, 2)]
    assert all(p.exists() for p in rotations), "rotation did not trigger"
    assert not out_current.with_name(f"{out_current.name}.3").exists(), (
        "more than MAX_ROTATIONS generations retained")
    for path in [out_current, *rotations]:
        assert path.stat().st_size <= max_bytes + 256, (
            f"{path.name} exceeds bound: {path.stat().st_size}")
    # bounded retention by design: displaced generations are gone, the
    # newest output is retained in the live file
    retained = sum(p.stat().st_size for p in [out_current, *rotations])
    assert retained < result.bytes_written
    out_text = out_current.read_text(encoding="utf-8")
    assert "spam-1999" in out_text


def test_tail_reads_only_last_k_bytes(tmp_path):
    blob = tmp_path / "blob.log"
    payload = b"x" * 5000 + b"-END-OF-BLOB-42"
    blob.write_bytes(payload)
    assert tail(blob, 15) == b"-END-OF-BLOB-42"
    assert tail(blob, len(payload)) == payload
    assert tail(blob, 10 ** 9) == payload
    assert tail(blob, 0) == b""
    assert blob.stat().st_size == len(payload)  # nothing truncated/rewritten


def test_tail_excerpt_bounded_and_from_stderr(tmp_path):
    log_dir = tmp_path / "logs"
    child = _write_child(tmp_path, "big_err.py", CHILD_BIG_STDERR)
    result = run_streamed([PY, child], log_dir, "BASE", timeout_s=30)
    assert result.exit_code == 0
    assert 0 < len(result.tail_excerpt) <= TAIL_EXCERPT_BYTES
    assert "TAIL-MARKER-9f2c" in result.tail_excerpt


# --------------------------------------------------------------------------- #
# exit codes / env / cwd
# --------------------------------------------------------------------------- #
def test_exit_code_propagates(tmp_path):
    child = _write_child(tmp_path, "exit7.py", _CHILD_EXIT)
    result = run_streamed([PY, child], tmp_path / "logs", "REPRODUCE",
                          timeout_s=30)
    assert result.exit_code == 7
    assert result.timed_out is False
    assert result.duration_s > 0


def test_env_and_cwd_forwarded(tmp_path):
    log_dir = tmp_path / "logs"
    workdir = tmp_path / "work"
    workdir.mkdir()
    child = _write_child(tmp_path, "env_cwd.py", _CHILD_ENV_CWD)
    result = run_streamed(
        [PY, child], log_dir, "PREPARE", timeout_s=30,
        env={"A4_STREAM_MARKER": "v10-h04-ok"}, cwd=workdir)
    assert result.exit_code == 0
    out_text = Path(result.log_paths["stdout"]).read_text(encoding="utf-8")
    assert "v10-h04-ok" in out_text
    assert str(workdir) in out_text
