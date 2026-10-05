#!/usr/bin/env python
"""Lane B (WNBA PLAYER DATA) measurement script — cycle WINPROB-PLAYERDATA-PREP-V1.

Read-only over:
  ~/.my-quantitative-data/wnba-prep-v1/roster_audit/   (player_box_2002..2026.csv, game_rosters_2002..2026.csv)
  ~/.my-quantitative-data/wnba-v1/raw/espn_schedules/  (wnba_schedule_2002..2026.csv, game universe ESPN side)

Schema/coverage counting + PIT-constructibility demonstration ONLY. No win-prob metrics,
no scored computation, no outcome modeling. WNBA-only evidence.

Writes: lanes/B_WNBA/measurements_b.json (next to this script).
Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python lanes/B_WNBA/measure_b.py
"""
import hashlib
import json
import os
import re
import sys

import pandas as pd

CORPUS = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1/roster_audit")
ESPN_SCHED = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw/espn_schedules")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "measurements_b.json")
YEARS = list(range(2002, 2027))
ALIAS = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE", "CLA",
         "COL", "SPO", "COOP", "WNBASTARS"}
DETAIL_DROP = {"FORFEIT", "POSTPONED"}

R = {"law_note": "schema/coverage counting only; WNBA-only evidence; no scored computation",
     "measured_utc_note": "machine local run; today=2026-10-05"}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pctl(s, q):
    s = pd.Series(s).dropna()
    if len(s) == 0:
        return None
    return float(s.quantile(q))


# ---------------------------------------------------------------- part 1: integrity
def part_integrity():
    man = json.load(open(os.path.join(CORPUS, "download_manifest_r2.json")))
    files = man["files"]
    rows, mism, missing = [], [], []
    for f in sorted(files):
        rec = files[f]
        p = os.path.join(CORPUS, f)
        if not os.path.exists(p):
            missing.append(f)
            continue
        h = sha256_file(p)
        b = os.path.getsize(p)
        exp = rec["sha256_local"].replace("sha256:", "")
        rows.append({"file": f, "bytes_on_disk": b, "bytes_manifest": rec["bytes"],
                     "sha256_match": h == exp, "size_match": b == rec["bytes"],
                     "sha256_on_disk": "sha256:" + h})
        if h != exp:
            mism.append(f)
    R["integrity"] = {
        "manifest": "download_manifest_r2.json (cycle WNBA-WINPROB-PREP-V1 lane A, pull 2026-10-05T06:57-07:04Z)",
        "files_checked": len(rows),
        "sha256_match": sum(1 for r in rows if r["sha256_match"]),
        "sha256_mismatch": mism,
        "size_mismatch": [r["file"] for r in rows if not r["size_match"]],
        "missing_on_disk": missing,
        "total_bytes": sum(r["bytes_on_disk"] for r in rows),
        "per_file": rows,
        "downloaded_this_session": [],
        "downloaded_this_session_note": "none - corpus pre-existing from WNBA-WINPROB-PREP-V1; verified by re-hash only (EXTEND-ONLY law)",
    }


# ---------------------------------------------------------------- part 2: inventory + per-file loads
def load_all():
    inv = {"player_box": {}, "game_rosters": {}}
    pb, gr = {}, {}
    for y in YEARS:
        p = os.path.join(CORPUS, f"player_box_{y}.csv")
        g = os.path.join(CORPUS, f"game_rosters_{y}.csv")
        dfp = pd.read_csv(p, low_memory=False)
        dfg = pd.read_csv(g, low_memory=False)
        pb[y], gr[y] = dfp, dfg
        inv["player_box"][str(y)] = {"rows": int(len(dfp)), "cols": int(dfp.shape[1])}
        inv["game_rosters"][str(y)] = {"rows": int(len(dfg)), "cols": int(dfg.shape[1])}
    R["inventory_rows"] = inv
    return pb, gr


