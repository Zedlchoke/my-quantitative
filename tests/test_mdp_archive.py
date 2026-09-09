"""MDP-V1 lane A3: immutable archive + manifest tests (tests/test_mdp_archive.py).

Covers the frozen archive_protocol and mdp.raw_chunk_manifest@1 schema:
happy-path layout, immutability (re-put no-op / HashDisagreement fail
closed), crash-boundary atomicity at every frozen write stage (temp write,
flush+fsync, replace, re-read verify, manifest publication), truncated
payload, wrong byte length, wrong count, wrong sha, orphan scan findings,
secret-denylist rejection, entitlement field enforcement and prev/next
linkage checks.

All IO runs under pytest tmp_path; no network; stdlib only.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import archive  # noqa: E402
from market_data_plane.manifest import (  # noqa: E402
    MANIFEST_FIELDS,
    REASON_CODES,
    ManifestValidationError,
    build_manifest,
    canonical_manifest_bytes,
    compute_manifest_id,
    sha256_hex,
    validate_manifest,
    verify_manifest_chain,
)

ENVELOPE_FIELDS = [
    "schema_version", "event_id", "raw_id", "source_id", "venue", "instrument_id",
    "asset_class", "event_type", "exchange_time_utc_ns", "receive_time_utc_ns",
    "available_time_utc_ns", "sequence_number", "price", "quantity", "side",
    "bid_price", "ask_price", "bid_size", "ask_size", "currency", "price_precision",
    "size_precision", "quality_status", "reason_codes", "raw_sha256",
    "manifest_sha256", "normalizer_version",
]


def event_identity_id(event: dict) -> str:
    """Freeze field_rules.event_id: sha256 of 0x1F-joined identity string."""
    identity = "\x1f".join(
        str(value)
        for value in (
            event["schema_version"], event["source_id"], event["venue"],
            event["instrument_id"], event["event_type"], event["exchange_time_utc_ns"],
            event["receive_time_utc_ns"], event["available_time_utc_ns"],
            event["sequence_number"], event["raw_sha256"],
        )
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


_UNSET = object()


def make_event(seq: int, exchange_ns: int, *, instrument: str = "BTC-USDT",
               source: str = "src1", venue: str = "VEN", sequence: int = _UNSET) -> dict:
    if sequence is _UNSET:
        sequence = seq
    event = {field: None for field in ENVELOPE_FIELDS}
    event.update(
        schema_version="mdp.market_event@1",
        raw_id=f"raw-{seq}",
        source_id=source,
        venue=venue,
        instrument_id=instrument,
        asset_class="crypto",
        event_type="TRADE",
        exchange_time_utc_ns=exchange_ns,
        receive_time_utc_ns=exchange_ns + 10,
        available_time_utc_ns=exchange_ns + 20,
        sequence_number=sequence,
        price="100.01",
        quantity="2",
        price_precision=2,
        size_precision=0,
        quality_status="VALID",
        reason_codes=[],
        raw_sha256=sha256_hex(f"raw-bytes-{seq}".encode("utf-8")),
        manifest_sha256="a" * 64,
        normalizer_version="norm@1",
    )
    event["event_id"] = event_identity_id(event)
    return event


def identity_kwargs(**over) -> dict:
    kwargs = dict(
        source_id="src1",
        provider_id="prov1",
        venue="VEN",
        instrument_id="BTC-USDT",
        asset_class="crypto",
        event_class="trades",
        request_identity_secrets_removed={"symbol": "BTC-USDT", "window": "1d"},
        entitlement_evidence_ref="entitlement-evidence-123",
        allowed_use_classification="RESEARCH_AUTHORIZED",
        retrieval_start_utc_ns=1_000,
        retrieval_end_utc_ns=2_000,
        media_type="application/x-ndjson",
        encoding="utf-8",
        parser_version="parser@1",
        normalizer_version="norm@1",
        created_utc=42,
    )
    kwargs.update(over)
    return kwargs


def put(root: Path, events: list, **over) -> dict:
    return archive.put_chunk_records(root, events, **identity_kwargs(**over))


# ---------------------------------------------------------------------------
# frozen-schema binding guards
# ---------------------------------------------------------------------------


def test_manifest_fields_match_freeze():
    """The module's field list equals the freeze's 33-field manifest list."""
    frozen = (
        "schema_version", "manifest_id", "source_id", "provider_id", "venue",
        "instrument_id", "asset_class", "event_class", "request_identity_secrets_removed",
        "entitlement_evidence_ref", "allowed_use_classification", "retrieval_start_utc_ns",
        "retrieval_end_utc_ns", "payload_byte_length", "record_count", "payload_sha256",
        "media_type", "encoding", "min_exchange_time_utc_ns", "max_exchange_time_utc_ns",
        "min_receive_time_utc_ns", "max_receive_time_utc_ns", "min_available_time_utc_ns",
        "max_available_time_utc_ns", "parser_version", "normalizer_version",
        "prev_manifest_id", "next_manifest_id", "completeness_status", "gap_reasons",
        "sequence_semantics", "ordered_delivery", "created_utc",
    )
    assert len(frozen) == 33
    assert tuple(MANIFEST_FIELDS) == frozen
    from market_data_plane.manifest import REASON_CODES as MODULE_CODES
    assert len(MODULE_CODES) == 21


def test_put_chunk_records_layout_and_manifest(tmp_path):
    events = [make_event(i, 1_000_000_000 + i * 1_000) for i in range(3)]
    out = put(tmp_path, events)

    sha = out["chunk_sha256"]
    assert out["chunk_path"] == tmp_path / "chunks" / sha[:2] / sha[2:4] / f"{sha}.jsonl"
    manifest = out["manifest"]
    assert out["manifest_path"] == tmp_path / "manifests" / f"{manifest['manifest_id']}.json"
    assert out["chunk_path"].exists() and out["manifest_path"].exists()

    # chunk bytes are the frozen canonical stream framing
    from market_data_plane._canonical import canonical_line_bytes
    assert out["chunk_path"].read_bytes() == b"".join(canonical_line_bytes(e) for e in events)
    assert sha256_hex(out["chunk_path"].read_bytes()) == sha
    assert out["record_count"] == 3

    # manifest carries the exact frozen 33-field list and derived statistics
    assert set(manifest.keys()) == set(MANIFEST_FIELDS)
    assert manifest["schema_version"] == "mdp.raw_chunk_manifest@1"
    assert manifest["payload_sha256"] == sha
    assert manifest["payload_byte_length"] == out["chunk_path"].stat().st_size
    assert manifest["record_count"] == 3
    assert manifest["min_exchange_time_utc_ns"] == 1_000_000_000
    assert manifest["max_exchange_time_utc_ns"] == 1_000_002_000
    assert manifest["min_receive_time_utc_ns"] == 1_000_000_010
    assert manifest["min_available_time_utc_ns"] == 1_000_000_020
    assert manifest["allowed_use_classification"] == "RESEARCH_AUTHORIZED"
    assert manifest["entitlement_evidence_ref"] == "entitlement-evidence-123"
    assert manifest["completeness_status"] == "COMPLETE"

    # manifest file bytes are canonical form and the id is the frozen self-hash
    raw = out["manifest_path"].read_bytes()
    assert raw == canonical_manifest_bytes(manifest)
    assert manifest["manifest_id"] == compute_manifest_id(manifest)
    assert validate_manifest(manifest)["manifest_id"] == manifest["manifest_id"]


def test_manifest_id_is_sha256_of_canonical_minus_id():
    manifest = build_manifest(
        payload_sha256=sha256_hex(b""), payload_byte_length=0, record_count=0,
        time_bounds={k: None for k in (
            "min_exchange_time_utc_ns", "max_exchange_time_utc_ns",
            "min_receive_time_utc_ns", "max_receive_time_utc_ns",
            "min_available_time_utc_ns", "max_available_time_utc_ns")},
        source_id="s", provider_id="p", venue="v", instrument_id="i", asset_class="a",
        event_class="e", entitlement_evidence_ref="ref", created_utc=7,
    )
    import hashlib as _hashlib
    from market_data_plane._canonical import canonical_json
    minus_id = {k: v for k, v in manifest.items() if k != "manifest_id"}
    expected = _hashlib.sha256(canonical_json(minus_id).encode("utf-8")).hexdigest()
    assert manifest["manifest_id"] == expected


def test_reput_identical_bytes_is_noop(tmp_path):
    events = [make_event(i, i * 1_000) for i in range(2)]
    first = put(tmp_path, events)
    chunk_before = first["chunk_path"].read_bytes()
    manifest_before = first["manifest_path"].read_bytes()
    chunk_stat = first["chunk_path"].stat()
    manifest_stat = first["manifest_path"].stat()

    second = put(tmp_path, events)  # identical events -> identical bytes/manifest

    assert second["chunk_deduplicated"] is True
    assert second["chunk_path"] == first["chunk_path"]
    assert second["manifest"]["manifest_id"] == first["manifest"]["manifest_id"]
    assert first["chunk_path"].read_bytes() == chunk_before
    assert first["manifest_path"].read_bytes() == manifest_before
    assert first["chunk_path"].stat().st_mtime_ns == chunk_stat.st_mtime_ns
    assert first["manifest_path"].stat().st_mtime_ns == manifest_stat.st_mtime_ns
    assert archive.scan_orphans(tmp_path)["chunks_without_manifest"] == []


def test_different_bytes_at_content_path_fail_closed_never_overwrite(tmp_path):
    events = [make_event(0, 1)]
    out = put(tmp_path, events)
    chunk_path = out["chunk_path"]
    original = chunk_path.read_bytes()

    # Simulate on-disk corruption, then re-put the ORIGINAL correct bytes.
    chunk_path.write_bytes(original + b"corruption\n")
    with pytest.raises(archive.HashDisagreement):
        archive.write_chunk(tmp_path, original)
    # fail closed: the differing bytes were detected, never overwritten
    assert chunk_path.read_bytes() == original + b"corruption\n"

    report = archive.scan_orphans(tmp_path)
    assert report["sha_mismatch_chunks"] == [
        {
            "path": str(chunk_path.relative_to(tmp_path)),
            "expected_sha256": out["chunk_sha256"],
            "actual_sha256": sha256_hex(original + b"corruption\n"),
        }
    ]


def test_publish_manifest_hash_disagreement_on_differing_existing_bytes(tmp_path):
    manifest = build_manifest(
        payload_sha256=sha256_hex(b"x"), payload_byte_length=1, record_count=1,
        source_id="s", provider_id="p", venue="v", instrument_id="i", asset_class="a",
        event_class="e", entitlement_evidence_ref="ref",
        parser_version="parser@1", normalizer_version="norm@1", created_utc=1,
    )
    path = archive.publish_manifest(tmp_path, manifest)
    on_disk = path.read_bytes()

    # Corrupt the published manifest on disk, then re-publish identical content.
    path.write_bytes(on_disk.replace(b'"record_count":1', b'"record_count":1\x00'))
    with pytest.raises(archive.HashDisagreement):
        archive.publish_manifest(tmp_path, manifest)
    assert path.read_bytes() == on_disk.replace(b'"record_count":1', b'"record_count":1\x00')


# ---------------------------------------------------------------------------
# crash-boundary atomicity (monkeypatch each frozen stage)
# ---------------------------------------------------------------------------


def _crash_at_binary_write(monkeypatch, message: str) -> None:
    """Make the write stage of every binary 'wb' open() raise.

    io.BufferedWriter is an immutable C type, so the write-stage crash is
    injected one level up: builtins.open returns a proxy whose write() raises
    while flush/fileno/flush/context-manager still delegate to the real
    handle.
    """
    import builtins

    real_open = builtins.open

    class _CrashOnWrite:
        def __init__(self, handle):
            self._handle = handle

        def write(self, data):
            raise RuntimeError(message)

        def flush(self):
            return self._handle.flush()

        def fileno(self):
            return self._handle.fileno()

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return self._handle.__exit__(*exc_info)

    def crashing_open(file, mode="r", *args, **kwargs):
        handle = real_open(file, mode, *args, **kwargs)
        if "w" in mode and "b" in mode:
            return _CrashOnWrite(handle)
        return handle

    monkeypatch.setattr(builtins, "open", crashing_open)


def test_crash_during_temp_write_no_final_chunk_no_temp_left(tmp_path, monkeypatch):
    _crash_at_binary_write(monkeypatch, "crash during write")
    with pytest.raises(RuntimeError, match="crash during write"):
        archive.write_chunk(tmp_path, b"record\n")
    assert not any(tmp_path.rglob("*.jsonl"))
    assert not any(tmp_path.rglob("manifests/*.json"))
    assert not any(tmp_path.rglob(".tmp-*"))


def test_crash_at_fsync_no_final_chunk(tmp_path, monkeypatch):
    def boom(fd):
        raise RuntimeError("crash at fsync")

    monkeypatch.setattr(os, "fsync", boom)
    with pytest.raises(RuntimeError, match="crash at fsync"):
        archive.write_chunk(tmp_path, b"record\n")
    assert not any(tmp_path.rglob("*.jsonl"))
    assert not any(tmp_path.rglob(".tmp-*"))


def test_crash_at_chunk_replace_no_final_content_path(tmp_path, monkeypatch):
    def boom(src, dst):
        raise RuntimeError("crash at replace")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(RuntimeError, match="crash at replace"):
        archive.write_chunk(tmp_path, b"record\n")
    assert not any(tmp_path.rglob("*.jsonl"))
    assert not any(tmp_path.rglob(".tmp-*"))


def test_crash_after_chunk_replace_before_manifest_publication(tmp_path, monkeypatch):
    real_replace = os.replace
    calls = {"n": 0}

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] == 2:  # first replace = chunk, second = manifest
            raise RuntimeError("crash before manifest publication")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky)
    events = [make_event(0, 10), make_event(1, 20)]
    with pytest.raises(RuntimeError, match="crash before manifest publication"):
        put(tmp_path, events)

    # frozen protocol: the verified chunk stays in place, no manifest exists
    from market_data_plane._canonical import canonical_line_bytes
    payload = b"".join(canonical_line_bytes(e) for e in events)
    sha = sha256_hex(payload)
    chunk_path = tmp_path / "chunks" / sha[:2] / sha[2:4] / f"{sha}.jsonl"
    assert chunk_path.exists()
    assert chunk_path.read_bytes() == payload
    assert not any((tmp_path / "manifests").iterdir())

    # explicit orphan: diagnosable, never guessed complete
    report = archive.scan_orphans(tmp_path)
    assert report["chunks_without_manifest"] == [sha]


def test_crash_reread_verification_catches_tampered_publish(tmp_path, monkeypatch):
    """If bytes under the final content path are wrong, re-read verify fails."""
    real_replace = os.replace

    def tampering_replace(src, dst):
        real_replace(src, dst)
        Path(dst).write_bytes(b"tampered\n")  # corrupt right after publish

    monkeypatch.setattr(os, "replace", tampering_replace)
    with pytest.raises(archive.HashDisagreement):
        archive.write_chunk(tmp_path, b"honest-record\n")
    # the tampered file is exposed by the orphan scan, never adopted
    report = archive.scan_orphans(tmp_path)
    sha_expected = sha256_hex(b"honest-record\n")
    assert report["sha_mismatch_chunks"][0]["expected_sha256"] == sha_expected


# ---------------------------------------------------------------------------
# truncated payload / wrong length / wrong count / wrong sha
# ---------------------------------------------------------------------------


def test_truncated_payload_detected(tmp_path):
    events = [make_event(i, i) for i in range(3)]
    out = put(tmp_path, events)
    chunk_path = out["chunk_path"]
    original = chunk_path.read_bytes()

    truncated = original[: len(original) // 2]
    chunk_path.write_bytes(truncated)

    report = archive.verify_chunk(tmp_path, out["chunk_sha256"],
                                  expected_byte_length=len(original),
                                  expected_record_count=3)
    assert report["exists"] is True
    assert report["errors"], "truncation must be reported"
    assert report["actual_sha256"] != out["chunk_sha256"]
    assert report["has_trailing_partial"] is True
    assert report["record_count"] == truncated.count(b"\n")

    scan = archive.scan_orphans(tmp_path)
    assert scan["sha_mismatch_chunks"] and scan["trailing_partial_records"]


def test_wrong_byte_length_and_wrong_count_against_manifest(tmp_path):
    events = [make_event(i, i) for i in range(3)]
    out = put(tmp_path, events)
    sha = out["chunk_sha256"]

    report = archive.verify_chunk(tmp_path, sha, expected_byte_length=10 ** 6)
    assert any("byte length" in err for err in report["errors"])
    report = archive.verify_chunk(tmp_path, sha, expected_record_count=99)
    assert any("record count" in err for err in report["errors"])


def test_replay_visible_count_mismatch_manifest(tmp_path):
    """Manifest with a WRONG record count (self-consistent id) is detected."""
    from market_data_plane import replay as replay_module

    events = [make_event(i, i) for i in range(3)]
    out = put(tmp_path, events)
    manifest = dict(out["manifest"])
    manifest["record_count"] = manifest["record_count"] + 1
    manifest["manifest_id"] = compute_manifest_id(manifest)
    archive.publish_manifest(tmp_path, manifest)

    routed = []
    result = replay_module.replay(tmp_path, [manifest["manifest_id"]],
                                  on_corrupt=routed.append)
    assert routed[0]["reason"] == "MANIFEST_MISMATCH"
    assert "record count" in routed[0]["detail"]
    assert result["input_complete"] is False
    assert result["event_count"] == 0


def test_wrong_payload_sha_manifest_points_to_missing_chunk(tmp_path):
    from market_data_plane import replay as replay_module

    events = [make_event(0, 0)]
    out = put(tmp_path, events)
    manifest = dict(out["manifest"])
    manifest["payload_sha256"] = "b" * 64  # wrong sha -> no such content chunk
    manifest["manifest_id"] = compute_manifest_id(manifest)
    archive.publish_manifest(tmp_path, manifest)

    scan = archive.scan_orphans(tmp_path)
    assert scan["manifests_without_chunk"] == [
        {"manifest_id": manifest["manifest_id"], "payload_sha256": "b" * 64}
    ]

    routed = []
    replay_module.replay(tmp_path, [manifest["manifest_id"]], on_corrupt=routed.append)
    assert routed[0]["reason"] == "MANIFEST_MISMATCH"
    assert "missing chunk" in routed[0]["detail"]


# ---------------------------------------------------------------------------
# orphan scan
# ---------------------------------------------------------------------------


def test_scan_orphans_empty_archive(tmp_path):
    report = archive.scan_orphans(tmp_path)
    assert report == {
        "chunks_without_manifest": [],
        "manifests_without_chunk": [],
        "trailing_partial_records": [],
        "sha_mismatch_chunks": [],
        "malformed_line_chunks": [],
        "manifest_unreadable": [],
        "unexpected_chunk_names": [],
        "stray_temp_files": [],
        "chunk_count": 0,
        "manifest_count": 0,
    }


def test_scan_orphans_finds_each_injected_anomaly(tmp_path):
    out1 = put(tmp_path, [make_event(i, i) for i in range(2)])
    out2 = put(tmp_path, [make_event(i, 100 + i) for i in range(2)],
               event_class="trades2", created_utc=43)
    sha1, sha2 = out1["chunk_sha256"], out2["chunk_sha256"]

    # 1. chunk without manifest
    out1["manifest_path"].unlink()
    # 2. manifest without chunk
    out2["chunk_path"].unlink()
    # 3. trailing partial record on a third chunk
    out3 = put(tmp_path, [make_event(9, 999)], event_class="trades3", created_utc=44)
    out3["chunk_path"].write_bytes(
        out3["chunk_path"].read_bytes() + b'{"partial": tru')
    # 4. stray temp file
    stray = tmp_path / "manifests" / ".tmp-999-0"
    stray.write_bytes(b"interrupted")
    # 5. unreadable manifest
    (tmp_path / "manifests" / ("c" * 64 + ".json")).write_bytes(b"{not json")

    report = archive.scan_orphans(tmp_path)
    assert report["chunks_without_manifest"] == [sha1]
    assert [item["payload_sha256"] for item in report["manifests_without_chunk"]] == [sha2]
    assert len(report["trailing_partial_records"]) == 1
    assert report["trailing_partial_records"][0]["sha256"] == out3["chunk_sha256"]
    assert report["stray_temp_files"] == [str(stray.relative_to(tmp_path))]
    assert len(report["manifest_unreadable"]) == 1
    assert report["chunk_count"] == 2 and report["manifest_count"] == 3


def test_verify_chunk_clean_report(tmp_path):
    out = put(tmp_path, [make_event(0, 1)])
    report = archive.verify_chunk(tmp_path, out["chunk_sha256"],
                                  expected_byte_length=out["chunk_byte_length"],
                                  expected_record_count=out["record_count"])
    assert report["errors"] == []
    assert report["exists"] is True
    assert report["byte_length"] == out["chunk_byte_length"]
    assert report["record_count"] == 1


# ---------------------------------------------------------------------------
# structural: append forbidden
# ---------------------------------------------------------------------------


def test_no_append_mode_anywhere_in_owned_io_modules():
    pattern = re.compile(r"open\([^)]*['\"]a[bx+]*['\"]")
    source = Path(archive.__file__).read_text()
    assert not pattern.search(source), "append-mode open found in market_data_plane.archive"


# ---------------------------------------------------------------------------
# manifest validation
# ---------------------------------------------------------------------------


def _valid_manifest() -> dict:
    return build_manifest(
        payload_sha256=sha256_hex(b"payload"), payload_byte_length=7, record_count=1,
        source_id="s", provider_id="p", venue="v", instrument_id="i", asset_class="a",
        event_class="e", entitlement_evidence_ref="ref",
        media_type="application/x-ndjson",
        encoding="utf-8",
        parser_version="parser@1",
        normalizer_version="norm@1",
        time_bounds={
            "min_exchange_time_utc_ns": 10, "max_exchange_time_utc_ns": 20,
            "min_receive_time_utc_ns": 11, "max_receive_time_utc_ns": 21,
            "min_available_time_utc_ns": 12, "max_available_time_utc_ns": 22,
        },
        created_utc=5,
    )


def test_validate_manifest_happy(tmp_path):
    assert validate_manifest(_valid_manifest())["record_count"] == 1


def test_validate_manifest_rejects_missing_and_extra_fields():
    manifest = _valid_manifest()
    incomplete = {k: v for k, v in manifest.items() if k != "venue"}
    with pytest.raises(ManifestValidationError, match="missing fields"):
        validate_manifest(incomplete)
    extra = dict(manifest)
    extra["unexpected"] = 1
    with pytest.raises(ManifestValidationError, match="unexpected fields"):
        validate_manifest(extra)


def test_validate_manifest_rejects_bad_enums_and_types():
    manifest = _valid_manifest()
    manifest["allowed_use_classification"] = "SURE_THING"
    with pytest.raises(ManifestValidationError, match="allowed_use_classification"):
        validate_manifest(manifest)

    manifest = _valid_manifest()
    manifest["completeness_status"] = "MOSTLY"
    with pytest.raises(ManifestValidationError, match="completeness_status"):
        validate_manifest(manifest)

    manifest = _valid_manifest()
    manifest["sequence_semantics"] = "SORT_OF"
    with pytest.raises(ManifestValidationError, match="sequence_semantics"):
        validate_manifest(manifest)

    manifest = _valid_manifest()
    manifest["ordered_delivery"] = 1  # bool-looking int must fail
    with pytest.raises(ManifestValidationError, match="ordered_delivery"):
        validate_manifest(manifest)

    manifest = _valid_manifest()
    manifest["record_count"] = -1
    with pytest.raises(ManifestValidationError, match="record_count"):
        validate_manifest(manifest)

    manifest = _valid_manifest()
    manifest["payload_byte_length"] = True  # bool is not a legal length
    with pytest.raises(ManifestValidationError, match="payload_byte_length"):
        validate_manifest(manifest)


def test_validate_manifest_min_max_and_retrieval_order():
    manifest = _valid_manifest()
    manifest["min_exchange_time_utc_ns"] = 100
    with pytest.raises(ManifestValidationError, match="min_exchange_time_utc_ns"):
        validate_manifest(manifest)

    manifest = _valid_manifest()
    manifest["retrieval_start_utc_ns"] = 999
    manifest["retrieval_end_utc_ns"] = 5
    with pytest.raises(ManifestValidationError, match="retrieval_start_utc_ns"):
        validate_manifest(manifest)


def test_validate_manifest_gap_reasons_consistency():
    manifest = _valid_manifest()
    manifest["completeness_status"] = "GAPS_PRESENT"
    with pytest.raises(ManifestValidationError, match="GAPS_PRESENT requires"):
        validate_manifest(manifest)

    manifest = _valid_manifest()
    manifest["gap_reasons"] = ["SEQUENCE_GAP"]
    with pytest.raises(ManifestValidationError, match="COMPLETE requires"):
        validate_manifest(manifest)

    manifest = _valid_manifest()
    manifest["completeness_status"] = "GAPS_PRESENT"
    manifest["gap_reasons"] = ["NOT_A_CODE"]
    with pytest.raises(ManifestValidationError, match="reason_codes@1"):
        validate_manifest(manifest)

    manifest = _valid_manifest()
    manifest["completeness_status"] = "GAPS_PRESENT"
    manifest["gap_reasons"] = ["SEQUENCE_GAP", "SEQUENCE_GAP"]
    with pytest.raises(ManifestValidationError, match="sorted and unique"):
        validate_manifest(manifest)

    assert "SEQUENCE_GAP" in REASON_CODES


def test_validate_manifest_entitlement_fields_required():
    manifest = _valid_manifest()
    manifest["entitlement_evidence_ref"] = ""
    with pytest.raises(ManifestValidationError, match="entitlement_evidence_ref"):
        validate_manifest(manifest)

    manifest = _valid_manifest()
    del manifest["entitlement_evidence_ref"]
    with pytest.raises(ManifestValidationError, match="entitlement"):
        validate_manifest(manifest)

    for classification in ("RESEARCH_AUTHORIZED", "RESEARCH_CONDITIONAL", "NOT_AUTHORIZED"):
        manifest = _valid_manifest()
        manifest["allowed_use_classification"] = classification
        manifest["manifest_id"] = compute_manifest_id(manifest)  # re-stamp after mutation
        assert validate_manifest(manifest)["allowed_use_classification"] == classification


def test_validator_rejects_secret_denylist_keys():
    for bad_key in ("api_key", "password", "auth_token", "client_secret", "AWS_SECRET"):
        manifest = _valid_manifest()
        manifest["request_identity_secrets_removed"] = {"symbol": "X", bad_key: "hunter2"}
        with pytest.raises(ManifestValidationError, match="secret-denylist"):
            validate_manifest(manifest)
    # nested keys are scanned too
    manifest = _valid_manifest()
    manifest["request_identity_secrets_removed"] = {"headers": {"Authorization": "Bearer x"}}
    with pytest.raises(ManifestValidationError, match="secret-denylist"):
        validate_manifest(manifest)
    # clean identity passes
    manifest = _valid_manifest()
    manifest["request_identity_secrets_removed"] = {"symbol": "X", "interval": "1m"}
    manifest["manifest_id"] = compute_manifest_id(manifest)  # re-stamp after mutation
    assert validate_manifest(manifest)["request_identity_secrets_removed"] == {
        "symbol": "X",
        "interval": "1m",
    }


def test_validate_manifest_self_hash_mismatch_is_hash_disagreement():
    manifest = _valid_manifest()
    manifest["record_count"] = manifest["record_count"] + 1  # id now stale
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_manifest(manifest)
    assert excinfo.value.code == "HASH_DISAGREEMENT"


def test_manifest_prev_next_linkage_checks():
    common = dict(
        source_id="s", provider_id="p", venue="v", instrument_id="i", asset_class="a",
        event_class="e", entitlement_evidence_ref="ref",
        parser_version="parser@1", normalizer_version="norm@1",
    )
    a0 = build_manifest(payload_sha256=sha256_hex(b"a"), payload_byte_length=1,
                        record_count=1, created_utc=1, **common)
    b0 = build_manifest(payload_sha256=sha256_hex(b"b"), payload_byte_length=1,
                        record_count=1, created_utc=2, **common)
    # Content-addressed ids make a bidirectionally-linked pair a fixed-point
    # problem, so real chains populate ONE direction (blockchain-style prev,
    # or forward-only next); the freeze keeps both nullable. Each non-null
    # link must match the actual neighbor.
    b_prev = dict(b0, prev_manifest_id=a0["manifest_id"])
    b_prev["manifest_id"] = compute_manifest_id(b_prev)
    assert verify_manifest_chain([a0, b_prev]) == [a0["manifest_id"], b_prev["manifest_id"]]

    a_next = dict(a0, next_manifest_id=b0["manifest_id"])
    a_next["manifest_id"] = compute_manifest_id(a_next)
    assert verify_manifest_chain([a_next, b0]) == [a_next["manifest_id"], b0["manifest_id"]]

    broken_prev = dict(b_prev, prev_manifest_id="d" * 64)
    broken_prev["manifest_id"] = compute_manifest_id(broken_prev)
    with pytest.raises(ManifestValidationError, match="prev"):
        verify_manifest_chain([a0, broken_prev])

    broken_next = dict(a_next, next_manifest_id="e" * 64)
    broken_next["manifest_id"] = compute_manifest_id(broken_next)
    with pytest.raises(ManifestValidationError, match="next"):
        verify_manifest_chain([broken_next, b0])

    with pytest.raises(ManifestValidationError, match="duplicate manifest ids"):
        verify_manifest_chain([a0, a0])


def test_load_manifest_roundtrip_and_missing(tmp_path):
    out = put(tmp_path, [make_event(0, 1)])
    loaded = archive.load_manifest(tmp_path, out["manifest"]["manifest_id"])
    assert loaded == out["manifest"]
    with pytest.raises(archive.ArchiveError, match="not found"):
        archive.load_manifest(tmp_path, "0" * 64)
