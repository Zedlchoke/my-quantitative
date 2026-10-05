"""schedule.py — PIPE lane recorder, cycle NFL-WINPROB-NG-SCORED-V1.

Versioned-schedule loading for the recorder. The recorder NEVER reads a live
schedule: it reads a games.csv SNAPSHOT whose sha256 is pinned and enters the
batch's inputs_digest. A fresh-pull function exists for real record time but is
NEVER executed by any lane mode (dispatch law: implement, do not run).

Laws implemented here (FREEZE_PACKET.md §3/§4, PROTOCOL §0 via frozen arms.py):
  - sha pin: the file is hashed BEFORE parsing; mismatch = loud failure.
  - quarantine: odds/probability columns are dropped at load, names disclosed
    (frozen arms.quarantine_report; PROTOCOL §9 inheritance).
  - kickoff canonicalization: gameday+gametime in America/New_York -> UTC via
    the frozen arms.kickoff_utc (DST-aware); 1999 dropped (not kickoff-capable,
    lane-A law); PRE rows dropped (count disclosed).
  - completed-games law: a game is warmup-admissible iff BOTH final scores are
    present AND its kickoff is STRICTLY before the batch timestamp.
  - future-with-score abort: any row with kickoff >= batch timestamp carrying a
    score means a corrupt/stale snapshot -> hard ABORT, nothing computed.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

TS_FMT = "%Y-%m-%dT%H:%M:%SZ"
SEASON_MIN = 2000  # 1999 has no parseable kickoffs (SUCCESSOR_DATA_AUDIT §1)


class FutureScoreAbort(RuntimeError):
    """A future game (kickoff >= batch time) carries a score: corrupt/stale
    snapshot. Hard abort — nothing is computed or written."""


class SchedulePinError(RuntimeError):
    """Snapshot bytes do not match the pinned sha256."""


def iso_z(ts: dt.datetime) -> str:
    return ts.astimezone(dt.timezone.utc).strftime(TS_FMT)


def ns(iso: str) -> int:
    d = dt.datetime.strptime(iso, TS_FMT).replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp()) * 10**9


def iso_of_ns(v: int) -> str:
    return dt.datetime.fromtimestamp(v / 10**9, dt.timezone.utc).strftime(TS_FMT)


@dataclass
class Schedule:
    path: Path
    sha256: str
    df: object                       # filtered pandas DataFrame (quarantined cols dropped)
    kickoff_ns: list                 # int64 epoch ns per row (original row order)
    quarantined_columns: list
    n_rows_total: int
    n_dropped_pre_2000: int
    n_dropped_preseason: int
    season_min: int
    season_max: int


def load_snapshot(arms, path, expected_sha256: str) -> Schedule:
    """Load a games.csv snapshot with a mandatory sha256 pin (fail-closed)."""
    import pandas as pd

    path = Path(path)
    got = _sha256_file(path)
    if got != expected_sha256:
        raise SchedulePinError(
            f"schedule snapshot pin violated: {path} sha256 {got} != pinned {expected_sha256}"
        )
    df = pd.read_csv(path, low_memory=False)
    n_total = len(df)
    quarantined = arms.quarantine_report(df.columns)
    df = df.drop(columns=[c for c in quarantined if c in df.columns])
    # 1999 exclusion (not kickoff-capable) and no season below the lineage era.
    n_pre = int((df["season"] < SEASON_MIN).sum())
    df = df[df["season"] >= SEASON_MIN].copy()
    # PRE rows never enter the recorder (frozen loader law).
    n_preseason = int((df["game_type"] == "PRE").sum())
    df = df[df["game_type"] != "PRE"].copy()
    # Kickoffs: parse ALL rows; any parse failure is a loud stop (fallback X
    # NOT ACTIVATED — gametime 100% present 2000+ on this snapshot family).
    kos = [arms.kickoff_utc(gd, gt) for gd, gt in zip(df["gameday"], df["gametime"])]
    df["kickoff_ns"] = [t.value for t in kos]
    df["home_lg"] = df["home_team"].map(arms.lineage)
    df["away_lg"] = df["away_team"].map(arms.lineage)
    assert df["home_lg"].notna().all() and df["away_lg"].notna().all()
    return Schedule(
        path=path,
        sha256=got,
        df=df,
        kickoff_ns=df["kickoff_ns"].to_numpy(dtype="int64").tolist(),
        quarantined_columns=quarantined,
        n_rows_total=n_total,
        n_dropped_pre_2000=n_pre,
        n_dropped_preseason=n_preseason,
        season_min=int(df["season"].min()),
        season_max=int(df["season"].max()),
    )


def future_score_violations(sched: Schedule, batch_ts_ns: int) -> list[str]:
    """HARD LEGALITY ASSERT: games with kickoff >= batch timestamp that already
    carry a final score. Any hit = corrupt/stale snapshot -> abort list."""
    df = sched.df
    ko = df["kickoff_ns"].to_numpy(dtype="int64")
    hs = df["home_score"]
    as_ = df["away_score"]
    scored = hs.notna().to_numpy() | as_.notna().to_numpy()
    bad = (ko >= batch_ts_ns) & scored
    return [str(g) for g in df.loc[bad, "game_id"].tolist()]


def split_rows(sched: Schedule, batch_ts_ns: int):
    """Split the snapshot under the completed-games law.

    Returns (warmup_rows, target_df_idx, counts):
      warmup_rows  — row dicts for COMPLETED games: both scores present AND
                     kickoff strictly < batch timestamp (REG+POST; PRE already
                     dropped at load). These are the only outcome-carrying rows
                     the recorder ever consumes (state-carry update input).
      target_idx   — df positional indices of FUTURE rows (kickoff >= batch,
                     no score) — candidates for a prediction batch.
      counts       — disclosure aggregates (per-season completed counts, etc.).
    No probability is computed here; no metric is computed on any row.
    """
    df = sched.df
    ko = df["kickoff_ns"].to_numpy(dtype="int64")
    scored = (df["home_score"].notna() & df["away_score"].notna()).to_numpy()
    warm_mask = (ko < batch_ts_ns) & scored
    fut_mask = (ko >= batch_ts_ns) & (~scored)
    started_no_score = int(((ko < batch_ts_ns) & (~scored)).sum())
    warm_rows = []
    per_season: dict[int, int] = {}
    sub = df.loc[warm_mask, ["game_id", "season", "week", "game_type", "gameday",
                             "gametime", "home_lg", "away_lg", "home_score",
                             "away_score", "location", "kickoff_ns"]]
    for row in sub.itertuples(index=False):
        hs, as_ = float(row.home_score), float(row.away_score)
        s_home = 0.5 if hs == as_ else (1.0 if hs > as_ else 0.0)
        season = int(row.season)
        per_season[season] = per_season.get(season, 0) + 1
        warm_rows.append(dict(
            kickoff_ns=int(row.kickoff_ns),
            home=row.home_lg,
            away=row.away_lg,
            s_home=s_home,
            season=season,
            week=int(row.week),
            game_type=str(row.game_type),
            game_id=str(row.game_id),
            is_neutral=(row.location == "Neutral"),
        ))
    counts = {
        "rows_total": int(len(df)),
        "warmup_completed_games": len(warm_rows),
        "in_progress_excluded": started_no_score,
        "future_unplayed": int(fut_mask.sum()),
        "completed_per_season": {str(k): per_season[k] for k in sorted(per_season)},
    }
    return warm_rows, df.index[fut_mask].tolist(), counts


def rows_to_gameset(arms, rows):
    """Deterministic frozen GameSet over row dicts (warmup rows and/or future
    target rows, already score-labelled or placeholder-labelled by the caller).
    Sorted by (kickoff_ns, game_id); identical-kickoff batches then behave
    exactly as the frozen arms.batches law demands."""
    import numpy as np

    rows = sorted(rows, key=lambda r: (r["kickoff_ns"], r["game_id"]))
    n = len(rows)
    col = lambda name, dtype: np.array([r[name] for r in rows], dtype=dtype)
    s_home = col("s_home", float)
    return arms.GameSet(
        df=None,
        kickoff_ns=col("kickoff_ns", np.int64),
        kickoff_date=np.array([
            dt.datetime.fromtimestamp(r["kickoff_ns"] / 10**9, dt.timezone.utc).date().isoformat()
            for r in rows
        ], dtype=object),
        home=col("home", object),
        away=col("away", object),
        s_home=s_home,
        y_bin=np.where(s_home == 0.5, 0.0, s_home),
        is_tie=np.array([r["s_home"] == 0.5 for r in rows], dtype=bool),
        is_reg=np.array([r.get("game_type", "REG") == "REG" for r in rows], dtype=bool),
        is_neutral=col("is_neutral", bool),
        season=col("season", np.int64),
        week=col("week", np.int64),
        game_id=col("game_id", object),
        quarantined_columns=[],
        n_dropped_over_ceiling=0,
        n_pre_dropped=0,
    )


# ---------------------------------------------------------------------------
# Fresh-pull function (IMPLEMENTED, NEVER EXECUTED by any lane mode).
# At real record time (post-GO only, controller-run) a fresh snapshot is pulled
# to a NEW versioned directory; its sha256 + pull time enter inputs_digest. The
# pinned registration snapshot is never overwritten.
# ---------------------------------------------------------------------------

def fetch_latest_schedule_snapshot(dest_dir, url: str = None, timestamp_url: str | None = None):
    """Pull the current nflverse `schedules` release games.csv into dest_dir
    (a NEW directory; refuses to overwrite existing bytes) and return
    {"path", "sha256", "bytes", "pulled_utc", "http"}.

    NOT CALLED anywhere in this cycle's lane runs (dispatch law). Exists so the
    real record-time path is already implemented and auditable. Public anonymous
    URL only; no API call; $0.
    """
    import urllib.request

    url = url or "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
    dest_dir = Path(dest_dir)
    if dest_dir.exists() and any(dest_dir.iterdir()):
        raise RuntimeError(f"refusing to write into non-empty {dest_dir} (append-only discipline)")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "games.csv"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:  # nosec - public fixed URL
        code = resp.status
        data = resp.read()
    if code != 200:
        raise RuntimeError(f"schedule pull failed: HTTP {code}")
    tmp = dest.with_suffix(".csv.partial")
    tmp.write_bytes(data)
    tmp.replace(dest)  # atomic publish; sha over the published bytes
    pulled_utc = dt.datetime.now(dt.timezone.utc).strftime(TS_FMT)
    return {
        "path": str(dest),
        "sha256": _sha256_file(dest),
        "bytes": len(data),
        "pulled_utc": pulled_utc,
        "http": code,
        "url": url,
    }


def _sha256_file(path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
