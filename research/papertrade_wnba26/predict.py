# predict.py — WNBA-WINPROB-2026-REMAINDER-V1 · Lane WNBA-REALPATH · 2026-10-07
#
# REALPATH prediction entry point: replays the B1-WNBA verbatim rating stream
# over completed games and emits pre-tip probabilities for upcoming fixtures.
#
# ---------------------------------------------------------------------------
# NO-STORAGE LAW (binding)
#   This module is a PURE FUNCTION. It performs NO file I/O, NO network access,
#   NO logging, NO printing, and holds NO global mutable state. Real-game
#   probabilities are computed ONLY post-GO by execute.py calling
#   wnba26_predict(); nothing here stores, persists, or transmits them.
#   Synthetic probabilities may exist in rehearsals/tests only.
# ---------------------------------------------------------------------------
#
# FROZEN ARM (FREEZE_PACKET §1 verbatim — never re-tuned):
#   B1-WNBA: own-Elo K=32 / HCA=50 / gamma=0.65, binary updates,
#   neutral site => HCA_eff = 0.
#
# ENGINE LAW (verbatim port of the pinned engine `arms.py`, sha
# 82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3,
# read-only source .worktrees/wnba-playerfeat-scored-v1/integration/lanes/
# T_SELECT/; equivalence to the frozen bytes is test-enforced):
#   p_home = 1 / (1 + 10^(-(R_h - R_a + HCA_eff) / 400)),  logistic scale 400.
#   Update (both sides):  R <- R + K * (outcome - p).  Outcome = home win
#   indicator; the away side takes outcome (1 - outcome) and expectation
#   (1 - p)  (zero-sum pair update).
#   Season boundary:      R <- 1500 + gamma * (R_end - 1500)  (league mean
#                         fixed 1500).
#   New franchise entry:  R = 1500.
#   Tip batching: games sharing an exact tip_utc are ALL predicted from the
#   same rating snapshot, then updates applied (a simultaneous game is never
#   an input to another). Games are strictly ordered by (tip_utc, game_id).
#
# STREAM STATE LAW (FREEZE_PACKET §3):
#   The rating state used for a game's prediction includes ONLY completed rows
#   (result present) with tip_utc < batch anchor — STRICT: the anchor is an
#   EXCLUSIVE deadline; a row stamped exactly at the anchor is excluded.
#
# BATCH ANCHOR LAW (FREEZE_PACKET §5; disclosed exclusive tightening):
#   anchor_for_game(tip, day_first_tip) = day_first_tip - 6h10m, where
#   day_first_tip is the earliest tip_utc of the game's Eastern calendar day
#   (America/New_York) in the upcoming slate. Strict/exclusive. The per-row
#   deadline variant is per_game_anchor(tip) = tip - 6h10m.
#
# INPUT SCHEMA (real rows as mapping-like dicts, e.g. csv.DictReader rows or
# pandas Series — both the pinned snapshot's columns):
#   game_id (or id), date (ISO-8601 tip, SPEC §3 canonicalization:
#   pd.to_datetime(espn.date, utc=True, format="ISO8601")), season,
#   home_id / away_id (franchise key = ESPN team id; a non-positive id or a
#   TBD side falls back to a "tbd:<abbr>" key with fresh-entry rating 1500),
#   home_score / away_score, status_type_name, neutral_site.
#   A completed row is RESULT-PRESENT iff status_type_name == "STATUS_FINAL"
#   and both scores are finite numbers; a FINAL row with equal scores is a
#   fail-closed error (binary outcome law). Rows without a result (e.g.
#   STATUS_POSTPONED) are excluded from the rating stream — never inferred.
#
# DETERMINISM: no wall clock, no randomness, no I/O. Same inputs -> identical
# outputs, including a byte-stable state_digest.

import hashlib
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Mapping, Tuple
from zoneinfo import ZoneInfo

__all__ = [
    "MODEL_ID",
    "B1_CONSTANTS",
    "ANCHOR_OFFSET",
    "ET_TZ",
    "SCALE",
    "LEAGUE_MEAN",
    "anchor_for_game",
    "per_game_anchor",
    "et_local_date",
    "day_first_tips",
    "replay_stream",
    "state_digest",
    "wnba26_predict",
]

