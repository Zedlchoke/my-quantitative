"""LIVE-DATA-GATEWAY-V1 lifecycle CLI (plan §13).

    python -m research.live_gateway start   [--port N] [--config P] [--runtime-root R]
    python -m research.live_gateway stop
    python -m research.live_gateway status
    python -m research.live_gateway serve   (internal: run in foreground)

start daemonizes via a detached child (nohup-equivalent: start_new_session),
writes snapshot/pid.json, refuses when already alive. stop sends SIGTERM
and waits <=10 s for a clean-shutdown heartbeat. status prints a short
canonical summary from the heartbeat (STALE when >30 s old).
No sudo, no login startup, no credentials — ever.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from typing import Optional

from .config import GatewayConfig
from .persistence import read_json
from .timeutils import default_now_ms, ms_to_iso_z

STOP_WAIT_S = 10.0
STATUS_STALE_AFTER_S = 30.0


def _pid_path(config: GatewayConfig) -> str:
    return config.runtime_dir("snapshot", "pid.json")


def _heartbeat_path(config: GatewayConfig) -> str:
    return config.runtime_dir("snapshot", "heartbeat.json")


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def cmd_start(args: argparse.Namespace) -> int:
    config = GatewayConfig.load(args.config)
    if args.port:
        config.port = args.port
    if args.runtime_root:
        config.runtime_root = args.runtime_root
    os.makedirs(config.runtime_dir("snapshot"), exist_ok=True)
    pid_file = _pid_path(config)
    existing = read_json(pid_file)
    if existing and isinstance(existing.get("pid"), int):
        if _pid_alive(existing["pid"]):
            print(
                f"REFUSING: gateway already running pid {existing['pid']} "
                f"(heartbeat {_heartbeat_path(config)})"
            )
            return 2
    log_dir = config.runtime_root
    console_log = os.path.join(log_dir, "gateway.console.log")
    env = dict(os.environ)
    env["LDGV_PORT"] = str(config.port)
    env["LDGV_RUNTIME_ROOT"] = config.runtime_root
    env["LDGV_CONFIG"] = args.config or ""
    child = subprocess.Popen(
        [
            sys.executable, "-m", "research.live_gateway", "serve",
            "--port", str(config.port),
            "--runtime-root", config.runtime_root,
        ]
        + (["--config", args.config] if args.config else []),
        stdout=open(console_log, "ab"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
        cwd=os.getcwd(),
    )
    with open(pid_file, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "pid": child.pid,
                "started_utc": ms_to_iso_z(default_now_ms()),
                "port": config.port,
            },
            handle,
        )
    print(
        f"STARTED pid {child.pid} on {config.bind}:{config.port}; "
        f"console log {console_log}"
    )
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    config = GatewayConfig.load(args.config)
    if args.runtime_root:
        config.runtime_root = args.runtime_root
    pid_file = _pid_path(config)
    data = read_json(pid_file)
    if not data or not isinstance(data.get("pid"), int):
        print("NOT RUNNING (no pid file)")
        return 1
    pid = data["pid"]
    if not _pid_alive(pid):
        print(f"NOT RUNNING (pid {pid} dead; stale pid file)")
        os.remove(pid_file)
        return 1
    os.kill(pid, signal.SIGTERM)
    deadline = time.time() + STOP_WAIT_S
    clean = False
    while time.time() < deadline:
        if not _pid_alive(pid):
            hb = read_json(_heartbeat_path(config)) or {}
            clean = bool(hb.get("shutdown_clean"))
            break
        time.sleep(0.2)
    if _pid_alive(pid):
        print(f"STOP TIMED OUT after {STOP_WAIT_S}s (pid {pid} still alive)")
        return 3
    verdict = "CLEAN" if clean else "UNCLEAN (no clean-shutdown heartbeat)"
    print(f"STOPPED pid {pid} — {verdict}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    config = GatewayConfig.load(args.config)
    if args.runtime_root:
        config.runtime_root = args.runtime_root
    pid_file = _pid_path(config)
    hb = read_json(_heartbeat_path(config)) or {}
    pid_data = read_json(pid_file) or {}
    pid = pid_data.get("pid")
    alive = isinstance(pid, int) and _pid_alive(pid)
    age_s: Optional[float] = None
    if isinstance(hb.get("now_utc"), str):
        try:
            from .timeutils import iso_z_to_ms

            age_s = max(0.0, (default_now_ms() - iso_z_to_ms(hb["now_utc"])) / 1000.0)
        except ValueError:
            age_s = None
    state = (
        "OFFLINE" if not alive
        else ("STALE" if (age_s is None or age_s > STATUS_STALE_AFTER_S) else "LIVE")
    )
    ws = (hb.get("ws") or {}) if isinstance(hb, dict) else {}
    rest_breaker = (hb.get("rest_breaker") or {}) if isinstance(hb, dict) else {}
    fanout = (hb.get("fanout") or {}) if isinstance(hb, dict) else {}
    rest = (hb.get("rest") or {}) if isinstance(hb, dict) else {}
    print(f"LIVE-DATA-GATEWAY-V1 status: {state}")
    print(f"  pid: {pid} alive={alive} heartbeat_age_s={age_s}")
    print(f"  uptime_s: {hb.get('uptime_s')}  version: {hb.get('version')}")
    print(
        f"  ws: state={ws.get('state')} reconnects={ws.get('reconnect_count')} "
        f"last_msg={ws.get('last_message_utc')} symbols={ws.get('subscribed_symbols')}"
    )
    print(
        f"  rest breaker: {rest_breaker.get('state')}  "
        f"suppressed={rest_breaker.get('suppressed_during_open')}  "
        f"allowed_retry_at={rest_breaker.get('allowed_retry_at_utc')}"
    )
    print(
        f"  rest upstream calls: {rest.get('upstream_calls')}  "
        f"cache hits/misses: {(rest.get('cache') or {}).get('hits')}/"
        f"{(rest.get('cache') or {}).get('misses')}  "
        f"coalesced suppressed: {rest.get('coalescer_suppressed')}"
    )
    print(
        f"  consumers: {len(fanout.get('connected_consumers') or [])}  "
        f"dropped slow: {fanout.get('dropped_slow_consumers')}  "
        f"seq: {fanout.get('seq')}"
    )
    print(f"  stale symbols: {hb.get('stale_symbols')}")
    print(
        f"  disk raw/cache bytes: {(hb.get('disk') or {}).get('raw_bytes')}/"
        f"{(hb.get('disk') or {}).get('cache_bytes')}"
    )
    print(f"  shutdown_clean: {hb.get('shutdown_clean')}")
    return 0 if state == "LIVE" else 1


def cmd_serve(args: argparse.Namespace) -> int:
    from .service import run_service

    config = GatewayConfig.load(args.config)
    if args.port:
        config.port = args.port
    if args.runtime_root:
        config.runtime_root = args.runtime_root
    asyncio.run(run_service(config))
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="research.live_gateway")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("start", "serve"):
        p = sub.add_parser(name)
        p.add_argument("--port", type=int, default=0)
        p.add_argument("--config", default=None)
        p.add_argument("--runtime-root", default=None)
    p_stop = sub.add_parser("stop")
    p_stop.add_argument("--config", default=None)
    p_stop.add_argument("--runtime-root", default=None)
    p_status = sub.add_parser("status")
    p_status.add_argument("--config", default=None)
    p_status.add_argument("--runtime-root", default=None)
    args = parser.parse_args(argv)
    return {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "serve": cmd_serve,
    }[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
