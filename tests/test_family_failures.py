"""Tests for the FAMILY_FAILURES registry and its validator.

The registry is the program's failure memory (owner amendment 2026-09-07):
every entry must trace to a closed terminal artifact, TECHABORT-class
entries carry no family-quality evidence, and a TERMINAL_PENDING entry
(the V15 case) must not finalize any failure field.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.governance.validate_family_failures import (
    SCHEMA,
    load_registry,
    validate_entry,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "research" / "wayfinder" / "FAMILY_FAILURES.jsonl"


def _base_entry(**over):
    entry = {
        "schema": SCHEMA,
        "cycle_id": "X-V1",
        "asset": "crypto",
        "family_id": "TEST-FAM",
        "family_title": "t",
        "status": "CLOSED",
        "verdict_class": "SCIENTIFIC_REJECTION",
        "no_quality_evidence": False,
        "primary_failure": {"code": "EXPECTANCY_NONPOSITIVE", "detail": "d"},
        "secondary_failures": [],
        "measured_summary": "s",
        "evidence": {
            "terminal_sha": "a" * 40,
            "evidence_path": "research/control/x_run/terminal.json",
            "ledger_row": "HYPOTHESIS_LEDGER.md §A",
        },
        "unknown_fields": [],
        "recorded_by": "Lead",
        "recorded_utc": "2026-09-07T00:00:00Z",
    }
    entry.update(over)
    return entry


def test_valid_entry_passes():
    assert validate_entry(_base_entry(), 1) == []


def test_bad_verdict_class_rejected():
    errs = validate_entry(_base_entry(verdict_class="REJECTED"), 1)
    assert any("verdict_class" in e for e in errs)


def test_missing_primary_failure_rejected():
    errs = validate_entry(_base_entry(primary_failure=None), 1)
    assert any("primary_failure" in e for e in errs)


def test_unknown_signature_code_rejected():
    errs = validate_entry(
        _base_entry(primary_failure={"code": "MADE_UP_CODE", "detail": "d"}), 1
    )
    assert any("signature code" in e for e in errs)


def test_techabort_carries_no_quality_evidence_flag():
    ok = validate_entry(
        _base_entry(verdict_class="TECHABORT", no_quality_evidence=True), 1
    )
    assert ok == []
    errs = validate_entry(
        _base_entry(verdict_class="TECHABORT", no_quality_evidence=False), 1
    )
    assert any("no_quality_evidence" in e for e in errs)


def test_terminal_pending_must_not_finalize_failures():
    pending = _base_entry(
        status="TERMINAL_PENDING",
        verdict_class=None,
        no_quality_evidence=True,
        primary_failure=None,
        secondary_failures=[],
    )
    assert validate_entry(pending, 1) == []
    errs = validate_entry(
        _base_entry(status="TERMINAL_PENDING", verdict_class=None, no_quality_evidence=True),
        1,
    )
    assert any("primary_failure" in e or "TERMINAL_PENDING" in e for e in errs)


def test_short_sha_rejected_and_null_needs_declaration():
    errs = validate_entry(
        _base_entry(evidence={"terminal_sha": "abc123", "evidence_path": "p", "ledger_row": None}),
        1,
    )
    assert any("40-hex" in e for e in errs)
    errs = validate_entry(
        _base_entry(
            evidence={"terminal_sha": None, "evidence_path": "p", "ledger_row": None},
        ),
        1,
    )
    assert any("unknown_fields" in e for e in errs)


def test_evidence_requires_path_or_ledger_row():
    errs = validate_entry(
        _base_entry(evidence={"terminal_sha": "a" * 40, "evidence_path": None, "ledger_row": None}),
        1,
    )
    assert any("evidence_path or ledger_row" in e for e in errs)


def test_duplicate_family_id_detected(tmp_path):
    reg = tmp_path / "r.jsonl"
    entry = _base_entry()
    reg.write_text(json.dumps(entry) + "\n" + json.dumps(entry) + "\n", encoding="utf-8")
    _, errors = load_registry(reg)
    assert any("duplicate family_id" in e for e in errors)


def test_real_registry_validates():
    assert REGISTRY.exists(), f"missing registry at {REGISTRY}"
    entries, errors = load_registry(REGISTRY)
    assert not errors, errors
    assert len(entries) >= 40
    classes = {e["verdict_class"] for e in entries if e["status"] == "CLOSED"}
    assert classes <= {
        "SCIENTIFIC_REJECTION",
        "DATA_BLOCK",
        "SELECTION_REJECTION",
        "TECHABORT",
        "PROCESS_INCIDENT",
        "NOT_RUN_SUPERSEDED",
    }


def test_real_registry_v15_is_terminal_pending_only():
    entries, _ = load_registry(REGISTRY)
    v15 = [e for e in entries if e["cycle_id"] == "CRYPTO-V15"]
    assert len(v15) == 1
    assert v15[0]["status"] == "TERMINAL_PENDING"
    assert v15[0]["verdict_class"] is None
    assert v15[0]["primary_failure"] is None


def test_real_registry_sprint_entries_declare_unknown_sha():
    entries, _ = load_registry(REGISTRY)
    sprints = [e for e in entries if e["asset"] == "sprint"]
    assert sprints
    for entry in sprints:
        assert entry["evidence"]["terminal_sha"] is None
        assert "terminal_sha" in entry["unknown_fields"]


@pytest.mark.parametrize(
    "code",
    [
        "CONTROL_OUTEARNED_ANCHOR",
        "CONTROL_REPRODUCED_MECHANISM",
        "FOLD_CONCENTRATION_OVER_LIMIT",
        "PIT_UNEVIDENCED",
        "COST_DOMINATED",
        "ETF_SHARE_SECTOR_DROWNING",
    ],
)
def test_real_registry_uses_core_signatures(code):
    entries, _ = load_registry(REGISTRY)
    used = {e["primary_failure"]["code"] for e in entries if e["primary_failure"]}
    used |= {s["code"] for e in entries for s in e["secondary_failures"]}
    assert code in used
