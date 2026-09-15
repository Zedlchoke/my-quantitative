"""Read-only dashboard snapshot builder (plan sections 9.1-9.8).

This module is a PURE VIEW over append-only shadow ledger bytes. It:

- reads JSONL event records ONLY through ``research.shadow_v1.ledger``
  readers (never writes, never rewrites, never truncates);
- validates the per-event accounting identity and refuses to publish
  numbers when an event fails it (red ``ACCOUNTING_MISMATCH`` banner,
  affected points become fail-closed gaps);
- builds the combined 300,000-USDT series as the STRICT sum of the
  three isolated sleeve equity series at common valid marks. Any sleeve
  mark-gap makes the combined point a gap with reason
  ``UNAVAILABLE_FAIL_CLOSED`` — never interpolated;
- computes today PnL against BOTH frozen windows (00:00 Asia/Ho_Chi_Minh
  and 00:00 UTC) using ONLY a valid mark stamped exactly at the window
  boundary. A missing boundary mark => ``UNAVAILABLE_FAIL_CLOSED``,
  never a value computed from a convenient later point. The exact
  window stamps are always printed;
- keeps FOUR SEPARATE counters (decision_count, order_intent_count,
  fill_count, closed_position_count) that are never conflated;
- exposes per-fill trade rows and click-through detail records whose
  cost rows (fee, slippage, every funding cashflow, total cost) come
  straight from the ledger bytes;
- shows SL/TP honestly: the three frozen cross-sectional families have
  NO native fixed stop/target, so ``stop_loss_price`` and
  ``take_profit_price`` are always the N/A strings and the true frozen
  ``exit_policy`` adapter string is shown. No stop or target number is
  ever invented;
- with no ledgers (pre-activation) everything renders as ``NOT_RUN`` /
  ``NO_TRADES_YET`` / ``UNAVAILABLE`` — never fake zeros.

The only emitted action type surfaced from the ledgers is
``TARGET_INTENT`` (enforced by ``research.shadow_v1.events`` at write
time and re-checked here).

Fill-record field mapping: the plan section 8 contract pins the record
fields but not the inner shape of ``virtual_fill_events``; this builder
therefore reads each fill dict tolerantly via the ``*_KEYS`` candidate
lists below and preserves the RAW fill dict in the click-through detail.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

from research.shadow_v1 import combined as combined_view
from research.shadow_v1 import events as shv1_events
from research.shadow_v1 import ledger as shv1_ledger
from research.shadow_v1 import scheduler as shv1_scheduler
from research.shadow_v1 import valuation as shv1_valuation

SCHEMA = "shv1_dashboard_snapshot_v1"
CYCLE_ID = "PROSPECTIVE-SHADOW-V1"

GAP_STATUS = "UNAVAILABLE_FAIL_CLOSED"
LOCAL_TZ_NAME = "Asia/Ho_Chi_Minh"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME)
UTC_TZ = dt.timezone.utc

STARTING_SLEEVE_EQUITY_USDT = 100_000.0
STARTING_COMBINED_EQUITY_USDT = 300_000.0
STARTING_COMBINED_LABEL = "300,000"

STATUS_RUNNING = "RUNNING"
STATUS_STALE = "STALE"
STATUS_DATA_BLOCKED = "DATA_BLOCKED"
STATUS_RISK_BLOCKED = "RISK_BLOCKED"
STATUS_STOPPED = "STOPPED"
STATUS_NOT_RUN = "NOT_RUN"

# ---- near-real valuation view (additive; marks from shv1_valuation_mark@1)
VALUATION_VIEW_SCHEMA = "shv1_valuation_view@1"
VALUATION_STALE_AFTER_SECONDS = 900.0  # 15 minutes at the 5-minute cadence
VALUATION_STATUS_NO_MARKS = "NO_MARKS"
VALUATION_STATUS_FLAT_OK = shv1_valuation.STATUS_FLAT_OK
VALUATION_STATUS_RUNNING = shv1_valuation.STATUS_RUNNING
VALUATION_STATUS_UNAVAILABLE = shv1_valuation.STATUS_UNAVAILABLE
SEED_RECORD_TYPE = shv1_valuation.SEED_RECORD_TYPE

SL_NA = "N/A — frozen family has no native fixed stop"
TP_NA = "N/A — frozen family has no native fixed target"

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"

_DAY_SECONDS = 86_400.0
_WEEK_SECONDS = 7.0 * _DAY_SECONDS

_REASON_VI = {
    STATUS_RUNNING: (
        "Đang chạy bình thường: đồng bộ lịch, dữ liệu và kế toán đều hợp lệ."
    ),
    STATUS_STALE: (
        "Dữ liệu cũ hơn hai chu kỳ quyết định liên tiếp: không có dấu hiệu "
        "mới nào được ghi nhận (fail-closed, không nội suy)."
    ),
    STATUS_DATA_BLOCKED: (
        "Quyết định bị chặn do thiếu dữ liệu PIT: không có giá nào được "
        "tổng hợp, không có lệnh nào được đặt."
    ),
    STATUS_RISK_BLOCKED: (
        "Quyết định bị chặn bởi giới hạn rủi ro ảo: chỉ tiêu mục tiêu được "
        "ghi lại trước/sau khi chặn, không có lệnh nào được đặt."
    ),
    STATUS_STOPPED: (
        "Đã dừng: sổ cái hỏng hoặc vi phạm hợp đồng sự kiện; từ chối hiển thị."
    ),
    STATUS_NOT_RUN: (
        "Chưa kích hoạt: chưa có sổ cái nào cho họ này (NO_TRADES_YET)."
    ),
}

# Tolerant virtual-fill field candidate lists (plan section 8 does not
# pin the inner fill shape; first present key wins).
VIRTUAL_TRADE_ID_KEYS = ("virtual_trade_id", "fill_id", "trade_id")
SYMBOL_KEYS = ("symbol", "asset")
SIDE_KEYS = ("side",)
QTY_KEYS = ("qty", "quantity", "filled_qty")
INTENDED_PRICE_KEYS = ("ref_price", "intended_price")
FILL_PRICE_KEYS = ("fill_price", "avg_fill_price", "entry_price")
FEE_KEYS = ("fee", "fee_amount")
SLIPPAGE_KEYS = ("slippage", "slippage_amount")
FILL_TS_KEYS = ("ts_utc", "actual_virtual_fill_time", "fill_time_utc", "executed_at_utc")
INTENDED_TS_KEYS = ("intended_fill_time", "intended_fill_utc")
SIGNAL_TIME_KEYS = ("signal_time", "signal_time_utc")
STATUS_KEYS = ("status", "position_status", "trade_status")
REALIZED_KEYS = ("realized_pnl",)
UNREALIZED_KEYS = ("unrealized_pnl",)
ENTRY_REASON_VI_KEYS = ("entry_reason_vi", "entry_reason")
EXIT_REASON_VI_KEYS = ("exit_reason_vi", "exit_reason")
SIGNAL_VALUE_KEYS = ("signal_value",)
RANK_KEYS = ("cross_sectional_rank", "rank")
TARGET_WEIGHT_KEYS = ("target_weight",)
PREVIOUS_WEIGHT_KEYS = ("previous_weight", "prev_weight")
MARK_KEYS = ("mark_price", "current_mark", "last_mark")
FUNDING_LIST_KEYS = ("funding_cashflows",)
FUNDING_SCALAR_KEYS = ("funding", "funding_cashflow")


class SnapshotError(RuntimeError):
    """Snapshot could not be built fail-closed."""


# ----------------------------------------------------------------------
# time helpers
# ----------------------------------------------------------------------
def parse_ts(text: Any) -> Optional[dt.datetime]:
    """Parse an ISO-8601 UTC timestamp (trailing Z or offset); naive -> UTC."""
    if not isinstance(text, str) or not text:
        return None
    raw = text.strip()
    if raw.endswith("Z") or raw.endswith("z"):
        raw = raw[:-1] + "+00:00"
    try:
        moment = dt.datetime.fromisoformat(raw)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC_TZ)
    return moment.astimezone(UTC_TZ)


def fmt_ts(moment: Optional[dt.datetime]) -> Optional[str]:
    if moment is None:
        return None
    return moment.astimezone(UTC_TZ).strftime(ISO_FMT)


def _now_utc_iso() -> str:
    return fmt_ts(dt.datetime.now(UTC_TZ))  # type: ignore[arg-type]


def _finite(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _first(mapping: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


# ----------------------------------------------------------------------
# frozen family identity (adapter constants + optional manifest check)
# ----------------------------------------------------------------------
def family_identity(family_id: str) -> Dict[str, Any]:
    """Frozen identity strings for one family (from the adapter registry)."""
    from research.shadow_v1.families import FAMILY_REGISTRY

    cls = FAMILY_REGISTRY.get(family_id)
    if cls is None:
        return {
            "family_id": family_id,
            "historical_family_id": None,
            "historical_verdict_label": None,
            "exit_policy": None,
            "decision_clock": None,
            "known_family": False,
        }
    return {
        "family_id": cls.FAMILY_ID,
        "historical_family_id": cls.HISTORICAL_FAMILY_ID,
        "historical_verdict_label": cls.HISTORICAL_VERDICT_LABEL,
        "exit_policy": cls.EXIT_POLICY,
        "decision_clock": cls.DECISION_CLOCK,
        "known_family": True,
    }


def _decision_interval_seconds(family_id: str) -> Optional[float]:
    try:
        schedule = shv1_scheduler.schedule_for(family_id)
    except shv1_scheduler.SchedulerError:
        return None
    return _WEEK_SECONDS if schedule == shv1_scheduler.SCHEDULE_WEEKLY_MONDAY_0000Z else _DAY_SECONDS


def _next_decision_utc(family_id: str, now_dt: dt.datetime) -> Optional[str]:
    try:
        upcoming = shv1_scheduler.pending_decisions(
            family_id,
            fmt_ts(now_dt),
            fmt_ts(now_dt + dt.timedelta(days=8)),
        )
    except shv1_scheduler.SchedulerError:
        return None
    return upcoming[0] if upcoming else None


# ----------------------------------------------------------------------
# per-record identity validation (read-only)
# ----------------------------------------------------------------------
def _record_identity_issues(record: Mapping[str, Any]) -> List[str]:
    """Derivable per-event identity checks; any hit refuses that event."""
    issues: List[str] = []
    if record.get("accounting_status") == shv1_events.ACCOUNTING_STATUS_MISMATCH:
        issues.append("record.accounting_status=IDENTITY_MISMATCH")
    equity = _finite(record.get("equity"))
    if equity is not None and equity <= 0:
        issues.append("equity_non_positive")
    gross = _finite(record.get("gross"))
    net = _finite(record.get("net"))
    if gross is not None and net is not None and abs(net) > gross + 1e-6:
        issues.append("abs(net)_exceeds_gross")
    fills = record.get("virtual_fill_events")
    if isinstance(fills, list) and fills:
        for cost_key, sum_keys in (
            ("fee", FEE_KEYS),
            ("slippage", SLIPPAGE_KEYS),
        ):
            declared = _finite(record.get(cost_key))
            parts = [_finite(_first(f, sum_keys)) for f in fills if isinstance(f, dict)]
            if declared is not None and parts and all(p is not None for p in parts):
                total = sum(float(p) for p in parts)  # type: ignore[arg-type]
                tol = max(1e-6, 1e-6 * abs(declared))
                if abs(total - declared) > tol:
                    issues.append(
                        f"record.{cost_key}={declared!r} != sum(virtual_fill_events."
                        f"{cost_key})={total!r}"
                    )
    return issues


def _normalize_funding(fill: Mapping[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[float]]:
    """Per-fill funding cashflows (list) + their scalar total, or UNAVAILABLE."""
    listed = _first(fill, FUNDING_LIST_KEYS)
    flows: List[Dict[str, Any]] = []
    if isinstance(listed, list):
        for item in listed:
            if isinstance(item, dict):
                flows.append(
                    {
                        "funding_time_utc": item.get("funding_time_utc", item.get("ts_utc")),
                        "rate": _finite(item.get("rate", item.get("funding_rate"))),
                        "notional": _finite(item.get("notional")),
                        "amount": _finite(item.get("amount", item.get("cashflow"))),
                        "raw": item,
                    }
                )
            elif isinstance(item, (int, float)) and not isinstance(item, bool):
                flows.append({"funding_time_utc": None, "rate": None, "notional": None,
                              "amount": float(item), "raw": item})
    scalar = _finite(_first(fill, FUNDING_SCALAR_KEYS))
    if not flows and scalar is not None:
        flows.append({"funding_time_utc": None, "rate": None, "notional": None,
                      "amount": scalar, "raw": scalar})
    total: Optional[float] = None
    amounts = [f["amount"] for f in flows]
    if amounts and all(a is not None for a in amounts):
        total = float(sum(amounts))  # type: ignore[arg-type]
    elif scalar is not None:
        total = scalar
    return flows, total


def _fill_status(raw_status: Any) -> str:
    if isinstance(raw_status, str):
        lowered = raw_status.strip().lower()
        if lowered in ("open", "closed"):
            return lowered
    return "unknown"


# ----------------------------------------------------------------------
# family block
# ----------------------------------------------------------------------
def _scan_family_ledger(path: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Read one ledger fail-closed. Returns (records, corruption_reason)."""
    if path is None or not os.path.exists(path):
        return [], None
    try:
        records = shv1_ledger.scan_events(path)
    except shv1_ledger.LedgerError as exc:
        return [], f"{type(exc).__name__}: {exc}"
    for record in records:
        try:
            shv1_events.validate_event_record(record)
        except shv1_events.EventContractError as exc:
            return [], f"EVENT_CONTRACT_VIOLATION: {exc}"
    records.sort(key=lambda r: (str(r.get("scheduled_decision_utc")), str(r.get("observed_at_utc"))))
    return records, None


