"""A7_PRELAUNCH_R2 probes (R2-9). Read-only on audited code; writes only here.
1) Designed-null bit-identity on MY OWN synthetic stream via frozen arms.py.
2) Doctored 2019-row cap probe against T_SELECT load filters.
Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python only.
"""
import hashlib, importlib.util, json, sys
import numpy as np

ARMS = "/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration/lanes/T_SELECT/arms.py"
PIN = "19dddd3ff2bec808e549981473e0523b4178cfd8c7c0db7c08b7e41a86d7d3e8"
got = hashlib.sha256(open(ARMS, "rb").read()).hexdigest()
assert got == PIN, f"arms.py drifted: {got}"
spec = importlib.util.spec_from_file_location("a7r2_arms", ARMS)
arms = importlib.util.module_from_spec(spec); sys.modules["a7r2_arms"] = arms
spec.loader.exec_module(arms)
print("arms sha256 pin asserted:", got)

# ---- my own synthetic stream (distinct generator: AJ lineages, 2025-2026) ----
import datetime as dt
def ns(y, m, d, h): return int(dt.datetime(y, m, d, h, tzinfo=dt.timezone.utc).timestamp()) * 10**9
rows = []  # (kickoff_ns, home, away, s_home, season, week, gid, is_neutral, is_reg)
def add(ko, h, a, sh, season, week, gid, neutral=False, reg=True):
    rows.append(dict(kickoff_ns=ko, home=h, away=a, s_home=sh, season=season,
                     week=week, game_id=gid, is_neutral=neutral, is_reg=reg))
# season 2025: 8 games incl. same-kickoff batch, tie, neutral, rest-day short week
add(ns(2025,9, 5,17), "AJ1","AJ2",1.0,2025,1,"AJ_S25_W1_A")
add(ns(2025,9, 5,17), "AJ3","AJ4",0.0,2025,1,"AJ_S25_W1_B")           # same-kickoff batch
add(ns(2025,9,12,18), "AJ5","AJ1",0.5,2025,2,"AJ_S25_W2_A")           # tie
add(ns(2025,9,15,18), "AJ2","AJ3",1.0,2025,2,"AJ_S25_W2_B",neutral=True)  # neutral
add(ns(2025,9,19,17), "AJ4","AJ6",1.0,2025,3,"AJ_S25_W3_A")
add(ns(2025,9,26,17), "AJ6","AJ5",0.0,2025,4,"AJ_S25_W4_A")
add(ns(2025,10,3,17), "AJ1","AJ5",1.0,2025,5,"AJ_S25_W5_A")
add(ns(2025,10,10,17), "AJ3","AJ2",0.0,2025,6,"AJ_S25_W6_A")
# season 2026: exercises lazy reversion + C3 prior boundary + short-rest away
add(ns(2026,9,11,17), "AJ2","AJ6",1.0,2026,1,"AJ_S26_W1_A")
add(ns(2026,9,11,17), "AJ4","AJ3",0.0,2026,1,"AJ_S26_W1_B")
add(ns(2026,9,14,17), "AJ5","AJ3",1.0,2026,2,"AJ_S26_W2_A")           # 3-day rest away (short)
add(ns(2026,9,21,17), "AJ6","AJ4",0.5,2026,3,"AJ_S26_W3_A")

rows.sort(key=lambda r: (r["kickoff_ns"], r["game_id"]))
gs = arms.GameSet(
    df=None,
    kickoff_ns=np.array([r["kickoff_ns"] for r in rows], dtype=np.int64),
    kickoff_date=np.array([dt.datetime.fromtimestamp(r["kickoff_ns"]/1e9, dt.timezone.utc).date().isoformat() for r in rows], dtype=object),
    home=np.array([r["home"] for r in rows], dtype=object),
    away=np.array([r["away"] for r in rows], dtype=object),
    s_home=np.array([r["s_home"] for r in rows], dtype=float),
    y_bin=np.array([0.0 if r["s_home"] == 0.5 else r["s_home"] for r in rows], dtype=float),
    is_tie=np.array([r["s_home"] == 0.5 for r in rows], dtype=bool),
    is_reg=np.array([r["is_reg"] for r in rows], dtype=bool),
    is_neutral=np.array([r["is_neutral"] for r in rows], dtype=bool),
    season=np.array([r["season"] for r in rows], dtype=np.int64),
    week=np.array([r["week"] for r in rows], dtype=np.int64),
    game_id=np.array([r["game_id"] for r in rows], dtype=object),
    quarantined_columns=[], n_dropped_over_ceiling=0, n_pre_dropped=0,
)

recs = arms.replay_elo(gs)
b1 = np.array([r.e_home for r in recs], dtype=float)
res = {"n_rows": len(rows), "seasons": [2025, 2026],
       "arms_sha256": got}

