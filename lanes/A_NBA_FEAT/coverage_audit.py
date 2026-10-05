#!/usr/bin/env python
"""Lane A_NBA_FEAT (WINPROB-PLAYERFEAT-PREP-V1) — per-season coverage audit.

Joins player_box 2016..2026 (predecessor 3 seasons read-only + 8 downloaded
this lane) to the schedule corpus on ESPN game_id. Emits a machine-readable
summary to stdout and a full evidence log under provenance/.

Read-only inputs:
  ~/.my-quantitative-data/playerdata-prep-v1/nba/player_box_raw/player_box_{2016,2021,2026}.csv
  ~/.my-quantitative-data/playerfeat-prep-v1/nba/player_box_raw/player_box_{2017..2020,2022..2025}.csv
  ~/.my-quantitative-data/nba-hoopr-v1/raw/nba_schedule_<season>.csv
"""
import json
import sys
from pathlib import Path

import pandas as pd

DATA = Path.home() / ".my-quantitative-data"
PRED = DATA / "playerdata-prep-v1" / "nba" / "player_box_raw"
CURR = DATA / "playerfeat-prep-v1" / "nba" / "player_box_raw"
SCHED = DATA / "nba-hoopr-v1" / "raw"
PROV = DATA / "playerfeat-prep-v1" / "nba" / "provenance"
SEASONS = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]

# Predecessor-documented 2026 schema (COVERAGE_SCHEMA.md §3, 57 columns),
# re-measured here from the pinned predecessor 2026 CSV header.
_pred_2026 = DATA / "playerdata-prep-v1" / "nba" / "player_box_raw" / "player_box_2026.csv"
PRED_COLUMNS = sorted(pd.read_csv(_pred_2026, nrows=0).columns.tolist())
assert len(PRED_COLUMNS) == 57, len(PRED_COLUMNS)

BOX_DTYPE = {
    "game_id": "int64", "season": "int64", "season_type": "int64",
    "team_id": "int64", "opponent_team_id": "Int64",
    "athlete_id": "Int64", "minutes": "float64", "points": "float64",
}
SCHED_DTYPE = {"game_id": "int64", "season": "int64", "season_type": "int64",
               "home_id": "int64", "away_id": "int64",
               "home_score": "float64", "away_score": "float64"}


