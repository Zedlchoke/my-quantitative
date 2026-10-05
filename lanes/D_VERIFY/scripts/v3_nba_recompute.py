#!/usr/bin/env python
"""D_VERIFY own-code NBA feature recompute (independent implementation of
FEATURE_SPEC.md laws). Builds the full feature table from raw bytes, then
compares sampled rows (and full-table diagnostics) against the lane's parquet."""
import os, json
import numpy as np
import pandas as pd

HOME = os.path.expanduser("~")
OUTP = "/Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration/lanes/D_VERIFY/nba_recompute_output.json"

SEASONS = list(range(2016, 2027))
def sched_path(y): return f"{HOME}/.my-quantitative-data/nba-hoopr-v1/raw/nba_schedule_{y}.csv"
def box_path(y):
    if y in (2016, 2021, 2026):
        return f"{HOME}/.my-quantitative-data/playerdata-prep-v1/nba/player_box_raw/player_box_{y}.csv"
    return f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/nba/player_box_raw/player_box_{y}.csv"

rows_out = []
for y in SEASONS:
    s = pd.read_csv(sched_path(y), low_memory=False)
    s = s.rename(columns={"game_id": "gid", "season_type": "st", "home_id": "hid", "away_id": "aid"})
    s["gid"] = s["gid"].astype(np.int64)
    s["tip"] = pd.to_datetime(s["game_date_time"], utc=True, format="mixed")
    played = s[(s["status_type_name"] == "STATUS_FINAL") & s["home_score"].notna() & s["away_score"].notna()].copy()
    b = pd.read_csv(box_path(y), low_memory=False)
    b["gid"] = b["game_id"].astype(np.int64)
    b["athlete_id_num"] = pd.to_numeric(b["athlete_id"], errors="coerce")
    b["minutes_num"] = pd.to_numeric(b["minutes"], errors="coerce")
    b["minutes_filled"] = b["minutes_num"].fillna(0.0)
    b["dnp"] = b["did_not_play"].astype(str).str.lower().eq("true")
    b["usable"] = b["athlete_id_num"].notna() & (~b["dnp"])

    # per (game, team) box pack: usable frame + dnp set
    box_by_gt = {}
    for (gid, tid), g in b.groupby(["gid", "team_id"]):
        u = g[g["usable"]]
        box_by_gt[(gid, int(tid))] = {
            "u": u[["athlete_id_num", "minutes_filled", "points"]].values,
            "dnp": set(g.loc[g["dnp"], "athlete_id_num"].dropna().astype(np.int64)),
            "ath_min": u.set_index(u["athlete_id_num"].astype(np.int64))["minutes_filled"].to_dict() if len(u) else {},
            "ath_ppm_hist": None,
        }

    # team-game sequences (rules 1-4: same season, played, st != 5)
    seq_games = played[played["st"] != 5]
    teams_games = {}
    for _, r in seq_games.iterrows():
        teams_games.setdefault(int(r["hid"]), []).append((r["tip"], int(r["gid"]), int(r["st"])))
        teams_games.setdefault(int(r["aid"]), []).append((r["tip"], int(r["gid"]), int(r["st"])))
    for t in teams_games:
        teams_games[t].sort(key=lambda x: (x[0], x[1]))

    def top5_share(vals):
        # vals: Nx2 array minutes_filled, athlete_id; ties broken by ascending athlete_id
        if len(vals) == 0: return 0.0
        mins = vals[:, 1].astype(float)
        mass = mins.sum()
        if mass <= 0: return 0.0
        order = sorted(range(len(vals)), key=lambda i: (-mins[i], int(vals[i, 0])))
        return float(mins[order[:5]].sum() / mass)

    # walk each team sequence, emit rows for every played target game (incl. st5 + exhibition targets)
    played_all = played  # targets: every played game of the season (both sides)
    for _, g in played_all.iterrows():
        gid = int(g["gid"]); tip = g["tip"]; st = int(g["st"])
        for t, opp, is_home in ((int(g["hid"]), int(g["aid"]), 1), (int(g["aid"]), int(g["hid"]), 0)):
            seq = teams_games.get(t, [])
            priors = [x for x in seq if x[0] < tip]  # STRICT inequality
            team_games_so_far = len(priors)
            n_used = 0; shares_all = []; shares_last5 = []
            player_tot_min = {}; player_tot_pts = {}; player_ppm_hist = {}
            dnp_seq = []  # (index-in-priors, set of dnp athletes, prior key)
            seq_index = {}
            for i, (ptip, pgid, pst) in enumerate(priors):
                seq_index[pgid] = i
            for (ptip, pgid, pst) in priors:
                pack = box_by_gt.get((pgid, t))
                if pack is None or len(pack["u"]) == 0:
                    dnp_seq.append((pgid, set()))
                    continue
                n_used += 1
                u = pack["u"]
                sh = top5_share(u)
                shares_all.append(sh); shares_last5.append(sh)
                if len(shares_last5) > 5: shares_last5.pop(0)
                for aid, mn, pts in u:
                    aid = int(aid); mn = float(mn); pts = float(pts)
                    player_tot_min[aid] = player_tot_min.get(aid, 0.0) + mn
                    player_tot_pts[aid] = player_tot_pts.get(aid, 0.0) + pts
                    ppm = (pts / mn) if mn > 0 else 0.0
                    player_ppm_hist.setdefault(aid, []).append(ppm)
                    if len(player_ppm_hist[aid]) > 5: player_ppm_hist[aid].pop(0)
                dnp_seq.append((pgid, pack["dnp"]))

            # top-3 set
            elig = [a for a, m in player_tot_min.items() if m >= 24.0]
            elig.sort(key=lambda a: (-player_tot_min[a], a))
            top3 = elig[:3]
            forms = []
            for a in top3:
                tm = player_tot_min[a]
                base = player_tot_pts[a] / tm if tm > 0 else 0.0
                hist = player_ppm_hist.get(a, [])
                if hist: forms.append(float(np.mean(hist)) - base)
            b_form = float(np.mean(forms)) if forms else 0.0
            b_n = len(forms)

            neutral = 1 if (n_used < 5 or b_n == 0) else 0

            if neutral:
                a_share5 = 0.0; a_load = 0.0; b_form_v = 0.0
                c_out = 0; c_streak = 0
            else:
                a_share5 = float(np.mean(shares_last5)) if shares_last5 else 0.0
                a_load = a_share5 - (float(np.mean(shares_all)) if shares_all else 0.0)
                b_form_v = b_form
                # Group C with trade guard
                # priors list indexable: priors[i]; dnp_seq[i] aligned
                def guard_ok(p_aid, h_pos):
                    # p has a usable row for team t in >=1 of the 10 team-games immediately preceding h
                    lo = max(0, h_pos - 10)
                    for j in range(lo, h_pos):
                        pj = priors[j][1]
                        pack = box_by_gt.get((pj, t))
                        if pack is not None and p_aid in pack["ath_min"]:
                            return True
                    return False
                c_out = 0
                for h_pos in (len(priors) - 1, len(priors) - 2):
                    if h_pos < 0: continue
                    hgid, dnpset = dnp_seq[h_pos]
                    for p in top3:
                        if p in dnpset and guard_ok(p, h_pos):
                            c_out = 1; break
                    if c_out: break
                # streak for top-1
                c_streak = 0
                if top3:
                    p1 = top3[0]
                    for h_pos in range(len(priors) - 1, -1, -1):
                        hgid, dnpset = dnp_seq[h_pos]
                        pack = box_by_gt.get((priors[h_pos][1], t))
                        if p1 in dnpset:
                            if guard_ok(p1, h_pos):
                                c_streak += 1
                                continue
                            else:
                                break
                        elif pack is not None and p1 in pack["ath_min"]:
                            break  # played
                        else:
                            break  # no evidence / box-less
            rows_out.append({
                "game_id": gid, "season": y, "season_type": st, "team_id": t, "opponent_id": opp,
                "is_home": is_home, "tip_utc": tip, "team_games_so_far": team_games_so_far,
                "n_prior_games_used": n_used, "feature_neutral": neutral,
                "a_top5_share_k5": a_share5, "a_load_top5_k5": a_load,
                "b_form_top3": b_form_v, "b_form_top3_n": b_n,
                "c_abs_out": c_out, "c_abs_streak": c_streak,
            })

