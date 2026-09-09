"""MDP-V1 lane A3: quarantine store tests (tests/test_mdp_quarantine.py).

Covers lineage-carrying quarantine records, forced reason codes from the
frozen reason_codes@1 registry (an event is never silently dropped), dedupe
by (raw reference, reason codes), crash-safe atomic batch writes (temp +
fsync + replace staged failures leave the previous store intact), visible
corruption on store reads, listing/replay of quarantined records, and the
end-to-end wiring from replay corruption routing into the store.

All IO runs under pytest tmp_path; no network; stdlib only.
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import archive, quarantine, replay  # noqa: E402
from market_data_plane._canonical import canonical_json, canonical_line_bytes  # noqa: E402
from market_data_plane.manifest import sha256_hex  # noqa: E402

ENVELOPE_FIELDS = [
    "schema_version", "event_id", "raw_id", "source_id", "venue", "instrument_id",
    "asset_class", "event_type", "exchange_time_utc_ns", "receive_time_utc_ns",
    "available_time_utc_ns", "sequence_number", "price", "quantity", "side",
    "bid_price", "ask_price", "bid_size", "ask_size", "currency", "price_precision",
    "size_precision", "quality_status", "reason_codes", "raw_sha256",
    "manifest_sha256", "normalizer_version",
]

REASON_CODES_AT_1 = (
    "MALFORMED_SHAPE", "MISSING_REQUIRED_FIELD", "UNKNOWN_EVENT_TYPE",
    "TIMEZONE_NAIVE_REJECTED", "NON_FINITE_PRICE", "PRECISION_LOSS",
    "NEGATIVE_PRICE", "NEGATIVE_SIZE", "CROSSED_QUOTE", "STALE_QUOTE",
    "IMPOSSIBLE_TIME_ORDER", "OUT_OF_ORDER_DELIVERY", "SEQUENCE_GAP",
    "SEQUENCE_RESET", "DUPLICATE_EVENT", "SOURCE_RESET_UNEVIDENCED",
    "UNKNOWN_INSTRUMENT", "MANIFEST_MISMATCH", "STATISTICAL_ANOMALY",
    "QUARANTINE_ORPHAN", "HASH_DISAGREEMENT",
)


def make_event(seq: int, exchange_ns: int, *, quality_status: str = "VALID") -> dict:
    event = {field: None for field in ENVELOPE_FIELDS}
    event.update(
        schema_version="mdp.market_event@1",
        event_id="0" * 63 + str(seq % 10),
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
        quality_status=quality_status,
        reason_codes=[],
        raw_sha256=sha256_hex(f"raw-{seq}".encode("utf-8")),
        manifest_sha256="a" * 64,
        normalizer_version="norm@1",
    )
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


# ---------------------------------------------------------------------------
# record shape / lineage / ids
# ---------------------------------------------------------------------------


def test_add_and_list_roundtrip_with_full_lineage(tmp_path):
    store = quarantine.QuarantineStore(tmp_path)
    event = make_event(0, 1_000)
    record = store.build_record(
        reason_codes=["MALFORMED_SHAPE"],
        manifest_id="f" * 64,
        chunk_sha256="e" * 64,
        byte_offset=512,
        event=event,
        quarantined_utc_ns=1_000_000,
        rule_version="reason_codes@1",
    )
    assert record["quarantine_id"] == hashlib.sha256(
        canonical_json({k: v for k, v in record.items() if k != "quarantine_id"})
        .encode("utf-8")
    ).hexdigest()
    summary = store.add([record])
    assert summary["added"] == [record["quarantine_id"]]
    assert summary["deduped"] == 0

    listed = store.records()
    assert listed == [record]
    stored = listed[0]
    assert stored["reason_codes"] == ["MALFORMED_SHAPE"]
    assert stored["manifest_id"] == "f" * 64  # raw reference lineage
    assert stored["chunk_sha256"] == "e" * 64
    assert stored["byte_offset"] == 512
    assert stored["event"] == event
    assert stored["quarantined_utc_ns"] == 1_000_000
    assert stored["rule_version"] == "reason_codes@1"

    # store file is canonical JSONL: one canonical record + newline per line
    raw = (tmp_path / "quarantine" / "records.jsonl").read_bytes()
    assert raw == canonical_line_bytes(record)


def test_quarantine_id_deterministic_and_content_bound(tmp_path):
    store = quarantine.QuarantineStore(tmp_path)
    kwargs = dict(
        reason_codes=["SEQUENCE_GAP"], manifest_id="a" * 64,
        chunk_sha256="b" * 64, byte_offset=0, event=None,
        quarantined_utc_ns=7,
    )
    first = store.build_record(**kwargs)
    second = store.build_record(**kwargs)
    assert first["quarantine_id"] == second["quarantine_id"]
    shifted = store.build_record(**{**kwargs, "byte_offset": 8})
    assert shifted["quarantine_id"] != first["quarantine_id"]


# ---------------------------------------------------------------------------
# forced reason codes (never silently dropped)
# ---------------------------------------------------------------------------


def test_local_reason_code_registry_matches_freeze():
    """A3's local reason_codes@1 copy equals the freeze (A1 reconciles)."""
    assert quarantine.REASON_CODES == REASON_CODES_AT_1
    assert quarantine.REJECT_TO_QUARANTINE_CODES == (
        "MALFORMED_SHAPE", "MISSING_REQUIRED_FIELD", "UNKNOWN_EVENT_TYPE",
        "TIMEZONE_NAIVE_REJECTED", "NON_FINITE_PRICE", "PRECISION_LOSS",
        "NEGATIVE_PRICE", "NEGATIVE_SIZE", "CROSSED_QUOTE", "IMPOSSIBLE_TIME_ORDER",
        "SOURCE_RESET_UNEVIDENCED", "UNKNOWN_INSTRUMENT", "MANIFEST_MISMATCH",
        "HASH_DISAGREEMENT", "QUARANTINE_ORPHAN",
    )
    assert quarantine.FLAG_SUSPECT_CODES == (
        "STALE_QUOTE", "OUT_OF_ORDER_DELIVERY", "SEQUENCE_GAP", "SEQUENCE_RESET",
        "STATISTICAL_ANOMALY",
    )
    assert quarantine.BOOKKEEPING_CODES == ("DUPLICATE_EVENT",)


