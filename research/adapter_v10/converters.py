"""BG2 -- daily target books to portfolio / fill / scoring payloads (G1).

Conversion is a pure function of the strategy-supplied book and the fill
sweep of the same instant. Sign semantics are derived ONCE here from the
weight vector (positive = long, negative = short) so no downstream consumer
can disagree with the book; weights are validated against an explicit cap
ceiling (default 0.30, stricter allowed, looser rejected).
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Optional, Sequence

from research.adapter_v10.protocol import (
    DEFAULT_WEIGHT_CAP_MAX,
    AdapterError,
    ContractViolation,
    FillRecord,
    StressSpec,
    TargetBook,
    WEIGHT_TOL,
)

BOOK_STATUS_OK = "OK"
STATUS_CARRY = "CARRIED_FORWARD"
STATUS_FORCE_FLAT = "FORCE_FLAT"


def normalise_target_book(
    raw: Any,
    *,
    decision_ns: int,
    cap_max: float = DEFAULT_WEIGHT_CAP_MAX,
    allow_empty: bool = True,
) -> TargetBook:
    """Validate + normalise any supported strategy book shape into TargetBook.

    Accepted inputs: a mapping ``{symbol: weight}``, a sequence of
    ``[symbol, weight]`` pairs, or a dict carrying ``weights`` in either shape
    (the repo-wide convention). Missing symbols get weight 0.0 by construction;
    duplicated symbols are refused.
    """
    if isinstance(raw, Mapping):
        payload: dict[str, Any] = dict(raw)
        status = str(payload.get("status") or BOOK_STATUS_OK)
        carried = bool(payload.get("carried_forward", False))
        reason = payload.get("reason_code")
        diagnostics_raw = payload.get("diagnostics") or {}
        if "weights" in payload:
            body: Any = payload["weights"]
        elif "longs" in payload or "shorts" in payload:
            body = []
        else:
            # a bare {symbol: weight} mapping IS the book
            body = {key: value for key, value in payload.items()}
    else:
        body = raw
        status, carried, reason, diagnostics_raw = BOOK_STATUS_OK, False, None, {}

    weights_map = _pairs_to_mapping(body)
    longs_input = None
    shorts_input = None
    if isinstance(raw, Mapping):
        if "longs" in raw or "shorts" in raw:
            longs_input = _pairs_to_mapping(raw.get("longs", []))
            shorts_input = _pairs_to_mapping(raw.get("shorts", []))

    if not weights_map and not (longs_input or shorts_input):
        if not allow_empty:
            raise ContractViolation(f"target book at {decision_ns} is empty")
    if not weights_map:
        merged: dict[str, float] = {}
        for sym, weight in {**(longs_input or {}), **(shorts_input or {})}.items():
            if sym in merged:
                raise ContractViolation(f"duplicate symbol across legs: {sym}")
            merged[sym] = float(weight)
        weights_map = merged

    cleaned: list[tuple[str, float]] = []
    for sym in sorted(weights_map):
        weight = float(weights_map[sym])
        if not math.isfinite(weight):
            raise ContractViolation(f"non-finite weight for {sym}")
        if abs(weight) > float(cap_max) + WEIGHT_TOL:
            raise ContractViolation(
                f"cap breach at {decision_ns}: |w({sym})|={abs(weight)} exceeds "
                f"{float(cap_max)}"
            )
        if abs(weight) <= WEIGHT_TOL:
            weight = 0.0
        cleaned.append((sym, round(weight, 12)))

    longs = tuple((s, w) for s, w in cleaned if w > 0.0)
    shorts = tuple((s, w) for s, w in cleaned if w < 0.0)
    gross = round(math.fsum(abs(w) for _, w in cleaned), 12)
    net = round(math.fsum(w for _, w in cleaned), 12)
    return TargetBook(
        decision_ns=int(decision_ns),
        status=status,
        weights=tuple(cleaned),
        longs=longs,
        shorts=shorts,
        carried_forward=carried,
        reason_code=None if reason is None else str(reason),
        diagnostics={
            **_json_safe_mapping(diagnostics_raw),
            "gross_realised": gross,
            "net_exposure": net,
            "n_legs": len(cleaned),
            "max_abs_weight": max((abs(w) for _, w in cleaned), default=0.0),
            "cap_max": float(cap_max),
        },
    )


def _pairs_to_mapping(body: Any) -> dict[str, float]:
    """Accept `{sym: w}`, `[[sym, w], ...]` or `(sym, w)` tuples."""
    out: dict[str, float] = {}
    if isinstance(body, Mapping):
        for sym, weight in body.items():
            key = str(sym)
            if key in out:
                raise ContractViolation(f"duplicate symbol in book: {key}")
            out[key] = float(weight)
        return out
    if isinstance(body, Sequence) and not isinstance(body, (str, bytes)):
        for entry in body:
            try:
                sym, weight = entry[0], entry[1]
            except (TypeError, IndexError) as exc:
                raise ContractViolation(
                    f"book entries must be [symbol, weight] pairs, got {entry!r}"
                ) from exc
            key = str(sym)
            if key in out:
                raise ContractViolation(f"duplicate symbol in book: {key}")
            out[key] = float(weight)
        return out
    if body in (None, [], {}):
        return {}
    raise ContractViolation(f"unsupported target book body: {type(body)!r}")


def _json_safe_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"value": str(value)}
    return {str(k): value[k] for k in sorted(value, key=str)}


def fill_payload_row(
    *,
    decision_ns: int,
    action: str,
    book: Optional[TargetBook],
    fills: Sequence[FillRecord],
    prior_weights: Mapping[str, float],
    new_weights: Mapping[str, float],
    cost_charged: Optional[float],
    carry_forward: bool,
) -> dict[str, Any]:
    """One boundary row of the BG2 scoring payload (fill-level truth attached)."""
    fills_out = []
    for record in fills:
        entry = record.as_dict()
        entry["signed_weight_change"] = round(
            float(new_weights.get(record.symbol, 0.0))
            - float(prior_weights.get(record.symbol, 0.0)),
            12,
        )
        fills_out.append(entry)
    return {
        "decision_ns": int(decision_ns),
        "action": action,
        "status": book.status if book is not None else STATUS_FORCE_FLAT,
        "reason_code": book.reason_code if book is not None else "force_flat_boundary",
        "carried_forward": bool(carry_forward),
        "weights": {
            sym: round(float(w), 12)
            for sym, w in sorted(new_weights.items())
            if float(w) != 0.0
        },
        "longs": [
            [sym, round(w, 12)] for sym, w in sorted(new_weights.items()) if w > 0.0
        ],
        "shorts": [
            [sym, round(w, 12)] for sym, w in sorted(new_weights.items()) if w < 0.0
        ],
        "prior_weights": {
            sym: round(float(w), 12)
            for sym, w in sorted(prior_weights.items())
            if float(w) != 0.0
        },
        "gross_realised": round(math.fsum(abs(w) for w in new_weights.values()), 12),
        "net_exposure": round(math.fsum(float(w) for w in new_weights.values()), 12),
        "turnover_one_side": round(
            math.fsum(
                abs(
                    float(new_weights.get(sym, 0.0)) - float(prior_weights.get(sym, 0.0))
                )
                for sym in set(new_weights) | set(prior_weights)
            ),
            12,
        ),
        "cost_charged": None if cost_charged is None else round(cost_charged, 12),
        "fills": fills_out,
    }


def build_portfolio_payload(rows: Iterable[Mapping[str, Any]], *, stress: StressSpec) -> dict[str, Any]:
    """Assemble the full BG2 portfolio/fill/scoring payload."""
    rows_out = [dict(row) for row in rows]
    gross_values = [row["gross_realised"] for row in rows_out]
    return {
        "stress": stress.signature(),
        "n_boundaries": len(rows_out),
        "rows": rows_out,
        "summary": {
            "gross_max": max(gross_values) if gross_values else 0.0,
            "gross_mean": round(sum(gross_values) / len(gross_values), 12)
            if gross_values
            else 0.0,
            "total_turnover_one_side": round(
                math.fsum(row["turnover_one_side"] for row in rows_out), 12
            ),
            "total_cost_charged": round(
                math.fsum(
                    float(row["cost_charged"] or 0.0)
                    for row in rows_out
                ),
                12,
            ),
            "skipped_boundaries": sum(1 for row in rows_out if row["carried_forward"]),
            "force_flat_present": any(
                row["action"] == STATUS_FORCE_FLAT for row in rows_out
            ),
        },
    }


def summarise_books(books: Sequence[TargetBook]) -> dict[str, Any]:
    """Fold-agnostic book census used inside deterministic artifacts."""
    if not books:
        return {"n_books": 0}
    return {
        "n_books": len(books),
        "n_long_legs": sum(len(book.longs) for book in books),
        "n_short_legs": sum(len(book.shorts) for book in books),
        "gross_min": round(min(_gross(book) for book in books), 12),
        "gross_max": round(max(_gross(book) for book in books), 12),
        "cap_breaches": [],
    }


def _gross(book: TargetBook) -> float:
    return math.fsum(abs(weight) for _, weight in book.weights)


__all__ = [
    "AdapterError",
    "BASELINE_PAYLOAD_STATUS_OK",
    "build_portfolio_payload",
    "fill_payload_row",
    "normalise_target_book",
    "summarise_books",
]

#: Kept for readability at import sites that only want the ok-status token.
BASELINE_PAYLOAD_STATUS_OK = BOOK_STATUS_OK
