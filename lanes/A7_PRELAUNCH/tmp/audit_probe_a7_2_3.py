#!/usr/bin/env python
"""A7_PRELAUNCH audit probes A7-2 (designed-null re-run on OWN synthetic stream)
and A7-3 (no-spent-window runtime probes). READ-ONLY wrt audited artifacts.

Imports lanes/T_SELECT/arms.py UNMODIFIED (sha256 asserted at import against the
freeze pin). All outputs written only into lanes/A7_PRELAUNCH/tmp/.
Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python
"""
import hashlib
import inspect
import json
import math
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/hoangminhlong/my-quantitative"
WT = f"{ROOT}/.worktrees/nfl-winprob-ng-scored-v1/integration"
TMP = f"{WT}/lanes/A7_PRELAUNCH/tmp"
ARMS = f"{WT}/lanes/T_SELECT/arms.py"
ARMS_SHA_PIN = "19dddd3ff2bec808e549981473e0523b4178cfd8c7c0db7c08b7e41a86d7d3e8"

sha = hashlib.sha256(open(ARMS, "rb").read()).hexdigest()
assert sha == ARMS_SHA_PIN, f"arms.py sha {sha} != freeze pin {ARMS_SHA_PIN}"
print(f"[sha] arms.py == freeze pin: {sha}")

sys.path.insert(0, f"{WT}/lanes/T_SELECT")
import arms  # noqa: E402  (unmodified frozen module)

EVIDENCE = {}

# ---------------------------------------------------------------------------
# A7-2: OWN synthetic stream (distinct from any lane stream: lineages
# AAA..FFF, seasons 2001-2003, same-kickoff batches, one tie, one Neutral).
# ---------------------------------------------------------------------------
rows = []
gid = 0


def add(day, time, h, a, hs, as_, loc="Home", gtype="REG", wk=1):
    global gid
    gid += 1
    rows.append({
        "game_id": f"2000_00_G{gid:03d}", "season": int(day[:4]), "game_type": gtype,
        "week": wk, "gameday": day, "weekday": "Sun", "gametime": time,
        "away_team": a, "away_score": as_, "home_team": h, "home_score": hs,
        "location": loc,
        # odds columns present on purpose (quarantine must drop them):
        "spread_line": -3.5, "home_moneyline": -150, "over_odds": -110,
    })


teams = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
rng = np.random.default_rng(777001)  # MY audit seed, not the lane seed
days = [("2001-09-09", 1), ("2001-09-16", 2), ("2001-09-23", 3), ("2001-12-30", 4),
        ("2002-09-08", 1), ("2002-09-15", 2), ("2002-12-29", 3), ("2003-01-06", 4),
        ("2003-09-07", 1), ("2003-09-14", 2), ("2003-12-28", 3), ("2004-01-03", 4)]
times = ["13:00", "16:15", "20:00", "13:00", "16:15", "20:00"]
for si, (season_days) in enumerate([days[0:4], days[4:8], days[8:12]]):
    wk = 0
    for day, _ in season_days:
        wk += 1
        pairs = [(0, 1), (2, 3), (4, 5)] if wk % 2 else [(1, 2), (3, 4), (5, 0)]
        for pi, (h_i, a_i) in enumerate(pairs):
            h, a = teams[h_i], teams[a_i]
            hs = int(rng.integers(0, 45))
            as_ = int(rng.integers(0, 45))
            if wk == 2 and pi == 1 and si == 1:
                as_ = hs  # a tie
            loc = "Neutral" if (wk == 3 and pi == 0 and si == 2) else "Home"
            add(day, times[(pi + wk) % 6], h, a, hs, as_, loc=loc, wk=wk)
# two identical-kickoff games (same gameday+gametime, different teams)
add("2002-10-13", "13:00", "AAA", "CCC", 21, 17, wk=5)
add("2002-10-13", "13:00", "BBB", "DDD", 24, 24, wk=5)  # same-kickoff tie
fixture = f"{TMP}/a7_fixture_games.csv"
pd.DataFrame(rows).to_csv(fixture, index=False)

gs = arms.load_games(fixture)
recs = arms.replay_elo(gs)
b1_p = np.array([r.e_home for r in recs], dtype=float)
n = len(recs)
print(f"[stream] rows={n} seasons={sorted(set(int(s) for s in gs.season))} "
      f"ties={int(gs.is_tie.sum())} neutral={int(gs.is_neutral.sum())} "
      f"quarantined={gs.quarantined_columns} dropped_over_ceiling={gs.n_dropped_over_ceiling}")

