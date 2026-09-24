"""Combined history + Daily / weekly / monthly PnL buckets (view layer).

Quy ước chốt bởi owner (2026-09-23, bổ sung 2026-09-24):

- Mọi ranh giới kỳ theo giờ Việt Nam (Asia/Ho_Chi_Minh, UTC+7, không
  DST): ngày / tuần / tháng đều đóng tại 00:00 (12 giờ đêm) giờ VN —
  "tháng cuối cùng" được tính tới mark mới nhất, không chốt sớm.
- Tuần bắt đầu 00:00 thứ Tư ("tuần đầu tiên là thứ 4 tuần trước"):
  một tuần = [Thứ Tư 00:00, Thứ Tư kế tiếp 00:00) giờ VN.
- PnL của một kỳ = equity mark hợp lệ CUỐI trong kỳ − equity mark
  hợp lệ GẦN NHẤT trước đầu kỳ − VỐN THÊM chảy vào trong kỳ
  (capital flow; kỳ đầu tiên nối từ vốn gốc của các sleeve sáng lập).
- Owner 2026-09-24: BTC4H-BANDRIDGE là sleeve thứ tư mounted giữa
  chừng. Lịch sử TRƯỚC thời điểm mount phải giữ nguyên là chuỗi
  3 sleeve ($300,000 vốn gốc); khoản vốn +$100,000 của sleeve thứ tư
  là CAPITAL FLOW — không được hiện thành lợi nhuận và không được
  viết lại quá khứ 3 sleeve.
- Fail-closed: chỉ nhận mark status OK + equity hữu hạn; kỳ không có
  mark hợp lệ thì KHÔNG có số (không nội suy, không kéo giá trị cũ).

Pure functions over the engine snapshot (no I/O, deterministic):
``compose_combined_history(valuation)`` và
``build_pnl_periods(valuation)``. KHÔNG sửa engine, KHÔNG sửa ledger —
chỉ tái hợp các chuỗi per-family mà engine đã cung cấp.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
UTC = timezone.utc

SCHEMA = "shv1_pnl_periods_v1"
HISTORY_SCHEMA = "shv1_combined_history_v1"
KINDS = ("daily", "weekly", "monthly")
WEEKDAY_WEDNESDAY = 2  # Monday == 0

# các family valuation mark được worker ghi trên cùng lưới 5 phút;
# hai "first mark" cách nhau dưới ngưỡng này coi như cùng khởi đầu.
FOUNDING_TOLERANCE_SECONDS = 60.0

GAP_STATUS = "UNAVAILABLE_FAIL_CLOSED"


def _parse_ts(ts: Any) -> Optional[datetime]:
    if not isinstance(ts, str) or not ts.strip():
        return None
    text = ts.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def _fmt_ts(moment: Optional[datetime]) -> Optional[str]:
    return None if moment is None else moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_day(day: date) -> str:
    return day.strftime("%Y-%m-%d")


def _finite(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _family_points(
    family: Mapping[str, Any],
) -> List[Tuple[datetime, Optional[float], str]]:
    """(ts, equity-or-None, status) per series point, sorted by ts."""
    points: List[Tuple[datetime, Optional[float], str]] = []
    for point in family.get("series") or ():
        if not isinstance(point, Mapping):
            continue
        moment = _parse_ts(point.get("ts"))
        if moment is None:
            continue
        points.append(
            (
                moment,
                _finite(point.get("equity")),
                str(point.get("status") or GAP_STATUS),
            )
        )
    points.sort(key=lambda item: item[0])
    return points


# ----------------------------------------------------------------------
# Combined history: 3 sleeve sáng lập trước, sleeve mounted sau cộng vào
# như capital flow — đọc THUẦN từ các chuỗi per-family của engine.
# ----------------------------------------------------------------------
def compose_combined_history(valuation: Mapping[str, Any]) -> Dict[str, Any]:
    """Rebuild the combined equity history across a mid-program sleeve
    mount, using ONLY the per-family series + seeds the engine already
    published.

    Modes:
    - ``families``: every family block carries its own ``series`` — the
      combined series is the strict sum of the sleeves MOUNTED at each
      timestamp (a mounted sleeve without a valid point there makes the
      whole point a gap: fail-closed, no partial sums, no
      interpolation). Before the founding sleeves are all mounted the
      combined point is a gap (no single-sleeve fake history).
    - ``combined_only`` (fallback for old envelopes/fixtures without
      per-family series): the engine's combined series is passed
      through unchanged.

    Capital flows: late-mounted sleeves contribute a flow record
    ``{ts, family_id, amount}`` at their first series timestamp, with
    the amount taken from their seed record. The founding baseline is
    the strict sum of the FOUNDING sleeves' seeds (not of later
    sleeves), so pre-mount history is measured against the capital
    that actually existed then.
    """
    valuation = valuation or {}
    families = valuation.get("families") or {}
    parsed: Dict[str, List[Tuple[datetime, Optional[float], str]]] = {}
    seeds: Dict[str, Optional[Tuple[datetime, float]]] = {}
    for fid, fam in families.items():
        if not isinstance(fam, Mapping):
            continue
        pts = _family_points(fam)
        if not pts:
            continue
        parsed[fid] = pts
        seed = (fam.get("seeds") or [None])
        first_seed = seed[0] if seed and isinstance(seed[0], Mapping) else None
        stamp = _parse_ts(first_seed.get("ts_utc")) if first_seed else None
        equity = _finite(first_seed.get("equity")) if first_seed else None
        seeds[fid] = (stamp, equity) if stamp is not None and equity is not None else None

    if not parsed:
        return _compose_from_combined_only(valuation)

    first_ts = {fid: pts[0][0] for fid, pts in parsed.items()}
    global_first = min(first_ts.values())
    founding = sorted(
        fid
        for fid, ts in first_ts.items()
        if (ts - global_first).total_seconds() <= FOUNDING_TOLERANCE_SECONDS
    )
    complete_ts = max(first_ts[fid] for fid in founding)

    # baseline = strict sum of the FOUNDING sleeves' seeds, only when
    # they share one seed timestamp.
    baseline: Optional[float] = 0.0
    baseline_ts: Optional[datetime] = None
    baseline_stamps: set[datetime] = set()
    for fid in founding:
        seed = seeds.get(fid)
        if seed is None:
            baseline = None
            break
        stamp, equity = seed
        baseline_stamps.add(stamp)
        baseline += equity
    if baseline is not None:
        if len(baseline_stamps) != 1:
            baseline = None
        else:
            baseline_ts = baseline_stamps.pop()

    # capital flows from late-mounted sleeves (first series ts).
    flows: List[Dict[str, Any]] = []
    for fid in sorted(parsed):
        if fid in founding:
            continue
        seed = seeds.get(fid)
        flows.append(
            {
                "ts_utc": _fmt_ts(first_ts[fid]),
                "family_id": fid,
                "amount_usdt": seed[1] if seed else None,
                "source": "first valuation mark of late-mounted sleeve; amount from its CAPITAL_SEED record",
            }
        )
    flows.sort(key=lambda f: f["ts_utc"] or "")

    # combined series over the union of timestamps.
    by_ts: Dict[str, Dict[str, Tuple[datetime, Optional[float], str]]] = {}
    for fid, pts in parsed.items():
        for moment, equity, status in pts:
            by_ts.setdefault(fid, {})[_fmt_ts(moment)] = (moment, equity, status)
    all_ts = sorted({ts for m in by_ts.values() for ts in m})
    series: List[Dict[str, Any]] = []
    for ts in all_ts:
        mounted = [fid for fid in sorted(parsed) if first_ts[fid] <= _parse_ts(ts)]
        if _parse_ts(ts) < complete_ts:
            series.append(
                {
                    "ts": ts,
                    "status": GAP_STATUS,
                    "equity": None,
                    "reason": "founding sleeves chưa đủ mặt (chưa cộng từng phần)",
                }
            )
            continue
        missing = []
        total = 0.0
        contributions: Dict[str, float] = {}
        for fid in mounted:
            point = by_ts[fid].get(ts)
            if point is None or point[1] is None or point[2] != "OK":
                missing.append(fid)
                continue
            total += point[1]
            contributions[fid] = point[1]
        if missing:
            series.append(
                {
                    "ts": ts,
                    "status": GAP_STATUS,
                    "equity": None,
                    "reason": "thiếu mark hợp lệ: " + ", ".join(missing),
                }
            )
            continue
        series.append(
            {
                "ts": ts,
                "status": "OK",
                "equity": total,
                "contributions": contributions,
            }
        )

    return {
        "schema": HISTORY_SCHEMA,
        "mode": "families",
        "series": series,
        "capital_flows": flows,
        "baseline_equity": baseline,
        "baseline_ts_utc": _fmt_ts(baseline_ts),
        "founding_families": founding,
        "mount_complete_ts_utc": _fmt_ts(complete_ts),
    }


def _compose_from_combined_only(valuation: Mapping[str, Any]) -> Dict[str, Any]:
    """Fallback: no per-family series — pass the engine combined series
    through; flows derive from seed stamps that differ from the
    founding (earliest) seed stamp."""
    combined = valuation.get("combined") or {}
    series: List[Dict[str, Any]] = []
    for point in combined.get("series") or ():
        if not isinstance(point, Mapping):
            continue
        moment = _parse_ts(point.get("ts"))
        if moment is None:
            continue
        series.append(
            {
                "ts": _fmt_ts(moment),
                "status": str(point.get("status") or GAP_STATUS),
                "equity": _finite(point.get("equity")),
            }
        )
    series.sort(key=lambda p: p["ts"])

    stamps: Dict[datetime, float] = {}
    stamp_families: Dict[datetime, List[str]] = {}
    for fid, fam in (valuation.get("families") or {}).items():
        if not isinstance(fam, Mapping):
            continue
        seed = (fam.get("seeds") or [None])
        first_seed = seed[0] if seed and isinstance(seed[0], Mapping) else None
        stamp = _parse_ts(first_seed.get("ts_utc")) if first_seed else None
        equity = _finite(first_seed.get("equity")) if first_seed else None
        if stamp is None or equity is None:
            continue
        stamps[stamp] = stamps.get(stamp, 0.0) + equity
        stamp_families.setdefault(stamp, []).append(fid)

    baseline: Optional[float] = None
    baseline_ts: Optional[datetime] = None
    flows: List[Dict[str, Any]] = []
    if stamps:
        founding_stamp = min(stamps)
        baseline = stamps[founding_stamp]
        baseline_ts = founding_stamp
        for stamp in sorted(stamps):
            if stamp == founding_stamp:
                continue
            flows.append(
                {
                    "ts_utc": _fmt_ts(stamp),
                    "family_id": "+".join(sorted(stamp_families[stamp])),
                    "amount_usdt": stamps[stamp],
                    "source": "seed record with a later timestamp than the founding seed",
                }
            )
    return {
        "schema": HISTORY_SCHEMA,
        "mode": "combined_only",
        "series": series,
        "capital_flows": flows,
        "baseline_equity": baseline,
        "baseline_ts_utc": _fmt_ts(baseline_ts),
        "founding_families": sorted(stamp_families.get(min(stamps, default=stamp), [])) if stamps else [],
        "mount_complete_ts_utc": None,
    }


def _cum_flows(
    flows: Sequence[Mapping[str, Any]], moment: datetime
) -> Tuple[float, bool]:
    """Σ flow amounts with ts <= moment; poisoned flag when any flow at
    or before the boundary has an unknown amount (fail-closed)."""
    total = 0.0
    poisoned = False
    for flow in flows:
        ts = _parse_ts(flow.get("ts_utc"))
        if ts is None or ts > moment:
            continue
        amount = _finite(flow.get("amount_usdt"))
        if amount is None:
            poisoned = True
            continue
        total += amount
    return total, poisoned


# ----------------------------------------------------------------------
# PnL periods (flow-aware)
# ----------------------------------------------------------------------
def bucket_start_date(day: date, kind: str) -> date:
    """VN-local calendar date a bucket starts on, anchored at midnight
    VN: the day itself / the Wednesday leading it / the 1st of month."""
    if kind == "daily":
        return day
    if kind == "weekly":
        return day - timedelta(days=(day.weekday() - WEEKDAY_WEDNESDAY) % 7)
    if kind == "monthly":
        return day.replace(day=1)
    raise ValueError(f"unknown kind: {kind}")


def bucket_end_date(start: date, kind: str) -> date:
    """Exclusive end (VN-local calendar date)."""
    if kind == "daily":
        return start + timedelta(days=1)
    if kind == "weekly":
        return start + timedelta(days=7)
    if kind == "monthly":
        return (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    raise ValueError(f"unknown kind: {kind}")


def _vn_midnight_utc(day: date) -> datetime:
    """00:00 (12 giờ đêm) giờ VN of ``day`` as a UTC instant."""
    return datetime(day.year, day.month, day.day, tzinfo=VN_TZ).astimezone(UTC)


def _label(start: date, kind: str) -> str:
    if kind == "daily":
        return start.strftime("%d/%m")
    if kind == "weekly":
        end = bucket_end_date(start, kind) - timedelta(days=1)
        return f"{start.strftime('%d/%m')} → {end.strftime('%d/%m')}"
    return start.strftime("%m/%Y")


def _aggregate(
    points: Sequence[Tuple[datetime, float]],
    baseline: Optional[float],
    baseline_ts: Optional[str],
    flows: Sequence[Mapping[str, Any]],
    kind: str,
    now_dt: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """One pass: group valid points into buckets, then chain each
    bucket's PnL from the last equity strictly before its start,
    subtracting capital flows that landed between the two boundary
    marks (a flow is never PnL)."""
    groups: Dict[date, Dict[str, Any]] = {}
    for moment, equity in points:
        vn_day = moment.astimezone(VN_TZ).date()
        start = bucket_start_date(vn_day, kind)
        group = groups.get(start)
        if group is None:
            group = {"first": (moment, equity), "last": (moment, equity), "marks": 1}
            groups[start] = group
        else:
            group["last"] = (moment, equity)
            group["marks"] += 1

    rows: List[Dict[str, Any]] = []
    prev_equity = baseline
    prev_ts: Optional[str] = baseline_ts
    prev_moment: Optional[datetime] = _parse_ts(baseline_ts) if baseline_ts else None
    prev_is_seed = True
    for start in sorted(groups):
        group = groups[start]
        end = bucket_end_date(start, kind)
        end_moment, end_equity = group["last"]
        start_equity = prev_equity
        flows_in = 0.0
        flows_poisoned = False
        flow_names: List[str] = []
        if prev_moment is not None:
            cum_prev, poison_prev = _cum_flows(flows, prev_moment)
            cum_end, poison_end = _cum_flows(flows, end_moment)
            flows_in = cum_end - cum_prev
            flows_poisoned = poison_prev or poison_end
            for flow in flows:
                ts = _parse_ts(flow.get("ts_utc"))
                if (
                    ts is not None
                    and prev_moment < ts <= end_moment
                    and flow.get("family_id")
                ):
                    flow_names.append(str(flow["family_id"]))
        pnl = (
            end_equity - start_equity - flows_in
            if start_equity is not None and not flows_poisoned
            else None
        )
        pct = (
            pnl / start_equity * 100.0
            if pnl is not None and start_equity
            else None
        )
        rows.append(
            {
                "key": _iso_day(start) if kind != "monthly" else start.strftime("%Y-%m"),
                "label": _label(start, kind),
                "start_local_date": _iso_day(start),
                "end_local_date_exclusive": _iso_day(end),
                "start_utc": _fmt_ts(_vn_midnight_utc(start)),
                "end_utc": _fmt_ts(_vn_midnight_utc(end)),
                "start_equity": start_equity,
                "end_equity": end_equity,
                "start_mark_utc": prev_ts,
                "start_from_seed": prev_is_seed and prev_ts is not None,
                "end_mark_utc": _fmt_ts(end_moment),
                "marks": group["marks"],
                "capital_flows_usdt": flows_in if (flows_in or flow_names) else None,
                "capital_flow_families": flow_names or None,
                "pnl_usdt": pnl,
                "pnl_pct": pct,
                # "chưa đóng" = kỳ chưa kết thúc theo giờ VN hiện tại
                "open": bool(now_dt is not None and _vn_midnight_utc(end) > now_dt),
            }
        )
        prev_equity = end_equity
        prev_ts = _fmt_ts(end_moment)
        prev_moment = end_moment
        prev_is_seed = False
    return rows


def build_pnl_periods(
    valuation: Mapping[str, Any],
    now_dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Daily/weekly/monthly PnL periods over the combined history.

    Buckets exist only where valid marks exist (a day/week/month with
    no mark is absent — the UI renders it empty, never interpolated).
    ``now_dt`` (aware UTC) decides which periods are still open.
    Capital flows (late-mounted sleeves) are subtracted — vốn thêm
    không bao giờ hiện thành lợi nhuận.
    """
    history = compose_combined_history(valuation)
    points: List[Tuple[datetime, float]] = []
    for point in history["series"]:
        if point["status"] != "OK" or point.get("equity") is None:
            continue
        moment = _parse_ts(point["ts"])
        if moment is not None:
            points.append((moment, float(point["equity"])))
    points.sort(key=lambda item: item[0])
    flows = history["capital_flows"]
    periods: Dict[str, List[Dict[str, Any]]] = {
        kind: _aggregate(
            points,
            history["baseline_equity"],
            history["baseline_ts_utc"],
            flows,
            kind,
            now_dt=now_dt,
        )
        for kind in KINDS
    }
    return {
        "schema": SCHEMA,
        "tz": "Asia/Ho_Chi_Minh",
        "tz_note": (
            "mọi ranh giới ngày/tuần/tháng đóng tại 00:00 (12 giờ đêm) "
            "giờ Việt Nam; tuần bắt đầu 00:00 thứ Tư"
        ),
        "mode": history["mode"],
        "founding_families": history["founding_families"],
        "baseline_equity": history["baseline_equity"],
        "baseline_ts_utc": history["baseline_ts_utc"],
        "capital_flows": flows,
        "last_mark_utc": _fmt_ts(points[-1][0]) if points else None,
        "point_count": len(points),
        **periods,
    }
