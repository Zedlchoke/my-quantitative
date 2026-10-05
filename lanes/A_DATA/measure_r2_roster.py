#!/usr/bin/env python3
"""wbap-a-data-r2 — roster/lineup PIT measurement for W-H2 (WNBA-WINPROB-PREP-V1).

Measures, per season 2002-2026 (ESPN side only — rosters/box are ESPN-keyed):
  1. per-season game_rosters coverage vs the Lane A filter-law game universe
  2. game linkage (game_id keys, date columns present?)
  3. rows-per-game / starters-per-game distributions
  4. team-season opening-roster (game-1) availability — W-H2 v1 input
  5. player_box minutes coverage per team-season — W-H2 prior-season input
  6. computable-continuity fraction per season T (2003-2026)
  7. retro-fill / data-quality hazards (duplicates, starter!=5 games,
     roster-only athletes with zero player_box rows all season)
  8. 2025 roster-vs-player_box starter agreement (all games, dispatch >= 20)

Schema/coverage counting ONLY — no win-prob metrics, no outcome modeling.
Read-only over ~/.my-quantitative-data/wnba-v1/raw/ (EXTEND-ONLY corpus) and the
digest-verified downloads in ~/.my-quantitative-data/wnba-prep-v1/roster_audit/.
Writes roster_audit/measurements_r2.json. WNBA data only — no NBA input anywhere.
"""
import json
import os
from collections import Counter
from pathlib import Path

import pandas as pd

RAW = Path.home() / ".my-quantitative-data" / "wnba-v1" / "raw"
AUD = Path.home() / ".my-quantitative-data" / "wnba-prep-v1" / "roster_audit"
OUT_JSON = AUD / "measurements_r2.json"

SEASONS = list(range(2002, 2027))
ALLSTAR_ABBR = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE", "CLA",
                "COL", "SPO", "COOP", "WNBASTARS"}
FRANCHISE_OF_NAME = {
    "Utah Starzz": "LVA", "San Antonio Silver Stars": "LVA", "San Antonio Stars": "LVA",
    "Las Vegas Aces": "LVA", "Orlando Miracle": "CON", "Connecticut Sun": "CON",
    "Detroit Shock": "DAL", "Tulsa Shock": "DAL", "Dallas Wings": "DAL",
    "Los Angeles Sparks": "LAS", "Charlotte Sting": "CHA", "Cleveland Rockers": "CLE",
    "Houston Comets": "HOU", "Sacramento Monarchs": "SAC", "Miami Sol": "MIA",
    "Portland Fire": "POR_PDX", "Phoenix Mercury": "PHO", "New York Liberty": "NYL",
    "Minnesota Lynx": "MIN", "Seattle Storm": "SEA", "Washington Mystics": "WAS",
    "Indiana Fever": "IND", "Atlanta Dream": "ATL", "Chicago Sky": "CHI",
    "Golden State Valkyries": "GSV", "Toronto Tempo": "TOR",
}

R = {"law_note": "schema/coverage counting only; WNBA-only evidence"}


def as_int_dict(s):
    return {str(k): int(v) for k, v in s.items()}


# ------------------------------------------------------------------ 1. schedule universe (Lane A filter law)
espn_rows = []
for y in SEASONS:
    d = pd.read_csv(RAW / "espn_schedules" / f"wnba_schedule_{y}.csv", low_memory=False)
    d["season_file"] = y
    espn_rows.append(d)
espn = pd.concat(espn_rows, ignore_index=True)
espn["game_id_str"] = espn["game_id"].astype(str)

played = espn[espn["status_type_state"] == "post"].copy()
played = played[~played["status_type_detail"].fillna("").str.contains("Forfeit|Postponed", case=False)]
played = played[~played["home_abbreviation"].isin(ALLSTAR_ABBR) & ~played["away_abbreviation"].isin(ALLSTAR_ABBR)]
played["tip_utc"] = pd.to_datetime(played["date"], utc=True, format="ISO8601")
played["franchise_home"] = played["home_display_name"].map(FRANCHISE_OF_NAME)
played["franchise_away"] = played["away_display_name"].map(FRANCHISE_OF_NAME)
assert played["franchise_home"].notna().all() and played["franchise_away"].notna().all(), "unmapped display name in universe"