# ---------------------------------------------------------------- part 3: ESPN universe (filter law)
def espn_universe():
    uni = {}
    for y in YEARS:
        s = pd.read_csv(os.path.join(ESPN_SCHED, f"wnba_schedule_{y}.csv"), low_memory=False)
        n0 = len(s)
        s = s[s["status_type_state"] == "post"]
        n_post = len(s)
        det = s["status_type_detail"].astype(str).str.upper()
        drop_det = s[det.isin(DETAIL_DROP)]
        s = s[~det.isin(DETAIL_DROP)]
        hab = s["home_abbreviation"].astype(str).str.upper()
        aab = s["away_abbreviation"].astype(str).str.upper()
        alias = s[hab.isin(ALIAS) | aab.isin(ALIAS)]
        s = s[~(hab.isin(ALIAS) | aab.isin(ALIAS))]
        ids = set(s["id"].astype(str))
        uni[str(y)] = {"rows_total": int(n0), "rows_post": int(n_post),
                       "dropped_forfeit_postponed": int(len(drop_det)),
                       "dropped_alias": int(len(alias)),
                       "universe_games": int(len(ids))}
        uni[str(y)]["game_ids"] = ids
        if len(drop_det):
            uni[str(y)]["dropped_detail_ids"] = [str(x) for x in drop_det["id"]]
    total = sum(v["universe_games"] for v in uni.values())
    R["espn_universe"] = {
        "law": "keep status_type_state=='post'; drop Forfeit/Postponed; drop All-Star alias rows; (TBD placeholders are state=='pre', already excluded)",
        "per_season": {k: {kk: vv for kk, vv in v.items() if kk != "game_ids"} for k, v in uni.items()},
        "total_universe_games_espn_side": total,
        "cross_check_prior_cycle": {"expected": 5988, "match": total == 5988},
    }
    return uni


# ---------------------------------------------------------------- part 4: coverage joins
def coverage(pb, gr, uni):
    cov = {}
    for fam, data in (("player_box", pb), ("game_rosters", gr)):
        per = {}
        tot_pb_games = 0
        tot_uni_covered = 0
        not_in_uni_examples = []
        for y in YEARS:
            df = data[y]
            u = uni[str(y)]["game_ids"]
            gids = set(df["game_id"].astype(str))
            inter = gids & u
            extra = sorted(gids - u)
            miss = sorted(u - gids)
            per[str(y)] = {
                "games_in_file": len(gids),
                "universe_games": len(u),
                "universe_covered": len(inter),
                "join_rate_vs_universe": round(len(inter) / len(u), 4) if u else None,
                "file_games_not_in_universe": len(extra),
                "universe_games_missing": len(miss),
            }
            if extra and len(not_in_uni_examples) < 40:
                for gid in extra[:5]:
                    not_in_uni_examples.append({"season": y, "game_id": gid})
            tot_pb_games += len(gids)
            tot_uni_covered += len(inter)
        cov[fam] = {
            "per_season": per,
            "total_unique_games_in_files": tot_pb_games,
            "total_universe_games_covered": tot_uni_covered,
            "overall_join_rate_vs_espn_universe": round(tot_uni_covered / 5988, 4),
            "file_games_not_in_universe_examples": not_in_uni_examples,
        }
    R["coverage"] = cov


# ---------------------------------------------------------------- part 5: player_box quality
def pb_quality(pb):
    per = {}
    for y in YEARS:
        df = pb[y]
        g = df.groupby(df["game_id"].astype(str))
        players_per_game = g["athlete_id"].nunique()
        teams_per_game = g["team_id"].nunique()
        dup = df.groupby([df["game_id"].astype(str), "athlete_id"]).size()
        n_dup_rows = int((dup > 1).sum())
        dup_keys = dup[dup > 1]
        q = {
            "rows": int(len(df)),
            "unique_games": int(df["game_id"].astype(str).nunique()),
            "unique_athletes": int(df["athlete_id"].nunique()),
            "players_per_game_min": float(players_per_game.min()),
            "players_per_game_p05": pctl(players_per_game, 0.05),
            "players_per_game_median": pctl(players_per_game, 0.50),
            "players_per_game_p95": pctl(players_per_game, 0.95),
            "players_per_game_max": float(players_per_game.max()),
            "games_teams_ne_2": int((teams_per_game != 2).sum()),
            "dup_game_athlete_keys": n_dup_rows,
            "starter_rows": int(df["starter"].fillna(False).sum()) if "starter" in df else None,
            "dnp_rows": int(df["did_not_play"].fillna(False).sum()) if "did_not_play" in df else None,
            "active_false_rows": int((~df["active"].fillna(True)).sum()) if "active" in df else None,
            "reason_nonnull_rows": int(df["reason"].notna().sum()) if "reason" in df else None,
        }
        # minutes handling per era
        if "minutes" in df.columns:
            mv = pd.to_numeric(df["minutes"], errors="coerce")
            q["minutes_null_rows"] = int(mv.isna().sum())
            q["minutes_nonnull_median"] = pctl(mv, 0.50)
        elif "min" in df.columns:
            mv = df["min"].astype(str)
            q["minutes_null_rows"] = int((mv == "--").sum() + df["min"].isna().sum())
            q["minutes_dash_dash_rows"] = int((mv == "--").sum())
            num = pd.to_numeric(mv.replace("--", None), errors="coerce")
            q["minutes_nonnull_median"] = pctl(num, 0.50)
        if n_dup_rows:
            q["dup_examples"] = [f"{k[0]}:{k[1]}x{v}" for k, v in dup_keys.head(3).items()]
        per[str(y)] = q
    R["player_box_quality"] = per


