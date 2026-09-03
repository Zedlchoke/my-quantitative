"""Snapshot pin revalidation and license-evidence revalidation.

All filesystem fixtures are SYNTHETIC (built under pytest ``tmp_path``); the
real-snapshot integration cases live in ``test_real_snapshot.py`` and skip
when the V2 staging directory is absent.  Nothing here performs network I/O
and no credential is ever read or printed.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from research.stocks_free_v3.authority import (
    ISSUER_DISTRIBUTION_RECORDS_SHA256,
    MANIFEST_PIN,
    SNAPSHOT_PINS,
    S0_END,
    S0_START,
    S1_END,
    S1_START,
    WARMUP_END,
    WARMUP_START,
    LicenseEvidenceReport,
    PinStatus,
    SnapshotRevalidationReport,
    revalidate_license_evidence,
    verify_snapshot_pins,
)
from research.stocks_free_v3.authority import (
    VERDICT_FAIL,
    VERDICT_NOT_RUN,
    VERDICT_PASS,
)

# --- pin table integrity (the committed pins themselves) ----------------------- #


def test_pin_table_has_expected_shape() -> None:
    assert len(SNAPSHOT_PINS) == 39  # 12 symbols x 3 pulls + 3 metadata files
    assert SNAPSHOT_PINS["MANIFEST.json"] == MANIFEST_PIN
    for symbol in ("SPY", "XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE", "XLC"):
        for suffix in ("all_p1", "none_p1", "none_p2"):
            assert f"{symbol}_{suffix}.json" in SNAPSHOT_PINS
    for digest in SNAPSHOT_PINS.values():
        assert len(digest) == 64 and digest == digest.lower()


def test_frozen_windows_match_plan() -> None:
    assert (WARMUP_START, WARMUP_END) == (date(2018, 1, 2), date(2018, 4, 3))
    assert (S0_START, S0_END) == (date(2018, 4, 4), date(2025, 7, 31))
    assert (S1_START, S1_END) == (date(2025, 8, 1), date(2026, 7, 31))


# --- synthetic snapshot verification -------------------------------------------- #


def _write(path: Path, name: str, payload: bytes) -> str:
    (path / name).write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def test_verify_snapshot_pins_all_verified(tmp_path: Path) -> None:
    digests = {
        name: _write(tmp_path, name, name.encode())
        for name in ("MANIFEST.json", "SPY_none_p1.json", "common_coverage.json")
    }
    # build a report over a pin table restricted to the three synthetic files
    report = _verify_with_pins(tmp_path, digests)
    assert report.verdict == VERDICT_PASS
    assert sorted(report.verified) == sorted(digests)
    assert report.mismatched == () and report.unavailable == ()


def test_verify_snapshot_pins_detects_tampering(tmp_path: Path) -> None:
    name = "SPY_none_p1.json"
    pin = _write(tmp_path, name, b"original bytes")
    (tmp_path / name).write_bytes(b"tampered bytes")
    report = _verify_with_pins(tmp_path, {name: pin})
    assert report.verdict == VERDICT_FAIL
    assert report.mismatched == (name,)
    assert report.pins[0].actual_sha256 == hashlib.sha256(b"tampered bytes").hexdigest()


def test_verify_snapshot_pins_absent_file_is_unavailable(tmp_path: Path) -> None:
    report = _verify_with_pins(tmp_path, {"XLU_none_p1.json": "0" * 64})
    assert report.verdict == VERDICT_FAIL
    assert report.unavailable == ("XLU_none_p1.json",)
    assert report.pins[0].actual_sha256 is None


def test_verify_snapshot_pins_records_full_payload(tmp_path: Path) -> None:
    pin = _write(tmp_path, "MANIFEST.json", b"{}")
    report = _verify_with_pins(tmp_path, {"MANIFEST.json": pin})
    payload = json.loads(report.canonical_json())
    assert payload["verdict"] == VERDICT_PASS
    assert payload["pin_count"] == 1
    assert payload["pins"][0]["status"] == "VERIFIED"


def _verify_with_pins(root: Path, pins: dict[str, str]) -> SnapshotRevalidationReport:
    """Run the verifier against a synthetic pin table (monkeypatched)."""
    import research.stocks_free_v3.authority as authority

    original = dict(authority.SNAPSHOT_PINS)
    authority.SNAPSHOT_PINS.clear()
    authority.SNAPSHOT_PINS.update(pins)
    try:
        return verify_snapshot_pins(root)
    finally:
        authority.SNAPSHOT_PINS.clear()
        authority.SNAPSHOT_PINS.update(original)


# --- pin status validation ------------------------------------------------------- #


def test_pin_status_rejects_bad_state() -> None:
    with pytest.raises(ValueError):
        PinStatus(name="x", expected_sha256="0" * 64, status="SOMETHING", actual_sha256=None)
    with pytest.raises(ValueError):
        PinStatus(name="x", expected_sha256="0" * 64, status="UNAVAILABLE", actual_sha256="1" * 64)
    with pytest.raises(ValueError):
        PinStatus(name="x", expected_sha256="nothex", status="VERIFIED", actual_sha256="1" * 64)


# --- license evidence revalidation (synthetic control dir) ----------------------- #


_DA1 = {
    "provider": "Twelve Data",
    "plan": "Basic (free)",
    "ten_point_checks": {
        "1_basic_price_exactly_0": "PASS (official pricing page)",
        "6_personal_internal_noncommercial_research_permitted": "PASS (terms)",
        "7_local_storage_snapshots_checksums_reproducibility": "PASS WITH MATERIAL CONDITIONS",
        "8_no_redistribution_no_raw_in_git": "PASS (terms prohibit redistribution)",
    },
}

_CONTROL_MANIFEST = {
    "license_note": (
        "local persistent storage permitted within subscription (TD terms); "
        "deletion within 30 days post-termination; redistribution forbidden"
    ),
    "issuer_evidence": {
        "spdr_distributions_sha256_prefix": ISSUER_DISTRIBUTION_RECORDS_SHA256[:16]
    },
}


def _write_control(tmp_path: Path, da1: object, manifest: object) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "da1_authority.json").write_text(json.dumps(da1), encoding="utf-8")
    (tmp_path / "snapshot_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


def test_license_evidence_passes_on_frozen_terms(tmp_path: Path) -> None:
    control = _write_control(tmp_path, _DA1, _CONTROL_MANIFEST)
    report = revalidate_license_evidence(control)
    assert isinstance(report, LicenseEvidenceReport)
    assert report.verdict == VERDICT_PASS
    names = {c.name for c in report.checks}
    assert {
        "provider_and_plan_frozen",
        "zero_cost_usd0",
        "internal_noncommercial_research_only",
        "local_storage_within_subscription",
        "no_redistribution_no_raw_in_git",
        "license_note_revalidated",
        "issuer_distribution_records_prefix_match",
    } <= names
    # control artifact digests are recorded for the audit trail
    assert set(report.artifact_digests) == {"da1_authority.json", "snapshot_manifest.json"}


def test_license_evidence_fails_on_terms_drift(tmp_path: Path) -> None:
    drifted = json.loads(json.dumps(_DA1))
    drifted["plan"] = "Basic (free) -> Grow (paid)"
    drifted["ten_point_checks"]["8_no_redistribution_no_raw_in_git"] = "FAIL"
    control = _write_control(tmp_path, drifted, _CONTROL_MANIFEST)
    report = revalidate_license_evidence(control)
    assert report.verdict == VERDICT_FAIL
    by_name = {c.name: c for c in report.checks}
    assert by_name["provider_and_plan_frozen"].verdict == VERDICT_FAIL
    assert by_name["no_redistribution_no_raw_in_git"].verdict == VERDICT_FAIL


def test_license_evidence_not_run_when_control_absent(tmp_path: Path) -> None:
    report = revalidate_license_evidence(tmp_path)  # empty dir
    assert report.verdict == VERDICT_NOT_RUN
    for check in report.checks:
        assert check.verdict == VERDICT_NOT_RUN
        assert "UNAVAILABLE" in check.detail


def test_license_evidence_staging_manifest_full_digest(tmp_path: Path) -> None:
    control = _write_control(tmp_path / "control", _DA1, _CONTROL_MANIFEST)
    staging = tmp_path / "staging"
    staging.mkdir()
    staging_manifest = {
        "issuer_evidence": {"spdr_distributions_sha256": ISSUER_DISTRIBUTION_RECORDS_SHA256}
    }
    (staging / "MANIFEST.json").write_text(json.dumps(staging_manifest), encoding="utf-8")
    wrong_pin = dict(SNAPSHOT_PINS)
    wrong_pin["MANIFEST.json"] = "0" * 64
    import research.stocks_free_v3.authority as authority

    original = dict(authority.SNAPSHOT_PINS)
    authority.SNAPSHOT_PINS.clear()
    authority.SNAPSHOT_PINS.update(wrong_pin)
    try:
        report = revalidate_license_evidence(control, staging_root=staging)
    finally:
        authority.SNAPSHOT_PINS.clear()
        authority.SNAPSHOT_PINS.update(original)
    by_name = {c.name: c for c in report.checks}
    # the synthetic pin table pins a different MANIFEST.json -> byte check fails
    assert by_name["staging_manifest_issuer_digest"].verdict == VERDICT_FAIL


def test_license_evidence_never_performs_network_or_credential_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The revalidation path must not touch sockets or credential stores."""
    import socket
    import urllib.request

    control = _write_control(tmp_path, _DA1, _CONTROL_MANIFEST)

    def _blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access attempted during revalidation")

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(urllib.request, "urlopen", _blocked)
    report = revalidate_license_evidence(control)
    assert report.verdict == VERDICT_PASS
