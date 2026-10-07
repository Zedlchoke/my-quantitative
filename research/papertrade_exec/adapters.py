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
  The NBA engine path (EXEC-NBA-REWIRE, ERRATUM_NBA_REWIRE.md) is the LAWFUL
  PROSPECTIVE PIT path landed by NBA-WINPROB-PROSPECTIVE-PREP-V1 (Lane D):
  research/papertrade_nba/loader.py + predict.py, byte-pinned package `nba26`.
  It reads ONLY the frozen ESPN per-date payloads (composite pin 3d527b3c…,
  extended post-GO solely via the self-hashed refresh-manifest chain) and
  NEVER the scored cycle's bind corpus (that path is DEAD here — kept as
  documented history in nba_real_corpus_read, never called).
- No network anywhere in this module except espn_fetch_scoreboard(), the
  post-GO-only payload-refresh fetch (same $0 no-auth endpoint lineage as the
  frozen 208 payloads); every rehearsal/test path is frozen-snapshot-only.
  The Odds API capture lives in execute.py behind the core quota-guarded
  client, post-GO only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import importlib
from dataclasses import dataclass, field
from datetime import datetime, timezone, date as _date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from . import (EXIT_BLOCKED_NO_GO, EXIT_BLOCKED_OTHER, EXIT_BLOCKED_TAMPER,
               EXIT_PIN_DRIFT, BlockError, load_pins, load_pinned_package,
               sha256_file)

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


def load_nba_fixtures_window(payloads_dir: Path, start_day_utc: str,
                             end_day_utc: str,
                             *, season_types: tuple[int, ...] | None = None) -> list[Fixture]:
    """Multi-day batch (EXEC-NBA-REWIRE): upcoming fixtures whose UTC TIP date
    lies in [start_day_utc, end_day_utc] (inclusive). Same identity laws as
    `load_nba_fixtures` (real tips; scores never read). Note the per-day
    loader is payload-file-scoped (scoreboard_<date>.json, ESPN schedule-day),
    so this window reads each file in the superset range and then filters by
    tip UTC date, deduped by match_id."""
    out: list[Fixture] = []
    seen: set[str] = set()
    d = _date.fromisoformat(start_day_utc) - timedelta(days=1)
    end = _date.fromisoformat(end_day_utc) + timedelta(days=1)
    while d <= end:
        for f in load_nba_fixtures(payloads_dir, d.isoformat(),
                                   season_types=season_types):
            tip_day = f.kickoff_utc[:10]
            if start_day_utc <= tip_day <= end_day_utc and f.match_id not in seen:
                seen.add(f.match_id)
                out.append(f)
        d += timedelta(days=1)
    out.sort(key=lambda x: (x.kickoff_utc, x.match_id))
    return out


NBA_B1_STAR = {"K": 32, "HCA": 100, "gamma": 0.75}   # quoted frozen constants


def nba_engine_replay_synthetic(harness_root: Path,
                                completed: list[dict], upcoming: list[Fixture]) -> list[dict]:
    """RETAINED FOR THE BATTERY (history law): ratings replay through the
    SCORED harness's own pure functions on SYNTHETIC inputs only (namespace
    SYN*, zero real outcomes). NOT the forecasting engine since EXEC-NBA-REWIRE
    (that is `nba_engine_predict`); kept because the battery's
    law-equivalence/history test exercises it and deleting is riskier."""
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
        state_digest = hashlib.sha256(
            json.dumps({"home": st[f.home]["R"], "away": st[f.away]["R"],
                        "hca": arms.HCA}, sort_keys=True).encode()).hexdigest()
        out.append({"match_id": f.match_id, "p_home": round(p_home, 6),
                    "state_digest": state_digest})
    return out

# The prospective PIT package (Lane D). predict.py does a bare
# `from loader import ...`, so loader.py must be spec-loaded first under the
# exact module name it imports.
NBA26_LOADER_MODULE = "loader"
NBA26_PREDICT_MODULE = "nba26_pit_predict"
NBA_REFRESH_MANIFEST = "REFRESH_MANIFEST.jsonl"
ESPN_SCOREBOARD_URL = ("https://site.api.espn.com/apis/site/v2/sports/"
                       "basketball/nba/scoreboard?dates={day}")


