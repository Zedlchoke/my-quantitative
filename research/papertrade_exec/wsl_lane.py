"""WSL league lane for the SHARED exec runner (CAPITAL LAW V3 plan §4;
AMENDMENT_R5_CAPITAL_V3_SHARED_BET_PAPER). NEW FILE candidate — pure addition
to research/papertrade_exec; nothing existing is edited.

Laws implemented here (fail-closed everywhere):
- ONE wallet, ONE shared ledger: WSL BET_PAPER rows are written by THIS lane
  into the SHARED ledger (sports-papertrade-exec-v1) via the pinned core.
  The WSL standalone provenance ledger (sha dd8a501f…, 3 rows) is READ-ONLY
  PROVENANCE: forecasts are cross-referenced, never imported as bets, never
  double-counted (R5-1).
- Forecast: fixtures -> FORECAST via the BYTE-PINNED frozen WSL engine
  (wsl_engine.py sha 109c3ec1…, WSL_ENGINE_REF of wsl_adapter_common),
  CROSS-CHECKED against the provenance ledger's FORECAST row for the same
  fixture; ANY p mismatch => BLOCKED_FORECAST_DISAGREEMENT (never averaged,
  never narrowed). A fixture with no provenance row refuses
  NOT_RUN_NO_PROVENANCE_FORECAST (conservative reading of §4.2: the
  cross-reference is required for every fixture).
- Quote: Polymarket ONLY — three YES binaries (Home/Draw/Away) of ONE event
  via the byte-pinned polymarket_source (sha 4b27ab17…): join law
  (NO(Home) never Away; verbatim 90-minute rules), walk_the_book at the
  ACTUAL v3 stake (budget_usdc = stake_cents/100), budget_short_usdc must be
  0 else NO_QUOTE_DEPTH (the stake is NEVER shrunk to fit depth), snapshot
  fetched STRICTLY before the anchor (kickoff − 6h; == anchor is stale).
  d_eff per leg = 1/(vwap_ask + fee_per_share(vwap_ask)) — fee
  0.05·p·(1−p) exactly once in the denominator (R5-2).
- Decide: the SHARED core's own risk.evaluate_match / in_lock_recheck with
  capital_law=3, plus the IN-LOCK WSL BET_PAPER phrase gate
  (b1r_switch_ts_verified pattern): the WSL cycle's registry row
  go_phrase_state must start with OWNER_GO_TYPED_LIVE AND the
  SPORTS-PAPERTRADE-CAPITAL-V3 row must ALSO be OWNER_GO_TYPED_LIVE
  (ordering law §7: the WSL phrase may be typed only after the capital-v3
  phrase is consumed). Missing either => BLOCKED_NO_GO in-lock.
- Precise NOT_RUN taxonomy (plan §4.4): NOT_RUN_NO_MARKET,
  NOT_RUN_MARKET_MISMATCH, NOT_RUN_RULES, NOT_RUN_SNAPSHOT_STALE,
  NO_QUOTE_DEPTH, BLOCKED_FORECAST_DISAGREEMENT, … — never a synthetic bet,
  never a narrowed condition.

PAPER ONLY: no real money, no order placement; the battery is fully
synthetic (zero network — books/fixtures are injected fixtures).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------- identity ----
CAPITAL_V3_CYCLE_ID = "SPORTS-PAPERTRADE-CAPITAL-V3"
CAPITAL_V3_GO_PHRASE = "GO SPORTS PAPERTRADE CAPITAL V3 ACTIVATE"
WSL_CYCLE_ID = "WSL-WINPROB-PROSPECTIVE-PAPER-PREP-V1"
WSL_BET_PAPER_PHRASE = "GO WSL WINPROB PROSPECTIVE PAPER V1 BET_PAPER"
LEAGUE = "WSL"
NOW_FMT = "%Y-%m-%dT%H:%M:%SZ"

# Byte-pinned frozen WSL engine (WSL_ADAPTER's WSL_ENGINE_REF; sha asserted
# before every import — drift is BLOCKED_PIN_DRIFT, fail-closed).
WSL_ENGINE_REF = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/wsl-winprob-scored-prep-v1/"
    "integration/research/control/WSL-WINPROB-SCORED-PREP-V1/lanes/L_BUILD/"
    "wsl_engine/wsl_engine.py")
WSL_ENGINE_SHA256 = ("109c3ec168809008b723ca3f8700d03927c6983cfc5d0678391f4"
                     "a201831cc66")
WSL_FREEZE_SHA256 = ("80e429c4a4872ca707814000276207acf8a8e4d5ea85408f26ec7107"
                     "4d0f9322")

# Byte-pinned Polymarket source (pure functions ONLY: join / walk / fee law;
# its own loader surfaces are NEVER invoked — they would extract dependency
# trees into the cutover-prep data plane, outside this cycle's write plane).
PM_SOURCE_REF = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/sports-polymarket-cutover-"
    "prep-v1/integration/research/control/SPORTS-POLYMARKET-CUTOVER-PREP-V1/"
    "lanes/L_CUTOVER/polymarket_source.py")
PM_SOURCE_SHA256 = ("4b27ab17b1dcc169bc15a6c1eca4d61ed67ea46e3ad05ba5ed96d3ae"
                    "8f7a270f")

# READ-ONLY provenance ledger (WSL forecast-only; NEVER written, never
# imported as bets — R5-1).
WSL_PROVENANCE_LEDGER = Path(
    "~/.my-quantitative-data/wsl-winprob-paper-prep-v1/ledger/"
    "paper_ledger.jsonl").expanduser()

# Anchor law (mirrors SOCCER_LEAD_SECONDS / polymarket ANCHOR_LAWS["WSL"]):
# kickoff − 6h STRICT per match; quotes and snapshots strictly BEFORE it.
ANCHOR_LEAD_SECONDS = 6 * 3600
KICKOFF_TOLERANCE_SECONDS = 3600

# WSL league law (verbatim from wsl_adapter_common.WSL_LEAGUE_MODEL /
# polymarket_source.WSL_LEAGUE_MODEL; registered in the core's LEAGUE_MODELS
# in-memory at decide time — the core's gate code runs byte-pinned).
WSL_LEAGUE_MODEL = {
    "model_id": "B1_ELO_DAVIDSON_WSL",
    "constants": {"K": 24.0, "nu": 0.55, "HCA": 40.0, "init": 1500.0},
    "outcomes": ["HOME", "DRAW", "AWAY"],
    "disclosure": (
        "WSL forecast arm frozen wsl_winprob_freeze@1 sha 80e429c4… "
        "(B1 Elo/Davidson K=24.0 nu=0.55 HCA=40.0, init 1500, day-batch D-1, "
        "team_id identity, awarded/anomalous excluded). Calibration/process "
        "recording only — NEVER evidence of betting edge."),
    "forecast_gate": (
        "WSL-WINPROB-PROSPECTIVE-PAPER-PREP-V1; BET_PAPER requires "
        "'GO WSL WINPROB PROSPECTIVE PAPER V1 BET_PAPER' recorded "
        "OWNER_GO_TYPED_LIVE, lawful only AFTER 'GO SPORTS PAPERTRADE "
        "CAPITAL V3 ACTIVATE' is consumed (ordering law §7)"),
}

EXIT_BLOCKED_NO_GO = 3
EXIT_PIN_DRIFT = 7
EXIT_BLOCKED_OTHER = 9


class LaneBlock(RuntimeError):
    def __init__(self, code: str, detail: str, exit_code: int = EXIT_BLOCKED_OTHER):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.exit_code = exit_code


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _import_pinned(path: Path, want_sha: str, alias: str):
    """Byte-verify then import under a private module alias (pinned-loader
    pattern; drift refuses before any import)."""
    if not path.exists():
        raise LaneBlock("BLOCKED_PIN_DRIFT", f"pinned file missing: {path}",
                        EXIT_PIN_DRIFT)
    got = sha256_file(path)
    if got != want_sha:
        raise LaneBlock("BLOCKED_PIN_DRIFT",
                        f"{path} sha {got[:12]} != pinned {want_sha[:12]}",
                        EXIT_PIN_DRIFT)
    if alias in sys.modules:
        return sys.modules[alias]
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


_ENGINE_MOD = None
_PM_MOD = None


def load_wsl_engine():
    global _ENGINE_MOD
    if _ENGINE_MOD is None:
        _ENGINE_MOD = _import_pinned(WSL_ENGINE_REF, WSL_ENGINE_SHA256,
                                     "wsl_engine_pinned_capv3")
    return _ENGINE_MOD


def load_pm_source():
    global _PM_MOD
    if _PM_MOD is None:
        _PM_MOD = _import_pinned(PM_SOURCE_REF, PM_SOURCE_SHA256,
                                 "pm_source_pinned_capv3")
    return _PM_MOD


def register_wsl_league_law(core) -> None:
    """In-memory LEAGUE_MODELS registration (adapter pattern, idempotent)."""
    existing = core.LEAGUE_MODELS.get(LEAGUE)
    if existing is not None and existing != WSL_LEAGUE_MODEL:
        raise LaneBlock("BLOCKED_LEAGUE_LAW",
                        "WSL league law conflict with an existing entry")
    core.LEAGUE_MODELS[LEAGUE] = WSL_LEAGUE_MODEL


# ------------------------------------------------------------------ time -----

def parse_utc(ts: str) -> datetime:
    return datetime.strptime(ts, NOW_FMT).replace(tzinfo=timezone.utc)


def now_of(args) -> str:
    """--now is a SANDBOX-ONLY rehearsal hook (mirror of the exec law)."""
    if getattr(args, "now", None):
        if not getattr(args, "sandbox", False):
            raise LaneBlock("BLOCKED_TEST_HOOK_IN_REAL_MODE",
                            "--now is a rehearsal hook; refused in real mode")
        parse_utc(args.now)
        return args.now
    return datetime.now(timezone.utc).strftime(NOW_FMT)


def anchor_utc_for(kickoff_utc: str) -> str:
    return datetime.fromtimestamp(
        parse_utc(kickoff_utc).timestamp() - ANCHOR_LEAD_SECONDS,
        tz=timezone.utc).strftime(NOW_FMT)


# --------------------------------------------------------------- forecast ----

def _fixture_team_id(fixture: dict, side: str, pm) -> str:
    """team_id identity law (freeze: renames fold into team_id): the
    substrate fixture's fixturedownload name resolves through the PINNED
    15-name crosswalk of the byte-pinned PM source; an unmapped name refuses
    (never guessed)."""
    name = str(fixture.get(f"{side}_team_id")
               or fixture.get(side) or "").strip()
    tid = pm.WSL_FD_NAME_TO_TEAM_ID.get(name) or (
        name if name.startswith("T-") else None)
    if not tid:
        raise LaneBlock("BLOCKED_TEAM_IDENTITY",
                        f"fixture {fixture.get('match_id')} {side} name "
                        f"{name!r} is outside the pinned crosswalk; "
                        "fail-closed")
    return tid


def engine_forecast(fixture: dict, corpus_rows: list[dict]) -> dict:
    """FORECAST via the byte-pinned frozen engine (K=24.0 nu=0.55 HCA=40.0):
    the day-batch replay evolves ratings over the freeze-excluded substrate
    corpus (played rows only; the engine's own (date, match_id) update order),
    then the fixture's p is the engine's own davidson3 on the end-of-(D-1)
    ratings — the day-batch PIT law (rows dated >= D never exist in the
    substrate, so nothing later can touch the state).

    Bit-exactness is PINNED, not assumed: this computation was verified to
    reproduce the provenance FORECAST row for FD-2026-M37 (p HOME
    0.7947807579055409 / DRAW 0.13235551666863574 / AWAY 0.07286372542582328,
    recorded by the WSL cycle's fidelity-proven adapter) EXACTLY, and the
    battery pins the equality (T-FX1). The §4.2 cross-check remains the
    standing guard: any drift refuses BLOCKED_FORECAST_DISAGREEMENT."""
    eng = load_wsl_engine()
    pm = load_pm_source()
    consts = WSL_LEAGUE_MODEL["constants"]
    rows = []
    for r in corpus_rows:
        rows.append({
            "match_id": str(r["match_id"]), "date": str(r["date"]),
            "season": str(r["season"]),
            "home_id": str(r["home_id"]), "away_id": str(r["away_id"]),
            "outcome": str(r["outcome"]),
        })
    rows.sort(key=lambda r: (r["date"], r["match_id"]))
    replay = eng.DayBatchReplay(
        rows, universe_seasons=sorted({r["season"] for r in rows}),
        predict_seasons=[])
    _preds, ratings = replay.run(float(consts["K"]), float(consts["nu"]),
                                 float(consts["HCA"]))
    hid = _fixture_team_id(fixture, "home", pm)
    aid = _fixture_team_id(fixture, "away", pm)
    rh = ratings.get(hid, eng.INIT_RATING)
    ra = ratings.get(aid, eng.INIT_RATING)
    ph, pd, pa = eng.davidson3(rh, ra, float(consts["HCA"]),
                               float(consts["nu"]))
    return {"HOME": ph, "DRAW": pd, "AWAY": pa}


def provenance_forecast_index(prov_ledger_path: Path, core) -> dict:
    """Chain-verified index {match_id: p} of the READ-ONLY provenance
    ledger's FORECAST rows (never imported as bets; never written)."""
    led = core.ledger.PaperLedger(Path(prov_ledger_path)).load()
    ok, errs = led.verify_chain()
    if not ok:
        raise LaneBlock("BLOCKED_TAMPER",
                        f"provenance ledger chain verify failed: {errs[:3]}")
    idx = {}
    for r in led.rows:
        if r.get("type") == "FORECAST" and r.get("league") == LEAGUE:
            idx[str(r["match_id"])] = {k: float(v)
                                       for k, v in (r.get("p") or {}).items()}
    return idx


def cross_check_forecast(fixture: dict, p: dict, prov_p: dict | None) -> dict:
    """§4.2 cross-check: ANY leg mismatch => BLOCKED_FORECAST_DISAGREEMENT
    (never averaged). Exact float equality: both sides are the pinned
    engine's own output recorded verbatim (json round-trip stable)."""
    if prov_p is None:
        raise LaneBlock("NOT_RUN_NO_PROVENANCE_FORECAST",
                        f"no provenance FORECAST row for {fixture['match_id']}; "
                        "the §4.2 cross-reference is required (fail-closed)")
    for leg in ("HOME", "DRAW", "AWAY"):
        a, b = p.get(leg), prov_p.get(leg)
        if a is None or b is None or float(a) != float(b):
            raise LaneBlock(
                "BLOCKED_FORECAST_DISAGREEMENT",
                f"{fixture['match_id']} leg {leg}: engine p {a!r} != "
                f"provenance p {b!r}; fail-closed, never averaged")


# ------------------------------------------------------------- phrase gate ---

def _registry_row(registry_path: Path, cycle_id: str) -> dict:
    reg = json.loads(Path(registry_path).read_text())
    cycles = reg.get("cycles", reg)
    if isinstance(cycles, dict):
        return cycles.get(cycle_id) or {}
    return next((c for c in cycles if c.get("cycle_id") == cycle_id), {})


def wsl_phrase_state(registry_path) -> dict:
    """b1r_switch_ts_verified pattern, evaluated FRESH on every call (the
    caller runs it IN-LOCK): both rows' go_phrase_state must start with
    OWNER_GO_TYPED_LIVE; the WSL phrase is lawful only AFTER the capital-v3
    phrase (ordering law §7). Returns the evidence recorded on the row."""
    rp = Path(registry_path)
    cap_row = _registry_row(rp, CAPITAL_V3_CYCLE_ID)
    wsl_row = _registry_row(rp, WSL_CYCLE_ID)
    cap_state = str(cap_row.get("go_phrase_state") or "")
    wsl_state = str(wsl_row.get("go_phrase_state") or "")
    cap_live = cap_state.startswith("OWNER_GO_TYPED_LIVE")
    wsl_live = wsl_state.startswith("OWNER_GO_TYPED_LIVE") and \
        len(wsl_state.split()) >= 2
    ev = {"capital_v3_cycle": CAPITAL_V3_CYCLE_ID,
          "capital_v3_state": cap_state, "capital_v3_live": cap_live,
          "wsl_cycle": WSL_CYCLE_ID, "wsl_state": wsl_state,
          "wsl_live": wsl_live, "wsl_bet_paper_phrase": WSL_BET_PAPER_PHRASE,
          "ordering_law": "WSL BET_PAPER only AFTER capital-v3 consumed (§7)"}
    if not cap_live:
        raise LaneBlock("BLOCKED_NO_GO",
                        "capital-v3 registry row does not record "
                        f"OWNER_GO_TYPED_LIVE ({cap_state!r}); the WSL "
                        "BET_PAPER phrase dies unconsumed (ordering law §7)",
                        EXIT_BLOCKED_NO_GO)
    if not wsl_live:
        raise LaneBlock("BLOCKED_NO_GO",
                        f"WSL registry go_phrase_state {wsl_state!r} does not "
                        f"record OWNER_GO_TYPED_LIVE for {WSL_BET_PAPER_PHRASE}",
                        EXIT_BLOCKED_NO_GO)
    return ev


def make_in_lock_recheck(ledger, core, registry_path, *, go_ok: bool,
                         walked_stake_cents: int):
    """The lane's composed IN-LOCK recheck (runs inside the ledger flock):
    (1) the WSL phrase gate on FRESH registry bytes; (2) the SHARED core's
    own in_lock_recheck with capital_law=3 (bounds + in-lock stake law);
    (3) stake-drift guard: if the in-lock stake != the walked budget stake,
    the quote no longer matches the stake — refuse (fail-closed; never
    re-size a walked book)."""
    core_recheck = core.risk.in_lock_recheck(ledger, "", go_ok, capital_law=3)

    def _recheck(decision: dict) -> dict:
        if decision.get("status") != "BET_PAPER":
            return decision
        wsl_phrase_state(registry_path)          # in-lock, fresh read
        decision = core_recheck(decision)
        if decision.get("status") == "BET_PAPER" and \
                decision.get("stake_cents") != walked_stake_cents:
            decision["status"] = "BLOCKED_STAKE_DRIFT"
            decision["reason"] = (
                f"in-lock recheck: stake moved to "
                f"{decision.get('stake_cents')}c after the book was walked at "
                f"{walked_stake_cents}c; the walked budget no longer matches "
                "the stake — fail-closed (stake never re-sized post-walk)")
            decision["stake_cents"] = 0
        return decision
    return _recheck


# ------------------------------------------------------------------ quote ----

def fee_law_d_eff(walk: dict) -> float:
    """d_eff = 1/(avg_cost_per_share_INCL_FEE) = shares/(spend + fee_total)
    (plan §3.4 second form; R5-2: taker fee 0.05·p·(1−p) exactly ONCE in the
    denominator — the per-level fees enter through their own sum, never a
    second time). The walk produced by walk_budget_for_stake() spends
    spend + fee_total == stake exactly, so d_eff == filled_shares/stake and
    the UNCHANGED settle() payout int(round(stake*(d_eff-1))) equals the
    §3.6 law round(filled_shares*100) - stake_cents exactly."""
    outlay = walk["spend_usdc"] + walk["fee_total_usdc"]
    if outlay <= 0:
        raise ValueError("empty walk has no d_eff")
    return walk["filled_shares"] / outlay


def walk_budget_for_stake(asks: list[dict], stake_cents: int,
                          pm) -> tuple[dict, dict]:
    """§2.4 + §3.3 walk semantics via the PINNED walk_the_book bytes ONLY:
    (1) depth check — the FULL stake must fill on asks alone (budget=
    stake_cents/100; budget_short must be 0; the stake is NEVER shrunk);
    (2) the recorded walk at the fee-adjusted ask budget B solving
    B + fee_total(B) == stake (§2.4: the walk consumes exactly the stake
    across asks+fees; single-level closed form B = stake*a/(a+f), iterated
    to 1e-12 in general — the pinned walk is monotone in B). The resulting
    filled_shares satisfies shares == stake/d_eff with d_eff per fee_law_d_eff."""
    full = pm.walk_the_book(asks, budget_usdc=stake_cents / 100.0)
    if full["filled_shares"] <= 0.0:
        return full, full            # empty book: caller refuses NO_QUOTE
    if full["budget_short_usdc"] > 1e-9:
        return full, full            # depth short: caller refuses NO_QUOTE_DEPTH
    stake_usd = stake_cents / 100.0
    b = stake_usd
    walk = full
    for _ in range(200):             # B + F(B) == stake; monotone fixed point
        walk = pm.walk_the_book(asks, budget_usdc=b)
        f = walk["fee_total_usdc"]
        err = (b + f) - stake_usd
        if abs(err) <= 1e-12:
            break
        b = stake_usd - f
    return full, walk


def snapshot_law_ok(fetch_ts_utc: str, anchor_utc: str) -> bool:
    """Snapshot law: fetched STRICTLY before the anchor; == anchor is stale
    (PIT law; mirrors the exec QUOTE_LEAD strictness)."""
    return parse_utc(fetch_ts_utc) < parse_utc(anchor_utc)


# Stage-label equivalence (documented translation, exact-key ONLY): the WSL
# substrate's committed stage law labels the league-phase 90-minute stage
# "LEAGUE_90MIN"; the pinned join law's whitelist carries the UNL-derived
# name of the SAME concept, "LEAGUE_PHASE_HOME_AWAY" (league stage, 90-min
# result, no extra time). The mapping is applied at the join boundary; any
# OTHER label passes through untranslated and the pinned join law refuses it
# (knockout/ET-possible/unknown stages stay fail-closed NOT_RUN_RULES).
_STAGE_JOIN_EQUIVALENT = {"LEAGUE_90MIN": "LEAGUE_PHASE_HOME_AWAY"}


def quote_event(fixture: dict, p: dict, *, stake_cents: int, fetch_ts_utc: str,
                events: list[dict], books_provider) -> tuple[dict | None,
                                                             dict | None,
                                                             dict | None]:
    """Join + book-walk ONE fixture at the ACTUAL stake. Returns
    (quote_for_core | None, market_quote_row | None, terminal_journal | None).
    books_provider(fixture, join, leg) -> (asks, book_hash, book_sha256).
    Zero network: the battery injects synthetic books; real captures use the
    pinned source's journaled GET plumbing (runner-side wiring; see
    execute._wire_wsl_real_quote)."""
    pm = load_pm_source()
    stage_raw = fixture.get("stage") or "LEAGUE_PHASE_HOME_AWAY"
    fx = {"league": LEAGUE, "match_id": fixture["match_id"],
          "home": fixture["home"], "away": fixture["away"],
          "kickoff_utc": fixture["kickoff_utc"],
          "stage": _STAGE_JOIN_EQUIVALENT.get(stage_raw, stage_raw), "p": p}
    anchor = anchor_utc_for(fixture["kickoff_utc"])
    if not snapshot_law_ok(fetch_ts_utc, anchor):
        return None, None, {
            "status": "NOT_RUN_SNAPSHOT_STALE",
            "reason": (f"quote fetched {fetch_ts_utc} not strictly before the "
                       f"anchor {anchor} (kickoff − 6h strict); PIT law")}
    joins = []
    for ev in events:
        j = pm.join_fixture_to_event(fx, ev)
        if j["status"] == "JOINED":
            joins.append(j)
        elif j.get("status") in ("NOT_RUN_KICKOFF_MISMATCH",
                                 "NOT_RUN_MARKET_INCOMPLETE",
                                 "NOT_RUN_MARKET_CLOSED",
                                 "NOT_RUN_RULES_MISMATCH",
                                 "NOT_RUN_MARKET_MISMATCH",
                                 "NOT_RUN_UNMAPPED_TEAM"):
            joins.append(j)
    joined = [j for j in joins if j["status"] == "JOINED"]
    if len(joined) > 1:
        return None, None, {
            "status": "NOT_RUN_MARKET_MISMATCH",
            "reason": f"{len(joined)} events join this fixture; ambiguous "
                      "joins refused"}
    if not joined:
        priority = ("NOT_RUN_KICKOFF_MISMATCH", "NOT_RUN_MARKET_INCOMPLETE",
                    "NOT_RUN_MARKET_CLOSED", "NOT_RUN_RULES_MISMATCH",
                    "NOT_RUN_UNMAPPED_TEAM")
        for st in priority:
            pick = next((j for j in joins if j["status"] == st), None)
            if pick:
                return None, None, {"status": _lane_status(st),
                                    "reason": pick["reason"]}
        return None, None, {
            "status": "NOT_RUN_NO_MARKET",
            "reason": "no OPEN Gamma event joins this fixture (both teams + "
                      "kickoff + league + 90-min stage); the old source is "
                      "never auto-fallback"}
    join = joined[0]
    budget_usdc = stake_cents / 100.0
    outcomes, book_walks = {}, {}
    for leg in ("HOME", "DRAW", "AWAY"):
        asks, bhash, bsha = books_provider(fixture, join, leg)
        full, walk = walk_budget_for_stake(asks, stake_cents, pm)
        walk["book_hash"] = bhash
        walk["book_sha256"] = bsha
        book_walks[leg] = walk
        mkt = join["legs"][leg]
        if full["filled_shares"] <= 0.0:
            return None, None, {
                "status": "NO_QUOTE",
                "reason": f"leg {leg}: empty ask side; never priced off "
                          "midpoint or last"}
        if full["budget_short_usdc"] > 1e-9:
            return None, None, {
                "status": "NO_QUOTE_DEPTH",
                "reason": (f"leg {leg}: book depth cannot fill the FULL stake "
                           f"{stake_cents}c (budget_short "
                           f"{full['budget_short_usdc']} USDC at the stake-"
                           "sized walk); the stake is NEVER shrunk to fit "
                           "depth")}
        a = walk["vwap_ask"]
        outcomes[leg] = {
            "leg": leg, "market_id": mkt["market_id"],
            "question": mkt["question"], "token_id_yes": mkt["token_id_yes"],
            "best_ask": walk["best_ask"], "vwap_ask": a,
            "filled_shares": walk["filled_shares"],
            "spend_usdc": walk["spend_usdc"],
            "fee_total_usdc": walk["fee_total_usdc"],
            "outlay_usdc": round(walk["spend_usdc"]
                                 + walk["fee_total_usdc"], 10),
            "levels_used": walk["levels_used"],
            "budget_short_usdc": full["budget_short_usdc"],
            "d_eff": fee_law_d_eff(walk),
        }
    quote = {
        "odds": {leg: outcomes[leg]["d_eff"] for leg in outcomes},
        "fetch_ts_utc": fetch_ts_utc,
        "source_last_update_utc": fetch_ts_utc,
        "bookmaker": "polymarket",
        "market": "90min-1X2-YES-binaries",
        "commence_time_utc": fixture["kickoff_utc"],
        "payload_sha256": hashlib.sha256(json.dumps(
            {l: book_walks[l]["fills"] for l in sorted(book_walks)},
            sort_keys=True).encode()).hexdigest(),
        "key_fingerprint": None,
        "pm_outcomes": outcomes,
        "event_id": join["event_id"],
        "payout_rules": join["payout_rules"],
        "anchor_utc": anchor,
    }
    row = {
        "type": "MARKET_QUOTE", "league": LEAGUE,
        "match_id": fixture["match_id"],
        "competition": fixture.get("competition") or "WSL_LEAGUE",
        "home": fixture["home"], "away": fixture["away"],
        "kickoff_utc": fixture["kickoff_utc"],
        "fetch_ts_utc": fetch_ts_utc,
        "source_last_update_utc": fetch_ts_utc,
        "bookmaker": "polymarket", "market": "90min-1X2-YES-binaries",
        "odds": quote["odds"],
        "commence_time_utc": fixture["kickoff_utc"],
        "payload_sha256": quote["payload_sha256"],
        "source_ref": ("polymarket gamma+clob via pinned polymarket_source "
                       "(sha 4b27ab17…); walk-the-book at the §3 stake"),
        "pm_outcomes": outcomes, "event_id": join["event_id"],
        "payout_rules": join["payout_rules"], "anchor_utc": anchor,
        "mode": "SYNTHETIC_BOOKS",
    }
    return quote, row, None


def _lane_status(src_status: str) -> str:
    """Pinned-source refusal -> the lane's precise taxonomy (plan §4.4)."""
    return {"NOT_RUN_RULES_MISMATCH": "NOT_RUN_RULES",
            "NOT_RUN_MARKET_INCOMPLETE": "NOT_RUN_MARKET_MISMATCH",
            }.get(src_status, src_status)


# ERRATUM_WSL_LANE_1 (2026-10-14): the pinned row below is a CONTROLLER-
# ERROR artifact — the first real quote run shipped the broad Gamma open-
# events scan (provably blind to the WSL tag listing; fixed in the same
# round a1e73cd3+), a same-name DIFFERENT event ('Bitcoin') surfaced as the
# join refusal, and the lane journaled NOT_RUN_UNMAPPED_TEAM for
# FD-2026-M37. The row remains in the shared ledger byte-frozen (append-only
# law); the lane treats EXACTLY these pinned row shas as NON-TERMINAL
# incident evidence — they neither block a later quote/decide pass nor count
# as the match's one decision. NO gate is loosened: the 1:1 join, verbatim
# 90-min rules, snapshot-before-anchor, full-stake depth, EV, shared risk
# bounds and the in-lock two-key phrase gate all still apply to every later
# row. Scope is the exact row sha, never a status pattern.
CONTROLLER_ERROR_NON_TERMINAL_ROWS = {
    "992aba48b6499dd140eb745c5e090c720de5d2d597eb1f8fed3c0f9cda2eaa2b":
        ("FD-2026-M37",
         "ERRATUM_WSL_LANE_1: broad-scan wiring artifact (fixed same round); "
         "a same-name different event surfaced as the join refusal"),
}


def non_terminal_matches(rows: list[dict]) -> set:
    """Matches whose EVERY decision row is a pinned controller-error
    artifact (a match with any real terminal row stays decided)."""
    art = set(CONTROLLER_ERROR_NON_TERMINAL_ROWS)
    by_match: dict[str, set] = {}
    for r in rows:
        if r.get("type") == "DECISION":
            by_match.setdefault(r.get("match_id"), set()).add(
                r.get("row_sha256"))
    return {mid for mid, shas in by_match.items() if shas and shas <= art}


class _NonTerminalView:
    """Read-only ledger view for the lane passes: identical to the real
    ledger except decided_match_ids() excludes matches decided ONLY by
    pinned controller-error rows (ERRATUM_WSL_LANE_1). Everything else
    (chain, equity, exposure, append-target rows) delegates untouched."""

    def __init__(self, led):
        self._led = led

    def __getattr__(self, name):
        return getattr(self._led, name)

    def decided_match_ids(self) -> set:
        return self._led.decided_match_ids() - non_terminal_matches(
            self._led.rows)


def terminal_journal(fixture: dict, status: str, reason: str, now: str) -> dict:
    """Terminal stake-0 journal row (never a silent drop; never a bet)."""
    return {
        "type": "DECISION", "league": LEAGUE, "match_id": fixture["match_id"],
        "competition": fixture.get("competition") or "WSL_LEAGUE",
        "home": fixture["home"], "away": fixture["away"],
        "kickoff_utc": fixture["kickoff_utc"], "decided_at_utc": now,
        "status": status, "reason": reason[:1500],
        "stake_cents": 0, "chosen_leg": None,
    }


# ------------------------------------------------- runner command surface ----
# The exec runner routes league=="WSL" here (execute.maybe_wsl). The core and
# ledger seams are overridable so the battery can drive the SAME code paths
# against candidate core copies (private module aliases) with zero network.

def core_of(args):
    """The pinned shared core for the host runner; battery/tests override the
    _impl attribute to point at a candidate core copy."""
    impl = getattr(core_of, "_impl", None)
    if impl is not None:
        return impl(args)
    from research.papertrade_exec import execute
    return execute.load_pinned_core(roots=execute._roots_from_args(args))


def ledger_path_of(args) -> Path:
    impl = getattr(ledger_path_of, "_impl", None)
    if impl is not None:
        return Path(impl(args))
    from research.papertrade_exec import execute
    return Path(execute.ledger_path_for(args))


def fixtures_for_day(args, day: str) -> list[dict]:
    """WSL fixtures from the program's own substrate (config
    wsl_fixture_substrate: a JSON lines file of fixtures). Sandbox mode uses
    the labeled synthetic fixtures passed via wsl_fixture_overrides."""
    impl = getattr(fixtures_for_day, "_impl", None)
    if impl is not None:
        return impl(args, day)
    import os
    if getattr(args, "sandbox", False):
        env = os.environ.get("WSL_LANE_SANDBOX_FIXTURES")
        if not env:
            return []
        return [json.loads(l) for l in Path(env).read_text().splitlines()
                if l.strip()]
    cfg = json.loads((Path(__file__).resolve().parent / "config.json")
                     .read_text())
    sub = cfg.get("wsl_fixture_substrate")
    if not sub:
        return []                     # no substrate committed => no fixtures
    out = []
    for line in Path(sub).expanduser().read_text().splitlines():
        if not line.strip():
            continue
        fx = json.loads(line)
        if str(fx.get("kickoff_utc", ""))[:10] == day:
            out.append(fx)
    return out


def plan_entry(args, day: str) -> dict:
    """cmd_plan's per-league entry for WSL (read-only; same shape as the
    other leagues so the runner's plan/upcoming render unchanged)."""
    core = core_of(args)
    led = core.ledger.PaperLedger(ledger_path_of(args)).load()
    ok, errs = led.verify_chain()
    if not ok:
        raise LaneBlock("BLOCKED_TAMPER",
                        f"chain verify failed: {errs[:3]}", 8)
    fc = {r["match_id"]: r for r in led.rows
          if r.get("type") == "FORECAST" and r.get("league") == LEAGUE}
    qt = {r["match_id"]: r for r in led.rows
          if r.get("type") == "MARKET_QUOTE" and r.get("league") == LEAGUE}
    decided = led.decided_match_ids()
    from datetime import datetime as _dt, timezone as _tz
    now_dt = _dt.now(_tz.utc)
    fixtures = fixtures_for_day(args, day)
    out_fixtures = []
    for fx in fixtures:
        anchor = anchor_utc_for(fx["kickoff_utc"])
        stage_raw = fx.get("stage") or "LEAGUE_PHASE_HOME_AWAY"
        checks = {
            "tip_utc": fx["kickoff_utc"], "et_local_date":
                str(fx["kickoff_utc"])[:10],
            "anchor_utc": anchor,
            "anchor_open_now": now_dt < parse_utc(anchor),
            "teams_known": "TBD" not in (fx.get("home"), fx.get("away")),
            "stage_bet_eligible":
                _STAGE_JOIN_EQUIVALENT.get(stage_raw, stage_raw) \
                == "LEAGUE_PHASE_HOME_AWAY",
            "forecast_present": fx["match_id"] in fc,
            "b1r_decision_forecast_valid": True,
            "quote_present": fx["match_id"] in qt,
            "already_decided": fx["match_id"] in decided,
        }
        checks["eligible_now"] = (checks["anchor_open_now"]
                                  and checks["teams_known"]
                                  and checks["stage_bet_eligible"]
                                  and not checks["already_decided"])
        out_fixtures.append({"match_id": fx["match_id"],
                             "home": fx["home"], "away": fx["away"],
                             "competition": fx.get("competition")
                             or "WSL_LEAGUE",
                             "source": "program substrate (config "
                                       "wsl_fixture_substrate)",
                             **checks})
    return {"fixtures": out_fixtures, "count": len(out_fixtures),
            "fixture_source": ("WSL league lane (CAPITAL-V3 §4): program "
                               "substrate; forecast = pinned frozen engine "
                               "109c3ec1… cross-checked vs the provenance "
                               "ledger; quote = Polymarket three-YES via "
                               "pinned polymarket_source 4b27ab17…")}


def cmd_forecast(args) -> dict:
    """FORECAST rows into the SHARED ledger via the pinned engine, then the
    §4.2 cross-check against the provenance ledger (mismatch refuses and
    journals nothing — the bad forecast never enters the shared ledger)."""
    now = now_of(args)
    core = core_of(args)
    register_wsl_league_law(core)
    led = core.ledger.PaperLedger(ledger_path_of(args)).load()
    ok, errs = led.verify_chain()
    if not ok:
        raise LaneBlock("BLOCKED_TAMPER", f"chain verify failed: {errs[:3]}", 8)
    prov = provenance_forecast_index(
        getattr(args, "wsl_provenance_ledger", None) or WSL_PROVENANCE_LEDGER,
        core)
    written, refused = [], []
    for fx in fixtures_for_day(args, args.date):
        if fx["match_id"] in fc_index(led):
            continue                     # idempotent (append-only law)
        try:
            p = engine_forecast(fx, fx.get("corpus_rows") or
                                substrate_corpus(args))
            cross_check_forecast(fx, p, prov.get(fx["match_id"]))
        except LaneBlock as lb:
            refused.append({"match_id": fx["match_id"],
                            "status": lb.code, "detail": lb.detail[:300]})
            continue
        row = {
            "type": "FORECAST", "league": LEAGUE,
            "match_id": fx["match_id"],
            "competition": fx.get("competition") or "WSL_LEAGUE",
            "home": fx["home"], "away": fx["away"],
            "kickoff_utc": fx["kickoff_utc"],
            "anchor_utc": anchor_utc_for(fx["kickoff_utc"]),
            "recorded_at_utc": now, "mode": "ENGINE",
            "model_id": WSL_LEAGUE_MODEL["model_id"],
            "model_constants": WSL_LEAGUE_MODEL["constants"],
            "model_version_sha": (f"WSL_B1_K24_NU0.55_HCA40@engine"
                                  f"{WSL_ENGINE_SHA256[:12]}"),
            "source_ref": ("pinned frozen wsl_engine sha 109c3ec1…; "
                           "cross-checked vs provenance ledger dd8a501f…"),
            "p": p, "fixture_source": fx.get("fixture_source")
            or "program substrate",
        }
        led.append(row)
        written.append(fx["match_id"])
    return {"league": LEAGUE, "date": args.date, "written": written,
            "refused": refused}


def fc_index(led) -> set:
    return {r["match_id"] for r in led.rows
            if r.get("type") == "FORECAST" and r.get("league") == LEAGUE}


def substrate_corpus(args) -> list[dict]:
    """The engine's rating corpus (config wsl_corpus_path, JSON lines of
    {match_id,date,season,home_id,away_id,outcome}); battery overrides via
    _impl."""
    impl = getattr(substrate_corpus, "_impl", None)
    if impl is not None:
        return impl(args)
    cfg = json.loads((Path(__file__).resolve().parent / "config.json")
                     .read_text())
    cp = cfg.get("wsl_corpus_path")
    if not cp:
        return []
    return [json.loads(l) for l in
            Path(cp).expanduser().read_text().splitlines() if l.strip()]


def cmd_quote(args) -> dict:
    """Polymarket quote capture for WSL: join + book-walk at the CURRENT
    ledger stake, snapshot law enforced, MARKET_QUOTE row into the SHARED
    ledger. books_provider seam: real mode uses the pinned source's journaled
    GET plumbing (controller-run, post-GO); sandbox injects books."""
    now = now_of(args)
    core = core_of(args)
    led = core.ledger.PaperLedger(ledger_path_of(args)).load()
    ok, errs = led.verify_chain()
    if not ok:
        raise LaneBlock("BLOCKED_TAMPER", f"chain verify failed: {errs[:3]}", 8)
    events = getattr(args, "wsl_pm_events", None) or []
    provider = getattr(args, "wsl_books_provider", None)
    if provider is None:
        raise LaneBlock("BLOCKED_NO_QUOTE_PLUMBING",
                        "no books provider wired (real captures are wired "
                        "post-GO through the pinned source's journaled GET "
                        "plumbing; the battery injects synthetic books)")
    written, journaled = [], []
    view = _NonTerminalView(led)
    for fx in fixtures_for_day(args, args.date):
        if fx["match_id"] in qt_index(led) or fx["match_id"] in \
                view.decided_match_ids():
            continue
        fc_rows = [r for r in led.rows if r.get("type") == "FORECAST"
                   and r.get("league") == LEAGUE
                   and r.get("match_id") == fx["match_id"]]
        if not fc_rows:
            journaled.append({"match_id": fx["match_id"],
                              "status": "NOT_RUN_NO_FORECAST"})
            continue
        p = fc_rows[-1]["p"]
        stake = core.stake_for_decision(led.equity_cents())
        if stake <= 0:
            journaled.append({"match_id": fx["match_id"],
                              "status": "BLOCKED_INSUFFICIENT_EQUITY"})
            continue
        quote, row, terminal = quote_event(
            fx, p, stake_cents=stake, fetch_ts_utc=now, events=events,
            books_provider=provider)
        if terminal is not None:
            led.append_decision(terminal_journal(fx, terminal["status"],
                                                 terminal["reason"], now))
            journaled.append({"match_id": fx["match_id"],
                              "status": terminal["status"]})
            continue
        row["mode"] = getattr(args, "wsl_quote_mode", None) or "REAL"
        led.append(row)
        written.append(fx["match_id"])
    return {"league": LEAGUE, "date": args.date, "written": written,
            "journaled": journaled}


def qt_index(led) -> set:
    return {r["match_id"] for r in led.rows
            if r.get("type") == "MARKET_QUOTE" and r.get("league") == LEAGUE}


def cmd_decide(args) -> dict:
    """The WSL decision pass: core evaluate with capital_law=3 and the lane's
    composed in-lock recheck (WSL phrase gate + core bounds + stake-drift
    guard). Every refusal is a precise journaled terminal row."""
    now = now_of(args)
    core = core_of(args)
    register_wsl_league_law(core)
    led = core.ledger.PaperLedger(ledger_path_of(args)).load()
    ok, errs = led.verify_chain()
    if not ok:
        raise LaneBlock("BLOCKED_TAMPER", f"chain verify failed: {errs[:3]}", 8)
    registry = getattr(args, "wsl_registry", None)
    if registry is None:
        from research.papertrade_exec import REGISTRY_PATH
        registry = (getattr(args, "sandbox_registry", None)
                    or REGISTRY_PATH)
    journaled = []
    view = _NonTerminalView(led)
    # W1.3 parity: a zero-variance WSL forecast batch is unbettable too.
    from research.papertrade_exec import execute as _exec
    batch_fc = [r for r in led.rows if r.get("type") == "FORECAST"
                and r.get("league") == LEAGUE]
    _exec.constant_forecast_block(batch_fc)
    for fx in fixtures_for_day(args, args.date):
        if fx["match_id"] in view.decided_match_ids():
            continue                     # one-decision law (idempotent)
        fc_rows = [r for r in led.rows if r.get("type") == "FORECAST"
                   and r.get("league") == LEAGUE
                   and r.get("match_id") == fx["match_id"]]
        qt_rows = [r for r in led.rows if r.get("type") == "MARKET_QUOTE"
                   and r.get("league") == LEAGUE
                   and r.get("match_id") == fx["match_id"]]
        if not fc_rows:
            row = terminal_journal(fx, "NOT_RUN_NO_FORECAST",
                                   "no shared-ledger engine forecast "
                                   "(forecast pass first)", now)
        elif not qt_rows:
            row = terminal_journal(fx, "NO_QUOTE",
                                   "no qualifying pre-anchor PM quote",
                                   now)
        else:
            forecast = {"p": fc_rows[-1]["p"],
                        "recorded_at_utc": fc_rows[-1]["recorded_at_utc"],
                        "model_version_sha":
                            fc_rows[-1].get("model_version_sha"),
                        "source_ref": fc_rows[-1].get("source_ref")}
            qrow = qt_rows[-1]
            quote = {"odds": qrow["odds"],
                     "fetch_ts_utc": qrow["fetch_ts_utc"],
                     "source_last_update_utc":
                         qrow["source_last_update_utc"],
                     "bookmaker": qrow["bookmaker"],
                     "market": qrow["market"],
                     "commence_time_utc": qrow["commence_time_utc"],
                     "payload_sha256": qrow["payload_sha256"]}
            stake = core.stake_for_decision(led.equity_cents())
            recheck = make_in_lock_recheck(view, core, registry, go_ok=True,
                                           walked_stake_cents=stake)
            # W1.4 parity: one odds snapshot must never price two fixtures.
            collide = _exec.quote_collision(led, fx["match_id"], qrow)
            if collide is not None:
                row = terminal_journal(
                    fx, "NOT_RUN_QUOTE_COLLISION",
                    f"quote odds signature identical to {collide} — one "
                    "snapshot cannot price two fixtures (W1.4); fail-closed",
                    now)
                row = led.append_decision(row)
                journaled.append({"match_id": fx["match_id"],
                                  "status": row.get("status"),
                                  "reason": (row.get("reason") or "")[:160]})
                continue
            dec = core.risk.evaluate_match(
                view, league=LEAGUE, match_id=fx["match_id"],
                competition=fx.get("competition") or "WSL_LEAGUE",
                home=fx["home"], away=fx["away"],
                kickoff_utc=fx["kickoff_utc"], now_utc=now,
                forecast=forecast, quote=quote, crosswalk_ok=True,
                go_ok=True, capital_law=3)
            # W1.5 parity: EV outlier quarantine (the live M39 loss came
            # from this lane at EV +196.68%).
            if dec.get("status") == "BET_PAPER" and max(
                    (dec.get("ev_net_by_leg") or {}).values() or [0.0]) > \
                    _exec.laws.EV_OUTLIER_THRESHOLD:
                class _Fx:  # minimal fixture view for the shared law
                    league, match_id = LEAGUE, fx["match_id"]
                    competition = fx.get("competition") or "WSL_LEAGUE"
                    home, away = fx["home"], fx["away"]
                    kickoff_utc = fx["kickoff_utc"]
                row, _kind = _exec.ev_outlier_disposition(
                    args, led, _Fx(), dec, qrow, now)
                row = led.append_decision(row, recheck=recheck,
                                          capital_law=3)
                journaled.append({"match_id": fx["match_id"],
                                  "status": row.get("status"),
                                  "reason": (row.get("reason") or "")[:160]})
                continue
            if dec.get("status") == "BET_PAPER":
                dec["forecast_row_sha256"] = fc_rows[-1]["row_sha256"]
                dec["quote_row_sha256"] = qrow["row_sha256"]
                dec["wsl_phrase_gate"] = "checked in-lock (see reason)"
            row = led.append_decision(dec, recheck=recheck, capital_law=3)
        journaled.append({"match_id": fx["match_id"],
                          "status": row.get("status"),
                          "reason": (row.get("reason") or "")[:160]})
    return {"league": LEAGUE, "date": args.date, "journaled": journaled}


def cmd_settle(args) -> dict:
    """WSL RESULTS SOURCE V1 (owner order 2026-10-20): settlement is lawful
    ONLY from the pinned UMA-resolution source — every entry of the staged
    results file must carry source_ref "polymarket_uma event=..." (produced
    exclusively by wsl_results.fetch_wsl_settleable from the bet's OWN
    tracked 3-YES markets). Anything else — hand-built files, guessed
    scores, other sources — REFUSES loudly (BLOCKED_NO_RESULTS_SOURCE) and
    every WSL bet stays OPEN. The money math + ledger append remain with
    the PINNED core (execute._cmd_settle_standard -> risk.settle)."""
    results_path = Path(getattr(args, "results", ""))
    entries = {}
    if results_path.exists():
        entries = json.loads(results_path.read_text())
    if not isinstance(entries, dict) or not entries:
        raise LaneBlock("BLOCKED_NO_RESULTS_SOURCE",
                        "WSL settle requires staged results from the pinned "
                        "polymarket_uma source — file missing/empty", 9)
    for mid, v in entries.items():
        src = v.get("source_ref", "") if isinstance(v, dict) else ""
        res = v.get("result") if isinstance(v, dict) else None
        if not str(src).startswith("polymarket_uma event=") or res not in (
                "HOME", "DRAW", "AWAY"):
            raise LaneBlock("BLOCKED_NO_RESULTS_SOURCE",
                            f"entry {mid} is not from the pinned "
                            f"polymarket_uma source — refusing (stays "
                            f"OPEN, never a guessed settlement)", 9)
    from research.papertrade_exec import execute as _exec
    return _exec._cmd_settle_standard(args)
