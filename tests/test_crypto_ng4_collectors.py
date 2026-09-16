"""CRYPTO-NG4 collector unit goldens — SYNTHETIC ONLY, NO NETWORK.

Lane A8 goldens for the frozen A3 prospective contract
(cng4-a3-prospective-contract-dossier.json, schema cng4_a3_prospective_contract@1):

- envelope {recv_utc, channel, seq, payload} shape + microsecond recv_utc
- reconnect gap-marking: synthetic drop -> explicit gap record written INTO
  the raw shard (the gap is DATA), fail-loud semantics
- duplicate / out-of-order handling per freeze field 8 (verbatim capture,
  counted, never deduplicated at capture)
- content-addressed raw-byte hashing + manifest append with
  prev_manifest_sha256 head chaining + tamper detection
- payload-shape validation: wrong shape -> LOUD rejected subrecord, main
  shard untouched
- heartbeat file writing (bytes-written + per-channel shape counts)
- inode-check on append handles; day rollover; orphan shard finalization

Run: .venv/bin/python -m pytest tests/test_crypto_ng4_collectors.py -q
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parent
sys.path.insert(0, str(WORKTREE))

from research.control.crypto_ng4_run.collectors import core, venues  # noqa: E402
from research.control.crypto_ng4_run.collectors.collector import (  # noqa: E402
    Collector,
    write_pidfile,
)
from research.control.crypto_ng4_run.collectors.core import (  # noqa: E402
    AppendHandle,
    LoudError,
    ManifestAppender,
    ShardWriter,
    finalize_orphan_shards,
    manifest_has_path,
    shard_rel_path,
)


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.t = start

    def __call__(self) -> datetime:
        return self.t

    def advance(self, seconds: float) -> None:
        from datetime import timedelta

        self.t = self.t + timedelta(seconds=seconds)


def fresh(tmp_path: Path, venue: str = "coinbase"):
    root = tmp_path / "raw"
    run = tmp_path / "run"
    root.mkdir(parents=True)
    run.mkdir(parents=True)
    clock = FakeClock(datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc))
    return root, run, clock


def make_collector(tmp_path: Path, venue: str = "coinbase"):
    root = tmp_path / "raw"
    run = tmp_path / "run"
    root.mkdir(parents=True, exist_ok=True)
    run.mkdir(parents=True, exist_ok=True)
    clock = FakeClock(datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc))
    col = Collector(venue, data_root=root, run_dir=run, clock=clock)
    import time as _time

    col.monotonic = _time.monotonic  # real monotonic; watchdog not driven in tests
    col.tracker = venues.SequenceTracker(venue)
    col._open_shard(core.utc_now_iso(clock))
    return col, root, run, clock


def read_shard_lines(path: Path) -> list:
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# envelope + shard layout (freeze fields 2/7)
# ---------------------------------------------------------------------------
def test_envelope_shape_and_microsecond_recv_utc(tmp_path):
    root, run, clock = fresh(tmp_path)
    sw = ShardWriter(root, "coinbase", "2026-09-16", 1, clock=clock)
    sw.open()
    sw.append_message(
        "2026-09-16T12:00:00.123456Z", "ticker", None, {"channel": "ticker"}
    )
    p = sw.close("2026-09-16T12:00:01Z")
    assert p == root / "coinbase" / "2026" / "09" / "16" / "00000001.jsonl"
    (row,) = read_shard_lines(p)
    assert set(row.keys()) == {"recv_utc", "channel", "seq", "payload"}
    assert row["seq"] is None
    assert row["recv_utc"] == "2026-09-16T12:00:00.123456Z"
    assert row["recv_utc"].endswith("Z") and len(row["recv_utc"].split(".")[1]) == 7  # 123456Z -> 6 frac digits + Z
    assert row["payload"] == {"channel": "ticker"}


def test_shard_path_convention_venue_day_epoch(tmp_path):
    root, _, _ = fresh(tmp_path)
    assert shard_rel_path("kraken", "2026-11-02", 7) == "kraken/2026/11/02/00000007.jsonl"


# ---------------------------------------------------------------------------
# gap marking: synthetic drop -> gap record written, fail-loud (field 5)
# ---------------------------------------------------------------------------
def test_coinbase_gap_marked_as_data_record(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "coinbase")
    msgs = [
        {"channel": "ticker", "timestamp": "t", "sequence_num": n, "events": []}
        for n in (0, 1, 2)
    ] + [{"channel": "ticker", "timestamp": "t", "sequence_num": 5, "events": []}]
    for m in msgs:
        col.process_text(json.dumps(m))
    rel = shard_rel_path("coinbase", "2026-09-16", col.conn_epoch)
    shard_path = root / (rel + ".open")
    lines = read_shard_lines(shard_path)
    gaps = [ln for ln in lines if ln.get("type") == "gap"]
    assert len(gaps) == 1, "synthetic drop must produce exactly one gap record"
    g = gaps[0]
    assert g["venue"] == "coinbase" and g["channel"] == "ticker"
    assert g["from_seq"] == 2 and g["to_seq"] == 5 and g["missing_count"] == 2
    assert g["first_recv_utc"].endswith("Z")
    assert col.shard.gap_count == 1
    # the gap did NOT suppress the offending message itself
    assert sum(1 for ln in lines if ln.get("payload", {}).get("sequence_num") == 5) == 1


def test_coinbase_duplicate_and_regression_not_gaps(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "coinbase")
    for n in (0, 1, 2, 2, 1):  # duplicate then regression
        col.process_text(
            json.dumps({"channel": "ticker", "timestamp": "t", "sequence_num": n, "events": []})
        )
    lines = read_shard_lines(root / (shard_rel_path("coinbase", "2026-09-16", col.conn_epoch) + ".open"))
    assert not [ln for ln in lines if ln.get("type") == "gap"]
    assert col.shard.gap_count == 0
    assert col.shard.dup_count == 2  # both repeated (channel, seq) keys counted
    assert col.tracker.reg_count == 2  # both in-epoch regressions counted, neither a frozen gap
    assert len(lines) == 5  # verbatim capture: ALL five lines preserved


def test_kraken_book_snapshot_resets_continuity_and_gap_detected(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "kraken")

    def book(seq):
        # MEASURED census shape: side 'buy'/'sell', numeric price/qty
        return {"feed": "book", "product_id": "PF_XBTUSD", "side": "buy", "seq": seq, "price": 100.0, "qty": 1.0, "timestamp": 1}

    col.process_text(json.dumps(book(10)))
    col.process_text(json.dumps({"feed": "book_snapshot", "product_id": "PF_XBTUSD", "ticks": [], "timestamp": 2}))
    col.process_text(json.dumps(book(10)))  # fresh snapshot clears continuity
    lines = read_shard_lines(root / (shard_rel_path("kraken", "2026-09-16", col.conn_epoch) + ".open"))
    assert not [ln for ln in lines if ln.get("type") == "gap"]
    col.process_text(json.dumps(book(14)))  # delta 10 -> 14 = gap of 3
    lines = read_shard_lines(root / (shard_rel_path("kraken", "2026-09-16", col.conn_epoch) + ".open"))
    gaps = [ln for ln in lines if ln.get("type") == "gap"]
    assert len(gaps) == 1 and gaps[0]["missing_count"] == 3
    assert gaps[0]["channel"] == "book" and "PF_XBTUSD" in gaps[0]["instrument"]


def test_deribit_prev_change_id_gap_and_snapshot_reset(tmp_path):
    """MEASURED semantics: the 100ms book channel aggregates events, so
    inter-delivery change_id deltas are large by design; losslessness is
    carried by prev_change_id.  Gap iff prev_change_id != last delivered
    change_id; snapshot resets continuity."""
    col, root, run, clock = make_collector(tmp_path, "deribit")

    def dbk(change_id, typ, prev_change_id=None):
        data = {
            "timestamp": 1789552274651,
            "type": typ,
            "change_id": change_id,
            "instrument_name": "BTC-PERPETUAL",
            "bids": [],
            "asks": [],
        }
        if prev_change_id is not None:
            data["prev_change_id"] = prev_change_id
        return {
            "jsonrpc": "2.0",
            "method": "subscription",
            "params": {"channel": "book.BTC-PERPETUAL.100ms", "data": data},
        }

    col.process_text(json.dumps(dbk(174318940803, "snapshot")))
    col.process_text(json.dumps(dbk(174318940804, "change", prev_change_id=174318940803)))
    # MEASURED: aggregated delta >> 1 is NOT a gap when prev_change_id chains
    col.process_text(json.dumps(dbk(174318969050, "change", prev_change_id=174318940804)))
    lines = read_shard_lines(root / (shard_rel_path("deribit", "2026-09-16", col.conn_epoch) + ".open"))
    assert not [ln for ln in lines if ln.get("type") == "gap"]
    # lost update: prev_change_id does not chain to the last delivered id
    col.process_text(json.dumps(dbk(174318969999, "change", prev_change_id=174318940900)))
    lines = read_shard_lines(root / (shard_rel_path("deribit", "2026-09-16", col.conn_epoch) + ".open"))
    (g,) = [ln for ln in lines if ln.get("type") == "gap"]
    assert g["channel"] == "book.BTC-PERPETUAL.100ms"
    assert g["from_seq"] == 174318969050 and g["missing_count"] == -1
    col.process_text(json.dumps(dbk(135083969957, "snapshot")))  # snapshot resets
    col.process_text(json.dumps(dbk(135083969958, "change", prev_change_id=135083969957)))
    lines = read_shard_lines(root / (shard_rel_path("deribit", "2026-09-16", col.conn_epoch) + ".open"))
    assert len([ln for ln in lines if ln.get("type") == "gap"]) == 1


def test_envelope_seq_is_change_id_only_for_deribit(tmp_path):
    col_cb, root, _, _ = make_collector(tmp_path, "coinbase")
    col_cb.process_text(json.dumps({"channel": "ticker", "timestamp": "t", "sequence_num": 9, "events": []}))
    lines = read_shard_lines(root / (shard_rel_path("coinbase", "2026-09-16", col_cb.conn_epoch) + ".open"))
    assert lines[0]["seq"] is None

    col_db, droot, _, _ = make_collector(tmp_path / "db", "deribit")
    col_db.process_text(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "subscription",
                "params": {
                    "channel": "book.ETH-PERPETUAL.100ms",
                    "data": {"timestamp": 1, "type": "snapshot", "change_id": 135084001413, "instrument_name": "ETH-PERPETUAL", "bids": [], "asks": []},
                },
            }
        )
    )
    dlines = read_shard_lines(droot / (shard_rel_path("deribit", "2026-09-16", col_db.conn_epoch) + ".open"))
    assert dlines[0]["seq"] == 135084001413


# ---------------------------------------------------------------------------
# payload-shape validation: wrong shape -> LOUD rejected subrecord
# ---------------------------------------------------------------------------
def test_shape_mismatch_goes_to_rejected_subrecord_not_main_shard(tmp_path, capsys):
    col, root, run, clock = make_collector(tmp_path, "coinbase")
    bad = json.dumps({"channel": "ticker", "timestamp": "t", "events": []})  # missing sequence_num
    col.process_text(bad)
    assert col.stats["shape_errors"] == 1
    shard_path = root / (shard_rel_path("coinbase", "2026-09-16", col.conn_epoch) + ".open")
    assert shard_path.read_text() == ""  # main shard untouched
    rejected = col.shard.rejected_path
    (rec,) = read_shard_lines(rejected)
    assert rec["type"] == "rejected" and "sequence_num" in rec["reason"]
    assert rec["raw_line"] == bad  # raw bytes preserved for audit
    assert "LOUD" in capsys.readouterr().err  # fails LOUD on stderr
    # valid message still accepted afterwards
    col.process_text(json.dumps({"channel": "ticker", "timestamp": "t", "sequence_num": 0, "events": []}))
    lines = read_shard_lines(shard_path)
    assert len(lines) == 1 and lines[0]["payload"]["sequence_num"] == 0


def test_non_json_line_rejected_not_dropped(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "kraken")
    col.process_text("this is not json{{{")
    assert col.stats["shape_errors"] == 1
    (rec,) = read_shard_lines(col.shard.rejected_path)
    assert "json_parse_error" in rec["reason"]
    assert rec["raw_line"] == "this is not json{{{"


def test_measured_wire_shapes_validate(tmp_path):
    # real census sample shapes (FDF-V1 raw bytes, abridged) MUST validate
    cb = {"channel": "ticker", "timestamp": "2026-09-16T09:51:15.231945313Z", "sequence_num": 0,
          "events": [{"type": "snapshot", "tickers": [{"type": "ticker", "product_id": "BTC-USD", "price": "75862", "best_bid": "75862", "best_ask": "75862.01"}]}]}
    kr = {"time": 1789552274602, "product_id": "PF_ETHUSD", "funding_rate": 0.020631772453125,
          "relative_funding_rate": 8.5928125e-06, "bid": 2402.0, "ask": 2402.1,
          "markPrice": 2402.11890772056, "feed": "ticker"}
    krb = {"feed": "book", "product_id": "PF_XBTUSD", "side": "ask", "seq": 296370912, "price": 75862.0, "qty": 0.5, "timestamp": 1789552274602}
    db = {"jsonrpc": "2.0", "method": "subscription",
          "params": {"channel": "ticker.ETH-PERPETUAL.100ms",
                     "data": {"timestamp": 1789552274651, "type": "snapshot", "instrument_name": "ETH-PERPETUAL",
                              "mark_price": 2402.22, "index_price": 2401.92, "current_funding": 0.0}}}
    for spec, payload in ((venues.VENUE_SPECS["coinbase"], cb), (venues.VENUE_SPECS["kraken"], kr),
                          (venues.VENUE_SPECS["kraken"], krb), (venues.VENUE_SPECS["deribit"], db)):
        v = spec.validate(payload)
        assert v.ok, f"{spec.name} measured shape rejected: {v.reason}"


# ---------------------------------------------------------------------------
# hashing + manifests (freeze field 7)
# ---------------------------------------------------------------------------
def test_manifest_row_content_addressed_and_chained(tmp_path):
    root, run, clock = fresh(tmp_path)
    man = ManifestAppender(root / "manifest.jsonl")
    assert man.head_sha256() == hashlib.sha256(b"").hexdigest()
    sw = ShardWriter(root, "coinbase", "2026-09-16", 1, clock=clock)
    sw.open()
    sw.append_message("2026-09-16T12:00:00.000000Z", "ticker", None, {"a": 1})
    p = sw.close("2026-09-16T12:00:01Z")
    row = sw.manifest_row("2026-09-16T12:00:01Z", man.head_sha256())
    man.append_row(row)
    assert row["sha256"] == core.sha256_file(p)
    assert row["bytes"] == p.stat().st_size
    assert row["lines"] == 1
    assert row["prev_manifest_sha256"] == hashlib.sha256(b"").hexdigest()
    # second shard chains the full prior manifest head
    head_after_first = man.head_sha256()
    assert head_after_first == hashlib.sha256((root / "manifest.jsonl").read_bytes()).hexdigest()
    sw2 = ShardWriter(root, "kraken", "2026-09-16", 1, clock=clock)
    sw2.open()
    sw2.append_message("2026-09-16T12:00:02.000000Z", "ticker", None, {"b": 2})
    p2 = sw2.close("2026-09-16T12:00:03Z")
    row2 = sw2.manifest_row("2026-09-16T12:00:03Z", man.head_sha256())
    man.append_row(row2)
    assert row2["prev_manifest_sha256"] == head_after_first
    assert row2["venue"] == "kraken"
    assert man.row_count() == 2


def test_manifest_tamper_detected_fail_loud(tmp_path):
    """Chain semantics: sibling-collector appends are legitimate (the row
    re-chains onto the current head under the flock), but EDITING already-
    written manifest bytes breaks the per-row prev_manifest_sha256 chain
    and the next append must fail loud."""
    root, run, clock = fresh(tmp_path)
    man = ManifestAppender(root / "manifest.jsonl")
    rows_written = []
    for epoch in (1, 2):
        sw = ShardWriter(root, "coinbase", "2026-09-16", epoch, clock=clock)
        sw.open()
        sw.append_message("2026-09-16T12:00:00.000000Z", "ticker", None, {"a": epoch})
        sw.close("x")
        row = sw.manifest_row("x", man.head_sha256())
        man.append_row(row)
        rows_written.append(row)
    mp = root / "manifest.jsonl"
    # tamper with the FIRST row's bytes
    lines = mp.read_text().splitlines()
    lines[0] = lines[0].replace("coinbase", "tampered")
    mp.write_text("\n".join(lines) + "\n")
    sw2 = ShardWriter(root, "coinbase", "2026-09-16", 3, clock=clock)
    sw2.open()
    sw2.append_message("2026-09-16T12:00:05.000000Z", "ticker", None, {"b": 2})
    sw2.close("y")
    with pytest.raises(LoudError, match="chain BROKEN"):
        man.append_row(sw2.manifest_row("y", man.head_sha256()))


def test_manifest_sibling_append_rechains(tmp_path):
    """Two ManifestAppender handles on one file (the 3-venue process case):
    the second append must re-chain onto the first's bytes, not fail."""
    root, run, clock = fresh(tmp_path)
    man_a = ManifestAppender(root / "manifest.jsonl")
    man_b = ManifestAppender(root / "manifest.jsonl")
    sw = ShardWriter(root, "coinbase", "2026-09-16", 1, clock=clock)
    sw.open()
    sw.append_message("2026-09-16T12:00:00.000000Z", "ticker", None, {"a": 1})
    sw.close("x")
    man_a.append_row(sw.manifest_row("x", man_a.head_sha256()))  # venue A row
    sw2 = ShardWriter(root, "kraken", "2026-09-16", 1, clock=clock)
    sw2.open()
    sw2.append_message("2026-09-16T12:00:01.000000Z", "ticker", None, {"b": 2})
    sw2.close("y")
    # venue B built its row BEFORE A appended (stale head) — must re-chain
    stale_row = sw2.manifest_row("y", man_b.head_sha256())
    man_b.append_row(stale_row)
    assert stale_row["prev_manifest_sha256"] == man_a.head_sha256()
    # and the chain over the file verifies
    import hashlib as _h

    data = (root / "manifest.jsonl").read_bytes()
    first, second = data.splitlines(keepends=True)
    assert json.loads(second)["prev_manifest_sha256"] == _h.sha256(first).hexdigest()


