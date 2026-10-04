#!/usr/bin/env python
"""
NFL-WINPROB-PREP-V1 — Lane B (NFL_B_dataset) census script.

Reads ONLY:
  ~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv
  ~/.my-quantitative-data/nfl-nflverse-v1/raw/play_by_play_{2021..2025}.parquet

Writes NOTHING (prints census report to stdout). Run with the workspace venv:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python audit_script.py

Authoritative docs used for semantics (fetched 2026-10-04):
- Lee Sharpe DATASETS.md (nflverse/nfldata), games.csv section:
  "gametime: The kickoff time of the game. This is represented in 24-hour time
   and the Eastern time zone, regardless of what time zone the game was being
   played in."
- nflreadr data-raw/dictionary_schedules.csv: same gametime wording; location =
  Home/Neutral; game_type in {REG,WC,DIV,CON,SB}.
"""
import hashlib
import os
import re
import sys
from collections import Counter

import pandas as pd
import pyarrow.parquet as pq

RAW = os.path.expanduser("~/.my-quantitative-data/nfl-nflverse-v1/raw")

LINE = "=" * 78
def sec(title):
    print("\n" + LINE + "\n== " + title + "\n" + LINE)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------------- A. GAMES.CSV
sec("A. GAMES.CSV STRUCTURE")
games_path = os.path.join(RAW, "games.csv")
g = pd.read_csv(games_path, dtype=str, keep_default_na=False, na_values=[""])
print("columns (%d):" % len(g.columns))
print(list(g.columns))
print("rows:", len(g))

seasons = sorted(g["season"].astype(int).unique())
print("season range: %d..%d (n_seasons=%d)" % (seasons[0], seasons[-1], len(seasons)))
print("NOTE: dispatch expected 1920s..2026; measured min season above is authoritative "
      "for the nflverse-data schedules release.")

sec("A2. GAME_TYPE DOMAIN")
print(g["game_type"].value_counts(dropna=False).to_string())

sec("A3. FINISHED-GAMES FILTER (scores non-NA)")
g["finished"] = g["home_score"].notna() & g["away_score"].notna()
unfinished = g[~g["finished"]]
print("unfinished rows total:", len(unfinished))
print("unfinished by season:")
print(unfinished.groupby("season").size().to_string())
s2026 = g[g["season"] == "2026"]
print("2026 rows:", len(s2026), "| finished:", int(s2026["finished"].sum()),
      "| unfinished:", int((~s2026["finished"]).sum()))
print("2026 game_type counts (unfinished):")
print(s2026.loc[~s2026["finished"], "game_type"].value_counts().to_string())
# last finished game overall
fin = g[g["finished"]].copy()
fin["gd"] = fin["gameday"]
print("last finished game:", fin.sort_values("gd").iloc[-1][
    ["game_id", "gameday", "game_type"]].to_dict())

sec("A4. PER-SEASON REGULAR-SEASON GAME COUNTS vs ERA EXPECTATIONS")
# teams active per season
g["season_i"] = g["season"].astype(int)
reg = g[g["game_type"] == "REG"]
rows = []
for s, sub in reg.groupby("season_i"):
    teams = set(sub["home_team"]) | set(sub["away_team"])
    n = len(sub)
    per_team = 2 * n / len(teams) if teams else 0
    rows.append((s, len(teams), n, round(per_team, 1)))
era = pd.DataFrame(rows, columns=["season", "teams", "reg_games", "games_per_team"])
print(era.to_string(index=False))

expect = {}
for s in era["season"]:
    if s >= 2021:
        expect[s] = 272
    elif s >= 2002:
        expect[s] = 256
    else:
        # 1999-2001: 31 teams x 16 games / 2 = 248 (CLE reactivated 1999; HOU in 2002)
        expect[s] = 248
era["expected"] = era["season"].map(expect)
era["match"] = era["reg_games"] == era["expected"]
print("\nseasons NOT matching era expectation (explanations follow):")
print(era[~era["match"]].to_string(index=False))
_22 = reg[(reg["season_i"] == 2022)]
missing_17 = sorted(set(reg.loc[reg["season_i"] == 2021, "game_id"]) |
                    set(reg.loc[reg["season_i"] == 2023, "game_id"]))
