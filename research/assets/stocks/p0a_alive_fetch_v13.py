"""P0a alive-side fetch + combined census verdict. Bounded waiter under the
machine-wide heavy lock (contract: p0_census_contract.json governance).

Poll acquire every 60s up to 240 attempts (4h) -> NOT_RUN_RESOURCE_CONFLICT
each miss (never contention). On acquire: fetch 410 alive submissions JSONs
(declared UA, 2.0s spacing, gzip) to .staging_sec_v13/submissions_alive/,
compute bookable pairs, merge with dead-side census, evaluate the EX-ANTE
floor, write p0a_form4_census.json. Release FINISHED / FAILED (+stderr tail).
"""
import json, hashlib, os, sys, time, traceback, urllib.request, gzip, io, datetime

W = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/integration"
sys.path.insert(0, f"{W}/research")
from governance import heavy_lock

CACHE = f"{W}/.staging_sec_v13/submissions_alive"
COHORT = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v12/integration/research/control/stocks_free_v9_run/cohort_v9.json"
UA = "Research my-quantitative@example.com"
DATES = ["2018-04-04","2018-07-03","2018-10-02","2019-01-03","2019-04-04","2019-07-05","2019-10-03","2020-01-03","2020-04-03","2020-07-06","2020-09-10","2020-12-09","2021-03-12","2021-06-11","2021-09-10","2021-12-09","2022-03-11","2022-06-10","2022-09-12","2022-12-09","2023-02-17","2023-05-19","2023-08-21","2023-11-17","2024-02-21","2024-05-21","2024-08-21","2024-11-19","2025-02-24","2025-05-23"]
WIN_LO, WIN_HI = "2018-01-01", "2025-05-23"
STATUS = f"{W}/research/control/stocks_free_v13_run/p0a_alive_fetch_status.json"

def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def status(**kw):
    base = {"cycle": "STOCKS-FREE-V13", "job": "P0A_ALIVE_FETCH", "updated_utc": now()}
    base.update(kw)
    json.dump(base, open(STATUS, "w"), indent=1)

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def form4_rows(d):
    rec = d.get("filings", {}).get("recent", {})
    forms = rec.get("form", [])
    return [(rec.get("filingDate", [""] * len(forms))[i], rec.get("acceptanceDateTime", [""] * len(forms))[i] or "")
            for i, fm in enumerate(forms) if fm == "4"]

def bookable(accs):
    days = sorted({a[:10] for a in accs if a})
    pairs, per_fold = 0, [0, 0, 0]
    for j, D in enumerate(DATES):
        lo = DATES[j - 1] if j > 0 else WIN_LO
        if any(lo < ad <= D for ad in days):
            pairs += 1
            per_fold[0 if j < 10 else (1 if j < 20 else 2)] += 1
    return pairs, per_fold