mine = pd.DataFrame(rows_out).sort_values(["season", "tip_utc", "game_id", "team_id"]).reset_index(drop=True)
print("my rows:", len(mine))

# ---- compare to lane table ----
lane = pd.read_parquet(f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/nba/features/nba_player_features_2016_2026.parquet")
lane = lane.sort_values(["season", "tip_utc", "game_id", "team_id"]).reset_index(drop=True)

key_mine = set(zip(mine.game_id, mine.team_id))
key_lane = set(zip(lane.game_id, lane.team_id))
diag = {
    "my_rows": len(mine), "lane_rows": len(lane),
    "keys_only_mine": len(key_mine - key_lane), "keys_only_lane": len(key_lane - key_mine),
}
m = mine.merge(lane, on=["game_id", "team_id"], suffixes=("_m", "_l"))
SCAL = ["a_top5_share_k5", "a_load_top5_k5", "b_form_top3"]
INTC = ["season", "season_type", "opponent_id", "is_home", "team_games_so_far",
        "n_prior_games_used", "feature_neutral", "b_form_top3_n", "c_abs_out", "c_abs_streak"]
bad = {}
for c in INTC:
    mm = m[f"{c}_m"].astype(float) != m[f"{c}_l"].astype(float)
    if mm.any(): bad[c] = int(mm.sum())
for c in SCAL:
    d = (m[f"{c}_m"].astype(float) - m[f"{c}_l"].astype(float)).abs()
    nd = int((d > 1e-9).sum())
    if nd: bad[c] = {"n_gt_1e-9": nd, "max_abs_diff": float(d.max())}
# neutral iff-zero both directions
nz1 = m[(m.feature_neutral_m == 1) & ((m.a_top5_share_k5_l != 0) | (m.a_load_top5_k5_l != 0) | (m.b_form_top3_l != 0) | (m.c_abs_out_l != 0) | (m.c_abs_streak_l != 0))]
nz2 = m[(m.feature_neutral_m == 0) & ((m.a_top5_share_k5_l == 0) & (m.a_load_top5_k5_l == 0) & (m.b_form_top3_l == 0) & (m.b_form_top3_n_l == 0))]
diag["mismatch_detail"] = bad
diag["neutral_violations"] = {"neutral_but_nonzero": int(len(nz1)), "nonneutral_allzero_n0": int(len(nz2))}
diag["max_abs_scalars"] = {c: float((m[f"{c}_m"].astype(float) - m[f"{c}_l"].astype(float)).abs().max()) for c in SCAL}

# sampled rows for the report: deterministic selection across seasons + special cases
samples = []
import random
random.seed(20261005)
sel_keys = set()
sel = []
# 1 neutral early-season
cand = mine[(mine.feature_neutral == 1)].sort_values("team_games_so_far")
r0 = cand.iloc[100]; sel.append((int(r0.game_id), int(r0.team_id), "neutral_early_season"))
# 2-7 spread
by_season = {s: g for s, g in m.groupby("season_l")}
for s in [2016, 2017, 2019, 2021, 2023, 2026]:
    g = by_season[s]
    row = g.iloc[random.randrange(len(g))]
    sel.append((int(row.game_id), int(row.team_id), f"random_{s}"))
# trade guard case: find Patty Mills in box 2025
b25 = pd.read_csv(box_path(2025), low_memory=False)
pm = b25[b25["athlete_display_name"].str.contains("Mills", na=False)]
pm_lac = pm[pm["team_id"] == 12]
pm_utah = pm[pm["team_id"] == 26]
guard_info = {
    "mills_rows_2025": int(len(pm)),
    "mills_LAC_rows": int(len(pm_lac)),
    "mills_last_UTAH_row": pm_utah[pm_utah["did_not_play"].astype(str).str.lower() == "false"]["game_date"].max() if len(pm_utah) else None,
    "mills_UTAH_dnp_rows": pm_utah[pm_utah["did_not_play"].astype(str).str.lower() == "true"][["game_id", "game_date"]].to_dict("records"),
}
if len(pm_lac):
    lac_gids = sorted(pm_lac["game_id"].astype(int).unique())
    # pick a mid-LAC-tenure game
    gid_pick = lac_gids[len(lac_gids)//2]
    for tid in (12, 26):
        lr = lane[(lane.game_id == gid_pick) & (lane.team_id == tid)]
        if len(lr): sel.append((gid_pick, tid, "mills_trade_guard_target"))
sel = [(k[0], k[1], k[2]) for k in sel]
srows = []
for gid, tid, why in sel:
    lm = m[(m.game_id == gid) & (m.team_id == tid)]
    if not len(lm):
        srows.append({"why": why, "game_id": gid, "team_id": tid, "found": False}); continue
    r = lm.iloc[0]
    srows.append({
        "why": why, "game_id": gid, "team_id": tid, "season": int(r.season_l),
        "team_games_so_far": {"mine": int(r.team_games_so_far_m), "lane": int(r.team_games_so_far_l)},
        "n_prior_games_used": {"mine": int(r.n_prior_games_used_m), "lane": int(r.n_prior_games_used_l)},
        "feature_neutral": {"mine": int(r.feature_neutral_m), "lane": int(r.feature_neutral_l)},
        "a_top5_share_k5": {"mine": float(r.a_top5_share_k5_m), "lane": float(r.a_top5_share_k5_l),
                             "absdiff": abs(float(r.a_top5_share_k5_m) - float(r.a_top5_share_k5_l))},
        "a_load_top5_k5": {"mine": float(r.a_load_top5_k5_m), "lane": float(r.a_load_top5_k5_l),
                            "absdiff": abs(float(r.a_load_top5_k5_m) - float(r.a_load_top5_k5_l))},
        "b_form_top3": {"mine": float(r.b_form_top3_m), "lane": float(r.b_form_top3_l),
                         "absdiff": abs(float(r.b_form_top3_m) - float(r.b_form_top3_l))},
        "b_form_top3_n": {"mine": int(r.b_form_top3_n_m), "lane": int(r.b_form_top3_n_l)},
        "c_abs_out": {"mine": int(r.c_abs_out_m), "lane": int(r.c_abs_out_l)},
        "c_abs_streak": {"mine": int(r.c_abs_streak_m), "lane": int(r.c_abs_streak_l)},
    })
diag["samples"] = srows
diag["mills_guard_info"] = guard_info

# is_exhibition cross-check on 3 box-less games
ex = lane[lane.game_id.isin([400900132, 400975285, 401070917])][["game_id", "team_id", "is_exhibition", "n_prior_games_used", "feature_neutral"]]
diag["boxless_game_rows"] = ex.to_dict("records")
diag["exhibition_rows_total"] = int(lane["is_exhibition"].sum())

print(json.dumps(diag, indent=1, default=str))
json.dump(diag, open(OUTP, "w"), indent=1, default=str)
