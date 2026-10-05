# a7_recompute.py — A7 INDEPENDENT PRELAUNCH AUDIT · own-code recompute (A7-2/A7-3 real part)
#
# WRITTEN FRESH by the auditor from the frozen engine-law TEXT (arms.py header comment +
# SELECTION_REPORT §2). Does NOT import arms.py or harness.py. Audits, never repairs.
# Reads ONLY real seasons <= 2018 (train-internal recomputation of the SAME numbers).
# No OOS access; no writes outside lanes/A7_PRELAUNCH/tmp.
#
# Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python (only).

import gzip
import hashlib
import json
import math
import os

import numpy as np
import pandas as pd

HOME = os.path.expanduser("~")
FEATURE_PARQUET = HOME + "/.my-quantitative-data/playerfeat-prep-v1/wnba/features/wnba_player_features_2002_2026.parquet"
FEATURE_SHA256 = "ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf"
LINEAGE_CSV = HOME + "/.my-quantitative-data/wnba-prep-v1/team_key_table.csv"
ESPN_DIR = HOME + "/.my-quantitative-data/wnba-v1/raw/espn_schedules"
STATS_DIR = HOME + "/.my-quantitative-data/wnba-v1/raw/wnba_stats_schedules"
OUT_DIR = HOME + "/.my-quantitative-data/wnba-playerfeat-scored-v1/selection"
A7_TMP = ("/Users/hoangminhlong/my-quantitative/.worktrees/wnba-playerfeat-scored-v1/"
          "integration/lanes/A7_PRELAUNCH/tmp")

SEASON_MAX_REAL = 2018
SEASON_MIN_REAL = 2002
WARMUP_SEASONS = (1997, 1998, 1999, 2000, 2001)
BLOCKS = ((2011, 2012), (2013, 2014), (2015, 2016), (2017, 2018))
BLOCK_SEASONS = tuple(s for b in BLOCKS for s in b)
GRID_K = (8.0, 16.0, 32.0)
GRID_HCA = (0.0, 50.0, 100.0)
GRID_GAMMA = (0.65, 0.75, 0.85)
GRID_PHI = (-50.0, -25.0, 0.0, 25.0, 50.0)
SEED = 20261005
LEAGUE_MEAN = 1500.0
SCALE = 400.0
LL_EPS = 1e-15
ALL_STAR_ALIASES = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE",
                    "CLA", "COL", "SPO", "COOP", "WNBASTARS"}
XB_COL, XB_REASON = "b5_minutes_hhi", "b5_neutral_reason"
XC_COL, XC_REASON = "c_absence_share", "c_neutral_reason"

results = {}


def check(name, ok, detail=""):
    results[name] = {"ok": bool(ok), "detail": detail}
    print(("PASS " if ok else "FAIL ") + name + ("  " + detail if detail else ""))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- my own engine
def run_engine(games, k=None, hca=None, gamma=None, phi=None, x_fn=None, c_fn=None,
               p0=None):
    """Independent implementation of the frozen law:
    p = 1/(1+10^(-(Rh-Ra+HCA_eff+phi*(xh-xa))/400)); R += K*(outcome - expectation)
    with away expectation 1-p; season open: R = 1500 + gamma*(R_end-1500) (new
    franchise 1500); identical-tip games predicted from one snapshot then updated;
    neutral rows HCA_eff=0. c_fn (when given) modulates the season-open prior as
    1500 + gamma*c*(R_end-1500) through the SAME arithmetic (c=1 is an exact no-op
    by IEEE identity: 1.0*x == x)."""
    r = {}
    last_season = {}
    preds = []
    i, n = 0, len(games)
    while i < n:
        tip = games[i]["tip"]
        j = i
        batch = []
        while j < n and games[j]["tip"] == tip:
            batch.append(games[j])
            j += 1
        ctx = []
        for g in batch:
            hca_eff = 0.0 if g["neutral"] else hca
            c_h = c_fn(g["row_home"], g["season"]) if c_fn is not None else None
            c_a = c_fn(g["row_away"], g["season"]) if c_fn is not None else None
            rh = _eff(g["fk_home"], g["season"], gamma, c_h, r, last_season, c_fn)
            ra = _eff(g["fk_away"], g["season"], gamma, c_a, r, last_season, c_fn)
            arg = rh - ra + hca_eff
            if x_fn is not None:
                xh, _ = x_fn(g["row_home"], g["season"])
                xa, _ = x_fn(g["row_away"], g["season"])
                arg = arg + phi * (xh - xa)
            p_home = p0 if p0 is not None else 1.0 / (1.0 + 10.0 ** (-arg / SCALE))
            ctx.append((g, p_home))
            preds.append({"game_id": g["game_id"], "season": g["season"],
                          "p_home": p_home, "home_win": g["home_win"],
                          "neutral": g["neutral"]})
        if p0 is None:
            for g, p_home in ctx:
                y = float(g["home_win"])
                r[g["fk_home"]] = r[g["fk_home"]] + k * (y - p_home)
                r[g["fk_away"]] = r[g["fk_away"]] + k * ((1.0 - y) - (1.0 - p_home))
        i = j
    return preds


