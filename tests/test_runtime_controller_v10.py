"""Adversarial controller tests (sprint V9H H01/H02/H03/H04; PLAN §6.H08 items 1-12).

H08 item -> test id map:
    1  test_h08_01_exit0_verified_completes
    2  test_h08_02_exit0_without_artifact_failed_incomplete
    3  test_h08_03_raising_child_records_exit_and_stderr_tail
    4  test_h08_04a_timeout_escalation_timed_out / test_h08_04b_external_sigterm_signalled
    5  test_h08_05_timeout_kills_exact_group_only
    6  test_h08_06_resume_identity_match_and_reuse_rejection
    7  test_h08_07_concurrent_workers_no_crossmatch
    8  test_h08_08_stale_heartbeat_warns_without_death
    9  test_h08_09_interrupted_atomic_write_parseable
    10 test_h08_10_death_after_base_partial_pre_score
    11 test_h08_11_timeout_never_null
    12 test_h08_12_log_readable_and_growing_while_alive

Synthetic fixtures only (`python -c`, `sleep`); deterministic, no network,
no name-based process matching anywhere.
"""

from __future__ import annotations

import inspect
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest

from research import runtime_controller_v10 as rc
from research.runtime_controller_v10 import (
    IdentityMismatchError,
    TailRotatingLog,
    WorkerController,
    atomic_write_json,
    command_hash,
    load_json_safe,
)
from research.status_cli_v10 import collect_rows, format_table, main as status_main

PY = sys.executable


# --------------------------------------------------------------------- helpers
def make_controller(state_dir: Path, **overrides: Any) -> WorkerController:
    kwargs: Dict[str, Any] = {
        "poll_interval_s": 0.05,
        "heartbeat_interval_s": 0.25,
        "term_grace_s": 0.4,
    }
    kwargs.update(overrides)
    return WorkerController(state_dir, **kwargs)


def wait_until(pred: Callable[[], bool], *, timeout: float = 6.0, interval: float = 0.05) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pred():
            return True
        time.sleep(interval)
    return pred()


class SpawnJob:
    """Runs controller.spawn in a daemon thread; captures result/exception."""

    def __init__(self, controller: WorkerController, **spawn_kwargs: Any) -> None:
        self.result: Optional[Dict[str, Any]] = None
        self.exc: Optional[BaseException] = None
        self._thread = threading.Thread(
            target=self._run, args=(controller,), kwargs=spawn_kwargs, daemon=True
        )
        self._thread.start()

    def _run(self, controller: WorkerController, **spawn_kwargs: Any) -> None:
        try:
            self.result = controller.spawn(**spawn_kwargs)
        except BaseException as exc:  # noqa: BLE001 - surfaced to the test
            self.exc = exc

    def join(self, timeout: float = 40.0) -> Dict[str, Any]:
        self._thread.join(timeout=timeout)
        assert not self._thread.is_alive(), "spawn thread did not finish"
        if self.exc is not None:
            raise self.exc
        assert self.result is not None
        return self.result


@pytest.fixture()
def guard():
    """Best-effort hygiene: exact-pid cleanup of processes a test tracked."""
    procs: List[subprocess.Popen[Any]] = []
    pids: List[int] = []

    class _Guard:
        @staticmethod
        def track_proc(proc: subprocess.Popen[Any]) -> subprocess.Popen[Any]:
            procs.append(proc)
            return proc

        @staticmethod
        def track_pid(pid: int) -> int:
            pids.append(int(pid))
            return int(pid)

    yield _Guard
    for proc in procs:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except (OSError, subprocess.SubprocessError):
            pass
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def spawn_kwargs(tmp_path: Path, trial: str, argv: List[str], **overrides: Any) -> Dict[str, Any]:
    (tmp_path / "wt").mkdir(parents=True, exist_ok=True)
    kw: Dict[str, Any] = {
        "cmd_argv": argv,
        "trial_id": trial,
        "launch_sha": "a" * 64,
        "worktree": str(tmp_path / "wt"),
        "output_dir": str(tmp_path / "out" / trial),
        "timeout_s": 10.0,
    }
    kw.update(overrides)
    return kw