universe = played[["game_id_str", "season_file", "tip_utc", "season_type"]].rename(columns={"season_file": "season"})
universe_by_season = {y: set(g["game_id_str"]) for y, g in universe.groupby("season")}
all_espn_ids = set(espn["game_id_str"])

# team game ordinals within each franchise-season (ordered by tip_utc, both home/away rows)
ord_rows = []
for _, r in played.sort_values("tip_utc").iterrows():
    ord_rows.append((r["season_file"], r["franchise_home"], r["game_id_str"]))
    ord_rows.append((r["season_file"], r["franchise_away"], r["game_id_str"]))
team_games = pd.DataFrame(ord_rows, columns=["season", "franchise", "game_id_str"]).drop_duplicates(
    ["season", "franchise", "game_id_str"])
team_games["game_ordinal"] = team_games.groupby(["season", "franchise"]).cumcount() + 1
first_game = team_games[team_games["game_ordinal"] == 1][["season", "franchise", "game_id_str"]]
n_team_seasons = {y: int(g["franchise"].nunique()) for y, g in team_games.groupby("season")}

R["universe"] = {
    "espn_schedule_rows": int(len(espn)),
    "filter_law_universe_rows": int(len(universe)),
    "team_seasons_per_season": as_int_dict(pd.Series(n_team_seasons)),
    "franchise_season_pairs": int(team_games[["season", "franchise"]].drop_duplicates().shape[0]),
}

# ------------------------------------------------------------------ 2. load roster + box files
def boolify(s: pd.Series) -> pd.Series:
    return s.astype(str).str.upper().isin(["TRUE", "1"])


ASG_UPPER = {"WEST", "EAST", "ALL", "USA", "DEL", "PAR", "WIL", "STE", "CLA", "COL", "SPO",
             "COOP", "WNBASTARS", "TEAM USA", "TEAM WNBA"}


def roster_with_franchise(y: int) -> pd.DataFrame:
    rr = roster[y].copy()
    up = rr["team_display_name"].astype(str).str.strip().str.upper()
    asg = up.isin(ASG_UPPER) | up.str.startswith("TEAM ")
    rr = rr[~asg].copy()
    rr["franchise"] = rr["team_display_name"].map(FRANCHISE_OF_NAME)
    unmapped = rr.loc[rr["franchise"].isna(), "team_display_name"].unique().tolist()
    assert not unmapped, f"unmapped roster team for {y}: {unmapped}"
    rr.attrs["asg_rows_dropped"] = int(asg.sum())
    return rr


roster, box = {}, {}
schema_sets = {}
ESPN_ABBR_FRANCHISE_2002 = {  # 2002 box uses old short schema; abbr map incl. the TUL=Detroit artifact
    "CHA": "CHA", "CLE": "CLE", "IND": "IND", "LOS": "LAS", "MIA": "MIA", "MIN": "MIN",
    "NYL": "NYL", "ORL": "CON", "PHO": "PHO", "POR": "POR_PDX", "SAC": "SAC",
    "SEA": "SEA", "TUL": "DAL", "UTH": "LVA"}
for y in SEASONS:
    rr = pd.read_csv(AUD / f"game_rosters_{y}.csv", low_memory=False)
    rr["game_id_str"] = rr["game_id"].astype(str)
    roster[y] = rr
    schema_sets[y] = set(rr.columns)
    bb = pd.read_csv(AUD / f"player_box_{y}.csv", low_memory=False,
                     usecols=lambda c: c in {"game_id", "season", "season_type", "game_date", "athlete_id",
                                             "athlete_display_name", "team_id", "team_abbreviation",
                                             "team_display_name", "starter", "did_not_play", "active",
                                             "reason", "minutes", "min", "home_away"})
    if "minutes" not in bb.columns and "min" in bb.columns:
        bb = bb.rename(columns={"min": "minutes"})
    bb["game_id_str"] = bb["game_id"].astype(str)
    box[y] = bb