def nba_engine_available(nba26_root: Path) -> Path | None:
    p = Path(nba26_root) / "research" / "papertrade_nba" / "predict.py"
    return p if p.exists() else None


def nba_engine_entry_drift(predict_path: Path) -> str | None:
    """None when every pinned nba26 file matches its pins.json sha256; else a
    human-readable drift reason (BLOCKED_PIN_DRIFT_ENTRY in the probe,
    BLOCKED_PIN_DRIFT in real mode)."""
    files = load_pins().get("packages", {}).get("nba26", {}).get("files", {})
    pkg_dir = Path(predict_path).parent
    for fname in sorted(files):
        want = files[fname].get("sha256")
        if want is None:
            continue
        path = pkg_dir / fname
        if not path.exists():
            return f"nba26/{fname} missing (pin {want[:12]})"
        got = sha256_file(path)
        if got != want:
            return f"nba26/{fname} sha {got[:12]} != pin {want[:12]}"
    return None


def nba_engine_modules(predict_path: Path):
    """Lazy-import Lane D's PIT path (loader.py then predict.py). Raises
    BLOCKED_NBA_ENTRY on absence or contract drift."""
    import importlib.util as _ilu
    pkg_dir = Path(predict_path).parent
    loader_path = pkg_dir / "loader.py"
    if not loader_path.exists():
        raise BlockError("BLOCKED_NBA_ENTRY",
                         f"Lane D loader absent: {loader_path}")
    lmod = sys.modules.get(NBA26_LOADER_MODULE)
    if lmod is None:
        spec = _ilu.spec_from_file_location(NBA26_LOADER_MODULE, loader_path)
        lmod = _ilu.module_from_spec(spec)
        sys.modules[NBA26_LOADER_MODULE] = lmod
        spec.loader.exec_module(lmod)
    pmod = sys.modules.get(NBA26_PREDICT_MODULE)
    if pmod is None:
        spec = _ilu.spec_from_file_location(NBA26_PREDICT_MODULE, predict_path)
        pmod = _ilu.module_from_spec(spec)
        sys.modules[NBA26_PREDICT_MODULE] = pmod
        spec.loader.exec_module(pmod)
    if not hasattr(pmod, "nba26_predict"):
        raise BlockError("BLOCKED_NBA_ENTRY",
                         "predict.py exposes no nba26_predict (contract drift)")
    return lmod, pmod


def _nba_meta_sha(meta_path: Path) -> str | None:
    try:
        txt = meta_path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in txt.splitlines():
        if line.startswith("sha256="):
            return line.split("=", 1)[1].strip()
    return None


