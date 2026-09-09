"""Research transaction-cost analysis (MDP-V1 lane A4).

Frozen contract (``tca_contract`` and plans/PLAN_market_data_plane_v1.md
section 7.4):

- fills are INPUT EVIDENCE ONLY: this module measures executed prints against
  recorded quote/clock evidence.  It contains no order-placement concept and
  never routes, places, amends or cancels anything;
- metrics: ``arrival_mid`` = (bid+ask)/2 of the venue BBO at the decision
  timestamp (a recorded consolidated BBO is used only as an explicit fallback
  when no venue-local quote evidence exists); ``decision_to_fill_slippage_bps``
  = ``side_sign*(fill-arrival_mid)/arrival_mid*1e4``;
  ``effective_spread_bps`` = ``2*side_sign*(fill-mid_at_fill)/fill*1e4``;
  ``realized_spread_bps`` at the frozen horizons H in
  ``[1e9, 5e9, 3e10, 3e11]`` ns = ``2*side_sign*(fill-mid_at_fill_plus_H)/fill*1e4``;
  ``fill_ratio`` = filled_quantity/submitted_quantity; separate ``fees`` and
  ``funding_or_swap`` columns; ``impact_proxy_bps`` =
  ``side_sign*(mid_at_fill_plus_H - mid_at_fill)/mid_at_fill*1e4``;
- fees, funding and slippage remain separate columns before any total-cost
  view (:func:`total_cost_view` is the only place they are summed);
- NOT_EVALUABLE semantics: missing quote evidence, missing clock evidence,
  missing side, currency mismatch without conversion evidence, or missing fee
  evidence for fee-inclusive views each return a :class:`~.depth.NotEvaluable`
  sentinel for the AFFECTED METRIC ONLY.  Substituting zero is forbidden.

Arithmetic policy: every price/size/fee computation is ``decimal.Decimal``
parsed from the canonical decimal strings of the frozen envelope; ratios are
divided in Decimal and converted to float ONLY at the metric boundary (the
``*_bps`` output cells).  Each row also carries ``_decimal_bps``, the exact
Decimal ratio values, so :func:`total_cost_view` can sum costs without float
accumulation and convert only the final total.  ``mid`` values are exact
Decimals (dividing a decimal sum by 2 is exact) and are never floats.

Horizon/as-of conventions: the quote at a timestamp ``t`` (decision, fill, or
fill+H) is the deterministic venue-local winner with
``t - staleness_threshold_ns <= exchange_time_utc_ns <= t`` (both boundaries
inclusive -- horizon-boundary exactness), returned by
:func:`bbo.venue_asof_quote` with the REQUIRED ``staleness_threshold_ns``
parameter of the evaluation call.

Rows are returned sorted by ``fill_id`` so the whole result is invariant under
input permutation of the fills.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .bbo import parse_decimal, venue_asof_quote
from .depth import NotEvaluable

__all__ = [
    "REALIZED_SPREAD_HORIZONS_NS",
    "evaluate_tca",
    "total_cost_view",
    "REASON_MISSING_QUOTE_EVIDENCE",
    "REASON_MISSING_CLOCK_EVIDENCE",
    "REASON_MISSING_SIDE",
    "REASON_CURRENCY_MISMATCH",
    "REASON_MISSING_FEE_EVIDENCE",
    "REASON_MISSING_FILL_EVIDENCE",
    "REASON_MALFORMED_QUOTE_EVIDENCE",
    "REASON_MISSING_SUBMITTED_QUANTITY",
    "REASON_NO_EVALUABLE_FILLS",
]

# Frozen realized-spread horizons in nanoseconds.
REALIZED_SPREAD_HORIZONS_NS: Tuple[int, int, int, int] = (
    1_000_000_000,
    5_000_000_000,
    30_000_000_000,
    300_000_000_000,
)

_BPS = Decimal(10_000)

REASON_MISSING_QUOTE_EVIDENCE = "MISSING_QUOTE_EVIDENCE"
REASON_MISSING_CLOCK_EVIDENCE = "MISSING_CLOCK_EVIDENCE"
REASON_MISSING_SIDE = "MISSING_SIDE"
REASON_CURRENCY_MISMATCH = "CURRENCY_MISMATCH_NO_CONVERSION"
REASON_MISSING_FEE_EVIDENCE = "MISSING_FEE_EVIDENCE"
REASON_MISSING_FILL_EVIDENCE = "MISSING_FILL_EVIDENCE"
REASON_MALFORMED_QUOTE_EVIDENCE = "MALFORMED_QUOTE_EVIDENCE"
REASON_MISSING_SUBMITTED_QUANTITY = "MISSING_SUBMITTED_QUANTITY_EVIDENCE"
REASON_NO_EVALUABLE_FILLS = "NO_EVALUABLE_FILLS"

_SIDE_PLUS = frozenset({"buy", "b", "long", "1", 1})
_SIDE_MINUS = frozenset({"sell", "s", "short", "-1", -1})


def _side_sign(side: Any) -> Optional[int]:
    if isinstance(side, str):
        side = side.strip().lower()
    if side in _SIDE_PLUS:
        return 1
    if side in _SIDE_MINUS:
        return -1
    return None


def _int_or_none(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _currency_conflict(fill_currency: Any, evidence_currency: Any) -> bool:
    """True only on PROVEN mismatch; unknown (None) currency is unproven, not a mismatch."""
    return (
        fill_currency is not None
        and evidence_currency is not None
        and fill_currency != evidence_currency
    )


def _quote_mid(quote: Mapping[str, Any]) -> Decimal:
    """Exact (bid+ask)/2 from a QUOTE event dict; raises ValueError if malformed."""
    bid = parse_decimal(quote["bid_price"], "bid_price")
    ask = parse_decimal(quote["ask_price"], "ask_price")
    return (bid + ask) / 2  # exact: dividing a decimal sum by 2 terminates


def _recorded_consolidated_mid(recorded: Any) -> Decimal:
    """Mid from an explicitly recorded consolidated BBO evidence mapping."""
    if not isinstance(recorded, Mapping):
        raise ValueError("recorded consolidated evidence must be a mapping")
    return (
        parse_decimal(recorded["bid"], "consolidated_bid")
        + parse_decimal(recorded["ask"], "consolidated_ask")
    ) / 2


def _bps(num: Decimal, den: Decimal) -> Decimal:
    """Exact-input bps ratio; sign-normalised so exact zero is ``0`` not ``-0``."""
    value = (num / den) * _BPS
    if value == 0:
        return Decimal(0)
    return value


def _asof_mid(
    quotes: Sequence[Mapping[str, Any]],
    venue: Any,
    instrument_id: Any,
    at_ns: int,
    staleness_threshold_ns: int,
    fill_currency: Any,
) -> Tuple[Optional[Decimal], Optional[NotEvaluable]]:
    """Venue-local as-of mid, or (None, NotEvaluable) with the precise reason."""
    quote = venue_asof_quote(quotes, venue, instrument_id, at_ns, staleness_threshold_ns)
    if quote is None:
        return None, NotEvaluable(
            REASON_MISSING_QUOTE_EVIDENCE,
            f"no fresh venue quote for {(venue, instrument_id)} at t={at_ns}",
        )
    if _currency_conflict(fill_currency, quote.get("currency")):
        return None, NotEvaluable(
            REASON_CURRENCY_MISMATCH,
            f"fill currency {fill_currency!r} vs quote currency {quote.get('currency')!r}; "
            "no conversion evidence supplied",
        )
    try:
        return _quote_mid(quote), None
    except (KeyError, ValueError) as exc:
        return None, NotEvaluable(REASON_MALFORMED_QUOTE_EVIDENCE, str(exc))


def _evaluate_fill(
    fill: Mapping[str, Any],
    quotes: Sequence[Mapping[str, Any]],
    staleness_threshold_ns: int,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "fill_id": fill.get("fill_id"),
        "venue": fill.get("venue"),
        "instrument_id": fill.get("instrument_id"),
    }
    dec: Dict[str, Decimal] = {}
    row["_decimal_bps"] = dec

    # -- fill evidence -----------------------------------------------------
    price: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    try:
        if fill.get("price") is not None:
            price = parse_decimal(fill["price"], "fill_price")
        if fill.get("quantity") is not None:
            quantity = parse_decimal(fill["quantity"], "fill_quantity")
    except ValueError:
        price = quantity = None
    if price is None or quantity is None:
        fill_ne = NotEvaluable(
            REASON_MISSING_FILL_EVIDENCE, "fill price/quantity evidence missing or malformed"
        )
    else:
        fill_ne = None
    row["price"] = price if price is not None else fill_ne
    row["quantity"] = quantity if quantity is not None else fill_ne

    # -- clock and side evidence -------------------------------------------
    side_sign = _side_sign(fill.get("side"))
    decision_ns = _int_or_none(fill.get("decision_time_utc_ns"))
    fill_ns = _int_or_none(fill.get("fill_time_utc_ns"))

    # -- arrival mid (venue BBO; recorded consolidated fallback only) -------
    arrival_mid: Optional[Decimal] = None
    arrival_source: Any = None
    arrival_ne: Optional[NotEvaluable] = None
    if decision_ns is None:
        arrival_ne = NotEvaluable(
            REASON_MISSING_CLOCK_EVIDENCE, "decision_time_utc_ns missing or not integer ns"
        )
    else:
        mid, ne = _asof_mid(
            quotes,
            fill.get("venue"),
            fill.get("instrument_id"),
            decision_ns,
            staleness_threshold_ns,
            fill.get("currency"),
        )
        if mid is not None:
            arrival_mid, arrival_source = mid, "venue_quote"
        elif (
            ne is not None
            and ne.reason == REASON_MISSING_QUOTE_EVIDENCE
            and fill.get("consolidated_arrival_bbo") is not None
        ):
            # Consolidated fallback ONLY when recorded as explicit evidence.
            try:
                arrival_mid = _recorded_consolidated_mid(fill["consolidated_arrival_bbo"])
                arrival_source = "consolidated_recorded"
            except (KeyError, ValueError) as exc:
                arrival_ne = NotEvaluable(REASON_MALFORMED_QUOTE_EVIDENCE, str(exc))
        else:
            arrival_ne = ne
    row["arrival_mid"] = arrival_mid if arrival_mid is not None else arrival_ne
    row["arrival_mid_source"] = arrival_source

    # -- decision-to-fill slippage -----------------------------------------
    if side_sign is None:
        row["decision_to_fill_slippage_bps"] = NotEvaluable(
            REASON_MISSING_SIDE, f"unrecognised side evidence: {fill.get('side')!r}"
        )
    elif arrival_ne is not None and arrival_mid is None:
        row["decision_to_fill_slippage_bps"] = arrival_ne
    elif fill_ne is not None:
        row["decision_to_fill_slippage_bps"] = fill_ne
    else:
        value = _bps(side_sign * (price - arrival_mid), arrival_mid)
        dec["decision_to_fill_slippage_bps"] = value
        row["decision_to_fill_slippage_bps"] = float(value)

    # -- mid at fill + effective spread ------------------------------------
    mid_at_fill: Optional[Decimal] = None
    mid_fill_ne: Optional[NotEvaluable]
    if fill_ns is None:
        mid_fill_ne = NotEvaluable(
            REASON_MISSING_CLOCK_EVIDENCE, "fill_time_utc_ns missing or not integer ns"
        )
    else:
        mid_at_fill, mid_fill_ne = _asof_mid(
            quotes,
            fill.get("venue"),
            fill.get("instrument_id"),
            fill_ns,
            staleness_threshold_ns,
            fill.get("currency"),
        )
    row["mid_at_fill"] = mid_at_fill if mid_at_fill is not None else mid_fill_ne

    if side_sign is None:
        row["effective_spread_bps"] = NotEvaluable(REASON_MISSING_SIDE, "side evidence missing")
    elif mid_fill_ne is not None and mid_at_fill is None:
        row["effective_spread_bps"] = mid_fill_ne
    elif fill_ne is not None:
        row["effective_spread_bps"] = fill_ne
    else:
        value = _bps(2 * side_sign * (price - mid_at_fill), price)
        dec["effective_spread_bps"] = value
        row["effective_spread_bps"] = float(value)

    # -- realized spread and impact at the frozen horizons ------------------
    realized: Dict[int, Any] = {}
    impact: Dict[int, Any] = {}
    for horizon in REALIZED_SPREAD_HORIZONS_NS:
        if fill_ns is None:
            realized[horizon] = NotEvaluable(
                REASON_MISSING_CLOCK_EVIDENCE, "fill_time_utc_ns required for horizon lookup"
            )
            impact[horizon] = realized[horizon]
            continue
        mid_h, ne_h = _asof_mid(
            quotes,
            fill.get("venue"),
            fill.get("instrument_id"),
            fill_ns + horizon,
            staleness_threshold_ns,
            fill.get("currency"),
        )
        if mid_h is None:
            realized[horizon] = ne_h
            impact[horizon] = ne_h
            continue
        if side_sign is None:
            realized[horizon] = NotEvaluable(REASON_MISSING_SIDE, "side evidence missing")
            impact[horizon] = realized[horizon]
            continue
        if fill_ne is not None:
            realized[horizon] = fill_ne
            impact[horizon] = realized[horizon]
            continue
        realized[horizon] = float(_bps(2 * side_sign * (price - mid_h), price))
        dec[f"realized_spread_bps_{horizon}"] = _bps(2 * side_sign * (price - mid_h), price)
        if mid_at_fill is None:
            impact[horizon] = mid_fill_ne
            continue
        impact[horizon] = float(_bps(side_sign * (mid_h - mid_at_fill), mid_at_fill))
        dec[f"impact_proxy_bps_{horizon}"] = _bps(side_sign * (mid_h - mid_at_fill), mid_at_fill)
    row["realized_spread_bps"] = realized
    row["impact_proxy_bps"] = impact

    # -- fees and funding (separate columns, never zero-substituted) --------
    fee: Optional[Decimal] = None
    try:
        if fill.get("fee") is not None:
            fee = parse_decimal(fill["fee"], "fee")
    except ValueError:
        fee = None
    if fee is None:
        row["fees"] = NotEvaluable(
            REASON_MISSING_FEE_EVIDENCE, "fee evidence missing; zero must not be substituted"
        )
        row["fees_bps"] = row["fees"]
    elif _currency_conflict(fill.get("currency"), fill.get("fee_currency")):
        row["fees"] = fee
        row["fees_bps"] = NotEvaluable(
            REASON_CURRENCY_MISMATCH, "fee currency differs from fill currency without conversion"
        )
    elif fill_ne is not None:
        row["fees"] = fee
        row["fees_bps"] = NotEvaluable(
            REASON_MISSING_FILL_EVIDENCE, "fee bps need fill price/quantity notional"
        )
    else:
        row["fees"] = fee
        value = _bps(fee, price * quantity)
        dec["fees_bps"] = value
        row["fees_bps"] = float(value)

    funding: Optional[Decimal] = None
    try:
        if fill.get("funding_or_swap") is not None:
            funding = parse_decimal(fill["funding_or_swap"], "funding_or_swap")
    except ValueError:
        funding = None
    if funding is None:
        row["funding_or_swap"] = NotEvaluable(
            REASON_MISSING_FEE_EVIDENCE,
            "funding/swap evidence missing; zero must not be substituted",
        )
        row["funding_bps"] = row["funding_or_swap"]
    elif _currency_conflict(fill.get("currency"), fill.get("funding_currency")):
        row["funding_or_swap"] = funding
        row["funding_bps"] = NotEvaluable(
            REASON_CURRENCY_MISMATCH,
            "funding currency differs from fill currency without conversion",
        )
    elif fill_ne is not None:
        row["funding_or_swap"] = funding
        row["funding_bps"] = NotEvaluable(
            REASON_MISSING_FILL_EVIDENCE, "funding bps need fill price/quantity notional"
        )
    else:
        row["funding_or_swap"] = funding
        value = _bps(funding, price * quantity)
        dec["funding_bps"] = value
        row["funding_bps"] = float(value)

    return row


def evaluate_tca(
    fills: Sequence[Mapping[str, Any]],
    quotes: Sequence[Mapping[str, Any]],
    *,
    staleness_threshold_ns: int,
    submitted_quantity: Any = None,
) -> Dict[str, Any]:
    """Research TCA over input fill evidence and quote evidence.

    ``fills``: mappings with at least ``fill_id``, ``venue``, ``instrument_id``,
    ``side`` (buy/sell), ``price``, ``quantity`` (canonical decimal strings),
    ``decision_time_utc_ns`` and ``fill_time_utc_ns`` (integer ns clock
    evidence); optional ``fee``/``fee_currency``, ``funding_or_swap``/
    ``funding_currency``, and ``consolidated_arrival_bbo`` = recorded
    ``{"bid": ..., "ask": ...}`` consolidated evidence used ONLY as fallback
    when no venue-local quote exists at the decision timestamp.

    ``quotes``: QUOTE event dicts per the frozen envelope (used via the BBO
    module's deterministic as-of venue-local lookup).

    ``staleness_threshold_ns`` is REQUIRED (no default).  ``submitted_quantity``
    is the recorded submitted-size evidence for ``fill_ratio``; when absent,
    ``fill_ratio`` is NOT_EVALUABLE -- never zero, never guessed.

    Returns ``{"fills": [row, ...] sorted by fill_id, "fill_ratio": float|NotEvaluable,
    "realized_spread_horizons_ns": [...]}``.  Per-metric cells are floats
    (converted at the boundary after Decimal division), exact ``Decimal``
    amounts (arrival/mid/fees columns) or :class:`NotEvaluable` sentinels.
    """
    rows = [
        _evaluate_fill(fill, quotes, staleness_threshold_ns)
        for fill in sorted(fills, key=lambda f: str(f.get("fill_id")))
    ]
    total_filled = Decimal(0)
    any_quantity = False
    for fill in fills:
        try:
            if fill.get("quantity") is not None:
                total_filled += parse_decimal(fill["quantity"], "fill_quantity")
                any_quantity = True
        except ValueError:
            continue
    if not any_quantity or submitted_quantity is None:
        fill_ratio: Any = NotEvaluable(
            REASON_MISSING_SUBMITTED_QUANTITY,
            "submitted_quantity evidence (or filled quantities) missing",
        )
    else:
        try:
            submitted = parse_decimal(submitted_quantity, "submitted_quantity")
        except ValueError:
            fill_ratio = NotEvaluable(
                REASON_MISSING_SUBMITTED_QUANTITY, "submitted_quantity malformed"
            )
        else:
            fill_ratio = float(total_filled / submitted)
    return {
        "fills": rows,
        "fill_ratio": fill_ratio,
        "realized_spread_horizons_ns": list(REALIZED_SPREAD_HORIZONS_NS),
    }


def total_cost_view(
    tca_result: Mapping[str, Any],
    fees_included: bool = True,
    funding_included: bool = True,
) -> Dict[str, Any]:
    """Sum ONLY the evaluable cost columns; report every excluded column.

    The total per fill is ``decision_to_fill_slippage_bps + [fees_bps] +
    [funding_bps]`` -- effective/realized spread and the impact proxy are
    diagnostics and are deliberately never summed (double counting).  Exact
    Decimal components are summed from ``_decimal_bps`` and converted to float
    only at this final boundary.  A fill whose core slippage is not evaluable
    has no total (sentinel, never zero).

    ``fees_included``/``funding_included``=False excludes the column by request
    (reason ``EXCLUDED_BY_REQUEST``); when included but the evidence is missing
    the column is excluded with its evidence reason.  The aggregate is the
    fill-quantity-weighted mean over fills with an evaluable total, else
    ``NO_EVALUABLE_FILLS``.
    """
    excluded: List[Dict[str, Any]] = []
    included = ["decision_to_fill_slippage_bps"]
    if not fees_included:
        excluded.append({"column": "fees_bps", "reason": "EXCLUDED_BY_REQUEST"})
    else:
        included.append("fees_bps")
    if not funding_included:
        excluded.append({"column": "funding_bps", "reason": "EXCLUDED_BY_REQUEST"})
    else:
        included.append("funding_bps")

    per_fill: List[Dict[str, Any]] = []
    weighted_total = Decimal(0)
    weight_sum = Decimal(0)
    for row in tca_result.get("fills", []):
        slip_dec = row["_decimal_bps"].get("decision_to_fill_slippage_bps")
        fill_excluded: List[Dict[str, Any]] = []
        if slip_dec is None:
            core = row["decision_to_fill_slippage_bps"]
            per_fill.append(
                {
                    "fill_id": row.get("fill_id"),
                    "total_bps": NotEvaluable(
                        core.reason, "core decision-to-fill slippage not evaluable"
                    )
                    if isinstance(core, NotEvaluable)
                    else NotEvaluable(REASON_MISSING_QUOTE_EVIDENCE, "core slippage missing"),
                    "excluded": fill_excluded,
                }
            )
            continue
        components = [slip_dec]
        if fees_included:
            fee_dec = row["_decimal_bps"].get("fees_bps")
            if fee_dec is None:
                reason = (
                    row["fees_bps"].reason
                    if isinstance(row["fees_bps"], NotEvaluable)
                    else REASON_MISSING_FEE_EVIDENCE
                )
                excluded.append(
                    {"column": "fees_bps", "fill_id": row.get("fill_id"), "reason": reason}
                )
                fill_excluded.append({"column": "fees_bps", "reason": reason})
            else:
                components.append(fee_dec)
        if funding_included:
            fund_dec = row["_decimal_bps"].get("funding_bps")
            if fund_dec is None:
                reason = (
                    row["funding_bps"].reason
                    if isinstance(row["funding_bps"], NotEvaluable)
                    else REASON_MISSING_FEE_EVIDENCE
                )
                excluded.append(
                    {"column": "funding_bps", "fill_id": row.get("fill_id"), "reason": reason}
                )
                fill_excluded.append({"column": "funding_bps", "reason": reason})
            else:
                components.append(fund_dec)
        total = sum(components, Decimal(0))
        per_fill.append(
            {
                "fill_id": row.get("fill_id"),
                "total_bps": float(total),
                "excluded": fill_excluded,
            }
        )
        quantity = row.get("quantity")
        if isinstance(quantity, Decimal):
            weighted_total += total * quantity
            weight_sum += quantity

    aggregate: Any
    if weight_sum > 0:
        aggregate = float(weighted_total / weight_sum)
    else:
        aggregate = NotEvaluable(
            REASON_NO_EVALUABLE_FILLS, "no fill has both an evaluable total and a quantity"
        )
    return {
        "per_fill": per_fill,
        "excluded": excluded,
        "included_columns": included,
        "weighted_total_bps": aggregate,
    }
