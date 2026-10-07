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
    EXIT_BLOCKED_ANCHOR, EXIT_BLOCKED_KEY, EXIT_BLOCKED_NO_GO, EXIT_BLOCKED_TAMPER,
    EXIT_HEAD_DRIFT, EXIT_OK, GO_PHRASE, LEAGUES, REGISTRY_PATH, SOCCER_LEAD_SECONDS,
    BlockError, load_pins, nba_payload_composite, sha256_file, verify_pins)
from research.papertrade_exec import adapters as A  # noqa: E402

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


def load_config() -> dict:
    p = Path(__file__).resolve().parent / "config.json"
    return json.loads(p.read_text())

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
        raise BlockError("BLOCKED_FIXTURES_SOURCE",
                         "real soccer fixtures come from The Odds API events "
                         "endpoint via the core client (post-GO, quota-guarded); "
                         "pre-GO use --sandbox rehearsal fixtures")
    raise BlockError("BLOCKED_LEAGUE", f"unknown league {league}")


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


def batch_anchor(fixtures: list, league: str) -> tuple[str, dict]:
    """Anchor deadline(s): NBA/WNBA T0-6h10m with T0 = earliest tip of the
    league's run-day batch (exclusive); SOCCER kickoff-6h strict per match."""
    if league in ("NBA", "WNBA"):
        t0 = min(f.kickoff_dt for f in fixtures)
        anchor = t0 - timedelta(seconds=BATCH_LEAD_SECONDS)
        return A.iso_z(anchor), {f.match_id: A.iso_z(anchor) for f in fixtures}
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
        res = A.soccer_engine_replay(replay_path, fixtures,
                                     PINNED_DATA["soccer_corpus"],
                                     fixtures[0].kickoff_utc[:10])
        drafts = [{"match_id": r["match_id"],
                   "p": {"HOME": float(r["p_home"]), "DRAW": float(r["p_draw"]),
                         "AWAY": float(r["p_away"])},
                   "model_version_sha": "soccer_b1_replay",
                   "source_ref": "soccer_b1_replay", "mode": "ENGINE"}
                  for r in res]
        wiring.update({"engine_mode": "ENGINE"})
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
    A.nba_incremental_refresh(
        PINNED_DATA["nba_payloads"], fixtures[0].kickoff_utc[:10],
        fixtures[-1].kickoff_utc[:10], go_ok=True)
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
    drafts, wiring = compute_forecasts(args, league, fixtures)
    _, per_anchor = batch_anchor(fixtures, league)
    written, skipped = [], []
    for f, d in zip(fixtures, drafts):
        if f.match_id in existing:
            skipped.append(f.match_id)
            continue
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
    return {"league": league, "date": args.date, "now_utc": now,
            "written": written, "skipped_existing": skipped,
            "wiring": wiring, "sandbox": bool(args.sandbox)}


def forecast_index(led) -> dict:
    idx = {}
    for r in led.rows:
        if r["type"] == "FORECAST":
            idx.setdefault(r["match_id"], r)
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

def cmd_quote(args) -> dict:
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
    if args.sandbox:
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
    # ---- real capture: core quota-guarded client, pinned sport key ---------
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
    sport_key = DEFAULT_SPORT_KEYS[league]
    try:
        body, hdrs = client.get_odds(sport_key)
    except odds_mod.QuotaSkip as qs:
        journaled = journal_quota_skip(led, fixtures, now, str(qs), existing)
        return {"league": league, "date": args.date, "quota_skip": True,
                "journaled": journaled}
    except odds_mod.KeyHalted as kh:
        raise BlockError("BLOCKED_KEY", f"HALT_KEY engaged: {kh}", EXIT_BLOCKED_KEY)
    return {"league": league, "date": args.date, "captured_bytes": len(body),
            "note": "payload mapping to MARKET_QUOTE rows is the post-GO capture "
                    "path (events->fixtures 1:1); pre-GO this branch is "
                    "unreachable because the gate refuses first"}


def journal_quota_skip(led, fixtures, now: str, why: str, existing: dict) -> list:
    """Journaled QUOTA_SKIP DECISION rows (skipped matches would silently
    vanish; the law journals them instead). No network happened (the core
    client's precheck raises before any call)."""
    journaled = []
    for f in fixtures:
        if f.match_id in existing:
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
    return " ".join(s.split()).strip().casefold()


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


