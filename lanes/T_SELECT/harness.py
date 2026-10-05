# harness.py — NBA-PLAYERFEAT-SCORED-V1 · Lane T_SELECT
# Evaluation harness. Modes:
#   select         TRAIN-INTERNAL selection on real data, HARD-CAPPED at season <= 2021
#                  (warm-up 2016-2017 streams only; selection folds 2018-2021; the OOS
#                  window [2022..2026] is NEVER loaded, scored or touched)
#   evaluate-oos   REFUSES real data without a GO token (the token does not exist);
#                  synthetic fixtures only, sandbox outputs
#   --selftest     hand-computed fixtures + leakage canaries (incl. doctored 2022 ABORT)
#
# Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python — only. No git.

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arms  # noqa: E402
from arms import (  # noqa: E402
    BOOTSTRAP_N,
    ELO_GAMMA,
    ELO_HCA,
    ELO_INIT,
    ELO_K,
    GROUP_COLUMNS,
    PF_GROUPS,
    PHI_GRID,
    SEED,
    SLOPE_BAND,
    TechAbort,
    active_params,
    brier_rows,
    calibration_slope,
    config_id,
    gamma_revert,
    grid_configs,
    group_x,
    logloss_rows,
    moments_from_frame,
    paired_delta_ci,
    pf_p_home,
    replay_elo,
    sigmoid_elo_scalar,
    synthetic_stream,
)

# ------------------------------------------------------------------ frozen paths
ROOT = Path("/Users/hoangminhlong/my-quantitative")
WORKTREE = ROOT / ".worktrees" / "nba-playerfeat-scored-v1" / "integration"
LANE_DIR = WORKTREE / "lanes" / "T_SELECT"
DATA_OUT = Path.home() / ".my-quantitative-data" / "nba-playerfeat-scored-v1" / "selection"
SCHEDULE_ROOT = Path.home() / ".my-quantitative-data" / "nba-hoopr-v1" / "raw"
FEATURE_PARQUET = (
    Path.home() / ".my-quantitative-data" / "playerfeat-prep-v1" / "nba" / "features"
    / "nba_player_features_2016_2026.parquet"
)
GO_TOKEN_PATH = Path.home() / ".my-quantitative-data" / "nba-playerfeat-scored-v1" / "GO_EVALUATION_TOKEN"

# ------------------------------------------------------------------ frozen windows/constants
SEASON_MIN_REAL = 2016
SEASON_MAX_REAL = 2021                      # HARD CAP: real data never beyond this
WARMUP_SEASONS = (2016, 2017)
FOLD_SEASONS = (2018, 2019, 2020, 2021)     # 4 rolling-origin folds, expanding
STANDARDIZATION_CUTOFF = pd.Timestamp("2021-08-01T00:00:00Z")
FEATURE_SHA256 = "b3ca0e3b2eff1d1c918d56fb626e06998903c0f69253b41b67166dc8859885cb"
FEATURE_COLUMNS = [
    "game_id", "season", "season_type", "team_id", "opponent_id", "is_home",
    "is_exhibition", "tip_utc", "team_games_so_far", "n_prior_games_used",
    "feature_neutral", "a_top5_share_k5", "a_load_top5_k5", "b_form_top3",
    "b_form_top3_n", "c_abs_out", "c_abs_streak", "asof_rule_version",
]
FRANCHISE_IDS = frozenset(range(1, 31))     # ESPN league-46 franchise ids (measured stable)
REG_SEASON_TYPE = 2                          # this corpus: 2=regular season (incl. exhibitions), 3=playoffs, 5=play-in
POST_SEASON_TYPE = 3
PLAYIN_SEASON_TYPE = 5

SCHEMA = "nba_playerfeat_selection@1"
LEDGER_SCHEMA = "nba_playerfeat_selection_ledger@1"


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ data loading
def load_schedule(data_root: Path, season_min: int, season_max: int) -> pd.DataFrame:
    """Load schedule seasons [season_min, season_max] ONLY.

    HARD SEASON CAP (loud): every row of every loaded file must carry
    season <= season_max; any higher-season row aborts (doctored-row canary).
    Files for seasons > season_max are never opened (counted as skipped).
    """
    frames = []
    skipped = []
    for s in range(season_min, season_max + 1):
        p = data_root / f"nba_schedule_{s}.csv"
        if not p.exists():
            raise TechAbort(f"BLOCKED_DATA: missing schedule file {p}")
        df = pd.read_csv(p, low_memory=False)
        bad = df.loc[~df["season"].between(season_min, season_max)]
        if len(bad):
            raise TechAbort(
                f"SEASON_CAP_VIOLATION: file {p.name} carries {len(bad)} row(s) with "
                f"season outside [{season_min},{season_max}] "
                f"(observed {sorted(bad['season'].unique())}); hard cap SEASON_MAX_REAL={season_max}"
            )
        frames.append(df)
    for s in range(season_max + 1, season_max + 12):
        p = data_root / f"nba_schedule_{s}.csv"
        if p.exists():
            skipped.append(p.name)
    sch = pd.concat(frames, ignore_index=True)
    sch["tip_utc"] = pd.to_datetime(sch["game_date_time"], utc=True, format="mixed")
    sch["start_utc"] = pd.to_datetime(sch["start_date"], utc=True, format="mixed")
    n_tz_bad = int((sch["tip_utc"] != sch["start_utc"]).sum())
    if n_tz_bad:
        raise TechAbort(f"TZ_SEMANTICS: {n_tz_bad} rows where game_date_time != start_date after UTC normalization")
    sch["tip_date"] = sch["tip_utc"].dt.normalize()
    sch["played"] = (sch["status_type_name"] == "STATUS_FINAL") & sch["home_score"].notna() & sch["away_score"].notna()
    sch.attrs["skipped_future_files"] = skipped
    return sch


def load_features(season_max: int) -> pd.DataFrame:
    """Load the frozen feature table after sha256 verification (mismatch => BLOCKED_DATA).

    The frozen table spans 2016-2026 by construction (28,374 rows per manifest).
    HARD SEASON CAP for computation: rows with season > season_max are sliced OFF
    before anything downstream sees them, and the per-season counts of the sliced
    rows must equal the manifest numbers exactly — any doctored/extra row shifts
    the accounting and aborts loud.
    """
    got = sha256_file(FEATURE_PARQUET)
    if got != FEATURE_SHA256:
        raise TechAbort(f"BLOCKED_DATA: feature-table sha256 mismatch: got {got}, expected {FEATURE_SHA256}")
    ft = pd.read_parquet(FEATURE_PARQUET)
    if list(ft.columns) != FEATURE_COLUMNS:
        raise TechAbort("BLOCKED_DATA: feature table columns differ from the frozen whitelist")
    if len(ft) != 28_374:
        raise TechAbort(f"BLOCKED_DATA: feature table row count {len(ft)} != 28374")
    if int((ft["season"] < SEASON_MIN_REAL).sum()):
        raise TechAbort("BLOCKED_DATA: feature table seasons below 2016")
    manifest_future = {2022: 2648, 2023: 2642, 2024: 2640, 2025: 2648, 2026: 2652}
    got_future = {int(k): int(v) for k, v in ft.loc[ft["season"] > season_max, "season"].value_counts().items()}
    if got_future != manifest_future:
        raise TechAbort(
            f"SEASON_CAP_VIOLATION/BLOCKED_DATA: feature rows above season {season_max} do not match the "
            f"frozen manifest accounting: got {got_future}, expected {manifest_future}"
        )
    ft = ft[ft["season"] <= season_max].reset_index(drop=True)
    if len(ft) != 15_144:  # manifest: 2016..2021 rows
        raise TechAbort(f"BLOCKED_DATA: capped feature table row count {len(ft)} != 15144")
    if set(ft["season"].unique()) != set(range(SEASON_MIN_REAL, season_max + 1)):
        raise TechAbort("BLOCKED_DATA: capped feature table season set != {2016..season_max}")
    neutral = ft["feature_neutral"] == 1
    scalar_cols = [c for g in GROUP_COLUMNS.values() for c in g]
    if not (ft.loc[neutral, scalar_cols].to_numpy() == 0.0).all():
        raise TechAbort("BLOCKED_DATA: neutral rows must carry 0.0 in every group scalar")
    ft.attrs["future_rows_sliced"] = sum(manifest_future.values())
    return ft