def _today_block(
    points: List[Dict[str, Any]],
    boundary_dt: dt.datetime,
    now_dt: dt.datetime,
    tz_name: str,
) -> Dict[str, Any]:
    """Today PnL over one window. Boundary mark must be stamped EXACTLY at
    the window start; a missing boundary mark is UNAVAILABLE_FAIL_CLOSED."""
    boundary_iso = fmt_ts(boundary_dt)
    by_ts: Dict[str, Dict[str, Any]] = {}
    for point in points:
        if point.get("status") == "OK" and point.get("equity") is not None:
            by_ts[str(point["ts"])] = point
    block: Dict[str, Any] = {
        "tz": tz_name,
        "window_start_utc": boundary_iso,
        "window_start_local": boundary_dt.astimezone(LOCAL_TZ).isoformat(),
        "window_end_utc": fmt_ts(now_dt),
        "boundary_mark_required_at": boundary_iso,
        "boundary_mark_ts": None,
        "end_mark_ts": None,
        "pnl_usdt": None,
        "pnl_pct": None,
        "status": GAP_STATUS,
        "reason": None,
    }
    boundary_point = by_ts.get(boundary_iso)
    if boundary_point is None:
        block["reason"] = (
            f"no valid mark stamped exactly at the window boundary "
            f"{boundary_iso} (UNAVAILABLE_FAIL_CLOSED; never computed from "
            "a convenient later point)"
        )
        return block
    later = [p for p in points if boundary_iso < str(p["ts"]) <= fmt_ts(now_dt)
             and p.get("status") == "OK" and p.get("equity") is not None]
    if later:
        end_point = max(later, key=lambda p: str(p["ts"]))
    else:
        # Measured: the newest mark after the boundary IS the boundary mark.
        end_point = boundary_point
        block["reason"] = "no marks after the window boundary yet; equity unchanged since the boundary mark"
    start_equity = float(boundary_point["equity"])
    end_equity = float(end_point["equity"])
    block["boundary_mark_ts"] = boundary_point["ts"]
    block["end_mark_ts"] = end_point["ts"]
    block["pnl_usdt"] = end_equity - start_equity
    block["pnl_pct"] = (end_equity - start_equity) / start_equity * 100.0 if start_equity else None
    block["status"] = "OK"
    return block


def _drawdown_series(points: List[Dict[str, Any]], baseline: float) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    peak = baseline
    for point in points:
        equity = _finite(point.get("equity"))
        if point.get("status") != "OK" or equity is None:
            out.append({"ts": point.get("ts"), "status": GAP_STATUS,
                        "drawdown_abs": None, "drawdown_pct": None})
            continue
        peak = max(peak, equity)
        dd_abs = peak - equity
        out.append({
            "ts": point["ts"],
            "status": "OK",
            "drawdown_abs": dd_abs,
            "drawdown_pct": (dd_abs / peak * 100.0) if peak > 0 else None,
        })
    return out


