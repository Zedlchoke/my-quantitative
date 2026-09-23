"""Frozen snapshot digest + shape (fail-closed)."""

import gzip
import json
import shutil
from pathlib import Path

import pytest

from psv1_spy.snapshot import (
    SNAPSHOT_PATH,
    SNAPSHOT_SHA256,
    SnapshotDigestMismatch,
    load_sessions,
    sha256_of_file,
    verify_snapshot,
)

SNAPSHOT_EXISTS = Path(SNAPSHOT_PATH).exists()

requires_snapshot = pytest.mark.skipif(
    not SNAPSHOT_EXISTS, reason="frozen SPY snapshot not present on this machine"
)


@requires_snapshot
def test_frozen_snapshot_digest_matches():
    assert sha256_of_file(SNAPSHOT_PATH) == SNAPSHOT_SHA256
    assert verify_snapshot(SNAPSHOT_PATH) == SNAPSHOT_SHA256


@requires_snapshot
def test_snapshot_shape_measured():
    sessions = load_sessions()
    assert len(sessions) == 2943
    assert sessions[0].date == "2015-01-02"
    assert sessions[-1].date == "2026-09-16"
    dates = [s.date for s in sessions]
    assert len(set(dates)) == len(dates)
    assert dates == sorted(dates)


def test_loader_fail_closed_on_digest_mismatch(tmp_path):
    # synthetic gzip payload with WRONG bytes must be rejected
    bad = tmp_path / "bad.json.gz"
    with gzip.open(bad, "wt") as f:
        json.dump([{"date": "2015-01-02", "open": 1, "high": 1, "low": 1,
                    "close": 1, "adjusted_close": 1, "volume": 1}], f)
    with pytest.raises(SnapshotDigestMismatch):
        load_sessions(str(bad), verify=True)


@requires_snapshot
def test_loader_fail_closed_on_tampered_snapshot_bytes(tmp_path):
    tampered = tmp_path / "tampered.json.gz"
    shutil.copyfile(SNAPSHOT_PATH, tampered)
    raw = bytearray(tampered.read_bytes())
    raw[-1] ^= 0xFF  # flip one bit at the tail of the gzip stream
    tampered.write_bytes(bytes(raw))
    with pytest.raises(SnapshotDigestMismatch):
        load_sessions(str(tampered), verify=True)
