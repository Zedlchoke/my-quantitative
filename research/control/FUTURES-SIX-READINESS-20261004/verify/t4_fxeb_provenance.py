"""VERIFY-A7READY T4 — FX-EB provenance chain.

Sample >= 6 new calendar cells traced cell -> capture file -> sha256 ->
fetch_log entry (or sibling-capture provenance):
  * ECH26 + ECM26 (sibling pcal_58_6e_20210703144932.json: own parse + sha256)
  * 3 BP cells (BPU24/BPU25/BPZ26) from this lane's pcal_42_6b_dl_20240903.xls
    (sha256 + xlrd re-extraction if xlrd present)
  * 1 6E holiday window 2023-09-03 (svc_20230903_20240708161439.json sha256 +
    raw-byte event grep)
Plus: fetch budget count (claim 19 attempts), and IMM-rule scan — every
OBTAINED cell/window in fx_eb/calendar/*.json + holiday JSON must carry
source_file + source_sha256 provenance keys (expect zero unprovenanced).
Writes verify/fxeb_provenance.json. Read-only everywhere.
"""
import hashlib
import json
import os
import re

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep"
ROUND = os.path.join(WT, "research/control/FUTURES-SIX-READINESS-20261004")
FX = os.path.join(ROUND, "fx_eb")
P3CAPS = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior"
          "/prep/research/control/FUTURES-P3-QUARANTINE-20261004/"
          "cal_permitted/captures")

res = {"schema": "verify_fxeb_provenance@1", "checks": {}}

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

cal = json.load(open(os.path.join(FX, "calendar/fx_eb_expiry_2023_2026.json")))

# ---------- fetch budget ----------
lines = [json.loads(l) for l in open(os.path.join(FX, "fetch_log.jsonl"))
         if l.strip()]
statuses = {}
for j in lines:
    s = j.get("status") or j.get("result") or "?"
    statuses[s] = statuses.get(s, 0) + 1
res["checks"]["fetch_budget"] = {
    "n_lines": len(lines), "claim": 19, "ok": len(lines) == 19,
    "statuses": statuses,
    "fields_sample": sorted(set(k for j in lines for k in j))[:20],
}

# ---------- ECH26 / ECM26 ----------
sib = os.path.join(P3CAPS, "pcal_58_6e_20210703144932.json")
sib_sha = sha256_file(sib)
cal_sha_6e = cal["6E"]["quarters"]["2026Q1"]["source_sha256"]
stext = open(sib, errors="replace").read()
sdata = json.loads(stext)
# find contract rows containing ECH26 / ECM26 and a last trade date
def find_contract(obj, codes, hits=None):
    if hits is None:
        hits = []
    if isinstance(obj, dict):
        blob = json.dumps(obj)
        for code in codes:
            if code in blob:
                hits.append((code, obj))
                break
    elif isinstance(obj, list):
        for v in obj:
            find_contract(v, codes, hits)
    return hits

hits = find_contract(sdata, ["ECH26", "ECM26"])
found = {}
for code, obj in hits:
    blob = json.dumps(obj)
    m = re.search(r'"lastTradeDate[^"]*"\s*:\s*"([\d-]+)"', blob)
    m2 = re.search(code + r'"[\s\S]{0,400}?"([\d]{4}-[\d]{2}-[\d]{2})"', blob)
    found[code] = {"raw_hit": blob[:300],
                   "lastTradeDate_field": m.group(1) if m else None,
                   "first_date_near": m2.group(1) if m2 else None}
res["checks"]["ech26_ecm26"] = {
    "sibling_capture": sib,
    "sibling_sha256": sib_sha,
    "calendar_source_sha256": cal_sha_6e,
    "sha_match": sib_sha == cal_sha_6e,
    "calendar_values": {
        "ECH26": cal["6E"]["quarters"]["2026Q1"]["last_trade_date"],
        "ECM26": cal["6E"]["quarters"]["2026Q2"]["last_trade_date"]},
    "reextracted": found,
}

# ---------- BP cells from XLS ----------
xls = os.path.join(FX, "captures/pcal_42_6b_dl_20240903.xls")
xls_sha = sha256_file(xls)
cal_sha_6b = cal["6B"]["quarters"]["2024Q3"]["source_sha256"]
bp = {"xls_path": xls, "our_sha256": xls_sha,
      "calendar_source_sha256": cal_sha_6b, "sha_match": xls_sha == cal_sha_6b}
