"""DATA-EDGE-UNLOCK-V1 collector unit goldens — SYNTHETIC ONLY, NO NETWORK.

Lane C goldens for the frozen cycle contract
(research/control/data_edge_unlock_v1/lane_c/c_collection_contract.json,
schema deu_c_collection_contract@1) adopting the CNG4 A3 conventions, with
hand-computed fixtures:

- envelope {recv_utc, channel, seq, payload} shape + microsecond recv_utc
- shard atomic rename + content-addressed path convention; closed shard
  NEVER rewritten
- gap detection fires on a sequence jump (gap record written INTO the raw
  shard; the gap is DATA)
- duplicate / regression counting (verbatim capture, never deduplicated at
  capture)
- manifest append with prev_manifest_sha256 head chaining + tamper
  detection + standalone chain/shard verifier
- inode-change detection on append handles (Q-13)
- heartbeat watchdog threshold math (CB 15s probe->reconnect, KR 60s
  reconnect, DB 45s reconnect; total-silence reconnect)
- payload-shape failure is LOUD (rejected subrecord, stderr, main shard
  untouched)
- degraded-channel detection (Coinbase l2_data re-attempt policy)
- Deribit trades census summary math + trades trade_seq gap rule
- PID/liveness default location: data-root runtime dir, NEVER research/

Run: .venv/bin/python -m pytest tests/test_deu_collectors.py -q
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parent
sys.path.insert(0, str(WORKTREE))

from research.assets.data_edge_unlock_v1.collectors import core, venues  # noqa: E402
from research.assets.data_edge_unlock_v1.collectors.collector import (  # noqa: E402
    Collector,
    summarize_census_lines,
    write_pidfile,
    remove_pidfile,
)
from research.assets.data_edge_unlock_v1.collectors.core import (  # noqa: E402
    AppendHandle,
    LoudError,
    ManifestAppender,
    ShardWriter,
    finalize_orphan_shards,
    manifest_has_path,
    shard_rel_path,
    verify_manifest_chain,
)


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.t = start

    def __call__(self) -> datetime:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t = self.t + timedelta(seconds=seconds)


class FakeMono:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


DAY = "2026-09-17"


def fresh(tmp_path: Path, venue: str = "coinbase"):
    root = tmp_path / "raw"
    run = tmp_path / "runtime"
    root.mkdir(parents=True)
    run.mkdir(parents=True)
    clock = FakeClock(datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc))
    return root, run, clock


def make_collector(tmp_path: Path, venue: str = "coinbase", **kw):
    root = tmp_path / "raw"
    run = tmp_path / "runtime"
    root.mkdir(parents=True, exist_ok=True)
    run.mkdir(parents=True, exist_ok=True)
    clock = FakeClock(datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc))
    col = Collector(venue, data_root=root, run_dir=run, clock=clock, **kw)
    import time as _time

    col.monotonic = _time.monotonic  # real monotonic; watchdog tests inject a fake
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
    sw = ShardWriter(root, "coinbase", DAY, 1, clock=clock)
    sw.open()
    sw.append_message("2026-09-17T12:00:00.123456Z", "ticker", None, {"channel": "ticker"})
    p = sw.close("2026-09-17T12:00:01Z")
    assert p == root / "coinbase" / "2026" / "09" / "17" / "00000001.jsonl"
    (row,) = read_shard_lines(p)
    assert set(row.keys()) == {"recv_utc", "channel", "seq", "payload"}
    assert row["seq"] is None
    assert row["recv_utc"] == "2026-09-17T12:00:00.123456Z"
    assert row["recv_utc"].endswith("Z") and len(row["recv_utc"].split(".")[1]) == 7  # 6 frac digits + Z
    assert row["payload"] == {"channel": "ticker"}


def test_shard_atomic_rename_and_closed_never_rewritten(tmp_path):
    root, _, clock = fresh(tmp_path)
    sw = ShardWriter(root, "deribit", DAY, 3, clock=clock)
    sw.open()
    open_path = root / "deribit" / "2026" / "09" / "17" / "00000003.jsonl.open"
    assert open_path.exists()
    sw.append_message("2026-09-17T12:00:00.000000Z", "c", None, {"k": 1})
    final = sw.close("2026-09-17T12:00:01Z")
    assert final.exists() and not open_path.exists()  # atomic rename, .open gone
    # a second writer closing onto the SAME (venue, day, epoch) is refused
    sw2 = ShardWriter(root, "deribit", DAY, 3, clock=clock)
    sw2.open()
    sw2.append_message("z", "c", None, {})
    with pytest.raises(LoudError, match="refusing rewrite"):
        sw2.close("z")


def test_shard_path_convention_venue_day_epoch(tmp_path):
    root, _, _ = fresh(tmp_path)
    assert shard_rel_path("kraken", "2026-11-02", 7) == "kraken/2026/11/02/00000007.jsonl"


# ---------------------------------------------------------------------------
# gap marking: sequence jump -> gap record written INTO the shard (field 5)
# ---------------------------------------------------------------------------
def test_coinbase_gap_marked_as_data_record(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "coinbase")
    msgs = [
        {"channel": "ticker", "timestamp": "t", "sequence_num": n, "events": []}
        for n in (0, 1, 2)
    ] + [{"channel": "ticker", "timestamp": "t", "sequence_num": 5, "events": []}]
    for m in msgs:
        col.process_text(json.dumps(m))
    rel = shard_rel_path("coinbase", DAY, col.conn_epoch)
    lines = read_shard_lines(root / (rel + ".open"))
    gaps = [ln for ln in lines if ln.get("type") == "gap"]
    assert len(gaps) == 1, "sequence jump 2->5 must produce exactly one gap record"
    g = gaps[0]
    assert g["venue"] == "coinbase" and g["channel"] == "ticker"
    assert g["from_seq"] == 2 and g["to_seq"] == 5 and g["missing_count"] == 2  # 3,4 missing
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
    lines = read_shard_lines(root / (shard_rel_path("coinbase", DAY, col.conn_epoch) + ".open"))
    assert not [ln for ln in lines if ln.get("type") == "gap"]
    assert col.shard.gap_count == 0
    assert col.shard.dup_count == 2  # both repeated (channel, seq) keys counted
    assert col.tracker.reg_count == 2
    assert len(lines) == 5  # verbatim capture: ALL five lines preserved


def test_kraken_book_snapshot_resets_continuity_and_gap_detected(tmp_path):
    """MEASURED CORRECTION (live wire 2026-09-17, 46k msgs): Kraken book seq
    is ONE counter per product_id SHARED across buy/sell sides — interleaved
    sides are consecutive integers, so per-(product, side) keying is wrong.
    Gap iff per-product delta > 1; snapshot resets continuity."""
    col, root, run, clock = make_collector(tmp_path, "kraken")

    def book(seq, side="buy"):
        return {"feed": "book", "product_id": "PF_XBTUSD", "side": side, "seq": seq, "price": 100.0, "qty": 1.0, "timestamp": 1}

    # interleaved sides, consecutive per-product ints: NO gap may fire
    col.process_text(json.dumps(book(10, "sell")))
    col.process_text(json.dumps(book(11, "buy")))
    col.process_text(json.dumps(book(12, "sell")))
    col.process_text(json.dumps({"feed": "book_snapshot", "product_id": "PF_XBTUSD", "ticks": [], "timestamp": 2}))
    col.process_text(json.dumps(book(12, "buy")))  # fresh snapshot clears continuity
    lines = read_shard_lines(root / (shard_rel_path("kraken", DAY, col.conn_epoch) + ".open"))
    assert not [ln for ln in lines if ln.get("type") == "gap"]
    col.process_text(json.dumps(book(16, "sell")))  # 12 -> 16 = gap of 3
    lines = read_shard_lines(root / (shard_rel_path("kraken", DAY, col.conn_epoch) + ".open"))
    gaps = [ln for ln in lines if ln.get("type") == "gap"]
    assert len(gaps) == 1 and gaps[0]["missing_count"] == 3
    assert gaps[0]["channel"] == "book" and "PF_XBTUSD" in gaps[0]["instrument"]
    # the OTHER product has its own sequence space (no cross-product gap)
    col.process_text(json.dumps({"feed": "book", "product_id": "PF_ETHUSD", "side": "buy", "seq": 5, "price": 1.0, "qty": 1.0, "timestamp": 3}))
    lines = read_shard_lines(root / (shard_rel_path("kraken", DAY, col.conn_epoch) + ".open"))
    assert len([ln for ln in lines if ln.get("type") == "gap"]) == 1


def test_deribit_heartbeat_and_test_request_are_answered_with_public_test(tmp_path):
    """MEASURED start defect (2026-09-17): Deribit drops the connection at
    ~60s when the client never answers the server's heartbeat with a
    public/test request; no test_request is delivered before the drop.
    Both heartbeat and test_request must queue the public/test reply."""
    col, root, run, clock = make_collector(tmp_path, "deribit")
    col.process_text(json.dumps({"jsonrpc": "2.0", "method": "heartbeat"}))
    assert col._pending_sends == [{"jsonrpc": "2.0", "id": 902, "method": "public/test", "params": {}}]
    col.process_text(json.dumps({"jsonrpc": "2.0", "method": "test_request"}))
    assert len(col._pending_sends) == 2
    assert all(m["method"] == "public/test" for m in col._pending_sends)
    # a subscription message queues NO reply
    col.process_text(json.dumps({
        "jsonrpc": "2.0", "method": "subscription",
        "params": {"channel": "ticker.ETH-PERPETUAL.100ms",
                   "data": {"timestamp": 1789552274651, "type": "snapshot", "instrument_name": "ETH-PERPETUAL",
                            "mark_price": 2402.22, "index_price": 2401.92, "current_funding": 0.0}}}))
    assert len(col._pending_sends) == 2
    # the messages themselves are still captured verbatim
    lines = read_shard_lines(root / (shard_rel_path("deribit", DAY, col.conn_epoch) + ".open"))
    assert [ln["channel"] for ln in lines] == ["rpc_heartbeat", "rpc_test_request", "ticker.ETH-PERPETUAL.100ms"]


def test_deribit_prev_change_id_gap_and_snapshot_reset(tmp_path):
    """MEASURED semantics (CNG4 live wire): the 100ms book channel aggregates
    events, so inter-delivery change_id deltas are large by design;
    losslessness is carried by prev_change_id.  Gap iff prev_change_id !=
    last delivered change_id; snapshot resets continuity."""
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
    # aggregated delta >> 1 is NOT a gap when prev_change_id chains
    col.process_text(json.dumps(dbk(174318969050, "change", prev_change_id=174318940804)))
    lines = read_shard_lines(root / (shard_rel_path("deribit", DAY, col.conn_epoch) + ".open"))
    assert not [ln for ln in lines if ln.get("type") == "gap"]
    # lost update: prev_change_id does not chain to the last delivered id
    col.process_text(json.dumps(dbk(174318969999, "change", prev_change_id=174318940900)))
    lines = read_shard_lines(root / (shard_rel_path("deribit", DAY, col.conn_epoch) + ".open"))
    (g,) = [ln for ln in lines if ln.get("type") == "gap"]
    assert g["channel"] == "book.BTC-PERPETUAL.100ms"
    assert g["from_seq"] == 174318969050 and g["missing_count"] == -1
    col.process_text(json.dumps(dbk(135083969957, "snapshot")))  # snapshot resets
    col.process_text(json.dumps(dbk(135083969958, "change", prev_change_id=135083969957)))
    lines = read_shard_lines(root / (shard_rel_path("deribit", DAY, col.conn_epoch) + ".open"))
    assert len([ln for ln in lines if ln.get("type") == "gap"]) == 1


def test_deribit_trades_raw_trade_seq_gap_and_envelope_seq(tmp_path):
    """CYCLE EXTENSION (census-gated): trades.{inst}.raw carries a strict
    per-instrument trade_seq; gap iff seq > prev + 1; envelope seq = the
    delivered trade_seq."""
    col, root, run, clock = make_collector(tmp_path, "deribit", include_deribit_trades=True)

    def trade(tseq, instr="BTC-PERPETUAL", ts=1789552274651):
        return {
            "jsonrpc": "2.0",
            "method": "subscription",
            "params": {
                "channel": f"trades.{instr}.raw",
                "data": [
                    {
                        "trade_seq": tseq,
                        "trade_id": f"BTC-{tseq}",
                        "timestamp": ts,
                        "tick_direction": 0,
                        "price": 75000.5,
                        "mark_price": 75000.4,
                        "instrument_name": instr,
                        "index_price": 74999.9,
                        "amount": 0.25,
                        "direction": "buy",
                    }
                ],
            },
        }

    col.process_text(json.dumps(trade(100)))
    col.process_text(json.dumps(trade(101)))
    col.process_text(json.dumps(trade(103)))  # 101 -> 103: trade 102 lost
    lines = read_shard_lines(root / (shard_rel_path("deribit", DAY, col.conn_epoch) + ".open"))
    gaps = [ln for ln in lines if ln.get("type") == "gap"]
    assert len(gaps) == 1
    g = gaps[0]
    assert g["channel"] == "trades.BTC-PERPETUAL.raw"
    assert g["from_seq"] == 101 and g["to_seq"] == 103 and g["missing_count"] == 1
    # envelope seq carries the delivered trade_seq
    data_lines = [ln for ln in lines if ln.get("type") != "gap"]
    assert data_lines[-1]["seq"] == 103
    # the ETH raw channel has its OWN sequence space (no cross-instrument gap)
    col.process_text(json.dumps(trade(7, instr="ETH-PERPETUAL")))
    lines = read_shard_lines(root / (shard_rel_path("deribit", DAY, col.conn_epoch) + ".open"))
    assert len([ln for ln in lines if ln.get("type") == "gap"]) == 1


def test_envelope_seq_is_change_id_only_for_deribit(tmp_path):
    col_cb, root, _, _ = make_collector(tmp_path, "coinbase")
    col_cb.process_text(json.dumps({"channel": "ticker", "timestamp": "t", "sequence_num": 9, "events": []}))
    lines = read_shard_lines(root / (shard_rel_path("coinbase", DAY, col_cb.conn_epoch) + ".open"))
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
    dlines = read_shard_lines(droot / (shard_rel_path("deribit", DAY, col_db.conn_epoch) + ".open"))
    assert dlines[0]["seq"] == 135084001413


# ---------------------------------------------------------------------------
# payload-shape validation: wrong shape -> LOUD rejected subrecord (Q-13)
# ---------------------------------------------------------------------------
def test_shape_mismatch_goes_to_rejected_subrecord_not_main_shard(tmp_path, capsys):
    col, root, run, clock = make_collector(tmp_path, "coinbase")
    bad = json.dumps({"channel": "ticker", "timestamp": "t", "events": []})  # missing sequence_num
    col.process_text(bad)
    assert col.stats["shape_errors"] == 1
    shard_path = root / (shard_rel_path("coinbase", DAY, col.conn_epoch) + ".open")
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
    cb = {"channel": "ticker", "timestamp": "2026-09-17T09:51:15.231945313Z", "sequence_num": 0,
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
# degraded-channel detection (freeze field 17: Coinbase l2_data re-attempt)
# ---------------------------------------------------------------------------
def test_coinbase_error_envelope_records_degraded_channel_and_captures(tmp_path, capsys):
    col, root, run, clock = make_collector(tmp_path, "coinbase")
    err = json.dumps({"type": "error", "message": "l2_data requires authentication", "reason": "auth required"})
    col.process_text(err)
    assert col.stats["degraded_channels"]["l2_data"] == "l2_data requires authentication"
    assert "LOUD CHANNEL DEGRADED" in capsys.readouterr().err
    # the error envelope itself is still captured verbatim (nothing dropped)
    lines = read_shard_lines(root / (shard_rel_path("coinbase", DAY, col.conn_epoch) + ".open"))
    assert len(lines) == 1 and lines[0]["payload"]["type"] == "error"


def test_deribit_rpc_error_and_kraken_rejection_recorded(tmp_path):
    col_db, _, _, _ = make_collector(tmp_path / "db", "deribit")
    col_db.process_text(json.dumps({"jsonrpc": "2.0", "id": 101, "error": {"code": -32602, "message": "Invalid params: unknown channel"}}))
    assert "Invalid params: unknown channel" in col_db.stats["degraded_channels"]["rpc"]

    col_kr, _, _, _ = make_collector(tmp_path / "kr", "kraken")
    col_kr.process_text(json.dumps({"event": "subscriptionStatus", "status": "error", "feed": "trade", "message": "Unknown feed"}))
    assert "Unknown feed" in col_kr.stats["degraded_channels"]["trade"]

    # non-error control envelopes do NOT degrade anything
    col_kr.process_text(json.dumps({"event": "subscribed", "feed": "book", "product_ids": ["PF_XBTUSD"]}))
    assert list(col_kr.stats["degraded_channels"].keys()) == ["trade"]


# ---------------------------------------------------------------------------
# hashing + manifests (freeze field 7)
# ---------------------------------------------------------------------------
def test_manifest_row_schema_fields_and_content_addressed_chain(tmp_path):
    root, run, clock = fresh(tmp_path)
    man = ManifestAppender(root / "manifest.jsonl")
    assert man.head_sha256() == hashlib.sha256(b"").hexdigest()
    sw = ShardWriter(root, "coinbase", DAY, 1, clock=clock)
    sw.open()
    sw.append_message("2026-09-17T12:00:00.000000Z", "ticker", None, {"a": 1})
    p = sw.close("2026-09-17T12:00:01Z")
    row = sw.manifest_row("2026-09-17T12:00:01Z", man.head_sha256())
    # the frozen manifest_row field list (contract freeze field 7)
    required = {"venue", "conn_epoch", "path", "sha256", "bytes", "lines", "per_channel_counts",
                "gap_count", "dup_count", "heartbeat_count", "first_recv_utc", "last_recv_utc",
                "closed_utc", "prev_manifest_sha256"}
    assert required <= set(row.keys())
    assert row["schema"] == "deu_shard_manifest_row@1"
    man.append_row(row)
    assert row["sha256"] == core.sha256_file(p)
    assert row["bytes"] == p.stat().st_size
    assert row["lines"] == 1
    assert row["conn_epoch"] == 1
    assert row["prev_manifest_sha256"] == hashlib.sha256(b"").hexdigest()
    # second shard chains the full prior manifest head
    head_after_first = man.head_sha256()
    assert head_after_first == hashlib.sha256((root / "manifest.jsonl").read_bytes()).hexdigest()
    sw2 = ShardWriter(root, "kraken", DAY, 1, clock=clock)
    sw2.open()
    sw2.append_message("2026-09-17T12:00:02.000000Z", "ticker", None, {"b": 2})
    sw2.close("2026-09-17T12:00:03Z")
    row2 = sw2.manifest_row("2026-09-17T12:00:03Z", man.head_sha256())
    man.append_row(row2)
    assert row2["prev_manifest_sha256"] == head_after_first
    assert man.row_count() == 2
    # standalone verifier passes over the intact chain + shard bytes
    verdict = verify_manifest_chain(root / "manifest.jsonl")
    assert verdict["verdict"] == "PASS" and verdict["rows"] == 2 and verdict["shard_rows_verified"] == 2


def test_manifest_tamper_detected_fail_loud(tmp_path):
    """Chain semantics: sibling-collector appends are legitimate (the row
    re-chains onto the current head under the flock), but EDITING already-
    written manifest bytes breaks the per-row prev_manifest_sha256 chain
    and the next append must fail loud."""
    root, run, clock = fresh(tmp_path)
    man = ManifestAppender(root / "manifest.jsonl")
    for epoch in (1, 2):
        sw = ShardWriter(root, "coinbase", DAY, epoch, clock=clock)
        sw.open()
        sw.append_message("2026-09-17T12:00:00.000000Z", "ticker", None, {"a": epoch})
        sw.close("x")
        man.append_row(sw.manifest_row("x", man.head_sha256()))
    mp = root / "manifest.jsonl"
    lines = mp.read_text().splitlines()
    lines[0] = lines[0].replace("coinbase", "tampered")
    mp.write_text("\n".join(lines) + "\n")
    sw2 = ShardWriter(root, "coinbase", DAY, 3, clock=clock)
    sw2.open()
    sw2.append_message("2026-09-17T12:00:05.000000Z", "ticker", None, {"b": 2})
    sw2.close("y")
    with pytest.raises(LoudError, match="chain BROKEN"):
        man.append_row(sw2.manifest_row("y", man.head_sha256()))
    with pytest.raises(LoudError, match="chain BROKEN"):
        verify_manifest_chain(mp)


def test_verify_manifest_chain_catches_shard_byte_tamper(tmp_path):
    root, _, clock = fresh(tmp_path)
    man = ManifestAppender(root / "manifest.jsonl")
    sw = ShardWriter(root, "kraken", DAY, 1, clock=clock)
    sw.open()
    sw.append_message("2026-09-17T12:00:00.000000Z", "ticker", None, {"a": 1})
    p = sw.close("x")
    man.append_row(sw.manifest_row("x", man.head_sha256()))
    # tamper with the CLOSED shard's bytes (a closed shard is never rewritten
    # in a live run; the verifier must catch it if it ever happens)
    with p.open("ab") as fh:
        fh.write(b'{"tampered":true}\n')
    with pytest.raises(LoudError, match="sha256 MISMATCH"):
        verify_manifest_chain(root / "manifest.jsonl")


def test_manifest_sibling_append_rechains(tmp_path):
    """Two ManifestAppender handles on one file (the 3-venue process case):
    the second append must re-chain onto the first's bytes, not fail."""
    root, run, clock = fresh(tmp_path)
    man_a = ManifestAppender(root / "manifest.jsonl")
    man_b = ManifestAppender(root / "manifest.jsonl")
    sw = ShardWriter(root, "coinbase", DAY, 1, clock=clock)
    sw.open()
    sw.append_message("2026-09-17T12:00:00.000000Z", "ticker", None, {"a": 1})
    sw.close("x")
    man_a.append_row(sw.manifest_row("x", man_a.head_sha256()))  # venue A row
    sw2 = ShardWriter(root, "kraken", DAY, 1, clock=clock)
    sw2.open()
    sw2.append_message("2026-09-17T12:00:01.000000Z", "ticker", None, {"b": 2})
    sw2.close("y")
    # venue B built its row BEFORE A appended (stale head) — must re-chain
    stale_row = sw2.manifest_row("y", man_b.head_sha256())
    man_b.append_row(stale_row)
    assert stale_row["prev_manifest_sha256"] == man_a.head_sha256()
    # and the chain over the file verifies
    data = (root / "manifest.jsonl").read_bytes()
    first, second = data.splitlines(keepends=True)
    assert json.loads(second)["prev_manifest_sha256"] == hashlib.sha256(first).hexdigest()