def _eff(fk, season, gamma, c, r, last_season, c_fn):
    if last_season.get(fk) != season:
        if fk in r:
            if c_fn is not None:
                r[fk] = LEAGUE_MEAN + gamma * c * (r[fk] - LEAGUE_MEAN)
            else:
                r[fk] = LEAGUE_MEAN + gamma * (r[fk] - LEAGUE_MEAN)
        else:
            r[fk] = LEAGUE_MEAN
        last_season[fk] = season
    return r[fk]


def log_loss(p, y):
    pc = min(max(p, LL_EPS), 1.0 - LL_EPS)
    return -(y * math.log(pc) + (1 - y) * math.log(1 - pc))


def mean_ll(preds):
    return sum(log_loss(d["p_home"], d["home_win"]) for d in preds) / len(preds)


def pooled_ll(preds, seasons):
    pts = [d for d in preds if d["season"] in seasons]
    return sum(log_loss(d["p_home"], d["home_win"]) for d in pts) / len(pts), len(pts)


def hexstream(preds):
    return [float(d["p_home"]).hex() for d in preds]


# ---------------------------------------------------------------- my own loaders
def load_all():
    dig = sha256_file(FEATURE_PARQUET)
    check("A2_feature_sha_matches_manifest", dig == FEATURE_SHA256, dig[:16] + "…")

    ft = pd.read_parquet(FEATURE_PARQUET)
    n_total = len(ft)
    ft = ft[ft["season"] <= SEASON_MAX_REAL]
    rows, games_index = {}, {}
    for r in ft.itertuples(index=False):
        gid, side = str(r.game_id), str(r.team_side)
        rows[(gid, side)] = {
            "season": int(r.season),
            "franchise_key": str(r.franchise_key),
            "continuity_c": None if pd.isna(r.continuity_c) else float(r.continuity_c),
            "continuity_neutral_reason": str(r.continuity_neutral_reason),
            "xb": None if pd.isna(getattr(r, XB_COL)) else float(getattr(r, XB_COL)),
            "xb_reason": str(getattr(r, XB_REASON)),
            "xc": None if pd.isna(getattr(r, XC_COL)) else float(getattr(r, XC_COL)),
            "xc_reason": str(getattr(r, XC_REASON)),
        }
        g = games_index.setdefault(gid, {"season": int(r.season), "sides": {}})
        g["sides"][side] = int(r.team_id)
    check("A2_feature_rows_2_per_game", len(rows) == 2 * len(games_index),
          "%d rows / %d games (total file rows %d)" % (len(rows), len(games_index), n_total))

    # ESPN universe, seasons 2002..2018 only
    frames = []
    for year in range(SEASON_MIN_REAL, SEASON_MAX_REAL + 1):
        p = os.path.join(ESPN_DIR, "wnba_schedule_%d.csv" % year)
        frames.append(pd.read_csv(p, dtype={"game_id": str, "id": str}))
    esp = pd.concat(frames, ignore_index=True)
    post = esp["status_type_state"] == "post"
    bad = (esp["status_type_name"].isin(["Forfeit", "Postponed"])
           | esp["status_type_description"].fillna("").isin(["Forfeit", "Postponed"])
           | esp["status_type_short_detail"].fillna("").isin(["Forfeit", "Postponed"]))
    alias = (esp["home_abbreviation"].isin(ALL_STAR_ALIASES)
             | esp["away_abbreviation"].isin(ALL_STAR_ALIASES))
    uni = esp[post & ~bad & ~alias]
    uni = uni[uni["season"] <= SEASON_MAX_REAL]
    got, want = set(uni["game_id"].astype(str)), set(games_index)
    check("A2_universe_identity_vs_feature_table", got == want,
          "missing %d extra %d" % (len(want - got), len(got - want)))

    games = []
    for r in uni.itertuples(index=False):
        gid = str(r.game_id)
        fi = games_index[gid]
        assert fi["season"] == int(r.season)
        games.append({
            "tip": pd.Timestamp(str(r.date)).tz_convert("UTC"),
            "game_id": gid, "season": int(r.season),
            "fk_home": rows[(gid, "home")]["franchise_key"],
            "fk_away": rows[(gid, "away")]["franchise_key"],
            "home_win": int(int(r.home_score) > int(r.away_score)),
            "neutral": bool(r.neutral_site) if not pd.isna(r.neutral_site) else False,
            "row_home": rows[(gid, "home")], "row_away": rows[(gid, "away")],
        })
    check("A2_train_games_3995", len(games) == 3995, str(len(games)))

    # lineage + warm-up (stream-only)
    lin = pd.read_csv(LINEAGE_CSV, keep_default_na=False)
    abbr2fk = {}
    for _, r in lin.iterrows():
        for a in str(r["stats_abbrs"]).split(";"):
            a = a.strip()
            if a:
                abbr2fk.setdefault(a, set()).add(str(r["franchise_key"]).strip())
    check("A2_lineage_unambiguous", all(len(v) == 1 for v in abbr2fk.values()),
          "%d abbrs" % len(abbr2fk))
    abbr2fk = {a: next(iter(v)) for a, v in abbr2fk.items()}
    warm = []
    for year in WARMUP_SEASONS:
        with gzip.open(os.path.join(STATS_DIR, "wnba_schedule_%d.csv.gz" % year), "rt") as f:
            df = pd.read_csv(f, dtype={"game_id": str})
        for r in df.itertuples(index=False):
            hk = abbr2fk.get(str(r.home_team_abbreviation).strip())
            ak = abbr2fk.get(str(r.away_team_abbreviation).strip())
            assert hk and ak
            warm.append({
                "tip": pd.Timestamp(str(r.game_date)).tz_localize("UTC"),
                "game_id": "W%d-%s" % (year, r.game_id), "season": int(r.season),
                "fk_home": hk, "fk_away": ak,
                "home_win": int(int(r.home_pts) > int(r.away_pts)),
                "neutral": False, "row_home": None, "row_away": None,
            })
    check("A2_warmup_rows_1022", len(warm) == 1022, str(len(warm)))
    check("A2_warmup_seasons_stream_only",
          max(g["season"] for g in warm) == 2001 and min(g["season"] for g in warm) == 1997)

    full = sorted(warm + games, key=lambda g: (g["tip"], g["game_id"]))
    return rows, games, warm, full


