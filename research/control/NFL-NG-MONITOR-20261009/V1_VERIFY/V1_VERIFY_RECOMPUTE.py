#!/usr/bin/env python
"""V1 independent recompute for NFL-NG-MONITOR-20261009 (A7-style verifier).

Fresh-context, independent implementation. READ-ONLY on all cycle paths.
Writes nothing outside this V1_VERIFY directory (and nothing at all unless
--write-outputs is passed; the verifier passes it to drop a results JSON in
its own verify dir only).
"""
import csv
import datetime as dt
import hashlib
import json
import math
import os
import sys

REPO = "/Users/hoangminhlong/my-quantitative"
DATA = "/Users/hoangminhlong/.my-quantitative-data/nfl-ng-monitor-20261009"
NG_DATA = "/Users/hoangminhlong/.my-quantitative-data/nfl-ng-scored-v1"
LEDGER = f"{NG_DATA}/predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl"
STAGING = f"{REPO}/research/control/NFL-NG-MONITOR-20261009"

EXPECT = {
    "ledger_sha": "7d9af2867b480f08c7b195398e15f927fd45172e25899130125a7e8f1a922c90",
    "games_sha": "9c925388e875b6e90c4ba21e7029e0a0ff44648d4528dcab080d1c11dbe560e1",
    "timestamp_sha": "0081235036d5199df02b4c11ef12515875f63d6e23fe090cd6038236abee47a2",
    "report_arm": {  # values as printed (6dp) in MONITORING_REPORT_20261009.md
        "B0": {"p_home": 0.571399, "ll": 0.847229, "brier": 0.326497},
        "B1_STAR": {"p_home": 0.544343, "ll": 0.786015, "brier": 0.296309},
        "C3": {"p_home": 0.529183, "ll": 0.753286, "brier": 0.280035},
    },
    # full-precision values in monitor_results_20261009.json
    "results_json": {
        "B0": {"ll": 0.8472288627675941, "brier": 0.326496817201},
        "B1_STAR": {"ll": 0.7860149454892909, "brier": 0.29630930164900005},
        "C3": {"ll": 0.7532857954968586, "brier": 0.280034647489},
    },
}

out = {"checks": [], "fail": []}


def check(name, ok, detail):
    out["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
    if not ok:
        out["fail"].append(name)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- 1. ledger ----------
ledger_sha = sha256(LEDGER)
st = os.stat(LEDGER)
ledger_mtime = dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc)
with open(LEDGER, "rb") as f:
    raw = f.read()
lines = raw.decode("utf-8").splitlines()
rows = [json.loads(l) for l in lines]

check("1a ledger sha256 == 7d9af286...", ledger_sha == EXPECT["ledger_sha"],
      f"{ledger_sha}")
check("1b ledger line count == 129", len(lines) == 129 and len(rows) == 129,
      f"{len(lines)} lines, {len(rows)} parsed rows")
check("1c ledger mtime predates monitor retrieval 2026-10-09T10:58:11Z",
      ledger_mtime < dt.datetime(2026, 10, 9, 10, 58, 11, tzinfo=dt.timezone.utc),
      f"mtime={ledger_mtime.isoformat()}")

gid_counts = {}
arms_seen = set()
schema_ok = cycle_ok = season_ok = type_ok = by_ok = True
prematch_ok = True
for r in rows:
    gid_counts[r["game_id"]] = gid_counts.get(r["game_id"], 0) + 1
    arms_seen.add(r["arm_id"])
    schema_ok &= r["schema_version"] == "nfl_ng_ledger@1"
    cycle_ok &= r["cycle_id"] == "NFL-WINPROB-NG-SCORED-V1"
    season_ok &= r["season"] == 2026
    type_ok &= r["game_type"] == "REG"
    by_ok &= r["recorded_by"] == "EXEC-POST-GO-EXECUTOR"
    prematch_ok &= r["recorded_at_utc"] < r["kickoff_utc"]

gids = sorted(gid_counts)
check("1d 43 distinct game_ids, each exactly 3 rows",
      len(gids) == 43 and set(gid_counts.values()) == {3},
      f"{len(gids)} game_ids; rows-per-game multiset={sorted(set(gid_counts.values()))}")
check("1e arms exactly {B0,B1_STAR,C3}", arms_seen == {"B0", "B1_STAR", "C3"},
      f"arms={sorted(arms_seen)}")
check("1f all rows schema/cycle/season/type/recorded_by conform",
      schema_ok and cycle_ok and season_ok and type_ok and by_ok,
      f"schema_ok={schema_ok} cycle_ok={cycle_ok} season2026={season_ok} REG={type_ok} "
      f"recorded_by_ok={by_ok}")
