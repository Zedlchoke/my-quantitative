"""Frozen cell runner for A5-V15-F1-ELITE-SIZE-ASYM (A8-I lane).

``run_arm(arm_id, data_root, scored=False)`` executes the frozen daily
decision loop for one arm over the frozen folds and returns a cell-result
dict shaped like the V14 scored-driver contract
(``research/control/v14_run/tools/run_v14_cell.py``) expects -- the field
names ``baseline_run.daily_returns/books/positions/portfolio_metrics``,
``scored_metrics`` (``net_return_sum``, ``expectancy_per_day``,
``max_drawdown``, ``position_pf``, ``cost_fills``, ``cost_holding_terms``,
``cost_total``, ``funding_sum``, ``price_pnl_sum``, ``remediated_kernel``),
``fold_signs`` and ``hashes.result_sha256`` are kept compatible -- plus the
family obligations: fills-vs-holding cost breakout, per-fold nets,
per-symbol PnL shares, stress tiers and the refusal-registry digest.

Frozen mechanics (authorities in the package docstring; nothing tuned):

* daily decisions at 00:00:00 UTC on every scored day of folds F0/F1/F2;
  force-flat (target book = empty, fills at that day's 00:00 open) on the
  last scored day of every fold; purge days carry no decision and no
  position (re-entry at the next fold's first scored day);
* features per ``features.py`` (MEASURED_BOUND_LAG_3D hard; amendment_1
  >10% window-hole refusals recorded per symbol-date);
* book per ``book.py`` (7/6/7 anchor/control, 5/10/5 neighbour; side gross
  0.5 per populated side; signed cap 0.30; gross <= 1.0);
* fill model: a fill occurs only when ``|delta_w| >= 0.05`` (a held target
  below the threshold carries); fill price = 00:00 UTC bar OPEN of the fill
  date (decision date D for the baseline, x1.5-fee and +2-ticks tiers;
  D+1 for the +1-day delay tier per the proposal's ``delay_arm``).  A
  refused symbol-date is EXCLUDED from that day's cross-section (proposal
  warmup ``fail_closed``: "excluded from that day's cross-section, logged,
  and weights renormalized over eligible symbols") and its decision never
  becomes a fill (amendment_1): a refused HELD symbol carries its existing
  weight unchanged for that day;
* costs charged EXACTLY ONCE per fill event:
  ``cost = |delta_w| * equity * (taker_fee_bps*1e-4*fee_multiplier
  + slippage_ticks * tick_size / fill_price)`` -- the inherited cost-once
  kernel convention (L-V14-0); a carried boundary charges exactly 0.0 and
  ``cost_holding_terms`` is asserted 0.0 by construction;
* funding: native settlement rows applied EXACTLY ONCE per holding
  interval, cashflow ``= -weight * rate * equity`` per settlement stamp in
  the interval (cost-only convention, booked separately from fill costs);
* stress tiers (p3 inherited convention, applied to booked PnL at this
  kernel layer): ``fee_x1_5`` (fee x1.5 = 7.5 bps), ``plus2ticks``
  (slippage 2 -> 4 ticks), ``delay_plus1d`` (fills +1 day).  The +1-day
  delay at the window's final edge (the terminal force-flat decision of F2
  would fill on 2026-08-22, outside the authorized window) realizes its
  exit at the LAST available 15m bar close of 2026-08-21 -- recorded as
  ``terminal_delay_clamped: true``; no data is synthesized;
* fold attribution: every PnL row belongs to the fold of the last scored
  day at or before its instant -- so a delayed exit leg landing on a purge
  day stays with the fold whose positions it closes.

``position_pf`` population: per-instant per-symbol rows
``(price_pnl + funding - cost)`` over every held/filled symbol-instant.

This module is a pure, data-injected library: nothing persists, nothing
publishes, no wall-clock field enters the result (two identical runs are
byte-identical).  The lane itself computes NO PnL on real staged data and
sets no scored flags anywhere -- ``scored`` is only recorded verbatim in
the result dict for the driver contract.
"""

from __future__ import annotations

