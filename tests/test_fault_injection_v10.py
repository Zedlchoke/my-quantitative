"""A10 integration-level adversarial suite (sprint V9H→V10 wave-H2, gate H-5/H-8).

Attacks the INTEGRATED stack beyond the A3/A4 unit suites:

* gate H-5: TEN consecutive timeout/orphan rounds through
  ``WorkerController`` — child+grandchild, sub-second frozen timeout,
  exact-group kill every round, zero orphans after each round (verified via
  ``ps -o pgid=`` filtering by the RECORDED pgid only; never pgrep/pkill),
  while an unrelated control process group survives all ten rounds.
* over-cap admission storm (3 near-simultaneous admits, cap=1 and
  probe-less cap=2 forced to 1).
* governor RAM-shrink + lower-only-after-pnl-seen lock.
* PARTIAL_PRE_SCORE end-to-end: real child completes BASE phase marker and
  base artifacts, then dies by SIGKILL before STRESS — classification
  precedence over UNKNOWN_EXTERNAL_KILL, base artifacts preserved, no score
  published marker.
* cross-match storm: three concurrent workers with seeded randomly delayed
  heartbeats/terminations; records never cross-contaminate.
* cache parity end-to-end: producer subprocess run cache-off vs cache-on
  through ``run_streamed`` twice → byte-equal sha256 manifests; tampering
  one artifact makes ``SharedCacheMergeGate`` reject.
* atomic-write crash injection across BOTH production writers (governor
  state + controller records): crash between tmp-write and os.replace
  leaves previous state parseable; retry succeeds.

Synthetic fixtures/probes only: no network, no scored backtests, no
name-based process matching anywhere. Identity-based checks only.
"""

from __future__ import annotations

import json
import os
import random
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest

from research import runtime_controller_v10 as rc
from research.cache_v10 import SharedCacheMergeGate
from research.reproduction_stream_v10 import read_state, run_streamed
from research.resource_governor_v10 import (
    OverCapacityError,
    PromotionLockedError,
    ResourceGovernorV10,
    freeze,
)
from research.runtime_controller_v10 import (
    WorkerController,
    atomic_write_json,
    command_hash,
    load_json_safe,
)

PY = sys.executable


