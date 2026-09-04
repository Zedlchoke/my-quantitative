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

``arm``            one of the family's three frozen arms: "anchor",
                   "neighbour", "causal_negative_control" (the driver also
                   accepts the shorthand "control").
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
                      ``usd_index_daily_returns`` ({YYYY-MM-DD: equal-weight
                      USD-index daily return} for the frozen D1 diagnostic),
                      ``fill_delay_events`` ({decision_id: delayed-fill
                      count} for the frozen one-event-delay stress, carried
                      UNBLENDED), ``incremental_alpha`` (float vs the frozen
                      benchmark treatment).

Runner-side enforcement (fail closed, codes on ``DecisionRuleError``):
DECISION_CLOCK_VIOLATION (decision/fill instants not 16:00-NY daily bars),
ONE_EVENT_LAG_VIOLATION (same-bar fill or fill lag > 4 days),
FOLD_FORCE_FLAT_VIOLATION (a trade spans an internal fold boundary),
MISSING_FINANCING_EVENT / FINANCING_EVENT_UNMATCHED / MISSING_FINANCING_FORMULA
/ FINANCING_FORMULA_INCONSISTENT, DUPLICATE_DECISION_ID, CLOCK_UNSUPPORTED.
Weekend entries are dropped fail-closed by the inherited session gate.
"""
import math
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
DROPOUT_SURVIVAL_MIN = 5        # of 7 single-pair exclusions
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


def usd_drift_corr(trades, usd_index_daily_returns):
    """Frozen inherited D1 diagnostic: Pearson corr between daily aggregate
    trade pnl and the equal-weight USD-index daily return (frozen D1 formula,
    supplied by the family as meta.usd_index_daily_returns).  Evaluates only
    over >= USD_DIAG_MIN_DAYS days with trades; otherwise it cannot fail."""
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
    book columns are 0.0 placeholders, publication refused)."""
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
    drop_one = {}
    for excl in PAIRS:
        sub = [p for t, p in zip(scored, pnls_fin) if t["pair"] != excl]
        drop_one[excl] = round(sum(sub) / len(sub), 10) if sub else 0.0
    usd = usd_drift_corr([dict(t, _pnl=p) for t, p in zip(scored, pnls_fin)],
                         meta.get("usd_index_daily_returns") or {})
    if scored:
        stress = stress_book(specs, {t["decision_id"] for t in scored},
                             fill_delay_events=meta.get("fill_delay_events"))
    else:
        stress = {}
    delay_events = meta.get("fill_delay_events") or {}
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
        "break_even_cost_bps": accounting.break_even_bps(
            [t["_gross_move_pnl"] for t in scored]) if scored else None,
        "usd_drift_diag": usd,
        "stress": stress,
        "delay_stress": {"carried_unblended": True,
                         "n_delayed_trades": len(delay_events)},
        "incremental_alpha": meta.get("incremental_alpha"),
    }
    record = accounting.build_scored_record(
        dual, record_id=extra["cell_id"], cost_tier=BASE_TIER, extra=extra)
    # Dry-run placeholders: no scored metric may leave this module.
    if dry_run:
        for key in ("gross_price_pnl_usd", "price_only_pnl_usd",
                    "financing_adjustment_usd", "financing_adjusted_pnl_usd"):
            record[key] = 0.0
        record["dry_run"] = True
        record["real_pnl"] = False
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
    surv = sum(1 for v in rec["drop_one_expectancy"].values() if v > 0)
    if surv < DROPOUT_SURVIVAL_MIN:
        g.append("DROP_ONE_PAIR_SURVIVAL_INSUFFICIENT")
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
