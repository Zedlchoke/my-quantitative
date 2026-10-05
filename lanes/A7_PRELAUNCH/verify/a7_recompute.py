# a7_recompute.py — A7_NEGVERIFY OWN-CODE recompute. NOTHING here imports the
# T_SELECT lane: loader, Elo replay, metrics, bootstrap and synthetic streams are
# re-implemented from the frozen laws in the plan/dispatch. Recomputes ONLY the
# train-internal numbers already contained in SELECTION_LEDGER.jsonl (folds
# 2018-2021; warm-up 2016-2017 streams only). No OOS path is referenced.
#
# Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCHED = Path.home() / ".my-quantitative-data" / "nba-hoopr-v1" / "raw"
FEAT = Path.home() / ".my-quantitative-data" / "playerfeat-prep-v1" / "nba" / "features" / "nba_player_features_2016_2026.parquet"
LEDGER = Path("/Users/hoangminhlong/my-quantitative/.worktrees/nba-playerfeat-scored-v1/integration/lanes/T_SELECT/SELECTION_LEDGER.jsonl")
OUT = Path(__file__).resolve().parent / "a7_recompute_results.json"

SEASONS = range(2016, 2021 + 1)          # 2016..2021 ONLY — OOS files never referenced
FOLDS = (2018, 2019, 2020, 2021)
CUTOFF = pd.Timestamp("2021-08-01T00:00:00Z")
FRANCHISE = frozenset(range(1, 31))
K, HCA, GAMMA, INIT = 32.0, 100.0, 0.75, 1500.0
CLAMP = 1e-15
SEED = 20261005
PHI_GRID = (-50.0, -25.0, 0.0, 25.0, 50.0)
GROUPS = {"PF-A": ("a_top5_share_k5", "a_load_top5_k5"),
          "PF-B": ("b_form_top3",),
          "PF-C": ("c_abs_out", "c_abs_streak")}
MANIFEST_SEASONS = {2016: 2634, 2017: 2620, 2018: 2628, 2019: 2628, 2020: 2290,
                    2021: 2344, 2022: 2648, 2023: 2642, 2024: 2640, 2025: 2648, 2026: 2652}
