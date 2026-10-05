#!/usr/bin/env python3
"""delta_reverify_r2.py — independent re-verification for wbap-d-verify-r2.

Fresh implementation (does NOT import or execute any lane script). Read-only over
~/.my-quantitative-data/wnba-v1/raw/ and ~/.my-quantitative-data/wnba-prep-v1/.
Schema/coverage counting ONLY — no win-prob metric, no Elo, no scored computation.
"""
import csv
import gzip
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

RAW = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw")
PREP = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1")
RA = os.path.join(PREP, "roster_audit")

ALIAS = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE",
         "CLA", "COL", "SPO", "COOP", "WNBASTARS"}
ET = ZoneInfo("America/New_York")

PASS, FAIL = "PASS", "FAIL"
results = {}


def check(name, ok, detail):
    results[name] = (PASS if ok else FAIL, detail)
    print(f"[{results[name][0]}] {name}: {detail}")


def parse_ts(s):
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def norm_name(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def is_true(v):
    return (v or "").strip().lower() == "true"


# ---------------------------------------------------------------- load corpus
espn = []
for y in range(2002, 2027):
    with open(os.path.join(RAW, "espn_schedules", f"wnba_schedule_{y}.csv"),
              newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            espn.append(row)

stats = []
for y in range(1997, 2027):
    with gzip.open(os.path.join(RAW, "wnba_stats_schedules", f"wnba_schedule_{y}.csv.gz"),
                   "rt", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stats.append(row)

# ------------------------------------------------- identity / census anchors
espn_ids = [r["id"] for r in espn]
stats_ids = [r["game_id"] for r in stats]
check("identity_espn", len(espn) == 6029 and len(set(espn_ids)) == 6029
      and len({r["season"] for r in espn}) == 25,
      f"ESPN rows={len(espn)} unique={len(set(espn_ids))} seasons={len({r['season'] for r in espn})}")
check("identity_stats", len(stats) == 7009 and len(set(stats_ids)) == 7009
      and len({r["season"] for r in stats}) == 30,
      f"stats rows={len(stats)} unique={len(set(stats_ids))} seasons={len({r['season'] for r in stats})}")

shape_ok = all(r["game_id"].startswith("10") and len(r["game_id"]) == 10
               and r["game_id"][3:5] == r["season"][2:4] for r in stats)
td_map = defaultdict(Counter)
for r in stats:
    td_map[r["season_type"]][r["game_id"][2]] += 1
crosstab_ok = set(td_map["regular-season"]) == {"2"} and set(td_map["playoffs"]) == {"4"}
check("stats_id_shape", shape_ok and crosstab_ok,
      f"prefix10/len10/YY ok={shape_ok}; type-digit crosstab reg->2 / po->4 ok={crosstab_ok}")

# ------------------------------------------------------------ filter law ESPN
non_post = [r for r in espn if r["status_type_state"] != "post"]
forfeit = [r for r in espn if r["status_type_detail"] == "Forfeit"]
postponed = [r for r in espn if r["status_type_detail"] == "Postponed"]
alias_rows = [r for r in espn if r["home_abbreviation"] in ALIAS
              or r["away_abbreviation"] in ALIAS]
tbd = [r for r in espn if r["status_type_state"] != "post"
       and "TBD" in (r["home_display_name"] + r["away_display_name"]
                     + r["home_abbreviation"] + r["away_abbreviation"] + r["notes_headline"])]
null_scores = [r for r in espn if r["home_score"] == "" or r["away_score"] == ""]

check("filter_nonpost", len(non_post) == 17 and all(r["season"] == "2026" for r in non_post)
      and len(null_scores) == 0,
      f"non-post rows={len(non_post)} (all 2026={all(r['season'] == '2026' for r in non_post)}), "
      f"null-score rows={len(null_scores)}")
check("filter_forfeit", len(forfeit) == 1 and forfeit[0]["id"] == "401018942",
      f"forfeit rows={len(forfeit)} id={forfeit[0]['id'] if forfeit else None}")
check("filter_postponed", len(postponed) == 2
      and {r["id"] for r in postponed} == {"401507167", "401857072"},
      f"postponed rows={len(postponed)} ids={sorted(r['id'] for r in postponed)}")
check("filter_tbd", len(tbd) == 7, f"TBD placeholder rows={len(tbd)}")

zero0 = [r for r in espn if r["home_score"] == "0" and r["away_score"] == "0"
         and r["status_type_state"] == "post"]
check("filter_espn_zero0_post", len(zero0) == 3
      and {r["id"] for r in zero0} == {"401018942", "401507167", "401857072"},
      f"post 0-0 rows={len(zero0)} = exactly the Forfeit + 2 Postponed rows "
      f"{sorted(r['id'] for r in zero0)}")

s00 = [r for r in stats if r["home_pts"] == "0" and r["away_pts"] == "0"]
snull = [r for r in stats if r["home_pts"] == "" or r["away_pts"] == ""]
check("filter_stats_00", len(s00) == 1 and s00[0]["game_id"] == "1021800162"
      and s00[0]["home_wl"] == "" and len(snull) == 0,
      f"stats 0-0 rows={len(s00)} (id={s00[0]['game_id'] if s00 else None}), null-pts={len(snull)}")

# Check 1: alias rows, per-token counts, stats-side 0
tagged = sum(1 for r in alias_rows
             if r["notes_headline"] == "" or "star" in r["notes_headline"].lower())
check("alias_rows_21", len(alias_rows) == 21 and tagged == 21,
      f"alias rows={len(alias_rows)}; headline empty-or-*star*-tagged={tagged}")

per_token = Counter()
for r in alias_rows:
    for ab in (r["home_abbreviation"], r["away_abbreviation"]):
        if ab in ALIAS:
            per_token[ab] += 1
expected_tokens = {"EAST": 11, "WEST": 11, "USA": 4, "WIL": 3, "ALL": 3, "STE": 2,
                   "DEL": 2, "PAR": 1, "COL": 1, "CLA": 1, "SPO": 1, "COOP": 1,
                   "WNBASTARS": 1}
check("alias_13_tokens", dict(per_token) == expected_tokens,
      f"tokens={len(per_token)}/13; per-token={dict(sorted(per_token.items()))}")
alias_seasons = sorted({r["season"] for r in alias_rows})
oly = {"2008", "2012", "2016", "2020"}
check("alias_seasons", len(alias_seasons) == 21 and not (oly & set(alias_seasons))
      and len(alias_rows) == len(alias_seasons),
      f"alias seasons={len(alias_seasons)} (one row each; Olympic years absent="
      f"{not (oly & set(alias_seasons))})")
stats_alias = [r for r in stats if r["home_team_abbreviation"] in ALIAS
               or r["away_team_abbreviation"] in ALIAS]
check("stats_alias_0", len(stats_alias) == 0, f"stats-side alias rows={len(stats_alias)}")

# Check 1: neutral-site rows (flag casing varies by season file — case-insensitive)
alias_ids = {id(r) for r in alias_rows}
neutral = [r for r in espn if is_true(r["neutral_site"])]
neutral_real = [r for r in neutral if id(r) not in alias_ids]
check("neutral_rows_16", len(neutral) == 16 and len(neutral_real) == 6,
      f"neutral rows={len(neutral)} = {len(neutral)-len(neutral_real)} alias + {len(neutral_real)} real: "
      + "; ".join(f"{r['game_date'][:10]} {r['away_display_name']}@{r['home_display_name']}"
                  for r in sorted(neutral_real, key=lambda r: r["date"])))

# Cup rows / finals (headline-based detector; 'Cup' rows must all be season_type 2, 2021-2026)
cup = [r for r in espn if "Cup" in r["notes_headline"]]
cup_by_season = Counter(r["season"] for r in cup)
finals = [r for r in cup if "Championship" in r["notes_headline"]]
fin2021 = [r for r in cup if r["season"] == "2021" and is_true(r["neutral_site"])]
check("cup_rows_301_finals_6", len(cup) == 301
      and all(r["season_type"] == "2" for r in cup)
      and set(cup_by_season) == {"2021", "2022", "2023", "2024", "2025", "2026"}
      and len(finals) == 5 and len(fin2021) == 1,
      f"Cup rows={len(cup)} all season_type2={all(r['season_type'] == '2' for r in cup)} "
      f"per-season={dict(sorted(cup_by_season.items()))}; finals={len(finals) + len(fin2021)} "
      f"(5 Championship-headline + 1 neutral 2021)")

# ESPN real universe
tbd_ids = {id(r) for r in tbd}
univ = [r for r in espn if r["status_type_state"] == "post"
        and r["status_type_detail"] not in ("Forfeit", "Postponed")
        and id(r) not in alias_ids and id(r) not in tbd_ids]
n2 = sum(1 for r in univ if r["season_type"] == "2")
po = sum(1 for r in univ if r["season_type"] == "3")
rs_excl_cup = n2 - len(cup)
check("universe_5988", len(univ) == 5988 and rs_excl_cup == 5230 and len(cup) == 301
      and po == 457 and len(univ) == rs_excl_cup + len(cup) + po,
      f"universe={len(univ)} = {rs_excl_cup} RS-excl-Cup + {len(cup)} Cup + {po} PO "
      f"(season_type2 rows={n2} incl. Cup)")

stats_real = [r for r in stats if not (r["home_pts"] == "0" and r["away_pts"] == "0")]
srs = sum(1 for r in stats_real if r["season_type"] == "regular-season")
spo = sum(1 for r in stats_real if r["season_type"] == "playoffs")
check("stats_real_7008", len(stats_real) == 7008 and srs == 6493 and spo == 515,
      f"stats real={len(stats_real)} = {srs} RS + {spo} PO")
check("stats_pre2002_1022", sum(1 for r in stats_real if int(r["season"]) <= 2001) == 1022,
      f"stats real pre-2002={sum(1 for r in stats_real if int(r['season']) <= 2001)}")

# ------------------------------------------------------- timestamp laws (ESPN)
ts_gdt = ts_sd = 0
for r in espn:
    try:
        d, g, s = parse_ts(r["date"]), parse_ts(r["game_date_time"]), parse_ts(r["start_date"])
    except Exception:
        continue
    ts_gdt += (d == g)
    ts_sd += (d == s)
check("ts_espn_schedule", ts_gdt == 6029 and ts_sd == 6029,
      f"date==game_date_time {ts_gdt}/6029; date==start_date {ts_sd}/6029")
spot = next(r for r in espn if r["id"] == "401857072")
check("ts_spot_401857072", parse_ts(spot["date"]) == parse_ts(spot["game_date_time"]),
      f"date={spot['date']} == game_date_time={spot['game_date_time']} (same instant="
      f"{parse_ts(spot['date']) == parse_ts(spot['game_date_time'])})")

# ------------------------------------------------- cross-source union (join)
def et_date(r):
    return parse_ts(r["game_date_time"]).astimezone(ET).date()


skey = defaultdict(list)
for r in stats_real:
    k = tuple(sorted([norm_name(r["home_team_name"]), norm_name(r["away_team_name"])]))
    skey[k].append((datetime.strptime(r["game_date"], "%Y-%m-%d").date(), r))


def ekey(r):
    return tuple(sorted([norm_name(r["home_display_name"]), norm_name(r["away_display_name"])]))


unmatched = {id(r): r for r in stats_real}
matched = window0 = scorefb = grpfb = espn_only = 0
unmatched_espn = []
for r in univ:
    k = ekey(r)
    et = et_date(r)
    cands = [sr for sr in skey.get(k, [])
             if id(sr[1]) in unmatched and abs((sr[0] - et).days) <= 1]
    if len(cands) == 1:
        del unmatched[id(cands[0][1])]
        matched += 1
        window0 += (cands[0][0] == et)
        continue
    cands2 = [sr for sr in skey.get(k, []) if id(sr[1]) in unmatched
              and sr[1]["home_pts"] == r["home_score"] and sr[1]["away_pts"] == r["away_score"]]
    if len(cands2) == 1:
        del unmatched[id(cands2[0][1])]
        matched += 1
        scorefb += 1
    else:
        unmatched_espn.append(r)
# pass 3: identical (name-pair, score) groups with equal small unmatched counts
# (same-score back-to-backs; any bijection yields the same pairing count)
ge = defaultdict(list)
for r in unmatched_espn:
    ge[(ekey(r), r["home_score"], r["away_score"])].append(r)
gs = defaultdict(list)
for r in unmatched.values():
    gs[(tuple(sorted([norm_name(r["home_team_name"]), norm_name(r["away_team_name"])])),
        r["home_pts"], r["away_pts"])].append(r)
for k, es in ge.items():
    ss = gs.get(k, [])
    if 0 < len(es) == len(ss) <= 2:
        for _r in es:
            matched += 1
            grpfb += 1
        for sr in ss:
            del unmatched[id(sr)]
left_e = [r for r in unmatched_espn
          if len(ge[(ekey(r), r["home_score"], r["away_score"])])
          != len(gs.get((ekey(r), r["home_score"], r["away_score"]), []))
          or len(ge[(ekey(r), r["home_score"], r["away_score"])]) > 2]
espn_only = len(left_e)
stats_only = len(unmatched)
union = len(univ) + stats_only
check("union_7017", matched == 5979 and espn_only == 9 and stats_only == 1029 and union == 7017
      and window0 == matched - scorefb - grpfb,
      f"matched={matched} (window offset0={window0}, score-fallback={scorefb}, "
      f"group-fallback={grpfb}); ESPN-only={espn_only} ({sorted(r['id'] for r in left_e)}); "
      f"stats-only={stats_only}; union={union}")

# --------------------------------------------- 20-key lineage table re-verify
tk = []
with open(os.path.join(PREP, "team_key_table.csv"), newline="", encoding="utf-8") as f:
    rdr = csv.reader(f)
    next(rdr)
    tk = [row for row in rdr]
keys = [r[0] for r in tk]
flat = "|".join(",".join(r) for r in tk)
lva = next((r for r in tk if r[0] == "LVA"), None)
dal = next((r for r in tk if r[0] == "DAL"), None)
name2fk = {}
abbr2fk = {}
for row in tk:
    for col in (1, 3):
        for dn in row[col].split(";"):
            name2fk[dn.strip()] = row[0]
    for ab in row[4].split(";"):
        abbr2fk[ab.strip()] = row[0]
for a in ALIAS:  # ASG teams are not franchises
    abbr2fk[a] = "ASG"
lineage_ok = (len(tk) == 20 and "SAN_DAL" not in flat and "DET_TUL" not in flat
              and lva and dal
              and all(n in lva[1] for n in ("Utah Starzz", "San Antonio Stars", "Las Vegas Aces"))
              and lva[-2] == "1997" and lva[-1] == "2026"
              and all(n in dal[1] for n in ("Detroit Shock", "Tulsa Shock", "Dallas Wings"))
              and dal[-2] == "1998" and dal[-1] == "2026")
check("lineage_20keys", lineage_ok,
      f"rows={len(tk)}; SAN_DAL/DET_TUL absent={'SAN_DAL' not in flat and 'DET_TUL' not in flat}; "
      f"LVA {lva[-2]}-{lva[-1]} (UTA/SAN/LVA); DAL {dal[-2]}-{dal[-1]} (DET/TUL/DAL)")

# ============================================================ ROSTER AUDIT ===
rosters, pboxes = {}, {}
for y in range(2002, 2027):
    with open(os.path.join(RA, f"game_rosters_{y}.csv"), newline="", encoding="utf-8") as f:
        rosters[y] = list(csv.DictReader(f))
    with open(os.path.join(RA, f"player_box_{y}.csv"), newline="", encoding="utf-8") as f:
        pboxes[y] = list(csv.DictReader(f))
check("roster_loaded", len(rosters) == 25 and len(pboxes) == 25,
      f"25 roster files ({sum(len(v) for v in rosters.values())} rows) + 25 player_box files "
      f"({sum(len(v) for v in pboxes.values())} rows)")

hdrs = set()
for y in rosters:
    with open(os.path.join(RA, f"game_rosters_{y}.csv"), newline="", encoding="utf-8") as f:
        hdrs.add(tuple(next(csv.reader(f))))
hdr = next(iter(hdrs))
check("roster_schema", len(hdrs) == 1 and len(hdr) == 22 and "game_id" in hdr
      and not any(c == "game_date" or c == "date" for c in hdr),
      f"one identical header across 25 files, {len(hdr)} cols; game_id present; "
      f"date column absent={not any(c in ('game_date', 'date') for c in hdr)}")

# --- (a) coverage vs universe; game-1; missing = 5, none a game-1
univ_ids = {r["id"]: r for r in univ}
universe_by_season = defaultdict(set)
for r in univ:
    universe_by_season[int(r["season"])].add(r["id"])
teamid_map = defaultdict(dict)
univ_games_by_team = defaultdict(list)
unmapped_dn = Counter()
for r in univ:
    y = int(r["season"])
    for side in ("home", "away"):
        fk = name2fk.get(r[f"{side}_display_name"])
        if not fk:
            unmapped_dn[(y, r[f"{side}_display_name"])] += 1
            continue
        teamid_map[y][r[f"{side}_id"]] = fk
        univ_games_by_team[(y, fk)].append((parse_ts(r["game_date_time"]), r["id"], r[f"{side}_id"]))
check("universe_names_mapped", not unmapped_dn,
      f"universe team display names unmapped to franchise keys: {dict(unmapped_dn) if unmapped_dn else 'NONE'}")

roster_games = defaultdict(set)
roster_rows_by_gt = defaultdict(int)
dup_keys = Counter()
all_roster_gids = set()
empty_gid = bad_gid = 0
for y, rows in rosters.items():
    for r in rows:
        gid = (r.get("game_id") or "").strip()
        if not gid:
            empty_gid += 1
            continue
        if not re.fullmatch(r"[0-9]{9,10}", gid):
            bad_gid += 1
        all_roster_gids.add(gid)
        roster_games[y].add(gid)
        roster_rows_by_gt[(gid, r["team_id"])] += 1
        dup_keys[(gid, r["team_id"], r["athlete_id"])] += 1

covered_total = sum(len(roster_games[y] & universe_by_season[y]) for y in roster_games)
missing = {y: universe_by_season[y] - roster_games[y] for y in sorted(universe_by_season)}
missing_detail = []
for y, ids in missing.items():
    for gid in ids:
        r = univ_ids[gid]
        missing_detail.append(f"{y}:{gid} {r['game_date'][:10]} {r['away_display_name']}@{r['home_display_name']}")
n_missing = sum(len(v) for v in missing.values())
check("roster_coverage_5983", covered_total == 5983 and n_missing == 5,
      f"universe games with rosters={covered_total}/5988; missing={n_missing}: {missing_detail}")

first_game = {}
for (y, fk), lst in univ_games_by_team.items():
    lst.sort()
    first_game[(y, fk)] = lst[0]
viol = []
for y, ids in missing.items():
    for gid in ids:
        r = univ_ids[gid]
        for side in ("home", "away"):
            fk = name2fk.get(r[f"{side}_display_name"])
            if fk and first_game.get((y, fk)) and first_game[(y, fk)][1] == gid:
                viol.append((y, gid, fk))
check("missing_not_game1", not viol,
      f"missing-roster games that are a team's season game-1: {viol if viol else 'NONE'}")

g1_missing = []
g1_lt10 = []
g1_min = 10 ** 9
for (y, fk), (tip, gid, tid) in first_game.items():
    n = roster_rows_by_gt.get((gid, tid), 0)
    g1_min = min(g1_min, n)
    if n < 1:
        g1_missing.append((y, fk, gid, n))
    if n < 10:
        g1_lt10.append((y, fk, gid, n))
check("opening_game1_presence", not g1_missing,
      f"team-seasons={len(first_game)}; game-1 roster ABSENT: "
      f"{g1_missing if g1_missing else 'NONE (100% presence)'}; "
      f"game-1 rows<10 per TEAM ({len(g1_lt10)} team-seasons): {g1_lt10}; min rows/team={g1_min}")

dups = {k: c for k, c in dup_keys.items() if c > 1}
check("duplicates_0", not dups, f"duplicate (game,team,athlete) rows across 25 seasons: {len(dups)}")

# --- (c) game linkage
full_espn_ids = set(espn_ids)
unresolved = all_roster_gids - full_espn_ids
nonuniv = all_roster_gids - set(univ_ids)
check("game_linkage_100pct", empty_gid == 0 and bad_gid == 0 and not unresolved,
      f"roster rows with empty/malformed game_id={empty_gid}/{bad_gid}; distinct roster game_ids="
      f"{len(all_roster_gids)}; unresolvable vs full ESPN schedule={len(unresolved)}; "
      f"roster gids outside filter-law universe={len(nonuniv)} (ASG+forfeit, all in full schedule="
      f"{all(g in full_espn_ids for g in nonuniv)})")

# --- (d) minutes-side coverage + computable-continuity T=2003..2026
pb_games = defaultdict(set)
pb_minutes_games = defaultdict(set)
pb_gameteam = defaultdict(set)
box2002 = pboxes[2002]
stub_all_dd = all(r["min"] == "--" for r in box2002)
for r in box2002:
    pb_games[2002].add(r["game_id"])
for y in range(2003, 2027):
    for r in pboxes[y]:
        pb_games[y].add(r["game_id"])
        pb_gameteam[y].add((r["game_id"], r["team_id"]))
        try:
            if float(r["minutes"]) > 0:
                pb_minutes_games[y].add(r["game_id"])
        except (ValueError, KeyError, TypeError):
            pass

cov_rows = []
for y in range(2002, 2027):
    u = len(universe_by_season[y])
    g = len(pb_games[y] & universe_by_season[y])
    gm = len(pb_minutes_games[y] & universe_by_season[y])
    cov_rows.append((y, g, u, u - g, gm))
exp_cov = {2002: (16, 271), 2003: (194, 255), 2004: (214, 237), 2005: (229, 238)}
exp_missing = {2010: 1, 2012: 2, 2016: 2}   # measured; matches lane A's own measurements_r2.json
cov_ok = all((cov_rows[y - 2002][1], cov_rows[y - 2002][2]) == exp_cov[y] for y in exp_cov)
cov_ok = cov_ok and all(cov_rows[y - 2002][3] == exp_missing.get(y, 0) for y in range(2009, 2027))
cov_ok = cov_ok and all(2 <= cov_rows[y - 2002][3] <= 7 for y in range(2006, 2009))
check("box_coverage", cov_ok and stub_all_dd and len(box2002) == 344,
      f"2002 stub rows={len(box2002)} games-with-rows={cov_rows[0][1]}/271 minutes-all-'--'={stub_all_dd}; "
      f"missing games per season: " + ", ".join(f"{y}:{m}" for y, _g, _u, m, _gm in cov_rows)
      + " (NOTE: audit MD sec6 says '2009-2025 complete (0 missing)' — its own machine output "
      + "and these bytes say 2010:1, 2012:2, 2016:2; all ratios stay >=0.94 >= 0.8)")

# expansion = franchise with NO universe games in the immediately-prior season
# (first roster era 2002 excluded — those franchises predate the ESPN coverage window)
seasons_fk = defaultdict(set)
for (y, fk) in univ_games_by_team:
    seasons_fk[fk].add(y)
expansion = set()
for T in range(2003, 2027):
    for fk in seasons_fk:
        if T in seasons_fk[fk] and (T - 1) not in seasons_fk[fk]:
            expansion.add((T, fk))
exp_expected = {(2006, "CHI"), (2008, "ATL"), (2025, "GSV"), (2026, "POR_PDX"), (2026, "TOR")}
check("expansion_set", expansion == exp_expected,
      f"derived expansion team-seasons={sorted(expansion)}; matches audit's "
      f"{sorted(exp_expected)}={expansion == exp_expected}")


def box_ratio(y, fk):
    ug = {gid for (_t, gid, _i) in univ_games_by_team.get((y, fk), [])}
    if not ug:
        return None
    fids = {tid for tid, f2 in teamid_map[y].items() if f2 == fk}
    withrows = {gid for gid in ug if any((gid, tid) in pb_gameteam[y] for tid in fids)}
    return len(withrows) / len(ug)


cont_rows = []
for T in range(2003, 2027):
    exp_teams = {fk for (y, fk) in univ_games_by_team if y == T}
    exp_here = {fk for fk in exp_teams if (T, fk) in expansion}
    nonexp = exp_teams - exp_here
    # gate per audit sec6 = "game-1 roster present" (presence, not a row-count threshold)
    gate = {fk: roster_rows_by_gt.get((first_game[(T, fk)][1],
                                       first_game[(T, fk)][2]), 0) >= 1 for fk in nonexp}
    ratios = {fk: (box_ratio(T - 1, fk) or 0.0) for fk in nonexp}
    comp = [fk for fk in ratios if gate[fk] and ratios[fk] >= 0.8]
    cont_rows.append({"T": T, "teams": len(nonexp), "gate_ok": sum(gate.values()),
                      "min_ratio": round(min(ratios.values()), 4) if ratios else None,
                      "ge08": len(comp),
                      "pct": round(100.0 * len(comp) / len(ratios), 1) if ratios else None})

exp_frac = {2003: 0.0, 2004: 38.5, 2005: 92.3}
cc_ok = True
for row in cont_rows:
    T = row["T"]
    if T in exp_frac:
        cc_ok &= (row["pct"] == exp_frac[T])
    else:
        cc_ok &= (row["pct"] == 100.0 and row["ge08"] == row["teams"] and row["gate_ok"] == row["teams"])
check("computable_continuity", cc_ok,
      f"minutes-weighted computable fraction (>=0.8 prior-box): "
      + "; ".join(f"T{r['T']}:{r['ge08']}/{r['teams']}={r['pct']}%" for r in cont_rows))
gate90 = all(r["gate_ok"] == r["teams"] and r["teams"] > 0 for r in cont_rows if 2003 <= r["T"] <= 2025)
check("gate90_2003_2025", gate90,
      "roster gate 100% every season 2003-2025 (>=~90% B-lane gate): " + ("PASS 23/23" if gate90 else "FAIL"))

# --- (e) retro-fill scan — audit's probe key: (franchise, athlete) has NO box row
# that season ("same-team-season"); box 2002 has no display names -> franchise via
# the key table's espn_abbrs column; ASG rows dropped on both sides first.
retro = {}
retro_gamelevel = {}
for y in range(2002, 2027):
    rf = {}
    for r in rosters[y]:
        fk = name2fk.get(r["team_display_name"])
        if fk:
            rf[(fk, r["athlete_id"])] = rf.get((fk, r["athlete_id"]), 0) + 1
    bf = set()
    for r in pboxes[y]:
        fk = (name2fk.get(r.get("team_display_name"))
              if r.get("team_display_name") else
              abbr2fk.get(r.get("team_abbreviation")))
        if fk and fk != "ASG":
            bf.add((fk, r["athlete_id"]))
    only = [r for r in rosters[y]
            if (name2fk.get(r["team_display_name"]), r["athlete_id"]) not in bf
            and name2fk.get(r["team_display_name"])]
    st = sum(1 for r in only if is_true(r["starter"]))
    retro[y] = (len(only), st)
    # game-level cross-probe (stricter; box omits DNP players before 2012)
    rk = {(r["game_id"], r["team_id"], r["athlete_id"]) for r in rosters[y]}
    bk2 = {(r["game_id"], r["team_id"], r["athlete_id"]) for r in pboxes[y]}
    retro_gamelevel[y] = len(rk - bk2)
retro_ok = (retro[2002] == (1061, 412) and retro[2003] == (10, 4) and retro[2004] == (1, 0)
            and retro[2005] == (9, 0) and all(retro[y] == (0, 0) for y in range(2006, 2027)))
check("retrofill", retro_ok,
      "roster rows with no same-team-SEASON (franchise,athlete) box row: "
      + ", ".join(f"{y}:{v[0]}(starter {v[1]})" for y, v in sorted(retro.items()))
      + f"; stricter game-level probe (box omits DNP players pre-2012): "
      + ", ".join(f"{y}:{n}" for y, n in sorted(retro_gamelevel.items()) if n))

# --- (f) 2025 starter cross-check (universe games; raw file also holds the ASG game)
r25, b25 = rosters[2025], pboxes[2025]
univ25 = universe_by_season[2025]
box_start = defaultdict(set)     # starters only
box_flag = {}
for r in b25:
    if r["game_id"] in univ25:
        box_flag[(r["game_id"], r["team_id"], r["athlete_id"])] = is_true(r["starter"])
        if is_true(r["starter"]):
            box_start[(r["game_id"], r["team_id"])].add(r["athlete_id"])
both5 = fivev5 = 0
for (g, t), bset in box_start.items():
    rset = {r["athlete_id"] for r in r25 if r["game_id"] == g and r["team_id"] == t
            and is_true(r["starter"])}
    if len(rset) == 5 and len(bset) == 5:
        both5 += 1
        fivev5 += (rset == bset)
row_total = row_agree = 0
for r in r25:
    if r["game_id"] not in univ25:
        continue
    k = (r["game_id"], r["team_id"], r["athlete_id"])
    if k in box_flag:
        row_total += 1
        row_agree += (box_flag[k] == is_true(r["starter"]))
n_g25 = len({r["game_id"] for r in r25 if r["game_id"] in univ25})
raw_g25 = len({r["game_id"] for r in r25})
raw_rows25 = len(r25)
asg_extra = raw_g25 - n_g25
check("starter_2025", len(box_start) == 622 and both5 == 622 and fivev5 == 622
      and row_total == 7115 and row_agree == 7115 and n_g25 == 311,
      f"universe games={n_g25} (raw file {raw_g25} games/{raw_rows25} rows — includes "
      f"{asg_extra} ASG game with 25 roster rows, removed by the filter-law join); "
      f"team-games={len(box_start)}; 5v5 both sides with IDENTICAL starter sets={fivev5}/{both5}; "
      f"row-level starter flags agree={row_agree}/{row_total}")

# --- (g) as-of law text
law_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "A_DATA",
                        "ROSTER_PIT_AUDIT_WNBA.md")
law = open(law_path, encoding="utf-8").read()
law_has = {
    "strictly-prior-game facts binding (law cl.1)": "season T−1 games" in law or "season T-1 games" in law,
    "knowable by construction (law cl.1)": "knowable before T's first tip" in law,
    "season-T rosters never inputs (law cl.2)": "Season-T roster rows are NEVER inputs" in law,
    "game-day fields forbidden pre-game (law cl.2)": "forbidden as pre-game features" in law
                                                      and "`starter`/`did_not_play`/`active`/`ejected`/`reason`" in law,
    "window T>=2006 minutes / T>=2003 roster (law cl.4)": ("T ≥ 2006" in law and "T = 2003" in law),
    "filter-law inner join mandatory (law cl.3)": "inner-joined to the lane A filter-law universe" in law,
    "display-name joins (law cl.5)": "team_display_name" in law,
}
check("asof_law_text", all(law_has.values()), f"clauses: {law_has}")

# ------------------------------------------------------------------ detail
print("\n=== computable-continuity (independent re-derivation) ===")
for r in cont_rows:
    print(r)
print("\n=== box games-with-rows / universe per season ===")
for y, g, u, m, gm in cov_rows:
    print(f"{y}: {g}/{u} (missing {m}; minutes>0 games {gm})")

out = {k: v[0] for k, v in results.items()}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "reverify_r2_results.json"), "w"), indent=1)
fails = [k for k, v in results.items() if v[0] == FAIL]
print(f"\nTOTAL: {len(results) - len(fails)}/{len(results)} PASS; failures: {fails if fails else 'none'}")
sys.exit(1 if fails else 0)