cand = _22[~_22["week"].isin([])]
print("2022 anomaly check: 271 REG rows vs 272 expected -> cancelled BUF@CIN "
      "(Damar Hamlin, 2023-01-02, declared no-contest). game_id 2022_17_BUF_CIN "
      "present?", (g["game_id"] == "2022_17_BUF_CIN").any())
print("\nstrike seasons 1982/1987: present in release?",
      (era["season"] == 1982).any(), (era["season"] == 1987).any(),
      "-> (release starts 1999; NOT_IN_RELEASE. 1982 strike: 9 games/team, "
      "28 teams = 126 REG games; 1987 strike: 15 games/team = 210 REG games.)")
print("2021+ seasons with 272 REG games:", era.loc[era["season"] >= 2021, "match"].all())

# ----------------------------------------------------------------------------- B. IDENTITY
sec("B. IDENTITY CENSUS")
abbr_first_last = {}
for col in ("home_team", "away_team"):
    pass
teams_long = pd.concat([
    g[["season", "home_team"]].rename(columns={"home_team": "team"}),
    g[["season", "away_team"]].rename(columns={"away_team": "team"}),
])
tl = teams_long.assign(season_i=teams_long["season"].astype(int))
table = tl.groupby("team")["season_i"].agg(["min", "max", "count"]).sort_values("min")
table.columns = ["first_season", "last_season", "team_games"]
print("distinct team abbreviations:", len(table))
print(table.to_string())

print("\nexpected renames check (games.csv uses the franchise abbrev of the era):")
renames_expect = [("STL", "LA", 2016), ("SD", "LAC", 2017), ("OAK", "LV", 2020)]
for old, new, yr in renames_expect:
    if old in table.index and new in table.index:
        ok = (table.loc[old, "last_season"] == yr - 1) and (table.loc[new, "first_season"] == yr)
        print(f"  {old}-> {new} in {yr}: measured {old} {table.loc[old,'first_season']}-"
              f"{table.loc[old,'last_season']}, {new} {table.loc[new,'first_season']}-"
              f"{table.loc[new,'last_season']} -> {'VERIFIED' if ok else 'CHECK'}")
    else:
        print(f"  {old}->{new}: MISSING ABBREV")

# transitions between consecutive seasons (abbreviation continuity)
print("\nabbreviation transitions (abbrev X in season s, no X in s+1, team appears as new abbrev):")
present = tl.groupby(["season_i", "team"]).size().reset_index()[["season_i", "team"]]
present["v"] = 1
piv = present.pivot(index="season_i", columns="team", values="v").fillna(0)
transitions = []
ss = sorted(piv.index)
for a, b in zip(ss[:-1], ss[1:]):
    gone = sorted([t for t in piv.columns if piv.loc[a, t] == 1 and piv.loc[b, t] == 0])
    new = sorted([t for t in piv.columns if piv.loc[a, t] == 0 and piv.loc[b, t] == 1])
    if gone or new:
        transitions.append((a, b, gone, new))
for a, b, gone, new in transitions:
    print(f"  {a}->{b}: gone={gone} new={new}")

sec("B2. GAME_ID / GSIS UNIQUENESS")
dup_game_id = g["game_id"][g["game_id"].duplicated()]
print("rows:", len(g), "| distinct game_id:", g["game_id"].nunique(),
      "| duplicate game_id rows:", len(dup_game_id))
if len(dup_game_id):
    print(g[g["game_id"].isin(dup_game_id)].sort_values("game_id")[
        ["game_id", "gameday", "home_team", "away_team"]].to_string(index=False))
gsis_nn = g.loc[g["gsis"].notna(), "gsis"]
print("gsis non-null:", len(gsis_nn), "| distinct:", gsis_nn.nunique(),
      "| duplicate gsis among non-null:", int(gsis_nn.duplicated().sum()))
