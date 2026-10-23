"""SPORTS-PAPERTRADE-EXEC-V1 production runner (pre-GO build; GO is the
owner's alone: `GO SPORTS PAPERTRADE EXEC V1 RUN ALL`).

Subcommands
  plan --date D [--league L]        read-only fixtures + anchors + eligibility
  forecast --league L --date D      gated; FORECAST rows; refuses at/after
                                    anchor; idempotent
  quote --league L --date D         gated; quota-guarded capture (real) or
                                    labeled synthetic capture (sandbox)
  decide --league L --date D        gated; crosswalk 1:1 fail-closed; EV per
                                    core risk law; in-lock append
  run-day --date D                  chain all three leagues
  settle --league L --date D --results FILE   refunds on cancel/postpone
  dashboard [--league]              core dashboard.build (SANDBOX banner when
                                    sandbox genesis)
  verify-pins [--expect-head SHA]   byte pins (blocking) + HEAD check
  key-check [--key-path P]          key hygiene probe (BLOCKED_KEY on failure)

GO gate (`exec_go_state`, this package — NOT the sibling cycle's go_gate path):
GO_TOKEN.json in research/control/SPORTS-PAPERTRADE-EXEC-V1/ whose
go_phrase_typed_by_owner EQUALS the registered phrase verbatim, AND this
cycle's registry row phase containing GO_CONSUMED. Missing/wrong either =>
BLOCKED_NO_GO, fail-closed, nothing written.

--sandbox switches mutation commands to a SANDBOX ledger + SANDBOX control
copies (the gate code path is identical); real mode always uses the worktree
control dir + real registry. `--now` (deterministic rehearsal clock) and the
source-root overrides are accepted in sandbox mode ONLY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if __package__ in (None, ""):                       # direct-script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from research.papertrade_exec import (  # noqa: E402
    BATCH_LEAD_SECONDS, CONTROL_DIR, CONTROL_DIR_NAME, DEFAULT_DATA_ROOT,
    EXIT_BLOCKED_ANCHOR, EXIT_BLOCKED_KEY, EXIT_BLOCKED_NO_GO, EXIT_BLOCKED_OTHER,
    EXIT_BLOCKED_TAMPER, EXIT_HEAD_DRIFT, EXIT_OK, EXIT_PIN_DRIFT, GO_PHRASE,
    LEAGUES, REGISTRY_PATH, SOCCER_LEAD_SECONDS,
    BlockError, load_pins, nba_payload_composite, sha256_file, verify_pins)
from research.papertrade_exec import laws                            # noqa: E402
from research.papertrade_exec import adapters as A                    # noqa: E402

PINNED_ROOTS = {
    "paper_core_root": Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                            "sports-papertrade-v1/integration/research/papertrade"),
    "wnba26_root": Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                        "wnba-2026-remainder-v1/integration"),
    "nba_harness_root": Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                             "nba-winprob-ng-scored-v1/integration/research/control/"
                             "NBA-WINPROB-NG-SCORED-V1/harness"),
    "nba26_root": Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                       "nba-winprob-prospective-prep-v1/integration"),
    "soccer_root": Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                        "soccer-intl-winprob-prospective-prep-v1/integration"),
}
PINNED_DATA = {
    "wnba_schedule": Path("~/.my-quantitative-data/wnba-2026-remainder-v1/"
                          "refresh_20261007/wnba_schedule_2026.csv").expanduser(),
    "nba_payloads": Path("~/.my-quantitative-data/nba-winprob-prospective-prep-v1/"
                         "espn_schedule_2026_27").expanduser(),
    "soccer_corpus": Path("~/.my-quantitative-data/soccer-intl-winprob-prospective-"
                          "prep-v1/corpus/results.csv").expanduser(),
}
DEFAULT_SPORT_KEYS = {"NBA": "basketball_nba", "WNBA": "basketball_wnba",
                      "SOCCER": "soccer_uefa_nations_league"}

# --- CAPITAL LAW V3 (SPORTS-PAPERTRADE-CAPITAL-V3; plan §1–§5) ---------------
# The v3 path is DEAD CODE until BOTH (a) config.json carries
# capital_law={"version":3,"effective_utc":...} AND (b) the cycle registry
# row SPORTS-PAPERTRADE-CAPITAL-V3 records go_phrase_state OWNER_GO_TYPED_LIVE.
# Absent/malformed either side => v2 behavior byte-for-byte (a pre-GO
# crash/restart is indistinguishable from the pre-v3 program).

CAPITAL_V3_CYCLE_ID = "SPORTS-PAPERTRADE-CAPITAL-V3"


def _capital_v3_registry_path(args) -> Path:
    """Mirror of require_gate's registry resolution (sandbox fixture vs the
    worktree's plans/CYCLE_REGISTRY.json via REGISTRY_PATH)."""
    if getattr(args, "sandbox", False):
        return Path(args.sandbox_registry)
    return REGISTRY_PATH


def capital_law_for(args, core, config: dict | None = None) -> int:
    """2|3 resolution for a decision pass. Registry row extraction mirrors
    exec_go_state (cycles dict-or-list); the config half and the decision are
    the PINNED CORE's own capital_law_version() — fail-closed to 2."""
    row = {}
    try:
        reg = json.loads(_capital_v3_registry_path(args).read_text())
        cycles = reg.get("cycles", reg)
        if isinstance(cycles, dict):
            row = cycles.get(CAPITAL_V3_CYCLE_ID) or {}
        else:
            row = next((c for c in cycles
                        if c.get("cycle_id") == CAPITAL_V3_CYCLE_ID), {})
    except Exception:                     # absent/malformed registry => v2
        row = {}
    cfg = load_config() if config is None else config
    return core.capital_law_version(cfg, row)


def league_paused(league: str) -> dict | None:
    """QD1 (A7-M2): a league under an owner pause refuses NEW decisions —
    settle and dashboard keep running. Returns the pause record or None.
    A MALFORMED league_pauses table fails CLOSED (treated as paused with
    an explicit reason) — an unreadable owner law never silently re-opens
    betting (A7-R1)."""
    try:
        table = load_config().get("league_pauses")
        if table is None:
            return None
        if not isinstance(table, dict):
            return {"active": True,
                    "reason": "league_pauses config MALFORMED (not an "
                              "object) — fail-closed pause (A7-R1)"}
        entry = table.get(league)
        if not isinstance(entry, dict):
            return None
        if entry.get("active") is True:
            return entry
        if "active" not in entry:
            return {"active": True,
                    "reason": f"league_pauses[{league}] missing 'active' "
                              "— fail-closed pause (A7-R1)"}
        return None
    except Exception:
        return {"active": True,
                "reason": "league_pauses config unreadable — fail-closed "
                          "pause (A7-R1)"}


def ncaa_configured(league: str) -> bool:
    """W5.1: an NCAA lane joins the runner ONLY when config registers its
    sport_keys entry (NCAA-M / NCAA-W — the WSL activation pattern)."""
    try:
        return league in (load_config().get("sport_keys") or {})
    except Exception:
        return False


def ncaa_leagues_configured() -> list[str]:
    from research.papertrade_exec import NCAA_LEAGUES
    return [lg for lg in NCAA_LEAGUES if ncaa_configured(lg)]


def wsl_configured() -> bool:
    """CAPITAL-V3 §4 gating: WSL joins the runner ONLY when config.json
    registers sport_keys.WSL (the config template is never auto-applied; the
    live config commit is a post-GO controller act)."""
    try:
        return "WSL" in (load_config().get("sport_keys") or {})
    except Exception:
        return False



# Gamma's verified WSL tag (the broad open-events offset scan provably misses
# live WSL games — measured and fixed for the watcher 2026-10-14, verified ON
# Gamma event 1167584 = Arsenal WFC v Birmingham City WFC). The lane's quote
# wiring therefore scans the TAG completely; every page is journaled and
# pinned append-only through the pinned source's own GET plumbing.
WSL_GAMMA_TAG_ID = "105959"


def _wire_wsl_real_quote(args) -> None:
    """CAPITAL-V3 §4.3 REAL quote plumbing for the WSL lane (the missing
    piece the first WSL quote incident exposed as BLOCKED_NO_QUOTE_PLUMBING):
    in real mode the RUNNER fetches the WSL-tagged Gamma events completely
    and binds a books_provider — both through the byte-pinned polymarket_
    source's own journaled + append-only snapshot GETs (raw body, url,
    retrieval UTC, sha256 pinned BEFORE parsing). The lane module and its
    laws stay untouched; this is the runner-side call-site wiring only.
    Sandbox mode returns untouched (the battery injects synthetic books via
    the same seam attributes)."""
    if getattr(args, "sandbox", False):
        return
    import urllib.parse
    from research.papertrade_exec import wsl_lane
    pm = wsl_lane.load_pm_source()
    run = f"wsl_lane_{now_utc_real().replace(':', '')}"

    def books_provider(fixture, join, leg):
        token = join["legs"][leg]["token_id_yes"]
        body, _ent = pm.http_get_json(
            f"{pm.CLOB_BOOK_URL}?{urllib.parse.urlencode({'token_id': token})}",
            now=now_utc_real(), journal_run=run,
            snapshot_kind="clob_books",
            snapshot_name=f"wsl_{join['event_id']}_{leg}")
        book = body if isinstance(body, dict) else {}
        asks = book.get("asks") or []
        return asks, str(book.get("hash")), hashlib.sha256(
            json.dumps(book, sort_keys=True).encode()).hexdigest()

    events = []
    for page in range(30):                     # full tagged scan (offset law)
        q = urllib.parse.urlencode({
            "tag_id": WSL_GAMMA_TAG_ID, "closed": "false", "limit": "100",
            "offset": str(page * 100), "end_date_min": now_utc_real()})
        url = f"https://gamma-api.polymarket.com/events?{q}"
        body, _ent = pm.http_get_json(
            url, now=now_utc_real(), journal_run=run,
            snapshot_kind="gamma_events",
            snapshot_name=f"wsl_tag_p{page:02d}")
        page_events = body.get("events", body) if isinstance(body, dict) \
            else body
        if not isinstance(page_events, list):
            raise BlockError("BLOCKED_WSL_GAMMA",
                             "WSL Gamma tag response is not an event list",
                             EXIT_BLOCKED_OTHER)
        events.extend(page_events)
        if len(page_events) < 100:
            break
    else:
        raise BlockError("BLOCKED_WSL_GAMMA",
                         "WSL Gamma tag scan exceeded the provider offset "
                         "limit; refusing to quote from a partial scan",
                         EXIT_BLOCKED_OTHER)
    args.wsl_pm_events = events
    args.wsl_books_provider = books_provider


def maybe_wsl(args, cmd_name: str):
    """WSL lane call-site (plan §4): route the WSL league to wsl_lane
    (fixtures -> pinned-engine forecast -> Polymarket quote -> core decide
    with the in-lock WSL phrase gate). Any other league returns None
    (unchanged path). WSL without the config key is BLOCKED_LEAGUE — the
    identical refusal the pre-v3 runner gave for an unknown league. Real-mode
    quote commands get the journaled Gamma/CLOB plumbing bound here."""
    if getattr(args, "league", None) != "WSL":
        return None
    if not wsl_configured():
        raise BlockError("BLOCKED_LEAGUE",
                         "league WSL is not registered in config sport_keys "
                         "(see research/capital_v3/config.capital_v3.template."
                         "json; the live config commit is a post-GO act)",
                         EXIT_BLOCKED_OTHER)
    if cmd_name == "quote":
        _wire_wsl_real_quote(args)
    from research.papertrade_exec import wsl_lane
    return getattr(wsl_lane, f"cmd_{cmd_name}")(args)
# --- end CAPITAL LAW V3 runner block -----------------------------------------


# ------------------------------------------------------------------ fixtures --

def load_config() -> dict:
    p = Path(__file__).resolve().parent / "config.json"
    return json.loads(p.read_text())


# CAPITAL-V3 apply-fix 2026-10-10 (activation incident A-1, RE-FIX: the block originally sat ABOVE load_config's definition and its import-time call hit NameError->except->False; moved below the definition): the CLI surface
# must accept --league WSL whenever the lane is configured — ops_service's
# per-league cadence invokes these subcommands, and argparse choices=LEAGUES
# (core 3-tuple) exited 2 on WSL and crash-looped the supervisor (12:47Z).
# Fail-closed: without wsl_configured() the choices are the core 3-tuple.
LEAGUE_CHOICES = tuple(LEAGUES) + (("WSL",) if wsl_configured() else ()) \
    + tuple(ncaa_leagues_configured())


def _soccer_sport_keys() -> list[str]:
    """The registered SOCCER sport keys (config law: starts with
    soccer_uefa_nations_league; grows ONLY by an explicit config commit)."""
    keys = load_config()["sport_keys"]["SOCCER"]
    if not isinstance(keys, list) or not keys or \
            not all(isinstance(k, str) and k.strip() for k in keys):
        raise BlockError("BLOCKED_CONFIG",
                         "sport_keys.SOCCER must be a non-empty list of "
                         "sport keys (config law)", EXIT_BLOCKED_OTHER)
    return keys


def _provider_quota_guard_for(args):
    """W1.2: the exec-owned provider-credit guard bound to this data root."""
    from research.papertrade_exec.quota_guard import ProviderQuotaGuard
    return ProviderQuotaGuard(Path(args.data_root))


def _odds_for(args):
    """The pinned core quota-guarded client (shared by the soccer events
    fetch and the odds capture). Key hygiene failure is BLOCKED_KEY."""
    core = load_pinned_core(roots=_roots_from_args(args))
    odds_mod = core.odds_client
    quota = odds_mod.QuotaLedger(
        state_path=Path(args.data_root) / "data" / "quota_state.json",
        journal_path=Path(args.data_root) / "data" / "quota_journal.jsonl")
    try:
        client = odds_mod.OddsClient(quota=quota)
    except (FileNotFoundError, PermissionError, ValueError, OSError) as e:
        raise BlockError("BLOCKED_KEY",
                         f"key hygiene failure: {type(e).__name__}: {e}",
                         EXIT_BLOCKED_KEY)
    return odds_mod, quota, client


def _persist_events_snapshot(args, sport_key: str, body: bytes,
                             hdrs: dict) -> str:
    """Persist the raw events response + a meta record (the fixture rows'
    snapshot source; data files are overwritten per fetch — the append-only
    law binds the LEDGER, and every fetch is additionally journaled in the
    quota journal). Returns the snapshot sha256."""
    out = Path(args.data_root) / "data"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"events_{sport_key}.json").write_bytes(body)
    meta = {
        "endpoint": f"/v4/sports/{sport_key}/events",
        "fetched_at_utc": datetime.now(timezone.utc).strftime(NOW_FMT),
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "http_status": 200,
        "remaining_header": hdrs.get("x-requests-remaining"),
        "note": "0-credit events endpoint via core quota-guarded client",
    }
    (out / f"events_{sport_key}.meta.json").write_text(
        json.dumps(meta, indent=1, sort_keys=True))
    return meta["sha256"]


def soccer_stage_law(sport_key: str, kickoff_date: str) -> dict:
    """Stage/venue classification from the committed competition_law table
    (config.json; fail-closed, never guessed). A match is BET-ELIGIBLE only
    where the frozen B1 target semantics (3-way FULL-TIME 90/120-min,
    shootout=draw) and the bookmaker h2h semantics (90 minutes) are the SAME
    result AND the competition format guarantees a true home-and-away venue
    in the window (the frozen adapter passes neutral=False). Everything else
    — knockout/ET-possible windows, unknown venues, uncovered dates, unknown
    keys — is NOT_RUN."""
    law = load_config().get("competition_law", {})
    windows = law.get(sport_key)
    if not windows:
        return {"bet_eligible": False, "stage": "UNKNOWN_STAGE",
                "reason": (f"no committed competition_law window for sport "
                           f"key {sport_key}; fail-closed NOT_RUN (never "
                           "guessed)")}
    for w in windows:
        win = w.get("window", {})
        if str(win.get("from", "")) <= kickoff_date <= str(win.get("to", "")):
            return {"bet_eligible": bool(w.get("bet_eligible")),
                    "stage": w.get("stage", "UNKNOWN_STAGE"),
                    "reason": str(w.get("evidence", ""))}
    return {"bet_eligible": False, "stage": "UNKNOWN_STAGE",
            "reason": (f"kickoff date {kickoff_date} outside every committed "
                       f"competition_law window for {sport_key}; fail-closed "
                       "NOT_RUN")}


def stage_law_decision(fixture, cls: dict, now: str) -> dict:
    """Terminal NOT_RUN journal for a fixture outside the committed stage/venue
    law (specific reason; stake 0; never a silent drop)."""
    return {
        "type": "DECISION", "league": fixture.league,
        "match_id": fixture.match_id, "competition": fixture.competition,
        "home": fixture.home, "away": fixture.away,
        "kickoff_utc": fixture.kickoff_utc, "decided_at_utc": now,
        "status": "NOT_RUN_STAGE_LAW",
        "reason": f"[stage={cls['stage']}] {cls['reason']}",
        "stake_cents": 0, "chosen_leg": None,
    }


def write_soccer_competition_report(led, out_dir: Path) -> dict:
    """Exec-owned per-competition supplement (the pinned dashboard breaks
    NBA/WNBA/SOCCER by league; this adds the per-soccer-competition
    BET / NO_BET / NOT_RUN breakdown the expansion law requires)."""
    per: dict[str, dict] = {}
    for r in led.rows:
        if r.get("league") != "SOCCER":
            continue
        comp = r.get("competition") or "unknown"
        slot = per.setdefault(comp, {"forecasts": 0, "decisions": {},
                                     "matches": set()})
        slot["matches"].add(r.get("match_id"))
        if r["type"] == "FORECAST":
            slot["forecasts"] += 1
        elif r["type"] == "DECISION":
            st = r.get("status") or "?"
            slot["decisions"][st] = slot["decisions"].get(st, 0) + 1
    out = {"schema": "soccer_by_competition@1",
           "generated_at_utc": now_utc_real(),
           "law": ("BET_PAPER counts as BET; NO_EDGE counts as NO_BET; every "
                   "other status counts as NOT_RUN/BLOCKED. Stage/venue law: "
                   "config competition_law (fail-closed)."),
           "competitions": {}}
    for comp, slot in sorted(per.items()):
        dec = slot["decisions"]
        out["competitions"][comp] = {
            "matches": len(slot["matches"]),
            "forecasts": slot["forecasts"],
            "bet": dec.get("BET_PAPER", 0),
            "no_bet": dec.get("NO_EDGE", 0),
            "not_run_blocked": sum(v for k, v in dec.items()
                                   if k not in ("BET_PAPER", "NO_EDGE")),
            "decisions_by_status": dec,
        }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "soccer_by_competition.json").write_text(
        json.dumps(out, indent=1, sort_keys=True))
    return out


