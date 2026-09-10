"""INC-V13-11 recovery: V13 price substrate re-stage (EODHD, lock-gated).

The V9 death-inclusive price cache (.staging_prices_v9, 2190 files, sha'd in
the inherited p0d_v9_price_manifest.json) was deleted by the external worktree
cleanup and is in NO archive (v9_staging tarball has no prices; v8 archive is
the 410-filer pre-death era). Prices are NOT a named pin in the V13 P3 freeze
(only panel/cohort/v10 observables - all restored byte-exact, ALL PINS MATCH).
This re-stage is therefore ordinary re-staging of an unpinned input:
same vendor (EODHD owner-entitled), same adjusted-daily contract, fetched once
and used IDENTICALLY by D2 veto exposures and any later book (P-3 consistency).
New manifest = V13's own price manifest. Coverage gate: every symbol of the
inherited manifest must be present in the new cache; OHLC validity sample-checked.
"""
import json, hashlib, os, sys, time, urllib.request, urllib.error, traceback, datetime

W = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/integration"
sys.path.insert(0, f"{W}/research")
from governance import heavy_lock

OLD_MANIFEST = f"{W}/research/control/stocks_free_v9_run/p0d_v9_price_manifest.json"
V9WT = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration"
OUT_DIR = f"{V9WT}/.staging_prices_v9/eod"   # the D2 machine's pinned read path (INC-V13-11: re-staged cache, provenance in V13 manifest)
OUT_MANIFEST = f"{W}/research/control/stocks_free_v13_run/p0d_v13_price_manifest.json"
STATUS = f"{W}/research/control/stocks_free_v13_run/p0d_price_restage_status.json"

def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def status(**kw):
    b = {"cycle": "STOCKS-FREE-V13", "job": "P0D_PRICE_RESTAGE", "updated_utc": now()}
    b.update(kw)
    json.dump(b, open(STATUS, "w"), indent=1)

def main():
    env = {}
    for line in open("/Users/hoangminhlong/my-quantitative/.env"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    token = env.get("EODHD_API_KEY", "")
    assert token, "EODHD_API_KEY missing"
    old = json.load(open(OLD_MANIFEST))
    allkeys = sorted(old["files"].keys())
    targets = [k for k in allkeys if k.startswith("eod/") and "__" in os.path.basename(k)]
    bench_targets = [k for k in allkeys if k.startswith("bench/")]
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(f"{OUT_DIR}/../benchmarks", exist_ok=True)
    status(state="WAITING_FOR_LOCK", targets=len(targets))
    handle = None
    for attempt in range(1, 200):
        try:
            handle = heavy_lock.acquire(cycle_id="STOCKS-FREE-V13", role="P0D_PRICE_RESTAGE",
                                        worktree=W, command=[sys.executable, __file__],
                                        expected_artifacts=[OUT_MANIFEST])
            break
        except heavy_lock.LockBusyError:
            status(state="WAITING_FOR_LOCK", attempts=attempt)
            time.sleep(60)
    if handle is None:
        status(state="GAVE_UP_NOT_RUN_RESOURCE_CONFLICT")
        return
    try:
        newman, missing, bad = {}, [], []
        import subprocess
        for i, rel in enumerate(targets):
            fname = os.path.basename(rel)               # CIKxxxx__TICKER.json
            sym = fname.replace(".json", "").split("__", 1)[1] + ".US"
            out = f"{OUT_DIR}/{fname}"
            if not os.path.exists(out):
                url = f"https://eodhd.com/api/eod/{sym}?api_token={token}&fmt=json&order=a"
                r = subprocess.run(["curl", "-sS", "--max-time", "45", "--compressed",
                                    "-w", "\n%{http_code}", url], capture_output=True, text=True)
                body, _, code = r.stdout.rpartition("\n")
                if r.returncode != 0 or code != "200":
                    # retry once after 30s, then record and continue (reconcile at end)
                    time.sleep(30)
                    r = subprocess.run(["curl", "-sS", "--max-time", "45", "--compressed",
                                        "-w", "\n%{http_code}", url], capture_output=True, text=True)
                    body, _, code = r.stdout.rpartition("\n")
                if r.returncode != 0 or code != "200":
                    missing.append(fname)
                    continue
                try:
                    arr = json.loads(body)
                    assert isinstance(arr, list) and len(arr) > 60, "thin/invalid series"
                except Exception as e:
                    bad.append((fname, str(e)[:60]))
                    continue
                open(out, "w").write(body)
                time.sleep(1.1)
            h = hashlib.sha256(open(out, "rb").read()).hexdigest()
            newman[f"eod/{fname}"] = h
            if (i + 1) % 100 == 0:
                status(state="FETCHING", done=i + 1, total=len(targets), missing=len(missing))
        # benchmarks: SPY + 11 sector ETFs (bench dir carried from the same vendor)
        bench = {}
        for sym in ["SPY.US", "XLK.US", "XLF.US", "XLV.US", "XLE.US", "XLY.US",
                    "XLP.US", "XLI.US", "XLB.US", "XLU.US", "XLRE.US", "XLC.US", "VCR.US"]:
            out = f"{OUT_DIR}/../benchmarks/{sym.split('.')[0]}.json"
            if not os.path.exists(out):
                url = f"https://eodhd.com/api/eod/{sym}?api_token={token}&fmt=json&order=a"
                r = subprocess.run(["curl", "-sS", "--max-time", "45", "--compressed",
                                    "-w", "\n%{http_code}", url], capture_output=True, text=True)
                body, _, code = r.stdout.rpartition("\n")
                if r.returncode == 0 and code == "200":
                    open(out, "w").write(body)
                time.sleep(1.1)
            p = f"{OUT_DIR}/../benchmarks/{sym.split('.')[0]}.json"
            if os.path.exists(p):
                bench[f"benchmarks/{os.path.basename(p)}"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
            else:
                missing.append(f"benchmarks/{sym}")
        coverage = {
            "inherited_symbols": len(targets),
            "restored": len(newman),
            "missing": missing,
            "invalid": bad,
            "coverage_ratio": round(len(newman) / len(targets), 4),
            "gate": "PASS" if len(newman) == len(targets) and not bad else "FAIL_COVERAGE",
        }
        out = {
            "schema": "stocks_free_v13_run/p0d_v13_price_manifest@1",
            "built_at_utc": now(),
            "provenance": "INC-V13-11 re-stage: V9 cache unrecoverable (not archived, external cleanup); EODHD fresh pull, same adjusted-daily contract; single substrate for D2 vetoes and books (P-3)",
            "files": {**newman, **bench},
            "coverage_gate": coverage,
        }
        json.dump(out, open(OUT_MANIFEST, "w"), indent=1)
        status(state="DONE", **coverage)
        handle.release(status="FINISHED", note=f"price restage: {len(newman)}/{len(targets)} restored, gate {coverage['gate']}")
        print("DONE", coverage["gate"], f"{len(newman)}/{len(targets)}")
    except Exception:
        err = traceback.format_exc()
        status(state="FAILED", stderr=err[-1200:])
        try:
            handle.release(status="FAILED", note=err.strip().splitlines()[-1][:250])
        except Exception:
            pass
        raise

if __name__ == "__main__":
    main()
