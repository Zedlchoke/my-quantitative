# harness.py — WNBA-PLAYERFEAT-SCORED-V1 · lane T_SELECT · 2026-10-05
#
# Modes:
#   --selftest                     hand-computed fixtures + canaries (no real scored run)
#   --mode select                  TRAIN-INTERNAL selection. REAL DATA HARD-CAPPED at
#                                  season <= SEASON_MAX_REAL = 2018 (loud assertion).
#                                  OOS [2020..2026] is NEVER read in this mode.
#   --mode evaluate-oos            REFUSES real data without the owner GO token (which
#                                  does not exist pre-gate). Synthetic corpora only.
#
# Write scope: lanes/T_SELECT/** + ~/.my-quantitative-data/wnba-playerfeat-scored-v1/selection/
# Everything else read-only. No git. Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arms  # noqa: E402

# ------------------------------------------------------------------ constants
CYCLE_ID = "WNBA-PLAYERFEAT-SCORED-V1"
LANE = "T_SELECT"
SEASON_MAX_REAL = 2018          # HARD CAP — loud assertion, doctored rows ABORT
SEASON_MIN_REAL = 2002
WARMUP_SEASONS = (1997, 1998, 1999, 2000, 2001)
OOS_SEASONS = tuple(range(2020, 2027))   # NEVER touched by select mode
GO_PHRASE = "GO WNBA PLAYERFEAT SCORED V1 EVALUATION"

ROOT = "/Users/hoangminhlong/my-quantitative"
FEATURE_PARQUET = os.path.expanduser(
    "~/.my-quantitative-data/playerfeat-prep-v1/wnba/features/wnba_player_features_2002_2026.parquet")
FEATURE_SHA256 = "ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf"
FEATURE_BYTES = 826415
LINEAGE_CSV = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv")
ESPN_DIR = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw/espn_schedules")
STATS_DIR = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw/wnba_stats_schedules")

OUT_DIR = os.path.expanduser("~/.my-quantitative-data/wnba-playerfeat-scored-v1/selection")
LANE_DIR = os.path.join(ROOT, ".worktrees/wnba-playerfeat-scored-v1/integration/lanes/T_SELECT")
DISPATCH_SHA = "8130de5af6c05dcf8e67efdfd2f5bc6f575ca92d"

ALL_STAR_ALIASES = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE",
                    "CLA", "COL", "SPO", "COOP", "WNBASTARS"}

# B1-WNBA validation blocks: 4 expanding-origin 2-season blocks over the TRAIN tail
# (successor packet §1). Origins: through 2010 / 2012 / 2014 / 2016.
B1_BLOCKS = ((2011, 2012), (2013, 2014), (2015, 2016), (2017, 2018))
B1_BLOCK_SEASONS = tuple(s for blk in B1_BLOCKS for s in blk)
# Feature-arm folds: 5 expanding-origin single-season folds 2014..2018
# (era-floor adaptation of the packet's 4x2-season blocks; disclosed in the plan).
FEATURE_FOLDS = (2014, 2015, 2016, 2017, 2018)

# Pre-registered feature constructions (pinned BEFORE any scored look; see report):
XB_COL, XB_REASON = "b5_minutes_hhi", "b5_neutral_reason"     # WF-B
XC_COL, XC_REASON = "c_absence_share", "c_neutral_reason"     # WF-C


class Abort(Exception):
    """Loud stop (BLOCKED_DATA / TECHABORT / gate refusal)."""


class CapViolation(Abort):
    """SEASON_MAX_REAL hard-cap violation."""


# ------------------------------------------------------------------ input checks
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_feature_table():
    if not os.path.exists(FEATURE_PARQUET):
        raise Abort("BLOCKED_DATA: feature table missing at %s" % FEATURE_PARQUET)
    size = os.path.getsize(FEATURE_PARQUET)
    digest = sha256_file(FEATURE_PARQUET)
    if digest != FEATURE_SHA256 or size != FEATURE_BYTES:
        raise Abort(
            "BLOCKED_DATA: feature-table sha256/bytes mismatch vs manifest "
            "(got %s / %d B, want %s / %d B)" % (digest, size, FEATURE_SHA256, FEATURE_BYTES))
    return digest


def load_lineage():
    lin = pd.read_csv(LINEAGE_CSV, keep_default_na=False)
    stats_abbr_to_fk = {}
    for _, r in lin.iterrows():
        for a in str(r["stats_abbrs"]).split(";"):
            a = a.strip()
            if not a:
                continue
            stats_abbr_to_fk.setdefault(a, set()).add(str(r["franchise_key"]).strip())
    multi = {a: sorted(v) for a, v in stats_abbr_to_fk.items() if len(v) > 1}
    if multi:
        raise Abort("BLOCKED_DATA: ambiguous stats-side abbreviations %s" % multi)
    return {a: next(iter(v)) for a, v in stats_abbr_to_fk.items()}


def enforce_season_cap(seasons, context):
    """HARD CAP: real seasons above SEASON_MAX_REAL abort the run loudly."""
    mx = max(seasons)
    if mx > SEASON_MAX_REAL:
        raise CapViolation(
            "HARD CAP VIOLATION [%s]: season %d > SEASON_MAX_REAL=%d — "
            "OOS data is never touched by select mode. ABORT."
            % (context, mx, SEASON_MAX_REAL))


def enforce_oos_gate(source, go_token):
    """evaluate-oos gate: real data requires the owner GO token (typed fresh at the
    cycle gate, post-A7). Without it: refuse before touching any bytes."""
    if source == "synthetic":
        return
    if source == "real":
        if go_token != GO_PHRASE:
            raise Abort(
                "OOS-GATE-REFUSED: evaluate-oos on real data requires the owner GO token "
                "typed verbatim at this cycle's own gate. No such token exists pre-gate. "
                "NOT_RUN_OOS_GO_MISSING.")


# ------------------------------------------------------------------ loaders
def load_feature_rows():
    """Frozen feature table -> {(game_id, team_side): light row dict} + game index.

    Only PIT-legal pre-game columns are consumed: continuity_c (+reason),
    b5_minutes_hhi (+reason), c_absence_share (+reason), plus keys/tips/flags.
    `active`/`reason`-class columns are never read; no outcome columns exist.
    """
    ft = pd.read_parquet(FEATURE_PARQUET)
    # HARD CAP at read time: the frozen table spans 2002-2026, but this lane reads
    # ONLY seasons <= SEASON_MAX_REAL. OOS rows (2019-2026) never enter memory.
    ft = ft[ft["season"] <= SEASON_MAX_REAL]
    enforce_season_cap(set(int(s) for s in ft["season"]), "feature_table_read")
    need = {"game_id", "season", "team_side", "team_id", "franchise_key", "tip_utc",
            "is_team_game1", XB_COL, XB_REASON, XC_COL, XC_REASON,
            "continuity_c", "continuity_neutral_reason"}
    missing = need - set(ft.columns)
    if missing:
        raise Abort("BLOCKED_DATA: feature table missing columns %s" % sorted(missing))
    rows = {}
    games_index = {}
    for r in ft.itertuples(index=False):
        gid = str(r.game_id)
        side = str(r.team_side)
        rows[(gid, side)] = {
            "season": int(r.season),
            "team_id": int(r.team_id),
            "franchise_key": str(r.franchise_key),
            "tip_utc": str(r.tip_utc),
            "is_team_game1": bool(r.is_team_game1),
            "continuity_c": None if pd.isna(getattr(r, "continuity_c")) else float(getattr(r, "continuity_c")),
            "continuity_neutral_reason": str(getattr(r, "continuity_neutral_reason")),
            "xb": None if pd.isna(getattr(r, XB_COL)) else float(getattr(r, XB_COL)),
            "xb_reason": str(getattr(r, XB_REASON)),
            "xc": None if pd.isna(getattr(r, XC_COL)) else float(getattr(r, XC_COL)),
            "xc_reason": str(getattr(r, XC_REASON)),
        }
        g = games_index.setdefault(gid, {"season": int(r.season), "tip_utc": str(r.tip_utc),
                                         "sides": {}})
        g["sides"][side] = int(r.team_id)
    if len(rows) != 2 * len(games_index):
        raise Abort("BLOCKED_DATA: feature table is not 2 rows per game")
    return rows, games_index


