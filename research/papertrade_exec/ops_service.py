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
                       "WSL": 48,
                       # W5.1: the NCAA lanes mirror the NBA lookahead
                       "NCAA-M": 24, "NCAA-W": 24}
SERVICE_PORT = 8791
# --- PAPERDESK-FIXALL-NCAA-V1 W1.7 ------------------------------------------
# Identical repeated failures collapse into ONE incident row + a counter +
# first/last stamps (the runtime audit found 446 identical TICK_ERROR rows =
# 12.2% of the incident file, and DASHBOARD_REBUILT at 61.4%).
COLLAPSING_KINDS = {"TICK_ERROR", "CADENCE_FORECAST_BLOCKED",
                    "CADENCE_QUOTE_BLOCKED", "CADENCE_PLAN_BLOCKED",
                    "CADENCE_DECIDE_BLOCKED", "SETTLE_FETCH_ERROR",
                    "SETTLE_BLOCKED", "SETTLE_SKIP", "RECONCILE_ERROR"}
STORM_REPORT_EVERY = 25          # re-journal the storm every N occurrences
STORM_CLOSEOUT_IDLE_S = 600      # storm quiet this long -> close-out row
# --- PAPERDESK-FIXALL-NCAA-V1 W0.2/W0.3 (owner work package 2026-10-21) -----
# W0.2 measured goal: a finished NBA/WNBA bet settles <= 3h after the match
# ends. SETTLE_GRACE_HOURS stays 3 (grace bounds premature-FINAL risk; first
# lawful attempt is kickoff+3h ~= end+0.5h, throttle 30min => worst ~1h after
# end). The due queue is REBUILT every tick — a failed attempt never removes
# a bet from the row (each attempt journaled to settle_attempts.jsonl).
# W0.3: a bet still OPEN past (estimated end + STUCK_ALARM_H) alarms high
# (SETTLE_STUCK_ALARM, re-alarmed every STUCK_REALARM_H); past
# (estimated end + DEAD_LETTER_H) it enters the dead-letter state (still
# OPEN in the ledger, labeled + aged on the dashboard; ONLY the owner can
# resolve it, via the audited `resolve-stuck` path — never a hand edit).
STUCK_ALARM_H = 6.0
DEAD_LETTER_H = 48.0
STUCK_REALARM_H = 24.0
END_ESTIMATE_H = {"NBA": 2.5, "WNBA": 2.5, "SOCCER": 2.0, "WSL": 2.0,
                  "NCAA-M": 2.5, "NCAA-W": 2.5}
# W5.5: the MANDATORY truth label (owner law — never removable; no text
# anywhere may claim NCAA has a money edge: the men's model LOST to the
# closing line in the audited money test; the women's has no price data).
NCAA_TRUTH_LABEL = ("Dự đoán — mô hình thắng bài kiểm tra dự đoán (đã "
                    "kiểm toán), CHƯA có bằng chứng thắng thị trường: "
                    "bản nam đã thua giá đóng cửa trong bài kiểm tra tiền; "
                    "bản nữ chưa kiểm tra được.")


def _cadence_leagues() -> tuple:
    """CAPITAL-V3 §4: WSL joins the cadence ONLY when the committed config
    registers sport_keys.WSL (inert otherwise — identical league set)."""
    leagues = list(LEAGUES)
    try:
        if "WSL" in (execute.load_config().get("sport_keys") or {}):
            leagues.append("WSL")
    except Exception:
        pass
    try:
        leagues.extend(execute.ncaa_leagues_configured())   # W5.1
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


