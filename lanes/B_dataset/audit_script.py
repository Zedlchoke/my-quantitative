#!/usr/bin/env python3
"""
audit_script.py — Lane B (B_dataset) byte-to-field audit of nbaallelo.csv
Cycle: NBA-WINPROB-PREP-V1. Read-only over the raw file; prints all results to stdout.
Run: python3 audit_script.py
Deps: pandas (2.3.1), numpy. No network, no writes.
"""
import hashlib
import sys

import numpy as np
import pandas as pd

CSV = "/Users/hoangminhlong/.my-quantitative-data/nba-538-v1/raw/nbaallelo.csv"
EXPECTED_SHA = "d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc"
EXPECTED_SIZE = 18173265


def sec(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def sha256_and_size(path):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


# ---------------------------------------------------------------- check 1
sec("CHECK 1: hash, size, row count")
sha, size = sha256_and_size(CSV)
print(f"sha256  = {sha}")
print(f"expect  = {EXPECTED_SHA}")
print(f"hash match = {sha == EXPECTED_SHA}")
print(f"size    = {size} (expect {EXPECTED_SIZE}, match={size == EXPECTED_SIZE})")

df = pd.read_csv(CSV)
print(f"data rows (excl header) = {len(df)}")
print(f"header columns          = {len(df.columns)}")

# ---------------------------------------------------------------- check 2
sec("CHECK 2: column census — dtypes and categorical domains")
print("\n--- columns / inferred dtypes / null counts ---")
census = pd.DataFrame({
    "dtype": df.dtypes.astype(str),
    "n_null": df.isna().sum(),
    "n_unique": [df[c].nunique(dropna=False) for c in df.columns],
})
print(census.to_string())

for col in ["lg_id", "_iscopy", "is_playoffs", "game_location", "game_result"]:
    print(f"\n--- domain of {col} ---")
    print(df[col].value_counts(dropna=False).to_string())

sec("CHECK 2b: _iscopy semantics + mirror verification")
per_game_rows = df.groupby("game_id").size().value_counts().sort_index()
print("\nrows-per-game_id distribution:")
print(per_game_rows.to_string())
n_games = df["game_id"].nunique()
print(f"distinct game_id = {n_games}; total rows = {len(df)}; "
      f"rows = 2 x games for {per_game_rows.get(2, 0)} games")

iscopy_loc = pd.crosstab(df["_iscopy"], df["game_location"])
print("\ncrosstab _iscopy x game_location:")
print(iscopy_loc.to_string())

r0 = df[df["_iscopy"] == 0].set_index("game_id")
r1 = df[df["_iscopy"] == 1].set_index("game_id")
print(f"\nrows with _iscopy=0: {len(r0)}, _iscopy=1: {len(r1)}, common game_ids: "
      f"{len(r0.index.intersection(r1.index))}")
common = r0.index.intersection(r1.index)
m = r0.loc[common].join(r1.loc[common], how="inner", lsuffix="_a", rsuffix="_b")

chk = {}
chk["pts mirror violated (pts_a != opp_pts_b)"] = int((m["pts_a"] != m["opp_pts_b"]).sum())
chk["opp_pts mirror violated (opp_pts_a != pts_b)"] = int((m["opp_pts_a"] != m["pts_b"]).sum())
chk["elo_i mirror violated (elo_i_a != opp_elo_i_b)"] = int((m["elo_i_a"] != m["opp_elo_i_b"]).sum())
chk["opp_elo_i mirror violated (opp_elo_i_a != elo_i_b)"] = int((m["opp_elo_i_a"] != m["elo_i_b"]).sum())
chk["same team mirrored (team_id_a == team_id_b)"] = int((m["team_id_a"] == m["team_id_b"]).sum())
chk["opp mismatch (team_id_a != opp_id_b)"] = int((m["team_id_a"] != m["opp_id_b"]).sum())
chk["fran mismatch (fran_id_a != opp_fran_b)"] = int((m["fran_id_a"] != m["opp_fran_b"]).sum())
locpair = m["game_location_a"] + m["game_location_b"]
chk["location pair HA"] = int((locpair == "HA").sum())
chk["location pair AH"] = int((locpair == "AH").sum())
chk["location pair NN"] = int((locpair == "NN").sum())
chk["location OTHER (both H or both A)"] = int((~locpair.isin(["HA", "AH", "NN"])).sum())
respair = m["game_result_a"] + m["game_result_b"]
chk["result pair WL"] = int((respair == "WL").sum())
chk["result pair LW"] = int((respair == "LW").sum())
chk["result OTHER"] = int((~respair.isin(["WL", "LW"])).sum())
chk["year_id mismatch"] = int((m["year_id_a"] != m["year_id_b"]).sum())
chk["date mismatch"] = int((m["date_game_a"] != m["date_game_b"]).sum())
chk["gameorder mismatch"] = int((m["gameorder_a"] != m["gameorder_b"]).sum())
chk["is_playoffs mismatch"] = int((m["is_playoffs_a"] != m["is_playoffs_b"]).sum())
fc_dev = (m["forecast_a"] + m["forecast_b"] - 1.0).abs()
chk["forecast complementarity: max |f_a+f_b-1|"] = float(fc_dev.max())
chk["forecast complementarity: mean |f_a+f_b-1|"] = float(fc_dev.mean())
for k, v in chk.items():
    print(f"  {k}: {v}")

# _iscopy vs H: is _iscopy=0 always the home row?
non_h_orig = int(((df["_iscopy"] == 0) & (df["game_location"] != "H")).sum())
h_copy = int(((df["_iscopy"] == 1) & (df["game_location"] == "H")).sum())
nn = df[df["game_location"] == "N"]
print(f"\nrows _iscopy=0 & location!=H: {non_h_orig}")
print(f"rows _iscopy=1 & location==H: {h_copy}")
print(f"rows location=='N': {len(nn)}")
if len(nn):
    print(nn[["game_id", "date_game", "team_id", "fran_id", "opp_id",
              "game_location", "is_playoffs", "notes"]].head(20).to_string())

# ---------------------------------------------------------------- check 3
sec("CHECK 3: chronology & coverage")
d = pd.to_datetime(df["date_game"], format="%m/%d/%Y")
df = df.assign(_date=d)
print(f"min(date_game) = {df['_date'].min().date()}  max(date_game) = {df['_date'].max().date()}")
print(f"rows with date year >= 2016: {int((df['_date'].dt.year >= 2016).sum())}")
print(f"distinct gameorder values = {df['gameorder'].nunique()} "
      f"(min {df['gameorder'].min()}, max {df['gameorder'].max()})")

go = df["gameorder"].to_numpy()
print(f"gameorder non-decreasing: {bool(np.all(np.diff(go) >= 0))}")
if not np.all(np.diff(go) >= 0):
    bad = np.where(np.diff(go) < 0)[0]
    print(f"  first decreasing indices: {bad[:10]}, total {len(bad)}")
dt = df["_date"].to_numpy()
print(f"date_game non-decreasing across file: {bool(np.all(dt[1:] >= dt[:-1]))}")
if not np.all(dt[1:] >= dt[:-1]):
    bad = np.where(dt[1:] < dt[:-1])[0]
    print(f"  first decreasing indices: {bad[:10]}, total {len(bad)}")
    idx = df.index[bad[:5] + 1]
    print(df.loc[idx, ["gameorder", "game_id", "date_game"]].to_string())

g = df.groupby("gameorder")["_date"].nunique()
print(f"gameorder groups with >1 distinct date: {int((g > 1).sum())}")

# game_id date prefix vs date_game
pref = pd.to_datetime(df["game_id"].str[:8], format="%Y%m%d", errors="coerce")
mm = pref != df["_date"]
print(f"game_id date-prefix != date_game: {int(mm.sum())} rows / "
      f"{df.loc[mm, 'game_id'].nunique()} games "
      f"({100 * mm.mean():.3f}% of rows)")
if mm.sum():
    sm = df.loc[mm, ["game_id", "date_game"]].drop_duplicates("game_id")
    delta = (pref - df["_date"]).dt.days.loc[mm]
    print(f"  prefix-date minus date_game (days): value_counts:")
    print(delta.value_counts().head(10).to_string())
    print(f"  examples:\n{sm.head(8).to_string()}")

print(f"\nLAST ROWS (file order):")
print(df.tail(4)[["gameorder", "game_id", "date_game", "year_id", "is_playoffs",
                  "team_id", "fran_id", "pts", "opp_id", "opp_pts",
                  "game_location", "game_result"]].to_string())

# per-season census + expectation
sec("CHECK 3b: rows/games per season vs era expectation")
per_season = df.groupby("year_id").agg(
    rows=("game_id", "size"),
    games=("game_id", "nunique"),
    teams=("team_id", "nunique"),
    lg=("lg_id", lambda s: ",".join(sorted(s.unique()))),
)
po = df[df["is_playoffs"] == 1].groupby("year_id")["game_id"].nunique()
per_season["po_games"] = po.reindex(per_season.index).fillna(0).astype(int)
per_season["rs_games"] = per_season["games"] - per_season["po_games"]

# games-per-team schedule length by era (historical NBA/BAA regular season)
SCHED = {}
for y in range(1968, 1999):
    SCHED[y] = 82
SCHED.update({1947: 60, 1948: 48, 1949: 60, 1950: 68, 1951: 66, 1952: 66,
              1953: 70, 1954: 72, 1955: 72, 1956: 72, 1957: 72, 1958: 72,
              1959: 72, 1960: 75, 1961: 79, 1962: 80, 1963: 80, 1964: 80,
              1965: 80, 1966: 80, 1967: 81, 1999: 50, 2012: 66})
for y in range(2000, 2012):
    SCHED[y] = 82
for y in range(2013, 2016):
    SCHED[y] = 82

def exp_po(year_id, teams, rs_games):
    """approx expected playoff games: rounds by era x ~5.5 games/series"""
    if year_id == 1947:  # BAA: 6? teams, semis+finals (3 rounds of ~4-5 games)
        return 20
    if year_id == 1948:
        return 22
    if 1949 <= year_id <= 1950:
        return 30
    if 1951 <= year_id <= 1954:
        return 30
    if 1955 <= year_id <= 1966:
        return 35
    if 1967 <= year_id <= 1974:
        return 45
    if 1975 <= year_id <= 1983:
        return 60
    if year_id == 1984:
        return 70
    return 85  # modern 15-series, best-of-7-ish

per_season["exp_rs"] = [SCHED.get(y, None) * t / 2 for y, t in zip(per_season.index, per_season["teams"])]
per_season["exp_total"] = per_season["exp_rs"] + [exp_po(y, t, r) for y, t, r in
                                                  zip(per_season.index, per_season["teams"], per_season["rs_games"])]
per_season["dev_pct"] = (per_season["games"] - per_season["exp_total"]) / per_season["exp_total"] * 100
print(per_season.to_string(float_format=lambda x: f"{x:.1f}"))
flag = per_season[per_season["dev_pct"].abs() > 10]
print(f"\nseasons deviating >10% from expectation: {len(flag)}")
if len(flag):
    print(flag[["games", "teams", "rs_games", "po_games", "exp_rs", "exp_total", "dev_pct"]]
          .to_string(float_format=lambda x: f"{x:.1f}"))

print("\nnotes on flagged seasons (teams x schedule):")
for y in flag.index:
    print(f"  {y}: teams={per_season.loc[y,'teams']}, rs_games={per_season.loc[y,'rs_games']}, "
          f"games/team={2*per_season.loc[y,'rs_games']/per_season.loc[y,'teams']:.1f}")

# ---------------------------------------------------------------- check 4
sec("CHECK 4: identity — team_id/fran_id census, renames, continuity map")
tm = df.groupby("team_id").agg(fran_id=("fran_id", lambda s: ",".join(sorted(s.unique()))),
                               first_season=("year_id", "min"),
                               last_season=("year_id", "max"),
                               games=("game_id", "size"))
print("\n--- FULL team_id -> fran_id map ---")
print(tm.sort_values(["fran_id", "first_season"]).to_string())

multi = tm[tm["fran_id"].str.contains(",")]
print(f"\nteam_ids mapped to >1 fran_id (identity anomaly): {len(multi)}")
if len(multi):
    print(multi.to_string())

fr = df.groupby("fran_id").agg(team_ids=("team_id", lambda s: ",".join(sorted(s.unique()))),
                               first_season=("year_id", "min"),
                               last_season=("year_id", "max"),
                               games=("game_id", "size"))
fr["n_team_ids"] = fr["team_ids"].str.split(",").str.len()
print(f"\ndistinct team_id = {df['team_id'].nunique()}, distinct fran_id = {df['fran_id'].nunique()}")
print(f"fran_ids with >1 team_id (rename/lineage): {int((fr['n_team_ids'] > 1).sum())}")
print("\n--- fran_id -> team_ids (renames) ---")
print(fr[fr["n_team_ids"] > 1].sort_index().to_string())

# per-team-id season ranges inside each fran (to spot gaps -> separate lineages)
gap_rows = []
for fran, sub in df.groupby("fran_id"):
    for tid, s2 in sub.groupby("team_id"):
        yrs = sorted(s2["year_id"].unique())
        gaps = [y for a, b in zip(yrs, yrs[1:]) for y in range(a + 1, b) ]
        if gaps:
            gap_rows.append((fran, tid, yrs[0], yrs[-1], gaps))
print(f"\nteam_ids with internal season gaps: {len(gap_rows)}")
for r in gap_rows:
    print(f"  fran={r[0]} team={r[1]} span={r[2]}-{r[3]} missing={r[4]}")

# fran_id with disjoint team-id timeline (two true lineages sharing a fran_id)
print("\n--- fran_id season-continuity check (team_id timeline within fran) ---")
for fran, sub in df.groupby("fran_id"):
    tl = sub.groupby("team_id")["year_id"].agg(["min", "max"]).sort_values("min")
    ids = list(tl.itertuples())
    for a, b in zip(ids, ids[1:]):
        if b.min > a.max + 1:
            print(f"  fran={fran}: GAP between {a.Index} (..{a.max}) and {b.Index} ({b.min}..)")

sec("CHECK 4b: FRANCHISE CONTINUITY MAP (one row per fran lineage)")
for fran, sub in df.groupby("fran_id"):
    tl = sub.groupby("team_id")["year_id"].agg(["min", "max"]).sort_values("min")
    chain = " -> ".join(f"{t} [{int(a)}-{int(b)}]" for t, a, b in tl.itertuples(index=True))
    print(f"{fran}: {chain}")

# ---------------------------------------------------------------- check 5
sec("CHECK 5: same-day duplicates + games per day")
dupday = df.groupby(["team_id", "date_game"]).size()
print(f"(team_id, date_game) pairs appearing >1 time: {int((dupday > 1).sum())}")
if (dupday > 1).sum():
    print(dupday[dupday > 1].head(20).to_string())
per_day = df.groupby("date_game")["game_id"].nunique()
print(f"distinct game dates: {len(per_day)}; games/day mean={per_day.mean():.2f} "
      f"median={per_day.median():.0f} max={per_day.max()} on {per_day.idxmax()}")
print("games/day top 10:")
print(per_day.sort_values(ascending=False).head(10).to_string())

# ---------------------------------------------------------------- check 6
sec("CHECK 6: neutral site + notes census")
print("game_location domain (again, explicit):", dict(df["game_location"].value_counts(dropna=False)))
nt = df["notes"]
nn_t = nt.notna() & (nt.astype(str).str.strip() != "")
print(f"notes non-empty rows: {int(nn_t.sum())} ({100 * nn_t.mean():.3f}%)")
print("notes value_counts (top 30):")
print(nt[nn_t].value_counts().head(30).to_string())
print("\nnotes samples (first 15 distinct):")
print(pd.DataFrame({"game_id": df.loc[nn_t, "game_id"], "date": df.loc[nn_t, "date_game"],
                    "notes": nt[nn_t]}).drop_duplicates("notes").head(15).to_string())

# ---------------------------------------------------------------- check 7
sec("CHECK 7: nulls, duplicates, integrity")
print("null counts per column:")
print(df.isna().sum().to_string())
dup_gt = df.duplicated(subset=["game_id", "team_id"]).sum()
print(f"\nduplicate (game_id, team_id) rows: {int(dup_gt)}")
dup_full = df.duplicated().sum()
print(f"fully duplicated rows: {int(dup_full)}")
print(f"games with both rows same location: {chk['location OTHER (both H or both A)']}")
print(f"games with both rows same result:   {chk['result OTHER']}")
print(f"pts mirror violations: {chk['pts mirror violated (pts_a != opp_pts_b)']}")
print(f"pts range: min={df['pts'].min()} max={df['pts'].max()}")
print(f"games with pts==0 (any row): {int((df['pts'] == 0).sum())}")
if (df["pts"] == 0).sum():
    z = df[df["pts"] == 0]
    print(z[["game_id", "date_game", "team_id", "fran_id", "pts", "opp_pts",
             "game_location", "notes"]].head(20).to_string())
print(f"games with pts>190: {int((df['pts'] > 190).sum())}")
print(df[df["pts"] > 190][["game_id", "date_game", "team_id", "pts", "opp_pts"]].head(10).to_string())
print(f"win_equiv range: {df['win_equiv'].min():.4f} .. {df['win_equiv'].max():.4f}")
print(f"seasongame range: {df['seasongame'].min()} .. {df['seasongame'].max()}")

# seasongame sanity: strictly increasing by 1 within (team_id, year_id)?
sg = df.sort_values(["team_id", "year_id", "_date", "gameorder"]).groupby(["team_id", "year_id"])["seasongame"]
first_sg = sg.first()
seq_ok = (first_sg == 1).mean()
maxsg = sg.max()
print(f"team-seasons with first seasongame==1: {100 * seq_ok:.2f}% "
      f"({int((first_sg != 1).sum())} violations of {(~first_sg.isna()).sum()})")
print(f"max seasongame seen: {maxsg.max()} (team-season {maxsg.idxmax()})")

# ---------------------------------------------------------------- check 8
sec("CHECK 8: playoff structure")
po_rows = df[df["is_playoffs"] == 1]
print(f"playoff rows total = {len(po_rows)}; playoff games = {po_rows['game_id'].nunique()}")
print("\nplayoff games per season:")
print(per_season["po_games"].to_string())
odd = per_season[(per_season["po_games"] < 10) | (per_season["po_games"] > 130)]
print(f"\nseasons with playoff games <10 or >130: {len(odd)}")
if len(odd):
    print(odd[["po_games", "teams"]].to_string())
# check a playoff series count sanity for 2015: 15 series
lg2015 = df[(df["year_id"] == 2015) & (df["is_playoffs"] == 1)]
print(f"\n2015 playoff games: {lg2015['game_id'].nunique()}")

# ---------------------------------------------------------------- check 9
sec("CHECK 9: 538 elo/forecast columns (cross-check only, not our model)")
print(f"elo_i:    min={df['elo_i'].min():.1f} max={df['elo_i'].max():.1f} mean={df['elo_i'].mean():.1f}")
print(f"opp_elo_i min={df['opp_elo_i'].min():.1f} max={df['opp_elo_i'].max():.1f}")
era = df.assign(de=pd.cut(df["year_id"], [1946, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2015],
                          right=True)).groupby("de", observed=True)["elo_i"].agg(["min", "max", "mean"])
print("\nelo_i by era:")
print(era.to_string(float_format=lambda x: f"{x:.1f}"))
print(f"\nforecast: min={df['forecast'].min():.6f} max={df['forecast'].max():.6f}")
print(f"forecast complementarity across game pairs: max dev={chk['forecast complementarity: max |f_a+f_b-1|']:.3e}, "
      f"mean dev={chk['forecast complementarity: mean |f_a+f_b-1|']:.3e}")
print(f"elo_n range: {df['elo_n'].min():.1f} .. {df['elo_n'].max():.1f}")

# season-start carryover: (elo_first_game_of_season - 1500) / (elo_last_game_prev_season - 1500)
df = df.sort_values(["team_id", "year_id", "_date", "gameorder"])
rows = []
for (tid, yr), s in df.groupby(["team_id", "year_id"]):
    if yr <= df["year_id"].min() + 1:
        continue
    s_prev = df[(df["team_id"] == tid) & (df["year_id"] == yr - 1)]
    if s_prev.empty:
        continue
    elo_first = s.sort_values(["_date", "gameorder"]).iloc[0]["elo_i"]
    elo_last_prev = s_prev.sort_values(["_date", "gameorder"]).iloc[-1]["elo_i"]
    den = elo_last_prev - 1500.0
    if abs(den) > 5.0:
        rows.append((tid, yr, elo_first, elo_last_prev, (elo_first - 1500.0) / den))
car = pd.DataFrame(rows, columns=["team_id", "year_id", "elo_first", "elo_last_prev", "factor"])
print(f"\nseason-boundary carryover: {len(car)} team-seasons with prior history "
      f"(excluded |elo_last-1500|<=5)")
print(f"carryover factor: median={car['factor'].median():.4f} mean={car['factor'].mean():.4f} "
      f"p10={car['factor'].quantile(0.1):.4f} p90={car['factor'].quantile(0.9):.4f}")
byyear = car.groupby("year_id")["factor"].median()
print("\nmedian carryover factor by season:")
print(byyear.to_string(float_format=lambda x: f"{x:.3f}"))

# ---------------------------------------------------------------- check 10
sec("CHECK 10: COVID/bubble era rows (2020) — expected absent given 2015 end")
mask20 = (df["_date"] >= "2020-01-01") & (df["_date"] <= "2021-12-31")
print(f"rows dated 2020-01-01..2021-12-31: {int(mask20.sum())}")
mask_aug15 = (df["_date"] >= "2015-07-01")
print(f"rows dated on/after 2015-07-01 (offseason+): {int(mask_aug15.sum())}")
print(f"=> COVID/bubble audit: NOT_RUN / NOT_APPLICABLE — file ends "
      f"{df['_date'].max().date()}; 2020 bubble season NOT in this dataset.")

sec("SUMMARY LINE (for handoff)")
print(f"rows={len(df)}, games={n_games}, seasons={per_season.index.min()}-{per_season.index.max()}, "
      f"last_date={df['_date'].max().date()}, distinct team_id={df['team_id'].nunique()}, "
      f"distinct fran_id={df['fran_id'].nunique()}, "
      f"pts_mirror_violations={chk['pts mirror violated (pts_a != opp_pts_b)']}, "
      f"same_day_dupes={int((dupday > 1).sum())}, "
      f"carryover_median={car['factor'].median():.4f}")