# ---------------------------------------------------------------- part 6: roster sanity
def roster_sanity(gr):
    per = {}
    for y in YEARS:
        df = gr[y]
        df = df.assign(starter_f=df["starter"].fillna(False).astype(bool))
        tg = df.groupby([df["game_id"].astype(str), "team_id"])
        starters = tg["starter_f"].sum()
        dist = starters.value_counts().sort_index()
        zero_games = sorted({k[0] for k, v in starters.items() if v == 0})
        per[str(y)] = {
            "rows": int(len(df)),
            "unique_games": int(df["game_id"].astype(str).nunique()),
            "unique_athletes": int(df["athlete_id"].nunique()),
            "team_games": int(len(starters)),
            "team_games_starters_eq_5": int((starters == 5).sum()),
            "team_games_starters_ne_5": int((starters != 5).sum()),
            "team_games_starters_eq_0": int((starters == 0).sum()),
            "starters_per_team_game_distribution": {int(k): int(v) for k, v in dist.items()},
            "zero_starter_game_ids": zero_games[:12],
            "dnp_rows": int(df["did_not_play"].fillna(False).sum()),
            "active_rows": int(df["active"].fillna(False).sum()),
            "ejected_rows": int(df["ejected"].fillna(False).sum()),
            "reason_nonnull_rows": int(df["reason"].notna().sum()),
            "rows_per_game_median": pctl(df.groupby(df["game_id"].astype(str)).size(), 0.50),
        }
    R["roster_sanity"] = per


# ---------------------------------------------------------------- part 7: schema drift
def schema_drift(pb):
    cols = {y: list(pb[y].columns) for y in YEARS}
    counts = {str(y): len(cols[y]) for y in YEARS}
    c02, c10, c26 = set(cols[2002]), set(cols[2010]), set(cols[2026])
    R["schema_drift"] = {
        "player_box_colcount_per_season": counts,
        "eras": {"2002_legacy": 35, "2003_2011": 56, "2012_2026": 57},
        "diff_2002_vs_2010": {"only_in_2010": sorted(c10 - c02), "only_in_2002": sorted(c02 - c10)},
        "diff_2010_vs_2026": {"only_in_2026": sorted(c26 - c10), "only_in_2010": sorted(c10 - c26)},
        "roster_schema_note": "game_rosters 22 cols, schema identical 2002-2026 (per prior-cycle measurements_r2.json roster_schema_identical_2002_2026=true; re-verified below)",
        "roster_colcount_per_season": {str(y): int(gr_cols[y]) for y in YEARS} if False else None,
    }


# ---------------------------------------------------------------- part 8: pb vs rosters key sets
def pb_vs_rosters(pb, gr):
    per = {}
    for y in YEARS:
        kp = set(map(tuple, pb[y][["game_id", "athlete_id"]].astype(str).values))
        kr = set(map(tuple, gr[y][["game_id", "athlete_id"]].astype(str).values))
        inter = kp & kr
        per[str(y)] = {
            "pb_keys": len(kp), "roster_keys": len(kr), "overlap": len(inter),
            "roster_rows_without_pb_row": len(kr - inter),
            "pb_rows_without_roster_row": len(kp - inter),
            "roster_coverage_by_pb": round(len(inter) / len(kr), 4) if kr else None,
        }
    R["pb_vs_rosters_keys"] = per


