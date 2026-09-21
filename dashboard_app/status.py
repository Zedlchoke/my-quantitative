"""App-level status: LIVE / STALE / DATA ERROR.

Rules (dispatch §8 + plan §9.7):

- LIVE       : heartbeats and valuation marks fresh within contract.
- STALE      : older than the allowed threshold but old data still
               readable (never rendered as a loss).
- DATA ERROR : files/schema broken or unreadable (the page then shows
               the last good snapshot, clearly labelled, or an error
               screen when none exists).

Contract thresholds (from the frozen engine): a valuation mark is stale
after ``staleness_rule_seconds`` (900 s); the scheduler/valuation
heartbeat loops run every 300 s, so a heartbeat older than 900 s is
stale. These are read from the engine snapshot when present and fall
back to the same defaults.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

HEARTBEAT_SCHEMA_PREFIX = "shv1_e_worker_heartbeat"
VALUATION_HEARTBEAT_SCHEMA_PREFIX = "shv1_valuation_worker_heartbeat"
DEFAULT_STALE_AFTER_SECONDS = 900.0


def _parse_ts(text: Any) -> Optional[datetime]:
    if not isinstance(text, str) or not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_heartbeat(path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Read one heartbeat json; returns (obj, error)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            obj = json.load(fh)
    except FileNotFoundError:
        return None, "file not found"
    except OSError as exc:
        return None, f"read error: {exc}"
    except ValueError as exc:
        return None, f"invalid json: {exc}"
    if not isinstance(obj, dict):
        return None, "heartbeat is not a json object"
    return obj, None


def heartbeat_view(
    obj: Optional[Dict[str, Any]],
    error: Optional[str],
    expected_schema_prefix: str,
    now: datetime,
    stale_after_seconds: float,
) -> Dict[str, Any]:
    """Freshness of one heartbeat file (schema-checked)."""
    view: Dict[str, Any] = {
        "present": obj is not None,
        "readable": error is None,
        "error": error,
        "schema_ok": False,
        "last_loop_utc": None,
        "age_seconds": None,
        "fresh": False,
        "last_error": None,
        "pid": None,
    }
    if obj is None:
        return view
    schema = obj.get("schema")
    view["schema_ok"] = (
        isinstance(schema, str) and schema.startswith(expected_schema_prefix)
    )
    view["last_loop_utc"] = obj.get("last_loop_utc")
    view["last_error"] = obj.get("last_error")
    view["pid"] = obj.get("pid")
    moment = _parse_ts(obj.get("last_loop_utc"))
    if moment is not None:
        view["age_seconds"] = max(0.0, (now - moment).total_seconds())
        view["fresh"] = view["age_seconds"] <= stale_after_seconds
    if not view["schema_ok"]:
        view["fresh"] = False
    return view


def _newest_mark_age_seconds(snapshot: Dict[str, Any], now: datetime) -> Optional[float]:
    """Age of the newest valid combined mark (from the engine snapshot)."""
    try:
        as_of = snapshot["valuation"]["combined"]["as_of_utc"]
    except (KeyError, TypeError):
        return None
    moment = _parse_ts(as_of)
    if moment is None:
        return None
    return max(0.0, (now - moment).total_seconds())


def app_status(
    snapshot: Optional[Dict[str, Any]],
    build_error: Optional[str],
    heartbeat_obj: Optional[Dict[str, Any]],
    heartbeat_error: Optional[str],
    valuation_heartbeat_obj: Optional[Dict[str, Any]],
    valuation_heartbeat_error: Optional[str],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Compute the single top-level status block for the page."""
    now = now or datetime.now(timezone.utc)
    stale_after = DEFAULT_STALE_AFTER_SECONDS
    if snapshot is not None:
        try:
            rule = snapshot["valuation"]["staleness_rule_seconds"]
            if isinstance(rule, (int, float)) and rule > 0:
                stale_after = float(rule)
        except (KeyError, TypeError):
            pass

    hb = heartbeat_view(
        heartbeat_obj, heartbeat_error, HEARTBEAT_SCHEMA_PREFIX, now, stale_after
    )
    vhb = heartbeat_view(
        valuation_heartbeat_obj,
        valuation_heartbeat_error,
        VALUATION_HEARTBEAT_SCHEMA_PREFIX,
        now,
        stale_after,
    )
    mark_age = _newest_mark_age_seconds(snapshot, now) if snapshot else None

    reasons: List[str] = []
    state = "LIVE"

    if snapshot is None:
        state = "DATA ERROR"
        reasons.append(
            f"không đọc được snapshot: {build_error or 'chưa build lần nào'}"
        )
    else:
        if build_error:
            # Files/schema are broken NOW. Old data may still be shown,
            # but the honest top-level state is DATA ERROR (dispatch §8).
            state = "DATA ERROR"
            reasons.append(f"lần build gần nhất lỗi: {build_error}")
        marks_stale = mark_age is not None and mark_age > stale_after
        hb_stale = (hb["present"] and not hb["fresh"]) or (
            hb["error"] and hb["error"] != "file not found"
        )
        vhb_stale = (vhb["present"] and not vhb["fresh"]) or (
            vhb["error"] and vhb["error"] != "file not found"
        )
        if state == "LIVE" and (marks_stale or hb_stale or vhb_stale):
            state = "STALE"
        if marks_stale:
            reasons.append(
                f"mark định giá mới nhất đã {int(mark_age)}s cũ (> {int(stale_after)}s)"
            )
        if hb["present"] and not hb["fresh"]:
            reasons.append("heartbeat decision worker quá cũ hoặc sai schema")
        if vhb["present"] and not vhb["fresh"]:
            note = ""
            if vhb.get("last_error"):
                note = f"; last_error: {vhb['last_error']}"
            reasons.append(
                "heartbeat valuation worker quá cũ hoặc sai schema"
                f"{note} — giữ mark hợp lệ cuối, không quy thành lỗ"
            )

    if not reasons:
        reasons.append("heartbeat và valuation marks còn mới theo contract")

    return {
        "state": state,
        "reasons": reasons,
        "stale_after_seconds": stale_after,
        "mark_age_seconds": mark_age,
        "decision_heartbeat": hb,
        "valuation_heartbeat": vhb,
        "computed_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def family_chip(fam_block: Dict[str, Any], heartbeat_data_status: Optional[str]) -> Dict[str, Any]:
    """Per-card chip: RUNNING / FLAT / DATA BLOCKED / STALE (+ note).

    Primary source is the engine family status (marks view); the
    decision heartbeat's data_status can only DOWNGRADE the colour to
    yellow, never upgrade it to green.
    """
    engine_status = str(fam_block.get("status") or "UNAVAILABLE_FAIL_CLOSED")
    stale = bool(fam_block.get("stale"))
    blocked = heartbeat_data_status in ("DATA_BLOCKED", "RISK_BLOCKED") or (
        engine_status == "UNAVAILABLE_FAIL_CLOSED"
    )
    if blocked:
        chip, tone = "DATA BLOCKED", "warn"
    elif stale or engine_status == "STALE":
        chip, tone = "STALE", "warn"
    elif engine_status == "FLAT_OK":
        chip, tone = "FLAT", "flat"
    elif engine_status in ("RUNNING", "OK"):
        chip, tone = "RUNNING", "ok"
    else:
        chip, tone = engine_status, "warn"
    note = str(fam_block.get("status_note") or "") or None
    return {"chip": chip, "tone": tone, "engine_status": engine_status,
            "heartbeat_data_status": heartbeat_data_status, "note": note}
