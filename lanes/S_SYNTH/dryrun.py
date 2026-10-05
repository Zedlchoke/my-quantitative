# dryrun.py — WNBA-PLAYERFEAT-SCORED-V1 · lane S_SYNTH · synthetic OOS-like rehearsal
#
# Runs the FULL 2-arm evaluation path (B0 const 0.603755 + B1-WNBA K=32/HCA=50/gamma=0.65)
# on SYNTHETIC corpus files in the real corpus formats (ESPN-like schedules + feature-table
# parquet), importing the FROZEN lane T_SELECT code as-is (no modification; frozen bytes
# pinned by sha256 and asserted). Nothing real is scored: all game ids are SYNTH_-prefixed
# and every synthetic season is >= 2027 (real OOS window [2020..2026] is never touched).
#
# Language law: calibration/forecasting vocabulary only.
# Determinism: seed 20261005 everywhere; no wall-clock inside outputs.
# Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import sys

INTEGRATION = "/Users/hoangminhlong/my-quantitative/.worktrees/wnba-playerfeat-scored-v1/integration"
T_SELECT_DIR = os.path.join(INTEGRATION, "lanes/T_SELECT")
LANE_DIR = os.path.join(INTEGRATION, "lanes/S_SYNTH")

sys.path.insert(0, T_SELECT_DIR)
import arms  # noqa: E402  (frozen)
import harness  # noqa: E402  (frozen)

