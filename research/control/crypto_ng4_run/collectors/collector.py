"""Async collector main loop for one venue (CRYPTO-NG4 lane A8).

Contract binding (frozen A3 dossier):
- reconnect: exponential backoff 1s,2s,4s,... capped 60s; new
  connection_epoch per connection; connection boundaries recorded; NO
  cross-epoch sequence stitching.
- heartbeat: venue-native heartbeat channel/watchdog (CB 15s probe-then-
  reconnect, KR 60s reconnect, DB 45s reconnect); plus a total-silence
  watchdog and aiohttp WS ping keepalive.
- shard per (venue, UTC day, connection_epoch); day rollover closes the
  shard (manifest row) and opens the next with the SAME epoch.
- payload-shape mismatch fails LOUD (stderr + rejected subrecord + counts).
- local heartbeat FILE with bytes-written + per-shape counts every <= 60s.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import aiohttp

from .core import (
    DEFAULT_DATA_ROOT,
    LoudError,
    ManifestAppender,
    ShardWriter,
    finalize_orphan_shards,
    utc_now_iso,
)
from .venues import VENUE_SPECS, SequenceTracker, VenueSpec

HEARTBEAT_FILE_PERIOD_S = 15.0  # dispatch: every <= 60s
RECV_TIMEOUT_S = 0.5
PROBE_GRACE_S = 10.0
BACKOFF_START_S = 1.0
BACKOFF_CAP_S = 60.0


def _utc_day(clock: Callable[[], datetime]) -> str:
    return clock().strftime("%Y-%m-%d")


class Collector:
    def __init__(
        self,
        venue: str,
        data_root: Path = DEFAULT_DATA_ROOT,
        run_dir: Optional[Path] = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        max_seconds: Optional[float] = None,
    ) -> None:
        if venue not in VENUE_SPECS:
            raise LoudError(f"unknown venue '{venue}' (known: {sorted(VENUE_SPECS)})")
        self.spec: VenueSpec = VENUE_SPECS[venue]
        self.venue = venue
        self.data_root = Path(data_root)
        self.run_dir = Path(run_dir) if run_dir else Path(__file__).resolve().parent / "run"
        self.clock = clock
        self.max_seconds = max_seconds
        self.monotonic = time.monotonic

        self.conn_epoch = 0
        self.tracker = None  # rebuilt per connection epoch
        self.shard: Optional[ShardWriter] = None
        self.manifest = ManifestAppender(self.data_root / "manifest.jsonl")
        self.stop_requested = False
        self.backoff = BACKOFF_START_S

        # heartbeat-file counters
        self.stats: Dict[str, Any] = {
            "venue": venue,
            "source_id": f"{venue}_ws",
            "endpoint": self.spec.endpoint,
            "instruments": list(self.spec.instruments),
            "pid": os.getpid(),
            "started_process_utc": None,
            "shadow_start_utc": None,  # first byte received from the venue
            "conn_epoch": 0,
            "disconnects": 0,
            "connect_errors": 0,
            "shape_errors": 0,
            "reconnect_probe_sent": 0,
            "bytes_written": 0,
            "lines_written": 0,
            "gap_count": 0,
            "dup_count": 0,
            "heartbeat_count": 0,
            "per_channel_counts": {},
            "last_recv_utc": None,
            "last_venue_heartbeat_utc": None,
        }
        self.hb_path = self.run_dir / f"{venue}.heartbeat.json"
        self.conn_log = self.run_dir / f"{venue}.connections.jsonl"
        self._last_hb_file_mono = 0.0
        self._hb_last_venue_mono: Optional[float] = None
        self._last_message_mono: Optional[float] = None
        self._probe_sent_mono: Optional[float] = None
        self._conn_open: Dict[str, Any] = {}

    # -- bookkeeping ------------------------------------------------------
    def _record_connection(self, rec: Dict[str, Any]) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(rec, separators=(",", ":"), default=str).encode("utf-8")
        with open(self.conn_log, "ab") as fh:
            fh.write(raw + b"\n")
            fh.flush()
            os.fsync(fh.fileno())

    def write_heartbeat_file(self) -> None:
        self.stats["updated_utc"] = utc_now_iso(self.clock)
        self.stats["conn_epoch"] = self.conn_epoch
        if self.shard is not None:
            self.stats["shard_rel"] = self.shard.rel
            self.stats["bytes_written"] = self.shard.bytes
            self.stats["lines_written"] = self.shard.lines
            self.stats["per_channel_counts"] = dict(self.shard.per_channel_counts)
            self.stats["gap_count"] = self.shard.gap_count
            self.stats["dup_count"] = self.shard.dup_count
            self.stats["heartbeat_count"] = self.shard.heartbeat_count
        self.stats["shape_errors"] = self.stats.get("shape_errors", 0)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.hb_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.stats, indent=2, default=str) + "\n")
        os.replace(tmp, self.hb_path)  # atomic
        self._last_hb_file_mono = self.monotonic()

    # -- shard lifecycle ---------------------------------------------------
    def _open_shard(self, now_iso: str) -> None:
        day = _utc_day(self.clock)
        self.shard = ShardWriter(self.data_root, self.venue, day, self.conn_epoch, clock=self.clock)
        self.shard.open()
        self.shard.first_recv_utc = None

    def _close_shard(self, now_iso: str) -> None:
        if self.shard is None:
            return
        final = self.shard.close(closed_utc=now_iso)
        if self.shard.lines:
            row = self.shard.manifest_row(closed_utc=now_iso, prev_manifest_sha256=self.manifest.head_sha256())
            self.manifest.append_row(row)
        else:
            # empty shard (e.g. connect failed immediately): remove instead
            # of emitting a zero-line manifest row — nothing was captured.
            final.unlink(missing_ok=True)
            self.shard.rejected_path.unlink(missing_ok=True)
        self.shard = None

    # -- message path (the contract-critical one) --------------------------
    def process_text(self, raw_line: str) -> None:
        """Parse -> classify -> validate (LOUD) -> gap-track -> append."""
        recv_utc = utc_now_iso(self.clock)
        if self.stats["shadow_start_utc"] is None:
            self.stats["shadow_start_utc"] = recv_utc
        self.stats["last_recv_utc"] = recv_utc
        self._last_message_mono = self.monotonic()

        try:
            payload = json.loads(raw_line)
        except ValueError as exc:
            assert self.shard is not None
            self.stats["shape_errors"] = self.stats.get("shape_errors", 0) + 1
            self.shard.append_rejection(recv_utc, f"json_parse_error: {exc}", raw_line)
            return

        channel = self.spec.classify(payload)
        verdict = self.spec.validate(payload)
        if not verdict.ok:
            assert self.shard is not None
            self.stats["shape_errors"] = self.stats.get("shape_errors", 0) + 1
            self.shard.append_rejection(recv_utc, verdict.reason, raw_line)
            return

        # gap detection (venue-specific frozen semantics)
        envelope_seq, gap = (None, None)
        if self.spec.track is not None:
            envelope_seq, gap = self.spec.track(self.tracker, payload)
        if gap is not None:
            assert self.shard is not None
            self.shard.append_gap_record(
                recv_utc=recv_utc,
                channel=gap.get("channel", channel),
                instrument=gap.get("instrument", "unknown"),
                from_seq=gap["from_seq"],
                to_seq=gap["to_seq"],
                missing_count=gap.get("missing_count"),
            )

        # duplicate accounting (verbatim capture still proceeds)
        line_hash = hashlib.sha256(raw_line.encode("utf-8")).hexdigest()
        dup_key = self._dup_key(channel, payload, envelope_seq)
        if self.shard is not None:
            self.shard.note_duplicate(channel, dup_key, line_hash)
            self.shard.append_message(recv_utc, channel, envelope_seq, payload)

        if channel == self.spec.heartbeat_channel:
            self.shard.heartbeat_count += 1
            self.stats["last_venue_heartbeat_utc"] = recv_utc
            self._hb_last_venue_mono = self.monotonic()
            self._probe_sent_mono = None

    def _dup_key(self, channel: str, payload: Dict[str, Any], envelope_seq: Optional[int]):
        """Contract dedupe key: (venue, connection_epoch, venue sequence /
        trade id, sha256(raw)) — the epoch + raw-line hash are bound at the
        shard level, so the collector contributes the venue identity here."""
        venue = self.venue
        if venue == "coinbase":
            seq = payload.get("sequence_num")
            return (venue, channel, seq) if isinstance(seq, int) else None
        if venue == "kraken":
            feed = payload.get("feed")
            if feed == "book":
                return (venue, "book", payload.get("product_id"), payload.get("side"), payload.get("seq"))
            if feed == "trade":
                return (venue, "trade", payload.get("product_id"), payload.get("seq"))
            if feed in ("book_snapshot", "trade_snapshot", "ticker", "heartbeat"):
                return (venue, feed, payload.get("product_id"), payload.get("time") or payload.get("timestamp"))
            return None
        if venue == "deribit":
            params = payload.get("params")
            if isinstance(params, dict):
                data = params.get("data")
                if isinstance(data, dict):
                    return (venue, params.get("channel"), data.get("change_id"), data.get("timestamp"))
            return None
        return None

    # -- main loop ----------------------------------------------------------
    async def run(self) -> Dict[str, Any]:
        self.stats["started_process_utc"] = utc_now_iso(self.clock)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.data_root.mkdir(parents=True, exist_ok=True)

        orphans = finalize_orphan_shards(
            self.data_root, self.venue, self.manifest, utc_now_iso(self.clock)
        )
        if orphans:
            print(f"[{self.venue}] finalized {len(orphans)} orphan shard(s) on startup", flush=True)

        deadline = None if self.max_seconds is None else self.monotonic() + self.max_seconds
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=15, sock_read=None)

        while not self.stop_requested:
            if deadline is not None and self.monotonic() >= deadline:
                break
            try:
                await self._run_connection(timeout)
            except LoudError:
                raise  # never paper over integrity failures
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.stats["connect_errors"] += 1
                print(
                    f"[{self.venue}] connection failed: {type(exc).__name__}: {str(exc)[:200]}",
                    file=sys.stderr,
                    flush=True,
                )
            if self.stop_requested:
                break
            await self._sleep_backoff()
        self.write_heartbeat_file()
        return dict(self.stats)

    async def _sleep_backoff(self) -> None:
        delay = self.backoff
        self.backoff = min(self.backoff * 2.0, BACKOFF_CAP_S)
        end = self.monotonic() + delay
        while not self.stop_requested and self.monotonic() < end:
            await asyncio.sleep(min(0.25, max(0.0, end - self.monotonic())))

    async def _run_connection(self, timeout: aiohttp.ClientTimeout) -> None:
        now_iso = utc_now_iso(self.clock)
        # time-based connection epoch: unique across restarts of this
        # collector (a per-process counter would collide shard names with
        # shards closed by a previous process instance)
        self.conn_epoch = int(time.time() * 1000)
        self.stats["conn_epoch"] = self.conn_epoch
        self.tracker = SequenceTracker(self.venue)
        self._conn_open = {
            "venue": self.venue,
            "conn_epoch": self.conn_epoch,
            "open_utc": now_iso,
            "monotonic_at_open": self.monotonic(),
            "note": "wall-vs-monotonic pair for drift audit (contract field 3)",
        }
        self._hb_last_venue_mono = self.monotonic()
        self._last_message_mono = self.monotonic()
        self._probe_sent_mono = None
        self.backoff = BACKOFF_START_S

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.ws_connect(
                self.spec.endpoint,
                heartbeat=20,  # aiohttp WS ping keepalive (TCP liveness)
                max_msg_size=8 * 1024 * 1024,
            ) as ws:
                self._open_shard(now_iso)
                for sub in self.spec.subscribe_messages():
                    await ws.send_str(json.dumps(sub))
                self._record_connection(self._conn_open)
                self.write_heartbeat_file()
                try:
                    while not self.stop_requested:
                        if self._watchdog_due(ws):
                            break
                        try:
                            msg = await asyncio.wait_for(ws.receive(), timeout=RECV_TIMEOUT_S)
                        except asyncio.TimeoutError:
                            continue
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            self.process_text(msg.data)
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            self.process_text(msg.data.decode("utf-8", errors="replace"))
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.ERROR):
                            self.stats["disconnects"] += 1
                            print(f"[{self.venue}] ws closed/error — reconnecting", file=sys.stderr, flush=True)
                            break
                finally:
                    close_iso = utc_now_iso(self.clock)
                    self._record_connection(
                        {
                            **self._conn_open,
                            "close_utc": close_iso,
                            "close_reason": "collector_stop" if self.stop_requested else "reconnect",
                        }
                    )
                    self._close_shard(close_iso)
                    self.write_heartbeat_file()

    def _watchdog_due(self, ws) -> bool:
        """Venue heartbeat absence -> probe -> reconnect (contract field 6);
        total silence -> reconnect; heartbeat file every <= 60s; day
        rollover closes the shard and opens the next (same conn_epoch)."""
        now = self.monotonic()
        if now - self._last_hb_file_mono >= HEARTBEAT_FILE_PERIOD_S:
            self.write_heartbeat_file()

        # UTC day rollover -> new shard, same connection epoch
        if self.shard is not None:
            day_now = _utc_day(self.clock)
            if day_now != self.shard.day_utc:
                rollover_iso = utc_now_iso(self.clock)
                self._close_shard(rollover_iso)
                self._open_shard(rollover_iso)
                self._record_connection({**self._conn_open, "note": "day_rollover_shard_split", "at_utc": rollover_iso})

        if self._last_message_mono is not None and now - self._last_message_mono > self.spec.silence_timeout_s:
            print(f"[{self.venue}] total silence > {self.spec.silence_timeout_s}s — reconnect", file=sys.stderr, flush=True)
            return True

        hb_expired = (
            self._hb_last_venue_mono is not None
            and now - self._hb_last_venue_mono > self.spec.heartbeat_timeout_s
        )
        if hb_expired and self._probe_sent_mono is None:
            probe = self.spec.probe_messages()
            if not probe:
                # Kraken policy: absence > 60s -> reconnect (no probe step)
                print(f"[{self.venue}] heartbeat absent > {self.spec.heartbeat_timeout_s}s — reconnect", file=sys.stderr, flush=True)
                return True
            for m in probe:
                asyncio.ensure_future(_send_json(ws, m))
            self._probe_sent_mono = now
            self.stats["reconnect_probe_sent"] = self.stats.get("reconnect_probe_sent", 0) + 1
            print(f"[{self.venue}] heartbeat absent > {self.spec.heartbeat_timeout_s}s — probe sent", file=sys.stderr, flush=True)
        elif self._probe_sent_mono is not None and now - self._probe_sent_mono > PROBE_GRACE_S:
            print(f"[{self.venue}] probe unanswered > {PROBE_GRACE_S}s — reconnect", file=sys.stderr, flush=True)
            return True
        return False

    def request_stop(self, *_args: Any) -> None:
        self.stop_requested = True


async def _send_json(ws, obj: Dict[str, Any]) -> None:
    try:
        await ws.send_str(json.dumps(obj))
    except Exception:
        pass  # connection is dying; the reconnect path owns recovery


def write_pidfile(run_dir: Path, venue: str, extra: Dict[str, Any]) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"{venue}.pid"
    payload = {
        "schema": "cng4_collector_pidfile@1",
        "venue": venue,
        "pid": os.getpid(),
        "started_utc": utc_now_iso(),
        "endpoint": extra.get("endpoint"),
        "instruments": extra.get("instruments"),
        "data_root": str(extra.get("data_root")),
        "code_sha256": extra.get("code_sha256"),
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(tmp, path)
    return path


def remove_pidfile(run_dir: Path, venue: str, pid: int) -> None:
    path = run_dir / f"{venue}.pid"
    try:
        if path.exists() and json.loads(path.read_text()).get("pid") == pid:
            path.unlink()
    except (ValueError, OSError):
        pass


async def amain(venue: str, data_root: Path, max_seconds: Optional[float] = None) -> int:
    collector = Collector(venue, data_root=data_root, max_seconds=max_seconds)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, collector.request_stop)
        except (NotImplementedError, ValueError):
            signal.signal(sig, lambda *_: collector.request_stop())
    code_sha = hashlib.sha256()
    here = Path(__file__).resolve().parent
    for mod in sorted(here.glob("*.py")):
        code_sha.update(mod.read_bytes())
    write_pidfile(
        collector.run_dir,
        venue,
        {
            "endpoint": collector.spec.endpoint,
            "instruments": collector.spec.instruments,
            "data_root": collector.data_root,
            "code_sha256": code_sha.hexdigest(),
        },
    )
    try:
        stats = await collector.run()
    finally:
        remove_pidfile(collector.run_dir, venue, os.getpid())
    print(json.dumps({"event": "collector_exit", "venue": venue, "stats": stats}, default=str))
    return 0


def main(argv: list) -> int:
    if len(argv) < 2 or argv[1] not in VENUE_SPECS:
        print("usage: run_one.py <coinbase|kraken|deribit> [--data-root PATH] [--max-seconds N]", flush=True)
        return 2
    venue = argv[1]
    data_root = DEFAULT_DATA_ROOT
    max_seconds = None
    args = argv[2:]
    if "--data-root" in args:
        data_root = Path(args[args.index("--data-root") + 1])
    if "--max-seconds" in args:
        max_seconds = float(args[args.index("--max-seconds") + 1])
    return asyncio.run(amain(venue, data_root, max_seconds))


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv))