class VerifiedLedgerView:
    """W2.1: the whole chain is verified ONCE at construction; afterwards a
    tick pays only for the APPENDED rows (prev-sha linkage verified against
    the trusted tail), with a sparse full re-verify (hourly) and an
    immediate full re-verify whenever the file shrinks or any incremental
    link fails (fail-closed — any inconsistency is a TAMPER, never a
    guess). Hash-chain semantics are byte-identical to the pinned
    verify_chain; the parity test proves old-path == new-path state."""

    FULL_REVERIFY_S = 3600

    def __init__(self, core, path: Path):
        self._core = core
        self.path = Path(path)
        self._sha_hex = core.ledger.sha256_hex
        self._canon = core.ledger.canonical_json
        self._led = core.ledger.PaperLedger(self.path).load()
        ok, errs = self._led.verify_chain()
        if not ok:
            raise BlockError("BLOCKED_TAMPER",
                             f"chain verify failed: {errs[:3]}",
                             execute.EXIT_BLOCKED_TAMPER)
        self._tail_sha = (self._led.rows[-1]["row_sha256"] if self._led.rows
                          else "0" * 64)
        self._verified_rows = len(self._led.rows)
        self._last_full = time.time()
        try:
            st = self.path.stat()
            self._size = st.st_size
        except OSError:
            self._size = 0

    def state(self):
        """The verified PaperLedger (incrementally refreshed)."""
        self._refresh()
        return self._led

    def _verify_new_rows(self, new_rows: list[dict]) -> tuple[bool, str]:
        prev = self._tail_sha
        for i, r in enumerate(new_rows, 1):
            if r.get("prev_row_sha256") != prev:
                return False, f"appended row {i}: prev mismatch"
            expect = self._sha_hex(self._canon(
                {k: v for k, v in r.items() if k != "row_sha256"}))
            if r.get("row_sha256") != expect:
                return False, f"appended row {i}: hash mismatch"
            prev = r.get("row_sha256", prev)
        return True, ""

    def _refresh(self) -> None:
        try:
            size = self.path.stat().st_size
        except OSError:
            size = 0
        if size < self._size or size == 0:
            self._full_reverify()          # truncation/rewrite: full path
            return
        if size == self._size:
            if time.time() - self._last_full > self.FULL_REVERIFY_S:
                self._full_reverify()
            return
        with open(self.path, "rb") as f:
            f.seek(self._size)
            raw = f.read()
        new_rows = []
        for line in raw.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                new_rows.append(json.loads(line))
            except json.JSONDecodeError:
                self._full_reverify()      # partially-written tail: full
                return
        ok, why = self._verify_new_rows(new_rows)
        if not ok:
            raise BlockError("BLOCKED_TAMPER",
                             f"incremental chain verify failed: {why}",
                             execute.EXIT_BLOCKED_TAMPER)
        self._led.rows.extend(new_rows)
        self._tail_sha = new_rows[-1]["row_sha256"] if new_rows \
            else self._tail_sha
        self._verified_rows = len(self._led.rows)
        self._size = size

    def _full_reverify(self) -> None:
        self._led = self._core.ledger.PaperLedger(self.path).load()
        ok, errs = self._led.verify_chain()
        if not ok:
            raise BlockError("BLOCKED_TAMPER",
                             f"chain verify failed: {errs[:3]}",
                             execute.EXIT_BLOCKED_TAMPER)
        self._tail_sha = (self._led.rows[-1]["row_sha256"]
                          if self._led.rows else "0" * 64)
        self._verified_rows = len(self._led.rows)
        self._last_full = time.time()
        try:
            self._size = self.path.stat().st_size
        except OSError:
            self._size = 0


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
        self._stuck_cache: list[dict] = []   # W0.3 dashboard feed
        self._upcoming_cache: list[dict] = []  # W2.4 health feed

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
        now = now_utc()
        # W1.7 storm collapse: an identical repeating failure is ONE row
        # with a counter + first/last stamps (plus a close-out when the
        # storm goes quiet) — never a per-tick flood.
        if kind in COLLAPSING_KINDS:
            key = f"{kind}:{detail[:160]}"
            st = self._load_json(self.state_dir / "incident_storms.json", {})
            e = st.get(key) or {"count": 0, "first_utc": now, "kind": kind,
                                "journaled_count": 0}
            e["count"] += 1
            e["last_utc"] = now
            e["last_detail"] = detail[:200]
            row = None
            if e["count"] == 1 or \
                    e["count"] - e["journaled_count"] >= STORM_REPORT_EVERY:
                e["journaled_count"] = e["count"]
                row = {"ts_utc": now, "kind": kind, "detail": detail,
                       "storm_count": e["count"],
                       "storm_first_utc": e["first_utc"],
                       "storm_last_utc": e["last_utc"], **extra}
            st = {k: v for k, v in st.items() if k != key}
            st[key] = e
            st = dict(sorted(st.items())[-200:])
            _atomic_write(self.state_dir / "incident_storms.json", st)
            if row is not None:
                self._incidents.append(row)
                self._incidents = self._incidents[-500:]
                with open(self.state_dir / "incidents.jsonl", "a") as f:
                    f.write(json.dumps(row, sort_keys=True, default=str)
                            + "\n")
            return
        row = {"ts_utc": now, "kind": kind, "detail": detail, **extra}
        self._incidents.append(row)
        self._incidents = self._incidents[-500:]
        with open(self.state_dir / "incidents.jsonl", "a") as f:
            f.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    def _close_storms(self) -> None:
        """Journal a close-out (count/first/last) for storms that went
        quiet — the counter becomes a complete history, not a dangling
        number."""
        p = self.state_dir / "incident_storms.json"
        st = self._load_json(p, {})
        if not st:
            return
        now = datetime.now(timezone.utc)
        changed = False
        for key, e in list(st.items()):
            if e.get("count", 0) <= e.get("journaled_count", 0):
                continue
            try:
                idle = (now - _parse_ts(e["last_utc"])).total_seconds()
            except (KeyError, ValueError):
                continue
            if idle >= STORM_CLOSEOUT_IDLE_S:
                self.incident(
                    f"{e['kind']}_STORM_CLOSED",
                    f"{e['kind']} storm closed: {e['count']} occurrences "
                    f"between {e['first_utc']} and {e['last_utc']}; last: "
                    f"{e.get('last_detail', '')[:140]}")
                e["journaled_count"] = e["count"]
                changed = True
        if changed:
            _atomic_write(p, st)

    def _metric(self, kind: str, fields: dict) -> None:
        """W1.7 metrics plane: high-frequency operational beats (dashboard
        rebuilds) are METRICS, not incidents — 61.4% of the incident file
        was DASHBOARD_REBUILT noise."""
        row = {"ts_utc": now_utc(), "kind": kind, **fields}
        with open(self.state_dir / "metrics.jsonl", "a") as f:
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
        """Journal every observed paused<->running transition (audit trail).
        W1.7: the FIRST observation after a (re)start records the state
        WITHOUT journaling a transition — the runtime audit measured 30
        RESUMED vs 4 PAUSED because every process start emitted one spurious
        RESUMED row (init None -> not-paused). Resume rows carry the last
        pause payload for attribution."""
        payload = self.pause_flag_payload()
        paused = payload is not None
        if self._last_pause_state is None:
            # W1.7: startup baseline. A service starting ALREADY paused
            # journals one informative PAUSED row; a service starting
            # unpaused journals NOTHING (the runtime audit measured 30
            # RESUMED vs 4 PAUSED — one spurious RESUMED per process
            # start).
            self._last_pause_state = paused
            if paused:
                (self.state_dir / "last_pause_payload.json").write_text(
                    json.dumps(payload or {}, sort_keys=True))
                self.incident("DECISIONS_PAUSED_BY_UI",
                              json.dumps(payload or {}, sort_keys=True))
            return
        if paused != self._last_pause_state:
            if paused:
                (self.state_dir / "last_pause_payload.json").write_text(
                    json.dumps(payload or {}, sort_keys=True))
                self.incident("DECISIONS_PAUSED_BY_UI",
                              json.dumps(payload or {}, sort_keys=True))
            else:
                last = self._load_json(
                    self.state_dir / "last_pause_payload.json", {})
                self.incident("DECISIONS_RESUMED_BY_UI",
                              "pause_decisions.flag removed; last pause "
                              f"payload: {json.dumps(last, sort_keys=True)}"
                              [:240])
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
        wise (fail-closed — settle and cadence stop for this tick).
        W2.1: the full chain verify runs ONCE per process; afterwards the
        view verifies only appended rows (hourly full re-verify; any
        inconsistency is TAMPER)."""
        ns = self._runner_args("dashboard")
        core = execute.load_pinned_core(roots={})
        if getattr(self, "_ledger_view", None) is None or \
                str(self._ledger_view.path) != str(execute.ledger_path_for(ns)):
            self._ledger_view = VerifiedLedgerView(
                core, execute.ledger_path_for(ns))
        led = self._ledger_view.state()
        return core, led, execute.ledger_path_for(ns)

    # ----------------------------------------------------------------- settle --
    def _journal_attempt(self, league: str, date: str, outcome: dict) -> None:
        """W0.2 metrics plane: EVERY settle attempt is recorded (even silent
        throttled-invisible repeats) so a bet can never fall out of the row
        without evidence. Append-only JSONL, not an incident stream."""
        rec = {"ts_utc": now_utc(), "league": league, "date": date,
               **outcome}
        with open(self.state_dir / "settle_attempts.jsonl", "a") as f:
            f.write(json.dumps(rec, sort_keys=True, default=str) + "\n")

    def _prune_settle_why(self, settled_ids: list[str]) -> None:
        """W0.3: a settled bet's keep-open reason is a GHOST — delete it the
        moment the bet settles (the runtime audit found 6/8 entries were
        ghosts of bets settled the previous day, the #1 source of wrong
        'stuck' readings). Same for the stuck/dead-letter plane."""
        ids = set(settled_ids)
        p = self.state_dir / "settle_last_why.json"
        last_why = self._load_json(p, {})
        if last_why:
            kept = {k: v for k, v in last_why.items() if k not in ids}
            if len(kept) != len(last_why):
                _atomic_write(p, kept)
        sp = self.state_dir / "stuck_state.json"
        st = self._load_json(sp, {})
        if st:
            kept = {k: v for k, v in st.items() if k not in ids}
            if len(kept) != len(st):
                _atomic_write(sp, kept)
                self._stuck_cache = [e for e in self._stuck_cache
                                     if e.get("match_id") in kept]

    def _stuck_scan(self, led, open_bets: list[dict], now_dt: datetime) -> None:
        """W0.3: stuck-alarm + dead-letter plane. A bet is STUCK when it is
        still OPEN past (estimated end + 6h) — high incident, re-alarm every
        24h — and DEAD-LETTER past (estimated end + 48h) — still OPEN in the
        ledger, but labeled + aged for the dashboard; only the owner can
        resolve it through the audited resolve-stuck path."""
        st = self._load_json(self.state_dir / "stuck_state.json", {})
        changed = False
        for r in open_bets:
            mid = r["match_id"]
            league = r["league"]
            try:
                ko = _parse_ts(r["kickoff_utc"])
            except (KeyError, ValueError):
                continue
            end_est = ko + timedelta(hours=END_ESTIMATE_H.get(league, 2.5))
            age_h = (now_dt - end_est).total_seconds() / 3600.0
            entry = st.get(mid) or {}
            if age_h < STUCK_ALARM_H:
                continue
            if not entry:
                entry = {"league": league,
                         "home": r.get("home"), "away": r.get("away"),
                         "kickoff_utc": r["kickoff_utc"],
                         "first_stuck_utc": now_utc(),
                         "stuck_age_h_at_first": round(age_h, 2),
                         "last_alarm_utc": now_utc(),
                         "dead_letter": False}
                st[mid] = entry
                changed = True
                self.incident("SETTLE_STUCK_ALARM",
                              f"{mid} ({league} {r.get('home')} v "
                              f"{r.get('away')}) OPEN {age_h:.1f}h past "
                              "estimated end — high alarm (W0.3)",
                              match_id=mid, league=league)
            else:
                last = entry.get("last_alarm_utc")
                due_realarm = True
                if last:
                    try:
                        due_realarm = (now_dt - _parse_ts(last)).total_seconds() \
                            >= STUCK_REALARM_H * 3600
                    except ValueError:
                        due_realarm = True
                if due_realarm:
                    entry["last_alarm_utc"] = now_utc()
                    entry["stuck_age_h_latest"] = round(age_h, 2)
                    changed = True
                    self.incident("SETTLE_STUCK_ALARM",
                                  f"{mid} still OPEN {age_h:.1f}h past "
                                  "estimated end (re-alarm)",
                                  match_id=mid, league=league)
            if age_h >= DEAD_LETTER_H and not entry.get("dead_letter"):
                entry["dead_letter"] = True
                entry["dead_letter_utc"] = now_utc()
                entry["dead_letter_age_h"] = round(age_h, 2)
                changed = True
                self.incident("SETTLE_DEAD_LETTER",
                              f"{mid} OPEN {age_h:.1f}h past estimated end — "
                              "dead-letter (owner resolution only, audited "
                              "resolve-stuck path)",
                              match_id=mid, league=league)
        # drop entries for bets that settled
        settled_refs = led.settled_decision_refs()
        live_ids = {r["match_id"] for r in open_bets}
        for mid in [k for k in st if k not in live_ids]:
            st.pop(mid)
            changed = True
        if changed or not st:
            _atomic_write(self.state_dir / "stuck_state.json", st)
        self._stuck_cache = sorted(
            ({"match_id": k, **v,
              "why": (self._load_json(self.state_dir /
                                      "settle_last_why.json", {})
                      .get(k, ""))}
             for k, v in st.items()),
            key=lambda e: (not e.get("dead_letter"),
                           -(e.get("stuck_age_h_latest")
                             or e.get("stuck_age_h_at_first") or 0)))

    def resolve_stuck(self, match_id: str, results_path: str,
                      token: dict) -> dict:
        """W0.3 owner-only audited resolution for a dead-lettered bet: the
        owner places ops/control/owner_resolution_token.json ({by, at_utc,
        note}) and supplies a results FILE; the settlement itself runs the
        NORMAL pinned cmd_settle path (append-only, chain-verified) — this
        method NEVER writes the ledger directly."""
        resolved = []
        for (league, date), rows in self._open_by_group().items():
            if not any(r["match_id"] == match_id for r in rows):
                continue
            self.incident("RESOLUTION_OWNER",
                          f"{match_id} owner resolution via resolve-stuck "
                          f"(token by={token.get('by')} "
                          f"at={token.get('at_utc')} "
                          f"note={str(token.get('note', ''))[:120]})",
                          match_id=match_id, league=league)
            ns = self._runner_args("settle", league=league, date=date,
                                   results=results_path)
            report = execute.cmd_settle(ns)
            resolved.append(report)
            self._prune_settle_why([s["match_id"] for s in
                                    report.get("settled", [])])
            for s in report.get("settled", []):
                self.incident("SETTLE_DONE",
                              f"{s['match_id']} result={s['result']} "
                              f"pnl_cents={s['pnl_cents']} "
                              f"outcome={s['outcome_for_leg']}",
                              match_id=s["match_id"], league=league)
            return {"league": league, "report": report}
        raise SystemExit(f"no open bet {match_id} in the due groups")

    def _open_by_group(self) -> dict:
        core, led, _lpath = self._ledger_state()
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
        return due

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
        # W0.3 stuck/dead-letter plane runs EVERY tick on the full open row
        # (independent of any throttle).
        self._stuck_scan(led, open_bets, now)
        # W0.2: the due queue is REBUILT from the ledger every tick — every
        # OPEN bet past kickoff+grace is considered again each pass; a failed
        # attempt never removes a bet from the row (only the per-source
        # throttle paces the network calls).
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
                self._journal_attempt(league, date,
                                      {"outcome": "BLOCKED",
                                       "code": be.code, "detail": be.detail[:200]})
                self.incident("SETTLE_BLOCKED", f"{league} {date}: "
                              f"{be.code}: {be.detail}", league=league)
                continue
            except Exception as e:              # network etc — keep OPEN
                self._journal_attempt(league, date,
                                      {"outcome": "FETCH_ERROR",
                                       "error": f"{type(e).__name__}: {e}"[:200]})
                self.incident("SETTLE_FETCH_ERROR", f"{league} {date}: "
                              f"{type(e).__name__}: {e}", league=league)
                continue
            self._journal_attempt(league, date,
                                  {"outcome": "FETCHED",
                                   "settleable": sorted(settleable),
                                   "inconclusive": [i["match_id"] for i in
                                                    inconclusive]})
            out["kept_open"] += len(inconclusive)
            last_why = self._load_json(
                self.state_dir / "settle_last_why.json", {})
            for inc in inconclusive:
                if last_why.get(inc["match_id"]) != inc["why"]:
                    kind = "STALE_CORPUS" if league == "WSL" \
                        else "SETTLE_KEEP_OPEN"
                    # WSL health law (owner DoD 2026-10-21): a past-kickoff
                    # bet with no clean UMA resolution is surfaced as
                    # STALE_CORPUS — the final score is unavailable and is
                    # NEVER inferred from UMA W/D/L partials.
                    self.incident(kind,
                                  f"{inc['match_id']}: {inc['why']}",
                                  match_id=inc["match_id"], league=league)
                    last_why[inc["match_id"]] = inc["why"]
            _atomic_write(self.state_dir / "settle_last_why.json", last_why)
            if league == "WSL":
                from research.papertrade_exec import wsl_results
                wsl_open = [r for r in open_bets if r["league"] == "WSL"]
                health = wsl_results.classify_open_bets(
                    rows=wsl_open, ledger_rows=led.rows)
                _atomic_write(self.state_dir / "wsl_settle_health.json",
                              {"generated_at_utc": now_utc(),
                               "bets": health})
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
            settled_ids = [s["match_id"] for s in report.get("settled", [])]
            if settled_ids:
                # W0.3: the settled bets' ghost keep-open reasons are gone
                # the moment the settle lands.
                self._prune_settle_why(settled_ids)
                # W2.4 block 2: CLV capture at settle time.
                self._record_clv(led, settled_ids)
                # W5.5: refresh the NCAA prediction-quality metrics.
                self._refresh_ncaa_metrics(led)
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
        if league in ("NBA", "WNBA") or league.startswith("NCAA-"):
            # W5.2: the NCAA lanes settle through the SAME scoreboard
            # source + team-name normalization law (norm equality on the
            # full display names — the W0.1 lesson, applied from day one).
            return RF.fetch_espn_results(
                league=league, date=date, match_ids=mids,
                ledger_rows=all_rows, data_root=self.data_root,
                sandbox=self.sandbox)
        # SOCCER: stage law FIRST (fail-closed for knockout/unknown), then the
        # 1-credit quota-guarded /scores capture.
        # W0.5 (PAPERDESK-FIXALL-NCAA-V1): a match that KICKED OFF and aged
        # past the settle grace while standing OUTSIDE the stage law can
        # never produce a lawful bet result — but an open bet on it must not
        # stay open forever either. Past kickoff+grace such a match settles
        # VOID (refund per config settlement_refund_results) with the stage
        # refusal as the source_ref — the normal pinned settle path records
        # it; never a hand edit. Matches not yet past grace stay plain
        # inconclusive (their window may still resolve).
        now_dt = datetime.now(timezone.utc)
        ineligible = []
        void_settleable: dict = {}
        eligible_rows = []
        for r in rows:
            stage = execute.soccer_stage_law(r["competition"],
                                             r["kickoff_utc"][:10])
            if stage.get("bet_eligible"):
                eligible_rows.append(r)
                continue
            ko = _parse_ts(r["kickoff_utc"])
            if now_dt >= ko + timedelta(hours=self.grace_hours):
                void_settleable[r["match_id"]] = {
                    "result": "VOID",
                    "source_ref": (
                        f"stage_law_ineligible_after_kickoff stage="
                        f"{stage.get('stage')} reason={stage.get('reason')}"
                        f" kickoff={r['kickoff_utc']} voided_at={now_utc()}"),
                }
            else:
                ineligible.append({"match_id": r["match_id"],
                                   "why": f"stage law fail-closed: "
                                          f"{stage}"})
        settleable: dict = {}
        inconclusive: list = []
        if eligible_rows:
            odds_mod, quota, client = execute._odds_for(
                self._runner_args("dashboard"))   # args carriers (data_root)
            scores_client = RF.make_scores_client(odds_mod, quota)
            # W1.2: credit calls obey the PROVIDER-credit meter as well.
            from research.papertrade_exec.quota_guard import (
                GuardedClient, ProviderQuotaSkip)
            scores_client = GuardedClient(
                scores_client, execute._provider_quota_guard_for(
                    self._runner_args("dashboard")))
            try:
                settleable, inconclusive = RF.fetch_soccer_scores(
                    odds_mod=odds_mod, quota=quota, client=scores_client,
                    sport_keys=execute._soccer_sport_keys(), match_ids=mids,
                    ledger_rows=all_rows, data_root=self.data_root,
                    sandbox=self.sandbox)
            except ProviderQuotaSkip as qs:    # provider-cap law, W1.2
                raise BlockError("BLOCKED_ODDS_API",
                                 f"scores refused by the provider-credit "
                                 f"guard: {qs}", execute.EXIT_BLOCKED_OTHER)
        for mid, v in void_settleable.items():
            settleable.setdefault(mid, v)
        return settleable, inconclusive + ineligible

    def _record_clv(self, led, settled_ids: list[str]) -> None:
        """W2.4 block 2 — Closing Line Value, captured as an AMENDMENT plane
        (append-only ops state; ledger rows are NEVER edited). Law: the
        closing price of a bet is its OWN league's quote row nearest the
        kickoff (the last quote at or before the tip — pre-cutover that is
        the pinned Pinnacle/PM snapshot nearest kickoff, post-cutover the PM
        book); clv_frac = bet_decimal / close_decimal - 1 (positive = the
        bet beat the close). A bet with no pre-tip quote records an honest
        NO_CLOSE_PRICE entry — never an inferred CLV."""
        rec_path = self.state_dir / "clv_records.jsonl"
        have: set = set()
        if rec_path.exists():
            for l in rec_path.read_text().splitlines():
                try:
                    have.add(json.loads(l).get("match_id"))
                except json.JSONDecodeError:
                    continue
        want = set(settled_ids) - have
        if not want:
            return
        by_mid: dict = {}
        for r in led.rows:
            if r.get("type") == "DECISION" and r.get("match_id") in want:
                by_mid[r["match_id"]] = r
        for mid in sorted(want):
            dec = by_mid.get(mid)
            if not dec:
                continue
            leg = dec.get("chosen_leg")
            bet_odds = (dec.get("odds_frozen") or {}).get(leg)
            ko = str(dec.get("kickoff_utc") or "")
            quotes = [q for q in led.rows
                      if q.get("type") == "MARKET_QUOTE"
                      and q.get("match_id") == mid
                      and str(q.get("fetch_ts_utc") or "") <= ko]
            rec = {"ts_utc": now_utc(), "match_id": mid,
                   "league": dec.get("league"), "leg": leg,
                   "bet_decimal": bet_odds}
            if not quotes or not leg or not bet_odds:
                rec.update({"status": "NO_CLOSE_PRICE",
                            "why": "no pre-tip quote row (CLV never "
                                   "inferred)"})
            else:
                close = max(quotes, key=lambda q: str(q.get("fetch_ts_utc")))
                close_odds = (close.get("odds") or {}).get(leg)
                if not close_odds:
                    rec.update({"status": "NO_CLOSE_PRICE",
                                "why": f"closing quote lacks {leg}"})
                else:
                    rec.update({
                        "status": "OK",
                        "close_decimal": close_odds,
                        "clv_frac": float(bet_odds) / float(close_odds) - 1.0,
                        "close_source": close.get("bookmaker"),
                        "close_fetch_ts_utc": close.get("fetch_ts_utc"),
                        "law": "clv = bet_decimal/close_decimal - 1 "
                               "(+ = beat the close)"})
            with open(rec_path, "a") as f:
                f.write(json.dumps(rec, sort_keys=True, default=str) + "\n")

    def _refresh_ncaa_metrics(self, led) -> None:
        """W5.5: the CORRECT measure for the NCAA prediction lanes —
        running log-loss/Brier of the lane forecast vs the actual result,
        and vs the PM-implied probability from the lane's own quote rows
        (a forecast that beats PM price is the only honest benchmark).
        Read-only math over the chain-verified rows; a state artifact."""
        import math
        from research.papertrade_exec import NCAA_LEAGUES
        rows = led.rows
        fc = {}
        qt = {}
        for r in rows:
            if r.get("type") == "FORECAST" and                     r.get("league") in NCAA_LEAGUES:
                fc.setdefault(r["match_id"], r)
            elif r.get("type") == "MARKET_QUOTE" and                     r.get("league") in NCAA_LEAGUES:
                qt.setdefault(r["match_id"], r)
        out = {}
        for mid, f in fc.items():
            stl = next((r for r in rows if r.get("type") == "SETTLEMENT"
                        and r.get("match_id") == mid), None)
            if not stl:
                continue
            p_home = float((f.get("p") or {}).get("HOME") or 0.0)
            result = stl.get("result")
            if result not in ("HOME", "AWAY"):
                continue
            y = 1.0 if result == "HOME" else 0.0
            p = min(max(p_home, 1e-6), 1 - 1e-6)
            slot = out.setdefault(f["league"], {"n": 0, "ll": 0.0,
                                                "brier": 0.0,
                                                "pm_ll": 0.0, "pm_n": 0})
            slot["n"] += 1
            slot["ll"] += -(y * math.log(p) + (1 - y) * math.log(1 - p))
            slot["brier"] += (p - y) ** 2
            q = qt.get(mid)
            if q:
                dec_home = float(((q.get("odds") or {}).get("HOME")) or 0)
                if dec_home > 1:
                    pm = min(max(1.0 / dec_home, 1e-6), 1 - 1e-6)
                    slot["pm_ll"] += -(y * math.log(pm)
                                       + (1 - y) * math.log(1 - pm))
                    slot["pm_n"] += 1
        for slot in out.values():
            n, pn = slot.pop("n"), slot.pop("pm_n")
            slot["logloss"] = slot.pop("ll") / n if n else None
            slot["brier"] = slot.pop("brier") / n if n else None
            slot["pm_logloss"] = slot.pop("pm_ll") / pn if pn else None
            slot["settled"] = n
        _atomic_write(self.state_dir / "ncaa_metrics.json",
                      {"generated_at_utc": now_utc(),
                       "truth_label": NCAA_TRUTH_LABEL,
                       "leagues": out})

    def _clv_summary(self) -> dict:
        """Per-league CLV aggregates + record tail for the dashboard."""
        p = self.state_dir / "clv_records.jsonl"
        if not p.exists():
            return {"by_league": {}, "tail": []}
        recs = []
        for l in p.read_text().splitlines():
            try:
                recs.append(json.loads(l))
            except json.JSONDecodeError:
                continue
        by_league: dict = {}
        for r in recs:
            if r.get("status") != "OK" or r.get("clv_frac") is None:
                continue
            slot = by_league.setdefault(r.get("league") or "?",
                                        {"n": 0, "clv_frac_sum": 0.0})
            slot["n"] += 1
            slot["clv_frac_sum"] += r["clv_frac"]
        for slot in by_league.values():
            slot["clv_avg_frac"] = slot["clv_frac_sum"] / slot["n"]
            del slot["clv_frac_sum"]
        return {"by_league": by_league, "tail": recs[-25:]}

    def _mark_lane_step(self, league: str, step: str, ok: bool) -> None:
        """W2.4 block 4: per-lane health state (last ok/blocked per step)."""
        p = self.state_dir / "league_health_state.json"
        st = self._load_json(p, {})
        slot = st.setdefault(league, {})
        slot[f"last_{step}_{'ok' if ok else 'blocked'}_utc"] = now_utc()
        _atomic_write(p, st)

    def _league_health(self) -> dict:
        health = self._load_json(
            self.state_dir / "league_health_state.json", {})
        wsl = self._load_json(
            self.state_dir / "wsl_settle_health.json", {})
        prov = self._load_json(
            self.data_root / "data" / "provider_quota_state.json", {})
        internal = self._load_json(
            self.data_root / "data" / "quota_state.json", {})
        for league, slot in health.items():
            slot["upcoming_in_window"] = sum(
                1 for u in (self._upcoming_cache or [])
                if u.get("league") == league)
            slot["open_lane_flags"] = {
                "wsl_settle_health": (wsl.get("bets") or [])
                if league == "WSL" else None,
                "stuck": [s for s in (self._stuck_cache or [])
                          if s.get("league") == league] or None,
            }
        return {"leagues": health,
                "quota_internal": {k: internal.get(k) for k in
                                   ("used_today", "used_month", "halted",
                                    "halt_reason") if k in internal},
                "quota_provider": prov}

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
        # W2.2: the THROTTLE and plan-cache decisions stay single-threaded
        # here; only the network-heavy _run_chain runs concurrently per
        # league so one slow source cannot stall the other leagues (the
        # settle pass always ran first in the same tick — priority kept).
        due_tasks: list[tuple[str, str, list]] = []
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
                due_tasks.append((league, d, eligible))
            summary[league] = league_notes
        if due_tasks:
            from concurrent.futures import ThreadPoolExecutor
            max_workers = min(len(due_tasks), 4)
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {
                    ex.submit(self._run_chain, league, d, eligible):
                        (league, d)
                    for league, d, eligible in due_tasks}
                for fut, (league, d) in futures.items():
                    try:
                        actions = fut.result()
                    except Exception as e:        # never kill the tick
                        actions = {"error": f"{type(e).__name__}: {e}"[:200]}
                        self.incident("CADENCE_CHAIN_ERROR",
                                      f"{league} {d}: {actions['error']}",
                                      league=league)
                    summary.setdefault(league, []).append(
                        {"date": d, "action": actions})
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

        def _cmd_retry_tail_drift(name: str, ns):
            """W2.2: chains run concurrently per league; the pinned append
            refuses a STALE tail (append-only, never rebase). A refusal is
            retried with backoff — every cmd_* reloads the ledger fresh and
            the forecast/quote/decide idempotency laws make each retry
            exact (already-written rows are skipped), so concurrent chains
            converge instead of corrupting."""
            delays = (0.05, 0.1, 0.2, 0.4)
            for attempt, delay in enumerate((0.0,) + delays):
                if delay:
                    time.sleep(delay)
                try:
                    return getattr(execute, f"cmd_{name}")(ns)
                except Exception as e:
                    if attempt < len(delays) and "tail drift" in str(e):
                        if attempt == 0:
                            self.incident(
                                "CADENCE_TAIL_DRIFT_RETRY",
                                f"{league} {date} {name}: concurrent append "
                                f"refused a stale tail — retrying fresh "
                                f"({type(e).__name__})", league=league)
                        continue
                    raise

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
                report = _cmd_retry_tail_drift(name, ns)
                actions[name] = report
                if flag is not None:
                    flag["ok"] = True
                self._mark_lane_step(league, name, True)   # W2.4 health
                self.incident(f"CADENCE_{name.upper()}_OK",
                              f"{league} {date}: "
                              f"{json.dumps(report, default=str)[:300]}",
                              league=league)
            except BlockError as be:
                actions[name] = {"blocked": be.code, "detail": be.detail}
                self._mark_lane_step(league, name, False)  # W2.4 health
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
            # W1.7: rebuild beats are METRICS (61.4% of the old incident
            # file was this row), not incidents.
            self._metric("DASHBOARD_REBUILT",
                         {"matches": report.get("matches"),
                          "equity_cents": report.get("equity_cents")})
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

    def _ai_pending_watch(self) -> None:
        """W4.4: the whole AI layer being down/silent is an OWNER ALARM,
        never a silent bet-killer. PENDING_AI entries older than 30 minutes
        raise AI_PROVIDER_DOWN (once per entry per day; the pending queue
        itself stays on the dashboard)."""
        from research.papertrade_exec import ai_gate_v2 as G
        for e in G.pending_alarm_owners(self.data_root):
            st = self._load_json(self.state_dir / "ai_alarms.json", {})
            key = e["match_id"]
            last = st.get(key)
            today = now_utc()[:10]
            if last == today:
                continue
            st[key] = today
            _atomic_write(self.state_dir / "ai_alarms.json", st)
            self.incident("AI_PROVIDER_DOWN",
                          f"{key} PENDING_AI for {e.get('age_min')}min "
                          f"(>30min) with no valid hash-locked verdict — "
                          "owner alarm (bets wait, none killed)",
                          match_id=key)

    def _maybe_weekly_scorecard(self) -> None:
        """A7-M3 (W4.5): the AI scorecard computes WEEKLY (or on first
        boot) — ALLOW realized vs VETO hypothetical, net value, and the
        suggest-only downgrade proposal; surfaced on the dashboard via the
        desk payload. Read-only over the verified ledger + opinions."""
        import time as _t
        from research.papertrade_exec import ai_scorecard
        p = self.state_dir / "ai_scorecard.json"
        last = self._load_json(p, {}).get("computed_at_epoch", 0)
        if _t.time() - last < 7 * 86400:
            return
        try:
            core, led, _lp = self._ledger_state()
            sc = ai_scorecard.compute_scorecard(
                ledger_rows=led.rows,
                opinions_dir=self.data_root / "ai_review" / "opinions_v2")
            sc["computed_at_epoch"] = _t.time()
            sc["computed_at_utc"] = now_utc()
            _atomic_write(p, sc)
            self.incident("AI_SCORECARD_COMPUTED",
                          f"scored={sc.get('reviews_scored')} "
                          f"net_value_cents="
                          f"{sc.get('net_value_of_ai_layer_cents')}")
        except Exception as e:            # never block the tick
            self.incident("AI_SCORECARD_ERROR",
                          f"{type(e).__name__}: {e}")

    def _ai_pending_view(self) -> list[dict]:
        from research.papertrade_exec import ai_gate_v2 as G
        try:
            pending = G._load_pending(self.data_root)
        except Exception:
            pending = {}
        return [{"match_id": k, **v} for k, v in sorted(pending.items())]

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
        self._close_storms()
        self._ai_pending_watch()
        self._maybe_weekly_scorecard()
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
        # W1.7 fail-fast law: the 2026-10-09 storm (446 identical
        # TICK_ERROR FileNotFoundError on pins.json across 9.2 h) happened
        # because the service kept ticking with a missing pinned file.
        # Startup now verifies the required pin PATHS exist; a missing one
        # is ONE loud incident + a slow-restart exit (never a per-tick
        # storm).
        missing = []
        try:
            pins = execute.load_pins()
            for name, meta in (pins.get("data") or {}).items():
                p = meta.get("path")
                if meta.get("required") and p and \
                        not Path(p).expanduser().exists():
                    missing.append(f"{name}: {p}")
        except Exception as e:
            missing.append(f"pins unreadable: {type(e).__name__}: {e}")
        if missing:
            self.incident("PIN_FILE_MISSING",
                          "required pinned source(s) absent at startup: "
                          + "; ".join(missing))
            time.sleep(300)            # slow the restart loop, stay loud
            raise SystemExit(3)
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
            # W2.2-side fix (found by the restart battery): the single-
            # instance lock is released EXPLICITLY — a GC-timed release
            # made an in-process relaunch refuse nondeterministically.
            try:
                fcntl.flock(fh, fcntl.LOCK_UN)
                fh.close()
            except OSError:
                pass

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
            desk={"stuck": self._stuck_cache,
                  "clv": self._clv_summary(),
                  "health": self._league_health(),
                  "ai_pending": self._ai_pending_view(),
                  "ncaa": {"label": NCAA_TRUTH_LABEL,
                           "metrics": self._load_json(
                               self.state_dir / "ncaa_metrics.json", {})
                           .get("leagues", {})},
                  "ai_scorecard": self._load_json(
                      self.state_dir / "ai_scorecard.json", {})},
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
    # W0.3 audited owner resolution (dead-letter plane): the owner places
    # ops/control/owner_resolution_token.json ({by, at_utc, note}) and runs
    # resolve-stuck with a results FILE — settlement goes through the NORMAL
    # pinned cmd_settle path; no direct ledger write exists anywhere.
    ap.add_argument("--resolve-stuck", dest="resolve_stuck", default=None,
                    metavar="MATCH_ID",
                    help="resolve one dead-lettered OPEN bet (owner only)")
    ap.add_argument("--resolution-results", dest="resolution_results",
                    default=None,
                    help="results JSON file for --resolve-stuck "
                         "{match_id: {result, source_ref}}")
    args = ap.parse_args(argv)
    if args.resolve_stuck:
        if not args.resolution_results:
            ap.error("--resolve-stuck requires --resolution-results FILE")
        svc = OpsService(
            data_root=Path(args.data_root), sandbox=args.sandbox,
            settle_grace_hours=args.settle_grace_hours, serve=False)
        token_path = svc.control_dir / "owner_resolution_token.json"
        if not token_path.exists():
            print(json.dumps({"blocked": "RESOLUTION_TOKEN_ABSENT",
                              "detail": f"owner must place {token_path} "
                                        "({by, at_utc, note}) first"}))
            return 4
        try:
            token = json.loads(token_path.read_text())
        except json.JSONDecodeError:
            print(json.dumps({"blocked": "RESOLUTION_TOKEN_MALFORMED"}))
            return 4
        report = svc.resolve_stuck(args.resolve_stuck,
                                   args.resolution_results, token)
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
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
