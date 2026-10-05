#!/usr/bin/env python
"""D_VERIFY own-code NFL crosswalk verification: joins, round-trip, freshness,
named-player spot checks. Independent implementation."""
import os, json
import pandas as pd

HOME = os.path.expanduser("~")
PRED = f"{HOME}/.my-quantitative-data/playerdata-prep-v1/nfl"
XW = f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/nfl/raw_players/players.parquet"
OUTP = "/Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration/lanes/D_VERIFY/nfl_output.json"

pl = pd.read_parquet(XW)
res = {"players_rows": int(len(pl)), "players_cols": int(len(pl.columns)),
       "gsis_null": int(pl["gsis_id"].isna().sum()),
       "gsis_unique": int(pl["gsis_id"].nunique()),
       "pfr_nonnull": int(pl["pfr_id"].notna().sum()),
       "latest_team_distinct": int(pl["latest_team"].nunique())}

def season_join(season):
    st = pd.read_parquet(f"{PRED}/raw_stats_player/stats_player_week_{season}.parquet")
    ids = st["player_id"].dropna().unique()
    ids_set = set(ids)
    xw_set = set(pl["gsis_id"].dropna())
    matched = ids_set & xw_set
    dups = int(st.duplicated(subset=["player_id", "game_id"]).sum())
    return {"rows": int(len(st)), "null_player_rows": int(st["player_id"].isna().sum()),
            "distinct_gsis": len(ids_set), "matched": len(matched),
            "rate": len(matched) / len(ids_set) if len(ids_set) else None, "dups": dups}

def snap_join(season):
    sn = pd.read_parquet(f"{PRED}/raw_snap_counts/snap_counts_{season}.parquet")
    ids = sn["pfr_id"].dropna().unique() if "pfr_id" in sn.columns else sn[ [c for c in sn.columns if "pfr" in c][0] ].dropna().unique()
    col = "pfr_id" if "pfr_id" in sn.columns else [c for c in sn.columns if "pfr" in c][0]
    ids_set = set(ids)
    xw_set = set(pl["pfr_id"].dropna())
    matched = ids_set & xw_set
    un = sorted(ids_set - xw_set)
    un_rows = int(sn[sn[col].isin(un)].shape[0])
    dups = int(sn.duplicated(subset=[col, "game_id"]).sum())
    return {"rows": int(len(sn)), "distinct_pfr": len(ids_set), "matched": len(matched),
            "rate": len(matched) / len(ids_set) if ids_set else None,
            "unmatched_ids": un, "unmatched_rows": un_rows, "dups": dups,
            "game_id_col_present": "game_id" in sn.columns}

res["weekly"] = {str(y): season_join(y) for y in (2024, 2025, 2026)}
res["snap_cols_2026"] = list(pd.read_parquet(f"{PRED}/raw_snap_counts/snap_counts_2026.parquet").columns)
# snap join uses the right pfr column name; detect once
sn26 = pd.read_parquet(f"{PRED}/raw_snap_counts/snap_counts_2026.parquet")
assert "pfr_player_id" in sn26.columns, f"pfr col missing: {list(sn26.columns)}"
pfr_col = "pfr_player_id"
def snap_join2(sn, season):
    ids_set = set(sn[pfr_col].dropna().unique())
    xw_set = set(pl["pfr_id"].dropna())
    matched = ids_set & xw_set
    un = sorted(ids_set - xw_set)
    un_rows = int(sn[sn[pfr_col].isin(un)].shape[0])
    dupcols = [c for c in ("pfr_id", pfr_col, "game_id") if c in sn.columns]
    return {"rows": int(len(sn)), "distinct_pfr": len(ids_set), "matched": len(matched),
            "rate": len(matched) / len(ids_set) if ids_set else None,
            "unmatched_ids": un, "unmatched_rows": un_rows,
            "dups": int(sn.duplicated(subset=[pfr_col, "game_id"]).sum()) if "game_id" in sn.columns else None}
res["snap_2025"] = snap_join2(pd.read_parquet(f"{PRED}/raw_snap_counts/snap_counts_2025.parquet"), 2025)
res["snap_2026"] = snap_join2(sn26, 2026)