R["schema"] = {
    "roster_columns_2002": sorted(schema_sets[2002]),
    "roster_columns_2026": sorted(schema_sets[2026]),
    "roster_schema_identical_2002_2026": all(s == schema_sets[2002] for s in schema_sets.values()),
    "roster_schema_variants": {str(y): sorted(s) for y, s in schema_sets.items()
                               if s != schema_sets[min(schema_sets)]} or "none",
    "roster_has_date_column": bool(any("date" in " ".join(s).lower() and "headshot" not in " ".join(s)
                                       for s in schema_sets.values())),
    "roster_has_game_id_column": all("game_id" in s for s in schema_sets.values()),
}

# ------------------------------------------------------------------ 3. per-season roster coverage vs universe
per_season = {}
universe_coverage_rows = []
for y in SEASONS:
    rr = roster_with_franchise(y)
    gids = set(rr["game_id_str"])
    uni = universe_by_season[y]
    cov = len(gids & uni)
    per_season[y] = {
        "roster_rows": int(len(rr)),
        "roster_unique_games": len(gids),
        "universe_games": len(uni),
        "universe_games_with_roster": cov,
        "universe_games_missing_roster": len(uni - gids),
        "roster_games_not_in_universe": len(gids - uni),
        "roster_games_not_in_any_schedule": len(gids - all_espn_ids),
        "teams_present": int(rr["franchise"].nunique()),
        "unique_athletes": int(rr["athlete_id"].nunique()),
        "dup_game_team_athlete_rows": int(rr.duplicated(["game_id_str", "team_abbreviation", "athlete_id"]).sum()),
        "starter_true_rows": int(boolify(rr["starter"]).sum()),
        "dnp_true_rows": int(boolify(rr["did_not_play"]).sum()),
        "active_true_rows": int(boolify(rr["active"]).sum()),
        "reason_nonnull_rows": int(rr["reason"].notna().sum()),
        "ejected_true_rows": int(boolify(rr["ejected"]).sum()),
    }
    missing = sorted(uni - gids)
    extra = sorted((gids - uni))[:12]
    if missing or (gids - uni):
        universe_coverage_rows.append({
            "season": y, "missing_universe_games": missing[:12], "n_missing": len(missing),
            "roster_only_games_sample": extra, "n_roster_only": len(gids - uni)})

    # per-game distributions
    pg = rr.groupby("game_id_str").size()
    st = rr[boolify(rr["starter"])].groupby("game_id_str").size()
    no_starter_games = sorted(set(pg.index) - set(st.index))
    bad_starter_games = {g: int(c) for g, c in st[st != 10].items()}
    per_season[y].update({
        "rows_per_game_median": float(pg.median()),
        "rows_per_game_p05": float(pg.quantile(0.05)),
        "rows_per_game_p95": float(pg.quantile(0.95)),
        "games_with_roster_rows": int(len(pg)),
        "starters_per_game_median": float(st.median()) if len(st) else None,
        "games_with_exactly_10_starters": int((st == 10).sum()) if len(st) else 0,
        "games_with_not_10_starters": int((st != 10).sum()) if len(st) else None,
        "games_with_zero_starter_rows": no_starter_games,
        "games_with_starters_ne_10_counts": bad_starter_games,
        "starters_per_game_distribution": as_int_dict(st.value_counts()) if len(st) else {},
    })

    # roster team_abbreviation artifacts (ESPN DET/TUL alias law)
    if y <= 2009:
        det_rows = int((rr.loc[rr["team_display_name"] == "Detroit Shock", "team_abbreviation"] == "TUL").sum())
        det_total = int((rr["team_display_name"] == "Detroit Shock").sum())
        per_season[y]["detroit_rows_labeled_TUL"] = f"{det_rows}/{det_total}"

