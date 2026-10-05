#!/usr/bin/env python
"""D_VERIFY counterfactual: recompute 2025 with trade guard DISABLED to prove the
frozen guard is load-bearing (i.e. without it, stale-DNP fabricates absences)."""
import os, json
import numpy as np
import pandas as pd

HOME = os.path.expanduser("~")
y = 2025
s = pd.read_csv(f"{HOME}/.my-quantitative-data/nba-hoopr-v1/raw/nba_schedule_{y}.csv", low_memory=False)
s = s.rename(columns={"game_id": "gid", "season_type": "st", "home_id": "hid", "away_id": "aid"})
s["gid"] = s["gid"].astype(np.int64)
s["tip"] = pd.to_datetime(s["game_date_time"], utc=True, format="mixed")
played = s[(s["status_type_name"] == "STATUS_FINAL") & s["home_score"].notna() & s["away_score"].notna()].copy()
b = pd.read_csv(f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/nba/player_box_raw/player_box_{y}.csv", low_memory=False)
b["gid"] = b["game_id"].astype(np.int64)
b["athlete_id_num"] = pd.to_numeric(b["athlete_id"], errors="coerce")
b["minutes_filled"] = pd.to_numeric(b["minutes"], errors="coerce").fillna(0.0)
b["dnp"] = b["did_not_play"].astype(str).str.lower().eq("true")
b["usable"] = b["athlete_id_num"].notna() & (~b["dnp"])
box_by_gt = {}
for (gid, tid), g in b.groupby(["gid", "team_id"]):
    u = g[g["usable"]]
    box_by_gt[(gid, int(tid))] = {"u": u[["athlete_id_num", "minutes_filled", "points"]].values,
                                  "dnp": set(g.loc[g["dnp"], "athlete_id_num"].dropna().astype(np.int64)),
                                  "ath_min": u.set_index(u["athlete_id_num"].astype(np.int64))["minutes_filled"].to_dict() if len(u) else {}}
seq_games = played[played["st"] != 5]
teams_games = {}
for _, r in seq_games.iterrows():
    teams_games.setdefault(int(r["hid"]), []).append((r["tip"], int(r["gid"])))
    teams_games.setdefault(int(r["aid"]), []).append((r["tip"], int(r["gid"])))
for t in teams_games: teams_games[t].sort()

def build(guard: bool):
    out = []
    for _, g in played.iterrows():
        gid = int(g["gid"]); tip = g["tip"]
        for t in (int(g["hid"]), int(g["aid"])):
            priors = [x for x in teams_games.get(t, []) if x[0] < tip]
            n_used = 0; shares_last5 = []; ptm = {}; ptp = {}
            dnp_seq = []
            for (ptip, pgid) in priors:
                pack = box_by_gt.get((pgid, t))
                if pack is None or len(pack["u"]) == 0:
                    dnp_seq.append(set()); continue
                n_used += 1
                u = pack["u"]; mins = u[:, 1].astype(float)
                mass = mins.sum()
                sh = 0.0 if mass <= 0 else float(mins[sorted(range(len(u)), key=lambda i: (-mins[i], int(u[i, 0])))[:5]].sum() / mass)
                shares_last5.append(sh)
                if len(shares_last5) > 5: shares_last5.pop(0)
                for aid, mn, pts in u:
                    aid = int(aid); mn = float(mn); pts = float(pts)
                    ptm[aid] = ptm.get(aid, 0.0) + mn
                    ptp[aid] = ptp.get(aid, 0.0) + pts
                dnp_seq.append(pack["dnp"])
            elig = [a for a, m in ptm.items() if m >= 24.0]
            elig.sort(key=lambda a: (-ptm[a], a))
            top3 = elig[:3]
            neutral = 1 if (n_used < 5 or not top3) else 0
            c_out = 0
            if not neutral:
                def guard_ok(p, hpos):
                    if not guard: return True
                    for j in range(max(0, hpos - 10), hpos):
                        pack = box_by_gt.get((priors[j][1], t))
                        if pack is not None and p in pack["ath_min"]: return True
                    return False
                for hpos in (len(priors) - 1, len(priors) - 2):
                    if hpos < 0: continue
                    if any(p in dnp_seq[hpos] and guard_ok(p, hpos) for p in top3):
                        c_out = 1; break
            out.append((gid, t, c_out))
    return pd.DataFrame(out, columns=["game_id", "team_id", "c_abs_out_noguard" if not guard else "c_abs_out"])

with_guard = build(True)
no_guard = build(False)
cmp = with_guard.merge(no_guard, on=["game_id", "team_id"])
diff = cmp[cmp.c_abs_out != cmp.c_abs_out_noguard]
lane = pd.read_parquet(f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/nba/features/nba_player_features_2016_2026.parquet")
lane25 = lane[lane.season == 2025][["game_id", "team_id", "c_abs_out"]]
chk = cmp.merge(lane25, on=["game_id", "team_id"])
print("2025 rows:", len(cmp))
print("rows where guard changes c_abs_out (counterfactual):", len(diff))
print("guard-on vs lane agree:", int((chk.c_abs_out_x == chk.c_abs_out_y).sum()), "/", len(chk))
print(diff.head(10).to_string())
json.dump({"rows": len(cmp), "guard_changes": len(diff),
           "guard_on_matches_lane": int((chk.c_abs_out_x == chk.c_abs_out_y).sum()),
           "sample_diffs": diff.head(10).to_dict("records")},
          open("/Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration/lanes/D_VERIFY/nba_guard_counterfactual_output.json", "w"), indent=1)