def nba_payload_verdict(payloads_dir: Path, frozen_composite: str) -> dict:
    """Manifest-aware frozen-corpus verification (EXEC-NBA-REWIRE).

    Layer 1 (bytes): every scoreboard_*.json re-hashed; a sibling .meta
    record must exist and match (missing/stale meta = tamper, fail-closed).
    Layer 2 (composite): sha256 of the newline-joined per-file sha256 list,
    lexicographic by filename. Equal to the frozen pin -> OK (pristine frozen
    208-file snapshot). Otherwise the appended REFRESH_MANIFEST.jsonl must
    lawfully account for the difference: each record carries a valid
    self-sha, chains prev_composite (first == the frozen pin), and the last
    record's new_composite must equal the recomputed composite. Any other
    state fails closed. Returns {ok, effective_composite, why}.
    """
    base = Path(payloads_dir)
    paths = sorted(base.glob("scoreboard_*.json"))
    if not paths:
        return {"ok": False, "effective_composite": "", "why": "no payloads"}
    shas, why = [], None
    for jp in paths:
        digest = sha256_file(jp)
        mp = jp.with_name(jp.stem + ".meta")
        if not mp.is_file():
            why = why or f"{jp.name}: meta missing"
        elif _nba_meta_sha(mp) != digest:
            why = why or f"{jp.name}: bytes != meta sha"
        shas.append(digest)
    composite = hashlib.sha256("\n".join(shas).encode()).hexdigest()
    if why:
        return {"ok": False, "effective_composite": composite, "why": why}
    if composite == frozen_composite:
        return {"ok": True, "effective_composite": composite, "why": None}
    mf = base / NBA_REFRESH_MANIFEST
    if not mf.is_file():
        return {"ok": False, "effective_composite": composite,
                "why": (f"composite {composite[:12]} != frozen pin "
                        f"{frozen_composite[:12]} and no refresh manifest")}
    try:
        records = [json.loads(line) for line in mf.read_text().splitlines()
                   if line.strip()]
    except json.JSONDecodeError as e:
        return {"ok": False, "effective_composite": composite,
                "why": f"refresh manifest malformed: {e}"}
    expected_prev, last_new = frozen_composite, None
    for rec in records:
        day = rec.get("day", "?")
        body = {k: v for k, v in rec.items() if k != "record_sha256"}
        want = hashlib.sha256(
            json.dumps(body, sort_keys=True).encode()).hexdigest()
        if rec.get("record_sha256") != want:
            return {"ok": False, "effective_composite": composite,
                    "why": f"refresh record {day}: self-sha mismatch"}
        if rec.get("prev_composite") != expected_prev:
            return {"ok": False, "effective_composite": composite,
                    "why": f"refresh record {day}: prev_composite chain break"}
        expected_prev = rec.get("new_composite")
        last_new = rec.get("new_composite")
    if last_new is None or composite != last_new:
        return {"ok": False, "effective_composite": composite,
                "why": ("computed composite != manifest-chained composite "
                        "(unrecorded bytes or tamper)")}
    return {"ok": True, "effective_composite": composite, "why": None}


def nba_engine_predict(payloads_dir: Path, asof_anchor_utc: str, from_utc: str,
                       *, expected_composite_sha: str | None = None,
                       predict_path: Path | None = None) -> list[dict]:
    """Real NBA forecast through Lane D's LAWFUL PIT path (EXEC-NBA-REWIRE).

    Lazy-imports the byte-pinned prospective package (research/papertrade_nba/
    loader.py + predict.py), verifies the frozen payload corpus (bytes-vs-meta
    + composite pin, extended lawfully only via the refresh-manifest chain),
    then load_completed (FINAL, tip STRICTLY < anchor) + load_upcoming
    (SCHEDULED, tip >= from_utc) and nba26_predict under the frozen B1_STAR
    law (K=32/HCA=100/gamma=0.75 quoted; warm-up R0=1500 carried
    pre-registration). NEVER reads the scored cycle's bind corpus.

    Raises: BLOCKED_NBA_ENTRY (entry absent / contract drift),
    BLOCKED_PIN_DRIFT (entry bytes drifted from the pins),
    BLOCKED_NBA_PAYLOAD_TAMPER (corpus verification failed).
    Returns [{match_id, tip_utc, p_home, p_away, state_digest, model_id,
    constants}] — IN-MEMORY ONLY; callers must never persist engine
    probabilities pre-GO (rehearsal rows stay mode=SYNTHETIC).
    """
    if predict_path is None:
        pins = load_pins().get("packages", {}).get("nba26", {})
        wt, pd = pins.get("worktree"), pins.get("pkg_dir")
        if not (wt and pd):
            raise BlockError("BLOCKED_NBA_ENTRY", "nba26 pins absent")
        predict_path = Path(wt) / pd / "predict.py"
    predict_path = Path(predict_path)
    if not predict_path.exists():
        raise BlockError("BLOCKED_NBA_ENTRY",
                         f"Lane D predict entry absent: {predict_path}")
    drift = nba_engine_entry_drift(predict_path)
    if drift:
        raise BlockError("BLOCKED_PIN_DRIFT",
                         f"{drift}; re-pin deliberately before a real run "
                         "trusts it", EXIT_PIN_DRIFT)
    lmod, pmod = nba_engine_modules(predict_path)
    if expected_composite_sha:
        verdict = nba_payload_verdict(Path(payloads_dir),
                                      expected_composite_sha)
        if not verdict["ok"]:
            raise BlockError("BLOCKED_NBA_PAYLOAD_TAMPER",
                             "frozen payload corpus verification failed: "
                             f"{verdict['why']}", EXIT_BLOCKED_TAMPER)
    try:
        lmod.verify_composite(payloads_dir, expected_sha=None, strict=True)
    except Exception as e:                 # CompositeTamperError + friends
        raise BlockError("BLOCKED_NBA_PAYLOAD_TAMPER",
                         "Lane D verify_composite refused the payload dir "
                         f"({type(e).__name__}: {e})", EXIT_BLOCKED_TAMPER)
    completed = lmod.load_completed(payloads_dir, asof_anchor_utc)
    upcoming = lmod.load_upcoming(payloads_dir, from_utc)
    results = pmod.nba26_predict(upcoming, completed, asof_anchor_utc)
    return [dict(r) for r in results]