SEED = 20261005
B0_P0 = 0.603755                      # frozen train-window rate (T_SELECT report section 3)
B1_CFG = {"k": 32.0, "hca": 50.0, "gamma": 0.65}   # frozen B1-WNBA (T_SELECT report section 4)
WARMUP_SEASONS = (2027, 2028)         # synthetic warm-up analog (stream-only, no features)
SCORED_SEASONS = (2029, 2030)         # synthetic OOS-like folds (the 2 scored seasons)
FROZEN_SHA = {                        # pinned from lanes/DISPATCH/handoff_T_SELECT.json
    "harness.py": "b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e",
    "arms.py": "82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3",
}
TEAMS = ["SY_A", "SY_B", "SY_C", "SY_D", "SY_E", "SY_F", "SY_G", "SY_H"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Loud(AssertionError):
    """Any rehearsal check failure must fail LOUD (nonzero exit)."""


# ------------------------------------------------------------------ corpus generation
def generate_corpus(out_dir):
    """Deterministic synthetic corpus in the real corpus formats.

    - warm-up seasons 2027-2028: ESPN-like schedule CSVs, single round robin,
      one game/day; stream-only rows (no feature rows; loader will attach None).
    - scored seasons 2029-2030: ESPN-like schedule CSVs (all ordered pairings,
      4 games/date on 2 exact tips per date -> same-tip batching + date clusters)
      + feature-table-format parquet (2 rows per game, real corpus column names,
      incl. neutral-reason feature columns and game-1 v2 continuity rows).
    """
    import pandas as pd
    import random
    corpus_dir = os.path.join(out_dir, "synth_corpus")
    os.makedirs(corpus_dir, exist_ok=True)
    rng = random.Random(SEED)
    # planted signal strong enough that the rehearsal demonstrates the frozen
    # engine TRACKING it end-to-end (a sign-flip would be caught); the frozen
    # B0/B1 scalars/config stay untouched.
    strength = {fk: 1500.0 + 250.0 * rng.uniform(-1, 1) for fk in TEAMS}

    def p_true(fk_h, fk_a, neutral):
        return 1.0 / (1.0 + 10.0 ** (-(strength[fk_h] - strength[fk_a] + (0.0 if neutral else 60.0)) / 400.0))

    tid = {fk: 101 + i for i, fk in enumerate(TEAMS)}
    games = []  # scored games (dict form, reused by loader-shaped in-memory path)

    # ---- warm-up schedules (CSV, ESPN-like columns)
    for season in WARMUP_SEASONS:
        day = dt.datetime(season, 6, 1, tzinfo=dt.timezone.utc)
        rows = []
        for i, a in enumerate(TEAMS):
            for b in TEAMS[i + 1:]:
                home, away = (a, b) if rng.random() < 0.5 else (b, a)
                rows.append({
                    "game_id": "SYNTH_W%d-%03d" % (season, len(rows)),
                    "season": season,
                    "tip_utc": day.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "home_franchise_key": home, "away_franchise_key": away,
                    "home_win": int(rng.random() < p_true(home, away, False)),
                    "neutral_site": False,
                })
                day += dt.timedelta(days=1)
        pd.DataFrame(rows).to_csv(os.path.join(corpus_dir, "warmup_schedule_%d.csv" % season), index=False)

    # ---- scored schedules + feature-table parquet
    first_seen = {}   # (season, fk) -> game_id of the team's season game 1 (by stream order)
    for season in SCORED_SEASONS:
        pairs = [(a, b) for a in TEAMS for b in TEAMS if a != b]
        assert len(pairs) == 56
        sched, feats = [], []
        for slot, (home, away) in enumerate(pairs):
            date_idx, half = divmod(slot, 4)
            day = dt.datetime(season, 6, 1, tzinfo=dt.timezone.utc) + dt.timedelta(days=date_idx)
            tip = day.replace(hour=18 if half in (0, 1) else 20, minute=30 if half in (2, 3) else 0)
            neutral = slot in (12, 37)          # exactly 2 neutral-site rows per scored season
            gid = "SYNTH_%d-G%03d" % (season, slot)
            home_win = int(rng.random() < p_true(home, away, neutral))
            sched.append({
                "game_id": gid, "season": season,
                "tip_utc": tip.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "home_franchise_key": home, "away_franchise_key": away,
                "home_team_id": tid[home], "away_team_id": tid[away],
                "home_win": home_win, "neutral_site": bool(neutral),
            })
            for side, fk in (("home", home), ("away", away)):
                key = (season, fk)
                is_g1 = key not in first_seen
                if is_g1:
                    first_seen[key] = gid
                xb = None if rng.random() < 0.2 else round(0.08 + 0.08 * rng.random(), 6)
                xc = None if rng.random() < 0.2 else round(0.02 + 0.20 * rng.random(), 6)
                feats.append({
                    "game_id": gid, "season": season, "team_side": side,
                    "team_id": tid[fk], "franchise_key": fk,
                    "tip_utc": tip.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "is_team_game1": is_g1,
                    "continuity_c": (None if is_g1 else round(0.55 + 0.45 * rng.random(), 6)),
                    "continuity_neutral_reason": ("game1_v2_no_prior" if is_g1 else ""),
                    "b5_minutes_hhi": xb,
                    "b5_neutral_reason": ("expansion_rotation" if xb is None else ""),
                    "c_absence_share": xc,
                    "c_neutral_reason": ("insufficient_history" if xc is None else ""),
                })
        pd.DataFrame(sched).to_csv(os.path.join(corpus_dir, "scored_schedule_%d.csv" % season), index=False)
        pd.DataFrame(feats).to_parquet(os.path.join(corpus_dir, "scored_features_%d.parquet" % season), index=False)
        games.extend(sched)
    games.sort(key=lambda g: (g["tip_utc"], g["game_id"]))
    return corpus_dir, strength


# ------------------------------------------------------------------ corpus loading (file round-trip)
def load_corpus(corpus_dir):
    """Read the synthetic corpus FILES back and build the frozen-code dict shapes:
    warm-up rows carry row_home/row_away=None (stats-side warm-up law mirror);
    scored rows get light feature rows via the sanctioned (game_id, side) join
    (harness.attach_feature_sides equivalent, filled from the parquet)."""
    import pandas as pd
    warmup, scored = [], []
    feat_rows = {}
    for season in SCORED_SEASONS:
        ft = pd.read_parquet(os.path.join(corpus_dir, "scored_features_%d.parquet" % season))
        for r in ft.itertuples(index=False):
            row = {
                "season": int(r.season), "team_id": int(r.team_id),
                "franchise_key": str(r.franchise_key), "tip_utc": str(r.tip_utc),
                "is_team_game1": bool(r.is_team_game1),
                "continuity_c": None if pd.isna(r.continuity_c) else float(r.continuity_c),
                "continuity_neutral_reason": str(r.continuity_neutral_reason),
                "xb": None if pd.isna(getattr(r, "b5_minutes_hhi")) else float(getattr(r, "b5_minutes_hhi")),
                "xb_reason": str(getattr(r, "b5_neutral_reason")),
                "xc": None if pd.isna(getattr(r, "c_absence_share")) else float(getattr(r, "c_absence_share")),
                "xc_reason": str(getattr(r, "c_neutral_reason")),
            }
            feat_rows[(str(r.game_id), str(r.team_side))] = row

    def _sched(path, warm):
        df = pd.read_csv(path, dtype={"game_id": str})
        out = []
        for r in df.itertuples(index=False):
            gid = str(r.game_id)
            if not gid.startswith("SYNTH_"):
                raise Loud("non-SYNTH id in synthetic corpus: %s" % gid)
            if int(r.season) < 2027:
                raise Loud("synthetic season < 2027: %s" % gid)
            g = {
                "tip": pd.Timestamp(str(r.tip_utc)), "game_id": gid,
                "season": int(r.season),
                "fk_home": str(r.home_franchise_key), "fk_away": str(r.away_franchise_key),
                "home_win": int(r.home_win), "neutral": bool(r.neutral_site),
                "row_home": None, "row_away": None,
            }
            if not warm:
                rh, ra = feat_rows.get((gid, "home")), feat_rows.get((gid, "away"))
                if rh is None or ra is None:
                    raise Loud("feature rows missing for %s" % gid)
                if rh["franchise_key"] != g["fk_home"] or ra["franchise_key"] != g["fk_away"]:
                    raise Loud("franchise mismatch on %s" % gid)
                g["row_home"], g["row_away"] = rh, ra
            out.append(g)
        return out

    for season in WARMUP_SEASONS:
        warmup.extend(_sched(os.path.join(corpus_dir, "warmup_schedule_%d.csv" % season), warm=True))
    for season in SCORED_SEASONS:
        scored.extend(_sched(os.path.join(corpus_dir, "scored_schedule_%d.csv" % season), warm=False))

    if len(set(g["game_id"] for g in warmup + scored)) != len(warmup) + len(scored):
        raise Loud("duplicate game_id in synthetic corpus")
    warmup.sort(key=lambda g: (g["tip"], g["game_id"]))
    scored.sort(key=lambda g: (g["tip"], g["game_id"]))
    full = harness.build_full_games(warmup, scored)
    return warmup, scored, full


# ------------------------------------------------------------------ metrics (driver side, deterministic)
def brier_score(preds):
    if not preds:
        return float("nan")
    return sum((d["p_home"] - float(d["home_win"])) ** 2 for d in preds) / len(preds)


def reliability_block(preds):
    """Binned reliability/resolution/uncertainty (10 fixed bins) + the EXACT
    decomposition identity as an internal consistency proof of this code:
      BS = spread_p + REL - RES + UNC - 2*cov_uv
    with spread_p = mean within-bin squared p deviation, REL = Σ (n_b/N)(p̄_b−ȳ_b)²,
    RES = Σ (n_b/N)(ȳ_b−ȳ)², UNC = ȳ(1−ȳ), cov_uv = mean within-bin (p−p̄_b)(y−ȳ_b).
    (For a constant predictor spread_p = cov_uv = 0 -> classical REL−RES+UNC form.)"""
    bins = {}
    for d in preds:
        b = min(int(d["p_home"] * 10), 9)
        bins.setdefault(b, []).append(d)
    n = len(preds)
    ybar = sum(float(d["home_win"]) for d in preds) / n
    rel = res = spread_p = cov_uv = 0.0
    for b, ds in sorted(bins.items()):
        nb = len(ds)
        pb = sum(d["p_home"] for d in ds) / nb
        yb = sum(float(d["home_win"]) for d in ds) / nb
        rel += (nb / n) * (pb - yb) ** 2
        res += (nb / n) * (yb - ybar) ** 2
        spread_p += sum((d["p_home"] - pb) ** 2 for d in ds) / n
        cov_uv += sum((d["p_home"] - pb) * (float(d["home_win"]) - yb) for d in ds) / n
    unc = ybar * (1.0 - ybar)
    bs = brier_score(preds)
    rhs = spread_p + rel - res + unc - 2.0 * cov_uv
    if abs(bs - rhs) > 1e-9:
        raise Loud("Brier decomposition identity violated: %r vs %r" % (bs, rhs))
    return {"reliability": rel, "resolution": res, "uncertainty": unc,
            "within_bin_p_spread": spread_p, "cross_term": cov_uv,
            "decomposition_identity_ok": True, "n_bins_nonempty": len(bins)}


def fold_metrics(preds):
    m = {"n": len(preds), "mean_ll": arms.mean_ll(preds), "brier": brier_score(preds)}
    m.update(reliability_block(preds))
    m["calibration_slope"] = arms.calibration_slope(preds)
    return m


def csv_preds(path, preds):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["game_id", "season", "tip_utc", "p_home", "p_home_hex",
                    "home_win", "neutral", "flags"])
        for d in preds:
            w.writerow([d["game_id"], d["season"], d["tip"].isoformat(), repr(d["p_home"]),
                        float(d["p_home"]).hex(), d["home_win"], d["neutral"],
                        "|".join(d["flags"])])