R["per_season_roster"] = per_season
R["universe_coverage_exceptions"] = universe_coverage_rows

# what non-universe games DO have rosters? (ASG / postponed / forfeit / pre?)
extras = []
for y in SEASONS:
    gids = set(roster[y]["game_id_str"]) - universe_by_season[y]
    if gids:
        rows = espn[espn["game_id_str"].isin(gids)]
        extras.append({str(y): rows[["game_id_str", "date", "status_type_state", "status_type_detail",
                                     "home_display_name", "away_display_name", "home_abbreviation",
                                     "away_abbreviation"]].astype(str).to_dict("records")})
R["roster_nonuniverse_games"] = extras

# ------------------------------------------------------------------ 4. opening-roster (game-1) availability — W-H2 v1 input
open_rows = []
for y in SEASONS:
    rr = roster[y]
    f1 = first_game[first_game["season"] == y]
    covered = set(rr["game_id_str"])
    have = f1["game_id_str"].isin(covered)
    # quality of the game-1 roster: starters at that game for the two teams
    n_open_starters = []
    g1_ids = set(f1.loc[have, "game_id_str"])
    if g1_ids:
        sub = rr[rr["game_id_str"].isin(g1_ids)]
        st = sub[boolify(sub["starter"])].groupby("game_id_str").size()
        n_open_starters = st.tolist()
    open_rows.append({
        "season": y,
        "team_seasons": len(f1),
        "game1_covered": int(have.sum()),
        "game1_covered_pct": round(have.mean() * 100, 1) if len(f1) else None,
        "game1_rows_min": int(min(n_open_starters)) if n_open_starters else None,
        "game1_starters_eq_10": int(sum(1 for s in n_open_starters if s == 10)),
    })
R["opening_roster_game1"] = open_rows

# ------------------------------------------------------------------ 5. player_box coverage + 6. computable continuity
def box_with_franchise(y: int) -> pd.DataFrame:
    bb = box[y].copy()
    if "team_display_name" in bb.columns:
        bb["franchise"] = bb["team_display_name"].map(FRANCHISE_OF_NAME)
        up = bb["team_display_name"].astype(str).str.strip().str.upper()
        asg_mask = up.isin({"WEST", "EAST", "ALL", "USA", "DEL", "PAR", "WIL", "STE", "CLA",
                            "COL", "SPO", "COOP", "WNBASTARS", "TEAM USA", "TEAM WNBA"}) | up.str.startswith("TEAM ")
        n_asg = int(asg_mask.sum())
        bb = bb[~asg_mask].copy()
        unmapped = bb.loc[bb["franchise"].isna(), "team_display_name"].unique().tolist()
    else:  # 2002 old schema: map via ESPN abbreviation (incl. TUL=Detroit artifact)
        bb["franchise"] = bb["team_abbreviation"].map(ESPN_ABBR_FRANCHISE_2002)
        asg_mask = bb["team_abbreviation"].isin(["EAST", "WEST", "ALL", "USA"])
        n_asg = int(asg_mask.sum())
        bb = bb[~asg_mask].copy()
        unmapped = bb.loc[bb["franchise"].isna(), "team_abbreviation"].unique().tolist()
    assert not unmapped, f"unmapped box team for {y}: {unmapped}"
    bb.attrs["asg_rows_dropped"] = n_asg
    return bb


box_per_season = {}
for y in SEASONS:
    bb = box[y]
    gids = set(bb["game_id_str"])
    uni = universe_by_season[y]
    mins = pd.to_numeric(bb["minutes"], errors="coerce")
    box_per_season[y] = {
        "box_rows": int(len(bb)),
        "box_unique_games": len(gids),
        "universe_games_with_box": len(gids & uni),
        "universe_games_missing_box": len(uni - gids),
        "rows_with_minutes_gt0": int((mins > 0).sum()),
        "rows_minutes_null": int(mins.isna().sum()),
        "dnp_true_rows": int(boolify(bb["did_not_play"]).sum()),
    }