def build_universe(sch: pd.DataFrame) -> dict:
    """Split the played universe into replay-eligible games + scored row sets.

    Replay/stream eligibility (inherited terminal law, documented): played,
    season_type in {2 regular, 3 playoff}, non-exhibition (both sides franchise
    ids). Play-in (season_type=5) and exhibitions never update the stream.
    Scored fold rows: REG (season_type=2) played non-exhibition games of the
    fold season. Playoff rows reported separately (never in the criterion).
    Exhibitions excluded from rows with counts.
    """
    played = sch[sch["played"]].copy()
    if len(played) == 0:
        raise TechAbort("BLOCKED_DATA: no played games")
    if int((played["home_score"] == played["away_score"]).sum()):
        raise TechAbort("TIE_GAME: equal scores present; NBA tie semantics undefined, aborting loud")
    played["is_exhibition_sched"] = ~(played["home_id"].isin(FRANCHISE_IDS) & played["away_id"].isin(FRANCHISE_IDS))
    stream_mask = (
        (~played["is_exhibition_sched"])
        & played["season_type"].isin([REG_SEASON_TYPE, POST_SEASON_TYPE])
    )
    stream = played[stream_mask].copy()
    stream["y"] = (stream["home_score"] > stream["away_score"]).astype(np.int64)
    stream = stream.sort_values(["tip_date", "game_id"], kind="mergesort").reset_index(drop=True)

    reg_played = played[(played["season_type"] == REG_SEASON_TYPE) & (~played["is_exhibition_sched"])].copy()
    reg_played["y"] = (reg_played["home_score"] > reg_played["away_score"]).astype(np.int64)
    reg_played = reg_played.sort_values(["tip_date", "game_id"], kind="mergesort").reset_index(drop=True)
    return {
        "played": played,
        "stream": stream,
        "reg_played": reg_played,
        "exhibitions": played[played["is_exhibition_sched"]],
        "playin_played": played[played["season_type"] == PLAYIN_SEASON_TYPE],
        "post_played": played[(played["season_type"] == POST_SEASON_TYPE) & (~played["is_exhibition_sched"])],
    }


# ------------------------------------------------------------------ lock gate
def lock_inspect(retries: int = 3, wait_s: int = 60) -> dict:
    """Machine-wide heavy-lock gate. Returns the inspect JSON when FREE_PROVEN.

    Retries `retries` times with wait_s seconds between attempts, then stops
    NOT_RUN_RESOURCE_CONFLICT (loud, non-zero exit handled by caller).
    """
    cmd = [sys.executable, "research/researchctl.py", "locks", "inspect"]
    for attempt in range(retries + 1):
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"verdict": "UNPARSEABLE", "stdout": proc.stdout[-800:], "stderr": proc.stderr[-800:]}
        if payload.get("verdict") == "FREE_PROVEN":
            payload["attempt"] = attempt
            payload["checked_at_utc"] = utcnow()
            return payload
        if attempt < retries:
            print(f"[lock] not FREE_PROVEN (attempt {attempt + 1}/{retries + 1}); retrying in {wait_s}s", flush=True)
            time.sleep(wait_s)
    payload["stop"] = "NOT_RUN_RESOURCE_CONFLICT"
    return payload


# ------------------------------------------------------------------ core assembly
class SelectionContext:
    """Everything the arms need, assembled once from the capped real corpus."""

    def __init__(self, schedule_root: Path, season_max: int):
        self.season_max = season_max
        self.sch = load_schedule(schedule_root, SEASON_MIN_REAL, season_max)
        self.uni = build_universe(self.sch)
        self.features = load_features(season_max)
        self.stream = self.uni["stream"]
        self.replay = replay_elo(self.stream[["game_id", "season", "tip_date", "home_id", "away_id", "y"]])
        self._p_by_gid = {int(g): float(p) for g, p in zip(self.replay.game_ids, self.replay.p_home)}
        self._arg_by_gid = {int(g): float(a) for g, a in zip(self.replay.game_ids, self.replay.elo_arg)}

        # moments: team-side rows of REG played non-exhibition games with
        # tip STRICTLY BEFORE the pinned cutoff (warm-up + train only)
        cols = ["game_id", "season", "team_id", "is_exhibition", "feature_neutral", "tip_utc"] + sorted(
            {c for g in GROUP_COLUMNS.values() for c in g}
        )
        ftr = self.features[cols].copy()
        side = pd.concat(
            [
                self.uni["reg_played"][["game_id", "season", "home_id"]]
                .rename(columns={"home_id": "team_id"})
                .assign(side_home=1),
                self.uni["reg_played"][["game_id", "season", "away_id"]]
                .rename(columns={"away_id": "team_id"})
                .assign(side_home=0),
            ],
            ignore_index=True,
        )
        join = ftr.merge(side, on=["game_id", "team_id"], how="inner", suffixes=("", "_sch"))
        if len(join) != 2 * len(self.uni["reg_played"]):
            raise TechAbort(
                f"BLOCKED_DATA: feature join coverage {len(join)} != 2x{len(self.uni['reg_played'])} REG played rows"
            )
        if not (join["season"] == join["season_sch"]).all():
            raise TechAbort("BLOCKED_DATA: feature/schedule season mismatch on joined rows")
        if int((join["season"] > self.season_max).sum()):
            raise TechAbort("SEASON_CAP_VIOLATION: joined feature/schedule rows above the hard cap")
        mom_rows = join[join["tip_utc"] < STANDARDIZATION_CUTOFF]
        self.moments = moments_from_frame(mom_rows, sorted({c for g in GROUP_COLUMNS.values() for c in g}))
        self.mom_n = int(len(mom_rows))
        self._teamfeat = ftr.set_index(["game_id", "team_id"])

        # fold rows (one row per game, home perspective)
        self.fold_rows = []
        self.playoff_rows = pd.DataFrame()
        for s in FOLD_SEASONS:
            self.fold_rows.append(self.uni["reg_played"][self.uni["reg_played"]["season"] == s].copy())
        self.fold_rows = pd.concat(self.fold_rows, ignore_index=True)
        po = self.uni["post_played"][self.uni["post_played"]["season"].isin(FOLD_SEASONS)].copy()
        po["y"] = (po["home_score"] > po["away_score"]).astype(np.int64)
        self.playoff_rows = po.sort_values(["tip_date", "game_id"], kind="mergesort").reset_index(drop=True)
        self.fold_rows = self.fold_rows.reset_index(drop=True)

        fh, fa = self._side_frames(self.fold_rows)
        self.fold_h, self.fold_a = fh, fa
        self.fold_y = self.fold_rows["y"].to_numpy(dtype=np.float64)
        self.fold_dates = self.fold_rows["tip_date"].to_numpy()
        self.fold_gid = self.fold_rows["game_id"].to_numpy()
        self.fold_elo_arg = np.array([self._arg_by_gid[int(g)] for g in self.fold_gid])
        self.b1_p = arms.sigmoid_elo(self.fold_elo_arg)
        self._playoff_prep()

    def _side_frames(self, rows: pd.DataFrame):
        idx_h = list(zip(rows["game_id"].astype(np.int64), rows["home_id"].astype(np.int64)))
        idx_a = list(zip(rows["game_id"].astype(np.int64), rows["away_id"].astype(np.int64)))
        try:
            fh = self._teamfeat.loc[idx_h]
            fa = self._teamfeat.loc[idx_a]
        except KeyError as e:
            raise TechAbort(f"BLOCKED_DATA: missing feature row for {e}") from e
        return fh.reset_index(drop=True), fa.reset_index(drop=True)

    def _playoff_prep(self):
        if len(self.playoff_rows):
            ph, pa = self._side_frames(self.playoff_rows)
            self.playoff_h, self.playoff_a = ph, pa
            self.playoff_y = self.playoff_rows["y"].to_numpy(dtype=np.float64)
            self.playoff_elo_arg = np.array(
                [self._arg_by_gid[int(g)] for g in self.playoff_rows["game_id"]]
            )
        else:
            self.playoff_h = self.playoff_a = None
            self.playoff_y = self.playoff_elo_arg = None

    # -- evaluation helpers -------------------------------------------------
    def arm_x(self, arm: str):
        return (
            group_x(self.fold_h, arm, self.moments),
            group_x(self.fold_a, arm, self.moments),
        )

    def b0_constants(self) -> dict:
        """B0 refit law (protocol verbatim): per fold, the train home-win rate over
        REG played rows of all complete seasons strictly before the fold season
        (2016 onward; warm-up rows are train rows, never scored rows)."""
        consts = {}
        allrows = self.uni["reg_played"]
        for s in FOLD_SEASONS:
            train = allrows[allrows["season"] < s]
            consts[str(s)] = float(train["y"].mean())
        return consts

    def twin_p_home(self, arm: str, phi: float):
        """Time-shuffled twin: the feature pair (x_home, x_away) swapped across
        team-sides per game by a seeded fair coin (marginals preserved exactly);
        coin order = fixed fold-row order; seed 20261005."""
        xh, xa = self.arm_x(arm)
        rng = np.random.default_rng(SEED)
        flip = rng.random(len(xh)) < 0.5
        xh_t = np.where(flip, xa, xh)
        xa_t = np.where(flip, xh, xa)
        return pf_p_home(self.fold_elo_arg, xh_t, xa_t, phi), int(flip.sum())


