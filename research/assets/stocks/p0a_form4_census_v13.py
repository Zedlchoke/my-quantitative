"""P0a: Form-4 census, death-inclusive cohort — dead-side over the V9 cache + live canary.

Contract: p0_census_contract.json (frozen 2daf294 BEFORE counting).
Dead side: local parse of .staging_sec_v9/submissions_dead (no network).
Canary: live re-fetch per P-7 protocol (12 dead + 2 never-existed + 2 living).
Alive side: separate lock-gated fetch (p0a_alive_fetch_v13.py).
"""
import json, hashlib, os, glob, time, urllib.request, urllib.error, gzip, io, datetime, sys

W = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/integration"
CACHE = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration/.staging_sec_v9/submissions_dead"
COHORT = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v12/integration/research/control/stocks_free_v9_run/cohort_v9.json"
UA = "Research my-quantitative@example.com"
DATES = ["2018-04-04","2018-07-03","2018-10-02","2019-01-03","2019-04-04","2019-07-05","2019-10-03","2020-01-03","2020-04-03","2020-07-06","2020-09-10","2020-12-09","2021-03-12","2021-06-11","2021-09-10","2021-12-09","2022-03-11","2022-06-10","2022-09-12","2022-12-09","2023-02-17","2023-05-19","2023-08-21","2023-11-17","2024-02-21","2024-05-21","2024-08-21","2024-11-19","2025-02-24","2025-05-23"]
FOLDS = [DATES[0:10], DATES[10:20], DATES[20:30]]
WIN_LO, WIN_HI = "2018-01-01", "2025-05-23"   # acceptance window: grid start-open .. last decision date

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def form4_rows(d):
    rec = d.get("filings", {}).get("recent", {})
    forms = rec.get("form", [])
    out = []
    for i, fm in enumerate(forms):
        if fm == "4":
            acc = rec.get("acceptanceDateTime", [""] * len(forms))[i] or ""
            fd = rec.get("filingDate", [""] * len(forms))[i] or ""
            out.append((fd, acc))
    return out, forms

def bookable_pairs(acceptances):
    """(entity, D) pair count per fold + total: >=1 acceptance in (prev(D), D]."""
    acc_days = sorted({a[:10] for a in acceptances if a})
    pairs = 0
    per_fold = [0, 0, 0]
    for j, D in enumerate(DATES):
        lo = DATES[j - 1] if j > 0 else "2018-01-01"
        hit = any(lo < ad <= D for ad in acc_days)
        if hit:
            pairs += 1
            fold = 0 if j < 10 else (1 if j < 20 else 2)
            per_fold[fold] += 1
    return pairs, per_fold