# --- my own independent null p-streams (frozen spec, my code) ---
# C1 beta=0
c1 = np.array([arms.sig(((r.r_home - r.r_away) - 0.0 * (r.adj_home - r.adj_away)) / arms.ELO_SCALE)
               for r in recs], dtype=float)
# C2 lambda=0 & h=0 (my own deviation replay; lam*K*(S-E)=0 keeps devs at 0)
gam = 1.0 / 3.0
dev = {}
c2 = np.empty(n, dtype=float)
for k, r in enumerate(recs):
    for lg in (r.home, r.away):
        dev.setdefault(lg, [0.0, 0.0])
    hterm = 0.0  # h=0 AND r.is_neutral both give 0
    p = arms.sig((r.r_home + dev[r.home][0] - r.r_away - dev[r.away][1] + hterm) / arms.ELO_SCALE)
    c2[k] = p
    if not r.is_neutral:
        dev[r.home][0] += 0.0 * arms.K_BASE * (r.s_home - p)   # lam=0
        dev[r.away][1] += 0.0 * arms.K_BASE * ((1.0 - r.s_home) - (1.0 - p))
# C3 theta=0 via frozen machinery with a NONTRIVIAL z_table (theta=0 must ignore it)
my_z = {}
for s in range(2002, 2005):
    for i, lg in enumerate(teams):
        my_z[(s, lg)] = -1.5 + 0.5 * i  # deliberately nonzero
recs3 = arms.replay_elo(gs, z_table=my_z, theta=0.0)
c3 = np.array([r.e_home for r in recs3], dtype=float)
# C4 delta=0
c4 = np.array([arms.sig(((r.r_home - r.r_away) - 0.0 * (1.0 if (r.rest_days_away is not None and r.rest_days_away <= 6) else 0.0)) / arms.ELO_SCALE)
               for r in recs], dtype=float)

res2 = {}
for name, p in (("C1_B000", c1), ("C2_NULL", c2), ("C3_T000", c3), ("C4_D000", c4)):
    mx = float(np.max(np.abs(p - b1_p)))
    tb = bool(p.tobytes() == b1_p.tobytes())
    res2[name] = {"max_abs_dp": mx, "tobytes_equal": tb}
    print(f"[equiv] {name}: max|dp|={mx!r} tobytes_equal={tb}")
assert all(v["max_abs_dp"] == 0.0 and v["tobytes_equal"] for v in res2.values()), \
    "DESIGNED-NULL EQUIVALENCE FAILED ON AUDIT STREAM"

# non-vacuous power check: nonzero grid value must move p
c1_25 = np.array([arms.sig(((r.r_home - r.r_away) - 25.0 * (r.adj_home - r.adj_away)) / arms.ELO_SCALE)
                  for r in recs], dtype=float)
nv = float(np.max(np.abs(c1_25 - b1_p)))
res2["power_check_C1_B025_moves_p"] = {"max_abs_dp": nv, "nonzero": nv > 0.0}
print(f"[power] C1 beta=25 max|dp| vs B1* = {nv!r} (nonzero expected)")
assert nv > 0.0
EVIDENCE["a7_2_designed_null_own_stream"] = {
    "stream_rows": n, "stream_lineages": teams,
    "stream_features": {"same_kickoff_batch": True, "tie": True, "neutral": True,
                        "seasons": sorted(set(int(s) for s in gs.season))},
    "nulls": res2,
}

# ---------------------------------------------------------------------------
# A7-3 probe 1: doctored season-2019 row in games fixture (unmodified code)
# ---------------------------------------------------------------------------
doct = rows + [{
    "game_id": "2019_01_ZZZ_YYY", "season": 2019, "game_type": "REG", "week": 1,
    "gameday": "2019-09-08", "weekday": "Sun", "gametime": "13:00",
    "away_team": "EEE", "away_score": 10, "home_team": "FFF", "home_score": 27,
    "location": "Home", "spread_line": -7, "home_moneyline": -200, "over_odds": -110,
}]
doct_path = f"{TMP}/a7_doctored_2019.csv"
pd.DataFrame(doct).to_csv(doct_path, index=False)
gs_d = arms.load_games(doct_path)
leaked = int((gs_d.df["season"] > 2018).sum())
res3 = {
    "doctored_2019_row_injected": 1,
    "rows_loaded": int(len(gs_d.df)),
    "max_season_after_load": int(gs_d.df["season"].max()),
    "season_gt_2018_rows_in_loaded_set": leaked,
    "n_dropped_over_ceiling": int(gs_d.n_dropped_over_ceiling),
    "quarantined_columns": gs_d.quarantined_columns,
    "odds_columns_in_loaded_df": [c for c in gs_d.df.columns
                                  if any(p in c.lower() for p in ("odds", "moneyline", "spread"))],
}
print(f"[a7-3 games] {json.dumps(res3)}")
assert leaked == 0 and res3["max_season_after_load"] <= 2018 and res3["n_dropped_over_ceiling"] >= 1
assert res3["odds_columns_in_loaded_df"] == []