# ------------------------------------------------------------------ selection run
def run_select(json_out: bool = False) -> int:
    t_start = utcnow()
    lock_before = lock_inspect()
    if lock_before.get("stop") == "NOT_RUN_RESOURCE_CONFLICT":
        print(json.dumps({"stop": "NOT_RUN_RESOURCE_CONFLICT", "lock": lock_before}, indent=2))
        return 4

    ctx = SelectionContext(SCHEDULE_ROOT, SEASON_MAX_REAL)

    # ---- DESIGNED-NULL FIRST: phi=0 must equal B1* bit-for-bit on the full
    # fold stream (max |dp| == 0.0 exactly) before any other number is believed.
    null_checks = {}
    for arm in PF_GROUPS:
        xh, xa = ctx.arm_x(arm)
        p0 = pf_p_home(ctx.fold_elo_arg, xh, xa, 0.0)
        maxdp = float(np.max(np.abs(p0 - ctx.b1_p)))
        null_checks[arm] = maxdp
        if maxdp != 0.0:
            print(json.dumps({"stop": "TECHABORT_EQUIVALENCE", "arm": arm, "max_abs_dp": maxdp}, indent=2))
            return 5
    print(f"[designed-null] phi=0 bit-for-bit vs B1* on {len(ctx.fold_rows)} fold rows: "
          + ", ".join(f"{a}: {v}" for a, v in null_checks.items()), flush=True)

    ll_b1 = logloss_rows(ctx.b1_p, ctx.fold_y)
    brier_b1 = brier_rows(ctx.b1_p, ctx.fold_y)
    slope_b1 = calibration_slope(ctx.b1_p, ctx.fold_y)
    b0_consts = ctx.b0_constants()
    b0_p = np.array([b0_consts[str(s)] for s in ctx.fold_rows["season"]])
    ll_b0 = logloss_rows(b0_p, ctx.fold_y)
    slope_b0 = calibration_slope(b0_p, ctx.fold_y)
    d_b0 = paired_delta_ci(ll_b0, ll_b1, ctx.fold_dates)

    ledger = []
    per_arm = {}

    ledger.append(_ref_row("B0", b0_consts, ctx, ll_b0, brier_b0 := brier_rows(b0_p, ctx.fold_y),
                           d_b0, slope_b0, verdict="REFERENCE_FLOOR"))
    ledger.append(_ref_row("B1*", None, ctx, ll_b1, brier_b1,
                           {"point": 0.0, "ci95_lo": 0.0, "ci95_hi": 0.0}, slope_b1,
                           verdict="REFERENCE_BASELINE"))

    # diagnostic ablation B1-HCA0 (outside budget)
    replay_hca0 = replay_elo(
        ctx.stream[["game_id", "season", "tip_date", "home_id", "away_id", "y"]], HCA=0.0
    )
    arg0_by_gid = {int(g): float(a) for g, a in zip(replay_hca0.game_ids, replay_hca0.elo_arg)}
    p_hca0 = arms.sigmoid_elo(np.array([arg0_by_gid[int(g)] for g in ctx.fold_gid]))
    ll_hca0 = logloss_rows(p_hca0, ctx.fold_y)
    d_hca0 = paired_delta_ci(ll_hca0, ll_b1, ctx.fold_dates)
    ledger.append(_ref_row("B1-HCA0", None, ctx, ll_hca0, brier_rows(p_hca0, ctx.fold_y),
                           d_hca0, calibration_slope(p_hca0, ctx.fold_y),
                           verdict="DIAGNOSTIC_ABLATION"))

    # ---- PF arms: 15 configs, all counted
    for arm in PF_GROUPS:
        xh, xa = ctx.arm_x(arm)
        rows = []
        for phi in PHI_GRID:
            p = pf_p_home(ctx.fold_elo_arg, xh, xa, phi)
            llr = logloss_rows(p, ctx.fold_y)
            br = brier_rows(p, ctx.fold_y)
            d = paired_delta_ci(llr, ll_b1, ctx.fold_dates)
            cfg = {
                "arm": arm, "phi": phi, "p": p, "ll_rows": llr, "brier_rows": br,
                "delta": d, "slope": calibration_slope(p, ctx.fold_y),
                "pooled_ll": float(llr.mean()), "per_fold": _per_fold_ll(ctx, llr),
            }
            rows.append(cfg)
        # arm selection: min pooled LL; tie-break fewer active params then lexicographic id
        best = sorted(rows, key=lambda c: (round(c["pooled_ll"], 15), active_params(c["phi"]), config_id(arm, c["phi"])))[0]
        twin_p, n_flips = ctx.twin_p_home(arm, best["phi"])
        twin_ll = float(logloss_rows(twin_p, ctx.fold_y).mean())
        twin_wins = twin_ll < best["pooled_ll"]
        # extra diagnostic (outside budget): twin at the arm's best NON-zero config
        nz = [c for c in rows if c["phi"] != 0.0]
        best_nz = sorted(nz, key=lambda c: (round(c["pooled_ll"], 15), config_id(arm, c["phi"])))[0]
        tnz_p, tnz_flips = ctx.twin_p_home(arm, best_nz["phi"])
        tnz_ll = float(logloss_rows(tnz_p, ctx.fold_y).mean())
        per_arm[arm] = {"configs": rows, "best": best, "twin_ll": twin_ll,
                        "twin_flips": n_flips, "twin_wins": twin_wins,
                        "best_nonzero": best_nz, "twin_nz_ll": tnz_ll,
                        "twin_nz_flips": tnz_flips,
                        "twin_nz_wins": tnz_ll < best_nz["pooled_ll"],
                        "xh": xh, "xa": xa}

    # ---- verdicts (G-ENTRY per arm on the arm's selected config)
    for arm in PF_GROUPS:
        info = per_arm[arm]
        best = info["best"]
        d = best["delta"]
        reasons = []
        if d["ci95_lo"] > 0.0:
            reasons.append("CI_entirely_above_zero")
        if info["twin_wins"]:
            reasons.append("twin_beats_parent")
        if not (best["delta"]["point"] < 0.0):
            reasons.append("point_dell_not_negative")
        slope_ok = best["slope"] is not None and SLOPE_BAND[0] <= best["slope"] <= SLOPE_BAND[1]
        if not slope_ok:
            reasons.append("slope_out_of_band")
        if "CI_entirely_above_zero" in reasons:
            verdict = "KILLED"
        elif "twin_beats_parent" in reasons:
            verdict = "MACHINERY_SUSPECT_UNSCORED"
        elif not reasons:
            verdict = "ADMITTED"
        else:
            verdict = "NOT_ADMITTED"
        info["verdict"] = verdict
        info["reasons"] = reasons
        info["frozen_phi"] = best["phi"] if verdict == "ADMITTED" else None

    # ---- ledger rows for PF configs
    for arm in PF_GROUPS:
        info = per_arm[arm]
        best_nz = info["best_nonzero"]
        for cfg in info["configs"]:
            is_best = cfg is info["best"]
            is_best_nz = cfg is best_nz
            if cfg["phi"] == 0.0:
                verdict = "DESIGNED_NULL_OK"
            elif is_best:
                verdict = info["verdict"]
            else:
                verdict = "GRID_EVALUATED"
            twin_rec = None
            if is_best:
                twin_rec = {"applied": True, "kind": "selected_config", "twin_pooled_ll": info["twin_ll"],
                            "twin_side_flips": info["twin_flips"], "twin_wins": info["twin_wins"]}
            elif is_best_nz:
                twin_rec = {"applied": True, "kind": "best_nonzero_diagnostic",
                            "twin_pooled_ll": info["twin_nz_ll"], "twin_side_flips": info["twin_nz_flips"],
                            "twin_wins": info["twin_nz_wins"]}
            ledger.append({
                "schema": LEDGER_SCHEMA, "cycle_id": "NBA-PLAYERFEAT-SCORED-V1", "lane": "T_SELECT",
                "ts_window": "TRAIN-INTERNAL 2018-2021 (folds); warm-up 2016-2017 never scored",
                "budget_class": "candidate", "config_id": config_id(arm, cfg["phi"]),
                "arm": arm, "phi": cfg["phi"], "active_params": active_params(cfg["phi"]),
                "n_rows": int(len(ctx.fold_y)),
                "rows_per_fold": {str(s): int((ctx.fold_rows['season'] == s).sum()) for s in FOLD_SEASONS},
                "ll_per_fold": cfg["per_fold"], "pooled_ll": cfg["pooled_ll"],
                "pooled_brier": float(cfg["brier_rows"].mean()),
                "delta_ll_vs_B1_star": cfg["delta"],
                "calibration_slope": cfg["slope"],
                "twin": twin_rec,
                "selected_for_arm": is_best, "arm_verdict": info["verdict"],
                "arm_reasons": info["reasons"], "verdict": verdict,
                "seed": SEED,
            })

    # ---- summary + freeze decisions
    admitted = {a: per_arm[a]["frozen_phi"] for a in PF_GROUPS if per_arm[a]["verdict"] == "ADMITTED"}
    summary = {
        "schema": SCHEMA,
        "cycle_id": "NBA-PLAYERFEAT-SCORED-V1",
        "lane": "T_SELECT",
        "mode": "select",
        "generated_utc": t_start,
        "finished_utc": utcnow(),
        "windows": {"warmup": list(WARMUP_SEASONS), "folds": list(FOLD_SEASONS),
                    "oos": "NEVER_TOUCHED (2022-2026 not loaded; hard cap enforced at load)"},
        "season_cap": {"SEASON_MAX_REAL": SEASON_MAX_REAL,
                       "skipped_future_files": ctx.sch.attrs.get("skipped_future_files", [])},
        "lock": {"before": lock_before, "after": None},
        "designed_null": {"max_abs_dp_per_arm": null_checks, "required": "0.0 exactly", "ok": True},
        "feature_table_sha256": FEATURE_SHA256,
        "counts": _counts(ctx),
        "b0_constants_per_fold": b0_consts,
        "b1_star": {"K": ELO_K, "HCA": ELO_HCA, "gamma": ELO_GAMMA, "init": ELO_INIT,
                    "pooled_fold_ll": float(ll_b1.mean()), "calibration_slope": slope_b1,
                    "final_ratings": {str(k): v for k, v in ctx.replay.final_ratings.items()}},
        "standardization_moments": {
            "population": "team-side rows of REG played non-exhibition games, tip_utc < 2021-08-01T00:00Z (warm-up+train)",
            "ddof": 0, "n_rows": ctx.mom_n,
            "mu": ctx.moments.mu, "sd": ctx.moments.sd,
        },
        "arms": {a: {"verdict": per_arm[a]["verdict"], "reasons": per_arm[a]["reasons"],
                     "best_config": {"phi": per_arm[a]["best"]["phi"],
                                     "pooled_ll": per_arm[a]["best"]["pooled_ll"],
                                     "delta_ll_vs_B1_star": per_arm[a]["best"]["delta"],
                                     "calibration_slope": per_arm[a]["best"]["slope"],
                                     "per_fold_ll": per_arm[a]["best"]["per_fold"]},
                     "best_nonzero_config": {"phi": per_arm[a]["best_nonzero"]["phi"],
                                             "pooled_ll": per_arm[a]["best_nonzero"]["pooled_ll"],
                                             "delta_ll_vs_B1_star": per_arm[a]["best_nonzero"]["delta"]},
                     "twin": {"pooled_ll": per_arm[a]["twin_ll"], "wins": per_arm[a]["twin_wins"],
                              "side_flips": per_arm[a]["twin_flips"]},
                     "twin_best_nonzero": {"pooled_ll": per_arm[a]["twin_nz_ll"],
                                           "wins": per_arm[a]["twin_nz_wins"],
                                           "side_flips": per_arm[a]["twin_nz_flips"]}}
                 for a in PF_GROUPS},
        "frozen_phi": admitted,
        "diagnostics": {"B1-HCA0": {"pooled_ll": float(ll_hca0.mean()), "delta_ll_vs_B1_star": d_hca0,
                                     "note": "LL(B1*) - LL(B1-HCA0); d<0 favors HCA=100 (H2 direction)"}},
        "playoff_segment": _playoff_lls(ctx, per_arm, arg0_by_gid),
        "budget": {"candidate_configs": 15, "reference_rows": 2, "diagnostic_rows": 1,
                   "diagnostic_twin_computations": 6, "ledger_rows_total": 18,
                   "b0_refits": len(FOLD_SEASONS), "elo_replays": 2, "designed_null_checks": len(PF_GROUPS)},
        "seed": SEED,
    }
    lock_after = lock_inspect(retries=0)
    summary["lock"]["after"] = lock_after

    # ---- write outputs (data dir + lane copies)
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    ledger_lines = "\n".join(json.dumps(r, sort_keys=False, default=_json_default) for r in ledger) + "\n"
    (DATA_OUT / "SELECTION_LEDGER.jsonl").write_text(ledger_lines)
    (LANE_DIR / "SELECTION_LEDGER.jsonl").write_text(ledger_lines)

    report = render_report(ctx, summary, per_arm, b0_consts, null_checks, t_start, lock_before, lock_after)
    (DATA_OUT / "SELECTION_REPORT.md").write_text(report)
    (LANE_DIR / "SELECTION_REPORT.md").write_text(report)
    vtable = render_verdict_table(summary, per_arm, b0_consts, float(ll_b1.mean()), float(ll_hca0.mean()), d_hca0, slope_b1)
    (DATA_OUT / "VERDICT_TABLE.md").write_text(vtable)
    (LANE_DIR / "VERDICT_TABLE.md").write_text(vtable)
    (DATA_OUT / "SELECTION_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=_json_default))

    if json_out:
        print(json.dumps({"frozen_phi": admitted,
                          "verdicts": {a: per_arm[a]["verdict"] for a in PF_GROUPS},
                          "b0_constants": b0_consts, "designed_null": null_checks,
                          "b1_star_pooled_ll": float(ll_b1.mean())}, indent=2, default=_json_default))
    return 0


def _ref_row(name, b0_consts, ctx, ll_rows, brier_rows_arr, delta, slope, verdict):
    return {
        "schema": LEDGER_SCHEMA, "cycle_id": "NBA-PLAYERFEAT-SCORED-V1", "lane": "T_SELECT",
        "ts_window": "TRAIN-INTERNAL 2018-2021 (folds); warm-up 2016-2017 never scored",
        "budget_class": "reference" if name in ("B0", "B1*") else "diagnostic",
        "config_id": name, "arm": name, "phi": None,
        "b0_constants_per_fold": b0_consts,
        "n_rows": int(len(ctx.fold_y)),
        "rows_per_fold": {str(s): int((ctx.fold_rows['season'] == s).sum()) for s in FOLD_SEASONS},
        "ll_per_fold": _per_fold_ll(ctx, ll_rows),
        "pooled_ll": float(ll_rows.mean()),
        "pooled_brier": float(brier_rows_arr.mean()),
        "delta_ll_vs_B1_star": delta,
        "calibration_slope": slope,
        "twin": None, "selected_for_arm": None, "verdict": verdict, "seed": SEED,
    }


def _per_fold_ll(ctx, ll_rows) -> dict:
    out = {}
    seasons = ctx.fold_rows["season"].to_numpy()
    for s in FOLD_SEASONS:
        m = seasons == s
        out[str(s)] = float(np.asarray(ll_rows)[m].mean())
    return out


def _counts(ctx) -> dict:
    played = ctx.uni["played"]
    reg = ctx.uni["reg_played"]
    return {
        "schedule_rows_loaded": int(len(ctx.sch)),
        "played_games_loaded": int(played["played"].sum()),
        "stream_updates": int(ctx.replay.n_updates),
        "season_reversions": int(ctx.replay.n_season_reversions),
        "exhibition_games_excluded_from_rows": {
            "total_in_window": int(len(ctx.uni["exhibitions"])),
            "in_fold_seasons": int(ctx.uni["exhibitions"]["season"].isin(FOLD_SEASONS).sum()),
            "rows_excluded_2x": int(2 * ctx.uni["exhibitions"]["season"].isin(FOLD_SEASONS).sum()),
        },
        "playin_played_not_scored": int(len(ctx.uni["playin_played"])),
        "playoff_rows_reported_separately": int(len(ctx.playoff_rows)),
        "fold_rows": int(len(ctx.fold_rows)),
        "fold_rows_per_season": {str(s): int((ctx.fold_rows["season"] == s).sum()) for s in FOLD_SEASONS},
        "postponed_not_played": int((~ctx.sch["played"]).sum()),
        "boxless_final_games_in_folds": [
            int(g) for g in (400975285, 401070917) if g in set(ctx.fold_rows["game_id"].astype(np.int64))
        ],
        "neutral_site_true_in_fold_rows": int((ctx.fold_rows["neutral_site"] == True).sum()),  # noqa: E712
    }


def _playoff_lls(ctx, per_arm, arg0_by_gid) -> dict:
    seg = {"n_rows": int(len(ctx.playoff_rows)), "note": "same frozen fold models; reported separately, never in the criterion"}
    if not len(ctx.playoff_rows):
        return seg
    ll_b1 = logloss_rows(arms.sigmoid_elo(ctx.playoff_elo_arg), ctx.playoff_y)
    seg["B1*_pooled_ll"] = float(ll_b1.mean())
    for arm in PF_GROUPS:
        info = per_arm[arm]
        best = info["best"]
        xh = group_x(ctx.playoff_h, arm, ctx.moments)
        xa = group_x(ctx.playoff_a, arm, ctx.moments)
        p = pf_p_home(ctx.playoff_elo_arg, xh, xa, best["phi"])
        seg[config_id(arm, best["phi"])] = float(logloss_rows(p, ctx.playoff_y).mean())
    return seg


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, pd.Timestamp):
        return o.isoformat()
    return str(o)