# ---- post-GO incremental payload refresh (code + manifest plumbing) --------

def nba_refresh_game_days(start_day: str, end_day: str,
                          lookback_days: int = 0) -> list[str]:
    """Inclusive game-day list [start - lookback, end] as YYYYMMDD (pure)."""
    d = _date.fromisoformat(start_day) - timedelta(days=lookback_days)
    end = _date.fromisoformat(end_day)
    out = []
    while d <= end:
        out.append(d.strftime("%Y%m%d"))
        d += timedelta(days=1)
    return out


def espn_fetch_scoreboard(day_yyyymmdd: str) -> bytes:
    """NETWORK — post-GO ONLY (go gate + refresh gate). Same $0 no-auth
    endpoint lineage as the frozen 208 payloads. The rehearsal and the whole
    test battery are frozen-snapshot-only and never call this."""
    import urllib.request
    url = ESPN_SCOREBOARD_URL.format(day=day_yyyymmdd)
    with urllib.request.urlopen(url, timeout=30) as resp:
        if resp.status != 200:
            raise BlockError("BLOCKED_NBA_REFRESH",
                             f"{url} -> HTTP {resp.status}")
        return resp.read()


def _nba_meta_text(url: str, fetched_at: str, blob: bytes) -> str:
    return (f"url={url}\nfetched_at_utc={fetched_at}\n"
            f"bytes={len(blob)}\nsha256={hashlib.sha256(blob).hexdigest()}\n"
            "http_status=200\n")


