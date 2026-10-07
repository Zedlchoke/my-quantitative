"""Per-league adapters for the exec runner — real fixture pipelines + lazy
engine imports with labeled synthetic fallbacks.

LAWS
- Fixture identity (teams, tips, kickoffs) comes from the PINNED REAL snapshots
  (WNBA schedule CSV; NBA ESPN per-date payloads). Probabilities are NEVER
  computed and never stored pre-GO: the rehearsal path uses the SYNTHETIC
  fallback adapters and every FORECAST/MARKET_QUOTE row produced by them is
  labeled mode=SYNTHETIC with a source_ref that says SYNTHETIC.
- Engines are lazy-imported from the sibling worktrees by byte-pinned paths.
  Missing entry files (Lane B/C concurrency) surface BLOCKED_WNBA_ENTRY /
  BLOCKED_SOCCER_ENTRY and the clearly-labeled synthetic fallback runs instead.
  The NBA engine path is wired to the scored harness pure functions (Stream /
  ArmConfig / sigmoid / Game); its REAL completed-game corpus read is
  outcome-bind-token-gated by that cycle's own law and therefore refuses here
  (BLOCKED_NBA_CORPUS_BIND) — disclosed, fail-closed, never worked around.
- No network anywhere in this module. The Odds API capture lives in execute.py
  behind the core quota-guarded client, post-GO only.
"""
from __future__ import annotations

import csv
import json
import sys
import importlib
from dataclasses import dataclass, field
from datetime import datetime, timezone, date as _date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from . import BlockError, load_pinned_package, sha256_file

ET = ZoneInfo("America/New_York")


