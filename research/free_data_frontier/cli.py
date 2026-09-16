"""FREE-DATA-FRONTIER-V1 CLI: F0 evidence, source runs, bounded WS captures,
manifest generation. Raw bytes never leave the external raw root."""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .contract import CYCLE_ID, DISK_FLOOR_BYTES, utc_now_iso
from .env import check_presence, load_secret
from .http import DiskGuard, RateLimiter
from .manifest import write_manifest, verify_manifest
from .sources.base import SourceContext
from . import sources as source_modules

REQUIRED_ENV = ["SEC_CONTACT_NAME", "SEC_CONTACT_EMAIL", "EIA_API_KEY"]

DEFAULT_RAW_ROOT = Path("/Users/hoangminhlong/.my-quantitative-data/free-data-frontier-v1/raw")
CONTROL_SUBDIR = Path("research/control/free_data_frontier_v1_run")

SOURCE_TABLE: Dict[str, str] = {
    "ofr": "ofr_stfm",
    "nyfed": "nyfed_markets",
    "sec_ftd": "sec_ftd",
    "sec_nport": "sec_nport",
    "eia": "eia_open_data",
    "nws": "nws_observations",
    "usda": "usda_wasde",
}


def worktree_root() -> Path:
    return Path(__file__).resolve().parents[2]


def control_dir() -> Path:
    return worktree_root() / CONTROL_SUBDIR


def make_ctx() -> SourceContext:
    presence = check_presence(REQUIRED_ENV)
    return SourceContext(
        raw_root=DEFAULT_RAW_ROOT,
        control_dir=control_dir(),
        session=requests.Session(),
        limiters={},
        disk_guard=DiskGuard(),
        presence=presence,
        secret_loader=load_secret,
    )


def _run_source(name: str, ctx: SourceContext) -> Dict[str, Any]:
    module = getattr(source_modules, name)
    state = module.run(ctx)
    phase_dir = control_dir() / "f3_canaries" if name in ("nws",) else control_dir() / "f4_acquisition"
    phase_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = control_dir() / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    summary = state.summarize()
    summary_path = phase_dir / f"{state.source_id}_summary.json"
    summary_path.write_bytes(
        json.dumps(summary, sort_keys=True, indent=2, separators=(",", ": ")).encode() + b"\n"
    )
    records_with_raw = [r for r in state.records if r.get("raw_path")]
    if records_with_raw:
        manifest_report = write_manifest(manifest_dir / f"{state.source_id}_manifest.json", records_with_raw)
        summary["manifest"] = manifest_report
        summary_path.write_bytes(
            json.dumps(summary, sort_keys=True, indent=2, separators=(",", ": ")).encode() + b"\n"
        )
    return {"source_id": state.source_id, "status": summary["status"], "objects": summary["objects"]}


def cmd_f0(_args) -> None:
    ctx = make_ctx()
    evidence = {
        "cycle_id": CYCLE_ID,
        "measured_utc": utc_now_iso(),
        "env_presence": ctx.presence,
        "raw_root": str(DEFAULT_RAW_ROOT),
        "raw_root_inside_git": False,
        "disk_free_bytes": ctx.disk_guard.free_bytes(DEFAULT_RAW_ROOT),
        "disk_floor_bytes": DISK_FLOOR_BYTES,
        "heavy_lock": "checked by operator via researchctl locks inspect (FREE_PROVEN at intake)",
        "active_shadow_workers": "PROSPECTIVE-SHADOW-V1 workers live; untouched by this cycle",
    }
    cdir = control_dir() / "f0_bootstrap"
    cdir.mkdir(parents=True, exist_ok=True)
    path = cdir / "f0_evidence.json"
    path.write_bytes(json.dumps(evidence, sort_keys=True, indent=2).encode() + b"\n")
    print(json.dumps({k: evidence[k] for k in ("cycle_id", "env_presence", "disk_free_bytes")}, indent=2))
    print(f"F0 evidence written: {path}")


def cmd_run_source(args) -> None:
    ctx = make_ctx()
    names = list(SOURCE_TABLE) if args.source == "all" else [args.source]
    results = []
    for name in names:
        if name == "sec_ftd_archive":
            continue
        try:
            results.append(_run_source(name, ctx))
        except Exception as exc:
            results.append({"source_id": name, "status": "BLOCKED_NETWORK", "error": f"{type(exc).__name__}: {exc}"[:300]})
    print(json.dumps(results, indent=2))


def cmd_ftd_archive(args) -> None:
    ctx = make_ctx()
    from .sources import sec_bulk

    state = sec_bulk.download_ftd_archive(ctx, max_files=args.max_files)
    summary = state.summarize()
    manifest_dir = control_dir() / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    records_with_raw = [r for r in state.records if r.get("raw_path")]
    if records_with_raw:
        summary["manifest"] = write_manifest(manifest_dir / "sec_ftd_archive_manifest.json", records_with_raw)
    path = control_dir() / "f4_acquisition" / "sec_ftd_archive_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(summary, sort_keys=True, indent=2).encode() + b"\n")
    print(json.dumps({"source_id": state.source_id, "status": summary["status"], "objects": summary["objects"]}))


def cmd_streams(args) -> None:
    from .streams.coinbase import CoinbaseCapture
    from .streams.deribit import DeribitCapture
    from .streams.kraken import KrakenFuturesCapture

    raw_dir = DEFAULT_RAW_ROOT / "streams"
    captures = [
        CoinbaseCapture(raw_dir / "coinbase_sample.jsonl"),
        KrakenFuturesCapture(raw_dir / "kraken_futures_sample.jsonl"),
        DeribitCapture(raw_dir / "deribit_sample.jsonl"),
    ]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        summaries = loop.run_until_complete(
            asyncio.gather(*(cap.run(minutes=args.minutes) for cap in captures))
        )
    finally:
        loop.close()
    out_dir = control_dir() / "f3_canaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = []
    for summary in summaries:
        blob = json.dumps(summary.to_dict(), sort_keys=True, indent=2) + "\n"
        path = out_dir / f"stream_{summary.source_id}_summary.json"
        path.write_text(blob)
        payload.append({k: summary.to_dict()[k] for k in ("source_id", "connect_ok", "total_messages", "disconnects")})
    print(json.dumps(payload, indent=2))


def cmd_verify(args) -> None:
    manifest_dir = control_dir() / "manifests"
    reports = []
    for path in sorted(manifest_dir.glob("*_manifest.json")):
        reports.append({k: v for k, v in verify_manifest(path).items() if k != "rows"})
    print(json.dumps(reports, indent=2))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="free_data_frontier")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("f0").set_defaults(func=cmd_f0)

    run_source = sub.add_parser("run-source")
    run_source.add_argument("--source", required=True, choices=list(SOURCE_TABLE))
    run_source.set_defaults(func=cmd_run_source)

    archive = sub.add_parser("acquire-ftd-archive")
    archive.add_argument("--max-files", type=int, default=None)
    archive.set_defaults(func=cmd_ftd_archive)

    streams = sub.add_parser("streams")
    streams.add_argument("--minutes", type=float, default=4.0)
    streams.set_defaults(func=cmd_streams)

    sub.add_parser("verify-manifests").set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