def nba_incremental_refresh(payloads_dir: Path, start_day: str, end_day: str,
                            *, go_ok: bool, fetch_fn=None,
                            anchor_composite: str | None = None,
                            now_utc: str | None = None,
                            lookback_days: int = 0) -> dict:
    """POST-GO cadence step (EXEC-NBA-REWIRE): fetch per-date ESPN scoreboard
    payloads for the game-days in [start-lookback, end], write bytes + a
    .meta record (frozen format), and append a self-hashed REFRESH_MANIFEST
    record chaining prev_composite -> new_composite so corpus verification
    stays fail-closed (composite == frozen pin OR manifest-chained).

    Defense in depth: refuses BLOCKED_NO_GO unless go_ok is True even though
    the caller is already behind the GO gate; refuses a corpus that does not
    verify BEFORE refreshing (BLOCKED_NBA_PAYLOAD_TAMPER). PRE-GO this is
    never executed — the rehearsal uses the frozen snapshot only and
    documents completed=0 => ratings at R0=1500 (the lawfully correct opening
    state with zero FINAL games)."""
    if not go_ok:
        raise BlockError("BLOCKED_NO_GO",
                         "NBA payload refresh is a post-GO step; refusing "
                         "(rehearsal uses the frozen snapshot)",
                         EXIT_BLOCKED_NO_GO)
    fetch = fetch_fn or espn_fetch_scoreboard
    base = Path(payloads_dir)
    if anchor_composite is None:
        anchor_composite = load_pins().get("data", {})\
            .get("nba_espn_schedule_2026_27", {}).get("composite_sha256")
    verdict = nba_payload_verdict(base, anchor_composite)
    if not verdict["ok"]:
        raise BlockError("BLOCKED_NBA_PAYLOAD_TAMPER",
                         f"corpus must verify BEFORE refresh: {verdict['why']}",
                         EXIT_BLOCKED_TAMPER)
    prev = verdict["effective_composite"]
    now = now_utc or iso_z(datetime.now(timezone.utc))
    applied = []
    for day in nba_refresh_game_days(start_day, end_day, lookback_days):
        blob = fetch(day)
        if not blob:
            raise BlockError("BLOCKED_NBA_REFRESH",
                             f"empty scoreboard payload for {day}")
        url = ESPN_SCOREBOARD_URL.format(day=day)
        jp = base / f"scoreboard_{day}.json"
        old = sha256_file(jp) if jp.exists() else None
        jp.write_bytes(blob)
        (base / f"scoreboard_{day}.meta").write_text(
            _nba_meta_text(url, now, blob))
        shas = [sha256_file(p) for p in sorted(base.glob("scoreboard_*.json"))]
        new = hashlib.sha256("\n".join(shas).encode()).hexdigest()
        rec = {"action": "create" if old is None else "refresh", "day": day,
               "file": jp.name, "old_sha256": old,
               "sha256": hashlib.sha256(blob).hexdigest(),
               "fetched_at_utc": now, "prev_composite": prev,
               "new_composite": new}
        rec["record_sha256"] = hashlib.sha256(
            json.dumps(rec, sort_keys=True).encode()).hexdigest()
        with open(base / NBA_REFRESH_MANIFEST, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        applied.append({"day": day, "action": rec["action"],
                        "new_composite": new})
        prev = new
    return {"fetched": applied, "effective_composite": prev,
            "note": ("pins.json frozen composite deliberately untouched "
                     "(frozen history); verification accepts the manifest "
                     "chain anchored at it")}


def nba_real_corpus_read(harness_root: Path):
    """DEAD / UNREACHABLE since EXEC-NBA-REWIRE (ERRATUM_NBA_REWIRE.md).

    History: the pre-rewire NBA engine path routed real ratings through the
    SCORED cycle's harness corpus, whose outcome-bind law refused this
    cycle's GO (BLOCKED_NBA_CORPUS_BIND — the bind token is mintable only by
    that cycle's own postgo gate; disclosed, never worked around). The rewire
    replaced this path with the prospective PIT path (`nba_engine_predict`);
    no caller reaches this function anymore. Kept as documented history
    because deleting it is the riskier change. Do NOT call."""
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
                         f"DEAD PATH (kept as history): real OOS outcome read "
                         f"refused by the scored cycle's own outcome-bind law "
                         f"({type(e).__name__}: {e}); the NBA engine path no "
                         "longer routes here — see ERRATUM_NBA_REWIRE.md")
    raise BlockError("BLOCKED_NBA_CORPUS_BIND", "unexpected: unmasked read returned")


# ------------------------------------------------------------------- SOCCER --

SOCIER_LEAGUES_NOTE = "sport keys pinned in config.json (start: soccer_uefa_nations_league)"


