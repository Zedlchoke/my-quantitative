"""MDP-V1 lane A3: deterministic replay tests (tests/test_mdp_replay.py).

Covers the frozen replay_contract: total order with event_id final
tie-break, in-process and cross-process (different cwd) byte-identical
replays, exact predicate recording, newer-file non-discovery, corruption
routing (bad JSON, non-canonical bytes, hash/count/length mismatch,
duplicates) via quarantine callback or CorruptReplayInput, and
manifest-semantics-conditional flagging (SEQUENCE_GAP / SEQUENCE_RESET /
OUT_OF_ORDER_DELIVERY).

All IO runs under pytest tmp_path; no network; stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import archive, replay  # noqa: E402
from market_data_plane._canonical import canonical_line_bytes, replay_order_key  # noqa: E402
from market_data_plane.manifest import compute_manifest_id, sha256_hex  # noqa: E402

ENVELOPE_FIELDS = [
    "schema_version", "event_id", "raw_id", "source_id", "venue", "instrument_id",
    "asset_class", "event_type", "exchange_time_utc_ns", "receive_time_utc_ns",
    "available_time_utc_ns", "sequence_number", "price", "quantity", "side",
    "bid_price", "ask_price", "bid_size", "ask_size", "currency", "price_precision",
    "size_precision", "quality_status", "reason_codes", "raw_sha256",
    "manifest_sha256", "normalizer_version",
]

RESEARCH_ROOT = Path(__file__).resolve().parents[1]


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


_UNSET = object()


def make_event(seq: int, exchange_ns: int, *, instrument: str = "BTC-USDT",
               source: str = "src1", venue: str = "VEN", event_type: str = "TRADE",
               raw_extra: str = "", sequence: int = _UNSET) -> dict:
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
        event_type=event_type,
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
        raw_sha256=sha256_hex(f"raw-bytes-{seq}-{raw_extra}".encode("utf-8")),
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


def stream_bytes(events: list) -> bytes:
    return b"".join(canonical_line_bytes(event) for event in events)


def test_envelope_fields_match_freeze():
    """The module's envelope copy equals the freeze's 27-field event list."""
    assert len(ENVELOPE_FIELDS) == 27
    assert replay.ENVELOPE_FIELDS == ENVELOPE_FIELDS


def test_hot_path_import_isolation(tmp_path):
    """Replay/archive import no pandas/pandera/dvc/nautilus_trader (freeze rule)."""
    runner = tmp_path / "isolation_probe.py"
    runner.write_text(
        "import sys\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "import market_data_plane.archive\n"
        "import market_data_plane.replay\n"
        "import market_data_plane.quarantine\n"
        "banned = {'pandas', 'pandera', 'dvc', 'nautilus_trader'}\n"
        "loaded = sorted(banned & set(sys.modules))\n"
        "print('LOADED:', loaded)\n",
        encoding="utf-8",
    )
    proc = subprocess.run([sys.executable, str(runner), str(RESEARCH_ROOT / "research")],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "LOADED: []"


# ---------------------------------------------------------------------------
# total order and determinism
# ---------------------------------------------------------------------------


def test_total_order_and_manifest_list_order_independence(tmp_path):
    events_a = [make_event(0, 3_000), make_event(1, 1_000)]
    events_b = [make_event(2, 2_000, source="src2"), make_event(3, 1_500)]
    manifest_a = put(tmp_path, events_a)["manifest"]
    manifest_b = put(tmp_path, events_b, source_id="src2", event_class="trades-b",
                     created_utc=43)["manifest"]

    expected = sorted(events_a + events_b, key=replay_order_key)
    assert [e["event_id"] for e in expected] == [
        events_a[1]["event_id"],  # exchange 1_000
        events_b[1]["event_id"],  # exchange 1_500
        events_b[0]["event_id"],  # exchange 2_000
        events_a[0]["event_id"],  # exchange 3_000
    ]

    result_forward = replay.replay(tmp_path, [manifest_a["manifest_id"], manifest_b["manifest_id"]])
    result_reversed = replay.replay(tmp_path, [manifest_b["manifest_id"], manifest_a["manifest_id"]])
    assert result_forward["stream_digest"] == result_reversed["stream_digest"]
    assert result_forward["event_count"] == 4
    assert result_forward["stream_digest"] == hashlib.sha256(stream_bytes(expected)).hexdigest()
    events_out = replay.replay_events(
        tmp_path, [manifest_b["manifest_id"], manifest_a["manifest_id"]])
    assert [e["event_id"] for e in events_out] == [e["event_id"] for e in expected]


def test_event_id_is_final_tie_break(tmp_path):
    # Two events identical on the first eight order-key fields; only
    # event_id (via raw_sha256) distinguishes them.
    e1 = make_event(0, 1_000, raw_extra="first")
    e2 = make_event(0, 1_000, raw_extra="second")
    assert e1["event_id"] != e2["event_id"]
    expected_sorted_ids = sorted([e1["event_id"], e2["event_id"]])
    for case, (first, second, created) in enumerate(
        ((e1, e2, 101), (e2, e1, 102)), start=1
    ):
        manifest = put(tmp_path, [second, first],
                       event_class=f"tie-{case}", created_utc=created)["manifest"]
        streamed = replay.replay_events(tmp_path, [manifest["manifest_id"]])
        assert [e["event_id"] for e in streamed] == expected_sorted_ids
        assert replay.replay(tmp_path, [manifest["manifest_id"]])["event_count"] == 2


def test_replay_twice_in_process_byte_identical(tmp_path):
    manifest = put(tmp_path, [make_event(i, (5 - i) * 1_000) for i in range(5)])["manifest"]
    first = replay.replay(tmp_path, [manifest["manifest_id"]], predicate={"venue": "VEN"})
    second = replay.replay(tmp_path, [manifest["manifest_id"]], predicate={"venue": "VEN"})
    assert first == second
    assert first["stream_digest"] == second["stream_digest"]
    stream1 = b"".join(canonical_line_bytes(e)
                       for e in replay.replay_events(tmp_path, [manifest["manifest_id"]],
                                                     predicate={"venue": "VEN"}))
    stream2 = b"".join(canonical_line_bytes(e)
                       for e in replay.replay_events(tmp_path, [manifest["manifest_id"]],
                                                     predicate={"venue": "VEN"}))
    assert stream1 == stream2
    assert hashlib.sha256(stream1).hexdigest() == first["stream_digest"]


def test_replay_subprocess_different_cwd_byte_identical(tmp_path):
    """Same replay in a SUBPROCESS from a different cwd yields the same digest."""
    manifest = put(tmp_path, [make_event(i, 10_000 - i) for i in range(4)])["manifest"]
    in_process = replay.replay(tmp_path, [manifest["manifest_id"]],
                               predicate={"instrument_id": "BTC-USDT"})

    other_cwd = tmp_path / "unrelated-cwd"
    other_cwd.mkdir()
    runner = other_cwd / "replay_runner.py"
    runner.write_text(
        "import json, sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from market_data_plane import replay\n"
        "root = Path(sys.argv[2])\n"
        "ids = sys.argv[3].split(',') if sys.argv[3] else []\n"
        "predicate = json.loads(sys.argv[4]) if sys.argv[4] else None\n"
        "result = replay.replay(root, ids, predicate)\n"
        "print(json.dumps(result, sort_keys=True))\n",
        encoding="utf-8",
    )
    env = dict(os.environ, PYTHONHASHSEED="random")
    proc = subprocess.run(
        [sys.executable, str(runner), str(RESEARCH_ROOT / "research"), str(tmp_path),
         manifest["manifest_id"], json.dumps({"instrument_id": "BTC-USDT"})],
        cwd=other_cwd, capture_output=True, text=True, env=env, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    from_other_process = json.loads(proc.stdout)
    assert from_other_process == in_process
    assert from_other_process["stream_digest"] == in_process["stream_digest"]


# ---------------------------------------------------------------------------
# predicate
# ---------------------------------------------------------------------------


def test_predicate_recorded_exactly_and_filters(tmp_path):
    events_x = [make_event(i, i * 1_000, instrument="ETH-USDT") for i in range(2)]
    events_btc = [make_event(9, 5_000, instrument="BTC-USDT")]
    manifest = put(tmp_path, events_x + events_btc, event_class="mixed",
                   created_utc=43)["manifest"]

    predicate = {"instrument_id": "ETH-USDT"}
    result = replay.replay(tmp_path, [manifest["manifest_id"]], predicate)
    assert result["predicate"] == predicate  # recorded exactly as given
    assert result["event_count"] == 2
    assert result["stream_digest"] == hashlib.sha256(stream_bytes(events_x)).hexdigest()

    empty = replay.replay(tmp_path, [manifest["manifest_id"]])
    assert empty["predicate"] is None
    assert empty["event_count"] == 3

    everything = replay.replay(tmp_path, [manifest["manifest_id"]], {})
    assert everything["event_count"] == 3  # empty predicate matches all


def test_predicate_with_unknown_key_raises(tmp_path):
    manifest = put(tmp_path, [make_event(0, 1)])["manifest"]
    with pytest.raises(replay.ReplayInputError, match="envelope field"):
        replay.replay(tmp_path, [manifest["manifest_id"]], {"not_a_field": 1})
    with pytest.raises(replay.ReplayInputError, match="JSON-serializable"):
        replay.replay(tmp_path, [manifest["manifest_id"]], {"venue": object()})


# ---------------------------------------------------------------------------
# newer-file non-discovery
# ---------------------------------------------------------------------------


def test_replay_never_discovers_newer_files(tmp_path):
    manifest_one = put(tmp_path, [make_event(i, i * 1_000) for i in range(2)])["manifest"]
    baseline = replay.replay(tmp_path, [manifest_one["manifest_id"]])

    # A newer chunk + manifest appear in the archive after the first replay.
    newer = put(tmp_path, [make_event(50, 50_000)], event_class="newer", created_utc=99)

    # Make the new chunk unreadable: any discovery/read of it must fail loudly.
    newer["chunk_path"].chmod(0o000)
    try:
        again = replay.replay(tmp_path, [manifest_one["manifest_id"]])
        assert again == baseline
        assert again["stream_digest"] == baseline["stream_digest"]
        assert again["event_count"] == baseline["event_count"]
    finally:
        newer["chunk_path"].chmod(0o644)


# ---------------------------------------------------------------------------
# corruption routing
# ---------------------------------------------------------------------------


def _put_raw_chunk(root: Path, payload: bytes, record_count: int, **over) -> dict:
    from market_data_plane.manifest import build_manifest
    manifest = build_manifest(
        payload_sha256=sha256_hex(payload), payload_byte_length=len(payload),
        record_count=record_count, time_bounds={}, **identity_kwargs(**over),
    )
    archive.write_chunk(root, payload, expected_record_count=record_count)
    archive.publish_manifest(root, manifest)
    return {"manifest": manifest, "chunk_path": archive.chunk_path(root, manifest["payload_sha256"])}


def test_corrupt_bad_json_routes_to_callback_and_marks_incomplete(tmp_path):
    good = make_event(0, 1_000)
    payload = canonical_line_bytes(good) + b'{"broken json"\n' + canonical_line_bytes(make_event(1, 2_000))
    out = _put_raw_chunk(tmp_path, payload, record_count=3, event_class="broken",
                         created_utc=43)

    routed = []
    result = replay.replay(tmp_path, [out["manifest"]["manifest_id"]], on_corrupt=routed.append)
    assert len(routed) == 1
    assert routed[0]["reason"] == "MALFORMED_SHAPE"
    assert routed[0]["manifest_id"] == out["manifest"]["manifest_id"]
    assert routed[0]["chunk_sha256"] == out["manifest"]["payload_sha256"]
    assert routed[0]["byte_offset"] == len(canonical_line_bytes(good))
    assert result["event_count"] == 2
    assert result["input_complete"] is False
    assert result["chunk_digests"][0]["corrupt_record_count"] == 1


def test_corrupt_bad_json_raises_without_callback(tmp_path):
    payload = b'{"not canonical"\n'
    out = _put_raw_chunk(tmp_path, payload, record_count=1, event_class="broken2",
                         created_utc=44)
    with pytest.raises(replay.CorruptReplayInput) as excinfo:
        replay.replay(tmp_path, [out["manifest"]["manifest_id"]])
    assert excinfo.value.record["reason"] == "MALFORMED_SHAPE"


def test_non_canonical_line_is_corrupt(tmp_path):
    import json as _json
    event = make_event(0, 7)
    non_canonical = (_json.dumps(event) + "\n").encode("utf-8")  # unsorted keys
    assert canonical_line_bytes(event) != non_canonical
    out = _put_raw_chunk(tmp_path, non_canonical, record_count=1,
                         event_class="uncanon", created_utc=45)
    routed = []
    replay.replay(tmp_path, [out["manifest"]["manifest_id"]], on_corrupt=routed.append)
    assert routed[0]["reason"] == "MALFORMED_SHAPE"
    assert "canonical" in routed[0]["detail"]


def test_corrupt_chunk_hash_mismatch_routes_whole_chunk(tmp_path):
    manifest_id = put(tmp_path, [make_event(i, i * 100) for i in range(2)])["manifest"]["manifest_id"]
    out = put(tmp_path, [make_event(9, 9_000)], event_class="tampered", created_utc=43)
    out["chunk_path"].write_bytes(b"totally different bytes\n")

    routed = []
    result = replay.replay(tmp_path, [manifest_id, out["manifest"]["manifest_id"]],
                           on_corrupt=routed.append)
    tampered = [record for record in routed if record["reason"] == "HASH_DISAGREEMENT"]
    assert len(tampered) == 1
    assert tampered[0]["chunk_sha256"] == out["manifest"]["payload_sha256"]
    assert result["event_count"] == 2  # only the healthy chunk streams
    assert result["input_complete"] is False


def test_corrupt_byte_length_mismatch_routes(tmp_path):
    events = [make_event(i, i) for i in range(2)]
    payload = stream_bytes(events)
    out = _put_raw_chunk(tmp_path, payload, record_count=2, event_class="lenbad",
                         created_utc=46)
    manifest = dict(out["manifest"])
    manifest["payload_byte_length"] = manifest["payload_byte_length"] + 3
    manifest["manifest_id"] = compute_manifest_id(manifest)
    archive.publish_manifest(tmp_path, manifest)  # a different manifest id/file

    routed = []
    replay.replay(tmp_path, [manifest["manifest_id"]], on_corrupt=routed.append)
    assert routed[0]["reason"] == "MANIFEST_MISMATCH"
    assert "byte length" in routed[0]["detail"]


def test_missing_manifest_routed_visibly(tmp_path):
    routed = []
    result = replay.replay(tmp_path, ["f" * 64], on_corrupt=routed.append)
    assert routed[0]["reason"] == "MANIFEST_MISMATCH"
    assert result["event_count"] == 0
    assert result["input_complete"] is False
    with pytest.raises(replay.CorruptReplayInput):
        replay.replay(tmp_path, ["f" * 64])


# ---------------------------------------------------------------------------
# duplicates
# ---------------------------------------------------------------------------


def test_duplicate_event_first_streams_second_routed_to_callback(tmp_path):
    shared = [make_event(i, i * 1_000) for i in range(2)]
    fresh = make_event(7, 7_000)
    manifest_a = put(tmp_path, shared + [fresh])["manifest"]
    manifest_b = put(tmp_path, shared, event_class="overlap", created_utc=43)["manifest"]

    routed = []
    result = replay.replay(tmp_path, [manifest_a["manifest_id"], manifest_b["manifest_id"]],
                           on_corrupt=routed.append)
    duplicates = [record for record in routed if record["reason"] == "DUPLICATE_EVENT"]
    assert len(duplicates) == 2  # both shared events appear twice
    assert all(record["event_id"] in {e["event_id"] for e in shared} for record in duplicates)
    assert result["event_count"] == 3  # first occurrences + fresh stream once each


def test_duplicate_event_raises_without_callback(tmp_path):
    shared = make_event(0, 1_000)
    manifest_a = put(tmp_path, [shared])["manifest"]
    manifest_b = put(tmp_path, [shared], event_class="overlap", created_utc=43)["manifest"]
    with pytest.raises(replay.CorruptReplayInput) as excinfo:
        replay.replay(tmp_path, [manifest_a["manifest_id"], manifest_b["manifest_id"]])
    assert excinfo.value.record["reason"] == "DUPLICATE_EVENT"


# ---------------------------------------------------------------------------
# semantics-conditional flagging
# ---------------------------------------------------------------------------


def test_sequence_gap_flagged_only_under_contiguous(tmp_path):
    events = [make_event(0, 1_000), make_event(1, 2_000), make_event(5, 3_000)]
    contiguous = put(tmp_path, events, sequence_semantics="CONTIGUOUS")["manifest"]
    none_sem = put(tmp_path, events, sequence_semantics="NONE", event_class="none-sem",
                   created_utc=43)["manifest"]

    flagged = replay.replay(tmp_path, [contiguous["manifest_id"]])
    gaps = [flag for flag in flagged["semantic_flags"] if flag["reason"] == "SEQUENCE_GAP"]
    assert len(gaps) == 1
    assert gaps[0]["detail"] == "missing sequence numbers [2, 3, 4]"
    assert gaps[0]["manifest_id"] == contiguous["manifest_id"]
    assert flagged["event_count"] == 3

    unflagged = replay.replay(tmp_path, [none_sem["manifest_id"]])
    assert unflagged["semantic_flags"] == []
    assert unflagged["stream_digest"] == flagged["stream_digest"]  # flags never rewrite bytes


def test_sequence_reset_flagged_under_contiguous(tmp_path):
    events = [make_event(0, 1_000), make_event(1, 2_000),
              make_event(2, 3_000, sequence=0), make_event(3, 4_000, sequence=1)]
    manifest = put(tmp_path, events, sequence_semantics="CONTIGUOUS")["manifest"]
    result = replay.replay(tmp_path, [manifest["manifest_id"]])
    resets = [flag for flag in result["semantic_flags"] if flag["reason"] == "SEQUENCE_RESET"]
    assert len(resets) == 1
    assert "sequence 0 follows 1" in resets[0]["detail"]


def test_null_sequence_rejected_under_contiguous_but_streams_under_none(tmp_path):
    event = make_event(0, 1_000, sequence=None)
    contiguous = put(tmp_path, [event], sequence_semantics="CONTIGUOUS")["manifest"]
    routed = []
    result = replay.replay(tmp_path, [contiguous["manifest_id"]], on_corrupt=routed.append)
    assert routed[0]["reason"] == "MALFORMED_SHAPE"
    assert "CONTIGUOUS" in routed[0]["detail"]
    assert result["event_count"] == 0

    none_sem = put(tmp_path, [event], sequence_semantics="NONE", event_class="none2",
                   created_utc=43)["manifest"]
    ok = replay.replay(tmp_path, [none_sem["manifest_id"]])
    assert ok["event_count"] == 1
    assert ok["semantic_flags"] == []
    assert ok["input_complete"] is True


def test_out_of_order_flagged_only_under_ordered_delivery(tmp_path):
    events = [make_event(0, 5_000), make_event(1, 1_000)]  # file order violates time order
    ordered = put(tmp_path, events, ordered_delivery=True)["manifest"]
    unordered = put(tmp_path, events, ordered_delivery=False, event_class="unordered",
                    created_utc=43)["manifest"]

    flagged = replay.replay(tmp_path, [ordered["manifest_id"]])
    flags = [flag for flag in flagged["semantic_flags"] if flag["reason"] == "OUT_OF_ORDER_DELIVERY"]
    assert len(flags) == 1
    assert flags[0]["manifest_id"] == ordered["manifest_id"]
    assert "ordered_delivery=true" in flags[0]["detail"]

    # With ordered_delivery=false the delivery-order flag is never raised.
    # (A SEQUENCE_RESET flag may still appear under CONTIGUOUS sequence
    # semantics -- delivery order and sequence semantics are independent
    # frozen dimensions.)
    silent = replay.replay(tmp_path, [unordered["manifest_id"]])
    assert [flag for flag in silent["semantic_flags"]
            if flag["reason"] == "OUT_OF_ORDER_DELIVERY"] == []
    assert silent["stream_digest"] == flagged["stream_digest"]


def test_out_of_order_in_order_file_has_no_flag(tmp_path):
    events = [make_event(i, i * 1_000) for i in range(3)]
    manifest = put(tmp_path, events, ordered_delivery=True)["manifest"]
    result = replay.replay(tmp_path, [manifest["manifest_id"]])
    assert result["semantic_flags"] == []


def test_result_records_inputs_and_chunk_digests(tmp_path):
    manifest = put(tmp_path, [make_event(0, 1)])["manifest"]
    result = replay.replay(tmp_path, [manifest["manifest_id"]], {"venue": "VEN"})
    assert result["manifest_ids"] == [manifest["manifest_id"]]
    assert result["predicate"] == {"venue": "VEN"}
    assert result["order_key_fields"] == [
        "exchange_time_utc_ns", "receive_time_utc_ns", "available_time_utc_ns",
        "source_id", "venue", "instrument_id", "event_type", "sequence_number", "event_id",
    ]
    assert result["input_complete"] is True
    assert len(result["chunk_digests"]) == 1
    assert result["chunk_digests"][0]["event_count"] == 1
    assert result["quarantined"] == []
    assert result["duplicates"] == []
