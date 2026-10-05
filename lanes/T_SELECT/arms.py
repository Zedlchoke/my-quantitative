"""arms.py — T_SELECT lane, cycle NFL-WINPROB-NG-SCORED-V1 (TRAIN-INTERNAL SELECTION ONLY).

Implements the frozen Elo replay machinery and candidate arms per:
  - PROTOCOL_NFL_NG.md §0 binding laws (kickoff-grain as-of, same-kickoff exclusion,
    tie law, neutral-site law, completed-games law, franchise lineage continuity),
  - MECHANISMS_NFL_NG.md §2 exact operationalizations (C1/C2/C3/C4),
  - DISPATCH_T_SELECT.md pre-registered grids (pinned; not modifiable here).

TRAIN ONLY: seasons 2000..2018 in games.csv, pbp seasons <= 2017.
ZERO reads of season > 2018 outcomes: hard load filter + assertions below.
Calibration/forecasting vocabulary only. Deterministic; seed 20261005.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Grep-auditable constants (hard load filters + frozen machinery constants)
# ---------------------------------------------------------------------------
SEASON_MIN_GAMES = 2000
SEASON_MAX_GAMES = 2018  # hard load filter for games.csv (TRAIN ceiling)
SEASON_MAX_PBP = 2017    # hard load filter for pbp parquets (C3 priors only)

ELO_INIT = 1500.0
K_BASE = 40.0
GAMMA = 2.0 / 3.0
ELO_SCALE = 400.0
NY_TZ = "America/New_York"
NEUTRAL_LABEL = "Neutral"
SEED = 20261005
INNER_TEST_SEASONS = (2014, 2015, 2016, 2017, 2018)

# 32-lineage franchise map (frozen law): relocations fold into one rating stream;
# CLE/BAL separate; HOU expansion from 2002; everything else identity.
LINEAGE_MAP = {"SD": "LAC", "STL": "LA", "OAK": "LV"}

# Pre-registered grids (DISPATCH_T_SELECT.md — pinned, do not modify)
GRID_C1_BETA = (0, 25, 50, 75, 100)
GRID_C2_LAMBDA = (0.25, 0.5, 0.75)
GRID_C2_GAMMA_D = {"1O3": 1.0 / 3.0, "1O2": 0.5}
GRID_C2_H = (0, 25)
GRID_C3_THETA = (0, 25, 50, 75, 100)
GRID_C4_DELTA = (0, 25, 50)


def sig(x: float) -> float:
    """Logistic function."""
    return 1.0 / (1.0 + math.exp(-x))


def elo_expected(r_own: float, r_opp: float) -> float:
    """B1* pre-game expected score (HCA=0)."""
    return sig((r_own - r_opp) / ELO_SCALE)


def elo_update(r: float, s: float, e: float, k: float = K_BASE) -> float:
    """One Elo update: r + k*(S - E). Ties enter with S = 0.5 (TIE LAW update)."""
    return r + k * (s - e)


def season_revert(r: float, theta: float = 0.0, z: float | None = None) -> float:
    """Offseason reversion R <- 1500 + gamma*(R-1500) [+ theta*z] (C3 prior term)."""
    out = ELO_INIT + GAMMA * (r - ELO_INIT)
    if theta != 0.0 and z is not None:
        out = out + theta * z
    return out


# ---------------------------------------------------------------------------
# Kickoff canonicalization (frozen lane-A law: gameday+gametime in
# America/New_York -> UTC, DST-aware). NFL gametimes are >= 12:00 local, so the
# only DST edge is the fall-back day where post-2am times are standard time
# (ambiguous=False is the DST-aware correct resolution).
# ---------------------------------------------------------------------------
def kickoff_utc(gameday: str, gametime: str) -> pd.Timestamp:
    ts = pd.Timestamp(f"{gameday} {gametime}")
    loc = ts.tz_localize(NY_TZ, ambiguous=False, nonexistent="raise")
    return loc.tz_convert("UTC")


def lineage(team_abbr: str) -> str:
    return LINEAGE_MAP.get(team_abbr, team_abbr)


# ---------------------------------------------------------------------------
# Data loading with hard filters
# ---------------------------------------------------------------------------
@dataclass
class GameSet:
    df: pd.DataFrame          # filtered, sorted by (kickoff_ns, game_id)
    kickoff_ns: np.ndarray    # int64 epoch ns
    kickoff_date: np.ndarray  # ISO date strings (bootstrap cluster key)
    home: np.ndarray          # lineage codes
    away: np.ndarray
    s_home: np.ndarray        # 1.0 home win / 0.0 loss / 0.5 tie (update stream)
    y_bin: np.ndarray         # 1.0/0.0 binary label (ties flagged separately)
    is_tie: np.ndarray
    is_reg: np.ndarray
    is_neutral: np.ndarray
    season: np.ndarray
    week: np.ndarray
    game_id: np.ndarray
    quarantined_columns: list
    n_dropped_over_ceiling: int
    n_pre_dropped: int


# Leakage quarantine: odds/probability columns are never read. They are dropped
# at load with names recorded (PROTOCOL §9 quarantine inheritance).
QUARANTINED_COLUMNS = {
    "spread_line", "total_line", "total", "under_odds", "over_odds",
    "away_moneyline", "home_moneyline", "away_spread_odds", "home_spread_odds",
}
QUARANTINE_PATTERNS = ("odds", "moneyline", "spread")


def quarantine_report(columns) -> list[str]:
    names = []
    for c in columns:
        cl = str(c).lower()
        if c in QUARANTINED_COLUMNS or any(p in cl for p in QUARANTINE_PATTERNS):
            names.append(str(c))
    return sorted(names)


def load_games(csv_path: str) -> GameSet:
    df = pd.read_csv(csv_path, low_memory=False)
    quarantined = quarantine_report(df.columns)
    df = df.drop(columns=[c for c in quarantined if c in df.columns])
    n_total = len(df)
    # HARD FILTER: seasons 2000..2018 only (grep-auditable constants above).
    df = df[(df["season"] >= SEASON_MIN_GAMES) & (df["season"] <= SEASON_MAX_GAMES)].copy()
    n_dropped = n_total - len(df)
    # Assertions: no row outside the TRAIN ceiling survives the filter.
    assert int(df["season"].max()) <= SEASON_MAX_GAMES, "season > SEASON_MAX_GAMES leaked"
    assert int(df["season"].min()) >= SEASON_MIN_GAMES, "season < SEASON_MIN_GAMES leaked"
    # PRE rows dropped with count disclosed (leakage law).
    n_pre = int((df["game_type"] == "PRE").sum())
    df = df[df["game_type"] != "PRE"].copy()
    # Scores must be complete in TRAIN (Lane A: 0 missing 2000-2018).
    assert int(df["home_score"].isna().sum() + df["away_score"].isna().sum()) == 0
    # Kickoffs: 100% parseable required (fallback X = NOT ACTIVATED per Lane A).
    kos = [kickoff_utc(gd, gt) for gd, gt in zip(df["gameday"], df["gametime"])]
    df["kickoff_ns"] = [t.value for t in kos]          # exact int64 epoch ns
    df["kickoff_date"] = [t.date().isoformat() for t in kos]  # bootstrap cluster key
    df["home_lg"] = df["home_team"].map(lineage)
    df["away_lg"] = df["away_team"].map(lineage)
    assert df["home_lg"].notna().all() and df["away_lg"].notna().all()
    # Deterministic fixed order: sort by kickoff, then game_id.
    df = df.sort_values(["kickoff_ns", "game_id"], kind="mergesort").reset_index(drop=True)
    home_score = df["home_score"].to_numpy(dtype=float)
    away_score = df["away_score"].to_numpy(dtype=float)
    is_tie = home_score == away_score
    s_home = np.where(is_tie, 0.5, np.where(home_score > away_score, 1.0, 0.0))
    y_bin = np.where(home_score > away_score, 1.0, 0.0)
    gs = GameSet(
        df=df,
        kickoff_ns=df["kickoff_ns"].to_numpy(dtype=np.int64),
        kickoff_date=df["kickoff_date"].to_numpy(),
        home=df["home_lg"].to_numpy(),
        away=df["away_lg"].to_numpy(),
        s_home=s_home,
        y_bin=y_bin,
        is_tie=is_tie,
        is_reg=(df["game_type"] == "REG").to_numpy(),
        is_neutral=(df["location"] == NEUTRAL_LABEL).to_numpy(),
        season=df["season"].to_numpy(dtype=int),
        week=df["week"].to_numpy(dtype=int),
        game_id=df["game_id"].to_numpy(),
        quarantined_columns=quarantined,
        n_dropped_over_ceiling=n_dropped,
        n_pre_dropped=n_pre,
    )
    return gs


def batches(gs: GameSet):
    """Yield index arrays of games sharing an identical kickoff timestamp.

    Same-kickoff games never inform each other: the whole batch is predicted
    from the pre-batch state, then all updates are applied (PROTOCOL §0.1).
    """
    n = len(gs.kickoff_ns)
    start = 0
    while start < n:
        end = start + 1
        while end < n and gs.kickoff_ns[end] == gs.kickoff_ns[start]:
            end += 1
        yield np.arange(start, end)
        start = end


# ---------------------------------------------------------------------------
# Replay record (per-game, as-of kickoff)
# ---------------------------------------------------------------------------
@dataclass
class ReplayRecord:
    idx: int
    season: int
    week: int
    game_id: str
    home: str
    away: str
    r_home: float          # B1*-stream rating as-of kickoff (post season reversion)
    r_away: float
    e_home: float          # B1* expected score
    e_away: float
    s_home: float          # 1 / 0 / 0.5
    adj_home: float        # C1: SOS_i(t) - Sbar(t); 0.0 when n_i(t) == 0
    adj_away: float
    rest_days_away: float | None  # days since away's strictly-prior kickoff
    is_reg: bool
    is_neutral: bool
    is_tie: bool


def replay_elo(gs: GameSet, z_table: dict | None = None, theta: float = 0.0) -> list[ReplayRecord]:
    """Deterministic kickoff-grain Elo replay.

    One pass over games sorted by (kickoff, game_id). B1* core law:
      - ratings start at ELO_INIT at a lineage's first appearance;
      - season reversion R <- 1500 + (2/3)(R-1500) applied lazily at each
        lineage's FIRST PREDICTION of a new season (no term for first season /
        expansion lineages; C3 adds theta*z_i(s) exactly there);
      - identical-kickoff batches predicted from pre-batch state, updated after;
      - ties update with S = 0.5 (both teams);
      - postseason games update ratings (completed-games law).
    C1 SOS bookkeeping and C4 rest-days bookkeeping ride the same pass (they are
    properties of the B1* stream, arm-independent for prediction-only arms).
    """
    ratings: dict[str, float] = {}
    reverted: dict[str, int] = {}
    sos_sum: dict[tuple[str, int], float] = {}
    sos_n: dict[tuple[str, int], int] = {}
    last_kick: dict[str, int] = {}
    records: list[ReplayRecord] = []

    for bidx in batches(gs):
        i0, i1 = bidx[0], bidx[-1]
        season_b = int(gs.season[i0])
        # S-bar(t): league mean of SOS over lineages with n_i(t) > 0 this season
        # (undefined SOS at season openers contributes nothing; adjustment == 0).
        vals = [
            sos_sum[(lg, season_b)] / sos_n[(lg, season_b)]
            for lg in set(ratings)
            if sos_n.get((lg, season_b), 0) > 0
        ]
        sbar = sum(vals) / len(vals) if vals else None

        # --- prediction phase (pre-batch state; per-lineage lazy reversion) ---
        recs = []
        for i in bidx:
            h, a = gs.home[i], gs.away[i]
            season = int(gs.season[i])
            for lg in (h, a):
                if lg not in ratings:
                    ratings[lg] = ELO_INIT
                    reverted[lg] = season  # first season in data: no prior to revert
                elif reverted[lg] < season:
                    z = z_table.get((season, lg)) if z_table is not None else None
                    ratings[lg] = season_revert(ratings[lg], theta, z)
                    reverted[lg] = season
            r_h, r_a = ratings[h], ratings[a]
            e_h = elo_expected(r_h, r_a)
            e_a = 1.0 - e_h
            adj_h = (sos_sum[(h, season)] / sos_n[(h, season)] - sbar) if sos_n.get((h, season), 0) > 0 else 0.0
            adj_a = (sos_sum[(a, season)] / sos_n[(a, season)] - sbar) if sos_n.get((a, season), 0) > 0 else 0.0
            rest = None
            if a in last_kick:
                rest = (gs.kickoff_ns[i] - last_kick[a]) / (86400.0 * 1e9)
                rest = math.floor(rest + 1e-9)
            recs.append(ReplayRecord(
                idx=int(i), season=season, week=int(gs.week[i]), game_id=str(gs.game_id[i]),
                home=h, away=a, r_home=r_h, r_away=r_a, e_home=e_h, e_away=e_a,
                s_home=float(gs.s_home[i]),
                adj_home=adj_h, adj_away=adj_a, rest_days_away=rest,
                is_reg=bool(gs.is_reg[i]), is_neutral=bool(gs.is_neutral[i]),
                is_tie=bool(gs.is_tie[i]),
            ))

        # --- update phase (post-batch; identical kickoffs never informed each other) ---
        for r in recs:
            ratings[r.home] = elo_update(ratings[r.home], r.s_home, r.e_home)
            ratings[r.away] = elo_update(ratings[r.away], 1.0 - r.s_home, r.e_away)
            for lg, e in ((r.home, r.e_home), (r.away, r.e_away)):
                key = (lg, r.season)
                sos_sum[key] = sos_sum.get(key, 0.0) + e
                sos_n[key] = sos_n.get(key, 0) + 1
            last_kick[r.home] = gs.kickoff_ns[r.idx]
            last_kick[r.away] = gs.kickoff_ns[r.idx]
        records.extend(recs)
        del i0, i1
    return records


# ---------------------------------------------------------------------------
# C2 home/away split deviations (state replay over the frozen B1* stream)
# ---------------------------------------------------------------------------
def replay_c2(records: list[ReplayRecord], lam: float, gamma_d: float, h: float,
              venue_perm_rng: np.random.Generator | None = None,
              return_devs: bool = False):
    """Per-game p_home for C2. R stream is exactly B1* (ratings read, never written).

    Deviations d^H, d^A init 0 at lineage start; in-role updates
    d <- d + lam*K*(S - E) with E from the full prediction formula; offseason
    decay d <- gamma_d*d at the lineage's first prediction of a new season;
    neutral-site games scored with h = 0 and receive no deviation updates.
    venue_perm_rng: if given, swap the home/away ROLE labels on a random half of
    games for the deviation updates only (negative control; predictions keep
    true labels).
    return_devs: also return per-row (bonus_home, bonus_away) where
    bonus_home = d^H + hterm and bonus_away = d^A (prediction-formula bonuses).
    """
    dev: dict[str, list[float]] = {}
    decayed: dict[str, int] = {}
    out = np.empty(len(records), dtype=float)
    bh = np.empty(len(records), dtype=float)
    ba = np.empty(len(records), dtype=float)
    for k, r in enumerate(records):
        for lg in (r.home, r.away):
            if lg not in dev:
                dev[lg] = [0.0, 0.0]
                decayed[lg] = r.season
            elif decayed[lg] < r.season:
                dev[lg][0] *= gamma_d
                dev[lg][1] *= gamma_d
                decayed[lg] = r.season
        d_h, d_a = dev[r.home][0], dev[r.away][1]
        hterm = 0.0 if r.is_neutral else h
        p = sig((r.r_home + d_h - r.r_away - d_a + hterm) / ELO_SCALE)
        out[k] = p
        bh[k] = d_h + hterm
        ba[k] = d_a
        if not r.is_neutral:  # flagged games receive no deviation updates
            if venue_perm_rng is not None and venue_perm_rng.random() < 0.5:
                # venue-label permutation control: roles swapped in the UPDATE
                # channel only (E computed under the swapped-role formula).
                p_swap = sig((r.r_home + dev[r.home][1] - r.r_away - dev[r.away][0] + hterm) / ELO_SCALE)
                dev[r.home][1] += lam * K_BASE * (r.s_home - p_swap)
                dev[r.away][0] += lam * K_BASE * ((1.0 - r.s_home) - (1.0 - p_swap))
            else:
                dev[r.home][0] += lam * K_BASE * (r.s_home - p)
                dev[r.away][1] += lam * K_BASE * ((1.0 - r.s_home) - (1.0 - p))
    if return_devs:
        return out, bh, ba
    return out


# ---------------------------------------------------------------------------
# C3 z-standardization from pbp (offseason-prior role ONLY; SEASON_MAX_PBP=2017)
# ---------------------------------------------------------------------------
def z_standardize(E: dict[str, float]) -> dict[str, float]:
    """z_i = (E_i - mean)/sd (population sd, ddof=0) across the given lineages.
    Returns {} when dispersion is degenerate (sd == 0)."""
    if not E:
        return {}
    vals = np.array(sorted(E.values()), dtype=float)
    mu = float(vals.mean())
    sd = float(vals.std(ddof=0))
    if sd == 0.0:
        return {}
    return {lg: (E - mu) / sd for lg, E in E.items()}


def build_z_table(pbp_dir: str) -> dict[tuple[int, str], float]:
    """z_i(s) = (E_i(s-1) - mean)/sd (population sd, ddof=0) across lineages
    present in prior season s-1, E = 0.5*(off EPA/play + def EPA-allowed/play),
    over prior-season REG plays with both team attributions set and epa non-null."""
    import pyarrow.parquet as pq

    per_season: dict[int, dict[str, float]] = {}
    for year in range(SEASON_MIN_GAMES, SEASON_MAX_PBP + 1):
        tbl = pq.read_table(
            f"{pbp_dir}/play_by_play_{year}.parquet",
            columns=["season", "season_type", "posteam", "defteam", "epa"],
        ).to_pandas()
        assert int(tbl["season"].max()) <= SEASON_MAX_PBP, "pbp season > SEASON_MAX_PBP leaked"
        reg = tbl[tbl["season_type"] == "REG"]
        pt = reg["posteam"].astype("string")
        dt = reg["defteam"].astype("string")
        m = reg[
            pt.notna() & (pt.str.strip() != "") & pt.isin(LINEAGE_ALL)
            & dt.notna() & (dt.str.strip() != "") & dt.isin(LINEAGE_ALL)
            & reg["epa"].notna()
        ]
        off = m.groupby(m["posteam"], observed=True)["epa"].agg(["sum", "count"])
        dfn = m.groupby(m["defteam"], observed=True)["epa"].agg(["sum", "count"])
        E: dict[str, float] = {}
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

    z_table: dict[tuple[int, str], float] = {}
    for s in range(SEASON_MIN_GAMES + 1, SEASON_MAX_PBP + 2):  # target seasons 2001..2018
        prev = per_season.get(s - 1, {})
        zs = z_standardize(prev)
        for lg, z in zs.items():
            z_table[(s, lg)] = z
    return z_table


LINEAGE_ALL = {
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
    "GB", "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA", "MIN", "NE", "NO",
    "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
}
