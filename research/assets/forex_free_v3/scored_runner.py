#!/usr/bin/env python
"""FOREX-FREE-V3: central scored runner (V3-I lane, adapted from V2).

Architecture is the proven V2 one: family modules expose arm APIs that
produce schedules, the runner does ALL booking (through the V3 P1 accounting
kernel, NOT V2's), applies the frozen Stage-A gates, supports a dummy
dry-run mode (``scored=false``, ``real_pnl=false``, publication refused) and
publishes once-only, digest-addressed, behind a freeze token.  Gate
thresholds are frozen in
``research/control/forex_free_v3_run/baseline_invariants.json`` and were set
BEFORE any V3 scored PnL existed; no gate may change after any real cell
result is visible.

=======================================================================
FAMILY API CONTRACT (family lanes implement against THIS, nothing else)
=======================================================================

A family module (or object) registered via :func:`register_family` must
expose exactly one entry point::

    def run_arm(arm: str, data_paths: dict, macro_reader, freeze_token: str | None)
        -> {"decisions": [...], "financing_events": [...], "meta": {...}}

``arm``            one of the family's three frozen SCORED arms: "anchor",
                   "neighbour", "causal_negative_control" (the driver also
                   accepts the shorthand "control") -- plus the REQUIRED
                   "benchmark_treatment" arm (V3-I, finding H1): the frozen
                   benchmark treatment of baseline_invariants.json
                   ``v3_benchmark_treatment`` -- the SAME mechanism with macro
                   conditioning removed, at identical decision clock, fills,
                   universe, warmup and costs, emitting decisions AND financing
                   events exactly like a scored arm.  The runner calls it
                   whenever a SCORED anchor cell is computed and refuses a cell
                   that cannot supply it (fail closed); it is never a scored
                   cell itself (``compute_cell`` refuses it as an ``arm``).
``data_paths``     opaque mapping passed through from the driver; the only
                   key the runner itself understands is ``macro_vintages``
                   (see :mod:`research.assets.forex_free_v3.macro_reader`).
``macro_reader``   a ``PolicyRateReader`` built by the runner.  Read policy
                   rates ONLY through it: ``macro_reader.policy_rate(area,
                   decision_ts)`` / ``.differential(base_area, quote_area,
                   decision_ts)``.  It is availability-gated and raises
                   ``MacroDataBlocked`` (``BLOCKED_DATA``) when a series is
                   missing; ``None`` return = NO_EVAL (fail closed, never
                   backfill).
``freeze_token``   ``None`` => DUMMY DRY-RUN mode (scored=false); the frozen
                   W3 token => scored mode.  Families must not branch on
                   anything else.

Return payload:

``decisions``         list of DECISION EVENTS, daily-or-slower (both
                      selected proposals are DAILY).  Exactly one entry per
                      round trip; flat = absence, never side 0.  Required
                      keys::
                          decision_id    unique string (becomes trade_id)
                          pair           "BASE/QUOTE", never "USD" alone
                          decision_ts    UTC ISO instant of the completed
                                         16:00 America/New_York daily bar
                          side           +1 long base / -1 short base
                          notional_usd   10000 (frozen USD-unit design)
                          entry_bar_ts   UTC ISO of the NEXT 16:00-NY bar
                                         after decision_ts (one-event lag;
                                         Friday decisions fill Monday)
                          entry_price    OPEN of entry_bar_ts
                          exit_bar_ts    UTC ISO of the exit fill bar
                          exit_price     OPEN of exit_bar_ts
                          force_flat     true when closed at a fold boundary
``financing_events``  one per decision::
                          {"decision_id": id,
                           "financing_adjustment_usd": number (may be <= 0),
                           "formula": "<frozen formula identifier>"}
                      The runner CARRIES, sums and digests the adjustment;
                      it NEVER computes it.  A decision without a matching
                      event is refused (MISSING_FINANCING_EVENT).  All
                      events of one arm must carry the same ``formula``.
``meta``              dict with REQUIRED key ``decision_clock`` == "daily"
                      (any other declared clock is refused: CLOCK_UNSUPPORTED)
                      and OPTIONAL keys: ``proposal_id``, ``pair_universe``,
                      ``fill_delay_events`` ({decision_id: delayed-fill
                      count} for the frozen one-event-delay stress, carried
                      UNBLENDED), ``incremental_alpha`` (pass-through for
                      non-anchor arms only).

V3-I runner-owned statistics (family meta is NOT consulted):

* USD index (finding H2): the frozen D1 equal-weight USD-leg return index
  is computed INSIDE the runner from the authorized 7-pair H1 snapshot
  (``data_paths`` "usd_index_h1_dir", else "price_h1_dir", else "h1_dir");
  per scored arm the correlation of daily arm PnL vs the index feeds the
  frozen ``usd_corr_abs_ceiling`` gate.  ``meta.usd_index_daily_returns``
  is ignored.  A SCORED run with booked trades but no price source fails
  closed (USD_INDEX_SOURCE_MISSING); a dry-run never leaks the statistic.
* incremental alpha (finding H1): for a SCORED anchor cell the runner
  books the family's ``benchmark_treatment`` arm through the SAME cost
  kernel (dual book) and records
  ``incremental_alpha = anchor financing-adjusted expectancy -
  benchmark expectancy``; the value is ALWAYS present on a scored anchor
  record.  Dry-run records carry ``None`` (no outcome may leak).

Runner-side enforcement (fail closed, codes on ``DecisionRuleError``):
DECISION_CLOCK_VIOLATION (decision/fill instants not 16:00-NY daily bars),
ONE_EVENT_LAG_VIOLATION (same-bar fill or fill lag > 4 days),
FOLD_FORCE_FLAT_VIOLATION (a trade spans an internal fold boundary),
MISSING_FINANCING_EVENT / FINANCING_EVENT_UNMATCHED / MISSING_FINANCING_FORMULA
/ FINANCING_FORMULA_INCONSISTENT, DUPLICATE_DECISION_ID, CLOCK_UNSUPPORTED.
Weekend entries are dropped fail-closed by the inherited session gate.
"""
import json
import math
import os
import threading
from datetime import datetime, timedelta, timezone