def _key_window_active(sport_key: str, day: str) -> bool:
    """W1.1: a registered soccer sport key is ACTIVE for `day` only when its
    committed competition_law has a window covering that date. Inactive keys
    (e.g. soccer_fifa_world_cup_group — a 2030 window; the provider 404s the
    key today) may NOT be polled on the cadence: at most ONE events poll per
    UTC day (the 'max 1/day' note the runtime audit caught being violated
    ~230-280x/day)."""
    law = load_config().get("competition_law", {}).get(sport_key) or []
    for w in law:
        win = w.get("window", {})
        if str(win.get("from", "")) <= day <= str(win.get("to", "")):
            return True
    return False


def _inactive_key_poll_ok(args, sport_key: str) -> bool:
    """1/day pacing state for INACTIVE keys (W1.1). State lives under
    <data-root>/data/soccer_key_poll.json {key: last_poll_utc_date}."""
    state_path = Path(args.data_root) / "data" / "soccer_key_poll.json"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    state: dict = {}
    try:
        state = json.loads(state_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    if state.get(sport_key) == today:
        return False
    state[sport_key] = today
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=1, sort_keys=True))
    return True


def real_soccer_fixtures(args, day: str, client=None, odds_mod=None) -> list:
    """REAL soccer fixtures from The Odds API /events via the core
    quota-guarded client (0-credit endpoint, journaled like every call).
    Union across the registered sport keys, deduped fail-closed — BOTH by
    event id and by (commence_time, team-set) slot ACROSS keys (the same real
    match listed under two keys must never yield two fixtures) — filtered to
    the UTC kickoff day. Network/HTTP failures are BLOCKED_ODDS_API (loud,
    nothing written). `client`/`odds_mod` are battery seams (offline fake
    client with the REAL exception classes); production passes neither."""
    if client is None:
        odds_mod, _quota, client = _odds_for(args)
    fixtures: list = []
    seen: dict[str, object] = {}
    slots: dict[tuple, tuple] = {}        # slot -> (sport_key, match_id)
    for key in _soccer_sport_keys():
        # W1.1: inactive keys (no committed law window covering `day`) are
        # polled at most once per UTC day — the provider 404s them and the
        # runtime audit measured 232-282 wasted calls/day against one key.
        if not _key_window_active(key, day) and \
                not _inactive_key_poll_ok(args, key):
            continue
        try:
            body, hdrs = client.get_events(key)
        except odds_mod.QuotaSkip as qs:      # 0-cost still honours the guard
            raise BlockError("BLOCKED_ODDS_API",
                             f"events fetch refused by the quota guard: {qs}",
                             EXIT_BLOCKED_OTHER)
        except odds_mod.KeyHalted as kh:
            raise BlockError("BLOCKED_KEY",
                             f"HALT_KEY engaged: {kh}", EXIT_BLOCKED_KEY)
        except Exception as e:                # URLError/HTTPError → loud
            raise BlockError("BLOCKED_ODDS_API",
                             f"events fetch failed for {key}: "
                             f"{type(e).__name__}: {e}", EXIT_BLOCKED_OTHER)
        sha = _persist_events_snapshot(args, key, body, hdrs)
        for fx in A.soccer_fixtures_from_events(body, key, snapshot_sha=sha):
            prior = seen.get(fx.match_id)
            if prior is not None:
                if (prior.home, prior.away, prior.kickoff_utc) != \
                        (fx.home, fx.away, fx.kickoff_utc):
                    raise BlockError("BLOCKED_FIXTURES_DUPLICATE",
                                     f"event id {fx.match_id} conflicts "
                                     "across registered sport keys",
                                     EXIT_BLOCKED_OTHER)
                continue
            slot = (fx.kickoff_utc, frozenset({A.norm(fx.home),
                                               A.norm(fx.away)}))
            other = slots.get(slot)
            if other is not None and other[1] != fx.match_id:
                raise BlockError(
                    "BLOCKED_FIXTURES_DUPLICATE",
                    f"events {other[1]} (sport key {other[0]}) and "
                    f"{fx.match_id} (sport key {key}) share one "
                    "(commence_time, team-set) slot across sport keys; 1:1 "
                    "matching would be ambiguous; fail-closed",
                    EXIT_BLOCKED_OTHER)
            slots[slot] = (key, fx.match_id)
            seen[fx.match_id] = fx
            if fx.kickoff_utc[:10] == day:
                fixtures.append(fx)
    fixtures.sort(key=lambda x: (x.kickoff_utc, x.match_id))
    return fixtures


def fixtures_for(args, league: str, day: str) -> list:
    if league == "NBA":
        to_day = getattr(args, "to_date", None)
        if to_day:                       # multi-day batch window (tip-UTC dates)
            return A.load_nba_fixtures_window(PINNED_DATA["nba_payloads"],
                                              day, to_day)
        # unchanged single-day law: the ESPN schedule-day payload file
        return A.load_nba_fixtures(PINNED_DATA["nba_payloads"], day)
    if league == "WNBA":
        return A.load_wnba_fixtures(PINNED_DATA["wnba_schedule"], day)
    if league == "SOCCER":
        if getattr(args, "sandbox", False):
            return synthetic_soccer_fixtures(day)
        return real_soccer_fixtures(args, day)
    if league.startswith("NCAA-"):
        from research.papertrade_exec import adapters_ncaa as AN
        if getattr(args, "sandbox", False):
            return synthetic_ncaa_fixtures(day, league)
        payload, body = AN.fetch_scoreboard(league, day)
        games = AN.games_from_payload(league, payload, body)
        return AN.upcoming_fixtures(games, day)
    raise BlockError("BLOCKED_LEAGUE", f"unknown league {league}")

NOW_FMT = "%Y-%m-%dT%H:%M:%SZ"


# --------------------------------------------------------------------- gate --

def exec_go_state(control_dir: str | Path, registry_path: str | Path) -> tuple[bool, str]:
    """This cycle's own two-key GO state (single phrase by construction).

    1. GO_TOKEN.json exists in `control_dir`, parses, carries the required
       provenance fields, and `go_phrase_typed_by_owner` EQUALS the registered
       phrase verbatim (any other phrase — including the three retired
       lane phrases — refuses).
    2. The registry row for SPORTS-PAPERTRADE-EXEC-V1 has a phase containing
       GO_CONSUMED (token without consumption refuses; P-8 law).
    """
    control = Path(control_dir)
    token = control / "GO_TOKEN.json"
    if not token.exists():
        return False, "GO_TOKEN.json absent (owner GO not yet transcribed)"
    try:
        tok = json.loads(token.read_text())
    except json.JSONDecodeError:
        return False, "GO_TOKEN.json malformed; fail-closed"
    for f in ("go_phrase_typed_by_owner", "typed_at_utc", "transcribed_by",
              "registry_consumption_note"):
        if not tok.get(f):
            return False, f"GO_TOKEN.json missing field {f}; fail-closed"
    if tok["go_phrase_typed_by_owner"] != GO_PHRASE:
        return False, ("GO_TOKEN.json phrase does not equal the registered "
                       "single phrase verbatim; fail-closed (retired phrases "
                       "are accepted nowhere)")
    reg = json.loads(Path(registry_path).read_text())
    cycles = reg.get("cycles", reg)
    if isinstance(cycles, dict):
        row = cycles.get("SPORTS-PAPERTRADE-EXEC-V1") or {}
    else:
        row = next((c for c in cycles
                    if c.get("cycle_id") == "SPORTS-PAPERTRADE-EXEC-V1"), {})
    phase = str(row.get("phase", ""))
    if "GO_CONSUMED" not in phase:
        return False, (f"registry phase '{phase or 'EMPTY'}' does not record "
                       "GO_CONSUMED (token without consumption refuses)")
    return True, "GO token (verbatim phrase) + registry GO_CONSUMED both present"


def require_gate(args) -> tuple[bool, str, Path]:
    if getattr(args, "sandbox", False):
        ctrl = Path(args.sandbox_control_dir)
        reg = Path(args.sandbox_registry)
    else:
        ctrl, reg = CONTROL_DIR, REGISTRY_PATH
    ok, why = exec_go_state(ctrl, reg)
    if not ok:
        raise BlockError("BLOCKED_NO_GO", why, EXIT_BLOCKED_NO_GO)
    return ok, why, ctrl


# ------------------------------------------------------------------- ledger --

def _core(roots: dict):
    return load_pinned_core(roots)


def load_pinned_core(roots: dict | None):
    from research.papertrade_exec import load_pinned_package
    core = load_pinned_package("spt_core", "paper_core", roots=roots)
    return core


def ledger_path_for(args) -> Path:
    if getattr(args, "sandbox", False):
        return Path(args.ledger) if args.ledger else \
            Path(args.data_root) / "sandbox" / "sandbox_ledger.jsonl"
    return Path(args.ledger) if args.ledger else \
        Path(args.data_root) / "ledger" / "paper_ledger.jsonl"


def open_ledger(args, *, create: bool):
    """Load + chain-verify; refuse tampered ledgers (fail-closed for ALL
    mutations and reads). Sandbox ledgers must stay sandbox; a real-mode
    genesis requires the post-GO path with the key fingerprint (GEN-1)."""
    core = load_pinned_core(roots=_roots_from_args(args))
    led = core.ledger.PaperLedger(ledger_path_for(args)).load()
    ok, errs = led.verify_chain()
    if not ok:
        raise BlockError("BLOCKED_TAMPER",
                         f"ledger chain verify failed: {errs[:3]}", EXIT_BLOCKED_TAMPER)
    genesis = next((r for r in led.rows if r["type"] == "GENESIS"), None)
    sandbox = bool(getattr(args, "sandbox", False))
    if genesis is None:
        if not create:
            raise BlockError("BLOCKED_NO_LEDGER",
                             f"no genesis at {led.path}; refusing (create=False)")
        if sandbox:
            pins = {"exec_cycle": "SPORTS-PAPERTRADE-EXEC-V1",
                    "erratum": "ERRATUM_CAPITAL_LAW_V2 (frozen-before-first-paper-row)",
                    "pins_file_sha256": sha256_file(
                        Path(__file__).resolve().parent / "pins.json")}
            led.genesis(plan_sha256=pins["pins_file_sha256"], sandbox=True,
                        key_fingerprint=None, pins=pins)
        else:
            odds = core.odds_client
            try:
                fp = odds.read_key_fingerprint()   # GEN-1: real genesis binds it
            except (FileNotFoundError, PermissionError, ValueError, OSError) as e:
                raise BlockError("BLOCKED_KEY",
                                 f"real genesis key hygiene failure: "
                                 f"{type(e).__name__}: {e}", EXIT_BLOCKED_KEY)
            led.genesis(plan_sha256=sha256_file(
                Path(__file__).resolve().parent / "pins.json"), sandbox=False,
                key_fingerprint=fp)
        genesis = led.rows[0]
    if sandbox and not genesis.get("sandbox"):
        raise BlockError("BLOCKED_SANDBOX_MISMATCH",
                         "sandbox mode refuses a REAL ledger (row law)")
    if not sandbox and genesis.get("sandbox"):
        raise BlockError("BLOCKED_SANDBOX_MISMATCH",
                         "real mode refuses a SANDBOX ledger (row law)")
    return core, led


def _roots_from_args(args) -> dict:
    out = {}
    for key, default in PINNED_ROOTS.items():
        out[key] = Path(getattr(args, key, None) or default)
    return out


# ------------------------------------------------------------------ fixtures --
# (fixtures_for / real_soccer_fixtures live directly after load_config above)

def synthetic_soccer_fixtures(day: str) -> list:
    """Deterministic SYNTHETIC The-Odds-API-shaped events for the rehearsal.
    Clearly labeled; never a real fixture list."""
    out = []
    for i in range(3):
        mid = f"SYN-SOC-{day}-{i+1}"
        ko = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc) \
            + timedelta(hours=15 + 2 * i, minutes=30)
        out.append(A.Fixture(
            league="SOCCER", match_id=mid,
            home=f"SynHome{i+1}", away=f"SynAway{i+1}",
            kickoff_utc=ko.strftime(NOW_FMT), competition="soccer_uefa_nations_league",
            et_local_date=A.et_local_date(ko),
            source_ref=f"SYNTHETIC_EVENTS_REHEARSAL#{mid}"))
    return out


def synthetic_ncaa_fixtures(day: str, league: str) -> list:
    """Deterministic SYNTHETIC NCAA fixtures for the rehearsal (clearly
    labeled; never a real fixture list)."""
    out = []
    for i in range(2):
        mid = f"SYN-{league}-{day}-{i+1}"
        ko = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc) \
            + timedelta(hours=17 + 3 * i)
        out.append(A.Fixture(
            league=league, match_id=mid,
            home=f"SynNcaa{league}H{i+1}", away=f"SynNcaa{league}A{i+1}",
            kickoff_utc=ko.strftime(NOW_FMT),
            competition="NCAA_REGULAR",
            et_local_date=A.et_local_date(ko),
            source_ref=f"SYNTHETIC_NCAA_REHEARSAL#{mid}",
            note=json.dumps({"neutral": i == 1, "conf_game_flag": i == 0,
                             "conference_unknown": False,
                             "season": 2026, "season_type": 2})))
    return out


def batch_anchor(fixtures: list, league: str) -> tuple[str, dict]:
    """Anchor deadline(s): NBA/WNBA T0-6h10m with T0 = earliest tip of the
    league's run-day batch (exclusive); SOCCER kickoff-6h strict per match."""
    if league in ("NBA", "WNBA"):
        t0 = min(f.kickoff_dt for f in fixtures)
        anchor = t0 - timedelta(seconds=BATCH_LEAD_SECONDS)
        return A.iso_z(anchor), {f.match_id: A.iso_z(anchor) for f in fixtures}
    if league.startswith("NCAA-"):
        # W5.4 anchor law: regular season = the NBA batch law (T0-6h10m);
        # tournament games = kickoff-6h PER MATCH (soccer law) with the
        # neutral flag mandatory in the note (the frozen feature reads it).
        if any((f.competition or "") == "NCAA_TOURNAMENT" for f in fixtures):
            per = {f.match_id: A.iso_z(f.kickoff_dt -
                                       timedelta(seconds=SOCCER_LEAD_SECONDS))
                   for f in fixtures}
            return "", per
        t0 = min(f.kickoff_dt for f in fixtures)
        anchor = t0 - timedelta(seconds=BATCH_LEAD_SECONDS)
        return A.iso_z(anchor), {f.match_id: A.iso_z(anchor)
                                 for f in fixtures}
    return "", {f.match_id: A.iso_z(f.kickoff_dt - timedelta(seconds=SOCCER_LEAD_SECONDS))
                for f in fixtures}


def check_anchor(fixtures: list, league: str, now: str):
    """REFUSE at/after the anchor: any target match whose anchor has passed
    (now >= anchor, exclusive deadline) refuses the WHOLE command (no partial
    batch, nothing written)."""
    _, per = batch_anchor(fixtures, league)
    now_dt = datetime.strptime(now, NOW_FMT).replace(tzinfo=timezone.utc)
    passed = {m: a for m, a in per.items() if now_dt >= A.parse_tip(a)}
    if passed:
        raise BlockError("BLOCKED_ANCHOR_PASSED",
                         f"anchor deadline(s) passed for {sorted(passed)}; "
                         "refusing the batch, nothing written "
                         "(NOT_RUN forever, no backfill)", EXIT_BLOCKED_ANCHOR)


# ----------------------------------------------------------------- p / rows --

def probe_engine(league: str, roots: dict) -> dict:
    """Report the league engine's wiring status WITHOUT computing anything.
    Sandbox rehearsals never store engine probabilities; this probe is what
    the rehearsal report quotes honestly."""
    out = {"league": league, "engine_mode": "SYNTHETIC_FALLBACK",
           "entry_status": "WIRED_SYNTHETIC_FALLBACK"}
    if league == "WNBA":
        predict_path = A.wnba_engine_available(roots["wnba26_root"])
        if predict_path is None:
            out.update({"entry_status": "BLOCKED_WNBA_ENTRY",
                        "detail": (f"Lane B predict entry absent at "
                                   f"{roots['wnba26_root']}/research/"
                                   "papertrade_wnba26/predict.py")})
            return out
        pin = _pin_sha_for("wnba26", "predict.py")
        if pin and sha256_file(predict_path) != pin:
            out.update({"entry_status": "BLOCKED_PIN_DRIFT_ENTRY",
                        "detail": ("wnba26/predict.py bytes drifted from the "
                                   "recorded pin; re-pin required before a "
                                   "real run trusts it")})
            return out
        out.update({"entry_status": "WIRED_ENGINE_READY",
                    "entry": str(predict_path),
                    "detail": ("wnba26_predict entry present + pin-verified; "
                               "contract predict_matches/wnba26_predict")})
    elif league == "NBA":
        predict_path = A.nba_engine_available(roots["nba26_root"])
        if predict_path is None:
            out.update({"entry_status": "BLOCKED_NBA_ENTRY",
                        "detail": (f"Lane D predict entry absent at "
                                   f"{roots['nba26_root']}/research/"
                                   "papertrade_nba/predict.py")})
            return out
        drift = A.nba_engine_entry_drift(predict_path)
        if drift:
            out.update({"entry_status": "BLOCKED_PIN_DRIFT_ENTRY",
                        "detail": (drift + "; re-pin required before a real "
                                   "run trusts it")})
            return out
        out.update({"entry_status": "WIRED_ENGINE_READY",
                    "entry": str(predict_path),
                    "detail": ("prospective PIT path (Lane D loader.py + "
                               "predict.py, frozen ESPN payloads ONLY — "
                               "composite 3d527b3c… / refresh-manifest chain) "
                               "present + pin-verified; real forecast = "
                               "nba26_predict under the frozen B1_STAR law "
                               "(EXEC-NBA-REWIRE; see ERRATUM_NBA_REWIRE.md — "
                               "the old scored-corpus path is DEAD)")})
    elif league == "SOCCER":
        replay_path = A.soccer_engine_available(roots["soccer_root"])
        if replay_path is None:
            out.update({"entry_status": "BLOCKED_SOCCER_ENTRY",
                        "detail": (f"Lane C replay entry absent at {replay_path}; "
                                   "soccer_b1_replay(fixtures, corpus_csv, "
                                   "asof_date) required for a real run")})
            return out
        pin = _pin_sha_for("soccer", "replay.py")
        if pin and sha256_file(replay_path) != pin:
            out.update({"entry_status": "BLOCKED_PIN_DRIFT_ENTRY",
                        "detail": ("soccer/replay.py bytes drifted from the "
                                   "recorded pin; re-pin required before a "
                                   "real run trusts it")})
            return out
        out.update({"entry_status": "WIRED_ENGINE_READY",
                    "entry": str(replay_path),
                    "detail": "soccer_b1_replay entry present + pin-verified"})
    return out


