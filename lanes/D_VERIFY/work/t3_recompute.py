#!/usr/bin/env python
"""D_VERIFY T3 — independent recompute of the feature table (own as-of implementation).

Written from FEATURE_SPEC.md alone. Deliberately different code path from
build_features.py: per-(team,season) game lists built by dict accumulation, window
selection by explicit index slicing on a sorted python list, all sums via python loops.
"""
import json, math, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

DATA = os.path.expanduser("~/.my-quantitative-data")
WORK = "/Users/hoangminhlong/my-quantitative/.worktrees/nfl-playerfeat-prep-v1/integration/lanes/D_VERIFY/work"
ET = ZoneInfo("America/New_York")
SEASONS = (2024, 2025, 2026)

# ---------------------------------------------------------------- load, my own way
games = pd.read_csv(f"{DATA}/nfl-ng-prep-v1/raw_schedules_r1_20261005/games.csv")
games = games[games["season"].isin(SEASONS)]

def kickoff_utc(row):
    naive = datetime.strptime(f"{row['gameday']} {row['gametime']}", "%Y-%m-%d %H:%M")
    return naive.replace(tzinfo=ET).astimezone(timezone.utc)

gk = {}
for r in games.itertuples(index=False):
    gk[r.game_id] = kickoff_utc(r._asdict() if hasattr(r, "_asdict") else r)

# rebuild itertuples field access safe: use dict rows
gk = {}
gmeta = {}
for r in games.to_dict("records"):
    naive = datetime.strptime(f"{r['gameday']} {r['gametime']}", "%Y-%m-%d %H:%M")
    ko = naive.replace(tzinfo=ET).astimezone(timezone.utc)
    gk[r["game_id"]] = ko
    gmeta[r["game_id"]] = r

stats_parts = []
for y in SEASONS:
    s = pd.read_parquet(f"{DATA}/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_{y}.parquet")
    stats_parts.append(s[s["player_id"].notna()])
stats = pd.concat(stats_parts, ignore_index=True)
stat_gids = set(stats["game_id"])

snap_parts = []
for y in (2025, 2026):
    snap_parts.append(pd.read_parquet(f"{DATA}/playerdata-prep-v1/nfl/raw_snap_counts/snap_counts_{y}.parquet"))
snap = pd.concat(snap_parts, ignore_index=True)
snap = snap[snap["game_id"].isin(gk)]

cw = pd.read_parquet(f"{DATA}/playerfeat-prep-v1/nfl/raw_players/players.parquet")
pfr2gsis = {}
for r in cw[cw["gsis_id"].notna()].drop_duplicates("gsis_id").to_dict("records"):
    if r["pfr_id"] is not None and not (isinstance(r["pfr_id"], float) and math.isnan(r["pfr_id"])):
        pfr2gsis[r["pfr_id"]] = r["gsis_id"]

# per (season, team) prior-game bookkeeping, built by my own accumulation
team_games = {}   # (season, team) -> list of (ko, game_id) in corpus, unsorted
qb_rows = {}      # (season, team) -> list of dicts
skill_rows = {}
snap_rows = {}
for r in stats.to_dict("records"):
    ko = gk[r["game_id"]]
    key = (int(r["season"]), r["team"])
    if r["position"] == "QB":
        qb_rows.setdefault(key, []).append((ko, r["game_id"], r))
    if r["position_group"] in ("WR", "RB", "TE"):
        skill_rows.setdefault(key, []).append((ko, r["game_id"], r))
for gid, meta in gmeta.items():
    if gid not in stat_gids:
        continue
    for t in (meta["away_team"], meta["home_team"]):
        team_games.setdefault((int(meta["season"]), t), []).append((gk[gid], gid))
for r in snap.to_dict("records"):
    if r["game_id"] not in gk:
        continue
    snap_rows.setdefault((int(r["season"]), r["team"]), []).append((gk[r["game_id"]], r))

def qb_agg(rows, gids):
    yds = td = i = att = epa = 0.0
    for _, _, r in rows:
        if r["game_id"] not in gids:
            continue
        yds += float(r["passing_yards"]) if pd.notna(r["passing_yards"]) else 0.0
        td += float(r["passing_tds"]) if pd.notna(r["passing_tds"]) else 0.0
        i += float(r["passing_interceptions"]) if pd.notna(r["passing_interceptions"]) else 0.0
        att += float(r["attempts"]) if pd.notna(r["attempts"]) else 0.0
        epa += float(r["passing_epa"]) if pd.notna(r["passing_epa"]) else 0.0
    return yds, td, i, att, epa