check("1g extra: every row recorded BEFORE kickoff (pre-match identity)",
      prematch_ok, f"all_recorded_at_lt_kickoff={prematch_ok}")

wk_games = {}
for g in gids:
    wk_games.setdefault(g.split("_")[1], set()).add(g)
wk_counts = {w: len(s) for w, s in sorted(wk_games.items())}
check("1h week games 05/06/07 == 15/14/14",
      wk_counts == {"05": 15, "06": 14, "07": 14}, f"{wk_counts}")

per_arm_wk = {}
for r in rows:
    per_arm_wk.setdefault((r["arm_id"], r["game_id"].split("_")[1]), 0)
    per_arm_wk[(r["arm_id"], r["game_id"].split("_")[1])] += 1
arm_wk_ok = all(per_arm_wk.get((a, w)) == n for a in ("B0", "B1_STAR", "C3")
                for w, n in (("05", 15), ("06", 14), ("07", 14)))
check("1i per-arm-per-week 15/14/14 for each arm", arm_wk_ok,
      f"{dict(sorted(((f'{a}_w{w}', n) for (a, w), n in per_arm_wk.items())))}")

kicks = sorted(r["kickoff_utc"] for r in rows)
check("1j kickoff range", kicks[0] == "2026-10-09T00:15:00Z"
      and kicks[-1] == "2026-10-27T00:15:00Z",
      f"{kicks[0]} .. {kicks[-1]}")

# hash chain (linkage + row_hash recomputation)
genesis_anchor = "9978a950cfa52f531c6cc1ccf650ca46cfcecb5a0d38c8468f6a66381ef70f6e"
link_ok = recompute_ok = True
prev_expect = f"GENESIS:{genesis_anchor}"
for i, r in enumerate(rows):
    link_ok &= (r["prev_row_hash"] == prev_expect)
    payload = {k: v for k, v in r.items() if k != "row_hash"}
    rh = hashlib.sha256(json.dumps(payload, sort_keys=False,
                                   separators=(",", ":")).encode("utf-8")).hexdigest()
    recompute_ok &= (rh == r["row_hash"])
    prev_expect = r["row_hash"]
check("1k extra: hash chain links + row_hash recomputation (129)",
      link_ok and recompute_ok,
      f"links_ok={link_ok} row_hash_recompute_ok={recompute_ok}")

# ---------- 2. snapshot provenance ----------
games_sha = sha256(f"{DATA}/games.csv")
ts_sha = sha256(f"{DATA}/timestamp.json")
prov = json.load(open(f"{DATA}/provenance_monitor_20261009.json"))
ts_content = json.load(open(f"{DATA}/timestamp.json"))
check("2a games.csv sha == 9c925388...", games_sha == EXPECT["games_sha"], games_sha)
check("2b timestamp.json sha == 00812350...", ts_sha == EXPECT["timestamp_sha"], ts_sha)
check("2c provenance JSON records both shas + retrieval_utc",
      prov["sha256"]["games.csv"] == games_sha
      and prov["sha256"]["timestamp.json"] == ts_sha
      and prov["retrieval_utc"] == "2026-10-09T10:58:11Z",
      f"retrieval_utc={prov['retrieval_utc']}")
check("2d provenance ledger_sha == computed ledger sha",
      prov["ledger_sha256"] == ledger_sha, f"{prov['ledger_sha256'][:12]}...")
check("2e timestamp.json content fresh (2026-10-09 06:46:37 EDT)",
      ts_content == {"last_updated": "2026-10-09 06:46:37 EDT"}, f"{ts_content}")
rep = open(f"{STAGING}/MONITORING_REPORT_20261009.md").read()
check("2f report quotes same games.csv sha + retrieval time",
      EXPECT["games_sha"] in rep and "2026-10-09T10:58:11Z" in rep, "report text match")

# ---------- 3. FINAL/PENDING split from snapshot (own code) ----------
with open(f"{DATA}/games.csv", newline="") as f:
    snap = {r["game_id"]: r for r in csv.DictReader(f)}
print(f"snapshot rows total: {len(snap)}")

final, pending, missing, partial, identity_bad = [], [], [], [], []
for g in gids:
    s = snap.get(g)
    if s is None:
        missing.append(g)
        continue
    a, h = str(s["away_score"]).strip(), str(s["home_score"]).strip()
    if a == "" and h == "":
        pending.append(g)
    elif a != "" and h != "":
        res, tot = str(s.get("result", "")).strip(), str(s.get("total", "")).strip()
        final.append((g, int(a), int(h), res, tot))
    else:
        partial.append((g, s["away_score"], s["home_score"]))
    # identity check vs ledger B0 row
    lrow = next(r for r in rows if r["game_id"] == g and r["arm_id"] == "B0")
    if s["home_team"] != lrow["home_team"] or s["away_team"] != lrow["away_team"]:
        identity_bad.append(g)