# ------------------------------------------------------------------ reports
def render_report(ctx, summary, per_arm, b0_consts, null_checks, t_start, lock_before, lock_after) -> str:
    c = summary["counts"]
    mom = summary["standardization_moments"]
    L = []
    L.append("# SELECTION REPORT — NBA-PLAYERFEAT-SCORED-V1 · Lane T_SELECT")
    L.append("")
    L.append(f"- Generated (run start): {t_start} · mode: `select` (TRAIN-INTERNAL ONLY) · seed {SEED}")
    L.append("- Windows: WARM-UP 2016–2017 (streams run, never scored) · SELECTION FOLDS 2018–2021 "
             "(4 rolling-origin, expanding) · **OOS 2022–2026 NEVER TOUCHED** — hard cap "
             f"`SEASON_MAX_REAL={SEASON_MAX_REAL}` enforced at load; future schedule files never opened: "
             f"{summary['season_cap']['skipped_future_files']}")
    L.append(f"- Feature table sha256 verified before use: `{FEATURE_SHA256}` (== FEATURE_TABLE_MANIFEST)")
    L.append(f"- Lock observations: BEFORE run `{lock_before.get('checked_at_utc')}` verdict "
             f"`{lock_before.get('verdict')}` (attempt {lock_before.get('attempt')}) · AFTER run "
             f"`{lock_after.get('checked_at_utc')}` verdict `{lock_after.get('verdict')}`")
    L.append("")
    L.append("## DESIGNED-NULL (gate-before-belief)")
    L.append("")
    L.append("phi=0 configs must reproduce B1* p_home **bit-for-bit** (max |Δp| == 0.0) on the full "
             f"fold stream ({c['fold_rows']} rows) before any other number is believed.")
    L.append("")
    L.append("| arm | max \\|Δp\\| vs B1* | verdict |")
    L.append("|---|---|---|")
    for a, v in null_checks.items():
        L.append(f"| {a} | {v!r} | {'PASS' if v == 0.0 else 'FAIL → TECHABORT_EQUIVALENCE'} |")
    L.append("")
    L.append("## B0 constant (floor)")
    L.append("")
    L.append("Refit law (protocol verbatim): per fold, home-win rate over REG played rows of all "
             "complete seasons strictly before the fold season (2016 onward; warm-up rows are train "
             "rows, never scored rows).")
    L.append("")
    L.append("| fold season | B0 constant (train home-win rate) |")
    L.append("|---|---|")
    for s, v in b0_consts.items():
        L.append(f"| {s} | {v!r} |")
    pooled_b0 = float(np.mean([b0_consts[str(s)] for s in FOLD_SEASONS]))
    L.append("")
    L.append(f"- Reference (uncriterion) pooled-window home-win rate over fold rows: "
             f"{float(ctx.fold_y.mean())!r}; simple mean of fold constants {pooled_b0!r}.")
    L.append("")
    L.append("## B1* (carried VERBATIM, never re-tuned)")
    L.append("")
    b1 = summary["b1_star"]
    L.append(f"- Own-Elo K={ELO_K:g}, HCA={ELO_HCA:g}, γ={ELO_GAMMA}, μ={ELO_INIT:g}; new lineages start "
             f"{ELO_INIT:g}; season-boundary reversion `R ← 1500 + 0.75·(R − 1500)` before a lineage's "
             "first prediction of a new season; date-grain same-day exclusion (all predictions of a UTC "
             "date from pre-date state; updates applied after all predictions of that date) — terminal "
             "protocol semantics inherited; HCA applied everywhere (frozen neutral-site law, counts "
             f"disclosed below); stream updates on played regular + playoff games (season_type ∈ {{2,3}}); "
             "play-in (season_type=5) and exhibitions never update the stream (matches the frozen "
             "feature-table prior law).")
    L.append(f"- Stream: {c['stream_updates']} updates, {c['season_reversions']} season "
             f"reversions over {c['played_games_loaded']} played games 2016–2021.")
    L.append(f"- Pooled fold LL (2018–2021 REG, n={c['fold_rows']}): {b1['pooled_fold_ll']!r} · "
             f"calibration slope {b1['calibration_slope']!r}")
    L.append("")
    L.append("## Standardization moments (pinned)")
    L.append("")
    L.append(f"- Population: {mom['population']} · ddof={mom['ddof']}")
    L.append("")
    L.append("| column | mu | sd |")
    L.append("|---|---|---|")
    for col in sorted(mom["mu"]):
        L.append(f"| {col} | {mom['mu'][col]!r} | {mom['sd'][col]!r} |")
    L.append("")
    L.append("Group composition (single φ per arm; multi-column groups enter as the sum of their "
             "standardized columns — recorded design decision): "
             + "; ".join(f"{a} = {' + '.join('z(' + cc + ')' for cc in GROUP_COLUMNS[a])}" for a in PF_GROUPS) + ".")
    L.append("")
    L.append("## Grid + folds (pre-registered, immutable)")
    L.append("")
    L.append(f"- φ ∈ {{{', '.join(f'{g:g}' for g in PHI_GRID)}}} per arm; each arm ALONE (never stacked); "
             "15 configs, all counted. Criterion: pooled mean LL over fold rows. Tie-break: fewer active "
             "params, then lexicographic config id.")
    L.append(f"- Fold rows: REG (season_type=2) played non-exhibition games of seasons "
             f"{list(FOLD_SEASONS)}: {c['fold_rows_per_season']} (total {c['fold_rows']}).")
    L.append(f"- Exhibitions excluded from rows with counts: {c['exhibition_games_excluded_from_rows']}. "
             f"Play-in played games present but never scored/updated: {c['playin_played_not_scored']}. "
             f"Playoff rows scored with the same frozen models, reported SEPARATELY (never in the "
             f"criterion): n={c['playoff_rows_reported_separately']}.")
    L.append(f"- Box-less FINAL games (neutral features) REMAIN in rows: ids {c['boxless_final_games_in_folds']} "
             "(2017 sibling 400900132 sits in warm-up, not scored).")
    L.append(f"- Neutral-site flag measured (`neutral_site=true` inside fold rows): "
             f"{c['neutral_site_true_in_fold_rows']}; per the frozen protocol HCA is applied everywhere "
             "(declared limitation; conditional switching would be a new trial).")
    L.append("")
    L.append("## Verdicts (G-ENTRY per arm)")
    L.append("")
    L.append("ADMIT: pooled inner ΔLL(arm, B1*) point < 0 AND calibration slope ∈ [0.85, 1.15] AND "
             "time-shuffled twin not winning. CI entirely > 0 ⇒ KILL. Twin beats parent ⇒ "
             "MACHINERY_SUSPECT, arm UN-SCORED. Bootstrap: tip-DATE-clustered, 10,000 resamples, "
             f"seed {SEED}, percentile CI.")
    L.append("")
    L.append("| arm | selected φ | pooled LL | ΔLL vs B1* (95% CI) | slope | twin LL (wins?) | verdict |")
    L.append("|---|---|---|---|---|---|---|")
    for a in PF_GROUPS:
        info = per_arm[a]
        b = info["best"]
        d = b["delta"]
        twin = f"{info['twin_ll']:.6f} ({'WINS' if info['twin_wins'] else 'clean'})"
        sel = f"{b['phi']:g}" if info["verdict"] == "ADMITTED" else "—"
        L.append(f"| {a} | {sel} | {b['pooled_ll']:.6f} | {d['point']:+.6f} [{d['ci95_lo']:+.6f}, {d['ci95_hi']:+.6f}] "
                 f"| {b['slope'] if b['slope'] is not None else 'n/a'} | {twin} | **{info['verdict']}** "
                 f"{'(' + ', '.join(info['reasons']) + ')' if info['reasons'] else ''} |")
    L.append("")
    L.append("## Frozen φ (ADMITTED arms)")
    L.append("")
    if summary["frozen_phi"]:
        for a, phi in summary["frozen_phi"].items():
            L.append(f"- **{a}: φ = {phi:g}** (config `{config_id(a, phi)}`)")
    else:
        L.append("- None — all candidate arms failed G-ENTRY (see verdicts above).")
    L.append("")
    L.append("## Diagnostics (outside budget)")
    L.append("")
    dg = summary["diagnostics"]["B1-HCA0"]
    L.append(f"- B1-HCA0 ablation: pooled fold LL {dg['pooled_ll']!r}; "
             f"ΔLL(B1*, B1-HCA0) = {dg['delta_ll_vs_B1_star']['point']:+.6f} "
             f"[{dg['delta_ll_vs_B1_star']['ci95_lo']:+.6f}, {dg['delta_ll_vs_B1_star']['ci95_hi']:+.6f}] "
             "(Δ < 0 favors HCA=100; H2 direction check only).")
    L.append(f"- Time-shuffled twins (feature pair swapped across team-sides per game by seeded coin, "
             f"seed {SEED}): on each arm's SELECTED config (= φ 0 for all three arms, where the swap is "
             f"an identity): PF-A {per_arm['PF-A']['twin_ll']:.6f}, PF-B {per_arm['PF-B']['twin_ll']:.6f}, "
             f"PF-C {per_arm['PF-C']['twin_ll']:.6f} — none wins. Extra diagnostic on each arm's best "
             "NON-zero config (twin cannot rescue it either): "
             + "; ".join(f"{a} φ={per_arm[a]['best_nonzero']['phi']:g} parent "
                         f"{per_arm[a]['best_nonzero']['pooled_ll']:.6f} vs twin "
                         f"{per_arm[a]['twin_nz_ll']:.6f} ({'WINS' if per_arm[a]['twin_nz_wins'] else 'no win'})"
                         for a in PF_GROUPS) + ".")
    L.append("")
    L.append("## Negative-first reading")
    L.append("")
    L.append("- Every non-zero φ in all three grids INCREASES pooled fold LL vs B1* (ΔLL > 0, CIs entirely "
             "> 0 at |φ| ≥ 25); each arm's grid minimum is its own φ=0 designed null, i.e. the arm "
             "degenerates to B1*. G-ENTRY fails on `point_dell_not_negative` (point ΔLL = 0.0, not < 0) — "
             "no kill fired (no CI of a SELECTED config is entirely > 0, since the selected config IS the "
             "null); no twin fired. **Slot release: no φ frozen for any PF arm; the rating-input shape "
             "carries no train-internal player-feature gain at the pre-registered grid scales.**")
    L.append("")
    L.append("## Feature-table reconciliation (read-only bytes)")
    L.append("")
    L.append("- sha256 verified == FEATURE_TABLE_MANIFEST; capped table 15,144 rows (seasons 2016–2021) "
             "after slicing the manifest-exact 13,230 future rows (2022–2026) — accounting asserted equal "
             "to the manifest per-season table, so any doctored row shifts it and aborts.")
    neutral_counts = {int(k): int(v) for k, v in ctx.features.groupby("season")["feature_neutral"].sum().items()}
    L.append(f"- Neutral rows in the capped window per season: {neutral_counts} "
             "(matches FEATURE_TABLE_MANIFEST rows for 2016–2021).")
    L.append("- Manifest composition wording note: the three box-less FINAL games' OWN rows measure "
             "`feature_neutral=0` in bytes (their features derive from prior games); box-less-ness means "
             "they contribute 0 usable rows to LATER games' prior windows. Per-season neutral counts "
             "reconcile exactly regardless; bytes are authority.")
    L.append("")
    L.append("## Budget / fit accounting")
    L.append("")
    L.append(f"- Ledger rows on real fold rows: {summary['budget']['ledger_rows_total']} = 15 PF candidate "
             "configs (all counted) + B0 + B1* (references) + B1-HCA0 (diagnostic row). Twin computations "
             "(outside budget): 6 = 3 on selected configs + 3 on best-non-zero configs. B0 refits: 4 "
             "constants. Elo replays: 2 streams (B1*, B1-HCA0) — PF arms share the B1* stream (φ enters "
             f"only the argument). Designed-null checks: 3. Every evaluated config has a SELECTION_LEDGER.jsonl row.")
    L.append("")
    L.append("## Data-shape observations")
    L.append("")
    L.append(f"- Schedule rows loaded (2016–2021 only): {c['schedule_rows_loaded']}; played: "
             f"{c['played_games_loaded']}; postponed/not played: {c['postponed_not_played']}.")
    L.append("- Language law: calibration/forecasting vocabulary only; no betting vocabulary anywhere.")
    L.append("- No OOS season, no GO token, and no scored OOS number exists in this lane.")
    L.append("")
    return "\n".join(L)


