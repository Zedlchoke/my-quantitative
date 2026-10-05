#!/usr/bin/env python
"""A7-6 independent replay: recompute pooled inner LL for B0 / B1STAR / C1_B025 /
C3_T050 with MY OWN implementation from the raw stream — no lane code imported
(no arms.py, no select.py, no boot.py). Frozen spec implemented from the
protocol/freeze documents:
  TRAIN = seasons 2000..2018 of ~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv
  kickoff = gameday+gametime America/New_York -> UTC; order (kickoff, game_id)
  Elo init 1500, K=40, scale 400, HCA=0; lazy season reversion
  R <- 1500 + (2/3)(R-1500) [+ theta*z] at a lineage's first prediction of a
  new season; same-kickoff batches predicted pre-batch, updated post-batch;
  ties excluded from LL, S=0.5 update; POST rows update ratings only.
  C1 SOS: per (lineage, season) mean expected score accumulated in the update
  phase; adj = sos_mean - Sbar(t) (league mean over lineages with n>0 this
  season), 0 when n==0; p = sig(((r_h - r_a) - beta*(adj_h - adj_a))/400).
  C3 z: target season s uses prior season s-1 REG plays with both attributions
  in the 32 lineage codes and epa non-null; off=mean epa/play, def=-mean epa
  allowed/play, E=0.5*(off+def); z=(E-mean)/sd (population, ddof=0).
Inner folds: test seasons 2014..2018, eval rows = REG non-tie; pooled = mean.
Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python
"""
import json
import math
from collections import defaultdict
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

GAMES = "/Users/hoangminhlong/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv"
PBP_DIR = "/Users/hoangminhlong/.my-quantitative-data/nfl-ng-scored-v1/raw_pbp_2000_2017"
OUT = "/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration/lanes/A7_PRELAUNCH/tmp/a7_6_replay_evidence.json"

LINEAGE_MAP = {"SD": "LAC", "STL": "LA", "OAK": "LV"}
LINEAGE_ALL = {
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
    "GB", "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA", "MIN", "NE", "NO",
    "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
}
K, GAMMA, SCALE, INIT = 40.0, 2.0 / 3.0, 400.0, 1500.0
FOLDS = (2014, 2015, 2016, 2017, 2018)
NY = ZoneInfo("America/New_York")