def _build_family(
    family_id: str,
    path: Optional[str],
    now_dt: dt.datetime,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """Returns (family_block, trade_rows, detail_index, chart_markers)."""
    meta = family_identity(family_id)
    digest = shv1_ledger.ledger_digest(path) if path else None
    nbytes = shv1_ledger.byte_count(path) if path else 0
    records, corruption = _scan_family_ledger(path)

    block: Dict[str, Any] = {
        "family_id": family_id,
        "starting_equity_usdt": STARTING_SLEEVE_EQUITY_USDT,
        "identity": dict(meta),
        "ledger_path": os.path.abspath(path) if path else None,
        "ledger_digest": digest,
        "ledger_bytes": nbytes,
        "ledger_present": bool(path and os.path.exists(path)),
        "corruption": corruption,
        "status": STATUS_NOT_RUN,
        "status_reason_vi": _REASON_VI[STATUS_NOT_RUN],
        "stop_loss_price": SL_NA,
        "take_profit_price": TP_NA,
        "exit_policy": meta["exit_policy"],
        "historical_verdict_label": meta["historical_verdict_label"],
        "chart_points": [],
        "drawdown_series": [],
        "counters": {
            "decision_count": 0,
            "order_intent_count": 0,
            "fill_count": 0,
            "closed_position_count": 0,
        },
        "mismatch_reasons": [],
    }
    trade_rows: List[Dict[str, Any]] = []
    detail_index: Dict[str, Dict[str, Any]] = {}
    markers: List[Dict[str, Any]] = []
    source = {
        "ledger_digest": digest,
        "ledger_path": block["ledger_path"],
        "family_id": family_id,
    }

    if corruption:
        block["status"] = STATUS_STOPPED
        block["status_reason_vi"] = _REASON_VI[STATUS_STOPPED]
        block["mismatch_reasons"].append(corruption)
        block["identity_incidents"] = []
        block["no_order"] = {"emitted_action_types": None, "ok": True}
        block["data_age_seconds"] = None
        block["stale"] = False
        block["gap_status"] = GAP_STATUS
        block["source"] = {
            "ledger_digest": digest,
            "ledger_path": block["ledger_path"],
            "family_id": family_id,
            "as_of_utc": None,
        }
        return block, trade_rows, detail_index, markers

    if not records:
        # Pre-activation reality: no events at all. Counters are None
        # (NOT_RUN) when the ledger file itself is absent; an existing
        # but empty ledger file establishes an actual zero.
        established = block["ledger_present"]
        block.update(
            {
                "current_equity_usdt": None,
                "equity_as_of_utc": None,
                "today": {
                    "Asia/Ho_Chi_Minh": {
                        "status": STATUS_NOT_RUN,
                        "pnl_usdt": None,
                        "pnl_pct": None,
                        "reason": "no ledger events (NO_TRADES_YET)",
                    },
                    "UTC": {
                        "status": STATUS_NOT_RUN,
                        "pnl_usdt": None,
                        "pnl_pct": None,
                        "reason": "no ledger events (NO_TRADES_YET)",
                    },
                },
                "total_pnl_usdt": None,
                "total_pnl_pct": None,
                "realized_pnl_usdt": None,
                "unrealized_pnl_usdt": None,
                "fees_usdt": None,
                "slippage_usdt": None,
                "funding_usdt": None,
                "fills_today": None,
                "fills_total": None if not established else 0,
                "open_positions": {},
                "open_position_count": None if not established else 0,
                "win_count": None,
                "lose_count": None,
                "pnl_unresolved_fills": 0,
                "blocked_decisions": None if not established else 0,
                "gross": None,
                "net": None,
                "btc_beta": None,
                "exposure_as_of_utc": None,
                "drawdown_current": None,
                "drawdown_max": None,
                "last_signal_utc": None,
                "last_fill_utc": None,
                "next_decision_utc": _next_decision_utc(family_id, now_dt),
                "decision_interval_seconds": _decision_interval_seconds(family_id),
                "data_age_seconds": None,
                "stale": False,
                "gap_status": "NO_TRADES_YET",
                "counters": {
                    "decision_count": 0 if established else None,
                    "order_intent_count": 0 if established else None,
                    "fill_count": 0 if established else None,
                    "closed_position_count": 0 if established else None,
                },
                "identity_incidents": [],
                "no_order": {"emitted_action_types": None, "ok": True},
                "source": {
                    "ledger_digest": digest,
                    "ledger_path": block["ledger_path"],
                    "family_id": family_id,
                    "as_of_utc": None,
                },
            }
        )
        return block, trade_rows, {}, markers  # pre-activation NOT_RUN

    # ---- counters (FOUR SEPARATE values, never conflated) ----
    decision_count = len(records)
    order_intent_count = 0
    fill_rows: List[Dict[str, Any]] = []
    qty_by_symbol: Dict[str, float] = {}
    last_price_by_symbol: Dict[Tuple[str, Optional[str]], Dict[str, Any]] = {}
    prev_cost_digest: Optional[str] = None
    identity_issues: List[Dict[str, Any]] = []
    gap_seen = False
    last_signal_utc: Optional[str] = None
    last_fill_utc: Optional[str] = None
    blocked_decisions = 0
    fees: Optional[float] = None
    slippage: Optional[float] = None
    funding_total: Optional[float] = None
    realized_total = 0.0
    realized_unresolved = 0
    win_count = lose_count = 0

    for record in records:
        rec_ts = record.get("observed_at_utc") or record.get("scheduled_decision_utc")
        last_signal_utc = record.get("scheduled_decision_utc")
        issues = _record_identity_issues(record)
        if issues:
            identity_issues.append({"event_id": record["event_id"], "ts": rec_ts,
                                    "reasons": issues})
        equity = _finite(record.get("equity"))
        valid = (
            record.get("accounting_status") == shv1_events.ACCOUNTING_STATUS_OK
            and equity is not None
            and not issues
        )
        if record.get("data_status") == shv1_events.DATA_STATUS_BLOCKED or (
            record.get("risk_status") == shv1_events.RISK_STATUS_BLOCKED
        ):
            blocked_decisions += 1
        if record.get("data_status") == shv1_events.DATA_STATUS_OK:
            order_intent_count += len(record.get("target_weights") or {})

        # chart point: valid mark or fail-closed gap
        point: Dict[str, Any] = {
            "ts": rec_ts,
            "equity": equity if valid else None,
            "status": "OK" if valid else GAP_STATUS,
            "event_id": record["event_id"],
        }
        if not valid:
            gap_seen = True
            point["reason"] = (
                "; ".join(issues)
                if issues
                else f"record status accounting={record.get('accounting_status')!r} "
                f"data={record.get('data_status')!r} (no valid valuation)"
            )
            point["missing_symbols"] = []
        block["chart_points"].append(point)

        # markers
        cost_digest = record.get("cost_regime_digest")
        if prev_cost_digest is not None and cost_digest != prev_cost_digest:
            markers.append({"ts": rec_ts, "kind": "cost_regime_boundary",
                            "family_id": family_id, "event_id": record["event_id"],
                            "label": "cost regime changed (frozen hash boundary)"})
        prev_cost_digest = cost_digest
        if record.get("data_status") == shv1_events.DATA_STATUS_BLOCKED or (
            record.get("risk_status") == shv1_events.RISK_STATUS_BLOCKED
        ):
            markers.append({"ts": rec_ts, "kind": "blocked", "family_id": family_id,
                            "event_id": record["event_id"],
                            "label": f"blocked decision ({record.get('data_status')!r})"})
        if issues:
            markers.append({"ts": rec_ts, "kind": "incident", "family_id": family_id,
                            "event_id": record["event_id"],
                            "label": "accounting identity incident"})

        # cumulative cost books: last record carrying numbers wins
        rec_fee = _finite(record.get("fee"))
        rec_slip = _finite(record.get("slippage"))
        rec_funding = _finite(record.get("funding_cashflow"))
        if rec_fee is not None:
            fees = rec_fee
        if rec_slip is not None:
            slippage = rec_slip
        if rec_funding is not None:
            funding_total = rec_funding

        # fills
        fills = record.get("virtual_fill_events")
        fills = fills if isinstance(fills, list) else []
        for idx, fill in enumerate(fills):
            if not isinstance(fill, dict):
                continue
            symbol = _first(fill, SYMBOL_KEYS)
            side = _first(fill, SIDE_KEYS)
            qty = _finite(_first(fill, QTY_KEYS))
            ref_price = _finite(_first(fill, INTENDED_PRICE_KEYS))
            fill_price = _finite(_first(fill, FILL_PRICE_KEYS))
            fee = _finite(_first(fill, FEE_KEYS))
            slip = _finite(_first(fill, SLIPPAGE_KEYS))
            fill_ts = _first(fill, FILL_TS_KEYS) or rec_ts
            intended_ts = _first(fill, INTENDED_TS_KEYS)
            signal_time = _first(fill, SIGNAL_TIME_KEYS) or record.get("scheduled_decision_utc")
            status = _fill_status(_first(fill, STATUS_KEYS))
            realized = _finite(_first(fill, REALIZED_KEYS))
            unrealized = _finite(_first(fill, UNREALIZED_KEYS))
            funding_flows, funding_sum = _normalize_funding(fill)
            if isinstance(symbol, str) and qty is not None:
                signed = qty if side == "buy" else -qty if side == "sell" else 0.0
                qty_by_symbol[symbol] = qty_by_symbol.get(symbol, 0.0) + signed
            price = fill_price if fill_price is not None else ref_price
            if isinstance(symbol, str) and price is not None:
                last_price_by_symbol[(symbol, status)] = {
                    "price": price, "ts": fill_ts, "source": "last_virtual_fill_price"
                }
            last_fill_utc = fill_ts
            trade_id = _first(fill, VIRTUAL_TRADE_ID_KEYS) or f"{record['event_id']}:{idx}"
            trade_id = str(trade_id)
            if realized is not None:
                realized_total += realized
                if realized > 0:
                    win_count += 1
                elif realized < 0:
                    lose_count += 1
            else:
                realized_unresolved += 1
            notional = abs(qty * ref_price) if (qty is not None and ref_price is not None) else None
            entry_price = fill_price if fill_price is not None else ref_price
            mark_info = last_price_by_symbol.get((str(symbol) if isinstance(symbol, str) else "", "open"))
            if status == "closed":
                mark_or_exit = price
            else:
                mark_or_exit = (mark_info or {}).get("price", price)
            row = {
                "virtual_trade_id": trade_id,
                "family": family_id,
                "asset": symbol,
                "side": side,
                "status": status,
                "signal_time": signal_time,
                "intended_fill_time": intended_ts,
                "actual_virtual_fill_time": fill_ts,
                "entry_price": entry_price,
                "current_mark_or_exit_price": mark_or_exit,
                "quantity": qty,
                "notional": notional,
                "fee": fee,
                "slippage": slip,
                "funding": funding_sum,
                "realized_pnl": realized,
                "unrealized_pnl": unrealized,
                "return_pct": None,
                "stop_loss_price": SL_NA,
                "take_profit_price": TP_NA,
                "exit_policy": meta["exit_policy"],
                "event_id": record["event_id"],
                "ledger_digest": digest,
                "source_ts": rec_ts,
            }
            if realized is not None and notional:
                row["return_pct"] = realized / notional * 100.0
            trade_rows.append(row)
            fill_rows.append(fill)

            # ---- click-through detail (plan section 9.5) ----
            sym_key = str(symbol) if isinstance(symbol, str) else None
            target_weight = _finite(_first(fill, TARGET_WEIGHT_KEYS))
            if target_weight is None and sym_key:
                target_weight = _finite((record.get("target_weights") or {}).get(sym_key))
            previous_weight = _finite(_first(fill, PREVIOUS_WEIGHT_KEYS))
            if previous_weight is None and sym_key:
                previous_weight = _finite((record.get("previous_weights") or {}).get(sym_key))
            signal_value = _finite(_first(fill, SIGNAL_VALUE_KEYS))
            if signal_value is None and sym_key:
                signal_value = _finite((record.get("signal_values") or {}).get(sym_key))
            rank = _first(fill, RANK_KEYS)
            cost_parts = [v for v in (fee, slip, funding_sum) if v is not None]
            total_cost = float(sum(cost_parts)) if len(cost_parts) == 3 else None
            entry_reason_vi = _first(fill, ENTRY_REASON_VI_KEYS) or (
                "Vào vị thế theo tín hiệu chiến lược (TARGET_INTENT) tại mốc giá "
                "tham chiếu đã đóng; khối lượng và giá là ảo, không có lệnh thật."
            )
            if status == "closed":
                exit_reason_vi = _first(fill, EXIT_REASON_VI_KEYS) or (
                    "Đóng vị thế theo chính sách thoát đã đóng băng: "
                    f"{meta['exit_policy']}. Không có stop-loss/take-profit cố định."
                )
            else:
                exit_reason_vi = _first(fill, EXIT_REASON_VI_KEYS) or (
                    "Vị thế còn mở: chưa có lý do thoát."
                )
            requested_qty = qty
            requested_notional = notional
            detail = {
                "virtual_trade_id": trade_id,
                "family": family_id,
                "arm": record.get("arm_id"),
                "asset": symbol,
                "side": side,
                "status": status,
                "decision_timestamp_utc": record.get("scheduled_decision_utc"),
                "feature_cutoff_utc": record.get("feature_cutoff_utc"),
                "data_available_at_utc": record.get("observed_at_utc"),
                "data_status": record.get("data_status"),
                "signal_value": signal_value,
                "cross_sectional_rank": rank,
                "eligible_universe": record.get("eligible_symbols"),
                "target_weight": target_weight,
                "previous_weight": previous_weight,
                "requested_qty": requested_qty,
                "requested_notional": requested_notional,
                "virtual_filled_qty": qty,
                "intended_price": ref_price,
                "virtual_avg_fill_price": fill_price,
                "current_mark": mark_info.get("price") if (status != "closed" and mark_info) else None,
                "current_mark_source": (mark_info or {}).get("source") if status != "closed" else None,
                "exit_price": price if status == "closed" else None,
                "fee": fee,
                "funding_cashflows": funding_flows,
                "funding_total": funding_sum,
                "slippage": slip,
                "total_transaction_cost": total_cost,
                "realized_pnl_usdt": realized,
                "unrealized_pnl_usdt": unrealized,
                "return_pct": row["return_pct"],
                "entry_reason_vi": entry_reason_vi,
                "exit_reason_vi": exit_reason_vi,
                "event_id": record["event_id"],
                "config_digest": record.get("config_digest"),
                "data_snapshot_digest": record.get("data_snapshot_digest"),
                "cost_regime_digest": record.get("cost_regime_digest"),
                "code_freeze_sha": record.get("code_freeze_sha"),
                "source_ledger": {
                    "path": block["ledger_path"],
                    "digest": digest,
                    "bytes": nbytes,
                },
                "statuses": {
                    "accounting_status": record.get("accounting_status"),
                    "data_status": record.get("data_status"),
                    "risk_status": record.get("risk_status"),
                    "no_order_proof": record.get("no_order_proof"),
                },
                "stop_loss_price": SL_NA,
                "take_profit_price": TP_NA,
                "exit_policy": meta["exit_policy"],
                "ledger_digest": digest,
                "source_ts": rec_ts,
                "raw_virtual_fill_event": fill,
            }
            detail_index[trade_id] = detail
            if status == "closed":
                markers.append({"ts": fill_ts, "kind": "exit", "family_id": family_id,
                                "event_id": record["event_id"], "label": f"exit {symbol}"})
            else:
                markers.append({"ts": fill_ts, "kind": "entry", "family_id": family_id,
                                "event_id": record["event_id"], "label": f"entry {symbol}"})

    # open positions from the reconstructed signed-quantity book
    open_positions = {s: q for s, q in qty_by_symbol.items() if q != 0.0}

    # today windows (both frozen definitions)
    now_local = now_dt.astimezone(LOCAL_TZ)
    hcm_boundary = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    hcm_boundary_utc = hcm_boundary.astimezone(UTC_TZ)
    utc_boundary = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    today_hcm = _today_block(block["chart_points"], hcm_boundary_utc, now_dt, LOCAL_TZ_NAME)
    today_utc = _today_block(block["chart_points"], utc_boundary, now_dt, "UTC")

    def _count_fills_in_window(window: Dict[str, Any]) -> int:
        start = window.get("window_start_utc")
        end = window.get("window_end_utc")
        count = 0
        for row in trade_rows:
            ts = row.get("actual_virtual_fill_time")
            if isinstance(ts, str) and start and end and start < ts <= end:
                count += 1
        return count

    today_hcm["fills_in_window"] = _count_fills_in_window(today_hcm)
    today_utc["fills_in_window"] = _count_fills_in_window(today_utc)

    # today PnL honouring fills? PnL comes from equity marks only (already).
    latest = block["chart_points"][-1]
    latest_valid = [p for p in block["chart_points"] if p["status"] == "OK"]
    current_equity = latest_valid[-1]["equity"] if latest_valid else None
    equity_ts = latest_valid[-1]["ts"] if latest_valid else None
    total_pnl = (
        current_equity - STARTING_SLEEVE_EQUITY_USDT
        if current_equity is not None
        else None
    )
    dd_series = _drawdown_series(block["chart_points"], STARTING_SLEEVE_EQUITY_USDT)
    block["drawdown_series"] = dd_series
    dd_ok = [d for d in dd_series if d["status"] == "OK"]
    max_dd = max(dd_ok, key=lambda d: d["drawdown_abs"]) if dd_ok else None
    current_dd = dd_ok[-1] if dd_ok else None

    last_record = records[-1]
    interval = _decision_interval_seconds(family_id)
    last_valid_ts = parse_ts(equity_ts) if equity_ts else None
    data_age_seconds = (
        (now_dt - last_valid_ts).total_seconds() if last_valid_ts else None
    )
    stale = (
        data_age_seconds is not None
        and interval is not None
        and data_age_seconds > 2.0 * interval
    )

    # status resolution
    if identity_issues:
        status = STATUS_STOPPED
    elif last_record.get("data_status") == shv1_events.DATA_STATUS_BLOCKED:
        status = STATUS_DATA_BLOCKED
    elif last_record.get("risk_status") == shv1_events.RISK_STATUS_BLOCKED:
        status = STATUS_RISK_BLOCKED
    elif stale:
        status = STATUS_STALE
    else:
        status = STATUS_RUNNING

    block.update(
        {
            "status": status,
            "status_reason_vi": _REASON_VI[status],
            "current_equity_usdt": current_equity,
            "equity_as_of_utc": equity_ts,
            "today": {"Asia/Ho_Chi_Minh": today_hcm, "UTC": today_utc},
            "total_pnl_usdt": total_pnl,
            "total_pnl_pct": (
                total_pnl / STARTING_SLEEVE_EQUITY_USDT * 100.0
                if total_pnl is not None
                else None
            ),
            "realized_pnl_usdt": realized_total if trade_rows else None,
            "unrealized_pnl_usdt": (
                sum(r["unrealized_pnl"] for r in trade_rows if r["unrealized_pnl"] is not None)
                if any(r["unrealized_pnl"] is not None for r in trade_rows)
                else None
            ),
            "fees_usdt": fees,
            "slippage_usdt": slippage,
            "funding_usdt": funding_total,
            "fills_today": today_hcm["fills_in_window"],
            "fills_total": len(trade_rows),
            "open_positions": open_positions,
            "open_position_count": len(open_positions),
            "win_count": win_count if trade_rows else None,
            "lose_count": lose_count if trade_rows else None,
            "pnl_unresolved_fills": realized_unresolved if realized_unresolved else 0,
            "blocked_decisions": blocked_decisions,
            "gross": _finite(last_record.get("gross")),
            "net": _finite(last_record.get("net")),
            "btc_beta": _finite(last_record.get("btc_beta")),
            "exposure_as_of_utc": last_record.get("observed_at_utc")
            or last_record.get("scheduled_decision_utc"),
            "drawdown_current": current_dd,
            "drawdown_max": max_dd,
            "last_signal_utc": last_signal_utc,
            "last_fill_utc": last_fill_utc,
            "next_decision_utc": _next_decision_utc(family_id, now_dt),
            "decision_interval_seconds": interval,
            "data_age_seconds": data_age_seconds,
            "stale": stale,
            "gap_status": GAP_STATUS if gap_seen else ("OK" if latest_valid else GAP_STATUS),
            "counters": {
                "decision_count": decision_count,
                "order_intent_count": order_intent_count,
                "fill_count": len(trade_rows),
                "closed_position_count": sum(
                    1 for r in trade_rows if r["status"] == "closed"
                ),
            },
            "mismatch_reasons": block["mismatch_reasons"]
            + [i["reasons"][0] for i in identity_issues],
            "identity_incidents": identity_issues,
            "no_order": {
                "emitted_action_types": (
                    (last_record.get("no_order_proof") or {}).get("emitted_action_types")
                ),
                "ok": all(
                    (r.get("no_order_proof") or {}).get("emitted_action_types") == ["TARGET_INTENT"]
                    for r in records
                ),
            },
            "source": dict(source, as_of_utc=latest.get("ts")),
        }
    )
    if identity_issues:
        block["status"] = STATUS_STOPPED
        block["status_reason_vi"] = _REASON_VI[STATUS_STOPPED]

    # ---- per-symbol mini price series for click-through details (plan 9.5)
    series_by_symbol: Dict[str, List[Dict[str, Any]]] = {}
    blocked_markers: List[Dict[str, Any]] = []
    for record in records:
        rec_ts = record.get("observed_at_utc") or record.get("scheduled_decision_utc")
        if record.get("data_status") == shv1_events.DATA_STATUS_BLOCKED or (
            record.get("risk_status") == shv1_events.RISK_STATUS_BLOCKED
        ):
            blocked_markers.append({"ts": rec_ts, "event_id": record["event_id"]})
        for fill in record.get("virtual_fill_events") or []:
            if not isinstance(fill, dict):
                continue
            sym = _first(fill, SYMBOL_KEYS)
            price = _finite(_first(fill, FILL_PRICE_KEYS)) or _finite(
                _first(fill, INTENDED_PRICE_KEYS)
            )
            if isinstance(sym, str) and price is not None:
                status = _fill_status(_first(fill, STATUS_KEYS))
                series_by_symbol.setdefault(sym, []).append(
                    {
                        "ts": _first(fill, FILL_TS_KEYS) or rec_ts,
                        "price": price,
                        "kind": "exit" if status == "closed" else "entry",
                    }
                )
    for det in detail_index.values():
        det["price_series"] = series_by_symbol.get(det.get("asset"), [])
        det["blocked_event_markers"] = blocked_markers

    return block, trade_rows, detail_index, markers


# ----------------------------------------------------------------------
# combined block
# ----------------------------------------------------------------------
def _build_combined(
    family_blocks: Mapping[str, Dict[str, Any]],
    now_dt: dt.datetime,
    shadow_start_utc: Optional[str],
) -> Dict[str, Any]:
    sleeves: Dict[str, List[Dict[str, Any]]] = {}
    for fid in sorted(family_blocks):
        sleeves[fid] = family_blocks[fid]["chart_points"]
    any_points = any(pts for pts in sleeves.values())
    raw = combined_view.combined_equity_series(sleeves) if any_points else []
    raw_by_ts = {str(p["ts"]): p for p in raw}

    all_ts = sorted({str(p["ts"]) for pts in sleeves.values() for p in pts})
    anchor_ts = shadow_start_utc or (all_ts[0] if all_ts else None)

    chart_points: List[Dict[str, Any]] = []
    anchor_note = (
        "pre-event starting capital: three isolated sleeves at 100,000 USDT "
        "each (frozen config), combined 300,000 USDT"
    )
    if anchor_ts is not None:
        measured_at_anchor = raw_by_ts.get(str(anchor_ts))
        if measured_at_anchor is None:
            chart_points.append(
                {
                    "ts": str(anchor_ts),
                    "equity": STARTING_COMBINED_EQUITY_USDT,
                    "status": "OK",
                    "kind": "anchor",
                    "note": anchor_note,
                }
            )
        elif measured_at_anchor.get("status") == "OK":
            measured_at_anchor["kind"] = "anchor+measured"
            measured_at_anchor["anchor_confirmed"] = (
                float(measured_at_anchor["equity"]) == STARTING_COMBINED_EQUITY_USDT
            )
        # a measured GAP at the anchor ts is kept as-is (never masked)

    sleeve_start = {
        fid: family_blocks[fid]["starting_equity_usdt"] for fid in sorted(family_blocks)
    }
    prev_valid_equity: Optional[float] = None
    for point in raw:
        ts = str(point["ts"])
        entry: Dict[str, Any] = {"ts": ts, "status": point["status"], "equity": point.get("equity")}
        for inherited in ("kind", "anchor_confirmed", "note"):
            if inherited in point:
                entry[inherited] = point[inherited]
        if point["status"] == "OK":
            contributions = {}
            for fid in sorted(sleeves):
                match = next(
                    (p for p in sleeves[fid] if str(p["ts"]) == ts and p.get("status") == "OK"),
                    None,
                )
                contributions[fid] = {
                    "equity": match["equity"] if match else None,
                    "pnl": (match["equity"] - sleeve_start[fid])
                    if match and match.get("equity") is not None
                    else None,
                }
            entry["contributions"] = contributions
            equity = float(point["equity"])
            entry["daily_pnl"] = (
                equity - prev_valid_equity if prev_valid_equity is not None else None
            )
            entry["cumulative_pnl"] = equity - STARTING_COMBINED_EQUITY_USDT
            prev_valid_equity = equity
        else:
            entry["reason"] = GAP_STATUS
            entry["missing_sleeves"] = sorted(point.get("by_sleeve", {}).keys())
            entry["by_sleeve"] = point.get("by_sleeve")
        chart_points.append(entry)

    # de-duplicate by timestamp (at most one entry per ts; a measured gap
    # at the anchor ts is preserved, never masked by the placeholder)
    by_ts_dedup: Dict[str, Dict[str, Any]] = {}
    for point in chart_points:
        prev = by_ts_dedup.get(point["ts"])
        if prev is not None and prev.get("kind") == "anchor" and not point.get("kind"):
            continue  # measured entry replaces the placeholder
        by_ts_dedup[point["ts"]] = point
    chart_points = [by_ts_dedup[ts] for ts in sorted(by_ts_dedup)]

    valid_points = [p for p in chart_points if p["status"] == "OK" and p.get("equity") is not None]
    dd_series = _drawdown_series(chart_points, STARTING_COMBINED_EQUITY_USDT)

    # combined today: all three sleeves must reconcile at BOTH boundary marks
    def _combined_window(tz_name: str, boundary_dt: dt.datetime) -> Dict[str, Any]:
        boundary_iso = fmt_ts(boundary_dt)
        per_family = {
            fid: _today_block(sleeves[fid], boundary_dt, now_dt, tz_name)
            for fid in sorted(sleeves)
        }
        oks = [b for b in per_family.values() if b["status"] == "OK"]
        if len(oks) == len(per_family) and per_family:
            pnl = sum(b["pnl_usdt"] for b in oks)
            start_total = sum(
                next(
                    (
                        float(p["equity"])
                        for p in sleeves[fid]
                        if str(p["ts"]) == boundary_iso and p.get("status") == "OK"
                    ),
                    STARTING_SLEEVE_EQUITY_USDT,
                )
                for fid in sorted(sleeves)
            )
            block = {
                "tz": tz_name,
                "window_start_utc": boundary_iso,
                "window_start_local": boundary_dt.astimezone(LOCAL_TZ).isoformat(),
                "window_end_utc": fmt_ts(now_dt),
                "status": "OK",
                "pnl_usdt": pnl,
                "pnl_pct": pnl / start_total * 100.0 if start_total else None,
                "boundary_mark_ts": boundary_iso,
                "per_family": per_family,
                "reason": None,
            }
        else:
            missing = sorted(fid for fid, b in per_family.items() if b["status"] != "OK")
            block = {
                "tz": tz_name,
                "window_start_utc": boundary_iso,
                "window_start_local": boundary_dt.astimezone(LOCAL_TZ).isoformat(),
                "window_end_utc": fmt_ts(now_dt),
                "status": GAP_STATUS,
                "pnl_usdt": None,
                "pnl_pct": None,
                "boundary_mark_ts": None,
                "per_family": per_family,
                "reason": (
                    "UNAVAILABLE_FAIL_CLOSED — sleeves without a valid "
                    f"boundary mark: {missing}"
                ),
            }
        return block

    hcm_boundary = now_dt.astimezone(LOCAL_TZ).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).astimezone(UTC_TZ)
    utc_boundary = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    current_equity = valid_points[-1]["equity"] if valid_points else None

    def _sum_counter(key: str) -> Optional[int]:
        values = [family_blocks[fid]["counters"].get(key) for fid in family_blocks]
        if all(v is None for v in values):
            return None
        return sum(v for v in values if v is not None)

    counters = {
        key: _sum_counter(key)
        for key in ("decision_count", "order_intent_count", "fill_count", "closed_position_count")
    }
    return {
        "baseline_usdt": STARTING_COMBINED_EQUITY_USDT,
        "baseline_label": STARTING_COMBINED_LABEL,
        "anchor_ts": anchor_ts,
        "chart_points": chart_points,
        "valid_points": valid_points,
        "drawdown_series": dd_series,
        "current_equity_usdt": current_equity,
        "current_equity_as_of_utc": valid_points[-1]["ts"] if valid_points else None,
        "today": {
            "Asia/Ho_Chi_Minh": _combined_window(LOCAL_TZ_NAME, hcm_boundary),
            "UTC": _combined_window("UTC", utc_boundary),
        },
        "total_pnl_usdt": (
            current_equity - STARTING_COMBINED_EQUITY_USDT
            if current_equity is not None
            else None
        ),
        "total_pnl_pct": (
            (current_equity - STARTING_COMBINED_EQUITY_USDT)
            / STARTING_COMBINED_EQUITY_USDT
            * 100.0
            if current_equity is not None
            else None
        ),
        "drawdown_max": max(
            (d for d in dd_series if d["status"] == "OK"),
            key=lambda d: d["drawdown_abs"],
            default=None,
        ),
        "drawdown_current": next(
            (d for d in reversed(dd_series) if d["status"] == "OK"), None
        ),
        "counters": counters,
        "strict_sum_note": (
            "combined = strict sum of the three isolated sleeve equity series "
            "at common valid marks; any sleeve gap => UNAVAILABLE_FAIL_CLOSED, "
            "never interpolated"
        ),
    }