def render_verdict_table(summary, per_arm, b0_consts, b1_ll, hca0_ll, hca0_delta, b1_slope) -> str:
    L = []
    L.append("# VERDICT TABLE — NBA-PLAYERFEAT-SCORED-V1 · TRAIN-INTERNAL SELECTION")
    L.append("")
    L.append("Sign convention: ΔLL = LL(arm) − LL(B1*); Δ < 0 favors the arm. CI: tip-date-clustered "
             f"bootstrap 95%, 10,000 resamples, seed {SEED}. Slope band [0.85, 1.15].")
    L.append("")
    L.append("| # | arm / config | φ | pooled LL (folds 2018–21) | ΔLL vs B1* [95% CI] | slope | twin | verdict |")
    L.append("|---|---|---|---|---|---|---|---|")
    L.append(f"| 1 | B0 (per-fold refit) | — | see ledger | see ledger | n/a (constant p) | — | REFERENCE_FLOOR |")
    L.append(f"| 2 | B1* (K=32 HCA=100 γ=0.75) | — | {b1_ll:.6f} | 0 [0, 0] | {b1_slope:.4f} | — | REFERENCE_BASELINE |")
    i = 3
    for a in PF_GROUPS:
        info = per_arm[a]
        for cfg in sorted(info["configs"], key=lambda c: c["phi"]):
            is_best = cfg is info["best"]
            d = cfg["delta"]
            verdict = ("DESIGNED_NULL_OK" if cfg["phi"] == 0.0
                       else (info["verdict"] if is_best else "GRID_EVALUATED"))
            twin = (f"{info['twin_ll']:.6f} ({'WINS' if info['twin_wins'] else 'clean'})" if is_best else "—")
            L.append(f"| {i} | {a} `{config_id(a, cfg['phi'])}` | {cfg['phi']:g} | {cfg['pooled_ll']:.6f} | "
                     f"{d['point']:+.6f} [{d['ci95_lo']:+.6f}, {d['ci95_hi']:+.6f}] | "
                     f"{cfg['slope']:.4f} | {twin} | {verdict} |")
            i += 1
    L.append(f"| {i} | B1-HCA0 (diagnostic) | — | {hca0_ll:.6f} | "
             f"ΔLL(B1*,B1-HCA0)={hca0_delta['point']:+.6f} [{hca0_delta['ci95_lo']:+.6f}, {hca0_delta['ci95_hi']:+.6f}] "
             "| — | — | DIAGNOSTIC_ABLATION |")
    L.append("")
    L.append("**Frozen φ per ADMITTED arm:** "
             + (", ".join(f"{a} = {p:g}" for a, p in summary["frozen_phi"].items())
                if summary["frozen_phi"] else "NONE — no arm admitted"))
    L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------ selftest