def test_empty_reason_codes_rejected(tmp_path):
    store = quarantine.QuarantineStore(tmp_path)
    with pytest.raises(quarantine.QuarantineStoreError, match="never silently dropped"):
        store.build_record(reason_codes=[], manifest_id="a" * 64)
    with pytest.raises(quarantine.QuarantineStoreError):
        store.build_record(reason_codes=None, manifest_id="a" * 64)
    assert store.records() == []


def test_unknown_reason_code_rejected(tmp_path):
    store = quarantine.QuarantineStore(tmp_path)
    with pytest.raises(quarantine.QuarantineStoreError, match="reason_codes@1"):
        store.build_record(reason_codes=["MADE_UP_CODE"], manifest_id="a" * 64)
    # every frozen code is accepted; A3's local registry equals the freeze
    for code in REASON_CODES_AT_1:
        assert store.build_record(reason_codes=[code], quarantined_utc_ns=1)


def test_reason_codes_normalized_sorted_unique(tmp_path):
    store = quarantine.QuarantineStore(tmp_path)
    record = store.build_record(
        reason_codes=["SEQUENCE_GAP", "STALE_QUOTE", "SEQUENCE_GAP"],
        manifest_id="a" * 64,
        quarantined_utc_ns=3,
    )
    assert record["reason_codes"] == ["SEQUENCE_GAP", "STALE_QUOTE"]  # sorted, unique


def test_event_payload_type_enforced(tmp_path):
    store = quarantine.QuarantineStore(tmp_path)
    with pytest.raises(quarantine.QuarantineStoreError, match="event must be a dict"):
        store.build_record(reason_codes=["MALFORMED_SHAPE"], event="not-a-dict")
    with pytest.raises(quarantine.QuarantineStoreError, match="byte_offset"):
        store.build_record(reason_codes=["MALFORMED_SHAPE"], byte_offset="12")


