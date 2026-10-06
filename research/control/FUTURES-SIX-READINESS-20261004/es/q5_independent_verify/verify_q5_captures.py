#!/usr/bin/env python
"""
ES-READINESS lane, FUTURES-SIX-READINESS-20261004 — independent verification of
Q5-permitted captures (P3 quarantine round, cal_permitted/captures/).

Owner law for this round: Q5 archived data may be used ONLY after independent
verification — (a) sha256 every capture file ourselves, (b) re-extract the
claimed values from the RAW capture bytes with OUR OWN script, (c) compare to
the claimed values. This script implements exactly that. It is written from
scratch against the raw JSON structure observed in the captures themselves;
no Q5 extraction code was copied or imported.

Read-only inputs:
  P3_DIR/cal_permitted/captures/*.json         (raw capture bytes)
  P3_DIR/cal_permitted/captures/SHA256SUMS.txt (Q5's own digest manifest)
  P3_DIR/cal_permitted/cal_permitted_coverage.json (claimed values + claimed sha256)

Outputs (this directory):
  sha256_sums_mine.txt      our recomputed digests, sha256sum format
  extracted_es_grid.json    our grid re-extracted from raw bytes
  verify_report.json        verdicts: digest matches, cell-by-cell diff, weekly string
"""
import hashlib
import json
import os
import re
import sys
from datetime import date

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep"
P3 = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
      "research/control/FUTURES-P3-QUARANTINE-20261004")
CAP = os.path.join(P3, "cal_permitted", "captures")
COV = os.path.join(P3, "cal_permitted", "cal_permitted_coverage.json")
SUMS = os.path.join(CAP, "SHA256SUMS.txt")
OUT = os.path.dirname(os.path.abspath(__file__))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- load claims
cov = json.load(open(COV))
t1 = cov["targets"]["T1_es_nq_2026_session_times"]
weekly_claim = t1["ES_weekly_globex"]
dev_claim = t1["ES_2026_holiday_deviations"]

claimed_files = ([weekly_claim["capture"]] + dev_claim["captures"])

q5_sums = {}
for line in open(SUMS):
    line = line.strip()
    if not line:
        continue
    digest, name = line.split(None, 1)
    q5_sums[name.strip()] = digest

# ------------------------------------------- OUR OWN extraction from raw bytes
def extract_es_grid_from_svc(raw_bytes):
    """Own parser over the raw by-product service JSON.

    Structure observed directly in the raw bytes:
      {"props":...,"products":[{"globex":"ES","id":133,
        "tradingHours":{"schedules":[{"groupCode":"ES","eventDate":"YYYY-MM-DD",
        "events":[{"tradingDate":..., "eventTime":"HH:MM",
                   "marketEventType":"preopen|open|closed"}],...}]}},...]}
    Returns {eventDate: [(tradingDate, eventTime, marketEventType), ...]} for
    product ES / id 133 / groupCode ES only.
    """
    d = json.loads(raw_bytes.decode("utf-8"))
    grid = {}
    for prod in d.get("products", []):
        if prod.get("globex") != "ES" or prod.get("id") != 133:
            continue
        scheds = prod.get("tradingHours", {}).get("schedules", [])
        for sch in scheds:
            ed = sch.get("eventDate")
            for ev in sch.get("events", []):
                grid.setdefault(ed, []).append(
                    (ev.get("tradingDate"), ev.get("eventTime"),
                     ev.get("marketEventType")))
    return grid


def extract_es_weekly_from_cspecs(raw_bytes):
    """Own parser for the ContractSpecs service JSON: TradingHours.vandhr[]
    entries {venue, hours}; return the CME Globex venue hours string
    (HTML entities left raw; normalized for comparison separately)."""
    d = json.loads(raw_bytes.decode("utf-8"))
    out = {}
    for entry in d.get("TradingHours", {}).get("vandhr", []):
        venue = (entry.get("venue") or "").strip()
        out[venue] = entry.get("hours") or ""
    return out


def norm(s):
    s = re.sub(r"<br\s*/?>", " ", s)
    s = s.replace("&nbsp;", " ").replace("&rsquo;", "'")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# ---------------------------------------------------------------- run verify
