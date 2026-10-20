"""Durable supervisor for SPORTS-PAPERTRADE-EXEC-V1 (ERRATUM_EXEC_5).

One process, one flock (`ops/service.lock` — a second instance refuses to
start, NEVER fights the ledger's own flock). Each tick, in order:

  1. SETTLE pass  — open BET_PAPER decisions with kickoff+grace passed get
     exactly one results fetch per throttle window (ESPN free; The Odds API
     /scores costs a credit and waits >= 6h between attempts); only FINAL,
     identity-matched records reach the frozen `settle` subcommand.
     Inconclusive sources journal a reason and keep the bet OPEN — no
     inference, no backfill, no settlement from non-FINAL scores.
  2. CADENCE pass — per league/date, fixtures whose anchor is still open and
     inside the policy lookahead (WNBA/NBA 24h, SOCCER 48h) run the EXISTING
     frozen runner chain forecast -> quote -> decide (every refusal law stays
     inside the runner; the supervisor only chooses WHEN). Throttled per
     (league, date); a BLOCKED_ANCHOR_PASSED is terminal for that date and is
     journaled as the NOT_RUN evidence.
  3. Dashboard rebuild (pinned static page) when the ledger changed or the
     rebuild is > 5 min old; the LIVE page is served separately by
     live_dashboard on 127.0.0.1 only.

Everything is derived from disk each tick, so a crash (or a reboot under
launchd KeepAlive) resumes without duplicate ledger rows — the ledger's own
append-only chain, settled_decision_refs and decided_match_ids are the
idempotency layer. Heartbeat, incidents and cadence/settle state live under
<data-root>/ops/ (sandbox: <data-root>/sandbox/ops/).
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from research.papertrade_exec import BlockError, LEAGUES          # noqa: E402
from research.papertrade_exec import execute                       # noqa: E402
from research.papertrade_exec import live_dashboard                # noqa: E402
from research.papertrade_exec import results_fetch as RF           # noqa: E402

TICK_SECONDS_DEFAULT = 30
CADENCE_THROTTLE_S = 900           # min spacing per (league, date) attempt
ESPN_SETTLE_THROTTLE_S = 1800      # free source; keep it polite anyway
SOCCER_SETTLE_THROTTLE_S = RF.SOCCER_RETRY_MIN_SECONDS
DASHBOARD_MAX_AGE_S = 300
DEFAULT_LOOKAHEAD_H = {"NBA": 24, "WNBA": 24, "SOCCER": 48,
                       # CAPITAL-V3 §4: WSL cadence lookahead (mirrors SOCCER)
                       "WSL": 48}
SERVICE_PORT = 8791


def _cadence_leagues() -> tuple:
    """CAPITAL-V3 §4: WSL joins the cadence ONLY when the committed config
    registers sport_keys.WSL (inert otherwise — identical league set)."""
    leagues = list(LEAGUES)
    try:
        if "WSL" in (execute.load_config().get("sport_keys") or {}):
            leagues.append("WSL")
    except Exception:
        pass
    return tuple(leagues)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)


def _atomic_write(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))
    os.replace(tmp, path)


class OpsService:
    def __init__(self, *, data_root: Path, sandbox: bool,
                 tick_seconds: int = TICK_SECONDS_DEFAULT,
                 lookahead_hours: dict | None = None,
                 settle_grace_hours: int = RF.SETTLE_GRACE_HOURS,
                 port: int = SERVICE_PORT, serve: bool = True,
                 once: bool = False):
        self.data_root = Path(data_root)
        self.sandbox = sandbox
        self.tick_seconds = tick_seconds
        self.lookahead = {**DEFAULT_LOOKAHEAD_H, **(lookahead_hours or {})}
        self.grace_hours = settle_grace_hours
        self.port = port
        self.serve_enabled = serve
        self.once = once
        self.ops = self.data_root / ("sandbox/ops" if sandbox else "ops")
        self.state_dir = self.ops / "state"
        self.results_dir = self.ops / "results"
        self.control_dir = self.ops / "control"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.control_dir.mkdir(parents=True, exist_ok=True)
        # AMENDMENT_MACOS_APP_UI_V1: the external UI controller may pause the
        # DECISION loop only (never settle, never laws) by atomically placing
        # pause_decisions.flag here; payload {by, at_utc, reason} is copied
        # into the incident journal on every observed transition.
        self._last_pause_state = None
        self._incidents: list[dict] = []
        self._stop = False
        self._srv = None
        self.tick_count = 0
        self.last_tick_ms = None
        self.last_cadence = None          # (ts, summary)
        self.last_settle = None
        self.last_rebuild = None

    # ------------------------------------------------------------- plumbing --
    def reconcile_missed_windows(self) -> int:
        """AMENDMENT_MACOS_APP_UI_V1 round-2 (owner audit P0-5): make missed
        decision windows EVIDENCED instead of silent. Scope = the cadence
        plan window only (today..+2 — identical to cadence_pass). A fixture
        whose anchor already passed without a decision gets ONE ops INCIDENT
        (`MISSED_WINDOW_ANCHOR_PASSED`), deduplicated forever by state file.
        This is the ops audit plane: NEVER a ledger row, NEVER a bet, NEVER a
        backfill — the no-backfill law is unchanged; the skip is simply
        journaled so an operator can see it."""
        seen_path = self.state_dir / "missed_windows.json"
        seen = set((self._load_json(seen_path, {}) or {}).get("matches", []))
        today = datetime.now(timezone.utc).date()
        dates = [(today + timedelta(days=i)).isoformat() for i in range(3)]
        now_dt = datetime.now(timezone.utc)
        journaled = 0
        for league in _cadence_leagues():
            for d in dates:
                ns = self._runner_args("plan", date=d, league=league)
                try:
                    report = execute.cmd_plan(ns)
                except Exception:
                    continue          # plan refuses (gate/none) — skip quietly
                entry = (report or {}).get("leagues", {}).get(league, {})
                for f in entry.get("fixtures") or []:
                    if not f.get("teams_known") or f.get("already_decided"):
                        continue
                    anchor = f.get("anchor_utc")
                    if not anchor:
                        continue
                    try:
                        anchor_dt = _parse_ts(anchor)
                    except Exception:
                        continue
                    if anchor_dt >= now_dt:
                        continue
                    key = f"{league}:{d}:{f.get('match_id')}"
                    if key in seen:
                        continue
                    self.incident(
                        "MISSED_WINDOW_ANCHOR_PASSED",
                        f"{league} {f.get('match_id')} "
                        f"{f.get('home')} v {f.get('away')} "
                        f"anchor={anchor} passed with no decision — window "
                        "skipped forever (no backfill, no row)",
                        league=league, match_id=f.get("match_id"), date=d)
                    seen.add(key)
                    journaled += 1
        _atomic_write(seen_path, {"matches": sorted(seen)[-2000:]})
        return journaled

    def _load_json(self, path: Path, default):
        if path.exists():
            try:
                return json.loads(path.read_text())
            except json.JSONDecodeError:
                return default
        return default

    def incident(self, kind: str, detail: str, **extra) -> None:
        row = {"ts_utc": now_utc(), "kind": kind, "detail": detail, **extra}
        self._incidents.append(row)
        self._incidents = self._incidents[-500:]
        with open(self.state_dir / "incidents.jsonl", "a") as f:
            f.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    # ------------------------------------------------------------ ui control --
    def pause_flag_payload(self) -> dict | None:
        """Read the pause-decisions flag; None when absent. A corrupt flag is
        read as PAUSED (payload {"corrupt": true}) — fail-closed, and settle
        keeps running regardless (the flag gates cadence only)."""
        p = self.control_dir / "pause_decisions.flag"
        if not p.exists():
            return None
        try:
            payload = json.loads(p.read_text())
            return payload if isinstance(payload, dict) else {"corrupt": True}
        except (json.JSONDecodeError, OSError):
            return {"corrupt": True}

    def decisions_paused(self) -> bool:
        return self.pause_flag_payload() is not None

    def _pause_watch(self) -> None:
        """Journal every observed paused<->running transition (audit trail)."""
        payload = self.pause_flag_payload()
        paused = payload is not None
        if paused != self._last_pause_state:
            if paused:
                self.incident("DECISIONS_PAUSED_BY_UI",
                              json.dumps(payload or {}, sort_keys=True))
            else:
                self.incident("DECISIONS_RESUMED_BY_UI",
                              "pause_decisions.flag removed")
            self._last_pause_state = paused

    def _runner_args(self, sub: str, **kw):
        """In-process runner invocation with the exact CLI law (same parser,
        same gates); --sandbox/--now only in rehearsal mode."""
        argv = ["--data-root", str(self.data_root)]
        if self.sandbox:
            argv += ["--sandbox"]
        argv += [sub]
        for k, v in kw.items():
            argv += [f"--{k}", str(v)]
        ns = execute.build_parser().parse_args(argv)
        if self.sandbox:               # main() normally sets these
            ns.sandbox_control_dir = str(
                self.data_root / "sandbox" / "control")
            ns.sandbox_registry = str(self.data_root / "sandbox" / "control" /
                                      "CYCLE_REGISTRY.json")
        return ns

    def _ledger_state(self):
        """(core, led) on a VERIFIED chain; raises BlockError TAMPER other-
        wise (fail-closed — settle and cadence stop for this tick)."""
        ns = self._runner_args("dashboard")
        core = execute.load_pinned_core(roots={})
        led = core.ledger.PaperLedger(execute.ledger_path_for(ns)).load()
        ok, errs = led.verify_chain()
        if not ok:
            raise BlockError("BLOCKED_TAMPER",
                             f"chain verify failed: {errs[:3]}",
                             execute.EXIT_BLOCKED_TAMPER)
        return core, led, execute.ledger_path_for(ns)

    # ----------------------------------------------------------------- settle --
    def settle_pass(self) -> dict:
        out = {"attempted": 0, "settled": 0, "kept_open": 0}
        try:
            core, led, _lpath = self._ledger_state()
        except BlockError as be:
            self.incident("SETTLE_SKIP", f"{be.code}: {be.detail}")
            return out
        settled_refs = led.settled_decision_refs()
        open_bets = [r for r in led.rows
                     if r.get("type") == "DECISION"
                     and r.get("status") == "BET_PAPER"
                     and r["row_sha256"] not in settled_refs]
        now = datetime.now(timezone.utc)
        due: dict[tuple[str, str], list[dict]] = {}
        for r in open_bets:
            ko = _parse_ts(r["kickoff_utc"])
            if now >= ko + timedelta(hours=self.grace_hours):
                due.setdefault((r["league"], r["kickoff_utc"][:10]),
                               []).append(r)
        for (league, date), rows in sorted(due.items()):
            if not self._throttle_ok(f"settle:{league}:{date}",
                                     ESPN_SETTLE_THROTTLE_S
                                     if league != "SOCCER" else
                                     SOCCER_SETTLE_THROTTLE_S):
                continue
            out["attempted"] += 1
            try:
                settleable, inconclusive = self._fetch_results(
                    league, date, rows, led.rows)
            except BlockError as be:            # quota/key laws propagate
                self.incident("SETTLE_BLOCKED", f"{league} {date}: "
                              f"{be.code}: {be.detail}", league=league)
                continue
            except Exception as e:              # network etc — keep OPEN
                self.incident("SETTLE_FETCH_ERROR", f"{league} {date}: "
                              f"{type(e).__name__}: {e}", league=league)
                continue
            out["kept_open"] += len(inconclusive)
            last_why = self._load_json(
                self.state_dir / "settle_last_why.json", {})
            for inc in inconclusive:
                if last_why.get(inc["match_id"]) != inc["why"]:
                    self.incident("SETTLE_KEEP_OPEN",
                                  f"{inc['match_id']}: {inc['why']}",
                                  match_id=inc["match_id"], league=league)
                    last_why[inc["match_id"]] = inc["why"]
            _atomic_write(self.state_dir / "settle_last_why.json", last_why)
            if not settleable:
                continue
            rpath = self.results_dir / f"{league.lower()}_{date}.json"
            _atomic_write(rpath, {
                m: {"result": v["result"], "source_ref": v["source_ref"]}
                for m, v in settleable.items()})
            ns = self._runner_args("settle", league=league, date=date,
                                   results=str(rpath))
            try:
                report = execute.cmd_settle(ns)
            except BlockError as be:
                self.incident("SETTLE_BLOCKED", f"{league} {date}: "
                              f"{be.code}: {be.detail}", league=league)
                continue
            for s in report.get("settled", []):
                out["settled"] += 1
                self.incident("SETTLE_DONE",
                              f"{s['match_id']} result={s['result']} "
                              f"pnl_cents={s['pnl_cents']} "
                              f"outcome={s['outcome_for_leg']}",
                              match_id=s["match_id"], league=league)
            self.last_settle = (now_utc(), report)
        return out

    def _fetch_results(self, league, date, rows, all_rows):
        mids = [r["match_id"] for r in rows]
        if league == "WSL":
            # WSL RESULTS SOURCE V1 (owner order 2026-10-20): the bet's OWN
            # tracked Polymarket 3-YES markets, resolved by UMA under the
            # pinned 90-minute rules — identity by construction. Ambiguous /
            # pending / postponed resolutions stay OPEN (never guessed).
            from research.papertrade_exec import wsl_results
            return wsl_results.fetch_wsl_settleable(
                rows=rows, ledger_rows=all_rows, data_root=self.data_root,
                sandbox=self.sandbox)
        if league in ("NBA", "WNBA"):
            return RF.fetch_espn_results(
                league=league, date=date, match_ids=mids,
                ledger_rows=all_rows, data_root=self.data_root,
                sandbox=self.sandbox)
        # SOCCER: stage law FIRST (fail-closed for knockout/unknown), then the
        # 1-credit quota-guarded /scores capture.
        ineligible = []
        eligible_rows = []
        for r in rows:
            stage = execute.soccer_stage_law(r["competition"],
                                             r["kickoff_utc"][:10])
            if stage.get("bet_eligible"):
                eligible_rows.append(r)
            else:
                ineligible.append({"match_id": r["match_id"],
                                   "why": f"stage law fail-closed: "
                                          f"{stage}"})
        if not eligible_rows:
            return {}, ineligible
        odds_mod, quota, client = execute._odds_for(
            self._runner_args("dashboard"))   # args carriers only (data_root)
        scores_client = RF.make_scores_client(odds_mod, quota)
        settleable, inconclusive = RF.fetch_soccer_scores(
            odds_mod=odds_mod, quota=quota, client=scores_client,
            sport_keys=execute._soccer_sport_keys(), match_ids=mids,
            ledger_rows=all_rows, data_root=self.data_root,
            sandbox=self.sandbox)
        return settleable, inconclusive + ineligible

    # ---------------------------------------------------------------- cadence --
    @staticmethod
    def window_eligible(f: dict, league: str, now_dt: datetime,
                        lookahead_hours: dict) -> bool:
        """POLICY layer only: the runner keeps every hard law. A match enters
        the capture window when its anchor is still open and the time to the
        anchor is within the league lookahead (limits early price lock-in
        without ever crossing the anchor)."""
        try:
            anchor = _parse_ts(f["anchor_utc"])
        except (KeyError, ValueError, TypeError):
            return False
        return bool(f.get("eligible_now")) and now_dt < anchor and \
            (anchor - now_dt) <= timedelta(hours=lookahead_hours[league])

    def cadence_pass(self) -> dict:
        summary = {}
        today = datetime.now(timezone.utc).date()
        dates = [(today + timedelta(days=i)).isoformat() for i in range(3)]
        upcoming = []
        cache_path = self.state_dir / "plan_cache.json"
        cache = self._load_json(cache_path, {})
        for league in _cadence_leagues():
            league_notes = []
            for d in dates:
                key = f"cadence:{league}:{d}"
                fresh = self._throttle_ok(key, CADENCE_THROTTLE_S)
                report = None
                if fresh:
                    ns = self._runner_args("plan", date=d, league=league)
                    try:
                        report = execute.cmd_plan(ns)
                    except BlockError as be:
                        self.incident("CADENCE_PLAN_BLOCKED",
                                      f"{league} {d}: {be.code}: {be.detail}",
                                      league=league)
                        continue
                    cache[key] = {"ts": now_utc(), "report": report}
                    _atomic_write(cache_path, {
                        k: v for k, v in cache.items()
                        if (v.get("report", {}).get("date") or d) >=
                        (today - timedelta(days=14)).isoformat()})
                else:
                    report = (cache.get(key) or {}).get("report")
                if not report:
                    continue
                entry = report["leagues"].get(league, {})
                fixtures = entry.get("fixtures") or []
                now_dt = datetime.now(timezone.utc)
                eligible = [f for f in fixtures if self.window_eligible(
                    f, league, now_dt, self.lookahead)]
                for f in fixtures:
                    if f.get("anchor_utc") and f.get("teams_known"):
                        upcoming.append({
                            "league": league, "match_id": f["match_id"],
                            "home": f["home"], "away": f["away"],
                            "anchor_utc": f["anchor_utc"],
                            "eligible_now": bool(f.get("eligible_now")),
                            "note": self._fixture_note(f)})
                if not eligible:
                    league_notes.append({"date": d, "action": "NONE",
                                         "fixtures": len(fixtures)})
                    continue
                if not fresh:
                    league_notes.append({"date": d, "action": "THROTTLED",
                                         "eligible": len(eligible)})
                    continue
                actions = self._run_chain(league, d, eligible)
                league_notes.append({"date": d, "action": actions,
                                     "eligible": len(eligible)})
            summary[league] = league_notes
        self.last_cadence = (now_utc(), summary)
        self._upcoming_cache = sorted(
            upcoming, key=lambda u: u["anchor_utc"])[:25]
        return summary

    @staticmethod
    def _fixture_note(f: dict) -> str:
        notes = []
        if not f.get("teams_known"):
            notes.append("teams TBD")
        if f.get("forecast_present"):
            notes.append("forecast present")
        if f.get("quote_present"):
            notes.append("quote present")
        if f.get("already_decided"):
            notes.append("decided")
        if not f.get("stage_bet_eligible"):
            notes.append("stage law fail-closed")
        return "; ".join(notes) or "awaiting window"

    def _run_chain(self, league: str, date: str, eligible: list) -> dict:
        actions = {}
        forecast_ran = {"ok": False}
        quote_ran = {"ok": False}

        def _needs_forecast() -> bool:
            for f in eligible:
                if not f.get("forecast_present"):
                    return True
                # B1R switch law: a SOCCER match without a VALID B1R decision
                # forecast still needs the (idempotent) emission pass; decide
                # will journal NOT_RUN_NO_B1R_FORECAST if the anchor then
                # refuses a lawful twin.
                if league == "SOCCER" and \
                        not f.get("b1r_decision_forecast_valid", True):
                    return True
            return False

        steps = (
            ("forecast", _needs_forecast, forecast_ran),
            ("quote",
             lambda: forecast_ran["ok"] or
             any(f.get("forecast_present") and not f.get("quote_present")
                 for f in eligible),
             quote_ran),
            ("decide",
             lambda: quote_ran["ok"] or
             any(f.get("forecast_present") and f.get("quote_present")
                 and not f.get("already_decided") for f in eligible),
             None))
        for name, needed, flag in steps:
            if not needed():
                actions[name] = "SKIP_NOT_NEEDED"
                continue
            try:
                ns = self._runner_args(name, league=league, date=date)
                report = getattr(execute, f"cmd_{name}")(ns)
                actions[name] = report
                if flag is not None:
                    flag["ok"] = True
                self.incident(f"CADENCE_{name.upper()}_OK",
                              f"{league} {date}: "
                              f"{json.dumps(report, default=str)[:300]}",
                              league=league)
            except BlockError as be:
                actions[name] = {"blocked": be.code, "detail": be.detail}
                self.incident(f"CADENCE_{name.upper()}_BLOCKED",
                              f"{league} {date}: {be.code}: {be.detail}",
                              league=league)
                if be.code == "BLOCKED_ANCHOR_PASSED":
                    break            # terminal for the date: NOT_RUN evidence
        return actions

    # -------------------------------------------------------------- dashboard --
    def maybe_rebuild_dashboard(self) -> None:
        ns = self._runner_args("dashboard")
        lpath = Path(execute.ledger_path_for(ns))
        marker = self.state_dir / "dashboard_marker.json"
        last = self._load_json(marker, {})
        mtime = lpath.stat().st_mtime if lpath.exists() else 0
        age_ok = (time.time() - last.get("ts", 0)) > DASHBOARD_MAX_AGE_S
        if mtime <= last.get("mtime", 0) and not age_ok:
            return
        try:
            report = execute.cmd_dashboard(ns)
            self.last_rebuild = (now_utc(), report.get("matches"))
            _atomic_write(marker, {"ts": time.time(), "mtime": mtime})
            self.incident("DASHBOARD_REBUILT",
                          f"{report.get('matches')} matches, "
                          f"equity_cents={report.get('equity_cents')}")
        except BlockError as be:
            self.incident("DASHBOARD_BLOCKED", f"{be.code}: {be.detail}")

    # ------------------------------------------------------------------ tick --
    def _throttle_ok(self, key: str, min_interval_s: int) -> bool:
        p = self.state_dir / "throttle.json"
        st = self._load_json(p, {})
        if time.time() - st.get(key, 0) < min_interval_s:
            return False
        st[key] = time.time()
        st = {k: v for k, v in st.items()
              if time.time() - v < 30 * 86400}
        _atomic_write(p, st)
        return True

    def _write_heartbeat(self, started: float, results: dict) -> None:
        hb = {
            "ts_utc": now_utc(),
            "pid": os.getpid(),
            "sandbox": self.sandbox,
            "tick_count": self.tick_count,
            "last_tick_utc": now_utc(),
            "last_tick_ms": self.last_tick_ms,
            "last_cadence_tick_utc": self.last_cadence[0]
            if self.last_cadence else None,
            "last_cadence_result": self.last_cadence[1]
            if self.last_cadence else None,
            "last_settle_tick_utc": self.last_settle[0]
            if self.last_settle else None,
            "last_settle_result": self.last_settle[1]
            if self.last_settle else None,
            "last_dashboard_rebuild_utc": self.last_rebuild[0]
            if self.last_rebuild else None,
            "decisions_paused": self.decisions_paused(),
            "tick_summary": results,
            "lookahead_hours": self.lookahead,
            "port": self.port if self.serve_enabled else None,
        }
        _atomic_write(self.state_dir / "heartbeat.json", hb)

    def tick(self) -> dict:
        t0 = time.time()
        self.tick_count += 1
        self._pause_watch()
        results = {}
        results["settle"] = self.settle_pass()
        if self.decisions_paused():
            # AMENDMENT_MACOS_APP_UI_V1: the UI paused new DECISIONS only.
            # Settlement and dashboard rebuild continue — an already-open
            # BET_PAPER row still settles from pinned sources while paused;
            # no new forecast/quote/decision attempt is made at all.
            results["cadence"] = "PAUSED_BY_UI_FLAG"
            self.last_cadence = (now_utc(), "PAUSED_BY_UI_FLAG")
        else:
            results["cadence"] = self.cadence_pass()
        self.maybe_rebuild_dashboard()
        self.last_tick_ms = int((time.time() - t0) * 1000)
        self._write_heartbeat(t0, results)
        return results

    def run_forever(self) -> None:
        lock_path = self.ops / "service.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(lock_path, "a+")
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print(json.dumps({"blocked": "SINGLE_INSTANCE",
                              "detail": "another ops supervisor holds "
                                        f"{lock_path}"}))
            raise SystemExit(3)

        def _sigterm(_sig, _frm):
            self._stop = True
        signal.signal(signal.SIGTERM, _sigterm)
        signal.signal(signal.SIGINT, _sigterm)
        # A (re)start means "re-measure now": drop only the CADENCE pacing
        # (plans are free/0-credit); SETTLE throttles survive restarts so a
        # crash loop can never accelerate the 1-credit soccer /scores spend.
        tp = self.state_dir / "throttle.json"
        st = self._load_json(tp, {})
        kept = {k: v for k, v in st.items() if not k.startswith("cadence:")}
        if len(kept) != len(st):
            _atomic_write(tp, kept)
        self.incident("SERVICE_START",
                      f"pid={os.getpid()} sandbox={self.sandbox} "
                      f"port={self.port if self.serve_enabled else '-'}")
        try:
            missed = self.reconcile_missed_windows()
            if missed:
                self.incident("MISSED_WINDOWS_RECONCILED",
                              f"journaled {missed} missed window(s)")
        except Exception as e:            # reconciliation never blocks service
            self.incident("RECONCILE_ERROR", f"{type(e).__name__}: {e}")
        if self.serve_enabled:
            self._srv = live_dashboard.serve(self.state_fn, self.port)
        try:
            while not self._stop:
                try:
                    self.tick()
                except Exception as e:            # never die on one bad tick
                    self.incident("TICK_ERROR",
                                  f"{type(e).__name__}: {e}")
                if self.once:
                    break
                for _ in range(self.tick_seconds * 10):
                    if self._stop:
                        break
                    time.sleep(0.1)
        finally:
            if self._srv:
                self._srv.shutdown()
            self.incident("SERVICE_STOP", f"pid={os.getpid()}")

    # ------------------------------------------------------------------ state --
    def state_fn(self) -> dict:
        t0 = time.time()
        core = execute.load_pinned_core(roots={})
        hb = self._load_json(self.state_dir / "heartbeat.json", None)
        inc_lines = []
        inc_path = self.state_dir / "incidents.jsonl"
        if inc_path.exists():
            inc_lines = [json.loads(l)
                         for l in inc_path.read_text().splitlines()
                         if l.strip()][-30:]
        upcoming = getattr(self, "_upcoming_cache", []) or \
            (hb or {}).get("upcoming", [])
        fp = None
        try:
            fp = core.odds_client.read_key_fingerprint()
        except Exception:
            fp = None
        capital_law = 2
        try:
            capital_law = execute.capital_law_for(
                self._runner_args("dashboard"), core)
        except Exception:
            capital_law = 2                     # fail-closed display
        return live_dashboard.build_state(
            core=core,
            ledger_path=execute.ledger_path_for(
                self._runner_args("dashboard")),
            data_root=self.data_root, sandbox=self.sandbox,
            key_fingerprint=fp, heartbeat=hb, incidents=inc_lines,
            upcoming=upcoming, capital_law=capital_law,
            serve_latency_ms=int((time.time() - t0) * 1000))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m research.papertrade_exec.ops_service",
        description="SPORTS-PAPERTRADE-EXEC-V1 durable supervisor "
                    "(ERRATUM_EXEC_5; paper only; binds 127.0.0.1)")
    ap.add_argument("--data-root", default=str(execute.DEFAULT_DATA_ROOT))
    ap.add_argument("--sandbox", action="store_true")
    ap.add_argument("--once", action="store_true",
                    help="single tick then exit (tests / manual pass)")
    ap.add_argument("--tick-seconds", type=int, default=TICK_SECONDS_DEFAULT)
    ap.add_argument("--port", type=int, default=SERVICE_PORT)
    ap.add_argument("--no-serve", action="store_true")
    ap.add_argument("--lookahead-wnba-hours", type=int, default=24)
    ap.add_argument("--lookahead-nba-hours", type=int, default=24)
    ap.add_argument("--lookahead-soccer-hours", type=int, default=48)
    ap.add_argument("--settle-grace-hours", type=int,
                    default=RF.SETTLE_GRACE_HOURS)
    args = ap.parse_args(argv)
    svc = OpsService(
        data_root=Path(args.data_root), sandbox=args.sandbox,
        tick_seconds=args.tick_seconds,
        lookahead_hours={"NBA": args.lookahead_nba_hours,
                         "WNBA": args.lookahead_wnba_hours,
                         "SOCCER": args.lookahead_soccer_hours},
        settle_grace_hours=args.settle_grace_hours,
        port=args.port, serve=not args.no_serve, once=args.once)
    svc.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
