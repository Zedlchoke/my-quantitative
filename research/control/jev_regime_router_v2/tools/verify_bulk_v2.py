#!/usr/bin/env python3
"""JRV2 post-bulk verification — all 3 cells (run AFTER the bulk worker exits).

Verifies completeness + cache integrity vs fold_contract, computes the owner's
mandated occupancy/persistence statistics, and freezes per-cell response
manifests. Classification-only (no PnL anywhere). Read-only w.r.t. decisions.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from collections import Counter
from datetime import datetime, timezone

REPO = pathlib.Path("/Users/hoangminhlong/my-quantitative")
CYCLE = REPO / ".worktrees/jev-regime-router-v2/integration/research/control/jev_regime_router_v2"
sys.path.insert(0, str(CYCLE))

CELLS = {
    "BTC_H1": 8567,
    "BTC_H4": 1997,
    "SPY_D1": 2751,
}


def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    from jrv2.freezes import Freezes
    from jrv2.safety import run_persistence

    fz = Freezes(CYCLE)
    params = fz.persistence_params()
    manifests = {}
    all_ok = True

    for cell, expected in CELLS.items():
        d = CYCLE / "runtime" / "replay" / cell
        dec_files = sorted(d.glob("decisions_*.jsonl"))
        lines = []
        for f in dec_files:
            lines.extend(json.loads(l) for l in f.open() if l.strip())
        n = len(lines)
        ids = [x["state_id"] for x in lines]
        dup = len(ids) - len(set(ids))
        from jrv2.safety import effective_from_response
        status = Counter(x.get("status", "?") for x in lines)
        eff_pairs = [effective_from_response(x, params) for x in lines]
        eff = Counter(label for label, _, _ in eff_pairs)
        # persisted timeline: route raw responses through the safety layer
        bars = run_persistence(lines, params)
        persisted = [b.persisted for b in bars]
        pc = Counter(persisted)
        switches = sum(1 for i in range(1, len(persisted)) if persisted[i] != persisted[i - 1])
        # dwell distribution + UNKNOWN runs
        dwell, runs, cur, ln = [], [], persisted[0] if persisted else None, 0
        for p in persisted:
            if p == cur:
                ln += 1
            else:
                dwell.append((cur, ln)); runs.append((cur, ln)); cur, ln = p, 1
        if cur is not None:
            dwell.append((cur, ln)); runs.append((cur, ln))
        unknown_runs = [l for c, l in runs if c == "TRANSITION_UNKNOWN"]
        dw = sorted(l for _, l in dwell)
        # usage from cache
        cache_dir = d / "adapter_cache"
        ti = to = nc = 0
        for cf in cache_dir.glob("*.json"):
            e = json.loads(cf.read_text())
            u = (e.get("response") or {}).get("usage") or {}
            ti += u.get("input_tokens") or 0
            to += u.get("output_tokens") or 0
            nc += 1
        cache_pairs = set()
        for cf in cache_dir.glob("*.json"):
            e = json.loads(cf.read_text())
            cache_pairs.add((e.get("state_id"), e.get("input_digest")))
        digest_match = sum(1 for x in lines if (x.get("state_id"), x.get("input_digest")) in cache_pairs)
        manifest = {
            "schema": "jrv2_bulk_response_manifest@1",
            "cell": cell,
            "frozen_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "expected_decisions": expected,
            "observed_decisions": n,
            "duplicate_state_ids": dup,
            "completeness_ok": n == expected and dup == 0,
            "status_counts": dict(status),
            "effective_label_counts": dict(eff),
            "effective_unknown_share": round(eff.get("TRANSITION_UNKNOWN", 0) / n, 4) if n else None,
            "persisted_counts": dict(pc),
            "persisted_switches": switches,
            "dwell_bars": {"min": dw[0] if dw else None, "p50": dw[len(dw)//2] if dw else None,
                            "p90": dw[int(len(dw)*0.9)] if dw else None, "max": dw[-1] if dw else None},
            "unknown_runs_bars": {"n": len(unknown_runs),
                                   "max_run": max(unknown_runs) if unknown_runs else 0,
                                   "share_of_bars": round(sum(unknown_runs) / n, 4) if n else None},
            "cache_entries": nc,
            "cache_digest_matches": digest_match,
            "cache_integrity_ok": nc >= n and digest_match == n,
            "usage": {"input_tokens": ti, "output_tokens": to, "avg_input_per_call": round(ti / max(nc, 1))},
            "model_pin": fz.model_pin.get("pinned_model"),
            "decisions_sha256": sha256_file(dec_files[0]) if dec_files else None,
        }
        out = d / "bulk_response_manifest.json"
        out.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
        manifests[cell] = manifest
        ok = manifest["completeness_ok"] and manifest["cache_integrity_ok"]
        all_ok &= ok
        print(f"{cell}: n={n}/{expected} dup={dup} status={dict(status)} effUNKNOWN={manifest['effective_unknown_share']} "
              f"switches={switches} maxUnknownRun={manifest['unknown_runs_bars']['max_run']} tokens_in={ti/1e6:.1f}M ok={ok}")

    total_in = sum(m["usage"]["input_tokens"] for m in manifests.values())
    total_out = sum(m["usage"]["output_tokens"] for m in manifests.values())
    print(f"TOTAL bulk usage: {total_in/1e6:.1f}M input + {total_out/1e3:.0f}K output tokens")
    print("VERDICT:", "BULK_VERIFIED" if all_ok else "BULK_INCOMPLETE_FAIL_CLOSED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