# ------------------------------------------------------------------ hand fixture
def run_hand_fixture(expected_path, out_dir):
    """3-game fixture run through the SAME frozen engine; cross-checked against
    independently hand-computed constants (pure-math derivation from the frozen
    engine-law text; see fixtures/expected_hand_fixture.json)."""
    import pandas as pd
    with open(expected_path) as fh:
        exp = json.load(fh)
    tip1 = pd.Timestamp("2029-07-01T18:00:00+00:00")
    tip2 = pd.Timestamp("2029-07-02T18:00:00+00:00")

    def games(home_win_f2):
        return [
            {"tip": tip1, "game_id": "SYNTH_FX-1", "season": 2029, "fk_home": "FX_A",
             "fk_away": "FX_B", "home_win": 1, "neutral": False, "row_home": None, "row_away": None},
            {"tip": tip2, "game_id": "SYNTH_FX-2", "season": 2029, "fk_home": "FX_B",
             "fk_away": "FX_A", "home_win": home_win_f2, "neutral": False, "row_home": None, "row_away": None},
            {"tip": tip2, "game_id": "SYNTH_FX-3", "season": 2029, "fk_home": "FX_A",
             "fk_away": "FX_C", "home_win": 1, "neutral": False, "row_home": None, "row_away": None},
        ]

    TOL = 1e-12
    res = {"tol": TOL, "checks": {}}

    def close(name, got, want):
        if abs(got - want) > TOL:
            raise Loud("hand fixture %s: got %r want %r" % (name, got, want))
        res["checks"][name] = {"got": got, "want": want, "ok": True}

    preds, _ = arms.run_stream(games(0), k=B1_CFG["k"], hca=B1_CFG["hca"], gamma=B1_CFG["gamma"])
    by_id = {d["game_id"]: d for d in preds}
    close("fx1_p_home", by_id["SYNTH_FX-1"]["p_home"], exp["games"][0]["p_home"])
    close("fx2_p_home", by_id["SYNTH_FX-2"]["p_home"], exp["games"][1]["p_home"])
    close("fx3_p_home", by_id["SYNTH_FX-3"]["p_home"], exp["games"][2]["p_home"])
    close("b1_mean_ll", arms.mean_ll(preds), exp["b1_mean_ll"])
    close("b1_mean_brier", brier_score(preds), exp["b1_mean_brier"])

    b0_preds, _ = arms.run_stream(games(0), p0=B0_P0)
    close("b0_mean_ll", arms.mean_ll(b0_preds), exp["b0_mean_ll"])
    close("b0_mean_brier", brier_score(b0_preds), exp["b0_mean_brier"])
    dll = arms.ll_delta(preds, b0_preds)
    for i in range(3):
        close("paired_dll_game%d" % (i + 1), dll[i], exp["paired_dll_per_game"][i])
    close("paired_dll_point", sum(dll) / 3.0, exp["paired_dll_point"])

    # tip-batch no-leak ON THE FIXTURE: flipping f2's outcome must not move any
    # p_home in the same tip batch (f2 and f3 share tip2; f1 untouched).
    preds_flip, _ = arms.run_stream(games(1), k=B1_CFG["k"], hca=B1_CFG["hca"], gamma=B1_CFG["gamma"])
    by_id_flip = {d["game_id"]: d for d in preds_flip}
    if [float(d["p_home"]).hex() for d in preds] != [float(d["p_home"]).hex() for d in preds_flip]:
        raise Loud("tip-batch leak: flipping an outcome moved a p_home in the stream")
    res["tip_batch_no_leak_byte_identical"] = True

    csv_preds(os.path.join(out_dir, "hand_fixture_predictions.csv"), preds)
    return res