# ------------------------------------------------------------------- helpers
def make_controller(state_dir: Path, **overrides: Any) -> WorkerController:
    kwargs: Dict[str, Any] = {
        "poll_interval_s": 0.05,
        "heartbeat_interval_s": 0.25,
        "term_grace_s": 0.35,
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

    def join(self, timeout: float = 60.0) -> Dict[str, Any]:
        self._thread.join(timeout=timeout)
        assert not self._thread.is_alive(), "spawn thread did not finish"
        if self.exc is not None:
            raise self.exc
        assert self.result is not None
        return self.result


def spawn_kwargs(tmp_path: Path, trial: str, argv: List[str], **overrides: Any) -> Dict[str, Any]:
    (tmp_path / "wt").mkdir(parents=True, exist_ok=True)
    kw: Dict[str, Any] = {
        "cmd_argv": argv,
        "trial_id": trial,
        "launch_sha": "b" * 64,
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


def pgid_members(pgid: int) -> List[int]:
    """Live pids whose process group id equals the RECORDED ``pgid``.

    Identity-based orphan check only: one full-table `ps` snapshot filtered
    by the exact recorded pgid. No pgrep/pkill/name matching anywhere.
    """
    proc = subprocess.run(
        ["ps", "-A", "-o", "pid=", "-o", "pgid="],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, f"ps table probe failed: {proc.stderr}"
    members: List[int] = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == str(pgid):
            members.append(int(parts[0]))
    return members


@pytest.fixture()
def control_group():
    """Unrelated long-lived process group that must survive every round."""
    proc = subprocess.Popen(
        [PY, "-c", "import time; time.sleep(180)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.monotonic() + 5
    ident = None
    while time.monotonic() < deadline:
        ident = rc.ps_identity(proc.pid)
        if ident:
            break
        time.sleep(0.05)
    assert ident is not None, "control group identity never captured"
    try:
        yield {"pid": proc.pid, "pgid": ident[1]}
    finally:
        try:
            os.killpg(ident[1], signal.SIGKILL)
        except OSError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.SubprocessError:
            pass


# ------------------------------------------------------------------ gate H-5
def test_gate_h5_ten_consecutive_timeout_orphan_rounds(
    tmp_path: Path, control_group: Dict[str, int]
) -> None:
    ctrl = make_controller(tmp_path / "state")
    control_pid = int(control_group["pid"])
    control_pgid = int(control_group["pgid"])

    for round_index in range(10):
        trial = f"ft-orphan-r{round_index}"
        ignores_term = round_index % 2 == 1
        arm = "signal.signal(signal.SIGTERM, signal.SIG_IGN); " if ignores_term else ""
        inner = (
            "import signal, subprocess, sys, time\n"
            f"{arm}"
            "gc = subprocess.Popen(['sleep', '60'])\n"
            "print('GC_PID', gc.pid, flush=True)\n"
            "time.sleep(60)\n"
        )
        out_dir = tmp_path / "out" / trial
        record = SpawnJob(
            ctrl,
            **spawn_kwargs(
                tmp_path, trial, [PY, "-c", inner],
                output_dir=str(out_dir), timeout_s=0.85,
            ),
        ).join()

        assert record["terminal_state"] == "TIMED_OUT", f"round {round_index}"
        evidence = record["evidence"]
        assert evidence.get("sigterm_sent_utc"), f"round {round_index}: no SIGTERM evidence"
        assert evidence.get("reaped") is True, f"round {round_index}: leader not reaped"
        if ignores_term:
            assert evidence.get("sigkill_sent_utc"), f"round {round_index}: escalation missing"
            assert record["exit_signal"] == int(signal.SIGKILL)

        recorded_pgid = int(record["pgid"])
        assert recorded_pgid > 1
        log_text = (out_dir / "logs" / "worker_stdout.log").read_text(encoding="utf-8")
        gc_lines = [ln for ln in log_text.splitlines() if "GC_PID" in ln]
        assert gc_lines, f"round {round_index}: grandchild pid line missing"
        gc_pid = int(gc_lines[-1].split("GC_PID")[1].strip().split()[0])

        assert wait_until(
            lambda pgid=recorded_pgid: not pgid_members(pgid), timeout=8
        ), f"round {round_index}: orphans with pgid {recorded_pgid}: {pgid_members(recorded_pgid)}"
        assert rc.ps_identity(int(record["pid"])) is None, f"round {round_index}: leader alive"
        assert rc.ps_identity(gc_pid) is None, f"round {round_index}: grandchild {gc_pid} orphaned"

        try:
            os.kill(control_pid, 0)
        except OSError as exc:
            raise AssertionError(
                f"round {round_index}: unrelated control group was killed"
            ) from exc
        survivors = [pid for pid in pgid_members(control_pgid) if pid == control_pid]
        assert survivors == [control_pid], (
            f"round {round_index}: control group membership disturbed: "
            f"{pgid_members(control_pgid)}"
        )


# ------------------------------------------------------- over-cap admission
class AdmissionStorm:
    """Near-simultaneous admit_worker attempts sharing one active counter."""

    def __init__(self, governor: ResourceGovernorV10, workers: int) -> None:
        self.governor = governor
        self.active = 0
        self.lock = threading.Lock()
        self.barrier = threading.Barrier(workers)
        self.accepted: List[int] = []
        self.rejected: List[str] = []
        self.threads: List[threading.Thread] = []

    def _attempt(self) -> None:
        self.barrier.wait(timeout=10)
        try:
            with self.lock:
                self.governor.admit_worker(self.active)
                self.active += 1
                self.accepted.append(self.active)
        except OverCapacityError as exc:
            with self.lock:
                self.rejected.append(str(exc))

    def fire(self) -> None:
        self.threads = [
            threading.Thread(target=self._attempt, daemon=True) for _ in range(self.barrier.parties)
        ]
        for thread in self.threads:
            thread.start()
        for thread in self.threads:
            thread.join(timeout=15)
            assert not thread.is_alive(), "admission attempt hung"


def test_over_cap_admission_storm_cap_one_accepts_exactly_one() -> None:
    governor = freeze(
        cap_contract=1,
        reserved_ram_gb=2.0,
        measured_peak_worker_ram_gb=1.0,
        available_ram_gb=64.0,
    )
    storm = AdmissionStorm(governor, workers=3)
    storm.fire()
    assert len(storm.accepted) == 1, f"accepted={storm.accepted} rejected={storm.rejected}"
    assert len(storm.rejected) == 2
    for reason in storm.rejected:
        assert "effective_heavy_workers=1" in reason
    assert storm.active == 1

    storm.active = 0
    governor.admit_worker(0)
    with pytest.raises(OverCapacityError):
        governor.admit_worker(1)


def test_cap_two_without_probe_evidence_is_forced_to_one(tmp_path: Path) -> None:
    state_path = tmp_path / "governor_state.json"
    governor = freeze(
        cap_contract=2,
        reserved_ram_gb=2.5,
        measured_peak_worker_ram_gb=1.0,
        available_ram_gb=64.0,
        state_path=str(state_path),
    )
    assert governor.effective_heavy_workers == 1
    with pytest.raises(OverCapacityError):
        governor.admit_worker(1)
    for _ in range(3):
        governor.record_two_worker_probe(safe=True, detail="a10 synthetic probe")
    assert governor.effective_heavy_workers == 2
    governor.admit_worker(0)
    governor.admit_worker(1)
    with pytest.raises(OverCapacityError):
        governor.admit_worker(2)

    restored = ResourceGovernorV10.load_state(state_path)
    assert restored.consecutive_safe_two_worker_probes == 3
    assert restored.effective_heavy_workers == 2


# ------------------------------------------------------------- RAM shrink
def test_governor_ram_shrink_and_lower_only_after_pnl_lock(tmp_path: Path) -> None:
    state_path = tmp_path / "freeze.json"

    def rebuild_from(prev: ResourceGovernorV10, available_gb: float) -> ResourceGovernorV10:
        return ResourceGovernorV10(
            contract_cap=prev.contract_cap,
            reserved_ram_gb=2.0,
            measured_peak_worker_ram_gb=1.0,
            available_ram_gb=available_gb,
            available_method="injected",
            state_path=str(state_path),
            probe_records=list(prev.probe_records),
            pnl_visible=prev.pnl_visible,
            cap_snapshot_at_pnl=prev.cap_snapshot_at_pnl,
        )

    current = freeze(
        cap_contract=4,
        reserved_ram_gb=2.0,
        measured_peak_worker_ram_gb=1.0,
        available_ram_gb=32.0,
        state_path=str(state_path),
    )
    assert current.ram_cap_workers == 30
    assert current.effective_heavy_workers == 1
    for i in range(3):
        current.record_two_worker_probe(safe=True, detail=f"probe-{i}")
    assert current.effective_heavy_workers == 4

    shrunk = rebuild_from(current, available_gb=2.5)
    assert shrunk.ram_cap_workers == 0
    assert shrunk.effective_heavy_workers == 0
    with pytest.raises(OverCapacityError):
        shrunk.admit_worker(0)

    current = rebuild_from(current, available_gb=4.0)
    current.declare_pnl_visible(note="A10 synthetic pnl visibility")
    assert current.cap_snapshot_at_pnl == 2

    raised_contract = rebuild_from(current, available_gb=32.0)
    assert raised_contract.effective_heavy_workers <= current.cap_snapshot_at_pnl
    with pytest.raises(PromotionLockedError):
        raised_contract.record_two_worker_probe(safe=True, detail="raise attempt")
    raised_record = raised_contract.record_two_worker_probe(
        safe=False, detail="unsafe probe still recordable"
    )
    assert raised_record["safe"] is False
    raised_contract.set_contract_cap(16)
    assert raised_contract.effective_heavy_workers <= current.cap_snapshot_at_pnl

    deep = rebuild_from(raised_contract, available_gb=0.5)
    assert deep.effective_heavy_workers == 0

    restored = ResourceGovernorV10.load_state(state_path)
    assert restored.pnl_visible is True
    assert restored.effective_heavy_workers <= current.cap_snapshot_at_pnl
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["reserved_ram_gb"] >= 2.0
    assert payload["cap_snapshot_at_pnl"] == current.cap_snapshot_at_pnl


# ------------------------------------------------------ PARTIAL_PRE_SCORE
def test_partial_pre_score_end_to_base_death_preserves_artifacts(tmp_path: Path) -> None:
    ctrl = make_controller(tmp_path / "state")
    out_dir = tmp_path / "out" / "ft-partial"
    out_dir.mkdir(parents=True)
    base_payload = {"status": "base_done", "rows": [i * 3 for i in range(64)]}
    script = (
        "import json, os, signal, time\n"
        f"out = {str(out_dir)!r}\n"
        "open(os.path.join(out, 'PREPARE.marker'), 'w').write('prep')\n"
        f"payload = {base_payload!r}\n"
        "with open(os.path.join(out, 'base_artifact.json'), 'w') as fh:\n"
        "    json.dump(payload, fh, sort_keys=True)\n"
        "open(os.path.join(out, 'BASE.marker'), 'w').write('base')\n"
        "time.sleep(0.05)\n"
        "os.kill(os.getpid(), signal.SIGKILL)\n"
        "time.sleep(30)\n"
    )
    record = SpawnJob(
        ctrl,
        **spawn_kwargs(
            tmp_path, "ft-partial", [PY, "-c", script], output_dir=str(out_dir),
            timeout_s=12.0,
            base_marker=lambda: (out_dir / "BASE.marker").exists(),
            stress_marker=lambda: (out_dir / "STRESS.marker").exists(),
        ),
    ).join()

    assert record["terminal_state"] == "PARTIAL_PRE_SCORE"
    assert record["markers"]["base_reached"] is True
    assert record["markers"]["stress_reached"] is False
    assert record["exit_signal"] == int(signal.SIGKILL)
    assert record["artifact_verification"].get("ok") is False
    evidence = record["evidence"]
    assert "STRESS" in evidence.get("partial_reason", "")
    assert "not pipeline completion" in evidence.get("base_only_timestamp_note", "")

    persisted = json.loads((out_dir / "base_artifact.json").read_text(encoding="utf-8"))
    assert persisted == base_payload
    assert not (out_dir / "score_published.json").exists()
    terminal = load_json_safe(ctrl.terminal_path("ft-partial"))
    assert terminal is not None and terminal["terminal_state"] == "PARTIAL_PRE_SCORE"
    flat = json.dumps(terminal, sort_keys=True)
    assert '"COMPLETED"' not in flat


# -------------------------------------------------------- cross-match storm
def test_cross_match_storm_three_concurrent_workers_never_contaminated(
    tmp_path: Path,
) -> None:
    rng = random.Random(90210826)
    ctrl = make_controller(tmp_path / "state")

    plans = {
        "ft-xm-a": {"delay_s": 0.9, "hb": 0.05, "outcome": "COMPLETE"},
        "ft-xm-b": {"delay_s": rng.uniform(6.0, 9.0), "hb": 0.04, "outcome": "EXTERNAL_TERM"},
        "ft-xm-c": {"delay_s": 30.0, "hb": 0.03, "outcome": "TIMEOUT"},
    }
    tags = {tid: f"TAG<{tid.upper()}>" for tid in plans}
    jobs: Dict[str, SpawnJob] = {}
    artifacts: Dict[str, Path] = {}

    for tid, plan in plans.items():
        tag = tags[tid]
        art = tmp_path / "artifacts" / f"{tid}.json"
        artifacts[tid] = art
        body = (
            "import json, os, sys, time\n"
            f"tag = {tag!r}\n"
            f"delay = {plan['delay_s']!r}\n"
            f"hb = {plan['hb']!r}\n"
            f"art = {str(art)!r}\n"
            "steps = max(1, int(delay / hb))\n"
            "for i in range(steps):\n"
            "    print(f'{tag} hb {{}}'.format(i), flush=True)\n"
            "    time.sleep(hb)\n"
            "os.makedirs(os.path.dirname(art), exist_ok=True)\n"
            "with open(art, 'w') as fh:\n"
            "    json.dump({'owner': tag}, fh, sort_keys=True)\n"
            "print(f'{tag} done', flush=True)\n"
        )
        verifier = self_verifier(tid, tag, art)
        job = SpawnJob(
            ctrl,
            **spawn_kwargs(
                tmp_path, tid, [PY, "-c", body],
                output_dir=str(tmp_path / "out" / tid),
                artifact_verifier=verifier,
                timeout_s=0.8 if plan["outcome"] == "TIMEOUT" else 20.0,
            ),
        )
        jobs[tid] = job
        time.sleep(rng.uniform(0.0, 0.12))

    rec_b = wait_for_identity(ctrl, "ft-xm-b", timeout=6)
    time.sleep(rng.uniform(0.15, 0.3))
    os.kill(int(rec_b["pid"]), signal.SIGTERM)

    finals = {tid: job.join() for tid, job in jobs.items()}

    expected_states = {
        "ft-xm-a": "COMPLETED",
        "ft-xm-b": "SIGNALLED",
        "ft-xm-c": "TIMED_OUT",
    }
    seen_ids: List[str] = []
    for tid, record in finals.items():
        seen_ids.append(str(record["trial_id"]))
        expected = expected_states[tid]
        actual = record["terminal_state"]
        assert actual == expected, f"{tid}: designed {expected}, got {actual}"
        tag = tags[tid]
        own_log = Path(record["log_paths"]["stdout"]).read_text(encoding="utf-8")
        assert tag in own_log, f"{tid}: own tag missing from own log"
        for other_id, other_tag in tags.items():
            if other_id != tid:
                assert other_tag not in own_log, f"{tid}: log contaminated by {other_id}"
        hb = load_json_safe(ctrl.heartbeat_path(tid))
        assert hb is not None and hb["trial_id"] == tid
        assert int(hb["pgid"]) == int(record["pgid"])
        assert record["command_hash"] == command_hash(record["command_argv"])
        if plans[tid]["outcome"] == "EXTERNAL_TERM":
            assert record["exit_signal"] == int(signal.SIGTERM)
            assert record["evidence"].get("controller_sent_signals") is False
        if plans[tid]["outcome"] == "COMPLETED":
            assert json.loads(artifacts[tid].read_text())["owner"] == tags[tid]
        if plans[tid]["outcome"] == "TIMEOUT":
            assert finals[tid]["evidence"].get("sigterm_sent_utc")

    assert sorted(seen_ids) == sorted(plans), "terminal records crossed trials"
    ids = [(finals[t]["pid"], finals[t]["pgid"]) for t in plans]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            assert ids[i][0] != ids[j][0] and ids[i][1] != ids[j][1]


def self_verifier(expected_trial: str, expected_tag: str, artifact: Path) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def verify(record: Dict[str, Any]) -> Dict[str, Any]:
        if record.get("trial_id") != expected_trial:
            return {
                "ok": False,
                "detail": {"error": f"CROSS_MATCH: verifier for {expected_trial} saw {record.get('trial_id')}"},
            }
        joined = " ".join(map(str, record.get("command_argv") or []))
        if expected_tag not in joined:
            return {"ok": False, "detail": {"error": f"CROSS_MATCH: argv lacks {expected_tag}"}}
        if not artifact.exists():
            return {"ok": False, "detail": {"error": "own artifact missing"}}
        try:
            if json.loads(artifact.read_text()).get("owner") != expected_tag:
                return {"ok": False, "detail": {"error": "artifact owner mismatch"}}
        except ValueError:
            return {"ok": False, "detail": {"error": "artifact unreadable"}}
        return {"ok": True, "detail": {"verified_trial": expected_trial}}

    return verify


# ------------------------------------------------------------ cache parity
PRODUCER_SOURCE = """\
import csv
import hashlib
import json
import os
import time

out_dir = os.environ["PRODUCER_OUT"]
cache_mode = os.environ.get("CACHE_MODE", "unset")
os.makedirs(out_dir, exist_ok=True)

inputs = {
    "data_catalog_hash": "cat-hash-0001",
    "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    "window_start": "2025-01-01T00:00:00Z",
    "window_end": "2025-02-01T00:00:00Z",
    "bar_type": "15m",
    "funding_model": "v1",
    "signal_inputs": {"ma_window": 14, "dead_zone": 0.0},
}

with open(os.path.join(out_dir, "inputs.json"), "w") as fh:
    json.dump(inputs, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\\n")

rows = []
aggregate = 0
for sym in sorted(inputs["symbols"]):
    digest = hashlib.sha256(
        (sym + "|" + inputs["window_end"] + "|%d" % inputs["signal_inputs"]["ma_window"]).encode()
    ).hexdigest()
    rows.append({"symbol": sym, "schedule_hash": digest})
    aggregate += sum(ord(ch) for ch in digest[:16])

with open(os.path.join(out_dir, "signal_schedule.csv"), "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=["symbol", "schedule_hash"])
    writer.writeheader()
    for row in sorted(rows, key=lambda r: r["symbol"]):
        writer.writerow(row)

with open(os.path.join(out_dir, "metrics.json"), "w") as fh:
    json.dump({"aggregate": aggregate, "n_rows": len(rows)}, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\\n")

print("PRODUCER DONE cache_mode=%s" % cache_mode, flush=True)
time.sleep(0.02)
"""


def test_cache_parity_end_to_end_off_vs_on_then_tamper_rejected(tmp_path: Path) -> None:
    producer = tmp_path / "producer.py"
    producer.write_text(PRODUCER_SOURCE, encoding="utf-8")
    logs_root = tmp_path / "logs"
    arts = {
        "off": tmp_path / "artifacts_cache_off",
        "on": tmp_path / "artifacts_cache_on",
    }

    results = {}
    for mode, art_dir in arts.items():
        result = run_streamed(
            [PY, str(producer)],
            log_dir=log_dirs(logs_root, mode),
            phase_label="BASE",
            timeout_s=60,
            env={"PRODUCER_OUT": str(art_dir), "CACHE_MODE": mode},
            cwd=str(tmp_path),
        )
        results[mode] = result
        assert result.terminal_state == "EXITED", f"{mode}: {result.tail_excerpt}"
        assert result.exit_code == 0, f"{mode}: tail={result.tail_excerpt}"
        assert art_dir.is_dir() and (art_dir / "metrics.json").exists()
        state = read_state(result.state_path)
        assert state is not None and state["timed_out"] is False

    gate = SharedCacheMergeGate()
    parity, why = gate.parity_from_dirs(arts["on"], arts["off"])
    assert parity is True and why is None, f"parity failed: {why}"
    on_manifest = gate.sha256_manifest(arts["on"])
    off_manifest = gate.sha256_manifest(arts["off"])
    assert on_manifest == off_manifest and len(on_manifest) >= 3

    decision = gate.evaluate(
        parity_dirs=(arts["on"], arts["off"]),
        repro_all_match=True,
        raw_reads=1,
        wall_time_cached_s=1.0,
        wall_time_uncached_s=4.0,
        strict=True,
    )
    assert decision["adopted"] is True and decision["reasons"] == []

    (arts["on"] / "metrics.json").write_text(
        (arts["on"] / "metrics.json").read_text(encoding="utf-8") + '{"tampered": true}\n',
        encoding="utf-8",
    )
    parity_bad, why_bad = gate.parity_from_dirs(arts["on"], arts["off"])
    assert parity_bad is False and "metrics.json" in (why_bad or "")

    rejected = gate.evaluate(
        parity_dirs=(arts["on"], arts["off"]),
        repro_all_match=True,
        raw_reads=1,
        wall_time_cached_s=1.0,
        wall_time_uncached_s=4.0,
        strict=True,
    )
    assert rejected["adopted"] is False
    assert any("artifact_manifest_mismatch" in reason for reason in rejected["reasons"])


def log_dirs(root: Path, mode: str) -> Path:
    path = root / mode
    path.mkdir(parents=True, exist_ok=True)
    return path


# ----------------------------------------------- atomic-write crash injection
def test_atomic_write_crash_between_tmp_and_replace_recovers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "freeze_crash.json"
    governor = freeze(
        cap_contract=2,
        reserved_ram_gb=2.0,
        measured_peak_worker_ram_gb=1.0,
        available_ram_gb=8.0,
        state_path=str(state_path),
    )
    before = json.loads(state_path.read_text(encoding="utf-8"))
    assert before["pnl_visible"] is False

    real_replace = os.replace
    calls = {"n": 0}

    def flaky_replace(src: Any, dst: Any) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("injected crash between tmp-write and os.replace")
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky_replace)
    with pytest.raises(OSError):
        governor.save_state()
    monkeypatch.undo()

    after_crash = json.loads(state_path.read_text(encoding="utf-8"))
    assert after_crash == before
    restored = ResourceGovernorV10.load_state(state_path)
    assert restored.pnl_visible is False and restored.contract_cap == 2

    governor.declare_pnl_visible(note="retry after injected crash")
    retried = json.loads(state_path.read_text(encoding="utf-8"))
    assert retried["pnl_visible"] is True
    assert ResourceGovernorV10.load_state(state_path).cap_snapshot_at_pnl is not None
    for litter in state_path.parent.glob(".*.tmp"):
        assert litter.name != state_path.name

    ctrl = make_controller(tmp_path / "state_ctrl")
    record_path = ctrl.record_path("ft-crash-rec")
    atomic_write_json(record_path, {"trial_id": "ft-crash-rec", "v": 1})

    calls2 = {"n": 0}

    def flaky_once(src: Any, dst: Any) -> None:
        calls2["n"] += 1
        if calls2["n"] == 1:
            raise OSError("injected crash on record replace")
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky_once)
    with pytest.raises(OSError):
        atomic_write_json(record_path, {"trial_id": "ft-crash-rec", "v": 2})
    monkeypatch.undo()

    assert load_json_safe(record_path) == {"trial_id": "ft-crash-rec", "v": 1}
    assert [r["trial_id"] for r in ctrl.load_records()] == ["ft-crash-rec"]
    atomic_write_json(record_path, {"trial_id": "ft-crash-rec", "v": 2})
    assert load_json_safe(record_path) == {"trial_id": "ft-crash-rec", "v": 2}