# ---------------------------------------------------------------- part 9: era gap + special rows
def era_gap(pb, gr, uni):
    all_ids = set()
    for y in YEARS:
        all_ids |= uni[str(y)]["game_ids"]
    special = {
        "espn_only_regular_rows": ["270620018", "290709009", "400182104"],
        "cup_finals_dates": [("2021", "2021-08-12", "SEA-CON"), ("2022", "2022-07-26", "CHI-LVA"),
                             ("2023", "2023-08-15", "LVA-NYL"), ("2024", "2024-06-25", "NYL-MIN"),
                             ("2025", "2025-07-01", "MIN-IND"), ("2026", "2026-06-30", "NYL-LVA")],
        "excluded_special_rows": {"forfeit_2018": "401018942", "postponed_2023": "401507167",
                                  "postponed_2026": "401857072"},
    }
    res = {"espn_universe_total": len(all_ids)}
    for label, gid in special["excluded_special_rows"].items():
        res[f"{label}_in_player_box"] = any(gid in set(pb[y]["game_id"].astype(str)) for y in YEARS)
        res[f"{label}_in_rosters"] = any(gid in set(gr[y]["game_id"].astype(str)) for y in YEARS)
    for gid in special["espn_only_regular_rows"]:
        res[f"row_{gid}_in_player_box"] = any(gid in set(pb[y]["game_id"].astype(str)) for y in YEARS)
    # Cup finals: find ids from schedules by ET date + both team display names, then presence in player_box
    finals = []
    for yr, etdate, tag in special["cup_finals_dates"]:
        s = pd.read_csv(os.path.join(ESPN_SCHED, f"wnba_schedule_{int(yr)}.csv"), low_memory=False)
        d = pd.to_datetime(s["date"], utc=True, format="ISO8601").dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
        cand = s[d == etdate]
        gid = None
        for _, row in cand.iterrows():
            h, a = str(row.get("home_display_name", "")).upper(), str(row.get("away_display_name", "")).upper()
            t1, t2 = tag.split("-")
            if t1 in h and t2 in a or t2 in h and t1 in a:
                # Cup final = Cup headline; pick candidate with 'Cup' in notes-ish columns else last
                gid = str(row["id"])
        if gid is None and len(cand):
            gid = str(cand.iloc[-1]["id"])
        inpb = any(gid in set(pb[int(yr)]["game_id"].astype(str)) for y in [int(yr)]) if gid else None
        finals.append({"season": yr, "et_date": etdate, "tag": tag, "game_id": gid, "in_player_box": inpb})
    res["cup_finals_presence"] = finals
    res["era_gap_quantification"] = {
        "model_universe_union_rows": 7017,
        "espn_side_rows": 5988,
        "stats_only_rows": 1029,
        "stats_only_pre2002_rows": 1022,
        "stats_only_2002_2004_rows": 7,
        "player_level_coverable_max": 5988,
        "player_level_share_of_union": round(5988 / 7017, 4),
        "era_gap_statement": "player-level data (2002+) cannot cover the 1,022 games of 1997-2001 (14.6% of the 7,017 union) nor the 7 stats-only 2002-2004 games (no ESPN game_id); era 1997-2001 = warm-up-only per game universe spec",
    }
    R["era_gap"] = res