digest_rows = []
grid_by_capture = {}
for ent in claimed_files:
    fname = os.path.basename(ent["file"])
    path = os.path.join(CAP, fname)
    row = {"file": fname,
           "claimed_sha256": ent["sha256"],
           "in_q5_sha256sums_txt": fname in q5_sums}
    if not os.path.exists(path):
        row.update({"status": "MISSING_FROM_DISK",
                    "our_sha256": None,
                    "sha256_match_claim": None,
                    "sha256_match_q5sums": None})
        digest_rows.append(row)
        continue
    ours = sha256_file(path)
    row.update({
        "status": "PRESENT",
        "our_sha256": ours,
        "sha256_match_claim": ours == ent["sha256"],
        "sha256_match_q5sums": (q5_sums.get(fname) == ours) if fname in q5_sums else None,
        "size_bytes": os.path.getsize(path)})
    if fname.endswith(".json") and (fname.startswith("svc_")
                                    or fname.startswith("es_set_")):
        try:
            grid_by_capture[fname] = extract_es_grid_from_svc(open(path, "rb").read())
            row["es_grid_extracted"] = True
            row["es_event_dates"] = sorted(grid_by_capture[fname].keys())
        except Exception as e:  # noqa: BLE001
            row["es_grid_extracted"] = False
            row["parse_error"] = repr(e)
    digest_rows.append(row)

# weekly string from raw bytes
cspecs_path = os.path.join(CAP, "cspecs_133_20260405234659.json")
weekly_raw = extract_es_weekly_from_cspecs(open(cspecs_path, "rb").read())
ours_globex = norm(weekly_raw.get("CME Globex:", ""))
claim_raw = weekly_claim["verbatim"].split("[capture")[0].strip()
# claimed verbatim carries the venue label "CME Globex: " then the opening
# sentence; the raw field continues with TACO/BTIC/TMAC paragraphs, so the
# claim must equal venue-prefix + a prefix of ours.
claim_globex = norm(claim_raw)
claim_body = claim_globex
for pref in ("CME Globex: ", "CME Globex:"):
    if claim_body.startswith(pref):
        claim_body = claim_body[len(pref):]
        break
weekly_match = ours_globex.startswith(claim_body)

# merged grid from raw bytes, compared cell-by-cell vs claimed.
# Claimed grid is keyed by TRADING date (session date), aggregating all events
# whose tradingDate equals the key — verified against raw MLK capture bytes:
# claimed "2026-01-20" == union of events with tradingDate 2026-01-20 across
# eventDates 01-18/01-19/01-20. We therefore re-key ours by tradingDate too,
# and compare [time, type] lists (claimed drops tradingDate == key by
# construction).
merged_full = {}   # tradingDate -> set of (eventDate, time, type)
merged = {}        # tradingDate -> sorted list of [time, type]
for fname, g in sorted(grid_by_capture.items()):
    for ed, evs in g.items():
        for td, tm, mt in evs:
            merged_full.setdefault(td, set()).add((ed, tm, mt))
for td, evs in merged_full.items():
    merged[td] = sorted([tm, mt] for _, tm, mt in evs)

claimed_cells = {ed: sorted([x[0], x[1]] for x in cell["events"])
                 for ed, cell in dev_claim["cells"].items()}

cell_report = {}
for ed in sorted(set(claimed_cells) | set(merged)):
    c = claimed_cells.get(ed)
    m = merged.get(ed)
    if c is None and m is not None:
        cell_report[ed] = {"verdict": "EXTRA_IN_OUR_EXTRACTION",
                           "note": "present captures yield events the claimed grid omits",
                           "ours": m}
    elif m is None:
        cell_report[ed] = {"verdict": "MISSING_FROM_OUR_EXTRACTION",
                           "note": "claimed but no present capture yields it",
                           "claimed": c}
    else:
        if m == c:
            cell_report[ed] = {"verdict": "MATCH", "ours": m}
        elif sorted(map(tuple, m)) == sorted(set(map(tuple, c))):
            # claim carries literal duplicates of the same (time, type) event —
            # an artifact of appending across two overlapping captures; the
            # set of distinct event values is identical.
            cell_report[ed] = {"verdict": "MATCH_SET_EQUAL_CLAIM_HAS_DUPLICATES",
                               "claimed": c, "ours": m}
        else:
            cell_report[ed] = {"verdict": "MISMATCH", "claimed": c, "ours": m}

n_match = sum(1 for v in cell_report.values()
              if v["verdict"] in ("MATCH", "MATCH_SET_EQUAL_CLAIM_HAS_DUPLICATES"))
n_extra = sum(1 for v in cell_report.values() if v["verdict"] == "EXTRA_IN_OUR_EXTRACTION")
n_missing = sum(1 for v in cell_report.values() if v["verdict"] == "MISSING_FROM_OUR_EXTRACTION")
n_mismatch = sum(1 for v in cell_report.values() if v["verdict"] == "MISMATCH")

