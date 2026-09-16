import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from research.free_data_frontier.manifest import (
    deterministic_json_bytes,
    load_manifest,
    recompute_sha256,
    verify_manifest,
    write_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _record(tmp_raw, dataset_id, payload):
    raw_dir = tmp_raw / "raw"
    raw_dir.mkdir(exist_ok=True)
    raw = raw_dir / f"{dataset_id}.bin"
    raw.write_bytes(payload)
    return {
        "source_id": "s",
        "dataset_id": dataset_id,
        "canonical_request_id": "r" * 64,
        "source_url_redacted": "https://x/y",
        "retrieved_time_utc": "2026-09-16T00:00:00Z",
        "http_status": 200,
        "content_type": "application/octet-stream",
        "content_length": len(payload),
        "raw_path": str(raw),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "parser_version": "free_data_frontier@1",
        "authority_status": "PASS_SAMPLE",
        "event_time_utc": None,
        "effective_time_utc": None,
        "available_time_utc": None,
        "available_time_evidence": None,
        "vintage": None,
        "retrieval_time_only": True,
        "notes": [],
    }


def test_manifest_bytes_deterministic(tmp_path):
    records = [_record(tmp_path, "b", b"2"), _record(tmp_path, "a", b"1")]
    out1 = tmp_path / "m1.json"
    out2 = tmp_path / "m2.json"
    write_manifest(out1, records)
    write_manifest(out2, list(reversed(records)))
    assert out1.read_bytes() == out2.read_bytes()
    blob = deterministic_json_bytes({"z": 1, "a": [3, 2, 1]})
    assert blob.endswith(b"\n")
    assert json.loads(blob) == {"z": 1, "a": [3, 2, 1]}


def test_manifest_written_sorted_and_valid(tmp_path):
    records = [_record(tmp_path, "b", b"2"), _record(tmp_path, "a", b"1")]
    path = tmp_path / "manifest.json"
    write_manifest(path, records)
    loaded = load_manifest(path)
    assert [r["dataset_id"] for r in loaded] == ["a", "b"]


def test_verify_manifest_from_raw_bytes(tmp_path):
    records = [_record(tmp_path, "a", b"payload-1"), _record(tmp_path, "b", b"payload-2")]
    path = tmp_path / "manifest.json"
    write_manifest(path, records)
    report = verify_manifest(path)
    assert report["verdict"] == "ALL_MATCH"
    assert report["verified"] == 2

    # mutate one raw object -> mismatch
    target = Path(records[1]["raw_path"])
    target.write_bytes(b"tampered")
    report = verify_manifest(path)
    assert report["verdict"] == "MISMATCH_OR_MISSING"
    assert report["failed"] == 1


def test_verify_manifest_missing_raw(tmp_path):
    records = [_record(tmp_path, "a", b"payload")]
    path = tmp_path / "manifest.json"
    write_manifest(path, records)
    Path(records[0]["raw_path"]).unlink()
    report = verify_manifest(path)
    assert report["verdict"] == "MISMATCH_OR_MISSING"
    assert report["missing"] == 1


def test_recompute_sha256_matches_hashlib(tmp_path):
    payload = b"streaming-hash-check" * 5000
    p = tmp_path / "f.bin"
    p.write_bytes(payload)
    assert recompute_sha256(p) == hashlib.sha256(payload).hexdigest()


def test_no_raw_data_root_inside_repo():
    """Raw bytes live outside Git; the module must not reference a repo-raw path."""
    from research.free_data_frontier import contract

    source = Path(contract.__file__).read_text()
    assert ".worktrees" not in source
    assert "my-quantitative-data" not in source


def test_no_raw_files_tracked_in_git():
    """git ls-files must contain no raw/bulk artifact for this cycle."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = result.stdout.splitlines()
    offenders = [
        f
        for f in tracked
        if "free_data_frontier" in f and ("/raw/" in f or f.endswith(".zip"))
    ]
    assert offenders == []