check("3a no join failures (all 43 gids in snapshot)", not missing,
      f"missing={missing}")
check("3b exactly 1 FINAL", len(final) == 1, f"{final}")
g, a, h, res, tot = final[0]
check("3c FINAL is 2026_05_TB_DAL with TB 24 @ DAL 16 (away 24 home 16)",
      g == "2026_05_TB_DAL" and a == 24 and h == 16,
      f"game={g} away_score={a} home_score={h} result={res!r} total={tot!r}")
check("3d other 42 PENDING with both score fields empty",
      len(pending) == 42, f"pending_n={len(pending)} partial={partial}")
check("3e no partial/ambiguous score states", not partial, f"{partial}")
check("3f home/away identity ledger==snapshot for all 43", not identity_bad,
      f"bad={identity_bad}")
# derived consistency on the FINAL row
check("3g FINAL row derived fields consistent (result/total/overtime populated)",
      res != "" and tot != "", f"result={res!r} total={tot!r} "
      f"overtime={snap[g].get('overtime','')!r}")

# ---------- 4. per-arm descriptor recompute from ledger rows ----------
y = 1 if h > a else 0  # home-win indicator; DAL(16) < TB(24) -> y=0 (away won)
metrics = {}
for arm in ("B0", "B1_STAR", "C3"):
    prow = next(r for r in rows if r["game_id"] == g and r["arm_id"] == arm)
    p = float(prow["p_home"])
    ll = -(y * math.log(p) + (1 - y) * math.log(1 - p))
    brier = (p - y) ** 2
    acc = 1.0 if (p > 0.5) == bool(y) else 0.0
    metrics[arm] = {"p_home": p, "ll": ll, "brier": brier, "acc": acc,
                    "p_home_str": prow["p_home"]}

print(json.dumps({a: {k: v for k, v in m.items() if k != 'p_home_str'}
                  for a, m in metrics.items()}, indent=2))

for arm in ("B0", "B1_STAR", "C3"):
    m = metrics[arm]
    e = EXPECT["report_arm"][arm]
    rj = EXPECT["results_json"][arm]
    check(f"4{chr(97+(['B0','B1_STAR','C3'].index(arm)))} {arm} p_home ledger==report",
          abs(m["p_home"] - e["p_home"]) < 1e-12,
          f"ledger={m['p_home_str']} report={e['p_home']}")
    check(f"4{chr(100+['B0','B1_STAR','C3'].index(arm))} {arm} LL matches report 6dp (1e-6)",
          abs(m["ll"] - e["ll"]) < 1e-6,
          f"recomputed={m['ll']:.12f} report={e['ll']} drift={abs(m['ll']-e['ll']):.2e}")
    check(f"4{chr(103+['B0','B1_STAR','C3'].index(arm))} {arm} Brier matches report 6dp (1e-6)",
          abs(m["brier"] - e["brier"]) < 1e-6,
          f"recomputed={m['brier']:.12f} report={e['brier']} drift={abs(m['brier']-e['brier']):.2e}")
    check(f"4{chr(106+['B0','B1_STAR','C3'].index(arm))} {arm} matches results-JSON full precision",
          abs(m["ll"] - rj["ll"]) < 1e-12 and abs(m["brier"] - rj["brier"]) < 1e-12,
          f"ll_drift={abs(m['ll']-rj['ll']):.2e} brier_drift={abs(m['brier']-rj['brier']):.2e}")
    check(f"4{chr(109+['B0','B1_STAR','C3'].index(arm))} {arm} p_home>0.5 on DAL & accuracy 0.0",
          m["p_home"] > 0.5 and m["acc"] == 0.0,
          f"p_home={m['p_home']} acc={m['acc']}")

check("4m all three arms LL ordering B1_STAR < B0, C3 < B1_STAR (monotone in p_home on this obs)",
      metrics["C3"]["ll"] < metrics["B1_STAR"]["ll"] < metrics["B0"]["ll"],
      f"C3={metrics['C3']['ll']:.6f} < B1_STAR={metrics['B1_STAR']['ll']:.6f} "
      f"< B0={metrics['B0']['ll']:.6f}")

# ---------- 5. artifacts consistency / writes detection ----------
staging_py = sha256(f"{STAGING}/monitor_analysis.py")
data_py = sha256(f"{DATA}/monitor_analysis.py")
staging_csv = sha256(f"{STAGING}/joined_monitor_20261009.csv")
data_csv = sha256(f"{DATA}/joined_monitor_20261009.csv")
check("5a monitor_analysis.py identical in repo staging vs data dir", staging_py == data_py,
      staging_py[:16])
