"""Frozen runner for TAKER-SAT: ``run_arm(arm_id, data_root, scored)``.

Executes one frozen arm end-to-end on the 15m grid: frozen schedule (5-day
per-fold decisions + purge force-flats), the cross-sectional extreme-fade
book, next-allowed-fill execution at staged 00:00 UTC bar opens, funding
applied once per settlement stamp, costs charged EXACTLY ONCE per fill, and
the V14-driver-compatible cell dict (the ``run_v14_cell.py`` field
contract: ``scored_metrics`` with cost broken out fills-vs-holding,
per-fold nets, per-symbol PnL shares, MDD, position PF, expectancy, refusal
registry digest).

DISCIPLINE (implementation lane): ``scored`` is RECORDED VERBATIM in the
cell payload -- the family package takes no position on authorization.
Guarding unauthorized scored execution lives at the DRIVER layer (the
owner-gated ``--publish`` / ``--expect-head`` / exactly-once ledger chain,
the V14 ``run_v14_cell.py`` architecture, matched by the elite_size_asym
family); an in-family unconditional guard would sit at the wrong layer and
TECHABORT every legitimate scored invocation.  Remediation A1-ordered
pre-score (driver-owned guard; V14-aligned); budget still 0/6.  Tests and
dry runs invoke with ``scored=False``.  The runner is a pure, data-injected
library over a staged parquet root
(``<root>/{metrics,klines,funding}/<SYM>.parquet``); tests drive it
exclusively on HAND-COMPUTED synthetic roots.  Nothing here persists
artifacts or touches a scored ledger.

STRESS TIER (V12 selection freeze via the proposal): base = fee x1.0,
1 native tick slippage, no delay; stress = fee x1.5 (7.5 bps), +2 ticks
(3 total) and a +1-day execution delay -- decision-date fills move to the
next day's 00:00 UTC open.  The force-flat exits stay AT the fold boundary
in every tier: "force-flat fold boundaries" is a binding constraint of the
fold contract, so a delayed exit that would hold a position past the fold
cannot be the intended reading (and the final delayed bar 2026-08-22 00:00
is outside the staged klines, which end with 2026-08-21 -- fail-closed
either way).  Recorded as a resolved tension in the lane handoff.

Fail-closed everywhere: malformed staged inputs raise; a refused decision
never becomes a fill; missing bars raise (never a far substitute beyond the
same UTC day); funding beyond the documented |rate| <= 0.0375 cap raises.
"""

from __future__ import annotations

import hashlib
import json
import math
from bisect import bisect_left
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import ContractViolation
from research.v15.families.taker_sat import arms
from research.v15.families.taker_sat import book as book_mod
from research.v15.families.taker_sat import features
from research.v15.families.taker_sat.features import StagedDataError
from research.v15.families.taker_sat.frozen_identity import (
    ARM_IDS,
    BASE_SLIP_TICKS,
    FAMILY_ID,
    FOLDS,
    FUNDING_RATE_ABS_CAP,
    STRESS_DELAY_DAYS,
    STRESS_FEE_MULTIPLIER,
    STRESS_SLIP_TICKS,
    TAKER_FEE_BPS,
    UNIVERSE,
    verify_pinned_authorities,
)
from research.v15.families.taker_sat.refusal_registry import RefusalRegistry

DAY_MS = 86_400_000
BAR_MS = 900_000  # 15m klines

SCHEMA_VERSION = "v15i.taker_sat.cell.v1"

#: Recorded verbatim in every cell payload (A1-ordered pre-score remediation:
#: the scored guard is DRIVER-owned -- --publish/--expect-head + ledger chain
#: -- never an in-family refusal; V14-aligned, elite_size_asym pattern).
SCORED_FLAG_SEMANTICS = (
    "scored flag recorded verbatim; unauthorized scored execution is "
    "refused at the driver layer (--publish/--expect-head + exactly-once "
    "ledger chain), never inside the family package"
)

COST_TIERS: dict[str, dict[str, float]] = {
    "base": {
        "fee_multiplier": 1.0,
        "slip_ticks": float(BASE_SLIP_TICKS),
        "delay_days": 0.0,
    },
    "stress": {
        "fee_multiplier": float(STRESS_FEE_MULTIPLIER),
        "slip_ticks": float(STRESS_SLIP_TICKS),
        "delay_days": float(STRESS_DELAY_DAYS),
    },
}


