"""SHV1 G2 - transactional control-state IO fails closed (tests/test_atomic_io.py).

Sandboxed: every case runs on tmp_path fixtures; no real control file touched.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import atomic_io  # noqa: E402


def _validator(obj):
    if obj.get("kind") != "ok":
        raise atomic_io.SchemaValidationError("kind must be 'ok'")


def test_roundtrip_write_readback(tmp_path):
    p = tmp_path / "state.json"
    sha = atomic_io.atomic_write_json(p, {"kind": "ok", "v": 1}, schema_validator=_validator)
    assert p.exists()
    assert atomic_io.load_json_strict(p, schema_validator=_validator) == {"kind": "ok", "v": 1}
    assert sha == atomic_io.sha256_file(p)


def test_schema_validation_before_write_leaves_file_untouched(tmp_path):
    p = tmp_path / "state.json"
    p.write_text('{"kind": "ok"}\n')
    before = p.read_bytes()
    with pytest.raises(atomic_io.SchemaValidationError):
        atomic_io.atomic_write_json(p, {"kind": "bad"}, schema_validator=_validator)
    assert p.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp.*"))


def test_cas_mismatch_fails_closed(tmp_path):
    p = tmp_path / "state.json"
    atomic_io.atomic_write_json(p, {"kind": "ok", "v": 1}, schema_validator=_validator)
    stale = "0" * 64
    with pytest.raises(atomic_io.ControlStateDrift, match="CAS mismatch"):
        atomic_io.atomic_write_json(p, {"kind": "ok", "v": 2}, schema_validator=_validator,
                                    expect_prev_sha=stale)
    assert json.loads(p.read_text())["v"] == 1


def test_truncated_file_fails_closed(tmp_path):
    p = tmp_path / "state.json"
    p.write_text('{"kind": "ok", "v": 1, "secret_truncat')
    with pytest.raises(atomic_io.ControlStateDrift):
        atomic_io.load_json_strict(p, schema_validator=_validator)


def test_malformed_json_fails_closed(tmp_path):
    p = tmp_path / "state.json"
    p.write_text("not json at all {{{")
    with pytest.raises(atomic_io.ControlStateDrift):
        atomic_io.load_json_strict(p)


def test_missing_file_fails_closed(tmp_path):
    with pytest.raises(atomic_io.ControlStateDrift):
        atomic_io.load_json_strict(tmp_path / "absent.json")


def test_parallel_writer_fails_closed(tmp_path):
    """Second writer while the sidecar flock is held must fail, not interleave."""
    p = tmp_path / "state.json"
    atomic_io.atomic_write_json(p, {"kind": "ok", "v": 1}, schema_validator=_validator)
    holder = tmp_path / "holder.py"
    holder.write_text(
        "import fcntl, os, time\n"
        f"fd = os.open({str(tmp_path / 'state.json.lock')!r}, os.O_CREAT | os.O_RDWR)\n"
        "fcntl.flock(fd, fcntl.LOCK_EX)\n"
        "print('HELD', flush=True)\n"
        "time.sleep(5)\n"
    )
    proc = subprocess.Popen([sys.executable, str(holder)], stdout=subprocess.PIPE, text=True)
    try:
        assert proc.stdout.readline().strip() == "HELD"
        with pytest.raises(atomic_io.WriteLockBusy):
            atomic_io.atomic_write_json(p, {"kind": "ok", "v": 2}, schema_validator=_validator,
                                        lock_timeout=0.2)
        assert json.loads(p.read_text())["v"] == 1  # bytes untouched
    finally:
        proc.kill()
        proc.wait()


def test_event_journal_append_only(tmp_path):
    ev = tmp_path / "events.jsonl"
    atomic_io.append_event(ev, {"event": "A"})
    first = ev.read_bytes()
    atomic_io.append_event(ev, {"event": "B"})
    lines = ev.read_text().strip().splitlines()
    assert len(lines) == 2
    assert ev.read_bytes().startswith(first)  # history never rewritten
    assert json.loads(lines[1])["event"] == "B"