def test_closed_shard_never_rewritten(tmp_path):
    root, _, clock = fresh(tmp_path)
    sw = ShardWriter(root, "deribit", "2026-09-16", 3, clock=clock)
    sw.open()
    sw.append_message("2026-09-16T12:00:00.000000Z", "c", None, {})
    sw.close("c1")
    sw2 = ShardWriter(root, "deribit", "2026-09-16", 3, clock=clock)
    sw2.open()
    with pytest.raises(Exception):
        # closing onto the existing closed shard is refused
        sw3 = ShardWriter(root, "deribit", "2026-09-16", 3, clock=clock)
        sw3.open()
        sw3.append_message("z", "c", None, {})
        sw3.close("z")


# ---------------------------------------------------------------------------
# inode-check on append handles (plan §7 hygiene)
# ---------------------------------------------------------------------------
def test_inode_check_catches_replaced_file(tmp_path):
    p = tmp_path / "shard.jsonl"
    h = AppendHandle(p)
    h.write_line(b'{"ok":true}')
    replaced = tmp_path / "other.jsonl"
    replaced.write_text("x")
    os.replace(replaced, p)  # file replaced under the handle
    with pytest.raises(LoudError, match="inode-check FAILED"):
        h.write_line(b'{"ok":false}')


# ---------------------------------------------------------------------------
# heartbeat file + day rollover + orphan finalization
# ---------------------------------------------------------------------------
def test_heartbeat_file_written_with_counts(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "kraken")
    col.process_text(json.dumps({"feed": "ticker", "time": 1, "product_id": "PF_XBTUSD"}))
    col.process_text(json.dumps({"feed": "heartbeat"}))
    col.write_heartbeat_file()
    hb = json.loads((run / "kraken.heartbeat.json").read_text())
    assert hb["venue"] == "kraken"
    assert hb["bytes_written"] > 0 and hb["lines_written"] == 2
    assert hb["per_channel_counts"]["ticker"] == 1 and hb["per_channel_counts"]["heartbeat"] == 1
    assert hb["heartbeat_count"] == 1
    assert hb["updated_utc"].endswith("Z")
    assert hb["endpoint"] == "wss://futures.kraken.com/ws/v1"


