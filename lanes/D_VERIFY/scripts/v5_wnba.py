#!/usr/bin/env python
"""D_VERIFY own-code WNBA verification: universe re-derivation, per-season join
rates, worked-example recomputes (Group A continuity / B minutes / C absence),
outcome-column scan. Independent implementation from FEATURE_SPEC text."""
import os, json
import numpy as np
import pandas as pd

HOME = os.path.expanduser("~")
CORP = f"{HOME}/.my-quantitative-data/wnba-prep-v1/roster_audit"
SCHED = f"{HOME}/.my-quantitative-data/wnba-v1/raw/espn_schedules"
OUTP = "/Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration/lanes/D_VERIFY/wnba_output.json"

ALLSTAR = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE", "CLA", "COL", "SPO", "COOP", "WNBASTARS"}
YEARS = list(range(2002, 2027))

uni_rows = []
for y in YEARS:
    s = pd.read_csv(f"{SCHED}/wnba_schedule_{y}.csv", low_memory=False)
    s["game_id"] = s["game_id"].astype(str)
    post = s[s["status_type_state"].astype(str).str.lower() == "post"].copy()
    # drop Forfeit/Postponed: by status_type_name AND by detail/description text (fillna first;
    # pandas 3.0 string-dtype NA propagation makes bare .str.contains miss NA rows)
    post = post[~post["status_type_name"].astype(str).isin(["STATUS_FORFEIT", "STATUS_POSTPONED"])]
    txt = (post["status_type_description"].fillna("").astype(str) + "|" +
           post["status_type_detail"].fillna("").astype(str))
    post = post[~(txt.str.contains("Forfeit", case=False, na=False) | txt.str.contains("Postponed", case=False, na=False))]
    post = post[~(post["home_abbreviation"].isin(ALLSTAR) | post["away_abbreviation"].isin(ALLSTAR))]
    post["season"] = y
    uni_rows.append(post)
uni = pd.concat(uni_rows, ignore_index=True)
uni["tip"] = pd.to_datetime(uni["date"], utc=True, format="ISO8601")
per_season_uni = {int(y): int(n) for y, n in uni.groupby("season").size().items()}
print("universe games:", len(uni), "per-season:", per_season_uni)

# join rates
res = {"universe_total": int(len(uni)), "per_season_universe": per_season_uni, "per_season": {}}
for y in YEARS:
    pb = pd.read_csv(f"{CORP}/player_box_{y}.csv", low_memory=False)
    gr = pd.read_csv(f"{CORP}/game_rosters_{y}.csv", low_memory=False)
    ids = set(uni.loc[uni.season == y, "game_id"])
    pb_ids = set(pb["game_id"].astype(str))
    gr_ids = set(gr["game_id"].astype(str))
    # 2002 minutes null share
    min_null_share = None
    if y == 2002:
        min_null_share = float(pb["minutes"].isna().mean()) if "minutes" in pb else "NO_MIN_COL"
    res["per_season"][str(y)] = {
        "uni_games": len(ids),
        "pb_cov_games": len(ids & pb_ids), "pb_rate": round(len(ids & pb_ids) / len(ids), 4),
        "gr_cov_games": len(ids & gr_ids), "gr_rate": round(len(ids & gr_ids) / len(ids), 4),
        "pb_minutes_null_share_2002": min_null_share,
    }
for y in ("2002", "2003", "2004", "2013", "2026"):
    r = res["per_season"][y]
    print(y, "uni", r["uni_games"], "pb", r["pb_cov_games"], r["pb_rate"], "gr", r["gr_cov_games"], r["gr_rate"])

# lineage: espn_display_name -> franchise via team_key_table (OWN implementation)
tk = pd.read_csv(f"{HOME}/.my-quantitative-data/wnba-prep-v1/team_key_table.csv")
name2fr = {}
for _, r in tk.iterrows():
    for nm in str(r["espn_display_names"]).split(";"):
        name2fr[nm.strip()] = r["franchise_key"]
# (season, team_id) -> franchise from universe rows (home+away display names + ids)
mrows = []
for y in YEARS:
    sub = uni[uni.season == y]
    for side in ("home", "away"):
        mrows.append(sub[[f"{side}_id", f"{side}_display_name"]].copy())
        mrows[-1].columns = ["team_id", "display_name"]
        mrows[-1]["season"] = y
mmap = pd.concat(mrows).drop_duplicates()
mmap["franchise_key"] = mmap["display_name"].map(name2fr)
assert mmap["franchise_key"].notna().all(), "unmapped universe teams"
g = mmap.groupby("team_id")["franchise_key"].nunique()
assert (g <= 1).all(), f"team_id->multi-franchise: {g[g>1]}"
tmap = {(int(r.season), int(r.team_id)): r.franchise_key for r in mmap.itertuples()}
res["lineage"] = {"universe_team_seasons_mapped": len(tmap), "multi_franchise_violations": 0}

def franch_of(season, team_id):
    return tmap.get((season, int(team_id)))

