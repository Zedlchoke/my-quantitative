"""Lane E scoring primitives — per-event gross/cost/net and aggregates.

Per-event contract (G3_FREEZE shared control 5 + dispatch E1):
- gross PnL in RETURN space = direction x (exit_price / entry_price - 1):
    LONG  : ratio - 1
    SHORT : 1 - ratio
  using the RAW prices already carried on the decision records (R2-1).
- cost: the record's frozen cost band by DV tier at entry
    cost_entry_bps_x1 = base_bps(DV tier) x 3.35  (Q-2 open band, entry fill)
    cost_exit_bps_x1  = base_bps(DV tier) x 1.0   (close ~ midday, exit fill)
  Per-side application EXACTLY ONCE (two fills per round trip):
    round_trip_bps(power) = (entry + exit) x power,  power in {1.0, 1.5, 2.0}
  (powers read from the frozen engine constants emv1.config.COST_STRESS_POWERS).
- net = gross - round_trip_return.

Aggregates per arm / fold / pooled: net expectancy per event (bps),
PF = sum(gains) / sum(|losses|) on NET, counts. All functions are pure and
deterministic (fixed iteration order over caller-supplied sequences).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

BPS = 10_000.0


def event_gross_return(rec: dict) -> float:
    """Directional gross return of one round trip, return space, raw prices."""
    ratio = rec["exit_price"] / rec["entry_price"]
    if rec["direction"] == "LONG":
        return ratio - 1.0
    if rec["direction"] == "SHORT":
        return 1.0 - ratio
    raise ValueError(f"invalid direction {rec['direction']!r}")


def event_round_trip_cost_return(rec: dict, power: float) -> float:
    """Round-trip cost as a return fraction: two fills, each costed once,
    scaled by the stress power. bps -> fraction."""
    rt_bps = (rec["cost_entry_bps_x1"] + rec["cost_exit_bps_x1"]) * power
    return rt_bps / BPS


def event_net_return(rec: dict, power: float) -> float:
    return event_gross_return(rec) - event_round_trip_cost_return(rec, power)


def aggregate(nets: Sequence[float], gross: Optional[Sequence[float]] = None) -> dict:
    """Pooled aggregates over a fixed-order sequence of per-event nets.

    pf: sum(positive nets) / |sum(negative nets)|; when there are NO losing
    events the ratio is infinite — represented as pf=None with the class
    "NO_LOSSES" (mechanically passes any finite PF bar).
    """
    n = len(nets)
    total = 0.0
    gains = 0.0
    losses = 0.0  # negative sum
    pos = 0
    neg = 0
    for v in nets:
        total += v
        if v > 0.0:
            gains += v
            pos += 1
        elif v < 0.0:
            losses += v
            neg += 1
    out = {
        "n": n,
        "net_expectancy_bps": round(total / n * BPS, 4) if n else None,
        "net_sum": total,
        "gains_sum": gains,
        "losses_sum": losses,  # <= 0
        "positive_events": pos,
        "negative_events": neg,
        "zero_events": n - pos - neg,
    }
    if n:
        out["gross_expectancy_bps"] = (
            round(sum(gross) / n * BPS, 4) if gross is not None else None
        )
    else:
        out["gross_expectancy_bps"] = None
    if losses == 0.0:
        out["pf"] = None
        out["pf_class"] = "NO_LOSSES"
    else:
        out["pf"] = round(gains / abs(losses), 4)
        out["pf_class"] = "FINITE"
    return out


def fold_aggregates(records: Sequence[dict], power: float,
                    fold_order: Sequence[str]) -> dict:
    """Per-fold aggregates in the frozen fold order F1..F4."""
    by_fold: Dict[str, List[float]] = {f: [] for f in fold_order}
    for r in records:  # file order
        by_fold.setdefault(r["fold"], []).append(event_net_return(r, power))
    return {
        f: aggregate(v)
        for f, v in by_fold.items()
        if v  # folds with zero records are omitted from the book's support
    }


def net_expectancy_bps(records: Sequence[dict], power: float,
                       gross: bool = False) -> Optional[float]:
    """Pooled per-event expectancy (bps); gross=True ignores costs."""
    vals = [
        event_gross_return(r) if gross else event_net_return(r, power)
        for r in records
    ]
    if not vals:
        return None
    return round(sum(vals) / len(vals) * BPS, 4)


def mean_round_trip_bps(records: Sequence[dict], power: float) -> Optional[float]:
    """Event-weighted mean round-trip band cost (bps) — the 'measured' cost
    figure read from the frozen band contract on the actual book."""
    if not records:
        return None
    tot = 0.0
    for r in records:
        tot += (r["cost_entry_bps_x1"] + r["cost_exit_bps_x1"]) * power
    return round(tot / len(records), 4)


def concentration(records: Sequence[dict], power: float,
                  top_k: int = 3) -> dict:
    """Single-name concentration on |book net|.

    Primary share (bar basis, cancellation-robust):
        share_name = |sum of nets in name| / sum(|net| over all events)
    Also reported: share vs |total book net| (cancelling basis).
    Returns ranked contributors (largest |net| first).
    """
    per_name: Dict[str, float] = {}
    abs_total = 0.0
    for r in records:
        v = event_net_return(r, power)
        per_name[r["ticker"]] = per_name.get(r["ticker"], 0.0) + v
        abs_total += abs(v)
    book_total = sum(per_name.values())
    rows = []
    for name, v in per_name.items():
        rows.append({
            "ticker": name,
            "net_sum": round(v, 6),
            "share_abs_denom": round(abs(v) / abs_total, 6) if abs_total else None,
            "share_book_net": round(abs(v) / abs(book_total), 6) if book_total else None,
        })
    rows.sort(key=lambda x: (-abs(x["net_sum"]), x["ticker"]))
    return {
        "basis": "|sum_name_net| / sum_|event_net|",
        "max_share": rows[0]["share_abs_denom"] if rows else None,
        "book_net_total": round(book_total, 6),
        "abs_net_total": round(abs_total, 6),
        "n_names": len(rows),
        "top": rows[:top_k],
    }


def largest_net_name(records: Sequence[dict], power: float) -> Optional[str]:
    """Ticker with the largest |sum of nets| (the drop-one candidate)."""
    per_name: Dict[str, float] = {}
    for r in records:
        v = event_net_return(r, power)
        per_name[r["ticker"]] = per_name.get(r["ticker"], 0.0) + v
    if not per_name:
        return None
    return max(sorted(per_name), key=lambda t: abs(per_name[t]))


def drop_records_of_name(records: Sequence[dict], ticker: str) -> List[dict]:
    return [r for r in records if r["ticker"] != ticker]
