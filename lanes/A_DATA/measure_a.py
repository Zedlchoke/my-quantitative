#!/usr/bin/env python3
"""Lane A (WNBA-WINPROB-PREP-V1) game-universe measurement.

Read-only over ~/.my-quantitative-data/wnba-v1/raw/ (EXTEND-ONLY corpus).
Schema/coverage counting ONLY — no win-prob metrics, no scored computation.
Writes measurements JSON to ~/.my-quantitative-data/wnba-prep-v1/measurements_a.json.
"""
import json
import os
import re
import sys

import pandas as pd

RAW = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw")
OUT = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1")
os.makedirs(OUT, exist_ok=True)

R = {}

# ------------------------------------------------------------------ load
espn_rows, stats_rows = [], []
for y in range(2002, 2027):
    f = os.path.join(RAW, "espn_schedules", f"wnba_schedule_{y}.csv")
    d = pd.read_csv(f, low_memory=False)
    d["season_file"] = y
    espn_rows.append(d)
espn = pd.concat(espn_rows, ignore_index=True)

for y in range(1997, 2027):
    f = os.path.join(RAW, "wnba_stats_schedules", f"wnba_schedule_{y}.csv.gz")
    d = pd.read_csv(f, compression="gzip")
    d["season_file"] = y
    stats_rows.append(d)
stats = pd.concat(stats_rows, ignore_index=True)