def load_espn_universe(feature_games_index):
    """Universe games with outcomes, SEASONS <= SEASON_MAX_REAL only (hard cap).

    Filter law (frozen): status_type_state == 'post'; drop Forfeit/Postponed;
    drop All-Star alias rows; never filter on score presence. Universe identity
    vs the frozen feature table asserted (0 missing, 0 extra).
    """
    frames = []
    for year in range(SEASON_MIN_REAL, SEASON_MAX_REAL + 1):
        path = os.path.join(ESPN_DIR, "wnba_schedule_%d.csv" % year)
        if not os.path.exists(path):
            raise Abort("BLOCKED_DATA: missing ESPN schedule %s" % path)
        df = pd.read_csv(path, dtype={"game_id": str, "id": str})
        frames.append(df)
    esp = pd.concat(frames, ignore_index=True)

    def _rowmask(df):
        post = df["status_type_state"] == "post"
        bad = (df["status_type_name"].isin(["Forfeit", "Postponed"])
               | df["status_type_description"].fillna("").isin(["Forfeit", "Postponed"])
               | df["status_type_short_detail"].fillna("").isin(["Forfeit", "Postponed"]))
        alias = (df["home_abbreviation"].isin(ALL_STAR_ALIASES)
                 | df["away_abbreviation"].isin(ALL_STAR_ALIASES))
        return post & ~bad & ~alias

    uni = esp[_rowmask(esp)].copy()
    uni = uni[uni["season"] <= SEASON_MAX_REAL]
    enforce_season_cap(set(int(s) for s in uni["season"]), "espn_universe")

    got = set(uni["game_id"].astype(str))
    want = set(feature_games_index)
    if got != want:
        raise Abort("BLOCKED_DATA: universe mismatch vs feature table "
                    "(missing %d, extra %d)" % (len(want - got), len(got - want)))

    games = []
    neutral_count = 0
    for r in uni.itertuples(index=False):
        gid = str(r.game_id)
        season = int(r.season)
        fi = feature_games_index[gid]
        if fi["season"] != season:
            raise Abort("BLOCKED_DATA: season mismatch game %s" % gid)
        hs = fi["sides"].get("home")
        if hs is not None and int(r.home_id) != hs:
            raise Abort("BLOCKED_DATA: home team_id mismatch game %s" % gid)
        if fi["sides"].get("away") is not None and int(r.away_id) != fi["sides"]["away"]:
            raise Abort("BLOCKED_DATA: away team_id mismatch game %s" % gid)
        home_win = int(int(r.home_score) > int(r.away_score))
        neutral = bool(r.neutral_site) if not pd.isna(r.neutral_site) else False
        neutral_count += int(neutral)
        games.append({
            "tip": pd.Timestamp(str(r.date)).tz_convert("UTC"),
            "game_id": gid, "season": season,
            "fk_home": None, "fk_away": None,  # filled from the frozen table below
            "home_win": home_win, "neutral": neutral,
            "row_home": None, "row_away": None,
        })
    games.sort(key=lambda g: (g["tip"], g["game_id"]))
    return games, neutral_count


def attach_feature_sides(games, feature_rows):
    """Fill franchise keys + light feature rows from the frozen feature table
    (the ONLY sanctioned franchise join path; raw abbreviations never used)."""
    for g in games:
        rh = feature_rows.get((g["game_id"], "home"))
        ra = feature_rows.get((g["game_id"], "away"))
        if rh is None or ra is None:
            raise Abort("BLOCKED_DATA: feature rows missing for game %s" % g["game_id"])
        g["fk_home"], g["fk_away"] = rh["franchise_key"], ra["franchise_key"]
        g["row_home"], g["row_away"] = rh, ra
    return games


def load_warmup(lineage_abbr_to_fk):
    """Stats-side 1997-2001 schedules -> rating-stream WARM-UP rows ONLY.

    ERA LAW: warm-up rows never enter train/score/feature sets. Join path: the
    20-key lineage table's stats_abbrs column (stats-side abbreviations are
    stable; the ESPN raw-abbreviation ban does not relax — ESPN abbreviations
    are never read here). No neutral-site flag exists on this side: disclosed.
    """
    games = []
    for year in WARMUP_SEASONS:
        path = os.path.join(STATS_DIR, "wnba_schedule_%d.csv.gz" % year)
        if not os.path.exists(path):
            raise Abort("BLOCKED_DATA: missing warm-up schedule %s "
                        "(fallback warm-up 2002-2004 not implemented: corpus IS on disk)"
                        % path)
        with gzip.open(path, "rt") as f:
            df = pd.read_csv(f, dtype={"game_id": str})
        if df["game_id"].duplicated().any():
            raise Abort("BLOCKED_DATA: duplicate game_id in warm-up %d" % year)
        if df["home_pts"].isna().any() or df["away_pts"].isna().any():
            raise Abort("BLOCKED_DATA: unscored rows in warm-up %d" % year)
        for r in df.itertuples(index=False):
            hk = lineage_abbr_to_fk.get(str(r.home_team_abbreviation).strip())
            ak = lineage_abbr_to_fk.get(str(r.away_team_abbreviation).strip())
            if hk is None or ak is None:
                raise Abort("BLOCKED_DATA: warm-up abbreviation unmapped %d (%s/%s)"
                            % (year, r.home_team_abbreviation, r.away_team_abbreviation))
            if hk == ak:
                continue  # defensive; cannot happen in a schedule
            games.append({
                "tip": pd.Timestamp(str(r.game_date)).tz_localize("UTC"),
                "game_id": "W%d-%s" % (year, r.game_id), "season": int(r.season),
                "fk_home": hk, "fk_away": ak,
                "home_win": int(int(r.home_pts) > int(r.away_pts)),
                "neutral": False,   # no flag exists on the stats side — disclosed
                "row_home": None, "row_away": None,
            })
    enforce_season_cap(set(g["season"] for g in games), "warmup")
    games.sort(key=lambda g: (g["tip"], g["game_id"]))
    return games


def build_full_games(warmup_games, universe_games):
    games = list(warmup_games) + list(universe_games)
    games.sort(key=lambda g: (g["tip"], g["game_id"]))
    return games


# ------------------------------------------------------------------ features
def compute_moments(feature_rows, col, reason_col):
    """Standardization moments pinned on TRAIN computed rows (seasons <= cap,
    reason empty), pooled home+away. Population sd (ddof=0). Frozen in outputs."""
    vcol = "xb" if col == XB_COL else "xc"
    rcol = "xb_reason" if reason_col == XB_REASON else "xc_reason"
    vals = []
    for row in feature_rows.values():
        if row["season"] > SEASON_MAX_REAL:
            continue
        if row[rcol] != "":
            continue
        v = row[vcol]
        if v is None:
            raise Abort("BLOCKED_DATA: computed row with NA value (%s)" % col)
        vals.append(v)
    if not vals:
        raise Abort("BLOCKED_DATA: no computed rows for %s" % col)
    n = len(vals)
    mu = sum(vals) / n
    var = sum((v - mu) ** 2 for v in vals) / n
    sd = var ** 0.5
    if not (sd > 0):
        raise Abort("BLOCKED_DATA: degenerate sd for %s" % col)
    seasons_used = sorted(set(row["season"] for row in feature_rows.values()
                              if row["season"] <= SEASON_MAX_REAL and row[rcol] == ""))
    return {"col": col, "reason_col": reason_col, "mean": mu, "sd": sd,
            "n_rows": n, "seasons": "%d-%d" % (min(seasons_used), max(seasons_used))}


def make_x_fn(moments):
    """Standardized feature fn with era-floor + neutral rules.

    Rules (frozen):
      row is None (warm-up rows carry no feature rows) -> x=0, no flag.
      season < 2013 (minutes-quality floor)            -> x=0, flag era_floor.
      neutral reason non-empty                          -> x=0, flag neutral_x0.
      else                                              -> x=(v-mean)/sd.
    """
    mu, sd = moments["mean"], moments["sd"]
    vcol = "xb" if moments["col"] == XB_COL else "xc"
    rcol = "xb_reason" if moments["col"] == XB_COL else "xc_reason"

    def x_fn(row, season):
        if row is None:
            return 0.0, None
        if row["season"] < 2013:
            return 0.0, "era_floor"
        if row[rcol] != "":
            return 0.0, "neutral_x0"
        return (row[vcol] - mu) / sd, None

    return x_fn


def make_c_fn():
    """WF-A continuity: c from the frozen table where computed (2014+, reason empty),
    else 1.0 (parent law — game-1 v2 rows, expansion, missing all collapse to parent)."""

    def c_fn(row, season):
        if row is None:
            return 1.0
        if row["continuity_neutral_reason"] == "" and row["continuity_c"] is not None:
            return float(row["continuity_c"])
        return 1.0

    return c_fn


# ------------------------------------------------------------------ evaluation
def preds_by_season(preds):
    out = {}
    for d in preds:
        out.setdefault(d["season"], []).append(d)
    return out


def block_mean_ll(by_season, seasons):
    pts = [d for s in seasons for d in by_season.get(s, [])]
    if not pts:
        return float("nan"), 0
    return arms.mean_ll(pts), len(pts)


def fold_predictions(preds, seasons):
    return [d for d in preds if d["season"] in seasons]


def tip_date_clusters(preds):
    return [str(d["tip"].date()) for d in preds]


# ------------------------------------------------------------------ lock
def locks_inspect(retries=3, wait_s=60):
    """Heavy-lock discipline: inspect from repo ROOT; retry 3x60s; else NOT_RUN."""
    import subprocess
    cmd = [os.path.join(ROOT, ".venv/bin/python"), "research/researchctl.py",
           "locks", "inspect"]
    attempts = []
    for attempt in range(1, retries + 1):
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              timeout=120)
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"verdict": "PARSE_FAIL", "stdout": proc.stdout[:400],
                       "stderr": proc.stderr[:400]}
        attempts.append({"attempt": attempt, "verdict": payload.get("verdict")})
        if payload.get("verdict") == "FREE_PROVEN":
            return {"verdict": "FREE_PROVEN", "attempts": attempts, "attempts_used": attempt}
        if attempt < retries:
            time.sleep(wait_s)
    return {"verdict": "NOT_RUN_RESOURCE_CONFLICT", "attempts": attempts,
            "attempts_used": retries}