def _pin_sha_for(pkg_key: str, fname: str) -> str | None:
    pins = load_pins()
    return pins["packages"].get(pkg_key, {}).get("files", {})\
        .get(fname, {}).get("sha256")


def compute_forecasts(args, league: str, fixtures: list) -> tuple[list[dict], dict]:
    """FORECAST drafts for the batch. SANDBOX/rehearsal mode ALWAYS stores the
    labeled synthetic adapter (zero real probabilities pre-GO) while the
    wiring probe reports what a post-GO real run would use. REAL mode is
    engine-first: WNBA via Lane B's entry, SOCCER via Lane C's entry, NBA via
    the prospective PIT path (Lane D loader+predict, frozen ESPN payloads
    only) — each raising its BLOCKED_* family if the pinned entry is
    absent/drifted at run time (fail-closed, journaled by the caller)."""
    roots = _roots_from_args(args)
    wiring = probe_engine(league, roots)
    if getattr(args, "sandbox", False):
        drafts = []
        for f in fixtures:
            p = A.synthetic_three_way_p(f.match_id) if league == "SOCCER" \
                else A.synthetic_two_way_p(f.match_id)
            drafts.append({"match_id": f.match_id, "p": p,
                           "model_version_sha": "SYNTHETIC_ADAPTER_NOT_ENGINE",
                           "source_ref": "SYNTHETIC_ADAPTER_REHEARSAL "
                                         "(no real p pre-GO)",
                           "mode": "SYNTHETIC"})
        return drafts, wiring
    # ---- REAL mode (reachable only post-GO): engine-first, fail-closed ----
    if league == "WNBA":
        predict_path = A.wnba_engine_available(roots["wnba26_root"])
        if predict_path is None:
            raise BlockError("BLOCKED_WNBA_ENTRY",
                             "Lane B predict entry absent; no fallback in real "
                             "mode (dispatch: rehearsal falls back, real run "
                             "refuses)")
        pin = _pin_sha_for("wnba26", "predict.py")
        if pin and sha256_file(predict_path) != pin:
            raise BlockError("BLOCKED_PIN_DRIFT",
                             f"wnba26/predict.py sha "
                             f"{sha256_file(predict_path)[:12]} != pin "
                             f"{pin[:12]}; re-pin before a real run", 7)
        res = A.wnba_engine_predict(
            predict_path, A.wnba_completed_rows(PINNED_DATA["wnba_schedule"]),
            A.wnba_raw_upcoming(PINNED_DATA["wnba_schedule"], fixtures[0].kickoff_utc[:10]))
        by_mid = {r["match_id"]: r for r in res}
        drafts = []
        for f in fixtures:
            r = by_mid.get(f.match_id)
            if r is None:
                raise BlockError("BLOCKED_WNBA_ENTRY",
                                 f"engine returned no prediction for {f.match_id}")
            drafts.append({"match_id": f.match_id,
                           "p": {"HOME": r["p_home"], "AWAY": r["p_away"]},
                           "model_version_sha": "wnba26_predict",
                           "source_ref": f"wnba26_predict@state="
                                         f"{r.get('state_digest','')}",
                           "mode": "ENGINE"})
        wiring.update({"engine_mode": "ENGINE"})
        return drafts, wiring
    if league == "SOCCER":
        replay_path = A.soccer_engine_available(roots["soccer_root"])
        if replay_path is None:
            raise BlockError("BLOCKED_SOCCER_ENTRY",
                             "Lane C replay entry absent; no fallback in real mode")
        pin = _pin_sha_for("soccer", "replay.py")
        if pin and sha256_file(replay_path) != pin:
            raise BlockError("BLOCKED_PIN_DRIFT",
                             f"soccer/replay.py sha "
                             f"{sha256_file(replay_path)[:12]} != pin "
                             f"{pin[:12]}; re-pin before a real run", 7)
        # Stage/venue law FIRST (owner 2026-10-07 item 4): the frozen B1
        # target is full-time 90/120-min (shootout=draw) while bookmaker 1X2
        # settles on 90 minutes — matches outside the committed
        # LEAGUE_PHASE_HOME_AWAY windows are journaled NOT_RUN_STAGE_LAW and
        # never reach the engine. Then the freeze-anchored crosswalk
        # extension (verified fail-closed before the engine runs); names
        # still unresolved are split out per-fixture and journaled NOT_RUN by
        # the caller — never fuzzy, never batch-killing.
        stage_missed = []
        stage_ok = []
        for f in fixtures:
            cls = soccer_stage_law(f.competition, f.kickoff_utc[:10])
            if cls["bet_eligible"]:
                stage_ok.append(f)
            else:
                stage_missed.append({"match_id": f.match_id, "home": f.home,
                                     "away": f.away,
                                     "kickoff_utc": f.kickoff_utc,
                                     "competition": f.competition,
                                     "reason": cls["reason"],
                                     "stage": cls["stage"],
                                     "status": "NOT_RUN_STAGE_LAW"})
        mod, mapping = A.soccer_extension_crosswalk(
            replay_path,
            Path(__file__).resolve().parent / "PROVIDER_NAME_CROSSWALK_EXTENSION.csv")
        resolvable, missed = A.soccer_crosswalk_split(mod, mapping, stage_ok)
        drafts = []
        if resolvable:
            res = A.soccer_engine_replay(replay_path, resolvable,
                                         PINNED_DATA["soccer_corpus"],
                                         fixtures[0].kickoff_utc[:10])
            drafts = [{"match_id": r["match_id"],
                       "p": {"HOME": float(r["p_home"]), "DRAW": float(r["p_draw"]),
                             "AWAY": float(r["p_away"])},
                       "model_version_sha": "soccer_b1_replay",
                       "source_ref": "soccer_b1_replay", "mode": "ENGINE"}
                      for r in res]
        wiring.update({"engine_mode": "ENGINE" if drafts else "NO_ENGINE_ROWS",
                       "stage_law_miss": stage_missed,
                       "crosswalk_miss": [
                           {"match_id": f.match_id, "home": f.home,
                            "away": f.away, "kickoff_utc": f.kickoff_utc,
                            "competition": f.competition,
                            "reason": why, "status": "CROSSWALK_MISS"}
                           for f, why in missed]})
        return drafts, wiring
    if league.startswith("NCAA-"):
        # W5.3/W5.4: the frozen state store is the PIT source; the GBM
        # layer runs ONLY on a sha-pinned artifact, else the lane degrades
        # HONESTLY to the frozen Elo layer (audited) with the mode
        # journaled. Feature gaps (unknown conference flags) travel in the
        # row — never guessed.
        from research.papertrade_exec import ncaa_state_store as NSS
        from research.papertrade_exec import ncaa_model as NM
        store_path = _ncaa_plane_dir(args) / league / "state.json"
        st = NSS.NcaaState.load(store_path)
        if st is None or st.games_processed == 0:
            raise BlockError(
                "BLOCKED_NCAA_STATE_ABSENT",
                f"no replayed state store at {store_path} — run the "
                "ncaa-refresh-state job first (fail-closed, never "
                "guessed)", EXIT_BLOCKED_OTHER)
        artifacts_dir = _ncaa_plane_dir(args) / league / "artifacts"
        season = datetime.now(timezone.utc).year
        model, manifest = NM.load_pinned(artifacts_dir, league, season)
        drafts = []
        for f in fixtures:
            note = json.loads(f.note or "{}")
            game = {"season": note.get("season") or season,
                    "home_id": note.get("home_id"),
                    "away_id": note.get("away_id"),
                    "home_conference_id": note.get("home_conference_id"),
                    "away_conference_id": note.get("away_conference_id"),
                    "neutral_site": bool(note.get("neutral")),
                    "date": note.get("date") or f.kickoff_utc[:10]}
            feat = NSS.pregame_features(st, game)
            if model is not None:
                p_home = NM.predict_home_p(model, [NSS.feature_vector(feat)])[0]
                mode, src = "NCAA_GBM_PINNED", \
                    f"gbm@{manifest['sha256'][:12]} season={manifest['season']}"
            else:
                p_home = feat["p_elo"]
                mode = "NCAA_ELO_FALLBACK_NO_SKLEARN"
                src = "frozen Elo layer (audited); refit job not run"
            gaps = {k: note.get(k) for k in ("conference_unknown",
                                             "conf_game_flag") }
            drafts.append({"match_id": f.match_id,
                           "p": {"HOME": round(p_home, 6),
                                 "AWAY": round(1.0 - p_home, 6)},
                           "model_version_sha":
                               (manifest["sha256"][:12] if model else mode),
                           "source_ref": f"ncaa_{league} {src} "
                                         f"state={st.digest()[:16]} "
                                         f"feature_gaps={gaps}",
                           "mode": mode})
        wiring.update({"engine_mode": "ENGINE" if model is not None
                       else "ELO_FALLBACK_NO_SKLEARN",
                       "state_sha256": st.digest()[:16],
                       "games_processed": st.games_processed})
        return drafts, wiring
    # NBA real mode (EXEC-NBA-REWIRE): the lawful PROSPECTIVE PIT path landed
    # by NBA-WINPROB-PROSPECTIVE-PREP-V1 (byte-pinned `nba26` package). The
    # old scored-corpus path is DEAD (bind token unmintable by this gate —
    # disclosed); this path reads the frozen ESPN payloads only and NEVER the
    # scored bind corpus. See ERRATUM_NBA_REWIRE.md.
    anchor_utc, _ = batch_anchor(fixtures, league)
    predict_path = Path(roots["nba26_root"]) / "research" / "papertrade_nba" / "predict.py"
    if not predict_path.exists():
        raise BlockError("BLOCKED_NBA_ENTRY",
                         f"Lane D predict entry absent: {predict_path}")
    drift = A.nba_engine_entry_drift(predict_path)
    if drift:
        raise BlockError("BLOCKED_PIN_DRIFT",
                         f"{drift}; re-pin deliberately before a real run "
                         "trusts it", 7)
    # Post-GO cadence: refresh the payload corpus for the batch's game-days
    # BEFORE forecasting (post-GO only; the rehearsal never reaches this
    # branch). Entry checks above must stay FIRST so a drifted/absent entry
    # can never touch the corpus.
    # W1.3 ROOT CAUSE (runtime audit 2026-10-21): the refresh window used to
    # equal the FORECAST window (lookback 0), so the corpus never gained a
    # FINAL row — every team stayed at R0=1500 and the engine returned the
    # pure-HCA constant p=0.640065 for all 14 live forecasts. The refresh now
    # walks back `nba_refresh_lookback_days` (config; default 14) so
    # completed game-days feed the engine before any forecast.
    A.nba_incremental_refresh(
        PINNED_DATA["nba_payloads"], fixtures[0].kickoff_utc[:10],
        fixtures[-1].kickoff_utc[:10], go_ok=True,
        lookback_days=int(load_config().get("nba_refresh_lookback_days", 14)))
    composite_pin = load_pins()["data"]["nba_espn_schedule_2026_27"]["composite_sha256"]
    res = A.nba_engine_predict(
        PINNED_DATA["nba_payloads"], anchor_utc, anchor_utc,
        expected_composite_sha=composite_pin, predict_path=predict_path)
    by_mid = {str(r["match_id"]): r for r in res}
    predict_sha = sha256_file(predict_path)
    drafts = []
    for f in fixtures:
        r = by_mid.get(f.match_id)
        if r is None:
            raise BlockError("BLOCKED_NBA_ENTRY",
                             f"engine returned no prediction for {f.match_id}")
        drafts.append({"match_id": f.match_id,
                       "p": {"HOME": float(r["p_home"]),
                             "AWAY": float(r["p_away"])},
                       "model_version_sha": f"nba26_predict@{predict_sha[:12]}",
                       "source_ref": (f"nba26_predict@model_id={r['model_id']} "
                                      f"state={r['state_digest'][:16]} "
                                      "corpus=frozen ESPN payloads only"),
                       "mode": "ENGINE"})
    wiring.update({"engine_mode": "ENGINE"})
    return drafts, wiring


def cmd_forecast(args) -> dict:
    _r = maybe_wsl(args, "forecast")
    if _r is not None:
        return _r
    require_gate(args)
    verify_pins(roots=_roots_from_args(args))
    now = now_of(args)
    league = args.league
    fixtures = fixtures_for(args, league, args.date)
    if not fixtures:
        return {"league": league, "date": args.date, "fixtures": 0,
                "note": "no upcoming fixtures for this date (nothing to forecast)"}
    check_anchor(fixtures, league, now)          # refuse BEFORE any write
    core, led = open_ledger(args, create=True)
    existing = forecast_index(led)
    decided = led.decided_match_ids()
    drafts, wiring = compute_forecasts(args, league, fixtures)
    draft_by_mid = {d["match_id"]: d for d in drafts}
    missed = {m["match_id"]: m for m in
              wiring.get("crosswalk_miss", [])
              + wiring.get("stage_law_miss", [])}
    _, per_anchor = batch_anchor(fixtures, league)
    written, skipped, journaled_miss = [], [], []
    for f in fixtures:
        if f.match_id in existing or f.match_id in decided:
            skipped.append({"match_id": f.match_id,
                            "why": "forecast row exists" if f.match_id in existing
                            else "match already decided (terminal)"})
            continue
        d = draft_by_mid.get(f.match_id)
        if d is None:
            continue                    # crosswalk-miss: journaled below
        row = {
            "type": "FORECAST", "league": league, "match_id": f.match_id,
            "competition": f.competition, "home": f.home, "away": f.away,
            "kickoff_utc": f.kickoff_utc,
            "recorded_at_utc": now,
            "anchor_utc": per_anchor[f.match_id],
            "model_version_sha": d["model_version_sha"], "p": d["p"],
            "source_ref": d["source_ref"], "mode": d["mode"],
            "fixture_source": f.source_ref,
        }
        led.append(row)
        written.append(f.match_id)
    for f in fixtures:
        m = missed.get(f.match_id)
        if m is None or f.match_id in existing or f.match_id in decided \
                or f.match_id in draft_by_mid or f.match_id in written \
                or f.match_id in journaled_miss:
            continue
        led.append_decision(miss_decision(f, m, now))
        journaled_miss.append(f.match_id)
    emitted_b1r = []
    if league == "SOCCER":
        # Post-switch emission (switch GO-packet step 1): a B1 row written
        # above (or already in the ledger) must never stand alone — append
        # its B1R twin now, while every anchor in the batch is still open.
        b1r_switch_ts_verified(Path(args.sandbox_registry)
                               if getattr(args, "sandbox", False)
                               else REGISTRY_PATH)
        emitted_b1r = emit_b1r_forecasts(led, fixtures, now)
    return {"league": league, "date": args.date, "now_utc": now,
            "written": written, "skipped_existing": skipped,
            "journaled_crosswalk_miss": journaled_miss,
            "emitted_b1r": emitted_b1r,
            "wiring": wiring, "sandbox": bool(args.sandbox)}


def crosswalk_miss_decision(fixture, miss: dict, now: str) -> dict:
    """Terminal NOT_RUN journal for a fixture the frozen+extended crosswalk
    cannot resolve (dashboard cause: identity_crosswalk). Specific reason,
    stake 0, never a silent drop."""
    return {
        "type": "DECISION", "league": fixture.league,
        "match_id": fixture.match_id, "competition": fixture.competition,
        "home": fixture.home, "away": fixture.away,
        "kickoff_utc": fixture.kickoff_utc, "decided_at_utc": now,
        "status": "CROSSWALK_MISS", "reason": miss["reason"],
        "stake_cents": 0, "chosen_leg": None,
    }


def miss_decision(fixture, miss: dict, now: str) -> dict:
    """Dispatch a NOT_RUN-family journal by its miss kind (stage law vs
    crosswalk) — one loop in cmd_forecast journals both."""
    if miss.get("status") == "NOT_RUN_STAGE_LAW":
        return stage_law_decision(fixture, miss, now)
    return crosswalk_miss_decision(fixture, miss, now)


# B1R switch (SOCCER-INTL-B1R-PAPER-SWITCH-V1; owner GO consumed
# 2026-10-10T02:20:20Z): for SOCCER matches the decision forecast is the
# B1R_SOCCER row when present; the parallel B1 row stays in the ledger as
# control. Non-soccer selection law unchanged (first FORECAST wins).
SOCCER_DECISION_MODEL_ID = "B1R_SOCCER"

# B1R fail-closed law (owner instruction 2026-10-10; ERRATUM_2 E-1
# disposition 2 of SOCCER-INTL-WC-EURO-PAPER-PREP-V1; FREEZE_BOUNDARY.json
# of the switch cycle). After switch_ts a SOCCER decision may be grounded
# ONLY in a B1R_SOCCER FORECAST row that (a) carries the frozen inner map
# sha, (b) resolves control_ref_row_sha256 to the parallel B1 control row
# of the SAME fixture, (c) is the byte-exact frozen-map transform of that
# control's p (T4/T6), and (d) was recorded strictly before its anchor.
# Anything else — including a B1-only match — journals
# NOT_RUN_NO_B1R_FORECAST (stake 0, terminal). The B1 emission pass makes
# the B1R twin exist for every post-switch B1 row before any decision.
B1R_SWITCH_CYCLE = "SOCCER-INTL-B1R-PAPER-SWITCH-V1"
B1R_SWITCH_TS = "2026-10-10T02:20:20Z"          # registry CAS GO-consumption
B1R_MAP_INNER_SHA = ("1f4a4c4f26639b31dcb9c79035e8cfe3fb57deb693c5def729e"
                     "402bba953befd")