def cmd_decide(args) -> dict:
    require_gate(args)
    verify_pins(roots=_roots_from_args(args))
    core, led = open_ledger(args, create=True)
    risk = core.risk
    go_ok = True   # gate passed above; evaluate_match still re-checks PIT laws
    now = now_of(args)
    league = args.league
    fixtures = fixtures_for(args, league, args.date)
    if not fixtures:
        return {"league": league, "date": args.date, "fixtures": 0}
    fc, qt = forecast_index(led), quote_index(led)
    decided = led.decided_match_ids()
    journaled, skipped = [], []
    for f in fixtures:
        if f.match_id in decided:
            skipped.append({"match_id": f.match_id, "why": "already decided"})
            continue
        ok, why = crosswalk_ok(f, fc.get(f.match_id), qt.get(f.match_id))
        dec = risk.evaluate_match(
            led, league=league, match_id=f.match_id, competition=f.competition,
            home=f.home, away=f.away, kickoff_utc=f.kickoff_utc, now_utc=now,
            forecast=fc.get(f.match_id), quote=qt.get(f.match_id),
            crosswalk_ok=ok, go_ok=go_ok)
        led.append_decision(dec, recheck=risk.in_lock_recheck(led, now, go_ok))
        journaled.append({"match_id": f.match_id, "status": dec["status"],
                          "reason": dec.get("reason", "")[:120]})
    return {"league": league, "date": args.date, "now_utc": now,
            "journaled": journaled, "skipped": skipped}


# ------------------------------------------------------------------ run-day --

def cmd_run_day(args) -> dict:
    report = {"date": args.date, "leagues": {}}
    hard = None
    for league in LEAGUES:
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
    return {"ledger": str(path), "out": str(out_dir), "sandbox": summary["sandbox"],
            "matches": len(summary["matches"]),
            "equity_cents": summary["equity_cents"],
            "open_exposure_cents": summary["open_exposure_cents"],
            "status_counts": summary["status_counts"]}


# --------------------------------------------------------------- plan / pins --

def cmd_plan(args) -> dict:
    report = {"date": args.date, "generated_at_utc": now_utc_real(),
              "leagues": {}}
    leagues = [args.league] if args.league else list(LEAGUES)
    for league in leagues:
        entry = {"fixtures": []}
        try:
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
                checks = {
                    "tip_utc": f.kickoff_utc,
                    "et_local_date": f.et_local_date,
                    "anchor_utc": anchor,
                    "anchor_open_now": now_dt < A.parse_tip(anchor),
                    "teams_known": "TBD" not in (f.home, f.away),
                    "forecast_present": f.match_id in fc,
                    "quote_present": f.match_id in qt,
                    "already_decided": f.match_id in decided,
                }
                checks["eligible_now"] = (checks["anchor_open_now"]
                                          and checks["teams_known"]
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
                           "(post-GO); sandbox: labeled synthetic events"),
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
    p.add_argument("--league", choices=LEAGUES, default=None)
    add_to_date(p)
    p.set_defaults(fn=lambda a: _emit(cmd_plan(a)))

    p = sub.add_parser("forecast"); add_roots(p); p.add_argument("--league", choices=LEAGUES, required=True)
    p.add_argument("--date", required=True)
    add_to_date(p)
    p.set_defaults(fn=lambda a: _emit(cmd_forecast(a)))

    p = sub.add_parser("quote"); add_roots(p); p.add_argument("--league", choices=LEAGUES, required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--key-path", default=None, help="sandbox/test key path override")
    add_to_date(p)
    p.set_defaults(fn=lambda a: _emit(cmd_quote(a)))

    p = sub.add_parser("decide"); add_roots(p); p.add_argument("--league", choices=LEAGUES, required=True)
    p.add_argument("--date", required=True)
    add_to_date(p)
    p.set_defaults(fn=lambda a: _emit(cmd_decide(a)))

    p = sub.add_parser("run-day"); add_roots(p); p.add_argument("--date", required=True)
    p.set_defaults(fn=lambda a: _emit(cmd_run_day(a)))

    p = sub.add_parser("settle"); add_roots(p); p.add_argument("--league", choices=LEAGUES, required=True)
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
    return ap


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
        return args.fn(args)
    except BlockError as be:
        print(json.dumps({"blocked": be.code, "detail": be.detail}, indent=1))
        return be.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