def test_day_rollover_closes_shard_same_epoch(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "deribit")
    col.process_text(json.dumps({"jsonrpc": "2.0", "method": "subscription",
                                 "params": {"channel": "volatility_index.btc_volatility",
                                            "data": {"timestamp": 1, "VolatilityIndex": 40}}}))
    clock.advance(3600 * 13)
    col._watchdog_due(None)  # triggers rollover check (heartbeat file + day split)
    assert col.shard is not None
    assert col.shard.day_utc == "2026-09-17"
    assert col.shard.conn_epoch == col.conn_epoch
    # day-1 shard closed into the manifest
    assert manifest_has_path(root / "manifest.jsonl", shard_rel_path("deribit", "2026-09-16", col.conn_epoch))
    assert not manifest_has_path(root / "manifest.jsonl", shard_rel_path("deribit", "2026-09-17", col.conn_epoch))


def test_orphan_shard_finalized_on_restart(tmp_path):
    root, run, clock = fresh(tmp_path, "kraken")
    orphan_rel = shard_rel_path("kraken", "2026-09-15", 2)
    orphan = root / (orphan_rel + ".open")
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text('{"recv_utc":"2026-09-15T00:00:00.000000Z","channel":"ticker","seq":null,"payload":{"feed":"ticker"}}\n')
    man = ManifestAppender(root / "manifest.jsonl")
    finalized = finalize_orphan_shards(root, "kraken", man, "2026-09-16T00:00:00.000000Z")
    assert len(finalized) == 1
    assert not orphan.exists()
    assert (root / orphan_rel).exists()
    row = finalized[0]
    assert row["finalized_on_restart"] is True
    assert row["sha256"] == core.sha256_file(root / orphan_rel)
    assert row["path"] == orphan_rel
    assert not finalize_orphan_shards(root, "kraken", man, "z")  # idempotent