def soccer_fixtures_from_events(events_payload: bytes | str, sport_key: str,
                                *, snapshot_sha: str = "") -> list[Fixture]:
    """Map a The Odds API /v4/sports/{key}/events payload (0-credit endpoint,
    captured via the core client post-GO) into fixtures. Real path.

    Schema law (verified against the live 2026-10-07 payload): every event
    must be an object carrying non-empty string id/home_team/away_team and a
    parseable UTC commence_time (unknown extra keys are tolerated, required
    keys are not). Any schema drift is BLOCKED_FIXTURES_SCHEMA — loud, never
    silently filtered. Duplicate identity is fail-closed: the same event id
    twice with conflicting fields, or two different ids sharing one
    (commence_time, team-set) slot, refuse the whole payload (1:1 matching
    downstream would otherwise be ambiguous). Exact duplicates collapse.
    """
    events = json.loads(bytes(events_payload).decode())
    if not isinstance(events, list):
        raise BlockError("BLOCKED_FIXTURES_SCHEMA",
                         f"events payload for {sport_key} is not a JSON list",
                         EXIT_BLOCKED_OTHER)
    out: list[Fixture] = []
    by_id: dict[str, Fixture] = {}
    by_slot: dict[tuple[str, frozenset], str] = {}
    for ev in events:
        if not isinstance(ev, dict):
            raise BlockError("BLOCKED_FIXTURES_SCHEMA",
                             f"events payload for {sport_key} has a "
                             f"non-object entry: {type(ev).__name__}",
                             EXIT_BLOCKED_OTHER)
        missing = [k for k in ("id", "home_team", "away_team", "commence_time")
                   if not isinstance(ev.get(k), str) or not ev.get(k, "").strip()]
        if missing:
            raise BlockError("BLOCKED_FIXTURES_SCHEMA",
                             f"events payload for {sport_key}: entry "
                             f"{ev.get('id', '?')!r} missing/invalid fields "
                             f"{missing} (provider schema drift); fail-closed",
                             EXIT_BLOCKED_OTHER)
        try:
            raw = ev["commence_time"]
            tip = parse_tip(raw.replace("+00:00", "Z")
                            if not raw.endswith("Z") else raw)
        except (ValueError, TypeError) as e:
            raise BlockError("BLOCKED_FIXTURES_SCHEMA",
                             f"events payload for {sport_key}: event "
                             f"{ev['id']!r} commence_time "
                             f"{ev['commence_time']!r} unparseable: {e}",
                             EXIT_BLOCKED_OTHER)
        fx = Fixture(
            league="SOCCER", match_id=ev["id"],
            home=ev["home_team"], away=ev["away_team"], kickoff_utc=iso_z(tip),
            competition=sport_key, et_local_date=et_local_date(tip),
            source_ref=(f"the_odds_api/events/{sport_key}"
                        + (f"@{snapshot_sha[:12]}" if snapshot_sha else "")
                        + f"#{ev['id']}"))
        prior = by_id.get(fx.match_id)
        if prior is not None:
            if (prior.home, prior.away, prior.kickoff_utc) != \
                    (fx.home, fx.away, fx.kickoff_utc):
                raise BlockError(
                    "BLOCKED_FIXTURES_DUPLICATE",
                    f"event id {fx.match_id} appears twice with conflicting "
                    "identity (provider payload drift); fail-closed",
                    EXIT_BLOCKED_OTHER)
            continue                      # exact duplicate echo collapses
        slot = (fx.kickoff_utc, frozenset({norm(fx.home), norm(fx.away)}))
        other = by_slot.get(slot)
        if other is not None:
            raise BlockError(
                "BLOCKED_FIXTURES_DUPLICATE",
                f"events {other} and {fx.match_id} share one (commence_time, "
                "team-set) slot; 1:1 matching would be ambiguous; fail-closed",
                EXIT_BLOCKED_OTHER)
        by_id[fx.match_id] = fx
        by_slot[slot] = fx.match_id
        out.append(fx)
    out.sort(key=lambda x: (x.kickoff_utc, x.match_id))
    return out


def norm(s: str) -> str:
    """Fixture-slot normalization (whitespace/case only — never fuzzy)."""
    return " ".join(str(s).split()).strip().casefold()


def soccer_engine_module(replay_path: Path):
    """Lazy-import Lane C's pinned replay module (the same import
    `soccer_engine_replay` performs) and return it with the contract symbol
    checked. Raises BlockError(BLOCKED_SOCCER_ENTRY) on absence/drift."""
    if not Path(replay_path).exists():
        raise BlockError("BLOCKED_SOCCER_ENTRY",
                         f"Lane C replay entry absent: {replay_path}")
    pkg_dir = Path(replay_path).parent
    import importlib.util as _ilu
    spec_pkg = _ilu.spec_from_file_location(
        "soccer_prep_pkg", pkg_dir / "__init__.py",
        submodule_search_locations=[str(pkg_dir)])
    pkg_mod = _ilu.module_from_spec(spec_pkg)
    sys.modules["soccer_prep_pkg"] = pkg_mod
    spec_pkg.loader.exec_module(pkg_mod)
    import importlib as _imp
    mod = _imp.import_module("soccer_prep_pkg.replay")   # keeps `from . import` working
    if getattr(mod, "soccer_b1_replay", None) is None:
        raise BlockError("BLOCKED_SOCCER_ENTRY",
                         "replay.py landed but exposes no soccer_b1_replay "
                         "(contract drift)")
    return mod