R["per_season_player_box"] = box_per_season

# franchise presence per season from the universe (schedule truth)
franchise_by_season = {y: set(g["franchise"]) for y, g in team_games.groupby("season")}
# box coverage per (season, franchise): games with box rows / franchise universe games
tg_count = team_games.groupby(["season", "franchise"])["game_id_str"].nunique()
box_ratio = {}
box_games_ff = {}
for y in SEASONS:
    bb = box_with_franchise(y)
    bg = bb.groupby("franchise")["game_id_str"].nunique()
    box_games_ff[y] = bg.to_dict()
    ratios = {}
    for (s, f), n in tg_count.items():
        if int(s) != y:
            continue
        cov = int(bg.get(f, 0))
        ratios[f] = round(cov / int(n), 4) if n else None
    box_ratio[y] = ratios

continuity = []
for T in range(2003, 2027):
    f1T = first_game[first_game["season"] == T]
    coveredT = set(roster[T]["game_id_str"])
    open_ok = set(f1T.loc[f1T["game_id_str"].isin(coveredT), "franchise"])
    teamsT = franchise_by_season[T]
    teamsTm1 = franchise_by_season.get(T - 1, set())
    nonexp = teamsT - (teamsT - teamsTm1)
    ratios = box_ratio[T - 1]
    min_ok_08 = {t for t in nonexp if ratios.get(t, 0) is not None and ratios.get(t, 0) >= 0.8}
    min_ok_10 = {t for t in nonexp if ratios.get(t, 0) == 1.0}
    roster_ok = {t for t in nonexp if t in open_ok}
    expansion = teamsT - teamsTm1
    continuity.append({
        "season": T,
        "team_seasons": len(teamsT),
        "expansion_franchises": sorted(expansion),
        "roster_gate_ok": len(roster_ok),
        "roster_gate_pct": round(len(roster_ok) / len(nonexp) * 100, 1) if nonexp else None,
        "prior_box_ratio_min": min((ratios.get(t, 0) or 0) for t in nonexp) if nonexp else None,
        "prior_box_teams_ratio_ge_08": len(min_ok_08),
        "prior_box_teams_ratio_eq_10": len(min_ok_10),
        "computable_minutes_weighted_ge08": len(roster_ok & min_ok_08),
        "computable_minutes_pct_ge08": round(len(roster_ok & min_ok_08) / len(nonexp) * 100, 1) if nonexp else None,
        "computable_minutes_weighted_eq10": len(roster_ok & min_ok_10),
        "roster_only_continuity_pct": round(len(roster_ok) / len(nonexp) * 100, 1) if nonexp else None,
        "teams_missing_minutes_ge08": sorted(nonexp - min_ok_08),
        "prior_box_ratio_by_team": {t: ratios.get(t) for t in sorted(nonexp)},
    })
R["computable_continuity_per_season"] = continuity

# W-H2 gate: >= ~90% of team-seasons 2003+ (B lane gate) — measured on the roster gate
tt = [c for c in continuity if 2003 <= c["season"] <= 2025]
R["gate_90pct_2003_2025"] = {
    "seasons_meeting_90pct_rostergate": sum(1 for c in tt if c["roster_gate_pct"] is not None and c["roster_gate_pct"] >= 90.0),
    "seasons_total": len(tt),
    "seasons_below_90_rostergate": [{"season": c["season"], "pct": c["roster_gate_pct"]}
                                    for c in tt if c["roster_gate_pct"] is None or c["roster_gate_pct"] < 90.0],
    "seasons_meeting_90pct_minutes_ge08": sum(1 for c in tt if c["computable_minutes_pct_ge08"] is not None and c["computable_minutes_pct_ge08"] >= 90.0),
}

