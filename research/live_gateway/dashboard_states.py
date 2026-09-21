"""Dashboard status mapping — PURE function (plan §10, §12 test).

Maps a gateway /v1/status snapshot (+ optional worker heartbeat facts)
to the owner-verbatim chip set:

    WORKER LIVE / DECISION OK / DECISION DATA BLOCKED / MARK PRICE OK /
    MARK PRICE RATE LIMITED / MARK PRICE STALE / ACCOUNTING UNAVAILABLE

and the top badges LIVE / PARTIAL / STALE / DATA ERROR / OFFLINE.

The shared "DATA BLOCKED" chip is SPLIT: decision-blocked and
mark-price-blocked are never conflated. The live dashboard consumes
this only AFTER the owner GO (cutover step 1); until then it exists as
a tested pure contract.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def _mark_price_chip(
    mark_status: Optional[str], retry_allowed_at_utc: Optional[str]
) -> str:
    if mark_status in ("RATE_LIMITED",):
        return "MARK PRICE RATE LIMITED"
    if mark_status in ("STALE", "GAP_DETECTED", "DISCONNECTED"):
        return "MARK PRICE STALE"
    if mark_status in ("HEALTHY", "DEGRADED", "RECOVERING"):
        return "MARK PRICE OK"
    return "MARK PRICE STALE"  # unknown/None: honest default


def map_dashboard_status(
    status: Dict[str, Any],
    worker_heartbeat_age_s: Optional[float] = None,
    decision_data_ok: Optional[bool] = None,
    accounting_ok: Optional[bool] = None,
    schema_ok: bool = True,
) -> Dict[str, str]:
    """Produce {badge, chips:{...}} from one status snapshot.

    status: parsed GET /v1/status (or {} when the gateway is down).
    worker_heartbeat_age_s: age of the CONSUMER worker heartbeat
    (None = unknown). decision_data_ok / accounting_ok come from the
    worker's own ledger facts when available.
    """
    if not schema_ok or not isinstance(status, dict):
        return {
            "badge": "DATA ERROR",
            "worker": "WORKER LIVE" if worker_heartbeat_age_s is not None else "OFFLINE",
            "decision": "DECISION DATA BLOCKED",
            "mark_price": "MARK PRICE STALE",
            "accounting": "ACCOUNTING UNAVAILABLE",
            "retry_allowed_at_utc": None,
        }
    ws = status.get("ws") or {}
    ws_state = ws.get("state") or "DISCONNECTED"
    stale_symbols = status.get("stale_symbols") or []
    rest_breaker = (status.get("rest_breaker") or {}) or {}
    retry_allowed = rest_breaker.get("allowed_retry_at_utc")

    gateway_up = bool(status.get("pid"))
    ws_healthy = ws_state == "CONNECTED" and not stale_symbols

    if rest_breaker.get("state") == "RATE_LIMITED":
        mark_status = "RATE_LIMITED"
    elif not gateway_up or ws_state != "CONNECTED":
        mark_status = "DISCONNECTED"
    elif stale_symbols:
        mark_status = "STALE"
    else:
        mark_status = "HEALTHY"

    worker_live = (
        worker_heartbeat_age_s is None or worker_heartbeat_age_s <= 900.0
    )
    worker_chip = "WORKER LIVE" if worker_live else "OFFLINE"

    if decision_data_ok is None:
        decision_chip = (
            "DECISION OK"
            if mark_status in ("HEALTHY", "DEGRADED", "RECOVERING")
            else "DECISION DATA BLOCKED"
        )
    else:
        decision_chip = "DECISION OK" if decision_data_ok else "DECISION DATA BLOCKED"

    mark_chip = _mark_price_chip(mark_status, retry_allowed)
    accounting_chip = (
        "ACCOUNTING OK"
        if accounting_ok is None or accounting_ok
        else "ACCOUNTING UNAVAILABLE"
    )

    # Top badge law (plan §10): LIVE = worker + canonical price fresh;
    # PARTIAL = worker alive but one data surface failing; STALE = mark
    # too old; DATA ERROR = schema/read failure; OFFLINE = heartbeat dead.
    if not worker_live:
        badge = "OFFLINE"
    elif mark_status == "RATE_LIMITED":
        badge = "PARTIAL"
    elif mark_status == "STALE":
        badge = "STALE"
    elif mark_status == "DISCONNECTED" and not gateway_up:
        badge = "OFFLINE"
    elif mark_status == "DISCONNECTED":
        badge = "PARTIAL"
    elif decision_data_ok is False or accounting_ok is False:
        badge = "PARTIAL"
    else:
        badge = "LIVE"
    _ = ws_healthy  # documented; badge derives from mark_status above

    return {
        "badge": badge,
        "worker": worker_chip,
        "decision": decision_chip,
        "mark_price": mark_chip,
        "accounting": accounting_chip,
        "retry_allowed_at_utc": retry_allowed,
    }