from research.assets.forex_free_v3 import accounting
from research.assets.forex_free_v3.macro_reader import (
    MacroReader,
    PolicyRateReader,
)

FAMILIES: dict = {}
PAIRS = ("EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD",
         "USD/JPY", "USD/CHF", "USD/CAD")
NOTIONAL = 10000
ARMS = ("anchor", "neighbour", "control")
BENCHMARK_ARM = "benchmark_treatment"  # required family arm, never a scored cell
# USD-leg sign of the frozen D1 index: XXX/USD contributes -pair return,
# USD/XXX contributes +pair return.
USD_LEG_SIGN = {p: (-1.0 if p.endswith("/USD") else 1.0) for p in PAIRS}
BASE_TIER = 1.0
STRESS_TIERS = (1.5, 2.0)          # booked stress tiers (kernel ladder adds base 1.0)
FOLD_BOUNDARIES = ("2020-03-01T00:00:00+00:00", "2022-05-01T00:00:00+00:00",
                   "2024-07-01T00:00:00+00:00", "2026-09-02T23:59:59+00:00")
INTERNAL_BOUNDARIES = (FOLD_BOUNDARIES[1], FOLD_BOUNDARIES[2])
PURGE_DAYS = 14
FREEZE_TOKEN = "FOREX_FREE_V3_W3"  # freeze code per PLAN_forex_v3.md section 10
# Frozen before any V3 outcome (baseline_invariants.json, inherited V2 set):
MIN_EXPECTANCY = 0.0            # after-cost financing-adjusted expectancy > 0
MIN_PF = 1.10
MIN_POSITIVE_FOLDS = 2          # of 3 populated
MIN_FOLD_PF = 0.80
FOLD_POPULATED_MIN_TRADES = 30
MDD_CEILING_USD = 2500.0
MAX_POS_FOLD_SHARE = 0.50
MAX_PAIR_POS_SHARE = 0.40
STRESS_MIN_PF = 1.00
DROPOUT_SURVIVAL_MIN = 5        # frozen minimum; the scenario suite is the 7
                                # drop-one-PAIR exclusions PLUS 1
                                # drop-one-BEST-fold (V3-I finding M1)
NEIGHBOUR_MIN_EXPECTANCY = 0.0
CONTROL_REJECT_PF = 1.10
USD_CORR_CEILING = 0.30         # |corr(daily pnl, USD-index daily return)|
USD_DIAG_MIN_DAYS = 60
MIN_DECISIONS_PER_ARM = 40      # baseline v3_sample_floors
MAX_FILL_LAG_DAYS = 4           # weekend allowance for the one-event-lag fill
PER_ARM_TIMEOUT_MINUTES = 60.0  # resource_contract.per_arm_timeout_minutes


def register_family(family_id, module_or_instance) -> None:
    """Register a family module/object exposing ``run_arm``."""
    if not hasattr(module_or_instance, "run_arm"):
        raise ValueError(f"family {family_id!r} does not expose run_arm")
    FAMILIES[family_id] = module_or_instance