CLAIM = {
    "b1_pooled_ll": 0.6383266072624096,
    "b1_slope": 0.780102170044627,
    "pf_a_m25_pooled_ll": 0.6433649811794481,
    "pf_a_m25_dell": 0.0050383739170385316,
    "pf_a_m25_ci": (0.001709972581109865, 0.00837455097972726),
    "pf_b_p25_pooled_ll": 0.6425738848940037,
    "pf_b_p25_dell": 0.004247277631594099,
    "pf_b_p25_ci": (0.0014798661130811898, 0.007118006020916947),
    "b0_pooled_ll": 0.684339489926359,
    "hca0_pooled_ll": 0.6428161170449253,
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------- own loader + replay
def load_corpus() -> pd.DataFrame:
    frames = []
    for s in SEASONS:
        frames.append(pd.read_csv(SCHED / f"nba_schedule_{s}.csv", low_memory=False))
    sch = pd.concat(frames, ignore_index=True)
    sch["tip_utc"] = pd.to_datetime(sch["game_date_time"], utc=True, format="mixed")
    sch["tip_date"] = sch["tip_utc"].dt.normalize()
    sch["played"] = (sch["status_type_name"] == "STATUS_FINAL") & sch["home_score"].notna() & sch["away_score"].notna()
    return sch


def replay(games: pd.DataFrame, hca: float = HCA):
    """Own Elo replay: date-grain same-day exclusion, gamma reversion before a
    lineage's first prediction of a new season, new lineages at INIT, binary
    update R += K*(S-E). Returns per-game elo_arg aligned to input order."""
    arg_out = np.empty(len(games))
    pos = {int(g): i for i, g in enumerate(games["game_id"].to_numpy())}
    g = games.reset_index(drop=True)
    rat: dict[int, float] = {}
    rev: dict[int, int] = {}
    n_upd = n_rev = 0
    for _d, day in g.groupby("tip_date", sort=True):
        day = day.sort_values("game_id", kind="mergesort")
        pend = []
        for r in day.itertuples(index=False):
            h, a, s = int(r.home_id), int(r.away_id), int(r.season)
            for t in (h, a):
                if t not in rat:
                    rat[t], rev[t] = INIT, None
            for t in (h, a):
                if rev[t] != s:
                    rat[t] = INIT + GAMMA * (rat[t] - INIT)
                    rev[t] = s
                    n_rev += 1
            pend.append((int(r.game_id), h, a, rat[h] + hca - rat[a]))
        for gid, h, a, arg in pend:
            p = 1.0 / (1.0 + math.pow(10.0, -arg / 400.0))
            r = g.loc[pos[gid]]
            y = float(r["y"])
            rat[h] += K * (y - p)
            rat[a] += K * ((1.0 - y) - (1.0 - p))
            n_upd += 1
            arg_out[pos[gid]] = arg
    return arg_out, n_upd, n_rev


def ll_rows(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    pc = np.clip(p, CLAMP, 1.0 - CLAMP)
    return -(y * np.log(pc) + (1.0 - y) * np.log1p(-pc))


def slope_glm(p: np.ndarray, y: np.ndarray):
    """Own IRLS: y ~ 1 + logit(p), binomial logit link, no penalty."""
    q = np.clip(p, CLAMP, 1.0 - CLAMP)
    eta = np.log(q) - np.log1p(-q)
    if float(np.ptp(eta)) == 0.0:
        return None
    X = np.column_stack([np.ones_like(eta), eta])
    beta = np.zeros(2)
    for _ in range(500):
        v = np.clip(X @ beta, -700, 700)
        mu = 1.0 / (1.0 + np.exp(-v))
        w = np.maximum(mu * (1.0 - mu), 1e-300)
        z = v + (y - mu) / w
        A = (X * w[:, None]).T @ X
        b = (X * w[:, None]).T @ z
        new = np.linalg.solve(A, b)
        d = float(np.max(np.abs(new - beta)))
        beta = new
        if d < 1e-13:
            break
    return float(beta[1])


def boot_ci(d: np.ndarray, dates: np.ndarray, n_boot: int = 10_000, seed: int = SEED,
            chunk: int = 500) -> tuple[float, float]:
    """OWN independent tip-DATE-clustered percentile bootstrap (different RNG
    consumption pattern + bincount aggregation vs the lane's np.add.at/1000-chunk)."""
    _keys, inv = np.unique(dates, return_inverse=True)
    inv = inv.ravel()
    ssum = np.bincount(inv, weights=d, minlength=int(inv.max()) + 1)
    scnt = np.bincount(inv, minlength=int(inv.max()) + 1).astype(np.float64)
    n_cl = len(ssum)
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for s in range(0, n_boot, chunk):
        b = min(chunk, n_boot - s)
        idx = rng.integers(0, n_cl, size=(b, n_cl))
        means[s:s + b] = ssum[idx].sum(axis=1) / scnt[idx].sum(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def boot_ci_pattern_match(d: np.ndarray, dates: np.ndarray, n_boot: int = 10_000,
                          seed: int = SEED) -> tuple[float, float]:
    """Faithful replication of the lane's documented scheme (np.add.at cluster
    sums + rng.integers in 1000-row chunks, sorted unique cluster order) as a
    byte-match cross-check of the pinned-seed CI."""
    uniq, inv = np.unique(np.asarray(dates), return_inverse=True)
    ssum = np.zeros(len(uniq)); scnt = np.zeros(len(uniq))
    np.add.at(ssum, inv.ravel(), d)
    np.add.at(scnt, inv.ravel(), 1.0)
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for s in range(0, n_boot, 1000):
        b = min(1000, n_boot - s)
        idx = rng.integers(0, len(uniq), size=(b, len(uniq)))
        means[s:s + b] = ssum[idx].sum(axis=1) / scnt[idx].sum(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


# --------------------------------------------------------------- own synthetics
def my_synth(seed: int, n_days: int = 150, teams: int = 12, season_len: int = 50):
    """A7's OWN synthetic stream generator (construction deliberately different
    from the lane's: variable games/day 2..4, random rest days, 3 season labels)."""
    rng = np.random.default_rng(seed)
    rows, gid = [], 770_000_000 + seed
    for d in range(n_days):
        season = 2016 + d // season_len
        date = pd.Timestamp("2001-03-01") + pd.Timedelta(days=d)
        for _ in range(2 + int(rng.integers(0, 3))):
            h, a = rng.choice(teams, size=2, replace=False)
            if rng.random() < 0.05:
                continue  # random rest day: team a skipped
            rows.append({"game_id": gid, "season": season, "tip_date": date,
                         "home_id": int(h), "away_id": int(a), "y": int(rng.random() < 0.57)})
            gid += 1
    return pd.DataFrame(rows)


def main() -> int:
    res: dict = {"role": "A7_NEGVERIFY own-code recompute", "ok": True}

    # -- 0. feature-table sha (own hash)
    res["feat_sha_parquet"] = sha256_file(FEAT)
    res["feat_sha_matches_manifest"] = res["feat_sha_parquet"] == "b3ca0e3b2eff1d1c918d56fb626e06998903c0f69253b41b67166dc8859885cb"

    # -- 1. corpus + counts
    sch = load_corpus()
    played = sch[sch["played"]].copy()
    assert int((played["home_score"] == played["away_score"]).sum()) == 0, "tie present"
    played["exhib"] = ~(played["home_id"].isin(FRANCHISE) & played["away_id"].isin(FRANCHISE))
    stream = played[(~played["exhib"]) & played["season_type"].isin([2, 3])].copy()
    stream["y"] = (stream["home_score"] > stream["away_score"]).astype(np.int64)
    stream = stream.sort_values(["tip_date", "game_id"], kind="mergesort").reset_index(drop=True)
    reg = played[(played["season_type"] == 2) & (~played["exhib"])].copy()
    reg["y"] = (reg["home_score"] > reg["away_score"]).astype(np.int64)
    reg = reg.sort_values(["tip_date", "game_id"], kind="mergesort").reset_index(drop=True)
    counts = {
        "schedule_rows_loaded": int(len(sch)),
        "played": int(len(played)),
        "postponed": int((~sch["played"]).sum()),
        "stream_games": int(len(stream)),
        "playin_played": int((played["season_type"] == 5).sum()),
        "exhib_in_window": int(played["exhib"].sum()),
        "exhib_in_fold_seasons": int(played.loc[played["exhib"], "season"].isin(FOLDS).sum()),
    }
    res["corpus_counts"] = counts

    # -- 2. B1* replay (warm-up 2016-17 streams, never scored) + fold rows
    arg, n_upd, n_rev = replay(stream[["game_id", "season", "tip_date", "home_id", "away_id", "y"]])
    res["stream_updates"] = n_upd
    res["season_reversions"] = n_rev
    argmap = {int(g): float(a) for g, a in zip(stream["game_id"], arg)}

    fold = reg[reg["season"].isin(FOLDS)].reset_index(drop=True)
    fold_rows_per = {int(s): int((fold["season"] == s).sum()) for s in FOLDS}
    res["fold_rows_per_season"] = fold_rows_per
    y = fold["y"].to_numpy(np.float64)
    dates = fold["tip_date"].to_numpy()
    a_fold = np.array([argmap[int(g)] for g in fold["game_id"]])
    p_b1 = 1.0 / (1.0 + np.power(10.0, -a_fold / 400.0))
    ll_b1 = ll_rows(p_b1, y)
    res["b1_pooled_ll"] = float(ll_b1.mean())
    res["b1_slope"] = slope_glm(p_b1, y)
    res["b1_ll_abs_err"] = abs(res["b1_pooled_ll"] - CLAIM["b1_pooled_ll"])
    res["b1_slope_abs_err"] = abs(res["b1_slope"] - CLAIM["b1_slope"])
    res["b1_pooled_ll_within_1e-9"] = res["b1_ll_abs_err"] < 1e-9
    res["b1_slope_within_1e-8"] = res["b1_slope_abs_err"] < 1e-8

    # -- 3. features: manifest per-season accounting + moments + group x
    ft = pd.read_parquet(FEAT)
    per_season = {int(k): int(v) for k, v in ft["season"].value_counts().items()}
    res["feat_per_season_matches_manifest"] = per_season == MANIFEST_SEASONS
    res["feat_rows_total"] = int(len(ft))
    res["feat_capped_rows_2016_2021"] = int((ft["season"] <= 2021).sum())
    res["neutral_per_season_capped"] = {int(k): int(v) for k, v in
                                        ft[ft["season"] <= 2021].groupby("season")["feature_neutral"].sum().items()}

    idx = ft.set_index(["game_id", "team_id"])
    scalars = sorted({c for g in GROUPS.values() for c in g})

    def sides(rows: pd.DataFrame):
        h = idx.loc[list(zip(rows["game_id"].astype(np.int64), rows["home_id"].astype(np.int64)))].reset_index()
        a = idx.loc[list(zip(rows["game_id"].astype(np.int64), rows["away_id"].astype(np.int64)))].reset_index()
        return h, a

    # moments population: team-side rows of REG played non-exhibition, tip < cutoff
    all_h, all_a = sides(reg)
    allside = pd.concat([all_h, all_a], ignore_index=True)
    mom = allside[allside["tip_utc"] < CUTOFF]
    mu = {c: float(mom[c].mean()) for c in scalars}
    sd = {c: float(mom[c].std(ddof=0)) for c in scalars}
    res["moments"] = {"mu": mu, "sd": sd, "n_rows": int(len(mom))}
    res["mom_n"] = int(len(mom))
    # season sanity of the moment population
    res["mom_seasons"] = sorted(int(s) for s in mom["season"].unique())

    def xdiff(arm: str, rows_h: pd.DataFrame, rows_a: pd.DataFrame) -> np.ndarray:
        xh = np.zeros(len(rows_h)); xa = np.zeros(len(rows_a))
        for c in GROUPS[arm]:
            xh += (rows_h[c].to_numpy(np.float64) - mu[c]) / sd[c]
            xa += (rows_a[c].to_numpy(np.float64) - mu[c]) / sd[c]
        return xh - xa

    fh, fa = sides(fold)
    res["fold_join_coverage_2x"] = (len(allside) == 2 * len(reg))

    def pf_p(argf: np.ndarray, arm: str, phi: float, rows_h, rows_a) -> np.ndarray:
        return 1.0 / (1.0 + np.power(10.0, -(argf + phi * xdiff(arm, rows_h, rows_a)) / 400.0))

    # designed-null on the REAL fold rows (own code): phi=0 == B1* bit-for-bit
    dp = {}
    for arm in GROUPS:
        p0 = pf_p(a_fold, arm, 0.0, fh, fa)
        dp[arm] = float(np.max(np.abs(p0 - p_b1)))
    res["real_designed_null_maxdp"] = dp
    res["real_designed_null_all_zero"] = all(v == 0.0 for v in dp.values())

    # -- 4. PF grid recompute: BOTH named points + full 3x5 grid points (pooled LL)
    grid_ll = {}
    for arm in GROUPS:
        grid_ll[arm] = {}
        for phi in PHI_GRID:
            p = pf_p(a_fold, arm, phi, fh, fa)
            grid_ll[arm][f"{phi:g}"] = float(ll_rows(p, y).mean())
    res["grid_pooled_ll_own"] = grid_ll
    res["grid_min_at_phi0"] = {arm: (min(v, key=v.get) == "0") for arm, v in grid_ll.items()}
    res["pf_a_m25_pooled_ll"] = grid_ll["PF-A"]["-25"]
    res["pf_b_p25_pooled_ll"] = grid_ll["PF-B"]["25"]
    res["pf_a_m25_pooled_ll_abs_err"] = abs(grid_ll["PF-A"]["-25"] - CLAIM["pf_a_m25_pooled_ll"])
    res["pf_b_p25_pooled_ll_abs_err"] = abs(grid_ll["PF-B"]["25"] - CLAIM["pf_b_p25_pooled_ll"])

    # -- 5. deltas + own bootstrap on the two named points
    for tag, arm, phi, cl in (("pf_a_m25", "PF-A", -25.0, CLAIM["pf_a_m25_ci"]),
                              ("pf_b_p25", "PF-B", 25.0, CLAIM["pf_b_p25_ci"])):
        p = pf_p(a_fold, arm, phi, fh, fa)
        d = ll_rows(p, y) - ll_b1
        res[f"{tag}_dell_point"] = float(d.mean())
        res[f"{tag}_dell_abs_err"] = abs(float(d.mean()) - {"pf_a_m25": CLAIM["pf_a_m25_dell"], "pf_b_p25": CLAIM["pf_b_p25_dell"]}[tag])
        lo_i, hi_i = boot_ci(d, dates)
        lo_m, hi_m = boot_ci_pattern_match(d, dates)
        res[f"{tag}_ci_own_independent"] = [lo_i, hi_i]
        res[f"{tag}_ci_pattern_match"] = [lo_m, hi_m]
        res[f"{tag}_ci_claimed"] = list(cl)
        res[f"{tag}_ci_own_abs_err"] = [abs(lo_i - cl[0]), abs(hi_i - cl[1])]
        res[f"{tag}_ci_patternmatch_bitexact"] = (lo_m == cl[0] and hi_m == cl[1])

    # -- 6. B0 + B1-HCA0 (ledger-contained numbers, recomputed)
    consts = {int(s): float(reg.loc[reg["season"] < s, "y"].mean()) for s in FOLDS}
    b0p = np.array([consts[int(s)] for s in fold["season"]])
    res["b0_constants_own"] = {str(k): v for k, v in consts.items()}
    res["b0_pooled_ll"] = float(ll_rows(b0p, y).mean())
    res["b0_pooled_ll_abs_err"] = abs(res["b0_pooled_ll"] - CLAIM["b0_pooled_ll"])
    arg0, _, _ = replay(stream[["game_id", "season", "tip_date", "home_id", "away_id", "y"]], hca=0.0)
    m0 = {int(g): float(a) for g, a in zip(stream["game_id"], arg0)}
    p0h = 1.0 / (1.0 + np.power(10.0, -np.array([m0[int(g)] for g in fold["game_id"]]) / 400.0))
    res["hca0_pooled_ll"] = float(ll_rows(p0h, y).mean())
    res["hca0_pooled_ll_abs_err"] = abs(res["hca0_pooled_ll"] - CLAIM["hca0_pooled_ll"])

    # -- 7. designed-null on A7's OWN synthetic stream (own replay, own x)
    syn_ok = {}
    for sd_ in (101, 202, 303):
        st = my_synth(sd_)
        a_s, _, _ = replay(st)
        rng = np.random.default_rng(sd_ + 1)
        xh = rng.chisquare(3.0, size=len(st))
        xa = rng.chisquare(3.0, size=len(st))
        pb = 1.0 / (1.0 + np.power(10.0, -a_s / 400.0))
        pp = 1.0 / (1.0 + np.power(10.0, -(a_s + 0.0 * (xh - xa)) / 400.0))
        syn_ok[f"seed{sd_}"] = float(np.max(np.abs(pp - pb)))
    res["own_synthetic_designed_null_maxdp"] = syn_ok
    res["own_synthetic_designed_null_all_zero"] = all(v == 0.0 for v in syn_ok.values())

    # -- 8. extra report claims cross-checked
    res["playoff_rows"] = int(((played["season_type"] == 3) & (~played["exhib"]) & played["season"].isin(FOLDS)).sum())
    res["neutral_site_true_fold_rows"] = int((fold["neutral_site"].astype(str) == "True").sum()) if fold["neutral_site"].dtype == bool else int((fold["neutral_site"].astype(str).str.lower() == "true").sum())

    res["ok"] = bool(
        res["feat_sha_matches_manifest"] and res["feat_per_season_matches_manifest"]
        and res["b1_pooled_ll_within_1e-9"] and res["b1_slope_within_1e-8"]
        and res["real_designed_null_all_zero"] and res["own_synthetic_designed_null_all_zero"]
        and all(res["grid_min_at_phi0"].values())
        and res["pf_a_m25_dell_abs_err"] < 1e-9 and res["pf_b_p25_dell_abs_err"] < 1e-9
        and res["pf_a_m25_pooled_ll_abs_err"] < 1e-9 and res["pf_b_p25_pooled_ll_abs_err"] < 1e-9
        and max(res["pf_a_m25_ci_own_abs_err"]) < 5e-4 and max(res["pf_b_p25_ci_own_abs_err"]) < 5e-4
        and res["b0_pooled_ll_abs_err"] < 1e-9 and res["hca0_pooled_ll_abs_err"] < 1e-9
    )
    OUT.write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps(res, indent=2, default=str))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
