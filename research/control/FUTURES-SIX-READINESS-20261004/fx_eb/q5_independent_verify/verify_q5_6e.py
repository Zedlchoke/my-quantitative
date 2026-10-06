#!/usr/bin/env python
"""Q5 INDEPENDENT VERIFY — 6E-relevant captures (FX-EB-CALENDAR lane).

Owner law: archived Q5 data usable ONLY after independent VERIFY + reproduce
in THIS worktree. This script:
  1. sha256-hashes the sibling capture files itself (byte-level),
  2. re-extracts values from raw bytes with its OWN parser (no import of the
     sibling's code),
  3. compares with the sibling round's claimed values
     (FUTURES-P3-QUARANTINE-20261004/cal_permitted/cal_permitted_coverage.json
     -> targets.T2_fx_quarterly_expiries_2023_2025.6E),
  4. emits PASS/FAIL per capture + a machine JSON.

Values from quarantined P3-LANE captures (quarantine/ dir) are NEVER read here.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

VENV = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"
SIB = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
           "research/control/FUTURES-P3-QUARANTINE-20261004/cal_permitted")
SIB_CAP = SIB / "captures"
OUT_DIR = Path(__file__).resolve().parent

# 6E claims to reproduce (sibling T2)
CLAIMED_6E = {
    "ECH23": "13 Mar 2023", "ECM23": "19 Jun 2023", "ECU23": "18 Sep 2023",
    "ECZ23": "18 Dec 2023", "ECH24": "18 Mar 2024", "ECM24": "17 Jun 2024",
    "ECU24": "16 Sep 2024", "ECZ24": "16 Dec 2024", "ECH25": "17 Mar 2025",
    "ECM25": "16 Jun 2025", "ECU25": "15 Sep 2025", "ECZ25": "15 Dec 2025",
}
# QA cross-check row claimed by sibling (vs prior permitted lane): ECZ22 = 19 Dec 2022
CLAIMED_XCHECK = {"ECZ22": "19 Dec 2022"}


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse_pcal58(path):
    """Own parser for the archived official CmeWS ProductCalendar/Future/58 JSON."""
    rows = json.loads(Path(path).read_text())
    out = {}
    for r in rows:
        code = r.get("productCode")
        lt = r.get("lastTrade")
        exp = (r.get("expirationDate") or {}).get("dateOnlyLongFormat")
        cm = r.get("contractMonth")
        out[code] = {"contractMonth": cm, "lastTrade": lt, "expirationDateOnly": exp}
    return out


def main():
    results = {"schema": "fxeb_q5_independent_verify@1",
               "lane": "FX-EB-CALENDAR",
               "task_id": "FUTURES-SIX-READINESS-20261004",
               "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "law": "archived Q5 values enter this lane's calendar only if re-extracted here from bytes this lane hashed; P3-LANE quarantine/ captures never read",
               "captures": []}

    pcal = SIB_CAP / "pcal_58_6e_20210703144932.json"
    sibling_sums = {}
    for line in (SIB_CAP / "SHA256SUMS.txt").read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            sibling_sums[parts[1]] = parts[0]

    my_sha = sha256_file(pcal)
    sib_sha = sibling_sums.get(pcal.name)
    hash_match = (my_sha == sib_sha)
    rows = parse_pcal58(pcal)

    checks = []
    for code, claimed_lt in {**CLAIMED_6E, **CLAIMED_XCHECK}.items():
        mine = rows.get(code, {}).get("lastTrade")
        checks.append({"code": code, "sibling_claim": claimed_lt,
                       "my_reparse": mine,
                       "match": mine == claimed_lt})
    n_match = sum(1 for c in checks if c["match"])
    results["captures"].append({
        "capture": "pcal_58_6e_20210703144932.json",
        "my_sha256": my_sha,
        "sibling_manifest_sha256": sib_sha,
        "hash_match": hash_match,
        "parser": "own json.loads over raw bytes; fields productCode/lastTrade/expirationDate.dateOnlyLongFormat",
        "n_rows_in_file": len(rows),
        "claimed_values_checked": len(checks),
        "claimed_values_matched": n_match,
        "checks": checks,
        "verdict": "PASS" if (hash_match and n_match == len(checks)) else "FAIL",
    })

    # svc captures consumed by this lane (6E id=58 rides in the 10-product set)
    svc_names = sorted(p.name for p in SIB_CAP.glob("svc_*.json"))
    svc_results = []
    for name in svc_names:
        p = SIB_CAP / name
        my_sha = sha256_file(p)
        sib_sha = sibling_sums.get(name)
        try:
            d = json.loads(p.read_text())
            prods = d.get("products", [])
            ids = sorted(pr.get("id") for pr in prods)
            has_6e = 58 in ids
            # own parser: collect the 6E (id 58) schedules
            grid = {}
            for pr in prods:
                if pr.get("id") == 58:
                    for sch in (pr.get("tradingHours") or {}).get("schedules", []):
                        ed = sch.get("eventDate")
                        evs = [[e.get("tradingDate"), e.get("eventTime"),
                                e.get("marketEventType")] for e in sch.get("events", [])]
                        grid[ed] = evs
            err = None
            verdict = "PASS" if (my_sha == sib_sha and has_6e and grid) else "FAIL"
        except Exception as e:  # unparseable capture = FAIL
            ids, has_6e, grid, err = None, False, {}, repr(e)
            verdict = "FAIL"
        svc_results.append({
            "capture": name, "my_sha256": my_sha,
            "sibling_manifest_sha256": sib_sha,
            "hash_match": my_sha == sib_sha,
            "product_ids_found": ids, "has_id58_6e": has_6e,
            "id58_event_dates": sorted(grid.keys()),
            "error": err, "verdict": verdict,
        })
    results["svc_captures"] = svc_results
    n_pass = sum(1 for r in svc_results if r["verdict"] == "PASS")
    results["summary"] = {
        "pcal58_verdict": results["captures"][0]["verdict"],
        "svc_pass": f"{n_pass}/{len(svc_results)}",
        "all_fail_zero": all(r["verdict"] == "FAIL" for r in svc_results),
    }
    out = OUT_DIR / "q5_6e_verify_result.json"
    out.write_text(json.dumps(results, indent=1))
    print(json.dumps(results["captures"][0], indent=1)[:800])
    print(json.dumps(results["summary"], indent=1))
    print("svc FAILs:", [r["capture"] for r in svc_results if r["verdict"] == "FAIL"])


if __name__ == "__main__":
    main()
