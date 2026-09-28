#!/usr/bin/env python3
"""Binance L2 orderbook collector — lane CX, DATA-FOUNDATION-SIXSOURCE-V1.

PROSPECTIVE_FROM_2026-09-28 — this collector produces a from-today sample,
NOT historical data. Repo law stands: no order-book / forced-flow inference
from candles; nothing here may be presented as backtestable history.

Method (per dispatch packet PACKET_lane_cx.md):
  1. REST snapshot  GET {base}/api/v3/depth?symbol=<S>&limit=1000
     base tried in order: https://data-api.binance.vision, https://api.binance.com
  2. WS combined stream wss://stream.binance.com:9443/stream?streams=
        btcusdt@depth@100ms/ethusdt@depth@100ms
  3. Sequence verification per Binance docs: buffer pre-snapshot events;
     first applied event must satisfy U <= lastUpdateId <= u;
     thereafter require event.U == prev_u + 1 and event.pu == prev_u.
     Count and log every gap / pu violation. On reconnect: re-snapshot.
  4. Bounded: ONE window (default 600 s), raw file <= 200 MB, REST <= 30
     requests, sequential REST with >= 1 s spacing. Keyless only.

Outputs (outside git):
  <outdir>/l2_events_<LABEL>_<ts>.ndjson      one line per ws event, receive_ns included
  <outdir>/collector_manifest.json            sha256/bytes/start/end UTC + counters
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import time
from datetime import datetime, timezone

import aiohttp

LABEL = "PROSPECTIVE_FROM_2026-09-28"
REST_HOSTS = ["https://data-api.binance.vision", "https://api.binance.com"]
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
STREAMS = "/".join(s.lower() + "@depth@100ms" for s in SYMBOLS)
WS_URL = "wss://stream.binance.com:9443/stream?streams=" + STREAMS

MIN_FREE_BYTES = 5 * 1024**3
MAX_RAW_BYTES = 200 * 1024 * 1024
MAX_REST_REQUESTS = 30
REST_MIN_SPACING_S = 1.0
RECONNECT_BACKOFF_S = 2.0
WS_HEARTBEAT_S = 20.0

TERMS = {
    "rest_spec": "https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/rest-api.md",
    "ws_spec": "https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/web-socket-streams.md",
    "ruling": (
        "Official Binance spec: 'For APIs that only send public market data, please use "
        "the base endpoint https://data-api.binance.vision'; security NONE = 'Public market "
        "data' (no key); HTTP 429 on rate-limit breach; limits are per IP. Keyless public "
        "market data used within documented rate limits; no account, no API key."
    ),
    "screened_at_utc": None,  # filled at runtime
}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def df_free_bytes(path: str) -> int:
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class RestBudget:
    def __init__(self, max_requests: int):
        self.max = max_requests
        self.used = 0
        self.last_call_monotonic = 0.0
        self.log: list[dict] = []

    async def get_json(self, session: aiohttp.ClientSession, url: str, note: str) -> dict:
        if self.used >= self.max:
            raise RuntimeError(f"REST budget exhausted ({self.max}) before {note}")
        wait = REST_MIN_SPACING_S - (time.monotonic() - self.last_call_monotonic)
        if wait > 0:
            await asyncio.sleep(wait)
        t0 = time.monotonic()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            body = await resp.text()
            dt_ms = (time.monotonic() - t0) * 1000.0
            self.used += 1
            self.last_call_monotonic = time.monotonic()
            self.log.append(
                {
                    "note": note,
                    "url": url,
                    "http_status": resp.status,
                    "latency_ms": round(dt_ms, 1),
                    "used_of_max": self.used,
                    "receive_utc": utcnow_iso(),
                }
            )
            if resp.status != 200:
                raise RuntimeError(f"{note}: HTTP {resp.status}: {body[:200]}")
            return json.loads(body)


class SymbolState:
    """Per-symbol sequence verification state (Binance diff-depth rules)."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.last_update_id: int | None = None  # snapshot lastUpdateId
        self.prev_u: int | None = None
        self.synced = False
        self.events_received = 0
        self.events_dropped_pre_snapshot = 0
        self.events_dropped_stale = 0
        self.seq_gaps = 0  # U != prev_u + 1
        self.pu_violations = 0  # pu != prev_u (only checked when a pu field is present)
        self.pu_events_seen = 0  # spot payloads carry NO pu field (futures-only field)
        self.first_event_sync_ok: bool | None = None
        self.gap_details: list[dict] = []
        self.latencies_ms: list[int] = []
        self.snapshots: list[dict] = []

    def feed_snapshot(self, snap: dict, meta: dict):
        self.last_update_id = snap["lastUpdateId"]
        self.prev_u = None
        self.synced = False
        bids = snap.get("bids") or []
        asks = snap.get("asks") or []
        tob = {
            "best_bid": bids[0] if bids else None,
            "best_ask": asks[0] if asks else None,
            "n_bid_levels": len(bids),
            "n_ask_levels": len(asks),
        }
        self.snapshots.append({"meta": meta, "lastUpdateId": self.last_update_id, "top_of_book": tob})

    def feed_event(self, ev: dict) -> str:
        """Apply Binance diff rules; return disposition string. Never mutates raw logging."""
        self.events_received += 1
        U, u, pu = ev.get("U"), ev.get("u"), ev.get("pu")
        if U is None or u is None:
            return "malformed"
        lat_ms = int(max(0, time.time() * 1000.0 - float(ev.get("E", time.time() * 1000.0))))
        self.latencies_ms.append(lat_ms)
        if not self.synced:
            if self.last_update_id is None:
                self.events_dropped_pre_snapshot += 1
                return "dropped_pre_snapshot"
            if u <= self.last_update_id:
                self.events_dropped_stale += 1
                return "dropped_stale"
            if not (U <= self.last_update_id + 1 and u >= self.last_update_id + 1):
                # official rule: first processed event needs U <= lastUpdateId+1 <= u
                self.first_event_sync_ok = False
                self.synced = True
                self.prev_u = u
                return "resync_first_event_desync"
            self.first_event_sync_ok = True
            self.synced = True
            self.prev_u = u
            return "applied_first"
        disp = "applied"
        if pu is not None:
            self.pu_events_seen += 1
            if pu != self.prev_u:
                self.pu_violations += 1
                disp = "pu_violation"
        if U != (self.prev_u or 0) + 1:
            self.seq_gaps += 1
            disp = "seq_gap"
            if len(self.gap_details) < 10:
                self.gap_details.append(
                    {
                        "expected_U": (self.prev_u or 0) + 1,
                        "got_U": U,
                        "got_u": u,
                        "got_pu": pu,
                        "E": ev.get("E"),
                    }
                )
        self.prev_u = u
        return disp


