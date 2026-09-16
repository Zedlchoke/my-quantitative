"""Per-venue adapters: subscribe messages, classification, sequence
semantics, heartbeat policy and measured payload-shape validators.

Every shape rule below is the MEASURED census wire format (FDF-V1 census
bytes, sha-pinned in the frozen A3 contract freeze field 2).  Validation is
structural (keys/types of the measured fields) and is never lossy: a failing
message is written raw to the shard-rejected subrecord, counted LOUD, and
never silently dropped.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from . import ENDPOINTS, INSTRUMENTS


# ---------------------------------------------------------------------------
# sequence trackers (contract freeze fields 4/5)
# ---------------------------------------------------------------------------
class GapEvent(Tuple):  # typing aid only
    pass


class SequenceTracker:
    """Tracks one venue-native sequence space; returns gap records.

    Frozen semantics per venue:
    - coinbase : payload.sequence_num, per-connection monotone across ALL
      channels; gap iff delta > 1 across consecutive messages within the
      connection epoch (regressions/dups are NOT gaps — field 8 territory).
    - kraken   : book feed per (product_id, side) seq; trade feed per
      product seq; gap iff delta > 1.  book_snapshot / trade_snapshot reset
      continuity (fresh snapshot recovery, field 5).
    - deribit  : book change_id per instrument; losslessness on the 100ms
      aggregated channel is carried by prev_change_id (MEASURED: inter-
      delivery deltas are 10^2..10^3 by design); gap iff a change message's
      prev_change_id != the last delivered change_id; type:'snapshot'
      resets continuity (fresh snapshot recovery, field 5).
    """

    def __init__(self, venue: str) -> None:
        self.venue = venue
        self.last: Dict[Tuple[str, ...], int] = {}
        self.last_kind: Dict[Tuple[str, ...], str] = {}
        self.reg_count = 0  # in-epoch regressions/duplicates (not gaps)

    def reset(self, key: Tuple[str, ...]) -> None:
        self.last.pop(key, None)
        self.last_kind.pop(key, None)

    def reset_all(self) -> None:
        self.last.clear()
        self.last_kind.clear()

    def observe(
        self,
        key: Tuple[str, ...],
        seq: int,
        kind: str = "delta",  # 'delta' continues continuity; 'snapshot' resets
    ) -> Optional[Dict[str, Any]]:
        """Feed one sequenced message.  Returns a gap record dict when the
        frozen delta rule detects a gap, else None."""
        prev = self.last.get(key)
        prev_kind = self.last_kind.get(key)
        self.last[key] = seq
        self.last_kind[key] = kind
        if kind == "snapshot" or prev is None or prev_kind != "delta":
            return None
        if seq > prev + 1:
            return {
                "type": "gap",
                "venue": self.venue,
                "instrument": _instrument_of(key),
                "from_seq": prev,
                "to_seq": seq,
                "missing_count": seq - prev - 1,
            }
        if seq <= prev:
            # in-epoch regression/duplicate: counted, never a frozen gap,
            # raw line still written verbatim (dedupe is derivation-level).
            self.reg_count += 1
        return None


def _instrument_of(key: Tuple[str, ...]) -> str:
    return "/".join(part for part in key[1:] if part) or key[0]


# ---------------------------------------------------------------------------
# payload-shape validators (measured census shapes; structural only)
# ---------------------------------------------------------------------------
def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class ShapeVerdict:
    __slots__ = ("ok", "reason")

    def __init__(self, ok: bool, reason: str = "") -> None:
        self.ok = ok
        self.reason = reason


def _need(d: Any, field: str, checks: tuple, ctx: str) -> ShapeVerdict:
    if not isinstance(d, dict) or field not in d:
        return ShapeVerdict(False, f"{ctx}: missing field '{field}'")
    val = d[field]
    if isinstance(val, bool) and bool not in checks:
        return ShapeVerdict(False, f"{ctx}: field '{field}' is bool")
    for chk in checks:
        if isinstance(chk, type):
            if isinstance(val, chk):
                return ShapeVerdict(True)
        elif callable(chk):
            if chk(val):
                return ShapeVerdict(True)
    return ShapeVerdict(
        False,
        f"{ctx}: field '{field}' type {type(val).__name__} fails {checks}",
    )


# -- coinbase ---------------------------------------------------------------
def coinbase_validate(payload: Any) -> ShapeVerdict:
    """Measured: {channel:str, timestamp:str(ns ISO), sequence_num:int,
    events:list}; per-channel event shapes for ticker / market_trades /
    l2_data / heartbeats / subscriptions; bare error envelopes are captured
    verbatim (loud, never dropped)."""
    if not isinstance(payload, dict):
        return ShapeVerdict(False, "payload not an object")
    if payload.get("type") == "error":
        return _need(payload, "type", (str,), "coinbase.error")
    for f, t in (("channel", (str,)), ("timestamp", (str,)), ("sequence_num", (int,)), ("events", (list,))):
        v = _need(payload, f, t, "coinbase")
        if not v.ok:
            return v
    channel = payload["channel"]
    for ev in payload["events"]:
        if not isinstance(ev, dict):
            return ShapeVerdict(False, f"{channel}: event not an object")
        if channel == "market_trades":
            trades = ev.get("trades")
            if not isinstance(trades, list):
                return ShapeVerdict(False, "market_trades: missing trades[]")
            for tr in trades:
                for f in ("product_id", "trade_id", "price", "size", "side", "time"):
                    v = _need(tr, f, (str,), "market_trades.trade")
                    if not v.ok:
                        return v
        elif channel == "ticker":
            tickers = ev.get("tickers")
            if not isinstance(tickers, list):
                return ShapeVerdict(False, "ticker: missing tickers[]")
            for tk in tickers:
                v = _need(tk, "product_id", (str,), "ticker")
                if not v.ok:
                    return v
        elif channel == "l2_data":
            updates = ev.get("updates")
            v = _need(ev, "product_id", (str,), "l2_data")
            if not v.ok:
                return v
            if not isinstance(updates, list):
                return ShapeVerdict(False, "l2_data: missing updates[]")
            for up in updates:
                for f in ("event_time", "price_level", "new_quantity", "side"):
                    v = _need(up, f, (str,), "l2_data.update")
                    if not v.ok:
                        return v
        elif channel in ("heartbeats", "subscriptions", "error"):
            pass  # measured minimal shape: envelope fields suffice
    return ShapeVerdict(True)


def coinbase_sequence(payload: Dict[str, Any]) -> Optional[int]:
    seq = payload.get("sequence_num")
    return seq if isinstance(seq, int) else None


def coinbase_track_and_seq(
    tracker: SequenceTracker, payload: Dict[str, Any]
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    """CB sequence_num is ONE per-connection monotone counter across ALL
    channels (measured 0,1,2,...): a single tracker key per connection
    epoch.  Gap iff delta > 1 (freeze field 5); regressions/duplicates are
    NOT gaps (field 8).  Envelope seq is null for Coinbase (seq equals
    Deribit change_id where served, else null)."""
    seq = coinbase_sequence(payload)
    if seq is None:
        return None, None
    gap = tracker.observe(("conn",), seq, "delta")
    if gap:
        gap["channel"] = str(payload.get("channel", "unknown"))
    return None, gap


# -- kraken futures ----------------------------------------------------------
def kraken_validate(payload: Any) -> ShapeVerdict:
    """Measured feeds: ticker (time:int, product_id, bid, ask, markPrice,
    funding_rate...), book ({feed:'book', product_id, side, seq:int, price,
    qty, timestamp:int}), trade ({product_id, uid, side, type:'fill', time,
    qty, price, seq:int}), book_snapshot / trade_snapshot, heartbeat,
    event_* envelopes."""
    if not isinstance(payload, dict):
        return ShapeVerdict(False, "payload not an object")
    # control-plane envelopes first (MEASURED: subscription acks carry both
    # 'event' and 'feed' keys)
    if "event" in payload:
        return _need(payload, "event", (str,), "kraken.event")
    feed = payload.get("feed")
    if feed is None:
        return ShapeVerdict(False, "kraken: neither 'feed' nor 'event'")
    if not isinstance(feed, str):
        return ShapeVerdict(False, "kraken: 'feed' not a string")
    if feed == "heartbeat":
        return ShapeVerdict(True)
    if feed == "ticker":
        v = _need(payload, "time", (int,), "kraken.ticker")
        if not v.ok:
            return v
        return _need(payload, "product_id", (str,), "kraken.ticker")
    if feed == "book":
        for f, t in (("product_id", (str,)), ("side", (str,)), ("seq", (int,)), ("price", (_is_num,)), ("qty", (_is_num,)), ("timestamp", (int,))):
            v = _need(payload, f, t, "kraken.book")
            if not v.ok:
                return v
        return ShapeVerdict(True)
    if feed == "book_snapshot":
        return _need(payload, "product_id", (str,), "kraken.book_snapshot")
    if feed == "trade":
        for f, t in (("product_id", (str,)), ("uid", (str,)), ("side", (str,)), ("seq", (int,)), ("price", (_is_num,)), ("qty", (_is_num,)), ("time", (int,))):
            v = _need(payload, f, t, "kraken.trade")
            if not v.ok:
                return v
        return ShapeVerdict(True)
    if feed == "trade_snapshot":
        v = _need(payload, "product_id", (str,), "kraken.trade_snapshot")
        if not v.ok:
            return v
        if "trades" in payload and not isinstance(payload["trades"], list):
            return ShapeVerdict(False, "trade_snapshot: 'trades' not a list")
        return ShapeVerdict(True)
    return ShapeVerdict(True)  # event_info / unknown-but-fed messages: capture verbatim


def kraken_classify(payload: Dict[str, Any]) -> str:
    if isinstance(payload, dict):
        # control-plane envelopes (event + feed keys) classify as events
        if "event" in payload and "feed" not in payload:
            return f"event_{payload.get('event')}"
        feed = payload.get("feed")
        if isinstance(feed, str):
            if "event" in payload:
                return f"event_{payload.get('event')}"
            if feed == "book_snapshot":
                return "book_snapshot"
            if feed.startswith("book"):
                return "book"
            return feed
        if "event" in payload:
            return f"event_{payload.get('event')}"
    return "unknown"


def kraken_track_and_seq(
    tracker: SequenceTracker, payload: Dict[str, Any]
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    """Returns (envelope_seq, gap_record).  Envelope seq is null for Kraken
    (contract: seq equals Deribit change_id where served, else null)."""
    if "event" in payload:
        # control envelope (MEASURED: subscription acks carry BOTH 'event'
        # and 'feed' keys) — no sequence content, never tracked
        return None, None
    feed = payload.get("feed")
    if feed == "book":
        key = ("book", str(payload.get("product_id")), str(payload.get("side")))
        gap = tracker.observe(key, int(payload["seq"]), "delta")
        if gap:
            gap["channel"] = "book"
        return None, gap
    if feed == "book_snapshot":
        # MEASURED census side values are 'buy'/'sell'
        tracker.reset(("book", str(payload.get("product_id")), "buy"))
        tracker.reset(("book", str(payload.get("product_id")), "sell"))
        return None, None
    if feed == "trade":
        key = ("trade", str(payload.get("product_id")))
        gap = tracker.observe(key, int(payload["seq"]), "delta")
        if gap:
            gap["channel"] = "trade"
        return None, gap
    if feed == "trade_snapshot":
        tracker.reset(("trade", str(payload.get("product_id"))))
        return None, None
    return None, None


# -- deribit -----------------------------------------------------------------
def deribit_validate(payload: Any) -> ShapeVerdict:
    """Measured JSON-RPC 2.0: subscription messages carry
    params.{channel, data}; BOOK data = {timestamp:int(ms),
    type:'snapshot'|'change', change_id:int, instrument_name, bids/asks};
    TICKER data has NO 'type' field (measured census: timestamp, state,
    stats, index_price, mark_price, ...) and NO change_id.  rpc heartbeats
    (method heartbeat/test_request) and rpc responses are captured verbatim."""
    if not isinstance(payload, dict):
        return ShapeVerdict(False, "payload not an object")
    if payload.get("method") in ("heartbeat", "test_request"):
        return ShapeVerdict(True)
    if "params" not in payload:
        if "result" in payload or "error" in payload:
            return ShapeVerdict(True)
        return ShapeVerdict(False, "deribit: no 'params' and not an rpc response/heartbeat")
    params = payload["params"]
    if not isinstance(params, dict):
        return ShapeVerdict(False, "deribit: 'params' not an object")
    v = _need(params, "channel", (str,), "deribit")
    if not v.ok:
        return v
    channel = str(params["channel"])
    if channel.startswith("volatility_index"):
        # contract lists the volatility_index surface but the census measured
        # no data-shape for it: captured verbatim, not structurally enforced
        return ShapeVerdict(True)
    data = params.get("data")
    if not isinstance(data, dict):
        return ShapeVerdict(False, "deribit: 'data' not an object")
    v = _need(data, "timestamp", (int,), "deribit.data")
    if not v.ok:
        return v
    v = _need(data, "instrument_name", (str,), "deribit.data")
    if not v.ok:
        return v
    if channel.startswith("book."):
        # MEASURED: type ('snapshot'|'change') and change_id are book-only
        for f, t in (("type", (str,)), ("change_id", (int,))):
            v = _need(data, f, t, "deribit.book")
            if not v.ok:
                return v
        if data["type"] not in ("snapshot", "change"):
            return ShapeVerdict(False, f"deribit.data.type '{data['type']}' not snapshot|change")
    return ShapeVerdict(True)


def deribit_classify(payload: Dict[str, Any]) -> str:
    if isinstance(payload, dict):
        params = payload.get("params")
        if isinstance(params, dict) and params.get("channel"):
            return str(params["channel"])
        if "method" in payload:
            return f"rpc_{payload.get('method')}"
        if "result" in payload or "error" in payload:
            return "rpc_response"
    return "unknown"


def deribit_seq(payload: Dict[str, Any]) -> Optional[int]:
    """Envelope seq = change_id where served (book channels), else null."""
    params = payload.get("params")
    if isinstance(params, dict) and isinstance(params.get("data"), dict):
        cid = params["data"].get("change_id")
        if isinstance(cid, int):
            return cid
    return None


def deribit_track(
    tracker: SequenceTracker, payload: Dict[str, Any]
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    """book change_id per instrument.  MEASURED on live wire (2026-09-16,
    326/326 transitions): the 100ms channel aggregates orderbook events, so
    inter-delivery deltas are routinely 10^2..10^3 — losslessness is carried
    by the payload's own prev_change_id, and prev_change_id(N+1) ==
    change_id(N) on every observed transition.  Gap rule: on type:'change',
    prev_change_id != last delivered change_id -> lost updates -> gap record
    (missing_count -1 = unknown count of lost messages).  type:'snapshot'
    resets continuity (field 5 recovery).  A literal inter-delivery
    'delta != 1' rule would flag 100% of messages and make the contract's
    own 90% valid-triad floor unattainable; this reading is DECLARED as a
    collection incident in start_manifest.json + the A8 handoff.
    Envelope seq = change_id where served (book channels), else null."""
    params = payload.get("params")
    if not (isinstance(params, dict) and isinstance(params.get("data"), dict)):
        return deribit_seq(payload), None
    channel = str(params.get("channel", ""))
    data = params["data"]
    if not channel.startswith("book."):
        return deribit_seq(payload), None
    instrument = str(data.get("instrument_name", channel))
    key = ("book", instrument)
    cid = int(data["change_id"])
    if data.get("type") == "snapshot":
        tracker.reset(key)
        return cid, None
    prev = tracker.last.get(key)
    tracker.last[key] = cid
    tracker.last_kind[key] = "delta"
    gap = None
    if prev is not None:
        expected_prev = data.get("prev_change_id")
        if not isinstance(expected_prev, int) or expected_prev != prev:
            gap = {
                "type": "gap",
                "venue": "deribit",
                "channel": channel,
                "instrument": instrument,
                "from_seq": prev,
                "to_seq": cid,
                "missing_count": -1,  # unknown: lost update count not derivable
                "reason": "prev_change_id mismatch (lost update)",
            }
    return cid, gap


# ---------------------------------------------------------------------------
# venue registry
# ---------------------------------------------------------------------------
class VenueSpec:
    def __init__(
        self,
        name: str,
        subscribe_messages_fn,
        classify_fn,
        validate_fn,
        track_fn,
        seq_fn,
        heartbeat_channel: str,
        heartbeat_timeout_s: float,
        probe_messages_fn,
        silence_timeout_s: float,
    ) -> None:
        self.name = name
        self.endpoint = ENDPOINTS[name]
        self.instruments = INSTRUMENTS[name]
        self.subscribe_messages = subscribe_messages_fn
        self.classify = classify_fn
        self.validate = validate_fn
        self.track = track_fn
        self.seq = seq_fn
        self.heartbeat_channel = heartbeat_channel
        self.heartbeat_timeout_s = heartbeat_timeout_s
        self.probe_messages = probe_messages_fn
        self.silence_timeout_s = silence_timeout_s


def _cb_subscribe() -> List[Dict[str, Any]]:
    msgs = []
    for channel in ("ticker", "market_trades", "l2_data", "heartbeats"):
        msgs.append({"type": "subscribe", "product_ids": INSTRUMENTS["coinbase"], "channel": channel})
    return msgs


def _cb_probe() -> List[Dict[str, Any]]:
    # Coinbase has no public test echo; a subscriptions re-request doubles
    # as the probe (contract field 6: 'absence > 15s -> probe then reconnect').
    return [{"type": "subscriptions"}]


def _kr_subscribe() -> List[Dict[str, Any]]:
    msgs = []
    for feed in ("ticker", "trade", "book", "heartbeat"):
        m: Dict[str, Any] = {"event": "subscribe", "feed": feed}
        if feed != "heartbeat":
            m["product_ids"] = INSTRUMENTS["kraken"]
        msgs.append(m)
    return msgs


def _kr_probe() -> List[Dict[str, Any]]:
    return []  # contract: absence > 60s -> reconnect (no probe step)


def _db_subscribe() -> List[Dict[str, Any]]:
    channels = [f"book.{i}.100ms" for i in INSTRUMENTS["deribit"]]
    channels += [f"ticker.{i}.100ms" for i in INSTRUMENTS["deribit"]]
    channels += ["volatility_index.btc_volatility", "volatility_index.eth_volatility"]
    return [
        {"jsonrpc": "2.0", "id": 101, "method": "public/subscribe", "params": {"channels": channels}},
        {"jsonrpc": "2.0", "id": 601, "method": "public/set_heartbeat", "params": {"interval": 30}},
    ]


def _db_probe() -> List[Dict[str, Any]]:
    return [{"jsonrpc": "2.0", "id": 901, "method": "public/test", "params": {}}]


def _cb_classify(payload: Any) -> str:
    if isinstance(payload, dict):
        if isinstance(payload.get("channel"), str):
            return str(payload["channel"])
        if payload.get("type") in ("subscriptions", "error"):
            return str(payload["type"])
    return "unknown"


VENUE_SPECS: Dict[str, VenueSpec] = {
    "coinbase": VenueSpec(
        name="coinbase",
        subscribe_messages_fn=_cb_subscribe,
        classify_fn=_cb_classify,
        validate_fn=coinbase_validate,
        track_fn=coinbase_track_and_seq,
        seq_fn=coinbase_sequence,
        heartbeat_channel="heartbeats",
        heartbeat_timeout_s=15.0,
        probe_messages_fn=_cb_probe,
        silence_timeout_s=30.0,
    ),
    "kraken": VenueSpec(
        name="kraken",
        subscribe_messages_fn=_kr_subscribe,
        classify_fn=kraken_classify,
        validate_fn=kraken_validate,
        track_fn=kraken_track_and_seq,
        seq_fn=lambda p: None,
        heartbeat_channel="heartbeat",
        heartbeat_timeout_s=60.0,
        probe_messages_fn=_kr_probe,
        silence_timeout_s=90.0,
    ),
    "deribit": VenueSpec(
        name="deribit",
        subscribe_messages_fn=_db_subscribe,
        classify_fn=deribit_classify,
        validate_fn=deribit_validate,
        track_fn=deribit_track,
        seq_fn=deribit_seq,
        heartbeat_channel="rpc_heartbeat",
        heartbeat_timeout_s=45.0,
        probe_messages_fn=_db_probe,
        silence_timeout_s=60.0,
    ),
}