def franchise_minutes(season, franchise):
    # sum minutes over universe games for all team_ids of this franchise in `season`
    pb = pd.read_csv(f"{CORP}/player_box_{season}.csv", low_memory=False)
    pb["game_id"] = pb["game_id"].astype(str)
    pb["minutes_num"] = pd.to_numeric(pb["minutes"], errors="coerce")
    uids = set(uni.loc[uni.season == season, "game_id"])
    pb = pb[pb.game_id.isin(uids)]
    tids = [t for (s, t), f in tmap.items() if s == season and f == franchise]
    pb = pb[pb.team_id.isin(tids)]
    pb = pb[pb["minutes_num"].notna()]
    tot = 0.0; per_athlete = {}
    for _, r in pb.iterrows():
        tot += float(r["minutes_num"])
        per_athlete[int(r["athlete_id"])] = per_athlete.get(int(r["athlete_id"]), 0.0) + float(r["minutes_num"])
    return tot, per_athlete

# ---------------- worked examples ----------------
wk = {}

# (a) CON 2013 Group B: target 400445816, CON team (own lineage resolution)
pb13 = pd.read_csv(f"{CORP}/player_box_2013.csv", low_memory=False)
pb13["game_id"] = pb13["game_id"].astype(str)
pb13["minutes_num"] = pd.to_numeric(pb13["minutes"], errors="coerce")
row16 = uni[uni.game_id == "400445816"].iloc[0]
con_id = int(row16.home_id) if franch_of(2013, row16.home_id) == "CON" else int(row16.away_id)
team18 = uni[(uni.season == 2013) & ((uni.home_id == con_id) | (uni.away_id == con_id))][["game_id", "tip"]]
tgt_tip = row16.tip
priors = team18[team18.tip < tgt_tip].sort_values(["tip", "game_id"])  # STRICT
mins_list = []
for _, r in priors.iterrows():
    sub = pb13[(pb13.game_id == r.game_id) & (pb13.team_id == con_id)]
    if len(sub) == 0: continue
    tot = float(sub["minutes_num"].fillna(0).sum())
    mins_list.append((r.game_id, str(r.tip), tot))
last5 = mins_list[-5:]; last3 = mins_list[-3:]
wk["con2013_b"] = {
    "target": "400445816", "target_tip": str(tgt_tip), "con_team_id": con_id,
    "prior_game_minutes": mins_list,
    "b5_minutes_total": sum(m for _, _, m in last5),
    "b3_minutes_total": sum(m for _, _, m in last3),
    "b5_window_first_tip": last5[0][1], "b5_window_last_tip": last5[-1][1],
    "last5_ids": [g for g, _, _ in last5],
}
print("CON2013 worked example:", json.dumps(wk["con2013_b"], indent=1))

# (b) CON 2014 continuity (Group A, v2): game-1 neutral, game-2 c = matched/total
tot, per_ath = franchise_minutes(2013, "CON")
gr14 = pd.read_csv(f"{CORP}/game_rosters_2014.csv", low_memory=False)
gr14["game_id"] = gr14["game_id"].astype(str)
# CON team id in 2014 via lineage
con14_id = [t for (s, t), f in tmap.items() if s == 2014 and f == "CON"][0]
team18_14 = uni[(uni.season == 2014) & ((uni.home_id == con14_id) | (uni.away_id == con14_id))][["game_id", "tip"]].sort_values(["tip", "game_id"])
g1 = team18_14.iloc[0]
sheet = gr14[(gr14.game_id == g1.game_id) & (gr14.team_id == con14_id)]
roster = set(sheet["athlete_id"].astype(int))
matched = sum(v for k, v in per_ath.items() if k in roster)
g2 = team18_14.iloc[1]
wk["con2014_continuity"] = {
    "con_team_id_2014": con14_id,
    "game1_id": g1.game_id, "game1_tip": str(g1.tip),
    "game2_id": g2.game_id, "game2_tip": str(g2.tip),
    "game2_after_game1_strict": bool(g2.tip > g1.tip),
    "prior_minutes_total": tot, "matched": matched, "roster_size": len(roster),
    "c": matched / tot,
}
print("CON2014 continuity:", json.dumps(wk["con2014_continuity"], indent=1))