def as_bool(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s
    return s.astype("string").str.strip().eq("True").fillna(False)


def box_path(season: int) -> Path:
    p = CURR / f"player_box_{season}.csv"
    return p if p.exists() else PRED / f"player_box_{season}.csv"


def audit_season(season: int, log) -> dict:
    bp = box_path(season)
    sp = SCHED / f"nba_schedule_{season}.csv"
    log(f"=== season {season} ===")
    log(f"box={bp}")
    log(f"sched={sp}")
    box = pd.read_csv(bp, dtype=BOX_DTYPE, low_memory=False)
    sch = pd.read_csv(sp, dtype=SCHED_DTYPE, low_memory=False)

    # --- schema drift vs predecessor-documented 57 columns
    cols = sorted(box.columns)
    drift = {
        "n_cols": len(cols),
        "n_pred": len(PRED_COLUMNS),
        "missing_vs_pred": sorted(set(PRED_COLUMNS) - set(cols)),
        "extra_vs_pred": sorted(set(cols) - set(PRED_COLUMNS)),
    }

    # --- season label convention (ending-year): game_date range + season col
    gd = pd.to_datetime(box["game_date"], format="mixed", utc=True)
    season_col_vals = sorted(box["season"].unique().tolist())
    label_check = {
        "season_col_values": season_col_vals,
        "game_date_min": str(gd.min().date()),
        "game_date_max": str(gd.max().date()),
        "ending_year_ok": bool(season_col_vals == [season]
                               and gd.min().year in (season - 1,)
                               and gd.max().year in (season,)),
    }

    # --- schedule: rows, season_type composition, played games
    sch_by_st = sch["season_type"].value_counts().sort_index().to_dict()
    sch_by_st = {int(k): int(v) for k, v in sch_by_st.items()}
    reg_post_rows = int(sch["season_type"].isin([2, 3]).sum())
    played = sch[
        sch["status_type_name"].eq("STATUS_FINAL")
        & sch["home_score"].notna() & sch["away_score"].notna()
    ]
    played_ids = set(played["game_id"])

    # --- tip-time semantics from bytes: game_date_time (local+offset) vs start_date (UTC)
    gdt = pd.to_datetime(sch["game_date_time"], format="mixed", utc=True)
    sdt = pd.to_datetime(sch["start_date"], format="mixed", utc=True)
    gdt_parse_fail = int(pd.isna(gdt).sum())
    sdt_parse_fail = int(pd.isna(sdt).sum())
    eq = int((gdt == sdt).sum())
    tip = {"gdt_parse_fail": gdt_parse_fail, "sdt_parse_fail": sdt_parse_fail,
           "utc_equal_rows": eq, "sched_rows": len(sch)}

    # --- box structure
    n_rows = len(box)
    box_games = box["game_id"].unique()
    n_box_games = int(len(box_games))
    dup_mask = box.duplicated(subset=["game_id", "athlete_id"], keep=False)
    # duplicates on (game_id, athlete_id) among identified rows only
    ident = box[box["athlete_id"].notna()]
    dups = int(ident.duplicated(subset=["game_id", "athlete_id"]).sum())
    dnp = int(as_bool(box["did_not_play"]).sum())
    null_ath = int(box["athlete_id"].isna().sum())
    ppg = box.groupby("game_id").size()
    st_counts = {int(k): int(v) for k, v in
                 box["season_type"].value_counts().sort_index().items()}

    # --- joins
    box_id_set = set(box_games.tolist())
    joined_played = len(played_ids & box_id_set)
    join_rate = joined_played / len(played_ids) if played_ids else float("nan")
    orphans = sorted(box_id_set - set(sch["game_id"].tolist()))
    missing_played = sorted(played_ids - box_id_set)
    miss_status = (sch[sch["game_id"].isin(missing_played)]
                   ["status_type_name"].value_counts().to_dict())
    miss_status = {str(k): int(v) for k, v in miss_status.items()}

    res = {
        "season": season,
        "box_file": str(bp),
        "box_rows": n_rows,
        "box_cols": len(cols),
        "schema_drift": drift,
        "label_check": label_check,
        "sched_rows_total": len(sch),
        "sched_rows_by_season_type": sch_by_st,
        "sched_reg_post_rows": reg_post_rows,
        "sched_played_games": int(len(played_ids)),
        "box_distinct_games": n_box_games,
        "join_rate_played": round(join_rate, 4),
        "joined_played_games": joined_played,
        "orphan_box_games": len(orphans),
        "missing_played_status": miss_status,
        "dup_game_athlete_rows": dups,
        "dnp_rows": dnp,
        "null_athlete_rows": null_ath,
        "players_per_game_median": float(ppg.median()),
        "players_per_game_min": int(ppg.min()),
        "players_per_game_max": int(ppg.max()),
        "box_rows_by_season_type": st_counts,
        "tip_semantics": tip,
    }
    log(json.dumps({k: v for k, v in res.items() if k != "schema_drift"}, default=str))
    log("schema_drift=" + json.dumps(drift))
    if orphans:
        log("orphan_game_ids=" + ",".join(map(str, orphans[:50])))
    return res


def main() -> int:
    PROV.mkdir(parents=True, exist_ok=True)
    lines = []

    def log(s: str) -> None:
        print(s, flush=True)
        lines.append(s)

    results = [audit_season(s, log) for s in SEASONS]
    summary = {
        "cycle_id": "WINPROB-PLAYERFEAT-PREP-V1",
        "lane": "A_NBA_FEAT",
        "seasons": results,
        "totals": {
            "sched_rows_total": sum(r["sched_rows_total"] for r in results),
            "sched_played_games": sum(r["sched_played_games"] for r in results),
            "box_rows": sum(r["box_rows"] for r in results),
            "box_distinct_games": sum(r["box_distinct_games"] for r in results),
            "null_athlete_rows": sum(r["null_athlete_rows"] for r in results),
            "dup_game_athlete_rows": sum(r["dup_game_athlete_rows"] for r in results),
            "orphan_box_games": sum(r["orphan_box_games"] for r in results),
        },
    }
    (PROV / "coverage_audit_11seasons.json").write_text(json.dumps(summary, indent=2))
    (PROV / "coverage_audit_11seasons.txt").write_text("\n".join(lines) + "\n")
    print("SUMMARY_JSON_WRITTEN", PROV / "coverage_audit_11seasons.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