check("5b joined CSV identical in repo staging vs data dir", staging_csv == data_csv,
      staging_csv[:16])
with open(f"{STAGING}/joined_monitor_20261009.csv", newline="") as f:
    jrows = list(csv.DictReader(f))
final_csv = [r for r in jrows if r["status"] == "FINAL"]
check("5c joined CSV: 43 rows, 1 FINAL with outcome_home_win=0",
      len(jrows) == 43 and len(final_csv) == 1
      and final_csv[0]["outcome_home_win"] == "0"
      and final_csv[0]["game_id"] == "2026_05_TB_DAL",
      f"rows={len(jrows)} final={[r['game_id'] for r in final_csv]}")

fire = f"{NG_DATA}/cadence/fire_log.jsonl"
fire_mtime = dt.datetime.fromtimestamp(os.stat(fire).st_mtime, dt.timezone.utc)
check("5d NG cadence fire_log mtime predates monitor window",
      fire_mtime < dt.datetime(2026, 10, 9, 10, 50, 0, tzinfo=dt.timezone.utc),
      f"mtime={fire_mtime.isoformat()} sha={sha256(fire)[:16]}")

# any file in NG data dir modified during monitor window?
window_new = []
for root, dirs, files in os.walk(NG_DATA):
    for fn in files:
        p = os.path.join(root, fn)
        m = dt.datetime.fromtimestamp(os.stat(p).st_mtime, dt.timezone.utc)
        if m >= dt.datetime(2026, 10, 9, 10, 55, 0, tzinfo=dt.timezone.utc):
            window_new.append((p, m.isoformat()))
check("5e nothing in NG data dir modified/created during-or-after monitor window (>=10:55Z)",
      not window_new, f"hits={window_new[:5] if window_new else 'none'}")

# monitor data dir mtimes fit the declared window
mon_files = {}
for fn in sorted(os.listdir(DATA)):
    p = os.path.join(DATA, fn)
    mon_files[fn] = dt.datetime.fromtimestamp(os.stat(p).st_mtime, dt.timezone.utc).isoformat()
print("monitor data dir mtimes (UTC):", json.dumps(mon_files, indent=2))

# ---------- language audit of the committed report ----------
import re
hits = {}
for pat in (r"\bedge\b", r"\bbet", r"\bwager", r"\bprofit", r"\bodds\b", r"\bstake",
            r"\bROI\b", r"\bEV\b", r"expected value", r"positiv", r"skill",
            r"DESCRIPTIVE_MONITORING", r"READ-ONLY", r"NO scored", r"zero inferential"):
    hits[pat] = [(rep.count("\n", 0, m.start()) + 1, rep[max(0, m.start() - 60):m.end() + 60]
                  .replace("\n", " ")) for m in re.finditer(pat, rep, re.IGNORECASE)]
print("LANGUAGE AUDIT HITS:")
for pat, hh in hits.items():
    print(f"  {pat}: {len(hh)}")
    for ln, ctx in hh:
        print(f"    L{ln}: ...{ctx}...")

has_label = "DESCRIPTIVE_MONITORING" in rep
has_disclosures = ("NO scored-cell budget" in rep and "modifies" in rep
                   and "NO ledger" in rep and "READ-ONLY" in rep)
affirm = []
for pat in (r"\bedge\b", r"\bbet", r"\bwager", r"\bprofit", r"\bodds\b", r"\bstake",
            r"\bROI\b", r"\bEV\b", r"expected value"):
    for ln, ctx in hits[pat]:
        # negation/disclosure context heuristics
        low = ctx.lower()
        if not any(neg in low for neg in ("no ", "not", "nor ", "nothing", "without",
                                          "zero", "refus", "support no")):
            affirm.append((pat, ln, ctx))
check("5f report carries DESCRIPTIVE_MONITORING label", has_label, f"label={has_label}")
check("5g report carries explicit no-budget/no-ledger/read-only disclosures",
      has_disclosures, f"disclosures={has_disclosures}")
check("5h no affirmative edge/betting/profitability language (all hits are negations)",
      not affirm, f"affirmative_hits={affirm if affirm else 'none'}")

out["metrics"] = {a: {k: v for k, v in m.items()} for a, m in metrics.items()}
out["ledger_sha"] = ledger_sha
out["games_sha"] = games_sha
out["ts_sha"] = ts_sha
out["wk_counts"] = wk_counts
out["fail"] = out["fail"]

if "--write-outputs" in sys.argv:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "V1_VERIFY_RESULTS.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("wrote V1_VERIFY_RESULTS.json in verify dir")

print()
print("TOTAL FAILS:", out["fail"] if out["fail"] else "NONE — all checks PASS")
