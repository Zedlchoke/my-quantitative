#!/usr/bin/env python3
"""VERIFY-lane recompute of A5-EVENTS-BBO-COVERAGE:
CPI/EMPSIT 204+204 (17y x 12, all 08:30); anomalies verbatim; staleness range + two
independent recomputes from max mtime; BBO doc law statement.
Exit 0 = all pass."""
import json, sys, datetime
base = "research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/events_bbo_coverage"
fails = []
d = json.load(open(f"{base}/bls_dates.json"))
for k in ("CPI", "EMPSIT"):
    v = d["series"][k]
    per_year = {y: len(info["dates"]) for y, info in v["years"].items()}
    all0830 = all(info.get("all_0830") for info in v["years"].values())
    ok = (v["totals"]["scheduled_releases"] == 204 and len(per_year) == 17
          and set(per_year.values()) == {12} and all0830
          and v["totals"]["rows_all_0830_am"] == 204)
    print(f"{k}: n={sum(per_year.values())} years={len(per_year)} per_year=12 all_0830={all0830} -> {'OK' if ok else 'FAIL'}")
    if not ok: fails.append(k)
anoms = {a["id"] for a in d["anomalies"]}
need = {"CPI-2016-APRIL-DOUBLE-ENTRY", "BLS-2025-LATE-YEAR-VINTAGE-DIVERGENCE"}
print("anomalies recorded verbatim with no-cause handling:", "OK" if need <= anoms else f"MISSING {need - anoms}")
if not need <= anoms: fails.append("anomalies")
for a in d["anomalies"]:
    assert "no claim" in a["handling"] or "no cause" in a["handling"], a["id"]
c = json.load(open(f"{base}/coverage_remeasure.json"))
ages = {k: v["age_days_vs_20261003"] for k, v in c["ibkr_raw_staleness"].items()}
n_files = sum(v["n_files"] for v in c["ibkr_raw_staleness"].values())
ok = min(ages.values()) == 0.825 and max(ages.values()) == 0.891 and n_files == 1160
print(f"staleness range {min(ages.values())}-{max(ages.values())} over {n_files} files -> {'OK' if ok else 'FAIL'}")
if not ok: fails.append("staleness_range")
ref = datetime.datetime.fromisoformat(c["today_reference_utc"])
for sym in ("6A", "ES"):
    v = c["ibkr_raw_staleness"][sym]
    mt = datetime.datetime.fromisoformat(v["max_mtime_utc"])
    calc = round((ref - mt).total_seconds() / 86400, 3)
    ok = abs(calc - v["age_days_vs_20261003"]) < 0.001
    print(f"staleness recompute {sym}: json={v['age_days_vs_20261003']} calc={calc} -> {'OK' if ok else 'FAIL'}")
    if not ok: fails.append(f"staleness_{sym}")
md = open(f"{base}/BBO_AVAILABILITY_DOC.md").read()
ok = "cannot prove intrabar fill" in md and "queue position" in md and "MODELED COST" in md
print("BBO doc law (bbo-1m cannot prove fill/queue; MODELED COST):", "OK" if ok else "FAIL")
if not ok: fails.append("bbo_law")
sys.exit(1 if fails else 0)
