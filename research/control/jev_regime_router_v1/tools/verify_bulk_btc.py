#!/usr/bin/env python3
"""JRV1 post-bulk verification — BTCUSDT leg (run AFTER replay completes).

Checks completeness + cache integrity against the frozen fold contract,
then freezes the response manifest (digests + label/confidence/error stats)
as the pre-A7-2 evidence artifact. Read-only w.r.t. decisions/cache.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import statistics
import sys
from datetime import datetime, timezone

REPO = pathlib.Path("/Users/hoangminhlong/my-quantitative")
CYCLE = REPO / ".worktrees/jev-regime-router-v1/integration/research/control/jev_regime_router_v1"
sys.path.insert(0, str(CYCLE))


def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    from jrv1 import freezes as fz
    from jrv1.features import build_states  # noqa: F401 (import check)

    fold = fz.load_freeze("fold_contract.json")["BTCUSDT"]
    expected = fold["evaluable_decisions"]

    dec_path = CYCLE / "runtime/replay/btcusdt/decisions_btcusdt.jsonl"
    lines = [json.loads(l) for l in dec_path.open()] if dec_path.exists() else []
    n = len(lines)

    # completeness: every evaluable state exactly once
    states = fz.load_states("btcusdt") if hasattr(fz, "load_states") else None
    ids = [d["state_id"] for d in lines]
    dup = len(ids) - len(set(ids))

    # schema + stats
    ok = [d for d in lines if d.get("status") == "OK"]
    by_status: dict[str, int] = {}
    labels: dict[str, int] = {}
    confs = []
    for d in lines:
        by_status[d.get("status", "?")] = by_status.get(d.get("status", "?"), 0) + 1
        if d.get("status") == "OK":
            labels[d["regime"]] = labels.get(d["regime"], 0) + 1
            confs.append(d.get("confidence", 0.0))
    schema_err = by_status.get("SCHEMA_ERROR", 0)
    prov_err = by_status.get("PROVIDER_ERROR", 0) + by_status.get("TIMEOUT", 0)

    # cache integrity: entry per live decision, digests match
    cache_dir = CYCLE / "runtime/replay/btcusdt/adapter_cache"
    cache_entries = list(cache_dir.glob("*.json")) if cache_dir.exists() else []
    cache_by_state: dict[str, dict] = {}
    for cf in cache_entries:
        e = json.loads(cf.read_text())
        cache_by_state.setdefault(e["state_id"], e)
    digest_match = sum(
        1 for d in lines
        if d["state_id"] in cache_by_state
        and cache_by_state[d["state_id"]].get("input_digest") == d.get("input_digest")
    )

    manifest = {
        "schema": "jrv1_bulk_response_manifest@1",
        "asset": "btcusdt",
        "frozen_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expected_decisions": expected,
        "observed_decisions": n,
        "duplicate_state_ids": dup,
        "completeness_ok": n == expected and dup == 0,
        "status_counts": by_status,
        "raw_label_distribution": labels,
        "confidence": {
            "median": round(statistics.median(confs), 4) if confs else None,
            "share_ge_050": round(sum(c >= 0.50 for c in confs) / len(confs), 4) if confs else None,
        },
        "schema_error_share": round(schema_err / n, 4) if n else None,
        "provider_error_share": round(prov_err / n, 4) if n else None,
        "cache_entries": len(cache_entries),
        "cache_digest_matches": digest_match,
        "cache_integrity_ok": len(cache_entries) >= n and digest_match == n,
        "decisions_sha256": sha256_file(dec_path) if dec_path.exists() else None,
        "model_pin": fz.load_freeze("model_pin.json")["pinned_model"],
        "notes": [
            "canary 94 states included via cache (prompt V1 keys)",
            "SCHEMA_ERROR/PROVIDER_ERROR map to TRANSITION_UNKNOWN per frozen law (no retry)",
        ],
    }
    out = CYCLE / "runtime/replay/btcusdt/bulk_response_manifest.json"
    out.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=1, sort_keys=True))
    ok_all = manifest["completeness_ok"] and manifest["cache_integrity_ok"]
    print("VERDICT:", "BULK_VERIFIED" if ok_all else "BULK_INCOMPLETE_FAIL_CLOSED")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
