#!/usr/bin/env python3
"""Lane A (WNBA-WINPROB-PREP-V1) game-universe measurement — attempt 2.

Resumes/extends lanes/A_DATA/measure_a.py (attempt 1, killed by infra rate-limiting).
Fixes measured in attempt 1 output and re-verified here:
  - stats season_type is STRING ('regular-season'/'playoffs'); attempt 1 compared == 2/3 -> zeros.
  - attempt 1 'espn ts instant equality 94.03%/360 unequal' was a pandas mixed-format parse
    artifact; per-season ISO8601 parsing shows date == game_date_time instant for 100%.
  - attempt 1 DST sample 2025 empty (regex hunted offsets in a Z-suffixed column).
  - attempt 1 row-level join mixed UTC date vs local date and keyed by game_id prefix.
  - All-Star alias set extended: WIL/STE/COL/SPO/USA (attempt 1 missed Team Wilson/Stewart/Collier/Spoon/USA rows).
Canonical team keys are FRANCHISE-level (PHO==PHX 2025+, POR(2000-02)==PDX(2026)).

Read-only over ~/.my-quantitative-data/wnba-v1/raw/ (EXTEND-ONLY corpus).
Schema/coverage counting ONLY — no win-prob metrics, no scored computation.
Writes ~/.my-quantitative-data/wnba-prep-v1/measurements_a2.json and team_key_table.csv.
"""
import json
import os

import pandas as pd

RAW = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw")
OUT = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1")
os.makedirs(OUT, exist_ok=True)

R = {}

# ------------------------------------------------------------------ load
espn_rows, stats_rows = [], []
for y in range(2002, 2027):
    d = pd.read_csv(os.path.join(RAW, "espn_schedules", f"wnba_schedule_{y}.csv"), low_memory=False)
    d["season_file"] = y
    espn_rows.append(d)
espn = pd.concat(espn_rows, ignore_index=True)
for y in range(1997, 2027):
    d = pd.read_csv(os.path.join(RAW, "wnba_stats_schedules", f"wnba_schedule_{y}.csv.gz"), compression="gzip")
    d["season_file"] = y
    stats_rows.append(d)
stats = pd.concat(stats_rows, ignore_index=True)