def parse_tip(raw: str) -> datetime:
    """ESPN/odds-style tip strings: '2026-10-15T23:30Z' or '...T23:30:00Z'."""
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1]
    if len(s) == 16:                       # YYYY-MM-DDTHH:MM
        s += ":00"
    dt = datetime.fromisoformat(s)
    return dt.replace(tzinfo=timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def et_local_date(tip: datetime) -> str:
    return tip.astimezone(ET).date().isoformat()


@dataclass
class Fixture:
    league: str
    match_id: str
    home: str
    away: str
    kickoff_utc: str                       # ...Z, seconds precision
    competition: str
    et_local_date: str
    source_ref: str
    note: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def kickoff_dt(self) -> datetime:
        return parse_tip(self.kickoff_utc)


# --------------------------------------------------------------------- WNBA --

def load_wnba_fixtures(schedule_csv: Path, day_utc: str) -> list[Fixture]:
    """Remaining 2026 WNBA playoff games whose UTC tip falls on `day_utc`.

    Census law (FREEZE_PACKET §5): season==2026, season_type==3 (POST),
    status not completed, ALLSTAR excluded by the exhibition law. Tips are the
    snapshot's real ESPN tips; canonicalized to seconds-precision UTC.
    """
    out = []
    with open(schedule_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("season") != "2026" or r.get("season_type") != "3":
                continue
            if str(r.get("status_type_completed", "")).lower() == "true":
                continue
            if r.get("type_abbreviation") == "ALLSTAR":
                continue
            tip = parse_tip(r["date"])
            if tip.strftime("%Y-%m-%d") != day_utc:
                continue
            home, away = r.get("home_abbreviation") or "TBD", \
                r.get("away_abbreviation") or "TBD"
            out.append(Fixture(
                league="WNBA", match_id=str(r["id"]), home=home, away=away,
                kickoff_utc=iso_z(tip), competition=r.get("type_abbreviation", ""),
                et_local_date=et_local_date(tip),
                source_ref=f"wnba_schedule_2026.csv#{r['id']}",
                note=r.get("notes_headline", "")))
    out.sort(key=lambda x: (x.kickoff_utc, x.match_id))
    return out


def wnba_completed_rows(schedule_csv: Path) -> list[dict]:
    """Completed 2026 games (HISTORY — stream warm-up inputs for the engine,
    never scored rows). Rows carry the schedule-schema score fields."""
    rows = []
    with open(schedule_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("season") != "2026":
                continue
            if str(r.get("status_type_completed", "")).lower() != "true":
                continue
            if r.get("type_abbreviation") == "ALLSTAR":
                continue
            rows.append(r)
    return rows


def wnba_census(schedule_csv: Path) -> list[dict]:
    """The 15-game remaining census with per-game anchors (tip-6h10m), for
    plan evidence; must match FREEZE_PACKET §5."""
    seen = {}
    with open(schedule_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("season") != "2026" or r.get("season_type") != "3":
                continue
            if str(r.get("status_type_completed", "")).lower() == "true":
                continue
            if r.get("type_abbreviation") == "ALLSTAR":
                continue
            tip = parse_tip(r["date"])
            seen[r["id"]] = {
                "game_id": r["id"], "tip_utc": iso_z(tip),
                "et_local_date": et_local_date(tip),
                "matchup": f"{r.get('away_abbreviation') or 'TBD'} @ "
                           f"{r.get('home_abbreviation') or 'TBD'}",
                "per_game_anchor_utc": iso_z(tip - timedelta(seconds=6 * 3600 + 600)),
            }
    return [seen[k] for k in sorted(seen, key=lambda g: seen[g]["tip_utc"])]


def wnba_raw_upcoming(schedule_csv: Path, day_utc: str) -> list[dict]:
    """Raw pinned-snapshot rows for the day's remaining games (the exact
    schema Lane B's prediction entry consumes: id/date/season/home_id/away_id/
    *_abbreviation/neutral_site/status_type_name/scores)."""
    out = []
    with open(schedule_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("season") != "2026" or r.get("season_type") != "3":
                continue
            if str(r.get("status_type_completed", "")).lower() == "true":
                continue
            if r.get("type_abbreviation") == "ALLSTAR":
                continue
            if parse_tip(r["date"]).strftime("%Y-%m-%d") != day_utc:
                continue
            out.append(r)
    out.sort(key=lambda r: (r["date"], r["id"]))
    return out


def wnba_engine_available(wnba_root: Path) -> Path | None:
    p = Path(wnba_root) / "research" / "papertrade_wnba26" / "predict.py"
    return p if p.exists() else None


def wnba_engine_predict(predict_path: Path, completed_rows: list[dict],
                        upcoming_raw_rows: list[dict]) -> list[dict]:
    """Lazy-import Lane B's prediction entry (research/papertrade_wnba26/
    predict.py) and call the pinned contract — dispatch name
    `predict_matches(completed_rows, upcoming)`; Lane B's landed 2026-10-07
    entry is `wnba26_predict` with the same signature and return shape, so
    both names are accepted. Returns
    [{match_id, p_home, p_away, state_digest}].
    Raises BlockError(BLOCKED_WNBA_ENTRY) if the entry file or symbol is
    absent at run time (caller falls back to the labeled synthetic adapter)."""
    if not predict_path.exists():
        raise BlockError("BLOCKED_WNBA_ENTRY",
                         f"Lane B predict entry absent: {predict_path}")
    pkg_dir = predict_path.parent
    mod_name = "wnba26_predict_mod"
    import importlib.util as _ilu
    spec_pkg = _ilu.spec_from_file_location(
        "wnba26_pkg", pkg_dir / "__init__.py",
        submodule_search_locations=[str(pkg_dir)])
    pkg_mod = _ilu.module_from_spec(spec_pkg)
    sys.modules["wnba26_pkg"] = pkg_mod
    spec_pkg.loader.exec_module(pkg_mod)
    spec = _ilu.spec_from_file_location(mod_name, predict_path)
    mod = _ilu.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    entry = getattr(mod, "predict_matches", None) or \
        getattr(mod, "wnba26_predict", None)
    if entry is None:
        raise BlockError("BLOCKED_WNBA_ENTRY",
                         "predict.py landed but exposes neither predict_matches "
                         "nor wnba26_predict (contract drift)")
    results = entry(completed_rows, upcoming_raw_rows)
    out = []
    for r in results:
        item = {"match_id": r["match_id"], "p_home": float(r["p_home"]),
                "p_away": float(r["p_away"])}
        if "state_digest" in r:
            item["state_digest"] = r["state_digest"]
        out.append(item)
    return out


# ---------------------------------------------------------------------- NBA --

def load_nba_fixtures(payloads_dir: Path, day_utc: str,
                      *, season_types: tuple[int, ...] | None = None) -> list[Fixture]:
    """Upcoming NBA fixtures for `day_utc` from the pinned per-date ESPN
    scoreboard payloads (208 dates, 2026-10-15..2027-05-10). Tips are real;
    scores are never read (outcome-masked by construction: the loader only
    touches team/date/status fields)."""
    path = Path(payloads_dir) / f"scoreboard_{day_utc.replace('-', '')}.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    out = []
    for ev in data.get("events", []):
        comp = ev["competitions"][0]
        season = ev.get("season") or {}
        stype = int(season.get("type", 0))
        if season_types is not None and stype not in season_types:
            continue
        if ev["status"]["type"].get("state") not in ("pre",):
            continue  # started/finished games are not plannable (anchor passed)
        home = away = None
        for c in comp["competitors"]:
            if c["homeAway"] == "home":
                home = c["team"]["displayName"]
            else:
                away = c["team"]["displayName"]
        tip = parse_tip(ev["date"])
        out.append(Fixture(
            league="NBA", match_id=str(ev["id"]), home=home or "?", away=away or "?",
            kickoff_utc=iso_z(tip), competition=season.get("slug", ""),
            et_local_date=et_local_date(tip),
            source_ref=f"espn_schedule_2026_27/scoreboard_{day_utc.replace('-', '')}.json"
                       f"#{ev['id']}",
            extra={"season_type": stype}))
    out.sort(key=lambda x: (x.kickoff_utc, x.match_id))
    return out


NBA_B1_STAR = {"K": 32, "HCA": 100, "gamma": 0.75}


def nba_engine_replay_synthetic(harness_root: Path,
                                completed: list[dict], upcoming: list[Fixture]) -> list[dict]:
    """Ratings replay through the SCORED harness's own pure functions.

    `completed` are schedule-schema dicts (SYNTHETIC inputs here — namespace
    SYN*, zero real outcomes). Games are canonicalized by the harness's own
    `canonicalize`, replayed with its own `Stream(ArmConfig('B1_STAR'))`
    (K=32/HCA=100/gamma=0.75 frozen), and upcoming fixtures are predicted from
    the final rating state via the harness's `sigmoid` + season-boundary law —
    the same identity the scored cycle verified. Returns
    [{match_id, p_home, state_digest}].
    """
    import importlib.util as _ilu
    parent = Path(harness_root).parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    arms = importlib.import_module("harness.arms")
    gu = importlib.import_module("harness.game_universe")
    games = []
    for r in completed:
        tip, ld = gu.canonicalize(r["game_date_time"])
        games.append(gu.Game(
            game_id=str(r["game_id"]), season=int(r["season"]),
            season_type=int(r["season_type"]), tip_utc=tip, local_date=ld,
            home=r["home"], away=r["away"],
            home_score=int(r["home_score"]), away_score=int(r["away_score"]),
            neutral_site=False, has_pbp=True,
            venue=(0.0, 0.0), venue_tz_offset_hours=-5))
    stream = arms.Stream(games, arms.ArmConfig("B1_STAR"))
    stream.run()
    st = stream.final_state
    out = []
    for f in upcoming:
        upcoming_season = 2027  # ending-year key of the 2026-27 season
        stream.boundary(st, f.home, upcoming_season)
        stream.boundary(st, f.away, upcoming_season)
        p_home = arms.sigmoid((st[f.home]["R"] - st[f.away]["R"] + arms.HCA) / arms.S)
        state_digest = __import__("hashlib").sha256(
            json.dumps({"home": st[f.home]["R"], "away": st[f.away]["R"],
                        "hca": arms.HCA}, sort_keys=True).encode()).hexdigest()
        out.append({"match_id": f.match_id, "p_home": round(p_home, 6),
                    "state_digest": state_digest})
    return out


def nba_real_corpus_read(harness_root: Path):
    """Post-GO real ratings input. The scored cycle's law gates unmasked real
    outcomes behind ITS outcome-bind token (minted only by its postgo.py after
    its own owner-GO check). This cycle's GO is a different phrase, so the
    read refuses — fail-closed, disclosed. Never worked around here."""
    load_pinned_package("nba_harness_probe", "nba_harness")
    import importlib.util as _ilu
    parent = Path(harness_root).parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    rl = importlib.import_module("harness.real_loader")
    try:
        rl.load_oos_corpus(mask_outcomes=False, outcome_bind_token=None)
    except Exception as e:                     # OutcomeBindRefused expected
        raise BlockError("BLOCKED_NBA_CORPUS_BIND",
                         f"real OOS outcome read refused by the scored cycle's own "
                         f"outcome-bind law ({type(e).__name__}: {e}); this cycle's "
                         "GO does not mint that token — owner decision required")
    raise BlockError("BLOCKED_NBA_CORPUS_BIND", "unexpected: unmasked read returned")


# ------------------------------------------------------------------- SOCCER --

SOCIER_LEAGUES_NOTE = "sport keys pinned in config.json (start: soccer_uefa_nations_league)"


def soccer_fixtures_from_events(events_payload: bytes | str, sport_key: str) -> list[Fixture]:
    """Map a The Odds API /v4/sports/{key}/events payload (0-credit endpoint,
    captured via the core client post-GO) into fixtures. Real path."""
    events = json.loads(bytes(events_payload).decode())
    out = []
    for ev in events:
        tip = parse_tip(ev["commence_time"].replace("+00:00", "Z")
                        if not ev["commence_time"].endswith("Z") else ev["commence_time"])
        out.append(Fixture(
            league="SOCCER", match_id=str(ev["id"]),
            home=ev["home_team"], away=ev["away_team"], kickoff_utc=iso_z(tip),
            competition=sport_key, et_local_date=et_local_date(tip),
            source_ref=f"the_odds_api/events/{sport_key}#{ev['id']}"))
    out.sort(key=lambda x: (x.kickoff_utc, x.match_id))
    return out


def soccer_engine_available(soccer_root: Path) -> Path | None:
    p = Path(soccer_root) / "research" / "papertrade_soccer" / "replay.py"
    return p if p.exists() else None


def soccer_engine_replay(replay_path: Path, fixtures: list[Fixture],
                         corpus_csv: Path, asof_date: str) -> list[dict]:
    """Lazy-import Lane C's `soccer_b1_replay(fixtures, corpus_csv, asof_date)`.
    Raises BlockError(BLOCKED_SOCCER_ENTRY) when absent (caller falls back)."""
    if not replay_path.exists():
        raise BlockError("BLOCKED_SOCCER_ENTRY",
                         f"Lane C replay entry absent: {replay_path}")
    pkg_dir = replay_path.parent
    import importlib.util as _ilu
    spec_pkg = _ilu.spec_from_file_location(
        "soccer_prep_pkg", pkg_dir / "__init__.py",
        submodule_search_locations=[str(pkg_dir)])
    pkg_mod = _ilu.module_from_spec(spec_pkg)
    sys.modules["soccer_prep_pkg"] = pkg_mod
    spec_pkg.loader.exec_module(pkg_mod)
    import importlib as _imp
    mod = _imp.import_module("soccer_prep_pkg.replay")   # keeps `from . import` working
    entry = getattr(mod, "soccer_b1_replay", None)
    if entry is None:
        raise BlockError("BLOCKED_SOCCER_ENTRY",
                         "replay.py landed but exposes no soccer_b1_replay "
                         "(contract drift)")
    fx = [{"match_id": f.match_id, "kickoff_utc": f.kickoff_utc,
           "home_team": f.home, "away_team": f.away, "neutral": False,
           "match_date_local": f.kickoff_utc[:10]} for f in fixtures]
    return entry(fx, str(corpus_csv), asof_date)


# ------------------------------------------------------- synthetic fallbacks --

def _stable_int(s: str, mod: int) -> int:
    import hashlib
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16) % mod


def synthetic_two_way_p(match_id: str) -> dict:
    """Deterministic synthetic p (labeled SYNTHETIC everywhere it lands)."""
    p_home = round(0.55 + _stable_int(match_id, 200) / 1000.0, 6)
    return {"HOME": p_home, "AWAY": round(1.0 - p_home, 6)}


def synthetic_three_way_p(match_id: str) -> dict:
    h = _stable_int(match_id, 400) / 1000.0
    p_home = round(0.35 + h * 0.30, 6)
    p_draw = round(0.22 + (_stable_int(match_id + "d", 100) / 1000.0) * 0.10, 6)
    return {"HOME": p_home, "DRAW": p_draw, "AWAY": round(1.0 - p_home - p_draw, 6)}


def synthetic_odds(match_id: str, p: dict) -> dict:
    """Deterministic synthetic book (labeled SYNTHETIC wherever it lands).

    Geometry stays inside the core risk law's quote band (implied sum in
    [0.999, 1.20], every d > 1.0). Every 3rd match (stable hash) carries a
    deliberately mispriced HOME leg (implied_home = p/1.08 => EV_net 0.06 >=
    0.05 -> BET_PAPER path); the rest are fair-ish (best EV ~ -0.02 -> NO_EDGE
    path). Both decision paths get deterministic coverage."""
    legs = list(p)
    boosted = _stable_int(match_id + "boost", 3) == 0
    implied = {}
    for k in legs:
        implied[k] = p[k] / 1.08 if (k == "HOME" and boosted) else 0.0
    rest = [k for k in legs if implied[k] == 0.0]
    rest_mass = max(0.02, 1.01 - sum(implied.values()))
    rest_p = sum(p[k] for k in rest) or 1.0
    for k in rest:
        implied[k] = rest_mass * p[k] / rest_p
    return {k: round(min(50.0, max(1.01, 1.0 / implied[k])), 3) for k in legs}