import hashlib
import json
import math
from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from research.v15.families.elite_size_asym import arms as arms_mod
from research.v15.families.elite_size_asym import features as features_mod
from research.v15.families.elite_size_asym import loader as loader_mod
from research.v15.families.elite_size_asym.book import build_book
from research.v15.families.elite_size_asym.frozen_identity import (
    FAMILY_ID,
    FOLDS,
    GROSS_MAX,
    MIN_TRADE_DELTA,
    PURGE_DAYS,
    RECORDED_SPEC_SHA256,
    SLIPPAGE_TICKS,
    STRESS_DELAY_DAYS,
    STRESS_EXTRA_TICKS,
    STRESS_FEE_MULTIPLIER,
    STRESS_TIERS,
    TAKER_FEE_BPS,
    UNIVERSE,
    WEIGHT_CAP_SIGNED,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
)
from research.v15.families.elite_size_asym.refusal_registry import RefusalRegistry

SCHEMA = "v15_f1_cell_result_v1"
EQUITY = 1.0
_GROSS_TOL = 1e-12


class SpecViolation(RuntimeError):
    """A frozen invariant was violated at runtime (fail closed)."""


# --------------------------------------------------------------------------- #
# Calendar / stamps
# --------------------------------------------------------------------------- #
def parse_iso_date(raw: str) -> date:
    return date.fromisoformat(str(raw))


def date_ns(day: date) -> int:
    """Epoch-ns of the day's 00:00:00 UTC instant."""
    return (
        int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp())
        * 1_000_000_000
    )


def ns_to_date(ns: int) -> date:
    return datetime.fromtimestamp(int(ns) / 1_000_000_000, tz=timezone.utc).date()


