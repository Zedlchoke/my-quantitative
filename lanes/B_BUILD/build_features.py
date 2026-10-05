#!/usr/bin/env python
"""B_BUILD — NFL-PLAYERFEAT-PREP-V1 — frozen NFL player-feature table builder.

PREP ONLY: strictly prior-game aggregates of player stats / snap counts.
NO outcome columns, NO target-game status fields (NOT_RUN_PIT law), no win-prob or
calibration-on-outcomes computation, no betting vocabulary. Spec: FEATURE_SPEC.md (frozen
v1.0.0 before this build). Deterministic: double-run produces byte-identical parquet.

Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python (only).
Writes ONLY: lanes/B_BUILD/ artifacts + ~/.my-quantitative-data/nfl-playerfeat-prep-v1/**.
Usage: build_features.py [--selftest] [--outdir DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ASOF_RULE_VERSION = "asof-1.0.0-nfl-playerfeat-prep-v1"
ET = ZoneInfo("America/New_York")

DATA = os.path.expanduser("~/.my-quantitative-data")
STATS_DIR = f"{DATA}/playerdata-prep-v1/nfl/raw_stats_player"
SNAP_DIR = f"{DATA}/playerdata-prep-v1/nfl/raw_snap_counts"
CW_PATH = f"{DATA}/playerfeat-prep-v1/nfl/raw_players/players.parquet"
GAMES_CSV = f"{DATA}/nfl-ng-prep-v1/raw_schedules_r1_20261005/games.csv"

# sha256 pins from predecessor manifests (winprob-playerdata-prep-v1 lanes C_NFL +
# winprob-playerfeat-prep-v1 lane C_NFL_CROSSWALK). Mismatch => BLOCKED_DATA.
INPUT_PINS = {
    "raw_stats_player/stats_player_week_2024.parquet": (
        "847569d194ca3d96b5efcf91e6eac5e18780fc47568a713fd545a82d29d155c1",
        f"{STATS_DIR}/stats_player_week_2024.parquet"),
    "raw_stats_player/stats_player_week_2025.parquet": (
        "2a461becaa9adb3c93a3074a3a31f1e960162a50163371a2d34e28393b5fff10",
        f"{STATS_DIR}/stats_player_week_2025.parquet"),
    "raw_stats_player/stats_player_week_2026.parquet": (
        "49bc644ed4bf10546b399ce177045f09ef278a562fc894074311c8afa6b26179",
        f"{STATS_DIR}/stats_player_week_2026.parquet"),
    "raw_snap_counts/snap_counts_2025.parquet": (
        "47220218fecda7af7ee5b0272a8ecce7c1bfb1f4e1f0a2c8c90047571728ce20",
        f"{SNAP_DIR}/snap_counts_2025.parquet"),
    "raw_snap_counts/snap_counts_2026.parquet": (
        "fae0627d81f4ffa1802263ac0fad1a29f5c1986d5749a711bde7c50651498273",
        f"{SNAP_DIR}/snap_counts_2026.parquet"),
    "raw_players/players.parquet": (
        "485b198070f831ed3a9098b991cd4b5dd97407e23a08fe31629d18dc304885e2", CW_PATH),
}

SEASONS = (2024, 2025, 2026)
KS = (3, 5)

KEY_COLS = ["game_id", "season", "week", "game_type", "side", "team", "opponent"]
ASOF_COLS = ["kickoff_utc", "rest_days", "n_prior_games_used", "asof_rule_version"]
G1_COLS = [f"qb_{m}_k{k}" for k in KS for m in
           ("yds", "td", "int", "att", "epa", "ypa", "epa_pa", "yds_form", "epa_form")] + \
          ["qb_yds_std_pg", "qb_epa_std_pg"]
G2_COLS = ["skill_top3_share_k3", "skill_hhi_k3", "skill_usage_pg_k3", "skill_top5_share_k5"]
G3_COLS = ["g3_top5_absent_share_recent", "g3_top5_newly_absent_count",
           "g3_n_snap_prior_games"]
FLAG_COLS = ["flag_no_prior_in_corpus", "flag_g1_window_truncated_k3",
             "flag_g1_window_truncated_k5", "flag_g2_zero_usage",
             "flag_g3_no_snap_prior", "flag_g3_pfr_null_excluded"]
ALL_COLS = KEY_COLS + ASOF_COLS + G1_COLS + G2_COLS + G3_COLS + FLAG_COLS

BANNED_TOKENS = ("score", "result", "winner", "margin", "spread", "moneyline", "odds",
                 "win_prob", "winprob", "prob", "total", "overtime", "outcome", "vegas",
                 "favorite", "underdog", "cover", "log_loss", "brier")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_inputs() -> dict:
    out = {}
    for rel, (pin, path) in INPUT_PINS.items():
        h = sha256_file(path)
        out[rel] = h
        if h != pin:
            raise SystemExit(
                f"BLOCKED_DATA: input sha256 mismatch {rel} got {h} want {pin}")
    return out


def load_inputs():
    games = pd.read_csv(GAMES_CSV)
    games = games[games["season"].isin(SEASONS)].copy()
    ko = pd.to_datetime(games["gameday"].astype(str) + " " + games["gametime"].astype(str))
    games["kickoff_utc_ts"] = ko.dt.tz_localize(ET).dt.tz_convert("UTC")

    frames, placeholder_rows = [], 0
    for y in SEASONS:
        s = pd.read_parquet(f"{STATS_DIR}/stats_player_week_{y}.parquet")
        placeholder_rows += int(s["player_id"].isna().sum())
        frames.append(s[s["player_id"].notna()].copy())  # NaN-player placeholder excluded
    stats = pd.concat(frames, ignore_index=True)
    stats = stats.merge(games[["game_id", "kickoff_utc_ts"]], on="game_id", how="left")
    assert stats["kickoff_utc_ts"].notna().all(), "stats game_id without games.csv kickoff"

    snap = pd.concat([pd.read_parquet(f"{SNAP_DIR}/snap_counts_{y}.parquet")
                      for y in (2025, 2026)], ignore_index=True)
    snap = snap.merge(games[["game_id", "kickoff_utc_ts"]], on="game_id",
                      how="left")
    snap = snap[snap["kickoff_utc_ts"].notna()].copy()

    cw = pd.read_parquet(CW_PATH)[["gsis_id", "pfr_id"]].dropna(subset=["gsis_id"])
    cw = cw.drop_duplicates("gsis_id")
    pfr2gsis = (cw.dropna(subset=["pfr_id"]).drop_duplicates("pfr_id")
                .set_index("pfr_id")["gsis_id"])
    return games, stats, snap, pfr2gsis, placeholder_rows


# ------------------------------------------------------------------ feature functions

def _window_kicks(pk: pd.Series, k: int) -> pd.Series:
    """pk: team same-season prior kickoffs (already strictly < target)."""
    return pk.tail(min(k, len(pk)))


def g1_features(qb_team: pd.DataFrame, pk: pd.Series, target_kick) -> dict:
    """Spec §4. pk: team same-season prior kickoffs (strict < target)."""
    out = {c: np.nan for c in G1_COLS}
    n_prior = len(pk)
    if n_prior == 0:
        return out
    qb = qb_team[qb_team["kickoff_utc_ts"] < target_kick]
    std_yds = float(qb["passing_yards"].sum()) / n_prior
    std_epa = float(qb["passing_epa"].fillna(0.0).sum()) / n_prior
    out["qb_yds_std_pg"] = std_yds
    out["qb_epa_std_pg"] = std_epa
    for k in KS:
        win = _window_kicks(pk, k)
        n_used = len(win)
        rows = qb[qb["kickoff_utc_ts"].isin(win)]
        yds = float(rows["passing_yards"].sum())
        epa = float(rows["passing_epa"].fillna(0.0).sum())
        att = float(rows["attempts"].sum())
        out[f"qb_yds_k{k}"] = yds
        out[f"qb_td_k{k}"] = float(rows["passing_tds"].sum())
        out[f"qb_int_k{k}"] = float(rows["passing_interceptions"].sum())
        out[f"qb_att_k{k}"] = att
        out[f"qb_epa_k{k}"] = epa
        out[f"qb_ypa_k{k}"] = yds / att if att > 0 else np.nan
        out[f"qb_epa_pa_k{k}"] = epa / att if att > 0 else np.nan
        out[f"qb_yds_form_k{k}"] = yds / n_used - std_yds
        out[f"qb_epa_form_k{k}"] = epa / n_used - std_epa
    return out


def g2_features(skill_team: pd.DataFrame, pk: pd.Series, target_kick) -> dict:
    """Spec §5. usage = targets + carries per player; top-N shares + HHI."""
    out = {c: np.nan for c in G2_COLS}
    if len(pk) == 0:
        return out
    sk = skill_team[skill_team["kickoff_utc_ts"] < target_kick]

    def topn_share(rows: pd.DataFrame, n: int) -> tuple[float, float, float]:
        u = (rows["targets"].fillna(0.0) + rows["carries"].fillna(0.0)).to_numpy()
        tot = float(u.sum())
        if tot <= 0:
            return np.nan, np.nan, np.nan
        pid = rows["player_id"].to_numpy()
        dfp = pd.DataFrame({"pid": pid, "u": u}).groupby("pid", as_index=False)["u"].sum()
        dfp = dfp.sort_values(["u", "pid"], ascending=[False, True], kind="stable")
        share = dfp["u"].to_numpy() / tot
        return float(share[:n].sum()), float((share ** 2).sum()), tot

    win3 = _window_kicks(pk, 3)
    r3 = sk[sk["kickoff_utc_ts"].isin(win3)]
    s3, hhi, tot3 = topn_share(r3, 3)
    out["skill_top3_share_k3"] = s3
    out["skill_hhi_k3"] = hhi
    out["skill_usage_pg_k3"] = tot3 / len(win3)
    if np.isnan(s3):  # U_tot == 0 -> NaN + flag (spec §5)
        out["skill_usage_pg_k3"] = np.nan
        out["__zero_usage"] = 1
        return out  # k5 window is zero-usage too
    win5 = _window_kicks(pk, 5)
    r5 = sk[sk["kickoff_utc_ts"].isin(win5)]
    s5, _, _ = topn_share(r5, 5)
    out["skill_top5_share_k5"] = s5
    if np.isnan(s5):
        out["__zero_usage"] = 1
    return out


def g3_features(snap_team: pd.DataFrame, target_kick, pfr2gsis: pd.Series) -> dict:
    """Spec §6. pfr-null rule: EXCLUDE unresolved rows from the candidate pool."""
    out = {c: np.nan for c in G3_COLS}
    out["__pfr_null_in_window"] = 0
    st = snap_team[snap_team["kickoff_utc_ts"] < target_kick]
    if len(st) == 0:
        out["__no_snap"] = 1
        return out
    kicks = st["kickoff_utc_ts"].sort_values(kind="stable").drop_duplicates() \
        .reset_index(drop=True)
    out["g3_n_snap_prior_games"] = int(len(kicks))
    win = kicks.tail(min(3, len(kicks)))
    rows = st[st["kickoff_utc_ts"].isin(win)].copy()
    gsis = rows["pfr_player_id"].map(pfr2gsis)
    out["__pfr_null_in_window"] = int(gsis.isna().sum())
    rows = rows[gsis.notna()].copy()
    rows["gsis_id"] = gsis[rows.index]
    snaps = rows["offense_snaps"].fillna(0.0) + rows["defense_snaps"].fillna(0.0)
    if float(snaps.sum()) <= 0:
        out["__no_present"] = 1
        return out
    dfp = pd.DataFrame({"gid": rows["gsis_id"].to_numpy(), "s": snaps.to_numpy()})
    dfp = dfp.groupby("gid", as_index=False)["s"].sum()
    dfp = dfp.sort_values(["s", "gid"], ascending=[False, True], kind="stable")
    top = dfp.head(5)
    n_w = len(win)
    recent_kick = win.iloc[-1]
    rec = rows[rows["kickoff_utc_ts"] == recent_kick]
    rec_s = (rec["offense_snaps"].fillna(0.0) + rec["defense_snaps"].fillna(0.0)) \
        .groupby(rec["gsis_id"]).sum()
    n_present, n_absent, n_newly = 0, 0, 0
    for _, r in top.iterrows():
        tot = float(r["s"])
        if tot <= 0:
            continue
        rs = float(rec_s.get(r["gid"], 0.0))
        n_present += 1
        if rs < 0.5 * (tot / n_w):
            n_absent += 1
        if rs == 0.0:
            n_newly += 1
    if n_present:
        out["g3_top5_absent_share_recent"] = n_absent / n_present
        out["g3_top5_newly_absent_count"] = float(n_newly)
    else:
        out["__no_present"] = 1
    return out


# --------------------------------------------------------------------------- builder

def build_table(games: pd.DataFrame, stats: pd.DataFrame, snap: pd.DataFrame,
                pfr2gsis: pd.Series) -> pd.DataFrame:
    stat_gids = set(stats["game_id"].unique())
    uni = games[games["game_id"].isin(stat_gids)].sort_values(
        ["kickoff_utc_ts", "game_id"], kind="stable")

    qb_all = stats[stats["position"] == "QB"]
    skill_all = stats[stats["position_group"].isin(["WR", "RB", "TE"])]
    qb_by = dict(tuple(qb_all.groupby(["season", "team"], sort=True)))
    skill_by = dict(tuple(skill_all.groupby(["season", "team"], sort=True)))
    snap_by = dict(tuple(snap.groupby(["season", "team"], sort=True)))

    rows = []
    for _, tgame in uni.iterrows():
        gid = tgame["game_id"]
        season = int(tgame["season"])
        tkick = tgame["kickoff_utc_ts"]
        gs = games[(games["season"] == season) & (games["kickoff_utc_ts"] < tkick)
                   & games["game_id"].isin(stat_gids)]
        for side, team, opp in (("away", tgame["away_team"], tgame["home_team"]),
                                ("home", tgame["home_team"], tgame["away_team"])):
            tm = gs[(gs["away_team"] == team) | (gs["home_team"] == team)]
            pk = tm["kickoff_utc_ts"].sort_values(kind="stable").reset_index(drop=True)
            n_prior = len(pk)

            row = {c: np.nan for c in ALL_COLS}
            row.update({
                "game_id": gid, "season": season, "week": int(tgame["week"]),
                "game_type": tgame["game_type"], "side": side, "team": team,
                "opponent": opp,
                "kickoff_utc": tkick.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "rest_days": ((tkick - pk.iloc[-1]).total_seconds() / 86400.0
                              if n_prior else np.nan),
                "n_prior_games_used": n_prior,
                "asof_rule_version": ASOF_RULE_VERSION,
                "flag_no_prior_in_corpus": int(n_prior == 0),
                "flag_g1_window_truncated_k3": int(0 < n_prior < 3),
                "flag_g1_window_truncated_k5": int(0 < n_prior < 5),
            })
            if n_prior:
                f1 = g1_features(qb_by.get((season, team), qb_all.iloc[0:0]),
                                 pk, tkick)
                row.update({c: f1[c] for c in G1_COLS})
                f2 = g2_features(skill_by.get((season, team), skill_all.iloc[0:0]),
                                 pk, tkick)
                row.update({c: f2[c] for c in G2_COLS})
                row["flag_g2_zero_usage"] = int(f2.get("__zero_usage", 0))
            f3 = g3_features(snap_by.get((season, team), snap.iloc[0:0]), tkick, pfr2gsis)
            row.update({c: f3[c] for c in G3_COLS})
            row["flag_g3_no_snap_prior"] = int(f3.get("__no_snap", 0))
            row["flag_g3_pfr_null_excluded"] = int(f3.get("__pfr_null_in_window", 0) > 0)
            rows.append(row)

    df = pd.DataFrame(rows)[ALL_COLS]
    return df.sort_values(["kickoff_utc", "game_id", "side"],
                          kind="stable").reset_index(drop=True)


# ----------------------------------------------------------------------------- audits

def leak_scan(df: pd.DataFrame, games: pd.DataFrame, stat_gids: set) -> dict:
    """Full-table scan: declared n_prior_games_used == true count of same-season team games
    with kickoff strictly < target (kickoff strict inequality as-of)."""
    viol = 0
    for r in df.itertuples(index=False):
        sub = games[(games["season"] == r.season)
                    & ((games["away_team"] == r.team) | (games["home_team"] == r.team))
                    & games["game_id"].isin(stat_gids)]
        tk = pd.Timestamp(r.kickoff_utc.replace("Z", "+00:00"))
        n_true = int((sub["kickoff_utc_ts"] < tk).sum())
        if n_true != r.n_prior_games_used:
            viol += 1
    return {"rows": len(df), "n_prior_mismatch": viol}


def outcome_scan(df: pd.DataFrame) -> list:
    return [c for c in df.columns
            if any(t in c.lower() for t in BANNED_TOKENS)]


def perturbation_check(games, stats, snap, pfr2gsis, df, sample_gids) -> dict:
    """Target-game absence (one game at a time): perturb ONLY game X's own stats rows;
    row X's features must be identical (no target-game data may enter features)."""
    cols = [c for c in ALL_COLS if c != "asof_rule_version"]
    results = {}
    for gid in sample_gids:
        stats2 = stats.copy()
        mask = stats2["game_id"] == gid
        stats2.loc[mask, "passing_yards"] += 1000.0
        stats2.loc[mask, "targets"] += 50.0
        stats2.loc[mask, "passing_epa"] += 5.0
        df2 = build_table(games, stats2, snap, pfr2gsis)
        a = df[df["game_id"] == gid][cols].reset_index(drop=True)
        b = df2[df2["game_id"] == gid][cols].reset_index(drop=True)
        results[gid] = bool(a.equals(b))
    return results