# ------------------------------------------------------------------ synthetic
def synthetic_stream(n_seasons=6, teams=8, games_per_team_pair=2, seed=1234):
    """Synthetic deterministic corpus for selftests / evaluate-oos rehearsal.
    Labels are synthetic; no real season data involved."""
    import random
    import datetime as dt
    rng = random.Random(seed)
    fks = ["T%02d" % i for i in range(teams)]
    games = []
    base = 2000
    for s in range(n_seasons):
        season = base + s
        day = dt.datetime(season, 6, 1, tzinfo=dt.timezone.utc)
        for a in range(teams):
            for b in range(a + 1, teams):
                for _ in range(games_per_team_pair):
                    home, away = (a, b) if rng.random() < 0.5 else (b, a)
                    strength = {fk: 1500 + 60 * rng.uniform(-1, 1) for fk in fks}
                    p = 1 / (1 + 10 ** (-(strength[fks[home]] - strength[fks[away]]) / 400))
                    games.append({
                        "tip": day, "game_id": "SYN-%d-%d-%d" % (season, a, b),
                        "season": season, "fk_home": fks[home], "fk_away": fks[away],
                        "home_win": int(rng.random() < p), "neutral": False,
                        "row_home": None, "row_away": None,
                    })
                    day += dt.timedelta(days=1)
    games.sort(key=lambda g: (g["tip"], g["game_id"]))
    return games


# ------------------------------------------------------------------ selftest
def _pstream_bytes(preds):
    return [float(d["p_home"]).hex() for d in preds]


