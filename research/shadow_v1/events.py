"""Per-event record contract for PROSPECTIVE-SHADOW-V1 (plan section 8).

Every scheduled decision emits ONE append-only record even when no trade
is possible. The field set below is the exact plan section 8 contract;
``validate_event_record`` enforces it (all required fields present, no
unknown fields).

``event_id`` is deterministic:
    first 32 lowercase hex chars of
    sha256("PROSPECTIVE-SHADOW-V1|{family_id}|{arm_id}|{scheduled_decision_utc}")
Restarting a worker reproduces/resumes the same event; it is never
duplicated.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Mapping, Optional

CYCLE_ID = "PROSPECTIVE-SHADOW-V1"
SCHEMA = "shv1_event_v1"
EVENT_ID_DOMAIN = "PROSPECTIVE-SHADOW-V1"

#: Exact plan section 8 required field list, in plan order.
REQUIRED_FIELDS = (
    "schema",
    "cycle_id",
    "family_id",
    "arm_id",
    "event_id",
    "scheduled_decision_utc",
    "observed_at_utc",
    "feature_cutoff_utc",
    "data_snapshot_digest",
    "code_freeze_sha",
    "config_digest",
    "cost_regime_digest",
    "eligible_symbols",
    "rejected_symbols_with_reason",
    "signal_values",
    "target_weights",
    "previous_weights",
    "virtual_fill_events",
    "fee",
    "slippage",
    "funding_cashflow",
    "price_pnl",
    "total_pnl",
    "cash",
    "equity",
    "gross",
    "net",
    "btc_beta",
    "data_status",
    "accounting_status",
    "risk_status",
    "no_order_proof",
)

DATA_STATUS_OK = "OK"
DATA_STATUS_BLOCKED = "DATA_BLOCKED"
ACCOUNTING_STATUS_OK = "OK"
ACCOUNTING_STATUS_UNAVAILABLE = "UNAVAILABLE_FAIL_CLOSED"
ACCOUNTING_STATUS_MISMATCH = "IDENTITY_MISMATCH"
RISK_STATUS_OK = "OK"
RISK_STATUS_BLOCKED = "RISK_BLOCKED"

DATA_STATUSES = (DATA_STATUS_OK, DATA_STATUS_BLOCKED)
ACCOUNTING_STATUSES = (
    ACCOUNTING_STATUS_OK,
    ACCOUNTING_STATUS_UNAVAILABLE,
    ACCOUNTING_STATUS_MISMATCH,
)
RISK_STATUSES = (RISK_STATUS_OK, RISK_STATUS_BLOCKED)


class EventContractError(ValueError):
    """Raised when a record violates the plan section 8 contract."""


def compute_event_id(family_id: str, arm_id: str, scheduled_decision_utc: str) -> str:
    """Deterministic event id: first 32 lowercase hex of sha256."""
    domain = f"{EVENT_ID_DOMAIN}|{family_id}|{arm_id}|{scheduled_decision_utc}"
    return hashlib.sha256(domain.encode("utf-8")).hexdigest()[:32]


def validate_event_record(record: Mapping[str, Any]) -> None:
    """Strict contract check: all plan section 8 fields, no extras."""
    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        raise EventContractError(f"event record missing fields: {missing}")
    unknown = sorted(set(record) - set(REQUIRED_FIELDS))
    if unknown:
        raise EventContractError(f"event record has unknown fields: {unknown}")
    if record["schema"] != SCHEMA:
        raise EventContractError(
            f"schema must be {SCHEMA!r}, got {record['schema']!r}"
        )
    if record["cycle_id"] != CYCLE_ID:
        raise EventContractError(
            f"cycle_id must be {CYCLE_ID!r}, got {record['cycle_id']!r}"
        )
    expected_id = compute_event_id(
        record["family_id"], record["arm_id"], record["scheduled_decision_utc"]
    )
    if record["event_id"] != expected_id:
        raise EventContractError(
            "event_id is not deterministic from "
            f"(family_id, arm_id, scheduled_decision_utc): "
            f"expected {expected_id}, got {record['event_id']!r}"
        )
    for status_field, allowed in (
        ("data_status", DATA_STATUSES),
        ("accounting_status", ACCOUNTING_STATUSES),
        ("risk_status", RISK_STATUSES),
    ):
        if record[status_field] not in allowed:
            raise EventContractError(
                f"{status_field} must be one of {allowed}, got "
                f"{record[status_field]!r}"
            )
    proof = record["no_order_proof"]
    if not isinstance(proof, dict) or "emitted_action_types" not in proof:
        raise EventContractError("no_order_proof must carry emitted_action_types")
    for action in proof["emitted_action_types"]:
        if action != "TARGET_INTENT":
            raise EventContractError(
                f"forbidden action type in no_order_proof: {action!r}"
            )


def build_event(
    *,
    family_id: str,
    arm_id: str,
    scheduled_decision_utc: str,
    observed_at_utc: str,
    feature_cutoff_utc: str,
    data_snapshot_digest: str,
    code_freeze_sha: str,
    config_digest: str,
    cost_regime_digest: str,
    eligible_symbols: Any,
    rejected_symbols_with_reason: Any,
    signal_values: Any,
    target_weights: Any,
    previous_weights: Any,
    virtual_fill_events: Any,
    fee: Any,
    slippage: Any,
    funding_cashflow: Any,
    price_pnl: Any,
    total_pnl: Any,
    cash: Any,
    equity: Any,
    gross: Any,
    net: Any,
    btc_beta: Any,
    data_status: str = DATA_STATUS_OK,
    accounting_status: str = ACCOUNTING_STATUS_OK,
    risk_status: str = RISK_STATUS_OK,
    no_order_proof: Optional[dict] = None,
) -> Dict[str, Any]:
    """Build a full plan section 8 record; validates before returning."""
    record: Dict[str, Any] = {
        "schema": SCHEMA,
        "cycle_id": CYCLE_ID,
        "family_id": family_id,
        "arm_id": arm_id,
        "event_id": compute_event_id(family_id, arm_id, scheduled_decision_utc),
        "scheduled_decision_utc": scheduled_decision_utc,
        "observed_at_utc": observed_at_utc,
        "feature_cutoff_utc": feature_cutoff_utc,
        "data_snapshot_digest": data_snapshot_digest,
        "code_freeze_sha": code_freeze_sha,
        "config_digest": config_digest,
        "cost_regime_digest": cost_regime_digest,
        "eligible_symbols": eligible_symbols,
        "rejected_symbols_with_reason": rejected_symbols_with_reason,
        "signal_values": signal_values,
        "target_weights": target_weights,
        "previous_weights": previous_weights,
        "virtual_fill_events": virtual_fill_events,
        "fee": fee,
        "slippage": slippage,
        "funding_cashflow": funding_cashflow,
        "price_pnl": price_pnl,
        "total_pnl": total_pnl,
        "cash": cash,
        "equity": equity,
        "gross": gross,
        "net": net,
        "btc_beta": btc_beta,
        "data_status": data_status,
        "accounting_status": accounting_status,
        "risk_status": risk_status,
        "no_order_proof": no_order_proof
        if no_order_proof is not None
        else {"emitted_action_types": ["TARGET_INTENT"], "scan_digest": None},
    }
    validate_event_record(record)
    return record


def build_data_blocked_event(
    *,
    family_id: str,
    arm_id: str,
    scheduled_decision_utc: str,
    observed_at_utc: str,
    feature_cutoff_utc: str,
    code_freeze_sha: str,
    config_digest: str,
    cost_regime_digest: str,
    blocked_reason: str,
    no_order_proof: Optional[dict] = None,
) -> Dict[str, Any]:
    """DATA_BLOCKED record: the scheduled decision is emitted even when no
    trade is possible. No price is synthesized; the same deterministic
    event_id is consumed so a retry can never duplicate the decision."""
    return build_event(
        family_id=family_id,
        arm_id=arm_id,
        scheduled_decision_utc=scheduled_decision_utc,
        observed_at_utc=observed_at_utc,
        feature_cutoff_utc=feature_cutoff_utc,
        data_snapshot_digest=f"DATA_BLOCKED:{blocked_reason}",
        code_freeze_sha=code_freeze_sha,
        config_digest=config_digest,
        cost_regime_digest=cost_regime_digest,
        eligible_symbols=[],
        rejected_symbols_with_reason={"*": blocked_reason},
        signal_values={},
        target_weights={},
        previous_weights={},
        virtual_fill_events=[],
        fee=0.0,
        slippage=0.0,
        funding_cashflow=0.0,
        price_pnl=0.0,
        total_pnl=0.0,
        cash=None,
        equity=None,
        gross=None,
        net=None,
        btc_beta=None,
        data_status=DATA_STATUS_BLOCKED,
        accounting_status=ACCOUNTING_STATUS_UNAVAILABLE,
        risk_status=RISK_STATUS_OK,
        no_order_proof=no_order_proof,
    )
