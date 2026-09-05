#!/usr/bin/env python3
"""A7 C3: data/PIT authority — recompute ledger pin, base prefix byte-identity,
dedupe semantics (61 upgrades, monotone UNEVIDENCED->EVIDENCED), A-2 87-row count,
evidenced vintages 8/8, snapshot digests 156/156, read-only data discipline."""
import hashlib, json, subprocess
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v4/q-a7-prelaunch")
# data_raw/ is gitignored; the operative bytes for the scored run live in the
# integration tree. Audit those bytes; q-a7-prelaunch controls/ledger are identical
# bytes (git-tracked), asserted below.
DATA_ROOT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v4/integration")
TWIN_ROOT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v4/r-reproduce")
LEDGER = ROOT / "research/control/forex_free_v4_run/announcement_ledger.jsonl"
LEDGER_INTEG = DATA_ROOT / "research/control/forex_free_v4_run/announcement_ledger.jsonl"
BASE_LEDGER = ROOT / "research/control/forex_free_v4_run/announcement_ledger_base_v1.jsonl"
PIN_FILE = ROOT / "research/control/forex_free_v4_run/LEDGER_PINNED"
P0A = ROOT / "research/control/forex_free_v4_run/p0a_evidenced_vintages_manifest.json"
SNAP = ROOT / "research/control/forex_free_v1_run/staged_data_manifest.json"
VINT_DIR = DATA_ROOT / "data_raw/forex_free_v4_macro_evidenced"
NY = ZoneInfo("America/New_York")

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return sha_bytes(Path(p).read_bytes())
def ny_bar_at_or_after(t):
    d = t.astimezone(NY).date() - timedelta(days=1)
    for _ in range(6):
        bar = datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY)
        if bar >= t:
            return bar
        d += timedelta(days=1)
    return None

out = {"check": "C3_data_pit_authority"}

# 1. ledger pin
raw = LEDGER.read_bytes()
led_sha = sha_bytes(raw)
out["ledger"] = {
    "sha256": led_sha,
    "pin_expected": "ae5e1f2e64b8aa7c08472755bd73857543aa89b72ea81b70ad5c5d81e7cd6bd4",
    "match": led_sha == "ae5e1f2e64b8aa7c08472755bd73857543aa89b72ea81b70ad5c5d81e7cd6bd4",
    "rows": len(raw.splitlines()),
    "pin_file": PIN_FILE.read_text().strip() if PIN_FILE.exists() else None,
}

# 2. base prefix byte-identity
lines = raw.splitlines(keepends=True)
prefix = b"".join(lines[:159])
base_bytes = BASE_LEDGER.read_bytes()
out["base_prefix"] = {
    "prefix_sha256": sha_bytes(prefix),
    "base_pin": "169b9e447f01ba0114396a3f26f208f57f61008a6ce6e30873e3b6642f8cf895",
    "match_base_pin": sha_bytes(prefix) == "169b9e447f01ba0114396a3f26f208f57f61008a6ce6e30873e3b6642f8cf895",
    "byte_eq_base_ledger_file": prefix == base_bytes,
    "base_ledger_sha256": sha_bytes(base_bytes),
}

# 2b. cross-tree ledger identity (audit tree vs integration) + appended rows are
# upgrades of keys ALREADY PRESENT in the base prefix
out["ledger"]["byte_eq_integration_tree"] = raw == LEDGER_INTEG.read_bytes()
base_keys = set()
for l in lines[:159]:
    r = json.loads(l)
    base_keys.add((r["area"], r["effective_date"]))
appended = [json.loads(l) for l in lines[159:]]
not_in_base = [(r["area"], r["effective_date"]) for r in appended
               if (r["area"], r["effective_date"]) not in base_keys]
out["appended_rows"] = {
    "n": len(appended),
    "keys_all_in_base_prefix": not not_in_base,
    "keys_not_in_base": not_in_base[:10],
    "statuses": sorted({r["announcement"].get("status") for r in appended}),
    "areas": sorted({r["area"] for r in appended}),
}

# 3. dedupe semantics
rows = [json.loads(l) for l in raw.splitlines()]
rtc = {}
for r in rows:
    rtc[r.get("row_type")] = rtc.get(r.get("row_type"), 0) + 1
dedup, dup = {}, {}
for r in rows:
    k = (r["area"], r["effective_date"])
    dedup.setdefault(k, []).append(r)
dup = {k: v for k, v in dedup.items() if len(v) > 1}
def ev_rank(s): return 1 if (s or "").startswith("EVIDENCED") else 0
dirs, nonmono = {}, []
for k, v in dup.items():
    for a, b in zip(v, v[1:]):
        d = f"{a['announcement'].get('status')}->{b['announcement'].get('status')}"
        dirs[d] = dirs.get(d, 0) + 1
        if ev_rank(b["announcement"].get("status")) < ev_rank(a["announcement"].get("status")):
            nonmono.append(k)
keepers = [v[-1] for v in dedup.values()]
kst = {}
for k in keepers:
    s = k["announcement"].get("status")
    kst[s] = kst.get(s, 0) + 1
out["dedupe"] = {
    "row_type_counts": rtc,
    "raw_rate_change_rows": rtc.get("RATE_CHANGE"),
    "deduped_keys": len(dedup),
    "keys_with_duplicates": len(dup),
    "upgrade_rows": sum(len(v) - 1 for v in dup.values()),
    "upgrade_direction_counts": dirs,
    "non_monotone": nonmono,
    "keeper_status_counts": kst,
}

# 4. A-2 recompute: pre-announcement rows on the deduped basis + raw basis
def is_dt(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))
pre_keep = [k for k in keepers
            if k.get("effective_time_utc") and k["announcement"].get("operative_available_time_utc")
            and is_dt(k["effective_time_utc"]) > is_dt(k["announcement"]["operative_available_time_utc"])]