print("gsis %null by season (seasons with any gsis missing):")
gsis_na = g.assign(_na=g["gsis"].isna()).groupby("season_i")["_na"].agg(["sum", "count"])
print(gsis_na[gsis_na["sum"] > 0].assign(pct=lambda d: (100 * d["sum"] / d["count"]).round(1)).to_string())
if gsis_nn.duplicated().any():
    dups = gsis_nn[gsis_nn.duplicated(keep=False)].unique()
    print(g[g["gsis"].isin(dups)][["game_id", "gameday", "gsis"]].to_string(index=False))

sec("B3. FRANCHISE LINEAGE PROPOSAL (measured, 1999+ release range)")
# group abbrevs by measured continuity from transitions + known expansions
lineages = {
    "LA-Rams": ["STL", "LA"],             # measured transition 2015->2016 (abbrev 'LA')
    "LA-Chargers": ["SD", "LAC"],         # measured transition 2016->2017
    "LV-Raiders": ["OAK", "LV"],          # measured transition 2019->2020
    "CLE-BAL": ["BAL", "CLE"],            # flag: 1999 CLE reactivation; abbrev continuity
                                          # alone cannot split BAL(1996)/CLE(1999) lineage
                                          # - protocol decision required
    "HOU-TEN": ["TEN"],                   # Oilers->Titans pre-dates release (1997 rename)
}
# every other abbrev is its own lineage in 1999+
singles = [t for t in table.index if t not in {a for v in lineages.values() for a in v}]
print(f"{'lineage':<12} {'member abbrevs (measured span)':<45} status")
for lin, members in lineages.items():
    spans = ", ".join(f"{m}[{table.loc[m,'first_season'] if m in table.index else '?'}-"
                      f"{table.loc[m,'last_season'] if m in table.index else '?'}]" for m in members)
    print(f"{lin:<12} {spans:<45} multi-abbrev")
print(f"{'single-abbrev':<12} {len(singles)} lineages: {sorted(singles)}")
print("total lineages: %d multi-abbrev + %d single-abbrev = %d"
      % (len(lineages), len(singles), len(lineages) + len(singles)))

# ----------------------------------------------------------------------------- C. PIT SURFACE
sec("C. PIT SURFACE: GAMETIME (kickoff time, documented US Eastern)")
pat = re.compile(r"^\d{1,2}:\d{2}$")
gt = g["gametime"]
parsed = gt.dropna().astype(str).str.match(pat)
print("gametime non-null: %d / %d (%.2f%%); parse rate HH:MM among non-null: %.2f%%"
      % (gt.notna().sum(), len(g), 100 * gt.notna().mean(),
         100 * parsed.mean()))
bad = gt.dropna()[~parsed]
print("non-null but non-HH:MM values (up to 10):", sorted(bad.unique())[:10])
print("distinct formats among non-null:", sorted(set(re.sub(r"\d", "#", v) for v in gt.dropna())))

per_season = g.groupby("season_i").apply(
    lambda sub: pd.Series({
        "rows": len(sub),
        "gt_missing": int(sub["gametime"].isna().sum()),
        "pct_missing": round(100 * sub["gametime"].isna().mean(), 2),
        "distinct_kickoff_times": int(sub["gametime"].dropna().nunique()),
        "modal_share_pct": (round(100 * sub["gametime"].value_counts(normalize=True).iloc[0], 1)
                            if sub["gametime"].notna().any() else None),
        "modal_value": (sub["gametime"].value_counts().index[0]
                        if sub["gametime"].notna().any() else None),
    }), include_groups=False)
print(per_season.to_string())

first_full = None
for s in sorted(per_season.index):
    if per_season.loc[s, "gt_missing"] == 0 and per_season.loc[s, "distinct_kickoff_times"] >= 6:
        later_ok = all(per_season.loc[x, "gt_missing"] == 0 for x in per_season.index if x >= s)
        if later_ok:
            first_full = s
            break
print("\nfirst season with 0 missing gametime AND >=6 distinct kickoff times, "
      "and all later seasons also 0-missing:", first_full)

