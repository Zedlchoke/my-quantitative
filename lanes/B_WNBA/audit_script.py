#!/usr/bin/env python3
"""Lane B (WINPROB-NG-PREP-V1) WNBA data-layer audit.

Reads the downloads under ~/.my-quantitative-data/wnba-v1/raw/ and produces:
  - a row/game census per source and season
  - duplicate / missingness / chronology checks
  - franchise abbreviation transitions (ESPN + WNBA-stats sides)
  - timezone semantics measurement for game timestamps
  - tie / forfeit / anomaly scan
  - sha256 + bytes manifest of every downloaded file, cross-checked
    against GitHub release-asset digests where the API publishes one
  - audit_results.json written next to the data

Usage: python3 audit_script.py [RAW_DIR]  (default: ~/.my-quantitative-data/wnba-v1/raw)
"""
import csv
import gzip
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

import pandas as pd

RAW = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw")
PULL_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Expected sha256 from GitHub API `digest` field on release assets (where published).
EXPECTED = {
    "espn_schedules/wnba_schedule_2024.csv": "62994931d49303abd00f4fd13d46718f6efb97928ae73974e0d3e8cc7015c48f",
    "espn_schedules/wnba_schedule_2025.csv": "b1fe7187113b9336b3a60bbeac6a193fb94883ce85f8f5a7f7821c1056bad988",
    "espn_schedules/wnba_schedule_2026.csv": "685a9256350e356d70ba1d7564440b73e42d01e0a0bfbf3af043c30883a9e543",
    "espn_schedules/wnba_schedule_2024.parquet": "4c4b8f8dc4290996f5fee5786855018a9f4cf07c5c9ac32bc34644f26835cef6",
    "espn_schedules/wnba_schedule_2025.parquet": "c7cc5144a0d4bd84ddd22576930e178a47f81d9570802b2b23823e63ad9a333a",
    "espn_schedules/wnba_schedule_2026.parquet": "58aba80e5814e9f09987d19d17ead087cecabcf2318e5b71628bc9d27dc5acd0",
    "espn_schedules/wnba_games_in_data_repo.csv": "3c39960951874c7bff1470d68188fb9a24c139a4ff1b62a5f914615199faaefd",
    "espn_schedules/wnba_games_in_data_repo.parquet": "bd18568558341e86c59ee4f888f9a2e859516418b5fed700c61bb89add1ba3d5",
    "espn_schedules/wnba_schedule_master.parquet": "05d35418c3b7ccc0a55e505289a249e646fb86db9ce4073bdef4025e52541a57",
    "espn_sample_2025/team_box_2025.csv": "f32d9ebefa40632ff4166337c434ad290a8311497d595b849ee16ab657a55d99",
    "espn_sample_2025/team_box_2025.parquet": "b241743395be6808821a05134d2ea9386a585e6d60c3aa21dfe7c70f7893bf09",
    "espn_sample_2025/player_box_2025.csv": "dd0496590397a72dc36443e73dfea26d15668e3794289d452e882c46a2d90ad0",
    "espn_sample_2025/player_box_2025.parquet": "9a416f637b7e95af85670a26469ec876a7414a6f64e56128f74e054c1cac610f",
    "espn_sample_2025/play_by_play_2025.csv": "01493a7f6c7e368d46b96959fd753b2eda0aaf88b1d0ca403d4e7ee6e7537caf",
    "espn_sample_2025/play_by_play_2025.parquet": "d4c8a43b3700ec5a113b6eb0ca93591a62d32b4bcdabe6c6cd0b2c61bb8dc07e",
    "wnba_stats_schedules/wnba_schedule_2025.csv.gz": "094dc7e91eb0cf3f479e5cd0508079e92950f9fb03c8076b6bc7b9e06695f803",
    "wnba_stats_schedules/wnba_stats_schedule_master.csv": "32d86a60124cfcfaf1952de3fa1fdd7fd8c01608921b4388faaf72a6c928c4f9",
    "wnba_stats_schedules/wnba_stats_schedule_master.parquet": "93dc80e0cbe73003feb4381b388309ceb9356aeaf3bb60f092ccb1575d6d87cc",
    "wnba_stats_schedules/wnba_stats_schedule_2025.csv": "28508741d64c445f1af093d9bca448f6b6eb67dbd829db7b4898f6a5f542d985",
}