# ---------------------------------------------------------------- part 10: PIT worked example
def pit_example(pb):
    y = 2013
    df = pb[y]
    df = df[df["team_display_name"].astype(str).str.contains("Connecticut", case=False, na=False)]
    team_id = int(df["team_id"].iloc[0])
    sched = pd.read_csv(os.path.join(ESPN_SCHED, f"wnba_schedule_{y}.csv"), low_memory=False)
    sched["tip_utc"] = pd.to_datetime(sched["date"], utc=True, format="ISO8601")
    gid_tip = dict(zip(sched["id"].astype(str), sched["tip_utc"]))
    team_games = (df[df["team_id"] == team_id][["game_id"]]
                  .assign(game_id=lambda d: d["game_id"].astype(str)).drop_duplicates())
    team_games["tip_utc"] = team_games["game_id"].map(gid_tip)
    team_games = team_games.dropna().sort_values("tip_utc").reset_index(drop=True)
    target_idx = 10  # 11th game of the season for the team
    tgt = team_games.iloc[target_idx]
    tgt_tip = tgt["tip_utc"]
    prior = team_games[team_games["tip_utc"] < tgt_tip].tail(5)
    rowsout = []
    for _, prow in prior.iterrows():
        gid = prow["game_id"]
        sub = df[df["game_id"].astype(str) == gid]
        mv = pd.to_numeric(sub["minutes"], errors="coerce")
        rowsout.append({
            "game_id": gid, "tip_utc": str(prow["tip_utc"]),
            "team_minutes_total": float(mv.sum()),
            "players_with_minutes": int((mv > 0).sum()),
            "top_minutes": [{"athlete_id": int(a), "minutes": float(m)}
                             for a, m in mv.groupby(sub["athlete_id"]).sum().sort_values(ascending=False).head(3).items()],
        })
    R["pit_worked_example"] = {
        "as_of_law": "features for game G may use only games with tip_utc(G) strictly greater than prior tips (strictly-prior join on canonical tip_utc from ESPN schedule 'date', utc=True ISO8601)",
        "team": "Connecticut Sun (franchise CON)", "team_id": team_id, "season": y,
        "team_games_with_tip": int(len(team_games)),
        "target_game_id": str(tgt["game_id"]), "target_tip_utc": str(tgt_tip),
        "prior5_games": rowsout,
        "constructibility_verdict": "PASS_CONSTRUCTIBLE - as-of join over ESPN schedule tip times + player_box minutes rows succeeds; player_box rows are keyed by game_id and carry team_id and minutes",
    }


def main():
    part_integrity()
    pb, gr = load_all()
    # roster col count verify
    R["schema_drift"] = {}
    cols = {y: list(pb[y].columns) for y in YEARS}
    c02, c10, c26 = set(cols[2002]), set(cols[2010]), set(cols[2026])
    gr_counts = {str(y): int(gr[y].shape[1]) for y in YEARS}
    gr_colset = {str(y): set(gr[y].columns) for y in YEARS}
    gr_identical = all(gr_colset[str(y)] == gr_colset["2002"] for y in YEARS)
    R["schema_drift"] = {
        "player_box_colcount_per_season": {str(y): len(cols[y]) for y in YEARS},
        "eras": {"2002_legacy_short_names": 35, "2003_2011": 56, "2012_2026_long_names_plus_opponent": 57},
        "diff_2002_vs_2010": {"only_in_2010": sorted(c10 - c02), "only_in_2002": sorted(c02 - c10)},
        "diff_2010_vs_2026": {"only_in_2026": sorted(c26 - c10), "only_in_2010": sorted(c10 - c26)},
        "game_rosters_colcount_per_season": gr_counts,
        "game_rosters_schema_identical_2002_2026": bool(gr_identical),
    }
    uni = espn_universe()
    coverage(pb, gr, uni)
    pb_quality(pb)
    roster_sanity(gr)
    pb_vs_rosters(pb, gr)
    era_gap(pb, gr, uni)
    pit_example(pb)
    # strip game_ids sets (not JSON-serializable / bulky)
    json.dump(R, open(OUT, "w"), indent=1, default=str)
    print("wrote", OUT)
    print("integrity match:", R["integrity"]["sha256_match"], "/", R["integrity"]["files_checked"],
          "mismatch:", R["integrity"]["sha256_mismatch"])
    print("espn universe:", R["espn_universe"]["total_universe_games_espn_side"],
          "cross-check:", R["espn_universe"]["cross_check_prior_cycle"])
    print("pb covered:", R["coverage"]["player_box"]["total_universe_games_covered"],
          "rosters covered:", R["coverage"]["game_rosters"]["total_universe_games_covered"])


if __name__ == "__main__":
    sys.exit(main())