try:
    import xlrd  # noqa
    book = xlrd.open_workbook(xls)
    sh = book.sheet_by_index(0)
    rows = []
    for r in range(sh.nrows):
        vals = [sh.cell_value(r, c) for c in range(sh.ncols)]
        rows.append(vals)
    bp["n_rows"] = sh.nrows
    # locate contract codes and nearby dates
    import datetime as _dt
    def cell_dates(row):
        out = []
        for v in row:
            if isinstance(v, float) and 40000 < v < 60000:
                d = _dt.date(1899, 12, 30) + _dt.timedelta(days=int(v))
                out.append(d.isoformat())
            elif isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                out.append(v)
        return out
    extracted = {}
    for code in ("BPU24", "BPU25", "BPZ26"):
        for row in rows:
            if any(isinstance(v, str) and v.strip() == code for v in row):
                dates = cell_dates(row)
                if dates:
                    extracted[code] = {"row": row[:6], "dates": dates}
                    break
    bp["xlrd_extracted"] = extracted
    bp["calendar_values"] = {
        "BPU24": cal["6B"]["quarters"]["2024Q3"]["last_trade_date"],
        "BPU25": cal["6B"]["quarters"]["2025Q3"]["last_trade_date"],
        "BPZ26": cal["6B"]["quarters"]["2026Q4"]["last_trade_date"],
    }
    bp["xlrd_available"] = True
except Exception as ex:
    bp["xlrd_available"] = False
    bp["xlrd_error"] = repr(ex)
res["checks"]["bp_from_product42_xls"] = bp

# ---------- 6E holiday window 2023-09-03 ----------
hol = json.load(open(os.path.join(FX, "holiday/holiday_deviation_6e_6b.json")))
win = [w for w in hol["6E"]["windows"]
       if w["window_first_event_date"] == "2023-09-03"][0]
cap = win["captures"][0]
cap_path = os.path.join(FX, "captures", cap["capture"])
cap_sha = sha256_file(cap_path)
cap_text = open(cap_path, errors="replace").read()
res["checks"]["holiday_6e_2023_09_03"] = {
    "window": win["window_first_event_date"],
    "status": win["status"],
    "capture": cap["capture"],
    "claimed_sha256": cap["sha256"],
    "our_sha256": cap_sha,
    "sha_match": cap_sha == cap["sha256"],
    "claimed_n_deviation_events": win["deviation_events"],
    "in_fetch_log": any(cap["capture"] in json.dumps(j) for j in lines),
    "capture_mentions_id58": ('"58"' in cap_text or "Future/58" in cap_text
                              or "productIds=58" in cap_text or "id=58" in cap_text),
}

# ---------- IMM-rule scan ----------
bad = []
n_obtained = 0
for code in ("6E", "6B"):
    for q, cell in cal[code]["quarters"].items():
        if cell.get("status") == "OBTAINED":
            n_obtained += 1
            sf = cell.get("source_file")
            ss = cell.get("source_sha256")
            if not sf or not ss:
                bad.append({"kind": "expiry", code: code, "quarter": q})
n_win_ok = 0
for sym in ("6E", "6B"):
    sec = hol[sym] if isinstance(hol[sym], dict) else {}
    for w in sec.get("windows", []):
        if str(w.get("status", "")).startswith("OBTAINED"):
            ok = all(c.get("sha256") and c.get("capture")
                     for c in w.get("captures", []))
            if ok:
                n_win_ok += 1
            else:
                bad.append({"kind": "holiday", "window":
                            w.get("window_first_event_date"), "sym": sym})
res["checks"]["imm_rule_scan"] = {
    "obtained_expiry_cells": n_obtained,
    "obtained_expiry_cells_lacking_provenance": len(
        [b for b in bad if b["kind"] == "expiry"]),
    "obtained_holiday_windows_with_capture_provenance": n_win_ok,
    "violations": bad,
    "law_text": cal.get("law"),
    "zero_unprovenanced": len(bad) == 0,
}

with open(os.path.join(ROUND, "verify/fxeb_provenance.json"), "w") as fh:
    json.dump(res, fh, indent=1, default=str)
print(json.dumps(res["checks"], indent=1, default=str)[:5000])