# ---------------------------------------------------------------------------
# dedupe by (raw reference, reason codes)
# ---------------------------------------------------------------------------


def test_dedupe_same_raw_ref_same_reasons(tmp_path):
    store = quarantine.QuarantineStore(tmp_path)
    record = store.build_record(reason_codes=["HASH_DISAGREEMENT"],
                                manifest_id="a" * 64, chunk_sha256="b" * 64,
                                byte_offset=16, quarantined_utc_ns=1)
    assert store.add([record])["added"] == [record["quarantine_id"]]
    second = store.add([record])
    assert second["added"] == []
    assert second["deduped"] == 1
    assert len(store.records()) == 1


def test_no_dedupe_when_reasons_or_ref_differ(tmp_path):
    store = quarantine.QuarantineStore(tmp_path)
    base = dict(manifest_id="a" * 64, chunk_sha256="b" * 64, byte_offset=16,
                quarantined_utc_ns=1)
    r1 = store.build_record(reason_codes=["HASH_DISAGREEMENT"], **base)
    r2 = store.build_record(reason_codes=["MANIFEST_MISMATCH"], **base)  # same ref, new reason
    r3 = store.build_record(reason_codes=["HASH_DISAGREEMENT"],
                            **{**base, "byte_offset": 17})  # new ref, same reason
    summary = store.add([r1, r2, r3])
    assert len(summary["added"]) == 3
    assert len(store.records()) == 3


def test_dedupe_within_single_batch(tmp_path):
    store = quarantine.QuarantineStore(tmp_path)
    record = store.build_record(reason_codes=["DUPLICATE_EVENT"],
                                manifest_id="a" * 64, quarantined_utc_ns=1)
    summary = store.add([record, record])
    assert summary["added"] == [record["quarantine_id"]]
    assert summary["deduped"] == 1
    assert len(store.records()) == 1


# ---------------------------------------------------------------------------
# crash-safe atomic batch writes
# ---------------------------------------------------------------------------


def _seed_store(tmp_path: Path, count: int = 1) -> quarantine.QuarantineStore:
    store = quarantine.QuarantineStore(tmp_path)
    for index in range(count):
        store.add_record(reason_codes=["QUARANTINE_ORPHAN"], manifest_id=f"{index}" * 64,
                         quarantined_utc_ns=index)
    return store


@pytest.mark.parametrize("crash_where", ["write", "fsync", "replace"])
def test_crash_during_batch_write_leaves_store_intact(tmp_path, monkeypatch, crash_where):
    store = _seed_store(tmp_path)
    path = store.path
    before = path.read_bytes()

    import builtins

    real_open = builtins.open
    real_fsync = os.fsync
    real_replace = os.replace
    message = f"crash at {crash_where}"

    if crash_where == "write":
        class _CrashOnWrite:
            def __init__(self, handle):
                self._handle = handle

            def write(self, data):
                raise RuntimeError(message)

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
    elif crash_where == "fsync":
        def boom(fd):
            raise RuntimeError(message)
        monkeypatch.setattr(os, "fsync", boom)
    else:
        def boom(src, dst):
            raise RuntimeError(message)
        monkeypatch.setattr(os, "replace", boom)

    with pytest.raises(RuntimeError, match=message):
        store.add_record(reason_codes=["MANIFEST_MISMATCH"], manifest_id="c" * 64,
                         quarantined_utc_ns=99)

    monkeypatch.undo()
    # previous store content survives byte-for-byte; no partial or temp files
    assert path.read_bytes() == before
    assert len(store.records()) == 1
    assert not list(path.parent.glob(".tmp-*"))


def test_store_corrupt_line_raises_visibly(tmp_path):
    store = _seed_store(tmp_path)
    store.path.write_bytes(store.path.read_bytes() + b'{"torn": tru')  # external corruption
    with pytest.raises(quarantine.QuarantineStoreError, match="corrupt"):
        store.records()


