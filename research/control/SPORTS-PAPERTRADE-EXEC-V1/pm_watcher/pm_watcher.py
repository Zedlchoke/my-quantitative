#!/usr/bin/env python3
"""PM WATCHER — read-only Polymarket market watcher for the shared paper
program (SPORTS-PAPERTRADE-EXEC-V1; owner instruction 2026-10-10 Part B).

SCOPE. Seven observation scopes: NBA, WNBA, SOCCER (the live men's UNL
lane), WSL, and the four WC/Euro PREP groups (WC_GROUP, EURO_GROUP, WCQ,
EUROQ). WATCH-ONLY: this watcher NEVER writes the paper ledger, the
dashboard, the service state, or any config; it never falls back, never
activates the Polymarket cutover, and never types a GO. Production prices
stay on The Odds API / Pinnacle until the owner consumes
`GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER` (REGISTERED_NOT_CONSUMED).

LAWS (inherited verbatim, not re-derived):
- AMENDMENT_SOURCE_SWITCH_POLYMARKET.md §1/§2 join + snapshot laws, through
  the cutover prep cycle's frozen module `polymarket_source.py` (sha-pinned
  below; 3-YES same-event proof + kickoff tolerance + verbatim 90-min rules
  for soccer/WSL; NO(Home)-is-never-AWAY; futures/props excluded; $5
  walk-the-book ASK; fee 0.05·p·(1−p)).
- Snapshots: every Gamma/CLOB GET is journaled and pinned APPEND-ONLY with
  url, retrieval UTC, bytes, sha256 by that module — PM raw snapshots keep
  living in the cutover prep data plane (the single PM snapshot home; the
  exec V10 probe precedent). Derived reports/state/alerts live in THIS
  cycle's data plane under pm_watcher/.
- Endpoints: PUBLIC Gamma + CLOB read-only GETs only. No order, wallet,
  router, or trade endpoint; no auth, no keys, no purchases. Synpath is
  never used (owner round-9: native API only).
- WC/Euro groups are PREP observation: candidates found are REPORTED for a
  live-quote A7, never intake — paper eligibility for those groups stays
  behind the WC/EURO cycle's own GO.

CADENCE. Designed for one daily fire (no collision with the existing
cadences: exec service ticks 30s locally; HCAL1 13:00Z; Q1 13:30Z; NFL
00:00 local). Silence law: when a scope's signature is unchanged and still
zero-candidate, no alert is emitted — the state file update IS the record.

Fixture sources (fresh each run, read-only):
  NBA/WNBA/SOCCER — the program's OWN refreshed snapshots (ESPN payload
  dir; wnba_schedule_2026.csv; the quota-journaled UNL events snapshot the
  service refreshes at cadence) — no duplicate provider traffic.
  WSL — the WSL cycle's fixturedownload CSV (unplayed rows).
  WC/Euro groups — fresh public ESPN scoreboard GETs for the R2 probe
  matrix (journaled + snapshotted like every call).
Model p: read-only from the REAL ledger's chain-verified FORECAST rows
(B1R for England–Croatia today); scopes without recorded forecasts report
NOT_RUN_NO_RECORDED_FORECAST for EV — honest, per the cutover taxonomy.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[4]        # .../integration
sys.path.insert(0, str(WORKTREE))

EXEC_CYCLE = "SPORTS-PAPERTRADE-EXEC-V1"
DATA_ROOT = Path(os.path.expanduser(
    "~/.my-quantitative-data/sports-papertrade-exec-v1"))
WATCHER_DIR = DATA_ROOT / "pm_watcher"
STATE_PATH = WATCHER_DIR / "state" / "watcher_state.json"
ALERTS_PATH = WATCHER_DIR / "alerts.jsonl"
REPORTS_DIR = WATCHER_DIR / "reports"

# Byte-pinned reuse of the cutover prep cycle's frozen PM module (READ-ONLY
# import; drift refuses before any network happens).
PM_SOURCE_PATH = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/"
    "sports-polymarket-cutover-prep-v1/integration/research/control/"
    "SPORTS-POLYMARKET-CUTOVER-PREP-V1/lanes/L_CUTOVER/polymarket_source.py")
KNOWN_PM_SOURCE_SHA256 = None  # set by pin_or_die() at startup

NBA_PAYLOAD_DIR = Path(os.path.expanduser(
    "~/.my-quantitative-data/nba-winprob-prospective-prep-v1/"
    "espn_schedule_2026_27"))
WNBA_SCHEDULE_CSV = Path(os.path.expanduser(
    "~/.my-quantitative-data/wnba-2026-remainder-v1/refresh_20261007/"
    "wnba_schedule_2026.csv"))
UNL_EVENTS_JSON = DATA_ROOT / "data" / "events_soccer_uefa_nations_league.json"
UNL_EVENTS_META = DATA_ROOT / "data" / "events_soccer_uefa_nations_league.meta.json"
WSL_FD_CSV = Path(os.path.expanduser(
    "~/.my-quantitative-data/wsl-winprob-paper-prep-v1/evidence/"
    "fixturedownload/wsl-2026-UTC.csv"))

# The WC/Euro R2 probe matrix (SOCCER-INTL-WC-EURO-PAPER-PREP-V1, R2
# ESPN_PROBE_R2_SUMMARY.json): group -> ESPN soccer league slugs; years
# 2027..2031 (the R2 window; a later amendment extends it).
WC_EURO_MATRIX = {
    "WC_GROUP": ["fifa.world"],
    "EURO_GROUP": ["uefa.euro"],
    "WCQ": ["fifa.worldq.uefa", "fifa.worldq.afc", "fifa.worldq.caf",
            "fifa.worldq.concacaf", "fifa.worldq.conmebol", "fifa.worldq.ofc"],
    "EUROQ": ["uefa.euroq"],
}
WC_EURO_YEARS = ["2027", "2028", "2029", "2030", "2031"]
ESPN_SCOREBOARD = ("https://site.api.espn.com/apis/site/v2/sports/soccer/"
                   "{league}/scoreboard?dates={year}")
WSL_GAMMA_TAG_ID = "105959"  # Verified on Gamma event 1167584, 2026-10-14.

NOW_FMT = "%Y-%m-%dT%H:%M:%SZ"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def now_s() -> str:
    return utcnow().strftime(NOW_FMT)


def parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(str(ts).strip().replace("Z", "+00:00"))


def pin_or_die() -> None:
    """Verify the cutover module's bytes against the watcher's own pin file
    (first run records it; later runs refuse drift)."""
    global KNOWN_PM_SOURCE_SHA256
    got = hashlib.sha256(PM_SOURCE_PATH.read_bytes()).hexdigest()
    pin_file = Path(__file__).resolve().parent / "PM_SOURCE_SHA256.txt"
    if pin_file.exists():
        want = pin_file.read_text().strip().split()[0]
        if got != want:
            raise SystemExit(json.dumps({
                "blocked": "BLOCKED_PM_SOURCE_DRIFT",
                "detail": f"cutover polymarket_source.py sha {got} != pinned "
                          f"{want}; re-pin with evidence before watching"}))
    else:
        pin_file.write_text(got + "\n")
    KNOWN_PM_SOURCE_SHA256 = got


def load_pm_module():
    pin_or_die()
    import importlib.util
    spec = importlib.util.spec_from_file_location("exec_pm_source",
                                                  PM_SOURCE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["exec_pm_source"] = mod
    spec.loader.exec_module(mod)
    return mod


# ----------------------------------------------------------------- fixtures --

def future(kickoff: str, now_dt: datetime) -> bool:
    try:
        return parse_utc(kickoff) > now_dt
    except (ValueError, TypeError):
        return False


def load_nba_fixtures(now_dt: datetime) -> list[dict]:
    out = []
    for p in sorted(NBA_PAYLOAD_DIR.glob("scoreboard_*.json")):
        try:
            payload = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        for ev in payload.get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            teams = {}
            for c in comp.get("competitors", []):
                teams[c.get("homeAway")] = (c.get("team") or {})
            home = teams.get("home", {}).get("displayName") or "TBD"
            away = teams.get("away", {}).get("displayName") or "TBD"
            tip = ev.get("date", "")
            if tip.endswith("Z") and len(tip) == 17:
                tip = tip[:-1] + ":00Z"
            if "TBD" in (home, away) or not future(tip, now_dt):
                continue
            out.append({"league": "NBA", "match_id": str(ev.get("id")),
                        "home": home, "away": away, "kickoff_utc": tip,
                        "stage": "", "source_ref": f"espn_payloads#{p.name}"})
    out.sort(key=lambda x: (x["kickoff_utc"], x["match_id"]))
    return out


def load_wnba_fixtures(now_dt: datetime) -> list[dict]:
    out = []
    with open(WNBA_SCHEDULE_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("season") != "2026" or r.get("season_type") != "3":
                continue
            if str(r.get("status_type_completed", "")).lower() == "true":
                continue
            tip = r["date"].strip()
            if tip.endswith("Z") and len(tip) == 17:
                tip = tip[:-1] + ":00Z"
            if not future(tip, now_dt):
                continue
            out.append({"league": "WNBA", "match_id": str(r["id"]),
                        "home": r.get("home_abbreviation") or "TBD",
                        "away": r.get("away_abbreviation") or "TBD",
                        "kickoff_utc": tip, "stage": "",
                        "source_ref": f"wnba_schedule_2026.csv#{r['id']}"})
    out.sort(key=lambda x: (x["kickoff_utc"], x["match_id"]))
    return out


def load_soccer_fixtures(now_dt: datetime) -> tuple[list[dict], dict]:
    """The program's own quota-journaled UNL events snapshot (freshness meta
    disclosed; the service refreshes it at cadence)."""
    meta = {}
    if UNL_EVENTS_META.exists():
        meta = json.loads(UNL_EVENTS_META.read_text())
    out = []
    if UNL_EVENTS_JSON.exists():
        for e in json.loads(UNL_EVENTS_JSON.read_bytes()):
            tip = e.get("commence_time")
            if not tip or not future(tip, now_dt):
                continue
            out.append({"league": "SOCCER", "match_id": str(e.get("id")),
                        "home": e.get("home_team"), "away": e.get("away_team"),
                        "kickoff_utc": tip, "stage": "LEAGUE_PHASE_HOME_AWAY",
                        "source_ref": "program events snapshot (UNL)"})
    out.sort(key=lambda x: (x["kickoff_utc"], x["match_id"]))
    return out, {"snapshot_sha256": meta.get("sha256"),
                 "snapshot_fetched_at_utc": meta.get("fetched_at_utc")}


def load_wsl_fixtures(now_dt: datetime) -> list[dict]:
    out = []
    if not WSL_FD_CSV.exists():
        return out
    for r in csv.DictReader(WSL_FD_CSV.read_text().splitlines()):
        result = (r.get("Result") or "").strip()
        if result:
            continue                       # played
        d, t = r["Date"].split(" ", 1)
        dd, mm, yy = d.split("/")
        hh, mi = t.split(":")[:2]
        kickoff = f"{yy}-{mm}-{dd}T{int(hh):02d}:{mi}:00Z"
        if not future(kickoff, now_dt):
            continue
        out.append({"league": "WSL", "match_id": f"FD-2026-M{r['Match Number']}",
                    "home": r["Home Team"], "away": r["Away Team"],
                    "kickoff_utc": kickoff, "stage": "",
                    "source_ref": f"wsl-2026-UTC.csv#M{r['Match Number']}"})
    out.sort(key=lambda x: (x["kickoff_utc"], x["match_id"]))
    return out


def load_wc_euro_fixtures(group: str, ps, now_dt: datetime) -> tuple[list[dict], int]:
    """Fresh public ESPN scoreboard GETs for the group's R2 matrix; every
    call journaled + append-only snapshot via the cutover module. Returns
    (future fixtures, http_failures)."""
    jr = "pm_watcher_" + now_s().replace(":", "")
    out, failures = [], 0
    for league in WC_EURO_MATRIX[group]:
        for year in WC_EURO_YEARS:
            url = ESPN_SCOREBOARD.format(league=league, year=year)
            try:
                data, _ent = ps.http_get_json(
                    url, now=now_s(), journal_run=jr,
                    snapshot_kind="espn_wc_euro",
                    snapshot_name=f"wc_euro_{league}_y{year}")
            except Exception:
                failures += 1
                continue
            for ev in (data.get("events") or []):
                comp = (ev.get("competitions") or [{}])[0]
                teams = {}
                for c in comp.get("competitors", []):
                    teams[c.get("homeAway")] = (c.get("team") or {})
                home = teams.get("home", {}).get("displayName") or "TBD"
                away = teams.get("away", {}).get("displayName") or "TBD"
                tip = ev.get("date", "")
                if tip.endswith("Z") and len(tip) == 17:
                    tip = tip[:-1] + ":00Z"
                if "TBD" in (home, away) or not future(tip, now_dt):
                    continue
                out.append({"league": "SOCCER",     # soccer join law (3-YES)
                            "watch_group": group,
                            "match_id": str(ev.get("id")),
                            "home": home, "away": away, "kickoff_utc": tip,
                            "stage": "",            # stage law = WC/EURO GO's
                            "source_ref": f"espn:{league}:{year}"})
    out.sort(key=lambda x: (x["kickoff_utc"], x["match_id"]))
    return out, failures


# ------------------------------------------------------------------ ledger p --

def load_recorded_forecasts():
    """READ-ONLY: chain-verified REAL ledger -> match_id -> the decision
    forecast p (the B1R row when present, else the first FORECAST row)."""
    sys.path.insert(0, str(WORKTREE))
    from research.papertrade_exec import execute
    core = execute.load_pinned_core(roots={})
    led = core.ledger.PaperLedger(
        DATA_ROOT / "ledger" / "paper_ledger.jsonl").load()
    ok, errs = led.verify_chain()
    if not ok:
        raise SystemExit(json.dumps({"blocked": "BLOCKED_TAMPER",
                                     "detail": str(errs[:3])}))
    idx = execute.forecast_index(led)
    return {mid: {"p": r.get("p"), "model_id": r.get("model_id")
                  or r.get("model_version_sha"),
                  "row_sha256": r.get("row_sha256")}
            for mid, r in idx.items()}


# -------------------------------------------------------------------- scan --

def scan_scope(ps, scope: str, fixtures: list[dict], events: list[dict],
               forecasts: dict, now_dt: datetime,
               scan_complete: bool = True) -> dict:
    """One scope through the cutover join law; CLOB books only for JOINED
    events. statuses: per-fixture NOT_RUN taxonomy or QUOTED."""
    results = []
    for fx in fixtures:
        rec = {"match_id": fx["match_id"],
               "fixture": f"{fx['home']} v {fx['away']}",
               "kickoff_utc": fx["kickoff_utc"], "status": None}
        joins = []
        for ev in events:
            j = ps.join_fixture_to_event(fx, ev)
            if j["status"] == "JOINED":
                joins.append(j)
        if len(joins) > 1:
            rec.update({"status": "NOT_RUN_MARKET_MISMATCH",
                        "reason": f"{len(joins)} events join; ambiguous"})
            results.append(rec)
            continue
        if not joins:
            if scan_complete:
                rec.update({"status": "NOT_RUN_NO_MARKET",
                            "reason": ps.NOT_RUN_TAXONOMY["NOT_RUN_NO_MARKET"]})
            else:
                rec.update({"status": "NOT_RUN_SOURCE_SCAN_INCOMPLETE",
                            "reason": "Gamma's broad event scan hit the offset "
                                      "limit; absence of a market cannot be "
                                      "established"})
            results.append(rec)
            continue
        join = joins[0]
        rec["event_id"] = join["event_id"]
        rec["token_ids"] = {leg: join["legs"][leg]["token_id_yes"]
                            for leg in join["legs"]}
        rec["market_ids"] = {leg: join["legs"][leg]["market_id"]
                             for leg in join["legs"]}
        rec["payout_rules"] = join["payout_rules"]
        rec["kickoff_consistency"] = join["kickoff_consistency"]
        # books (read-only, journaled, append-only snapshots)
        quotes, book_fail = {}, None
        for leg in join["legs"]:
            q = urllib.parse.urlencode(
                {"token_id": join["legs"][leg]["token_id_yes"]})
            try:
                body, _ent = ps.http_get_json(
                    f"{ps.CLOB_BOOK_URL}?{q}", now=now_s(),
                    journal_run="pm_watcher_" + now_s().replace(":", ""),
                    snapshot_kind="clob_books",
                    snapshot_name=f"watch_{join['event_id']}_{leg}")
            except Exception as e:
                book_fail = f"leg {leg}: {type(e).__name__}: {e}"
                break
            book = body if isinstance(body, dict) else {}
            walk = ps.walk_the_book(book.get("asks") or [])
            walk["book_sha256"] = hashlib.sha256(json.dumps(
                book, sort_keys=True).encode()).hexdigest()
            quotes[leg] = walk
        if book_fail:
            rec.update({"status": "NO_QUOTE", "reason": book_fail})
            results.append(rec)
            continue
        empty = sorted(l for l, w in quotes.items()
                       if w["filled_shares"] <= 0.0)
        short = {l: w["budget_short_usdc"] for l, w in quotes.items()
                 if 0.0 < w["filled_shares"] and w["budget_short_usdc"] > 1e-9}
        rec["books"] = {l: {k: w.get(k) for k in
                            ("best_ask", "vwap_ask", "filled_shares",
                             "budget_short_usdc", "fee_per_share_at_vwap",
                             "book_sha256")} for l, w in quotes.items()}
        rec["data_at_utc"] = now_s()
        if empty:
            rec.update({"status": "NO_QUOTE",
                        "reason": f"legs {empty}: empty ask side at the $5 "
                                  "walk (never priced off mid/last)"})
            results.append(rec)
            continue
        if short:
            rec.update({"status": "NO_QUOTE_DEPTH",
                        "reason": f"$5 walk cannot fill: {short}"})
            results.append(rec)
            continue
        fc = forecasts.get(fx["match_id"])
        if not fc or not fc.get("p"):
            rec.update({"status": "NOT_RUN_NO_RECORDED_FORECAST",
                        "reason": ps.NOT_RUN_TAXONOMY[
                            "NOT_RUN_NO_RECORDED_FORECAST"]})
            results.append(rec)
            continue
        try:
            ev_by_leg = {leg: ps.ev_leg(fc["p"][leg], quotes[leg]["vwap_ask"])
                         for leg in quotes}
        except (KeyError, ValueError) as e:
            rec.update({"status": "NO_QUOTE",
                        "reason": f"EV law refused a leg ({e}); fail-closed"})
            results.append(rec)
            continue
        rec["model"] = {"model_id": fc.get("model_id"),
                        "forecast_row_sha256": fc.get("row_sha256")}
        rec["ev"] = {l: {"ev_net": e["ev_net"], "gate": e["gate"]}
                     for l, e in ev_by_leg.items()}
        passing = {l: e for l, e in ev_by_leg.items()
                   if e["gate"] == "EV_GATE_PASS"}
        rec["status"] = "QUOTED_EV_COMPUTED"
        rec["best_leg"] = (max(passing, key=lambda l: passing[l]["ev_net"])
                           if passing else None)
        results.append(rec)
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    sig = hashlib.sha256(json.dumps(
        sorted((r["match_id"], r["status"], r.get("event_id") or "")
               for r in results), sort_keys=True).encode()).hexdigest()
    return {"scope": scope, "n_fixtures": len(fixtures),
            "n_candidate_events": len({r.get("event_id") for r in results
                                       if r.get("event_id")}),
            "n_joined_1to1": sum(1 for r in results if r.get("event_id")),
            "n_full_leg_quotes": sum(1 for r in results if r.get("books")),
            "status_counts": counts, "results": results, "signature": sig}


def gamma_wsl_events(ps, now: str) -> tuple[list[dict], list[dict]]:
    """Use Gamma's verified WSL tag; its broad offset cap misses live games.

    A full tagged scan is required before reporting NOT_RUN_NO_MARKET. Every
    page uses the pinned source's append-only HTTP snapshot journal.
    """
    events, metas = [], []
    for page in range(21):
        q = urllib.parse.urlencode({
            "tag_id": WSL_GAMMA_TAG_ID, "closed": "false", "limit": "100",
            "offset": str(page * 100), "end_date_min": now})
        url = f"{ps.GAMMA_EVENTS_URL}?{q}"
        body, ent = ps.http_get_json(
            url, now=now, journal_run="pm_watcher_" + now.replace(":", ""),
            snapshot_kind="gamma_events", snapshot_name=f"wsl_tag_p{page:02d}")
        page_events = body.get("events", body) if isinstance(body, dict) else body
        if not isinstance(page_events, list):
            raise ValueError("WSL Gamma tag response is not an event list")
        events.extend(page_events)
        metas.append({"page": page, "n_events": len(page_events),
                      "sha256": ent["sha256"], "url": url})
        if len(page_events) < 100:
            return events, metas
    raise RuntimeError("WSL Gamma tag scan exceeded the provider offset limit")


def gamma_events(ps, scopes: list[str]) -> tuple[list[dict], dict]:
    now = now_s()
    broad_events, broad_metas = (ps.gamma_fetch_open_events(
        now=now, journal_run="pm_watcher_" + now.replace(":", ""),
        live=True) if set(scopes) != {"WSL"} else ([], []))
    broad_complete = bool(broad_metas) and any(
        isinstance(m.get("n_events"), int) and m["n_events"] < 100
        for m in broad_metas)
    by_id = {str(e.get("id")): e for e in broad_events}
    wsl_metas = []
    if "WSL" in scopes:
        wsl_events, wsl_metas = gamma_wsl_events(ps, now)
        by_id.update({str(e.get("id")): e for e in wsl_events})
    return list(by_id.values()), {
        "gamma_pages": len(broad_metas), "n_open_events": len(by_id),
        "broad_scan_complete": broad_complete,
        "broad_scan_last_page": broad_metas[-1] if broad_metas else None,
        "wsl_tag_pages": len(wsl_metas),
        "wsl_tag_events": sum(m["n_events"] for m in wsl_metas),
        "wsl_tag_complete": bool(wsl_metas)}


# ------------------------------------------------------------------ state --

def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"schema": "pm_watcher_state@1", "scopes": {}}


def emit_alert(scope: str, kind: str, detail: dict) -> None:
    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts_utc": now_s(), "scope": scope, "kind": kind, **detail}
    with ALERTS_PATH.open("a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scopes", default=None,
                    help="comma list (default: all seven)")
    args = ap.parse_args(argv)

    ps = load_pm_module()
    WATCHER_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    now_dt = utcnow()
    all_scopes = ["NBA", "WNBA", "SOCCER", "WSL",
                  "WC_GROUP", "EURO_GROUP", "WCQ", "EUROQ"]
    scopes = [s.strip().upper() for s in args.scopes.split(",")] \
        if args.scopes else all_scopes
    unknown = [s for s in scopes if s not in all_scopes]
    if unknown:
        raise SystemExit(json.dumps({"blocked": "BLOCKED_SCOPE",
                                     "detail": f"unknown scopes {unknown}"}))

    forecasts = load_recorded_forecasts()
    events, note = gamma_events(ps, scopes)

    report = {"schema": "pm_watcher_report@1", "generated_at_utc": now_s(),
              "mode": "READ_ONLY_WATCH (no production change; cutover GO "
                      "untouched)",
              "pm_source": {"path": str(PM_SOURCE_PATH),
                            "sha256": KNOWN_PM_SOURCE_SHA256},
              "gamma": note, "scopes": {}}
    state = load_state()
    for scope in scopes:
        if scope == "NBA":
            fixtures = load_nba_fixtures(now_dt)
            meta = {}
        elif scope == "WNBA":
            fixtures = load_wnba_fixtures(now_dt)
            meta = {}
        elif scope == "SOCCER":
            fixtures, meta = load_soccer_fixtures(now_dt)
        elif scope == "WSL":
            fixtures = load_wsl_fixtures(now_dt)
            meta = {}
        elif scope in WC_EURO_MATRIX:
            fixtures, http_fail = load_wc_euro_fixtures(scope, ps, now_dt)
            meta = {"espn_http_failures": http_fail,
                    "matrix": WC_EURO_MATRIX[scope],
                    "years": WC_EURO_YEARS}
        else:
            continue
        scan_complete = (note["wsl_tag_complete"] if scope == "WSL"
                         else note["broad_scan_complete"])
        res = scan_scope(ps, scope, fixtures, events, forecasts, now_dt,
                         scan_complete=scan_complete)
        res["source_meta"] = meta
        prev = state["scopes"].get(scope, {})
        prev_sig = prev.get("signature")
        res["changed_vs_prev"] = prev_sig is not None and prev_sig != res["signature"]
        if prev_sig is None:
            res["alert"] = "BASELINE_RECORDED"
        elif res["changed_vs_prev"]:
            new_events = sorted({r.get("event_id") for r in res["results"]
                                 if r.get("event_id")} -
                                set(prev.get("joined_event_ids") or []))
            res["alert"] = "MARKET_STATE_CHANGED"
            emit_alert(scope, "MARKET_STATE_CHANGED", {
                "prev_signature": prev_sig, "signature": res["signature"],
                "new_joined_event_ids": new_events,
                "n_candidate_events": res["n_candidate_events"]})
        else:
            res["alert"] = "QUIET_UNCHANGED"
        res["joined_event_ids"] = sorted({r.get("event_id")
                                          for r in res["results"]
                                          if r.get("event_id")})
        # state keeps counts only; the REPORT keeps full per-fixture rows
        state["scopes"][scope] = {k: res[k] for k in
                                  ("signature", "joined_event_ids",
                                   "n_fixtures", "n_candidate_events",
                                   "n_joined_1to1", "n_full_leg_quotes",
                                   "status_counts")}
        state["scopes"][scope]["last_scan_utc"] = now_s()
        report["scopes"][scope] = res
    state["last_run_utc"] = now_s()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=1, sort_keys=True))
    rpath = REPORTS_DIR / f"report_{now_s().replace(':', '')}.json"
    rpath.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    summary = {s: {k: v.get(k) for k in ("n_fixtures", "n_candidate_events",
                                         "n_joined_1to1", "n_full_leg_quotes",
                                         "status_counts", "alert")}
               for s, v in report["scopes"].items()}
    print(json.dumps({"report": str(rpath), "state": str(STATE_PATH),
                      "gamma": note, "scopes": summary}, indent=1,
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