present = [r for r in digest_rows if r["status"] == "PRESENT"]
missing = [r for r in digest_rows if r["status"] == "MISSING_FROM_DISK"]
digest_ok = all(r["sha256_match_claim"] for r in present)

# missing files: are they even in Q5's own fetch log?
fetch_log_rows = []
fl_path = os.path.join(P3, "cal_permitted", "fetch_log.jsonl")
if os.path.exists(fl_path):
    for line in open(fl_path):
        if line.strip():
            fetch_log_rows.append(json.loads(line))
for r in missing:
    hits = [h for h in fetch_log_rows if r["file"] in json.dumps(h)]
    r["fetch_log_hits"] = len(hits)
    r["in_q5_fetch_log"] = bool(hits)

# our own sha256sums artifact
with open(os.path.join(OUT, "sha256_sums_mine.txt"), "w") as f:
    for r in sorted(digest_rows, key=lambda x: x["file"]):
        dig = r["our_sha256"] or ("MISSING " + r["file"])
        f.write(f"{dig}  {r['file']}\n")

# extracted grid artifact
json.dump({
    "producer": "verify_q5_captures.py (ES-READINESS lane, FUTURES-SIX-READINESS-20261004)",
    "weekly_globex_by_venue_raw": weekly_raw,
    "weekly_globex_normalized": ours_globex,
    "grid_key": "tradingDate (session date); values = [eventTime, marketEventType]",
    "es_2026_event_grid_by_tradingdate_from_present_captures": merged,
    "es_event_grid_full_incl_eventdate":
        {td: [{"eventDate": ed, "eventTime": tm, "marketEventType": mt}
              for ed, tm, mt in sorted(evs)] for td, evs in merged_full.items()},
    "per_capture_eventdates": {k: sorted(v.keys()) for k, v in grid_by_capture.items()},
}, open(os.path.join(OUT, "extracted_es_grid.json"), "w"), indent=1)

report = {
    "lane": "ES-READINESS",
    "round": "FUTURES-SIX-READINESS-20261004",
    "law": ("Q5 permitted captures used only after: our own sha256; re-extraction "
            "from raw bytes with this script (own parser, no Q5 code); comparison "
            "vs claimed values. No network access; read-only on P3 dir."),
    "q5_sources": {
        "coverage_json": COV,
        "captures_dir": CAP,
        "q5_lane_report": os.path.join(P3, "cal_permitted", "CAL_PERMITTED_RETRY.md"),
    },
    "digest_verification": {
        "n_claimed_files": len(claimed_files),
        "n_present": len(present),
        "n_missing_from_disk": len(missing),
        "missing_files": [r["file"] for r in missing],
        "missing_fetch_log_status":
            {r["file"]: ("in_log" if r.get("in_q5_fetch_log") else "NOT_IN_LOG")
             for r in missing},
        "all_present_digests_match_claims": digest_ok,
        "per_file": digest_rows,
    },
    "weekly_globex_string": {
        "claimed": claim_globex,
        "ours_from_raw_bytes": ours_globex,
        "match": weekly_match,
        "capture": "cspecs_133_20260405234659.json",
    },
    "es_2026_holiday_deviation_cells": {
        "n_claimed_cells": len(claimed_cells),
        "n_match": n_match,
        "n_extra_in_ours": n_extra,
        "n_missing_from_ours": n_missing,
        "n_mismatch": n_mismatch,
        "all_present_captures_reproduce_claimed_cells": (n_missing == 0 and n_mismatch == 0),
        "cells": cell_report,
    },
    "verdict": None,
}
report["verdict"] = (
    "VERIFIED_WITH_RESIDUALS" if (digest_ok and weekly_match and n_missing == 0
                                  and n_mismatch == 0 and missing)
    else ("VERIFIED_FULL" if (digest_ok and weekly_match and n_missing == 0
                              and n_mismatch == 0)
          else "FAILED"))

json.dump(report, open(os.path.join(OUT, "verify_report.json"), "w"), indent=1)

print(json.dumps({
    "verdict": report["verdict"],
    "digests": f'{len(present)} present / {len(missing)} missing; all_present_match={digest_ok}',
    "weekly_match": weekly_match,
    "cells": f"claimed={len(claimed_cells)} match={n_match} extra={n_extra} "
             f"missing={n_missing} mismatch={n_mismatch}",
    "missing_files": [r["file"] for r in missing],
}, indent=1))
sys.exit(0)