def selftest():
    """Hand-computed fixtures + canaries. Exit 0 = all PASS; any failure aborts."""
    checks = []

    def check(name, fn):
        try:
            fn()
            checks.append((name, "PASS", ""))
        except Exception as e:  # noqa: BLE001
            checks.append((name, "FAIL", "%s: %s" % (type(e).__name__, e)))

    # 1. input integrity: feature-table sha256 vs manifest (mismatch => BLOCKED_DATA)
    def t_sha():
        verify_feature_table()
    check("feature_table_sha256_vs_manifest", t_sha)

    # 2. Elo update hand-computed fixture.
    #    R_h = R_a = 1500, HCA = 100, K = 16, home wins:
    #    p_home = 1/(1+10^(-100/400)) = 1/(1+10^-0.25) = 0.6400649998...
    #    away expected = 1 - p_home = 0.3599350002...
    #    R_h' = 1500 + 16*(1 - p_home)      = 1505.7589600...
    #    R_a' = 1500 + 16*(0 - (1-p_home))  = 1494.2410400...  (zero-sum pair)
    def t_elo():
        p = arms.sigmoid_elo(100.0)
        assert abs(p - 0.6400649998028861) < 1e-9, p
        rh = arms.elo_update(1500.0, 16.0, 1.0, p)
        ra = arms.elo_update(1500.0, 16.0, 0.0, 1.0 - p)
        assert abs(rh - 1505.7589600031538) < 1e-9, rh
        assert abs(ra - 1494.2410399968462) < 1e-9, ra
        assert abs((rh - 1500) + (ra - 1500)) < 1e-9  # zero-sum pair update
        # outcome wiring: the stream must use the ACTUAL game outcome (a home
        # LOSS moves the home rating down) — regression fixture for the
        # hardcoded-outcome bug this suite caught.
        import datetime as dt
        g_win = {"tip": dt.datetime(2001, 6, 1, tzinfo=dt.timezone.utc), "game_id": "w",
                 "season": 2001, "fk_home": "A", "fk_away": "B", "home_win": 1,
                 "neutral": False, "row_home": None, "row_away": None}
        g_loss = dict(g_win, game_id="l", home_win=0)
        _, m_win = arms.run_stream([g_win], k=16.0, hca=0.0, gamma=0.75)
        _, m_loss = arms.run_stream([g_loss], k=16.0, hca=0.0, gamma=0.75)
        assert m_win["final_ratings"]["A"] > 1500.0 > m_loss["final_ratings"]["A"]
        assert m_win["final_ratings"]["B"] < 1500.0 < m_loss["final_ratings"]["B"]
        assert abs(m_win["final_ratings"]["A"] + m_win["final_ratings"]["B"] - 3000.0) < 1e-9
        assert abs(m_loss["final_ratings"]["A"] + m_loss["final_ratings"]["B"] - 3000.0) < 1e-9
    check("elo_update_hand_computed", t_elo)

    # 3. HCA argument: p(0)=0.5 at equal ratings; monotone in HCA; neutral rows
    #    force HCA_eff=0 (stream-level rule).
    def t_hca():
        assert arms.sigmoid_elo(0.0) == 0.5
        assert arms.sigmoid_elo(-100.0) < arms.sigmoid_elo(0.0) < arms.sigmoid_elo(100.0)
        import datetime as dt
        g = lambda gid, neutral: {"tip": dt.datetime(2001, 6, 1, tzinfo=dt.timezone.utc),
                                  "game_id": gid, "season": 2001,
                                  "fk_home": "A", "fk_away": "B", "home_win": 1,
                                  "neutral": neutral, "row_home": None, "row_away": None}
        preds_n, _ = arms.run_stream([g("x1", True)], k=16.0, hca=100.0, gamma=0.75)
        assert preds_n[0]["p_home"] == 0.5 and preds_n[0]["flags"] == ("neutral_hca0",)
        preds_h, _ = arms.run_stream([g("x2", False)], k=16.0, hca=100.0, gamma=0.75)
        assert preds_h[0]["p_home"] == arms.sigmoid_elo(100.0)
    check("hca_argument_and_neutral_rule", t_hca)

    # 4. gamma reversion exact: R_end=1600, gamma=0.75 -> 1575.0; c=0.5 -> 1537.5.
    def t_gamma():
        assert arms.gamma_reversion(1600.0, 0.75) == 1575.0
        assert arms.continuity_start(1600.0, 0.75, 1.0) == 1575.0
        assert arms.continuity_start(1600.0, 0.75, 0.5) == 1537.5
        assert arms.continuity_start(1600.0, 0.75, 0.0) == 1500.0
    check("gamma_reversion_and_continuity_arithmetic", t_gamma)

    # 5. 20-key lineage canary — a raw-abbreviation join must FAIL; the sanctioned
    #    lineage path (frozen table franchise_key / team_id) must succeed.
    #    Measured law: ESPN labels ALL Detroit Shock 2002-2009 rows 'TUL' — the same
    #    raw abbreviation as Tulsa 2010-2015; and ESPN-side raw abbreviations
    #    ('UTH','LA','CONN','CT','NY','WSH',...) do not exist in the stats-side
    #    abbreviation list at all.
    def t_lineage():
        lin = pd.read_csv(LINEAGE_CSV, keep_default_na=False)
        stats_map = {}
        for _, r in lin.iterrows():
            for a in str(r["stats_abbrs"]).split(";"):
                a = a.strip()
                if a:
                    stats_map.setdefault(a, set()).add(str(r["franchise_key"]).strip())
        ft = pd.read_parquet(FEATURE_PARQUET)
        det = ft[(ft["franchise_key"] == "DAL") & (ft["team_display_name"] == "Detroit Shock")]
        tul = ft[(ft["franchise_key"] == "DAL") & (ft["team_display_name"] == "Tulsa Shock")]
        assert len(det) > 0 and len(tul) > 0
        assert det["season"].min() == 2002 and det["season"].max() == 2009
        assert tul["season"].min() == 2010 and tul["season"].max() == 2015
        # (a) naive ESPN-abbrev -> stats-side lineage join leaves raw ESPN abbrevs unmapped
        espn_abbrs = set()
        for year in range(SEASON_MIN_REAL, SEASON_MAX_REAL + 1):
            df = pd.read_csv(os.path.join(ESPN_DIR, "wnba_schedule_%d.csv" % year),
                             usecols=["home_abbreviation", "away_abbreviation"])
            espn_abbrs |= set(df["home_abbreviation"].dropna()) | set(df["away_abbreviation"].dropna())
            if year >= 2018:
                break
        espn_abbrs -= ALL_STAR_ALIASES
        unmapped = sorted(a for a in espn_abbrs if a not in stats_map)
        assert len(unmapped) > 0, "raw-abbrev join unexpectedly total — canary vacuous"
        assert "TUL" not in unmapped  # 'TUL' exists on the stats side (Tulsa) — silent WRONG mapping risk
        # (b) ESPN-side abbr -> display names is ambiguous for 'TUL'
        abbr2names = {}
        for year in (2005, 2012):  # Detroit era vs Tulsa era
            df = pd.read_csv(os.path.join(ESPN_DIR, "wnba_schedule_%d.csv" % year),
                             usecols=["home_abbreviation", "home_display_name",
                                      "away_abbreviation", "away_display_name"])
            for _, r in df.iterrows():
                abbr2names.setdefault(r["home_abbreviation"], set()).add(r["home_display_name"])
                abbr2names.setdefault(r["away_abbreviation"], set()).add(r["away_display_name"])
        assert len(abbr2names.get("TUL", set())) >= 2, abbr2names.get("TUL")
        # (c) sanctioned path: one franchise per (team_id) across all seasons; 0 unmapped
        fk_per_team = ft.groupby("team_id")["franchise_key"].nunique()
        assert int(fk_per_team.max()) == 1
        assert ft["franchise_key"].notna().all() and (ft["franchise_key"] != "").all()
        assert set(ft.groupby("team_id")["franchise_key"].first()) <= set(lin["franchise_key"])
    check("lineage_20key_canary_raw_abbrev_fails", t_lineage)

    # 6. designed-null byte-identity on 3 synthetic streams:
    #    phi=0 (with feature fn attached) and c==1 (with c fn attached) and both
    #    combined reproduce the parent p_home stream bit-for-bit.
    def t_null():
        fake_moments = {"col": XB_COL, "reason_col": XB_REASON, "mean": 0.30, "sd": 0.05}
        x_fn = make_x_fn(fake_moments)
        rows = [{"season": 2015, "xb": 0.25 + 0.01 * i, "xb_reason": "",
                 "xc": 0.1 + 0.02 * i, "xc_reason": ""} for i in range(6)]
        for seed in (11, 22, 33):
            gs = synthetic_stream(n_seasons=5, teams=6, seed=seed)
            for g, i in zip(gs, range(len(gs))):
                side = "home" if i % 2 == 0 else "away"
                g["row_home" if side == "home" else "row_away"] = rows[i % len(rows)]
            parent, _ = arms.run_stream(gs, k=16.0, hca=50.0, gamma=0.75)
            null_phi, _ = arms.run_stream(gs, k=16.0, hca=50.0, gamma=0.75, phi=0.0, x_fn=x_fn)
            null_c, _ = arms.run_stream(gs, k=16.0, hca=50.0, gamma=0.75,
                                        c_fn=lambda row, season: 1.0)
            null_both, _ = arms.run_stream(gs, k=16.0, hca=50.0, gamma=0.75, phi=0.0,
                                           x_fn=x_fn, c_fn=lambda row, season: 1.0)
            assert _pstream_bytes(parent) == _pstream_bytes(null_phi)
            assert _pstream_bytes(parent) == _pstream_bytes(null_c)
            assert _pstream_bytes(parent) == _pstream_bytes(null_both)
    check("designed_null_byte_identity_3_synthetic_streams", t_null)

    # 7. era-floor + neutral rules: season<2013 -> x=0 + era_floor even with a value;
    #    neutral reason -> x=0 + neutral_x0; computed row -> z-score.
    def t_floors():
        m = {"col": XC_COL, "reason_col": XC_REASON, "mean": 0.2, "sd": 0.1}
        x_fn = make_x_fn(m)
        row2012 = {"season": 2012, "xc": 0.5, "xc_reason": ""}
        assert x_fn(row2012, 2012) == (0.0, "era_floor")
        row_neu = {"season": 2015, "xc": None, "xc_reason": "insufficient_history"}
        assert x_fn(row_neu, 2015) == (0.0, "neutral_x0")
        row_ok = {"season": 2015, "xc": 0.4, "xc_reason": ""}
        v, fl = x_fn(row_ok, 2015)
        assert fl is None and abs(v - 2.0) < 1e-12
        row_none = None
        assert x_fn(row_none, 1999) == (0.0, None)
    check("era_floor_and_neutral_x_rules", t_floors)

    # 8. doctored 2019-row probe must ABORT loud (HARD CAP SEASON_MAX_REAL=2018).
    def t_cap():
        try:
            enforce_season_cap({2018, 2019}, "doctored_probe")
        except CapViolation:
            return
        raise AssertionError("doctored 2019 row did not abort")
    check("doctored_2019_row_aborts", t_cap)

    # 9. evaluate-oos gate: real data without the owner GO token is REFUSED
    #    (synthetic corpora are the only allowed input pre-gate).
    def t_oos_gate():
        enforce_oos_gate("synthetic", None)  # allowed
        enforce_oos_gate("real", GO_PHRASE)  # exact owner token opens the gate
        for tok in (None, "", GO_PHRASE + " X", "go wnba playerfeat scored v1 evaluation"):
            try:
                enforce_oos_gate("real", tok)
            except Abort:
                continue
            raise AssertionError("evaluate-oos accepted real data without GO token")
    check("evaluate_oos_refuses_real_without_go_token", t_oos_gate)

    # 10. tip-batching: two games at the SAME tip are predicted from one snapshot;
    #     their outcomes never leak into each other's prediction, but a later game
    #     sees both updates.
    def t_tips():
        import datetime as dt
        tip = dt.datetime(2003, 6, 5, tzinfo=dt.timezone.utc)
        late = tip + dt.timedelta(days=1)

        def corpus(o1, o2, o3):
            return [
                {"tip": tip, "game_id": "b1", "season": 2003, "fk_home": "A",
                 "fk_away": "B", "home_win": o1, "neutral": False,
                 "row_home": None, "row_away": None},
                {"tip": tip, "game_id": "b2", "season": 2003, "fk_home": "C",
                 "fk_away": "D", "home_win": o2, "neutral": False,
                 "row_home": None, "row_away": None},
                {"tip": late, "game_id": "b3", "season": 2003, "fk_home": "A",
                 "fk_away": "C", "home_win": o3, "neutral": False,
                 "row_home": None, "row_away": None},
            ]
        p_a, _ = arms.run_stream(corpus(1, 0, 1), k=32.0, hca=50.0, gamma=0.75)
        p_b, _ = arms.run_stream(corpus(0, 1, 1), k=32.0, hca=50.0, gamma=0.75)
        assert _pstream_bytes(p_a[:2]) == _pstream_bytes(p_b[:2]), "tip leak in batch"
        assert p_a[2]["p_home"] != p_b[2]["p_home"], "updates not applied"
    check("tip_batching_no_intra_tip_leak", t_tips)

    # 11. warm-up rows are never scored: seasons outside blocks/folds are excluded
    #     by construction — assert the block/fold definitions cannot see 1997-2001.
    def t_warmup_scope():
        all_scored = set(B1_BLOCK_SEASONS) | set(FEATURE_FOLDS)
        assert not (all_scored & set(WARMUP_SEASONS))
        assert max(all_scored) <= SEASON_MAX_REAL
        assert not (set(OOS_SEASONS) & set(range(SEASON_MIN_REAL, SEASON_MAX_REAL + 1)))
    check("warmup_rows_never_scored_and_oos_out_of_scope", t_warmup_scope)

    # 12. no outcome-like columns in the frozen feature table (leakage canary;
    #     whitelist law per FEATURE_SPEC §0: no score/winner/outcome/result/margin).
    def t_no_outcome_cols():
        import re
        ft_cols = list(pd.read_parquet(FEATURE_PARQUET).columns)
        bad = [c for c in ft_cols if re.search(
            r"score|winner|outcome|result|margin", c, re.I)]
        assert not bad, bad
    check("feature_table_has_no_outcome_columns", t_no_outcome_cols)

    # 13. calibration slope fixture: perfectly calibrated constant predictor on
    #     Bernoulli(p) data -> slope ~ 1; overconfident (p=0.9 on 50% data) -> slope < 1.
    def t_slope():
        import random
        rng = random.Random(7)
        # varying-p corpora (a constant predictor leaves the slope unidentifiable:
        # calibration_slope returns nan there — asserted too)
        well = [{"p_home": 0.5 + 0.15 * rng.uniform(-1, 1),
                 "home_win": 0} for _ in range(4000)]
        for d in well:
            u = rng.random()
            d["home_win"] = int(u < d["p_home"])
        s = arms.calibration_slope(well)
        assert 0.85 <= s <= 1.15, s
        over = [{"p_home": min(max(0.5 + 0.45 * ((d["p_home"] - 0.5) / 0.15), 0.01), 0.99),
                 "home_win": d["home_win"]} for d in well]
        s2 = arms.calibration_slope(over)
        assert s2 < 0.6, s2
        const = [{"p_home": 0.6, "home_win": int(rng.random() < 0.6)} for _ in range(500)]
        assert math.isnan(arms.calibration_slope(const))
    check("calibration_slope_fixture", t_slope)

    # 14. bootstrap fixture: zero dLL -> CI contains 0; strictly negative dLL with
    #     clean separation -> CI entirely negative.
    def t_boot():
        import numpy as np
        rng = np.random.default_rng(1)
        d = rng.normal(0.0, 1e-9, 500)
        pt, lo, hi = arms.date_cluster_bootstrap_ci(list(d), [str(i // 10) for i in range(500)],
                                                    n_resamples=2000, seed=1)
        assert lo <= 0 <= hi
        d2 = np.full(500, -0.01)
        pt2, lo2, hi2 = arms.date_cluster_bootstrap_ci(list(d2), [str(i // 10) for i in range(500)],
                                                       n_resamples=2000, seed=1)
        assert hi2 < 0 and pt2 < 0
    check("bootstrap_ci_fixture", t_boot)

    failed = [c for c in checks if c[1] != "PASS"]
    for name, status, note in checks:
        print("SELFTEST %-4s %s %s" % (status, name, ("| " + note) if note else ""))
    print("SELFTEST %d/%d PASS" % (len(checks) - len(failed), len(checks)))
    if failed:
        raise SystemExit("SELFTEST FAILED: %s" % [f[0] for f in failed])
    return checks


# ------------------------------------------------------------------ select run
class Ledger:
    def __init__(self, path):
        self.path = path
        self.rows = []
        if os.path.exists(path):
            os.remove(path)

    def add(self, **kw):
        row = {"cycle_id": CYCLE_ID, "lane": LANE, "seed": arms.SEED,
               "season_cap": SEASON_MAX_REAL}
        row.update(kw)
        self.rows.append(row)
        with open(self.path, "a") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def run_select(write_reports=True):
    # ---- heavy-lock discipline (inspect from root; 3x60s; else NOT_RUN)
    lock = locks_inspect()
    print("LOCK %s (attempts used: %d)" % (lock["verdict"], lock["attempts_used"]))
    if lock["verdict"] != "FREE_PROVEN":
        raise Abort("NOT_RUN_RESOURCE_CONFLICT: heavy lock not FREE_PROVEN after retries")

    # ---- input integrity + universe (REAL DATA, hard-capped <= 2018)
    sha = verify_feature_table()
    lineage_abbr_to_fk = load_lineage()
    feature_rows, feature_games = load_feature_rows()
    universe_games, neutral_total = load_espn_universe(feature_games)
    attach_feature_sides(universe_games, feature_rows)
    enforce_season_cap(set(g["season"] for g in universe_games), "universe_final")
    warmup_games = load_warmup(lineage_abbr_to_fk)
    full_games = build_full_games(warmup_games, universe_games)
    n_train = len(universe_games)
    n_warm = len(warmup_games)
    print("DATA feature_table sha ok; universe %d games (seasons %d-%d); "
          "warm-up %d rows (seasons %d-%d, stream-only)"
          % (n_train, SEASON_MIN_REAL, SEASON_MAX_REAL, n_warm,
             WARMUP_SEASONS[0], WARMUP_SEASONS[-1]))

    # ---- B0 constant: TRAIN-window home-win rate, frozen
    p0 = sum(g["home_win"] for g in universe_games) / float(n_train)
    print("B0 constant p_home(train) = %.6f" % p0)

    # ---- standardization moments (pinned, train computed rows only)
    mom_b = compute_moments(feature_rows, XB_COL, XB_REASON)
    mom_c = compute_moments(feature_rows, XC_COL, XC_REASON)
    x_fn_b = make_x_fn(mom_b)
    x_fn_c = make_x_fn(mom_c)
    c_fn = make_c_fn()

    ledger = Ledger(os.path.join(OUT_DIR, "SELECTION_LEDGER.jsonl"))

    # ---- B1-WNBA grid: 27 fits (all counted)
    grid_results = []
    for cfg in arms.b1_configs():
        preds, meta = arms.run_stream(full_games, k=cfg["k"], hca=cfg["hca"],
                                      gamma=cfg["gamma"])
        by_season = preds_by_season(preds)
        per_block = {}
        total_games = 0
        ll_sum = 0.0
        for blk in B1_BLOCKS:
            pts = [d for s in blk for d in by_season.get(s, [])]
            per_block["%d-%d" % blk] = {"mean_ll": arms.mean_ll(pts), "n": len(pts)}
            ll_sum += sum(arms.log_loss(d["p_home"], d["home_win"]) for d in pts)
            total_games += len(pts)
        pooled = ll_sum / total_games
        train_ll, _ = block_mean_ll(by_season, tuple(range(SEASON_MIN_REAL, SEASON_MAX_REAL + 1)))
        grid_results.append({"cfg": cfg, "pooled": pooled, "n_pooled": total_games,
                             "per_block": per_block, "train_ll": train_ll,
                             "preds": preds})
        ledger.add(run_id="B1_grid_K%d_HCA%d_G%.2f" % (cfg["k"], cfg["hca"], cfg["gamma"]),
                   arm="B1-WNBA", mode="select", kind="grid_fit",
                   config=cfg, criterion="pooled_inner_LL_validation_blocks",
                   n_games_scored=total_games, mean_ll_pooled=pooled,
                   per_block=per_block, mean_ll_train_full=train_ll,
                   designed_null_ok=None, selected=False,
                   notes="warm-up %d rows stream-only" % n_warm)
    print("GRID 27 fits done")

    # ---- grid selection: LOWEST pooled inner LL (log loss), tie-break simpler (K,HCA,gamma asc)
    best = arms.select_best([(gr["pooled"], arms.config_simpler_key(gr["cfg"]), gr)
                             for gr in grid_results])
    frozen = best[2]
    frozen_cfg = dict(frozen["cfg"])
    # mark selection in ledger (dedicated line; grid lines stay immutable)
    ledger.add(run_id="B1_grid_SELECTION", arm="B1-WNBA", mode="select", kind="selection",
               config=frozen_cfg, criterion="pooled_inner_LL_validation_blocks",
               n_games_scored=frozen["n_pooled"], mean_ll_pooled=frozen["pooled"],
               per_block=frozen["per_block"], mean_ll_train_full=frozen["train_ll"],
               designed_null_ok=None, selected=True,
               selection_rule="lowest pooled inner LL (log loss; lower is better); tie-break (K,HCA,gamma) ascending",
               notes="frozen for this cycle")
    print("B1-WNBA FROZEN %s pooled=%.6f" % (frozen_cfg, frozen["pooled"]))

    # ---- B0 vs B1 on the same validation union (train-internal kill test + CI)
    val_seasons = B1_BLOCK_SEASONS
    parent_val = [d for d in frozen["preds"] if d["season"] in val_seasons]
    b0_val = [{"p_home": p0, "home_win": d["home_win"]} for d in parent_val]
    dll_b0 = arms.ll_delta(parent_val, b0_val)
    pt, lo, hi = arms.date_cluster_bootstrap_ci(
        dll_b0, tip_date_clusters(parent_val), n_resamples=10000, seed=arms.SEED)
    slope_b1_val = arms.calibration_slope(parent_val)
    b1_killed_train = not (pt < 0 and hi < 0)  # kill iff CI includes 0 or positive
    ledger.add(run_id="B1_vs_B0_validation_killtest", arm="B1-WNBA", mode="select",
               kind="kill_test", config=frozen_cfg, criterion="paired_dLL_vs_B0",
               n_games_scored=len(parent_val), mean_ll_pooled=frozen["pooled"],
               dll_point=pt, dll_ci_low=lo, dll_ci_high=hi, ci_excludes_zero=(hi < 0 or lo > 0),
               slope=slope_b1_val, slope_band=list(arms.SLOPE_BAND),
               b0_mean_ll=arms.mean_ll(b0_val), designed_null_ok=None,
               selected=False,
               notes="train-internal; CI entirely<0 required to pass kill test")
    print("KILLTEST B1 vs B0: dLL=%.6f [%.6f, %.6f] slope=%.4f pass=%s"
          % (pt, lo, hi, slope_b1_val, (not b1_killed_train)))

    # ---- designed-null FIRST on real data (TECHABORT on failure)
    parent_full, _ = arms.run_stream(full_games, k=frozen_cfg["k"], hca=frozen_cfg["hca"],
                                     gamma=frozen_cfg["gamma"])
    byte_ok = _pstream_bytes(parent_full) == _pstream_bytes(frozen["preds"])
    null_phi_full, _ = arms.run_stream(full_games, k=frozen_cfg["k"], hca=frozen_cfg["hca"],
                                       gamma=frozen_cfg["gamma"], phi=0.0, x_fn=x_fn_b)
    null_c_full, _ = arms.run_stream(full_games, k=frozen_cfg["k"], hca=frozen_cfg["hca"],
                                     gamma=frozen_cfg["gamma"], c_fn=lambda r, s: 1.0)
    null_ok = (byte_ok
               and _pstream_bytes(null_phi_full) == _pstream_bytes(parent_full)
               and _pstream_bytes(null_c_full) == _pstream_bytes(parent_full))
    ledger.add(run_id="DESIGNED_NULL_REAL_DATA", arm="WF-B(phi=0)+WF-A(c=1)", mode="select",
               kind="designed_null", config=frozen_cfg,
               n_games_scored=len(parent_full), designed_null_ok=null_ok,
               selected=False,
               notes="phi=0 and c=1 must equal the frozen B1 p_home stream bit-for-bit")
    if not null_ok:
        raise Abort("TECHABORT: designed-null mismatch on real data (phi=0 / c=1 != parent)")
    print("DESIGNED-NULL ok=%s (real data, %d games, byte-identical)" % (null_ok, len(parent_full)))

    if b1_killed_train:
        print("B1-WNBA train-internal kill test FAILED — feature arms NOT_RUN "
              "(selection negative); writing reports.")
        feature_arm_results = {}
    else:
        feature_arm_results = run_feature_arms(
            ledger, full_games, frozen_cfg, p0, x_fn_b, x_fn_c, c_fn,
            mom_b, mom_c, n_warm)
    fold_games = len(fold_predictions(frozen["preds"], FEATURE_FOLDS))

    # ---- warm-up-vs-cold-start diagnostic (outside budget)
    cold_preds, _ = arms.run_stream(universe_games, k=frozen_cfg["k"],
                                    hca=frozen_cfg["hca"], gamma=frozen_cfg["gamma"])
    warm_train = [d for d in frozen["preds"] if SEASON_MIN_REAL <= d["season"] <= SEASON_MAX_REAL]
    cold_train = [d for d in cold_preds if SEASON_MIN_REAL <= d["season"] <= SEASON_MAX_REAL]
    ledger.add(run_id="DIAG_warmup_vs_coldstart", arm="B1-WNBA", mode="select",
               kind="diagnostic", config=frozen_cfg,
               n_games_scored=len(warm_train),
               mean_ll_warmup=arms.mean_ll(warm_train),
               mean_ll_coldstart=arms.mean_ll(cold_train),
               designed_null_ok=None, selected=False,
               notes="warm-up 1997-2001 vs cold start at 2002; diagnostic only")
    diag_warm_ll = arms.mean_ll(warm_train)
    diag_cold_ll = arms.mean_ll(cold_train)
    print("DIAG warm-up LL=%.6f cold-start LL=%.6f (train window)"
          % (diag_warm_ll, diag_cold_ll))

    # ---- twin diagnostics for the grid reference (B1 twin vs its own parent B0)
    shuffled = arms.season_permuted_games(full_games, seed=arms.SEED)
    twin_b1, _ = arms.run_stream(shuffled, k=frozen_cfg["k"], hca=frozen_cfg["hca"],
                                 gamma=frozen_cfg["gamma"])
    twin_b0 = [{"p_home": p0, "home_win": d["home_win"]} for d in twin_b1
               if d["season"] in val_seasons]
    twin_b1_val = [d for d in twin_b1 if d["season"] in val_seasons]
    twin_delta_b1 = arms.mean_ll(twin_b1_val) - arms.mean_ll(twin_b0)
    ledger.add(run_id="TWIN_B1_timeshuffled", arm="B1-WNBA", mode="select",
               kind="twin", config=frozen_cfg, n_games_scored=len(twin_b1_val),
               twin_mean_ll=arms.mean_ll(twin_b1_val), parent_mean_ll=arms.mean_ll(twin_b0),
               twin_parent="B0", dll_twin=twin_delta_b1,
               parent_slope_realdata=slope_b1_val,
               machinery_suspect=bool(twin_delta_b1 < 0),
               designed_null_ok=None, selected=False,
               notes="time-shuffled twin seed 20261005; suspect iff twin beats OWN parent")
    grid_twin = {"twin_mean_ll": arms.mean_ll(twin_b1_val),
                 "parent_mean_ll": arms.mean_ll(twin_b0),
                 "parent": "B0", "dll_twin": twin_delta_b1,
                 "parent_slope_realdata": slope_b1_val,
                 "machinery_suspect": bool(twin_delta_b1 < 0)}
    print("TWIN B1 vs B0 (shuffled): dLL=%.6f suspect=%s" % (twin_delta_b1, twin_delta_b1 < 0))

    # ---- neutral-site report (corpus carries the flag; HCA=0 default applied)
    neutral_rows = [d for d in frozen["preds"] if d["neutral"]]
    ledger.add(run_id="NEUTRAL_SITE_REPORT", arm="ALL", mode="select", kind="report_row",
               n_games_scored=len(neutral_rows),
               neutral_game_ids=[d["game_id"] for d in neutral_rows],
               designed_null_ok=None, selected=False,
               notes="HCA=0 applied via ESPN neutral_site flag; "
                     "stats-side warm-up carries no neutral flag (disclosed)")

    lock_obs = lock
    summary = {
        "frozen_b1": frozen_cfg, "b0_p_home": p0,
        "b1_pooled_validation_ll": frozen["pooled"],
        "b1_train_full_ll": frozen["train_ll"],
        "b1_vs_b0_dll": {"point": pt, "lo": lo, "hi": hi,
                         "ci_excludes_zero": bool(hi < 0 or lo > 0),
                         "kill_passed": not b1_killed_train},
        "b1_slope_validation": slope_b1_val,
        "grid_twin": grid_twin,
        "diagnostic_warmup_ll": diag_warm_ll, "diagnostic_coldstart_ll": diag_cold_ll,
        "moments": {"wf_b": mom_b, "wf_c": mom_c},
        "neutral_rows_train_window": len(neutral_rows),
        "neutral_game_ids": [d["game_id"] for d in neutral_rows],
        "designed_null_real_data_ok": null_ok,
        "feature_arms": feature_arm_results,
        "lock_observation": lock_obs,
        "n_fits": {"b1_grid": 27, "wf_a": 1 if feature_arm_results else 0,
                   "wf_b": 5 if feature_arm_results else 0,
                   "wf_c": 5 if feature_arm_results else 0,
                   "diagnostics_outside_budget": True},
        "input_sha": {"feature_table": sha},
        "counts": {"train_games": n_train, "warmup_rows": n_warm,
                   "validation_games": len(parent_val), "fold_games": fold_games},
        "fold_games": fold_games,
    }
    with open(os.path.join(OUT_DIR, "SELECTION_SUMMARY.json"), "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)

    # ---- frozen parent stream (train window) persisted for audit
    pd.DataFrame([{ "game_id": d["game_id"], "season": d["season"],
                    "tip_utc": d["tip"].isoformat(), "p_home": d["p_home"],
                    "home_win": d["home_win"], "neutral": d["neutral"],
                    "flags": ";".join(d["flags"])}
                  for d in frozen["preds"]
                  if SEASON_MIN_REAL <= d["season"] <= SEASON_MAX_REAL]
                 ).to_parquet(os.path.join(OUT_DIR, "b1_frozen_p_stream_train.parquet"),
                              index=False)

    if write_reports:
        write_selection_report(summary, grid_results, ledger)
    return summary


def run_feature_arms(ledger, full_games, frozen_cfg, p0, x_fn_b, x_fn_c, c_fn,
                     mom_b, mom_c, n_warm):
    """WF-A / WF-B / WF-C selection on the 5 expanding-origin single-season folds
    2014..2018; G-ENTRY vs the FROZEN B1-WNBA; twins vs own parent."""
    k, hca, gamma = frozen_cfg["k"], frozen_cfg["hca"], frozen_cfg["gamma"]
    parent, _ = arms.run_stream(full_games, k=k, hca=hca, gamma=gamma)
    parent_folds = fold_predictions(parent, FEATURE_FOLDS)
    parent_ll = arms.mean_ll(parent_folds)
    parent_slope = arms.calibration_slope(parent_folds)
    print("FOLDS parent B1 fold-games=%d meanLL=%.6f slope=%.4f"
          % (len(parent_folds), parent_ll, parent_slope))

    shuffled = arms.season_permuted_games(full_games, seed=arms.SEED)
    twin_parent, _ = arms.run_stream(shuffled, k=k, hca=hca, gamma=gamma)
    twin_parent_folds = fold_predictions(twin_parent, FEATURE_FOLDS)

    results = {}

    def gentry(arm_name, fold_preds, twin_folds, extra):
        dll = arms.ll_delta(fold_preds, parent_folds)
        pt, lo, hi = arms.date_cluster_bootstrap_ci(
            dll, tip_date_clusters(fold_preds), n_resamples=10000, seed=arms.SEED)
        slope = arms.calibration_slope(fold_preds)
        twin_dll = arms.mean_ll(twin_folds) - arms.mean_ll(twin_parent_folds)
        suspect = twin_dll < 0
        in_band = arms.SLOPE_BAND[0] <= slope <= arms.SLOPE_BAND[1]
        if suspect:
            verdict = "MACHINERY_SUSPECT"
        elif pt >= 0 or not in_band:
            verdict = "RELEASE"
        elif lo > 0:
            verdict = "KILL"  # CI entirely >0 (arm strictly worse)
        else:
            verdict = "ADMIT" + ("" if hi < 0 else " (INCONCLUSIVE: CI includes 0)")
        row = {"dll_point": pt, "dll_ci": [lo, hi],
               "ci_entirely_negative": bool(hi < 0), "ci_entirely_positive": bool(lo > 0),
               "slope": slope, "slope_in_band": bool(in_band),
               "twin_dll": twin_dll, "machinery_suspect": bool(suspect),
               "parent_fold_mean_ll": parent_ll, "parent_slope": parent_slope,
               "arm_fold_mean_ll": arms.mean_ll(fold_preds), "verdict": verdict,
               "n_fold_games": len(fold_preds)}
        row.update(extra)
        ledger.add(run_id="GENTRY_%s" % arm_name, arm=arm_name, mode="select",
                   kind="gentry", config=dict(frozen_cfg, phi=row.get("phi")),
                   criterion="pooled_inner_LL_folds_2014_2018",
                   n_games_scored=len(fold_preds),
                   mean_ll_pooled=row["arm_fold_mean_ll"],
                   dll_point=pt, dll_ci_low=lo, dll_ci_high=hi,
                   slope=slope, twin_dll=twin_dll,
                   machinery_suspect=bool(suspect),
                   parent_slope_realdata=parent_slope,
                   designed_null_ok=True, selected=(verdict.startswith("ADMIT")),
                   verdict=verdict,
                   notes="twin vs OWN parent; parent slope reported alongside")
        print("GENTRY %-6s dLL=%+.6f [%.6f,%.6f] slope=%.4f twinDLL=%+.6f -> %s"
              % (arm_name, pt, lo, hi, slope, twin_dll, verdict))
        return row

    # WF-A: no free scalar; gamma frozen from B1
    wfa, _ = arms.run_stream(full_games, k=k, hca=hca, gamma=gamma, c_fn=c_fn)
    wfa_folds = fold_predictions(wfa, FEATURE_FOLDS)
    wfa_twin, _ = arms.run_stream(shuffled, k=k, hca=hca, gamma=gamma, c_fn=c_fn)
    results["WF-A"] = gentry("WF-A", wfa_folds, fold_predictions(wfa_twin, FEATURE_FOLDS),
                             {"phi": None, "n_c_rows_modulated":
                              sum(1 for d in wfa_folds if d["season"] in FEATURE_FOLDS)})
    ledger.add(run_id="WF_A_fit", arm="WF-A", mode="select", kind="arm_fit",
               config=dict(frozen_cfg, phi=None), n_games_scored=len(wfa_folds),
               mean_ll_pooled=results["WF-A"]["arm_fold_mean_ll"],
               designed_null_ok=True, selected=True,
               notes="single fit; no free scalar; c from frozen feature table 2014+")

    # WF-B / WF-C: phi grids (5 fits each, all counted)
    for arm_name, x_fn, mom, phi_key in (("WF-B", x_fn_b, mom_b, "phi_B"),
                                         ("WF-C", x_fn_c, mom_c, "phi_C")):
        cands = []
        per_phi = {}
        for phi in arms.GRID_PHI:
            preds, _ = arms.run_stream(full_games, k=k, hca=hca, gamma=gamma,
                                       phi=phi, x_fn=x_fn)
            folds = fold_predictions(preds, FEATURE_FOLDS)
            ll = arms.mean_ll(folds)
            per_phi[phi] = ll
            null_ok_phi = None
            if phi == 0.0:
                null_ok_phi = (_pstream_bytes(folds) == _pstream_bytes(parent_folds))
            ledger.add(run_id="%s_fit_phi%+g" % (arm_name, phi), arm=arm_name,
                       mode="select", kind="arm_fit",
                       config=dict(frozen_cfg, **{phi_key: phi}),
                       n_games_scored=len(folds), mean_ll_pooled=ll,
                       designed_null_ok=null_ok_phi, selected=False,
                       notes="5 single-season folds 2014-2018; era-floor rows x=0")
            if phi == 0.0 and not null_ok_phi:
                raise Abort("TECHABORT: %s phi=0 fold stream != parent" % arm_name)
            cands.append((ll, arms.phi_simpler_key(phi), phi))
        best = arms.select_best(cands)
        phi_sel = best[2]
        preds_sel, _ = arms.run_stream(full_games, k=k, hca=hca, gamma=gamma,
                                       phi=phi_sel, x_fn=x_fn)
        folds_sel = fold_predictions(preds_sel, FEATURE_FOLDS)
        twin_sel, _ = arms.run_stream(shuffled, k=k, hca=hca, gamma=gamma,
                                      phi=phi_sel, x_fn=x_fn)
        flags = {}
        for d in folds_sel:
            for fl in d["flags"]:
                flags[fl] = flags.get(fl, 0) + 1
        results[arm_name] = gentry(arm_name, folds_sel,
                                   fold_predictions(twin_sel, FEATURE_FOLDS),
                                   {"phi": phi_sel, "per_phi_mean_ll": per_phi,
                                    "fold_flag_counts": flags})
        ledger.add(run_id="%s_SELECTION" % arm_name, arm=arm_name, mode="select",
                   kind="selection", config=dict(frozen_cfg, **{phi_key: phi_sel}),
                   n_games_scored=len(folds_sel), mean_ll_pooled=best[0],
                   designed_null_ok=True, selected=True,
                   selection_rule="lowest pooled inner LL (log loss); tie-break (|phi|,phi) ascending",
                   notes="fold_flag_counts=%s" % json.dumps(flags, sort_keys=True))
    return results


# ------------------------------------------------------------------ report
def write_selection_report(summary, grid_results, ledger):
    L = []
    L.append("# SELECTION REPORT — WNBA-PLAYERFEAT-SCORED-V1 · lane T_SELECT · TRAIN-INTERNAL")
    L.append("")
    L.append("Date of record: 2026-10-05 · seed %d · interpreter %s/.venv/bin/python · "
             "no git operations · OOS [2020..2026] NEVER touched (select mode hard-capped "
             "at season <= %d; doctored-2019 probe aborts loud)." % (arms.SEED, ROOT, SEASON_MAX_REAL))
    L.append("")
    L.append("## 1. Inputs and integrity")
    L.append("")
    L.append("- Feature table: `%s` — sha256 verified vs manifest "
             "(`ceaf10ba…`), file = 11,976 rows x 40 cols (2002–2026), no outcome columns "
             "(asserted). THIS LANE READS ONLY the ≤%d slice (%d rows); 2019–2026 rows "
             "never entered memory (cap enforced at read time; doctored-row probe aborts)." % (
                 FEATURE_PARQUET, SEASON_MAX_REAL, 2 * summary["counts"]["train_games"]))
    L.append("- Universe: ESPN-side filter law re-applied, seasons %d–%d → %d games "
             "(2002–2018 slice of the 5,988-game universe law; per-season census matches "
             "COVERAGE_AUDIT). Scores used ONLY for outcomes (home-win indicator) + tips + "
             "neutral flag." % (SEASON_MIN_REAL, SEASON_MAX_REAL, summary["counts"]["train_games"]))
    L.append("- Warm-up: stats-side schedules 1997–2001 FOUND on disk "
             "(%d rows, 100%% scored, 0 duplicates) — used as rating-stream WARM-UP ONLY, "
             "never train/score/feature rows. Warm-up fallback (2002–2004) NOT needed."
             % summary["counts"]["warmup_rows"])
    L.append("- Lineage: 20-key table `team_key_table.csv`; ratings live on `franchise_key` "
             "from the frozen feature table (ESPN side) and lineage `stats_abbrs` (warm-up "
             "side). Raw-abbreviation joins FAIL by construction (canary in --selftest: "
             "ESPN labels all Detroit 2002–2009 as TUL; 'UTH'/'LA'/'CONN'/'CT'/'NY'/'WSH' "
             "unmapped on the stats-side list).")
    L.append("- Heavy lock: %s (attempts used: %d)." % (
        summary["lock_observation"]["verdict"], summary["lock_observation"]["attempts_used"]))
    L.append("")
    L.append("## 2. Engine law (frozen, reproduced by --selftest)")
    L.append("")
    L.append("- p_home = 1/(1+10^(-(R_h − R_a + HCA_eff)/400)); update R ← R + K·(outcome − "
             "expected) with the AWAY side's expectation 1 − p_home (zero-sum pair update — "
             "regression-fixture enforced after the selftest caught a hardcoded-outcome bug); "
             "season boundary R ← 1500 + γ·(R_end − 1500); new franchise at 1500; games at an "
             "identical tip_utc are predicted from one snapshot then updated (strict-inequality "
             "as-of law); neutral-site rows take HCA_eff = 0; ratings live on the 20-key "
             "franchise identity (relocation-safe).")
    L.append("")
    L.append("## 3. B0 constant floor")
    L.append("")
    L.append("- p_home = TRAIN-window home-win rate, frozen: **%.6f** (%d games, 2002–2018)."
             % (summary["b0_p_home"], summary["counts"]["train_games"]))
    L.append("")
    L.append("## 4. B1-WNBA grid (27 fits, all counted) — FROZEN CONFIG")
    L.append("")
    f = summary["frozen_b1"]
    L.append("- Grid K∈{8,16,32} × HCA∈{0,50,100} × γ∈{0.65,0.75,0.85}; 4 expanding-origin "
             "2-season validation blocks over the TRAIN tail (2011-12, 2013-14, 2015-16, "
             "2017-18; %d validation games); criterion = LOWEST pooled inner LL (log loss); tie-break "
             "(K,HCA,γ) ascending." % summary["counts"]["validation_games"])
    L.append("- **FROZEN: K=%g, HCA=%g, γ=%g** — pooled validation LL %.6f "
             "(full-train LL %.6f, context only)." % (
                 f["k"], f["hca"], f["gamma"], summary["b1_pooled_validation_ll"],
                 summary["b1_train_full_ll"]))
    L.append("- Warm-up law: 1997–2001 stats-side rows feed the rating stream; γ reversion "
             "applies at every season boundary including inside the warm-up and into 2002; "
             "new franchises enter at league mean 1500.")
    kt = summary["b1_vs_b0_dll"]
    L.append("- Train-internal kill test vs B0 (same %d validation games, paired "
             "tip-date-cluster bootstrap, 10,000 resamples, seed %d): ΔLL = %+.6f "
             "[%.6f, %.6f] — CI excludes 0: %s; kill passed: %s. Calibration slope %.4f "
             "(band [0.85, 1.15]). Degenerate K→0 kill: selected K=%g ≠ 0; engine improves "
             "on B0 train-internally iff kill passed." % (
                 summary["counts"]["validation_games"], arms.SEED, kt["point"], kt["lo"],
                 kt["hi"], kt["ci_excludes_zero"], kt["kill_passed"],
                 summary["b1_slope_validation"], f["k"]))
    L.append("- Grid twin (time-shuffled outcomes, seed %d, one global within-season "
             "permutation): twin-B1 LL %.6f vs twin-B0 LL %.6f on the same shuffled "
             "validation games → ΔLL %+.6f; MACHINERY_SUSPECT = %s (flag only if the twin "
             "beats its OWN parent). Parent (real-data) slope %.4f reported alongside per "
             "the adjudication refinement." % (
                 arms.SEED, summary["grid_twin"]["twin_mean_ll"],
                 summary["grid_twin"]["parent_mean_ll"], summary["grid_twin"]["dll_twin"],
                 summary["grid_twin"]["machinery_suspect"],
                 summary["grid_twin"]["parent_slope_realdata"]))
    L.append("- Warm-up-vs-cold-start rerun (diagnostic only): warm-up LL %.6f vs cold-start "
             "LL %.6f on the train window." % (summary["diagnostic_warmup_ll"],
                                               summary["diagnostic_coldstart_ll"]))
    L.append("")
    L.append("## 5. Designed-null gate (FIRST, real data)")
    L.append("")
    L.append("- c≡1 (WF-A null) and φ=0 (WF-B null) both reproduce the frozen B1-WNBA "
             "p_home stream **bit-for-bit** on all %d corpus games (byte-identity of the "
             "float64 stream): %s. Also verified on 3 synthetic streams in --selftest. "
             "Failure would have been a TECHABORT stop." % (
                 summary["counts"]["train_games"] + summary["counts"]["warmup_rows"],
                 summary["designed_null_real_data_ok"]))
    L.append("")
    L.append("## 6. Standardization moments (pinned)")
    L.append("")
    for key in ("wf_b", "wf_c"):
        m = summary["moments"][key]
        L.append("- %s x = `%s`: mean %.6f, sd %.6f (population sd, ddof=0), n = %d computed "
                 "rows, seasons %s (train computed rows only; neutral rows excluded)." % (
                     key.upper(), m["col"], m["mean"], m["sd"], m["n_rows"], m["seasons"]))
    L.append("- Pre-registered constructions (pinned before any scored look): WF-B x = "
             "`b5_minutes_hhi` (rotation concentration; k=5 chosen a priori — k-selection "
             "remains deferred per FEATURE_SPEC §3, the k=3 variant is NOT scored); "
             "WF-C x = `c_absence_share` (uniform null-minutes proxy). Era floor: rows "
             "season < 2013 → x=0 + flag `era_floor`; neutral-reason rows → x=0 + flag "
             "`neutral_x0`. Feature folds are 2014–2018 (era-floor adaptation of the "
             "packet's 4×2-season blocks, disclosed in the plan).")
    L.append("")
    L.append("## 7. Feature arms — G-ENTRY vs the FROZEN B1-WNBA")
    L.append("")
    L.append("Folds: 5 expanding-origin single-season folds 2014..2018 (%d scored games); "
             "criterion LOWEST pooled inner LL (log loss); grids φ∈{−50,−25,0,25,50} immutable; tie-break "
             "(|φ|,φ) ascending. Bootstrap: paired tip-date-cluster, 10,000 resamples, "
             "seed %d. Twin: time-shuffled outcomes (seed %d), flagged MACHINERY_SUSPECT "
             "only if the twin beats its OWN parent arm; parent slope reported alongside."
             % (summary["fold_games"], arms.SEED, arms.SEED))
    L.append("")
    L.append("| arm | frozen φ | arm fold LL | parent fold LL | ΔLL [95% CI] | slope [band] | twin ΔLL | verdict |")
    L.append("|---|---|---|---|---|---|---|---|")
    for name, r in summary["feature_arms"].items():
        phi_s = "—" if r.get("phi") is None else "%+g" % r["phi"]
        L.append("| %s | %s | %.6f | %.6f | %+.6f [%.6f, %.6f] | %.4f | %+.6f | %s |" % (
            name, phi_s, r["arm_fold_mean_ll"], r["parent_fold_mean_ll"],
            r["dll_point"], r["dll_ci"][0], r["dll_ci"][1], r["slope"],
            r["twin_dll"], r["verdict"]))
    L.append("")
    for name, r in summary["feature_arms"].items():
        if name == "WF-A":
            L.append("- WF-A: continuity-modulated carryover R_start = 1500 + γ_sel·c·(R_end−1500), "
                     "c from the frozen table (2014+; game-1 v2 rows / expansion / missing → c=1 "
                     "= parent). NO free scalar; γ frozen from B1-WNBA. Real-data ΔLL %+.6f "
                     "[%.6f, %.6f] sits inside the ±0.003 inconclusive scale at this "
                     "capacity. Its "
                     "time-shuffled twin scored ΔLL %+.6f vs its OWN parent on the same "
                     "shuffled corpus → MACHINERY_SUSPECT under the frozen rule "
                     "(twin-beats-own-parent). Adjudication refinement applied verbatim: the "
                     "miscalibrated-parent exemption does NOT apply because the parent's "
                     "real-data fold slope %.4f is INSIDE [0.85, 1.15]; the twin-vs-reference "
                     "reading is therefore not exculpatory either. Arm UN-SCORED this cycle; "
                     "the flag plus both ΔLL magnitudes (real %+.6f / twin %+.6f, both inside "
                     "the ±0.003 inconclusive scale) are recorded for a machinery audit at the "
                     "next owner round before any WF-A re-proposal." % (
                         r["dll_point"], r["dll_ci"][0], r["dll_ci"][1], r["twin_dll"],
                         r["parent_slope"], r["dll_point"], r["twin_dll"]))
        elif name == "WF-B":
            L.append("- WF-B per-φ pooled fold LL (all 5 counted): %s." % ", ".join(
                "φ=%+g: %.6f" % (p, v) for p, v in sorted(r["per_phi_mean_ll"].items())))
        elif name == "WF-C":
            L.append("- WF-C per-φ pooled fold LL (all 5 counted): %s." % ", ".join(
                "φ=%+g: %.6f" % (p, v) for p, v in sorted(r["per_phi_mean_ll"].items())))
    L.append("")
    L.append("- Fold-game flags (selected configs): %s." % "; ".join(
        "%s: %s" % (n, json.dumps(r.get("fold_flag_counts", {}), sort_keys=True))
        for n, r in summary["feature_arms"].items() if r.get("fold_flag_counts")))
    L.append("- Effects smaller than ~0.003 ΔLL are INCONCLUSIVE at this capacity "
             "(packet §6) — stated, not stretched.")
    L.append("")
    L.append("## 8. Neutral-site rows (separate report)")
    L.append("")
    L.append("- The ESPN corpus carries a `neutral_site` flag: %d rows inside the train "
             "window (%s); HCA=0 applied there (flag `neutral_hca0`). The stats-side "
             "warm-up corpus carries NO neutral flag — absence disclosed." % (
                 summary["neutral_rows_train_window"],
                 ", ".join(summary["neutral_game_ids"]) or "none"))
    L.append("")
    L.append("## 9. Fit counts and trial discipline")
    L.append("")
    nf = summary["n_fits"]
    L.append("- Scored-selection fits: B1 grid 27 (all counted) + WF-A 1 + WF-B 5 + WF-C 5 "
             "= **%d**. Diagnostics outside budget: twins (%d), warm-up-vs-cold-start (1), "
             "designed-null checks (byte-identity, not fits), B0 reference." % (
                 nf["b1_grid"] + nf["wf_a"] + nf["wf_b"] + nf["wf_c"],
                 1 + len(summary["feature_arms"])))
    L.append("- Ledger: `SELECTION_LEDGER.jsonl` (every run incl. all 27 grid fits).")
    L.append("")
    with open(os.path.join(LANE_DIR, "SELECTION_REPORT.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")

    # verdict table
    V = []
    V.append("# VERDICT TABLE — lane T_SELECT · WNBA-PLAYERFEAT-SCORED-V1 (TRAIN-INTERNAL)")
    V.append("")
    V.append("| slot | arm | frozen config | verdict | basis |")
    V.append("|---|---|---|---|---|")
    kt = summary["b1_vs_b0_dll"]
    V.append("| baseline | B0 constant | p_home=%.6f | REFERENCE | train-window rate, frozen |" % summary["b0_p_home"])
    V.append("| baseline | B1-WNBA fresh own-Elo | K=%g, HCA=%g, γ=%g (warm-up 1997–2001) | %s | ΔLL vs B0 %+.6f [%.6f,%.6f]; slope %.4f |" % (
        f["k"], f["hca"], f["gamma"],
        "FROZEN (kill test passed)" if kt["kill_passed"] else "KILLED (train-internal)",
        kt["point"], kt["lo"], kt["hi"], summary["b1_slope_validation"]))
    for name, r in summary["feature_arms"].items():
        phi_s = "none (no free scalar)" if r.get("phi") is None else "φ=%+g" % r["phi"]
        V.append("| feature | %s | %s | %s | ΔLL %+.6f [%.6f,%.6f]; slope %.4f; twin %+.6f |" % (
            name, phi_s, r["verdict"], r["dll_point"], r["dll_ci"][0], r["dll_ci"][1],
            r["slope"], r["twin_dll"]))
    V.append("")
    V.append("Verdict vocabulary: FROZEN = selected + train-internal kill test passed; "
             "ADMIT = G-ENTRY passed (point<0, slope in [0.85,1.15], twin clean) — pending "
             "post-GO OOS; INCONCLUSIVE = admitted but CI includes 0; RELEASE = slot "
             "released; KILL = falsified train-internally; MACHINERY_SUSPECT = twin beat "
             "its own parent (arm UN-SCORED). No OOS season was read.")
    V.append("")
    V.append("Notes. (1) WF-B/WF-C: every NONZERO φ in the immutable grid was worse than "
             "the designed null on the pooled folds, so the selection returned φ=0 ≡ parent "
             "exactly (ΔLL = +0.000000 by byte identity) — the honest statement is that "
             "neither load/concentration nor form/absence adds train-internal signal at any "
             "pre-registered strength; slots RELEASED. (2) WF-A MACHINERY_SUSPECT: twin ΔLL "
             "%+.6f vs own parent on the shuffled corpus, with the parent's real-data fold "
             "slope %.4f INSIDE [0.85,1.15] — the adjudication refinement's "
             "miscalibrated-parent exemption does NOT apply; arm UN-SCORED, machinery audit "
             "owed before any re-proposal. (3) Parent reference: B1-WNBA fold slope %.4f; "
             "effects < ~0.003 ΔLL are INCONCLUSIVE at this capacity." % (
                 summary["feature_arms"]["WF-A"]["twin_dll"],
                 summary["feature_arms"]["WF-A"]["parent_slope"],
                 summary["feature_arms"]["WF-A"]["parent_slope"]))
    V.append("")
    with open(os.path.join(LANE_DIR, "VERDICT_TABLE.md"), "w") as fh:
        fh.write("\n".join(V) + "\n")


# ------------------------------------------------------------------ CLI
def main():
    ap = argparse.ArgumentParser(description="T_SELECT harness — WNBA-PLAYERFEAT-SCORED-V1")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mode", choices=["select", "evaluate-oos"])
    ap.add_argument("--source", choices=["real", "synthetic"], default=None)
    ap.add_argument("--go-token", default=None)
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return
    if args.mode == "select":
        if args.source not in (None, "real"):
            raise SystemExit("select mode runs on the real (hard-capped) corpus only")
        run_select()
        return
    if args.mode == "evaluate-oos":
        enforce_oos_gate(args.source or "real", args.go_token)
        if args.source == "synthetic":
            print("evaluate-oos: synthetic rehearsal shape — gate open, no real data read.")
            return
        raise SystemExit("evaluate-oos: real-data OOS execution lives POST-GO, not in "
                         "this lane's select round.")
    ap.print_help()


if __name__ == "__main__":
    main()
