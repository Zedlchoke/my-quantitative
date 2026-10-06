#!/usr/bin/env python3
"""ACQ-SKEPTIC recomputation 01: request accounting, record-size math,
get_cost/list ratio, coverage grid, latest-month, disk snapshot.

Read-only against the ACQ-OPT namespace; writes only this audit namespace.
"""
import json
from collections import Counter
from pathlib import Path

CTRL = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
            "futures-behavior/prep/research/control/"
            "FUTURES-BEHAVIOR-10SYMS-PREP-20261002")
CR = json.loads((CTRL / "acquisition_optimization/coverage_results.json").read_text())

print("=== REQUEST ACCOUNTING ===")
reqs = CR["requests"]
print("request_count field:", CR["request_count"])
print("len(requests):", len(reqs), " len(order):", len(CR["order"]))
statuses = Counter(r.get("http_status") for r in reqs.values())
print("http_status histogram:", dict(statuses))
non200 = {rid: (r.get("http_status"), (r.get("error_redacted") or "")[:200])
          for rid, r in reqs.items() if r.get("http_status") != 200}
print("non-200 requests:", json.dumps(non200, indent=1))
skipped = [rid for rid, r in reqs.items() if r.get("error_redacted") == "SKIPPED_CAP"]
print("SKIPPED_CAP:", skipped)
cap = CR.get("cap_exhausted")
print("cap_exhausted:", cap)
dupes = [rid for rid, c in Counter(CR["order"]).items() if c > 1]
print("duplicate rids in order:", dupes)
# phases
phases = Counter(r.get("phase") for r in reqs.values())
print("phase histogram:", dict(phases))
# endpoints
ends = Counter(r.get("endpoint") for r in reqs.values())
print("endpoint histogram:", dict(ends))

print()
print("=== RECORD-SIZE MATH (bytes == records x DBN size) ===")
RECORD_SIZE = {"ohlcv-1m": 56, "bbo-1m": 80, "statistics": 80, "definition": 520}
GB = 1e9
prices = CR["unit_prices_usd_per_gb"]["prices"]
print("unit prices:", prices, "source:", CR["unit_prices_usd_per_gb"]["source"])
bad = []
n_checked = 0
for pkg, pdata in CR["packages"].items():
    for ln in pdata.get("lines", []):
        rc, bs = ln.get("record_count"), ln.get("billable_size_bytes")
        if isinstance(rc, int) and isinstance(bs, int):
            n_checked += 1
            exp = rc * RECORD_SIZE[ln["schema"]]
            ok = (bs == exp)
            ratio = None
            if not ok:
                bad.append((pkg, ln["line_id"], rc, bs, exp, bs / exp if rc else None))
print(f"package lines with rc&bs ints: {n_checked}; mismatches: {len(bad)}")
for b in bad:
    print("  MISMATCH:", b)

# raw request-level spot check: every get_billable_size payload vs
# get_record_count payload for the same line
pairs_checked = 0
mismatch2 = []
by_rid = reqs
for rid, r in by_rid.items():
    if rid.endswith("-BS") and r.get("http_status") == 200:
        base = rid[:-3]
        rc_rec = by_rid.get(base + "-RC")
        if rc_rec and rc_rec.get("http_status") == 200:
            rc = rc_rec.get("payload")
            bs = r.get("payload")
            schema = r["params"].get("schema")
            if isinstance(rc, int) and isinstance(bs, int) and schema in RECORD_SIZE:
                pairs_checked += 1
                if bs != rc * RECORD_SIZE[schema]:
                    mismatch2.append((rid, rc, bs, rc * RECORD_SIZE[schema]))
print(f"request-pair spot checks (rc x size vs bs): {pairs_checked}; mismatches: {len(mismatch2)}")
for m in mismatch2[:10]:
    print("  MISMATCH:", m)

print()
print("=== GET_COST / LIST RATIO ===")
ratios = Counter()
for pkg, pdata in CR["packages"].items():
    for ln in pdata.get("lines", []):
        c = ln.get("cost_usd_get_cost")
        bs = ln.get("billable_size_bytes")
        if isinstance(c, (int, float)) and isinstance(bs, (int, float)) and bs > 0:
            lst = bs / GB * prices[ln["schema"]]
            ratios[round(c / lst, 4)] += 1