# --------------------------------------------------------------------------- #
# Staged bundle loaders (read-only; fail closed)
# --------------------------------------------------------------------------- #
def _load_klines(data_root: Path, universe: Sequence[str]) -> dict[str, dict]:
    """Per-symbol 15m bars (FILL PRICES ONLY): sorted unique 15m-grid opens."""
    import pandas as pd

    out: dict[str, dict[str, Any]] = {}
    for sym in sorted(str(s) for s in universe):
        path = data_root / "klines" / f"{sym}.parquet"
        if not path.is_file():
            raise StagedDataError(f"{sym}: klines parquet missing: {path}")
        frame = pd.read_parquet(path)
        for column in ("open_time_ms", "open"):
            if column not in frame.columns:
                raise StagedDataError(f"{sym}: klines column missing: {column}")
        frame = frame.sort_values("open_time_ms", kind="mergesort")
        times = [int(v) for v in frame["open_time_ms"]]
        opens = [float(v) for v in frame["open"]]
        if len(set(times)) != len(times):
            raise StagedDataError(f"{sym}: duplicate kline open_time_ms")
        for t in times:
            if t % BAR_MS != 0:
                raise StagedDataError(f"{sym}: kline stamp {t} off the 15m grid")
        for price in opens:
            if not (math.isfinite(price) and price > 0.0):
                raise StagedDataError(f"{sym}: non-positive kline open {price!r}")
        out[sym] = {"times_ms": times, "opens": opens}
    return out


def _load_funding(data_root: Path, universe: Sequence[str]) -> dict[str, list]:
    """Per-symbol settlement stamps (COST ONLY), capped at |rate| <= 0.0375."""
    import pandas as pd

    out: dict[str, list[tuple[int, float]]] = {}
    for sym in sorted(str(s) for s in universe):
        path = data_root / "funding" / f"{sym}.parquet"
        if not path.is_file():
            raise StagedDataError(f"{sym}: funding parquet missing: {path}")
        frame = pd.read_parquet(path)
        for column in ("funding_time_ms", "funding_rate"):
            if column not in frame.columns:
                raise StagedDataError(f"{sym}: funding column missing: {column}")
        frame = frame.sort_values("funding_time_ms", kind="mergesort")
        rows: list[tuple[int, float]] = []
        last: Optional[int] = None
        for ts_ms, rate in zip(frame["funding_time_ms"], frame["funding_rate"]):
            stamp = int(ts_ms)
            value = float(rate)
            if last is not None and stamp <= last:
                raise StagedDataError(f"{sym}: duplicate/unsorted funding stamps")
            last = stamp
            if not math.isfinite(value) or abs(value) > FUNDING_RATE_ABS_CAP:
                raise StagedDataError(
                    f"{sym}: funding rate {value!r} outside the documented "
                    f"|rate| <= {FUNDING_RATE_ABS_CAP} cap (fail-closed)"
                )
            rows.append((stamp, value))
        out[sym] = rows
    return out


def _load_tick_sizes(
    universe: Sequence[str], tick_sizes: Optional[Mapping[str, float]]
) -> dict[str, float]:
    """Native per-symbol ticks: explicit map (synthetic) or the frozen V12
    ``crypto_perpetual`` metadata loader (real runs; never a uniform stub)."""
    if tick_sizes is not None:
        return {str(k): float(v) for k, v in dict(tick_sizes).items()}
    from research.v12.families.oilev_v2.audits import load_tick_sizes as _v12_ticks

    return dict(_v12_ticks(list(universe)))


def _fill_price(bars: Mapping[str, Any], sym: str, fill_ns: int) -> float:
    """Next-allowed-fill: OPEN of the first 15m bar at/after the fill instant.

    Missing 00:00 slots shift to the next same-UTC-day bar open (never a
    far substitute); no bar on that day fails closed -- never synthesized.
    """
    ms = int(fill_ns) // 1_000_000
    times = bars[sym]["times_ms"]
    idx = bisect_left(times, ms)
    if idx >= len(times):
        raise StagedDataError(
            f"{sym}: no kline bar at/after the fill instant (fail-closed)"
        )
    bar_ms = times[idx]
    if bar_ms >= ms + DAY_MS:
        raise StagedDataError(
            f"{sym}: no kline bar on the fill day within the UTC day "
            "(next-allowed-fill refused to substitute across days)"
        )
    return float(bars[sym]["opens"][idx])