R["espn_identity"] = {
    "rows": int(len(espn)),
    "seasons": [int(x) for x in sorted(espn["season_file"].unique())],
    "unique_game_id": int(espn["game_id"].nunique()),
    "dup_rows": int(len(espn) - espn["game_id"].nunique()),
    "game_id_examples": [str(x) for x in espn["game_id"].iloc[[0, len(espn) // 2, -1]]],
}
R["stats_identity"] = {
    "rows": int(len(stats)),
    "seasons": [int(x) for x in sorted(stats["season_file"].unique())],
    "unique_game_id": int(stats["game_id"].nunique()),
    "dup_rows": int(len(stats) - stats["game_id"].nunique()),
    "game_id_examples": [str(x) for x in stats["game_id"].iloc[[0, len(stats) // 2, -1]]],
}

# ------------------------------------------------------------------ status / pre-filled law
R["espn_status"] = {
    "state_counts": {str(k): int(v) for k, v in espn["status_type_state"].value_counts().items()},
    "completed_counts": {str(k): int(v) for k, v in espn["status_type_completed"].astype(str).value_counts().items()},
    "detail_counts_nonfinal": {
        str(k): int(v) for k, v in espn.loc[espn["status_type_state"] != "post", "status_type_detail"].fillna("<null>").value_counts().items()
    },
    "detail_counts_post": {
        str(k): int(v) for k, v in espn.loc[espn["status_type_state"] == "post", "status_type_detail"].fillna("<null>").value_counts().items()
    },
}
pre = espn[espn["status_type_state"] != "post"]
zero_prefill = (
    pd.to_numeric(pre["home_score"], errors="coerce").eq(0)
    & pd.to_numeric(pre["away_score"], errors="coerce").eq(0)
)
R["espn_unplayed_law"] = {
    "nonpost_rows": int(len(pre)),
    "nonpost_rows_by_season": {int(k): int(v) for k, v in pre.groupby("season_file").size().items()},
    "nonpost_prefilled_0_0": int(zero_prefill.sum()),
    "nonpost_not_0_0": int((~zero_prefill).sum()),
}

# ------------------------------------------------------------------ filter law pieces (ESPN side)
ALLSTAR_ALIASES = {"EAST", "WEST", "ALL", "DEL", "PAR", "CLA", "COOP", "WNBASTARS"}
alias_rows = espn[
    espn["home_abbreviation"].isin(ALLSTAR_ALIASES) | espn["away_abbreviation"].isin(ALLSTAR_ALIASES)
]
R["espn_allstar_alias"] = {
    "rows": int(len(alias_rows)),
    "by_season": {int(k): int(v) for k, v in alias_rows.groupby("season_file").size().items()},
    "examples": [
        {
            "season": int(r["season_file"]),
            "game_id": str(r["game_id"]),
            "home": str(r["home_display_name"]),
            "away": str(r["away_display_name"]),
            "abbrs": f"{r['home_abbreviation']}/{r['away_abbreviation']}",
        }
        for _, r in alias_rows.iterrows()
    ],
}

tbd_rows = espn[
    espn["home_abbreviation"].fillna("TBD").eq("TBD")
    | espn["away_abbreviation"].fillna("TBD").eq("TBD")
    | espn["home_display_name"].fillna("").str.contains("TBD", case=False)
    | espn["away_display_name"].fillna("").str.contains("TBD", case=False)
]
R["espn_tbd_placeholder"] = {
    "rows": int(len(tbd_rows)),
    "by_season": {int(k): int(v) for k, v in tbd_rows.groupby("season_file").size().items()},
    "states": {str(k): int(v) for k, v in tbd_rows["status_type_state"].value_counts().items()},
}

forfeit = espn[espn["status_type_detail"].fillna("").str.contains("Forfeit", case=False)]
R["espn_forfeit"] = [
    {
        "game_id": str(r["game_id"]),
        "season": int(r["season_file"]),
        "date": str(r["date"]),
        "home": str(r["home_display_name"]),
        "away": str(r["away_display_name"]),
        "score": f"{r['home_score']}-{r['away_score']}",
        "state": str(r["status_type_state"]),
    }
    for _, r in forfeit.iterrows()
]
postponed = espn[espn["status_type_detail"].fillna("").str.contains("Postponed", case=False)]
R["espn_postponed"] = [
    {
        "game_id": str(r["game_id"]),
        "season": int(r["season_file"]),
        "date": str(r["date"]),
        "detail": str(r["status_type_detail"]),
        "state": str(r["status_type_state"]),
    }
    for _, r in postponed.iterrows()
]

neutral = espn[espn["neutral_site"].astype(str).str.upper().isin(["TRUE", "1"])]
R["espn_neutral_site"] = {
    "rows": int(len(neutral)),
    "by_season": {int(k): int(v) for k, v in neutral.groupby("season_file").size().items()},
}

cup = espn[espn["notes_headline"].fillna("").str.contains("Cup", case=False)]
cup_champ = espn[espn["notes_headline"].fillna("").str.contains("Commissioner", case=False)]
R["espn_commissioners_cup"] = {
    "rows_headline_cup": int(len(cup)),
    "by_season": {int(k): int(v) for k, v in cup.groupby("season_file").size().items()},
    "rows_headline_commissioner": int(len(cup_champ)),
    "cup_headline_examples": sorted(cup["notes_headline"].dropna().unique().tolist())[:12],
    "season_type_of_cup_rows": {str(k): int(v) for k, v in cup["season_type"].value_counts().items()},
}

# ------------------------------------------------------------------ canonical per-season census (ESPN, filter law applied)
played = espn[espn["status_type_state"] == "post"].copy()
played = played[~played["status_type_detail"].fillna("").str.contains("Forfeit|Postponed", case=False)]
played = played[
    ~played["home_abbreviation"].isin(ALLSTAR_ALIASES) & ~played["away_abbreviation"].isin(ALLSTAR_ALIASES)
]
played_rs = played[played["season_type"] == 2]
played_po = played[played["season_type"] == 3]
census = {}
for y in sorted(espn["season_file"].unique()):
    census[int(y)] = {
        "espn_rows_total": int((espn["season_file"] == y).sum()),
        "espn_played_total": int((played["season_file"] == y).sum()),
        "espn_played_rs": int((played_rs["season_file"] == y).sum()),
        "espn_played_po": int((played_po["season_file"] == y).sum()),
    }
R["espn_census"] = census
R["espn_census_2020"] = {
    "rows_total": int((espn["season_file"] == 2020).sum()),
    "played_total": int((played["season_file"] == 2020).sum()),
    "played_rs": int((played_rs["season_file"] == 2020).sum()),
    "played_po": int((played_po["season_file"] == 2020).sum()),
}

# ------------------------------------------------------------------ stats side law
# stats has no status column; unplayed/forfeit rows are pre-filled 0-0 (never filter on
# score presence for EXCLUSION of played — but both-zero rows cannot be real WNBA games:
# measured min team score in ESPN completed non-forfeit games > 0).
sboth0 = (pd.to_numeric(stats["home_pts"], errors="coerce").eq(0)) & (
    pd.to_numeric(stats["away_pts"], errors="coerce").eq(0)
)
R["stats_both_zero_rows"] = {
    "rows": int(sboth0.sum()),
    "by_season": {int(k): int(v) for k, v in stats[sboth0].groupby("season_file").size().items()},
    "rows_blank_wl": int(
        (stats.loc[sboth0, "home_wl"].isna() & stats.loc[sboth0, "away_wl"].isna()).sum()
    ),
}
salias = stats[
    stats["home_team_abbreviation"].isin(ALLSTAR_ALIASES) | stats["away_team_abbreviation"].isin(ALLSTAR_ALIASES)
]
R["stats_allstar_alias"] = {
    "rows": int(len(salias)),
    "by_season": {int(k): int(v) for k, v in salias.groupby("season_file").size().items()},
}
sforfeit = stats[sboth0]
R["stats_forfeit_rows"] = [
    {"game_id": str(r["game_id"]), "season": int(r["season_file"]), "date": str(r["game_date"]),
     "home": str(r["home_team_abbreviation"]), "away": str(r["away_team_abbreviation"]),
     "wl_home": str(r["home_wl"]), "wl_away": str(r["away_wl"])}
    for _, r in sforfeit.iterrows()
]

s_played = stats[~sboth0].copy()
s_played = s_played[
    ~s_played["home_team_abbreviation"].isin(ALLSTAR_ALIASES) & ~s_played["away_team_abbreviation"].isin(ALLSTAR_ALIASES)
]
s_rs = s_played[s_played["season_type"] == 2]
s_po = s_played[s_played["season_type"] == 3]
scensus = {}
for y in sorted(stats["season_file"].unique()):
    scensus[int(y)] = {
        "stats_rows_total": int((stats["season_file"] == y).sum()),
        "stats_played_total": int((s_played["season_file"] == y).sum()),
        "stats_played_rs": int((s_rs["season_file"] == y).sum()),
        "stats_played_po": int((s_po["season_file"] == y).sum()),
    }
R["stats_census"] = scensus
R["stats_season_type_counts"] = {str(k): int(v) for k, v in stats["season_type"].value_counts().items()}

# ------------------------------------------------------------------ reconciliation ESPN vs stats
recon = {}
for y in sorted(set(espn["season_file"].unique()) & set(stats["season_file"].unique())):
    e_n = int((espn["season_file"] == y).sum())
    s_n = int((stats["season_file"] == y).sum())
    e_p = int((played["season_file"] == y).sum())
    s_p = int((s_played["season_file"] == y).sum())
    recon[int(y)] = {"rows_espn": e_n, "rows_stats": s_n, "rows_diff": e_n - s_n,
                     "played_espn": e_p, "played_stats": s_p, "played_diff": e_p - s_p}
R["reconciliation"] = recon

# row-level join via measured display_name -> stats abbrev map (join law: NEVER raw ESPN abbr)
name_to_abbr = {}
s_names = stats.dropna(subset=["home_team_abbreviation"])[["home_team_name", "home_team_abbreviation"]]
for name, ab in s_names.drop_duplicates().itertuples(index=False):
    name_to_abbr.setdefault(str(name).strip(), str(ab).strip())

espn_j = played.copy()
espn_j["home_key"] = espn_j["home_display_name"].map(name_to_abbr)
espn_j["away_key"] = espn_j["away_display_name"].map(name_to_abbr)
# 2002 ESPN rows predate some naming? check unmapped
unmapped = espn_j[espn_j["home_key"].isna() | espn_j["away_key"].isna()]
R["recon_rowlevel_unmapped_names"] = sorted(
    set(espn_j.loc[espn_j["home_key"].isna(), "home_display_name"].dropna().tolist()
        + espn_j.loc[espn_j["away_key"].isna(), "away_display_name"].dropna().tolist())
)
stats_j = s_played.copy()
mg = espn_j.merge(
    stats_j[["game_date", "home_team_abbreviation", "away_team_abbreviation", "game_id"]]
    .rename(columns={"game_id": "stats_game_id"}),
    left_on=["game_date", "home_key", "away_key"],
    right_on=["game_date", "home_team_abbreviation", "away_team_abbreviation"],
    how="outer", indicator=True,
)
R["recon_rowlevel"] = {
    "espn_played_matched": int((mg["_merge"] == "both").sum()),
    "espn_played_only": int((mg["_merge"] == "left_only").sum()),
    "stats_played_only": int((mg["_merge"] == "right_only").sum()),
}
only_e = mg[mg["_merge"] == "left_only"]
R["recon_rowlevel_espn_only_examples"] = [
    {"season": int(r["season_file"]), "date": str(r["game_date"]),
     "home": str(r["home_display_name"]), "away": str(r["away_display_name"]),
     "abbrs": f"{r['home_abbreviation']}/{r['away_abbreviation']}",
     "headline": str(r["notes_headline"])[:60]}
    for _, r in only_e.head(20).iterrows()
]
only_s = mg[mg["_merge"] == "right_only"]
R["recon_rowlevel_stats_only_examples"] = [
    {"season": str(r["game_date"]), "home": str(r["home_team_abbreviation"]),
     "away": str(r["away_team_abbreviation"])}
    for _, r in only_s.head(20).iterrows()
]
eo = only_e.groupby("season_file").size()
so = only_s.groupby(only_s["game_id"].astype(str).str[:4]).size()
R["recon_rowlevel_by_season"] = {
    "espn_only": {int(k): int(v) for k, v in eo.items()},
    "stats_only": {str(k): int(v) for k, v in so.items()},
}

# ------------------------------------------------------------------ franchise map (stats side = stable spine)
fs = stats.groupby(["season_file", "home_team_abbreviation"]).size().reset_index()
abbr_seasons = fs.groupby("home_team_abbreviation")["season_file"].apply(lambda s: sorted(int(x) for x in s))
R["stats_abbr_seasons"] = {str(k): v for k, v in abbr_seasons.items()}

# names per abbr over time (stats side)
nm = stats.groupby(["home_team_abbreviation", "home_team_name"]).size().reset_index()
R["stats_abbr_names"] = {
    str(ab): sorted(set(nm.loc[nm["home_team_abbreviation"] == ab, "home_team_name"]))
    for ab in sorted(nm["home_team_abbreviation"].unique())
}

# franchise continuity chains (verify rename boundaries from data):
chains = {
    "UTA": [y for y in abbr_seasons.get("UTA", [])],
    "SAN": [y for y in abbr_seasons.get("SAN", [])],
    "DAL": [y for y in abbr_seasons.get("DAL", [])],
    "ORL": [y for y in abbr_seasons.get("ORL", [])],
    "CON": [y for y in abbr_seasons.get("CON", [])],
    "DET": [y for y in abbr_seasons.get("DET", [])],
    "TUL": [y for y in abbr_seasons.get("TUL", [])],
    "LAS": [y for y in abbr_seasons.get("LAS", [])],
    "LVA": [y for y in abbr_seasons.get("LVA", [])],
}
R["franchise_chain_verification"] = chains

# ------------------------------------------------------------------ ESPN abbreviation unreliability (join law evidence)
bad_map = []
for y in sorted(espn["season_file"].unique()):
    d = espn[espn["season_file"] == y]
    for side in ["home", "away"]:
        pairs = d.dropna(subset=[f"{side}_abbreviation"]).groupby(f"{side}_abbreviation")[f"{side}_display_name"].unique()
        for ab, names in pairs.items():
            if len(names) > 1:
                bad_map.append({"season": int(y), "side": side, "abbr": str(ab),
                                "display_names": sorted(str(n) for n in names),
                                "rows": int((d[f"{side}_abbreviation"] == ab).sum())})
R["espn_abbr_multiple_names"] = bad_map

# the 2002 DET/TUL artifact, re-measured
det02 = espn[(espn["season_file"] == 2002) & (espn["home_display_name"] == "Detroit Shock")]
tul02 = espn[(espn["season_file"] == 2002) & (espn["home_abbreviation"] == "TUL")]
R["espn_2002_det_artifact"] = {
    "detroit_shock_home_rows_2002": int(len(det02)),
    "their_home_abbrs": sorted(set(det02["home_abbreviation"].dropna())),
    "abbr_TUL_rows_2002": int(len(tul02)),
    "abbr_TUL_display_names_2002": sorted(set(tul02["home_display_name"].dropna())),
}
# ESPN vs stats abbr mismatch rate pre/post 2011 using name map
espn2 = espn.copy()
espn2["home_key"] = espn2["home_display_name"].map(name_to_abbr)
cmp = espn2.dropna(subset=["home_key", "home_abbreviation"]).copy()
cmp["mismatch"] = cmp["home_abbreviation"] != cmp["home_key"]
R["espn_abbr_vs_stats_mismatch"] = {
    "pre_2011": {
        "rows": int((cmp["season_file"] < 2011).sum()),
        "mismatch_rows": int(cmp.loc[cmp["season_file"] < 2011, "mismatch"].sum()),
        "mismatch_pct": round(float(cmp.loc[cmp["season_file"] < 2011, "mismatch"].mean() * 100), 2),
    },
    "from_2011": {
        "rows": int((cmp["season_file"] >= 2011).sum()),
        "mismatch_rows": int(cmp.loc[cmp["season_file"] >= 2011, "mismatch"].sum()),
        "mismatch_pct": round(float(cmp.loc[cmp["season_file"] >= 2011, "mismatch"].mean() * 100), 2),
    },
}

# ------------------------------------------------------------------ timestamps
dcol = espn["date"].astype(str)
R["ts_espn_schedule_date"] = {
    "example": dcol.iloc[0],
    "endswith_Z_pct": round(float(dcol.str.endswith("Z").mean() * 100), 2),
    "has_numeric_offset_pct": round(float(dcol.str.contains(r"[+-]\d{2}:?\d{2}$", regex=True).mean() * 100), 2),
    "distinct_formats_sample": sorted(set(dcol.str.slice(0, 4).tolist()))[:3],
}
sd = espn["start_date"].astype(str)
R["ts_espn_schedule_start_date"] = {
    "example": sd.iloc[0],
    "endswith_Z_pct": round(float(sd.str.endswith("Z").mean() * 100), 2),
    "equals_date_col_pct": round(float((sd == dcol).mean() * 100), 2),
}

gdt = espn["game_date_time"].astype(str)
off = gdt.str.extract(r"([+-]\d{4})$", expand=False)
R["ts_espn_schedule_game_date_time"] = {
    "example_2025": str(espn.loc[espn["season_file"] == 2025, "game_date_time"].iloc[0]),
    "null_rows": int(espn["game_date_time"].isna().sum()),
    "null_by_season": {int(k): int(v) for k, v in espn[espn["game_date_time"].isna()].groupby("season_file").size().items()},
    "rows_with_numeric_offset": int(off.notna().sum()),
    "rows_Z_suffixed": int(gdt.str.endswith("Z").sum()),
    "offset_distribution_top": {str(k): int(v) for k, v in off.value_counts().head(10).items()},
    "offset_by_month_2025": {str(k): int(v) for k, v in off[espn["season_file"] == 2025].groupby(
        espn.loc[espn["season_file"] == 2025, "date"].astype(str).str.slice(5, 7)).value_counts().items()},
}

# instant equality: date (UTC) vs game_date_time (local+offset) parsed to UTC
both = espn[espn["game_date_time"].notna()].copy()
utc1 = pd.to_datetime(both["date"], utc=True, errors="coerce")
utc2 = pd.to_datetime(both["game_date_time"], utc=True, errors="coerce")
eq = (utc1 == utc2)
R["ts_espn_instant_equality"] = {
    "rows_compared": int(len(both)),
    "equal_pct": round(float(eq.mean() * 100), 2),
    "unequal_rows": int((~eq).sum()),
}

# DST sampling: offsets across months for a full DST year with games (2025 + 2026)
for yr in (2025, 2026):
    d = espn[espn["season_file"] == yr].copy()
    d["month"] = d["date"].astype(str).str.slice(5, 7)
    o = d["game_date_time"].astype(str).str.extract(r"([+-]\d{4})$", expand=False)
    tab = {}
    for m in sorted(d["month"].unique()):
        tab[m] = {str(k): int(v) for k, v in o[d["month"] == m].value_counts().items()}
    R[f"ts_dst_sample_{yr}"] = tab

# stats game_date flavor
gd = stats["game_date"].astype(str)
R["ts_stats_game_date"] = {
    "example": gd.iloc[0],
    "ymd_format_pct": round(float(gd.str.match(r"^\d{4}-\d{2}-\d{2}$").mean() * 100), 2),
    "has_time_component": int(gd.str.contains("T|:").sum()),
}

# canonical law spot check: ESPN date (UTC) vs stats game_date (local) — game on same local date
chk = espn[(espn["season_file"] == 2025)].copy()
chk["utc"] = pd.to_datetime(chk["date"], utc=True, errors="coerce")
chk["et_date"] = chk["utc"].dt.tz_convert("America/New_York").dt.date
chk["gdt_local_date"] = pd.to_datetime(chk["game_date_time"], errors="coerce").dt.date
cmp2 = chk.dropna(subset=["gdt_local_date"])
R["ts_canonical_check_2025"] = {
    "rows": int(len(cmp2)),
    "et_date_eq_gdt_local_date_pct": round(float((cmp2["et_date"] == cmp2["gdt_local_date"]).mean() * 100), 2),
    "unequal_rows": int((cmp2["et_date"] != cmp2["gdt_local_date"]).sum()),
}
uneq = cmp2[cmp2["et_date"] != cmp2["gdt_local_date"]]
R["ts_canonical_check_2025_unequal_examples"] = [
    {"date_utc": str(r["utc"]), "et_date": str(r["et_date"]), "gdt_local": str(r["gdt_local_date"]),
     "gdt": str(r["game_date_time"]), "venue": str(r["venue_full_name"])}
    for _, r in uneq.head(10).iterrows()
]

# ------------------------------------------------------------------ 2025 sample re-verification
tb = pd.read_csv(os.path.join(RAW, "espn_sample_2025", "team_box_2025.csv"), low_memory=False)
pb = pd.read_csv(os.path.join(RAW, "espn_sample_2025", "player_box_2025.csv"), low_memory=False)
pbp = pd.read_csv(os.path.join(RAW, "espn_sample_2025", "play_by_play_2025.csv"), low_memory=False)
R["sample2025"] = {
    "team_box_rows": int(len(tb)),
    "team_box_unique_games": int(tb["game_id"].nunique()),
    "team_box_rows_per_game_violations": int((tb.groupby("game_id").size() != 2).sum()),
    "team_box_gdt_example": str(tb["game_date_time"].iloc[0]),
    "team_box_gdt_offset_pct": round(float(tb["game_date_time"].astype(str).str.contains(r"[+-]\d{4}$", regex=True).mean() * 100), 2),
    "team_box_points_in_paint_notnull_pct": round(float(tb["points_in_paint"].notna().mean() * 100), 2),
    "team_box_season_type": {str(k): int(v) for k, v in tb["season_type"].value_counts().items()},
    "player_box_rows": int(len(pb)),
    "player_box_unique_games": int(pb["game_id"].nunique()),
    "player_box_unique_players": int(pb["athlete_id"].nunique()),
    "player_box_active_counts": {str(k): int(v) for k, v in pb["active"].astype(str).value_counts().items()},
    "player_box_dnp_counts": {str(k): int(v) for k, v in pb["did_not_play"].astype(str).value_counts().items()},
    "player_box_starter_counts": {str(k): int(v) for k, v in pb["starter"].astype(str).value_counts().items()},
    "player_box_median_rows_per_game": float(pb.groupby("game_id").size().median()),
    "player_box_starters_per_game_median": float(
        pb[pb["starter"].astype(str).str.upper() == "TRUE"].groupby("game_id").size().median()),
    "pbp_rows": int(len(pbp)),
    "pbp_unique_games": int(pbp["game_id"].nunique()),
    "pbp_wallclock_example": str(pbp["wallclock"].iloc[0]),
    "pbp_wallclock_z_pct": round(float(pbp["wallclock"].astype(str).str.endswith("Z").mean() * 100), 2),
    "pbp_median_rows_per_game": float(pbp.groupby("game_id").size().median()),
}
# box <-> schedule gap on game_id (2025)
sched25_ids = set(espn.loc[(espn["season_file"] == 2025) & (espn["status_type_state"] == "post"), "game_id"])
box_ids = set(tb["game_id"])
R["sample2025"]["sched_post_games_2025"] = len(sched25_ids)
R["sample2025"]["box_minus_sched_post"] = len(box_ids - sched25_ids)
R["sample2025"]["sched_post_minus_box"] = len(sched25_ids - box_ids)

with open(os.path.join(OUT, "measurements_a.json"), "w") as f:
    json.dump(R, f, indent=1, default=str)

print(json.dumps({k: R[k] for k in [
    "espn_identity", "stats_identity", "espn_status", "espn_unplayed_law",
    "espn_2002_det_artifact", "espn_abbr_vs_stats_mismatch", "ts_canonical_check_2025",
    "recon_rowlevel", "sample2025"]}, indent=1, default=str))
print("WROTE", os.path.join(OUT, "measurements_a.json"))