results = {"pulled_at_utc": PULL_UTC, "raw_dir": RAW}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- integrity
manifest, digest_mismatch, digest_missing = [], [], []
for root, _, files in os.walk(RAW):
    for fn in sorted(files):
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, RAW)
        if fn.startswith("."):
            continue
        rec = {"file": rel, "bytes": os.path.getsize(p), "sha256": sha256(p)}
        exp = EXPECTED.get(rel)
        rec["github_digest_match"] = None if exp is None else (rec["sha256"] == exp)
        if exp is None and rel.endswith((".csv", ".parquet", ".csv.gz")):
            digest_missing.append(rel)
        elif exp is not None and rec["sha256"] != exp:
            digest_mismatch.append(rel)
        manifest.append(rec)
results["manifest"] = manifest
results["digest_mismatches"] = digest_mismatch
results["assets_without_published_digest"] = len(digest_missing)

# ------------------------------------------------------------ ESPN schedules
espn_rows = []
for y in range(2002, 2027):
    f = os.path.join(RAW, "espn_schedules", f"wnba_schedule_{y}.csv")
    if not os.path.exists(f):
        continue
    d = pd.read_csv(f, low_memory=False)
    d["season_file"] = y
    espn_rows.append(d)
espn = pd.concat(espn_rows, ignore_index=True)
results["espn_schedule"] = {
    "total_rows": int(len(espn)),
    "seasons": sorted(espn["season_file"].unique().tolist()),
    "rows_per_season": {int(k): int(v) for k, v in espn.groupby("season_file").size().items()},
    "unique_game_ids": int(espn["game_id"].nunique()),
    "duplicate_game_id_rows": int(len(espn) - espn["game_id"].nunique()),
    "dup_examples": espn[espn.duplicated("game_id", keep=False)]["game_id"].head(5).tolist(),
    "cols_sample": list(espn.columns[:24]),
}

# structure: one row per game?
g = espn.groupby("game_id").agg(n=("id", "size"),
                                n_home=("home_id", "nunique"),
                                n_away=("away_id", "nunique"))
results["espn_schedule"]["game_grain_violations"] = int(((g.n > 1)).sum())

# missingness: scores null / completed flag
comp = espn["status_type_completed"].astype(str).str.upper().isin(["TRUE", "1"])
scored = espn["home_score"].notna() & espn["away_score"].notna()
results["espn_schedule"]["rows_completed"] = int(comp.sum())
results["espn_schedule"]["rows_completed_but_score_null"] = int((comp & ~scored).sum())
results["espn_schedule"]["rows_not_completed_with_score"] = int((~comp & scored).sum())
results["espn_schedule"]["status_type_state_counts"] = {str(k): int(v) for k, v in espn["status_type_state"].value_counts().items()}
results["espn_schedule"]["null_score_rows_by_season"] = {int(k): int(v) for k, v in espn[~scored].groupby("season_file").size().items()}
results["espn_schedule"]["attendance_null_by_season"] = {int(k): int(v) for k, v in espn[espn["attendance"].isna()].groupby("season_file").size().items()}

# season_type / playoffs
results["espn_schedule"]["season_type_counts"] = {str(k): int(v) for k, v in espn["season_type"].fillna("<null>").astype(str).value_counts().items()}
post = espn["notes_headline"].fillna("").str.contains("Finals|Playoff|Semifinal|First Round|Round 1|Game [0-9]", case=False, regex=True)
results["espn_schedule"]["rows_with_playoff_style_headline"] = int(post.sum())