# ------------------------------------------------------------------ 7. retro-fill / quality hazards
hazards = {}
# (a) roster rows whose athlete has NO player_box row for that team-season at all
roster_only_examples = []
for y in SEASONS:
    rr = roster_with_franchise(y)
    bb = box_with_franchise(y)
    box_pairs = set(zip(bb["game_id_str"], bb["athlete_id"]))
    in_season = set(zip(bb["franchise"], bb["athlete_id"]))
    mask_season = pd.Series([p not in in_season for p in zip(rr["franchise"], rr["athlete_id"])], index=rr.index)
    n_no_season_row = int(mask_season.sum())
    starters_among = int(boolify(rr.loc[mask_season, "starter"]).sum()) if n_no_season_row else 0
    hazards[f"roster_rows_no_box_row_same_team_season_{y}"] = {
        "rows": n_no_season_row, "of_which_starter": starters_among}
    if n_no_season_row and len(roster_only_examples) < 40 and starters_among:
        ex = rr.loc[mask_season & boolify(rr["starter"]),
                    ["season", "game_id_str", "team_display_name", "athlete_display_name", "starter", "did_not_play"]].copy()
        ex["season"] = y
        roster_only_examples += ex.head(4).astype(str).to_dict("records")
R["roster_rows_no_box_row_same_team_season"] = hazards
R["retrofill_roster_rows_without_any_box_row_examples"] = roster_only_examples

# (b) player first-appearance order: roster first game ordinal vs box first appearance
first_gap_summary = []
for y in SEASONS:
    rr = roster_with_franchise(y)
    bb = box_with_franchise(y)
    r_first = rr.dropna(subset=["franchise"]).groupby(["franchise", "athlete_id"])["game_id_str"].min()
    mins = pd.to_numeric(bb["minutes"], errors="coerce")
    bbm = bb[mins > 0]
    b_first = bbm.dropna(subset=["franchise"]).groupby(["franchise", "athlete_id"])["game_id_str"].min()
    # ordinal lookup per (season, franchise): game -> ordinal
    tg = team_games[team_games["season"] == y]
    ord_lookup = {(f, g): o for f, g, o in zip(tg["franchise"], tg["game_id_str"], tg["game_ordinal"])}
    both = r_first.index.intersection(b_first.index)
    gaps = []
    for k in both:
        ro = ord_lookup.get((k[0], r_first[k]))
        bo = ord_lookup.get((k[0], b_first[k]))
        if ro is not None and bo is not None:
            gaps.append(ro - bo)
    gs = pd.Series(gaps)
    first_gap_summary.append({
        "season": y,
        "players_in_both": len(both),
        "roster_first_le_box_first_pct": round(float((gs >= 0).mean() * 100), 2) if len(gs) else None,
        "roster_first_minus_box_first_median": float(gs.median()) if len(gs) else None,
        "roster_first_earlier_by_gt10_games": int((gs > 10).sum()) if len(gs) else None,
    })
R["first_appearance_gap"] = first_gap_summary

# (c) roster files for games that were NOT played (postponed/forfeit/pre) — counted in section 3
# (d) duplicates league-wide
dup_total = sum(per_season[y]["dup_game_team_athlete_rows"] for y in SEASONS)
R["duplicate_game_team_athlete_rows_total"] = dup_total

# ------------------------------------------------------------------ 8. 2025 starter cross-check (roster vs player_box)
rr25 = roster_with_franchise(2025)
bb25 = box_with_franchise(2025)
rr25["st"] = boolify(rr25["starter"])
bb25["st"] = boolify(bb25["starter"])
games = sorted(set(rr25["game_id_str"]) & set(bb25["game_id_str"]))
cross = {"games_checked": len(games), "rows_compared": 0, "row_flag_agree": 0,
         "team_games_both_5": 0, "team_games_sets_equal": 0, "disagreement_examples": []}