# ----------------------------------------------------------------------
# banners / identity / heartbeat
# ----------------------------------------------------------------------
def _identity_block(
    family_ids: List[str],
    identity_manifest_path: Optional[str],
) -> Dict[str, Any]:
    manifest: Optional[Dict[str, Any]] = None
    load_error: Optional[str] = None
    if identity_manifest_path:
        try:
            with open(identity_manifest_path, "rb") as fh:
                manifest = json.loads(fh.read().decode("utf-8"))
        except (OSError, ValueError) as exc:
            load_error = f"{type(exc).__name__}: {exc}"
    entries = {}
    if manifest:
        entries = {e.get("family_id"): e for e in manifest.get("families", []) if isinstance(e, dict)}
    families: Dict[str, Any] = {}
    drift: List[str] = []
    for fid in family_ids:
        meta = family_identity(fid)
        entry = entries.get(fid)
        checked = []
        if entry is not None:
            for key, adapter_key in (
                ("historical_family_id", "historical_family_id"),
                ("historical_verdict_label", "historical_verdict_label"),
            ):
                if entry.get(key) is not None and entry.get(key) != meta.get(adapter_key):
                    drift.append(
                        f"{fid}: manifest {key}={entry.get(key)!r} != adapter "
                        f"{meta.get(adapter_key)!r}"
                    )
            checked = ["historical_family_id", "historical_verdict_label"]
        families[fid] = {
            **meta,
            "manifest_entry_found": entry is not None,
            "manifest_checked_fields": checked,
            "historical_verdict_label_source": (
                "identity_manifest+adapter_agree"
                if entry is not None and not any(fid in d for d in drift)
                else ("adapter_frozen_constant" if meta["known_family"] else None)
            ),
        }
    status = "DRIFT" if drift else ("OK" if manifest else "NOT_RUN")
    return {
        "identity_status": status,
        "identity_drift": drift,
        "manifest_path": identity_manifest_path,
        "manifest_load_error": load_error,
        "verdict_labels_policy": (manifest or {}).get("verdict_labels_policy"),
        "replay_label_rule": (manifest or {}).get("replay_label_rule"),
        "families": families,
    }