def skill_agg(rows, gids):
    usage = {}
    tot = 0.0
    for _, _, r in rows:
        if r["game_id"] not in gids:
            continue
        u = (float(r["targets"]) if pd.notna(r["targets"]) else 0.0) + \
            (float(r["carries"]) if pd.notna(r["carries"]) else 0.0)
        usage[r["player_id"]] = usage.get(r["player_id"], 0.0) + u
        tot += u
    return usage, tot

def topn(usage, n):
    items = sorted(usage.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[:n]

def g3_window(rows, tko):
    """rows: (ko, rec). Returns (n_snap_prior, window recs list, recent ko)."""
    kicks = sorted({ko for ko, _ in rows})
    prior = [k for k in kicks if k < tko]
    if not prior:
        return 0, [], None
    win = prior[-3:]
    wset = set(win)
    recs = [r for ko, r in rows if ko in wset]
    return len(prior), recs, win[-1]

# ------------------------------------------------------------------ full-table recount
tab = pd.read_parquet(f"{DATA}/nfl-playerfeat-prep-v1/features/nfl_playerfeat_table_v1.parquet")

full = {"rows": len(tab), "kickoff_str_mismatch": 0, "rest_mismatch": 0,
        "g3_n_mismatch": 0, "g3_nullflag_mismatch": 0}
sample_ids = set()
rest_dev_max = 0.0
for r in tab.to_dict("records"):
    gid, season, team = r["game_id"], int(r["season"]), r["team"]
    tko = gk[gid]
    ko_str = tko.strftime("%Y-%m-%dT%H:%M:%SZ")
    if ko_str != r["kickoff_utc"]:
        full["kickoff_str_mismatch"] += 1
    prior_gids = {g for (ko, g) in team_games.get((season, team), []) if ko < tko}
    n_prior = len(prior_gids)
    if n_prior != int(r["n_prior_games_used"]):
        full["kickoff_str_mismatch"] += 1
    exp_rest = (tko - max(ko for ko, g in team_games.get((season, team), []) if ko < tko)).total_seconds() / 86400.0 if n_prior else None
    got_rest = r["rest_days"]
    if exp_rest is None:
        if not pd.isna(got_rest):
            full["rest_mismatch"] += 1
    else:
        rest_dev_max = max(rest_dev_max, abs(float(got_rest) - exp_rest))
        if abs(float(got_rest) - exp_rest) > 1e-9:
            full["rest_mismatch"] += 1
    # G3 full recount
    rows3 = snap_rows.get((season, team), [])
    n_sp, _, _ = g3_window(rows3, tko)
    if n_sp != (int(r["g3_n_snap_prior_games"]) if pd.notna(r["g3_n_snap_prior_games"]) else 0):
        full["g3_n_mismatch"] += 1
    # pfr-null flag recount
    if n_sp:
        _, recs, _ = g3_window(rows3, tko)
        nulls = sum(1 for rec in recs if pfr2gsis.get(rec["pfr_player_id"]) is None)
        exp_flag = 1 if nulls > 0 else 0
    else:
        exp_flag = 0
    if exp_flag != int(r["flag_g3_pfr_null_excluded"]):
        full["g3_nullflag_mismatch"] += 1

print("full-table as-of recount:", full, "max rest_days abs dev:", rest_dev_max)

# ---------------------------------------------------------------- sampled deep recompute
def recompute_row(gid, side):
    meta = gmeta[gid]
    season = int(meta["season"])
    tko = gk[gid]
    team, opp = (meta["away_team"], meta["home_team"]) if side == "away" else \
                (meta["home_team"], meta["away_team"])
    key = (season, team)
    priors = sorted([p for p in team_games.get(key, []) if p[0] < tko])
    n_prior = len(priors)
    out = {"game_id": gid, "side": side, "team": team, "opponent": opp,
           "season": season, "week": int(meta["week"]), "game_type": meta["game_type"],
           "kickoff_utc": tko.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "n_prior_games_used": n_prior,
           "rest_days": (tko - priors[-1][0]).total_seconds() / 86400.0 if n_prior else None,
           "flag_no_prior_in_corpus": int(n_prior == 0),
           "flag_g1_window_truncated_k3": int(0 < n_prior < 3),
           "flag_g1_window_truncated_k5": int(0 < n_prior < 5)}
    qbr = qb_rows.get(key, [])
    skr = skill_rows.get(key, [])
    if n_prior:
        prior_gids = {g for _, g in priors}
        # std over all priors
        sy, _, _, _, se = qb_agg(qbr, prior_gids)
        std_yds, std_epa = sy / n_prior, se / n_prior
        out["qb_yds_std_pg"], out["qb_epa_std_pg"] = std_yds, std_epa
        for k in (3, 5):
            win_gids = {g for _, g in priors[-k:]}
            n_used = len(win_gids)
            y, td, i, att, epa = qb_agg(qbr, win_gids)
            out[f"qb_yds_k{k}"] = y
            out[f"qb_td_k{k}"] = td
            out[f"qb_int_k{k}"] = i
            out[f"qb_att_k{k}"] = att
            out[f"qb_epa_k{k}"] = epa
            out[f"qb_ypa_k{k}"] = y / att if att > 0 else None
            out[f"qb_epa_pa_k{k}"] = epa / att if att > 0 else None
            out[f"qb_yds_form_k{k}"] = y / n_used - std_yds
            out[f"qb_epa_form_k{k}"] = epa / n_used - std_epa
        for k, share_n, scol in ((3, 3, "k3"), (5, 5, "k5")):
            win_gids = {g for _, g in priors[-k:]}
            usage, tot = skill_agg(skr, win_gids)
            n_used = len(win_gids)
            if scol == "k3":
                if tot <= 0:
                    out["skill_top3_share_k3"] = out["skill_hhi_k3"] = out["skill_usage_pg_k3"] = None
                    out["flag_g2_zero_usage"] = 1
                    out["skill_top5_share_k5"] = None
                    break
                shares = [u / tot for _, u in topn(usage, 10 ** 6)]
                out["skill_top3_share_k3"] = sum(shares[:3])
                out["skill_hhi_k3"] = sum(s * s for s in shares)
                out["skill_usage_pg_k3"] = tot / n_used
            else:
                if tot <= 0:
                    out["skill_top5_share_k5"] = None
                    out["flag_g2_zero_usage"] = 1
                    break
                shares = [u / tot for _, u in topn(usage, 10 ** 6)]
                out["skill_top5_share_k5"] = sum(shares[:5])
        if "flag_g2_zero_usage" not in out:
            out["flag_g2_zero_usage"] = 0
    else:
        for c in ("qb_yds_std_pg", "qb_epa_std_pg"):
            out[c] = None
        for k in (3, 5):
            for m in ("yds", "td", "int", "att", "epa", "ypa", "epa_pa", "yds_form", "epa_form"):
                out[f"qb_{m}_k{k}"] = None
        for c in ("skill_top3_share_k3", "skill_hhi_k3", "skill_usage_pg_k3", "skill_top5_share_k5"):
            out[c] = None
        out["flag_g2_zero_usage"] = 0
    # G3
    rows3 = snap_rows.get(key, [])
    n_sp, recs, recent_ko = g3_window(rows3, tko)
    if n_sp == 0:
        out["g3_n_snap_prior_games"] = None
        out["g3_top5_absent_share_recent"] = None
        out["g3_top5_newly_absent_count"] = None
        out["flag_g3_no_snap_prior"] = 1
        out["flag_g3_pfr_null_excluded"] = 0
    else:
        out["g3_n_snap_prior_games"] = n_sp
        n_w = min(3, n_sp)
        nulls = sum(1 for rec in recs if pfr2gsis.get(rec["pfr_player_id"]) is None)
        out["flag_g3_pfr_null_excluded"] = int(nulls > 0)
        res = []
        for rec in recs:
            g = pfr2gsis.get(rec["pfr_player_id"])
            if g is None:
                continue
            s = (float(rec["offense_snaps"]) if pd.notna(rec["offense_snaps"]) else 0.0) + \
                (float(rec["defense_snaps"]) if pd.notna(rec["defense_snaps"]) else 0.0)
            res.append((g, s, rec))
        tot_by = {}
        for g, s, _ in res:
            tot_by[g] = tot_by.get(g, 0.0) + s
        grand = sum(tot_by.values())
        if grand <= 0:
            out["g3_top5_absent_share_recent"] = None
            out["g3_top5_newly_absent_count"] = None
            out["flag_g3_no_snap_prior"] = 0
        else:
            top = sorted(tot_by.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
            rec_by = {}
            for g, s, rec in res:
                if gk[rec["game_id"]] == recent_ko:
                    rec_by[g] = rec_by.get(g, 0.0) + s
            n_present = n_absent = n_newly = 0
            for g, tot in top:
                if tot <= 0:
                    continue
                rs = rec_by.get(g, 0.0)
                n_present += 1
                if rs < 0.5 * (tot / n_w):
                    n_absent += 1
                if rs == 0.0:
                    n_newly += 1
            out["g3_top5_absent_share_recent"] = n_absent / n_present if n_present else None
            out["g3_top5_newly_absent_count"] = float(n_newly) if n_present else None
            out["flag_g3_no_snap_prior"] = 0
    return out

def compare(rec, tab_row):
    diffs = []
    for col, mine in rec.items():
        if col in ("game_id", "side"):
            continue
        theirs = tab_row.get(col)
        if mine is None:
            if not (theirs is None or pd.isna(theirs)):
                diffs.append(f"{col}: mine=None theirs={theirs!r}")
            continue
        if isinstance(mine, str) or isinstance(theirs, str):
            if str(mine) != str(theirs):
                diffs.append(f"{col}: mine={mine!r} theirs={theirs!r}")
            continue
        if isinstance(mine, float) or isinstance(theirs, (int, float)):
            a, b = float(mine), float(theirs)
            tol = 1e-9 if a < 100 else 1e-7
            if abs(a - b) > tol:
                diffs.append(f"{col}: mine={a!r} theirs={b!r}")
        else:
            if mine != theirs:
                diffs.append(f"{col}: mine={mine!r} theirs={theirs!r}")
    return diffs

tab_idx = {(r["game_id"], r["side"]): r for r in tab.to_dict("records")}

# pick samples from the table itself
tab_ids = set(tab["game_id"])
opener = sorted([g for g in tab_ids if g.startswith("2026_01")])[0]
opener_row = [r for r in tab.to_dict("records") if r["game_id"] == opener][0]
lv_rows = [r for r in tab.to_dict("records")
           if r["season"] == 2026 and r["team"] == "LV"
           and int(r["flag_g3_pfr_null_excluded"]) == 1]
lv_pick = lv_rows[0]
wk2_2025 = [r for r in tab.to_dict("records") if r["season"] == 2025 and int(r["week"]) == 2
            and int(r["flag_g3_no_snap_prior"]) == 0]
w2_pick = wk2_2025[0]

samples = [
    ("2024_11_KC_BUF", "home"),          # KC worked example (Mahomes prior-3)
    ("2024_07_KC_SF", "away"),           # bye-week fixture
    (opener, opener_row["side"]),        # neutral opener (no-prior)
    (lv_pick["game_id"], lv_pick["side"]),   # pfr-null G3 exclusion row
    (w2_pick["game_id"], w2_pick["side"]),   # n_w=1 G3 case (absent share 0.0)
    ("2026_04_PIT_CLE", "home"),         # S3 fixture, G3 computable 2026
]
# dedupe while preserving order
seen = set()
samples = [s for s in samples if not (s in seen or seen.add(s))]
while len(samples) < 6:
    for r in tab.to_dict("records"):
        c = (r["game_id"], r["side"])
        if c not in seen:
            samples.append(c)
            seen.add(c)
            break

all_ok = True
report = []
for gid, side in samples:
    mine = recompute_row(gid, side)
    tr = tab_idx[(gid, side)]
    diffs = compare(mine, tr)
    all_ok &= not diffs
    report.append({"game_id": gid, "side": side, "team": mine["team"],
                   "n_prior": mine["n_prior_games_used"],
                   "rest_days": mine["rest_days"],
                   "qb_yds_k3": mine.get("qb_yds_k3"), "qb_td_k3": mine.get("qb_td_k3"),
                   "qb_int_k3": mine.get("qb_int_k3"), "qb_att_k3": mine.get("qb_att_k3"),
                   "top3_share_k3": mine.get("skill_top3_share_k3"),
                   "g3_absent": mine.get("g3_top5_absent_share_recent"),
                   "g3_n": mine.get("g3_n_snap_prior_games"),
                   "flags": {c: mine[c] for c in
                             ("flag_no_prior_in_corpus", "flag_g1_window_truncated_k3",
                              "flag_g1_window_truncated_k5", "flag_g2_zero_usage",
                              "flag_g3_no_snap_prior", "flag_g3_pfr_null_excluded")},
                   "col_diffs": diffs})
    print(f"\nsample {gid}/{side} ({mine['team']}): n_prior={mine['n_prior_games_used']} "
          f"rest={mine['rest_days']} yds/td/int/att k3="
          f"{mine.get('qb_yds_k3')}/{mine.get('qb_td_k3')}/{mine.get('qb_int_k3')}/{mine.get('qb_att_k3')} "
          f"top3={mine.get('skill_top3_share_k3')} g3={mine.get('g3_top5_absent_share_recent')} "
          f"g3n={mine.get('g3_n_snap_prior_games')}")
    print(f"  -> {len(diffs)} column diffs {diffs if diffs else '(IDENTICAL)'}")

verdict = {"full_table": full, "rest_dev_max": rest_dev_max,
           "samples": report, "all_sample_ok": all_ok}
json.dump(verdict, open(f"{WORK}/t3_results.json", "w"), indent=2, default=str)
print("\nOVERALL T3:", "RECOMPUTE_MATCH" if (all_ok and all(v == 0 for k, v in full.items())) else "DIFFS_FOUND")