def test_batch_write_is_one_atomic_replace(tmp_path, monkeypatch):
    store = quarantine.QuarantineStore(tmp_path)
    records = [
        store.build_record(reason_codes=["STALE_QUOTE"], manifest_id=f"{i}" * 64,
                           quarantined_utc_ns=i)
        for i in range(3)
    ]
    real_replace = os.replace
    calls = {"n": 0}

    def counting_replace(src, dst):
        calls["n"] += 1
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", counting_replace)
    store.add(records)
    assert calls["n"] == 1  # one atomic store commit for the whole batch
    assert len(store.records()) == 3


# ---------------------------------------------------------------------------
# listing / replay of quarantined records
# ---------------------------------------------------------------------------


def test_replay_listing_with_predicate(tmp_path):
    store = _seed_store(tmp_path, count=2)
    store.add_record(reason_codes=["CROSSED_QUOTE"], manifest_id="z" * 64,
                     byte_offset=1, quarantined_utc_ns=50)
    assert len(store.records()) == 3
    assert len(store.replay()) == 3
    assert [r["manifest_id"] for r in store.replay({"manifest_id": "z" * 64})] == ["z" * 64]
    assert len(store.replay({"reason_codes": ["QUARANTINE_ORPHAN"]})) == 2
    assert store.replay({"manifest_id": "nope"}) == []


def test_events_returns_parseable_events_only(tmp_path):
    store = quarantine.QuarantineStore(tmp_path)
    event = make_event(0, 5)
    store.add([
        store.build_record(reason_codes=["NEGATIVE_PRICE"], event=event,
                           quarantined_utc_ns=1),
        store.build_record(reason_codes=["QUARANTINE_ORPHAN"], event=None,
                           quarantined_utc_ns=2),
    ])
    assert store.events() == [event]


def test_missing_store_reads_empty(tmp_path):
    assert quarantine.QuarantineStore(tmp_path).records() == []


# ---------------------------------------------------------------------------
# end-to-end: replay corruption -> quarantine store
# ---------------------------------------------------------------------------


def test_replay_corruption_routed_into_quarantine_store(tmp_path):
    """A corrupted replay record lands in the store with full lineage."""
    good = make_event(0, 1_000)
    payload = canonical_line_bytes(good) + b'{"torn record"\n'
    from market_data_plane.manifest import build_manifest
    manifest = build_manifest(
        payload_sha256=sha256_hex(payload), payload_byte_length=len(payload),
        record_count=2, time_bounds={}, **identity_kwargs(event_class="torn", created_utc=7),
    )
    archive.write_chunk(tmp_path, payload, expected_record_count=2)
    archive.publish_manifest(tmp_path, manifest)
    chunk_sha = manifest["payload_sha256"]

    store = quarantine.QuarantineStore(tmp_path)

    def route_to_quarantine(record):
        store.add_record(
            reason_codes=[record["reason"]],
            manifest_id=record.get("manifest_id"),
            chunk_sha256=record.get("chunk_sha256"),
            byte_offset=record.get("byte_offset"),
            quarantined_utc_ns=123,
        )

    result = replay.replay(tmp_path, [manifest["manifest_id"]],
                           on_corrupt=route_to_quarantine)
    assert result["event_count"] == 1
    assert result["input_complete"] is False

    quarantined = store.records()
    assert len(quarantined) == 1
    assert quarantined[0]["reason_codes"] == ["MALFORMED_SHAPE"]
    assert quarantined[0]["manifest_id"] == manifest["manifest_id"]
    assert quarantined[0]["chunk_sha256"] == chunk_sha
    assert quarantined[0]["byte_offset"] == len(canonical_line_bytes(good))

    # re-running the same replay must not double-quarantine
    replay.replay(tmp_path, [manifest["manifest_id"]], on_corrupt=route_to_quarantine)
    assert len(store.records()) == 1


def test_no_append_mode_in_store_module_source():
    import re
    source = Path(quarantine.__file__).read_text()
    assert not re.search(r"open\([^)]*['\"]a[bx+]*['\"]", source), \
        "append-mode open found in market_data_plane.quarantine"