def _heartbeat_block(
    family_blocks: Mapping[str, Dict[str, Any]],
    now_dt: dt.datetime,
) -> Dict[str, Any]:
    last_scheduled = None
    last_completed = None
    total_bytes = 0
    per_family = {}
    for fid, block in sorted(family_blocks.items()):
        total_bytes += block["ledger_bytes"] or 0
        points = block["chart_points"]
        if points:
            candidate = max(points, key=lambda p: str(p["ts"]))
            if last_completed is None or str(candidate["ts"]) > str(
                last_completed["scheduled_decision_utc"]
            ):
                last_completed = {
                    "family_id": fid,
                    "event_id": candidate["event_id"],
                    "scheduled_decision_utc": candidate["ts"],
                }
        per_family[fid] = {
            "ledger_path": block["ledger_path"],
            "bytes": block["ledger_bytes"],
            "digest": block["ledger_digest"],
            "record_count": block["counters"]["decision_count"],
        }
    return {
        "method": "computed_from_ledger_bytes (read-only)",
        "now_utc": fmt_ts(now_dt),
        "last_scheduled_event": last_scheduled,
        "last_completed_event": last_completed,
        "ledger_byte_count": total_bytes,
        "per_family": per_family,
    }


# ----------------------------------------------------------------------
# near-real valuation view (additive read-only view over mark ledgers)
# ----------------------------------------------------------------------
def resolve_valuation_mark_paths(ledgers_dir: str) -> Dict[str, Optional[str]]:
    """Map each known family to its valuation mark ledger.

    Mark ledgers live in the ``valuation_marks/`` sibling of the
    strategy ``ledgers/`` directory under the same runtime root. The
    path is returned whether or not the file exists yet (the view
    reports ``marks_present`` honestly).
    """
    from research.shadow_v1.families import FAMILY_REGISTRY

    if not ledgers_dir:
        return {fid: None for fid in sorted(FAMILY_REGISTRY)}
    abs_dir = os.path.abspath(ledgers_dir).rstrip(os.sep)
    # ledgers dir is <runtime_root>/ledgers => marks live in the
    # <runtime_root>/valuation_marks sibling (same runtime root)
    runtime_root = (
        os.path.dirname(abs_dir)
        if os.path.basename(abs_dir) == "ledgers"
        else abs_dir
    )
    out: Dict[str, Optional[str]] = {}
    for fid in sorted(FAMILY_REGISTRY):
        out[fid] = shv1_valuation.valuation_marks_path(runtime_root, fid)
    return out


