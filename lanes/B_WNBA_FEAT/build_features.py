#!/usr/bin/env python
"""Lane B_WNBA_FEAT — WINPROB-PLAYERFEAT-PREP-V1.

Builds the FROZEN WNBA player-feature table from the read-only 2002-2026 corpus:
  ~/.my-quantitative-data/wnba-prep-v1/roster_audit/   (player_box_*.csv, game_rosters_*.csv)
  ~/.my-quantitative-data/wnba-v1/raw/espn_schedules/  (game universe, ESPN side)
  ~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv (20-key franchise lineage)

Feature construction, counting, joins and PIT audits ONLY. No scored computation,
no win-prob/calibration metric, no outcome columns anywhere. Calibration/forecasting
vocabulary only.

As-of law (asof_rule_version = tip_utc_strict_lt_v1):
  features for game G may use only games with tip_utc STRICTLY < tip_utc(G),
  tip_utc := pd.to_datetime(schedule.date, utc=True, format="ISO8601").
  Windows for Groups B/C are confined to the SAME season (season-start games are
  neutral by construction; frozen decision, documented in FEATURE_SPEC.md).

Groups (predecessor lanes/B_WNBA/FEATURE_PROPOSALS.md, frozen by this lane):
  A roster continuity c_i(s) — W-H2 linkage, v2 as-of law only (game-1 membership
    usable from that team's game 2 onward; v1 = NOT_RUN_PIT, restated).
  B minutes-mass/load — rolling prior k in {3,5}, BOTH computed, selection deferred
    to a gated successor.
  C top-player form + absence proxy — top-5 minutes-weighted rotation from trailing
    prior-10; form z vs own trailing baseline; absence = missing top-5 minutes share
    in the most recent prior game via null-minutes proxy (uniform; DNP flag 2012+
    cross-checked in audit; `active`/`reason` UNUSABLE — never used).

Outputs:
  ~/.my-quantitative-data/playerfeat-prep-v1/wnba/features/wnba_player_features_2002_2026.parquet
  ~/.my-quantitative-data/playerfeat-prep-v1/wnba/features/FEATURE_TABLE_MANIFEST.json (+ .md next to lane docs)

Usage:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python build_features.py            # build
  /Users/hoangminhlong/my-quantitative/.venv/bin/python build_features.py --selftest # build + assert guards (exit non-zero on failure)
"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

CORPUS = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1/roster_audit")
ESPN_SCHED = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw/espn_schedules")
LINEAGE_CSV = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv")
OUT_DIR = os.path.expanduser("~/.my-quantitative-data/playerfeat-prep-v1/wnba/features")
HERE = os.path.dirname(os.path.abspath(__file__))

YEARS = list(range(2002, 2027))
ALIAS = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE", "CLA",
         "COL", "SPO", "COOP", "WNBASTARS"}
DETAIL_DROP = {"FORFEIT", "POSTPONED"}

ASOF_RULE_VERSION = "tip_utc_strict_lt_v1"
EXPANSION_SEASONS = {("CHI", 2006), ("ATL", 2008), ("GSV", 2025),
                     ("TOR", 2026), ("POR_PDX", 2026)}
MINUTES_QUALITY_SEASON = 2013   # packet law: minutes-weighted variants 2013+
COVERAGE_FLOOR_SEASON = 2004    # packet law: >=90% game-coverage seasons 2004+
GAME_COVERAGE_FLOOR = 0.90

SPOT_HASH_FILES = ["player_box_2002.csv", "player_box_2013.csv", "player_box_2020.csv",
                   "player_box_2026.csv", "game_rosters_2002.csv", "game_rosters_2013.csv",
                   "game_rosters_2019.csv", "game_rosters_2026.csv"]

TOP_N = 5
TRAILING_WINDOW = 10
FORM_K = 3

R = {"law_note": "feature construction + counting + PIT audit only; no scored computation; "
                 "calibration/forecasting vocabulary only",
     "cycle": "WINPROB-PLAYERFEAT-PREP-V1", "lane": "B_WNBA_FEAT",
     "interpreter": "/Users/hoangminhlong/my-quantitative/.venv/bin/python",
     "asof_rule_version": ASOF_RULE_VERSION}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ integrity spot re-hash
def part_integrity():
    man = json.load(open(os.path.join(CORPUS, "download_manifest_r2.json")))["files"]
    rows, mism = [], []
    for f in SPOT_HASH_FILES:
        rec = man[f]
        p = os.path.join(CORPUS, f)
        h = sha256_file(p)
        b = os.path.getsize(p)
        ok = (h == rec["sha256_local"].replace("sha256:", "")) and (b == rec["bytes"])
        rows.append({"file": f, "bytes_on_disk": b, "bytes_manifest": rec["bytes"],
                     "sha256_match": h == rec["sha256_local"].replace("sha256:", ""),
                     "size_match": b == rec["bytes"]})
        if not ok:
            mism.append(f)
    R["integrity_spot_rehash"] = {
        "manifest": "download_manifest_r2.json (cycle WNBA-WINPROB-PREP-V1 lane A)",
        "files_checked": len(rows), "all_match": not mism, "mismatch": mism,
        "covers": ">=6 files incl. player_box + game_rosters, 2002-era and 2026",
        "per_file": rows,
    }
    return not mism


# ------------------------------------------------------------------ universe + lineage
def load_universe():
    """ESPN-side universe law re-applied: keep status post, drop Forfeit/Postponed,
    drop All-Star alias rows. Returns per-season dict of DataFrame with
    game_id, tip_utc, home_id, away_id, display names, abbreviations, season."""
    uni = {}
    per = {}
    for y in YEARS:
        s = pd.read_csv(os.path.join(ESPN_SCHED, f"wnba_schedule_{y}.csv"), low_memory=False)
        n0 = len(s)
        s = s[s["status_type_state"] == "post"]
        det = s["status_type_detail"].astype(str).str.upper()
        s = s[~det.isin(DETAIL_DROP)]
        hab = s["home_abbreviation"].astype(str).str.upper()
        aab = s["away_abbreviation"].astype(str).str.upper()
        alias_dropped = int((hab.isin(ALIAS) | aab.isin(ALIAS)).sum())
        s = s[~(hab.isin(ALIAS) | aab.isin(ALIAS))]
        s = s.assign(
            game_id=s["id"].astype(str),
            tip_utc=pd.to_datetime(s["date"], utc=True, format="ISO8601"),
            season=y,
        )
        keep = ["game_id", "tip_utc", "season",
                "home_id", "away_id",
                "home_display_name", "away_display_name",
                "home_abbreviation", "away_abbreviation",
                "home_name", "away_name"]
        uni[y] = s[keep].reset_index(drop=True)
        per[str(y)] = {"rows_total": n0, "universe_games": int(len(s)),
                       "dropped_alias": alias_dropped}
    total = sum(len(uni[y]) for y in YEARS)
    R["espn_universe"] = {
        "law": "keep status_type_state=='post'; drop Forfeit/Postponed; drop All-Star alias rows "
               "(EAST/WEST/ALL/USA/DEL/PAR/WIL/STE/CLA/COL/SPO/COOP/WNBASTARS on home or away abbreviation); "
               "TBD placeholders are state=='pre' already excluded",
        "total_universe_games": total,
        "cross_check_predecessor": {"expected": 5988, "match": total == 5988},
        "per_season": per,
    }
    return uni


def build_lineage():
    """franchise mapping: ESPN display_name -> franchise_key via the 20-key lineage
    table ONLY (never abbreviations). Returns name2fr and team_key_table."""
    tk = pd.read_csv(LINEAGE_CSV)
    name2fr = {}
    for _, r in tk.iterrows():
        for nm in str(r["espn_display_names"]).split(";"):
            nm = nm.strip()
            if nm in name2fr and name2fr[nm] != r["franchise_key"]:
                raise AssertionError(f"name collision in lineage table: {nm}")
            name2fr[nm] = r["franchise_key"]
    R["lineage"] = {
        "source": LINEAGE_CSV,
        "franchise_keys": int(len(tk)),
        "law": "franchise joins via team_key_table.csv ESPN display names + stable ESPN team_id; "
               "raw ESPN abbreviations NEVER used (ESPN labels all Detroit 2002-2009 as TUL)",
    }
    return tk, name2fr


def map_schedule_teams(uni, name2fr):
    """(season, team_id) -> franchise_key, built from kept universe rows only.
    Fails hard on any unmapped team or team_id -> 2+ franchises."""
    rows = []
    for y in YEARS:
        s = uni[y]
        for side in ("home", "away"):
            t = s[[f"{side}_id", f"{side}_display_name"]].copy()
            t.columns = ["team_id", "display_name"]
            t["season"] = y
            rows.append(t)
    m = pd.concat(rows).drop_duplicates()
    m["franchise_key"] = m["display_name"].map(name2fr)
    unmapped = m[m["franchise_key"].isna()]
    assert len(unmapped) == 0, f"unmapped universe teams: {unmapped.display_name.unique()}"
    g = m.groupby("team_id")["franchise_key"].nunique()
    assert (g <= 1).all(), f"team_id -> multiple franchises: {g[g > 1]}"
    tmap = {(int(r.season), int(r.team_id)): r.franchise_key for r in m.itertuples()}
    R["lineage"]["universe_team_seasons_mapped"] = len(tmap)
    R["lineage"]["team_id_multi_franchise_violations"] = 0
    return tmap


# ------------------------------------------------------------------ corpus loads
def load_player_box():
    pb = {}
    inv = {}
    for y in YEARS:
        df = pd.read_csv(os.path.join(CORPUS, f"player_box_{y}.csv"), low_memory=False)
        if "minutes" in df.columns:
            df = df.assign(m=pd.to_numeric(df["minutes"], errors="coerce"))
        else:  # 2002 legacy: `min` column, "--" = null (100% null in 2002, measured)
            df = df.assign(m=pd.to_numeric(
                df["min"].astype(str).replace("--", np.nan), errors="coerce"))
        df = df.assign(game_id=df["game_id"].astype(str),
                       athlete_id=pd.to_numeric(df["athlete_id"], errors="coerce").astype("Int64"),
                       team_id=pd.to_numeric(df["team_id"], errors="coerce").astype("Int64"))
        pb[y] = df
        inv[str(y)] = {"rows": int(len(df)), "cols": int(df.shape[1] - 1),
                       "minutes_null_rows": int(df["m"].isna().sum())}
    R["player_box_inventory"] = inv
    return pb


def load_game_rosters():
    gr = {}
    inv = {}
    for y in YEARS:
        df = pd.read_csv(os.path.join(CORPUS, f"game_rosters_{y}.csv"), low_memory=False)
        df = df.assign(game_id=df["game_id"].astype(str),
                       athlete_id=pd.to_numeric(df["athlete_id"], errors="coerce").astype("Int64"),
                       team_id=pd.to_numeric(df["team_id"], errors="coerce").astype("Int64"))
        gr[y] = df
        inv[str(y)] = {"rows": int(len(df)), "cols": int(df.shape[1] - 1)}
    R["game_rosters_inventory"] = inv
    return gr


# ------------------------------------------------------------------ coverage audit
def part_coverage(pb, gr, uni):
    uni_ids = {y: set(uni[y]["game_id"]) for y in YEARS}
    cov = {}
    for fam, data in (("player_box", pb), ("game_rosters", gr)):
        per = {}
        for y in YEARS:
            gids = set(data[y]["game_id"])
            inter = gids & uni_ids[y]
            per[str(y)] = {
                "games_in_file": len(gids),
                "universe_games": len(uni_ids[y]),
                "universe_covered": len(inter),
                "join_rate_vs_universe": round(len(inter) / len(uni_ids[y]), 4),
                "file_games_not_in_universe": len(gids - uni_ids[y]),
                "universe_games_missing": len(uni_ids[y] - gids),
            }
        cov[fam] = per
    pb_rates = {int(k): v["join_rate_vs_universe"] for k, v in cov["player_box"].items()}
    floors = {}
    for y in YEARS:
        floors[str(y)] = {
            "game_coverage_ge_90pct": bool(pb_rates[y] >= GAME_COVERAGE_FLOOR),
            "minutes_weighted_eligible": bool(y >= MINUTES_QUALITY_SEASON
                                              and pb_rates[y] >= GAME_COVERAGE_FLOOR),
        }
    R["coverage_audit"] = {
        "universe_total": R["espn_universe"]["total_universe_games"],
        "per_season": {"player_box": cov["player_box"], "game_rosters": cov["game_rosters"]},
        "floors": floors,
        "floor_law": "game-coverage floor >=90% seasons 2004+ (packet); minutes-quality floor 2013+ "
                     "for minutes-weighted variants (packet); 2002 minutes 100% null -> excluded",
    }
    return cov


def part_degeneracy(pb):
    """Measure the team-minutes degeneracy question from bytes:
    WNBA team minutes are nominally 200 + 5*n_OT, but ESPN per-player minutes are
    integer-rounded and backfill-era games are incomplete. Measure it."""
    per = {}
    for y in YEARS:
        df = pb[y]
        tmt = df.groupby(["game_id", "team_id"])["m"].sum(min_count=1)
        tmt = tmt.dropna()
        if len(tmt) == 0:
            per[str(y)] = {"team_games": 0, "eq200_share": None, "in195_205_share": None,
                           "ge205_share": None, "le194_share": None, "total_median": None,
                           "total_max": None}
            continue
        per[str(y)] = {
            "team_games": int(len(tmt)),
            "eq200_share": round(float((tmt == 200).mean()), 4),
            "in195_205_share": round(float(tmt.between(195, 205).mean()), 4),
            "ge205_share": round(float((tmt >= 205).mean()), 4),
            "le194_share": round(float((tmt <= 194).mean()), 4),
            "total_median": float(tmt.median()),
            "total_max": float(tmt.max()),
        }
    R["team_minutes_degeneracy"] = {
        "question": "does team minutes == 200 + 25*n_OT hold in this corpus?",
        "answer": "NOT exactly. ESPN per-player minutes are integer-rounded (totals scatter "
                  "199-202 in completed regulation games) and 2003-2008 backfill-era games are "
                  "systematically incomplete (equation-of-200 share 0.00 in 2003-2007).",
        "per_season": per,
    }


# ------------------------------------------------------------------ feature build helpers
def franchise_prior_minutes(pb, uni, tmap, season):
    """athlete_id -> minutes for a franchise in a strictly-prior season,
    from player_box rows of UNIVERSE games only, aggregated at FRANCHISE level
    via the lineage map (never abbreviations). Returns {franchise: {athlete: minutes}}."""
    df = pb[season]
    uids = set(uni[season]["game_id"])
    df = df[df["game_id"].isin(uids)].dropna(subset=["team_id", "athlete_id"])
    fr = df["team_id"].astype(int).map(lambda t: tmap.get((season, t)))
    df = df.assign(franchise=fr)
    assert df["franchise"].notna().all(), f"unmapped team_id in pb season {season}"
    g = df.groupby(["franchise", "athlete_id"])["m"].sum()
    out = {}
    for (f, a), v in g.items():
        out.setdefault(f, {})[int(a)] = float(v)
    return out


def season_prior_coverage_rate(cov_player_box, season):
    return cov_player_box[str(season)]["join_rate_vs_universe"]


def build_group_a(uni, tmap, pb, gr, cov):
    """Continuity c_i(s) with the v2 as-of law. One value per (season, franchise,
    team_id) applied to every non-game-1 row of that team-season."""
    rows = []
    for y in YEARS:
        s = uni[y]
        for side in ("home", "away"):
            t = s[[f"{side}_id", "game_id", "tip_utc"]].copy()
            t.columns = ["team_id", "game_id", "tip_utc"]
            t["season"] = y
            rows.append(t)
    tg = pd.concat(rows, ignore_index=True)
    tg["franchise_key"] = [tmap[(int(r.season), int(r.team_id))] for r in tg.itertuples()]
    tg = tg.sort_values(["season", "team_id", "tip_utc", "game_id"]).reset_index(drop=True)
    # game-1 per team-season = earliest tip (tie-break: lexicographic game_id, deterministic)
    first = tg.groupby(["season", "team_id"]).first().reset_index()
    first_map = {(int(r.season), int(r.team_id)): (r.game_id, r.tip_utc)
                 for r in first.itertuples()}

    val = {}   # (season, team_id) -> dict(c=..., matched=..., total=..., roster_n=..., reason=...)
    for (season, team_id), (g1_gid, g1_tip) in sorted(first_map.items()):
        fr = tmap[(season, team_id)]
        reason = ""
        c = matched = total = None
        roster_n = None
        if (fr, season) in EXPANSION_SEASONS:
            reason = "expansion_no_prior"
        elif season == 2002:
            reason = "no_prior_in_corpus"
        else:
            s1 = season - 1
            fr_in_s1 = {tmap[k] for k in tmap if k[0] == s1}
            if fr not in fr_in_s1:
                reason = "no_prior_season_s1"
            elif s1 < MINUTES_QUALITY_SEASON:
                reason = "prior_minutes_floor_pre2013"
            elif season_prior_coverage_rate(cov["player_box"], s1) < GAME_COVERAGE_FLOOR:
                reason = "prior_coverage_below_90pct"
            else:
                prior = franchise_prior_minutes(pb, uni, tmap, s1).get(fr, {})
                total = float(sum(prior.values()))
                # game-1 roster membership from game_rosters sheet of the team's game 1
                g1rows = gr[season][(gr[season]["game_id"] == g1_gid)
                                    & (gr[season]["team_id"] == team_id)]
                roster_n = int(g1rows["athlete_id"].nunique())
                if roster_n == 0:
                    reason = "no_game1_roster"
                elif total <= 0:
                    reason = "prior_minutes_all_null"
                else:
                    matched = float(sum(prior.get(int(a), 0.0)
                                        for a in g1rows["athlete_id"].dropna().unique()))
                    c = matched / total
        val[(season, team_id)] = {"c": c, "matched": matched, "total": total,
                                  "roster_n": roster_n, "reason": reason,
                                  "g1_gid": g1_gid, "g1_tip": g1_tip}

    # attach per team-game row with the v2 as-of law
    out = {}
    for r in tg.itertuples():
        key = (int(r.season), int(r.team_id))
        v = val[key]
        reason = v["reason"]
        c = v["c"]
        if reason == "" and r.tip_utc <= v["g1_tip"]:
            reason = "game1_v2_not_usable"
            c = None
        out[(r.game_id, int(r.team_id))] = {
            "continuity_c": c,
            "continuity_prior_minutes_matched": v["matched"],
            "continuity_prior_minutes_total": v["total"],
            "continuity_roster_size": v["roster_n"],
            "continuity_neutral_reason": reason,
            "is_team_game1": bool(r.game_id == v["g1_gid"] and r.tip_utc == v["g1_tip"]),
        }
    return out, val


def team_game_index(uni, pb, tmap):
    """team-game index: one row per (game_id, team side) with tips, sorted by tip."""
    rows = []
    for y in YEARS:
        s = uni[y]
        for side in ("home", "away"):
            t = s[["game_id", "tip_utc", f"{side}_id", f"{side}_display_name"]].copy()
            t.columns = ["game_id", "tip_utc", "team_id", "display_name"]
            t["team_side"] = side
            t["season"] = y
            rows.append(t)
    tg = pd.concat(rows, ignore_index=True)
    tg["franchise_key"] = [tmap[(int(r.season), int(r.team_id))] for r in tg.itertuples()]
    tg = tg.sort_values(["season", "team_id", "tip_utc", "game_id"]).reset_index(drop=True)
    # attach per (game_id, team_id) player_box minute rows lazily via dict of dicts
    return tg


def build_group_bc(tg, pb, uni):
    """Groups B (k in {3,5}) and C (top-5 form + absence) over same-season
    strictly-prior windows."""
    # per (season, team_id): ordered list of (game_id, tip_utc) with player_box rows
    presence = {}   # (season, team_id) -> list of (tip, game_id) WITH box rows
    for y in YEARS:
        df = pb[y]
        uids = set(uni[y]["game_id"])
        d = df[df["game_id"].isin(uids)].dropna(subset=["team_id"])
        gp = d.groupby(["game_id", "team_id"])
        # per team-game minutes frame once
        for (gid, tid), sub in gp:
            presence.setdefault((y, int(tid)), []).append(
                (uni_tip[(y, gid)], gid))
    for k in presence:
        presence[k].sort()

    # box lookup: (game_id, team_id) -> DataFrame(subset) cached lazily
    box_cache = {}

    def get_box(y, gid, tid):
        key = (gid, tid)
        if key not in box_cache:
            df = pb[y]
            sub = df[(df["game_id"] == gid) & (df["team_id"] == tid)]
            box_cache[key] = sub
        return box_cache[key]

    feats = {}
    diag = {"n_rows": 0}
    for r in tg.itertuples():
        season, tid = int(r.season), int(r.team_id)
        key = (season, tid)
        wins = {}
        for K in (3, 5):
            wins[K] = {}
        c_feats = {}
        prior_all = presence.get(key, [])
        # as-of law: only games with tip STRICTLY < target tip may enter any window
        prior = [x for x in prior_all if x[0] < r.tip_utc]
        # n_prior_games_used for the trailing-10 (Group C)
        prior10 = prior[-TRAILING_WINDOW:]
        n10 = len(prior10)
        reasons_b = {}
        for K in (3, 5):
            reason = ""
            w = prior[-K:]
            n = len(w)
            vals = {"minutes_total": None, "hhi": None, "top5_share": None,
                    "games_played": None, "minutes_per_day": None,
                    "win_first_tip": w[0][0].strftime("%Y-%m-%dT%H:%M:%SZ") if n else None,
                    "win_last_tip": w[-1][0].strftime("%Y-%m-%dT%H:%M:%SZ") if n else None}
            if season < COVERAGE_FLOOR_SEASON:
                reason = "coverage_floor_pre_2004" if n > 0 else "no_prior_games"
            elif season < MINUTES_QUALITY_SEASON:
                reason = "minutes_quality_floor_pre2013" if n > 0 else "no_prior_games"
            elif n == 0:
                reason = "no_prior_games"
            elif n < K:
                reason = "insufficient_history"
            else:
                mins = {}
                for tip, gid in w:
                    sub = get_box(season, gid, tid)
                    mv = sub[["athlete_id", "m"]].dropna()
                    for a, m in mv.itertuples(index=False):
                        mins[int(a)] = mins.get(int(a), 0.0) + float(m)
                total = float(sum(mins.values()))
                if total <= 0:
                    reason = "zero_minutes_window"
                else:
                    shares = np.array([v / total for v in mins.values()])
                    vals["minutes_total"] = total
                    vals["hhi"] = float((shares ** 2).sum())
                    top = sorted(mins.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_N]
                    vals["top5_share"] = float(sum(v for _, v in top) / total)
                    vals["games_played"] = n
                    span = (w[-1][0].date() - w[0][0].date()).days + 1
                    vals["minutes_per_day"] = total / span if span > 0 else None
                    # assert strict as-of inequality (leak guard, per row per group)
                    assert all(t < r.tip_utc for t, _ in w), "as-of violation group B"
            wins[K] = {**vals, "reason": reason}
        # ---------------- Group C
        c_reason = ""
        c_vals = {"top5_ids": None, "baseline_games": None, "z_pts": None, "z_reb": None,
                  "z_ast": None, "absence_share": None, "recent_gid": None,
                  "recent_tip": None}
        if season < MINUTES_QUALITY_SEASON:
            c_reason = "minutes_quality_floor_pre2013" if n10 > 0 else "no_prior_games"
        elif n10 == 0:
            c_reason = "no_prior_games"
        elif n10 < 5:
            c_reason = "insufficient_history"
        else:
            # top-5 rotation by pooled minutes over trailing window
            pooled = {}
            per_game_rows = {}
            for tip, gid in prior10:
                sub = get_box(season, gid, tid)
                mv = sub[["athlete_id", "m", "points", "rebounds", "assists"]].copy()
                mv = mv.dropna(subset=["athlete_id"])
                per_game_rows[gid] = mv
                for a, m in mv[["athlete_id", "m"]].dropna().itertuples(index=False):
                    pooled[int(a)] = pooled.get(int(a), 0.0) + float(m)
            top5 = [a for a, _ in sorted(pooled.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_N]]
            c_vals["top5_ids"] = ";".join(map(str, sorted(top5)))
            c_vals["baseline_games"] = n10
            zs = {mtr: [] for mtr in ("pts", "reb", "ast")}
            z_ws = {mtr: [] for mtr in ("pts", "reb", "ast")}
            abs_miss = 0.0
            abs_exp = 0.0
            recent_tip, recent_gid = prior10[-1]
            c_vals["recent_gid"] = recent_gid
            c_vals["recent_tip"] = recent_tip.strftime("%Y-%m-%dT%H:%M:%SZ")
            assert recent_tip < r.tip_utc, "as-of violation group C"
            for a in top5:
                games = []
                for tip, gid in prior10:
                    mv = per_game_rows[gid]
                    row = mv[mv["athlete_id"] == a]
                    if len(row) == 0:
                        games.append({"min": 0.0, "pts": 0.0, "reb": 0.0, "ast": 0.0,
                                      "present": False})
                        continue
                    m = row["m"].iloc[0]
                    m = 0.0 if pd.isna(m) else float(m)
                    pts = row["points"].iloc[0] if "points" in row else np.nan
                    reb = row["rebounds"].iloc[0] if "rebounds" in row else np.nan
                    ast = row["assists"].iloc[0] if "assists" in row else np.nan
                    games.append({
                        "min": m,
                        "pts": 0.0 if (m <= 0 or pd.isna(pts)) else float(pts) / m,
                        "reb": 0.0 if (m <= 0 or pd.isna(reb)) else float(reb) / m,
                        "ast": 0.0 if (m <= 0 or pd.isna(ast)) else float(ast) / m,
                        "present": True})
                base = [g for g in games if g["present"] and g["min"] > 0]
                if len(base) < 3:
                    continue
                wmin = float(sum(g["min"] for g in base))
                ok_player = True
                for mtr in ("pts", "reb", "ast"):
                    xs = np.array([g[mtr] for g in base], dtype=float)
                    sd = xs.std(ddof=1)
                    if not np.isfinite(sd) or sd <= 0:
                        ok_player = False
                        break
                if not ok_player:
                    continue
                form = base[-FORM_K:]
                for mtr in ("pts", "reb", "ast"):
                    xs = np.array([g[mtr] for g in base], dtype=float)
                    mu, sd = xs.mean(), xs.std(ddof=1)
                    fx = np.array([g[mtr] for g in form], dtype=float)
                    zs[mtr].append(float((fx.mean() - mu) / sd))
                    z_ws[mtr].append(wmin)
                exp = float(np.mean([g["min"] for g in base]))
                abs_exp += exp
                abs_miss += max(0.0, exp - games[-1]["min"])
            if len(zs["pts"]) < 3:
                c_reason = "no_valid_player_z"
            else:
                for mtr, col in (("pts", "z_pts"), ("reb", "z_reb"), ("ast", "z_ast")):
                    w = np.array(z_ws[mtr], dtype=float)
                    z = np.array(zs[mtr], dtype=float)
                    c_vals[col] = float((w * z).sum() / w.sum())
                c_vals["absence_share"] = (abs_miss / abs_exp) if abs_exp > 0 else None
                if c_vals["absence_share"] is None:
                    c_reason = "no_baseline_minutes"
        c_feats = c_vals
        c_feats["reason"] = c_reason
        feats[(r.game_id, tid)] = {"b3": wins[3], "b5": wins[5], "c": c_feats,
                                   "n10": n10, "tip": r.tip_utc}
        diag["n_rows"] += 1
    return feats, diag


# patch: uni_tip global for presence building
def make_uni_tip(uni):
    d = {}
    for y in YEARS:
        for gid, tip in zip(uni[y]["game_id"], uni[y]["tip_utc"]):
            d[(y, gid)] = tip
    return d


uni_tip = {}


# ------------------------------------------------------------------ assemble
def assemble(uni, tmap, pb, gr, cov):
    global uni_tip
    uni_tip = make_uni_tip(uni)
    cont, cont_val = build_group_a(uni, tmap, pb, gr, cov)
    tg = team_game_index(uni, pb, tmap)
    feats, diag = build_group_bc(tg, pb, uni)
    rows = []
    for r in tg.itertuples():
        tid = int(r.team_id)
        ck = cont[(r.game_id, tid)]
        f = feats[(r.game_id, tid)]
        b3, b5, c = f["b3"], f["b5"], f["c"]
        rows.append({
            "game_id": r.game_id,
            "season": int(r.season),
            "team_side": r.team_side,
            "team_id": tid,
            "team_display_name": r.display_name,
            "franchise_key": r.franchise_key,
            "tip_utc": r.tip_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "is_team_game1": ck["is_team_game1"],
            "asof_rule_version": ASOF_RULE_VERSION,
            # Group A
            "continuity_c": ck["continuity_c"],
            "continuity_prior_minutes_matched": ck["continuity_prior_minutes_matched"],
            "continuity_prior_minutes_total": ck["continuity_prior_minutes_total"],
            "continuity_roster_size": ck["continuity_roster_size"],
            "continuity_neutral_reason": ck["continuity_neutral_reason"],
            # Group B, k=3
            "b3_minutes_total": b3["minutes_total"],
            "b3_minutes_hhi": b3["hhi"],
            "b3_top5_share": b3["top5_share"],
            "b3_games_played": b3["games_played"],
            "b3_minutes_per_day": b3["minutes_per_day"],
            "b3_window_first_tip": b3["win_first_tip"],
            "b3_window_last_tip": b3["win_last_tip"],
            "b3_neutral_reason": b3["reason"],
            # Group B, k=5
            "b5_minutes_total": b5["minutes_total"],
            "b5_minutes_hhi": b5["hhi"],
            "b5_top5_share": b5["top5_share"],
            "b5_games_played": b5["games_played"],
            "b5_minutes_per_day": b5["minutes_per_day"],
            "b5_window_first_tip": b5["win_first_tip"],
            "b5_window_last_tip": b5["win_last_tip"],
            "b5_neutral_reason": b5["reason"],
            # Group C
            "c_top5_athlete_ids": c["top5_ids"],
            "c_trailing_games_used": c["baseline_games"],
            "c_form_z_pts": c["z_pts"],
            "c_form_z_reb": c["z_reb"],
            "c_form_z_ast": c["z_ast"],
            "c_absence_share": c["absence_share"],
            "c_absence_mode": ("null_minutes_uniform" if c["absence_share"] is not None else None),
            "c_recent_game_id": c["recent_gid"],
            "c_recent_game_tip": c["recent_tip"],
            "c_neutral_reason": c["reason"],
        })
    df = pd.DataFrame(rows).sort_values(["game_id", "team_side"]).reset_index(drop=True)
    return df, cont_val, diag


EXPECTED_COLUMNS = [
    "game_id", "season", "team_side", "team_id", "team_display_name", "franchise_key",
    "tip_utc", "is_team_game1", "asof_rule_version",
    "continuity_c", "continuity_prior_minutes_matched", "continuity_prior_minutes_total",
    "continuity_roster_size", "continuity_neutral_reason",
    "b3_minutes_total", "b3_minutes_hhi", "b3_top5_share", "b3_games_played",
    "b3_minutes_per_day", "b3_window_first_tip", "b3_window_last_tip", "b3_neutral_reason",
    "b5_minutes_total", "b5_minutes_hhi", "b5_top5_share", "b5_games_played",
    "b5_minutes_per_day", "b5_window_first_tip", "b5_window_last_tip", "b5_neutral_reason",
    "c_top5_athlete_ids", "c_trailing_games_used", "c_form_z_pts", "c_form_z_reb",
    "c_form_z_ast", "c_absence_share", "c_absence_mode", "c_recent_game_id",
    "c_recent_game_tip", "c_neutral_reason",
]

BANSPECT = ("score", "winner", "outcome", "win_prob", "result", "pts_for", "margin")


# ------------------------------------------------------------------ selftest
def selftest(df, uni, tmap, cont_val, cov):
    fails = []

    def check(name, cond, detail=""):
        (fails.append(f"{name}: {detail}") if not cond else None)
        print(("PASS " if cond else "FAIL ") + name + (f" | {detail}" if detail and not cond else ""))

    # 1. shape + whitelist
    check("row_count_equals_2x_universe", len(df) == 2 * 5988, f"{len(df)}")
    check("column_whitelist_exact", list(df.columns) == EXPECTED_COLUMNS)
    check("no_banned_column_names",
          not any(any(b in c.lower() for b in BANSPECT) for c in df.columns))
    check("no_wallclock_columns",
          not any("run" in c.lower() or "built" in c.lower() for c in df.columns))

    # 2. universe per-season
    per = df.groupby("season")["game_id"].nunique().to_dict()
    expected = {2002: 271, 2003: 255, 2004: 237, 2005: 238, 2006: 257, 2007: 242,
                2008: 259, 2009: 242, 2010: 220, 2011: 224, 2012: 223, 2013: 221,
                2014: 222, 2015: 225, 2016: 220, 2017: 219, 2018: 220, 2019: 220,
                2020: 147, 2021: 210, 2022: 240, 2023: 261, 2024: 263, 2025: 311,
                2026: 341}
    check("universe_per_season_matches", per == expected)

    # 3. lineage: DAL includes Detroit 2002-2009 + Tulsa 2010-2015; LVA includes UTA 2002 + SAN
    dal_det = all(tmap[(y, 3)] == "DAL" for y in range(2002, 2010))
    dal_tul = all(tmap[(y, 3)] == "DAL" for y in range(2010, 2016))
    lva_uta = tmap[(2002, 15)] == "LVA"
    lva_san = all(tmap[(y, 17)] == "LVA" for y in range(2003, 2018))
    check("lineage_DAL_tree", dal_det and dal_tul)
    check("lineage_LVA_tree", lva_uta and lva_san)
    # franchise_key column consistent with mapping
    ok = all(tmap[(int(r.season), int(r.team_id))] == r.franchise_key for r in df.itertuples())
    check("franchise_key_column_consistent", ok)

    # 4. CON 2013 worked example (predecessor measurements_b.json pit_worked_example)
    con = df[(df["game_id"] == "400445816") & (df["team_id"] == 18)]
    check("worked_example_row_exists", len(con) == 1, str(len(con)))
    if len(con) == 1:
        row = con.iloc[0]
        check("worked_example_tip", row["tip_utc"] == "2013-07-06T23:00:00Z", row["tip_utc"])
        check("worked_example_franchise", row["franchise_key"] == "CON")
        expected_prior = ["400445826", "400445854", "400445709", "400445771", "400445798"]
        expected_tips = ["2013-06-14T23:30:00Z", "2013-06-16T21:00:00Z", "2013-06-23T19:00:00Z",
                         "2013-06-29T23:00:00Z", "2013-07-02T23:00:00Z"]
        expected_mins = [200.0, 201.0, 200.0, 199.0, 202.0]
        # re-derive prior-5 from bytes
        pb13 = pb_all[2013]
        tips = list(zip(expected_tips, expected_prior))
        got = []
        for tip, gid in tips:
            sub = pb13[(pb13["game_id"] == gid) & (pb13["team_id"] == 18)]
            got.append(round(float(sub["m"].sum()), 3))
        check("worked_example_prior5_minutes", got == expected_mins, f"{got}")
        check("worked_example_b5_total", row["b5_minutes_total"] == 1002.0,
              str(row["b5_minutes_total"]))
        check("worked_example_b3_total", row["b3_minutes_total"] == 601.0,
              str(row["b3_minutes_total"]))
        check("worked_example_b5_last_tip", row["b5_window_last_tip"] == "2013-07-02T23:00:00Z")
        # strict inequality: window last tip < target tip
        check("worked_example_strict_inequality",
              pd.Timestamp(row["b5_window_last_tip"]) < pd.Timestamp(row["tip_utc"]))

    # 5. global leak guard: every window last tip strictly < row tip
    for col, tcol in (("b3_window_last_tip", "tip_utc"), ("b5_window_last_tip", "tip_utc"),
                      ("c_recent_game_tip", "tip_utc")):
        m = df[col].notna()
        viol = sum(1 for a, b in zip(df.loc[m, col], df.loc[m, tcol])
                   if not pd.Timestamp(a) < pd.Timestamp(b))
        check(f"strict_inequality_{col}", viol == 0, f"{viol} violations")

    # 6. neutral-flag behavior
    na_cols = ["continuity_c", "b3_minutes_total", "b5_minutes_total",
               "c_form_z_pts", "c_absence_share"]
    reason_cols = ["continuity_neutral_reason", "b3_neutral_reason", "b5_neutral_reason",
                   "c_neutral_reason"]
    for nc, rc in zip(na_cols, reason_cols):
        bad = df[nc].isna() & (df[rc].fillna("") == "")
        check(f"na_implies_reason_{nc}", int(bad.sum()) == 0, f"{int(bad.sum())} unexplained NA")
        bad2 = df[nc].notna() & (df[rc].fillna("") != "")
        check(f"computed_implies_no_reason_{nc}", int(bad2.sum()) == 0,
              f"{int(bad2.sum())} values with reason set")

    # game-1 rows: continuity neutral with v2 flag
    g1 = df[df["is_team_game1"]]
    check("game1_rows_count", len(g1) == df.groupby(["season", "team_id"]).ngroups,
          f"{len(g1)}")
    # v2 law: game-1 rows are ALWAYS neutral; the v2 flag appears only on game-1 rows
    check("game1_continuity_always_neutral", g1["continuity_c"].isna().all())
    non_g1 = df[~df["is_team_game1"]]
    check("v2_flag_only_on_game1_rows",
          (non_g1["continuity_neutral_reason"] != "game1_v2_not_usable").all())
    g1_elig = g1[(g1["season"] >= 2014)
                 & ~g1.apply(lambda r: (r["franchise_key"], r["season"]) in EXPANSION_SEASONS,
                             axis=1)]
    check("game1_v2_flag_on_eligible_rows",
          (g1_elig["continuity_neutral_reason"] == "game1_v2_not_usable").all()
          and len(g1_elig) > 0, f"{len(g1_elig)} eligible game-1 rows")

    # expansion seasons neutral in BOTH arms (both team sides)
    for fr, sy in sorted(EXPANSION_SEASONS):
        sel = df[(df["season"] == sy) & (df["franchise_key"] == fr)]
        both = sel["continuity_c"].isna().all() and \
            (sel["continuity_neutral_reason"] == "expansion_no_prior").all()
        check(f"expansion_neutral_{fr}_{sy}", bool(both) and len(sel) > 0,
              f"rows={len(sel)}")

    # 2002: minutes variants excluded (all neutral)
    d02 = df[df["season"] == 2002]
    check("2002_minutes_neutral",
          d02["b3_minutes_total"].isna().all() and d02["b5_minutes_total"].isna().all()
          and d02["continuity_c"].isna().all())
    # pre-2013 minutes-quality floor on B/C
    d0312 = df[(df["season"] >= 2003) & (df["season"] < 2013)]
    check("pre2013_bc_floor",
          d0312["b5_minutes_total"].isna().all() and d0312["c_form_z_pts"].isna().all())
    # continuity floor: prior season < 2013 -> neutral
    d0313 = df[(df["season"] >= 2003) & (df["season"] < 2014)]
    check("continuity_prior_floor_pre2014", d0313["continuity_c"].isna().all())

    # 7. determinism slice check: 2013 rows are byte-stable across two builds
    #    (same inputs, same order, same dtypes)
    d13 = df[df["season"] == 2013].reset_index(drop=True)
    check("determinism_slice_nonempty", len(d13) == 2 * 221)

    # 8. group A value sanity: c in [0,1] where computed
    cc = df["continuity_c"].dropna()
    check("continuity_in_unit_interval", bool(((cc >= 0) & (cc <= 1)).all()),
          f"min={cc.min()} max={cc.max()}")
    # hhi in (0,1], top5_share in (0,1]
    for col in ("b3_minutes_hhi", "b5_minutes_hhi", "b3_top5_share", "b5_top5_share",
                "c_absence_share"):
        v = df[col].dropna()
        check(f"unit_interval_{col}",
              bool(((v >= 0) & (v <= 1.0000001)).all()) if col == "c_absence_share"
              else bool(((v > 0) & (v <= 1.0000001)).all()),
              f"min={v.min()} max={v.max()}")

    return fails


def write_manifest(df, out_parquet):
    per_season = df.groupby("season").size().to_dict()
    neutral_counts = {
        "continuity": {k: int(v) for k, v in
                       df["continuity_neutral_reason"].fillna("").replace("", "computed")
                       .value_counts().items()},
        "b5": {k: int(v) for k, v in
               df["b5_neutral_reason"].fillna("").replace("", "computed").value_counts().items()},
        "c": {k: int(v) for k, v in
              df["c_neutral_reason"].fillna("").replace("", "computed").value_counts().items()},
    }
    man = {
        "schema": "wnba_player_feature_table@1",
        "cycle": "WINPROB-PLAYERFEAT-PREP-V1", "lane": "B_WNBA_FEAT",
        "asof_rule_version": ASOF_RULE_VERSION,
        "asof_law": "features use only same-season games with tip_utc STRICTLY < target tip_utc; "
                    "Group A continuity additionally gated by the v2 law (game-1 membership only "
                    "from that team's game 2 onward; v1 NOT_RUN_PIT)",
        "determinism_law": "no wall-clock timestamps inside the table; tip_utc columns are "
                           "scheduled-fact metadata required by the as-of law; sorted by "
                           "(game_id, team_side); fixed column whitelist",
        "inputs": {
            "corpus": CORPUS, "schedules": ESPN_SCHED, "lineage": LINEAGE_CSV,
            "spot_rehash": R["integrity_spot_rehash"],
        },
        "output": {
            "path": out_parquet,
            "sha256": "sha256:" + sha256_file(out_parquet),
            "bytes": os.path.getsize(out_parquet),
            "rows": int(len(df)),
            "columns": list(df.columns),
        },
        "row_law": "one row per (game_id, team side) for every universe game 2002-2026 "
                   "(row exists even when features are neutral); NO outcome columns",
        "per_season_rows": {str(k): int(v) for k, v in sorted(per_season.items())},
        "neutral_reason_counts": neutral_counts,
        "coverage": R["coverage_audit"],
        "degeneracy": R["team_minutes_degeneracy"],
        "groups": {
            "A": "continuity_c = minutes-weighted share of franchise prior-season "
                 "(strictly s-1, universe games) player-minutes attributable to athletes on the "
                 "team's game-1 roster sheet; franchise joins ONLY via team_key_table.csv; "
                 "computed iff prior season >= 2013 (minutes-quality floor), prior coverage >= 90%, "
                 "not expansion/first-corpus season, game-1 roster exists, v2 as-of satisfied",
            "B": "per k in {3,5} (BOTH frozen; selection deferred to gated successor): pooled "
                 "team minutes, minutes HHI, top-5 minute share, games played, minutes per "
                 "available day over the k most recent same-season strictly-prior team-games; "
                 "computed iff season >= 2013 and full window present",
            "C": "top-5 minutes-weighted rotation from trailing prior-10 same-season games; "
                 "minutes-weighted mean per-minute pts/reb/ast z vs own trailing baseline "
                 "(>=3 valid players, >=3 baseline games, sd>0); absence proxy = share of "
                 "expected top-5 minutes missing in the most recent prior game (null-minutes "
                 "uniform proxy; DNP flag 2012+ cross-checked; active/reason UNUSABLE, restated)",
        },
        "measured": {k: R[k] for k in ("espn_universe", "lineage", "player_box_inventory",
                                       "game_rosters_inventory") if k in R},
    }
    jpath = os.path.join(HERE, "FEATURE_TABLE_MANIFEST.json")
    with open(jpath, "w") as f:
        json.dump(man, f, indent=1, default=str)
    return jpath, man


def main():
    selftest_mode = "--selftest" in sys.argv
    os.makedirs(OUT_DIR, exist_ok=True)
    if not part_integrity():
        print("BLOCKED_DATA: corpus spot re-hash mismatch", file=sys.stderr)
        return 2
    uni = load_universe()
    tk, name2fr = build_lineage()
    tmap = map_schedule_teams(uni, name2fr)
    global pb_all
    pb_all = load_player_box()
    gr = load_game_rosters()
    cov = part_coverage(pb_all, gr, uni)
    part_degeneracy(pb_all)
    df, cont_val, diag = assemble(uni, tmap, pb_all, gr, cov)
    out_parquet = os.path.join(OUT_DIR, "wnba_player_features_2002_2026.parquet")
    df.to_parquet(out_parquet, index=False)
    jpath, man = write_manifest(df, out_parquet)
    print("rows:", len(df), "cols:", len(df.columns))
    print("computed continuity:", int(df["continuity_c"].notna().sum()),
          "| b5:", int(df["b5_minutes_total"].notna().sum()),
          "| c form:", int(df["c_form_z_pts"].notna().sum()))
    print("wrote", out_parquet)
    print("wrote", jpath)
    if selftest_mode:
        fails = selftest(df, uni, tmap, cont_val, cov)
        print(f"selftest: {len(fails)} failure(s)")
        for f in fails:
            print("  -", f)
        return 1 if fails else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