# ---------------------------------------------------------------------------
# inode-check on append handles (LESSONS Q-13)
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
# heartbeat watchdog threshold math (contract field 6) + heartbeat file
# ---------------------------------------------------------------------------
def test_watchdog_threshold_math_kraken_reconnects_without_probe(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "kraken")
    mono = FakeMono(1000.0)
    col.monotonic = mono
    col._last_hb_file_mono = mono()
    col._hb_last_venue_mono = mono()
    col._last_message_mono = mono()
    col._probe_sent_mono = None
    # KR heartbeat_timeout = 60s: NOT due at exactly +60, due past it
    assert venues.VENUE_SPECS["kraken"].heartbeat_timeout_s == 60.0
    mono.advance(60.0)
    assert col._watchdog_due(None) is False
    mono.advance(1.5)  # +61.5 total
    assert col._watchdog_due(None) is True  # reconnect (KR has NO probe step)
    assert col._probe_sent_mono is None


def test_watchdog_threshold_math_coinbase_probe_then_reconnect(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "coinbase")
    mono = FakeMono(2000.0)
    col.monotonic = mono
    col._last_hb_file_mono = mono()
    col._hb_last_venue_mono = mono()
    col._last_message_mono = mono()
    col._probe_sent_mono = None
    assert venues.VENUE_SPECS["coinbase"].heartbeat_timeout_s == 15.0
    mono.advance(14.0)
    assert col._watchdog_due(None) is False
    mono.advance(2.0)  # +16 > 15s -> probe first, NOT an immediate reconnect
    assert col._watchdog_due(None) is False
    assert col._probe_sent_mono == 2016.0
    assert col.stats["reconnect_probe_sent"] == 1
    col._last_message_mono = mono()  # keep total-silence branch quiet
    mono.advance(9.0)  # probe unanswered for 9s < grace 10s
    assert col._watchdog_due(None) is False
    mono.advance(2.0)  # probe unanswered > PROBE_GRACE_S -> reconnect
    assert col._watchdog_due(None) is True