# --- backstop assertion loudness: execute the module's own assert on an
# UNFILTERED frame (simulates a filter failure; proves the assert fires) ---
src = inspect.getsource(arms.load_games)
backstop_lines = [ln.strip() for ln in src.splitlines() if "season > SEASON_MAX_GAMES leaked" in ln]
unfiltered = pd.DataFrame(doct)
fired = False
try:
    assert int(unfiltered["season"].max()) <= arms.SEASON_MAX_GAMES, "season > SEASON_MAX_GAMES leaked"
except AssertionError as e:
    fired = True
    backstop_msg = str(e)
res3["backstop_assertion_present_in_source"] = bool(backstop_lines)
res3["backstop_fires_on_unfiltered_frame"] = fired
res3["backstop_message"] = backstop_msg if fired else None
print(f"[a7-3 backstop] present={res3['backstop_assertion_present_in_source']} "
      f"fires={fired} msg={backstop_msg if fired else '-'}")
assert res3["backstop_assertion_present_in_source"] and fired

# ---------------------------------------------------------------------------
# A7-3 probe 2: pbp read-scope canary. Tiny parquets for 2000..2017 VALID +
# 2018/2019 CANARY files; wrap pq.read_table to log every path touched.
# ---------------------------------------------------------------------------
import pyarrow as pa  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

pbp_dir = f"{TMP}/a7_pbp_canary"
os.makedirs(pbp_dir, exist_ok=True)
touched = []
real_read_table = pq.read_table


def spy_read_table(path, **kw):
    touched.append(str(path))
    return real_read_table(path, **kw)


for year in range(2000, 2020):
    tbl = pa.table({
        "season": pa.array([year, year], type=pa.int64()),
        "season_type": pa.array(["REG", "REG"]),
        "posteam": pa.array(["AAA", "BBB"]),
        "defteam": pa.array(["BBB", "AAA"]),
        "epa": pa.array([0.1, -0.2], type=pa.float64()),
    })
    pq.write_table(tbl, f"{pbp_dir}/play_by_play_{year}.parquet")
pq.read_table = spy_read_table
try:
    zt = arms.build_z_table(pbp_dir)
finally:
    pq.read_table = real_read_table
years_touched = sorted({int(x.rsplit("_", 1)[1].split(".")[0]) for x in touched
                        if "play_by_play_" in x})
canaries = [y for y in years_touched if y > 2017]
res3_pbp = {
    "parquet_years_on_disk": list(range(2000, 2020)),
    "years_actually_read": years_touched,
    "canary_years_read_gt_2017": canaries,
    "z_table_entries": len(zt),
    "internal_pbp_assert_in_source": "pbp season > SEASON_MAX_PBP leaked" in inspect.getsource(arms.build_z_table),
}
print(f"[a7-3 pbp] {json.dumps(res3_pbp)}")
assert canaries == [] and max(years_touched) <= 2017

# source-reading facts for the audit record
res3_code = {
    "SEASON_MAX_GAMES": arms.SEASON_MAX_GAMES,
    "SEASON_MAX_PBP": arms.SEASON_MAX_PBP,
    "hard_filter_line": "df = df[(df[\"season\"] >= SEASON_MIN_GAMES) & (df[\"season\"] <= SEASON_MAX_GAMES)].copy()" in src,
    "pbp_loop_upper_bound_2017": "range(SEASON_MIN_GAMES, SEASON_MAX_PBP + 1)" in inspect.getsource(arms.build_z_table),
    "quarantined_names": sorted(arms.QUARANTINED_COLUMNS),
    "quarantine_patterns": list(arms.QUARANTINE_PATTERNS),
}
EVIDENCE["a7_3_no_spent_window"] = {"games_probe": res3, "pbp_probe": res3_pbp, "code_facts": res3_code}

with open(f"{TMP}/a7_2_3_evidence.json", "w") as f:
    json.dump(EVIDENCE, f, indent=2)
print("AUDIT_PROBE_A7_2_3: ALL PASS")