pre_raw = [r for r in rows if r.get("row_type") == "RATE_CHANGE" and r.get("effective_time_utc")
           and r["announcement"].get("operative_available_time_utc")
           and is_dt(r["effective_time_utc"]) > is_dt(r["announcement"]["operative_available_time_utc"])]
out["a2"] = {
    "pre_announcement_deduped": len(pre_keep),
    "pre_announcement_raw": len(pre_raw),
}
# verify precomputed first_readable == first NY-16:00 bar >= max(effective, available) on all keepers
mism = []
for k in keepers:
    eff, avail, fr = k.get("effective_time_utc"), k["announcement"].get("operative_available_time_utc"), k.get("first_readable_decision_utc")
    if not (eff and avail and fr):
        continue
    bound = max(is_dt(eff), is_dt(avail))
    comp = ny_bar_at_or_after(bound)
    fr_dt = is_dt(fr)
    if comp is None or comp.astimezone(comp.tzinfo) != fr_dt.astimezone(comp.tzinfo):
        mism.append({"area": k["area"], "eff": eff, "avail": avail, "ledger_fr": fr,
                     "computed": comp.isoformat() if comp else None})
out["a2"]["first_readable_vs_max_rule_mismatches"] = len(mism)
out["a2"]["first_readable_examples"] = mism[:5]

# 5. evidenced vintages 8/8
man = json.loads(P0A.read_text())
vres, vok = {}, 0
for ccy, ent in sorted(man["per_area"].items()):
    p = VINT_DIR / f"{ccy}.json"
    exists = p.is_file()
    actual = sha_file(p) if exists else None
    ok = exists and actual == ent["evidenced_sha256_canonical"]
    vok += bool(ok)
    vres[ccy] = {"manifest": ent["evidenced_sha256_canonical"], "tree": actual, "match": ok}
out["evidenced_vintages"] = {"n": len(man["per_area"]), "match": vok, "fatal": man.get("fatal"), "detail": vres}

# 6. snapshot digests 156/156
sm = json.loads(SNAP.read_text())
digs = sm["digests_exec2"]
snap_ok, snap_miss, snap_detail = 0, [], {}
for rel, exp in digs.items():
    p = DATA_ROOT / rel
    exists = p.is_file()
    actual = sha_file(p) if exists else None
    ok = exists and actual == exp
    snap_ok += bool(ok)
    if not ok:
        snap_miss.append({"rel": rel, "exists": exists})
out["snapshots"] = {"manifest_entries": len(digs), "match": snap_ok, "missing_or_mismatch": snap_miss[:10],
                    "byte_identical_exec_repro_flag": sm.get("byte_identical_exec_repro")}

# 6b. twin-tree byte identity: every evidenced vintage + every snapshot also
# hashes identically in the r-reproduce tree
twin_vint = {"same": 0, "diff": []}
for ccy, ent in sorted(man["per_area"].items()):
    tp = TWIN_ROOT / "data_raw/forex_free_v4_macro_evidenced" / f"{ccy}.json"
    if tp.is_file() and sha_file(tp) == sha_file(VINT_DIR / f"{ccy}.json"):
        twin_vint["same"] += 1
    else:
        twin_vint["diff"].append(ccy)
twin_snap = {"same": 0, "diff": []}
for rel, exp in digs.items():
    ip, tp = DATA_ROOT / rel, TWIN_ROOT / rel
    if ip.is_file() and tp.is_file() and sha_file(ip) == sha_file(tp) == exp:
        twin_snap["same"] += 1
    else:
        twin_snap["diff"].append(rel)
out["twin_tree"] = {"vintages_same": twin_vint, "snapshots_same": twin_snap["same"],
                    "snapshots_diff_count": len(twin_snap["diff"]),
                    "snapshots_diff_sample": twin_snap["diff"][:5]}

# 7. read-only discipline: no code writes into data_raw
hits = []
for base in ("research/assets/forex_free_v4", "research/assets/forex_free_v3"):
    for p in (ROOT / base).rglob("*.py"):
        txt = p.read_text(errors="replace")
        for i, ln in enumerate(txt.splitlines(), 1):
            low = ln.lower()
            if "data_raw" in low and any(w in low for w in ("open(", "write", "to_csv", "to_json", "mkdir", "unlink", "rename", "shutil", "dump(")):
                hits.append(f"{p.relative_to(ROOT)}:{i}: {ln.strip()[:110]}")
out["read_only_discipline"] = {"suspicious_write_hits": hits}

ok = (out["ledger"]["match"] and out["base_prefix"]["match_base_pin"] and out["base_prefix"]["byte_eq_base_ledger_file"]
      and out["ledger"]["byte_eq_integration_tree"] and out["appended_rows"]["keys_all_in_base_prefix"]
      and out["dedupe"]["upgrade_rows"] == 61 and not out["dedupe"]["non_monotone"]
      and out["dedupe"]["raw_rate_change_rows"] == 212
      and set(out["dedupe"]["upgrade_direction_counts"]) == {"AVAILABILITY_UNEVIDENCED->EVIDENCED"}
      and out["evidenced_vintages"]["match"] == 8 and out["evidenced_vintages"]["n"] == 8
      and out["snapshots"]["match"] == 156 and out["snapshots"]["manifest_entries"] == 156
      and out["twin_tree"]["vintages_same"]["diff"] == [] and out["twin_tree"]["snapshots_diff_count"] == 0
      and not out["read_only_discipline"]["suspicious_write_hits"])
out["verdict"] = "PASS" if ok else "REVIEW"
print(json.dumps(out, indent=1))