async def run(args) -> int:
    outdir = os.path.abspath(os.path.expanduser(args.outdir))
    os.makedirs(outdir, exist_ok=True)

    checks: dict = {}
    free = df_free_bytes(outdir)
    checks["df_free_bytes"] = free
    checks["df_free_gib"] = round(free / 1024**3, 2)
    checks["df_floor_bytes"] = MIN_FREE_BYTES
    if free < MIN_FREE_BYTES:
        print(f"ABORT: only {checks['df_free_gib']} GiB free (<5 GiB floor)")
        return 2
    print(f"df check OK: {checks['df_free_gib']} GiB free")

    TERMS["screened_at_utc"] = utcnow_iso()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_path = os.path.join(outdir, f"l2_events_{LABEL}_{ts}.ndjson")

    states = {s: SymbolState(s) for s in SYMBOLS}
    budget = RestBudget(MAX_REST_REQUESTS)
    stats = {
        "label": LABEL,
        "symbols": SYMBOLS,
        "ws_url": WS_URL,
        "window_seconds": args.window,
        "start_utc": None,
        "end_utc": None,
        "reconnects": 0,
        "ws_connect_failures": 0,
        "events_total": 0,
        "dispositions": {},
        "raw_bytes_written": 0,
        "size_cap_hit": False,
        "rest_log": budget.log,
        "checks": checks,
        "terms": TERMS,
        "stop_reason": None,
    }

    timeout = aiohttp.ClientTimeout(total=None, sock_connect=15, sock_read=args.window + 120)
    connector = aiohttp.TCPConnector(limit=4)
    deadline = time.monotonic() + args.window

    def disposition(disp: str):
        stats["dispositions"][disp] = stats["dispositions"].get(disp, 0) + 1

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # Connect WS first so buffered events bridge the snapshot gap.
        try:
            ws = await session.ws_connect(
                WS_URL, heartbeat=WS_HEARTBEAT_S, receive_timeout=None, max_msg_size=0
            )
        except Exception as exc:  # noqa: BLE001
            stats["stop_reason"] = f"WS_CONNECT_FAILED: {type(exc).__name__}: {exc}"
            stats["ws_connect_failures"] += 1
            stats["end_utc"] = utcnow_iso()
            write_manifest(raw_path, stats, states, args)
            print("FATAL:", stats["stop_reason"])
            return 3

        raw_f = open(raw_path, "ab", buffering=0)
        meta_line = {
            "label": LABEL,
            "kind": "meta",
            "note": "Binance spot combined depth@100ms diff stream, keyless; from-today PROSPECTIVE sample",
            "symbols": SYMBOLS,
            "ws_url": WS_URL,
            "started_utc": utcnow_iso(),
        }
        nb = raw_f.write((json.dumps(meta_line, separators=(",", ":")) + "\n").encode())
        stats["raw_bytes_written"] += nb
        stats["start_utc"] = meta_line["started_utc"]

        # Buffered events taken before their symbol snapshot exists.
        pending: dict[str, list[dict]] = {s: [] for s in SYMBOLS}
        snapshot_done = {s: False for s in SYMBOLS}
        current_ws = ws

        async def take_snapshots():
            """Sequential REST snapshots, >=1 s spacing via RestBudget."""
            for sym in SYMBOLS:
                if snapshot_done[sym]:
                    continue
                got = False
                for host in REST_HOSTS:
                    url = f"{host}/api/v3/depth?symbol={sym}&limit=1000"
                    try:
                        snap = await budget.get_json(session, url, f"snapshot_{sym}")
                    except Exception as exc:  # noqa: BLE001
                        print(f"snapshot {sym} via {host} failed: {exc}")
                        continue
                    meta = {"host": host, "receive_utc": utcnow_iso()}
                    states[sym].feed_snapshot(snap, meta)
                    snapshot_done[sym] = True
                    got = True
                    print(
                        f"snapshot {sym}: lastUpdateId={snap['lastUpdateId']} "
                        f"levels={len(snap.get('bids', []))}b/{len(snap.get('asks', []))}a"
                    )
                    break
                if not got:
                    stats["stop_reason"] = f"SNAPSHOT_FAILED: {sym}"
                await asyncio.sleep(0)  # spacing enforced by RestBudget

        # Initial snapshots right after WS connect (events stream in and buffer meanwhile).
        await take_snapshots()

        try:
            while time.monotonic() < deadline and stats["stop_reason"] is None:
                remaining = deadline - time.monotonic()
                try:
                    msg = await asyncio.wait_for(current_ws.receive(), timeout=min(remaining, 5.0))
                except asyncio.TimeoutError:
                    continue
                except Exception as exc:  # noqa: BLE001
                    msg = None
                    err = f"WS_RECEIVE_ERROR: {type(exc).__name__}: {exc}"
                else:
                    err = None

                if err is not None or msg.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.ERROR,
                    aiohttp.WSMsgType.CLOSE,
                ):
                    if time.monotonic() >= deadline or budget.used >= MAX_REST_REQUESTS:
                        stats["stop_reason"] = "STOP_AT_BOUNDARY_ON_DISCONNECT"
                        break
                    stats["reconnects"] += 1
                    print(f"[{utcnow_iso()}] ws down ({err or msg}); reconnecting...")
                    try:
                        await current_ws.close()
                    except Exception:  # noqa: BLE001
                        pass
                    await asyncio.sleep(RECONNECT_BACKOFF_S)
                    try:
                        current_ws = await session.ws_connect(
                            WS_URL, heartbeat=WS_HEARTBEAT_S, receive_timeout=None, max_msg_size=0
                        )
                    except Exception as exc:  # noqa: BLE001
                        stats["ws_connect_failures"] += 1
                        stats["stop_reason"] = f"RECONNECT_FAILED: {type(exc).__name__}: {exc}"
                        break
                    # Re-snapshot every symbol after reconnect (REST budget permitting).
                    snapshot_done = {s: False for s in SYMBOLS}
                    pending = {s: [] for s in SYMBOLS}
                    await take_snapshots()
                    continue

                if msg.type != aiohttp.WSMsgType.TEXT:
                    continue

                recv_ns = time.time_ns()
                recv_ms = recv_ns // 1_000_000
                try:
                    payload = json.loads(msg.data)
                except json.JSONDecodeError:
                    disposition("json_error")
                    continue

                data = payload.get("data", payload)
                stream = payload.get("stream", "raw")
                if not isinstance(data, dict) or "e" not in data:
                    continue
                sym = data.get("s", "")
                st = states.get(sym)
                if st is None:
                    continue

                # Raw line first: raw evidence is preserved regardless of verification outcome.
                line = {
                    "label": LABEL,
                    "receive_ns": recv_ns,
                    "stream": stream,
                    "U": data.get("U"),
                    "u": data.get("u"),
                    "pu": data.get("pu"),
                    "E": data.get("E"),
                    "bids": data.get("b"),
                    "asks": data.get("a"),
                }
                blob = (json.dumps(line, separators=(",", ":")) + "\n").encode()
                if stats["raw_bytes_written"] + len(blob) > MAX_RAW_BYTES:
                    stats["size_cap_hit"] = True
                    stats["stop_reason"] = "SIZE_CAP_200MB"
                    break
                raw_f.write(blob)
                stats["raw_bytes_written"] += len(blob)
                stats["events_total"] += 1

                if not snapshot_done[sym]:
                    pending[sym].append(data)
                    if len(pending[sym]) > 5000:  # snapshot long overdue
                        stats["stop_reason"] = f"SNAPSHOT_TIMEOUT_BUFFER_OVERFLOW_{sym}"
                    continue

                for ev in pending[sym] + [data]:
                    disp = st.feed_event(ev)
                    disposition(disp)
                pending[sym].clear()
        finally:
            raw_f.close()
            try:
                await current_ws.close()
            except Exception:  # noqa: BLE001
                pass

    stats["end_utc"] = utcnow_iso()
    if stats["stop_reason"] is None:
        stats["stop_reason"] = "WINDOW_COMPLETE"

    write_manifest(raw_path, stats, states, args)
    summary = {
        "events_total": stats["events_total"],
        "reconnects": stats["reconnects"],
        "raw_bytes": stats["raw_bytes_written"],
        "raw_file": raw_path,
        "per_symbol": {
            s: {
                "received": st.events_received,
                "seq_gaps": st.seq_gaps,
                "pu_violations": st.pu_violations,
                "pu_events_seen": st.pu_events_seen,
                "dropped_pre_snapshot": st.events_dropped_pre_snapshot,
                "dropped_stale": st.events_dropped_stale,
                "first_event_sync_ok": st.first_event_sync_ok,
                "snapshots": st.snapshots,
            }
            for s, st in states.items()
        },
        "dispositions": stats["dispositions"],
        "stop_reason": stats["stop_reason"],
        "rest_used": budget.used,
    }
    print(json.dumps(summary, indent=2))
    return 0