# ---------------------------------------------------------------------------
# subscription wire messages match the frozen contract
# ---------------------------------------------------------------------------
def test_kraken_subscribed_ack_with_feed_key_is_control_envelope(tmp_path):
    """LIVE-WIRE regression (2026-09-16): subscription acks carry BOTH
    'event' and 'feed' keys; they must pass validation AND never reach the
    sequence tracker (KeyError 'seq' crash class)."""
    col, root, run, clock = make_collector(tmp_path, "kraken")
    ack = {"event": "subscribed", "feed": "book", "product_ids": ["PF_XBTUSD"]}
    col.process_text(json.dumps(ack))  # must not raise
    lines = read_shard_lines(root / (shard_rel_path("kraken", "2026-09-16", col.conn_epoch) + ".open"))
    assert len(lines) == 1 and lines[0]["channel"] == "event_subscribed"
    assert col.stats["shape_errors"] == 0


def test_subscribe_messages_match_frozen_identity():
    cb = venues.VENUE_SPECS["coinbase"].subscribe_messages()
    assert {"type": "subscribe", "product_ids": ["BTC-USD", "ETH-USD"], "channel": "heartbeats"} in cb
    assert any(m["channel"] == "l2_data" for m in cb)
    kr = venues.VENUE_SPECS["kraken"].subscribe_messages()
    assert {"event": "subscribe", "feed": "heartbeat"} in kr
    assert {"event": "subscribe", "feed": "book", "product_ids": ["PF_XBTUSD", "PF_ETHUSD"]} in kr
    db = venues.VENUE_SPECS["deribit"].subscribe_messages()
    channels = db[0]["params"]["channels"]
    assert "book.BTC-PERPETUAL.100ms" in channels and "ticker.ETH-PERPETUAL.100ms" in channels
    assert db[1]["method"] == "public/set_heartbeat" and db[1]["params"]["interval"] == 30
    # watchdog thresholds per contract field 6
    assert venues.VENUE_SPECS["coinbase"].heartbeat_timeout_s == 15.0
    assert venues.VENUE_SPECS["kraken"].heartbeat_timeout_s == 60.0
    assert venues.VENUE_SPECS["deribit"].heartbeat_timeout_s == 45.0


# ---------------------------------------------------------------------------
# pidfile
# ---------------------------------------------------------------------------
def test_pidfile_written_and_removed(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "coinbase")
    path = write_pidfile(run, "coinbase", {
        "endpoint": "wss://advanced-trade-ws.coinbase.com",
        "instruments": ["BTC-USD", "ETH-USD"],
        "data_root": root,
        "code_sha256": "deadbeef",
    })
    payload = json.loads(path.read_text())
    assert payload["venue"] == "coinbase" and isinstance(payload["pid"], int)
    assert payload["started_utc"].endswith("Z")
    from research.control.crypto_ng4_run.collectors.collector import remove_pidfile

    remove_pidfile(run, "coinbase", payload["pid"])
    assert not path.exists()
    # a foreign pid does not clobber the pidfile
    write_pidfile(run, "coinbase", {"endpoint": "e", "instruments": [], "data_root": root})
    remove_pidfile(run, "coinbase", payload["pid"] + 1)
    assert path.exists()