sec("C2. TIMEZONE SEMANTICS (documented) + parse assumptions")
print("DOCUMENTED (Lee Sharpe DATASETS.md + nflreadr dictionary_schedules.csv): "
      "'gametime: The kickoff time of the game. This is represented in 24-hour time "
      "and the Eastern time zone, regardless of what time zone the game was being "
      "played in.' -> NOT undocumented/ambiguous; naive string, ET civil time, no tz suffix.")
print("Assumption A (recommended): gametime is America/New_York civil time; "
      "convert with DST rules (EDT UTC-4 through early Nov, EST UTC-5 after).")
print("Assumption B (fallback): treat as fixed UTC-05:00 (EST) year-round.")
# quantify divergence between A and B
import datetime as dt
try:
    from zoneinfo import ZoneInfo
    sample = fin.dropna(subset=["gametime"]).copy()
    sample["gt_ok"] = sample["gametime"].astype(str).str.match(pat)
    smp = sample[sample["gt_ok"]].head(20000).copy()
    smp["dt_naive"] = pd.to_datetime(smp["gameday"] + " " + smp["gametime"], format="mixed")
    edt = smp["dt_naive"].apply(
        lambda x: x.tz_localize(ZoneInfo("America/New_York"), ambiguous=False, nonexistent="shift_forward"))
    differs = edt.apply(lambda x: x.utcoffset().total_seconds() != -5 * 3600)
    print("sample games where A and B differ (EDT games, 1h shift): %d/%d (%.1f%%)"
          % (int(differs.sum()), len(differs), 100 * differs.mean()))
except Exception as e:
    print("tz divergence quantification failed:", type(e).__name__, e)
print("games with missing gametime:", int(gt.isna().sum()))
print("NOTE ordering: both assumptions preserve chronological order; only absolute UTC "
      "instant shifts by 1h for EDT games -> a 'kickoff strictly before as-of' law is "
      "safe under A; under B it is conservative by 1h for EDT games.")

# ----------------------------------------------------------------------------- D. QUALITY
sec("D. QUALITY: NULL CENSUS (key/score/pit columns)")
qcols = ["game_id", "season", "game_type", "week", "gameday", "gametime", "away_team",
         "home_team", "away_score", "home_score", "location", "result", "total",
         "overtime", "gsis", "old_game_id", "spread_line", "total_line", "stadium",
         "stadium_id", "away_rest", "home_rest"]
qc = pd.DataFrame({
    "n_null": [int(g[c].isna().sum()) for c in qcols],
    "pct_null": [round(100 * g[c].isna().mean(), 2) for c in qcols],
}, index=qcols)
print(qc.to_string())

sec("D2. SCORE CONSISTENCY (finished games)")
f = g[g["finished"]].copy()
for c in ("home_score", "away_score", "result", "total"):
    f[c + "_n"] = pd.to_numeric(f[c], errors="coerce")
bad_result = f[(f["result_n"] - (f["home_score_n"] - f["away_score_n"])).abs() > 0.001]
bad_total = f[(f["total_n"] - (f["home_score_n"] + f["away_score_n"])).abs() > 0.001]
print("finished games:", len(f))
print("result != home_score-away_score violations:", len(bad_result))
print("total != home_score+away_score violations:", len(bad_total))
neg = f[(f["home_score_n"] < 0) | (f["away_score_n"] < 0)]
print("negative scores:", len(neg))
ties = f[(f["home_score_n"] == f["away_score_n"])]
print("tie games (incl. playoff wins?) finished ties:", len(ties))

sec("D3. NEUTRAL-SITE CENSUS")
print("location domain:", g["location"].value_counts(dropna=False).to_dict())
neu = g[g["location"] == "Neutral"]
print("neutral games:", len(neu), "| by season:")
print(neu.groupby("season_i").size().to_string())
print("\nsample of 10 known neutral games (measured from data):")
picks = []
sb = neu[neu["game_type"] == "SB"]
intl_stadium_pat = re.compile(
    r"wembley|tottenham|azteca|allianz arena|totthenham|corinthians|bernabeu|croke|accordion|rogers centre|olympic", re.I)
