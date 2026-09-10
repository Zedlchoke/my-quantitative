"""MDP-V2 lane A2: archive content-ID grammar, filename/body binding and
path-confinement security tests (finding F2).

Pins the frozen rules from
``research/control/market_data_plane_v2_run/architecture_freeze_v2.json``
(findings_and_negative_matrices.F2_identifier_and_path_confinement):

- content-ID grammar ``^[0-9a-f]{64}$`` for chunk_path/manifest_path path
  arguments (empty, short, 63/65-length, uppercase, non-hex and overlong
  IDs rejected; non-string/pathlike variants rejected);
- traversal/absolute/separator/encoded variants rejected FAIL CLOSED before
  any filesystem access (nothing created or consumed inside or outside the
  root);
- filename/body binding: valid manifest bytes stored under a different
  valid 64-hex filename fail closed on load_manifest and through the public
  replay()/replay_events() API;
- symlink escapes at a chunk directory boundary and at the manifests
  directory boundary fail closed without reading or writing the outside
  target;
- verify_chunk with a malicious ID raises ArchiveError (pinned A2 choice)
  and performs no filesystem write;
- positive control: a valid put_chunk_records -> load_manifest ->
  verify_chunk -> replay round trip still works and the on-disk layout is
  byte-compatible with the unchanged V1 scheme.

All IO runs under pytest tmp_path; hermetic; no network; stdlib only.
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import archive, replay  # noqa: E402
from market_data_plane._canonical import canonical_line_bytes  # noqa: E402
from market_data_plane.manifest import (  # noqa: E402
    ManifestValidationError,
    build_manifest,
    canonical_manifest_bytes,
    is_hex64,
    sha256_hex,
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


def make_event(seq: int, exchange_ns: int) -> dict:
    event = {field: None for field in ENVELOPE_FIELDS}
    event.update(
        schema_version="mdp.market_event@1",
        raw_id=f"raw-{seq}",
        source_id="src1",
        venue="VEN",
        instrument_id="BTC-USDT",
        asset_class="crypto",
        event_type="TRADE",
        exchange_time_utc_ns=exchange_ns,
        receive_time_utc_ns=exchange_ns + 10,
        available_time_utc_ns=exchange_ns + 20,
        sequence_number=seq,
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
        source_id="src1", provider_id="prov1", venue="VEN", instrument_id="BTC-USDT",
        asset_class="crypto", event_class="trades",
        request_identity_secrets_removed={"symbol": "BTC-USDT"},
        entitlement_evidence_ref="entitlement-evidence-123",
        allowed_use_classification="RESEARCH_AUTHORIZED",
        retrieval_start_utc_ns=1_000, retrieval_end_utc_ns=2_000,
        parser_version="parser@1", normalizer_version="norm@1",
        created_utc=42,
    )
    kwargs.update(over)
    return kwargs


def put(root: Path, events: list, **over) -> dict:
    return archive.put_chunk_records(root, events, **identity_kwargs(**over))


def _valid_manifest() -> dict:
    return build_manifest(
        payload_sha256=sha256_hex(b"payload"), payload_byte_length=7, record_count=1,
        source_id="s", provider_id="p", venue="v", instrument_id="i", asset_class="a",
        event_class="e", entitlement_evidence_ref="ref",
        parser_version="parser@1", normalizer_version="norm@1", created_utc=1,
    )


# Grammar-violating IDs: the defect this lane closes was that chunk_path only
# checked len >= 4 and manifest_path validated nothing.
BAD_IDS = [
    "",                                  # empty
    "a" * 4,                             # old len>=4 defect boundary
    "abcde",                             # short
    "a" * 63,                            # 63 chars
    "a" * 65,                            # 65 chars
    "A" * 64,                            # uppercase
    "g" * 64,                            # non-hex
    "0" * 32 + "G" * 32,                 # partially uppercase
    "a" * 32 + " " + "a" * 31,           # separator embedded (64 chars, non-hex)
    "a" * 128,                           # overlong
    "../evil",                           # traversal
    "../../outside/manifest",            # deep traversal
    "a/b" * 32,                          # separators
    "/etc/passwd",                       # absolute path
    "/tmp/" + "a" * 64 + ".jsonl",       # absolute target file
    "%2e%2e%2f" + "a" * 56,              # encoded traversal
    "..%2f" + "a" * 62,                  # encoded traversal
    "a" * 64 + "/../../escape",          # suffix traversal past root
    "a" * 64 + "\n",                     # trailing newline (not grammar)
]

# Non-string / pathlike variants must also be rejected (never coerced).
BAD_NON_STRING = [
    Path("../evil"),
    Path("a" * 64),
    b"a" * 64,
    None,
    64,
    ("a" * 64,),
]


# ---------------------------------------------------------------------------
# content-ID grammar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", BAD_IDS)
def test_chunk_path_rejects_grammar_violations(tmp_path, bad):
    with pytest.raises(archive.ArchiveError):
        archive.chunk_path(tmp_path, bad)


@pytest.mark.parametrize("bad", BAD_IDS)
def test_manifest_path_rejects_grammar_violations(tmp_path, bad):
    with pytest.raises(archive.ArchiveError):
        archive.manifest_path(tmp_path, bad)


@pytest.mark.parametrize("bad", BAD_NON_STRING)
def test_chunk_path_rejects_non_string_ids(tmp_path, bad):
    with pytest.raises(archive.ArchiveError):
        archive.chunk_path(tmp_path, bad)


@pytest.mark.parametrize("bad", BAD_NON_STRING)
def test_manifest_path_rejects_non_string_ids(tmp_path, bad):
    with pytest.raises(archive.ArchiveError):
        archive.manifest_path(tmp_path, bad)


def test_is_hex64_grammar_helper():
    assert is_hex64("a" * 64)
    assert is_hex64("0123456789abcdef" * 4)
    for bad in BAD_IDS + BAD_NON_STRING:
        assert not is_hex64(bad), f"is_hex64 must reject {bad!r}"


def test_valid_ids_compose_unchanged_v1_layout(tmp_path):
    valid = "0123456789abcdef" * 4
    assert archive.chunk_path(tmp_path, valid) == (
        tmp_path / "chunks" / "01" / "23" / f"{valid}.jsonl"
    )
    assert archive.manifest_path(tmp_path, valid) == (
        tmp_path / "manifests" / f"{valid}.json"
    )


# ---------------------------------------------------------------------------
# traversal / absolute / encoded variants: fail closed BEFORE filesystem access
# ---------------------------------------------------------------------------


def test_traversal_ids_fail_closed_before_any_filesystem_access(tmp_path):
    outside = tmp_path / "mdp_a2_outside_traversal"
    outside.mkdir()
    sentinel_chunk = outside / "sentinel.jsonl"
    sentinel_chunk.write_bytes(b"OUTSIDE-CHUNK-BYTES\n")
    outside_manifest = outside / "outside_manifest.json"
    outside_manifest.write_bytes(b'{"never": "read"}\n')

    root = tmp_path / "root"
    root.mkdir()
    chunk_id = f"../{outside.name}/sentinel"
    manifest_id = f"../{outside.name}/outside_manifest"

    with pytest.raises(archive.ArchiveError):
        archive.chunk_path(root, chunk_id)
    with pytest.raises(archive.ArchiveError):
        archive.manifest_path(root, manifest_id)
    # Load/verify fail on the grammar BEFORE any read: had the outside file
    # been read, the failure class would differ (missing/valid-JSON paths).
    with pytest.raises(archive.ArchiveError):
        archive.load_manifest(root, manifest_id)
    with pytest.raises(archive.ArchiveError):
        archive.verify_chunk(root, chunk_id)

    # nothing was created or consumed: root stays empty, outside untouched
    assert not any(root.iterdir())
    assert sentinel_chunk.read_bytes() == b"OUTSIDE-CHUNK-BYTES\n"
    assert outside_manifest.read_bytes() == b'{"never": "read"}\n'


def test_absolute_and_encoded_manifest_ids_never_read_outside(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "mdp_a2_outside_abs"
    outside.mkdir()
    target = outside / "target.json"
    target.write_bytes(b'{"outside": true}\n')

    for bad in (str(target), ".." + chr(92) + "windows-style", "%2e%2e/escape"):
        with pytest.raises(archive.ArchiveError):
            archive.load_manifest(root, bad)
        with pytest.raises(archive.ArchiveError):
            archive.verify_chunk(root, bad)
    assert not any(root.iterdir())
    assert target.read_bytes() == b'{"outside": true}\n'


# ---------------------------------------------------------------------------
# symlink escapes at directory boundaries
# ---------------------------------------------------------------------------


def test_symlink_escape_at_chunk_directory_boundary(tmp_path):
    outside = tmp_path / "outside_chunk_target"
    outside.mkdir()
    root = tmp_path / "root"
    (root / "chunks").mkdir(parents=True)

    payload = canonical_line_bytes(make_event(0, 1))
    sha = sha256_hex(payload)
    h2, h2b = sha[:2], sha[2:4]
    (outside / h2b).mkdir()
    (outside / h2b / f"{sha}.jsonl").write_bytes(payload)

    os.symlink(outside, root / "chunks" / h2)

    # read through the boundary must fail closed (outside target not consumed)
    with pytest.raises(archive.ArchiveError):
        archive.verify_chunk(root, sha)
    # write through the same boundary must fail closed before any write
    with pytest.raises(archive.ArchiveError):
        archive.write_chunk(root, payload)

    # the outside target bytes are untouched and no temp sibling appeared
    assert (outside / h2b / f"{sha}.jsonl").read_bytes() == payload
    assert sorted(p.name for p in outside.iterdir()) == [h2b]
    # and nothing real was created inside root through the symlink boundary
    # (Path.exists follows intermediate symlinks, so inspect the tree without
    # descending: only the planted symlink itself is present)
    assert (root / "chunks" / h2).is_symlink()
    inside_entries = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
    assert inside_entries == ["chunks", os.path.join("chunks", h2)]


def test_symlink_escape_at_manifests_directory_boundary(tmp_path):
    outside = tmp_path / "outside_manifests"
    outside.mkdir()
    root = tmp_path / "root"
    root.mkdir()

    manifest = _valid_manifest()
    mid = manifest["manifest_id"]
    (outside / f"{mid}.json").write_bytes(canonical_manifest_bytes(manifest))

    os.symlink(outside, root / "manifests")

    with pytest.raises(archive.ArchiveError):
        archive.load_manifest(root, mid)
    with pytest.raises(archive.ArchiveError):
        archive.publish_manifest(root, manifest)

    # outside bytes untouched, no temp sibling written outside
    assert sorted(p.name for p in outside.iterdir()) == [f"{mid}.json"]
    assert (outside / f"{mid}.json").read_bytes() == canonical_manifest_bytes(manifest)


# ---------------------------------------------------------------------------
# filename/body binding
# ---------------------------------------------------------------------------


def test_load_manifest_rejects_valid_body_under_different_valid_filename(tmp_path):
    out = put(tmp_path, [make_event(0, 1)])
    manifest = out["manifest"]
    decoy_id = "b" * 64
    assert decoy_id != manifest["manifest_id"] and is_hex64(decoy_id)
    decoy_path = tmp_path / "manifests" / f"{decoy_id}.json"
    decoy_path.write_bytes(out["manifest_path"].read_bytes())  # byte-identical body

    with pytest.raises(ManifestValidationError) as excinfo:
        archive.load_manifest(tmp_path, decoy_id)
    assert decoy_id in str(excinfo.value)
    assert manifest["manifest_id"] in str(excinfo.value)
    assert excinfo.value.code == "HASH_DISAGREEMENT"

    # the honest copy still loads; the decoy file was never rewritten
    assert archive.load_manifest(tmp_path, manifest["manifest_id"]) == manifest
    assert decoy_path.read_bytes() == out["manifest_path"].read_bytes()


def test_replay_rejects_filename_body_mismatch_fail_closed(tmp_path):
    out = put(tmp_path, [make_event(0, 1)])
    decoy_id = "c" * 64
    (tmp_path / "manifests" / f"{decoy_id}.json").write_bytes(
        out["manifest_path"].read_bytes()
    )

    # public API without a callback: CorruptReplayInput (ReplayError family)
    with pytest.raises(replay.CorruptReplayInput) as excinfo:
        replay.replay(tmp_path, [decoy_id])
    assert excinfo.value.record["reason"] == "HASH_DISAGREEMENT"

    # with a quarantine callback: routed visibly, nothing streams silently
    routed = []
    result = replay.replay(tmp_path, [decoy_id], on_corrupt=routed.append)
    assert result["event_count"] == 0
    assert result["input_complete"] is False
    assert routed[0]["reason"] == "HASH_DISAGREEMENT"
    assert routed[0]["manifest_id"] == decoy_id

    with pytest.raises(replay.ReplayError):
        replay.replay_events(tmp_path, [decoy_id])


# ---------------------------------------------------------------------------
# verify_chunk with a malicious ID (pinned: ArchiveError, no filesystem write)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["", "a" * 63, "A" * 64, "g" * 64, "../evil", "/tmp/x"])
def test_verify_chunk_malicious_id_raises_archive_error_no_write(tmp_path, bad):
    root = tmp_path / "root"  # deliberately never created
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    with pytest.raises(archive.ArchiveError):
        archive.verify_chunk(root, bad)
    after = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    assert before == after, "malicious verify_chunk must not touch the filesystem"


def test_verify_chunk_malicious_id_never_probes_existing_layout(tmp_path):
    out = put(tmp_path, [make_event(0, 1)])
    snapshot = {
        str(p.relative_to(tmp_path)): p.read_bytes()
        for p in sorted(tmp_path.rglob("*"))
        if p.is_file()
    }
    for bad in ("../" + out["chunk_sha256"][:2], out["chunk_sha256"].upper()):
        with pytest.raises(archive.ArchiveError):
            archive.verify_chunk(tmp_path, bad)
    after = {
        str(p.relative_to(tmp_path)): p.read_bytes()
        for p in sorted(tmp_path.rglob("*"))
        if p.is_file()
    }
    assert after == snapshot


# ---------------------------------------------------------------------------
# replay with malicious manifest IDs: fail closed, never silent acceptance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad", ["", "../evil", "/etc/passwd", "A" * 64, "g" * 64, "a" * 65, "%2e%2e"]
)
def test_replay_rejects_malicious_manifest_ids_fail_closed(tmp_path, bad):
    put(tmp_path, [make_event(0, 1)])  # healthy archive present

    # without a callback: CorruptReplayInput / ReplayInputError (ReplayError)
    with pytest.raises(replay.ReplayError):
        replay.replay(tmp_path, [bad])

    if bad == "":
        # the empty id fails at replay's own input-validation layer
        # (ReplayInputError), before any manifest load or routing happens.
        return

    # with a quarantine callback: routed visibly, nothing streams silently
    routed = []
    result = replay.replay(tmp_path, [bad], on_corrupt=routed.append)
    assert result["event_count"] == 0
    assert result["input_complete"] is False
    assert routed, f"malicious id {bad!r} must route a visible record"

    with pytest.raises(replay.ReplayError):
        replay.replay_events(tmp_path, [bad])


def test_replay_malicious_id_mixed_with_valid_id_streams_only_valid(tmp_path):
    out = put(tmp_path, [make_event(0, 1)])
    routed = []
    result = replay.replay(
        tmp_path, ["../evil", out["manifest"]["manifest_id"]],
        on_corrupt=routed.append,
    )
    assert result["event_count"] == 1
    assert result["input_complete"] is False
    assert any(r["manifest_id"] == "../evil" for r in routed)


# ---------------------------------------------------------------------------
# positive control: valid round trip keeps the byte-compatible V1 layout
# ---------------------------------------------------------------------------


def test_positive_control_roundtrip_and_v1_layout_byte_compatible(tmp_path):
    events = [make_event(i, 1_000 + i) for i in range(2)]
    out = put(tmp_path, events)

    sha = out["chunk_sha256"]
    expected_chunk = tmp_path / "chunks" / sha[:2] / sha[2:4] / f"{sha}.jsonl"
    assert out["chunk_path"] == expected_chunk
    assert expected_chunk.exists()
    assert expected_chunk.read_bytes() == b"".join(canonical_line_bytes(e) for e in events)
    assert sha256_hex(expected_chunk.read_bytes()) == sha

    manifest = out["manifest"]
    expected_manifest = tmp_path / "manifests" / f"{manifest['manifest_id']}.json"
    assert out["manifest_path"] == expected_manifest
    assert expected_manifest.exists()
    assert expected_manifest.read_bytes() == canonical_manifest_bytes(manifest)

    loaded = archive.load_manifest(tmp_path, manifest["manifest_id"])
    assert loaded == manifest

    report = archive.verify_chunk(
        tmp_path, sha,
        expected_byte_length=out["chunk_byte_length"],
        expected_record_count=out["record_count"],
    )
    assert report["errors"] == []

    streamed = replay.replay_events(tmp_path, [manifest["manifest_id"]])
    assert [e["exchange_time_utc_ns"] for e in streamed] == [1_000, 1_001]

    # identical re-put stays a deduplicated no-op; the archive stays clean
    second = put(tmp_path, events)
    assert second["chunk_deduplicated"] is True
    assert second["manifest"]["manifest_id"] == manifest["manifest_id"]
    scan = archive.scan_orphans(tmp_path)
    assert scan["chunks_without_manifest"] == []
    assert scan["manifests_without_chunk"] == []
    assert scan["sha_mismatch_chunks"] == []
    assert scan["unexpected_chunk_names"] == []