# ------------------------------------------------------------------ main rehearsal
def rehearsal(out_dir):
    os.makedirs(out_dir, exist_ok=True)

    # frozen-tree identity gate: refuse to run on drifted T_SELECT bytes
    frozen_sha_seen = {}
    for fname, want in FROZEN_SHA.items():
        got = sha256_file(os.path.join(T_SELECT_DIR, fname))
        frozen_sha_seen[fname] = got
        if got != want:
            raise Loud("FROZEN TREE DRIFT: %s sha %s != pinned %s" % (fname, got, want))

    corpus_dir, strength = generate_corpus(out_dir)
    warmup, scored, full = load_corpus(corpus_dir)
    if not scored:
        raise Loud("vacuous synthetic scored set")

    # ---- both arms on the identical full stream (warm-up feeds ratings only)
    b0_all, _ = arms.run_stream(full, p0=B0_P0)
    b1_all, meta1 = arms.run_stream(full, k=B1_CFG["k"], hca=B1_CFG["hca"], gamma=B1_CFG["gamma"])

    # ---- designed-null wrappers around the frozen B1 on the synthetic corpus
    #      (proves the neutral feature columns flow through the full path while
    #      the p_home stream stays bit-for-bit the parent)
    rows_all = [g[side] for g in scored for side in ("row_home", "row_away")]
    vals = [r["xb"] for r in rows_all if r["xb"] is not None and r["xb_reason"] == ""]
    mu = sum(vals) / len(vals)
    sd = (sum((v - mu) ** 2 for v in vals) / len(vals)) ** 0.5
    mom_b = {"col": harness.XB_COL, "reason_col": harness.XB_REASON, "mean": mu, "sd": sd}
    x_fn_b = harness.make_x_fn(mom_b)
    null_x, _ = arms.run_stream(full, k=B1_CFG["k"], hca=B1_CFG["hca"], gamma=B1_CFG["gamma"],
                                phi=0.0, x_fn=x_fn_b)
    null_c, _ = arms.run_stream(full, k=B1_CFG["k"], hca=B1_CFG["hca"], gamma=B1_CFG["gamma"],
                                c_fn=lambda r, s: 1.0)
    hx = [float(d["p_home"]).hex() for d in b1_all]
    null_ok = (hx == [float(d["p_home"]).hex() for d in null_x]
               and hx == [float(d["p_home"]).hex() for d in null_c])
    if not null_ok:
        raise Loud("designed-null mismatch on synthetic corpus")

    # ---- identical-game-set law + exact-arm identity + non-vacuousness
    def scored_folds(preds):
        return harness.fold_predictions(preds, SCORED_SEASONS)

    b0_s, b1_s = scored_folds(b0_all), scored_folds(b1_all)
    ids0 = [d["game_id"] for d in b0_s]
    ids1 = [d["game_id"] for d in b1_s]
    if len(b0_s) < 1 or len(b1_s) < 1:
        raise Loud("vacuous scored prediction set")
    if ids0 != ids1:
        raise Loud("identical-game-set law violated: arm id sequences differ")
    if len(set(ids0)) != len(ids0) or len(set(ids1)) != len(ids1):
        raise Loud("record ids not pairwise distinct within an arm")
    for a, b in zip(b0_s, b1_s):
        if (a["tip"], a["season"], a["home_win"], a["neutral"]) != (b["tip"], b["season"], b["home_win"], b["neutral"]):
            raise Loud("arm rows are not the same games row-wise")

    # ---- per-fold + pooled metrics, both arms
    per_fold = {}
    for season in SCORED_SEASONS:
        p0f = [d for d in b0_s if d["season"] == season]
        p1f = [d for d in b1_s if d["season"] == season]
        per_fold[str(season)] = {"B0": fold_metrics(p0f), "B1-WNBA": fold_metrics(p1f)}
    pooled = {"B0": fold_metrics(b0_s), "B1-WNBA": fold_metrics(b1_s)}

    # ---- paired dLL + tip-date-cluster bootstrap (10,000 resamples, seed 20261005)
    dll = arms.ll_delta(b1_s, b0_s)
    clusters = harness.tip_date_clusters(b1_s)
    pt, lo, hi = arms.date_cluster_bootstrap_ci(dll, clusters, n_resamples=10000, seed=SEED)
    pt2, lo2, hi2 = arms.date_cluster_bootstrap_ci(dll, clusters, n_resamples=10000, seed=SEED)
    boot_deterministic = (pt, lo, hi) == (pt2, lo2, hi2)
    if not boot_deterministic:
        raise Loud("bootstrap not deterministic under fixed seed")
    slope_b1 = arms.calibration_slope(b1_s)
    if math.isnan(slope_b1):
        raise Loud("synthetic B1 calibration slope unidentifiable (machinery broken)")
    slope_b1_in_band = arms.SLOPE_BAND[0] <= slope_b1 <= arms.SLOPE_BAND[1]

    # ---- hand-computed fixture through the same frozen engine
    fixture = run_hand_fixture(os.path.join(LANE_DIR, "fixtures/expected_hand_fixture.json"), out_dir)

    # ---- flags actually exercised on the synthetic scored folds
    flag_counts = {}
    for d in harness.fold_predictions(null_x, SCORED_SEASONS):
        for f in d["flags"]:
            flag_counts[f] = flag_counts.get(f, 0) + 1

    # ---- outputs (deterministic serialization)
    csv_preds(os.path.join(out_dir, "predictions_b0_scored.csv"), b0_s)
    csv_preds(os.path.join(out_dir, "predictions_b1_scored.csv"), b1_s)
    report = {
        "cycle_id": "WNBA-PLAYERFEAT-SCORED-V1", "lane": "S_SYNTH", "mode": "evaluate-oos-synthetic-rehearsal",
        "seed": SEED,
        "frozen_inputs": {"B0_p_home": B0_P0, "B1_config": B1_CFG,
                          "frozen_tree_sha256": frozen_sha_seen},
        "synthetic_corpus": {
            "warmup_seasons": list(WARMUP_SEASONS), "scored_seasons": list(SCORED_SEASONS),
            "n_warmup_games": len(warmup), "n_scored_games": len(scored),
            "n_full_stream": len(full), "id_prefix": "SYNTH_",
            "min_season": min(g["season"] for g in full),
            "neutral_rows_scored": sum(1 for g in scored if g["neutral"]),
            "team_strengths": {k: round(v, 6) for k, v in sorted(strength.items())},
            "standardization_moments_synthetic_b5_minutes_hhi":
                {"mean": mu, "sd": sd, "n": len(vals),
                 "note": "driver-side, same formula as harness.compute_moments "
                         "(population sd ddof=0); the frozen fn itself is bound to the real-cap law"},
        },
        "laws": {
            "identical_game_set": True,
            "exact_arm_ids_pairwise_distinct": True,
            "designed_null_byte_identity_on_synthetic": null_ok,
            "nonvacuous": len(b1_s) >= 1,
            "scored_folds_law": {
                "fold_seasons": sorted(set(d["season"] for d in b1_s)),
                "n_fold_rows": len(b1_s),
                "n_scored_corpus_rows": len(scored),
                "fold_rows_equal_corpus_rows": len(b1_s) == len(scored),
                "warmup_min_season_excluded_from_folds":
                    min(d["season"] for d in b1_s) >= 2027,
            },
        },
        "per_fold_metrics": per_fold,
        "pooled_metrics": pooled,
        "paired_dll_B1_minus_B0": {
            "point": pt, "ci_low": lo, "ci_high": hi,
            "n_resamples": 10000, "clusters": "tip UTC date",
            "n_clusters": len(set(clusters)), "seed": SEED,
            "deterministic_rerun_identical": boot_deterministic,
            "note": "synthetic smoke-run of the frozen bootstrap machinery; not a real-data claim",
        },
        "slope_B1_synthetic": {"value": slope_b1, "band": list(arms.SLOPE_BAND),
                               "in_band": slope_b1_in_band,
                               "note": "band is the real-data admission law; recorded, not gating on synthetic draws"},
        "flags_scored_folds": flag_counts,
        "hand_fixture": fixture,
        "final_ratings_n_franchises": len(meta1["final_ratings"]),
    }
    with open(os.path.join(out_dir, "rehearsal.json"), "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("REHEARSAL ok: scored=%d (seasons %s) warmup=%d | B0 LL %.6f | B1 LL %.6f | "
          "dLL %.6f [%.6f, %.6f] | slope %.4f | null_ok=%s fixture_ok=%s"
          % (len(b1_s), list(SCORED_SEASONS), len(warmup), pooled["B0"]["mean_ll"],
             pooled["B1-WNBA"]["mean_ll"], pt, lo, hi, slope_b1, null_ok, True))
    return report


def main():
    ap = argparse.ArgumentParser(description="S_SYNTH synthetic OOS-like rehearsal")
    ap.add_argument("--out", required=True, help="output run dir (sandbox)")
    args = ap.parse_args()
    rehearsal(os.path.abspath(os.path.expanduser(args.out)))


if __name__ == "__main__":
    main()