for g in games:
    r_g = rr25[rr25["game_id_str"] == g]
    b_g = bb25[bb25["game_id_str"] == g]
    m = r_g.merge(b_g[["game_id_str", "team_abbreviation", "athlete_id", "st"]].rename(columns={"st": "st_box"}),
                  on=["game_id_str", "team_abbreviation", "athlete_id"], how="outer", indicator=True)
    both = m[m["_merge"] == "both"]
    cross["rows_compared"] += int(len(m))
    cross["row_flag_agree"] += int((both["st"] == both["st_box"]).sum())
    for ta in set(r_g["team_abbreviation"]):
        rs = set(r_g.loc[(r_g["team_abbreviation"] == ta) & r_g["st"], "athlete_id"])
        bs = set(b_g.loc[(b_g["team_abbreviation"] == ta) & b_g["st"], "athlete_id"])
        if len(rs) == 5 and len(bs) == 5:
            cross["team_games_both_5"] += 1
            if rs == bs:
                cross["team_games_sets_equal"] += 1
            elif len(cross["disagreement_examples"]) < 8:
                names_r = set(r_g.loc[(r_g["team_abbreviation"] == ta) & r_g["st"], "athlete_display_name"])
                names_b = set(b_g.loc[(b_g["team_abbreviation"] == ta) & b_g["st"], "athlete_display_name"])
                cross["disagreement_examples"].append({
                    "game_id": g, "team": ta,
                    "roster_only": sorted(names_r - names_b), "box_only": sorted(names_b - names_r)})
R["starter_crosscheck_2025"] = cross

# (e) spot-check the >10-game first-appearance gaps (retro-fill probe)
gap_detail = []
for y in SEASONS:
    rr = roster_with_franchise(y)
    bb = box_with_franchise(y)
    r_first = rr.groupby(["franchise", "athlete_id"])["game_id_str"].min()
    mins = pd.to_numeric(bb["minutes"], errors="coerce")
    b_first = bb[mins > 0].groupby(["franchise", "athlete_id"])["game_id_str"].min()
    tg = team_games[team_games["season"] == y]
    ord_lookup = {(f, g): o for f, g, o in zip(tg["franchise"], tg["game_id_str"], tg["game_ordinal"])}
    rnames = rr.drop_duplicates(["franchise", "athlete_id"]).set_index(["franchise", "athlete_id"])["athlete_display_name"]
    for k in r_first.index.intersection(b_first.index):
        ro = ord_lookup.get((k[0], r_first[k]))
        bo = ord_lookup.get((k[0], b_first[k]))
        if ro is not None and bo is not None and (ro - bo) > 10:
            gap_detail.append({"season": y, "franchise": k[0], "athlete_id": str(k[1]),
                               "athlete": str(rnames.get(k, "?")),
                               "roster_first_game_ordinal": int(ro), "box_first_game_ordinal": int(bo),
                               "gap_games": int(ro - bo)})
R["first_appearance_gap_gt10_detail"] = gap_detail

# (f) schedule detail of the universe games with NO roster rows
missing_ids = []
for y in SEASONS:
    gids = universe_by_season[y] - set(roster[y]["game_id_str"])
    for g in sorted(gids):
        row = espn[espn["game_id_str"] == g].iloc[0]
        missing_ids.append({"season": y, "game_id": g, "date": str(row["date"]),
                            "home": str(row["home_display_name"]), "away": str(row["away_display_name"]),
                            "score": f"{row['home_score']}-{row['away_score']}",
                            "season_type": str(row["season_type"]),
                            "headline": str(row["notes_headline"])[:60]})
R["universe_games_without_roster_detail"] = missing_ids

with open(OUT_JSON, "w") as f:
    json.dump(R, f, indent=1, default=str)
print("WROTE", OUT_JSON)
print(json.dumps({k: R[k] for k in ["universe", "schema", "gate_90pct_2003_2025",
                                    "duplicate_game_team_athlete_rows_total",
                                    "starter_crosscheck_2025"]}, indent=1, default=str)[:4000])