def _valuation_today_block(
    points: List[Dict[str, Any]],
    boundary_dt: dt.datetime,
    now_dt: dt.datetime,
    tz_name: str,
) -> Dict[str, Any]:
    """Valuation-window PnL: a mark AT OR AFTER the boundary starts the
    window (the 5-minute cadence naturally produces boundary marks at
    00:00Z and 17:00Z). Missing input => UNAVAILABLE_FAIL_CLOSED."""
    boundary_iso = fmt_ts(boundary_dt)
    valid = sorted(
        (
            p
            for p in points
            if p.get("status") == "OK"
            and p.get("equity") is not None
            and parse_ts(p.get("ts")) is not None
            and boundary_iso <= str(p["ts"]) <= fmt_ts(now_dt)
        ),
        key=lambda p: str(p["ts"]),
    )
    block: Dict[str, Any] = {
        "tz": tz_name,
        "window_start_utc": boundary_iso,
        "window_start_local": boundary_dt.astimezone(LOCAL_TZ).isoformat(),
        "window_end_utc": fmt_ts(now_dt),
        "boundary_mark_ts": None,
        "end_mark_ts": None,
        "pnl_usdt": None,
        "pnl_pct": None,
        "status": GAP_STATUS,
        "reason": None,
    }
    if not valid:
        block["reason"] = (
            f"no valid valuation mark at or after the boundary {boundary_iso} "
            "(UNAVAILABLE_FAIL_CLOSED; never computed from a convenient "
            "earlier point)"
        )
        return block
    first = valid[0]
    last = valid[-1]
    start_equity = float(first["equity"])
    end_equity = float(last["equity"])
    pnl = end_equity - start_equity
    block.update(
        {
            "boundary_mark_ts": first["ts"],
            "end_mark_ts": last["ts"],
            "pnl_usdt": pnl,
            "pnl_pct": (pnl / start_equity * 100.0) if start_equity else None,
            "status": "OK",
            "reason": (
                "window open == window end (only the boundary mark exists so far)"
                if last is first
                else None
            ),
        }
    )
    return block