B1R_MODEL_VERSION_SHA = "soccer_b1r_v1"
B1_CONTROL_MODEL_VERSION_SHAS = {"soccer_b1_replay"}
B1_CONTROL_MODEL_IDS = {"B1_SOCCER"}
NOT_RUN_NO_B1R_FORECAST = "NOT_RUN_NO_B1R_FORECAST"
_B1R_ADAPTER = None
_B1R_MAP = None
_B1R_SWITCH_VERIFIED = False


def _b1r_adapter():
    """The switch cycle's b1r_adapter.py, byte-pinned via pins.json
    (verify_pins refuses on drift BEFORE this loader runs). Read-only
    cross-cycle reuse — the GO packet's 'reuse byte-for-byte' law."""
    global _B1R_ADAPTER
    if _B1R_ADAPTER is None:
        import importlib.util
        pkg = load_pins()["packages"]["b1r_switch"]
        path = Path(pkg["worktree"]) / pkg["pkg_dir"] / "b1r_adapter.py"
        spec = importlib.util.spec_from_file_location("exec_b1r_adapter", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["exec_b1r_adapter"] = mod
        spec.loader.exec_module(mod)
        _B1R_ADAPTER = mod
    return _B1R_ADAPTER


def b1r_map():
    """The frozen draw-calibration map, file+inner sha verified by the
    adapter's own law. Map-file drift is a HARD block (T1), not a per-match
    NOT_RUN — nothing may decide under a drifted map."""
    global _B1R_MAP
    if _B1R_MAP is None:
        try:
            _B1R_MAP = _b1r_adapter().load_map_verified()
        except _b1r_adapter().Refuse as e:
            raise BlockError("BLOCKED_B1R_MAP_PIN",
                             f"frozen B1R draw map refused: {e} "
                             "(T1; re-pin required)", EXIT_PIN_DRIFT)
    return _B1R_MAP


def b1r_switch_ts_verified(registry_path) -> bool:
    """The pinned switch_ts must be the registry-recorded GO-consumption
    instant of the B1R switch cycle. If the registry no longer records it,
    the B1R decision law cannot be enforced — SOCCER forecast/decide block
    loudly (fail-closed; NBA/WNBA unaffected)."""
    if _B1R_SWITCH_VERIFIED:
        return True
    reg = json.loads(Path(registry_path).read_text())
    cycles = reg.get("cycles", reg)
    if isinstance(cycles, dict):
        row = cycles.get(B1R_SWITCH_CYCLE) or {}
    else:
        row = next((c for c in cycles
                    if c.get("cycle_id") == B1R_SWITCH_CYCLE), {})
    state = str(row.get("go_phrase_state", ""))
    parts = state.split()
    if not state.startswith("OWNER_GO_TYPED_LIVE") or len(parts) < 2 or \
            parts[1] != B1R_SWITCH_TS:
        raise BlockError(
            "BLOCKED_B1R_SWITCH_TS_UNVERIFIED",
            f"registry go_phrase_state {state!r} does not record "
            f"{B1R_SWITCH_CYCLE} GO consumption at the pinned switch_ts "
            f"{B1R_SWITCH_TS}; the B1R decision law cannot be enforced — "
            "fail-closed (re-pin with evidence to resume soccer paper)",
            EXIT_BLOCKED_OTHER)
    globals()["_B1R_SWITCH_VERIFIED"] = True
    return True


def soccer_b1r_forecast(led, fixture, now: str) -> tuple[dict | None, str]:
    """The lawful B1R decision forecast for a SOCCER fixture, or
    (None, reason). Every rejection is specific and journaled by the caller
    as NOT_RUN_NO_B1R_FORECAST — a B1-only match is NEVER silently used."""
    rows = [r for r in led.rows if r.get("type") == "FORECAST"
            and r.get("league") == "SOCCER"
            and r.get("match_id") == fixture.match_id
            and r.get("model_id") == SOCCER_DECISION_MODEL_ID]
    if not rows:
        return None, ("no B1R_SOCCER forecast row for this match; after "
                      f"switch_ts {B1R_SWITCH_TS} a B1 row is CONTROL-ONLY "
                      "and can never ground a soccer decision")
    if len(rows) > 1:
        return None, (f"{len(rows)} B1R_SOCCER forecast rows for this "
                      "match; ambiguous (duplicate law), fail-closed")
    r = rows[0]
    if r.get("map_sha256") != B1R_MAP_INNER_SHA:
        return None, ("B1R row map_sha256 != frozen map pin; fail-closed")
    if r.get("model_version_sha") != B1R_MODEL_VERSION_SHA:
        return None, (f"B1R row model_version_sha "
                      f"{r.get('model_version_sha')!r} != "
                      f"{B1R_MODEL_VERSION_SHA!r}; fail-closed")
    cref = r.get("control_ref_row_sha256")
    ctl = next((x for x in led.rows if x.get("row_sha256") == cref),
               None) if cref else None
    if ctl is None:
        return None, ("control_ref_row_sha256 does not resolve to a ledger "
                      "row; fail-closed")
    if ctl.get("type") != "FORECAST" or ctl.get("league") != "SOCCER" or \
            ctl.get("match_id") != fixture.match_id:
        return None, ("control row is not a SOCCER FORECAST for this match; "
                      "fail-closed")
    if ctl.get("model_version_sha") not in B1_CONTROL_MODEL_VERSION_SHAS \
            and ctl.get("model_id") not in B1_CONTROL_MODEL_IDS:
        return None, ("control row is not a B1 forecast (wrong model "
                      "identity); fail-closed")
    if r.get("p_control_b1") != ctl.get("p"):
        return None, ("B1R p_control_b1 != control B1 p (derivation/"
                      "same-snapshot law T4 violated); fail-closed")
    m = b1r_map()                       # raises BLOCKED_B1R_MAP_PIN on drift
    ad = _b1r_adapter()
    try:
        t = ad.b1r_transform(ctl["p"]["HOME"], ctl["p"]["DRAW"],
                             ctl["p"]["AWAY"], m)
    except ad.Refuse as e:
        return None, f"frozen transform refused on the control p ({e})"
    if r.get("p") != t:
        return None, ("B1R p is not the byte-exact frozen-map transform of "
                      "the control B1 p (T4/T6); fail-closed")
    try:
        rec = A.parse_tip(r["recorded_at_utc"])
        anch = A.parse_tip(r["anchor_utc"])
    except (KeyError, TypeError, ValueError):
        return None, "B1R row timestamps missing/malformed; fail-closed"
    if rec >= anch:
        return None, ("B1R row recorded at/after its anchor (PIT law); no "
                      "late forecast is ever a decision basis")
    return r, "valid B1R decision forecast"


def no_b1r_decision(fixture, why: str, now: str) -> dict:
    """Terminal NOT_RUN_NO_B1R_FORECAST journal (stake 0; never a silent
    drop, never a B1-based decision)."""
    return {
        "type": "DECISION", "league": fixture.league,
        "match_id": fixture.match_id, "competition": fixture.competition,
        "home": fixture.home, "away": fixture.away,
        "kickoff_utc": fixture.kickoff_utc, "decided_at_utc": now,
        "status": NOT_RUN_NO_B1R_FORECAST, "reason": why,
        "stake_cents": 0, "chosen_leg": None,
    }


def emit_b1r_forecasts(led, fixtures: list, now: str) -> list[dict]:
    """Switch GO-packet step 1 (post-switch SOCCER batches): every B1
    FORECAST row of this batch gets its B1R twin APPENDED next to it (never
    replacing; control_ref -> the B1 row; recorded_at = now; anchor inherited
    and still open). Idempotent: a match that already carries ANY B1R row is
    skipped (duplicate law T3 — never a second B1R row)."""
    ad = _b1r_adapter()
    m = b1r_map()
    out = []
    for f in fixtures:
        if f.match_id in led.decided_match_ids():
            continue
        b1_rows = [r for r in led.rows
                   if r.get("type") == "FORECAST"
                   and r.get("league") == "SOCCER"
                   and r.get("match_id") == f.match_id
                   and (r.get("model_version_sha")
                        in B1_CONTROL_MODEL_VERSION_SHAS
                        or r.get("model_id") in B1_CONTROL_MODEL_IDS)]
        if not b1_rows:
            continue
        if len(b1_rows) > 1:
            raise BlockError("BLOCKED_B1R_CONTROL_AMBIGUOUS",
                             f"{len(b1_rows)} B1 control rows for "
                             f"{f.match_id}; 1:1 law refuses", EXIT_BLOCKED_OTHER)
        if any(r.get("type") == "FORECAST"
               and r.get("league") == "SOCCER"
               and r.get("match_id") == f.match_id
               and r.get("model_id") == SOCCER_DECISION_MODEL_ID
               for r in led.rows):
            continue                    # idempotent: the twin already exists
        b1 = b1_rows[0]
        try:
            (row,) = ad.build_forecast_rows(b1, m)
        except ad.Refuse as e:
            raise BlockError("BLOCKED_B1R_EMISSION",
                             f"frozen B1R emission refused for "
                             f"{f.match_id}: {e}", EXIT_BLOCKED_OTHER)
        row["recorded_at_utc"] = now
        if A.parse_tip(now) >= A.parse_tip(row["anchor_utc"]):
            continue        # never a backfill: the anchor passed, stay away
        appended = led.append(row)
        out.append({"match_id": f.match_id,
                    "row_sha256": appended["row_sha256"]})
    return out


def forecast_index(led) -> dict:
    idx = {}
    for r in led.rows:
        if r["type"] == "FORECAST":
            idx.setdefault(r["match_id"], r)
    for r in led.rows:
        if (r["type"] == "FORECAST" and r.get("league") == "SOCCER"
                and r.get("model_id") == SOCCER_DECISION_MODEL_ID):
            idx[r["match_id"]] = r
    return idx


def quote_index(led) -> dict:
    idx = {}
    for r in led.rows:
        if r["type"] == "MARKET_QUOTE":
            idx.setdefault(r["match_id"], r)
    return idx


def now_of(args) -> str:
    if getattr(args, "now", None):
        if not getattr(args, "sandbox", False):
            raise BlockError("BLOCKED_TEST_HOOK_IN_REAL_MODE",
                             "--now is a rehearsal hook; refused in real mode")
        datetime.strptime(args.now, NOW_FMT)     # validate
        return args.now
    return datetime.now(timezone.utc).strftime(NOW_FMT)


# -------------------------------------------------------------------- quote --

CUTOVER_GO_PHRASE = "GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER"
AI_AUTHORITY_GO_PHRASE = "GO SPORTS PAPERTRADE EXEC V1 AI AUTHORITY"
GO_TOKEN_FILES = {"pm_cutover_active": "GO_TOKEN_CUTOVER.json",
                  "ai_authority_active": "GO_TOKEN_AI_AUTHORITY.json"}
GO_REGISTRY_MARKERS = {"pm_cutover_active": "EXEC_CUTOVER_GO_CONSUMED",
                       "ai_authority_active":
                           "EXEC_AI_AUTHORITY_GO_CONSUMED"}


def _owner_go_state(key: str, *, sandbox: bool,
                    sandbox_control_dir=None, sandbox_registry=None) -> tuple[bool, str]:
    """The GO plane for one feature gate: the transcribed token file (with
    the registered phrase VERBATIM + provenance fields) AND this cycle's
    registry row phase carrying the GO_CONSUMED marker. SANDBOX is exempt
    (the rehearsal flips config flags via its own control copies; battery
    hooks stay sandbox-only). Fail-closed: any absence/mismatch => OFF."""
    from research.papertrade_exec import CONTROL_DIR, REGISTRY_PATH
    if sandbox:
        return True, "sandbox rehearsal plane (config flag governs)"
    ctrl = Path(sandbox_control_dir) if sandbox_control_dir else CONTROL_DIR
    reg_path = Path(sandbox_registry) if sandbox_registry else REGISTRY_PATH
    token_path = Path(ctrl) / GO_TOKEN_FILES[key]
    try:
        tok = json.loads(token_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return False, f"GO token absent/malformed: {token_path.name}"
    phrase = {"pm_cutover_active": CUTOVER_GO_PHRASE,
              "ai_authority_active": AI_AUTHORITY_GO_PHRASE}[key]
    for f in ("go_phrase_typed_by_owner", "typed_at_utc", "transcribed_by",
              "registry_consumption_note"):
        if not tok.get(f):
            return False, f"GO token missing field {f}"
    if str(tok["go_phrase_typed_by_owner"]).strip() != phrase:
        return False, "GO token phrase does not equal the registered phrase verbatim"
    try:
        reg = json.loads(reg_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return False, "registry unreadable"
    cycles = reg.get("cycles", reg)
    row = cycles.get("SPORTS-PAPERTRADE-EXEC-V1") if isinstance(cycles, dict) \
        else next((c for c in cycles
                   if c.get("cycle_id") == "SPORTS-PAPERTRADE-EXEC-V1"), {})
    if GO_REGISTRY_MARKERS[key] not in str(row.get("phase", "")):
        return False, (f"registry phase does not record "
                       f"{GO_REGISTRY_MARKERS[key]}")
    return True, "owner GO token + registry consumption both present"


def papertrade_flags(args) -> dict:
    """Feature-gate law (owner 2026-10-20; GOs typed + consumed
    2026-10-21):
      * REAL mode: a gate is ON only when BOTH keys hold — config
        feature_gates true AND the owner's transcribed GO token +
        registry GO_CONSUMED marker. Fail-closed either way.
      * SANDBOX mode: DEFAULTS to the PRE-GO state (OFF) so the pinned
        rehearsal always exercises the pre-GO path; a rehearsal may flip
        gates by placing sandbox_feature_gates.json in its OWN control
        copy (never the committed config)."""
    cfg_path = Path(__file__).resolve().parent / "config.json"
    try:
        cfg = json.loads(cfg_path.read_text())
    except Exception:
        cfg = {}
    fg = cfg.get("feature_gates") or {}
    sandbox = bool(getattr(args, "sandbox", False))
    out = {}
    if sandbox:
        fg = {"pm_cutover_active": False, "ai_authority_active": False}
        ctrl = getattr(args, "sandbox_control_dir", None)
        if ctrl:
            try:
                sf = json.loads((Path(ctrl) /
                                 "sandbox_feature_gates.json").read_text())
                fg.update({k: bool(sf.get(k)) for k in fg})
            except (FileNotFoundError, json.JSONDecodeError):
                pass                      # default pre-GO rehearsal state
    for key in ("pm_cutover_active", "ai_authority_active"):
        cfg_on = bool(fg.get(key, False))
        go_on, why = _owner_go_state(
            key, sandbox=sandbox,
            sandbox_control_dir=getattr(args, "sandbox_control_dir", None),
            sandbox_registry=getattr(args, "sandbox_registry", None))
        out[key] = bool(cfg_on and go_on)
        if key == "ai_authority_active":
            out["ai_gate_why"] = why
    return out


def _pm_probe_seam(args):
    """Sandbox-only rehearsal seam: PAPERTRADE_PM_PROBE_JSON points at a
    {match_id: quote} table the sandbox PM chain walks through the SAME
    wiring as production. Any seam (attribute or env file) is REFUSED in
    real mode — BLOCKED_TEST_HOOK_IN_REAL_MODE, nothing written."""
    seam = getattr(args, "pm_probe", None)
    env_path = os.environ.get("PAPERTRADE_PM_PROBE_JSON")
    if (seam is not None or env_path) and not getattr(args, "sandbox", False):
        raise BlockError("BLOCKED_TEST_HOOK_IN_REAL_MODE",
                         "pm_probe rehearsal hooks are refused in real mode",
                         EXIT_BLOCKED_OTHER)
    if getattr(args, "sandbox", False) and env_path:
        table = json.loads(Path(env_path).read_text())

        def seam(fx, stake):
            mid = fx.get("match_id") if isinstance(fx, dict) else \
                getattr(fx, "match_id", None)
            return table.get(str(mid))
    return seam


def pm_quote_rows_for_fixtures(args, fixtures, league, now, led=None,
                               core=None) -> list:
    """PM-CUTOVER path (feature gate ON only): the Polymarket book-walk is
    the SINGLE decision quote source. Any PM failure/missing leg => NOT_RUN
    refusal (no Odds API fallback, no inference).

    Identity law (owner 2026-10-21): the PM event is NEVER assumed from the
    fixture id — NBA/WNBA join by BOTH pinned team names (2-outcome
    moneyline market), SOCCER joins the three YES/NO markets of ONE event;
    the fixture<->PM crosswalk (event/market/token ids) is journaled with
    every quote. Both/all legs walk the CLOB book at the REAL current stake
    (v3 1% equity) — never a hardcoded probe stake, never AWAY = 1 - HOME."""
    from .pm_quote_source import QuoteSourceRouter
    from . import pm_moneyline as PMM
    sandbox = bool(getattr(args, "sandbox", False))
    seam = _pm_probe_seam(args)
    if seam is not None and not sandbox:
        raise BlockError("BLOCKED_TEST_HOOK_IN_REAL_MODE",
                         "pm_probe is a rehearsal hook; refused in real mode",
                         EXIT_BLOCKED_OTHER)
    stake = core.stake_for_decision(led.equity_cents())
    if stake <= 0:
        raise BlockError("NOT_RUN_PM_QUOTE",
                         f"stake law yields {stake}c on equity "
                         f"{led.equity_cents()}c", EXIT_BLOCKED_OTHER)
    router = QuoteSourceRouter(cutover_active=True,
                               data_root=Path(args.data_root), sandbox=sandbox)
    rows = []
    for f in fixtures:
        crosswalk = {"fixture_id": f.match_id, "league": league,
                     "home": f.home, "away": f.away}
        if league in ("NBA", "WNBA") or league.startswith("NCAA-"):
            if seam is not None:
                q = seam({"match_id": f.match_id, "home": f.home,
                          "away": f.away}, stake)
            else:
                ev, ml = PMM.discover_and_join(
                    home=f.home, away=f.away, kickoff_utc=f.kickoff_utc,
                    data_root=Path(args.data_root), sandbox=sandbox)
                if ev is None:
                    raise BlockError("NOT_RUN_PM_QUOTE",
                                     f"PM event join failed for "
                                     f"{f.match_id}: {ml}", EXIT_BLOCKED_OTHER)
                crosswalk.update({"pm_event_id": str(ev.get("id")),
                                  "pm_event_title": str(ev.get("title"))[:120]})
                q = router.quote(league=league,
                                 event_id=str(ev.get("id")),
                                 home=f.home, away=f.away,
                                 stake_cents=stake)
            if not q or not q.get("all_present"):
                raise BlockError("NOT_RUN_PM_QUOTE",
                                 f"PM book-walk failed for {f.match_id}",
                                 EXIT_BLOCKED_OTHER)
            # A YES ask is a $-price in [0,1]; the EV law consumes DECIMAL
            # odds — the executable conversion is 1 / VWAP (the walk's
            # average fill across levels at the real stake). best_ask stays
            # in the evidence and NEVER enters the gate math. AWAY is never
            # inferred as 1 - HOME; each leg walked on its own token.
            odds = {leg: round(1.0 / l["vwap_ask"], 6)
                    for leg, l in q["legs"].items()}
            src = "PM_CLOB_WALK_2WAY"
        elif league == "SOCCER":
            if seam is not None:
                q = seam({"match_id": f.match_id, "home": f.home,
                          "away": f.away}, stake)
            else:
                ev, legs_m = PMM.discover_and_join_3yes(
                    home=f.home, away=f.away,
                    data_root=Path(args.data_root), sandbox=sandbox)
                if ev is None:
                    raise BlockError("NOT_RUN_PM_QUOTE",
                                     f"PM 3-YES join failed for "
                                     f"{f.match_id}: {legs_m}",
                                     EXIT_BLOCKED_OTHER)
                crosswalk.update({"pm_event_id": str(ev.get("id")),
                                  "pm_event_title": str(ev.get("title"))[:120]})
                q = router.quote(league=league,
                                 event_id=str(ev.get("id")),
                                 home=f.home, away=f.away,
                                 market_ids={leg: str(m.get("id"))
                                             for leg, m in legs_m.items()},
                                 stake_cents=stake)
            if not q or not q.get("all_present"):
                raise BlockError("NOT_RUN_PM_QUOTE",
                                 f"PM 3-YES walk incomplete for "
                                 f"{f.match_id}", EXIT_BLOCKED_OTHER)
            # same ask->decimal-odds law as the 2-way leg (executable VWAP)
            odds = {leg: round(1.0 / l["vwap_ask"], 6)
                    for leg, l in q["legs"].items()
                    if l.get("best_ask") is not None}
            if set(odds) != {"HOME", "DRAW", "AWAY"}:
                raise BlockError("NOT_RUN_PM_QUOTE",
                                 f"PM 3-YES odds incomplete for "
                                 f"{f.match_id}: {sorted(odds)}",
                                 EXIT_BLOCKED_OTHER)
            src = "PM_CLOB_WALK_3YES"
        else:
            raise BlockError("NOT_RUN_PM_QUOTE",
                             f"no PM quote law for league {league}",
                             EXIT_BLOCKED_OTHER)
        payload = json.dumps({"match_id": f.match_id, "odds": odds,
                              "pm": q.get("event_id")}, sort_keys=True)
        rows.append({
            "type": "MARKET_QUOTE", "league": league,
            "match_id": f.match_id, "home": f.home, "away": f.away,
            "kickoff_utc": f.kickoff_utc, "bookmaker": "POLYMARKET_CLOB",
            "market": ("moneyline_2way" if league in ("NBA", "WNBA")
                       else "three_yes_1x2"), "odds": odds,
            "fetch_ts_utc": now, "source_last_update_utc": now,
            "commence_time_utc": f.kickoff_utc,
            "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "mode": "PM_CUTOVER", "source_ref": src,
            "stake_walk_cents": stake,
            "pm_crosswalk": crosswalk,
            "pm_walk": q})
    return rows


def cmd_quote(args) -> dict:
    _r = maybe_wsl(args, "quote")
    if _r is not None:
        return _r
    require_gate(args)
    verify_pins(roots=_roots_from_args(args))
    now = now_of(args)
    league = args.league
    fixtures = fixtures_for(args, league, args.date)
    if not fixtures:
        return {"league": league, "date": args.date, "fixtures": 0,
                "note": "no upcoming fixtures for this date"}
    check_anchor(fixtures, league, now)          # quotes obey the same refusal
    core, led = open_ledger(args, create=True)
    existing = quote_index(led)
    written, skipped = [], []
    flags = papertrade_flags(args)
    if args.sandbox:
        # Sandbox rehearsal of the cutover chain: with the flag ON and the
        # pm_probe seam injected the sandbox walks the SAME PM wiring (join
        # -> crosswalk -> per-leg walk at the real stake -> append). Without
        # the seam the rehearsal keeps the labeled SYNTHETIC book (never a
        # silent live network call from a rehearsal).
        if flags["pm_cutover_active"] and \
                _pm_probe_seam(args) is not None:
            fresh = [f for f in fixtures
                     if f.match_id not in existing and
                     f.match_id not in led.decided_match_ids()]
            rows = pm_quote_rows_for_fixtures(args, fresh, league, now,
                                              led=led, core=core)
            for r in rows:
                led.append(r)
            return {"league": league, "date": args.date, "now_utc": now,
                    "written": [r["match_id"] for r in rows],
                    "mode": "PM_CUTOVER_SANDBOX_SEAM", "rows": len(rows),
                    "sandbox": True}
        for f in fixtures:
            if f.match_id in existing:
                skipped.append(f.match_id)
                continue
            p = A.synthetic_three_way_p(f.match_id) if league == "SOCCER" \
                else A.synthetic_two_way_p(f.match_id)
            odds = A.synthetic_odds(f.match_id, p)
            payload = json.dumps({"match_id": f.match_id, "odds": odds,
                                  "synthetic": True}, sort_keys=True)
            row = {
                "type": "MARKET_QUOTE", "league": league, "match_id": f.match_id,
                "home": f.home, "away": f.away, "kickoff_utc": f.kickoff_utc,
                "bookmaker": "SYNTHETIC_BOOK (rehearsal)", "market": "h2h",
                "odds": odds, "fetch_ts_utc": now,
                "source_last_update_utc": now,
                "commence_time_utc": f.kickoff_utc,
                "payload_sha256": __import__("hashlib").sha256(
                    payload.encode()).hexdigest(),
                "key_fingerprint": "sandbox-synthetic-00",
                "mode": "SYNTHETIC",
                "source_ref": "SYNTHETIC_ODDS_REHEARSAL (no market data pre-GO)",
            }
            led.append(row)
            written.append(f.match_id)
        return {"league": league, "date": args.date, "now_utc": now,
                "written": written, "skipped_existing": skipped,
                "mode": "SYNTHETIC", "sandbox": True}
    if flags["pm_cutover_active"] or league.startswith("NCAA-"):
        # Cutover law: PM is the ONLY decision source; failures => NOT_RUN,
        # never an Odds API fallback. The NCAA lanes (W5.4) are BORN on this
        # law — they quote PM even pre-GO (no Odds API legacy exists for
        # them); both-cuts quote rows are APPENDED (rerun-safe) so decide
        # consumes the in-ledger evidence.
        decided = led.decided_match_ids()
        existing = quote_index(led)
        fresh = [f for f in fixtures
                 if f.match_id not in existing and f.match_id not in decided]
        rows = pm_quote_rows_for_fixtures(args, fresh, league, now,
                                          led=led, core=core)
        for r in rows:
            led.append(r)
        return {"league": league, "date": args.date, "now_utc": now,
                "written": [r["match_id"] for r in rows],
                "skipped_existing": sorted(existing & {f.match_id for f in
                                                       fixtures}),
                "mode": "PM_CUTOVER", "rows": len(rows)}
    # ---- real capture: core quota-guarded client, registered sport keys ----
    odds_mod = core.odds_client
    quota = odds_mod.QuotaLedger(
        state_path=Path(args.data_root) / "data" / "quota_state.json",
        journal_path=Path(args.data_root) / "data" / "quota_journal.jsonl")
    try:
        client = odds_mod.OddsClient(quota=quota)
    except (FileNotFoundError, PermissionError, ValueError, OSError) as e:
        raise BlockError("BLOCKED_KEY",
                         f"key hygiene failure: {type(e).__name__}: {e}",
                         EXIT_BLOCKED_KEY)
    # W1.2: credit calls additionally obey the PROVIDER-credit meter (the
    # provider debits 2 credits per basketball odds call; the pinned
    # internal counter books 1 — the guard caps and reconciles in the
    # provider's own unit, pinned bytes untouched).
    from research.papertrade_exec.quota_guard import (GuardedClient,
                                                      ProviderQuotaSkip)
    guard = _provider_quota_guard_for(args)
    client = GuardedClient(client, guard)
    keys = _soccer_sport_keys() if league == "SOCCER" \
        else [DEFAULT_SPORT_KEYS[league]]
    decided = led.decided_match_ids()
    bodies, hdrs, quota_skip = [], None, None
    for key in keys:
        try:
            body, hdrs = client.get_odds(key)
        except odds_mod.QuotaSkip as qs:
            quota_skip = qs
            break
        except ProviderQuotaSkip as qs:
            quota_skip = qs
            break
        except odds_mod.KeyHalted as kh:
            raise BlockError("BLOCKED_KEY", f"HALT_KEY engaged: {kh}", EXIT_BLOCKED_KEY)
        except Exception as e:
            raise BlockError("BLOCKED_ODDS_API",
                             f"odds capture failed for {key}: "
                             f"{type(e).__name__}: {e}", EXIT_BLOCKED_OTHER)
        bodies.append(json.loads(body))
    if quota_skip is not None:
        # No partial capture: a mid-loop skip refuses the WHOLE mapping
        # (conservative) and journals every not-yet-quoted fixture.
        journaled = journal_quota_skip(led, fixtures, now, str(quota_skip),
                                       existing, decided=decided)
        return {"league": league, "date": args.date, "quota_skip": True,
                "journaled": journaled}
    body = json.dumps([ev for b in bodies for ev in b]).encode()
    rows, journals = map_odds_payload(fixtures, body, now, league,
                                      client.fingerprint)
    plan_w = _quote_write_plan(rows, journals, existing, decided)
    written, skipped, journaled = [], [], []
    for r in plan_w["write"]:
        led.append(r)
        written.append(r["match_id"])
    for j in plan_w["journal"]:
        led.append_decision(j, recheck=in_lock_recheck_for(led, args, now))
        journaled.append(j["match_id"])
    return {"league": league, "date": args.date, "captured_bytes": len(body),
            "written": written,
            "skipped_existing": plan_w["skipped_existing"],
            "skipped_decided": plan_w["skipped_decided"],
            "journaled": journaled, "mode": "REAL", "sandbox": False,
            "quota_remaining": (hdrs or {}).get("x-requests-remaining")}


def _quote_write_plan(rows, journals, existing: dict, decided: set) -> dict:
    """Append plan for a real capture (rerun-safe, append-only):
    quote rows are written only for never-quoted, never-decided matches; NO_QUOTE
    journals only for never-decided matches (a decided match is terminal — its
    journaled reason stands; nothing is overwritten or duplicated)."""
    to_write, skipped_existing, skipped_decided = [], [], []
    for r in rows:
        if r["match_id"] in existing:
            skipped_existing.append(r["match_id"])
        elif r["match_id"] in decided:
            skipped_decided.append(r["match_id"])
        else:
            to_write.append(r)
    written_ids = {r["match_id"] for r in to_write}
    to_journal = [j for j in journals
                  if j["match_id"] not in existing
                  and j["match_id"] not in written_ids
                  and j["match_id"] not in decided]
    return {"write": to_write, "journal": to_journal,
            "skipped_existing": skipped_existing,
            "skipped_decided": skipped_decided}


WNBA_FULL_NAMES = {
    "ATL": "Atlanta Dream", "CHI": "Chicago Sky", "CONN": "Connecticut Sun",
    "DAL": "Dallas Wings", "GS": "Golden State Valkyries",
    "IND": "Indiana Fever", "LA": "Los Angeles Sparks", "LV": "Las Vegas Aces",
    "MIN": "Minnesota Lynx", "NY": "New York Liberty",
    "PHX": "Phoenix Mercury", "SEA": "Seattle Storm",
    "WAS": "Washington Mystics",
}


def _full_name(league: str, abbr: str) -> str:
    return WNBA_FULL_NAMES.get(abbr.strip().upper(), abbr) if league == "WNBA" \
        else abbr


def in_lock_recheck_for(led, args, now, capital_law: int = 2):
    """Core in-lock recheck bound to this runner's GO state (journal rows are
    stake-0; the recheck keeps them lawful under the append_decision law).
    capital_law passes the resolved CAPITAL-V3 version through to the pinned
    core (2 = pre-v3 law). Resolves the PINNED core (spt_core) via the
    package loader — the core is never importable as `research.papertrade`
    from this worktree."""
    ok, _why = exec_go_state(
        Path(args.sandbox_control_dir) if getattr(args, "sandbox", False)
        else CONTROL_DIR,
        Path(args.sandbox_registry) if getattr(args, "sandbox", False)
        else REGISTRY_PATH)
    return load_pinned_core(roots=_roots_from_args(args)).risk.in_lock_recheck(
        led, now, ok, capital_law=capital_law)


def map_odds_payload(fixtures, payload_bytes: bytes, now: str, league: str,
                     key_fingerprint: str):
    """Map a The-Odds-API /odds payload (pinnacle, decimal) to MARKET_QUOTE
    rows, 1:1 fail-closed against the pinned fixtures: provider event must
    match on exact commence_time AND the full-name team set; pinnacle must be
    present with the h2h market and every required leg. No fuzzy matching;
    unmatched/malformed fixtures are JOURNALED (DECISION NO_QUOTE), never
    dropped. Per-row PIT law: fetch_ts < tip - 6h strict."""
    events = json.loads(payload_bytes)
    by_key = {}
    for ev in events:
        names = frozenset({norm_team(ev.get("home_team", "")),
                           norm_team(ev.get("away_team", ""))})
        by_key[(ev.get("commence_time"), names)] = ev
    need = 3 if league == "SOCCER" else 2
    rows, journals = [], []

    def _journal(f, reason):
        journals.append({
            "type": "DECISION", "league": f.league, "match_id": f.match_id,
            "competition": f.competition, "home": f.home, "away": f.away,
            "kickoff_utc": f.kickoff_utc, "decided_at_utc": now,
            "status": "NO_QUOTE", "reason": reason,
            "stake_cents": 0, "chosen_leg": None,
        })

    for f in fixtures:
        names = frozenset({norm_team(_full_name(league, f.home)),
                           norm_team(_full_name(league, f.away))})
        ev = by_key.get((f.kickoff_utc, names))
        if ev is None:
            _journal(f, "no provider event matched 1:1 (commence_time + team "
                        "set); fail-closed")
            continue
        books = {b.get("key"): b for b in ev.get("bookmakers", [])}
        pin = books.get("pinnacle")
        if pin is None:
            _journal(f, "pinnacle absent from payload; fail-closed")
            continue
        last_update = pin.get("last_update") or ""
        mkt = next((m for m in pin.get("markets", []) if m.get("key") == "h2h"),
                   None)
        if mkt is None:
            _journal(f, "h2h market missing from pinnacle payload")
            continue
        outcomes = {}
        for o in mkt.get("outcomes", []):
            try:
                outcomes[str(o.get("name", "")).strip()] = float(o.get("price"))
            except (TypeError, ValueError):
                pass
        nh, na = norm_team(_full_name(league, f.home)), \
            norm_team(_full_name(league, f.away))
        odds = {}
        for oname, price in outcomes.items():
            n = norm_team(oname)
            if n == nh:
                odds["HOME"] = price
            elif n == na:
                odds["AWAY"] = price
            elif n in ("draw", "x"):
                odds["DRAW"] = price
        need_legs = ("HOME", "DRAW", "AWAY") if league == "SOCCER" \
            else ("HOME", "AWAY")
        missing = [k for k in need_legs if k not in odds]
        if missing:
            _journal(f, f"quote missing required legs {missing}; fail-loud")
            continue
        tip = datetime.strptime(f.kickoff_utc, "%Y-%m-%dT%H:%M:%SZ")
        fetch = datetime.strptime(now, "%Y-%m-%dT%H:%M:%SZ")
        if (tip - fetch).total_seconds() <= 6 * 3600:
            _journal(f, "fetch inside T-6h window; PIT row law refuses storage")
            continue
        if last_update:
            try:
                if datetime.strptime(
                        last_update, "%Y-%m-%dT%H:%M:%SZ") > fetch:
                    _journal(f, "source_last_update after fetch_ts; row law")
                    continue
            except ValueError:
                pass  # non-ISO stamp kept verbatim, disclosed in the row
        ev_sha = hashlib.sha256(json.dumps(
            {"id": ev.get("id"), "commence_time": ev.get("commence_time"),
             "home_team": ev.get("home_team"), "away_team": ev.get("away_team"),
             "pinnacle": pin}, sort_keys=True).encode()).hexdigest()
        rows.append({
            "type": "MARKET_QUOTE", "league": league,
            "match_id": f.match_id, "home": f.home, "away": f.away,
            "kickoff_utc": f.kickoff_utc, "bookmaker": "pinnacle",
            "market": "h2h", "odds": odds, "fetch_ts_utc": now,
            "source_last_update_utc": last_update,
            "commence_time_utc": ev.get("commence_time"),
            "payload_sha256": ev_sha, "key_fingerprint": key_fingerprint,
            "mode": "REAL", "source_ref": "the-odds-api v4 /odds "
                                          "bookmakers=pinnacle",
        })
    return rows, journals


def journal_quota_skip(led, fixtures, now: str, why: str, existing: dict,
                       decided: set | None = None) -> list:
    """Journaled QUOTA_SKIP DECISION rows (skipped matches would silently
    vanish; the law journals them instead). No network happened (the core
    client's precheck raises before any call). Already-decided matches are
    terminal — never re-journaled (append-only, one selection law)."""
    decided = decided or set()
    journaled = []
    for f in fixtures:
        if f.match_id in existing or f.match_id in decided:
            continue
        row = {"type": "DECISION", "league": f.league, "match_id": f.match_id,
               "competition": f.competition, "home": f.home, "away": f.away,
               "kickoff_utc": f.kickoff_utc, "decided_at_utc": now,
               "status": "QUOTA_SKIP", "reason": why,
               "stake_cents": 0, "chosen_leg": None}
        led.append_decision(row)
        journaled.append(f.match_id)
    return journaled


# ------------------------------------------------------------------- decide --

def norm_team(s: str) -> str:
    # W0.1 (PAPERDESK-FIXALL-NCAA-V1): ONE normalization runner-wide
    # (casefold + strip non-alnum). The previous casefold+space-collapse
    # variant was a second algorithm of the same concept — identity now has
    # exactly one normalization (crosswalk resolution lives in team_names).
    from research.papertrade_exec import team_names
    return team_names.norm(s)


def crosswalk_ok(fixture, forecast_row, quote_row) -> tuple[bool, str]:
    """1:1 identity crosswalk, fail-closed: fixture / forecast / quote must
    agree on normalized team names (and kickoff where present)."""
    if forecast_row is None:
        return False, "no forecast row"
    if quote_row is None:
        return False, "no quote row"
    if norm_team(forecast_row["home"]) != norm_team(fixture.home) or \
            norm_team(forecast_row["away"]) != norm_team(fixture.away):
        return False, "fixture/forecast team mismatch"
    if quote_row.get("home") and quote_row.get("away"):
        if norm_team(quote_row["home"]) != norm_team(fixture.home) or \
                norm_team(quote_row["away"]) != norm_team(fixture.away):
            return False, "fixture/quote team mismatch"
    if quote_row.get("kickoff_utc") and \
            quote_row["kickoff_utc"] != fixture.kickoff_utc:
        return False, "fixture/quote kickoff mismatch"
    return True, "1:1"


# --- W1.3 / W1.4 / W1.5 decision-path blocks (PAPERDESK-FIXALL-NCAA-V1,
#     owner work package 2026-10-21; laws sourced from laws.py) -------------

def constant_forecast_block(fc_rows: list[dict]) -> None:
    """W1.3: when EVERY forecast of one league batch carries the identical
    p dict (batch variance 0), the model carries no per-match information —
    the runtime audit measured 14/14 NBA forecasts at p=0.640065 (the pure
    HCA cold-start: corpus refresh lookback=0 => zero FINAL rows => every
    team at R0=1500). Root cause fixed at the caller (refresh now fetches
    completed game-days); THIS is the permanent decide-path block: the whole
    batch refuses (high incident via CADENCE_DECIDE_BLOCKED), no bet is
    placed on a constant."""
    rows = [r for r in fc_rows if r.get("p")]
    if len(rows) >= 2:
        first = json.dumps(rows[0]["p"], sort_keys=True)
        if all(json.dumps(r["p"], sort_keys=True) == first for r in rows):
            raise BlockError(
                "BLOCKED_CONSTANT_FORECAST",
                f"all {len(rows)} forecasts of this batch carry the "
                f"identical p ({first[:80]}…) — batch variance 0; the "
                "model carries no per-match information and NOTHING may "
                "be placed (W1.3)", EXIT_BLOCKED_OTHER)


def quote_odds_signature(quote_row: dict | None) -> str | None:
    """Stable signature of the DECISION-relevant odds payload (W1.4)."""
    odds = (quote_row or {}).get("odds") or {}
    if not odds:
        return None
    norm = {k: round(float(v), 6) for k, v in sorted(odds.items())}
    return hashlib.sha256(json.dumps(norm, sort_keys=True)
                          .encode()).hexdigest()


def _pm_family(quote_row: dict | None) -> bool:
    row = quote_row or {}
    return ("polymarket" in str(row.get("bookmaker", "")).casefold()
            or str(row.get("source_ref", "")).startswith("PM_CLOB"))


def quote_collision(led, match_id: str, quote_row: dict | None) -> str | None:
    """W1.4: the SAME quote snapshot must never serve two fixtures (runtime
    evidence: WSL M39 DRAW odds == M42 DRAW odds and M38 == M41 identical to
    15 decimal places — one PM snapshot reused across matches). Two arms:
      (a) identical non-trivial payload_sha256 (the snapshot bytes reused
          verbatim — precise for every bookmaker);
      (b) for PM book-walk rows only, EXACT float equality of the full odds
          vector (long VWAP floats that match to the last digit are one
          snapshot; coarse bookmaker prices like 1.85/2.05 legitimately
          repeat across fixtures and are NEVER a collision).
    Returns the earlier colliding match_id, or None."""
    if not quote_row:
        return None
    league = quote_row.get("league")
    sig_sha = str(quote_row.get("payload_sha256") or "")
    sig_sha_real = bool(sig_sha) and sig_sha != "0" * 64
    pm = _pm_family(quote_row)
    odds_exact = {k: float(v)
                  for k, v in (quote_row.get("odds") or {}).items()}
    for r in led.rows:
        if r.get("type") != "MARKET_QUOTE" or \
                r.get("match_id") == match_id or r.get("league") != league:
            continue
        r_sha = str(r.get("payload_sha256") or "")
        if sig_sha_real and r_sha == sig_sha:
            return r.get("match_id")
        if pm and _pm_family(r) and odds_exact and \
                {k: float(v) for k, v in (r.get("odds") or {}).items()} == \
                odds_exact:
            return r.get("match_id")
    return None


def pm_ev_crosscheck(args, fixture, p_frozen: dict, chosen_leg: str) -> dict:
    """W1.5 second-source cross-check: an INDEPENDENT quote for the same
    fixture from Polymarket (read-only public GET, free) — EV recomputed
    under the PM fee law 0.05·p·(1−p). Sandbox seam `args.pm_crosscheck`
    (fixture -> {'ok', 'odds': {leg: decimal}}) is rehearsal-only and
    refused in real mode. Returns {'ok', 'ev_net', 'odds'|'why'}."""
    seam = getattr(args, "pm_crosscheck", None)
    if seam is not None:
        if not getattr(args, "sandbox", False):
            raise BlockError("BLOCKED_TEST_HOOK_IN_REAL_MODE",
                             "pm_crosscheck rehearsal hook refused in real "
                             "mode", EXIT_BLOCKED_OTHER)
        return seam({"match_id": fixture.match_id, "home": fixture.home,
                     "away": fixture.away})
    from . import pm_moneyline as PMM
    try:
        ev, ml = PMM.discover_and_join(
            home=fixture.home, away=fixture.away,
            kickoff_utc=fixture.kickoff_utc,
            data_root=Path(args.data_root),
            sandbox=bool(getattr(args, "sandbox", False)))
    except Exception as e:                 # network etc — cross-check
        return {"ok": False, "why": f"PM cross-check failed: "
                                    f"{type(e).__name__}: {e}"}
    if ev is None:
        return {"ok": False, "why": f"PM cross-check no join: {ml}"}
    mapped = PMM.map_outcomes_to_legs(
        [str(o) for o in (json.loads(ml["outcomes"])
                          if isinstance(ml.get("outcomes"), str)
                          else ml.get("outcomes") or [])],
        home=fixture.home, away=fixture.away)
    if "error" in mapped:
        return {"ok": False, "why": f"PM cross-check map: {mapped['error']}"}
    prices = ml.get("outcomePrices")
    if isinstance(prices, str):
        prices = json.loads(prices)
    if not isinstance(prices, list):
        return {"ok": False, "why": "PM cross-check outcomePrices unreadable"}
    odds = {}
    for pos, leg in enumerate(mapped["legs"]):
        try:
            ask = float(prices[pos])
        except (TypeError, ValueError, IndexError):
            return {"ok": False, "why": "PM cross-check price unreadable"}
        if ask <= 0:
            return {"ok": False, "why": f"PM cross-check ask {ask} for "
                                        f"{leg}"}
        odds[leg] = round(1.0 / ask, 6)
    d = odds.get(chosen_leg)
    p_leg = (p_frozen or {}).get(chosen_leg)
    if not d or not p_leg:
        return {"ok": False, "why": f"PM cross-check missing {chosen_leg}"}
    fee = laws.PM_TAKER_FEE_RATE * p_leg * (1.0 - p_leg)
    return {"ok": True, "odds": odds,
            "ev_net": p_leg * d - 1.0 - fee,
            "source_ref": f"PM_GAMMA event={ev.get('id')} "
                          "(indicative outcomePrices; W1.5 cross-check)"}


def ev_outlier_disposition(args, led, fixture, dec: dict,
                           quote_row: dict | None, now: str) -> dict:
    """W1.5 quarantine law for EV_net > 100% (a live desk already placed
    and LOST one: WSL M39 at EV +196.68%). Returns a terminal-or-not
    decision row + the incident kind:
      * second source ALSO > 100%  -> NOT_PLACED_EV_OUTLIER (terminal:
        both sources agree the candidate is an outlier — never placed);
      * second source disagrees or unavailable -> QUARANTINED_EV_OUTLIER
        (non-terminal: the match may re-enter decide ONLY against a FRESH
        quote captured after the quarantine and with a PM cross-check on
        file; after 3 quarantines -> NOT_PLACED_EV_OUTLIER terminal).
    The 5% gate is untouched; this is an additional outlier law."""
    from research.papertrade_exec import laws
    best_leg, best_ev = max(
        ((leg, ev) for leg, ev in (dec.get("ev_net_by_leg") or {}).items()),
        key=lambda kv: kv[1], default=(None, None))
    cross = pm_ev_crosscheck(args, fixture, dec.get("p_frozen") or {},
                             best_leg or dec.get("chosen_leg") or "HOME")
    quarantines = [r for r in led.rows if r.get("type") == "DECISION"
                   and r.get("match_id") == fixture.match_id
                   and r.get("status") == "QUARANTINED_EV_OUTLIER"]
    base = {"type": "DECISION", "league": fixture.league,
            "match_id": fixture.match_id,
            "competition": fixture.competition,
            "home": fixture.home, "away": fixture.away,
            "kickoff_utc": fixture.kickoff_utc, "decided_at_utc": now,
            "ev_outlier_evidence": {
                "best_leg": best_leg, "best_ev_net": best_ev,
                "threshold": laws.EV_OUTLIER_THRESHOLD,
                "pm_crosscheck": cross}, "stake_cents": 0,
            "chosen_leg": None}
    if cross.get("ok") and cross.get("ev_net") is not None and \
            cross["ev_net"] > laws.EV_OUTLIER_THRESHOLD:
        base.update({"status": "NOT_PLACED_EV_OUTLIER",
                     "reason": (f"EV_outlier {best_ev:.4f} on {best_leg}; "
                                f"second source AGGREGATES the outlier "
                                f"(PM EV {cross['ev_net']:.4f}) — never "
                                "placed (W1.5)")})
        return base, "EV_OUTLIER_QUARANTINED"
    if len(quarantines) >= 3:
        base.update({"status": "NOT_PLACED_EV_OUTLIER",
                     "reason": (f"EV_outlier {best_ev:.4f} on {best_leg}; "
                                f"{len(quarantines)} prior quarantines "
                                "without a clean second-source "
                                "resolution — terminal (W1.5)")})
        return base, "EV_OUTLIER_QUARANTINED"
    why = (f"PM second-source EV {cross.get('ev_net'):.4f} disagrees"
           if cross.get("ok") else
           f"PM second-source unavailable: {cross.get('why')}")
    base.update({"status": "QUARANTINED_EV_OUTLIER",
                 "reason": (f"EV_outlier {best_ev:.4f} on {best_leg} > "
                            f"{laws.EV_OUTLIER_THRESHOLD}; {why} — "
                            "quarantined: fresh independent re-quote "
                            "required before any placement (W1.5)")})
    return base, "EV_OUTLIER_QUARANTINED"


def latest_quote_for(led, match_id: str) -> dict | None:
    """The most recent MARKET_QUOTE row for a match (quarantine re-entry
    consumes the FRESH quote, never the pre-quarantine snapshot)."""
    rows = [r for r in led.rows if r.get("type") == "MARKET_QUOTE"
            and r.get("match_id") == match_id]
    if not rows:
        return None
    return rows[-1]


def fresh_quote_available(led, match_id: str, after_utc: str) -> bool:
    q = latest_quote_for(led, match_id)
    return bool(q and str(q.get("fetch_ts_utc", "")) > str(after_utc))


def ai_boundary_review(candidate: dict, gates_ctx: dict,
                       flags: dict) -> dict:
    """LEGACY SANDBOX EVALUATOR — UNWIRED (W4.1, PAPERDESK-FIXALL-NCAA-V1):
    the decide path now runs apply_ai_gate_v2 (hash-locked ALLOW|VETO).
    This legacy evaluator is retained for the sandbox battery/display only
    and is called from NO decide path."""
    if not flags.get("ai_authority_active"):
        return {"action": "DISABLED", "why": "ai_authority OFF (pre-GO)"}
    from .decision_pipeline import evaluate_ai_gate
    decision, gates, reason = evaluate_ai_gate(
        ai_action=candidate.get("ai_action", "ABSTAIN"),
        ai_proposed_leg=candidate.get("ai_proposed_leg"),
        chosen_leg=gates_ctx["chosen_leg"],
        p_frozen=gates_ctx["p_frozen"], odds_frozen=gates_ctx["odds_frozen"],
        ev_net_by_leg=gates_ctx["ev_net_by_leg"],
        stake_cents=gates_ctx["stake_cents"],
        equity_cents=gates_ctx["equity_cents"],
        open_exposure_cents=gates_ctx["open_exposure_cents"],
        open_cap_cents=gates_ctx["open_cap_cents"],
        drawdown_frac=gates_ctx["drawdown_frac"],
        drawdown_paused=gates_ctx["drawdown_paused"],
        snapshot_before_anchor=gates_ctx["snapshot_before_anchor"],
        anchor_passed=gates_ctx["anchor_passed"],
        quote_present=gates_ctx["quote_present"],
        depth_walked=gates_ctx["depth_walked"], fees_once=True)
    return {"action": candidate.get("ai_action"), "decision": decision,
            "gates": gates, "reason": reason}


def _map_ai_opinion(op: dict) -> dict:
    """LEGACY SANDBOX MAPPING — UNWIRED (W4.1): the v2 gate reads
    schema-validated ALLOW|VETO opinions from ai_gate_v2; this legacy
    mapper is retained for the sandbox battery only.
    Normalize one ai_review opinion record to the runner gate vocabulary
    KEEP | VETO | SWITCH | ABSTAIN. Fail-closed: anything that is not an
    unambiguous, COMPLETED, pre-deadline actionable opinion is ABSTAIN (owner
    law: ABSTAIN / error / missing evidence / post-deadline => NOT placed).
    The AI NEVER supplies numbers — only the action + proposed leg travel;
    probabilities/prices/EV come exclusively from the frozen snapshot."""
    a = (lambda k, d=None: (op.get(k) if op.get(k) not in
                            (None, "", "None", "nil") else d))
    status = str(op.get("status") or "")
    if status != "COMPLETED":
        return {"action": "ABSTAIN", "proposed_leg": None,
                "why": f"opinion status {status!r} != COMPLETED"}
    completed, deadline = a("completedAtUTC"), a("deadlineUTC")
    if completed and deadline and str(completed) > str(deadline):
        return {"action": "ABSTAIN", "proposed_leg": None,
                "why": "opinion completed after its deadline"}
    verdict = str(a("verdict") or "").strip().upper()
    rec = str(a("recommendedAction") or "").strip().upper()
    leg = a("proposedLeg")
    leg = leg if leg in ("HOME", "DRAW", "AWAY") else None
    if verdict == "VETO" or rec == "VETO":
        return {"action": "VETO", "proposed_leg": None,
                "why": f"verdict={verdict or rec}"}
    if verdict in ("CHALLENGE", "ALTERNATIVE") and leg:
        return {"action": "SWITCH", "proposed_leg": leg,
                "why": f"verdict={verdict}"}
    if rec == "SWITCH" and leg:
        return {"action": "SWITCH", "proposed_leg": leg,
                "why": "recommended_action=SWITCH"}
    if rec == "KEEP":
        return {"action": "KEEP", "proposed_leg": None,
                "why": "recommended_action=KEEP"}
    return {"action": "ABSTAIN", "proposed_leg": None,
            "why": (f"verdict={verdict!r} recommendedAction={rec!r}"
                    " not actionable")}


def load_ai_opinion(args, match_id: str) -> dict:
    """LEGACY SANDBOX READER — UNWIRED (W4.1): the v2 gate reads
    hash-locked opinions via ai_gate_v2.load_opinion_for.
    Latest ai_review opinion for the match (opinions dir), normalized.
    Sandbox seam `args.ai_opinion` (dict) or PAPERTRADE_AI_OPINION_JSON
    ({match_id: record}) is rehearsal-only and refused in real mode.
    Missing/unreadable opinion => ABSTAIN (never an order)."""
    seam = getattr(args, "ai_opinion", None)
    env_path = os.environ.get("PAPERTRADE_AI_OPINION_JSON")
    if (seam is not None or env_path) and \
            not getattr(args, "sandbox", False):
        raise BlockError("BLOCKED_TEST_HOOK_IN_REAL_MODE",
                         "ai_opinion rehearsal hooks are refused in real "
                         "mode", EXIT_BLOCKED_OTHER)
    if seam is None and getattr(args, "sandbox", False) and env_path:
        seam = json.loads(Path(env_path).read_text()).get(str(match_id))
    if seam is not None:
        return _map_ai_opinion(seam)
    op_dir = Path(args.data_root) / "ai_review" / "opinions"
    try:
        files = sorted(op_dir.glob(f"{match_id}_*.json"))
        if not files:
            return {"action": "ABSTAIN", "proposed_leg": None,
                    "why": "no ai_review opinion on file"}
        latest = files[-1]          # timestamped names sort chronologically
        op = json.loads(latest.read_text())
        mapped = _map_ai_opinion(op)
        mapped["opinion_file"] = latest.name
        mapped["opinion_sha256"] = hashlib.sha256(
            latest.read_bytes()).hexdigest()
        return mapped
    except Exception as e:
        return {"action": "ABSTAIN", "proposed_leg": None,
                "why": f"opinion read failed: {type(e).__name__}: {e}"}


def ai_gate_context(dec: dict, quote_row: dict, *, led, core,
                    capital_law: int) -> dict:
    """LEGACY SANDBOX CONTEXT — UNWIRED (W4.1): kept for the sandbox
    battery; the decide path no longer calls it.
    Frozen-snapshot context for the AI boundary — ledger numbers ONLY.
    depth_walked: PM-cutover quotes carry per-leg book walks; pre-cutover
    pinned-source quotes stand in (the frozen fee/odds law)."""
    odds = quote_row.get("odds") or {}
    pm_walk = ((quote_row.get("pm_walk") or {}).get("legs")) or {}
    legs = sorted(dec.get("ev_net_by_leg") or {})
    dd = led.drawdown_frac()
    return {
        "chosen_leg": dec.get("chosen_leg"),
        "p_frozen": dec.get("p_frozen"),
        "odds_frozen": dec.get("odds_frozen"),
        "ev_net_by_leg": dec.get("ev_net_by_leg"),
        "stake_cents": dec.get("stake_cents"),
        "equity_cents": dec.get("equity_at_decision_cents"),
        "open_exposure_cents": led.open_exposure_cents(),
        "open_cap_cents": (core.OPEN_EXPOSURE_CAP_V3_CENTS
                           if capital_law == 3
                           else core.OPEN_EXPOSURE_CAP_CENTS),
        "drawdown_frac": dd,
        "drawdown_paused": dd >= core.DRAWDOWN_PAUSE_FRAC,
        # the deterministic engine only emits BET_PAPER pre-anchor (PIT law
        # already enforced by risk.evaluate_match on THIS frozen candidate)
        "snapshot_before_anchor": True,
        "anchor_passed": False,
        "quote_present": {leg: leg in odds for leg in legs},
        "depth_walked": ({leg: pm_walk.get(leg, {}).get("best_ask")
                          is not None for leg in legs} if pm_walk else
                         {leg: leg in odds for leg in legs}),
    }


def apply_ai_gate_v2(args, led, f, dec: dict, fc_row, quote_row,
                     now: str) -> dict | None:
    """THE single AI authority boundary, v2 (owner law; W4). Runs ONLY when
    ai_authority_active and only on a BET_PAPER candidate. Returns:
      * None                 — gate says proceed (ALLOW); dec carries the
                               ai_gate evidence block;
      * a terminal DECISION  — VETO / NO_VERDICT (caller appends + skips);
      * the string "PENDING" — no valid verdict inside the review window:
                               the candidate stays UNDECIDED (re-reviewed
                               next cadence pass until anchor-30min); the
                               silence of the AI layer never kills a bet
                               inside the window (owner QĐ2).
    The AI NEVER supplies numbers; opinions are hash-locked to the exact
    candidate (price/EV/model change => new hash => stale review void).
    M6 (U4): the whole ai_review plane follows the args.sandbox flag — a
    sandbox decide reads/writes <data-root>/sandbox/ai_review and never
    touches a byte of the real plane."""
    from research.papertrade_exec import ai_gate_v2 as G
    data_root = Path(args.data_root)
    sb = bool(getattr(args, "sandbox", False))
    chash = G.candidate_hash_for(dec, fc_row, quote_row)
    anchor = (fc_row or {}).get("anchor_utc") or ""
    op, why = G.load_opinion_for(data_root, f.match_id, chash, sandbox=sb)
    if op is not None:
        if str(op["verdict"]).strip().upper() == "VETO":   # L1 canonical
            G.clear_pending(data_root, f.match_id, "AI_VETO", sandbox=sb)
            row = {"type": "DECISION", "league": f.league,
                   "match_id": f.match_id, "competition": f.competition,
                   "home": f.home, "away": f.away,
                   "kickoff_utc": f.kickoff_utc, "decided_at_utc": now,
                   "anchor_utc": anchor,
                   "status": "NOT_PLACED_AI_VETO",
                   "reason": ("AI VETO (hash-locked opinion): " +
                              "; ".join(op.get("reason_codes") or []) +
                              f" | {op.get('summary', '')[:160]}"),
                   "ai_gate": {**G.ai_gate_block(op, why, "VETO", chash),
                               "hypothetical_leg": dec.get("chosen_leg"),
                               "hypothetical_stake_cents":
                                   dec.get("stake_cents"),
                               "hypothetical_decimal_odds":
                                   ((quote_row or {}).get("odds") or {})
                                   .get(dec.get("chosen_leg"))},
                   "stake_cents": 0, "chosen_leg": None}
            return row
        dec["ai_gate"] = G.ai_gate_block(op, why, "PLACE", chash)
        G.clear_pending(data_root, f.match_id, "AI_ALLOW", sandbox=sb)
        return None
    # no valid opinion:
    if anchor and not G.review_deadline_passed(anchor, now):
        G.pending_marker(data_root, f.match_id, chash, anchor, why,
                         sandbox=sb,
                         context={"league": f.league, "match_id": f.match_id,
                                  "home": f.home, "away": f.away,
                                  "kickoff_utc": f.kickoff_utc,
                                  "competition": f.competition,
                                  "chosen_leg": dec.get("chosen_leg"),
                                  "p_frozen": dec.get("p_frozen"),
                                  "odds_frozen": dec.get("odds_frozen"),
                                  "quote_row_sha256":
                                      (quote_row or {}).get("row_sha256"),
                                  "ev_net_by_leg": dec.get("ev_net_by_leg"),
                                  "stake_cents": dec.get("stake_cents")})
        return "PENDING"
    G.clear_pending(data_root, f.match_id, "AI_NO_VERDICT", sandbox=sb)
    row = {"type": "DECISION", "league": f.league,
           "match_id": f.match_id, "competition": f.competition,
           "home": f.home, "away": f.away, "kickoff_utc": f.kickoff_utc,
           "decided_at_utc": now, "anchor_utc": anchor,
           "status": "NOT_PLACED_AI_NO_VERDICT",
           "reason": (f"no valid hash-locked AI verdict by the review "
                      f"deadline (anchor-30m): {why} — not placed "
                      "(W4.4 owner law)"),
           "ai_gate": G.ai_gate_block(None, why, "NO_VERDICT", chash),
           "stake_cents": 0, "chosen_leg": None}
    return row


def cmd_decide(args) -> dict:
    # QD1/A7-R2: the pause check precedes EVERY lane dispatch (WSL
    # included) on the REAL plane — no lane is above an owner pause.
    pause = league_paused(args.league)
    if pause and not getattr(args, "sandbox", False):
        raise BlockError("BLOCKED_LEAGUE_PAUSED",
                         f"{args.league} is under an owner pause: "
                         f"{pause.get('reason', '')[:200]}",
                         EXIT_BLOCKED_OTHER)
    _r = maybe_wsl(args, "decide")
    if _r is not None:
        return _r
    require_gate(args)
    verify_pins(roots=_roots_from_args(args))
    core, led = open_ledger(args, create=True)
    risk = core.risk
    go_ok = True   # gate passed above; evaluate_match still re-checks PIT laws
    now = now_of(args)
    capital_law = capital_law_for(args, core)   # 2|3; absent pair => 2 (v3 §5)
    league = args.league
    if league.startswith("NCAA-"):
        from research.papertrade_exec import adapters_ncaa as AN
        AN.register_ncaa_league_law(risk, league)   # W5.1 lane law
    fixtures = fixtures_for(args, league, args.date)
    if not fixtures:
        return {"league": league, "date": args.date, "fixtures": 0}
    fc, qt = forecast_index(led), quote_index(led)
    decided = led.decided_match_ids()
    # W1.5 + U4-M4: a QUARANTINED_EV_OUTLIER row is deliberately
    # NON-terminal — the match may re-enter decide against a FRESH quote —
    # but a match with a FINAL NOT_PLACED_EV_OUTLIER row is TERMINAL: it
    # stays in `decided` and never re-enters the quarantine pool, no
    # matter how many QUARANTINED rows precede the final one. Every other
    # decided status stays terminal (one-selection law unchanged).
    terminal_outlier = {r["match_id"] for r in led.rows
                        if r.get("type") == "DECISION"
                        and r.get("status") == "NOT_PLACED_EV_OUTLIER"}
    quarantined = {r["match_id"] for r in led.rows
                   if r.get("type") == "DECISION"
                   and r.get("status") == "QUARANTINED_EV_OUTLIER"
                   and r["match_id"] not in terminal_outlier}
    effective_decided = decided - quarantined
    # W1.3: a constant forecast batch can never ground a bet.
    constant_forecast_block([fc[f.match_id] for f in fixtures
                             if f.match_id in fc])
    journaled, skipped = [], []
    for f in fixtures:
        if f.match_id in effective_decided:
            skipped.append({"match_id": f.match_id, "why": "already decided"})
            continue
        if league == "SOCCER" and not getattr(args, "sandbox", False):
            # Stage/venue law safety net (also covers matches forecasted
            # before a law window landed): outside the committed law the
            # match is journaled NOT_RUN_STAGE_LAW — terminal, never bet.
            cls = soccer_stage_law(f.competition, f.kickoff_utc[:10])
            if not cls["bet_eligible"]:
                row = stage_law_decision(f, cls, now)
                led.append_decision(row)
                journaled.append({"match_id": f.match_id,
                                  "status": row["status"],
                                  "reason": row["reason"][:120]})
                continue
        # B1R fail-closed law (SOCCER-INTL-B1R-PAPER-SWITCH-V1): a SOCCER
        # decision grounds ONLY in a validated B1R row — a B1-only match
        # journals NOT_RUN_NO_B1R_FORECAST and is terminal (never a silent
        # B1 fallback, never a late B1R backfill).
        fc_row = fc.get(f.match_id)
        if league == "SOCCER":
            b1r_switch_ts_verified(Path(args.sandbox_registry)
                                   if getattr(args, "sandbox", False)
                                   else REGISTRY_PATH)
            fc_row, b1r_why = soccer_b1r_forecast(led, f, now)
            if fc_row is None:
                row = no_b1r_decision(f, b1r_why, now)
                led.append_decision(
                    row, recheck=in_lock_recheck_for(led, args, now,
                                                     capital_law=capital_law))
                journaled.append({"match_id": f.match_id,
                                  "status": row["status"],
                                  "reason": row["reason"][:120]})
                continue
        ok, why = crosswalk_ok(f, fc_row, qt.get(f.match_id))
        # W1.5 quarantine re-entry: the fresh-quote law. A quarantined match
        # decides against the LATEST quote and only when a quote captured
        # AFTER the quarantine exists (the stale snapshot that tripped the
        # outlier is never reused).
        if f.match_id in quarantined:
            q_old = next((r for r in led.rows if r.get("type") == "DECISION"
                          and r.get("match_id") == f.match_id
                          and r.get("status") == "QUARANTINED_EV_OUTLIER"), {})
            q_row_fresh = latest_quote_for(led, f.match_id)
            if not fresh_quote_available(
                    led, f.match_id,
                    (q_old or {}).get("decided_at_utc", "")):
                # U4-M4 no-churn law: a quarantined match with NO fresh
                # quote yet must NEVER append another QUARANTINED ledger
                # row on every decide pass — the ops plane only (the
                # journaled report + one ai_review gate event) learns the
                # match is still quarantined; the ledger stays untouched
                # until a FRESH independent re-quote exists.
                journaled.append({"match_id": f.match_id,
                                  "status": "QUARANTINED_EV_OUTLIER",
                                  "reason": ("quarantine re-entry: no quote "
                                             "captured after the quarantine "
                                             "yet — still quarantined, no "
                                             "placement; no new ledger row "
                                             "(M4 no-churn)")})
                try:
                    from research.papertrade_exec import ai_gate_v2 as _G4
                    _G4.gate_event(
                        Path(args.data_root),
                        "EV_OUTLIER_STILL_QUARANTINED",
                        sandbox=bool(getattr(args, "sandbox", False)),
                        match_id=f.match_id)
                except Exception:
                    pass
                continue
            qt = {**qt, f.match_id: q_row_fresh}
        # W1.4: one odds snapshot must never serve two fixtures.
        collide = quote_collision(led, f.match_id, qt.get(f.match_id))
        if collide is not None:
            row = {"type": "DECISION", "league": f.league,
                   "match_id": f.match_id, "competition": f.competition,
                   "home": f.home, "away": f.away,
                   "kickoff_utc": f.kickoff_utc, "decided_at_utc": now,
                   "status": "NOT_RUN_QUOTE_COLLISION",
                   "reason": (f"quote odds signature identical to {collide} "
                              "— one snapshot cannot price two fixtures "
                              "(W1.4); fail-closed"),
                   "stake_cents": 0, "chosen_leg": None}
            led.append_decision(row)
            journaled.append({"match_id": f.match_id,
                              "status": row["status"],
                              "reason": row["reason"][:120]})
            continue
        dec = risk.evaluate_match(
            led, league=league, match_id=f.match_id, competition=f.competition,
            home=f.home, away=f.away, kickoff_utc=f.kickoff_utc, now_utc=now,
            forecast=fc_row, quote=qt.get(f.match_id),
            crosswalk_ok=ok, go_ok=go_ok, capital_law=capital_law)
        if league == "SOCCER" and dec.get("status") in ("BET_PAPER", "NO_EDGE"):
            # Decision cites the exact B1R row it was grounded in (map pin +
            # control reference travel with the row — switch law).
            dec["decision_forecast_row_sha256"] = fc_row["row_sha256"]
            dec["map_sha256"] = fc_row.get("map_sha256")
            dec["control_ref_row_sha256"] = fc_row.get("control_ref_row_sha256")
        # W1.5: EV outlier quarantine — EV_net above 100% is prima facie a
        # mispriced/mislabeled snapshot (the desk already placed and LOST
        # one: WSL M39 EV +196.68%). Mandatory independent re-quote +
        # second-source cross-check BEFORE anything is placed; still
        # abnormal => never placed. The 5% gate is untouched.
        if dec.get("status") == "BET_PAPER" and max(
                (dec.get("ev_net_by_leg") or {}).values() or [0.0]) > \
                laws.EV_OUTLIER_THRESHOLD:
            row, kind = ev_outlier_disposition(
                args, led, f, dec, qt.get(f.match_id), now)
            led.append_decision(
                row, recheck=risk.in_lock_recheck(led, now, go_ok,
                                                  capital_law=capital_law),
                capital_law=capital_law)
            journaled.append({"match_id": f.match_id,
                              "status": row["status"],
                              "reason": row["reason"][:120]})
            continue
        # THE single AI execution boundary, v2 (owner law, W4): AFTER the
        # deterministic gates, BEFORE the append. Flag OFF => DISABLED and
        # live behavior byte-identical to the pre-AI runner. Flag ON: the
        # candidate is hash-locked to an ALLOW/VETO opinion; no valid
        # opinion inside the review window => the candidate stays
        # UNDECIDED (PENDING_AI, retried each pass) — the AI layer's
        # silence never kills a bet inside the window; past the window =>
        # NOT_PLACED_AI_NO_VERDICT. SWITCH/CHALLENGE/ALTERNATIVE do not
        # exist in this path (sandbox-only legacy, unwired).
        flags = papertrade_flags(args)
        if flags["ai_authority_active"] and dec.get("status") == "BET_PAPER":
            outcome = apply_ai_gate_v2(args, led, f, dec, fc_row,
                                       qt.get(f.match_id), now)
            if outcome == "PENDING":
                journaled.append({"match_id": f.match_id,
                                  "status": "PENDING_AI",
                                  "reason": "no valid hash-locked opinion "
                                            "yet; review window open (W4.4)"})
                continue
            if outcome is not None:            # terminal VETO / NO_VERDICT
                led.append_decision(
                    outcome, recheck=risk.in_lock_recheck(
                        led, now, go_ok, capital_law=capital_law),
                    capital_law=capital_law)
                journaled.append({"match_id": f.match_id,
                                  "status": outcome["status"],
                                  "reason": outcome["reason"][:120]})
                continue
        led.append_decision(
            dec, recheck=risk.in_lock_recheck(led, now, go_ok,
                                              capital_law=capital_law),
            capital_law=capital_law)
        journaled.append({"match_id": f.match_id, "status": dec["status"],
                          "reason": dec.get("reason", "")[:120]})
    return {"league": league, "date": args.date, "now_utc": now,
            "journaled": journaled, "skipped": skipped}


# ------------------------------------------------------------------ run-day --

def cmd_run_day(args) -> dict:
    from .wsl_lane import LaneBlock as _LaneBlock
    report = {"date": args.date, "leagues": {}}
    hard = None
    # CAPITAL-V3 §4: WSL joins the run-day chain ONLY when the committed
    # config registers sport_keys.WSL (inert otherwise).
    leagues = list(LEAGUES) + (["WSL"] if wsl_configured() else [])
    for league in leagues:
        try:
            fc = run_sub(cmd_forecast, args, league)
            qt = run_sub(cmd_quote, args, league)
            dc = run_sub(cmd_decide, args, league)
            report["leagues"][league] = {"forecast": fc, "quote": qt, "decide": dc,
                                         "status": "OK"}
        except BlockError as be:
            report["leagues"][league] = {"status": be.code, "detail": be.detail}
            if be.exit_code in (EXIT_BLOCKED_NO_GO, EXIT_BLOCKED_KEY,
                                EXIT_BLOCKED_TAMPER, 7):
                hard = be
                break
        except _LaneBlock as lb:
            # WSL lane refusal (LaneBlock is not a BlockError): report
            # per-league and apply the SAME hard-break law — a lane block
            # must never crash the whole desk run, and a tamper/no-go/pin
            # refusal must never be swallowed into a green report.
            report["leagues"][league] = {"status": lb.code,
                                         "detail": lb.detail}
            if lb.exit_code in (EXIT_BLOCKED_NO_GO, EXIT_BLOCKED_KEY,
                                EXIT_BLOCKED_TAMPER, 7):
                hard = lb
                break
    write_run_report(args, report)
    if hard:
        raise hard
    return report


def run_sub(fn, args, league):
    import copy
    ns = argparse.Namespace(**vars(args))
    ns.league = league
    return fn(ns)


def write_run_report(args, report: dict) -> Path:
    root = Path(args.data_root) / ("sandbox" if getattr(args, "sandbox", False)
                                   else "runs")
    root.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    p = root / f"run_day_{args.date}_{ts}.json"
    p.write_text(json.dumps(report, indent=1, sort_keys=True))
    return p


# ------------------------------------------------------------------- settle --

def cmd_settle(args) -> dict:
    _r = maybe_wsl(args, "settle")
    if _r is not None:
        return _r
    return _cmd_settle_standard(args)


def _cmd_settle_standard(args) -> dict:
    require_gate(args)
    verify_pins(roots=_roots_from_args(args))
    core, led = open_ledger(args, create=False)
    risk = core.risk
    results = json.loads(Path(args.results).read_text())
    settled, skipped = [], []
    for r in led.rows:
        if r["type"] != "DECISION" or r["league"] != args.league or \
                r["status"] != "BET_PAPER":
            continue
        if args.date and r["kickoff_utc"][:10] != args.date:
            continue
        if r["row_sha256"] in led.settled_decision_refs():
            skipped.append({"match_id": r["match_id"], "why": "already settled"})
            continue
        res = results.get(r["match_id"])
        if res is None:
            skipped.append({"match_id": r["match_id"],
                            "why": "no result entry (outcome-masked rehearsal "
                                   "leaves bets open)"})
            continue
        result = res["result"] if isinstance(res, dict) else res
        src = (res.get("source_ref", "REHEARSAL_RESULT_FILE")
               if isinstance(res, dict) else "REHEARSAL_RESULT_FILE")
        row = risk.settle(led, decision_row=r, result=result,
                          settled_at_utc=now_of(args), source_ref=src)
        settled.append({"match_id": r["match_id"], "result": result,
                        "pnl_cents": row["pnl_cents"],
                        "outcome_for_leg": row["outcome_for_leg"]})
    return {"league": args.league, "date": args.date, "settled": settled,
            "skipped": skipped}


# ---------------------------------------------------------------- dashboard --

def cmd_dashboard(args) -> dict:
    core = load_pinned_core(roots=_roots_from_args(args))
    path = ledger_path_for(args)
    if not Path(path).exists():
        raise BlockError("BLOCKED_NO_LEDGER", f"no ledger at {path}")
    out_dir = Path(args.out) if args.out else \
        (Path(args.data_root) / ("sandbox/dashboard" if args.sandbox else "dashboard"))
    summary = core.dashboard.build(path, out_dir)
    if not summary["chain_ok"]:
        raise BlockError("BLOCKED_TAMPER", "chain verify failed at dashboard build",
                         EXIT_BLOCKED_TAMPER)
    # Exec-owned per-competition supplement (expansion law: BET/NO_BET/
    # NOT_RUN visible per soccer competition; the pinned dashboard stops at
    # the league level). Reads the same chain-verified ledger.
    led = core.ledger.PaperLedger(path).load()
    by_comp = write_soccer_competition_report(led, out_dir)
    return {"ledger": str(path), "out": str(out_dir), "sandbox": summary["sandbox"],
            "matches": len(summary["matches"]),
            "equity_cents": summary["equity_cents"],
            "open_exposure_cents": summary["open_exposure_cents"],
            "status_counts": summary["status_counts"],
            "soccer_by_competition": by_comp["competitions"]}


# --------------------------------------------------------------- plan / pins --

def cmd_plan(args) -> dict:
    report = {"date": args.date, "generated_at_utc": now_utc_real(),
              "leagues": {}}
    leagues = [args.league] if args.league else \
        list(LEAGUES) + (["WSL"] if wsl_configured() else []) \
        + ncaa_leagues_configured()
    for league in leagues:
        entry = {"fixtures": []}
        try:
            if league == "WSL":
                from research.papertrade_exec import wsl_lane
                report["leagues"][league] = wsl_lane.plan_entry(args, args.date)
                continue
            fixtures = fixtures_for(args, league, args.date)
            _, per_anchor = batch_anchor(fixtures, league) if fixtures else ({}, {})
            led = None
            lp = ledger_path_for(args)
            if Path(lp).exists():
                core = load_pinned_core(roots=_roots_from_args(args))
                led = core.ledger.PaperLedger(lp).load()
                if not led.verify_chain()[0]:
                    raise BlockError("BLOCKED_TAMPER", "chain verify failed",
                                     EXIT_BLOCKED_TAMPER)
                fc, qt = forecast_index(led), quote_index(led)
                decided = led.decided_match_ids()
            else:
                fc, qt, decided = {}, {}, set()
            now_dt = datetime.now(timezone.utc)
            for f in fixtures:
                anchor = per_anchor[f.match_id]
                if league == "SOCCER":
                    stage = soccer_stage_law(f.competition, f.kickoff_utc[:10])
                    stage_eligible = bool(stage["bet_eligible"])
                    try:
                        b1r_valid = led is not None and \
                            soccer_b1r_forecast(led, f, now_utc_real())[0] \
                            is not None
                    except BlockError:
                        b1r_valid = False      # map/registry drift: report,
                        # never crash the read-only plan; decide still blocks
                else:
                    stage_eligible = True      # no stage law beyond soccer
                    b1r_valid = True           # B1R law is soccer-only
                checks = {
                    "tip_utc": f.kickoff_utc,
                    "et_local_date": f.et_local_date,
                    "anchor_utc": anchor,
                    "anchor_open_now": now_dt < A.parse_tip(anchor),
                    "teams_known": "TBD" not in (f.home, f.away),
                    "stage_bet_eligible": stage_eligible,
                    "forecast_present": f.match_id in fc,
                    "b1r_decision_forecast_valid": b1r_valid,
                    "quote_present": f.match_id in qt,
                    "already_decided": f.match_id in decided,
                }
                checks["eligible_now"] = (checks["anchor_open_now"]
                                          and checks["teams_known"]
                                          and checks["stage_bet_eligible"]
                                          and not checks["already_decided"])
                entry["fixtures"].append({
                    "match_id": f.match_id, "home": f.home, "away": f.away,
                    "competition": f.competition, "source": f.source_ref,
                    **checks})
            entry["count"] = len(fixtures)
            entry["fixture_source"] = {
                "NBA": "espn_schedule_2026_27 payloads (pinned, composite 3d527b3c…)",
                "WNBA": "wnba_schedule_2026.csv (pinned 0ed97faf…)",
                "SOCCER": ("The Odds API events endpoint via core client "
                           "(live, 0-credit, quota-journaled; snapshot bytes "
                           "+ .meta persisted under <data-root>/data); "
                           "sandbox: labeled synthetic events"),
                "NCAA-M": ("ESPN college-basketball scoreboard (live, free; "
                           "sandbox: labeled synthetic fixtures)"),
                "NCAA-W": ("ESPN college-basketball scoreboard (live, free; "
                           "sandbox: labeled synthetic fixtures)"),
            }[league]
        except BlockError as be:
            entry = {"status": be.code, "detail": be.detail}
        report["leagues"][league] = entry
    return report


def now_utc_real() -> str:
    return datetime.now(timezone.utc).strftime(NOW_FMT)


def cmd_verify_pins(args) -> dict:
    roots = {k: (Path(v) if v else None)
             for k, v in vars(args).items() if k.endswith("_root")}
    report = verify_pins(roots={k: v for k, v in roots.items() if v})
    pins = load_pins()
    heads = {}
    for name, meta in pins["packages"].items():
        wt = meta.get("worktree")
        if wt and Path(wt).exists():
            try:
                measured = subprocess.run(
                    ["git", "-C", wt, "rev-parse", "HEAD"],
                    capture_output=True, text=True, timeout=20).stdout.strip()
            except Exception:
                measured = "MEASURE_FAILED"
            heads[name] = {"worktree": wt, "dispatch_head": meta.get("dispatch_head"),
                           "measured_head": measured,
                           "matches_dispatch_head": str(measured).startswith(
                               str(meta.get("dispatch_head", "^"))[:8])}
    report["heads"] = heads
    if args.expect_head:
        own = subprocess.run(["git", "-C", str(Path(__file__).resolve().parents[2]),
                              "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        if own != args.expect_head:
            raise BlockError("HEAD_DRIFT",
                             f"worktree HEAD {own} != pinned {args.expect_head}",
                             EXIT_HEAD_DRIFT)
        report["self_head"] = own
    return report


def cmd_key_check(args) -> dict:
    core = load_pinned_core(roots={})
    kp = Path(args.key_path).expanduser() if args.key_path else \
        core.odds_client.DEFAULT_KEY_PATH
    try:
        fp = core.odds_client.read_key_fingerprint(kp)
    except FileNotFoundError:
        raise BlockError("BLOCKED_KEY", f"key file missing: {kp}", EXIT_BLOCKED_KEY)
    except PermissionError as e:
        raise BlockError("BLOCKED_KEY",
                         f"key file mode law violated: {e}", EXIT_BLOCKED_KEY)
    except ValueError as e:
        raise BlockError("BLOCKED_KEY", f"key file invalid: {e}", EXIT_BLOCKED_KEY)
    return {"key_path": str(kp), "key_fingerprint": fp,
            "note": "only the 12-hex fingerprint is surfaced (key bytes law)"}


# --------------------------------------------------------------------- main --

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="python -m research.papertrade_exec.execute",
        description="SPORTS-PAPERTRADE-EXEC-V1 runner (pre-GO refusals are law)")
    ap.add_argument("--worktree", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    ap.add_argument("--ledger", default=None,
                    help="override ledger path (sandbox/test)")
    ap.add_argument("--sandbox", action="store_true",
                    help="SANDBOX ledger + SANDBOX control copies (rehearsal)")
    ap.add_argument("--sandbox-control-dir", default=None,
                    help="sandbox GO control dir (default <data-root>/sandbox/control)")
    ap.add_argument("--sandbox-registry", default=None,
                    help="sandbox registry copy for the gate (test seam)")
    ap.add_argument("--now", default=None,
                    help="rehearsal clock YYYY-MM-DDTHH:MM:SSZ (sandbox ONLY)")
    ap.add_argument("--paper_core_root", default=None)
    ap.add_argument("--wnba26_root", default=None)
    ap.add_argument("--nba_harness_root", default=None)
    ap.add_argument("--nba26_root", default=None)
    ap.add_argument("--soccer_root", default=None)
    def add_roots(sub_p):
        # accepted both before and after the subcommand (same dest)
        sub_p.add_argument("--paper_core_root", default=None)
        sub_p.add_argument("--wnba26_root", default=None)
        sub_p.add_argument("--nba_harness_root", default=None)
        sub_p.add_argument("--nba26_root", default=None)
        sub_p.add_argument("--soccer_root", default=None)

    def add_to_date(sub_p):
        # NBA multi-day batch window (fixtures whose UTC tip date lies in
        # [--date, --to-date]); default single-day (unchanged behavior).
        sub_p.add_argument("--to-date", dest="to_date", default=None)

    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan"); add_roots(p); p.add_argument("--date", required=True)
    p.add_argument("--league", choices=LEAGUE_CHOICES, default=None)
    add_to_date(p)
    p.set_defaults(fn=lambda a: _emit(cmd_plan(a)))

    p = sub.add_parser("forecast"); add_roots(p); p.add_argument("--league", choices=LEAGUE_CHOICES, required=True)
    p.add_argument("--date", required=True)
    add_to_date(p)
    p.set_defaults(fn=lambda a: _emit(cmd_forecast(a)))

    p = sub.add_parser("quote"); add_roots(p); p.add_argument("--league", choices=LEAGUE_CHOICES, required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--key-path", default=None, help="sandbox/test key path override")
    add_to_date(p)
    p.set_defaults(fn=lambda a: _emit(cmd_quote(a)))

    p = sub.add_parser("decide"); add_roots(p); p.add_argument("--league", choices=LEAGUE_CHOICES, required=True)
    p.add_argument("--date", required=True)
    add_to_date(p)
    p.set_defaults(fn=lambda a: _emit(cmd_decide(a)))

    p = sub.add_parser("run-day"); add_roots(p); p.add_argument("--date", required=True)
    p.set_defaults(fn=lambda a: _emit(cmd_run_day(a)))

    p = sub.add_parser("settle"); add_roots(p); p.add_argument("--league", choices=LEAGUE_CHOICES, required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--results", required=True, help="results JSON {match_id: {result, source_ref}}")
    p.set_defaults(fn=lambda a: _emit(cmd_settle(a)))

    p = sub.add_parser("dashboard"); add_roots(p)
    p.add_argument("--out", default=None)
    p.set_defaults(fn=lambda a: _emit(cmd_dashboard(a)))

    p = sub.add_parser("verify-pins"); add_roots(p)
    p.add_argument("--expect-head", default=None)
    p.set_defaults(fn=lambda a: _emit(cmd_verify_pins(a)))

    p = sub.add_parser("key-check")
    p.add_argument("--key-path", default=None)
    p.set_defaults(fn=lambda a: _emit(cmd_key_check(a)))

    p = sub.add_parser("ncaa-refresh-state")
    p.add_argument("--league", required=True)
    p.add_argument("--from-date", dest="from_date", required=True)
    p.add_argument("--to-date", dest="to_date", required=True)
    p.set_defaults(fn=lambda a: _emit(cmd_ncaa_refresh_state(a)))

    p = sub.add_parser("ai-evidence")
    p.add_argument("--league", required=True)
    p.add_argument("--match-id", required=True)
    p.add_argument("--home", required=True)
    p.add_argument("--away", required=True)
    # U5 wiring (optional): kickoff-date board + explicit ESPN team ids
    p.add_argument("--kickoff-utc", dest="kickoff_utc", default=None)
    p.add_argument("--team-ids", dest="team_ids", default=None,
                   help='JSON {"home": id, "away": id} (optional)')
    p.set_defaults(fn=lambda a: _emit(cmd_ai_evidence(a)))
    return ap


def _ncaa_plane_dir(args) -> Path:
    """A7-M1: the NCAA state/GBM artifacts honor the SANDBOX plane — a
    rehearsal never writes the real ncaa/ subtree (same plane law as the
    ops state)."""
    base = Path(args.data_root)
    if getattr(args, "sandbox", False):
        return base / "sandbox" / "ncaa"
    return base / "ncaa"


def cmd_ncaa_refresh_state(args) -> dict:
    """W5.3: the state-store bootstrap/refit job for one NCAA lane. Walks
    the day window [from, to] harvesting COMPLETED games through the SAME
    journaled ESPN scoreboard GETs, replays the FROZEN laws chronologically
    and saves the versioned store (state_sha256). The GBM refit for the
    eval season runs separately over the same harvested rows (artifact
    sha-pinned). Sandbox/test may inject the transport via the seam attr
    `ncaa_scoreboard` (refused in real mode)."""
    from research.papertrade_exec import adapters_ncaa as AN
    from research.papertrade_exec import ncaa_state_store as NSS
    from research.papertrade_exec import ncaa_model as NM
    league = args.league
    if league not in AN.ESPN_LEAGUE_PATH:
        raise BlockError("BLOCKED_LEAGUE", f"unknown NCAA lane {league}",
                         EXIT_BLOCKED_OTHER)
    seam = getattr(args, "ncaa_scoreboard", None)
    if seam is not None and not getattr(args, "sandbox", False):
        raise BlockError("BLOCKED_TEST_HOOK_IN_REAL_MODE",
                         "ncaa_scoreboard rehearsal hook refused in real "
                         "mode", EXIT_BLOCKED_OTHER)

    def fetch(day):
        if seam is not None:
            return seam(league, day)
        return AN.fetch_scoreboard(league, day)

    d0 = datetime.strptime(args.from_date, "%Y-%m-%d").date()
    d1 = datetime.strptime(args.to_date, "%Y-%m-%d").date()
    games = []
    d = d0
    while d <= d1:
        payload, body = fetch(d.isoformat())
        games.extend(AN.completed_games(AN.games_from_payload(
            league, payload, body)))
        d += timedelta(days=1)
    st = NSS.replay(games)
    store_path = _ncaa_plane_dir(args) / league / "state.json"
    rec = st.save(store_path, league=league)
    # GBM refit (regular-season rows only, seasons < eval season)
    refit_note = "sklearn absent — lane stays on the frozen Elo layer"
    try:
        season = datetime.now(timezone.utc).year
        train_rows = [{"features": NSS.pregame_features(st, g), "y": 1}
                      for g in []]  # placeholder; real rows built below
        train_rows = []
        st2 = NSS.NcaaState()
        for g in sorted(games, key=lambda g: (g["date"], g["home_id"],
                                              g["away_id"])):
            if str(g.get("season_type")) == "2" and \
                    int(g.get("season") or 0) < season:
                feat = NSS.pregame_features(st2, g)
                y = 1 if g["home_score"] > g["away_score"] else 0
                train_rows.append({"features": feat, "y": y})
            NSS.apply_result(st2, g)
        if train_rows:
            manifest = NM.refit(_ncaa_plane_dir(args) / league /
                                "artifacts", league, season, train_rows)
            refit_note = f"refit ok n={manifest['n_train']} " \
                         f"sha={manifest['sha256'][:12]}"
    except RuntimeError as e:
        refit_note = str(e)
    return {"league": league, "games_harvested": len(games),
            "state_sha256": rec["state_sha256"],
            "store": str(store_path), "refit": refit_note}


def cmd_ai_evidence(args) -> dict:
    """W4.3: the ONE research collector (read-only public GETs, allow-
    listed) — the JS producer shells out to THIS so both sides share one
    evidence implementation. Citations (url + fetched_at + excerpt) are
    journaled under <data-root>/ai_review/evidence/ and returned.
    U5 wiring (optional): --kickoff-utc fetches the MATCH-date board;
    --team-ids ('{"home": id, "away": id}' JSON) enables the roster-name
    news filter + per-team injuries source; ids absent from the CLI are
    looked up on the kickoff board by the collector itself."""
    from research.papertrade_exec import ai_research
    journal = Path(args.data_root) / "ai_review" / "evidence"
    team_ids = getattr(args, "team_ids", None)
    if isinstance(team_ids, str) and team_ids.strip():
        try:
            team_ids = json.loads(team_ids)
        except json.JSONDecodeError:
            team_ids = None                       # malformed: dormant, not guessed
    elif not isinstance(team_ids, dict):
        team_ids = None
    return ai_research.collect_evidence(
        league=args.league, match_id=args.match_id, home=args.home,
        away=args.away, journal_dir=journal,
        kickoff_utc=getattr(args, "kickoff_utc", None) or None,
        team_ids=team_ids)


def _emit(obj: dict) -> int:
    print(json.dumps(obj, indent=1, sort_keys=True, default=str))
    return EXIT_OK


def main(argv=None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if getattr(args, "sandbox", False):
        if not args.sandbox_control_dir:
            args.sandbox_control_dir = str(
                Path(args.data_root) / "sandbox" / "control")
        if not args.sandbox_registry:
            args.sandbox_registry = str(
                Path(args.data_root) / "sandbox" / "control" / "CYCLE_REGISTRY.json")
    try:
        # U4-L2 plane hygiene: the sandbox control/registry hooks are
        # REHEARSAL plumbing. Explicitly provided on the REAL plane
        # (compare against the None default) they are refused — a test
        # hook must never redirect the real gate/control plane.
        if not getattr(args, "sandbox", False) and (
                getattr(args, "sandbox_control_dir", None) is not None or
                getattr(args, "sandbox_registry", None) is not None):
            raise BlockError(
                "BLOCKED_TEST_HOOK_IN_REAL_MODE",
                "--sandbox-control-dir/--sandbox-registry are sandbox "
                "hooks and are refused in real mode (L2)",
                EXIT_BLOCKED_OTHER)
        return args.fn(args)
    except BlockError as be:
        print(json.dumps({"blocked": be.code, "detail": be.detail}, indent=1))
        return be.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