def fetch(cik10):
    import urllib.error
    req = urllib.request.Request(f"https://data.sec.gov/submissions/CIK{cik10}.json",
                                 headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    for attempt in (1, 2, 3):  # TRANSIENT_TRANSPORT: bounded 3-attempt backoff (SHV1 taxonomy)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                return raw
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(30 * attempt)

def main():
    os.makedirs(CACHE, exist_ok=True)
    cohort = json.load(open(COHORT))
    alive = cohort["members"]["ALIVE_EVIDENCED"]
    status(state="WAITING_FOR_LOCK", attempts=0, note="CRYPTO-V17 holds; NOT_RUN_RESOURCE_CONFLICT each miss")
    handle = None
    for attempt in range(1, 241):
        try:
            handle = heavy_lock.acquire(
                cycle_id="STOCKS-FREE-V13", role="P0_ALIVE_FETCH",
                worktree=W,
                command=[sys.executable, __file__],
                expected_artifacts=[f"{W}/research/control/stocks_free_v13_run/p0a_form4_census.json"],
            )
            status(state="LOCK_ACQUIRED", attempts=attempt)
            break
        except heavy_lock.LockBusyError:
            status(state="WAITING_FOR_LOCK", attempts=attempt)
            time.sleep(60)
        except Exception:
            status(state="CONTROL_STATE_DRIFT_FAIL_CLOSED", attempts=attempt, stderr=traceback.format_exc()[-800:])
            return
    if handle is None:
        status(state="GAVE_UP_NOT_RUN_RESOURCE_CONFLICT", attempts=240)
        return
    try:
        ents, manifest = {}, {}
        for i, m in enumerate(alive):
            c10 = m["cik"].replace("CIK", "").zfill(10)
            p = f"{CACHE}/CIK{c10}.json"
            if not os.path.exists(p):
                raw = fetch(c10)
                open(p, "wb").write(raw)
                time.sleep(2.0)
            manifest[m["cik"]] = sha256(p)
            d = json.load(open(p))
            rows = form4_rows(d)
            accs = [a if a else fd + "T00:00:00.000Z" for fd, a in rows]
            inw = [a for a in accs if WIN_LO <= a[:10] <= WIN_HI]
            pairs, per_fold = bookable(inw)
            oldest = min((fd for fd, _ in rows), default=None)
            ents[m["cik"]] = {"name": m["name"], "form4_slice_total": len(rows),
                              "form4_in_window": len(inw), "bookable_pairs": pairs,
                              "bookable_per_fold": per_fold,
                              "truncation_flag": bool(oldest and oldest > "2018-04-04" and d.get("filings", {}).get("files"))}
            if (i + 1) % 50 == 0:
                status(state="FETCHING", fetched=i + 1, total=len(alive))
        # merge with dead side
        dead_counts = json.load(open(f"{W}/research/control/stocks_free_v13_run/p0a_dead_entity_counts.json"))
        dead_pair_ents = {c: e for c, e in dead_counts.items() if e["bookable_pairs"] > 0}
        alive_pair_ents = {c: e for c, e in ents.items() if e["bookable_pairs"] > 0}
        total_pairs = sum(e["bookable_pairs"] for e in dead_pair_ents.values()) + sum(e["bookable_pairs"] for e in alive_pair_ents.values())
        fold_pairs = [sum(e["bookable_per_fold"][i] for e in list(dead_pair_ents.values()) + list(alive_pair_ents.values())) for i in range(3)]
        n_ents = len(dead_pair_ents) + len(alive_pair_ents)
        dead_pairs = sum(e["bookable_pairs"] for e in dead_pair_ents.values())
        dead_share = dead_pairs / total_pairs if total_pairs else 0.0
        floor = {
            "distinct_entities_with_1pair_min": 250, "observed": n_ents,
            "total_bookable_pairs_min": 1500, "observed_pairs": total_pairs,
            "dead_share_of_pairs_min": 0.03, "observed_dead_share": round(dead_share, 4),
            "per_fold_pairs_min_each": 250, "observed_per_fold": fold_pairs,
        }
        checks = {
            "entities": n_ents >= 250, "pairs": total_pairs >= 1500,
            "dead_share": dead_share >= 0.03,
            "per_fold": all(f >= 250 for f in fold_pairs),
        }
        verdict = "FORM4_CENSUS_FUNDABLE" if all(checks.values()) else "FORM4_CENSUS_BLOCKED_DATA_OR_SELECTION"
        out = {
            "schema": "stocks_free_v13_run/p0a_form4_census@1",
            "measured_at_utc": now(),
            "producer": "A1_STOCKS_V13; combined dead(cache)+alive(fresh) under machine lock",
            "floor_evaluation_ex_ante": {"floor": floor, "checks": checks, "verdict": verdict},
            "dead_side": {"pair_entities": len(dead_pair_ents), "total_pairs": dead_pairs},
            "alive_side": {"pair_entities": len(alive_pair_ents),
                            "total_pairs": total_pairs - dead_pairs,
                            "truncation_flagged": sum(1 for e in ents.values() if e["truncation_flag"])},
            "alive_raw_manifest_count": len(manifest),
            "note": "alive raw bytes local-only (.staging_sec_v13 gitignored); manifest sha256 committed separately",
        }
        json.dump(out, open(f"{W}/research/control/stocks_free_v13_run/p0a_form4_census.json", "w"), indent=1)
        json.dump({c: e for c, e in ents.items()}, open(f"{W}/research/control/stocks_free_v13_run/p0a_alive_entity_counts.json", "w"), indent=1)
        json.dump(manifest, open(f"{W}/research/control/stocks_free_v13_run/p0a_alive_raw_manifest.json", "w"), indent=1)
        status(state="DONE", verdict=verdict, total_pairs=total_pairs, entities=n_ents, dead_share=round(dead_share, 4), fold_pairs=fold_pairs)
        handle.release(status="FINISHED", note=f"P0a alive fetch+census done: {verdict}")
        print("DONE", verdict)
    except Exception:
        err = traceback.format_exc()
        status(state="FAILED", stderr=err[-1500:])
        try:
            handle.release(status="FAILED", note=("stderr tail: " + err.strip().splitlines()[-1][:300]))
        except Exception:
            pass
        raise

if __name__ == "__main__":
    main()