def _build_valuation_family(
    family_id: str,
    marks_path: Optional[str],
    now_dt: dt.datetime,
) -> Dict[str, Any]:
    """Read-only valuation view for ONE family (marks + seeds)."""
    block: Dict[str, Any] = {
        "family_id": family_id,
        "marks_path": os.path.abspath(marks_path) if marks_path else None,
        "marks_present": bool(marks_path and os.path.exists(marks_path)),
        "marks_digest": None,
        "mark_count": 0,
        "seed_count": 0,
        "status": VALUATION_STATUS_NO_MARKS,
        "status_note": "no valuation mark ledger (worker not writing yet)",
        "latest_mark": None,
        "latest_valid_mark": None,
        "data_age_seconds": None,
        "stale": False,
        "positions": [],
        "today": {
            "Asia/Ho_Chi_Minh": {},
            "UTC": {},
        },
        "total_pnl_usdt": None,
        "total_pnl_pct": None,
        "seeds": [],
        "series": [],
        "corruption": None,
    }
    if not marks_path:
        return block
    digest = shv1_valuation.valuation_digest(marks_path)
    block["marks_digest"] = digest
    try:
        records = shv1_valuation.read_valuation_records(marks_path)
    except shv1_valuation.ValuationError as exc:
        block["corruption"] = f"{type(exc).__name__}: {exc}"
        block["status"] = VALUATION_STATUS_UNAVAILABLE
        block["status_note"] = "mark ledger corrupt: refusing (never truncated)"
        return block

    marks: List[Dict[str, Any]] = []
    for rec in records:
        if rec.get("record_type") == SEED_RECORD_TYPE:
            block["seeds"].append(
                {
                    "seed_id": rec.get("seed_id"),
                    "ts_utc": rec.get("ts_utc"),
                    "equity": rec.get("equity"),
                    "record_type": SEED_RECORD_TYPE,
                    "note": rec.get("note"),
                }
            )
            continue
        try:
            shv1_valuation.validate_valuation_mark(rec)
        except shv1_valuation.ValuationError as exc:
            block["corruption"] = f"MARK_CONTRACT_VIOLATION: {exc}"
            block["status"] = VALUATION_STATUS_UNAVAILABLE
            block["status_note"] = "a mark violated its contract: refusing"
            return block
        marks.append(rec)

    block["mark_count"] = len(marks)
    block["seed_count"] = len(block["seeds"])
    if not marks:
        block["status_note"] = (
            "capital seed present, no market marks yet"
            if block["seeds"]
            else "no valuation marks yet"
        )
        return block

    series: List[Dict[str, Any]] = []
    valid_points: List[Dict[str, Any]] = []
    for rec in marks:
        ok = (
            rec.get("accounting_status") == shv1_events.ACCOUNTING_STATUS_OK
            and rec.get("equity") is not None
        )
        point = {
            "ts": rec.get("mark_timestamp_utc"),
            "equity": rec.get("equity") if ok else None,
            "status": "OK" if ok else GAP_STATUS,
            "mark_id": rec.get("mark_id"),
            "family_status": rec.get("status"),
        }
        series.append(point)
        if ok:
            valid_points.append(point)
    series.sort(key=lambda p: str(p["ts"]))
    valid_points.sort(key=lambda p: str(p["ts"]))
    block["series"] = series

    newest = max(marks, key=lambda r: str(r["mark_timestamp_utc"]))
    newest_valid = valid_points[-1] if valid_points else None
    newest_valid_rec = next(
        (
            r
            for r in reversed(marks)
            if r["mark_id"] == (newest_valid or {}).get("mark_id")
        ),
        None,
    )

    def _mark_view(rec: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if rec is None:
            return None
        return {
            "mark_id": rec.get("mark_id"),
            "mark_timestamp_utc": rec.get("mark_timestamp_utc"),
            "observed_at_utc": rec.get("observed_at_utc"),
            "status": rec.get("status"),
            "accounting_status": rec.get("accounting_status"),
            "equity": rec.get("equity"),
            "realized_pnl": rec.get("realized_pnl"),
            "unrealized_pnl": rec.get("unrealized_pnl"),
            "fees": rec.get("fees"),
            "slippage": rec.get("slippage"),
            "funding": rec.get("funding"),
            "cash": rec.get("cash"),
            "gross": rec.get("gross"),
            "net": rec.get("net"),
            "btc_beta": rec.get("btc_beta"),
            "price_source": rec.get("price_source"),
            "source_timestamp_utc": rec.get("source_timestamp_utc"),
            "source_digest": rec.get("source_digest"),
            "positions_digest": rec.get("positions_digest"),
        }

    block["latest_mark"] = _mark_view(newest)
    block["latest_valid_mark"] = _mark_view(newest_valid_rec)

    # data age from the newest VALID mark (an UNAVAILABLE mark proves a
    # gap, not freshness)
    if newest_valid is not None:
        age = (
            now_dt - parse_ts(newest_valid["ts"])
        ).total_seconds()
        block["data_age_seconds"] = age
        block["stale"] = age > VALUATION_STALE_AFTER_SECONDS

    newest_invalid = (
        newest.get("accounting_status") != shv1_events.ACCOUNTING_STATUS_OK
        or newest.get("equity") is None
    )
    if newest_invalid:
        block["status"] = VALUATION_STATUS_UNAVAILABLE
        block["status_note"] = (
            "newest mark is UNAVAILABLE_FAIL_CLOSED (missing price for an "
            "open position); no equity is shown, never stale reuse"
        )
    elif newest_valid_rec is None:
        block["status"] = VALUATION_STATUS_UNAVAILABLE
        block["status_note"] = "no valid mark exists"
    elif block["stale"]:
        block["status"] = STATUS_STALE
        block["status_note"] = (
            f"newest valid mark is older than "
            f"{VALUATION_STALE_AFTER_SECONDS:.0f}s (fail-closed freshness)"
        )
    else:
        block["status"] = newest_valid_rec.get("status")
        block["status_note"] = (
            "flat at seed capital (no open positions)"
            if block["status"] == VALUATION_STATUS_FLAT_OK
            else "marked from the frozen price source"
        )

    # per-position view from the newest valid mark
    if newest_valid_rec is not None:
        block["positions"] = [
            {
                "symbol": p.get("symbol"),
                "qty": p.get("qty"),
                "avg_price": p.get("avg_price"),
                "mark_price": p.get("mark_price"),
                "notional": p.get("notional"),
                "unrealized_pnl": p.get("unrealized_pnl"),
                "ts_opened": p.get("ts_opened"),
            }
            for p in (newest_valid_rec.get("positions") or [])
        ]

    equity_now = (
        float(newest_valid["equity"]) if newest_valid is not None else None
    )
    if equity_now is not None:
        block["total_pnl_usdt"] = (
            equity_now - STARTING_SLEEVE_EQUITY_USDT
        )
        block["total_pnl_pct"] = (
            block["total_pnl_usdt"] / STARTING_SLEEVE_EQUITY_USDT * 100.0
        )
    hcm_boundary = now_dt.astimezone(LOCAL_TZ).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).astimezone(UTC_TZ)
    utc_boundary = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    block["today"] = {
        "Asia/Ho_Chi_Minh": _valuation_today_block(
            series, hcm_boundary, now_dt, LOCAL_TZ_NAME
        ),
        "UTC": _valuation_today_block(series, utc_boundary, now_dt, "UTC"),
    }
    return block


def _build_valuation_combined(
    val_families: Mapping[str, Dict[str, Any]],
    now_dt: dt.datetime,
) -> Dict[str, Any]:
    """Combined valuation: strict sum at the newest COMMON valid mark.

    - sleeves with different latest mark times combine at the newest
      timestamp where ALL sleeves have valid marks;
    - with no common valid stamp the combined is UNAVAILABLE and the
      newest per-sleeve marks are shown with explicit ages;
    - NEVER mixes stale+fresh silently: if any sleeve's newest mark is
      UNAVAILABLE_FAIL_CLOSED (an open position without a price), the
      combined current equity is UNAVAILABLE_FAIL_CLOSED too.
    """
    combined: Dict[str, Any] = {
        "schema": VALUATION_VIEW_SCHEMA,
        "status": VALUATION_STATUS_NO_MARKS,
        "equity": None,
        "as_of_utc": None,
        "contributions": None,
        "reason": "no valuation marks exist for any sleeve",
        "per_sleeve_latest": {},
        "total_pnl_usdt": None,
        "total_pnl_pct": None,
        "today": {
            "Asia/Ho_Chi_Minh": {},
            "UTC": {},
        },
        "series": [],
        "note": (
            "combined = strict sum of isolated sleeve equities at the newest "
            "common valid valuation mark; no interpolation, no partial sums; "
            "a sleeve whose newest mark is UNAVAILABLE_FAIL_CLOSED makes the "
            "combined UNAVAILABLE_FAIL_CLOSED"
        ),
    }
    sleeve_points = {
        fid: block.get("series", [])
        for fid, block in sorted(val_families.items())
    }
    any_marks = any(pts for pts in sleeve_points.values())
    # per-sleeve newest + age (always surfaced)
    for fid, block in sorted(val_families.items()):
        latest = block.get("latest_mark")
        per: Dict[str, Any] = {
            "mark_timestamp_utc": (latest or {}).get("mark_timestamp_utc"),
            "status": block.get("status"),
            "equity": (latest or {}).get("equity"),
            "data_age_seconds": block.get("data_age_seconds"),
            "stale": block.get("stale"),
        }
        combined["per_sleeve_latest"][fid] = per

    if not any_marks:
        return combined

    common = shv1_valuation.combine_at_common_mark(sleeve_points)
    common_series: List[Dict[str, Any]] = []
    stamps = sorted(
        set.intersection(
            *(
                {str(p["ts"]) for p in pts if p.get("status") == "OK"}
                for pts in sleeve_points.values()
                if pts
            )
        )
    ) if all(pts for pts in sleeve_points.values()) else []
    for ts in stamps:
        pts = {
            fid: next(
                p for p in sleeve_points[fid]
                if str(p["ts"]) == ts and p.get("status") == "OK"
            )
            for fid in sleeve_points
        }
        common_series.append(
            {
                "ts": ts,
                "status": "OK",
                "equity": sum(float(p["equity"]) for p in pts.values()),
            }
        )
    combined["series"] = common_series

    # fail-closed override: a sleeve whose NEWEST mark is invalid
    # (open position, missing price) blocks the combined current equity
    any_newest_invalid = any(
        block.get("latest_mark") is not None
        and (
            block["latest_mark"].get("accounting_status")
            != shv1_events.ACCOUNTING_STATUS_OK
            or block["latest_mark"].get("equity") is None
        )
        for block in val_families.values()
    )
    if any_newest_invalid:
        combined.update(
            {
                "status": VALUATION_STATUS_UNAVAILABLE,
                "equity": None,
                "as_of_utc": None,
                "contributions": None,
                "reason": (
                    "at least one sleeve's newest mark is "
                    "UNAVAILABLE_FAIL_CLOSED (open position without a "
                    "price); combined current equity refused"
                ),
            }
        )
    elif common.get("status") != "OK":
        combined.update(
            {
                "status": VALUATION_STATUS_UNAVAILABLE,
                "equity": None,
                "as_of_utc": None,
                "contributions": None,
                "reason": common.get("reason"),
            }
        )
    else:
        equity = float(common["equity"])
        combined.update(
            {
                "status": "OK",
                "equity": equity,
                "as_of_utc": common.get("ts"),
                "contributions": common.get("contributions"),
                "reason": None,
                "total_pnl_usdt": equity - STARTING_COMBINED_EQUITY_USDT,
                "total_pnl_pct": (
                    (equity - STARTING_COMBINED_EQUITY_USDT)
                    / STARTING_COMBINED_EQUITY_USDT
                    * 100.0
                ),
            }
        )

    hcm_boundary = now_dt.astimezone(LOCAL_TZ).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).astimezone(UTC_TZ)
    utc_boundary = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    combined["today"] = {
        "Asia/Ho_Chi_Minh": _valuation_today_block(
            common_series, hcm_boundary, now_dt, LOCAL_TZ_NAME
        ),
        "UTC": _valuation_today_block(common_series, utc_boundary, now_dt, "UTC"),
    }
    return combined