# chronology
bad_chrono = {}
for y in range(2002, 2027):
    d = espn[espn["season_file"] == y]
    dates = pd.to_datetime(d["date"], utc=True, errors="coerce").sort_values()
    bad_chrono[y] = bool(dates.is_monotonic_increasing is False and dates.notna().all() and (dates.diff().dt.total_seconds().dropna() < 0).any())
results["espn_schedule"]["season_files_where_date_not_sorted_asc_in_file"] = [y for y, b in bad_chrono.items() if b]

# timezone semantics: schedule `date` col is UTC instant; measure skew vs local tip
tz_probe = espn[espn["game_date_time"].notna()].copy()
tz_probe["utc_date"] = pd.to_datetime(tz_probe["date"], utc=True, errors="coerce")
tz_probe["local_from_gdt"] = pd.to_datetime(tz_probe["game_date_time"], utc=True, errors="coerce")
same_inst = (tz_probe["utc_date"] == tz_probe["local_from_gdt"]).mean()
tz_probe["gdt_offset"] = tz_probe["game_date_time"].astype(str).str.extract(r"([+-]\d{4})$")[0]
results["espn_schedule"]["tz_semantics"] = {
    "schedule_date_col_example": str(espn["date"].iloc[0]),
    "game_date_time_example": str(tz_probe["game_date_time"].iloc[0]),
    "schedule_date_equals_gdt_instant_pct": round(float(same_inst * 100), 2),
    "gdt_offset_distribution": {str(k): int(v) for k, v in tz_probe["gdt_offset"].value_counts().head(8).items()},
    "gdt_offsets_by_season_example_2025": {str(k): int(v) for k, v in tz_probe[tz_probe.season_file == 2025]["gdt_offset"].value_counts().items()},
}

# franchise map from abbrevs
fr = defaultdict(set)
for _, r in espn.iterrows():
    ab = r["home_abbreviation"]
    if pd.notna(ab):
        fr[str(ab)].add(str(r["home_display_name"]) if pd.notna(r["home_display_name"]) else f"{r['home_location']} {r['home_name']}")
esp_abbr = {k: sorted(v) for k, v in sorted(fr.items())}
results["espn_schedule"]["abbrev_to_display_names"] = esp_abbr

# franchise transitions measured from data
tr = espn.drop_duplicates(["season_file", "home_abbreviation"])[["season_file", "home_abbreviation"]].sort_values("season_file")
results["espn_schedule"]["abbrevs_by_season"] = {int(y): sorted(gg) for y, gg in tr.groupby("season_file")["home_abbreviation"]}

# neutral site
ns = espn["neutral_site"].astype(str).str.upper().isin(["TRUE", "1"])
results["espn_schedule"]["neutral_site_true_by_season"] = {int(k): int(v) for k, v in espn[ns].groupby("season_file").size().items()}

# ties / anomalies among completed games
done = espn[comp & scored].copy()
done["home_score"] = done["home_score"].astype(float)
done["away_score"] = done["away_score"].astype(float)
results["espn_schedule"]["completed_ties"] = int((done["home_score"] == done["away_score"]).sum())
results["espn_schedule"]["completed_zero_scores"] = int(((done["home_score"] == 0) | (done["away_score"] == 0)).sum())
results["espn_schedule"]["max_single_team_score"] = float(pd.concat([done["home_score"], done["away_score"]]).max())
results["espn_schedule"]["min_single_team_score_completed"] = float(pd.concat([done["home_score"], done["away_score"]]).min())

# ------------------------------------------------------------ WNBA stats schedules
st_rows = []
for y in range(1997, 2027):
    f = os.path.join(RAW, "wnba_stats_schedules", f"wnba_schedule_{y}.csv.gz")
    if not os.path.exists(f):
        continue
    d = pd.read_csv(f, compression="gzip")
    d["season_file"] = y
    st_rows.append(d)