class DecisionRuleError(ValueError):
    """A family decision stream violated a frozen V3 rule; fail closed."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


class TechAbort(RuntimeError):
    """Fail-closed abort before any scored metric exists (PLAN section 11)."""

    reason = "TECHABORT"


# ---------- session gate (frozen, outcome-blind, inherited) ----------
def is_market_open_entry(ts_iso, tz="America/New_York"):
    """Frozen trading week: Sun 21:00 New York -> Fri 16:00 New York.
    Fill instants outside are dropped fail-closed."""
    t = datetime.fromisoformat(ts_iso)
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    from zoneinfo import ZoneInfo
    ny = t.astimezone(ZoneInfo(tz))
    wd, hm = ny.weekday(), ny.hour * 60 + ny.minute
    if wd == 6:                       # Sunday
        return hm >= 21 * 60
    if wd == 4:                       # Friday
        return hm < 16 * 60
    if wd == 5:                       # Saturday
        return False
    return True                       # Mon-Thu


def apply_session_gate(trades):
    kept, dropped = [], []
    for tr in trades:
        (kept if is_market_open_entry(tr["entry_bar_ts"]) else dropped).append(tr)
    return kept, dropped


# ---------- folds (inherited unchanged from V2 w2_freeze) ----------
def _parse(ts):
    return datetime.fromisoformat(ts)


def fold_of(entry_ts_iso):
    """Fold index by entry instant; None if purged (within PURGE_DAYS after a
    boundary) or before the first boundary (warmup region)."""
    t = _parse(entry_ts_iso)
    for i in range(3):
        lo = _parse(FOLD_BOUNDARIES[i])
        hi = _parse(FOLD_BOUNDARIES[i + 1])
        if lo <= t < hi:
            if t < lo + timedelta(days=PURGE_DAYS):
                return None
            return i
    return None


# ---------- decision-stream validation (V3 deltas) ----------
def _require_utc_iso(ts, code, what):
    try:
        t = datetime.fromisoformat(str(ts))
    except ValueError as exc:
        raise DecisionRuleError(code, f"{what} is not an ISO-8601 instant: {ts!r}") from exc
    if t.tzinfo is None:
        raise DecisionRuleError(code, f"{what} is timezone-naive: {ts!r}")
    return t.astimezone(timezone.utc)


def _is_ny_1600(t):
    from zoneinfo import ZoneInfo
    ny = t.astimezone(ZoneInfo("America/New_York"))
    return ny.hour == 16 and ny.minute == 0


def validate_decisions(decisions, financing_events):
    """Enforce the V3 decision-clock deltas; return (trades, adjustments).

    Trades are the decision dicts (order preserved) with parsed instants;
    adjustments maps decision_id -> financing_adjustment_usd exactly as the
    family carried it (never recomputed).
    """
    if not isinstance(decisions, list):
        raise DecisionRuleError("DECISION_CLOCK_VIOLATION",
                                "run_arm returned no decision list")
    if not decisions:
        # An empty book is a legitimate (gate-failing) outcome, not an abort:
        # it fails DECISION_FLOOR_NOT_MET / STRESS_EMPTY_TRADE_SET at gating.
        if financing_events:
            raise DecisionRuleError("FINANCING_EVENT_UNMATCHED",
                                    "financing events without any decision")
        return [], {}, None
    seen = set()
    for d in decisions:
        did = d.get("decision_id")
        if not isinstance(did, str) or not did:
            raise DecisionRuleError("DECISION_CLOCK_VIOLATION", "decision_id missing")
        if did in seen:
            raise DecisionRuleError("DUPLICATE_DECISION_ID", did)
        seen.add(did)
        if d.get("side") not in (1, -1):
            raise DecisionRuleError("DECISION_CLOCK_VIOLATION",
                                    f"{did}: side must be +1/-1, got {d.get('side')!r}")
        if d.get("pair") == accounting.CASH_CURRENCY:
            raise DecisionRuleError("DECISION_CLOCK_VIOLATION",
                                    f"{did}: cash currency is never a pair")
        if float(d.get("notional_usd", 0)) <= 0:
            raise DecisionRuleError("DECISION_CLOCK_VIOLATION",
                                    f"{did}: notional_usd must be > 0")
        dec = _require_utc_iso(d.get("decision_ts"), "DECISION_CLOCK_VIOLATION",
                               f"{did}: decision_ts")
        if not _is_ny_1600(dec):
            raise DecisionRuleError(
                "DECISION_CLOCK_VIOLATION",
                f"{did}: decision_ts {dec.isoformat()} is not a completed 16:00 "
                "America/New_York daily bar (daily-or-slower clock)")
        entry = _require_utc_iso(d.get("entry_bar_ts"), "DECISION_CLOCK_VIOLATION",
                                 f"{did}: entry_bar_ts")
        if not _is_ny_1600(entry):
            raise DecisionRuleError(
                "DECISION_CLOCK_VIOLATION",
                f"{did}: entry_bar_ts {entry.isoformat()} is not a 16:00-NY bar")
        exit_ = _require_utc_iso(d.get("exit_bar_ts"), "DECISION_CLOCK_VIOLATION",
                                 f"{did}: exit_bar_ts")
        if not _is_ny_1600(exit_):
            raise DecisionRuleError(
                "DECISION_CLOCK_VIOLATION",
                f"{did}: exit_bar_ts {exit_.isoformat()} is not a 16:00-NY bar")
        if not (entry > dec):
            raise DecisionRuleError(
                "ONE_EVENT_LAG_VIOLATION",
                f"{did}: fill {entry.isoformat()} is not strictly after the "
                "decision instant (same-bar fill forbidden)")
        if entry - dec > timedelta(days=MAX_FILL_LAG_DAYS):
            raise DecisionRuleError(
                "ONE_EVENT_LAG_VIOLATION",
                f"{did}: fill {entry.isoformat()} is more than {MAX_FILL_LAG_DAYS} days "
                "after the decision; not the next-session bar")
        if not (exit_ > entry):
            raise DecisionRuleError("DECISION_CLOCK_VIOLATION",
                                    f"{did}: exit_bar_ts is not after entry_bar_ts")
        for boundary in INTERNAL_BOUNDARIES:
            b = _parse(boundary)
            if entry < b <= exit_:
                raise DecisionRuleError(
                    "FOLD_FORCE_FLAT_VIOLATION",
                    f"{did}: trade [{entry.isoformat()} .. {exit_.isoformat()}] spans the "
                    f"fold boundary {boundary}; fold boundaries force-flat")
    adjustments = {}
    formulas = set()
    for ev in financing_events or []:
        did = (ev or {}).get("decision_id")
        if did not in seen:
            raise DecisionRuleError("FINANCING_EVENT_UNMATCHED",
                                    f"no decision carries id {did!r}")
        if did in adjustments:
            raise DecisionRuleError("FINANCING_EVENT_UNMATCHED",
                                    f"duplicate financing event for {did!r}")
        value = (ev or {}).get("financing_adjustment_usd")
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(float(value)):
            raise DecisionRuleError("MISSING_FINANCING_EVENT",
                                    f"{did}: financing_adjustment_usd must be a finite number")
        formula = (ev or {}).get("formula")
        if not isinstance(formula, str) or not formula:
            raise DecisionRuleError("MISSING_FINANCING_FORMULA",
                                    f"{did}: financing event carries no formula identifier")
        formulas.add(formula)
        adjustments[did] = float(value)
    missing = sorted(seen - set(adjustments))
    if missing:
        raise DecisionRuleError("MISSING_FINANCING_EVENT",
                                f"decisions without financing events: {missing}")
    if len(formulas) != 1:
        raise DecisionRuleError("FINANCING_FORMULA_INCONSISTENT",
                                f"arm mixes formula identifiers {sorted(formulas)}")
    return decisions, adjustments, formulas.pop()


# ---------- metrics (V2 conventions, carried unchanged) ----------
book_metrics = accounting.book_metrics  # same rounding/None-PF convention as V2


def fold_metrics(trades):
    out = []
    for f in range(3):
        ftr = [t for t in trades if t["_fold"] == f]
        m = book_metrics([t["_pnl"] for t in ftr])
        m["fold"] = f
        m["populated"] = m["trades"] >= FOLD_POPULATED_MIN_TRADES
        out.append(m)
    return out


def mdd_of(pnls):
    peak = trough = 0.0
    cum = 0.0
    mdd = 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        mdd = max(mdd, peak - cum)
    return round(mdd, 10)


def concentration(trades):
    """Share of gross positive pnl by pair; cash never appears (kernel rule)."""
    pos = [t for t in trades if t["_pnl"] > 0]
    gp = sum(t["_pnl"] for t in pos)
    if gp <= 0:
        return {}
    shares = {}
    for t in pos:
        if t["pair"] == accounting.CASH_CURRENCY:
            continue
        shares[t["pair"]] = shares.get(t["pair"], 0.0) + t["_pnl"]
    return {k: round(v / gp, 6) for k, v in shares.items()}


def fold_positive_share(folds):
    gp = sum(f["gross_positive"] for f in folds if f["gross_positive"] > 0)
    if gp <= 0:
        return 0.0
    return round(max(f["gross_positive"] for f in folds) / gp, 6)


def dropout_scenarios(scored, pnls_fin, folds):
    """Frozen dropout suite (V3-I finding M1): the SEVEN drop-one-PAIR
    exclusions (one per frozen universe pair, the inherited suite) PLUS ONE
    drop-one-BEST-fold exclusion (the fold with the highest expectancy among
    folds holding trades; its trades are removed and the after-cost
    expectancy of the reduced book recomputed) -- eight scenarios in total.

    A scenario survives iff the reduced book's financing-adjusted expectancy
    is > 0.  Returns the per-scenario record list; an unevaluable fold
    scenario (no fold holds trades) is recorded as NOT survived (fail
    closed).  The frozen gate counts survivals against the UNCHANGED
    DROPOUT_SURVIVAL_MIN (= 5)."""
    scenarios = []
    for excl in PAIRS:
        sub = [p for t, p in zip(scored, pnls_fin) if t["pair"] != excl]
        exp = round(sum(sub) / len(sub), 10) if sub else 0.0
        scenarios.append({"scenario": f"drop_pair:{excl}",
                          "expectancy": exp, "survived": bool(exp > 0)})
    candidates = [f for f in folds if f["trades"] > 0]
    if candidates:
        best = max(candidates, key=lambda f: (f["expectancy"], -f["fold"]))
        sub = [p for t, p in zip(scored, pnls_fin) if t["_fold"] != best["fold"]]
        exp = round(sum(sub) / len(sub), 10) if sub else 0.0
        scenarios.append({"scenario": f"drop_best_fold:{best['fold']}",
                          "expectancy": exp, "survived": bool(exp > 0)})
    else:
        scenarios.append({"scenario": "drop_best_fold:none",
                          "expectancy": None, "survived": False})
    return scenarios


# ---------- dry-run hygiene (V3-I, finding H3) ----------
_MONETARY_BOOK_KEYS = ("gross_price_pnl_usd", "price_only_pnl_usd",
                       "financing_adjustment_usd", "financing_adjusted_pnl_usd")


def _zero_metrics(metrics):
    """Placeholder metrics: every monetary field zeroed/None, counts kept."""
    out = dict(metrics)
    for key in ("total_pnl", "expectancy", "gross_positive"):
        if key in out:
            out[key] = 0.0
    if "pf" in out:
        out["pf"] = None
    if "cost_component_delta_vs_base_usd" in out:
        out["cost_component_delta_vs_base_usd"] = 0.0
    return out


def dry_run_sanitized(record):
    """V3-I H3 hygiene, applied to EVERY dummy dry-run record AFTER internal
    computation: zero/placeholder EVERY booked monetary metric so no outcome
    information can leave this module (the module contract and the driver's
    'Reveals no outcome' both demand it).  Counts (n_decisions,
    n_trades_kept, weekend_gate_dropped, purged_trades, folds_declared,
    per-metrics trades, delay_stress counts) and the scored/real_pnl/
    published=false flags survive untouched."""
    for key in _MONETARY_BOOK_KEYS:
        record[key] = 0.0
    for key in ("base", "base_price_only"):
        record[key] = _zero_metrics(record[key])
    record["folds"] = [_zero_metrics(f) for f in record["folds"]]
    record["stress"] = {tier: _zero_metrics(m)
                        for tier, m in record["stress"].items()}
    record["break_even_cost_bps"] = None
    record["mdd_usd"] = 0.0
    record["fold_positive_share"] = 0.0
    record["pair_concentration"] = {}
    record["drop_one_expectancy"] = {p: 0.0 for p in record["drop_one_expectancy"]}
    record["dropout_scenarios"] = [
        {"scenario": s["scenario"], "expectancy": None, "survived": None}
        for s in record["dropout_scenarios"]]
    record["incremental_alpha"] = None
    record["benchmark_treatment"] = None
    record["usd_drift_diag"] = {"corr": None,
                                "n_days": record["usd_drift_diag"]["n_days"],
                                "evaluated": False}
    record["dry_run"] = True
    record["real_pnl"] = False
    return record


# ---------- USD index (V3-I, finding H2: computed INSIDE the runner) ----------
def load_daily_16ny_closes(price_dir, pair):
    """Ascending ``[(utc datetime, close)]`` of a pair's 16:00-NY weekday H1
    bars from the canonical snapshot files (``{TAG}_1h_*.json`` under
    ``price_dir``; td_loader schema datetime/open/high/low/close).

    Error-status provider windows are skipped; duplicate bar stamps dedupe on
    first sighting; non-positive/non-finite closes fail closed
    (``BLOCKED_DATA``).  Read-only view of the SAME authorized snapshot the
    families consume -- never a new data authority.  A missing directory
    fails closed; a pair with no snapshot files contributes nothing (the
    equal-weight mean runs over the pairs present)."""
    tag = pair.replace("/", "")
    if not os.path.isdir(price_dir):
        raise RuntimeError(
            f"BLOCKED_DATA: USD-index H1 directory not found for {pair}: {price_dir!r}")
    names = sorted(f for f in os.listdir(price_dir)
                   if f.startswith(f"{tag}_1h_") and f.endswith(".json"))
    if not names:
        return []  # pair absent from this snapshot: no contribution
    from zoneinfo import ZoneInfo
    ny = ZoneInfo("America/New_York")
    rows = []
    seen = set()
    for name in names:
        with open(os.path.join(price_dir, name), "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict) and payload.get("status") == "error":
            continue  # provider no-coverage window
        values = payload.get("values") if isinstance(payload, dict) else None
        if not isinstance(values, list):
            raise RuntimeError(f"BLOCKED_DATA: malformed H1 window {name!r}")
        for row in values:
            raw = (row or {}).get("datetime")
            close = (row or {}).get("close")
            try:
                ts = datetime.strptime(str(raw), "%Y-%m-%d %H:%M:%S") \
                    if "-" in str(raw) and "T" not in str(raw) \
                    else datetime.fromisoformat(str(raw))
                ts = ts.replace(tzinfo=timezone.utc)  # snapshot stamps are UTC wall time
                close = float(close)
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    f"BLOCKED_DATA: malformed bar in {name!r}: {exc}") from exc
            if ts in seen:
                continue
            if not (math.isfinite(close) and close > 0):
                raise RuntimeError(
                    f"BLOCKED_DATA: non-positive/non-finite close in {name!r}")
            seen.add(ts)
            local = ts.astimezone(ny)
            if local.hour == 16 and local.minute == 0 and local.weekday() < 5:
                rows.append((ts, close))
    rows.sort(key=lambda b: b[0])
    return rows


def usd_index_daily_returns(price_dir, pairs=PAIRS):
    """Frozen D1 equal-weight USD-leg return index, built from the authorized
    H1 snapshot ONLY (V3-I finding H2 -- the family-supplied meta series is
    no longer consulted).

    Daily step = 16:00-NY bar -> next EXISTING 16:00-NY bar (a Fri->Mon step
    spans the weekend as one daily step).  ``XXX/USD`` contributes the
    NEGATIVE pair return, ``USD/XXX`` the positive pair return; the index
    value of a day is the equal-weight mean of the contributing pairs'
    signed returns, keyed by the UTC date of the later bar of the step.
    On a partial snapshot the mean runs over the pairs present (tests pin
    the 2-pair case); on the authorized snapshot that is the full 7-pair
    universe.  A source with NO usable pair raises (fail closed)."""
    per_pair = _usd_index_pair_steps(price_dir, pairs)
    if not per_pair:
        raise RuntimeError(
            f"BLOCKED_DATA: USD index has no usable pair under {price_dir!r}")
    days = sorted({d for steps in per_pair.values() for d in steps})
    return {d: math.fsum(s[d] for s in per_pair.values() if d in s)
            / sum(1 for s in per_pair.values() if d in s) for d in days}


def _usd_index_pair_steps(price_dir, pairs):
    """Per-pair signed daily-return steps {pair: {day: signed return}} for
    the pairs present in the snapshot (absent pairs contribute nothing)."""
    per_pair = {}
    for pair in pairs:
        bars = load_daily_16ny_closes(price_dir, pair)
        if not bars:
            continue
        steps = {}
        for (t0, c0), (t1, c1) in zip(bars, bars[1:]):
            steps[str(t1.date())] = USD_LEG_SIGN[pair] * (c1 / c0 - 1.0)
        per_pair[pair] = steps
    return per_pair


def usd_index_from_data_paths(data_paths):
    """Locate the snapshot directory in ``data_paths`` and build the index.

    Understood keys, in order: ``usd_index_h1_dir`` (explicit override),
    ``price_h1_dir`` (family1), ``h1_dir`` (family2).  Returns
    ``(index, source_key, n_pairs_used)``; ``(None, None, 0)`` when
    data_paths carries no price source at all (a SCORED run with booked
    trades then fails closed in :func:`compute_cell`).  A PRESENT but
    broken source raises (fail closed) -- a malformed snapshot can never
    silently disable the gate."""
    if not isinstance(data_paths, dict):
        return None, None, 0
    for key in ("usd_index_h1_dir", "price_h1_dir", "h1_dir"):
        source = data_paths.get(key)
        if isinstance(source, str) and source:
            per_pair = _usd_index_pair_steps(source, PAIRS)
            if not per_pair:
                raise RuntimeError(
                    f"BLOCKED_DATA: USD index has no usable pair under {source!r}")
            days = sorted({d for steps in per_pair.values() for d in steps})
            index = {d: math.fsum(s[d] for s in per_pair.values() if d in s)
                     / sum(1 for s in per_pair.values() if d in s) for d in days}
            return index, key, len(per_pair)
    return None, None, 0


def usd_drift_corr(trades, usd_index_daily_returns):
    """Frozen inherited D1 diagnostic: Pearson corr between daily aggregate
    trade pnl and the equal-weight USD-index daily return (frozen D1 formula,
    computed INSIDE the runner from the authorized snapshot -- V3-I finding
    H2).  Evaluates only over >= USD_DIAG_MIN_DAYS days with trades;
    otherwise it cannot fail."""
    daily = {}
    for t in trades:
        day = str(t["entry_bar_ts"])[:10]
        daily[day] = daily.get(day, 0.0) + t["_pnl"]
    days = sorted(daily)
    if len(days) < USD_DIAG_MIN_DAYS:
        return {"corr": None, "n_days": len(days), "evaluated": False}
    xs, ys = [], []
    for d in days:
        r = usd_index_daily_returns.get(d)
        if r is not None:
            xs.append(float(r))
            ys.append(daily[d])
    if len(xs) < 3:
        return {"corr": None, "n_days": len(xs), "evaluated": False}
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    r = cov / math.sqrt(vx * vy) if vx > 0 and vy > 0 else 0.0
    return {"corr": round(r, 6), "n_days": len(xs), "evaluated": True}


# ---------- booking (V3 kernel: dual book + F1-fixed stress) ----------
def _spec_of(decision):
    return accounting.TradeSpec(
        trade_id=decision["decision_id"], pair=decision["pair"],
        side="LONG" if decision["side"] > 0 else "SHORT",
        notional_usd=float(decision["notional_usd"]),
        entry_price=float(decision["entry_price"]),
        exit_price=float(decision["exit_price"]),
        entry_ts_utc=decision["entry_bar_ts"], exit_ts_utc=decision["exit_bar_ts"])


def book_trades(trades, financing_adjustments, dry_run=False):
    """Book kept decisions once per side at the base tier through the V3
    kernel, carrying BOTH book columns.  In dry_run the book columns are
    replaced by 0.0 placeholders (real_pnl=false); mechanics still book so
    counts/folds/costs reconcile without revealing any outcome."""
    specs = [_spec_of(d) for d in trades]
    dual = accounting.book_dual(specs, cost_tier=BASE_TIER,
                                financing_adjustment_usd=dict(financing_adjustments))
    out = []
    for d, col in zip(trades, dual):
        t2 = dict(d)
        t2["_gross_move_pnl"] = round(col.gross_price_pnl_usd, 10)
        t2["_price_only"] = 0.0 if dry_run else round(col.price_only_pnl_usd, 10)
        t2["_financing"] = 0.0 if dry_run else round(col.financing_adjustment_usd, 10)
        t2["_pnl"] = 0.0 if dry_run else round(col.financing_adjusted_pnl_usd, 10)
        t2["_dry_run"] = dry_run
        out.append(t2)
    return out, specs, dual


def stress_book(specs, scored_ids, fill_delay_events=None):
    """F1-FIXED stress booking via the kernel: the SAME trades re-booked at
    every tier of {1.0, 1.5, 2.0} with the tier multiplier applied to the
    BOOKED net PnL; rows pairwise distinct for a non-empty set (certified
    inside the kernel).  ``fill_delay_events`` (the frozen one-event delay)
    is carried UNBLENDED.  Returns {tier: metrics-dict} over the scored
    subset."""
    result = accounting.book_stress(specs, fill_delay_events=fill_delay_events)
    out = {}
    for tier, r in sorted(result.items()):
        rows = [net for tid, net in r.booked_rows if tid in scored_ids]
        m = dict(accounting.book_metrics(rows))
        m["cost_component_delta_vs_base_usd"] = r.cost_component_delta_vs_base_usd
        m["stress_rows_distinct_certified"] = True
        out[f"tier{tier}"] = m
    return out


# ---------- cell assembly ----------
def compute_cell(family_id, arm, data_paths, freeze_token=None,
                 macro_reader=None, timeout_minutes=None):
    """Run one arm of one family through the full V3 pipeline and return the
    cell record (gates evaluated separately by :func:`stage_a_gates`).

    ``freeze_token is None`` => DUMMY DRY-RUN (scored=false, real_pnl=false,
    every booked monetary metric is a 0.0/None placeholder per
    :func:`dry_run_sanitized`, publication refused).  A SCORED anchor cell
    additionally books the family's ``benchmark_treatment`` arm through the
    same kernel and records ``incremental_alpha`` (V3-I finding H1); the
    USD index is built runner-side from the snapshot (finding H2)."""
    if arm == BENCHMARK_ARM:
        raise ValueError(
            "BENCHMARK_TREATMENT_IS_NOT_A_SCORED_CELL: the benchmark treatment "
            "is booked inside its anchor cell, never as a cell of its own")
    fam = FAMILIES[family_id]  # KeyError for an unregistered family: fail closed
    dry_run = freeze_token is None
    if macro_reader is None:
        macro_reader = PolicyRateReader.from_data_paths(data_paths)
    out = call_family_arm(fam, arm, data_paths, macro_reader, freeze_token,
                          timeout_minutes)
    meta = out.get("meta") or {}
    clock = meta.get("decision_clock", "daily")
    if clock != "daily":
        raise DecisionRuleError("CLOCK_UNSUPPORTED",
                                f"declared decision_clock {clock!r} is not implemented; "
                                "daily-or-slower clock required, only 'daily' passes")
    decisions, adjustments, formula = validate_decisions(
        out.get("decisions"), out.get("financing_events"))
    kept, dropped = apply_session_gate(decisions)
    booked, specs, dual = book_trades(kept, adjustments, dry_run=dry_run)
    for t in booked:
        t["_fold"] = fold_of(t["entry_bar_ts"])
    scored = [t for t in booked if t["_fold"] is not None]
    pnls_fin = [0.0 if dry_run else t["_pnl"] for t in scored]
    pnls_price = [0.0 if dry_run else t["_price_only"] for t in scored]
    folds = fold_metrics([dict(t, _pnl=p) for t, p in zip(scored, pnls_fin)])
    conc = concentration([dict(t, _pnl=p) for t, p in zip(scored, pnls_fin)])
    mdd = mdd_of([p for _, p in sorted(zip(scored, pnls_fin),
                                       key=lambda sp: sp[0]["exit_bar_ts"])])
    pop = [f for f in folds if f["populated"]]
    scenarios = dropout_scenarios(scored, pnls_fin, folds)
    drop_one = {s["scenario"].split(":", 1)[1]: s["expectancy"]
                for s in scenarios if s["scenario"].startswith("drop_pair:")}
    # USD index: runner-built from the authorized snapshot (V3-I H2); the
    # family-supplied meta series is never consulted.
    usd_index, usd_source, usd_pairs = ((None, None, 0) if dry_run
                                        else usd_index_from_data_paths(data_paths))
    if usd_index is None and scored and not dry_run:
        raise DecisionRuleError(
            "USD_INDEX_SOURCE_MISSING",
            "scored run carries booked trades but data_paths supplies no H1 "
            "price source (usd_index_h1_dir / price_h1_dir / h1_dir); the "
            "frozen USD-drift gate cannot be evaluated fail-open")
    usd = usd_drift_corr([dict(t, _pnl=p) for t, p in zip(scored, pnls_fin)],
                         usd_index or {})
    if scored:
        stress = stress_book(specs, {t["decision_id"] for t in scored},
                             fill_delay_events=meta.get("fill_delay_events"))
    else:
        stress = {}
    delay_events = meta.get("fill_delay_events") or {}
    # Incremental alpha (V3-I H1): on a SCORED anchor cell the runner books
    # the family's benchmark_treatment arm through the SAME kernel and the
    # value is ALWAYS present; dry-run leaves None (no outcome may leak).
    # Non-anchor scored cells carry the meta pass-through (normally None).
    benchmark = None
    alpha = meta.get("incremental_alpha")
    if not dry_run and arm == "anchor":
        bench_out = call_family_arm(fam, BENCHMARK_ARM, data_paths,
                                    macro_reader, freeze_token, timeout_minutes)
        bench_meta = bench_out.get("meta") or {}
        if bench_meta.get("decision_clock", "daily") != "daily":
            raise DecisionRuleError("CLOCK_UNSUPPORTED",
                                    "benchmark_treatment declared a non-daily clock")
        bench_dec, bench_adj, bench_formula = validate_decisions(
            bench_out.get("decisions"), bench_out.get("financing_events"))
        bench_kept, _bench_dropped = apply_session_gate(bench_dec)
        bench_booked, _bench_specs, _bench_dual = book_trades(
            bench_kept, bench_adj, dry_run=False)
        for t in bench_booked:
            t["_fold"] = fold_of(t["entry_bar_ts"])
        bench_scored = [t for t in bench_booked if t["_fold"] is not None]
        if not bench_scored:
            raise DecisionRuleError(
                "BENCHMARK_BOOK_EMPTY",
                "benchmark_treatment produced no fold-assigned trades; the "
                "frozen incremental-alpha value could not be computed")
        bench_expectancy = round(
            math.fsum(t["_pnl"] for t in bench_scored) / len(bench_scored), 10)
        benchmark = {"n_decisions": len(bench_dec), "n_trades_kept": len(bench_kept),
                     "financing_formula": bench_formula,
                     "expectancy": bench_expectancy,
                     "proposal_id": bench_meta.get("proposal_id")}
        alpha = round(math.fsum([book_metrics(pnls_fin)["expectancy"],
                                 -bench_expectancy]), 10)
    extra = {
        "cell_id": f"{family_id}:{arm}:tier1.0",
        "family_id": family_id, "arm": arm,
        "proposal_id": meta.get("proposal_id"),
        "decision_clock": clock,
        "financing_formula": formula,
        "scored": not dry_run,
        "n_decisions": len(decisions),
        "n_trades_kept": len(kept),
        "weekend_gate_dropped": len(dropped),
        "purged_trades": sum(1 for t in booked if t["_fold"] is None),
        "folds_declared": list(FOLD_BOUNDARIES), "purge_days": PURGE_DAYS,
        "base": book_metrics(pnls_fin),          # financing-adjusted decision book
        "base_price_only": book_metrics(pnls_price),
        "folds": folds, "mdd_usd": mdd,
        "fold_positive_share": fold_positive_share(folds),
        "pair_concentration": conc,
        "drop_one_expectancy": drop_one,
        "dropout_scenarios": scenarios,
        "break_even_cost_bps": accounting.break_even_bps(
            [t["_gross_move_pnl"] for t in scored]) if scored else None,
        "usd_drift_diag": usd,
        "usd_index_source": usd_source,
        "usd_index_pairs": usd_pairs,
        "stress": stress,
        "delay_stress": {"carried_unblended": True,
                         "n_delayed_trades": len(delay_events)},
        "incremental_alpha": alpha,
        "benchmark_treatment": benchmark,
    }
    record = accounting.build_scored_record(
        dual, record_id=extra["cell_id"], cost_tier=BASE_TIER, extra=extra)
    # Dry-run placeholders: no scored metric may leave this module (V3-I H3).
    if dry_run:
        record = dry_run_sanitized(record)
    return record


# ---------- Stage-A gates (frozen; V2 set + V3 financing gate) ----------
def stage_a_gates(rec):
    """Frozen Stage-A gate set. Returns [all_pass, [failure reasons]].

    ``base`` metrics are the FINANCING-ADJUSTED book (the decision book);
    the price-only book is reported alongside and feeds the V3 financing
    gate only.  Positive raw PnL never overrides a firing gate."""
    g = []
    base = rec["base"]
    price_only = rec.get("base_price_only", base)
    if not (base["expectancy"] > MIN_EXPECTANCY):
        g.append("EXPECTANCY_NONPOSITIVE")
    # V3 financing gate: financing must not manufacture the edge.
    if base["expectancy"] > MIN_EXPECTANCY and price_only["expectancy"] <= 0:
        g.append("FINANCING_MANUFACTURES_EDGE")
    if base["pf"] is None or base["pf"] < MIN_PF:
        g.append("PF_BELOW_1.10")
    alpha = rec.get("incremental_alpha")
    if alpha is not None and not (alpha > 0):
        g.append("INCREMENTAL_ALPHA_NOT_POSITIVE")
    if rec.get("n_decisions", 0) < MIN_DECISIONS_PER_ARM:
        g.append("DECISION_FLOOR_NOT_MET")
    pop = [f for f in rec["folds"] if f["populated"]]
    if len([f for f in pop if f["expectancy"] > 0]) < MIN_POSITIVE_FOLDS:
        g.append("FEWER_THAN_2_POSITIVE_POPULATED_FOLDS")
    if any(f["pf"] is not None and f["pf"] < MIN_FOLD_PF for f in pop):
        g.append("POPULATED_FOLD_PF_BELOW_0.80")
    if rec["mdd_usd"] > MDD_CEILING_USD:
        g.append("MDD_ABOVE_FROZEN_CEILING")
    if rec["fold_positive_share"] > MAX_POS_FOLD_SHARE:
        g.append("POSITIVE_FOLD_SHARE_ABOVE_50PCT")
    if rec["pair_concentration"] and max(rec["pair_concentration"].values()) > MAX_PAIR_POS_SHARE:
        g.append("PAIR_CONCENTRATION_ABOVE_40PCT")
    if not rec["stress"]:
        g.append("STRESS_EMPTY_TRADE_SET")
    for tier in STRESS_TIERS:
        st = rec["stress"].get(f"tier{tier}")
        if st and not (st["total_pnl"] > 0 and (st["pf"] is None or st["pf"] >= STRESS_MIN_PF)):
            g.append(f"STRESS_TIER_{tier}_FAIL")
    # Frozen dropout survival over the scenario suite (V3-I M1): the 7
    # drop-one-pair exclusions + 1 drop-one-BEST-fold; survival = reduced-book
    # expectancy > 0; the cell needs >= DROPOUT_SURVIVAL_MIN survivals.
    scenarios = rec.get("dropout_scenarios")
    if not scenarios:
        # Hand-built/legacy records: derive the pair scenarios from the
        # drop-one dict (the fold scenario is then absent, not silently
        # credited as survived).
        scenarios = [{"scenario": f"drop_pair:{p}", "expectancy": v,
                      "survived": bool(v > 0)}
                     for p, v in (rec.get("drop_one_expectancy") or {}).items()]
    surv = sum(1 for s in scenarios if s["survived"])
    if surv < DROPOUT_SURVIVAL_MIN:
        g.append("DROPOUT_SURVIVAL_INSUFFICIENT")
    diag = rec["usd_drift_diag"]
    if diag["evaluated"] and abs(diag["corr"]) > USD_CORR_CEILING:
        g.append("USD_DRIFT_EXPLAINS_ANCHOR")
    return [len(g) == 0, g]


def mechanism_sanity(family_cells):
    """Cross-arm frozen rules: neighbour must support the anchor; the causal
    control must not itself be profitable-passing.  Input: {'anchor':rec,
    'neighbour':rec, 'control':rec} of ONE family (financing-adjusted base)."""
    a, n, c = family_cells["anchor"], family_cells["neighbour"], family_cells["control"]
    g = []
    if not (n["base"]["expectancy"] > NEIGHBOUR_MIN_EXPECTANCY):
        g.append("NEIGHBOUR_DOES_NOT_SUPPORT_ANCHOR")
    if c["base"]["expectancy"] > 0 and (c["base"]["pf"] is None or c["base"]["pf"] >= CONTROL_REJECT_PF):
        g.append("CONTROL_REPRODUCES_MECHANISM")
    return [len(g) == 0, g]


# ---------- per-arm wall-clock timeout (fail-closed TECHABORT) ----------
def call_family_arm(family, arm, data_paths, macro_reader, freeze_token,
                    timeout_minutes=None):
    """Invoke ``family.run_arm`` under the frozen per-arm wall clock.

    A timeout is a TECHABORT: fail closed BEFORE any scored metric exists
    (PLAN_forex_v3.md section 11).  ``timeout_minutes`` defaults to the
    frozen 60-minute resource contract; tests may pass a smaller float."""
    minutes = PER_ARM_TIMEOUT_MINUTES if timeout_minutes is None else float(timeout_minutes)
    result: dict = {}
    error: list = []

    def _target():
        try:
            result.update(family.run_arm(arm, data_paths, macro_reader, freeze_token))
        except BaseException as exc:  # noqa: BLE001 - re-raised on the main thread
            error.append(exc)

    worker = threading.Thread(target=_target, daemon=True)
    worker.start()
    worker.join(minutes * 60.0)
    if worker.is_alive():
        raise TechAbort(
            f"TECHABORT: family arm {arm!r} exceeded the {minutes:g}-minute wall clock")
    if error:
        raise error[0]
    return result


# ---------- once-only publication (freeze-token gated) ----------
def publish_cell(ledger_path, record, authorization_path, expected_freeze_token):
    """Publish exactly once per record digest through the P1 kernel publisher.

    Requires an authorization file {"freeze_token": ...} whose token equals
    the frozen W3 execution token; refuses dry-run/unreal records; flips
    ``published`` to true BEFORE digesting so the written row carries
    ``published: true`` covered by its self-verifying line digest; appends
    once-only per digest under an flock.  Returns (observed_delta,
    published_now); replay of an already-published digest is (0, 0)."""
    import json
    import os
    if not os.path.exists(authorization_path):
        raise ValueError("LAUNCH_AUTHORIZATION_MISSING")
    with open(authorization_path, "r", encoding="utf-8") as handle:
        auth = json.load(handle)
    if auth.get("freeze_token") != expected_freeze_token:
        raise ValueError("FREEZE_TOKEN_MISMATCH")
    payload = dict(record)
    payload["gates"], payload["gate_reasons"] = stage_a_gates(record)
    publisher = accounting.ScoredLedgerPublisher(ledger_path)
    return publisher.publish_scored_once(payload)