def main():
    now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cohort_h = sha256(COHORT)
    assert cohort_h == "6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195666249e3fa2aa62", "cohort pin drift"
    cohort = json.load(open(COHORT))
    dead = cohort["members"]["DEAD_EVIDENCED"]
    alive = cohort["members"]["ALIVE_EVIDENCED"]
    print(f"cohort pin MATCH; dead={len(dead)} alive={len(alive)}")

    ents, missing_cache, trunc = {}, [], []
    raw_manifest = {}
    for m in dead:
        cik10 = m["cik"].replace("CIK", "").zfill(10)
        p = f"{CACHE}/CIK{cik10}.json"
        if not os.path.exists(p):
            missing_cache.append(m["cik"])
            continue
        raw_manifest[m["cik"]] = sha256(p)
        d = json.load(open(p))
        rows, forms = form4_rows(d)
        accs = [a if a else fd + "T00:00:00.000Z" for fd, a in rows]
        in_win = [a for a in accs if WIN_LO <= a[:10] <= WIN_HI]
        pairs, per_fold = bookable_pairs(in_win)
        oldest = min((fd for fd, _ in rows), default=None)
        ents[m["cik"]] = {
            "name": m["name"], "death": m.get("death_filing_date_evidence"),
            "form4_slice_total": len(rows), "form4_in_window": len(in_win),
            "bookable_pairs": pairs, "bookable_per_fold": per_fold,
            "oldest_filing_in_slice": oldest, "acceptance_dt_populated": sum(1 for _, a in rows if a),
            "truncation_flag": bool(oldest and oldest > "2018-04-04" and d.get("filings", {}).get("files")),
        }
        if ents[m["cik"]]["truncation_flag"]:
            trunc.append(m["cik"])

    with_form4 = {c: e for c, e in ents.items() if e["form4_slice_total"] > 0}
    win_ents = {c: e for c, e in ents.items() if e["form4_in_window"] > 0}
    pair_ents = {c: e for c, e in ents.items() if e["bookable_pairs"] > 0}
    total_pairs = sum(e["bookable_pairs"] for e in pair_ents.values())
    fold_pairs = [sum(e["bookable_per_fold"][i] for e in pair_ents.values()) for i in range(3)]
    print(f"dead-side: cached={len(ents)} missing_cache={len(missing_cache)} with_any_form4={len(with_form4)} "
          f"in_window_ents={len(win_ents)} pair_ents={len(pair_ents)} total_pairs={total_pairs} fold_pairs={fold_pairs} truncation_flagged={len(trunc)}")

    # deterministic canary draw: 8 from sorted dead-with-Form4 (stride 147) + 4 famous
    famous = ["CIK0001418091", "CIK0000718877", "CIK0000899866", "CIK0000002034"]
    dwf = sorted(with_form4.keys())
    canaries = famous + [dwf[i] for i in range(0, min(len(dwf), 8 * 147), 147)][:8]

    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                return r.status, raw
        except urllib.error.HTTPError as e:
            return e.code, b""

    canary_rows = []
    for cik in canaries:
        c10 = cik.replace("CIK", "").zfill(10)
        st, raw = get(f"https://data.sec.gov/submissions/CIK{c10}.json")
        n4 = 0
        if st == 200:
            rows, _ = form4_rows(json.loads(raw))
            n4 = len(rows)
        canary_rows.append({"kind": "DEAD", "cik": cik, "name": ents.get(cik, {}).get("name", "?"), "http": st, "form4_present": n4 > 0})
        time.sleep(2.0)
    for cik, nm in [("CIK0009999990", "NEVER-EXISTED-1"), ("CIK0009999991", "NEVER-EXISTED-2")]:
        st, _ = get(f"https://data.sec.gov/submissions/{cik}.json")
        canary_rows.append({"kind": "NEVER_EXISTED", "cik": cik, "name": nm, "http": st, "expect_404": True})
        time.sleep(2.0)
    for cik, nm in [("CIK0000001800", "ABBOTT"), ("CIK0000078003", "PFIZER")]:
        st, raw = get(f"https://data.sec.gov/submissions/{cik}.json")
        n4 = 0
        if st == 200:
            rows, _ = form4_rows(json.loads(raw))
            n4 = len(rows)
        canary_rows.append({"kind": "LIVING", "cik": cik, "name": nm, "http": st, "form4_present": n4 > 0})
        time.sleep(2.0)

    dead_ok = all(r["http"] == 200 and r["form4_present"] for r in canary_rows if r["kind"] == "DEAD")
    never_ok = all(r["http"] == 404 for r in canary_rows if r["kind"] == "NEVER_EXISTED")
    living_ok = all(r["http"] == 200 and r["form4_present"] for r in canary_rows if r["kind"] == "LIVING")
    canary_verdict = "CANARY_PASS_CHANNEL_RETAINS_DEAD" if (dead_ok and never_ok and living_ok) else "CANARY_FAIL_SURVIVORSHIP_BIASED_CHANNEL_DIES"

    out = {
        "schema": "stocks_free_v13_run/p0a_form4_census_deadside@1",
        "measured_at_utc": now(),
        "producer": "A1_STOCKS_V13 in-worktree; contract frozen at 2daf294",
        "cohort_pin": cohort_h,
        "dead_side": {
            "cached_entities": len(ents), "missing_cache_files": missing_cache,
            "entities_with_any_form4": len(with_form4),
            "entities_with_inwindow_form4": len(win_ents),
            "entities_with_bookable_pairs": len(pair_ents),
            "total_bookable_pairs_dead": total_pairs,
            "bookable_pairs_per_fold_dead": fold_pairs,
            "acceptance_dt_population": "100% where form4 present (see per-entity acceptance_dt_populated)",
            "truncation_flagged_entities": len(trunc),
            "note_dead_side_only": "floor verdict requires alive side (p0a_alive_fetch); dead-only numbers published here",
        },
        "canary": {"rows": canary_rows, "verdict": canary_verdict},
        "raw_cache_manifest_sample": {c: raw_manifest[c] for c in list(sorted(raw_manifest))[:5]},
        "raw_cache_manifest_count": len(raw_manifest),
    }
    p = f"{W}/research/control/stocks_free_v13_run/p0a_form4_census_deadside.json"
    json.dump(out, open(p, "w"), indent=1)
    json.dump({c: e for c, e in ents.items()}, open(f"{W}/research/control/stocks_free_v13_run/p0a_dead_entity_counts.json", "w"), indent=1)
    # full raw manifest (gitignored size check: ~1769 entries, small) — commit as json
    json.dump(raw_manifest, open(f"{W}/research/control/stocks_free_v13_run/p0a_dead_raw_manifest.json", "w"), indent=1)
    print("canary verdict:", canary_verdict)
    print("artifacts written")

if __name__ == "__main__":
    main()