def test_watchdog_total_silence_reconnects_all_venues(tmp_path):
    thresholds = {"coinbase": 30.0, "kraken": 90.0, "deribit": 60.0}
    for venue, silence in thresholds.items():
        col, _, _, _ = make_collector(tmp_path / venue, venue)
        mono = FakeMono(500.0)
        col.monotonic = mono
        col._last_hb_file_mono = mono()
        col._hb_last_venue_mono = mono()
        col._last_message_mono = mono()
        col._probe_sent_mono = None
        assert venues.VENUE_SPECS[venue].silence_timeout_s == silence
        mono.advance(silence)
        # keep the venue-heartbeat branch fresh so ONLY the silence branch
        # can fire (heartbeat timeout < silence timeout on every venue)
        col._hb_last_venue_mono = mono()
        assert col._watchdog_due(None) is False  # not past, AT the threshold
        mono.advance(0.5)
        assert col._watchdog_due(None) is True  # total silence -> reconnect


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
    assert "degraded_channels" in hb  # Q-13: heartbeat carries shape + state


# ---------------------------------------------------------------------------
# day rollover + orphan finalization
# ---------------------------------------------------------------------------
def test_day_rollover_closes_shard_same_epoch(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "deribit")
    col.process_text(json.dumps({"jsonrpc": "2.0", "method": "subscription",
                                 "params": {"channel": "volatility_index.btc_volatility",
                                            "data": {"timestamp": 1, "VolatilityIndex": 40}}}))
    clock.advance(3600 * 13)
    col._last_hb_file_mono = col.monotonic()  # keep heartbeat-file write out of this check
    col._watchdog_due(None)  # triggers rollover check (heartbeat file + day split)
    assert col.shard is not None
    assert col.shard.day_utc == "2026-09-18"
    assert col.shard.conn_epoch == col.conn_epoch
    # day-1 shard closed into the manifest
    assert manifest_has_path(root / "manifest.jsonl", shard_rel_path("deribit", "2026-09-17", col.conn_epoch))
    assert not manifest_has_path(root / "manifest.jsonl", shard_rel_path("deribit", "2026-09-18", col.conn_epoch))