def write_manifest(raw_path: str, stats: dict, states: dict, args) -> None:
    outdir = os.path.dirname(raw_path)
    entry = {
        "file": os.path.basename(raw_path),
        "bytes": os.path.getsize(raw_path) if os.path.exists(raw_path) else 0,
        "sha256": sha256_of_file(raw_path) if os.path.exists(raw_path) else None,
    }
    manifest = {
        "label": LABEL,
        "kind": "collector_manifest",
        "law": (
            "PROSPECTIVE_FROM_2026-09-28: from-today sample, NOT historical data. "
            "No order-book/forced-flow inference from candles; not backtestable history."
        ),
        "collector": "collect_binance_l2.py",
        "config": {
            "window_seconds": args.window,
            "symbols": SYMBOLS,
            "rest_hosts": REST_HOSTS,
            "ws_url": WS_URL,
            "max_raw_bytes": MAX_RAW_BYTES,
            "max_rest_requests": MAX_REST_REQUESTS,
            "rest_min_spacing_s": REST_MIN_SPACING_S,
        },
        "start_utc": stats["start_utc"],
        "end_utc": stats["end_utc"],
        "stop_reason": stats["stop_reason"],
        "files": [entry],
        "stats": stats,
        "sequence_verification": {
            s: {
                "events_received": st.events_received,
                "seq_gaps": st.seq_gaps,
                "pu_violations": st.pu_violations,
                "pu_events_seen": st.pu_events_seen,
                "dropped_pre_snapshot": st.events_dropped_pre_snapshot,
                "dropped_stale": st.events_dropped_stale,
                "first_event_sync_ok": st.first_event_sync_ok,
                "gap_details": st.gap_details,
                "latency_ms": {
                    "n": len(st.latencies_ms),
                    "p50": sorted(st.latencies_ms)[len(st.latencies_ms) // 2] if st.latencies_ms else None,
                    "p95": sorted(st.latencies_ms)[int(len(st.latencies_ms) * 0.95)] if st.latencies_ms else None,
                    "max": max(st.latencies_ms) if st.latencies_ms else None,
                },
                "snapshots": st.snapshots,
            }
            for s, st in states.items()
        },
        "written_utc": utcnow_iso(),
    }
    mpath = os.path.join(outdir, "collector_manifest.json")
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"manifest written: {mpath}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--outdir",
        default=os.path.expanduser("~/.my-quantitative-data/sixsource-foundation-v1/crypto_l2"),
    )
    ap.add_argument("--window", type=int, default=600, help="bounded session seconds (ONE window)")
    args = ap.parse_args()
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        print("interrupted — partial files remain; manifest may be stale")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