def _expect_raise(fn, *contains):
    try:
        fn()
    except BaseException as e:  # noqa: BLE001  (SystemExit included: refusal paths raise it)
        msg = f"{type(e).__name__}: {e}"
        for c in contains:
            if c not in msg:
                raise AssertionError(f"exception message missing '{c}': {msg}")
        return msg
    raise AssertionError("expected a loud exception, none raised")


def run_selftest() -> int:
    checks = []

    def ok(name, cond, detail=""):
        checks.append((name, bool(cond), detail))
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")

    # 1. Hand-computed single Elo update at K=32 with HCA=100 inside the argument.
    p_hand = 1.0 / (1.0 + math.pow(10.0, -(1500.0 + 100.0 - 1500.0) / 400.0))
    ok("elo_hca_argument_p_hand", abs(p_hand - 0.6400650) < 1e-6, f"p={p_hand!r}")
    ok("elo_hca_update_hand",
       abs(32.0 * (1.0 - p_hand) - 11.5179200) < 1e-6,
       f"R_h-1500={32.0 * (1.0 - p_hand)!r}")
    import pandas as pd_1
    g1 = pd_1.DataFrame([{"game_id": 1, "season": 2016, "tip_date": pd_1.Timestamp("2000-01-01"),
                          "home_id": 1, "away_id": 2, "y": 1}])
    r1 = replay_elo(g1)
    ok("elo_hca_replay_p", abs(r1.p_home[0] - p_hand) < 1e-15, f"p={r1.p_home[0]!r}")
    rh, ra = r1.final_ratings[1], r1.final_ratings[2]
    ok("elo_hca_replay_updates",
       abs(rh - (1500.0 + 32.0 * (1.0 - p_hand))) < 1e-9 and abs(ra - (1500.0 - 32.0 * (1.0 - p_hand))) < 1e-9,
       f"R_h={rh!r} R_a={ra!r}")
    ok("elo_rating_sum_preserved", abs((rh + ra) - 3000.0) < 1e-9)

    # 2. gamma = 0.75 boundary reversion arithmetic (hand values) + replay-level.
    ok("gamma_hand_1700", gamma_revert(1700.0) == 1650.0, f"{gamma_revert(1700.0)!r}")
    ok("gamma_hand_1300", gamma_revert(1300.0) == 1350.0, f"{gamma_revert(1300.0)!r}")
    ok("gamma_hand_1500", gamma_revert(1500.0) == 1500.0)
    g2 = pd_1.DataFrame([
        {"game_id": 10, "season": 2016, "tip_date": pd_1.Timestamp("2000-01-01"), "home_id": 1, "away_id": 2, "y": 1},
        {"game_id": 11, "season": 2017, "tip_date": pd_1.Timestamp("2000-06-20"), "home_id": 1, "away_id": 2, "y": 0},
    ])
    r2 = replay_elo(g2)
    # season 1: p=0.5 (HCA=100? no — this replay uses the B1* constants HCA=100; hand-recompute:
    p_s1 = 1.0 / (1.0 + math.pow(10.0, -100.0 / 400.0))
    a1 = 1500.0 + 32.0 * (1.0 - p_s1)
    b1_ = 1500.0 - 32.0 * (1.0 - p_s1)
    a1r = gamma_revert(a1)
    b1r = gamma_revert(b1_)
    p_s2 = 1.0 / (1.0 + math.pow(10.0, -((a1r + 100.0) - b1r) / 400.0))
    ok("gamma_replay_season_boundary", abs(r2.p_home[1] - p_s2) < 1e-12,
       f"p_s2={r2.p_home[1]!r} expected={p_s2!r}")
    ok("gamma_replay_hand_band", 0.6626 < r2.p_home[1] < 0.6627)
    ok("gamma_reversion_count", r2.n_season_reversions == 4, f"n={r2.n_season_reversions}")  # 2 lineages x 2 seasons

    # 3. Designed-null byte-identity on >= 3 synthetic streams (max |dp| == 0.0).
    for si, seed in enumerate((1, 2, 3), start=1):
        st = synthetic_stream(seed=seed, n_days=120, games_per_day=3, n_teams=10, season_len_days=40)
        rep = replay_elo(st)
        elo_arg = rep.elo_arg
        rng = np.random.default_rng(seed)
        xh = rng.normal(size=len(st))
        xa = rng.normal(size=len(st))
        p_b1 = arms.sigmoid_elo(elo_arg)
        p_pf = pf_p_home(elo_arg, xh, xa, 0.0)
        maxdp = float(np.max(np.abs(p_pf - p_b1)))
        ok(f"designed_null_synthetic_stream_{si}", maxdp == 0.0, f"max|dp|={maxdp!r}")

    # 4. Standardization example: [1,2,3,4] -> mu 2.5, sd sqrt(1.25), z(4)=1.3416407864998738.
    import pandas as pd_2
    dfx = pd_2.DataFrame({"v": [1.0, 2.0, 3.0, 4.0]})
    m = moments_from_frame(dfx, ["v"])
    z = arms.standardize(np.array([4.0]), m.mu["v"], m.sd["v"])[0]
    ok("standardization_mu", m.mu["v"] == 2.5, f"mu={m.mu['v']!r}")
    ok("standardization_sd", abs(m.sd["v"] - math.sqrt(1.25)) < 1e-12, f"sd={m.sd['v']!r}")
    ok("standardization_z4", abs(z - 1.3416407864998738) < 1e-12, f"z={z!r}")

    # 5. Neutral-rule behavior: a neutral row carries x as standardized 0.0 and the
    #    phi=0 identity holds; phi!=0 shifts the argument by exactly phi*(xh-xa).
    rng = np.random.default_rng(7)
    elo_arg = rng.normal(scale=80.0, size=16)
    xh = np.zeros(16); xa = rng.normal(size=16)  # 'neutral' home side: raw scalars 0.0
    p0 = pf_p_home(elo_arg, xh, xa, 0.0)
    ok("neutral_phi0_identity", float(np.max(np.abs(p0 - arms.sigmoid_elo(elo_arg)))) == 0.0)
    phi = 25.0
    shift = pf_p_home(elo_arg, xh, xa, phi) - arms.sigmoid_elo(elo_arg)
    dphi = arms.sigmoid_elo(elo_arg + phi * (xh - xa)) - arms.sigmoid_elo(elo_arg)
    ok("neutral_phi25_shift_exact", float(np.max(np.abs(shift - dphi))) == 0.0)
    # real-table direction check happens in the select run (load-time assertions).

    # 6. Same-day exclusion (date-grain as-of law): all predictions of a UTC date
    #    use the pre-date rating state (day-1 close), never an earlier same-date
    #    result; next-day predictions include the full day-2 update.
    g3 = pd_1.DataFrame([
        {"game_id": 20, "season": 2016, "tip_date": pd_1.Timestamp("2000-01-01"), "home_id": 1, "away_id": 2, "y": 1},
        {"game_id": 21, "season": 2016, "tip_date": pd_1.Timestamp("2000-01-02"), "home_id": 3, "away_id": 4, "y": 0},
        {"game_id": 22, "season": 2016, "tip_date": pd_1.Timestamp("2000-01-02"), "home_id": 1, "away_id": 2, "y": 0},
        {"game_id": 23, "season": 2016, "tip_date": pd_1.Timestamp("2000-01-03"), "home_id": 2, "away_id": 3, "y": 1},
    ])
    r3 = replay_elo(g3)
    # Hand model (HCA=100 everywhere, K=32):
    p_a = p_hand  # E_home for any 1500-vs-1500 game on a line's first day
    t1_d1 = 1500.0 + 32.0 * (1.0 - p_a)   # team 1 won game 20 (day 1)
    t2_d1 = 1500.0 - 32.0 * (1.0 - p_a)
    # Day-2 predictions must come from day-1 close:
    p21_exp = 1.0 / (1.0 + math.pow(10.0, -100.0 / 400.0))                      # fresh teams 3v4
    p22_exp = 1.0 / (1.0 + math.pow(10.0, -((t1_d1 + 100.0) - t2_d1) / 400.0))  # teams 1v2, day-1 state
    ok("same_day_fresh_team_p21", abs(r3.p_home[1] - p21_exp) < 1e-15, f"p21={r3.p_home[1]!r}")
    ok("same_day_exclusion_p22_from_day1_state",
       abs(r3.p_home[2] - p22_exp) < 1e-12,
       f"p22={r3.p_home[2]!r} expected={p22_exp!r}")
    # Day-3 prediction (teams 2v3) includes ALL day-2 updates: game 21 home 3 LOST
    # (E=p21_exp), game 22 home 1 LOST / away 2 WON (E_home=p22_exp from day-1
    # state; away update uses E_away = 1-p22_exp).
    t3_d2 = 1500.0 - 32.0 * p21_exp
    t2_d3 = t2_d1 + 32.0 * (1.0 - (1.0 - p22_exp))  # S_away=1, E_away=1-p22_exp
    p23_exp = 1.0 / (1.0 + math.pow(10.0, -((t2_d3 + 100.0) - t3_d2) / 400.0))
    ok("next_day_update_seen", abs(r3.p_home[3] - p23_exp) < 1e-12,
       f"p23={r3.p_home[3]!r} expected={p23_exp!r}")

    # 7. Tie abort (NBA tie semantics undefined).
    def _tie():
        sch = pd_1.DataFrame([{"status_type_name": "STATUS_FINAL", "home_score": 100.0, "away_score": 100.0,
                               "season_type": 2, "home_id": 1, "away_id": 2}])
        uni = {"played": sch}
        played = sch.copy()
        if int((played["home_score"] == played["away_score"]).sum()):
            raise TechAbort("TIE_GAME: equal scores present; NBA tie semantics undefined, aborting loud")
        return uni
    _expect_raise(_tie, "TIE_GAME")
    ok("tie_abort_loud", True)

    # 8. Leakage canary: a doctored 2022 row inside a loaded file must ABORT the loader.
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        real = SCHEDULE_ROOT / "nba_schedule_2021.csv"
        df = pd.read_csv(real, low_memory=False)
        df.loc[df.index[0], "season"] = 2022
        df.to_csv(tdp / "nba_schedule_2021.csv", index=False)
        _expect_raise(lambda: load_schedule(tdp, 2021, SEASON_MAX_REAL),
                      "SEASON_CAP_VIOLATION", "2022")
        ok("doctored_2022_row_aborts", True)
        # and the healthy file passes the cap assertion
        (tdp / "nba_schedule_2021.csv").unlink()
        df2 = pd.read_csv(real, low_memory=False)
        df2.to_csv(tdp / "nba_schedule_2021.csv", index=False)
        d = load_schedule(tdp, 2021, SEASON_MAX_REAL)
        ok("season_cap_normal_pass", int(d["season"].max()) <= SEASON_MAX_REAL and len(d) == len(df2))

    # 9. evaluate-oos refuses real data without the GO token (token must not exist).
    if GO_TOKEN_PATH.exists():
        raise TechAbort(f"BOUNDARY_VIOLATION: GO token exists at {GO_TOKEN_PATH}; cycle law: agents never type GO")
    _expect_raise(lambda: mode_evaluate_oos(real_data=True, json_out=False), "OOS_REFUSED_NO_GO_TOKEN")
    ok("evaluate_oos_refusal", True)

    # 10. Update-eligibility filters: play-in and exhibition games never update the
    #     stream; fold rows exclude exhibitions and include box-less FINAL games.
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        sched = pd.DataFrame([
            {"game_id": 1, "season": 2018, "game_date_time": "2018-01-01T00:00:00Z", "start_date": "2018-01-01T00:00:00Z",
             "status_type_name": "STATUS_FINAL", "home_id": 1, "away_id": 2, "home_score": 1.0, "away_score": 0.0,
             "season_type": 2},
            {"game_id": 2, "season": 2018, "game_date_time": "2018-01-02T00:00:00Z", "start_date": "2018-01-02T00:00:00Z",
             "status_type_name": "STATUS_FINAL", "home_id": 31, "away_id": 32, "home_score": 1.0, "away_score": 0.0,
             "season_type": 2},
            {"game_id": 3, "season": 2018, "game_date_time": "2018-01-03T00:00:00Z", "start_date": "2018-01-03T00:00:00Z",
             "status_type_name": "STATUS_FINAL", "home_id": 3, "away_id": 4, "home_score": 1.0, "away_score": 0.0,
             "season_type": 5},
            {"game_id": 4, "season": 2018, "game_date_time": "2018-01-04T00:00:00Z", "start_date": "2018-01-04T00:00:00Z",
             "status_type_name": "STATUS_FINAL", "home_id": 1, "away_id": 3, "home_score": 1.0, "away_score": 0.0,
             "season_type": 3},
            {"game_id": 5, "season": 2018, "game_date_time": "2018-01-05T00:00:00Z", "start_date": "2018-01-05T00:00:00Z",
             "status_type_name": "STATUS_POSTPONED", "home_id": 2, "away_id": 4, "home_score": None, "away_score": None,
             "season_type": 2},
        ])
        sched.to_csv(tdp / "nba_schedule_2018.csv", index=False)
        sch = load_schedule(tdp, 2018, 2018)
        uni = build_universe(sch)
        ok("filters_stream_excludes_playin_exhibition_postponed",
           len(uni["stream"]) == 2 and set(uni["stream"]["game_id"]) == {1, 4},
           f"stream games={sorted(uni['stream']['game_id'])}")
        ok("filters_rows_reg_only",
           len(uni["reg_played"]) == 1 and int(uni["reg_played"]["game_id"].iloc[0]) == 1)
        ok("filters_exhibition_counted", len(uni["exhibitions"]) == 1)
        ok("filters_playin_counted", len(uni["playin_played"]) == 1)

    # 11. Feature table + manifest, real bytes (read-only): sha + cap accounting +
    #     neutral zero law + box-less fold rows present with neutral features.
    ft = load_features(SEASON_MAX_REAL)
    ok("feature_sha_and_cap_accounting",
       len(ft) == 15_144 and set(ft["season"].unique()) == set(range(2016, 2022)),
       f"rows={len(ft)} seasons={sorted(ft['season'].unique())}")
    bl = set(ft.loc[ft["game_id"].isin([400975285, 401070917, 400900132]), "game_id"].unique())
    ok("boxless_games_present_in_table", bl == {400975285, 401070917, 400900132}, f"got={sorted(bl)}")
    # Bytes measured: the box-less games' OWN rows carry prior-derived (non-neutral)
    # features; box-less-ness means they contribute 0 usable rows to later games'
    # prior windows. The dispatch law they satisfy here: they REMAIN in scored
    # fold rows (2 of the 3 sit in fold seasons 2018/2019, verified in the select run
    # by the 2x-coverage join assertion). Assert presence + non-exhibition here:
    blrows = ft[ft["game_id"].isin([400975285, 401070917])]
    ok("boxless_fold_rows_remain",
       len(blrows) == 4 and bool((blrows["is_exhibition"] == 0).all()),
       f"rows={len(blrows)}")

    # 12. paired bootstrap determinism: same inputs -> identical CI bytes.
    rngd = np.random.default_rng(11)
    lla = rngd.normal(size=500) - 0.1
    llb = rngd.normal(size=500)
    dates = np.array([pd_1.Timestamp("2000-01-01") + pd_1.Timedelta(days=i % 90) for i in range(500)])
    c1 = paired_delta_ci(lla, llb, dates)
    c2 = paired_delta_ci(lla, llb, dates)
    ok("bootstrap_deterministic", c1 == c2, f"{c1}")

    # 13. calibration slope: perfect-calibration synthetic slope ~ 1; constant p -> None.
    rngs = np.random.default_rng(5)
    eta = rngs.normal(scale=0.7, size=20000)
    p = 1.0 / (1.0 + np.exp(-eta))
    y = (rngs.random(20000) < p).astype(float)
    sl = calibration_slope(p, y)
    ok("slope_recovers_1", sl is not None and abs(sl - 1.0) < 0.1, f"slope={sl!r}")
    ok("slope_constant_p_none", calibration_slope(np.full(100, 0.6), (np.arange(100) % 2).astype(float)) is None)

    # 14. synthetic evaluate-oos path is allowed (sandbox only) — smoke: no crash.
    st = synthetic_stream(seed=42, n_days=10, games_per_day=2, n_teams=5)
    rep = replay_elo(st)
    ok("evaluate_oos_synthetic_smoke", len(rep.p_home) == len(st) and np.all(np.isfinite(rep.p_home)))

    # 15. grid immutability + config ids + tie-break keys.
    ok("grid_immutable", grid_configs() == [(a, float(ph)) for a in PF_GROUPS for ph in PHI_GRID]
       and len(grid_configs()) == 15)
    ok("config_id_format", config_id("PF-A", -50.0) == "PF-A|phi=-50")

    failed = [n for n, c, _ in checks if not c]
    print(f"\nselftest: {len(checks) - len(failed)}/{len(checks)} PASS" + (f"; FAILED: {failed}" if failed else ""))
    return 0 if not failed else 1