def test_orphan_shard_finalized_on_restart(tmp_path):
    root, run, clock = fresh(tmp_path, "kraken")
    orphan_rel = shard_rel_path("kraken", "2026-09-16", 2)
    orphan = root / (orphan_rel + ".open")
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text('{"recv_utc":"2026-09-16T00:00:00.000000Z","channel":"ticker","seq":null,"payload":{"feed":"ticker"}}\n')
    man = ManifestAppender(root / "manifest.jsonl")
    finalized = finalize_orphan_shards(root, "kraken", man, "2026-09-17T00:00:00.000000Z")
    assert len(finalized) == 1
    assert not orphan.exists()
    assert (root / orphan_rel).exists()
    row = finalized[0]
    assert row["finalized_on_restart"] is True
    assert row["sha256"] == core.sha256_file(root / orphan_rel)
    assert row["path"] == orphan_rel
    assert not finalize_orphan_shards(root, "kraken", man, "z")  # idempotent


# ---------------------------------------------------------------------------
# subscription wire messages match the frozen contract identity
# ---------------------------------------------------------------------------
def test_subscribe_messages_match_frozen_identity():
    cb = venues.VENUE_SPECS["coinbase"].subscribe_messages()
    assert {"type": "subscribe", "product_ids": ["BTC-USD", "ETH-USD"], "channel": "heartbeats"} in cb
    assert any(m["channel"] == "l2_data" for m in cb)  # freeze field 17: re-attempted
    assert any(m["channel"] == "market_trades" for m in cb)
    kr = venues.VENUE_SPECS["kraken"].subscribe_messages()
    assert {"event": "subscribe", "feed": "heartbeat"} in kr
    assert {"event": "subscribe", "feed": "book", "product_ids": ["PF_XBTUSD", "PF_ETHUSD"]} in kr
    db = venues.VENUE_SPECS["deribit"].subscribe_messages()
    channels = db[0]["params"]["channels"]
    assert "book.BTC-PERPETUAL.100ms" in channels and "ticker.ETH-PERPETUAL.100ms" in channels
    assert db[1]["method"] == "public/set_heartbeat" and db[1]["params"]["interval"] == 30
    # base deribit subscription EXCLUDES trades (census-gated)
    assert not any(c.startswith("trades.") for c in channels)
    db_trades = venues.deribit_subscribe_messages(include_trades=True)
    tchannels = db_trades[0]["params"]["channels"]
    assert "trades.BTC-PERPETUAL.raw" in tchannels and "trades.ETH-PERPETUAL.raw" in tchannels
    # the ONE permitted census subscription set
    assert venues.deribit_trades_census_channels() == [
        "trades.BTC-PERPETUAL.raw", "trades.BTC-PERPETUAL.100ms",
        "trades.ETH-PERPETUAL.raw", "trades.ETH-PERPETUAL.100ms",
    ]
    # watchdog thresholds per contract field 6
    assert venues.VENUE_SPECS["coinbase"].heartbeat_timeout_s == 15.0
    assert venues.VENUE_SPECS["kraken"].heartbeat_timeout_s == 60.0
    assert venues.VENUE_SPECS["deribit"].heartbeat_timeout_s == 45.0