def _funding_sum(
    funding_rows: Sequence[tuple[int, float]], lo_ms: int, hi_ms: int
) -> float:
    """Sum of settlement rates in the half-open ``[lo_ms, hi_ms)`` window.

    Half-open chaining attributes each settlement stamp to EXACTLY ONE held
    interval (a stamp at an exit/re-entry boundary belongs to the position
    opened there) -- funding is applied once per stamp, never double-counted.
    """
    lo_idx = bisect_left(funding_rows, (int(lo_ms), float("-inf")))
    hi_idx = bisect_left(funding_rows, (int(hi_ms), float("-inf")))
    return math.fsum(r for _t, r in funding_rows[lo_idx:hi_idx])


def _canonical(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _iso(ns: int) -> str:
    from research.v11.families.oilever_delev.strategy import iso_utc

    return iso_utc(int(ns))


# --------------------------------------------------------------------------- #
# run_arm
# --------------------------------------------------------------------------- #
def run_arm(
    arm_id: str,
    data_root,
    scored: bool = False,
    *,
    stress_tier: str = "base",
    tick_sizes: Optional[Mapping[str, float]] = None,
    universe: Optional[Sequence[str]] = None,
    folds: Optional[Sequence[tuple[str, str, str]]] = None,
) -> dict[str, Any]:
    """Run one frozen arm over the staged root; return the driver cell dict.

    ``scored`` is recorded VERBATIM in the cell payload (A1-ordered pre-score
    remediation: the guard against unauthorized scored execution is
    DRIVER-owned -- ``--publish``/``--expect-head`` + exactly-once ledger
    chain -- never an in-family refusal; V14-aligned).  Tests and dry runs
    invoke with ``scored=False``.  ``folds`` defaults to the frozen F0/F1/F2
    calendar; the explicit override exists for synthetic fixtures and must
    satisfy the same structural invariants.
    """
    arm_id = str(arm_id)
    if arm_id not in ARM_IDS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    scored = bool(scored)
    spec = arms.arm_spec(arm_id)
    authority_report = verify_pinned_authorities()
    universe_symbols = tuple(sorted(str(s) for s in (universe or UNIVERSE)))
    tier = dict(COST_TIERS.get(str(stress_tier), {}))
    if not tier:
        raise ContractViolation(
            f"unknown stress tier {stress_tier!r}; expected {sorted(COST_TIERS)}"
        )
    fee_multiplier = float(tier["fee_multiplier"])
    slip_ticks = int(tier["slip_ticks"])
    delay_days = int(tier["delay_days"])

    root = Path(data_root)
    daily, defects = features.load_metrics_daily(root, universe_symbols)
    bars = _load_klines(root, universe_symbols)
    funding = _load_funding(root, universe_symbols)
    ticks = _load_tick_sizes(universe_symbols, tick_sizes)
    missing_ticks = [s for s in universe_symbols if float(ticks.get(s, 0.0)) <= 0.0]
    if missing_ticks:
        raise StagedDataError(f"native tick sizes missing for {missing_ticks}")

    boundaries = book_mod.schedule(FOLDS if folds is None else folds)
    force_flat_ns_by_fold = {
        b["fold_label"]: int(b["instant_ns"])
        for b in boundaries
        if b["kind"] == "force_flat"
    }
    fill_ns_of: list[int] = []
    for boundary in boundaries:
        fill_ns = int(boundary["instant_ns"]) + delay_days * book_mod.DAY_NS
        if boundary["kind"] == "decision":
            flat_ns = force_flat_ns_by_fold[boundary["fold_label"]]
            if fill_ns >= flat_ns:
                raise ContractViolation(
                    "delayed decision fill would land at/after the fold "
                    f"force-flat instant ({boundary['fold_label']}); the fold "
                    "contract is binding (fail-closed schedule)"
                )
        fill_ns_of.append(fill_ns)
    for earlier, later in zip(fill_ns_of, fill_ns_of[1:]):
        if later <= earlier:
            raise ContractViolation("fill instants are not strictly increasing")

    refusals = RefusalRegistry()
    prev_weights: dict[str, float] = {}
    boundaries_out: list[dict[str, Any]] = []
    decision_records: list[dict[str, Any]] = []
    fill_records: list[dict[str, Any]] = []
    open_spans: dict[str, dict[str, Any]] = {}
    closed_spans: list[dict[str, Any]] = []
    held_spans_by_boundary: list[dict[str, dict[str, Any]]] = []
    boundary_prices: list[dict[str, float]] = []
    boundary_costs: list[dict[str, float]] = []
    price_cache: dict[tuple[str, int], float] = {}

    def price_at(sym: str, fill_ns: int) -> float:
        key = (sym, int(fill_ns))
        if key not in price_cache:
            price_cache[key] = _fill_price(bars, sym, int(fill_ns))
        return price_cache[key]

    def leg_rate(sym: str, price: float) -> float:
        return float(TAKER_FEE_BPS) * 1e-4 * fee_multiplier + slip_ticks * float(
            ticks[sym]
        ) / price

    # ---- pass 1: targets, fills, costs, span lifecycle ---- #
    for boundary, fill_ns in zip(boundaries, fill_ns_of):
        if boundary["kind"] == "force_flat":
            target: dict[str, float] = {}
            target_book: Optional[dict[str, Any]] = None
        else:
            scores = features.symbol_scores_at(
                arm_window_days=int(spec["window_days"]),
                arm_with_churn=bool(spec["with_churn"]),
                daily=daily,
                universe=universe_symbols,
                decision_date_ns=int(boundary["instant_ns"]),
                refusals=refusals,
            )
            target_book = book_mod.build_book(scores)
            target = {
                str(sym): float(w) for sym, w in target_book["weights"].items()
            }
            if target_book["reason_code"] == book_mod.REASON_INSUFFICIENT_AVAILABLE:
                refusals.record(
                    features.ns_to_date_str(int(boundary["instant_ns"])),
                    "",
                    book_mod.REASON_INSUFFICIENT_AVAILABLE,
                    detail={"n_available": int(target_book["n_available"])},
                )
            for sym, weight in sorted(target.items()):
                if float(weight) != 0.0:
                    decision_records.append(
                        {
                            "symbol": str(sym),
                            "decision_ts": int(boundary["instant_ns"]),
                        }
                    )
        carried = book_mod.weights_equal(prev_weights, target)
        changed = sorted(
            {
                sym
                for sym in set(prev_weights) | set(target)
                if abs(
                    float(prev_weights.get(sym, 0.0)) - float(target.get(sym, 0.0))
                )
                > 1e-15
            }
        )
        costs: dict[str, float] = {}
        for sym in changed:
            price = price_at(sym, fill_ns)
            old_w = float(prev_weights.get(sym, 0.0))
            new_w = float(target.get(sym, 0.0))
            delta = abs(new_w - old_w)
            rate = leg_rate(sym, price)
            cost = delta * rate
            costs[sym] = cost
            fill_records.append(
                {
                    "symbol": str(sym),
                    "ts_ns": int(fill_ns),
                    "weight_delta": round(new_w - old_w, 12),
                    "price": round(price, 12),
                    "cost": round(cost, 12),
                }
            )
            # cost allocation: the closing leg charges the closing span, the
            # opening leg the new span (a flip splits |dw|*rate into two
            # equal |w|*rate legs -- the total equals the transition charge).
            if abs(old_w) > 1e-15 and abs(new_w) > 1e-15 and (old_w > 0.0) != (
                new_w > 0.0
            ):
                span = open_spans.pop(sym)
                span["exit_ns"] = int(fill_ns)
                span["exit_price"] = price
                span["cost_allocated_per_unit"] += abs(old_w) * rate
                closed_spans.append(span)
                open_spans[sym] = _new_span(sym, boundary, fill_ns, price, new_w)
                open_spans[sym]["cost_allocated_per_unit"] = abs(new_w) * rate
            elif abs(old_w) > 1e-15:  # closing to flat
                span = open_spans.pop(sym)
                span["exit_ns"] = int(fill_ns)
                span["exit_price"] = price
                span["cost_allocated_per_unit"] += cost
                closed_spans.append(span)
            else:  # opening from flat
                span = _new_span(sym, boundary, fill_ns, price, new_w)
                span["cost_allocated_per_unit"] = cost
                open_spans[sym] = span
        boundary_prices.append(
            {
                sym: price_at(sym, fill_ns)
                for sym in sorted(set(prev_weights) | set(target))
            }
        )
        boundary_costs.append(costs)
        if target_book is not None:
            reason_code = str(target_book["reason_code"])
        else:
            reason_code = "FORCE_FLAT"
        boundaries_out.append(
            {
                "decision_ns": int(boundary["instant_ns"]),
                "fill_ns": int(fill_ns),
                "kind": str(boundary["kind"]),
                "fold_label": str(boundary["fold_label"]),
                "weights": [[s, float(target[s])] for s in sorted(target)],
                "carried_forward": bool(carried),
                "reason_code": reason_code,
                "cost_charged": round(math.fsum(costs.values()), 12),
            }
        )
        held_spans_by_boundary.append(
            {
                sym: open_spans[sym]
                for sym, w in target.items()
                if abs(float(w)) > 1e-15
            }
        )
        prev_weights = dict(target)

    if open_spans:
        raise ContractViolation(
            "positions remain open after the final force-flat (fail-closed)"
        )

    # ---- pass 2: realized rows over [f_i, f_{i+1}) on the held books ---- #
    realized_rows: list[dict[str, Any]] = []
    for i in range(len(boundaries_out)):
        row = {
            "decision_ns": boundaries_out[i]["fill_ns"],
            "instant_ns": boundaries_out[i]["decision_ns"],
            "instant_iso": _iso(boundaries_out[i]["fill_ns"]),
            "fold_label": boundaries_out[i]["fold_label"],
            "price_pnl_per_unit": 0.0,
            "funding_cashflow_per_unit": 0.0,
            "cost_charged_per_unit": math.fsum(boundary_costs[i].values()),
            "carried_boundary": bool(boundaries_out[i]["carried_forward"]),
        }
        if i + 1 < len(boundaries_out):
            lo_ms = boundaries_out[i]["fill_ns"] // 1_000_000
            hi_ms = boundaries_out[i + 1]["fill_ns"] // 1_000_000
            price_pnl = 0.0
            funding_cash = 0.0
            for sym, span in sorted(held_spans_by_boundary[i].items()):
                weight = float(span["signed_weight"])
                p0 = boundary_prices[i][sym]
                p1 = boundary_prices[i + 1][sym]
                leg_price_pnl = weight * (p1 - p0) / p0
                leg_funding = -weight * _funding_sum(funding[sym], lo_ms, hi_ms)
                price_pnl += leg_price_pnl
                funding_cash += leg_funding
                span["price_pnl_per_unit"] += leg_price_pnl
                span["funding_cashflow_per_unit"] += leg_funding
            row["price_pnl_per_unit"] = price_pnl
            row["funding_cashflow_per_unit"] = funding_cash
        row["net_return_per_unit"] = (
            row["price_pnl_per_unit"]
            + row["funding_cashflow_per_unit"]
            - row["cost_charged_per_unit"]
        )
        realized_rows.append(row)

    # ---- carried boundaries must charge exactly zero (cost once) ---- #
    holding_terms = math.fsum(
        r["cost_charged_per_unit"] for r in realized_rows if r["carried_boundary"]
    )
    if holding_terms != 0.0:
        raise ContractViolation(
            f"cost_holding_terms must be exactly 0 by construction, got "
            f"{holding_terms!r} (cost-once kernel)"
        )

    return _cell_payload(
        arm_id=arm_id,
        spec=spec,
        universe=universe_symbols,
        scored=scored,
        stress_tier=str(stress_tier),
        fee_multiplier=fee_multiplier,
        slip_ticks=slip_ticks,
        delay_days=delay_days,
        folds=folds if folds is not None else FOLDS,
        boundaries_out=boundaries_out,
        rows=realized_rows,
        closed_spans=closed_spans,
        decision_records=decision_records,
        fill_records=fill_records,
        refusals=refusals,
        defects=defects,
        authority_report=authority_report,
    )


def _new_span(
    sym: str, boundary: Mapping[str, Any], fill_ns: int, price: float, weight: float
) -> dict[str, Any]:
    return {
        "symbol": str(sym),
        "fold_label": str(boundary["fold_label"]),
        "entry_ns": int(fill_ns),
        "entry_price": float(price),
        "signed_weight": float(weight),
        "price_pnl_per_unit": 0.0,
        "funding_cashflow_per_unit": 0.0,
        "cost_allocated_per_unit": 0.0,
    }


def _cell_payload(
    *,
    arm_id: str,
    spec: Mapping[str, Any],
    universe: Sequence[str],
    scored: bool,
    stress_tier: str,
    fee_multiplier: float,
    slip_ticks: int,
    delay_days: int,
    folds,
    boundaries_out,
    rows,
    closed_spans,
    decision_records,
    fill_records,
    refusals: RefusalRegistry,
    defects,
    authority_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Assemble the V14-driver-compatible cell dict + result digest."""
    from research.adapter_v10.metrics import (
        daily_expectancy,
        daily_hit_rate,
        max_drawdown,
        position_profit_factor,
    )

    nets = [float(r["net_return_per_unit"]) for r in rows]
    span_pnls = [
        float(s["price_pnl_per_unit"])
        + float(s["funding_cashflow_per_unit"])
        - float(s["cost_allocated_per_unit"])
        for s in closed_spans
    ]
    pf, pf_reason = position_profit_factor(span_pnls)
    net_return_sum = math.fsum(nets)
    expectancy = daily_expectancy(nets)
    hit_rate = daily_hit_rate(nets)
    mdd = max_drawdown(nets)
    score_valid = all(
        isinstance(v, float) and math.isfinite(v)
        for v in (net_return_sum, mdd)
    ) and (expectancy is None or math.isfinite(expectancy))

    cost_fills = math.fsum(
        r["cost_charged_per_unit"] for r in rows if not r["carried_boundary"]
    )
    cost_holding = math.fsum(
        r["cost_charged_per_unit"] for r in rows if r["carried_boundary"]
    )
    funding_sum = math.fsum(float(r["funding_cashflow_per_unit"]) for r in rows)
    price_pnl_sum = math.fsum(float(r["price_pnl_per_unit"]) for r in rows)

    # per-fold nets (chronological fold order; every row trails exactly one fold)
    fold_labels = [label for _i, label, _s, _e in book_mod.fold_bounds(folds)]
    fold_net_sums = {label: 0.0 for label in fold_labels}
    for row in rows:
        label = str(row["fold_label"])
        if label not in fold_net_sums:
            raise ContractViolation(f"realized row trails unknown fold {label!r}")
        fold_net_sums[label] += float(row["net_return_per_unit"])
    fold_net_sums = {label: round(v, 12) for label, v in sorted(fold_net_sums.items())}
    fold_positive = [fold_net_sums[label] > 0.0 for label in sorted(fold_net_sums)]

    # per-symbol PnL + positive-PnL concentration shares
    pnl_by_symbol: dict[str, float] = {}
    for span, pnl in zip(closed_spans, span_pnls):
        sym = str(span["symbol"])
        pnl_by_symbol[sym] = pnl_by_symbol.get(sym, 0.0) + pnl
    pnl_by_symbol = {s: round(v, 12) for s, v in sorted(pnl_by_symbol.items())}
    total_positive = math.fsum(v for v in pnl_by_symbol.values() if v > 0.0)
    positive_share_by_symbol = {
        sym: (round(v / total_positive, 12) if total_positive > 0.0 and v > 0.0 else 0.0)
        for sym, v in pnl_by_symbol.items()
    }
    largest_symbol_positive_share = max(
        (v for v in positive_share_by_symbol.values()), default=0.0
    )

    scored_metrics = {
        "score_valid": bool(score_valid),
        "net_return_sum": round(net_return_sum, 12),
        "expectancy_per_day": (
            round(float(expectancy), 12) if expectancy is not None else None
        ),
        "max_drawdown": round(mdd, 12),
        "position_pf": round(pf, 12) if pf is not None else None,
        "pf_reason": pf_reason,
        "daily_hit_rate": round(hit_rate, 12) if hit_rate is not None else None,
        "n_positions": len(closed_spans),
        "n_decisions": len(decision_records),
        "n_fills": len(fill_records),
        "decisions": decision_records,
        "fills": fill_records,
        "cost_fills": round(cost_fills, 12),
        "cost_holding_terms": round(cost_holding, 12),
        "cost_total": round(cost_fills + cost_holding, 12),
        "funding_sum": round(funding_sum, 12),
        "price_pnl_sum": round(price_pnl_sum, 12),
        "remediated_kernel": True,
    }

    payload = {
        "schema": SCHEMA_VERSION,
        "artifact": "v15_i_family_2_cell",
        "family": FAMILY_ID,
        "arm_id": arm_id,
        "role": spec["role"],
        "feature": spec["feature"],
        "universe": list(universe),
        "scored": bool(scored),
        "scored_note": SCORED_FLAG_SEMANTICS,
        "stress_tier": str(stress_tier),
        "cost_model": {
            "taker_fee_bps": float(TAKER_FEE_BPS),
            "fee_multiplier": float(fee_multiplier),
            "slip_ticks": int(slip_ticks),
            "delay_days": int(delay_days),
            "principle": "costs and funding charged exactly once on booked PnL",
        },
        "pinned_authorities": {
            name: bool(entry["match"])
            for name, entry in dict(authority_report).items()
        },
        "schedule": {
            "n_boundaries": len(boundaries_out),
            "n_decision_boundaries": sum(
                1 for b in boundaries_out if b["kind"] == "decision"
            ),
            "n_force_flat_boundaries": sum(
                1 for b in boundaries_out if b["kind"] == "force_flat"
            ),
            "folds": [
                {"label": label, "start": start, "end_exclusive": end}
                for _i, label, start, end in book_mod.fold_bounds(folds)
            ],
        },
        "books": boundaries_out,
        "daily_returns": [
            {
                "decision_ns": int(r["decision_ns"]),
                "instant_ns": int(r["instant_ns"]),
                "instant_iso": r["instant_iso"],
                "fold_label": r["fold_label"],
                "price_pnl_per_unit": round(float(r["price_pnl_per_unit"]), 12),
                "funding_cashflow_per_unit": round(
                    float(r["funding_cashflow_per_unit"]), 12
                ),
                "cost_charged_per_unit": round(float(r["cost_charged_per_unit"]), 12),
                "net_return_per_unit": round(float(r["net_return_per_unit"]), 12),
                "carried_boundary": bool(r["carried_boundary"]),
            }
            for r in rows
        ],
        "positions": [
            {
                "symbol": str(s["symbol"]),
                "fold_label": s["fold_label"],
                "entry_ns": int(s["entry_ns"]),
                "exit_ns": int(s["exit_ns"]),
                "signed_weight": round(float(s["signed_weight"]), 12),
                "entry_price": round(float(s["entry_price"]), 12),
                "exit_price": round(float(s["exit_price"]), 12),
                "price_pnl_per_unit": round(float(s["price_pnl_per_unit"]), 12),
                "funding_cashflow_per_unit": round(
                    float(s["funding_cashflow_per_unit"]), 12
                ),
                "cost_allocated_per_unit": round(
                    float(s["cost_allocated_per_unit"]), 12
                ),
                "net_pnl_per_unit": round(pnl, 12),
            }
            for s, pnl in zip(closed_spans, span_pnls)
        ],
        "refusals": refusals.to_payload(),
        "defect_cells": {
            "count": len(defects),
            "cells": [
                dict(d)
                for d in sorted(
                    defects, key=lambda d: (d["symbol"], d["date"], d["reason"])
                )
            ],
        },
        "scored_metrics": scored_metrics,
        "fold_signs": {
            "fold_net_sums": fold_net_sums,
            "fold_positive": fold_positive,
        },
        "per_symbol": {
            "pnl_by_symbol": pnl_by_symbol,
            "positive_pnl_share_by_symbol": positive_share_by_symbol,
            "largest_symbol_positive_pnl_share": round(
                largest_symbol_positive_share, 12
            ),
        },
    }
    digest = hashlib.sha256(_canonical(payload).encode()).hexdigest()
    payload["hashes"] = {"result_sha256": digest}
    return payload


__all__ = [
    "COST_TIERS",
    "SCORED_FLAG_SEMANTICS",
    "SCHEMA_VERSION",
    "StagedDataError",
    "run_arm",
]