# --------------------------------------------------------------------------
# Frozen constants (FREEZE_PACKET §1; emitted verbatim in every entry)
# --------------------------------------------------------------------------
MODEL_ID = "B1_WNBA"
B1_CONSTANTS = {"K": 32, "HCA": 50, "gamma": 0.65}

_K = 32.0        # float form used by the update arithmetic (GRID_K entry 32)
_HCA = 50.0      # float form used by the home-advantage argument (GRID_HCA 50.0)
GAMMA = 0.65

LEAGUE_MEAN = 1500.0
SCALE = 400.0

#: Batch anchor offset: T0 - 6h10m, exclusive deadline (FREEZE_PACKET §5).
ANCHOR_OFFSET = timedelta(hours=6, minutes=10)

ET_TZ = ZoneInfo("America/New_York")


# --------------------------------------------------------------------------
# Small deterministic helpers
# --------------------------------------------------------------------------
def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_tip(value: Any) -> datetime:
    """ISO-8601 tip parse -> aware UTC datetime (naive input is fail-closed)."""
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value).strip()
        if s.endswith(("Z", "z")):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
        except ValueError as exc:
            raise ValueError(f"malformed tip timestamp {value!r}: {exc}") from exc
    if dt.tzinfo is None:
        raise ValueError(f"naive tip timestamp {value!r} (tz-aware required)")
    return dt.astimezone(timezone.utc)