def wait_for_identity(controller: WorkerController, trial: str, *, timeout: float = 5.0) -> Dict[str, Any]:
    found: Dict[str, Any] = {}

    def probe() -> bool:
        try:
            rec = controller.load_record(trial)
        except rc.UnknownTrialError:
            return False
        if rec.get("posix_start_identity"):
            found.update(rec)
            return True
        return False

    assert wait_until(probe, timeout=timeout), f"identity never captured for {trial}"
    return dict(found)


# ------------------------------------------------------------------- H08-01
def test_h08_01_exit0_verified_completes(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    argv = [PY, "-c", "print('worker-done')"]
    job = SpawnJob(
        ctrl,
        **spawn_kwargs(
            tmp_path, "t-complete", argv,
            artifact_verifier=lambda rec: {"ok": True, "detail": {"artifacts": "present"}},
        ),
    )
    record = job.join()
    assert record["terminal_state"] == "COMPLETED"
    assert record["exit_code"] == 0
    assert record["artifact_verification"]["ok"] is True
    marker = load_json_safe(ctrl.terminal_path("t-complete"))
    assert marker is not None and marker["terminal_state"] == "COMPLETED"
    assert marker["artifact_verification"]["ok"] is True
    assert record["timestamps"]["terminal_utc"] >= record["started_at_utc"]
    for key in (
        "trial_id", "pid", "pgid", "posix_start_identity", "command_hash",
        "launch_sha", "worktree", "output_dir", "phase", "started_at_utc",
        "last_heartbeat_utc", "last_log_at_utc", "exit_code", "exit_signal",
        "peak_rss_bytes", "terminal_state", "artifact_verification",
    ):
        assert key in record, f"missing worker-record field {key}"
    assert record["command_hash"] == command_hash(argv)
    assert record["pgid"] >= 2  # dedicated group, never 0/1
    assert "sigterm_sent_utc" not in record.get("evidence", {})  # no escalation on clean runs


# ------------------------------------------------------------------- H08-02
def test_h08_02_exit0_without_artifact_failed_incomplete(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    rec_a = SpawnJob(ctrl, **spawn_kwargs(tmp_path, "t-novf", [PY, "-c", "pass"])).join()
    assert rec_a["terminal_state"] == "FAILED_INCOMPLETE"
    assert rec_a["exit_code"] == 0
    assert rec_a["artifact_verification"]["reason"] == "no_verifier_injected"

    rec_b = SpawnJob(
        ctrl,
        **spawn_kwargs(
            tmp_path, "t-badvf", [PY, "-c", "pass"],
            artifact_verifier=lambda rec: {"ok": False, "detail": {"missing": "gate.json"}},
        ),
    ).join()
    assert rec_b["terminal_state"] == "FAILED_INCOMPLETE"
    assert rec_b["artifact_verification"]["ok"] is False

    def boom(_rec: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError("verifier exploded")

    rec_c = SpawnJob(
        ctrl, **spawn_kwargs(tmp_path, "t-vfraise", [PY, "-c", "pass"], artifact_verifier=boom)
    ).join()
    assert rec_c["terminal_state"] == "FAILED_INCOMPLETE"
    assert "verifier_raised" in rec_c["artifact_verification"]["reason"]
    for trial in ("t-novf", "t-badvf", "t-vfraise"):
        payload = load_json_safe(ctrl.terminal_path(trial))
        assert payload is None or payload["terminal_state"] != "COMPLETED"


# ------------------------------------------------------------------- H08-03
def test_h08_03_raising_child_records_exit_and_stderr_tail(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    argv = [PY, "-c", "import sys; print('boom-EVIDENCE-MARKER', file=sys.stderr); sys.exit(3)"]
    record = SpawnJob(ctrl, **spawn_kwargs(tmp_path, "t-raise", argv)).join()
    assert record["exit_code"] == 3
    assert record["exit_signal"] is None
    assert record["terminal_state"] == "FAILED_INCOMPLETE"
    stderr_tail = record.get("evidence", {}).get("stderr_tail", "")
    assert "boom-EVIDENCE-MARKER" in stderr_tail


# ------------------------------------------------------------------- H08-04
def test_h08_04a_timeout_escalation_timed_out(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    rec_i = SpawnJob(
        ctrl, **spawn_kwargs(tmp_path, "t-to-sleep", ["sleep", "30"], timeout_s=1.0)
    ).join()
    assert rec_i["terminal_state"] == "TIMED_OUT"
    ev = rec_i["evidence"]
    assert ev.get("sigterm_sent_utc")
    assert ev.get("reaped") is True
    assert rec_i["artifact_verification"]["ok"] is False

    argv = [
        PY, "-c",
        "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        "print('armed', flush=True); time.sleep(60)",
    ]
    rec_ii = SpawnJob(
        ctrl, **spawn_kwargs(tmp_path, "t-to-kill", argv, timeout_s=0.8)
    ).join()
    assert rec_ii["terminal_state"] == "TIMED_OUT"
    ev2 = rec_ii["evidence"]
    assert ev2.get("sigterm_sent_utc") and ev2.get("sigkill_sent_utc")
    assert rec_ii["exit_signal"] == signal.SIGKILL


def test_h08_04b_external_sigterm_signalled(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    job = SpawnJob(
        ctrl, **spawn_kwargs(tmp_path, "t-ext-term", ["sleep", "45"], timeout_s=20.0)
    )
    record = wait_for_identity(ctrl, "t-ext-term")
    os.kill(int(record["pid"]), signal.SIGTERM)  # external actor, exact pid
    final = job.join()
    assert final["terminal_state"] == "SIGNALLED"
    assert final["exit_signal"] == signal.SIGTERM
    assert final["exit_code"] is None
    assert final["evidence"].get("controller_sent_signals") is False
    assert final["artifact_verification"]["ok"] is False  # signals NEVER complete


# ------------------------------------------------------------------- H08-05
def test_h08_05_timeout_kills_exact_group_only(tmp_path: Path, guard: Any) -> None:
    ctrl = make_controller(tmp_path / "state", term_grace_s=0.4)
    sibling = guard.track_proc(
        subprocess.Popen(
            ["sleep", "20"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    )
    guard.track_pid(sibling.pid)
    inner = (
        "import subprocess, time\n"
        "gc = subprocess.Popen(['sleep', '30'])\n"
        "print('GC', gc.pid, flush=True)\n"
        "time.sleep(30)\n"
    )
    out_dir = tmp_path / "out" / "t-group"
    final = SpawnJob(
        ctrl,
        **spawn_kwargs(
            tmp_path, "t-group", [PY, "-c", inner], output_dir=str(out_dir), timeout_s=1.2
        ),
    ).join()
    assert final["terminal_state"] == "TIMED_OUT"
    assert final["evidence"].get("sigterm_sent_utc")
    log_text = (out_dir / "logs" / "worker_stdout.log").read_text(encoding="utf-8")
    gc_lines = [ln for ln in log_text.splitlines() if "GC " in ln]
    assert gc_lines, f"grandchild pid line missing from log: {log_text!r}"
    gc_pid = int(gc_lines[-1].split("GC")[1].strip().split()[0])
    guard.track_pid(gc_pid)
    assert wait_until(lambda: rc.ps_identity(final["pid"]) is None, timeout=5), "leader survived"
    assert wait_until(lambda: rc.ps_identity(gc_pid) is None, timeout=5), "grandchild orphaned"
    time.sleep(0.2)
    try:
        os.kill(sibling.pid, 0)
    except OSError as exc:
        raise AssertionError("unrelated sibling process group was killed") from exc


# ------------------------------------------------------------------- H08-06
def test_h08_06_resume_identity_match_and_reuse_rejection(tmp_path: Path, guard: Any) -> None:
    ctrl = make_controller(tmp_path / "state")
    # Simulate a worker whose original controller crashed: a live sleep in its
    # own session plus its persisted record; nobody supervises it.
    argv = ["sleep", "30"]
    orphan = guard.track_proc(
        subprocess.Popen(
            argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL, start_new_session=True,
        )
    )
    time.sleep(0.2)
    live = rc.ps_identity(orphan.pid)
    assert live is not None
    record = {
        "trial_id": "t-resume",
        "pid": orphan.pid,
        "pgid": live[1],
        "posix_start_identity": live[0],
        "command_hash": command_hash(argv),
        "command_argv": argv,
        "launch_sha": "a" * 64,
        "worktree": str(tmp_path / "wt"),
        "output_dir": str(tmp_path / "out" / "t-resume"),
        "phase": "BASE",
        "terminal_state": "RUNNING",
        "timestamps": {},
        "markers": {},
        "evidence": {},
        "supervision": {"controller_pid": 1, "resumed": False},
    }
    atomic_write_json(ctrl.record_path("t-resume"), record)
    identity = dict(
        pid=orphan.pid,
        posix_start_identity=live[0],
        command_hash_hex=record["command_hash"],
        worktree=str(tmp_path / "wt"),
    )
    matched = ctrl.match(**identity)
    assert matched["trial_id"] == "t-resume"
    with pytest.raises(IdentityMismatchError) as err_lstart:
        ctrl.match(**{**identity, "posix_start_identity": "Wed Jan  1 00:00:00 2025"})
    assert "posix_start_identity" in err_lstart.value.mismatches
    with pytest.raises(IdentityMismatchError) as err_hash:
        ctrl.match(**{**identity, "command_hash_hex": "f" * 64})
    assert "command_hash" in err_hash.value.mismatches
    # PID alone is insufficient: the correct pid plus wrong identity fields
    # is rejected as a mismatch, never matched.
    with pytest.raises(IdentityMismatchError) as err_pidonly:
        ctrl.match(
            pid=orphan.pid,
            posix_start_identity="x", command_hash_hex="y", worktree="z",
        )
    assert set(err_pidonly.value.mismatches) == {
        "posix_start_identity", "command_hash", "worktree"
    }
    # Full resume adopts the LIVE orphan (identity verified live via ps) and
    # enforces the re-frozen timeout on it.
    adopted = ctrl.resume(**identity, timeout_s=0.8)
    assert adopted["supervision"]["resumed"] is True
    assert adopted["terminal_state"] == "TIMED_OUT"
    assert wait_until(lambda: rc.ps_identity(orphan.pid) is None, timeout=5)

    # Resume refuses to double-supervise a trial this controller already owns.
    job = SpawnJob(
        ctrl, **spawn_kwargs(tmp_path, "t-live", ["sleep", "30"], timeout_s=5.0)
    )
    owned = wait_for_identity(ctrl, "t-live")
    with pytest.raises(rc.ControllerError):
        ctrl.resume(
            pid=int(owned["pid"]),
            posix_start_identity=str(owned["posix_start_identity"]),
            command_hash_hex=str(owned["command_hash"]),
            worktree=str(owned["worktree"]),
            trial_id="t-live",
            timeout_s=1.0,
        )
    stopped = ctrl.stop("t-live")
    assert stopped["terminal_state"] == "SIGNALLED"
    final = job.join()
    assert final["terminal_state"] == "SIGNALLED"

    # Resume against a DEAD unmatched worker reconciles honestly.
    dead_rec = dict(record)
    dead_rec["trial_id"] = "t-dead"
    dead_rec["pid"] = 2_000_000_000
    dead_rec["posix_start_identity"] = "Tue Jan  1 00:00:00 2035"
    atomic_write_json(ctrl.record_path("t-dead"), dead_rec)
    reconciled = ctrl.resume(
        pid=2_000_000_000,
        posix_start_identity="Tue Jan  1 00:00:00 2035",
        command_hash_hex=str(dead_rec["command_hash"]),
        worktree=str(dead_rec["worktree"]),
        trial_id="t-dead",
        timeout_s=1.0,
    )
    assert reconciled["terminal_state"] == "CONTROLLER_LOST"


# ------------------------------------------------------------------- H08-07
def test_h08_07_concurrent_workers_no_crossmatch(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    argv_a = [PY, "-c", "import time; print('AAA', flush=True); time.sleep(0.7)"]
    argv_b = [PY, "-c", "import time; print('BBB', flush=True); time.sleep(1.1)"]
    job_a = SpawnJob(
        ctrl, **spawn_kwargs(tmp_path, "t-con-a", argv_a, artifact_verifier=lambda rec: True)
    )
    job_b = SpawnJob(
        ctrl, **spawn_kwargs(tmp_path, "t-con-b", argv_b, artifact_verifier=lambda rec: True)
    )

    def both_running() -> bool:
        try:
            ra = ctrl.load_record("t-con-a")
            rb = ctrl.load_record("t-con-b")
        except rc.UnknownTrialError:
            return False
        return rc.ps_identity(ra["pid"]) is not None and rc.ps_identity(rb["pid"]) is not None

    assert wait_until(both_running, timeout=6)
    rec_a_mid = ctrl.load_record("t-con-a")
    rec_b_mid = ctrl.load_record("t-con-b")
    assert rec_a_mid["pid"] != rec_b_mid["pid"]
    assert rec_a_mid["pgid"] != rec_b_mid["pgid"]
    assert rec_a_mid["command_hash"] == command_hash(argv_a)
    assert rec_b_mid["command_hash"] == command_hash(argv_b)
    hb_a = load_json_safe(ctrl.heartbeat_path("t-con-a"))
    hb_b = load_json_safe(ctrl.heartbeat_path("t-con-b"))
    assert hb_a and hb_b and hb_a["trial_id"] == "t-con-a" and hb_b["trial_id"] == "t-con-b"
    final_a = job_a.join()
    final_b = job_b.join()
    for rec, argv, other, tag, anti in (
        (final_a, argv_a, final_b, "AAA", "BBB"),
        (final_b, argv_b, final_a, "BBB", "AAA"),
    ):
        assert rec["terminal_state"] == "COMPLETED"
        assert rec["command_argv"] == argv
        assert rec["pid"] != other["pid"]
        log_text = Path(rec["log_paths"]["stdout"]).read_text(encoding="utf-8")
        assert tag in log_text and anti not in log_text


# ------------------------------------------------------------------- H08-08
def test_h08_08_stale_heartbeat_warns_without_death(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    state_dir = tmp_path / "state"
    ctrl = make_controller(state_dir)
    old_iso = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() - 120))
    atomic_write_json(
        ctrl.record_path("t-stale"),
        {
            "trial_id": "t-stale",
            "pid": 2_000_000_001,
            "pgid": 2_000_000_001,
            "posix_start_identity": "Mon Aug 24 00:00:00 2026",
            "phase": "BASE",
            "terminal_state": "RUNNING",
            "last_heartbeat_utc": old_iso,
            "timestamps": {"spawned": old_iso, "last_heartbeat": old_iso},
        },
    )
    atomic_write_json(
        ctrl.heartbeat_path("t-stale"), {"trial_id": "t-stale", "heartbeat_utc": old_iso}
    )
    report = ctrl.stale_heartbeat("t-stale")
    assert report["stale"] is True
    assert report["warning"] and "may be alive" in report["warning"]
    assert load_json_safe(ctrl.record_path("t-stale"))["terminal_state"] == "RUNNING"
    assert not ctrl.terminal_path("t-stale").exists()  # staleness invented nothing
    rows = collect_rows(state_dir)
    row = next(r for r in rows if r["trial_id"] == "t-stale")
    assert row["stale_heartbeat"] is True and "may be alive" in row["note"]
    table = format_table(rows)
    assert "WARNING" in table and "t-stale" in table
    assert status_main(["--state-dir", str(state_dir), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    stale_rows = [r for r in payload if r["trial_id"] == "t-stale"]
    assert stale_rows and stale_rows[0]["state"] == "RUNNING"


# ------------------------------------------------------------------- H08-09
def test_h08_09_interrupted_atomic_write_parseable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "rec.json"
    atomic_write_json(target, {"v": 1})

    def boom(src: Any, dst: Any) -> None:
        raise OSError("simulated crash between tmp-write and replace")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        atomic_write_json(target, {"v": 2})
    monkeypatch.undo()
    assert load_json_safe(target) == {"v": 1}  # previous file untouched + parseable
    garbage = tmp_path / ".rec.json.deadbeef.tmp"
    garbage.write_text('{"v": 3, "trunc')
    assert load_json_safe(target) == {"v": 1}
    assert load_json_safe(garbage) is None  # partial tmp ignored safely
    atomic_write_json(target, {"v": 4})
    assert load_json_safe(target) == {"v": 4}


# ------------------------------------------------------------------- H08-10
def test_h08_10_death_after_base_partial_pre_score(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    base = tmp_path / "base_marker.json"
    script = (
        f"import os, signal\nopen({str(base)!r}, 'w').close()\n"
        "os.kill(os.getpid(), signal.SIGTERM)"
    )
    record = SpawnJob(
        ctrl,
        **spawn_kwargs(
            tmp_path, "t-partial", [PY, "-c", script],
            base_marker=lambda: base.exists(), stress_marker=None, timeout_s=8.0,
        ),
    ).join()
    assert record["terminal_state"] == "PARTIAL_PRE_SCORE"
    assert record["markers"]["base_reached"] is True
    assert record["markers"]["stress_reached"] is False
    assert record["exit_signal"] == signal.SIGTERM
    ev = record["evidence"]
    assert "not pipeline completion" in ev.get("base_only_timestamp_note", "")


# ------------------------------------------------------------------- H08-11
def test_h08_11_timeout_never_null(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    with pytest.raises(ValueError):
        ctrl.spawn([PY, "-c", "pass"], trial_id="t-null", launch_sha="x",
                   worktree=str(tmp_path), output_dir=str(tmp_path), timeout_s=None)
    with pytest.raises(ValueError):
        ctrl.resume(pid=1, posix_start_identity="x", command_hash_hex="y",
                    worktree=str(tmp_path), timeout_s=None)
    param = inspect.signature(WorkerController.spawn).parameters["timeout_s"]
    assert param.default is inspect.Parameter.empty  # callers MUST freeze a value
    # Production defaults are non-null and match the H03 contract.
    assert WorkerController.__init__.__defaults__ is not None or True
    fresh = WorkerController(tmp_path / "s2")
    assert fresh.term_grace_s == 30.0 and fresh.heartbeat_interval_s == 15.0
    assert rc.DEFAULT_TERM_GRACE_S == 30.0 and rc.DEFAULT_HEARTBEAT_INTERVAL_S == 15.0
    with pytest.raises(SystemExit):
        rc.main(["--state-dir", str(tmp_path / "s3"), "spawn", "--trial-id", "t-cli",
                 "sleep"])  # missing required --timeout-s


# ------------------------------------------------------------------- H08-12
def test_h08_12_log_readable_and_growing_while_alive(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    script = (
        "import time\n"
        "for i in range(60):\n"
        "    print('tick', i, flush=True)\n"
        "    time.sleep(0.03)\n"
    )
    job = SpawnJob(
        ctrl, **spawn_kwargs(
            tmp_path, "t-logs", [PY, "-c", script], artifact_verifier=lambda rec: True
        )
    )
    out_log = tmp_path / "out" / "t-logs" / "logs" / "worker_stdout.log"
    assert wait_until(lambda: out_log.exists() and out_log.stat().st_size > 0, timeout=8)
    first = out_log.stat().st_size
    head = out_log.read_bytes().decode("utf-8")[:64]
    assert "tick" in head and "T" in head.split(" ", 1)[0]  # timestamped line prefix
    assert wait_until(lambda: out_log.stat().st_size > first, timeout=8), "log not growing"
    assert wait_until(
        lambda: bool((load_json_safe(ctrl.record_path("t-logs")) or {}).get("last_log_at_utc")),
        timeout=8,
    )
    record = job.join()
    assert record["terminal_state"] == "COMPLETED"
    assert record["log_stats"]["stdout_bytes"] > 0
    assert record["last_log_at_utc"]


# --------------------------------------------------------------- extra units
def test_tail_rotating_log_bounds_size_and_keeps_tail(tmp_path: Path) -> None:
    log = TailRotatingLog(tmp_path / "r.log", max_bytes=400, keep_tail_bytes=120)
    for i in range(80):
        log.write_line(f"line-{i:03d} padding-padding".encode("utf-8"))
    log.close()
    data = (tmp_path / "r.log").read_bytes()
    assert log.rotations >= 1
    assert len(data) <= 600
    assert b"line-079" in data and b"line-000" not in data


def test_stop_signals_exact_group_only(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    job = SpawnJob(
        ctrl, **spawn_kwargs(tmp_path, "t-stop", ["sleep", "45"], timeout_s=60.0)
    )
    record = wait_for_identity(ctrl, "t-stop")
    stopped = ctrl.stop("t-stop")
    assert stopped["terminal_state"] == "SIGNALLED"  # controller-caused death
    assert stopped["evidence"].get("controller_sent_signals") is True
    assert stopped["evidence"].get("sigterm_sent_utc")
    final = job.join()
    assert final["terminal_state"] == "SIGNALLED"
    assert wait_until(lambda: rc.ps_identity(int(record["pid"])) is None, timeout=5)