def _valuation_block(
    family_ids: List[str],
    valuation_marks_by_family: Optional[Mapping[str, Optional[str]]],
    ledger_paths_by_family: Mapping[str, Optional[str]],
    now_dt: dt.datetime,
) -> Dict[str, Any]:
    derived = resolve_valuation_mark_paths(
        next(
            (
                os.path.dirname(p)
                for p in ledger_paths_by_family.values()
                if p
            ),
            "",
        )
        if any(ledger_paths_by_family.values())
        else ""
    )
    explicit = dict(valuation_marks_by_family) if valuation_marks_by_family else {}

    families: Dict[str, Dict[str, Any]] = {}
    mark_count = 0
    seed_count = 0
    for fid in family_ids:
        path = explicit.get(fid, derived.get(fid))
        block = _build_valuation_family(fid, path, now_dt)
        families[fid] = block
        mark_count += block["mark_count"]
        seed_count += block["seed_count"]
    combined = _build_valuation_combined(families, now_dt)
    return {
        "schema": VALUATION_VIEW_SCHEMA,
        "staleness_rule_seconds": VALUATION_STALE_AFTER_SECONDS,
        "families": families,
        "combined": combined,
        "counters": {
            "valuation_mark_count": mark_count,
            "valuation_seed_count": seed_count,
        },
        "counters_note": (
            "valuation_mark_count is a NEW separate counter rendered beside "
            "the four strategy counters; it never moves or re-labels them"
        ),
    }



# ----------------------------------------------------------------------
# public entry point
# ----------------------------------------------------------------------
def resolve_ledger_paths(ledgers_dir: str) -> Dict[str, Optional[str]]:
    """Map each known family to its ledger file inside ``ledgers_dir``."""
    from research.shadow_v1.families import FAMILY_REGISTRY

    out: Dict[str, Optional[str]] = {}
    for fid in sorted(FAMILY_REGISTRY):
        path = shv1_ledger.ledger_path(ledgers_dir, fid)
        out[fid] = path if os.path.exists(path) else None
    return out


def build_dashboard_snapshot(
    ledger_paths_by_family: Mapping[str, Optional[str]],
    now_utc: str,
    *,
    shadow_start_utc: Optional[str] = None,
    identity_manifest_path: Optional[str] = None,
    valuation_marks_by_family: Optional[Mapping[str, Optional[str]]] = None,
) -> Dict[str, Any]:
    """Build the read-only dashboard snapshot from append-only ledger files.

    ``now_utc`` pins the clock for reproducibility (the CLI passes it
    through; the server passes the current time). The builder NEVER
    writes to the ledgers and NEVER fabricates values: missing inputs
    are ``UNAVAILABLE_FAIL_CLOSED`` / ``NOT_RUN``.

    ``valuation_marks_by_family`` optionally pins the near-real mark
    ledgers explicitly; when omitted, the ``valuation_marks/`` sibling
    of each strategy ``ledgers/`` directory is derived (additive view:
    absent marks render as NO_MARKS and never touch the four strategy
    counters).
    """
    now_dt = parse_ts(now_utc)
    if now_dt is None:
        raise SnapshotError(f"invalid now_utc: {now_utc!r}")

    from research.shadow_v1.families import FAMILY_REGISTRY

    family_ids = sorted(set(ledger_paths_by_family) | set(FAMILY_REGISTRY))

    families: Dict[str, Dict[str, Any]] = {}
    trades: List[Dict[str, Any]] = []
    trade_index: Dict[str, Any] = {}
    markers: List[Dict[str, Any]] = []
    for fid in family_ids:
        block, rows, details, fam_markers = _build_family(
            fid,
            ledger_paths_by_family.get(fid),
            now_dt,
        )
        families[fid] = block
        trades.extend(rows)
        trade_index.update(details)
        markers.extend(fam_markers)

    trades.sort(key=lambda r: (str(r.get("actual_virtual_fill_time")), r["virtual_trade_id"]))
    for row in trades:
        event = trade_index.get(row["virtual_trade_id"])
        if event is not None:
            row["source_ts"] = event.get("source_ts")

    combined = _build_combined(families, now_dt, shadow_start_utc)

    # event index (click-through by event_id too)
    event_index: Dict[str, Any] = {}
    for fid, block in families.items():
        for point in block["chart_points"]:
            event_index[str(point["event_id"])] = {
                "event_id": point["event_id"],
                "family_id": fid,
                "ts": point["ts"],
                "status": point["status"],
                "ledger_path": block["ledger_path"],
                "ledger_digest": block["ledger_digest"],
            }

    mismatches = [
        {"family_id": fid, "reasons": b["mismatch_reasons"], "events": b["identity_incidents"]}
        for fid, b in sorted(families.items())
        if b["mismatch_reasons"]
    ]
    corrupt = [
        {"family_id": fid, "reason": b["corruption"]}
        for fid, b in sorted(families.items())
        if b["corruption"]
    ]
    identity_block = _identity_block(family_ids, identity_manifest_path)
    stale_families = sorted(fid for fid, b in families.items() if b["stale"])
    pre_activation = not any_active(families)

    banners: List[Dict[str, Any]] = []
    if corrupt:
        banners.append({
            "level": "red", "code": "LEDGER_CORRUPT",
            "message": "Sổ cái hỏng (crash mid-append hoặc vi phạm hợp đồng): "
                       "từ chối hiển thị, không bao giờ truncate.",
            "sources": corrupt,
        })
    if mismatches:
        banners.append({
            "level": "red", "code": "ACCOUNTING_MISMATCH",
            "message": "Vi phạm đồng nhất kế toán (equity == cash + vị thế): "
                       "từ chối hiển thị số liệu của các sự kiện vi phạm.",
            "sources": mismatches,
        })
    if identity_block["identity_drift"]:
        banners.append({
            "level": "red", "code": "IDENTITY_DRIFT",
            "message": "Nhãn verdict / định danh không khớp manifest đã đóng băng.",
            "sources": identity_block["identity_drift"],
        })
    if stale_families:
        banners.append({
            "level": "red", "code": "STALE_DATA",
            "message": "Dữ liệu cũ hơn hai chu kỳ liên tiếp của ít nhất một họ.",
            "sources": [{"family_id": fid} for fid in stale_families],
        })
    if not any_active(families):
        banners.append({
            "level": "neutral", "code": "NOT_RUN",
            "message": "NO_TRADES_YET — chưa kích hoạt: không có sổ cái sự kiện nào; "
                       "mọi số liệu là NOT_RUN/UNAVAILABLE, không bao giờ là số 0 giả.",
            "sources": [],
        })
    for fid, block in families.items():
        if block["gap_status"] == GAP_STATUS and block["counters"]["decision_count"]:
            banners.append({
                "level": "neutral", "code": "UNAVAILABLE_FAIL_CLOSED",
                "message": f"{fid}: có khoảng dữ liệu không định giá được "
                           "(fail-closed, không nội suy).",
                "sources": [{"family_id": fid, "reason": "mark gap in ledger"}],
            })

    if corrupt:
        system_status = "LEDGER_CORRUPT"
    elif mismatches:
        system_status = "ACCOUNTING_MISMATCH"
    elif identity_block["identity_drift"]:
        system_status = "IDENTITY_DRIFT"
    elif stale_families:
        system_status = "STALE"
    elif pre_activation:
        system_status = STATUS_NOT_RUN
    else:
        system_status = STATUS_RUNNING

    valuation_view = _valuation_block(
        family_ids,
        valuation_marks_by_family,
        ledger_paths_by_family,
        now_dt,
    )

    snapshot: Dict[str, Any] = {
        "schema": SCHEMA,
        "cycle_id": CYCLE_ID,
        "generated_utc": fmt_ts(now_dt),
        "now_utc": fmt_ts(now_dt),
        "timezone_default": LOCAL_TZ_NAME,
        "starting_virtual_capital_usdt": STARTING_COMBINED_EQUITY_USDT,
        "starting_virtual_capital_label": STARTING_COMBINED_LABEL,
        "shadow_start_utc": shadow_start_utc or combined["anchor_ts"],
        "pre_activation": pre_activation,
        "system_status": system_status,
        "accounting_ok": not mismatches,
        "banners": banners,
        "identity": identity_block,
        "families": families,
        "combined": combined,
        "valuation": valuation_view,
        "counters": combined["counters"],
        "counters_note": (
            "decision_count / order_intent_count / fill_count / "
            "closed_position_count are SEPARATE counters; they are never "
            "conflated into a single 'number of trades'"
        ),
        "trades": trades,
        "trade_index": trade_index,
        "event_index": event_index,
        "markers": markers,
        "scheduler_heartbeat": _heartbeat_block(families, now_dt),
        "sl_na": SL_NA,
        "tp_na": TP_NA,
        "exports_note": (
            "CSV/JSON exports are sanitized client-side views; they are NOT "
            "authority over the append-only ledgers and contain no credentials"
        ),
        "read_only_note": (
            "this dashboard is a view over append-only ledger bytes; it can "
            "never rewrite trades, equity or verdicts, and exposes no write "
            "endpoint capable of placing an order"
        ),
    }
    return snapshot


def any_active(family_blocks: Mapping[str, Dict[str, Any]]) -> bool:
    return any(
        (b["counters"].get("decision_count") or 0) > 0
        for b in family_blocks.values()
    )


def snapshot_json(snapshot: Mapping[str, Any]) -> str:
    """Canonical JSON text (sorted keys, no NaN) for bytes-stable output."""
    return json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