stats = pd.concat(st_rows, ignore_index=True)
results["stats_schedule"] = {
    "total_rows": int(len(stats)),
    "seasons": sorted(stats["season_file"].unique().tolist()),
    "rows_per_season": {int(k): int(v) for k, v in stats.groupby("season_file").size().items()},
    "unique_game_ids": int(stats["game_id"].nunique()),
    "duplicate_game_id_rows": int(len(stats) - stats["game_id"].nunique()),
    "season_type_counts": {str(k): int(v) for k, v in stats["season_type"].value_counts().items()},
    "game_id_format_examples_by_decade": {
        "1997": str(stats[stats.season_file == 1997]["game_id"].iloc[0]),
        "2010": str(stats[stats.season_file == 2010]["game_id"].iloc[0]),
        "2025": str(stats[stats.season_file == 2025]["game_id"].iloc[0]),
    },
}
st = stats.drop_duplicates(["season_file", "home_team_abbreviation"])
results["stats_schedule"]["abbrevs_by_season"] = {int(y): sorted(gg) for y, gg in st.groupby("season_file")["home_team_abbreviation"]}
# ties in completed stats-side games
sd = stats[stats["home_pts"].notna() & stats["away_pts"].notna()]
results["stats_schedule"]["scored_ties"] = int((sd["home_pts"] == sd["away_pts"]).sum())
results["stats_schedule"]["games_with_score_pct"] = round(float(100 * len(sd) / len(stats)), 2)

# cross-source check ESPN vs stats side on common seasons
xcheck = {}
for y in range(2002, 2026):
    e_n = int((espn["season_file"] == y).sum())
    s_n = int((stats["season_file"] == y).sum())
    xcheck[y] = {"espn": e_n, "stats": s_n, "diff": e_n - s_n}
results["cross_source_games_per_season"] = xcheck

# ------------------------------------------------------------ sample 2025 audits
tb = pd.read_csv(os.path.join(RAW, "espn_sample_2025", "team_box_2025.csv"), low_memory=False)
pb = pd.read_csv(os.path.join(RAW, "espn_sample_2025", "player_box_2025.csv"), low_memory=False)
pbp = pd.read_csv(os.path.join(RAW, "espn_sample_2025", "play_by_play_2025.csv"), low_memory=False)

results["team_box_2025"] = {
    "rows": int(len(tb)),
    "unique_games": int(tb["game_id"].nunique()),
    "rows_per_game_violations": int((tb.groupby("game_id").size() != 2).sum()),
    "season_type_counts": {str(k): int(v) for k, v in tb["season_type"].value_counts().items()},
    "points_in_paint_notnull_pct": round(float(tb["points_in_paint"].notna().mean() * 100), 2),
    "cols": len(tb.columns),
}
games_sched_2025 = espn[(espn.season_file == 2025) & comp & scored]
results["team_box_2025"]["sched_completed_games_2025"] = int(len(games_sched_2025))
results["team_box_2025"]["box_games_vs_sched_completed"] = int(tb["game_id"].nunique() - len(games_sched_2025))