# (c) GSV 2025 expansion neutrality from the table itself + own lineage map
tab = pd.read_parquet(f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/wnba/features/wnba_player_features_2002_2026.parquet")
tab["game_id"] = tab["game_id"].astype(str)
res["table"] = {"rows": int(len(tab)), "columns": list(tab.columns)}
BAN = ("score", "winner", "outcome", "win_prob", "result", "margin", "pts_for")
res["table"]["banned_name_hits"] = [c for c in tab.columns for b in BAN if b in c.lower()]
gsv25 = tab[(tab.season == 2025) & (tab.franchise_key == "GSV")]
wk["gsv2025"] = {"rows": int(len(gsv25)),
                 "all_neutral": bool((gsv25["continuity_neutral_reason"] == "expansion_no_prior").all()),
                 "c_all_na": bool(gsv25["continuity_c"].isna().all())}
por26 = tab[(tab.season == 2026) & (tab.franchise_key == "POR_PDX")]
wk["por_pdx2026"] = {"rows": int(len(por26)),
                     "all_neutral": bool((por26["continuity_neutral_reason"] == "expansion_no_prior").all())}
tor26 = tab[(tab.season == 2026) & (tab.franchise_key == "TOR")]
wk["tor2026"] = {"rows": int(len(tor26)),
                 "all_neutral": bool((tor26["continuity_neutral_reason"] == "expansion_no_prior").all())}
# 2002 all no_prior_in_corpus
t2002 = tab[tab.season == 2002]
wk["season2002"] = {"rows": int(len(t2002)),
                    "all_no_prior_in_corpus": bool((t2002["continuity_neutral_reason"] == "no_prior_in_corpus").all()),
                    "minutes_any_computed": bool(t2002[["b3_minutes_total", "b5_minutes_total", "c_absence_share"]].notna().any().any())}
print("GSV2025:", wk["gsv2025"], "POR26:", wk["por_pdx2026"], "TOR26:", wk["tor2026"], "S2002:", wk["season2002"])

# (d) IND 2013 absence recompute: target 400496780, IND side
pb13["athlete_id_num"] = pb13["athlete_id"].astype(int)
row_t = uni[uni.game_id == "400496780"].iloc[0]
home_id, away_id = int(row_t.home_id), int(row_t.away_id)
ind_id = home_id if franch_of(2013, home_id) == "IND" else away_id
team_rows = uni[(uni.season == 2013) & ((uni.home_id == ind_id) | (uni.away_id == ind_id))][["game_id", "tip"]]
priors_ind = team_rows[team_rows.tip < row_t.tip].sort_values(["tip", "game_id"])
pbid = set(pb13.game_id)
priors_with_box = priors_ind[priors_ind.game_id.isin(pbid)]
trail10 = priors_with_box.tail(10)
pooled = {}
for _, r in trail10.iterrows():
    sub = pb13[(pb13.game_id == r.game_id) & (pb13.team_id == ind_id)]
    sub = sub[sub["minutes_num"].notna()]
    for _, pr in sub.iterrows():
        a = int(pr.athlete_id)
        pooled.setdefault(a, []).append((r.game_id, float(pr.minutes_num), float(pr.get("points", np.nan) or 0)))
tot_min_by_a = {a: sum(m for _, m, _ in v) for a, v in pooled.items()}
top5 = sorted(tot_min_by_a, key=lambda a: (-tot_min_by_a[a], a))[:5]
recent = priors_with_box.iloc[-1]
exp_sum = 0.0; miss_sum = 0.0
for a in top5:
    games = pooled[a]
    mins_arr = [m for _, m, _ in games]
    base_min = float(np.mean(mins_arr))
    exp_sum += base_min
    rec = pb13[(pb13.game_id == recent.game_id) & (pb13.team_id == ind_id) & (pb13.athlete_id.astype(int) == a)]
    actual = 0.0 if len(rec) == 0 or pd.isna(rec.iloc[0]["minutes_num"]) else float(rec.iloc[0]["minutes_num"])
    miss_sum += max(0.0, base_min - actual)
wk["ind2013_absence"] = {
    "target": "400496780", "ind_team_id": ind_id, "recent_game": recent.game_id,
    "top5": top5, "absence_share": miss_sum / exp_sum if exp_sum else None,
}
print("IND2013 absence:", json.dumps(wk["ind2013_absence"], indent=1))
res["worked_examples"] = wk

# strict-inequality assertion on table columns (own scan)
tip_col = pd.to_datetime(tab["tip_utc"], utc=True, errors="coerce")
last3 = pd.to_datetime(tab["b3_window_last_tip"], utc=True, errors="coerce")
last5 = pd.to_datetime(tab["b5_window_last_tip"], utc=True, errors="coerce")
crec = pd.to_datetime(tab["c_recent_game_tip"], utc=True, errors="coerce")
res["table"]["strict_ineq_violations"] = {
    "b3": int((last3.notna() & (last3 >= tip_col)).sum()),
    "b5": int((last5.notna() & (last5 >= tip_col)).sum()),
    "c_recent": int((crec.notna() & (crec >= tip_col)).sum()),
}
res["table"]["computed_counts"] = {
    "continuity": int(tab["continuity_c"].notna().sum()),
    "b3": int(tab["b3_minutes_total"].notna().sum()),
    "b5": int(tab["b5_minutes_total"].notna().sum()),
    "c_form": int(tab["c_form_z_pts"].notna().sum()),
    "neutral_reason_counts_continuity": tab["continuity_neutral_reason"].replace("", np.nan).value_counts().to_dict(),
}
res["table"]["dups"] = int(tab.duplicated(subset=["game_id", "team_side"]).sum())
res["table"]["per_season_games"] = {int(k): int(v) for k, v in tab.groupby("season")["game_id"].nunique().items()}
print("strict_ineq:", res["table"]["strict_ineq_violations"])
print("computed counts:", res["table"]["computed_counts"])
json.dump(res, open(OUTP, "w"), indent=1, default=str)
print("DONE")