# ----------------------------------------------- my own bootstrap (same procedure)
def cluster_bootstrap(dll, clusters, n=10000, seed=SEED):
    d = np.asarray(dll, dtype=np.float64)
    c = np.asarray(clusters)
    uniq, inv = np.unique(c, return_inverse=True)
    sums = np.zeros(len(uniq))
    counts = np.zeros(len(uniq))
    np.add.at(sums, inv, d)
    np.add.at(counts, inv, 1.0)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(uniq), size=(n, len(uniq)))
    means = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi)


def main():
    rows, train_games, warm_games, full_games = load_all()

    # ---- B0 constant
    p0 = sum(g["home_win"] for g in train_games) / float(len(train_games))
    check("A2_B0_matches_frozen", abs(p0 - 0.6037546933667084) < 1e-12,
          "%.16f" % p0)

    # ---- ledger expectations
    ledger = [json.loads(l) for l in open(os.path.join(OUT_DIR, "SELECTION_LEDGER.jsonl"))]
    grid_rows = {r["run_id"]: r for r in ledger if r["run_id"].startswith("B1_grid_K")}

    # ---- all 27 grid configs with MY engine
    max_diff = 0.0
    worst = None
    matched = 0
    for k in GRID_K:
        for hca in GRID_HCA:
            for gamma in GRID_GAMMA:
                preds, _n = None, None
                preds = run_engine(full_games, k=k, hca=hca, gamma=gamma)
                pool, npool = pooled_ll(preds, BLOCK_SEASONS)
                rid = "B1_grid_K%d_HCA%d_G%.2f" % (k, hca, gamma)
                theirs = grid_rows[rid]["mean_ll_pooled"]
                d = abs(pool - theirs)
                if d > max_diff:
                    max_diff, worst = d, (rid, pool, theirs)
                if d < 1e-9:
                    matched += 1
                assert npool == grid_rows[rid]["n_games_scored"] == 1774, (rid, npool)
    check("A2_grid_27_points_match_ledger_within_1e-9", matched == 27,
          "matched %d/27; max|dLL|=%.3e at %s (mine %.15f theirs %.15f)"
          % (matched, max_diff, worst[0], worst[1], worst[2]))

    # ---- winner recompute
    winner = run_engine(full_games, k=32.0, hca=50.0, gamma=0.65)
    win_pool, n_val = pooled_ll(winner, BLOCK_SEASONS)
    check("A2_winner_pooled_LL_within_1e-9",
          abs(win_pool - 0.6234977203164429) < 1e-9,
          "mine %.15f theirs 0.6234977203164429  n_val=%d" % (win_pool, n_val))
    train_pool, _ = pooled_ll(winner, tuple(range(SEASON_MIN_REAL, SEASON_MAX_REAL + 1)))
    check("A2_winner_train_LL_context", abs(train_pool - 0.6365409377868896) < 1e-9,
          "%.15f" % train_pool)

    # ---- kill test vs B0 (same 1774 validation games)
    val = [d for d in winner if d["season"] in BLOCK_SEASONS]
    b0_val = [p0] * len(val)
    dll = [log_loss(d["p_home"], d["home_win"]) - log_loss(p0, d["home_win"])
           for d in val]
    clusters = [str(pd.Timestamp(d["tip"]).date()) if False else None for d in []]  # placeholder
    # clusters from tips: rebuild from train/warm games by game_id
    tip_by_gid = {g["game_id"]: g["tip"] for g in full_games}
    clusters = [str(tip_by_gid[d["game_id"]].date()) for d in val]
    pt, lo, hi = cluster_bootstrap(dll, clusters)
    check("A2_killtest_point_matches", abs(pt - (-0.054386188557277046)) < 1e-9,
          "mine %.15f theirs -0.054386188557277046" % pt)
    check("A2_killtest_ci_direction_negative_excl_0", lo < 0 and hi < 0,
          "mine [%.6f, %.6f] theirs [-0.070150, -0.038275]" % (lo, hi))

    # ---- named spot points (dispatch example + one more)
    for (k, hca, gamma) in ((16.0, 100.0, 0.75), (8.0, 0.0, 0.85), (32.0, 0.0, 0.65)):
        preds = run_engine(full_games, k=k, hca=hca, gamma=gamma)
        pool, _ = pooled_ll(preds, BLOCK_SEASONS)
        rid = "B1_grid_K%d_HCA%d_G%.2f" % (k, hca, gamma)
        d = abs(pool - grid_rows[rid]["mean_ll_pooled"])
        check("A2_spot_%s" % rid, d < 1e-9, "|d|=%.3e" % d)

    # ---- moments recompute (pinned)
    for col, rkey, key, (tm, tsd, tn) in (
            (XB_COL, "xb_reason", "wf_b", (0.11779397266213801, 0.010038602475927519, 2292)),
            (XC_COL, "xc_reason", "wf_c", (0.10769934328912245, 0.10354795612490496, 2292))):
        vcol = "xb" if col == XB_COL else "xc"
        vals = [row[vcol] for row in rows.values()
                if row["season"] <= SEASON_MAX_REAL and row[rkey] == ""]
        mu = sum(vals) / len(vals)
        sd = (sum((v - mu) ** 2 for v in vals) / len(vals)) ** 0.5
        check("A2_moments_%s" % key,
              len(vals) == tn and abs(mu - tm) < 1e-12 and abs(sd - tsd) < 1e-12,
              "n=%d mean=%.15f sd=%.15f" % (len(vals), mu, sd))

    # ---- designed null on REAL data (my engine, my x_fn)
    def x_fn_factory(col, rkey):
        vcol = "xb" if col == XB_COL else "xc"
        vals = [row[vcol] for row in rows.values()
                if row["season"] <= SEASON_MAX_REAL and row[rkey] == ""]
        mu = sum(vals) / len(vals)
        sd = (sum((v - mu) ** 2 for v in vals) / len(vals)) ** 0.5

        def x_fn(row, season):
            if row is None:
                return 0.0, None
            if row["season"] < 2013:
                return 0.0, "era_floor"
            if row[rkey] != "":
                return 0.0, "neutral_x0"
            return (row[vcol] - mu) / sd, None
        return x_fn

    parent = run_engine(full_games, k=32.0, hca=50.0, gamma=0.65)
    xb_fn = x_fn_factory(XB_COL, "xb_reason")
    null_phi = run_engine(full_games, k=32.0, hca=50.0, gamma=0.65,
                          phi=0.0, x_fn=xb_fn)
    null_c = run_engine(full_games, k=32.0, hca=50.0, gamma=0.65,
                        c_fn=lambda row, season: 1.0)
    hp = hexstream(parent)
    check("A3_real_phi0_byte_identity", hexstream(null_phi) == hp,
          "%d corpus games (warm-up 1022 + train 3995)" % len(hp))
    check("A3_real_c1_byte_identity", hexstream(null_c) == hp)

    # ---- my parent stream vs the persisted frozen parquet (independent-impl agreement)
    frozen_stream = pd.read_parquet(os.path.join(OUT_DIR, "b1_frozen_p_stream_train.parquet"))
    mine = {d["game_id"]: d["p_home"] for d in parent
            if SEASON_MIN_REAL <= d["season"] <= SEASON_MAX_REAL}
    theirs = dict(zip(frozen_stream["game_id"].astype(str), frozen_stream["p_home"].astype(float)))
    check("A2_persisted_stream_game_set", set(mine) == set(theirs),
          "%d vs %d rows" % (len(mine), len(theirs)))
    bit = sum(1 for gid in mine if float(mine[gid]).hex() == float(theirs[gid]).hex())
    maxdp = max(abs(mine[g] - theirs[g]) for g in mine)
    check("A2_persisted_stream_agreement", maxdp < 1e-9,
          "bit-identical %d/%d; max|dp|=%.3e" % (bit, len(mine), maxdp))

    # ---- WF-B phi=0 fold LL == parent fold LL (ledger corroboration of release math)
    led = {r["run_id"]: r for r in ledger}
    summary = json.load(open(os.path.join(OUT_DIR, "SELECTION_SUMMARY.json")))
    parent_fold_ll = summary["feature_arms"]["WF-B"]["parent_fold_mean_ll"]
    check("A5_wfb_phi0_ll_equals_parent",
          led["WF-B_fit_phi+0"]["mean_ll_pooled"] == parent_fold_ll
          == led["GENTRY_WF-B"]["mean_ll_pooled"] == 0.6329277455499628)
    check("A5_wfc_phi0_ll_equals_parent",
          led["WF-C_fit_phi+0"]["mean_ll_pooled"] == parent_fold_ll
          == led["GENTRY_WF-C"]["mean_ll_pooled"] == 0.6329277455499628)
    # every nonzero phi strictly worse than phi=0 (phi=0 optimal -> RELEASE justified)
    for arm, pref in (("WF-B", "WF-B_fit_phi"), ("WF-C", "WF-C_fit_phi")):
        lls = {p: led["%s%+g" % (pref, p)]["mean_ll_pooled"] for p in GRID_PHI}
        ok = all(lls[0.0] < lls[p] for p in GRID_PHI if p != 0.0)
        check("A5_%s_phi0_optimal" % arm, ok,
              " ".join("%+g:%.6f" % (p, v) for p, v in sorted(lls.items())))

    with open(os.path.join(A7_TMP, "a7_recompute_out.json"), "w") as f:
        json.dump(results, f, indent=1, sort_keys=True)
    n_fail = sum(1 for v in results.values() if not v["ok"])
    print("A7-RECOMPUTE %s (%d checks, %d failed)"
          % ("PASS" if n_fail == 0 else "FAIL", len(results), n_fail))
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