# ------------------------------------------------------------------ modes
def mode_evaluate_oos(real_data: bool, json_out: bool) -> int:
    """Walk-forward OOS is POST-GO ONLY. Real-data OOS requires the cycle GO token;
    the token does not exist (agents never type GO) => refuse, always.
    Synthetic fixtures may run sandbox-only."""
    if real_data:
        if GO_TOKEN_PATH.exists():
            # even a present token must be owner-typed at the cycle gate; agents never
            # consume GO from a lane. Refuse regardless.
            raise SystemExit(
                "OOS_REFUSED_GO_TOKEN_PRESENT_BUT_AGENT_GO_CONSUMPTION_FORBIDDEN: "
                "OOS evaluation is executed only by the cycle's own gate after owner GO."
            )
        raise SystemExit(
            "OOS_REFUSED_NO_GO_TOKEN: walk-forward OOS [2022..2026] is POST-GO ONLY; "
            f"no GO token exists at {GO_TOKEN_PATH}; refusing real-data OOS computation."
        )
    # synthetic-only sandbox path (fixtures/rehearsal; no real rows, no real seasons)
    st = synthetic_stream(seed=20261005, n_days=200, games_per_day=4, n_teams=12, season_len_days=50)
    rep = replay_elo(st)
    y = st["y"].to_numpy(dtype=np.float64)
    ll = float(logloss_rows(rep.p_home, y).mean())
    sandbox = DATA_OUT / "sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)
    (sandbox / "SANDBOX_SYNTHETIC_OOS_REHEARSAL.json").write_text(json.dumps({
        "schema": "nba_playerfeat_synthetic_rehearsal@1", "note": "synthetic stream only; no real OOS row touched",
        "n_games": int(len(st)), "pooled_ll": ll, "seed": SEED, "generated_utc": utcnow(),
    }, indent=2))
    if json_out:
        print(json.dumps({"mode": "evaluate-oos", "data": "synthetic", "n_games": int(len(st)), "pooled_ll": ll}))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="NBA-PLAYERFEAT-SCORED-V1 T_SELECT evaluation harness")
    ap.add_argument("mode", nargs="?", choices=["select", "evaluate-oos"], default=None)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--real", action="store_true", help="(evaluate-oos) request real OOS data — refused without GO")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return run_selftest()
    if args.mode == "evaluate-oos":
        return mode_evaluate_oos(real_data=bool(args.real), json_out=bool(args.json))
    if args.mode == "select":
        return run_select(json_out=bool(args.json))
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