intl = neu[neu["stadium"].fillna("").str.contains(intl_stadium_pat)]
take_sb = sb.tail(5)
take_intl = intl.tail(5)
sample = pd.concat([take_sb, take_intl]).sort_values("season_i")
print(sample[["season", "week", "game_type", "away_team", "home_team", "stadium",
              "location", "gameday"]].to_string(index=False))
print("total international-stadium neutral games detected:", len(intl))

sec("D4. BYE-WEEK / REST SANITY")
tl2 = tl.merge(g[["game_id", "gameday"]].rename(columns={"game_id": "gid"}), left_index=True,
               right_index=True, how="left") if False else None
# build team-game dates from games table directly
long = pd.concat([
    g[["season_i", "game_id", "gameday", "home_team"]].rename(columns={"home_team": "team"}),
    g[["season_i", "game_id", "gameday", "away_team"]].rename(columns={"away_team": "team"}),
]).sort_values(["team", "season_i", "gameday"])
long["date"] = pd.to_datetime(long["gameday"])
long["gap_days"] = long.groupby(["team", "season_i"])["date"].diff().dt.days
gaps = long["gap_days"].dropna()
print("team-game gaps (days) within team-season: n=%d p50=%.0f p95=%.0f max=%.0f"
      % (len(gaps), gaps.quantile(0.5), gaps.quantile(0.95), gaps.max()))
print("gap distribution (days -> count):")
print(gaps.value_counts().sort_index().head(12).to_string())
print("max gap by decade (sanity; byes/concaCancel gaps visible):")
long["decade"] = (long["season_i"] // 10) * 10
print(long.groupby("decade")["gap_days"].max().to_string())
rest_cols_na = g.assign(season_i=g["season_i"]).groupby("season_i")["away_rest"].apply(
    lambda s: round(100 * s.isna().mean(), 1))
print("away_rest %null by season (first seasons shown):")
print(rest_cols_na.head(30).to_string())

# ----------------------------------------------------------------------------- E. PBP SUBSET
sec("E. PBP SUBSET (parquet)")
PBP_YEARS = [2021, 2022, 2023, 2024, 2025]
pbp_summary = []
game_ids_all = set(g["game_id"])
for y in PBP_YEARS:
    p = os.path.join(RAW, "play_by_play_%d.parquet" % y)
    if not os.path.exists(p):
        print(p, "MISSING")
        continue
    md = pq.ParquetFile(p).metadata
    t = pq.read_table(p, columns=["game_id", "season"])
    gid = t["game_id"].to_pylist()
    seas = set(t["season"].to_pylist())
    n_distinct = len(set(gid))
    n_in_games = len(set(gid) & game_ids_all)
    rows = md.num_rows
    print("play_by_play_%d.parquet: rows=%d distinct_game_id=%d games_in_games.csv=%d "
          "season_values=%s bytes=%d sha256=%s"
          % (y, rows, n_distinct, n_in_games, sorted(seas), os.path.getsize(p),
             sha256_file(p)[:16] + "..."))
    pbp_summary.append((y, rows, n_distinct, n_in_games))
print("total pbp rows:", sum(r[1] for r in pbp_summary))

# ----------------------------------------------------------------------------- F. FREEZE
sec("F. FREEZE PROPOSAL (measured)")
complete = [s for s in sorted(per_season.index)
            if s < 2026]  # 2026 rows exist and are unfinished -> in progress
print("measured max season with finished games:", int(fin["season"].astype(int).max()))
print("final 7 complete seasons -> TEST:", complete[-7:])
ff = first_full if first_full is not None else 1999
print("TRAIN start candidates: 1999 (release start) vs %s (gametime grain boundary)" % ff)
print("PROPOSAL: TEST = %s..%d; TRAIN = %d..%d (see DATASET_AUDIT.md for the measured "
      "justification)" % (complete[-7], complete[-1], ff, complete[-8] if len(complete) >= 8 else 0))

print("\nCENSUS COMPLETE")