def soccer_extension_crosswalk(replay_path: Path, extension_path: Path):
    """Freeze-anchored crosswalk extension law (FREEZE_SKELETON §5 of
    SOCCER-INTL-WINPROB-PROSPECTIVE-PREP-V1: "extend the 8-pair seed
    empirically from real payloads; fail-closed until then").

    The pinned engine resolves provider names ONLY through the seed file that
    sits next to replay.py in the READ-ONLY prep worktree, so growth lands in
    THIS cycle's own extension file. Fail-closed chain, verified on every
    real run, before the engine is touched:
      1. extension sha256 == this cycle's pins.json data pin;
      2. extension bytes START WITH the pinned seed's exact bytes (the frozen
         8-pair anchor is a strict byte prefix — the extension can only
         append, never rewrite or shrink the seed);
      3. the pinned engine's own load_provider_crosswalk accepts the
         extension (header law, ambiguity law, 8-pair floor all still run).
    On success the replay module's crosswalk path is pointed at the extension
    for this process, so `soccer_b1_replay` itself resolves through the same
    verified mapping. Returns (module, mapping)."""
    mod = soccer_engine_module(replay_path)
    ext_path = Path(extension_path)
    if not ext_path.exists():
        raise BlockError("BLOCKED_PIN_DRIFT",
                         f"crosswalk extension missing: {ext_path}", EXIT_PIN_DRIFT)
    pin = load_pins().get("data", {}).get("soccer_crosswalk_extension_csv", {})
    got = sha256_file(ext_path)
    if not pin.get("sha256") or got != pin["sha256"]:
        raise BlockError("BLOCKED_PIN_DRIFT",
                         f"crosswalk extension sha {got[:12]} != pin "
                         f"{str(pin.get('sha256'))[:12]}; re-pin deliberately "
                         "with evidence before a real run trusts it",
                         EXIT_PIN_DRIFT)
    seed_bytes = Path(mod._PROVIDER_CROSSWALK_PATH).read_bytes()
    ext_bytes = ext_path.read_bytes()
    if not ext_bytes.startswith(seed_bytes):
        raise BlockError("BLOCKED_PIN_DRIFT",
                         "crosswalk extension does not extend the pinned "
                         "seed verbatim (frozen 8-pair anchor must be a "
                         "strict byte prefix); fail-closed", EXIT_PIN_DRIFT)
    mapping = mod.load_provider_crosswalk(ext_path)   # engine's own laws
    mod._PROVIDER_CROSSWALK_PATH = ext_path           # engine resolves the
    return mod, mapping                               # same verified mapping


def soccer_crosswalk_split(mod, mapping: dict,
                           fixtures: list) -> tuple[list, list]:
    """Per-fixture crosswalk pre-resolution (fail-closed, never fuzzy).
    Returns (resolvable, missed) where missed carries (fixture, reason) with
    the exact unresolved provider name — the caller journals them NOT_RUN;
    they never reach the engine (one miss would otherwise kill the batch)."""
    resolvable, missed = [], []
    for f in fixtures:
        try:
            mod.resolve_provider_name(f.home, mapping)
            mod.resolve_provider_name(f.away, mapping)
        except Exception as e:            # CrosswalkMissError / validation
            missed.append((f, f"{type(e).__name__}: {e}"))
            continue
        resolvable.append(f)
    return resolvable, missed


def soccer_engine_available(soccer_root: Path) -> Path | None:
    p = Path(soccer_root) / "research" / "papertrade_soccer" / "replay.py"
    return p if p.exists() else None


def soccer_engine_replay(replay_path: Path, fixtures: list[Fixture],
                         corpus_csv: Path, asof_date: str) -> list[dict]:
    """Lazy-import Lane C's `soccer_b1_replay(fixtures, corpus_csv, asof_date)`.
    Raises BlockError(BLOCKED_SOCCER_ENTRY) when absent (caller falls back)."""
    mod = soccer_engine_module(replay_path)
    fx = [{"match_id": f.match_id, "kickoff_utc": f.kickoff_utc,
           "home_team": f.home, "away_team": f.away, "neutral": False,
           "match_date_local": f.kickoff_utc[:10]} for f in fixtures]
    return mod.soccer_b1_replay(fx, str(corpus_csv), asof_date)


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