def test_deribit_trades_validator_shapes(tmp_path):
    ok = {"jsonrpc": "2.0", "method": "subscription",
          "params": {"channel": "trades.ETH-PERPETUAL.raw",
                     "data": [{"trade_seq": 5, "timestamp": 1, "instrument_name": "ETH-PERPETUAL",
                               "price": 2400.5, "amount": 1.0}]}}
    assert venues.deribit_validate(ok).ok
    bad_container = {"jsonrpc": "2.0", "method": "subscription",
                     "params": {"channel": "trades.ETH-PERPETUAL.raw", "data": {"trade_seq": 5}}}
    assert not venues.deribit_validate(bad_container).ok  # data must be a LIST
    bad_item = {"jsonrpc": "2.0", "method": "subscription",
                "params": {"channel": "trades.ETH-PERPETUAL.raw",
                           "data": [{"timestamp": 1, "instrument_name": "ETH-PERPETUAL",
                                     "price": 2400.5, "amount": 1.0}]}}  # missing trade_seq
    verdict = venues.deribit_validate(bad_item)
    assert not verdict.ok and "trade_seq" in verdict.reason


# ---------------------------------------------------------------------------
# census summary math (freeze field 18)
# ---------------------------------------------------------------------------
def test_census_summary_measures_shape_and_trade_seq_continuity():
    def raw(instr, tseq):
        return json.dumps({"jsonrpc": "2.0", "method": "subscription",
                           "params": {"channel": f"trades.{instr}.raw",
                                      "data": [{"trade_seq": tseq, "timestamp": 1,
                                                "instrument_name": instr, "price": 1.0,
                                                "amount": 1.0}]}})

    lines = [
        json.dumps({"jsonrpc": "2.0", "id": 909, "result": ["trades.BTC-PERPETUAL.raw"]}),
        raw("BTC-PERPETUAL", 10),
        raw("BTC-PERPETUAL", 11),
        raw("BTC-PERPETUAL", 14),  # jump: 12,13 lost
        raw("ETH-PERPETUAL", 500),
        json.dumps({"jsonrpc": "2.0", "method": "subscription",
                    "params": {"channel": "trades.BTC-PERPETUAL.100ms",
                               "data": [{"trade_seq": 15, "timestamp": 2, "instrument_name": "BTC-PERPETUAL", "price": 1.0, "amount": 1.0}]}}),
        "not json {{{",
    ]
    s = summarize_census_lines(lines)
    assert s["messages_total"] == 7 and s["parse_errors"] == 1
    assert s["per_channel_counts"] == {"trades.BTC-PERPETUAL.raw": 3, "trades.ETH-PERPETUAL.raw": 1, "trades.BTC-PERPETUAL.100ms": 1}
    assert s["data_container_types"]["trades.BTC-PERPETUAL.raw"] == "list"
    assert "trade_seq" in s["item_key_union"]["trades.BTC-PERPETUAL.raw"]
    btc = s["raw_trade_seq_continuity"]["BTC-PERPETUAL"]
    assert btc["count"] == 3 and btc["first"] == 10 and btc["last"] == 14
    assert btc["strictly_increasing"] is False  # hand-computed: 10,11,14
    assert btc["deltas_gt1"] == 1 and btc["deltas_le0"] == 0
    eth = s["raw_trade_seq_continuity"]["ETH-PERPETUAL"]
    assert eth["strictly_increasing"] is True and eth["count"] == 1
    # the 100ms channel is NOT tracked for continuity (aggregation unmeasured)
    assert "trades.BTC-PERPETUAL.100ms" not in str(s["raw_trade_seq_continuity"])