def _fmt_tip(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in ("true", "1")


def _to_int(value: Any, what: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"non-integer {what}: {value!r}") from exc


def _franchise_key(row: Mapping[str, Any], side: str) -> str:
    """Franchise key for one side: ESPN team id; TBD/non-positive -> tbd key."""
    raw_id = row.get(f"{side}_id")
    abbr = str(row.get(f"{side}_abbreviation", "TBD"))
    if raw_id is None:
        return f"tbd:{abbr}"
    tid = _to_int(raw_id, f"{side}_id")
    if tid <= 0:
        return f"tbd:{abbr}"
    return f"id:{tid}"


def et_local_date(tip: Any) -> Any:
    """SPEC §3 day-key law: local_date := tip_utc in America/New_York."""
    return _parse_tip(tip).astimezone(ET_TZ).date()


# --------------------------------------------------------------------------
# Row normalization (real pinned-snapshot schema)
# --------------------------------------------------------------------------
def _game_id(row: Mapping[str, Any]) -> str:
    raw = row.get("game_id", row.get("id"))
    if raw is None:
        raise ValueError(f"row without game_id/id: {row!r}")
    return str(raw)


def _tip_of(row: Mapping[str, Any]) -> datetime:
    raw = row.get("date", row.get("tip_utc"))
    if raw is None:
        raise ValueError(f"row without date/tip_utc: {row!r}")
    return _parse_tip(raw)


def _is_result_present(row: Mapping[str, Any]) -> bool:
    """Completed-only law: result present iff STATUS_FINAL + finite scores."""
    if str(row.get("status_type_name", "")) != "STATUS_FINAL":
        return False
    hs, as_ = row.get("home_score"), row.get("away_score")
    if hs is None or as_ is None:
        return False
    return math.isfinite(float(hs)) and math.isfinite(float(as_))


def _normalize_game(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Completed row -> engine game (verbatim stream input); result required."""
    hs = float(row["home_score"])
    as_ = float(row["away_score"])
    if hs == as_:
        raise ValueError(
            f"game {_game_id(row)}: FINAL row with equal scores {hs}-{as_} "
            "(binary outcome law; fail-closed)")
    return {
        "tip": _tip_of(row),
        "game_id": _game_id(row),
        "season": _to_int(row["season"], "season"),
        "fk_home": _franchise_key(row, "home"),
        "fk_away": _franchise_key(row, "away"),
        "home_win": 1.0 if hs > as_ else 0.0,
        "neutral": _truthy(row.get("neutral_site", False)),
    }


def _normalize_fixture(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Upcoming row -> prediction fixture (no result needed)."""
    return {
        "tip": _tip_of(row),
        "match_id": _game_id(row),
        "season": _to_int(row["season"], "season"),
        "fk_home": _franchise_key(row, "home"),
        "fk_away": _franchise_key(row, "away"),
        "neutral": _truthy(row.get("neutral_site", False)),
    }


# --------------------------------------------------------------------------
# Anchor laws
# --------------------------------------------------------------------------
def anchor_for_game(tip: Any, day_first_tip: Any) -> datetime:
    """Batch anchor = day_first_tip - 6h10m; STRICT EXCLUSIVE deadline.

    ``day_first_tip`` is the earliest tip_utc of the game's Eastern calendar
    day in the upcoming slate (T0 of the ET day). The returned instant gates
    the rating state: only completed rows with tip_utc STRICTLY before it
    feed the stream. ``tip`` is validated to belong to the same Eastern day
    and to be at or after ``day_first_tip`` (fail-closed against inconsistent
    callers).
    """
    tip_dt = _parse_tip(tip)
    first_dt = _parse_tip(day_first_tip)
    if et_local_date(tip_dt) != et_local_date(first_dt):
        raise ValueError(
            f"anchor law: tip {_fmt_tip(tip_dt)} and day_first_tip "
            f"{_fmt_tip(first_dt)} are not the same Eastern calendar day")
    if first_dt > tip_dt:
        raise ValueError(
            f"anchor law: day_first_tip {_fmt_tip(first_dt)} is after tip "
            f"{_fmt_tip(tip_dt)}")
    return first_dt - ANCHOR_OFFSET


def per_game_anchor(tip: Any) -> datetime:
    """Per-row deadline variant (FREEZE_PACKET §5): tip_utc - 6h10m."""
    return _parse_tip(tip) - ANCHOR_OFFSET


def day_first_tips(fixtures: List[Dict[str, Any]]) -> Dict[Any, datetime]:
    """ET day -> earliest tip_utc among the given fixtures (the day's T0)."""
    first: Dict[Any, datetime] = {}
    for f in fixtures:
        day = et_local_date(f["tip"])
        if day not in first or f["tip"] < first[day]:
            first[day] = f["tip"]
    return first


# --------------------------------------------------------------------------
# Verbatim B1-WNBA rating stream (port of pinned arms.py run_stream, parent
# path c=1 / phi=0; float operations identical, order identical)
# --------------------------------------------------------------------------
class _StreamState:
    """Per-franchise rating state with explicit season-segment bookkeeping.

    base[fk] + acc[fk] == r[fk] always; season boundaries re-derive base via
    1500 + gamma*(R_end - 1500); fresh franchise entries enter at 1500.
    """

    def __init__(self) -> None:
        self.base: Dict[str, float] = {}
        self.acc: Dict[str, float] = {}
        self.r: Dict[str, float] = {}
        self.r_end: Dict[str, float] = {}
        self.season: Dict[str, int] = {}

    def _entry(self, fk: str) -> float:
        if fk not in self.r_end:
            return LEAGUE_MEAN
        return LEAGUE_MEAN + GAMMA * (self.r_end[fk] - LEAGUE_MEAN)

    def pre_game_rating(self, fk: str, season: int) -> float:
        """Effective rating for a prediction, opening the season segment lazily."""
        if self.season.get(fk) != season:
            if fk in self.r:
                self.r_end[fk] = self.r[fk]
            self.base[fk] = self._entry(fk)
            self.acc[fk] = 0.0
            self.r[fk] = self.base[fk]
            self.season[fk] = season
        return self.r[fk]

    def apply_update(self, fk: str, outcome: float, p: float) -> None:
        step = _K * (outcome - p)
        self.acc[fk] += step
        self.r[fk] = self.base[fk] + self.acc[fk]

    def end_of_stream(self) -> None:
        """Freeze r_end for every open segment (arms.py end_of_stream)."""
        for fk, r in self.r.items():
            self.r_end[fk] = r


def replay_stream(games: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], _StreamState]:
    """Walk-forward B1-WNBA stream over (tip, game_id)-ordered games.

    Verbatim port of arms.run_stream for the parent arm (k=32, hca=50,
    gamma=0.65, c=1, phi=0): tip-batched snapshots (all games sharing an
    exact tip predicted from one state, updates applied after the batch),
    binary zero-sum updates. Returns the per-game p_home stream (same order
    as the sorted games) and the end-of-stream state.
    """
    ordered = sorted(games, key=lambda g: (g["tip"], g["game_id"]))
    st = _StreamState()
    preds: List[Dict[str, Any]] = []
    i = 0
    n = len(ordered)
    while i < n:
        # tip-batched snapshot: all games at this exact tip predicted from one state
        tip = ordered[i]["tip"]
        j = i
        batch = []
        while j < n and ordered[j]["tip"] == tip:
            batch.append(ordered[j])
            j += 1
        batch_ctx = []
        for g in batch:
            hca_eff = 0.0 if g["neutral"] else _HCA
            r_h = st.pre_game_rating(g["fk_home"], g["season"])
            r_a = st.pre_game_rating(g["fk_away"], g["season"])
            arg = (r_h - r_a) + hca_eff
            p_home = 1.0 / (1.0 + 10.0 ** (-arg / SCALE))
            batch_ctx.append((g, p_home))
            preds.append({"game_id": g["game_id"], "tip": g["tip"],
                          "p_home": p_home})
        for g, p_home in batch_ctx:
            hw = float(g["home_win"])
            st.apply_update(g["fk_home"], hw, p_home)
            st.apply_update(g["fk_away"], 1.0 - hw, 1.0 - p_home)
        i = j
    st.end_of_stream()
    return preds, st


def state_digest(st: _StreamState) -> str:
    """sha256 of the sorted rating table (proves the completed-only state).

    Canonical form: one line per materialized franchise, ascending franchise
    key, ``fk=repr(rating)`` (repr is the shortest round-trip float form and
    is byte-stable). No probability material enters this digest.
    """
    lines = [f"{fk}={st.r[fk]!r}" for fk in sorted(st.r)]
    return sha256_hex("\n".join(lines))


def _effective_rating(st: _StreamState, fk: str, season: int) -> float:
    """Rating a prediction would see (pre_game_rating postcondition, pure).

    Mirrors arms.pre_game_rating exactly without mutating the state: same
    season -> current rating; materialized in another season -> season-boundary
    reversion 1500 + gamma*(R_end - 1500); never seen -> fresh entry 1500.
    """
    if st.season.get(fk) == season:
        return st.r[fk]
    if fk in st.r_end:
        return LEAGUE_MEAN + GAMMA * (st.r_end[fk] - LEAGUE_MEAN)
    return LEAGUE_MEAN


# --------------------------------------------------------------------------
# Prediction entry point
# --------------------------------------------------------------------------
def wnba26_predict(completed_rows: List[Mapping[str, Any]],
                   upcoming: List[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Replay B1-WNBA over completed rows; predict the upcoming fixtures.

    Laws (see module docstring): games strictly ordered by (tip, game_id);
    tip-batch snapshot; day-batch state (one rating snapshot per Eastern day
    anchor, so same-ET-day fixtures — same tip or not — share one state);
    completed-only state with tip < anchor STRICT; neutral => HCA_eff = 0;
    deterministic; no I/O; nothing persisted.

    Returns entries sorted by (tip_utc, match_id):
      {match_id, tip_utc, p_home, p_away, state_digest, model_id,
       constants:{K:32, HCA:50, gamma:0.65}}
    """
    games = [_normalize_game(r) for r in completed_rows if _is_result_present(r)]
    fixtures = [_normalize_fixture(r) for r in upcoming]
    fixtures.sort(key=lambda f: (f["tip"], f["match_id"]))
    first_tips = day_first_tips(fixtures)

    # one replayed state per distinct day anchor (memoized; pure)
    states: Dict[datetime, _StreamState] = {}
    out: List[Dict[str, Any]] = []
    for f in fixtures:
        anchor = anchor_for_game(f["tip"], first_tips[et_local_date(f["tip"])])
        if anchor not in states:
            sub = [g for g in games if g["tip"] < anchor]  # STRICT exclusion
            states[anchor] = replay_stream(sub)[1]
        st = states[anchor]
        r_h = _effective_rating(st, f["fk_home"], f["season"])
        r_a = _effective_rating(st, f["fk_away"], f["season"])
        hca_eff = 0.0 if f["neutral"] else _HCA
        arg = (r_h - r_a) + hca_eff
        p_home = 1.0 / (1.0 + 10.0 ** (-arg / SCALE))
        out.append({
            "match_id": f["match_id"],
            "tip_utc": _fmt_tip(f["tip"]),
            "p_home": p_home,
            "p_away": 1.0 - p_home,
            "state_digest": state_digest(st),
            "model_id": MODEL_ID,
            "constants": dict(B1_CONSTANTS),
        })
    return out
