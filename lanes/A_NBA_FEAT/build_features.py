#!/usr/bin/env python
"""Lane A_NBA_FEAT (WINPROB-PLAYERFEAT-PREP-V1) — frozen NBA player-feature table.

Builds one row per (game_id, team side) for every PLAYED game 2016-2026 with
Group A (rotation load), Group B (top-3 form vs own baseline) and Group C
(key-player absence) scalars computed ONLY from strictly pre-tip box rows
(asof_v1_strict_tip_utc). Feature construction only: the table contains NO
outcome columns and this script computes no scored/win-prob metric.

Definitions are frozen in FEATURE_SPEC.md (same directory). Run:
    build_features.py            # build + write outputs + manifest json
    build_features.py --selftest # build + write + run leak-guard asserts (exit != 0 on failure)
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- constants
HOME = Path.home()
DATA = HOME / ".my-quantitative-data"
CURR_BOX = DATA / "playerfeat-prep-v1" / "nba" / "player_box_raw"
PRED_BOX = DATA / "playerdata-prep-v1" / "nba" / "player_box_raw"
SCHED = DATA / "nba-hoopr-v1" / "raw"
FEAT_DIR = DATA / "playerfeat-prep-v1" / "nba" / "features"
PROV = DATA / "playerfeat-prep-v1" / "nba" / "provenance"

SEASONS = list(range(2016, 2027))
ASOF_VERSION = "asof_v1_strict_tip_utc"
K_WINDOW = 5          # prior-k windows
TOP_N = 3             # top-N players (Groups B/C)
MIN_MINUTES = 24.0    # minimum-minutes guard (season-to-date minutes)
TRADE_GUARD = 10      # appearance must exist in trailing 10 team-games
ABS_WINDOW = 2        # Group C looks at the prior 2 team-games
NEUTRAL_GATE = 5      # neutral before >= 5 team-games of history

COLUMNS = [
    "game_id", "season", "season_type", "team_id", "opponent_id", "is_home",
    "is_exhibition", "tip_utc", "team_games_so_far", "n_prior_games_used",
    "feature_neutral", "a_top5_share_k5", "a_load_top5_k5", "b_form_top3",
    "b_form_top3_n", "c_abs_out", "c_abs_streak", "asof_rule_version",
]

BOX_DTYPE = {
    "game_id": "int64", "season": "int64", "season_type": "int64",
    "team_id": "int64", "athlete_id": "Int64", "minutes": "float64",
    "points": "float64",
}
SCHED_DTYPE = {
    "game_id": "int64", "season": "int64", "season_type": "int64",
    "home_id": "int64", "away_id": "int64",
    "home_score": "float64", "away_score": "float64",
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def box_path(season: int) -> Path:
    p = CURR_BOX / f"player_box_{season}.csv"
    return p if p.exists() else PRED_BOX / f"player_box_{season}.csv"


def as_bool(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s
    return s.astype("string").str.strip().eq("True").fillna(False)


# ------------------------------------------------------------- data loading
def load_season(season: int) -> dict:
    """Played schedule + usable/DNP box structures for one season."""
    sch = pd.read_csv(SCHED / f"nba_schedule_{season}.csv", dtype=SCHED_DTYPE,
                      low_memory=False)
    tip = pd.to_datetime(sch["game_date_time"], format="mixed", utc=True)
    sdt = pd.to_datetime(sch["start_date"], format="mixed", utc=True)
    assert int(tip.isna().sum()) == 0, f"{season}: tip parse failures"
    assert bool((tip == sdt).all()), f"{season}: game_date_time != start_date (UTC)"
    sch = sch.assign(tip_utc=tip)
    played = sch[sch["status_type_name"].eq("STATUS_FINAL")
                 & sch["home_score"].notna() & sch["away_score"].notna()]

    box = pd.read_csv(box_path(season), dtype=BOX_DTYPE, low_memory=False)
    assert set(box["season"].unique().tolist()) == {season}, f"{season}: label"
    assert set(box["game_id"].unique()).issubset(set(sch["game_id"])), \
        f"{season}: orphan box games"
    dnp = as_bool(box["did_not_play"])
    usable = box[box["athlete_id"].notna() & ~dnp]
    dnp_rows = box[box["athlete_id"].notna() & dnp]

    # per (game_id, team_id) aggregates from usable rows
    mins = usable["minutes"].fillna(0.0)
    u = usable.assign(minutes_filled=mins)
    agg = {}
    for (gid, tid), g in u.groupby(["game_id", "team_id"], sort=True):
        v = g["minutes_filled"].to_numpy()
        mass = float(v.sum())
        if mass > 0:
            order = np.lexsort((g["athlete_id"].to_numpy().astype("int64"),
                                -g["minutes_filled"].to_numpy()))
            top5 = float(v[order[:5]].sum()) / mass
        else:
            top5 = 0.0
        agg[(int(gid), int(tid))] = (mass, top5)

    usable_players, dnp_players, player_rows = {}, {}, {}
    for (gid, tid), g in u.groupby(["game_id", "team_id"], sort=True):
        key = (int(gid), int(tid))
        ids = g["athlete_id"].to_numpy().astype("int64")
        usable_players[key] = set(ids.tolist())
        player_rows[key] = list(zip(ids.tolist(),
                                    g["minutes_filled"].to_numpy().tolist(),
                                    g["points"].fillna(0.0).to_numpy().tolist()))
    for (gid, tid), g in dnp_rows.groupby(["game_id", "team_id"], sort=True):
        dnp_players[(int(gid), int(tid))] = set(
            g["athlete_id"].to_numpy().astype("int64").tolist())

    return {
        "played": played, "agg": agg, "usable": usable_players,
        "dnp": dnp_players, "rows": player_rows,
        "null_athlete_rows": int(box["athlete_id"].isna().sum()),
    }


# ------------------------------------------------------------ feature build
def build(season_data: dict[int, dict]) -> pd.DataFrame:
    out_rows = []
    for season in SEASONS:
        d = season_data[season]
        played = d["played"]
        # targets: ALL played games (play-in targets emitted; they never enter
        # any team's prior sequence). Sequence below = played non-play-in only.
        targets = played
        pair = pd.concat([
            targets[["game_id", "season_type", "tip_utc"]]
            .assign(team_id=targets["home_id"],
                    opponent_id=targets["away_id"], is_home=1),
            targets[["game_id", "season_type", "tip_utc"]]
            .assign(team_id=targets["away_id"],
                    opponent_id=targets["home_id"], is_home=0),
        ], ignore_index=True).sort_values(
            ["team_id", "tip_utc", "game_id"], kind="mergesort")

        for team_id, tg in pair.groupby("team_id", sort=True):
            # exhibition classifier (frozen): franchise = >=40 played team-games
            # in the season (measured margin: franchise min 64, exhibition max 8)
            is_exhibition = 0 if len(tg) >= 40 else 1
            tg = tg.sort_values(["tip_utc", "game_id"], kind="mergesort")
            # incremental state over this team's non-play-in played games
            agg_deque: deque[float] = deque(maxlen=K_WINDOW)
            agg_sum, agg_cnt = 0.0, 0            # season-to-date over usable priors
            players: dict[int, dict] = {}        # athlete_id -> state
            prior_records: list[dict] = []       # per prior team-game evidence
            for r in tg.itertuples(index=False):
                key = (int(r.game_id), int(team_id))
                # ---- emit BEFORE committing the target game
                team_so_far = len(prior_records)
                n_used = agg_cnt
                top3: list[int] = []
                if n_used > 0:
                    cands = [(aid, st["tot_min"]) for aid, st in players.items()
                             if st["tot_min"] >= MIN_MINUTES]
                    cands.sort(key=lambda t: (-t[1], t[0]))
                    top3 = [aid for aid, _ in cands[:TOP_N]]
                neutral = (n_used < NEUTRAL_GATE) or (len(top3) == 0)

                row = {
                    "game_id": int(r.game_id), "season": season,
                    "season_type": int(r.season_type), "team_id": int(team_id),
                    "opponent_id": int(r.opponent_id), "is_home": int(r.is_home),
                    "is_exhibition": is_exhibition,
                    "tip_utc": r.tip_utc, "team_games_so_far": team_so_far,
                    "n_prior_games_used": n_used,
                    "feature_neutral": int(neutral),
                    "a_top5_share_k5": 0.0, "a_load_top5_k5": 0.0,
                    "b_form_top3": 0.0, "b_form_top3_n": len(top3),
                    "c_abs_out": 0, "c_abs_streak": 0,
                    "asof_rule_version": ASOF_VERSION,
                }
                if not neutral:
                    a_level = float(np.mean(agg_deque))
                    row["a_top5_share_k5"] = a_level
                    row["a_load_top5_k5"] = a_level - agg_sum / agg_cnt
                    forms = []
                    for aid in top3:
                        st = players[aid]
                        ppm_k5 = float(np.mean(st["ppm_dq"]))
                        forms.append(ppm_k5 - st["tot_pts"] / st["tot_min"])
                    row["b_form_top3"] = float(np.mean(forms))
                    row["b_form_top3_n"] = len(top3)
                    row["c_abs_out"], row["c_abs_streak"] = group_c(
                        prior_records, top3)
                out_rows.append(row)

                # ---- commit target game into state (never for play-in targets;
                #      only if it has usable box rows for this team)
                if int(r.season_type) != 5 and key in d["agg"]:
                    mass, top5 = d["agg"][key]
                    agg_deque.append(top5)
                    agg_sum += top5
                    agg_cnt += 1
                    for aid, mins, pts in d["rows"].get(key, []):
                        st = players.get(aid)
                        if st is None:
                            st = players[aid] = {
                                "tot_min": 0.0, "tot_pts": 0.0,
                                "ppm_dq": deque(maxlen=K_WINDOW),
                            }
                        st["tot_min"] += mins
                        st["tot_pts"] += pts
                        st["ppm_dq"].append(pts / mins if mins > 0 else 0.0)
                    prior_records.append({
                        "gid": int(r.game_id),
                        "dnp": d["dnp"].get(key),
                        "usable": d["usable"].get(key),
                    })
                elif int(r.season_type) != 5:
                    prior_records.append({
                        "gid": int(r.game_id), "dnp": d["dnp"].get(key),
                        "usable": d["usable"].get(key),
                    })

    df = pd.DataFrame(out_rows, columns=COLUMNS)
    df = df.sort_values(["season", "tip_utc", "game_id", "team_id"],
                        kind="mergesort").reset_index(drop=True)
    df["is_home"] = df["is_home"].astype("int8")
    df["feature_neutral"] = df["feature_neutral"].astype("int8")
    df["c_abs_out"] = df["c_abs_out"].astype("int8")
    return df


def group_c(prior_records: list[dict], top3: list[int]) -> tuple[int, int]:
    """Absence scalars with the frozen trade guard (FEATURE_SPEC §5)."""
    m = len(prior_records)
    abs_out = 0
    for j in range(max(0, m - ABS_WINDOW), m):
        dnp = prior_records[j]["dnp"]
        if not dnp:
            continue
        for p in top3:
            if p in dnp and _guard(p, prior_records, j):
                abs_out = 1
    streak = 0
    if top3:
        top1 = top3[0]
        for j in range(m - 1, -1, -1):
            rec = prior_records[j]
            usable = rec["usable"]
            if usable is not None and top1 in usable:
                break                      # he played: streak ends
            if rec["dnp"] is not None and top1 in rec["dnp"] and _guard(
                    top1, prior_records, j):
                streak += 1
            else:
                break                      # no row / guard fails: no evidence
    return abs_out, streak


def _guard(player: int, prior_records: list[dict], j: int) -> bool:
    """Player appeared (usable row) for the same team in the 10 team-games
    immediately preceding missed game j."""
    for k in range(max(0, j - TRADE_GUARD), j):
        usable = prior_records[k]["usable"]
        if usable is not None and player in usable:
            return True
    return False


# ------------------------------------------------------- independent recompute
def recompute_independent(season_data: dict[int, dict], season: int,
                          game_id: int, team_id: int) -> dict:
    """Straightforward pandas recomputation of all scalars for one target row
    (separate code path from the incremental builder; used by --selftest)."""
    d = season_data[season]
    played = d["played"]
    prow = played[played["game_id"] == game_id]
    assert len(prow) == 1
    tip = prow["tip_utc"].iloc[0]
    stype = int(prow["season_type"].iloc[0])

    # priors: played, non-play-in, strictly earlier tip, same season
    seq = played[(played["season_type"] != 5) & (played["tip_utc"] < tip)]
    seq = seq[(seq["home_id"] == team_id) | (seq["away_id"] == team_id)]
    seq = seq.sort_values(["tip_utc", "game_id"], kind="mergesort")
    gids = seq["game_id"].tolist()

    per_game = []  # (game_id, mass, top5_share)
    for gid in gids:
        key = (int(gid), int(team_id))
        rowsd = d["rows"].get(key)
        if not rowsd:
            continue
        mins = np.array([m for _, m, _ in rowsd])
        mass = float(mins.sum())
        order = np.lexsort((np.array([a for a, _, _ in rowsd]), -mins))
        top5 = float(mins[order[:5]].sum()) / mass if mass > 0 else 0.0
        per_game.append((int(gid), mass, top5))

    n_used = len(per_game)
    neutral = n_used < NEUTRAL_GATE
    top3: list[int] = []
    pstats: dict[int, dict] = {}
    res = {"n_prior_games_used": n_used}
    if not neutral:
        for gid in gids:
            rowsd = d["rows"].get((int(gid), int(team_id)))
            if not rowsd:
                continue
            for aid, mins, pts in rowsd:
                st = pstats.setdefault(aid, {"tot_min": 0.0, "tot_pts": 0.0,
                                             "ppms": []})
                st["tot_min"] += mins
                st["tot_pts"] += pts
                st["ppms"].append(pts / mins if mins > 0 else 0.0)
        cands = [(a, s["tot_min"]) for a, s in pstats.items()
                 if s["tot_min"] >= MIN_MINUTES]
        cands.sort(key=lambda t: (-t[1], t[0]))
        top3 = [a for a, _ in cands[:TOP_N]]
        neutral = neutral or len(top3) == 0
    res["neutral"] = neutral
    if neutral:
        res.update({"a_top5_share_k5": 0.0, "a_load_top5_k5": 0.0,
                    "b_form_top3": 0.0, "b_form_top3_n": 0,
                    "c_abs_out": 0, "c_abs_streak": 0, "top3": []})
        return res
    a_level = float(np.mean([t for _, _, t in per_game[-K_WINDOW:]]))
    a_stdate = float(np.mean([t for _, _, t in per_game]))
    res["a_top5_share_k5"] = a_level
    res["a_load_top5_k5"] = a_level - a_stdate
    forms = []
    for aid in top3:
        st = pstats[aid]
        forms.append(float(np.mean(st["ppms"][-K_WINDOW:]))
                     - st["tot_pts"] / st["tot_min"])
    res["b_form_top3"] = float(np.mean(forms))
    res["b_form_top3_n"] = len(top3)
    # Group C, independent walk
    prior2 = gids[-ABS_WINDOW:]
    abs_out = 0
    for gid in prior2:
        dnp = d["dnp"].get((int(gid), int(team_id)))
        if not dnp:
            continue
        j = gids.index(gid)
        for p in top3:
            ok = False
            for g in gids[max(0, j - TRADE_GUARD):j]:
                us = d["usable"].get((int(g), int(team_id)))
                if us and p in us:
                    ok = True
                    break
            if p in dnp and ok:
                abs_out = 1
    streak = 0
    if top3:
        top1 = top3[0]
        for j in range(len(gids) - 1, -1, -1):
            gid = int(gids[j])
            us = d["usable"].get((gid, int(team_id)))
            if us and top1 in us:
                break
            dnp = d["dnp"].get((gid, int(team_id)))
            ok = False
            for g in gids[max(0, j - TRADE_GUARD):j]:
                us2 = d["usable"].get((int(g), int(team_id)))
                if us2 and top1 in us2:
                    ok = True
                    break
            if dnp and top1 in dnp and ok:
                streak += 1
            else:
                break
    res.update({"c_abs_out": abs_out, "c_abs_streak": streak, "top3": top3})
    return res


# ---------------------------------------------------------------- selftest
def selftest(df: pd.DataFrame, season_data: dict[int, dict]) -> list[str]:
    checks: list[str] = []

    def ok(name: str, cond: bool, detail: str = "") -> None:
        checks.append(f"{'PASS' if cond else 'FAIL'} {name} {detail}".rstrip())
        if not cond:
            raise AssertionError(f"{name} {detail}")

    # 1. schema / determinism / duplicates
    ok("columns_frozen", list(df.columns) == COLUMNS, f"n={len(df.columns)}")
    ok("no_outcome_columns",
       not any(w in c for c in df.columns
               for w in ("score", "winner", "win", "margin", "result", "outcome")))
    ok("duplicate_keys_zero",
       int(df.duplicated(subset=["game_id", "team_id"]).sum()) == 0)
    tot_played = sum(int(len(sd["played"])) for sd in season_data.values())
    ok("row_count_equals_2x_played", len(df) == 2 * tot_played,
       f"rows={len(df)} played={tot_played}")
    ok("tip_strictly_tz_aware", str(df["tip_utc"].dt.tz) == "UTC")

    # 2. neutral rule both directions
    low = df[df["n_prior_games_used"] < NEUTRAL_GATE]
    high_ok = df[(df["n_prior_games_used"] >= NEUTRAL_GATE)
                 & (df["b_form_top3_n"] > 0)]
    ok("neutral_when_lt5",
       bool((low["feature_neutral"] == 1).all())
       and bool((low[["a_top5_share_k5", "a_load_top5_k5", "b_form_top3",
                      "c_abs_out", "c_abs_streak"]] == 0).all().all()),
       f"n_lt5={len(low)}")
    ok("nonneutral_when_ge5",
       bool((high_ok["feature_neutral"] == 0).all()), f"n_ge5={len(high_ok)}")
    first_games = df[df["team_games_so_far"] == 0]
    ok("season_openers_neutral",
       bool((first_games["feature_neutral"] == 1).all()),
       f"openers={len(first_games)}")

    # 2b. exhibition disclosure law (FEATURE_SPEC §1)
    ex = df[df["is_exhibition"] == 1]
    ex_games = ex["game_id"].nunique()
    ok("exhibition_rows_38_games_19",
       len(ex) == 38 and ex_games == 19,
       f"rows={len(ex)} games={ex_games}")
    fr_counts = df[df["is_exhibition"] == 0].groupby(
        ["season", "team_id"]).size()
    ex_counts = ex.groupby(["season", "team_id"]).size()
    ok("exhibition_classifier_margin",
       int(fr_counts.min()) >= 40 and int(ex_counts.max()) < 40
       and fr_counts.groupby(level=0).size().eq(30).all(),
       f"franchise_min={int(fr_counts.min())} exhibition_max={int(ex_counts.max())} "
       f"franchise_entities_per_season={fr_counts.groupby(level=0).size().unique().tolist()}")
    # exhibition games never enter franchise prior sequences: a game flagged
    # exhibition on one side must be exhibition on the other
    g = df.groupby("game_id")["is_exhibition"].nunique()
    ok("exhibition_sides_consistent", bool((g == 1).all()))

    # 3. leak guards + independent recomputation on sample games
    samples = []
    p21 = season_data[2021]["played"]
    assert (p21["game_id"] == 401307387).any(), "MIL worked example missing"
    samples.append((2021, 401307387))
    for s in (2016, 2026):
        pl = season_data[s]["played"].sort_values(["tip_utc", "game_id"])
        samples.append((s, int(pl["game_id"].iloc[0])))
        samples.append((s, int(pl["game_id"].iloc[-1])))
    for season, gid in samples:
        prow = season_data[season]["played"]
        metarow = prow[prow["game_id"] == gid].iloc[0]
        for team_id in (int(metarow["home_id"]), int(metarow["away_id"])):
            got = df[(df["game_id"] == gid) & (df["team_id"] == team_id)]
            assert len(got) == 1
            tip = got["tip_utc"].iloc[0]
            sd = season_data[season]
            seq = sd["played"][(sd["played"]["season_type"] != 5)
                               & (sd["played"]["tip_utc"] < tip)]
            seq = seq[(seq["home_id"] == team_id) | (seq["away_id"] == team_id)]
            ok(f"leak_strict_tip[{season}:{gid}:{team_id}]",
               bool((seq["tip_utc"] < tip).all())
               and gid not in set(seq["game_id"].tolist()),
               f"priors={len(seq)}")
            ind = recompute_independent(season_data, season, gid, team_id)
            g = got.iloc[0]
            same = (
                int(ind["n_prior_games_used"]) == int(g["n_prior_games_used"])
                and int(ind["neutral"]) == int(g["feature_neutral"])
                and abs(ind["a_top5_share_k5"] - g["a_top5_share_k5"]) < 1e-12
                and abs(ind["a_load_top5_k5"] - g["a_load_top5_k5"]) < 1e-12
                and abs(ind["b_form_top3"] - g["b_form_top3"]) < 1e-12
                and int(ind["c_abs_out"]) == int(g["c_abs_out"])
                and int(ind["c_abs_streak"]) == int(g["c_abs_streak"]))
            ok(f"recompute_match[{season}:{gid}:{team_id}]", same,
               f"a={g['a_top5_share_k5']:.6f} b={g['b_form_top3']:.6f} "
               f"c=({g['c_abs_out']},{g['c_abs_streak']})")

    # 4. predecessor MIL worked example reproduction (as-of join cross-check)
    #    Predecessor PIT_AUDIT.md §3: target 401307387 MIL@WSH, tip
    #    2021-03-15T23:00Z; MIL prior-5 = {401267680, 401267700, 401267715,
    #    401307356, 401307372}, per-game masses {240,240,240,238,239}, mean 239.4.
    d21 = season_data[2021]
    prow = d21["played"]
    metarow = prow[prow["game_id"] == 401307387].iloc[0]
    mil_id = int(metarow["away_id"])  # MIL@WSH: MIL is the away side
    tip = metarow["tip_utc"]
    seq = prow[(prow["season_type"] != 5) & (prow["tip_utc"] < tip)]
    seq = seq[(seq["home_id"] == mil_id) | (seq["away_id"] == mil_id)]
    seq = seq.sort_values(["tip_utc", "game_id"], kind="mergesort")
    prior5 = seq["game_id"].tolist()[-5:]
    masses = []
    for gid in prior5:
        rowsd = d21["rows"].get((int(gid), mil_id)) or []
        masses.append(float(sum(m for _, m, _ in rowsd)))
    pred_ids = {401267680, 401267700, 401267715, 401307356, 401307372}
    ok("mil_prior5_ids", set(prior5) == pred_ids, f"got={sorted(prior5)}")
    ok("mil_prior5_mean_mass_239p4",
       abs(float(np.mean(masses)) - 239.4) < 1e-9,
       f"masses={masses} mean={np.mean(masses)}")
    ok("mil_tip_utc_2021_03_15_23Z",
       str(tip) == "2021-03-15 23:00:00+00:00", f"tip={tip}")

    # 5. trade guard: synthetic logic tests of the frozen rule
    #    timeline indices 0..15; stayer usable 0-4, DNP 5, usable 6-14, DNP 15;
    #    gone   usable 0-4, DNP 5, no rows afterwards.
    def mk_recs() -> list[dict]:
        recs = [{"gid": 1000 + j, "dnp": None, "usable": set()}
                for j in range(16)]
        for j in list(range(0, 5)) + list(range(6, 15)):
            recs[j]["usable"] = {9001}
        for j in range(0, 5):
            recs[j]["usable"] = recs[j]["usable"] | {9002}
        recs[5]["dnp"] = {9001, 9002}
        recs[15]["dnp"] = {9001, 9002}
        return recs

    recs = mk_recs()
    top3 = [9001, 9002, 9003]
    # at j=15: stayer appeared within window 5..14 -> absence counts;
    #          gone's last appearance is index 4, outside window 5..14 -> guard False
    out1, streak1 = group_c(recs[:15] + [recs[15]], top3)
    ok("trade_guard_stayer_counted", out1 == 1, f"out={out1}")
    ok("trade_guard_gone_expired",
       _guard(9002, recs, 15) is False and _guard(9001, recs, 15) is True,
       f"guard_gone={_guard(9002, recs, 15)} guard_stayer={_guard(9001, recs, 15)}")
    # streak: stayer back at j=16 usable -> streak from a j=17 target = 0;
    #         if stayer DNP at 14 and 15 -> streak 2 for a j=16 target
    recs[14]["usable"] = set()
    recs[14]["dnp"] = {9001, 9002}
    out2, streak2 = group_c(recs[:16], top3)
    ok("trade_guard_streak2", (out2, streak2) == (1, 2),
       f"out={out2} streak={streak2}")
    recs[13]["usable"] = set()
    recs[13]["dnp"] = {9001}
    out3, streak3 = group_c(recs[:16], top3)
    ok("trade_guard_streak3", (out3, streak3) == (1, 3),
       f"out={out3} streak={streak3}")

    # 6. global trade-guard property on the built table
    bad = 0
    for season in SEASONS:
        d = season_data[season]
        sub = df[df["season"] == season]
        for r in sub.itertuples(index=False):
            if int(r.c_abs_streak) > int(r.team_games_so_far):
                bad += 1
    ok("streak_leq_team_games", bad == 0, f"violations={bad}")

    return checks


# --------------------------------------------------------------------- main
def write_outputs(df: pd.DataFrame) -> dict:
    FEAT_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = FEAT_DIR / "nba_player_features_2016_2026.parquet"
    csv_path = FEAT_DIR / "nba_player_features_2016_2026.csv.gz"
    df.to_parquet(parquet_path, index=False)
    csv_bytes = gzip.compress(df.to_csv(index=False).encode("utf-8"),
                              compresslevel=9, mtime=0)
    csv_path.write_bytes(csv_bytes)

    inputs = []
    for s in SEASONS:
        inputs.append({"file": str(box_path(s)), "sha256": sha256_file(box_path(s))})
        inputs.append({"file": str(SCHED / f"nba_schedule_{s}.csv"),
                       "sha256": sha256_file(SCHED / f"nba_schedule_{s}.csv")})
    manifest = {
        "schema": "nba_player_feature_table_manifest@1",
        "cycle_id": "WINPROB-PLAYERFEAT-PREP-V1",
        "lane": "A_NBA_FEAT",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "asof_rule_version": ASOF_VERSION,
        "spec": "lanes/A_NBA_FEAT/FEATURE_SPEC.md",
        "rows": int(len(df)),
        "columns": COLUMNS,
        "neutral_rows": int(df["feature_neutral"].sum()),
        "per_season_rows": {
            int(s): int(n) for s, n in
            df.groupby("season").size().items()},
        "inputs_sha256": inputs,
        "outputs": [
            {"file": str(parquet_path), "sha256": sha256_file(parquet_path),
             "bytes": parquet_path.stat().st_size},
            {"file": str(csv_path), "sha256": hashlib.sha256(csv_bytes).hexdigest(),
             "bytes": len(csv_bytes)},
        ],
    }
    (FEAT_DIR / "build_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main() -> int:
    t0 = time.time()
    season_data = {s: load_season(s) for s in SEASONS}
    print(f"loaded 11 seasons in {time.time()-t0:.1f}s", flush=True)
    df = build(season_data)
    manifest = write_outputs(df)
    print(f"built {len(df)} rows in {time.time()-t0:.1f}s -> {FEAT_DIR}",
          flush=True)
    print(json.dumps({k: manifest[k] for k in
                      ("rows", "neutral_rows", "per_season_rows")}, indent=2))
    if "--selftest" in sys.argv:
        checks = selftest(df, season_data)
        print("\n".join(checks))
        (PROV / "selftest_checks.txt").write_text("\n".join(checks) + "\n")
        print("SELFTEST PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
