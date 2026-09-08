"""P0b: macro vintage re-pin — byte-compare DFII10/T10YIE/DGS10 vs FOREX-V8 P0 pins.

Method frozen in p0_census_contract.json (p0b_macro_repin_contract):
fresh GET fred/series/observations realtime 2018-01-01..2025-08-01 under the
owner FRED key (environment-only), normalize json.dumps(sort_keys=True),
sha256 byte-compare vs the V8 staged_vintaged_manifest pins.
ANY byte drift => lane 2 dies in P0 (plan sec2).
"""
import json, hashlib, os, urllib.request, urllib.parse, datetime

W = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/integration"
V8_MANIFEST = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v8/integration/research/control/forex_free_v8_run/staged_vintaged_manifest.json"

def main():
    env = {}
    for line in open("/Users/hoangminhlong/my-quantitative/.env"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    key = env.get("FRED_API_KEY", "")
    assert len(key) == 32, "FRED_API_KEY missing/wrong length (never printed)"

    man = json.load(open(V8_MANIFEST))
    rt_start = man["retrieval"]["realtime_start"]
    rt_end = man["retrieval"]["realtime_end"]
    rows = []
    for sid in ("DFII10", "T10YIE", "DGS10"):
        q = urllib.parse.urlencode({
            "series_id": sid, "realtime_start": rt_start, "realtime_end": rt_end,
            "file_type": "json", "api_key": key})
        req = urllib.request.Request(
            f"https://api.stlouisfed.org/fred/series/observations?{q}",
            headers={"User-Agent": "my-quantitative-research"})
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
        obs = resp["observations"]
        refetch = json.dumps(obs, sort_keys=True).encode()
        h_new = hashlib.sha256(refetch).hexdigest()
        pin = man["series"][sid]["sha256"]
        staged = open(f"{os.path.dirname(V8_MANIFEST)}/staged_vintaged/{sid}.json", "rb").read()
        rows.append({
            "series": sid,
            "request": f"fred/series/observations realtime_start={rt_start} realtime_end={rt_end} file_type=json (key redacted)",
            "api_count": resp.get("count"), "rows_refetched": len(obs),
            "sha256_refetched_normalized": h_new, "sha256_v8_pin": pin,
            "byte_identical_vs_staged": refetch == staged,
            "match": h_new == pin,
        })
        print(json.dumps(rows[-1]))
    verdict = "MACRO_REPIN_ALL_MATCH" if all(r["match"] and r["byte_identical_vs_staged"] for r in rows) else "MACRO_REPIN_DRIFT_LANE2_DIES"
    out = {
        "schema": "stocks_free_v13_run/p0b_macro_repin@1",
        "measured_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer": "A1_STOCKS_V13 (in-worktree P0; contract p0_census_contract.json p0b_macro_repin_contract)",
        "evidence": "FOREX-V8 staged_vintaged_manifest.json (staged 2026-09-08T03:00:42Z)",
        "series_results": rows,
        "verdict": verdict,
    }
    p = f"{W}/research/control/stocks_free_v13_run/p0b_macro_repin.json"
    json.dump(out, open(p, "w"), indent=1)
    print("verdict:", verdict, "->", p)

if __name__ == "__main__":
    main()
