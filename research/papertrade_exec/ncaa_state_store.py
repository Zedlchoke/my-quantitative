"""NCAA lanes (PAPERDESK-FIXALL-NCAA-V1 W5) — the FROZEN model state store.

The laws below are transcribed BYTE-SEMANTICALLY from the audited intake
`ncaa_intake/frozen_test.py` (CONFIRMED prediction program; owner law: no
constant may change):

  Elo:    K=20, HFA +65 (0 on a neutral floor), new teams 1500,
          between-season regression of the DISTANCE to 1500 by 25%
          (elo <- 1500 + (elo-1500)*0.75);
  Eff:    points-space, opponent+location adjusted, rebuilt game-by-game.
          L = expanding league mean points per team-game (init 70.0 while
          empty); H_PTS = 3.2 when not neutral; A = 0.06 update step;
          off/deff regress 25% toward 0 at the same season-change trigger;
  REST:   10.0 default (first appearance), else min(days since last game,
          30);
  p_elo:  1/(1+10^(-(elo_h - elo_a + adj)/400));
  features (frozen, pre-game): elo_diff = (elo_h+adj)-elo_a,
          eff_margin = pred_h - pred_a where pred_h = L+off_h+deff_a+hpts,
          pred_a = L+off_a+deff_h; net_diff = (off_h-deff_h)-(off_a-deff_a);
          rest_h, rest_a, rest_diff, conf_game (1 when conference ids match
          AND both are known), neutral.

UPDATE ORDER per game is the FROZEN one: features/pre-game p are computed
from the state BEFORE the game; then Elo update (home first), then
efficiency update (err_h then err_a), then last_date, then the expanding
mean. The replay test reconstructs the store from raw scores and demands a
bit-identical state hash across two independent rebuilds (the
anti-leakage check of the original audit).
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

K, HFA, REGRESS = 20.0, 65.0, 0.25
L0, H_PTS, A_EFF = 70.0, 3.2, 0.06
R0 = 1500.0
FEATURES = ("elo_diff", "eff_margin", "net_diff", "rest_h", "rest_a",
            "rest_diff", "conf_game", "neutral")
STATE_SCHEMA = "ncaa_state_store@1"


def _d(x) -> date:
    if isinstance(x, date):
        return x
    return datetime.strptime(str(x)[:10], "%Y-%m-%d").date()


class NcaaState:
    """One gender's model state. Plain dicts + the expanding mean — the
    exact numeric semantics of the frozen walk-forward pass."""

    def __init__(self):
        self.elo: dict = {}
        self.off: dict = {}
        self.deff: dict = {}
        self.last_date: dict = {}
        self.tot_pts = 0
        self.tot_tg = 0
        self.cur_season = None
        self.games_processed = 0

    # ------------------------------------------------------------- snapshot --
    def digest(self) -> str:
        body = json.dumps({
            "elo": {str(k): round(v, 12) for k, v in sorted(self.elo.items(),
                                                            key=lambda kv: str(kv[0]))},
            "off": {str(k): round(v, 12) for k, v in sorted(self.off.items(),
                                                            key=lambda kv: str(kv[0]))},
            "deff": {str(k): round(v, 12) for k, v in sorted(self.deff.items(),
                                                             key=lambda kv: str(kv[0]))},
            "last_date": {str(k): str(v) for k, v in
                          sorted(self.last_date.items(),
                                 key=lambda kv: str(kv[0]))},
            "tot_pts": self.tot_pts, "tot_tg": self.tot_tg,
            "cur_season": self.cur_season,
            "games_processed": self.games_processed,
        }, sort_keys=True)
        return hashlib.sha256(body.encode()).hexdigest()

    def save(self, path: Path, *, league: str) -> dict:
        rec = {"schema": STATE_SCHEMA, "league": league,
               "updated_at_utc": datetime.now(timezone.utc)
               .strftime("%Y-%m-%dT%H:%M:%SZ"),
               "games_processed": self.games_processed,
               "state_sha256": self.digest(),
               "state": {"elo": self.elo, "off": self.off,
                         "deff": self.deff, "last_date":
                             {str(k): str(v) for k, v in
                              self.last_date.items()},
                         "tot_pts": self.tot_pts, "tot_tg": self.tot_tg,
                         "cur_season": self.cur_season,
                         "games_processed": self.games_processed}}
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rec, indent=1, sort_keys=True))
        return rec

    @classmethod
    def load(cls, path: Path) -> "NcaaState | None":
        try:
            rec = json.loads(Path(path).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        st = rec.get("state") or {}
        obj = cls()
        obj.elo = {k: float(v) for k, v in (st.get("elo") or {}).items()}
        obj.off = {k: float(v) for k, v in (st.get("off") or {}).items()}
        obj.deff = {k: float(v) for k, v in (st.get("deff") or {}).items()}
        obj.last_date = {k: _d(v) for k, v in
                         (st.get("last_date") or {}).items()}
        obj.tot_pts = int(st.get("tot_pts") or 0)
        obj.tot_tg = int(st.get("tot_tg") or 0)
        obj.cur_season = st.get("cur_season")
        obj.games_processed = int(st.get("games_processed") or 0)
        return obj


def _season_change(st: NcaaState, season) -> None:
    """The frozen between-season trigger (same for Elo and O/D)."""
    for t in st.elo:
        st.elo[t] = R0 + (st.elo[t] - R0) * (1 - REGRESS)
    for t in st.off:
        st.off[t] *= (1 - REGRESS)
        st.deff[t] *= (1 - REGRESS)


def pregame_features(st: NcaaState, game: dict) -> dict:
    """Pre-game record: p_elo + the 8 frozen features, computed BEFORE any
    update. `game` keys: season, home_id, away_id, home_conference_id,
    away_conference_id, neutral_site, date. (Scores are NOT read here —
    PIT law.)"""
    season_change = st.cur_season is not None and \
        game["season"] != st.cur_season
    eh = st.elo.get(str(game["home_id"]), R0)
    ea = st.elo.get(str(game["away_id"]), R0)
    oh = st.off.get(str(game["home_id"]), 0.0)
    dh = st.deff.get(str(game["home_id"]), 0.0)
    oa = st.off.get(str(game["away_id"]), 0.0)
    da = st.deff.get(str(game["away_id"]), 0.0)
    L = (st.tot_pts / st.tot_tg) if st.tot_tg else L0
    neutral = bool(game.get("neutral_site"))
    adj = 0.0 if neutral else HFA
    p_elo = 1.0 / (1.0 + 10 ** (-(eh - ea + adj) / 400.0))
    hpts = 0.0 if neutral else H_PTS
    pred_h = L + oh + da + hpts
    pred_a = L + oa + dh
    d = _d(game["date"])
    rest_h = 10.0 if str(game["home_id"]) not in st.last_date else \
        min((d - st.last_date[str(game["home_id"])]).days, 30)
    rest_a = 10.0 if str(game["away_id"]) not in st.last_date else \
        min((d - st.last_date[str(game["away_id"])]).days, 30)
    hc, ac = game.get("home_conference_id"), game.get("away_conference_id")
    conf_game = 1.0 if (hc is not None and ac is not None
                        and str(hc) == str(ac)) else 0.0
    return {
        "p_elo": p_elo,
        "elo_diff": (eh + adj) - ea,
        "eff_margin": pred_h - pred_a,
        "net_diff": (oh - dh) - (oa - da),
        "rest_h": float(rest_h), "rest_a": float(rest_a),
        "rest_diff": float(rest_h) - float(rest_a),
        "conf_game": conf_game,
        "neutral": 1.0 if neutral else 0.0,
        "L": L, "season_change": season_change,
        "pred_h": pred_h, "pred_a": pred_a,
    }


def apply_result(st: NcaaState, game: dict, feat: dict | None = None) -> None:
    """The FROZEN post-game updates, in the frozen order. `game` needs
    home_score/away_score. Season-change regression fires BEFORE the game's
    own update when the season rolled (matching walk_forward)."""
    if st.cur_season is not None and game["season"] != st.cur_season:
        _season_change(st, game["season"])
    st.cur_season = game["season"]
    if feat is None:
        feat = pregame_features(st, game)
    home_id, away_id = str(game["home_id"]), str(game["away_id"])
    y = 1 if game["home_score"] > game["away_score"] else 0
    # Elo (home first — the frozen order)
    eh = st.elo.get(home_id, R0)
    ea = st.elo.get(away_id, R0)
    p_elo = feat["p_elo"]
    st.elo[home_id] = eh + K * (y - p_elo)
    st.elo[away_id] = ea + K * ((1 - y) - (1 - p_elo))
    # efficiency
    pred_h, pred_a = feat["pred_h"], feat["pred_a"]
    err_h = game["home_score"] - pred_h
    err_a = game["away_score"] - pred_a
    st.off[home_id] = st.off.get(home_id, 0.0) + A_EFF * err_h
    st.deff[away_id] = st.deff.get(away_id, 0.0) + A_EFF * err_h
    st.off[away_id] = st.off.get(away_id, 0.0) + A_EFF * err_a
    st.deff[home_id] = st.deff.get(home_id, 0.0) + A_EFF * err_a
    # rest + expanding mean
    d = _d(game["date"])
    st.last_date[home_id] = d
    st.last_date[away_id] = d
    st.tot_pts += game["home_score"] + game["away_score"]
    st.tot_tg += 2
    st.games_processed += 1


def replay(games: list[dict]) -> NcaaState:
    """Rebuild the store from raw scores, chronologically. Two independent
    replays MUST produce the same state digest (the anti-leakage check)."""
    st = NcaaState()
    for g in sorted(games, key=lambda g: (_d(g["date"]),
                                          str(g.get("home_id")),
                                          str(g.get("away_id")))):
        feat = pregame_features(st, g)
        apply_result(st, g, feat)
    return st


def feature_vector(feat: dict) -> list[float]:
    return [float(feat[k]) for k in FEATURES]