# --------------------------------------------------------------------------- manifest

def write_manifest(outdir: str, df: pd.DataFrame, n_games: int, sha_out: str,
                   hashes: dict, placeholder_rows: int, join_rates: dict,
                   coverage: dict, first_dates: dict, fut_kick: str) -> dict:
    man = {
        "cycle_id": "NFL-PLAYERFEAT-PREP-V1",
        "lane": "B_BUILD",
        "asof_rule_version": ASOF_RULE_VERSION,
        "spec": "lanes/B_BUILD/FEATURE_SPEC.md v1.0.0 (frozen before build)",
        "output": {
            "path": f"{outdir}/nfl_playerfeat_table_v1.parquet",
            "sha256": sha_out,
            "rows": int(len(df)),
            "cols": len(ALL_COLS),
            "games": int(n_games),
        },
        "inputs_sha256": hashes,
        "inputs_verified": "6/6 match predecessor manifests (re-hashed at build start)",
        "placeholder_rows_excluded": placeholder_rows,
        "per_season_rows": {str(k): int(v) for k, v in df.groupby("season").size().items()},
        "per_season_games": {str(k): int(v // 2) for k, v in
                             df.groupby("season").size().items()},
        "future_2026_games_no_rows": 209,
        "earliest_future_2026_kickoff_utc": fut_kick,
        "join_rates_remeasured": join_rates,
        "coverage": coverage,
        "first_computable_dates": first_dates,
        "outcome_columns": 0,
        "not_run_pit_law": ("target-game injury/active/DNP/starter status remains "
                            "NOT_RUN_PIT; G3 is a lagged prior-game proxy only"),
    }
    with open(f"{outdir}/FEATURE_TABLE_MANIFEST.json", "w") as f:
        json.dump(man, f, indent=2, sort_keys=True)
    return man


# ------------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--outdir", default=f"{DATA}/nfl-playerfeat-prep-v1/features")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    hashes = verify_inputs()
    print("input sha256 verification: 6/6 OK")
    games, stats, snap, pfr2gsis, placeholder_rows = load_inputs()
    df = build_table(games, stats, snap, pfr2gsis)
    n_games = df["game_id"].nunique()
    print(f"built {len(df)} rows / {n_games} games")

    out_path = f"{args.outdir}/nfl_playerfeat_table_v1.parquet"
    df[ALL_COLS].to_parquet(out_path, index=False)
    sha_out = sha256_file(out_path)
    print(f"parquet: {out_path} sha256={sha_out}")

    stat_gids = set(stats["game_id"].unique())
    checks: dict[str, dict] = {}
    if args.selftest:
        # S1 leak guard: kickoff strict inequality, full table
        ls = leak_scan(df, games, stat_gids)
        checks["S1_kickoff_strict_inequality_full_table"] = {
            **ls, "pass": ls["n_prior_mismatch"] == 0}

        # S2 KC worked example (predecessor PIT basis), re-derived from bytes.
        # KC had a wk6 bye 2024 -> weeks 1-10 give 9 prior games.
        kc = df[(df["game_id"] == "2024_11_KC_BUF") & (df["team"] == "KC")].iloc[0]
        ok_kc = (float(kc["qb_yds_k3"]) == 819.0 and float(kc["qb_td_k3"]) == 6.0
                 and float(kc["qb_int_k3"]) == 1.0 and float(kc["qb_att_k3"]) == 124.0
                 and kc["n_prior_games_used"] == 9)
        checks["S2_kc_worked_example_2024_11_KC_BUF"] = {
            "qb_yds_k3": float(kc["qb_yds_k3"]), "qb_td_k3": float(kc["qb_td_k3"]),
            "qb_int_k3": float(kc["qb_int_k3"]), "qb_att_k3": float(kc["qb_att_k3"]),
            "n_prior_games_used": int(kc["n_prior_games_used"]), "pass": bool(ok_kc)}

        # S3 target-game absence via one-at-a-time perturbation (KC example + fixtures)
        sample = [g for g in ("2024_11_KC_BUF", "2024_07_KC_SF", "2026_04_PIT_CLE",
                              "2026_03_ATL_GB") if g in stat_gids]
        per_gid = perturbation_check(games, stats, snap, pfr2gsis, df, sample)
        checks["S3_target_game_absence_perturbation"] = {
            "per_gid_rows_identical": per_gid, "pass": all(per_gid.values())}

        # S4 crosswalk canary: pfr-null player (WhitCo05 / Cody White, gsis 00-0035891)
        cw = pd.read_parquet(CW_PATH)[["gsis_id", "pfr_id"]]
        cody_null = bool(cw.loc[cw["gsis_id"] == "00-0035891", "pfr_id"].isna().all())
        snap_cody = int(((snap["pfr_player_id"] == "WhitCo05")
                         & (snap["season"] == 2026)).sum())
        lv = df[(df["team"] == "LV") & (df["season"] == 2026)]
        lv_flag = int(lv["flag_g3_pfr_null_excluded"].max()) if len(lv) else -1
        checks["S4_crosswalk_canary_pfr_null"] = {
            "cody_white_crosswalk_pfr_null": cody_null,
            "whitco05_snap2026_rows": snap_cody,
            "lv_flag_g3_pfr_null_excluded_max": lv_flag,
            "pass": cody_null and snap_cody > 0 and lv_flag == 1}

        # S5 bye-week fixture: KC bye wk6 2024 -> 2024_07_KC_SF, window = wks 5,4,3
        bk = df[(df["game_id"] == "2024_07_KC_SF") & (df["team"] == "KC")].iloc[0]
        p3 = stats[(stats["season"] == 2024) & (stats["team"] == "KC")
                   & (stats["position"] == "QB")
                   & stats["game_id"].isin(["2024_05_NO_KC", "2024_04_KC_LAC",
                                            "2024_03_KC_ATL"])]
        exp_yds = float(p3["passing_yards"].sum())
        ok_bye = (12.0 < float(bk["rest_days"]) < 14.0
                  and bk["n_prior_games_used"] == 5
                  and bk["flag_no_prior_in_corpus"] == 0
                  and float(bk["qb_yds_k3"]) == exp_yds == 793.0)
        checks["S5_bye_week_fixture_2024_07_KC_SF"] = {
            "rest_days": round(float(bk["rest_days"]), 4),
            "n_prior_games_used": int(bk["n_prior_games_used"]),
            "qb_yds_k3": float(bk["qb_yds_k3"]), "window_weeks": [5, 4, 3],
            "pass": bool(ok_bye)}

        # S6 determinism double-run: fresh rebuild in-process, byte-identical
        with tempfile.TemporaryDirectory() as td:
            df2 = build_table(games, stats, snap, pfr2gsis)
            p2 = f"{td}/rebuild.parquet"
            df2[ALL_COLS].to_parquet(p2, index=False)
            sha2 = sha256_file(p2)
        checks["S6_determinism_double_run"] = {
            "sha_first": sha_out, "sha_rebuild": sha2, "pass": sha_out == sha2}

        # S7 placeholder exclusion
        checks["S7_placeholder_exclusion"] = {
            "nan_player_rows_excluded": placeholder_rows, "expected": 48,
            "pass": placeholder_rows == 48}

        # S8 outcome-column ban
        bad = outcome_scan(df[ALL_COLS])
        checks["S8_outcome_column_ban"] = {"banned_hits": bad, "cols": len(ALL_COLS),
                                           "pass": not bad}

        with open(f"{args.outdir}/selftest_results.json", "w") as f:
            json.dump(checks, f, indent=2, sort_keys=True)
        n_pass = sum(1 for v in checks.values() if v["pass"])
        for k, v in checks.items():
            print(f"  [{'PASS' if v['pass'] else 'FAIL'}] {k}")
        print(f"selftest: {n_pass}/{len(checks)} PASS")
        if n_pass != len(checks):
            return 2

    # join rates re-measured
    cw_all = pd.read_parquet(CW_PATH)[["gsis_id", "pfr_id"]].dropna(subset=["gsis_id"]) \
        .drop_duplicates("gsis_id")
    gsis_set, pfr_set = set(cw_all["gsis_id"]), set(cw_all["pfr_id"].dropna())
    jr: dict = {"stats_gsis_resolved_by_season": {}}
    for y in SEASONS:
        ids = set(stats.loc[stats["season"] == y, "player_id"].unique())
        jr["stats_gsis_resolved_by_season"][str(y)] = {
            "players": len(ids), "resolved": len(ids & gsis_set),
            "rate": round(len(ids & gsis_set) / len(ids), 6)}
    jr["snap_pfr_resolved_by_season"] = {}
    for y in (2025, 2026):
        ids = set(snap.loc[snap["season"] == y, "pfr_player_id"].dropna().unique())
        jr["snap_pfr_resolved_by_season"][str(y)] = {
            "players": len(ids), "resolved": len(ids & pfr_set),
            "rate": round(len(ids & pfr_set) / len(ids), 6),
            "unresolved": sorted(ids - pfr_set)}

    # coverage + first computable dates
    cov = {}
    for y in SEASONS:
        d = df[df["season"] == y]
        cov[str(y)] = {
            "rows": int(len(d)), "games": int(len(d) // 2),
            "rows_g1g2_with_prior": int((d["n_prior_games_used"] > 0).sum()),
            "rows_flag_no_prior": int(d["flag_no_prior_in_corpus"].sum()),
            "rows_g3_computable": int(d["g3_n_snap_prior_games"].notna().sum()),
            "rows_flag_g3_no_snap": int(d["flag_g3_no_snap_prior"].sum()),
            "rows_flag_g3_pfr_null": int(d["flag_g3_pfr_null_excluded"].sum()),
            "rows_flag_g2_zero_usage": int(d["flag_g2_zero_usage"].sum()),
            "rows_flag_trunc_k3": int(d["flag_g1_window_truncated_k3"].sum()),
            "rows_flag_trunc_k5": int(d["flag_g1_window_truncated_k5"].sum()),
        }

    def first_date(mask) -> str | None:
        sub = df[mask]
        return sub.sort_values("kickoff_utc").iloc[0]["kickoff_utc"] if len(sub) else None

    fd = {
        "G1_G2_first_kickoff_utc": first_date(df["n_prior_games_used"] > 0),
        "G3_first_kickoff_utc": first_date((df["g3_n_snap_prior_games"].fillna(0) > 0)),
        "first_full_k5_window_utc": first_date(df["n_prior_games_used"] >= 5),
        "first_full_g3_k3_window_utc": first_date(df["g3_n_snap_prior_games"] >= 3),
    }
    fut = games[(games["season"] == 2026) & (~games["game_id"].isin(stat_gids))]
    fut_kick = fut["kickoff_utc_ts"].min().strftime("%Y-%m-%dT%H:%M:%SZ")

    write_manifest(args.outdir, df, n_games, sha_out, hashes, placeholder_rows,
                   jr, cov, fd, fut_kick)
    print("manifest: FEATURE_TABLE_MANIFEST.json written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
