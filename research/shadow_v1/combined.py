"""Read-only equal-capital combined view (plan sections 5, 9.3, G6).

This module holds NO references that can mutate sleeve accounts: view
functions take plain snapshots (dicts/lists of numbers) and return fresh
objects.

- combined_equity_series: strict sum of isolated equities at valid
  marks. Any sleeve mark-gap at a timestamp makes that combined point a
  gap with reason UNAVAILABLE_FAIL_CLOSED — never interpolated.
- pairwise_return_correlation on aligned valid equity series.
- same_symbol / same-direction overlap helper over weight books.
- combined gross/net/btc_beta exposures (additive across isolated
  sleeves; no cross-sleeve netting is ever fed back).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

GAP_STATUS = "UNAVAILABLE_FAIL_CLOSED"


class CombinedViewError(RuntimeError):
    """Invalid snapshot input for a combined view."""


def _require_point(point: Mapping[str, Any], sleeve: str) -> None:
    if "ts" not in point:
        raise CombinedViewError(f"sleeve {sleeve}: point missing 'ts'")


def combined_equity_series(
    sleeves: Mapping[str, Sequence[Mapping[str, Any]]]
) -> List[Dict[str, Any]]:
    """Strict sum across isolated sleeves at each timestamp.

    Each sleeve point: ``{"ts": iso, "equity": float|None,
    "status": "OK"|"UNAVAILABLE_FAIL_CLOSED", "missing_symbols": [...]}``.
    A sleeve with no point at a timestamp is treated as a gap there
    (fail closed; no carry-forward, no interpolation).
    """
    timestamps = set()
    for sleeve, pts in sleeves.items():
        for p in pts:
            if "ts" not in p:
                raise CombinedViewError(f"sleeve {sleeve}: point missing 'ts'")
            timestamps.add(str(p["ts"]))
    timestamps = sorted(timestamps)
    by_ts = {
        sleeve: {str(p["ts"]): p for p in pts} for sleeve, pts in sleeves.items()
    }
    combined: List[Dict[str, Any]] = []
    for ts in timestamps:
        gap_sleeves: Dict[str, Any] = {}
        total = 0.0
        ok = True
        for sleeve in sorted(sleeves):
            point = by_ts[sleeve].get(ts)
            if point is None:
                ok = False
                gap_sleeves[sleeve] = {
                    "reason": "no_point_at_timestamp",
                    "status": GAP_STATUS,
                }
                continue
            _require_point(point, sleeve)
            equity = point.get("equity")
            status = point.get("status", "OK" if equity is not None else GAP_STATUS)
            if status != "OK" or equity is None:
                ok = False
                gap_sleeves[sleeve] = {
                    "reason": GAP_STATUS,
                    "status": status,
                    "missing_symbols": list(point.get("missing_symbols", ())),
                }
                continue
            total += float(equity)
        if ok:
            combined.append(
                {"ts": ts, "status": "OK", "equity": total, "by_sleeve": None}
            )
        else:
            combined.append(
                {
                    "ts": ts,
                    "status": GAP_STATUS,
                    "equity": None,
                    "by_sleeve": gap_sleeves,
                }
            )
    return combined


def simple_returns(points: Sequence[Tuple[str, float]]) -> List[float]:
    """Simple returns over consecutive valid equity points."""
    returns: List[float] = []
    for prev, curr in zip(points, points[1:]):
        if prev == 0:
            raise CombinedViewError("zero prior equity: return undefined")
        returns.append(curr / prev - 1.0)
    return returns


def pairwise_return_correlation(
    series_a: Sequence[Mapping[str, Any]],
    series_b: Sequence[Mapping[str, Any]],
) -> Tuple[Optional[float], str]:
    """Pearson correlation of aligned simple returns.

    Fail closed: any gap in either series or timestamp misalignment
    returns (None, reason) instead of a number over partial data.
    """
    a_by_ts = {str(p["ts"]): p for p in series_a}
    b_by_ts = {str(p["ts"]): p for p in series_b}
    if set(a_by_ts) != set(b_by_ts):
        return None, "timestamp sets differ between sleeves"
    common = sorted(set(a_by_ts))
    if len(common) < 3:
        return None, "fewer than 3 aligned points; correlation NOT_RUN"
    a_points = []
    b_points = []
    for ts in common:
        pa, pb = a_by_ts[ts], b_by_ts[ts]
        if pa.get("status") != "OK" or pa.get("equity") is None:
            return None, f"sleeve A gap at {ts}"
        if pb.get("status") != "OK" or pb.get("equity") is None:
            return None, f"sleeve B gap at {ts}"
        a_points.append(float(pa["equity"]))
        b_points.append(float(pb["equity"]))
    ra = simple_returns(a_points)
    rb = simple_returns(b_points)
    n = len(ra)
    mean_a = sum(ra) / n
    mean_b = sum(rb) / n
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(ra, rb))
    var_a = sum((x - mean_a) ** 2 for x in ra)
    var_b = sum((y - mean_b) ** 2 for y in rb)
    if var_a == 0 or var_b == 0:
        return None, "zero variance in a return series; correlation undefined"
    corr = cov / math.sqrt(var_a * var_b)
    return corr, "OK"


def same_symbol_direction_overlap(
    book_a: Mapping[str, float],
    book_b: Mapping[str, float],
) -> Dict[str, Any]:
    """Same-symbol / same-direction overlap between two weight books."""
    shared = sorted(set(book_a) & set(book_b))
    same_direction = [s for s in shared if book_a[s] * book_b[s] > 0]
    opposite_direction = [s for s in shared if book_a[s] * book_b[s] < 0]
    overlap_gross = sum(
        min(abs(float(book_a[s])), abs(float(book_b[s]))) for s in shared
    )
    return {
        "shared_symbols": shared,
        "same_direction_symbols": same_direction,
        "opposite_direction_symbols": opposite_direction,
        "shared_notional_overlap_gross": overlap_gross,
    }


def combined_exposures(
    exposures: Sequence[Mapping[str, Any]]
) -> Dict[str, Optional[float]]:
    """Additive gross / net / btc_beta across isolated sleeves.

    Gross adds magnitudes (no netting between sleeves); net adds signed
    weights; btc_beta adds weighted betas. Any sleeve with unavailable
    exposure makes the combined figure UNAVAILABLE (None) — fail closed.
    """
    gross = 0.0
    net = 0.0
    btc_beta = 0.0
    for item in exposures:
        if item.get("status", "OK") != "OK" or item.get("gross") is None or item.get("net") is None:
            return {
                "gross": None,
                "net": None,
                "btc_beta": None,
                "status": GAP_STATUS,
                "reason": "sleeve exposure unavailable (UNAVAILABLE_FAIL_CLOSED)",
            }
        gross += float(item["gross"])
        net += float(item["net"])
        beta = item.get("btc_beta")
        if beta is not None:
            btc_beta += float(beta)
    return {"gross": gross, "net": net, "btc_beta": btc_beta, "status": "OK"}