results["player_box_2025"] = {
    "rows": int(len(pb)),
    "unique_games": int(pb["game_id"].nunique()),
    "unique_players": int(pb["athlete_id"].nunique()),
    "median_rows_per_game": float(pb.groupby("game_id").size().median()),
    "starters_true_per_game_median": float(pb[pb["starter"].astype(str).str.upper() == "TRUE"].groupby("game_id").size().median()),
    "starter_col_values": {str(k): int(v) for k, v in pb["starter"].value_counts().items()},
    "dnp_reason_counts": {str(k): int(v) for k, v in pb["reason"].fillna("<null>").value_counts().head(10).items()},
    "did_not_play_counts": {str(k): int(v) for k, v in pb["did_not_play"].astype(str).value_counts().items()},
    "active_col_counts": {str(k): int(v) for k, v in pb["active"].astype(str).value_counts().items()},
}
results["play_by_play_2025"] = {
    "rows": int(len(pbp)),
    "unique_games": int(pbp["game_id"].nunique()),
    "median_rows_per_game": float(pbp.groupby("game_id").size().median()),
    "period_max": int(pbp["period_number"].max()),
    "type_text_top5": {str(k): int(v) for k, v in pbp["type_text"].value_counts().head(5).items()},
    "wallclock_example": str(pbp["wallclock"].iloc[0]),
    "wallclock_all_utc_z_pct": round(float(pbp["wallclock"].astype(str).str.endswith("Z").mean() * 100), 2),
    "text_example": str(pbp["text"].iloc[0])[:120],
}
# clock sanity: end_game_seconds_remaining should be non-increasing within a game
one = pbp[pbp["game_id"] == pbp["game_id"].iloc[0]].copy()
one["seq"] = pd.to_numeric(one["sequence_number"], errors="coerce")
one = one.sort_values("seq")
egsr = pd.to_numeric(one["end_game_seconds_remaining"], errors="coerce").dropna()
results["play_by_play_2025"]["clock_monotonic_decreasing_within_game0"] = bool((egsr.diff().dropna() <= 0).mean() > 0.98)

# injuries / lineups availability statement inputs
results["pit_inputs"] = {
    "dedicated_injury_columns_in_player_box": sorted([c for c in pb.columns if c in ("reason", "did_not_play", "active", "ejected", "starter")]),
    "injury_feed_in_downloads": "NONE (no injury dataset in wehoop-family releases)",
    "lineup_datasets_available_not_downloaded": ["espn_wnba_game_rosters (2002-2026, 29MB)", "wnba_stats_lineups (2026 only, 18MB)"],
}

with open(os.path.join(RAW, "audit_results.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)

# ------------------------------------------------------------ console summary
print(f"PULL {PULL_UTC}")
print(f"files hashed: {len(manifest)} | digest mismatches: {len(digest_mismatch)} {digest_mismatch}")
print(f"assets without published digest: {results['assets_without_published_digest']}")
es = results["espn_schedule"]
print(f"ESPN schedule rows={es['total_rows']} seasons={len(es['seasons'])} unique_ids={es['unique_game_ids']} dupes={es['duplicate_game_id_rows']} grain_viol={es['game_grain_violations']}")
print("rows/season:", json.dumps(es["rows_per_season"]))
print("null-score rows by season:", json.dumps(es["null_score_rows_by_season"]))
print("attendance nulls by season:", json.dumps(es["attendance_null_by_season"]))
print("season_type:", json.dumps(es["season_type_counts"]))
print("tz:", json.dumps(es["tz_semantics"]["gdt_offsets_by_season_example_2025"]), "| equal-instant pct:", es["tz_semantics"]["schedule_date_equals_gdt_instant_pct"])
print("ties:", es["completed_ties"], "zero-scores:", es["completed_zero_scores"], "max pts:", es["max_single_team_score"])
print("neutral_site TRUE by season:", json.dumps(es["neutral_site_true_by_season"]))
print("abbrevs_by_season:", json.dumps(es["abbrevs_by_season"]))
ss = results["stats_schedule"]
print(f"STATS schedule rows={ss['total_rows']} seasons={len(ss['seasons'])} unique_ids={ss['unique_game_ids']} dupes={ss['duplicate_game_id_rows']}")
print("stats rows/season:", json.dumps(ss["rows_per_season"]))
print("stats abbrevs_by_season:", json.dumps(ss["abbrevs_by_season"]))
print("cross-source diffs (non-zero only):", {y: v for y, v in results["cross_source_games_per_season"].items() if v["diff"] != 0})
print("team_box:", json.dumps(results["team_box_2025"]))
print("player_box:", json.dumps({k: v for k, v in results["player_box_2025"].items() if k != "cols"}))
print("pbp:", json.dumps(results["play_by_play_2025"]))
print("pit:", json.dumps(results["pit_inputs"]))