def test_census_budget_capped_at_120s(tmp_path):
    with pytest.raises(LoudError, match="120s"):
        asyncio_run_census_too_long(tmp_path)


def asyncio_run_census_too_long(tmp_path):
    import asyncio
    from research.assets.data_edge_unlock_v1.collectors.collector import run_trades_census

    return asyncio.run(run_trades_census(121.0, tmp_path / "census.jsonl"))


# ---------------------------------------------------------------------------
# pidfile + runtime-dir policy (PID files NEVER under research/)
# ---------------------------------------------------------------------------
def test_default_run_dir_is_data_root_runtime_never_research(tmp_path):
    root = tmp_path / "raw"
    col = Collector("coinbase", data_root=root)
    assert col.run_dir == root.parent / "runtime"
    assert "research" not in str(col.run_dir)


def test_pidfile_written_and_removed(tmp_path):
    col, root, run, clock = make_collector(tmp_path, "coinbase")
    path = write_pidfile(run, "coinbase", {
        "endpoint": "wss://advanced-trade-ws.coinbase.com",
        "instruments": ["BTC-USD", "ETH-USD"],
        "data_root": root,
        "code_sha256": "deadbeef",
    })
    payload = json.loads(path.read_text())
    assert payload["schema"] == "deu_collector_pidfile@1"
    assert payload["venue"] == "coinbase" and isinstance(payload["pid"], int)
    assert payload["started_utc"].endswith("Z")
    remove_pidfile(run, "coinbase", payload["pid"])
    assert not path.exists()
    # a foreign pid does not clobber the pidfile
    write_pidfile(run, "coinbase", {"endpoint": "e", "instruments": [], "data_root": root})
    remove_pidfile(run, "coinbase", payload["pid"] + 1)
    assert path.exists()


def test_unknown_venue_is_loud(tmp_path):
    with pytest.raises(LoudError, match="unknown venue"):
        Collector("binance", data_root=tmp_path / "raw")
