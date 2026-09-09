"""Quality classification for canonical market events (frozen semantics).

Freeze authority: research/control/market_data_plane_v1_run/architecture_freeze.json
(sha256 7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02),
sections "reason_codes@1" and plans/PLAN_market_data_plane_v1.md section 6.4.

``evaluate(event, manifest_context, params)`` is a pure function of its three
inputs and returns ``(quality_status, reason_codes)``:

* sequence gaps are raised ONLY when the manifest declares
  ``sequence_semantics=CONTIGUOUS`` (with ``NONE`` a jump is not missing data);
* out-of-order delivery is flagged ONLY when the manifest declares
  ``ordered_delivery=true``;
* CROSSED_QUOTE applies inside ONE venue+instrument quote (this module
  evaluates a single event, so cross-venue disagreement can never be coded
  CROSSED_QUOTE — consolidated BBO contributors handle that, per the freeze);
* staleness is always an explicit threshold parameter (evaluation time and
  threshold are both required inputs; no hidden default);
* impossible time order is exchange_time > receive_time or receive_time >
  available_time;
* STATISTICAL_ANOMALY is diagnostic (suspect, never deletion): default rule
  flags |z| > 6 on log price change within instrument and event class — the
  recent reference prices for that instrument+event-class window are an
  explicit input (``QualityParams.recent_prices``), keeping evaluate() pure;
* DUPLICATE_EVENT is bookkeeping via :class:`DedupeIndex` (by event_id).

Rule evaluation order is deterministic (see ``_RULE_ORDER``); an event can
carry multiple codes.  Final status: INVALID if any rejection code, else
SUSPECT if any suspect code, else VALID.  Quarantine is decided by callers
(A3's quarantine store); this module only classifies.

No pandas/pandera/dvc/nautilus_trader import at module import time.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field

from . import reason_codes as _rc
from . import models as _models

__all__ = [
    "DedupeIndex",
    "QualityParams",
    "evaluate",
    "status_from_codes",
]


class DedupeIndex:
    """Small by-event_id duplicate index (bookkeeping for DUPLICATE_EVENT).

    Stream-scoped state owned by the caller and passed in through
    ``manifest_context["dedupe_index"]`` so that ``evaluate`` itself stays a
    pure function of its inputs plus this explicit state.
    """

    __slots__ = ("_seen",)

    def __init__(self, event_ids=()):
        self._seen = set(event_ids)

    def seen(self, event_id: str) -> bool:
        return event_id in self._seen

    def add(self, event_id: str) -> None:
        self._seen.add(event_id)

    def __len__(self) -> int:
        return len(self._seen)

    def __contains__(self, event_id: str) -> bool:
        return event_id in self._seen


@dataclass(frozen=True)
class QualityParams:
    """Explicit evaluation parameters (no hidden defaults where frozen).

    ``evaluation_time_ns`` and ``staleness_threshold_ns`` are REQUIRED — the
    staleness threshold is always an explicit input per the freeze.
    """

    evaluation_time_ns: int
    staleness_threshold_ns: int
    #: frozen default rule set flags |z| > 6
    anomaly_z_threshold: float = 6.0
    #: recent reference prices (floats, oldest..newest) for the same
    #: venue+instrument+event-class window; caller-supplied to keep purity
    recent_prices: tuple = ()
    #: minimum number of prior log-price changes required before a z-score is
    #: computed (below this the anomaly rule abstains, deterministically)
    min_anomaly_observations: int = 3
    #: explicit instrument registry set; None disables the check
    instrument_registry: frozenset = field(default=None)

    def __post_init__(self):
        if not isinstance(self.evaluation_time_ns, int) or \
                isinstance(self.evaluation_time_ns, bool):
            raise ValueError("evaluation_time_ns must be int UTC ns")
        if not isinstance(self.staleness_threshold_ns, int) or \
                isinstance(self.staleness_threshold_ns, bool) or \
                self.staleness_threshold_ns < 0:
            raise ValueError("staleness_threshold_ns must be int >= 0 (explicit)")
        if self.instrument_registry is not None and \
                not isinstance(self.instrument_registry, (set, frozenset)):
            raise ValueError("instrument_registry must be a set/frozenset or None")


#: Deterministic evaluation order (documentation of the frozen ordering below).
_RULE_ORDER = (
    "structural_validation",
    "IMPOSSIBLE_TIME_ORDER",
    "UNKNOWN_INSTRUMENT",
    "NEGATIVE_PRICE",
    "NEGATIVE_SIZE",
    "CROSSED_QUOTE",
    "STALE_QUOTE",
    "SEQUENCE_GAP/SEQUENCE_RESET/SOURCE_RESET_UNEVIDENCED",
    "OUT_OF_ORDER_DELIVERY",
    "DUPLICATE_EVENT",
    "STATISTICAL_ANOMALY",
)


def status_from_codes(reason_codes) -> str:
    """INVALID if any rejection code, else SUSPECT if any suspect, else VALID."""
    return _rc.final_status_for(reason_codes)


def evaluate(event, manifest_context, params: QualityParams):
    """Classify one event; return ``(quality_status, sorted_unique_codes)``.

    ``manifest_context`` is the explicit per-stream state dict; recognised
    keys (all optional):

    * ``sequence_semantics``: ``"CONTIGUOUS"`` or ``"NONE"`` (absent means the
      sequence rules do not apply);
    * ``ordered_delivery``: bool (absent/False disables OUT_OF_ORDER_DELIVERY);
    * ``last_sequence_number``: last sequence consumed from this stream;
    * ``sequence_reset_evidenced``: bool — when True a backwards sequence is
      coded SEQUENCE_RESET (suspect) instead of SOURCE_RESET_UNEVIDENCED
      (reject);
    * ``last_receive_time_ns``: receive time of the previous event in
      delivery order;
    * ``dedupe_index``: a :class:`DedupeIndex` instance.

    Purity: inputs ``event`` and ``manifest_context`` are never mutated (the
    DedupeIndex is explicit caller-owned state, not hidden mutation).
    """
    context = manifest_context if isinstance(manifest_context, dict) else {}

    # 1. Structural validation (construction-grade). A structurally invalid
    #    event fails with exactly the frozen reason code raised by models.
    try:
        canonical = _models.validate_event(event)
    except _models.MarketDataPlaneError as exc:
        return "INVALID", [exc.reason_code]

    codes: list[str] = []

    exchange_ns = canonical["exchange_time_utc_ns"]
    receive_ns = canonical["receive_time_utc_ns"]

    # 2. Impossible time order.
    if exchange_ns > receive_ns or receive_ns > canonical["available_time_utc_ns"]:
        codes.append("IMPOSSIBLE_TIME_ORDER")

    # 3. Unknown instrument (explicit registry parameter).
    registry = params.instrument_registry
    if registry is not None and canonical["instrument_id"] not in registry:
        codes.append("UNKNOWN_INSTRUMENT")

    # 4/5. Negative price / size (construction rejects these; re-check the
    #      canonical strings so evaluate() is safe on already-canonical input).
    for field_name in _models.PRICE_FIELDS:
        value = canonical[field_name]
        if value is not None and _models.decimal_string_to_decimal(value) < 0:
            codes.append("NEGATIVE_PRICE")
    for field_name in _models.SIZE_FIELDS:
        value = canonical[field_name]
        if value is not None and _models.decimal_string_to_decimal(value) < 0:
            codes.append("NEGATIVE_SIZE")

    # 6. Crossed quote: bid_price >= ask_price inside ONE venue+instrument.
    if canonical["event_type"] == "QUOTE":
        bid = _models.decimal_string_to_decimal(canonical["bid_price"])
        ask = _models.decimal_string_to_decimal(canonical["ask_price"])
        if bid >= ask:
            codes.append("CROSSED_QUOTE")

        # 7. Stale quote: explicit threshold at explicit evaluation time.
        age_ns = params.evaluation_time_ns - exchange_ns
        if age_ns > params.staleness_threshold_ns:
            codes.append("STALE_QUOTE")

    # 8. Sequence rules — only under declared CONTIGUOUS semantics.
    sequence_semantics = context.get("sequence_semantics")
    if sequence_semantics == "CONTIGUOUS":
        seq = canonical["sequence_number"]
        last_seq = context.get("last_sequence_number")
        if seq is None:
            codes.append("MANIFEST_MISMATCH")  # CONTIGUOUS declared, null sequence
        elif last_seq is not None:
            if seq > last_seq + 1:
                codes.append("SEQUENCE_GAP")
            elif seq <= last_seq:
                if context.get("sequence_reset_evidenced"):
                    codes.append("SEQUENCE_RESET")
                else:
                    codes.append("SOURCE_RESET_UNEVIDENCED")
    # sequence_semantics == NONE (or absent): a jump is not missing data.

    # 9. Out-of-order delivery — only when the manifest declares it ordered.
    if context.get("ordered_delivery") is True:
        last_receive = context.get("last_receive_time_ns")
        if last_receive is not None and receive_ns < last_receive:
            codes.append("OUT_OF_ORDER_DELIVERY")

    # 10. Duplicate bookkeeping via the explicit DedupeIndex.
    dedupe = context.get("dedupe_index")
    if isinstance(dedupe, DedupeIndex):
        if dedupe.seen(canonical["event_id"]):
            codes.append("DUPLICATE_EVENT")
        else:
            dedupe.add(canonical["event_id"])

    # 11. Statistical anomaly (diagnostic, never deletion): |z| > threshold on
    #     the log price change, within instrument and event class (the caller
    #     scopes recent_prices to that window).
    anomaly = _statistical_anomaly_code(canonical, params)
    if anomaly:
        codes.append(anomaly)

    codes = sorted(set(codes))
    return status_from_codes(codes), codes


def _statistical_anomaly_code(canonical: dict, params: QualityParams):
    """Return STATISTICAL_ANOMALY or None; deterministic, pure-python.

    Reference price: TRADE -> price; QUOTE -> exact Decimal mid of bid/ask.
    The latest log change is scored against the distribution of prior log
    changes built from ``params.recent_prices``.  Abstains (returns None)
    deterministically when there are fewer than
    ``params.min_anomaly_observations`` prior changes, when the prior
    dispersion is exactly zero (insufficient evidence), or when any relevant
    price is non-positive (log undefined).
    """
    if canonical["event_type"] == "TRADE":
        reference = _models.decimal_string_to_decimal(canonical["price"])
    elif canonical["event_type"] == "QUOTE":
        reference = _models.quote_mid(canonical["bid_price"], canonical["ask_price"])
    else:  # pragma: no cover - matrix only allows TRADE/QUOTE
        return None

    history = tuple(params.recent_prices)
    if len(history) < params.min_anomaly_observations + 1:
        return None

    reference_f = float(reference)
    if reference_f <= 0.0:
        return None
    changes = []
    for i in range(1, len(history)):
        prev_t, cur_t = float(history[i - 1]), float(history[i])
        if prev_t <= 0.0 or cur_t <= 0.0:
            return None
        changes.append(math.log(cur_t / prev_t))
    last_t = float(history[-1])
    if last_t <= 0.0:
        return None
    latest = math.log(reference_f / last_t)

    count = len(changes)
    mean = sum(changes) / count
    variance = sum((c - mean) ** 2 for c in changes) / count
    std = math.sqrt(variance)
    if std <= 0.0:
        return None  # no dispersion evidence: abstain, never guess
    z = (latest - mean) / std
    if abs(z) > params.anomaly_z_threshold:
        return "STATISTICAL_ANOMALY"
    return None


def classify_with_reason_codes(event, manifest_context, params: QualityParams) -> dict:
    """Convenience wrapper: return a new event dict carrying the evaluation.

    Uses :func:`models.set_quality` so the result stays canonical; quarantine
    remains a caller decision (status comes only from the frozen code classes).
    """
    status, codes = evaluate(event, manifest_context, params)
    return _models.set_quality(copy.deepcopy(event) if isinstance(event, dict) else event,
                               status, codes)


__all__.append("classify_with_reason_codes")