print("ratio histogram across ALL package lines (incl. anchors):", dict(ratios))
anchor = CR.get("cl_bbo_anchors", {})
for k, v in anchor.items():
    c, bs = v.get("cost_usd_get_cost"), v.get("billable_size_bytes")
    if isinstance(c, (int, float)) and isinstance(bs, (int, float)):
        print(f"anchor {k}: ratio={c/(bs/GB*prices[v['schema']]):.6f} cost={c} bs={bs} rc={v.get('record_count')} consistency={v.get('consistency_bytes_eq_rc_x_recsize')}")

print()
print("=== PACKAGE TOTALS RE-DERIVATION ===")
for pkg in ("A", "A_variant_24m_floor", "B", "C"):
    pdata = CR["packages"][pkg]
    lines = pdata["lines"]
    tot_rc = sum(ln["record_count"] for ln in lines if isinstance(ln.get("record_count"), int))
    tot_bs = sum(ln["billable_size_bytes"] for ln in lines if isinstance(ln.get("billable_size_bytes"), int))
    tot_gc = sum(ln["cost_usd_get_cost"] for ln in lines if isinstance(ln.get("cost_usd_get_cost"), (int, float)))
    tot_list = sum(ln["cost_usd_list"] for ln in lines if isinstance(ln.get("cost_usd_list"), (int, float)))
    stored = pdata["totals"]
    derived = [ln["line_id"] for ln in lines if ln.get("cost_basis")]
    print(f"pkg {pkg}: lines={len(lines)} derived={derived}")
    print(f"  recomputed: rc={tot_rc} bs={tot_bs} gb={tot_bs/GB:.4f} list={tot_list:.2f} gc={tot_gc:.2f}")
    print(f"  stored   : rc={stored['record_count']} bs={stored['billable_size_bytes']} gb={stored['billable_gb_decimal']} list={stored['cost_usd_list']} gc={stored['cost_usd_get_cost']} lines_failed={stored.get('lines_failed')} lines_derived={stored.get('lines_derived')}")

print()
print("=== COVERAGE GRID (earliest bands) ===")
cov = CR["coverage"]
band_summary = Counter()
for root, schemas in cov.items():
    for schema, cell in schemas.items():
        band_summary[cell.get("earliest_band")] += 1
print("earliest_band histogram:", dict(band_summary))
# verify each cell's refinement probe actually returned records>0
ref_bad = []
for root, schemas in cov.items():
    for schema, cell in schemas.items():
        for bp in cell.get("band_probes", []):
            if bp["band"].endswith("R"):
                if not (isinstance(bp["record_count"], int) and bp["record_count"] > 0):
                    ref_bad.append((root, schema, bp))
print("refinement probes (W1R) with records<=0 or None:", ref_bad)
# any non-W1 first hit?
first_hits = Counter()
for root, schemas in cov.items():
    for schema, cell in schemas.items():
        probes = cell.get("band_probes", [])
        first = next((p for p in probes if isinstance(p["record_count"], int) and p["record_count"] > 0), None)
        first_hits[first["band"] if first else "NONE"] += 1
print("first band with records>0 histogram:", dict(first_hits))

print()
print("=== LATEST MONTH ===")
for root, v in CR["latest"].items():
    print(f"  {root}: {v['window']} rc={v['record_count']} http={v['http_status']}")

print()
print("=== DISK SNAPSHOT ===")
snap = CR["disk_snapshot"]
print("captured:", snap.get("captured_utc"))
print("statvfs:", json.dumps(snap.get("statvfs"), indent=1))
print("df_h:", snap.get("df_h"))
print("du:", snap.get("du_sh_current_usage"))
st = snap["statvfs"]
avail_gb = st["available_bytes"] / 1e9
print(f"recomputed avail: {avail_gb:.2f} GB decimal; usable at 20% reserve: {avail_gb*0.8:.2f} GB")

print()
print("=== SYMBOLOGY FIX ===")
print(json.dumps(CR.get("symbology_fix"), indent=1)[:800])