# C1_B000 (beta=0): p = sig(((r_h - r_a) - 0*(adj_h - adj_a))/400) per select.py p_stream
c1_null = np.array([arms.sig(((r.r_home - r.r_away) - 0.0 * (r.adj_home - r.adj_away)) / arms.ELO_SCALE) for r in recs], dtype=float)
res["C1_B000_max_abs_dp"] = float(np.max(np.abs(c1_null - b1)))
res["C1_B000_bytes_equal"] = c1_null.tobytes() == b1.tobytes()
# C1_B025 power check (null not vacuous)
c1_b025 = np.array([arms.sig(((r.r_home - r.r_away) - 25.0 * (r.adj_home - r.adj_away)) / arms.ELO_SCALE) for r in recs], dtype=float)
res["C1_B025_max_abs_dp_nonzero"] = float(np.max(np.abs(c1_b025 - b1)))
# C2_NULL (lam=0, h=0): frozen replay_c2
c2_null = arms.replay_c2(recs, 0.0, arms.GRID_C2_GAMMA_D.get("1O3", 1.0/3.0), 0.0)
res["C2_NULL_max_abs_dp"] = float(np.max(np.abs(c2_null - b1)))
res["C2_NULL_bytes_equal"] = np.asarray(c2_null).tobytes() == b1.tobytes()
# C2 with h=25 power check
c2_h25 = arms.replay_c2(recs, 0.0, 1.0/3.0, 25.0)
res["C2_h25_max_abs_dp_nonzero"] = float(np.max(np.abs(c2_h25 - b1)))
# C3_T000: replay_elo with a non-trivial z_table and theta=0.0
z_tab = {(2026, lg): v for lg, v in {"AJ1": 0.9, "AJ2": -0.4, "AJ3": 0.2, "AJ4": -1.1, "AJ5": 0.7, "AJ6": -0.3}.items()}
recs_c3t0 = arms.replay_elo(gs, z_table=z_tab, theta=0.0)
c3_null = np.array([r.e_home for r in recs_c3t0], dtype=float)
res["C3_T000_max_abs_dp"] = float(np.max(np.abs(c3_null - b1)))
res["C3_T000_bytes_equal"] = c3_null.tobytes() == b1.tobytes()
# C3_T050 power check (prior must move p)
recs_c3t50 = arms.replay_elo(gs, z_table=z_tab, theta=50.0)
c3_t50 = np.array([r.e_home for r in recs_c3t50], dtype=float)
res["C3_T050_max_abs_dp_nonzero"] = float(np.max(np.abs(c3_t50 - b1)))
# C4_D000: p = sig(((r_h - r_a) - 0*short)/400)
c4_null = np.array([arms.sig(((r.r_home - r.r_away) - 0.0 * (1.0 if (r.rest_days_away is not None and r.rest_days_away <= 6) else 0.0)) / arms.ELO_SCALE) for r in recs], dtype=float)
res["C4_D000_max_abs_dp"] = float(np.max(np.abs(c4_null - b1)))
res["C4_D000_bytes_equal"] = c4_null.tobytes() == b1.tobytes()
# C4_D025 power check
c4_d025 = np.array([arms.sig(((r.r_home - r.r_away) - 25.0 * (1.0 if (r.rest_days_away is not None and r.rest_days_away <= 6) else 0.0)) / arms.ELO_SCALE) for r in recs], dtype=float)
res["C4_D025_max_abs_dp_nonzero"] = float(np.max(np.abs(c4_d025 - b1)))
res["designed_nulls_all_zero"] = (res["C1_B000_max_abs_dp"] == 0.0 and res["C2_NULL_max_abs_dp"] == 0.0
    and res["C3_T000_max_abs_dp"] == 0.0 and res["C4_D000_max_abs_dp"] == 0.0)
res["designed_nulls_bytes_equal_all"] = all(res[k] for k in ("C1_B000_bytes_equal","C2_NULL_bytes_equal","C3_T000_bytes_equal","C4_D000_bytes_equal"))

# ---- doctored 2019-row cap probe vs T_SELECT caps ----
import pandas as pd, tempfile, os
csv = os.path.join(tempfile.mkdtemp(), "doctored.csv")
cols = ["game_id","season","week","game_type","gameday","gametime","home_team","away_team",
        "home_score","away_score","location","spread_line","home_moneyline"]
data = [
 ["AJ_OK_2018_A",2018,1,"REG","2018-09-07","13:00","AJ1","AJ2",24,17,"Home",3.0,-150],
 ["AJ_OK_2018_B",2018,1,"REG","2018-09-08","13:00","AJ3","AJ4",10,10,"Home",1.5,-110],
 ["AJ_BAD_2019",2019,1,"REG","2019-09-06","13:00","AJ5","AJ6",21,14,"Home",2.5,-120],  # doctored: SPENT season
]
pd.DataFrame(data, columns=cols).to_csv(csv, index=False)
gs2 = arms.load_games(csv)
leaked = gs2.df["season"].max() > arms.SEASON_MAX_GAMES
res["probe_2019"] = {
    "n_rows_in_csv": 3,
    "n_dropped_over_ceiling": int(gs2.n_dropped_over_ceiling),
    "rows_surviving": int(len(gs2.df)),
    "max_season_surviving": int(gs2.df["season"].max()),
    "season_leak": bool(leaked),
    "odds_columns_quarantined": gs2.quarantined_columns,
    "verdict": "2019 row DROPPED at load; 0 rows > 2018 survive" if (not leaked and len(gs2.df) == 2 and gs2.n_dropped_over_ceiling == 1) else "FAIL",
}
# backstop assert demonstration on an unfiltered frame (loud assertion exists)
try:
    bad = pd.DataFrame({"season": [2019], "game_type": ["REG"], "home_score": [1.0], "away_score": [0.0]})
    m = int(bad["season"].max())
    assert m <= arms.SEASON_MAX_GAMES, "season > SEASON_MAX_GAMES leaked"
    res["probe_2019"]["backstop"] = "assert did NOT fire (unexpected)"
except AssertionError as e:
    res["probe_2019"]["backstop"] = f"loud backstop fired: {e}"

out = "/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration/lanes/A7_PRELAUNCH_R2/tmp/r2_9_results.json"
open(out, "w").write(json.dumps(res, indent=2, sort_keys=True) + "\n")
print(json.dumps(res, indent=2, sort_keys=True))
ok = res["designed_nulls_all_zero"] and res["designed_nulls_bytes_equal_all"] and res["probe_2019"]["verdict"].startswith("2019 row DROPPED")
print("R2_9_OVERALL:", "PASS" if ok else "FAIL")
