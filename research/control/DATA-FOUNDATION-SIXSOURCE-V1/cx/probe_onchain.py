#!/usr/bin/env python3
"""Bounded on-chain probe (Ethereum mainnet) — lane CX, DATA-FOUNDATION-SIXSOURCE-V1.

PROSPECTIVE_FROM_2026-09-28 — AS-OF-NOW chain state, NOT historical data.

Anti-retroactive labeling law (binding on any consumer of this artifact):
  Every block number, timestamp, balance or state read here is AS-OF-NOW
  state at the receive timestamp recorded per call. It is never point-in-time
  (PIT) history. This session performs NO wallet/address labeling and NO
  historical balance reconstruction. Any later use that back-dates these
  reads to earlier timestamps is prohibited by this law.

Provider screens (recorded BEFORE first data call):
  A) https://ethereum-rpc.publicnode.com — PublicNode self-describes as
     "Fastest, free-est, and privacy first RPC endpoints for 77 blockchains"
     (https://www.publicnode.com/); keyless public good. VERIFIED.
  B) https://cloudflare-eth.com — Cloudflare public Ethereum gateway;
     keyless HTTP 200 with no auth demand on screening call; the former
     Distributed Web Gateway docs page no longer documents the service
     (moved). Basis recorded with that disclosure; usage limited to 3 light
     read-only calls.
  Screened OUT: https://eth.llamarpc.com — homepage HTTP 526, endpoint
  unreachable; basis unverifiable -> not used (BLOCKED_LICENSE_VERIFY).

Budget: <=8 JSON-RPC calls total across <=2 providers (this probe: 6) + 1
keyless explorer call (blockscout). Sequential, >=1 s spacing.

Calls per provider: eth_blockNumber; eth_getBlockByNumber("latest", false);
eth_getBlockByNumber("finalized", false).

Output (outside git): <outdir>/onchain_probe_<ts>.json + manifest (sha256).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone

import requests

LABEL = "PROSPECTIVE_FROM_2026-09-28"
PROVIDERS = [
    ("publicnode", "https://ethereum-rpc.publicnode.com"),
    ("cloudflare", "https://cloudflare-eth.com"),
]
EXPLORER = ("blockscout", "https://eth.blockscout.com/api/v2/blocks/latest")
MAX_RPC_CALLS = 8
MIN_SPACING_S = 1.0
MIN_FREE_BYTES = 5 * 1024**3


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def df_free_bytes(path: str) -> int:
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize


def hex_to_int(h):
    try:
        return int(h, 16) if isinstance(h, str) else h
    except (TypeError, ValueError):
        return None


class Budget:
    def __init__(self, max_calls: int):
        self.max = max_calls
        self.used = 0
        self.last = 0.0

    def wait_spacing(self):
        wait = MIN_SPACING_S - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)


def rpc_call(budget: Budget, provider: str, url: str, method: str, params: list) -> dict:
    if budget.used >= MAX_RPC_CALLS:
        raise RuntimeError(f"RPC cap {MAX_RPC_CALLS} reached")
    budget.wait_spacing()
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    t0 = time.monotonic()
    try:
        resp = requests.post(url, json=payload, timeout=20)
        dt = (time.monotonic() - t0) * 1000.0
        budget.used += 1
        budget.last = time.monotonic()
        body = resp.json()
        record = {
            "provider": provider,
            "method": method,
            "params": params,
            "http_status": resp.status_code,
            "latency_ms": round(dt, 1),
            "receive_utc": utcnow_iso(),
            "jsonrpc_id": body.get("id"),
            "error": body.get("error"),
            "result": body.get("result"),
        }
    except Exception as exc:  # noqa: BLE001
        dt = (time.monotonic() - t0) * 1000.0
        budget.used += 1
        budget.last = time.monotonic()
        record = {
            "provider": provider,
            "method": method,
            "params": params,
            "http_status": None,
            "latency_ms": round(dt, 1),
            "receive_utc": utcnow_iso(),
            "error": f"{type(exc).__name__}: {exc}",
            "result": None,
        }
    print(f"[rpc {budget.used:02d}] {provider:10s} {method:28s} {record['latency_ms']:>8}ms "
          f"status={record['http_status']}")
    return record


def block_fields(result: dict | None) -> dict | None:
    if not isinstance(result, dict):
        return None
    return {
        "number_hex": result.get("number"),
        "number": hex_to_int(result.get("number")),
        "hash": result.get("hash"),
        "parentHash": result.get("parentHash"),
        "timestamp_hex": result.get("timestamp"),
        "timestamp_unix": hex_to_int(result.get("timestamp")),
        "timestamp_iso_utc": (
            datetime.fromtimestamp(hex_to_int(result.get("timestamp")), timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            if hex_to_int(result.get("timestamp"))
            else None
        ),
        "baseFeePerGas_hex": result.get("baseFeePerGas"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--outdir",
        default=os.path.expanduser("~/.my-quantitative-data/sixsource-foundation-v1/onchain"),
    )
    args = ap.parse_args()
    outdir = os.path.abspath(os.path.expanduser(args.outdir))
    os.makedirs(outdir, exist_ok=True)

    free = df_free_bytes(outdir)
    if free < MIN_FREE_BYTES:
        print(f"ABORT: df below floor ({free/1024**3:.2f} GiB free)")
        return 2
    print(f"df check OK: {free/1024**3:.2f} GiB free")

    budget = Budget(MAX_RPC_CALLS)
    doc = {
        "label": LABEL,
        "kind": "onchain_probe",
        "law": __doc__.split("Anti-retroactive labeling law")[1].split('"""')[0].strip(),
        "df_free_gib": round(free / 1024**3, 2),
        "provider_screens": {
            "publicnode": "VERIFIED — publicnode.com: 'Fastest, free-est, and privacy first "
                          "RPC endpoints for 77 blockchains'; keyless public good.",
            "cloudflare": "BASIS RECORDED WITH DISCLOSURE — cloudflare-eth.com responded "
                          "keyless HTTP 200, no auth demand; current Cloudflare docs page no "
                          "longer documents the gateway (moved). 3 light read-only calls only.",
            "llamarpc": "SCREENED OUT — homepage HTTP 526, endpoint unreachable; basis "
                        "unverifiable (BLOCKED_LICENSE_VERIFY); not used.",
        },
        "started_utc": utcnow_iso(),
        "calls": [],
        "explorer": None,
        "derived": {},
        "ended_utc": None,
        "stop_reason": None,
    }

    try:
        for name, url in PROVIDERS:
            r1 = rpc_call(budget, name, url, "eth_blockNumber", [])
            r2 = rpc_call(budget, name, url, "eth_getBlockByNumber", ["latest", False])
            r3 = rpc_call(budget, name, url, "eth_getBlockByNumber", ["finalized", False])
            doc["calls"] += [r1, r2, r3]

        # one keyless explorer/indexer call
        budget.wait_spacing()
        t0 = time.monotonic()
        try:
            resp = requests.get(EXPLORER[1], timeout=20)
            dt = (time.monotonic() - t0) * 1000.0
            try:
                body = resp.json()
            except ValueError:
                body = {"raw_prefix": resp.text[:300]}
            doc["explorer"] = {
                "provider": EXPLORER[0],
                "url": EXPLORER[1],
                "http_status": resp.status_code,
                "latency_ms": round(dt, 1),
                "receive_utc": utcnow_iso(),
                "body_top_fields": {k: body.get(k) for k in list(body)[:12]} if isinstance(body, dict) else body,
            }
        except Exception as exc:  # noqa: BLE001
            doc["explorer"] = {
                "provider": EXPLORER[0],
                "url": EXPLORER[1],
                "error": f"{type(exc).__name__}: {exc}",
                "receive_utc": utcnow_iso(),
            }
        print(f"[explorer ] {EXPLORER[0]} {EXPLORER[1]} -> {doc['explorer'].get('http_status')}")

        # derived metrics per provider
        derived = {}
        for name, _ in PROVIDERS:
            calls = [c for c in doc["calls"] if c["provider"] == name]
            tip = block_fields(calls[1]["result"] if len(calls) > 1 else None)
            fin = block_fields(calls[2]["result"] if len(calls) > 2 else None)
            head = hex_to_int(calls[0]["result"]) if calls and isinstance(calls[0]["result"], str) else None
            d = {"head_blockNumber": head, "latest": tip, "finalized": fin,
                 "finality_lag_blocks": None, "finality_lag_seconds": None,
                 "finalized_tag_supported": fin is not None}
            if tip and fin and tip["number"] is not None and fin["number"] is not None:
                d["finality_lag_blocks"] = tip["number"] - fin["number"]
                if tip["timestamp_unix"] and fin["timestamp_unix"]:
                    d["finality_lag_seconds"] = tip["timestamp_unix"] - fin["timestamp_unix"]
            derived[name] = d
        doc["derived"] = derived

        # provider disagreement
        pa, pb = derived.get("publicnode", {}), derived.get("cloudflare", {})
        doc["derived"]["provider_disagreement"] = {
            "latest_block_delta": (
                abs((pa.get("latest") or {}).get("number", 0) - (pb.get("latest") or {}).get("number", 0))
                if (pa.get("latest") and pb.get("latest"))
                else None
            ),
            "note": "calls are sequential ~1s apart; small deltas expected from chain progress + timing skew",
        }
    except Exception as exc:  # noqa: BLE001
        doc["stop_reason"] = f"ERROR: {type(exc).__name__}: {exc}"
        print("ERROR:", exc)

    doc["ended_utc"] = utcnow_iso()
    doc["rpc_calls_used"] = budget.used
    doc["rpc_calls_cap"] = MAX_RPC_CALLS

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join(outdir, f"onchain_probe_{ts}.json")
    with open(out_path, "w") as f:
        json.dump(doc, f, indent=2)
    manifest = {
        "label": LABEL,
        "kind": "manifest",
        "files": [{"file": os.path.basename(out_path), "bytes": os.path.getsize(out_path),
                   "sha256": sha256_of_file(out_path)}],
        "rpc_calls_used": budget.used,
        "written_utc": utcnow_iso(),
    }
    with open(os.path.join(outdir, "onchain_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("written:", out_path)

    for name, d in derived.items():
        print(f"  {name}: latest={d.get('latest') and d['latest']['number']} "
              f"finalized={d.get('finalized') and d['finalized']['number']} "
              f"lag_blocks={d.get('finality_lag_blocks')} lag_s={d.get('finality_lag_seconds')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