# round-trip 2026
st26 = pd.read_parquet(f"{PRED}/raw_stats_player/stats_player_week_2026.parquet")
gsis26 = set(st26["player_id"].dropna().unique())
pfr_of = dict(zip(pl["gsis_id"], pl["pfr_id"]))
holders = {g: pfr_of.get(g) for g in gsis26}
with_pfr = {g: p for g, p in holders.items() if p is not None and isinstance(p, str)}
pfr_null_named = []
for g, p in holders.items():
    if p is None or not isinstance(p, str):
        row = pl[pl.gsis_id == g]
        nm = row.iloc[0].get("display_name") if len(row) else g
        pos = row.iloc[0].get("position") if len(row) else None
        pfr_null_named.append(f"{nm} ({g})")
sn26_set = set(sn26[pfr_col].dropna().unique())
joinable = {g for g, p in with_pfr.items() if p in sn26_set}
res["roundtrip_2026"] = {
    "stats_distinct_gsis": len(gsis26),
    "with_pfr": len(with_pfr),
    "joinable_into_snap26": len(joinable),
    "rate_vs_all": len(joinable) / len(gsis26),
    "rate_vs_pfr_holders": len(joinable) / len(with_pfr) if with_pfr else None,
    "pfr_null_named": sorted(pfr_null_named),
}

# freshness: ACT ∧ last_season 2026
res["freshness"] = {
    "status_col_values": int(pl["status"].nunique()) if "status" in pl.columns else None,
    "weeks_observed_2026": sorted(st26["week"].unique().tolist()) if "week" in st26.columns else None,
}
if "status" in pl.columns and "last_season" in pl.columns:
    act26 = pl[(pl["status"] == "ACT") & (pl["last_season"] == 2026)]
    res["freshness"]["act_and_last_season_2026"] = int(len(act26))
    res["freshness"]["per_team_min"] = int(act26.groupby("latest_team").size().min())
    res["freshness"]["per_team_max"] = int(act26.groupby("latest_team").size().max())
    res["freshness"]["teams_present"] = int(act26["latest_team"].nunique())

# named player spot checks
def player_row(name=None, gsis=None, pfr=None):
    if gsis is not None:
        r = pl[pl.gsis_id == gsis]
    elif pfr is not None:
        r = pl[pl.pfr_id == pfr]
    else:
        r = pl[pl.display_name == name]
    return {c: (None if pd.isna(v) else (v.item() if hasattr(v, "item") else v)) for c, v in r.iloc[0].items()} if len(r) else None

spots = {}
spots["Cody White_pfr_null"] = player_row(gsis="00-0035891")
spots["Alec Anderson_pfr_null"] = player_row(gsis="00-0037428")
spots["Basil Okoye"] = player_row(name="Basil Okoye")
spots["Peter Woods"] = player_row(name="Peter Woods")
# top-8 QBs by 2026 passing yards — approximate via weekly stats passing yards
if "passing_yards" in st26.columns:
    qy = st26.groupby("player_id")["passing_yards"].sum().sort_values(ascending=False).head(8)
    spots["top8_qbs_2026"] = []
    for g, yds in qy.items():
        r = pl[pl.gsis_id == g]
        spots["top8_qbs_2026"].append({"gsis": g, "name": r.iloc[0]["display_name"],
                                       "pfr_id": (None if pd.isna(r.iloc[0]["pfr_id"]) else r.iloc[0]["pfr_id"]),
                                       "pass_yds_2026": float(yds),
                                       "in_snap26": (r.iloc[0]["pfr_id"] in sn26_set) if not pd.isna(r.iloc[0]["pfr_id"]) else False})
res["spot_checks"] = spots
json.dump(res, open(OUTP, "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in res.items() if k not in ("spot_checks",)}, indent=1, default=str))
print("TOP8 QBs:", json.dumps(spots.get("top8_qbs_2026"), indent=1, default=str))
print("CodyWhite:", spots["CodyWhite_pfr_null".replace("White_pfr_null", " White_pfr_null")] if False else spots["Cody White_pfr_null"])
print("AlecAnderson:", spots["Alec Anderson_pfr_null"])
print("BasilOkoye:", spots["Basil Okoye"])
print("PeterWoods:", spots["Peter Woods"])
