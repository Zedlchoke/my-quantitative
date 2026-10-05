"""Lane A (NBA-WINPROB-NG-PREP-V1) — schedule-corpus measurement.

SCHEMA/COVERAGE COUNTING ONLY. No win-prob metrics, no scored computation,
no model outputs on real outcomes (plan boundary).
Read-only on ~/.my-quantitative-data/nba-hoopr-v1/raw/ (EXTEND-ONLY corpus).

Outputs: measure_schedule_corpus.json (next to this script) + stdout summary.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

HOOPR = Path.home() / ".my-quantitative-data/nba-hoopr-v1/raw"
OUT = Path(__file__).parent / "measure_schedule_corpus.json"

SEASONS = list(range(2016, 2027))
ALLSTAR_PSEUDO = {"EAST", "WEST"}

R = {"ran_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}

# ---------------------------------------------------------------- A. schema
frames = {}
col_sets = {}
for s in SEASONS:
    f = HOOPR / f"nba_schedule_{s}.csv"
    df = pd.read_csv(f, dtype=str, keep_default_na=False)
    frames[s] = df
    col_sets[s] = set(df.columns)

base_cols = col_sets[2016]
schema_diffs = {}
for s in SEASONS:
    extra = sorted(col_sets[s] - base_cols)
    missing = sorted(base_cols - col_sets[s])
    if extra or missing:
        schema_diffs[s] = {"extra_cols": extra, "missing_cols": missing}
R["n_files"] = len(SEASONS)
R["n_columns_2016"] = len(base_cols)
R["schema_diffs_vs_2016"] = schema_diffs

df = pd.concat([frames[s].assign(season_file=s) for s in SEASONS], ignore_index=True)
R["total_rows"] = int(len(df))

# ------------------------------------------------------------- B. identity
R["unique_game_id"] = int(df["game_id"].nunique())
R["unique_id"] = int(df["id"].nunique())
R["game_id_eq_id_all_rows"] = bool((df["game_id"] == df["id"]).all())
dupes = df[df.duplicated("game_id", keep=False)]
R["rows_in_duplicated_game_id"] = int(len(dupes))
R["duplicated_game_ids_across_files"] = int(dupes["game_id"].nunique())

# --------------------------------------------------- C. season_type splits
df["season_type"] = df["season_type"].astype(int)
df["season"] = df["season"].astype(int)
st_counts = (
    df.groupby(["season_file", "season_type"]).size().unstack(fill_value=0)
)
R["season_type_counts_by_season_file"] = {
    int(k): {str(c): int(v) for c, v in row.items()}
    for k, row in st_counts.iterrows()
}
R["season_type_values_observed"] = sorted(df["season_type"].unique().tolist())

# NOTE: `season` field vs season_file — measure mismatch
R["season_field_eq_season_file"] = bool((df["season"] == df["season_file"]).all())

# --------------------------------------------- D. status / completed flags
df["completed"] = df["status_type_completed"].str.lower() == "true"
not_completed = df[~df["completed"]]
R["rows_not_completed_total"] = int(len(not_completed))
R["rows_not_completed_by_season"] = {
    int(k): int(v) for k, v in not_completed.groupby("season_file").size().items()
}
R["not_completed_status_descriptions"] = sorted(
    not_completed["status_type_description"].unique().tolist()
)
R["not_completed_detail_samples"] = sorted(
    not_completed["status_type_detail"].unique().tolist()
)[:10]
R["not_completed_state_values"] = sorted(
    not_completed["status_type_state"].unique().tolist()
)
# post vs pre among not-completed (postponed makeup listings sit at 'post' only
# if played elsewhere; scheduled-but-not-played remain 'pre'/'in')
R["not_completed_by_state"] = {
    k: int(v) for k, v in not_completed.groupby("status_type_state").size().items()
}

# postponed duplicate listings: a postponed row AND a completed row for the
# same home/away pair + season (the makeup carries a different game_id)
ppd = not_completed.copy()
pair_keys = (
    ppd["home_abbreviation"] + "|" + ppd["away_abbreviation"] + "|" + ppd["season_file"].astype(str)
)
comp_pairs = set(
    df[df["completed"]]["home_abbreviation"]
    + "|"
    + df[df["completed"]]["away_abbreviation"]
    + "|"
    + df[df["completed"]]["season_file"].astype(str)
)
ppd["has_makeup_candidate"] = pair_keys.isin(comp_pairs)
R["postponed_rows_with_makeup_candidate"] = int(ppd["has_makeup_candidate"].sum())
R["postponed_rows_total"] = int(len(ppd))
R["postponed_sample"] = [
    {
        "game_id": r["game_id"],
        "season": int(r["season_file"]),
        "date": r["game_date"],
        "home": r["home_abbreviation"],
        "away": r["away_abbreviation"],
        "status": r["status_type_description"],
        "notes": r["notes_headline"][:60],
        "has_makeup_candidate": bool(r["has_makeup_candidate"]),
    }
    for _, r in ppd.head(12).iterrows()
]

# ------------------------------------------------------------ E. All-Star
al = df[
    (df["season_type"] == 2)
    & (
        df["home_abbreviation"].isin(ALLSTAR_PSEUDO)
        | df["away_abbreviation"].isin(ALLSTAR_PSEUDO)
    )
]
R["allstar_rows_total"] = int(len(al))
R["allstar_by_season"] = {
    int(k): int(v) for k, v in al.groupby("season_file").size().items()
}
R["allstar_display_names"] = sorted(al["home_display_name"].unique().tolist())
R["allstar_completed_flags"] = {
    str(k): int(v) for k, v in al["completed"].value_counts().items()
}

# ---------------------------------------------------------- F. NBA Cup rows
cup_mask = df["notes_headline"].str.contains(
    "In-Season|NBA Cup|Championship", case=False, regex=True, na=False
)
cup = df[cup_mask]
R["cup_rows_total"] = int(len(cup))
R["cup_rows_by_season"] = {
    int(k): int(v) for k, v in cup.groupby("season_file").size().items()
}
R["cup_notes_headlines"] = sorted(cup["notes_headline"].unique().tolist())[:12]
R["cup_season_types"] = {
    str(k): int(v) for k, v in cup["season_type"].value_counts().items()
}
R["cup_neutral_site_values"] = {
    str(k): int(v) for k, v in cup["neutral_site"].str.lower().value_counts().items()
}
R["cup_completed_flags"] = {
    str(k): int(v) for k, v in cup["completed"].value_counts().items()
}

# ------------------------------------------------- G. dedupe law APPLIED
# law: keep status_type_completed == True; exclude All-Star EAST/WEST rows;
# one row per game_id (uniqueness already verified); flag Cup finals.
kept = df[df["completed"] & ~df.index.isin(al.index)].copy()
kept["is_cup"] = kept["notes_headline"].str.contains(
    "In-Season|NBA Cup|Championship", case=False, regex=True, na=False
)
played = {}
for s in SEASONS:
    sub = kept[kept["season_file"] == s]
    played[s] = {
        "raw_rows": int(len(frames[s])),
        "played_total": int(len(sub)),
        "regular_season_type2": int((sub["season_type"] == 2).sum()),
        "regular_non_cup": int(((sub["season_type"] == 2) & ~sub["is_cup"]).sum()),
        "cup_final_flagged": int((sub["is_cup"] & (sub["season_type"] == 2)).sum()),
        "play_in_type5": int((sub["season_type"] == 5).sum()),
        "playoffs_type3": int((sub["season_type"] == 3).sum()),
        "excluded_not_completed": int((~frames[s]["status_type_completed"].str.lower().eq("true")).sum()),
        "excluded_allstar": int(((frames[s]["season_type"] == 2) & frames[s]["home_abbreviation"].isin(ALLSTAR_PSEUDO)).sum()),
        "first_game_date": sub["game_date"].min(),
        "last_game_date": sub["game_date"].max(),
    }
R["played_counts_by_season"] = {str(k): v for k, v in played.items()}
R["kept_total"] = int(len(kept))

# --------------------------------------------- H. tip_utc canonicalization
gdt = pd.to_datetime(df["game_date_time"], format="ISO8601", utc=True, errors="coerce")
sd = pd.to_datetime(df["start_date"], format="ISO8601", utc=True, errors="coerce")
dt_ = pd.to_datetime(df["date"], format="ISO8601", utc=True, errors="coerce")
R["game_date_time_parse_fail"] = int(gdt.isna().sum())
R["start_date_parse_fail"] = int(sd.isna().sum())
R["tip_utc_eq_start_date_rows"] = int((gdt == sd).sum())
R["tip_utc_ne_start_date_rows"] = int((gdt != sd).sum())
R["start_date_eq_date_rows"] = int((sd == dt_).sum())
R["date_ne_start_date_rows"] = int((dt_ != sd).sum())
mm = df[gdt != sd]
R["tip_vs_start_date_mismatch_sample"] = [
    {
        "game_id": r["game_id"],
        "game_date_time": r["game_date_time"],
        "start_date": r["start_date"],
        "date": r["date"],
    }
    for _, r in mm.head(8).iterrows()
]
# local date (game_date) vs UTC date of the same instant — the DST/lawnmower quirk
utc_date = gdt.dt.tz_convert("UTC").dt.date
loc_date = pd.to_datetime(df["game_date"], format="%Y-%m-%d").dt.date
R["rows_where_utc_date_ne_local_date"] = int((utc_date != loc_date).sum())

# offset census + DST correctness on ET-home games
off = df["game_date_time"].str.slice(-5)
R["offset_value_counts_top"] = {k: int(v) for k, v in off.value_counts().head(8).items()}
ET = ZoneInfo("America/New_York")
et_home = df[
    df["home_abbreviation"].isin(
        ["BOS", "BKN", "NYK", "PHI", "TOR", "CHI", "CLE", "DET", "IND", "MIL",
         "ATL", "CHA", "MIA", "ORL", "WSH", "WAS"]
    )
]
et_gdt = pd.to_datetime(et_home["game_date_time"], format="ISO8601", utc=True)
expected_off = et_gdt.dt.tz_convert(ET).apply(lambda t: t.strftime("%z"))
actual_off = et_home["game_date_time"].str.slice(-5)
dst_bad = expected_off.reset_index(drop=True) != actual_off.reset_index(drop=True)
R["et_home_rows_checked"] = int(len(et_home))
R["et_home_offset_mismatches_vs_America_New_York"] = int(dst_bad.sum())
if int(dst_bad.sum()):
    bad_idx = et_home.reset_index(drop=True)[dst_bad]
    R["et_home_offset_mismatch_sample"] = [
        {
            "game_id": r["game_id"],
            "game_date_time": r["game_date_time"],
            "home": r["home_abbreviation"],
            "date": r["game_date"],
        }
        for _, r in bad_idx.head(8).iterrows()
    ]
# DST flip demo: one ET team, games around the Nov and Mar transitions
bos = df[df["home_abbreviation"] == "BOS"].copy()
bos_gdt = pd.to_datetime(bos["game_date_time"], format="ISO8601", utc=True)
flip_rows = []
for _, r in bos.assign(_t=bos_gdt).sort_values("_t").iterrows():
    o = r["game_date_time"][-5:]
    if flip_rows and flip_rows[-1]["offset"] != o:
        flip_rows.append(
            {
                "game_date": r["game_date"],
                "game_date_time": r["game_date_time"],
                "offset": o,
            }
        )
        if len(flip_rows) >= 6:
            break
R["bos_offset_flip_sample"] = flip_rows

# --------------------------------------------------------- I. spot rows for BDL
# deterministic pick: one mid-October-to-January completed regular-season game
# per selected season, home team BOS/DEN/OKC/MIA/LAL pool for stability
spot = []
want_seasons = [2016, 2018, 2020, 2021, 2022, 2024, 2025, 2026]
for s in want_seasons:
    sub = kept[(kept["season_file"] == s) & (kept["season_type"] == 2)]
    sub = sub[sub["home_abbreviation"].isin(["BOS", "DEN", "OKC", "MIA", "LAL", "GS"])]
    sub = sub[pd.to_datetime(sub["game_date"]).dt.month.isin([11, 12, 1])]
    if len(sub):
        r = sub.iloc[len(sub) // 2]
        spot.append(
            {
                "season_file": int(s),
                "bdl_season_starting": int(s) - 1,
                "game_id": r["game_id"],
                "game_date_local": r["game_date"],
                "home_abbr": r["home_abbreviation"],
                "away_abbr": r["away_abbreviation"],
                "home_display": r["home_display_name"],
                "away_display": r["away_display_name"],
                "home_score": int(r["home_score"]),
                "away_score": int(r["away_score"]),
                "tip_utc": pd.Timestamp(r["start_date"]).isoformat().replace("+00:00", "Z"),
                "tip_local": r["game_date_time"],
            }
        )
R["bdl_spot_candidates"] = spot

OUT.write_text(json.dumps(R, indent=1, default=str))
print(json.dumps({k: v for k, v in R.items() if k not in ("played_counts_by_season",)}, indent=1, default=str)[:4000])
print("PLAYED COUNTS:")
for s, v in played.items():
    print(s, v)