def sig(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def build_z_table() -> dict:
    z = {}
    per_season = {}
    for year in range(2000, 2018):  # priors only ever from <= 2017
        t = pd.read_parquet(f"{PBP_DIR}/play_by_play_{year}.parquet",
                            columns=["season", "season_type", "posteam", "defteam", "epa"])
        assert int(t["season"].max()) <= 2017
        reg = t[t["season_type"] == "REG"]
        pt = reg["posteam"].astype("string")
        dt_ = reg["defteam"].astype("string")
        m = reg[pt.notna() & (pt.str.strip() != "") & pt.isin(LINEAGE_ALL)
                & dt_.notna() & (dt_.str.strip() != "") & dt_.isin(LINEAGE_ALL)
                & reg["epa"].notna()]
        off = m.groupby(m["posteam"], observed=True)["epa"].agg(["sum", "count"])
        dfn = m.groupby(m["defteam"], observed=True)["epa"].agg(["sum", "count"])
        E = {}
        for lg in set(off.index) | set(dfn.index):
            o = off.loc[lg]
            off_pp = float(o["sum"]) / float(o["count"])
            if lg in dfn.index and float(dfn.loc[lg, "count"]) > 0:
                d = dfn.loc[lg]
                def_pp = -float(d["sum"]) / float(d["count"])
            else:
                def_pp = 0.0
            E[lg] = 0.5 * (off_pp + def_pp)
        per_season[year] = E
    vals_all = []
    for s in range(2001, 2019):
        prev = per_season.get(s - 1, {})
        if not prev:
            continue
        v = np.array(sorted(prev.values()), dtype=float)
        mu, sd = float(v.mean()), float(v.std(ddof=0))
        if sd == 0.0:
            continue
        for lg, e in prev.items():
            z[(s, lg)] = (e - mu) / sd
        vals_all.append(s)
    return z


def replay(gs, z_table=None, theta=0.0):
    """Returns per-row dicts with p-stream ingredients (own implementation)."""
    ratings, reverted = {}, {}
    sos_sum, sos_n = defaultdict(float), defaultdict(int)
    out = []
    n = len(gs)
    i = 0
    kick = gs["kickoff_ns"].to_numpy()
    while i < n:
        j = i + 1
        while j < n and kick[j] == kick[i]:
            j += 1
        season_b = int(gs["season"].iloc[i])
        vals = [sos_sum[(lg, season_b)] / sos_n[(lg, season_b)]
                for lg in set(ratings) if sos_n.get((lg, season_b), 0) > 0]
        sbar = (sum(vals) / len(vals)) if vals else None
        batch = []
        for k in range(i, j):
            h = gs["home_lg"].iloc[k]
            a = gs["away_lg"].iloc[k]
            season = int(gs["season"].iloc[k])
            for lg in (h, a):
                if lg not in ratings:
                    ratings[lg] = INIT
                    reverted[lg] = season
                elif reverted[lg] < season:
                    zv = z_table.get((season, lg)) if z_table is not None else None
                    r_new = INIT + GAMMA * (ratings[lg] - INIT)
                    if theta != 0.0 and zv is not None:
                        r_new += theta * zv
                    ratings[lg] = r_new
                    reverted[lg] = season
            r_h, r_a = ratings[h], ratings[a]
            e_h = sig((r_h - r_a) / SCALE)
            e_a = 1.0 - e_h
            adj_h = (sos_sum[(h, season)] / sos_n[(h, season)] - sbar) if sos_n.get((h, season), 0) > 0 else 0.0
            adj_a = (sos_sum[(a, season)] / sos_n[(a, season)] - sbar) if sos_n.get((a, season), 0) > 0 else 0.0
            out.append({"season": season, "is_reg": gs["game_type"].iloc[k] == "REG",
                        "is_tie": gs["home_score"].iloc[k] == gs["away_score"].iloc[k],
                        "y": 1.0 if gs["home_score"].iloc[k] > gs["away_score"].iloc[k] else 0.0,
                        "e_home": e_h, "adj_h": adj_h, "adj_a": adj_a})
            batch.append(out[-1])
        # updates post-batch (S from scores)
        for k, rec in zip(range(i, j), batch):
            hs = float(gs["home_score"].iloc[k])
            as_ = float(gs["away_score"].iloc[k])
            S = 0.5 if hs == as_ else (1.0 if hs > as_ else 0.0)
            h, a = gs["home_lg"].iloc[k], gs["away_lg"].iloc[k]
            season = int(gs["season"].iloc[k])
            ratings[h] += K * (S - rec["e_home"])
            ratings[a] += K * ((1.0 - S) - (1.0 - rec["e_home"]))
            sos_sum[(h, season)] += rec["e_home"]
            sos_n[(h, season)] += 1
            sos_sum[(a, season)] += 1.0 - rec["e_home"]
            sos_n[(a, season)] += 1
        i = j
    return out


def main():
    df = pd.read_csv(GAMES, low_memory=False)
    n_total = len(df)
    df = df[(df["season"] >= 2000) & (df["season"] <= 2018)].copy()
    n_drop = n_total - len(df)
    df = df[df["game_type"] != "PRE"].copy()
    kos = []
    for gd, gt in zip(df["gameday"], df["gametime"]):
        ts = pd.Timestamp(f"{gd} {gt}")
        kos.append(ts.tz_localize("America/New_York", ambiguous=False,
                                  nonexistent="raise").tz_convert("UTC").value)
    df["kickoff_ns"] = kos
    df["home_lg"] = df["home_team"].map(lambda t: LINEAGE_MAP.get(t, t))
    df["away_lg"] = df["away_team"].map(lambda t: LINEAGE_MAP.get(t, t))
    df = df.sort_values(["kickoff_ns", "game_id"], kind="mergesort").reset_index(drop=True)
    print(f"[load] rows={len(df)} dropped_over_ceiling={n_drop} seasons="
          f"{df['season'].min()}..{df['season'].max()}")

    fold_rows = {s: int(((df["season"] == s) & (df["game_type"] == "REG")
                         & (df["home_score"] != df["away_score"])).sum()) for s in FOLDS}
    n_inner = sum(fold_rows.values())
    print(f"[folds] per-fold rows {fold_rows} pooled {n_inner}")

    z = build_z_table()
    z_seasons = sorted({s for s, _ in z})
    print(f"[z] entries={len(z)} target seasons {z_seasons[0]}..{z_seasons[-1]}")

    ev = {"fold_rows": fold_rows, "n_inner": n_inner,
          "z_entries": len(z), "z_target_seasons": [z_seasons[0], z_seasons[-1]]}

    for label, kwargs in (("B1STAR", {}), ("C3_T050", {"z_table": z, "theta": 50.0})):
        recs = replay(df, **kwargs)
        lls, mask = [], np.zeros(len(recs), dtype=bool)
        for k, r in enumerate(recs):
            if r["is_reg"] and not r["is_tie"] and r["season"] in FOLDS:
                mask[k] = True
                p = min(max(r["e_home"], 1e-15), 1 - 1e-15)
                y = r["y"]
                lls.append(-(y * math.log(p) + (1 - y) * math.log(1 - p)))
        ll = float(np.mean(lls))
        pmin = min(r["e_home"] for r in recs)
        pmax = max(r["e_home"] for r in recs)
        ev[label] = {"pooled_inner_ll": ll, "n_inner_used": int(mask.sum()),
                     "p_home_min_all_rows": pmin, "p_home_max_all_rows": pmax,
                     "clamp_bound_binding": bool(pmin <= 1e-15 or pmax >= 1 - 1e-15)}
        print(f"[ll] {label}: pooled={ll!r} rows={int(mask.sum())} p range [{pmin:.4f},{pmax:.4f}]")

    # C1_B025 rides the B1* replay records (SOS bookkeeping is arm-independent);
    # replay_logit records the raw rating difference d = r_h - r_a.
    recs = replay_logit(df)
    lls = []
    for r in recs:
        if r["is_reg"] and not r["is_tie"] and r["season"] in FOLDS:
            p = sig((r["d"] - 25.0 * (r["adj_h"] - r["adj_a"])) / SCALE)
            p = min(max(p, 1e-15), 1 - 1e-15)
            y = r["y"]
            lls.append(-(y * math.log(p) + (1 - y) * math.log(1 - p)))
    ll_c1 = float(np.mean(lls))
    ev["C1_B025"] = {"pooled_inner_ll": ll_c1, "n_inner_used": len(lls)}
    print(f"[ll] C1_B025: pooled={ll_c1!r} rows={len(lls)}")

    # B0 — from the aligned replay records (is_reg/is_tie/season/y per row)
    p0 = float(np.mean([r["y"] for r in recs if r["is_reg"] and not r["is_tie"]]))
    inner_b0 = [r for r in recs if r["is_reg"] and not r["is_tie"] and r["season"] in FOLDS]
    ll_b0 = float(-np.mean([r["y"] * math.log(p0) + (1 - r["y"]) * math.log(1 - p0)
                            for r in inner_b0]))
    ev["B0"] = {"p0": p0, "pooled_inner_ll": ll_b0,
                "n_inner_used": len(inner_b0),
                "inner_home_wins": int(sum(r["y"] for r in inner_b0))}
    print(f"[ll] B0: pooled={ll_b0!r}")

    targets = {"B1STAR": 0.6524968479911611, "C3_T050": 0.6483475228409372,
               "C1_B025": 0.6526382289724465, "B0": 0.6830369855947883}
    ev["ledger_targets"] = targets
    ev["abs_diffs"] = {k: abs(ev[k]["pooled_inner_ll"] - v) for k, v in targets.items()}
    ev["within_1e-9"] = {k: (ev["abs_diffs"][k] < 1e-9) for k in targets}
    print("[diffs]", json.dumps(ev["abs_diffs"], indent=2))
    assert all(ev["within_1e-9"].values()), "A7-6 RECOMPUTE MISMATCH"
    with open(OUT, "w") as f:
        json.dump(ev, f, indent=2)
    print("A7_6 RECOMPUTE: ALL WITHIN 1e-9")


def replay_logit(df):
    """Same replay but records the rating-difference logit input d = r_h - r_a."""
    ratings, reverted = {}, {}
    sos_sum, sos_n = defaultdict(float), defaultdict(int)
    out = []
    n = len(df)
    kick = df["kickoff_ns"].to_numpy()
    i = 0
    while i < n:
        j = i + 1
        while j < n and kick[j] == kick[i]:
            j += 1
        season_b = int(df["season"].iloc[i])
        vals = [sos_sum[(lg, season_b)] / sos_n[(lg, season_b)]
                for lg in set(ratings) if sos_n.get((lg, season_b), 0) > 0]
        sbar = (sum(vals) / len(vals)) if vals else None
        batch = []
        for k in range(i, j):
            h, a = df["home_lg"].iloc[k], df["away_lg"].iloc[k]
            season = int(df["season"].iloc[k])
            for lg in (h, a):
                if lg not in ratings:
                    ratings[lg] = INIT
                    reverted[lg] = season
                elif reverted[lg] < season:
                    ratings[lg] = INIT + GAMMA * (ratings[lg] - INIT)
                    reverted[lg] = season
            r_h, r_a = ratings[h], ratings[a]
            e_h = sig((r_h - r_a) / SCALE)
            adj_h = (sos_sum[(h, season)] / sos_n[(h, season)] - sbar) if sos_n.get((h, season), 0) > 0 else 0.0
            adj_a = (sos_sum[(a, season)] / sos_n[(a, season)] - sbar) if sos_n.get((a, season), 0) > 0 else 0.0
            batch.append({
                "season": season, "is_reg": df["game_type"].iloc[k] == "REG",
                "is_tie": df["home_score"].iloc[k] == df["away_score"].iloc[k],
                "y": 1.0 if df["home_score"].iloc[k] > df["away_score"].iloc[k] else 0.0,
                "e_home": e_h, "d": r_h - r_a, "adj_h": adj_h, "adj_a": adj_a,
                "h": h, "a": a})
        out.extend(batch)
        for k, rec in zip(range(i, j), batch):
            hs, as_ = float(df["home_score"].iloc[k]), float(df["away_score"].iloc[k])
            S = 0.5 if hs == as_ else (1.0 if hs > as_ else 0.0)
            season = rec["season"]
            ratings[rec["h"]] += K * (S - rec["e_home"])
            ratings[rec["a"]] += K * ((1.0 - S) - (1.0 - rec["e_home"]))
            sos_sum[(rec["h"], season)] += rec["e_home"]
            sos_n[(rec["h"], season)] += 1
            sos_sum[(rec["a"], season)] += 1.0 - rec["e_home"]
            sos_n[(rec["a"], season)] += 1
        i = j
    return out


if __name__ == "__main__":
    main()
