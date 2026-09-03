#!/usr/bin/env python
"""FOREX-FREE-V1 F2 repair pass: collision-free refetch, canonical assembly,
weekend classification, frozen calendar exclusion, alignment + coverage proof."""
import hashlib, json, os, sys, time
from collections import Counter
from datetime import datetime, time as dtime, timedelta, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "research/assets/forex_free_v1")
import probe_td as P

RAW, CTL = P.RAW, P.CTL
NY = ZoneInfo("America/New_York")
# FROZEN FX trading-week calendar (preregistered; identical to FxWeekConvention default
# in research/assets/forex/sessions.py): open Sun 21:00 America/New_York, close Fri 16:00
# America/New_York, DST-correct via named zone. Bars outside [open, close) are excluded
# by this rule only — never by inspecting returns.
def week_bounds_utc(ts_utc):
    d = ts_utc.astimezone(NY).date()
    back = (d.weekday() + 1) % 7          # days since Sunday
    sunday = d - timedelta(days=back)
    op = datetime.combine(sunday, dtime(21, 0), NY)
    op_utc = op.astimezone(timezone.utc)
    cl_utc = (op + timedelta(days=4, hours=19)).astimezone(timezone.utc)  # Fri 16:00 NY
    if ts_utc < op_utc:                    # bar belongs to previous week
        op -= timedelta(days=7); cl = (op + timedelta(days=4, hours=19)).astimezone(timezone.utc)
        return op.astimezone(timezone.utc), cl
    return op_utc, cl_utc

def in_session(ts):
    o, c = week_bounds_utc(ts)
    return o <= ts < c

rep = {"refetched": [], "quarantined": [], "capped_remaining": []}
# 1) quarantine the seven truncated colliding files; refetch collision-free sub-window
for pair in P.PAIRS:
    tag = pair.replace("/", "")
    for pull in ("a", "b"):
        old = os.path.join(RAW, f"{tag}_1h_2025-10-14_{pull}.json")
        new = os.path.join(RAW, f"{tag}_1h_2025-10-14_2026-07-01_TRUNCATED_{pull}.json")
        if os.path.exists(old):
            os.replace(old, new)
            rep["quarantined"].append(os.path.basename(new))
    for sd, ed in [("2025-10-14", "2026-01-05")]:
        for pull in ("a", "b"):
            fp = os.path.join(RAW, f"{tag}_1h_{sd}_{ed}_{pull}.json")
            if P.load_json_or_none(fp) is None:
                body, j, err = P.td_get(pair, "1h", sd, ed)
                open(fp, "wb").write(body)
                n = len((j or {}).get("values") or [])
                rep["refetched"].append({"pair": pair, "start": sd, "end": ed, "pull": pull,
                                         "rows": n, "error": err,
                                         "sha256": hashlib.sha256(body).hexdigest()})
                if n >= 5000:
                    rep["capped_remaining"].append(fp)
# also refetch second half 2026-01-05->2026-07-01 with end-dated names (copy from valid short-name files)
for pair in P.PAIRS:
    tag = pair.replace("/", "")
    for pull in ("a", "b"):
        src = os.path.join(RAW, f"{tag}_1h_2026-01-05_{pull}.json")
        dst = os.path.join(RAW, f"{tag}_1h_2026-01-05_2026-07-01_{pull}.json")
        if os.path.exists(src) and not os.path.exists(dst):
            open(dst, "wb").write(open(src, "rb").read())

# 2) canonical assembly per pair/granularity
def files_for(tag, interval):
    out = []
    for f in sorted(os.listdir(RAW)):
        if f.startswith(f"{tag}_{interval}_") and f.endswith("_a.json") and "TRUNCATED" not in f:
            out.append(f[:-7])  # strip _a.json
    return out

def collect(tag, interval):
    rows, dups, files = [], 0, []
    for base in files_for(tag, interval):
        j = P.load_json_or_none(os.path.join(RAW, base + "_a.json"))
        if not j or "values" not in j:
            continue
        files.append(base)
        seen = {r["datetime"] for r in rows}
        for r in j["values"]:
            if r["datetime"] in seen:
                dups += 1
            else:
                rows.append(r); seen.add(r["datetime"])
    rows.sort(key=lambda r: r["datetime"])
    return rows, dups, files

out = {"pairs": {}}
for pair in P.PAIRS:
    tag = pair.replace("/", "")
    out["pairs"][pair] = {}
    for interval in ("1h", "4h"):
        rows, dups, files = collect(tag, interval)
        # alignment
        hrs = Counter(datetime.fromisoformat(r["datetime"].replace(" ", "T")).hour for r in rows)
        align_ok = all(h % (4 if interval == "4h" else 1) == 0 for h in hrs)
        # completed-bar: end dates all <= 2026-09-02 => complete; verify last bar + interval <= now
        last = datetime.fromisoformat(rows[-1]["datetime"].replace(" ", "T")).replace(tzinfo=timezone.utc) if rows else None
        completed = bool(last and last + timedelta(hours=4 if interval == "4h" else 1) <= datetime.now(timezone.utc))
        # weekend classification
        flat_wknd = nonflat_wknd = 0; sun_reopen = 0; suspect = []
        for r in rows:
            d = datetime.fromisoformat(r["datetime"].replace(" ", "T")).replace(tzinfo=timezone.utc)
            if d.weekday() >= 5:
                flat = float(r["high"]) == float(r["low"]) == float(r["open"]) == float(r["close"])
                if d.weekday() == 6 and d.hour >= 21:
                    sun_reopen += 1
                elif flat:
                    flat_wknd += 1
                else:
                    nonflat_wknd += 1
                    if len(suspect) < 10:
                        suspect.append(r["datetime"])
        # calendar exclusion (frozen rule)
        excluded = 0
        for r in rows:
            d = datetime.fromisoformat(r["datetime"].replace(" ", "T")).replace(tzinfo=timezone.utc)
            if not in_session(d):
                excluded += 1
        first = rows[0]["datetime"] if rows else None
        lastdt = rows[-1]["datetime"] if rows else None
        years = (datetime.fromisoformat(lastdt).date() - datetime.fromisoformat(first).date()).days / 365.25 if rows else 0
        out["pairs"][pair][interval] = {"first": first, "last": lastdt, "rows": len(rows),
            "boundary_duplicates": dups, "files": files, "alignment_ok": align_ok,
            "completed_bar": completed, "coverage_years": round(years, 3),
            "coverage_ge_65y": years >= 6.5,
            "weekend": {"sunday_reopen_2100plus": sun_reopen, "flat_weekend": flat_wknd,
                        "nonflat_weekend_excluded": nonflat_wknd, "suspect_sample": suspect},
            "calendar_excluded_out_of_session": excluded}
        print(pair, interval, "rows:", len(rows), "cov_y:", round(years, 3), "dups:", dups,
              "align:", align_ok, "wknd_flat:", flat_wknd, "nonflat:", nonflat_wknd, flush=True)

with open(os.path.join(CTL, "canonical_manifest.json"), "w") as f:
    json.dump(out, f, indent=1)
print("REPAIR DONE", flush=True)