R["espn_identity"] = {
    "rows": int(len(espn)),
    "seasons": [int(x) for x in sorted(espn["season_file"].unique())],
    "unique_game_id": int(espn["game_id"].nunique()),
    "game_id_len_distribution": {str(k): int(v) for k, v in espn["game_id"].astype(str).str.len().value_counts().items()},
    "game_id_examples": [str(x) for x in espn["game_id"].iloc[[0, len(espn) // 2, -1]]],
}
R["stats_identity"] = {
    "rows": int(len(stats)),
    "seasons": [int(x) for x in sorted(stats["season_file"].unique())],
    "unique_game_id": int(stats["game_id"].nunique()),
    "game_id_len_distribution": {str(k): int(v) for k, v in stats["game_id"].astype(str).str.len().value_counts().items()},
    "game_id_examples": [str(x) for x in stats["game_id"].iloc[[0, len(stats) // 2, -1]]],
    "game_id_season_prefix_verified": bool(
        all(str(r["game_id"])[3:5] == f"{r['season'] % 100:02d}" for _, r in stats.iterrows())
    ),
    "game_id_first2": {str(k): int(v) for k, v in stats["game_id"].astype(str).str[:2].value_counts().items()},
    "game_id_type_digit": {str(k): int(v) for k, v in stats["game_id"].astype(str).str[2].value_counts().items()},
    "game_id_type_digit_vs_season_type_crosstab": {
        f"{td}/{st}": int(len(stats[(stats["game_id"].astype(str).str[2] == td) & (stats["season_type"] == st)]))
        for td in ("2", "4") for st in sorted(set(stats["season_type"].astype(str)))
    },
    "season_type_values": sorted(set(stats["season_type"].astype(str))),
}

# ------------------------------------------------------------------ ESPN status / 0-0 prefill law
R["espn_status"] = {
    "state_counts": {str(k): int(v) for k, v in espn["status_type_state"].value_counts().items()},
    "detail_counts_post": {
        str(k): int(v) for k, v in espn.loc[espn["status_type_state"] == "post", "status_type_detail"].fillna("<null>").value_counts().items()
    },
}
pre = espn[espn["status_type_state"] != "post"]
prefill = (
    pd.to_numeric(pre["home_score"], errors="coerce").eq(0) & pd.to_numeric(pre["away_score"], errors="coerce").eq(0)
)
R["espn_unplayed_law"] = {
    "nonpost_rows": int(len(pre)),
    "nonpost_by_season": {int(k): int(v) for k, v in pre.groupby("season_file").size().items()},
    "nonpost_prefilled_0_0": int(prefill.sum()),
    "nonpost_not_0_0": int((~prefill).sum()),
}
R["espn_forfeit"] = espn.loc[espn["status_type_detail"].fillna("").str.contains("Forfeit", case=False),
    ["game_id", "season_file", "date", "home_display_name", "away_display_name", "home_score", "away_score", "status_type_state"]
].astype(str).to_dict("records")
R["espn_postponed"] = espn.loc[espn["status_type_detail"].fillna("").str.contains("Postponed", case=False),
    ["game_id", "season_file", "date", "home_display_name", "away_display_name", "home_score", "away_score", "status_type_state"]
].astype(str).to_dict("records")
# do the postponed/forfeit rows exist on stats side, and how?
s_forf = stats[pd.to_numeric(stats["home_pts"], errors="coerce").eq(0) & pd.to_numeric(stats["away_pts"], errors="coerce").eq(0)]
R["stats_both_zero_rows"] = s_forf[["game_id", "season_file", "game_date", "home_team_abbreviation",
                                    "away_team_abbreviation", "home_wl", "away_wl"]].astype(str).to_dict("records")
# postponed 2023 makeup pairing: ESPN rows CON games around 2023-06-07/06-09
_e = espn[(espn["season_file"] == 2023) & (espn["date"].astype(str).str[:10].isin(["2023-06-07", "2023-06-08", "2023-06-09"]))]
R["postponed_2023_context"] = _e[["game_id", "date", "home_display_name", "away_display_name",
                                  "status_type_detail", "home_score", "away_score"]].astype(str).to_dict("records")

# ------------------------------------------------------------------ All-Star / special-team rows (extended detector)
ALLSTAR_ABBR = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE", "CLA", "COL", "SPO", "COOP", "WNBASTARS"}
alias_rows = espn[espn["home_abbreviation"].isin(ALLSTAR_ABBR) | espn["away_abbreviation"].isin(ALLSTAR_ABBR)]
R["espn_allstar_alias"] = {
    "rows": int(len(alias_rows)),
    "by_season": {int(k): int(v) for k, v in alias_rows.groupby("season_file").size().items()},
    "examples": [
        {"season": int(r["season_file"]), "game_id": str(r["game_id"]),
         "home": str(r["home_display_name"]), "away": str(r["away_display_name"]),
         "abbrs": f"{r['home_abbreviation']}/{r['away_abbreviation']}"}
        for _, r in alias_rows.iterrows()
    ],
}
# stats side: any row with those abbreviations?
s_alias = stats[stats["home_team_abbreviation"].isin(ALLSTAR_ABBR) | stats["away_team_abbreviation"].isin(ALLSTAR_ABBR)]
R["stats_allstar_alias_rows"] = int(len(s_alias))

# TBD placeholders
tbd_rows = espn[espn["home_display_name"].fillna("").str.upper().eq("TBD")
                | espn["away_display_name"].fillna("").str.upper().eq("TBD")]
R["espn_tbd_placeholder"] = {
    "rows": int(len(tbd_rows)),
    "by_season": {int(k): int(v) for k, v in tbd_rows.groupby("season_file").size().items()},
    "states": {str(k): int(v) for k, v in tbd_rows["status_type_state"].value_counts().items()},
    "distinct_dates": sorted(tbd_rows["date"].astype(str).unique().tolist()),
}

# neutral site
neutral = espn[espn["neutral_site"].astype(str).str.upper().isin(["TRUE", "1"])]
R["espn_neutral_site"] = {
    "rows": int(len(neutral)),
    "by_season": {int(k): int(v) for k, v in neutral.groupby("season_file").size().items()},
    "rows_in_allstar_alias": int((neutral["home_abbreviation"].isin(ALLSTAR_ABBR) | neutral["away_abbreviation"].isin(ALLSTAR_ABBR)).sum()),
    "non_allstar_examples": neutral.loc[~(neutral["home_abbreviation"].isin(ALLSTAR_ABBR) | neutral["away_abbreviation"].isin(ALLSTAR_ABBR)),
        ["season_file", "date", "home_display_name", "away_display_name", "notes_headline"]].astype(str).to_dict("records"),
}

# Commissioner's Cup
cup = espn[espn["notes_headline"].fillna("").str.contains("Cup", case=False)]
cup_champ = espn[espn["notes_headline"].fillna("").str.contains("Cup Championship", case=False)
                 | (espn["notes_headline"].fillna("").str.contains("Cup", case=False)
                    & espn["neutral_site"].astype(str).str.upper().isin(["TRUE", "1"]))]
R["espn_commissioners_cup"] = {
    "rows_headline_cup": int(len(cup)),
    "by_season": {int(k): int(v) for k, v in cup.groupby("season_file").size().items()},
    "rows_championship": int(len(cup_champ)),
    "championship_by_season": {int(k): int(v) for k, v in cup_champ.groupby("season_file").size().items()},
    "season_type_of_cup_rows": {str(k): int(v) for k, v in cup["season_type"].value_counts().items()},
    "championship_neutral_site_rows": int(cup_champ["neutral_site"].astype(str).str.upper().isin(["TRUE", "1"]).sum()),
}

# ------------------------------------------------------------------ canonical per-season census (filter law applied)
played = espn[espn["status_type_state"] == "post"].copy()
played = played[~played["status_type_detail"].fillna("").str.contains("Forfeit|Postponed", case=False)]
played = played[~played["home_abbreviation"].isin(ALLSTAR_ABBR) & ~played["away_abbreviation"].isin(ALLSTAR_ABBR)]
played_rs = played[played["season_type"] == 2]
played_po = played[played["season_type"] == 3]
cup_rs = played_rs[played_rs["notes_headline"].fillna("").str.contains("Cup", case=False)]

s_played = stats[~(pd.to_numeric(stats["home_pts"], errors="coerce").eq(0)
                   & pd.to_numeric(stats["away_pts"], errors="coerce").eq(0))].copy()
s_played = s_played[~s_played["home_team_abbreviation"].isin(ALLSTAR_ABBR) & ~s_played["away_team_abbreviation"].isin(ALLSTAR_ABBR)]
s_rs = s_played[s_played["season_type"] == "regular-season"]
s_po = s_played[s_played["season_type"] == "playoffs"]

census = {}
for y in sorted(set(espn["season_file"].unique()) | set(stats["season_file"].unique())):
    census[int(y)] = {
        "espn_rows_total": int((espn["season_file"] == y).sum()) if y in set(espn["season_file"].unique()) else None,
        "espn_played_real": int((played["season_file"] == y).sum()) if y in set(espn["season_file"].unique()) else None,
        "espn_played_rs_excl_cup": int(((played_rs["season_file"] == y) & (~played_rs["notes_headline"].fillna("").str.contains("Cup", case=False))).sum()) if y in set(espn["season_file"].unique()) else None,
        "espn_cup_rows_played": int((cup_rs["season_file"] == y).sum()) if y in set(espn["season_file"].unique()) else None,
        "espn_played_po": int((played_po["season_file"] == y).sum()) if y in set(espn["season_file"].unique()) else None,
        "stats_rows_total": int((stats["season_file"] == y).sum()) if y in set(stats["season_file"].unique()) else None,
        "stats_played_real": int((s_played["season_file"] == y).sum()) if y in set(stats["season_file"].unique()) else None,
        "stats_played_rs": int((s_rs["season_file"] == y).sum()) if y in set(stats["season_file"].unique()) else None,
        "stats_played_po": int((s_po["season_file"] == y).sum()) if y in set(stats["season_file"].unique()) else None,
    }
R["census_per_season"] = census
R["season_type_totals"] = {
    "espn": {str(k): int(v) for k, v in espn["season_type"].value_counts().items()},
    "stats_played": {str(k): int(v) for k, v in s_played["season_type"].value_counts().items()},
}
R["wubble_2020"] = {
    "espn_rows_total": int((espn["season_file"] == 2020).sum()),
    "espn_played_real": int((played["season_file"] == 2020).sum()),
    "stats_played_real": int((s_played["season_file"] == 2020).sum()),
}

# ------------------------------------------------------------------ franchise map from data + canonical team-key table
# franchise_key: stable modern/primary key; era rows give per-season stats abbr + ESPN display names.
FRANCHISE_MAP = {
    # franchise_key: {season -> (stats_abbr, [espn display names observed])} filled below
}
abbr = stats.groupby("season_file").apply(
    lambda d: {r["home_team_name"]: r["home_team_abbreviation"] for _, r in
               d.dropna(subset=["home_team_abbreviation"])[["home_team_name", "home_team_abbreviation"]].drop_duplicates().iterrows()},
    include_groups=False,
)
name_by_season = {}  # season -> {name: abbr}
for y, m in abbr.items():
    name_by_season[y] = dict(m)
# ESPN display names observed per season (played rows, real teams only)
esp_names = {}
for y in sorted(espn["season_file"].unique()):
    d = played[played["season_file"] == y]
    names = set(d["home_display_name"].dropna()) | set(d["away_display_name"].dropna())
    esp_names[int(y)] = sorted(n for n in names if not any(a in ALLSTAR_ABBR for a in []) and n.upper() not in {"TBD"})

FRANCHISE_OF_NAME = {
    "Utah Starzz": "SAN_DAL", "San Antonio Silver Stars": "SAN_DAL", "San Antonio Stars": "SAN_DAL", "Dallas Wings": "SAN_DAL",
    "Orlando Miracle": "CON", "Connecticut Sun": "CON",
    "Detroit Shock": "DET_TUL", "Tulsa Shock": "DET_TUL",
    "Los Angeles Sparks": "LAS", "Las Vegas Aces": "LVA",
    "Charlotte Sting": "CHA", "Cleveland Rockers": "CLE", "Houston Comets": "HOU", "Sacramento Monarchs": "SAC",
    "Miami Sol": "MIA", "Portland Fire": "POR_PDX", "Phoenix Mercury": "PHO", "New York Liberty": "NYL",
    "Minnesota Lynx": "MIN", "Seattle Storm": "SEA", "Washington Mystics": "WAS", "Indiana Fever": "IND",
    "Atlanta Dream": "ATL", "Chicago Sky": "CHI", "Golden State Valkyries": "GSV", "Toronto Tempo": "TOR",
}
FRANCHISE_KEY_OUT = {
    "SAN_DAL": "DAL", "DET_TUL": "DAL_MERGED", "POR_PDX": "POR", "LVA": "LVA", "PHO": "PHO",
}
# canonical table rows: franchise_key, stats_abbr, espn_abbrs_observed, espn_display_names, first_season, last_season
tk = {}
for y in sorted(name_by_season):
    for name, a in name_by_season[y].items():
        fk = FRANCHISE_OF_NAME.get(name, name)
        t = tk.setdefault(fk, {"franchise_key": fk, "names": set(), "stats_abbrs": set(), "espn_names": set(),
                               "espn_abbrs": set(), "first": y, "last": y, "seasons": set()})
        t["names"].add(name); t["stats_abbrs"].add(a); t["seasons"].add(y)
        t["first"] = min(t["first"], y); t["last"] = max(t["last"], y)
for y, d in esp_names.items():
    for name in d:
        fk = FRANCHISE_OF_NAME.get(name)
        if fk is None:
            continue
        y = int(y)
        t = tk.setdefault(fk, {"franchise_key": fk, "names": set(), "stats_abbrs": set(), "espn_names": set(),
                               "espn_abbrs": set(), "first": y, "last": y, "seasons": set()})
        t["espn_names"].add(name); t["seasons"].add(y)
        t["first"] = min(t["first"], y); t["last"] = max(t["last"], y)
# espn abbrs per franchise (from espn rows matched by display name)
for side in ("home", "away"):
    for name, a in espn.groupby(f"{side}_display_name")[f"{side}_abbreviation"].agg(lambda s: set(s.dropna())).items():
        fk = FRANCHISE_OF_NAME.get(name)
        if fk and fk in tk:
            tk[fk]["espn_abbrs"] |= set(a)
R["team_key_table"] = {
    fk: {
        "franchise_key": fk,
        "stats_display_names": sorted(t["names"]),
        "stats_abbrs": sorted(t["stats_abbrs"]),
        "espn_display_names": sorted(t["espn_names"]),
        "espn_abbrs_observed": sorted(t["espn_abbrs"]),
        "seasons_present": sorted(t["seasons"]),
        "first_season": int(t["first"]),
        "last_season": int(t["last"]),
    }
    for fk, t in sorted(tk.items())
}
R["team_key_table_rows"] = len(R["team_key_table"])

# per-season abbr continuity checks
R["stats_abbr_reuse_events"] = {
    "PHO_vs_PHX": {str(y): name_by_season.get(y, {}).get("Phoenix Mercury") for y in (2024, 2025, 2026)},
    "POR_vs_PDX": {str(y): name_by_season.get(y, {}).get("Portland Fire") for y in (2000, 2002, 2026)},
    "SAN_two_names": sorted(n for n, a in name_by_season[2010].items() if a == "SAN"),
}

# ------------------------------------------------------------------ timestamps: canonical tip_utc law
# flavor 1/2/3: ESPN schedule date == start_date == game_date_time (per-file ISO parse)
eq_rows, eq_ok = 0, 0
for y in range(2002, 2027):
    d = espn[espn["season_file"] == y]
    a = pd.to_datetime(d["date"], utc=True, format="ISO8601")
    b = pd.to_datetime(d["game_date_time"], utc=True, format="ISO8601")
    eq_rows += len(d); eq_ok += int((a == b).sum())
R["ts_espn_schedule_instant_equality_fixed"] = {"rows": eq_rows, "equal": eq_ok, "pct": round(eq_ok / eq_rows * 100, 2)}
R["ts_espn_schedule_date_format"] = {
    "example": str(espn["date"].iloc[0]),
    "Z_pct": round(float(espn["date"].astype(str).str.endswith("Z").mean() * 100), 2),
    "gdt_offset_2025": espn.loc[espn["season_file"] == 2025, "game_date_time"].astype(str).str[-5:].value_counts().to_dict(),
    "gdt_offset_2026": espn.loc[espn["season_file"] == 2026, "game_date_time"].astype(str).str[-5:].value_counts().to_dict(),
}
# DST sample: 2026 gdt carries -0400 for ALL venues (ET rendering, not venue-local) — verify by venue
e26 = espn[espn["season_file"] == 2026].copy()
e26["off"] = e26["game_date_time"].astype(str).str.extract(r"([+-]\d{4})$")
R["ts_2026_offset_by_venue_sample"] = {
    "distinct_offsets": sorted(set(e26["off"].dropna())),
    "vegas_home_rows_offset": e26.loc[e26["home_display_name"] == "Las Vegas Aces", "off"].value_counts().to_dict(),
    "phoenix_home_rows_offset": e26.loc[e26["home_display_name"] == "Phoenix Mercury", "off"].value_counts().to_dict(),
    "seattle_home_rows_offset": e26.loc[e26["home_display_name"] == "Seattle Storm", "off"].value_counts().to_dict(),
}
# box flavor re-verification (2025 sample): box instant == schedule instant; box game_date == ET date
tb = pd.read_csv(os.path.join(RAW, "espn_sample_2025", "team_box_2025.csv"), low_memory=False)
sch25 = espn.loc[espn["season_file"] == 2025, ["game_id", "date"]].copy()
sch25["game_id"] = sch25["game_id"].astype(str)
tb2 = tb[["game_id", "game_date", "game_date_time"]].drop_duplicates("game_id").copy()
tb2["game_id"] = tb2["game_id"].astype(str)
mg = tb2.merge(sch25, on="game_id")
u_sch = pd.to_datetime(mg["date"], utc=True, format="ISO8601")
u_box = pd.to_datetime(mg["game_date_time"], utc=True, format="ISO8601")
et_date = u_sch.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
R["ts_box_flavor_2025"] = {
    "box_gdt_offset_counts": tb["game_date_time"].astype(str).str[-5:].value_counts().to_dict(),
    "box_instant_eq_schedule_instant": int((u_box == u_sch).sum()), "rows": len(mg),
    "box_gdt_localdate_eq_etdate": round(float((pd.to_datetime(mg["game_date_time"]).dt.strftime("%Y-%m-%d") == et_date).mean() * 100), 2),
    "box_game_date_eq_et_date_pct": round(float((mg["game_date"].astype(str) == et_date).mean() * 100), 2),
    "box_game_date_eq_utc_date_pct": round(float((mg["game_date"].astype(str) == u_sch.dt.strftime("%Y-%m-%d")).mean() * 100), 2),
}
# pbp wallclock (UTC) first event vs tip
pbp = pd.read_csv(os.path.join(RAW, "espn_sample_2025", "play_by_play_2025.csv"), low_memory=False, usecols=["game_id", "wallclock"])
pbp["game_id"] = pbp["game_id"].astype(str)
fw = pbp.groupby("game_id")["wallclock"].min()
mg3 = sch25.merge(fw.rename("fw").reset_index(), on="game_id")
mins = (pd.to_datetime(mg3["fw"], utc=True, format="ISO8601")
        - pd.to_datetime(mg3["date"], utc=True, format="ISO8601")).dt.total_seconds() / 60
R["ts_pbp_wallclock"] = {
    "Z_pct": round(float(pbp["wallclock"].astype(str).str.endswith("Z").mean() * 100), 2),
    "first_event_minus_tip_minutes_median": round(float(mins.median()), 1),
    "first_event_minus_tip_minutes_p05": round(float(mins.quantile(0.05)), 1),
    "first_event_minus_tip_minutes_p95": round(float(mins.quantile(0.95)), 1),
}

# ------------------------------------------------------------------ canonical join + full reconciliation
# join law: ESPN real played rows <-> stats real rows on (normalized franchise name pair, ET date +/- 1 day window),
# pass 2 resolves back-to-back series ambiguity by exact (team-pair, score) — score ties are decisive within a pair.
def norm_name(s: str) -> str:
    return str(s).strip().lower()

e2 = played.copy()
e2["tip_utc"] = pd.to_datetime(e2["date"], utc=True, format="ISO8601")
e2["et_date"] = e2["tip_utc"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
e2["hn"] = e2["home_display_name"].map(norm_name)
e2["an"] = e2["away_display_name"].map(norm_name)

s2 = s_played.copy()
s2["hn"] = s2["home_team_name"].map(norm_name)
s2["an"] = s2["away_team_name"].map(norm_name)
s2["gid"] = s2["game_id"].astype(str)

stats_by_key = {}
for _, r in s2.iterrows():
    stats_by_key.setdefault((r["hn"], r["an"]), []).append(
        (r["game_date"], r["gid"], int(r["home_pts"]), int(r["away_pts"])))

match = {}
consumed = set()
join_ambiguous = []
for _, r in e2.iterrows():
    d0 = pd.Timestamp(r["et_date"])
    cands = []
    for off in (-1, 0, 1):
        want = str((d0 + pd.Timedelta(days=off)).date())
        cands += [(gid, off) for gd, gid, _, _ in stats_by_key.get((r["hn"], r["an"]), []) if gd == want and gid not in consumed]
    uniq = {g for g, _ in cands}
    if len(uniq) == 1:
        g = uniq.pop()
        match[str(r["game_id"])] = (g, [o for gg, o in cands if gg == g][0])
        consumed.add(g)
    elif len(uniq) > 1:
        join_ambiguous.append({"game_id": str(r["game_id"]), "et_date": r["et_date"], "candidates": sorted(uniq)})

score_matched = []
for _, r in e2.iterrows():
    if str(r["game_id"]) in match:
        continue
    cand = [(gd, gid) for gd, gid, hp, ap in stats_by_key.get((r["hn"], r["an"]), [])
            if gid not in consumed and hp == int(r["home_score"]) and ap == int(r["away_score"])]
    if len(cand) == 1:
        match[str(r["game_id"])] = (cand[0][1], "score")
        consumed.add(cand[0][1])
        score_matched.append({"game_id": str(r["game_id"]), "season": int(r["season_file"]), "et_date": r["et_date"],
                              "stats_game_id": cand[0][1], "stats_date": cand[0][0]})

et_off_counts = {0: 0, "score": 0, -1: 0, 1: 0}
for g, (gid, off) in match.items():
    et_off_counts[off if off in et_off_counts else off] = et_off_counts.get(off, 0) + 1

espn_unmatched = [
    {"game_id": str(r["game_id"]), "season": int(r["season_file"]), "et_date": r["et_date"],
     "home": str(r["home_display_name"]), "away": str(r["away_display_name"]),
     "score": f"{r['home_score']}-{r['away_score']}", "headline": str(r["notes_headline"])[:50]}
    for _, r in e2.iterrows() if str(r["game_id"]) not in match
]
stats_unmatched = s2[~s2["gid"].isin(consumed)]
R["recon_rowlevel"] = {
    "espn_real_rows": int(len(e2)),
    "matched_to_stats": len(match),
    "matched_by_unique_window": len(match) - len(score_matched),
    "matched_by_score_fallback": len(score_matched),
    "score_fallback_examples": score_matched,
    "join_window_ambiguous_pairs_resolved_by_score": len(join_ambiguous),
    "join_ambiguous_examples": join_ambiguous[:6],
    "et_date_window_offset_distribution_of_matches": {str(k): int(v) for k, v in et_off_counts.items()},
    "espn_unmatched": len(espn_unmatched),
    "espn_unmatched_rows": espn_unmatched,
    "stats_real_rows": int(len(s2)),
    "stats_unmatched": int(len(stats_unmatched)),
    "stats_unmatched_by_season": {int(k): int(v) for k, v in stats_unmatched.groupby("season_file").size().items()},
    "stats_unmatched_2002plus": stats_unmatched.loc[stats_unmatched["season_file"] >= 2002,
        ["game_id", "season_file", "game_date", "home_team_abbreviation", "away_team_abbreviation", "home_pts", "away_pts", "season_type"]].astype(str).to_dict("records"),
}
R["model_universe"] = {
    "espn_real_rows": int(len(e2)),
    "stats_real_rows": int(len(s2)),
    "stats_only_rows": int(len(stats_unmatched)),
    "espn_only_rows": len(espn_unmatched),
    "union_rows": int(len(e2) + len(stats_unmatched)),
}

# 2019 suspended game evidence
R["suspended_2019"] = {
    "espn_row": espn.loc[espn["game_id"].astype(str) == "401156333",
                         ["game_id", "date", "home_display_name", "away_display_name", "home_score", "away_score", "notes_headline"]].astype(str).to_dict("records"),
    "stats_row": stats.loc[stats["game_id"].astype(str) == "1021900079",
                           ["game_id", "game_date", "home_team_name", "away_team_name", "home_pts", "away_pts"]].astype(str).to_dict("records"),
}

# 2021 cup championship stats-side gap evidence
cup21 = espn[(espn["season_file"] == 2021) & (espn["notes_headline"].fillna("").str.contains("Cup Championship", case=False))]
R["cup_championship_stats_gap_2021"] = {
    "espn": cup21[["game_id", "date", "home_display_name", "away_display_name"]].astype(str).to_dict("records"),
    "stats_rows_that_window": stats.loc[(stats["season_file"] == 2021) & (stats["game_date"].astype(str) >= "2021-08-12")
                                        & (stats["game_date"].astype(str) <= "2021-08-14"),
                                        ["game_id", "game_date", "home_team_abbreviation", "away_team_abbreviation"]].astype(str).to_dict("records"),
}

# ------------------------------------------------------------------ 2025 sample (kept from attempt 1, re-verified quickly)
R["sample2025"] = {
    "team_box_rows": int(len(tb)),
    "team_box_unique_games": int(tb["game_id"].nunique()),
    "player_box_rows": int(pd.read_csv(os.path.join(RAW, "espn_sample_2025", "player_box_2025.csv"), low_memory=False, usecols=["game_id"]).shape[0]),
    "pbp_rows": int(len(pbp)),
    "pbp_unique_games": int(pbp["game_id"].nunique()),
    "sched_post_games_2025": int(((espn["season_file"] == 2025) & (espn["status_type_state"] == "post")).sum()),
}

with open(os.path.join(OUT, "measurements_a2.json"), "w") as f:
    json.dump(R, f, indent=1, default=str)

# canonical team-key CSV
rows = []
for fk, t in R["team_key_table"].items():
    rows.append({
        "franchise_key": fk,
        "stats_display_names": "; ".join(t["stats_display_names"]),
        "stats_abbrs": "; ".join(t["stats_abbrs"]),
        "espn_display_names": "; ".join(t["espn_display_names"]),
        "espn_abbrs_observed": "; ".join(t["espn_abbrs_observed"]),
        "first_season": t["first_season"],
        "last_season": t["last_season"],
    })
pd.DataFrame(rows).sort_values(["first_season", "franchise_key"]).to_csv(
    os.path.join(OUT, "team_key_table.csv"), index=False)

print(json.dumps({k: R[k] for k in [
    "espn_identity", "stats_identity", "espn_unplayed_law", "espn_forfeit", "espn_postponed",
    "ts_espn_schedule_instant_equality_fixed", "ts_espn_schedule_date_format",
    "ts_2026_offset_by_venue_sample", "ts_box_flavor_2025", "ts_pbp_wallclock",
    "recon_rowlevel", "suspended_2019", "cup_championship_stats_gap_2021",
    "team_key_table_rows", "wubble_2020", "season_type_totals"]}, indent=1, default=str))
print("WROTE", os.path.join(OUT, "measurements_a2.json"))
