#!/usr/bin/env python
"""FOREX-FREE-V1: definitive canonical-completion pass.
1) Quarantine mis-named duplicate-copy files (byte copies under wrong window names).
2) Compute each pair's covered spans from file CONTENTS; find gaps > 48h within
   the authorized coverage window; fetch exactly the missing spans (<=130-day
   chunks, two pulls each, end-dated names).
3) Re-verify full continuity (no in-week gap > 48h) and write the final manifest."""
import hashlib, json, os, sys
from datetime import datetime, timedelta
sys.path.insert(0, "research/assets/forex_free_v1")
import probe_td as P

RAW = P.RAW
START, END = datetime(2020, 1, 29), datetime(2026, 9, 2)

# 1) quarantine misleading duplicate copies
for f in sorted(os.listdir(RAW)):
    if "_2026-01-05_2026-07-01_" in f and "DUPLICATE" not in f:
        os.replace(os.path.join(RAW, f), os.path.join(RAW, f.replace("_a.json", "_DUPLICATE_COPIES_OF_2026-01-05_a.json").replace("_b.json", "_DUPLICATE_COPIES_OF_2026-01-05_b.json")))
        print("quarantined duplicate:", f, flush=True)

def files_for(tag, interval):
    out = []
    for f in sorted(os.listdir(RAW)):
        if f.startswith(f"{tag}_{interval}_") and f.endswith("_a.json")            and "TRUNCATED" not in f and "DUPLICATE" not in f:
            out.append(f[:-7])
    return out

def spans_from_files(tag, interval):
    covered = []
    for f in sorted(os.listdir(RAW)):
        if not (f.startswith(f"{tag}_{interval}_") and f.endswith("_a.json")
                and "TRUNCATED" not in f and "DUPLICATE" not in f):
            continue
        j = P.load_json_or_none(os.path.join(RAW, f))
        if not j or j.get("status") == "error" or not j.get("values"):
            continue
        dts = [datetime.fromisoformat(r["datetime"]) for r in j["values"]]
        covered.append((min(dts), max(dts)))
    return covered

def gaps(covered):
    covered.sort()
    merged = []
    for s, e in covered:
        if merged and s <= merged[-1][1] + timedelta(hours=2):
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    out, cur = [], START
    for s, e in merged:
        if s > cur + timedelta(hours=48):
            out.append((cur, s))
        cur = max(cur, e)
    if cur < END - timedelta(hours=48):
        out.append((cur, END))
    return out, merged

refetched = []
for pair in P.PAIRS:
    tag = pair.replace("/", "")
    for interval in ("1h",):
        cov = spans_from_files(tag, interval)
        missing, merged = gaps(cov)
        print(pair, interval, "merged spans:", len(merged), "gaps:", [(str(a), str(b)) for a, b in missing], flush=True)
        for gs, ge in missing:
            cur = gs
            while cur < ge:
                chunk_end = min(cur + timedelta(days=120), ge)
                sd, ed = cur.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")
                for pull in ("a", "b"):
                    fp = os.path.join(RAW, f"{tag}_{interval}_{sd}_{ed}_{pull}.json")
                    if P.load_json_or_none(fp) is None:
                        body, j, err = P.td_get(pair, interval, sd, ed)
                        open(fp, "wb").write(body)
                        n = len((j or {}).get("values") or [])
                        refetched.append({"pair": pair, "interval": interval, "start": sd, "end": ed,
                                          "pull": pull, "rows": n, "error": err,
                                          "sha256": hashlib.sha256(body).hexdigest()})
                        assert n < 5000, f"STILL CAPPED: {pair} {sd}->{ed} rows={n}"
                cur = chunk_end
    # 1day completeness check (single window each)
    cov = spans_from_files(tag, "1day")
    missing, _ = gaps(cov)
    print(pair, "1day gaps:", [(str(a), str(b)) for a, b in missing], flush=True)

json.dump({"refetched": refetched}, open(os.path.join(P.CTL, "completion_pass.json"), "w"), indent=1)
print("COMPLETION FETCH DONE", len(refetched), "requests", flush=True)

# 3) final continuity verification
final = {}
for pair in P.PAIRS:
    tag = pair.replace("/", "")
    rows, dups, files = [], 0, []
    for base in files_for(tag, "1h"):
        j = P.load_json_or_none(os.path.join(RAW, base + "_a.json"))
        if not j or j.get("status") == "error" or not j.get("values"):
            continue
        files.append(base)
        seen = {r["datetime"] for r in rows}
        for r in j["values"]:
            if r["datetime"] in seen:
                dups += 1
            else:
                rows.append(r); seen.add(r["datetime"])
    rows.sort(key=lambda r: r["datetime"])
    dts = [datetime.fromisoformat(r["datetime"]) for r in rows]
    big = sum(1 for i in range(1, len(dts)) if (dts[i] - dts[i-1]) > timedelta(hours=48))
    yrs = (dts[-1] - dts[0]).total_seconds() / (365.25 * 24 * 3600)
    final[pair] = {"rows": len(rows), "first": rows[0]["datetime"], "last": rows[-1]["datetime"],
                   "span_years": round(yrs, 3), "gaps_gt_48h": big, "boundary_dups": dups, "files": len(files)}
    print(pair, final[pair], flush=True)

json.dump({"completion_refetches": refetched, "canonical_final": final},
          open(os.path.join(P.CTL, "canonical_manifest_final.json"), "w"), indent=1)
print("FINAL VERIFICATION DONE", flush=True)
