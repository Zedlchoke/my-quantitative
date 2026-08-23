"""A3 registry tests: append-only semantics, validation, monotonic order."""

from __future__ import annotations

import json

import pytest

from research.protocol.registry import append, load_all, verify_append_only


def test_append_creates_file_and_requires_fields(tmp_path):
    path = tmp_path / "registry" / "experiments.jsonl"
    stored = append({"experiment_id": "EXP-20260823-0001", "verdict": "FAIL"}, path)
    assert stored["experiment_id"] == "EXP-20260823-0001"
    assert path.exists()
    with pytest.raises(ValueError, match="verdict"):
        append({"experiment_id": "EXP-X"}, path)
    with pytest.raises(ValueError, match="experiment_id"):
        append({"verdict": "PASS"}, path)


def test_append_is_add_only_and_lines_are_valid_json(tmp_path):
    path = tmp_path / "experiments.jsonl"
    for i in range(3):
        append({"experiment_id": f"EXP-{i:04d}", "verdict": "PASS"}, path)
    before = path.read_bytes()
    append({"experiment_id": "EXP-9999", "verdict": "FAIL"}, path)
    after = path.read_bytes()
    assert after.startswith(before), "append must not rewrite existing bytes"
    lines = [json.loads(line) for line in after.decode().splitlines() if line]
    assert len(lines) == 4
    assert all("appended_at" in entry for entry in lines)
    assert load_all(path) == lines


def test_load_all_rejects_corrupt_line(tmp_path):
    path = tmp_path / "experiments.jsonl"
    append({"experiment_id": "EXP-1", "verdict": "PASS"}, path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{not-json\n")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_all(path)


def test_verify_append_only_detects_out_of_order_timestamps(tmp_path):
    path = tmp_path / "experiments.jsonl"
    append(
        {"experiment_id": "A", "verdict": "PASS", "appended_at": "2026-08-23T01:00:00+00:00"},
        path,
    )
    append(
        {"experiment_id": "B", "verdict": "PASS", "appended_at": "2026-08-23T02:00:00+00:00"},
        path,
    )
    assert verify_append_only(path) is True
    out_of_order = tmp_path / "bad.jsonl"
    entries = [
        {"experiment_id": "A", "verdict": "PASS", "appended_at": "2026-08-23T05:00:00+00:00"},
        {"experiment_id": "B", "verdict": "PASS", "appended_at": "2026-08-23T04:00:00+00:00"},
    ]
    with out_of_order.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")
    assert verify_append_only(out_of_order) is False


def test_verify_append_only_missing_stamp_raises(tmp_path):
    path = tmp_path / "experiments.jsonl"
    path.write_text(json.dumps({"experiment_id": "A", "verdict": "PASS"}) + "\n")
    with pytest.raises(ValueError, match="appended_at"):
        verify_append_only(path)


def test_load_all_missing_file_returns_empty(tmp_path):
    assert load_all(tmp_path / "nope.jsonl") == []