def ns_to_iso_utc(ns: int) -> str:
    return datetime.fromtimestamp(int(ns) / 1_000_000_000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def scored_days() -> List[date]:
    """Every scored decision day: folds concatenated; purge days excluded."""
    days: List[date] = []
    for fold in FOLDS:
        start = parse_iso_date(fold["start"])
        end = parse_iso_date(fold["end"])
        cursor = start
        while cursor <= end:
            days.append(cursor)
            cursor += timedelta(days=1)
    return days


def fold_end_days() -> List[date]:
    """The force-flat days: the last scored day of every fold."""
    return [parse_iso_date(fold["end"]) for fold in FOLDS]


def fold_index_for_day(day: date, sorted_scored: Sequence[date]) -> int:
    """Fold of the last scored day at or before ``day`` (purge days and
    delayed exit legs stay with the fold whose exposure they close)."""
    if not sorted_scored:
        raise SpecViolation("empty scored calendar")
    index = bisect_right(sorted_scored, day) - 1
    if index < 0:
        raise SpecViolation(f"day {day.isoformat()} precedes the scored window")
    nearest = sorted_scored[index]
    for idx, fold in enumerate(FOLDS):
        if parse_iso_date(fold["start"]) <= nearest <= parse_iso_date(fold["end"]):
            return idx
    raise SpecViolation(f"scored day {nearest.isoformat()} outside every fold")


# --------------------------------------------------------------------------- #
# Cost kernel (cost-once; inherited convention)
# --------------------------------------------------------------------------- #
def fill_cost(
    *,
    delta_w: float,
    fill_price: float,
    tick_size: float,
    fee_multiplier: float = 1.0,
    slippage_ticks: int = SLIPPAGE_TICKS,
) -> float:
    """Charge for ONE fill event (charged exactly once per fill)."""
    if fill_price <= 0.0 or tick_size <= 0.0:
        raise SpecViolation("fill price and tick size must be positive")
    rate = (
        TAKER_FEE_BPS * 1e-4 * float(fee_multiplier)
        + int(slippage_ticks) * float(tick_size) / float(fill_price)
    )
    return abs(float(delta_w)) * EQUITY * rate


# --------------------------------------------------------------------------- #
# Decision computation (features + refusals + target book)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DayDecision:
    decision_date: date
    force_flat: bool
    signals: Dict[str, float]
    target: Dict[str, float]
    refused: frozenset = field(default_factory=frozenset)


def _daily_values_for_symbol(
    spec: arms_mod.ArmSpec,
    cells: Mapping[date, loader_mod.MetricCell],
    decision_date: date,
) -> Dict[date, Optional[float]]:
    values: Dict[date, Optional[float]] = {}
    for day in features_mod.window_days(decision_date, spec.window_lookback_days):
        cell = cells.get(day)
        if cell is None or not cell.ok:
            values[day] = None
        elif spec.feature == "asym":
            values[day] = features_mod.s_daily(
                float(cell.sum_ratio_00), float(cell.count_ratio_00)
            )
        elif spec.feature == "level":
            values[day] = features_mod.c_daily(float(cell.count_ratio_00))
        else:
            raise SpecViolation(f"unknown frozen feature {spec.feature!r}")
    return values


def compute_day_decision(
    spec: arms_mod.ArmSpec,
    metrics_cells: Mapping[str, Mapping[date, loader_mod.MetricCell]],
    decision_date: date,
    force_flat: bool,
    registry: RefusalRegistry,
) -> DayDecision:
    """One decision date: features, hole refusals, frozen target book."""
    if force_flat:
        return DayDecision(
            decision_date=decision_date,
            force_flat=True,
            signals={},
            target={},
            refused=frozenset(),
        )
    signals: Dict[str, float] = {}
    refused: List[str] = []
    for symbol in UNIVERSE:
        values = _daily_values_for_symbol(
            spec, metrics_cells[symbol], decision_date
        )
        outcome = features_mod.feature_outcome(
            decision_date=decision_date,
            lookback_days=spec.window_lookback_days,
            daily_values=values,
        )
        if outcome.refused:
            refused.append(symbol)
            registry.record_window_hole(
                decision_date.isoformat(), symbol, outcome.refusal_reason or ""
            )
            continue
        signals[symbol] = float(outcome.signal)
    target = build_book(signals=signals, book_spec=spec.book_spec)
    return DayDecision(
        decision_date=decision_date,
        force_flat=False,
        signals=dict(sorted(signals.items())),
        target=target,
        refused=frozenset(refused),
    )


# --------------------------------------------------------------------------- #
# Simulation kernel (one stress parameterization of the frozen loop)
# --------------------------------------------------------------------------- #
def _simulate(
    spec: arms_mod.ArmSpec,
    snapshot: Mapping[str, Mapping[str, Any]],
    tick_sizes: Mapping[str, float],
    *,
    decisions: Mapping[date, DayDecision],
    sorted_scored: Sequence[date],
    registry_summary: Mapping[str, Any],
    fee_multiplier: float,
    slippage_ticks: int,
    delay_days: int,
) -> Dict[str, Any]:
    klines = snapshot["klines"]
    funding = snapshot["funding"]

    window_end = parse_iso_date(WINDOW_END_ISO)
    days = [day for day in sorted_scored]
    force_flat_set = set(fold_end_days())

    # --- fill instants (the delay tier shifts every fill +delay_days) ----- #
    def fill_instant(decision_day: date) -> Tuple[int, bool]:
        target_day = decision_day + timedelta(days=delay_days)
        if target_day <= window_end:
            return date_ns(target_day), False
        # Window-edge realization of the frozen +1 delay (terminal
        # force-flat only): the last available 15m bar close inside the
        # authorized window; no data synthesized.
        return int(klines[UNIVERSE[0]].last_bar_close_ns), True

    instant_to_days: Dict[int, List[date]] = {}
    timeline_set: set = {date_ns(day) for day in days}
    terminal_clamped = False
    for decision_day in days:
        instant, clamped = fill_instant(decision_day)
        terminal_clamped |= clamped
        timeline_set.add(instant)
        instant_to_days.setdefault(instant, []).append(decision_day)
    timeline = sorted(timeline_set)

    # --- mark / settlement accessors (fail-closed) ------------------------ #
    def mark(symbol: str, instant_ns: int) -> float:
        bars = klines[symbol]
        if instant_ns == int(bars.last_bar_close_ns):
            return float(bars.last_bar_close_price)
        opens = bars.opens
        day = ns_to_date(instant_ns)
        if day not in opens:
            raise loader_mod.FailClosed(
                f"{symbol}: no 15m kline open for required mark date "
                f"{day.isoformat()}"
            )
        return float(opens[day])

    stamps_by_symbol: Dict[str, List[int]] = {
        symbol: [int(ms) * 1_000_000 for ms, _rate in funding[symbol]]
        for symbol in UNIVERSE
    }

    def settlement_rates(symbol: str, start_ns: int, end_ns: int) -> List[float]:
        rows = funding[symbol]
        stamps = stamps_by_symbol[symbol]
        lo = bisect_right(stamps, start_ns)
        hi = bisect_right(stamps, end_ns)
        return [float(rows[i][1]) for i in range(lo, hi)]

    # --- walk the timeline ------------------------------------------------- #
    current: Dict[str, float] = {}
    fills: List[Dict[str, Any]] = []
    decision_rows: List[Dict[str, Any]] = []
    book_rows: List[Dict[str, Any]] = []
    daily_rows: List[Dict[str, Any]] = []
    pf_rows: List[Tuple[float, float, float]] = []  # (price, funding, cost)
    per_symbol_totals: Dict[str, float] = {sym: 0.0 for sym in UNIVERSE}

    cost_fills_total = 0.0
    price_pnl_total = 0.0
    funding_total = 0.0
    prev_ns: Optional[int] = None

    for instant in timeline:
        held = sorted(sym for sym, w in current.items() if w != 0.0)
        price_by_sym: Dict[str, float] = {}
        funding_by_sym: Dict[str, float] = {}
        interval_price = 0.0
        interval_funding = 0.0
        if prev_ns is not None:
            for symbol in held:
                p0 = mark(symbol, prev_ns)
                p1 = mark(symbol, instant)
                sym_price = current[symbol] * (p1 / p0 - 1.0)
                rates = settlement_rates(symbol, prev_ns, instant)
                sym_funding = math.fsum(
                    -current[symbol] * rate * EQUITY for rate in rates
                )
                price_by_sym[symbol] = sym_price
                funding_by_sym[symbol] = sym_funding
                interval_price += sym_price
                interval_funding += sym_funding
        # --- fills at this instant (charged exactly once per fill) -------- #
        cost_by_sym: Dict[str, float] = {}
        charged_here = 0.0
        for decision_day in sorted(instant_to_days.get(instant, [])):
            decision = decisions[decision_day]
            desired: Dict[str, float] = dict(decision.target)
            for symbol in UNIVERSE:
                if symbol in desired:
                    continue
                if (
                    current.get(symbol, 0.0) != 0.0
                    and symbol in decision.refused
                ):
                    # Refused HELD symbol: excluded from today's cross-
                    # section, its decision never becomes a fill -> carry.
                    desired[symbol] = current[symbol]
            effective: Dict[str, float] = {}
            for symbol in sorted(set(current) | set(desired)):
                target_w = float(desired.get(symbol, 0.0))
                current_w = float(current.get(symbol, 0.0))
                if abs(target_w - current_w) < MIN_TRADE_DELTA:
                    effective[symbol] = current_w
                else:
                    effective[symbol] = target_w
            if any(
                abs(w) > WEIGHT_CAP_SIGNED + _GROSS_TOL for w in effective.values()
            ):
                raise SpecViolation("signed weight cap breached in transition")
            if sum(abs(w) for w in effective.values()) > GROSS_MAX + _GROSS_TOL:
                raise SpecViolation("gross cap breached in transition")
            n_fills_before = len(fills)
            for symbol in sorted(effective):
                target_w = effective[symbol]
                current_w = float(current.get(symbol, 0.0))
                delta = target_w - current_w
                if delta == 0.0:
                    continue
                fill_price = mark(symbol, instant)
                cost = fill_cost(
                    delta_w=delta,
                    fill_price=fill_price,
                    tick_size=float(tick_sizes[symbol]),
                    fee_multiplier=fee_multiplier,
                    slippage_ticks=slippage_ticks,
                )
                cost_by_sym[symbol] = cost_by_sym.get(symbol, 0.0) + cost
                charged_here += cost
                cost_fills_total += cost
                fills.append(
                    {
                        "symbol": symbol,
                        "decision_ns": date_ns(decision_day),
                        "decision_date": decision_day.isoformat(),
                        "entry_ns": int(instant),
                        "delta_w": delta,
                        "weight_after": target_w,
                        "price": fill_price,
                        "cost": cost,
                        "force_flat": bool(decision.force_flat),
                    }
                )
                current[symbol] = target_w
            decision_rows.extend(
                {
                    "symbol": symbol,
                    "decision_ts": date_ns(decision_day),
                    "decision_date": decision_day.isoformat(),
                }
                for symbol, weight in sorted(decision.target.items())
                if weight != 0.0
            )
            book_rows.append(
                {
                    "decision_ns": date_ns(decision_day),
                    "decision_date": decision_day.isoformat(),
                    "weights": [
                        [sym, float(w)]
                        for sym, w in sorted(current.items())
                        if w != 0.0
                    ],
                    "carried_forward": len(fills) == n_fills_before,
                }
            )
        # --- per-symbol PnL rows (the position_pf population) ------------- #
        for symbol in sorted(set(price_by_sym) | set(cost_by_sym)):
            sym_price = price_by_sym.get(symbol, 0.0)
            sym_funding = funding_by_sym.get(symbol, 0.0)
            sym_cost = cost_by_sym.get(symbol, 0.0)
            pf_rows.append((sym_price, sym_funding, sym_cost))
            per_symbol_totals[symbol] += sym_price + sym_funding - sym_cost
        interval_net = interval_price + interval_funding - charged_here
        daily_rows.append(
            {
                "decision_ns": int(instant),
                "instant_iso": ns_to_iso_utc(instant),
                "fold_index": fold_index_for_day(ns_to_date(instant), sorted_scored),
                "net_return_per_unit": interval_net,
                "cost_charged_per_unit": charged_here,
                "price_pnl_per_unit": interval_price,
                "funding_per_unit": interval_funding,
            }
        )
        price_pnl_total += interval_price
        funding_total += interval_funding
        prev_ns = instant
        current = {sym: w for sym, w in current.items() if w != 0.0}

    net_total = price_pnl_total + funding_total - cost_fills_total
    run: Dict[str, Any] = {
        "daily_returns": daily_rows,
        "books": book_rows,
        "positions": fills,
        "decisions": decision_rows,
        "fills": [
            {
                "symbol": entry["symbol"],
                "ts_ns": entry["entry_ns"],
                "decision_date": entry["decision_date"],
                "cost": entry["cost"],
                "delta_w": entry["delta_w"],
            }
            for entry in fills
        ],
        "portfolio_metrics": {
            "net_return_sum": net_total,
            "expectancy_per_day": (
                net_total / len(daily_rows) if daily_rows else 0.0
            ),
            "max_drawdown": _max_drawdown(
                [row["net_return_per_unit"] for row in daily_rows]
            ),
            "position_pf": _profit_factor(pf_rows),
            "n_days_with_records": len(daily_rows),
            "price_pnl_sum": price_pnl_total,
            "funding_sum": funding_total,
            "cost_charged_sum": cost_fills_total,
            "gross_max_observed": _max_gross(book_rows),
        },
        "cost_breakout": _cost_breakout(daily_rows, book_rows, cost_fills_total),
        "per_symbol_totals": dict(sorted(per_symbol_totals.items())),
        "refusal_registry": dict(registry_summary),
        "stress": {
            "fee_multiplier": float(fee_multiplier),
            "slippage_ticks": int(slippage_ticks),
            "delay_days": int(delay_days),
            "terminal_delay_clamped": bool(terminal_clamped),
        },
        "hashes": {},
    }
    run["hashes"] = {"result_sha256": _payload_sha256(run)}
    return run


def _max_drawdown(daily_nets: Sequence[float]) -> float:
    """Max peak-to-trough drawdown of the cumulative per-unit daily net."""
    cumulative = 0.0
    peak = 0.0
    mdd = 0.0
    for value in daily_nets:
        cumulative += float(value)
        peak = max(peak, cumulative)
        mdd = max(mdd, peak - cumulative)
    return mdd


def _profit_factor(pf_rows: Sequence[Tuple[float, float, float]]) -> float:
    """PF over the per-symbol-per-instant position rows; 0.0 when the book
    never gains, and a finite JSON-safe sentinel when it never loses."""
    nets = [price + funding - cost for price, funding, cost in pf_rows]
    gains = math.fsum(v for v in nets if v > 0.0)
    losses = abs(math.fsum(v for v in nets if v < 0.0))
    if losses > 0.0:
        return gains / losses
    if gains > 0.0:
        return 1e12
    return 0.0


def _max_gross(book_rows: Sequence[Mapping[str, Any]]) -> float:
    return max(
        (sum(abs(float(w)) for _, w in row["weights"]) for row in book_rows),
        default=0.0,
    )


def _cost_breakout(
    daily_rows: Sequence[Mapping[str, Any]],
    book_rows: Sequence[Mapping[str, Any]],
    cost_total: float,
) -> Dict[str, Any]:
    """Cost split FILLS vs HOLDING (L-V14-0): a carried book has an
    identical prior/target and charges exactly 0.0, so ``cost_holding_terms``
    must be 0.0 by construction."""
    carried = {
        int(row["decision_ns"]) for row in book_rows if bool(row["carried_forward"])
    }
    fills_cost = 0.0
    holding_cost = 0.0
    for row in daily_rows:
        if int(row["decision_ns"]) in carried:
            holding_cost += float(row["cost_charged_per_unit"])
        else:
            fills_cost += float(row["cost_charged_per_unit"])
    holding_cost = round(holding_cost, 12)
    return {
        "cost_fills": round(fills_cost, 12),
        "cost_holding_terms": holding_cost,
        "cost_total": round(cost_total, 12),
        "holding_terms_zero_by_construction": holding_cost == 0.0,
        "carried_boundaries": len(carried),
        "transition_boundaries": len(book_rows) - len(carried),
    }


def _payload_sha256(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# run_arm: the frozen cell entry point
# --------------------------------------------------------------------------- #
_TIER_PARAMS: Dict[str, Tuple[float, int, int]] = {
    "baseline": (1.0, SLIPPAGE_TICKS, 0),
    "fee_x1_5": (STRESS_FEE_MULTIPLIER, SLIPPAGE_TICKS, 0),
    "plus2ticks": (1.0, SLIPPAGE_TICKS + STRESS_EXTRA_TICKS, 0),
    "delay_plus1d": (1.0, SLIPPAGE_TICKS, STRESS_DELAY_DAYS),
}


def _default_tick_sizes() -> Dict[str, float]:
    """Native tick sizes from the staged contract specs (the inherited v12
    crypto_perpetual metadata; L-V14-0 real per-instrument ticks)."""
    from research.v12.families.oilev_v2.audits import load_tick_sizes

    return {
        sym: float(tick) for sym, tick in load_tick_sizes(list(UNIVERSE)).items()
    }


_SCOPED_SNAPSHOT_CACHE: Dict[str, Dict[str, Dict[str, Any]]] = {}


def _snapshot_for(root: Path) -> Dict[str, Dict[str, Any]]:
    """Snapshot cache keyed by the resolved read-only staged root path.

    The staged root is immutable/read-only by contract (selection_freeze
    ``data_manifest_refs``), so per-path memoization is sound; mutation
    fixtures use their own fresh paths.
    """
    key = str(root.resolve())
    cached = _SCOPED_SNAPSHOT_CACHE.get(key)
    if cached is None:
        min_date = scored_days()[0] - timedelta(
            days=max(
                arms_mod.ARM_SPECS[arm].window_lookback_days
                for arm in arms_mod.ARM_SPECS
            )
        )
        cached = loader_mod.load_snapshot(root, min_date=min_date)
        _SCOPED_SNAPSHOT_CACHE[key] = cached
    return cached


def run_arm(
    arm_id: str,
    data_root: Optional[Path | str] = None,
    scored: bool = False,
    *,
    tick_sizes: Optional[Mapping[str, float]] = None,
) -> Dict[str, Any]:
    """Run one frozen arm over the frozen folds; return the cell dict.

    ``data_root`` defaults to the absolute staged root recorded in this
    package's ``staged_root.json``.  ``tick_sizes`` overrides the staged
    contract specs (the synthetic-fixture injection point).  ``scored`` is
    recorded verbatim; this runner never publishes, never writes, and
    carries no wall-clock field (byte-identical reruns).
    """
    spec = arms_mod.arm_spec(arm_id)
    root = Path(data_root) if data_root is not None else loader_mod.staged_data_root()
    if not root.is_dir():
        raise loader_mod.FailClosed(f"data_root missing: {root}")
    snapshot = _snapshot_for(root)
    if tick_sizes is not None:
        ticks = {str(sym): float(tick_sizes[sym]) for sym in UNIVERSE}
    else:
        ticks = _default_tick_sizes()
    missing_ticks = [sym for sym in UNIVERSE if sym not in ticks]
    if missing_ticks:
        raise loader_mod.FailClosed(f"tick sizes missing for: {missing_ticks}")

    # decisions + refusals are cost-independent: computed ONCE for the cell,
    # reused by every stress tier (byte-identical across tiers).
    sorted_scored = sorted(scored_days())
    force_flat_set = set(fold_end_days())
    registry = RefusalRegistry()
    decisions: Dict[date, DayDecision] = {
        day: compute_day_decision(
            spec, snapshot["metrics"], day, day in force_flat_set, registry
        )
        for day in sorted_scored
    }
    registry_summary = registry.summary()

    tier_runs: Dict[str, Dict[str, Any]] = {}
    for tier in STRESS_TIERS:
        fee_mult, slip_ticks, delay_days = _TIER_PARAMS[tier]
        tier_runs[tier] = _simulate(
            spec,
            snapshot,
            ticks,
            decisions=decisions,
            sorted_scored=sorted_scored,
            registry_summary=registry_summary,
            fee_multiplier=fee_mult,
            slippage_ticks=slip_ticks,
            delay_days=delay_days,
        )
    baseline = tier_runs["baseline"]
    metrics = baseline["portfolio_metrics"]
    if not baseline["cost_breakout"]["holding_terms_zero_by_construction"]:
        raise SpecViolation(
            "cost_holding_terms must be exactly 0 by construction "
            "(cost-once kernel); refusing to report the cell"
        )

    fold_ids = [fold["fold_id"] for fold in FOLDS]
    fold_nets = {idx: 0.0 for idx in range(len(FOLDS))}
    fold_day_counts = {idx: 0 for idx in range(len(FOLDS))}
    for row in baseline["daily_returns"]:
        idx = int(row["fold_index"])
        fold_nets[idx] = fold_nets.get(idx, 0.0) + float(row["net_return_per_unit"])
        fold_day_counts[idx] = fold_day_counts.get(idx, 0) + 1

    symbol_totals = {
        sym: float(value)
        for sym, value in baseline["per_symbol_totals"].items()
    }
    positive_totals = {
        sym: value for sym, value in symbol_totals.items() if value > 0.0
    }
    pool = math.fsum(positive_totals.values())
    shares = (
        {sym: value / pool for sym, value in sorted(positive_totals.items())}
        if pool > 0.0
        else {}
    )
    largest_positive_share = max(shares.values()) if shares else 0.0

    stress_positive = {
        tier: bool(
            tier_runs[tier]["portfolio_metrics"]["net_return_sum"] > 0.0
        )
        for tier in STRESS_TIERS
        if tier != "baseline"
    }

    scored_metrics = {
        "score_valid": all(
            math.isfinite(float(metrics[key]))
            for key in (
                "net_return_sum",
                "expectancy_per_day",
                "max_drawdown",
                "position_pf",
                "price_pnl_sum",
                "funding_sum",
                "cost_charged_sum",
            )
        ),
        "net_return_sum": metrics["net_return_sum"],
        "expectancy_per_day": metrics["expectancy_per_day"],
        "max_drawdown": metrics["max_drawdown"],
        "position_pf": metrics["position_pf"],
        "n_positions": len(baseline["positions"]),
        "n_decisions": len(baseline["decisions"]),
        "n_fills": len(baseline["fills"]),
        "decisions": baseline["decisions"],
        "fills": baseline["fills"],
        "cost_fills": baseline["cost_breakout"]["cost_fills"],
        "cost_holding_terms": baseline["cost_breakout"]["cost_holding_terms"],
        "cost_total": baseline["cost_breakout"]["cost_total"],
        "funding_sum": metrics["funding_sum"],
        "price_pnl_sum": metrics["price_pnl_sum"],
        "remediated_kernel": True,
    }

    cell: Dict[str, Any] = {
        "schema": SCHEMA,
        "family": "elite_size_asym",
        "family_id": FAMILY_ID,
        "arm_id": spec.arm_id,
        "arm_name": spec.name,
        "role": spec.role,
        "scored": bool(scored),
        "spec_pins": dict(RECORDED_SPEC_SHA256),
        "data_root": str(root),
        "universe": list(UNIVERSE),
        "scored_window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "folds": [dict(fold) for fold in FOLDS],
        "purge_days": list(PURGE_DAYS),
        "cost_model": {
            "taker_fee_bps": TAKER_FEE_BPS,
            "slippage_ticks": SLIPPAGE_TICKS,
            "weight_cap_signed": WEIGHT_CAP_SIGNED,
            "gross_max": GROSS_MAX,
            "min_trade_delta": MIN_TRADE_DELTA,
            "stress_tiers": {
                tier: {
                    "fee_multiplier": params[0],
                    "slippage_ticks": params[1],
                    "delay_days": params[2],
                }
                for tier, params in sorted(_TIER_PARAMS.items())
            },
        },
        "baseline_run": baseline,
        "stress_tiers": {
            tier: {
                "net_return_sum": tier_runs[tier]["portfolio_metrics"][
                    "net_return_sum"
                ],
                "price_pnl_sum": tier_runs[tier]["portfolio_metrics"][
                    "price_pnl_sum"
                ],
                "funding_sum": tier_runs[tier]["portfolio_metrics"]["funding_sum"],
                "cost_total": tier_runs[tier]["portfolio_metrics"][
                    "cost_charged_sum"
                ],
                "n_fills": len(tier_runs[tier]["positions"]),
                "terminal_delay_clamped": tier_runs[tier]["stress"][
                    "terminal_delay_clamped"
                ],
                "positive": stress_positive.get(tier),
                "hashes": tier_runs[tier]["hashes"],
            }
            for tier in STRESS_TIERS
        },
        "scored_metrics": scored_metrics,
        "fold_signs": {
            "fold_net_sums": {
                fold_ids[idx]: round(fold_nets[idx], 12) for idx in range(len(FOLDS))
            },
            "fold_positive": [fold_nets[idx] > 0.0 for idx in range(len(FOLDS))],
            "fold_day_counts": {
                fold_ids[idx]: fold_day_counts.get(idx, 0)
                for idx in range(len(FOLDS))
            },
        },
        "fold_nets": {
            fold_ids[idx]: {
                "net": fold_nets[idx],
                "n_days": fold_day_counts.get(idx, 0),
            }
            for idx in range(len(FOLDS))
        },
        "per_symbol_pnl": {
            "totals": dict(sorted(symbol_totals.items())),
            "positive_shares": dict(sorted(shares.items())),
            "largest_positive_share": largest_positive_share,
        },
        "refusal_registry": baseline["refusal_registry"],
        "hashes": {},
    }
    cell["hashes"] = {"result_sha256": _payload_sha256(cell)}
    return cell


__all__ = [
    "SCHEMA",
    "SpecViolation",
    "compute_day_decision",
    "fill_cost",
    "fold_end_days",
    "fold_index_for_day",
    "run_arm",
    "scored_days",
]
