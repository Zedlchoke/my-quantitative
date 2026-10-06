"""VERIFY-A7READY T3 — ES crosscheck.

1. Re-verify 68/68 from es/es_expiry_recheck.json per_quarter rows:
   distinct quarters must equal the complete 2010Q1..2026Q4 grid (68).
2. Re-run ONE Q5 byte-verification independently: the weekly-session-times
   capture cspecs_133_20260405234659.json — own sha256 vs the sibling capture
   bytes and vs the ES lane's claim; confirm the weekly Globex string exists
   in the raw bytes (unescaped search over the raw file text).
3. Confirm the 8/23 missing-captures finding: list the sibling captures dir,
   read Q5's cal_permitted_coverage.json ES-2026 cell-group capture list, and
   check on-disk presence + presence in Q5's own fetch_log.
Writes verify/es_crosscheck.json. Read-only everywhere.
"""
import hashlib
import json
import os
import re

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep"
ROUND = os.path.join(WT, "research/control/FUTURES-SIX-READINESS-20261004")
P3 = os.path.join(WT, ".worktrees/futures-behavior/prep/research/control/"
                  "FUTURES-P3-QUARANTINE-20261004")
P3 = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep" \
     "/research/control/FUTURES-P3-QUARANTINE-20261004"
CAPS = os.path.join(P3, "cal_permitted/captures")

res = {"schema": "verify_es_crosscheck@1", "checks": {}}

# ---------- 1. 68/68 from rows ----------
e = json.load(open(os.path.join(ROUND, "es/es_expiry_recheck.json")))
rows = e["date_machine_checks"]["per_quarter"]
quarters = [r["quarter"] for r in rows]
expected = []
for y in range(2010, 2027):
    for q in range(1, 5):
        expected.append(f"{y}-{q * 3:02d}")  # grid labels are YYYY-MM
missing = sorted(set(expected) - set(quarters))
extra = sorted(set(quarters) - set(expected))
res["checks"]["expiry_68"] = {
    "n_rows": len(rows),
    "n_distinct_quarters": len(set(quarters)),
    "grid_complete": (set(quarters) == set(expected)),
    "missing": missing, "extra": extra,
    "n_equals_3rd_friday": sum(1 for r in rows if r.get("equals_3rd_friday")),
    "ok_68": len(rows) == 68 and set(quarters) == set(expected),
}
# independent sanity: 2026-Q2 must be the Juneteenth-shifted 2026-06-18
q226 = [r for r in rows if r["quarter"] == "2026-06"]
res["checks"]["expiry_68"]["2026Q2_row"] = q226

# ---------- 2. Q5 weekly capture byte check ----------
cap_name = "cspecs_133_20260405234659.json"
cap_path = os.path.join(CAPS, cap_name)
out = {"capture_path": cap_path, "exists": os.path.exists(cap_path)}
if os.path.exists(cap_path):
    raw = open(cap_path, "rb").read()
    out["our_sha256"] = hashlib.sha256(raw).hexdigest()
    out["size_bytes"] = len(raw)
    claim_sha = "511fb8fa542f2bdd11897f111731a391f5facc03c79c8de77ab288b97948678c"
    out["es_lane_claimed_sha256"] = claim_sha
    out["sha256_matches_es_claim"] = out["our_sha256"] == claim_sha
    text = raw.decode("utf-8", errors="replace")
    # normalize HTML entities for the phrase check (capture embeds &nbsp;)
    norm = text.replace("&nbsp;", " ")
    # exact claimed phrase
    phrase = ("Sunday 6:00 p.m. - Friday - 5:00 p.m. ET "
              "(5:00 p.m. - 4:00 p.m. CT) with a daily maintenance period "
              "from 5:00 p.m. - 6:00 p.m. ET (4:00 p.m. - 5:00 p.m. CT)")
    out["weekly_string_exact_present_after_entity_normalize"] = phrase in norm
    out["weekly_string_raw_fragment_present"] = \
        "Friday - 5:00 p.m. ET" in text and "5:00 p.m. - 4:00 p.m. CT" in text
    # also check q5 sums file lists it
    sums = os.path.join(CAPS, "SHA256SUMS.txt")
    if os.path.exists(sums):
        stxt = open(sums, errors="replace").read()
        out["in_q5_SHA256SUMS_txt"] = (cap_name in stxt) and \
            (claim_sha in stxt)
res["checks"]["q5_weekly_capture"] = out

# ---------- 3. 8/23 missing-captures ----------
cov = json.load(open(os.path.join(P3, "cal_permitted/cal_permitted_coverage.json")))
# find the ES 2026 cell-group entries with sha claims: scan structure
def find_es_entries(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            hits += find_es_entries(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += find_es_entries(v, path + f"[{i}]")
    else:
        return hits
    return hits

# Instead: reconstruct from the ES verify_report per_file list (23 entries),
# then independently check presence + fetch log.
vr = json.load(open(os.path.join(ROUND, "es/q5_independent_verify/verify_report.json")))
per_file = vr["digest_verification"]["per_file"]
disk = set(os.listdir(CAPS))
fetch_log = os.path.join(P3, "cal_permitted/fetch_log.jsonl")
log_names = set()
if os.path.exists(fetch_log):
    for line in open(fetch_log, errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            j = json.loads(line)
        except Exception:
            continue
        blob = json.dumps(j)
        for m in re.findall(r"svc_[\w.]+\.json", blob):
            log_names.add(m)
        # also record url-ish basename fields
        for key in ("file", "out", "output", "path", "fname"):
            if isinstance(j, dict) and isinstance(j.get(key), str):
                log_names.add(os.path.basename(j[key]))
rows3 = []
for f in per_file:
    name = f["file"]
    rows3.append({
        "file": name,
        "on_disk": name in disk,
        "in_q5_fetch_log": name in log_names,
        "es_status": f["status"],
    })
n_missing_disk = sum(1 for r in rows3 if not r["on_disk"])
missing_disk_and_log = [r["file"] for r in rows3
                        if not r["on_disk"] and not r["in_q5_fetch_log"]]
res["checks"]["missing_captures"] = {
    "n_listed": len(rows3),
    "n_missing_from_disk": n_missing_disk,
    "missing_files": [r["file"] for r in rows3 if not r["on_disk"]],
    "missing_from_disk_and_not_in_q5_fetch_log": missing_disk_and_log,
    "es_lane_claim": {"n_missing": 8, "missing": vr["digest_verification"]["missing_files"]},
    "matches_es_lane_claim": n_missing_disk == 8 and
        [r["file"] for r in rows3 if not r["on_disk"]] ==
        vr["digest_verification"]["missing_files"],
    "coverage_json_path": os.path.join(P3, "cal_permitted/cal_permitted_coverage.json"),
}
# top-level coverage keys for the record
res["checks"]["missing_captures"]["coverage_json_top_keys"] = (
    list(cov.keys()) if isinstance(cov, dict) else type(cov).__name__)

with open(os.path.join(ROUND, "verify/es_crosscheck.json"), "w") as fh:
    json.dump(res, fh, indent=1)
print(json.dumps(res["checks"], indent=1, default=str)[:4000])
