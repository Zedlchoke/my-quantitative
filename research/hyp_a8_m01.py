"""V10 wave-I M01 panel family: ``A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL``.

Implementation-agent deliverable (wave I, PLAN.md section 8 I1). Binding spec
authority: ``research/audits/v10/proposals/a8_proposals_v10.{md,json}``
section 3 as integrated at commit ``77400df``, bound to freeze conditions
C1-C5 of ``research/control/v10_discovery_run/selection_freeze.json``. This
module implements ONLY what that spec prescribes -- nothing here reinterprets
a spec sentence. Ambiguities surface as fail-closed states or explicit reason
codes and are enumerated in ``research/audits/v10/i1_spec_trace.md``.

Mechanism (spec section 3): net aggressor-side order flow that failed to move
price marks an exhausted liquidity-consuming crowd; fade it with continuous
monotone dollar-neutral full-cross-section weights, retargeted once per UTC
calendar day, filled at the next allowed event after the last feature bar
closes, one UTC day holding horizon, always invested, force-flat at the final
scored-window boundary.

Observables (exactly two completed-bar series per symbol)::

    Q_i(D) = sum over block of quote_volume                  (total USDT notional)
    F_i(D) = sum over block of taker_buy_quote_volume / Q_i   in [0, 1]
    A_i(D) = 2 * F_i(D) - 1                                  in [-1, 1]

PIT convention (``research/pit_hooks_v10.py``): a bar's ``ts_event_ns`` IS its
exchange close stamp; blocks contain only bars whose close stamp lies in
``(D - 1d, D]``, so every contributing bar finished at-or-before the decision
instant ``D 00:00:00Z``. Reads come back sorted ascending by close stamp with
strict duplicate-close-stamp rejection. No forward fill anywhere, ever.

Constants derive from exactly four sources permitted by the spec discipline
(a8_proposals section 0): exchange/calendar facts, the frozen universe
manifest, preregistered transaction costs, and arithmetic risk bounds derived
from PLAN section 12 hard gates. There are NO free tuning parameters.

Arms shipped (frozen budget: anchor + neighbour + negative control):

* ``CONTROL_ANCHOR`` -- exactly section 3.6 (``M01-A``).
* ``NEIGHBOUR_PREWINDOW_DISPERSION`` -- ``M01-N`` (section 3.13).
* ``CONTROL_A8_SPEC_DAYMEAN`` -- the section 3.9 substitution realised exactly
  as written, INCLUDING the behaviour A7-N flagged as defective (see
  ``A7N_M01_CONTROL_DEFECT_QUOTE_VERBATIM``).
* ``CONTROL_C2_PRICE_CONTRARIAN_PLACEBO`` -- condition-C2 strengthening: the
  identical pipeline with the flow observable replaced by the negated
  standardised BLOCK PRICE MOVE, answering A7-N's named question ("whether
  flow adds anything over plain contrarian weighting of price") and therefore
  capable of flipping under participation-INDEPENDENT wide-range days.

No scoring happens here: the module emits target books, fill events, native
funding accrual spans and cost primitives. Scored execution stays in the
harness; nothing below reads or writes PnL/PF/drawdown.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pyarrow.parquet as pq

from research.data_audit_v10 import INTERVAL_NS
from research.panel import (
    _bar_type_dir,
    _decode_fixed16,
    _window_bounds_ns,
)

# --------------------------------------------------------------------------- #
# Frozen identity + structural constants (each traced in i1_spec_trace.md)
# --------------------------------------------------------------------------- #
FAMILY_ID = "A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL"
ANCHOR_CONFIG_ID = "M01-A"
NEIGHBOUR_CONFIG_ID = "M01-N"
SCHEMA_VERSION = "v10.hyp_a8_m01.v1"

#: 24h / 15min -- exchange-native bar grid fact (spec constant table, row 1).
BARS_PER_BLOCK = 96
BAR_INTERVAL_NS = INTERVAL_NS
DAY_NS = 86_400_000_000_000

#: Signal instants per scored year -- UTC calendar days in the scored window.
SIGNAL_INSTANTS_PER_YEAR = 365

#: MIN_ELIGIBLE = 8 of 10 (spec table row 3): keeps both sides of a capped
#: book diversified and the lambda bisection feasible.
MIN_ELIGIBLE = 8

#: CAP = 0.30 -- margin below the PLAN section 12 hard gate
#: "symbol contribution/risk <= 40%" (contract_v10.CAPS_V10 = 0.40).
CAP = 0.30

#: Unit-gross dollar-neutral book (spec table row 5).
GROSS_TARGET = 1.0

#: Audited pre-window slots consumed by neighbour M01-N (30 d x 96 bars).
PREWINDOW_SLOTS = 2880
PREWINDOW_DAYS = 30

#: Deterministic bisection bracket/tolerances quoted verbatim from step g.
LAMBDA_BRACKET_HIGH = 1e6
LAMBDA_MAX_HALVINGS = 200
GROSS_RESIDUAL_TOL = 1e-12

WEIGHT_ROUNDING_DECIMALS = 12

#: Preregistered cost floor (contract_v10 TAKER_FEE_FLOOR_BPS_V10 /
#: ADVERSE_TICKS_SLIPPAGE_FLOOR_V10); stricter frozen values remain allowed.
TAKER_FEE_FLOOR_BPS = 5.0
ADVERSE_TICK_SLIP_FLOOR = 1

WARMUP_DAYS_REQUIRED = 1  # 96 completed bars = 24 h (spec section 3.11)

#: C4 single-window discipline: fold boundaries come from the CONTRACT window
#: 00:00Z rule, NOT the measured 14:30Z variant (selection_freeze C4).
SCORED_WINDOW_START_UTC = "2025-08-21T00:00:00Z"
SCORED_WINDOW_END_UTC = "2026-08-21T00:00:00Z"
PREWINDOW_START_UTC = "2025-07-22T00:00:00Z"
PREWINDOW_END_UTC = SCORED_WINDOW_START_UTC

FROZEN_TRADING_COHORT: Tuple[str, ...] = (
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ENAUSDT",
    "SUIUSDT",
    "1000PEPEUSDT",
    "ADAUSDT",
    "BNBUSDT",
    "LINKUSDT",
)
#: Benchmark context ONLY: never a feature input, never a hedge leg.
BENCHMARK_SYMBOL_EXCLUDED = "BTCUSDT"

# --------------------------------------------------------------------------- #
# Verbatim quotations carried as named constants (no paraphrase permitted)
# --------------------------------------------------------------------------- #
SELECTION_FREEZE_C2_VERBATIM = (
    "C2 negative control strengthened per A7-N's named failure mode: the "
    "control must be capable of flipping under participation-INDEPENDENT "
    "wide-range days (the exact confound A7-N ruled the current design blind "
    "to); the strengthened control definition is authored into the frozen spec "
    "by A1 quoting a7n_challenge verbatim, NOT redesigned after results"
)

A7N_M01_CONTROL_DEFECT_QUOTE_VERBATIM = (
    "Control defect: substituting the cross-sectional day mean destroys "
    "symbol-specific variation but never asks whether flow adds anything over "
    "plain contrarian weighting of price -- the exact confusion that killed "
    "V9's residual proposal at 0.676. The specified control also degenerates "
    "into an all-long/all-short net-exposed book once lambda is bisected to "
    "gross 1.0, conflating market tilt with information loss."
)

A7N_M01_REQUIRED_BEFORE_FREEZE_QUOTE_VERBATIM = (
    "Required before freeze: strict-later-event fill clock fleet-wide (A8 "
    "fills at the open of the bar opening exactly at the decision instant; "
    "A9's uniform policy requires strictly later), weight-vector rank "
    "correlation against XSECT-WREV/XSECT-MOM, and ATT-TAKER-QV satisfied."
)

SPEC_NEGATIVE_CONTROL_SUBSTITUTION_QUOTE_VERBATIM = (
    "Replace per-symbol standardised imbalance with the cross-sectional day "
    "mean assigned to every symbol, i.e. destroy all symbol-specific "
    "variation while preserving the common market-wide flow component, then "
    "run the identical pipeline, standardisation, caps, clocks, fills and "
    "costs."
)

SPEC_FILL_CLOCK_QUOTE_VERBATIM = (
    "Fill clock: next allowed event after the signal bar completes, i.e. the "
    "OPEN of the 15-minute bar whose open timestamp equals D 00:00:00Z."
)

# --------------------------------------------------------------------------- #
# Arm vocabulary + statuses + eligibility reasons
# --------------------------------------------------------------------------- #
CONTROL_ANCHOR = "anchor"
CONTROL_A8_SPEC_DAYMEAN = "a8_spec_daymean"
CONTROL_C2_PRICE_CONTRARIAN_PLACEBO = "c2_price_contrarian_placebo"
CONTROL_MODES: Tuple[str, ...] = (
    CONTROL_ANCHOR,
    CONTROL_A8_SPEC_DAYMEAN,
    CONTROL_C2_PRICE_CONTRARIAN_PLACEBO,
)

NEIGHBOUR_CROSS_SECTIONAL_Z = "cross_sectional_z"
NEIGHBOUR_PREWINDOW_DISPERSION = "prewindow_dispersion"
NEIGHBOUR_MODES: Tuple[str, ...] = (
    NEIGHBOUR_CROSS_SECTIONAL_Z,
    NEIGHBOUR_PREWINDOW_DISPERSION,
)

FUNDING_SIGN_CONVENTION = "LONG_PAYS_POSITIVE_RATE"

STATUS_OK = "OK"
STATUS_SKIP_BELOW_MIN_ELIGIBLE = "SKIP_BELOW_MIN_ELIGIBLE"
STATUS_SKIP_INFEASIBLE_BOOK = "SKIP_INFEASIBLE_BOOK"
STATUS_SKIP_REQUIRE_ALL_FILLS = "SKIP_REBALANCE_REQUIRE_ALL_FILLS"
FORCE_FLAT_STATUS = "FORCE_FLAT"
FORCE_FLAT_REASON = "force_flat_final_scored_window_boundary"

INELIGIBLE_BLOCK_SIZE = "ineligible_block_size_not_96"
INELIGIBLE_NONPOSITIVE_QUOTE_VOLUME = "ineligible_nonpositive_quote_volume"
INELIGIBLE_FLOW_RATIO_OUT_OF_RANGE = "ineligible_flow_ratio_out_of_range"
INELIGIBLE_PREWINDOW_SIGMA_UNUSABLE = "ineligible_prewindow_sigma_unusable"


# --------------------------------------------------------------------------- #
# Fail-closed errors
# --------------------------------------------------------------------------- #
class CatalogUnavailable(KeyError):
    """A required symbol directory/part set is absent from the catalog tree."""


class DataIntegrityError(ValueError):
    """Bar stream violates integrity (duplicate stamps, non-finite values)."""


class BookInfeasibleError(ValueError):
    """The cap-bounded bisection cannot reach the unit-gross target."""


class SpecViolation(ValueError):
    """Caller arguments contradict the frozen spec (modes, brackets, caps)."""


# --------------------------------------------------------------------------- #
# Time helpers (mirrors research.panel semantics)
# --------------------------------------------------------------------------- #
def parse_iso_utc_ns(iso: str) -> int:
    """ISO-8601 UTC stamp/date -> epoch nanoseconds."""
    text = str(iso).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return calendar.timegm(dt.utctimetuple()) * 1_000_000_000 + dt.microsecond * 1000


def iso_from_ns(ns: int) -> str:
    dt = datetime.fromtimestamp(int(ns) // 1_000_000_000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_midnight_floor(ns: int) -> int:
    return (int(ns) // DAY_NS) * DAY_NS


def utc_midnight_ceil(ns: int) -> int:
    ns = int(ns)
    floor = (ns // DAY_NS) * DAY_NS
    return floor if floor == ns else floor + DAY_NS


def decision_days(*, window_start_iso: str, window_end_iso: str) -> List[int]:
    """UTC midnights D with ``window_start < D <= window_end``.

    Spec recipe step 2 ("for each UTC date D in [scored_start+1d,
    scored_end]") generalised to arbitrary ISO edges by taking whole UTC days;
    fold boundaries therefore never depend on a measured intraday window
    variant (freeze condition C4). Requires >= 2 instants: the renewable book
    must OPEN somewhere and be FORCE-FLATTENED at the final boundary.
    """
    start_ns, end_ns = _window_bounds_ns(window_start_iso, window_end_iso)
    first = utc_midnight_ceil(start_ns)
    last = utc_midnight_floor(end_ns)
    days = [d for d in range(first, last + 1, DAY_NS) if d > start_ns]
    if len(days) < 2:
        raise SpecViolation(
            "need at least two UTC boundaries (one open + final force-flat); got "
            f"{len(days)} inside [{window_start_iso}, {window_end_iso}]"
        )
    return days


def block_window_ns(decision_ns: int) -> Tuple[int, int]:
    """Exclusive-low / inclusive-high CLOSE-stamp bounds of block ``B(D)``."""
    d = int(decision_ns)
    if d % DAY_NS:
        raise SpecViolation(
            f"decision instant must be a UTC midnight, got {decision_ns}"
        )
    return d - DAY_NS, d


# --------------------------------------------------------------------------- #
# Immutable completed bar + reader (pyarrow-direct, research.panel idioms)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class M01Bar:
    """One completed 15m bar; ``ts_event_ns`` is its exchange CLOSE stamp."""

    ts_event_ns: int
    ts_init_ns: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    count: int
    taker_buy_quote_volume: float


_PRICE_COLS = ("open", "high", "low", "close", "volume")
_DECIMAL_STR_COLS = ("quote_volume", "taker_buy_quote_volume")
_COUNT_COL = "count"
_READ_COLUMNS = [
    *_PRICE_COLS,
    *_DECIMAL_STR_COLS,
    _COUNT_COL,
    "ts_event",
    "ts_init",
]


def _finite_decimal(raw: Any) -> float:
    try:
        value = float(str(raw))
    except (TypeError, ValueError) as exc:
        raise DataIntegrityError(f"unparsable decimal bar field: {raw!r}") from exc
    if not math.isfinite(value):
        raise DataIntegrityError(f"non-finite decimal bar field: {raw!r}")
    return value


def read_bars_15m(
    catalog_path: str | Path,
    symbol: str,
    window_start_iso: str,
    window_end_iso: str,
) -> Tuple[M01Bar, ...]:
    """Immutable completed-bar snapshot for ``symbol``, sorted by close stamp.

    Mirrors :func:`research.panel.load_bars_15m` layout/access while also
    carrying the aggressor-flow observables (``taker_buy_quote_volume``,
    ``quote_volume``) and trade ``count``. Duplicate close stamps are REJECTED
    (harness behaviour quoted by spec step 1); bars whose close stamp falls
    outside ``[start, end]`` are dropped, never shifted.
    """
    directory = Path(_bar_type_dir(catalog_path, str(symbol)))
    if not directory.exists():
        raise CatalogUnavailable(str(directory))
    files = sorted(directory.rglob("*.parquet"))
    if not files:
        raise CatalogUnavailable(f"no parquet parts under {directory}")
    start_ns, end_ns = _window_bounds_ns(window_start_iso, window_end_iso)
    by_ts: Dict[int, M01Bar] = {}
    for path in files:
        table = pq.read_table(path, columns=_READ_COLUMNS)
        cols = {name: table.column(name).to_pylist() for name in _READ_COLUMNS}
        for i, ts_raw in enumerate(cols["ts_event"]):
            ts_event = int(ts_raw)
            if ts_event < start_ns or ts_event > end_ns:
                continue
            if ts_event in by_ts:
                raise DataIntegrityError(
                    f"duplicate close stamp {ts_event} for {symbol}"
                )
            by_ts[ts_event] = M01Bar(
                ts_event_ns=ts_event,
                ts_init_ns=int(cols["ts_init"][i]),
                open=_decode_fixed16(cols["open"][i]),
                high=_decode_fixed16(cols["high"][i]),
                low=_decode_fixed16(cols["low"][i]),
                close=_decode_fixed16(cols["close"][i]),
                volume=_decode_fixed16(cols["volume"][i]),
                quote_volume=_finite_decimal(cols["quote_volume"][i]),
                taker_buy_quote_volume=_finite_decimal(
                    cols["taker_buy_quote_volume"][i]
                ),
                count=int(cols[_COUNT_COL][i]),
            )
    return tuple(by_ts[ts] for ts in sorted(by_ts))


def load_block_universe(
    catalog_path: str | Path,
    symbols: Sequence[str],
    *,
    window_start_iso: str,
    window_end_iso: str,
    warmup_days: int = WARMUP_DAYS_REQUIRED,
) -> Dict[str, Tuple[M01Bar, ...]]:
    """Bars per symbol over ``[floor(window_start) - warmup, window_end]``.

    Decision day D consumes the block ending AT D, so the earliest decision
    instant needs one completed day before the window edge. Everything read is
    still strictly-at-or-before the decision instant (PIT safe).
    """
    earliest_needed = utc_midnight_floor(
        parse_iso_utc_ns(window_start_iso)
    ) - int(warmup_days) * DAY_NS
    return {
        str(sym): read_bars_15m(
            catalog_path,
            str(sym),
            iso_from_ns(earliest_needed),
            window_end_iso,
        )
        for sym in symbols
    }


# --------------------------------------------------------------------------- #
# PIT assertions
# --------------------------------------------------------------------------- #
def assert_signal_pit(
    bars: Iterable[Any],
    *,
    decision_ns: int,
    context: str = "",
) -> None:
    """Every contributing bar closed at-or-before the decision instant."""
    decision = int(decision_ns)
    for bar in bars:
        close_ns = int(getattr(bar, "ts_event_ns"))
        if close_ns > decision:
            raise DataIntegrityError(
                f"lookahead{' in ' + context if context else ''}: bar close "
                f"{close_ns} after decision instant {decision}"
            )


# --------------------------------------------------------------------------- #
# Feature construction (spec steps 2b/2d + endpoint sanity check)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class SymbolDayFeature:
    """Per-symbol aggregates for one UTC-day block ``(D-1d, D]``."""

    symbol: str
    decision_ns: int
    n_bars: int
    quote_volume: float
    taker_buy_quote_volume: float
    imbalance_f: float
    imbalance_a: float
    block_open: float
    block_close: float
    block_move: float
    range_fraction: float  # sum((high-low)/close): participation-independent
    traded_value_proxy: float
    eligible: bool
    ineligible_reason: Optional[str]


def _daily_range_fraction(bars: Sequence[M01Bar]) -> float:
    return math.fsum(max(bar.high - bar.low, 0.0) / bar.close for bar in bars)


def _traded_value_proxy(bars: Sequence[M01Bar]) -> float:
    return math.fsum(bar.close * bar.volume for bar in bars)


def symbol_day_feature(
    bars: Sequence[M01Bar],
    symbol: str,
    decision_ns: int,
    *,
    prewindow_sigma: Optional[float] = None,
    require_prewindow_sigma: bool = False,
) -> SymbolDayFeature:
    """Aggregate one 96-slot block for one symbol.

    Eligibility applies in spec order: exactly ``BARS_PER_BLOCK`` completed
    bars, positive block quote volume, flow ratio inside [0, 1] up to float
    tolerance, and (neighbour arm only) a usable pinned pre-window dispersion.
    Block endpoints satisfy spec section 3.2's sanity-check requirement and
    NEVER enter the anchor sign.
    """
    lo_exclusive, hi_inclusive = block_window_ns(decision_ns)
    block = [b for b in bars if lo_exclusive < b.ts_event_ns <= hi_inclusive]

    qv = math.fsum(float(b.quote_volume) for b in block)
    tv = math.fsum(float(b.taker_buy_quote_volume) for b in block)
    block_open = float(block[0].open) if block else 0.0
    block_close = float(block[-1].close) if block else 0.0
    kwargs: Dict[str, Any] = {
        "symbol": str(symbol),
        "decision_ns": int(decision_ns),
        "n_bars": len(block),
        "quote_volume": qv,
        "taker_buy_quote_volume": tv,
        "imbalance_f": (tv / qv) if qv > 0.0 else 0.0,
        "imbalance_a": (2.0 * tv / qv - 1.0) if qv > 0.0 else 0.0,
        "block_open": block_open,
        "block_close": block_close,
        "block_move": (block_close / block_open - 1.0) if block_open > 0.0 else 0.0,
        "range_fraction": _daily_range_fraction(block),
        "traded_value_proxy": _traded_value_proxy(block),
        "eligible": False,
        "ineligible_reason": None,
    }

    def finish(**overrides: Any) -> SymbolDayFeature:
        payload = dict(kwargs)
        payload.update(overrides)
        return SymbolDayFeature(**payload)

    if len(block) != BARS_PER_BLOCK:
        return finish(ineligible_reason=INELIGIBLE_BLOCK_SIZE)

    assert_signal_pit(block, decision_ns=decision_ns, context=f"{symbol}@{decision_ns}")

    if not (math.isfinite(block_open) and math.isfinite(block_close)):
        raise DataIntegrityError(f"non-finite price endpoint for {symbol}")
    if not (math.isfinite(qv) and math.isfinite(tv)):
        raise DataIntegrityError(f"non-finite flow aggregate for {symbol}")

    if qv <= 0.0:
        return finish(ineligible_reason=INELIGIBLE_NONPOSITIVE_QUOTE_VOLUME)

    tol = 1e-9
    if kwargs["imbalance_f"] < -tol or kwargs["imbalance_f"] > 1.0 + tol:
        return finish(ineligible_reason=INELIGIBLE_FLOW_RATIO_OUT_OF_RANGE)

    if require_prewindow_sigma:
        sigma = None if prewindow_sigma is None else float(prewindow_sigma)
        if sigma is None or not math.isfinite(sigma) or sigma <= 0.0:
            return finish(ineligible_reason=INELIGIBLE_PREWINDOW_SIGMA_UNUSABLE)

    return finish(eligible=True)


# --------------------------------------------------------------------------- #
# Neighbour M01-N: hash-pinned pre-window flow dispersion
# --------------------------------------------------------------------------- #
def prewindow_sigma_i(
    bars: Sequence[M01Bar],
    *,
    prewindow_end_ns: int,
    prewindow_days: int = PREWINDOW_DAYS,
    slots_expected: Optional[int] = PREWINDOW_SLOTS,
) -> Optional[float]:
    """Sample stdev (ddof=1) of per-bar imbalance over the audited pre-window.

    ``a_b = 2*tqv_b/qv_b - 1`` over the ``2880`` censused slots strictly before
    ``prewindow_end_ns``. Bars with non-positive quote volume are skipped
    (never forward filled); any slot shortfall degrades to ``None`` so the name
    becomes ineligible that day instead of being silently renormalised.
    ``slots_expected=None`` accepts whatever complete slots exist (diagnostics
    only -- the scored neighbour always pins 2880).
    """
    edge = int(prewindow_end_ns)
    lower = edge - int(prewindow_days) * DAY_NS
    values: List[float] = []
    for bar in bars:
        if not lower < bar.ts_event_ns <= edge:
            continue
        if bar.quote_volume <= 0.0:
            continue
        values.append(2.0 * float(bar.taker_buy_quote_volume) / float(bar.quote_volume) - 1.0)
    if slots_expected is not None and len(values) != int(slots_expected):
        return None
    if len(values) < 2:
        return None
    sigma = statistics.stdev(values)  # sample stdev, ddof=1
    if not math.isfinite(sigma) or sigma <= 0.0:
        return None
    return float(sigma)


def prewindow_sigma_table(
    bars_by_symbol: Mapping[str, Sequence[M01Bar]],
    *,
    prewindow_end_ns: int,
    prewindow_days: int = PREWINDOW_DAYS,
) -> Dict[str, Any]:
    """Hash-pinned pre-window sigma table (computed ONCE, before any scoring)."""
    sigmas = {
        str(sym): prewindow_sigma_i(
            bars_by_symbol.get(str(sym)) or (),
            prewindow_end_ns=int(prewindow_end_ns),
            prewindow_days=int(prewindow_days),
        )
        for sym in sorted(bars_by_symbol)
    }
    return {
        "artifact": "m01_neighbour_prewindow_sigma_pin",
        "family_id": FAMILY_ID,
        "prewindow_end_ns": int(prewindow_end_ns),
        "prewindow_end_utc": iso_from_ns(int(prewindow_end_ns)),
        "prewindow_days": int(prewindow_days),
        "slots_expected": int(prewindow_days) * BARS_PER_BLOCK,
        "sigma_i": sigmas,
        "sha256": payload_sha256(sigmas),
    }


# --------------------------------------------------------------------------- #
# Deterministic serialisation / hashing (pit_hooks convention)
# --------------------------------------------------------------------------- #
def canonical_payload(obj: Any) -> str:
    """Byte-stable JSON via :func:`research.pit_hooks_v10.canonical_repr`."""
    from research.pit_hooks_v10 import canonical_repr

    return canonical_repr(obj)


def payload_sha256(obj: Any) -> str:
    """Deterministic content hash; two builds MUST agree byte-for-byte."""
    return hashlib.sha256(canonical_payload(obj).encode("utf-8")).hexdigest()


def canonical_json_text(obj: Any) -> str:
    """Canonical bytes as text (sorted keys, compact separators)."""
    return canonical_payload(obj)


def dump_json_artifact_text(payload: Mapping[str, Any], indent: int = 1) -> str:
    """Human-diffable sorted JSON for audit artifacts (tuples become arrays)."""
    return json.dumps(payload, indent=indent, sort_keys=True, default=str)


# --------------------------------------------------------------------------- #
# Lambda bisection (spec step g) + cap-bounded emission (step h)
# --------------------------------------------------------------------------- #
def solve_lambda(raw: Mapping[str, float], *, cap: float, gross: float) -> Tuple[float, float]:
    """Unique ``lambda >= 0`` with ``sum(|clip(lambda*raw, +-cap)|) == gross``.

    Bracket ``[0, 1e6]``, at most 200 halvings, stopping at the FIRST candidate
    whose constraint residual drops below ``1e-12`` -- all three literals taken
    verbatim from spec step g. Raises :class:`BookInfeasibleError` when the
    clipped-book capacity cannot reach gross (structurally prevented by
    ``MIN_ELIGIBLE``: capacity = cap x legs >= 0.30 x 8 = 2.4 > 1.0).
    """
    cap = float(cap)
    gross = float(gross)
    if gross <= 0.0:
        raise SpecViolation(f"gross target must be positive, got {gross}")
    if cap <= 0.0:
        raise SpecViolation(f"cap must be positive, got {cap}")
    magnitudes = [abs(float(v)) for v in raw.values()]
    active = [m for m in magnitudes if m > 0.0]
    if not active:
        raise BookInfeasibleError(
            f"every raw score is zero: clipped-book capacity 0 cannot reach gross {gross}"
        )

    def excess(lam: float) -> float:
        return math.fsum(min(lam * m, cap) for m in magnitudes) - gross

    lo, hi = 0.0, LAMBDA_BRACKET_HIGH
    if excess(hi) < 0.0:
        raise BookInfeasibleError(
            f"bracket upper bound {LAMBDA_BRACKET_HIGH} cannot reach gross {gross}"
        )
    residual = abs(excess(hi))
    for _ in range(LAMBDA_MAX_HALVINGS):
        mid = 0.5 * (lo + hi)
        if excess(mid) >= 0.0:
            hi = mid
        else:
            lo = mid
        residual = abs(excess(hi))
        if residual < GROSS_RESIDUAL_TOL:
            break
    if residual >= GROSS_RESIDUAL_TOL:
        raise BookInfeasibleError(
            f"lambda bisection exhausted {LAMBDA_MAX_HALVINGS} halvings with "
            f"residual {residual!r} not < {GROSS_RESIDUAL_TOL}"
        )
    return hi, residual


def emit_targets(
    raw: Mapping[str, float],
    *,
    cap: float = CAP,
    gross: float = GROSS_TARGET,
) -> Tuple[List[Tuple[str, float]], Dict[str, Any]]:
    """Clip a raw score vector into a cap-bounded unit-gross target book."""
    lam, residual = solve_lambda(raw, cap=cap, gross=gross)
    targets: List[Tuple[str, float]] = []
    for sym in sorted(raw):
        signed = max(-cap, min(cap, lam * float(raw[sym])))
        targets.append((sym, round(signed, WEIGHT_ROUNDING_DECIMALS)))
    diagnostics = {
        "lambda": lam,
        "gross_residual": residual,
        "gross_realised": round(
            math.fsum(abs(w) for _, w in targets), WEIGHT_ROUNDING_DECIMALS
        ),
        "net_exposure": round(math.fsum(w for _, w in targets), WEIGHT_ROUNDING_DECIMALS),
        "cap": cap,
        "max_abs_weight": max((abs(w) for _, w in targets), default=0.0),
        "clip_bound_active": any(abs(w) >= cap - 1e-15 for _, w in targets),
    }
    return targets, diagnostics


def cross_sectional_z(values: Mapping[str, float]) -> Dict[str, float]:
    """Sample-standardised copy (ddof=1); all zeros when stdev is exactly 0."""
    vals = {sym: float(v) for sym, v in values.items()}
    if len(vals) < 2:
        return {sym: 0.0 for sym in vals}
    mean = math.fsum(vals.values()) / len(vals)
    var = math.fsum((v - mean) ** 2 for v in vals.values()) / (len(vals) - 1)
    std = math.sqrt(var)
    if std == 0.0:
        return {sym: 0.0 for sym in vals}
    return {sym: (vals[sym] - mean) / std for sym in vals}


# --------------------------------------------------------------------------- #
# Raw scores (steps e-f) for every frozen arm
# --------------------------------------------------------------------------- #
def compute_day_signals(
    features: Mapping[str, SymbolDayFeature],
    *,
    control_mode: str = CONTROL_ANCHOR,
    neighbour_mode: str = NEIGHBOUR_CROSS_SECTIONAL_Z,
    prewindow_sigma: Optional[Mapping[str, Optional[float]]] = None,
) -> Dict[str, Any]:
    """Map per-symbol features to the raw score vector ``raw_i`` (steps e-g)."""
    if control_mode not in CONTROL_MODES:
        raise SpecViolation(
            f"control_mode must be one of {list(CONTROL_MODES)}, got {control_mode!r}"
        )
    if neighbour_mode not in NEIGHBOUR_MODES:
        raise SpecViolation(
            f"neighbour_mode must be one of {list(NEIGHBOUR_MODES)}, got {neighbour_mode!r}"
        )
    eligible = {str(s): f for s, f in sorted(features.items()) if f.eligible}
    detail: Dict[str, Any] = {
        "control_mode": control_mode,
        "neighbour_mode": neighbour_mode,
        "n_eligible": len(eligible),
        "raw": {},
        "notes": [],
    }
    if not eligible:
        detail["notes"].append("no_eligible_symbol_this_day")
        return detail

    if control_mode == CONTROL_A8_SPEC_DAYMEAN:
        # Section 3.9 substitution: ONE common level for every eligible name.
        # Deliberately NOT re-standardised: standardising a constant vector has
        # zero sample stdev, which would erase exactly the market-wide flow
        # component that spec sentence requires to survive. Trace doc DEV-01.
        day_mean = math.fsum(f.imbalance_a for f in eligible.values()) / len(eligible)
        detail["day_mean"] = day_mean
        detail["raw"] = {sym: day_mean for sym in eligible}
        detail["notes"].append("a8_spec_control_common_component_only")
        return detail

    if control_mode == CONTROL_C2_PRICE_CONTRARIAN_PLACEBO:
        # Condition-C2 strengthened control: identical pipeline, flow observable
        # replaced by negated standardised BLOCK PRICE MOVE, so it differs from
        # the anchor ONLY by whether FLOW carried information beyond plain
        # contrarian weighting of PRICE (A7-N's named confusion). Zero added
        # parameters, hence able to flip under participation-independent days.
        price_moves = {sym: f.block_move for sym, f in eligible.items()}
        z_price = cross_sectional_z(price_moves)
        detail["price_moves"] = price_moves
        detail["price_z"] = z_price
        detail["raw"] = {sym: -z_price[sym] for sym in eligible}
        detail["notes"].append("c2_strengthened_price_contrarian_placebo")
        return detail

    imbalances = {sym: feat.imbalance_a for sym, feat in eligible.items()}
    detail["imbalances"] = imbalances
    if neighbour_mode == NEIGHBOUR_PREWINDOW_DISPERSION:
        denom = _neighbour_denominators(eligible, prewindow_sigma or {})
        detail["denominators"] = denom
        detail["raw"] = {sym: -imbalances[sym] / denom[sym] for sym in eligible}
        detail["notes"].append("m01_n_prewindow_flow_dispersion_denominator")
        return detail

    z = cross_sectional_z(imbalances)
    detail["z_scores"] = z
    detail["raw"] = {sym: -z[sym] for sym in eligible}
    return detail


def _neighbour_denominators(
    eligible: Mapping[str, SymbolDayFeature],
    sigma_by_symbol: Mapping[str, Optional[float]],
) -> Dict[str, float]:
    """``sigma_i / sqrt(96)`` per eligible name, failing closed when unusable."""
    denom: Dict[str, float] = {}
    for sym in eligible:
        sigma = sigma_by_symbol.get(sym)
        if sigma is None or not math.isfinite(float(sigma)) or float(sigma) <= 0.0:
            raise SpecViolation(
                f"M01-N requires a pinned pre-window sigma for {sym}; none supplied"
            )
        denom[sym] = float(sigma) / math.sqrt(BARS_PER_BLOCK)
    return denom


def compute_targets(
    *,
    features: Mapping[str, SymbolDayFeature],
    control_mode: str = CONTROL_ANCHOR,
    neighbour_mode: str = NEIGHBOUR_CROSS_SECTIONAL_Z,
    prewindow_sigma: Optional[Mapping[str, Optional[float]]] = None,
    min_eligible: int = MIN_ELIGIBLE,
    cap: float = CAP,
    gross: float = GROSS_TARGET,
    reverse: bool = False,
) -> Dict[str, Any]:
    """Target book for ONE decision day, V9 runner-compatible shape.

    Returns ``{"status", "longs", "shorts", "weights", "diagnostics", ...}``.
    ``longs``/``shorts`` mirror the weekly/V9 ``[[symbol, weight], ...]``
    payload shape so the finalizer adopts this module without adapters;
    ``weights`` carries the novel continuous monotone geometry. Negative
    controls / neighbour select through ``control_mode``/``neighbour_mode``;
    ``reverse=True`` flips the sign end-to-end (runner idiom) and is NOT itself
    a negative control.
    """
    signals = compute_day_signals(
        features,
        control_mode=control_mode,
        neighbour_mode=neighbour_mode,
        prewindow_sigma=prewindow_sigma,
    )
    n_eligible = int(signals["n_eligible"])
    result: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "family_id": FAMILY_ID,
        "status": STATUS_OK,
        "n_eligible": n_eligible,
        "signals": signals,
        "carried_forward": False,
    }
    if n_eligible < int(min_eligible):
        result.update(
            status=STATUS_SKIP_BELOW_MIN_ELIGIBLE,
            reason_code=f"eligible_{n_eligible}_lt_min_{int(min_eligible)}",
            longs=[],
            shorts=[],
            weights=[],
            carried_forward=True,
            diagnostics={"gross_realised": 0.0, "net_exposure": 0.0},
        )
        return result

    raw = signals["raw"]
    if reverse:
        raw = {sym: -float(value) for sym, value in raw.items()}
    try:
        targets, diagnostics = emit_targets(raw, cap=cap, gross=gross)
    except BookInfeasibleError as exc:
        result.update(
            status=STATUS_SKIP_INFEASIBLE_BOOK,
            reason_code=str(exc),
            longs=[],
            shorts=[],
            weights=[],
            carried_forward=True,
            diagnostics={"gross_realised": 0.0, "net_exposure": 0.0},
        )
        return result

    weighted = [[sym, float(w)] for sym, w in targets]
    result.update(
        weights=[[sym, round(w, WEIGHT_ROUNDING_DECIMALS)] for sym, w in weighted],
        longs=[[sym, round(w, WEIGHT_ROUNDING_DECIMALS)] for sym, w in weighted if w > 0.0],
        shorts=[[sym, round(w, WEIGHT_ROUNDING_DECIMALS)] for sym, w in weighted if w < 0.0],
        diagnostics=diagnostics,
    )
    return result


# --------------------------------------------------------------------------- #
# Stress plumbing (PLAN section 11 cells become pure parameters here)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class StressParams:
    """Pre-declared stress surface in contract_v10.STRESS_MATRIX_V10 order.

    Defaults reproduce baseline exactly, so enabling a stress cell later is a
    pure parameter change needing NO code change.
    """

    fee_multiplier: float = 1.0                      # fee_slippage_x1_5 => 1.5
    tick_slip_ticks: int = ADVERSE_TICK_SLIP_FLOOR    # plus_2_ticks => floor + 2
    event_delay_events: int = 0                       # plus_1_event_delay => 1
    drop_symbols: Tuple[str, ...] = ()                # drop_one_symbol
    dropped_fold_index: Optional[int] = None          # drop_one_fold


def apply_stress_filter(
    symbols: Sequence[str],
    stress: Optional[StressParams] = None,
) -> List[str]:
    """Drop-one-symbol stress applied to the cohort (fail-closed on bad names)."""
    stress = stress or StressParams()
    known = [str(s) for s in symbols]
    dropped = [str(s) for s in stress.drop_symbols]
    unknown = sorted(set(dropped) - set(known))
    if unknown:
        raise SpecViolation(f"drop_one_symbol names outside the cohort: {unknown}")
    survivors = sorted(set(known) - set(dropped))
    if len(survivors) < MIN_ELIGIBLE:
        raise SpecViolation(
            f"drop_one_symbol leaves {len(survivors)} symbols < MIN_ELIGIBLE "
            f"{MIN_ELIGIBLE}; a capped book cannot stay diversified"
        )
    return survivors


def fill_cost_rate(
    *,
    price: float,
    tick_size: Optional[float],
    stress: Optional[StressParams] = None,
    taker_fee_bps: float = TAKER_FEE_FLOOR_BPS,
) -> float:
    """One-sided cost rate: taker fee (x multiplier) plus adverse tick slippage.

    Fail-closed when tick slippage is requested without a positive per-
    instrument tick size -- ticks are never invented.
    """
    stress = stress or StressParams()
    if not (math.isfinite(price) and price > 0.0):
        raise SpecViolation(f"fill price must be finite-positive, got {price!r}")
    ticks = int(stress.tick_slip_ticks)
    rate = float(taker_fee_bps) * 1e-4 * float(stress.fee_multiplier)
    if ticks:
        size = None if tick_size is None else float(tick_size)
        if size is None or not (math.isfinite(size) and size > 0.0):
            raise SpecViolation(
                "tick slippage requested without a positive per-instrument tick_size"
            )
        rate += ticks * size / float(price)
    return rate


def traded_notional(prev: Mapping[str, float], new: Mapping[str, float]) -> float:
    """One-side traded notional ``sum_i |w_new,i - w_prev,i|`` (flats included)."""
    keys = set(prev) | set(new)
    return math.fsum(
        abs(float(new.get(k, 0.0)) - float(prev.get(k, 0.0))) for k in keys
    )


def rebalance_cost(
    prev: Mapping[str, float],
    new: Mapping[str, float],
    *,
    prices: Mapping[str, float],
    tick_sizes: Optional[Mapping[str, float]] = None,
    stress: Optional[StressParams] = None,
    taker_fee_bps: float = TAKER_FEE_FLOOR_BPS,
) -> float:
    """Baseline cost charged once per side on the traded notional, per unit gross."""
    stress = stress or StressParams()
    total = 0.0
    for sym in sorted(set(prev) | set(new)):
        delta = abs(float(new.get(sym, 0.0)) - float(prev.get(sym, 0.0)))
        if delta == 0.0:
            continue
        if sym not in prices:
            raise SpecViolation(f"missing fill price for traded symbol {sym}")
        total += delta * fill_cost_rate(
            price=float(prices[sym]),
            tick_size=(tick_sizes or {}).get(sym),
            stress=stress,
            taker_fee_bps=taker_fee_bps,
        )
    return total


def chronological_folds(
    decision_days_seq: Sequence[int],
    *,
    folds: int = 3,
    stress: Optional[StressParams] = None,
    purge_days: int = WARMUP_DAYS_REQUIRED,
) -> List[Tuple[int, str, List[int]]]:
    """Contiguous chronological thirds with purge >= one holding period.

    Purge strips the trailing ``purge_days`` decision instants of each fold so
    a book opened inside fold k can never consume a fill belonging to fold k+1
    (purge >= holding horizon per contract). ``stress.dropped_fold_index``
    implements the ``drop_one_fold`` cell.
    """
    days = sorted(int(d) for d in decision_days_seq)
    n = int(folds)
    if n < 1 or len(days) < n + 1:
        raise SpecViolation(
            f"cannot form {n} folds with purge {purge_days} from {len(days)} decision days"
        )
    edges = [round(i * len(days) / n) for i in range(n + 1)]
    out: List[Tuple[int, str, List[int]]] = []
    for idx in range(n):
        stop = max(edges[idx] + 1, edges[idx + 1] - purge_days)
        members = days[edges[idx]:stop]
        label = f"F{idx + 1}"
        if (
            stress is not None
            and stress.dropped_fold_index is not None
            and idx == int(stress.dropped_fold_index)
        ):
            continue
        if not members:
            raise SpecViolation(f"fold {label} empty after purge={purge_days}")
        out.append((idx, label, members))
    return out


# --------------------------------------------------------------------------- #
# Fill-event clock (spec sections 3.4 and 3.6 step 3)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class FillEvent:
    """The single synchronous fill event for one symbol at one rebalance."""

    symbol: str
    decision_ns: int
    fill_open_ns: int       # OPEN stamp of the executed bar
    fill_bar_close_ns: int  # close stamp of the executed bar
    event_offset: int       # 0 = the bar opening exactly at the boundary
    price: float            # taker fill at that open


def bar_open_ns(bar: M01Bar) -> int:
    """Derived OPEN stamp of a close-stamped bar (repo PIT convention)."""
    return int(bar.ts_event_ns) - BAR_INTERVAL_NS


def resolve_fill_event(
    bars: Sequence[M01Bar],
    symbol: str,
    *,
    decision_ns: int,
    event_delay_events: int = 0,
) -> Optional[FillEvent]:
    """Locate the bar whose open equals the decision instant; walk delays.

    Spec fill clock: OPEN of the 15m bar opening at ``D 00:00:00Z``. Real close
    stamps sit a shave before the nominal grid line, so the covering bar is
    identified by interval containment ``derived_open <= D < close``: identical
    to "first bar closing after D" on a gapless tape, and yielding NO event --
    never a shifted substitute -- when the opening slot is missing. Non-zero
    ``event_delay_events`` walks exactly that many further allowed events
    (PLAN section 11 stress cell).
    """
    delay = int(event_delay_events)
    if delay < 0:
        raise SpecViolation("event_delay_events must be >= 0")
    decision = int(decision_ns)
    ordered = sorted(bars, key=lambda b: int(b.ts_event_ns))
    start_idx: Optional[int] = None
    for idx, bar in enumerate(ordered):
        if bar_open_ns(bar) <= decision < int(bar.ts_event_ns):
            start_idx = idx
            break
    if start_idx is None or start_idx + delay >= len(ordered):
        return None
    chosen = ordered[start_idx + delay]
    return FillEvent(
        symbol=str(symbol),
        decision_ns=decision,
        fill_open_ns=bar_open_ns(chosen),
        fill_bar_close_ns=int(chosen.ts_event_ns),
        event_offset=delay,
        price=float(chosen.open),
    )


# --------------------------------------------------------------------------- #
# Native funding accrual hook (spec step 4; settlements injected as fixture)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class HoldingSpan:
    """Signed weight held over ``(start_ns, end_ns]`` for one symbol."""

    symbol: str
    signed_weight: float
    start_ns: int
    end_ns: int


@dataclass(frozen=True, slots=True)
class FundingCashflow:
    """Native accrual for one settlement instant and one held leg."""

    symbol: str
    settle_ts_ns: int
    rate: float
    signed_weight: float
    cashflow_per_unit_capital: float
    sign_convention: str = FUNDING_SIGN_CONVENTION


def normalize_settlements(settlements: Iterable[Any]) -> Tuple[Any, ...]:
    """Validate/coerce a native settlement series through the shared PIT hook."""
    from research.pit_hooks_v10 import normalize_info_series

    return normalize_info_series(list(settlements))


def funding_cashflows(
    holdings: Sequence[HoldingSpan],
    settlements: Iterable[Any],
) -> List[FundingCashflow]:
    """Accrue native funding on every leg held across each settlement instant.

    Settlements form an injected native series (exchange-stamped, strict
    duplicate rejection, ascending) validated by
    :func:`research.pit_hooks_v10.normalize_info_series`. Only instants
    strictly inside ``(start_ns, end_ns]`` accrue, mirroring spec step 4
    ("whatever legs remain held"). Sign convention LONG_PAYS_POSITIVE_RATE =>
    ``cashflow = -weight * rate`` per unit of unit-gross capital. The mark-price
    overlay is UNAVAILABLE for this universe (spec section 2.5), so the basis is
    the boundary-weighted book itself -- trace doc approximation note AMB-03.
    """
    points = normalize_settlements(settlements)
    flows: List[FundingCashflow] = []
    for point in points:
        for span in holdings:
            if not (span.start_ns < point.publish_ts_ns <= span.end_ns):
                continue
            weight = float(span.signed_weight)
            if weight == 0.0:
                continue
            flows.append(
                FundingCashflow(
                    symbol=str(span.symbol),
                    settle_ts_ns=int(point.publish_ts_ns),
                    rate=float(point.value),
                    signed_weight=weight,
                    cashflow_per_unit_capital=-weight * float(point.value),
                )
            )
    flows.sort(key=lambda f: (f.settle_ts_ns, f.symbol))
    return flows


def derive_holding_spans(rows: Sequence[Mapping[str, Any]]) -> List[HoldingSpan]:
    """Collapse a schedule into ``(symbol, weight, start, end)`` accrual spans.

    Only APPLIED fill events create/span boundaries, so a skipped (carried)
    rebalance never truncates a span. A boundary whose fills were REFUSED (for
    example the final force-flat finding no event) still CLOSES the legs held
    until then: the closing edge falls back to ``decision_ns + one bar`` because
    the legs demonstrably survived that far and native accrual cannot be left
    unbounded (trace doc AMB-06).
    """
    spans: List[HoldingSpan] = []
    live: Dict[str, float] = {}
    start: Optional[int] = None

    def close_legs(end_ns: int) -> None:
        for sym, weight in sorted(live.items()):
            if float(weight) != 0.0:
                spans.append(HoldingSpan(str(sym), float(weight), int(start), int(end_ns)))

    for row in rows:
        fills = list(row.get("fills") or [])
        applied = [entry for entry in fills if entry.get("applied")]
        stamps = [int(e["fill_open_ns"]) for e in fills if "fill_open_ns" in e]
        if applied and stamps:
            boundary_open = min(
                int(e["fill_open_ns"])
                for e in applied
                if "fill_open_ns" in e
            )
        elif stamps:
            boundary_open = min(stamps)
        else:
            boundary_open = int(row["decision_ns"]) + BAR_INTERVAL_NS
        if start is not None and (applied or row.get("status") in (FORCE_FLAT_STATUS, STATUS_SKIP_REQUIRE_ALL_FILLS)):
            close_legs(boundary_open)
            live = {}
            start = None
        if applied:
            live = {
                str(sym): float(weight)
                for sym, weight in (row.get("weights") or [])
            }
            start = boundary_open
    if start is not None:
        close_legs(int(start))  # degenerate zero-length guard, never expected
    return spans


# --------------------------------------------------------------------------- #
# C2 strengthened-control diagnostics (participation-independent strata)
# --------------------------------------------------------------------------- #
PARTICIPATION_RANGE_KEY = "range_fraction"
STRATUM_SPLIT_RULE = "median_of_daily_cross_sectional_mean_range_fraction"
STRATA_DIAGNOSTIC_NOTE = (
    "post-hoc diagnostic only; never touches signals, weights, fills or costs"
)


def split_days_by_participation(
    day_records: Mapping[int, Mapping[str, float]],
    *,
    value_key: str = PARTICIPATION_RANGE_KEY,
) -> Tuple[List[int], List[int]]:
    """Split decision days at the deterministic median of a participation-
    independent price-geometry statistic (default ``range_fraction``).

    Diagnostic only: no stratum boundary enters the scored pipeline, and credit
    requires BOTH strata to agree. Trace doc AMB-04 records that the specific
    split rule was not fixed by the frozen spec; the median is used because it
    is the unique rank statistic requiring no parameter.
    """
    days = sorted(int(d) for d in day_records)
    values = sorted(float(day_records[d][value_key]) for d in days)
    if len(values) < 2:
        return list(days), []
    mid = len(values) // 2
    median = values[mid] if len(values) % 2 else 0.5 * (values[mid - 1] + values[mid])
    low = [d for d in days if float(day_records[d][value_key]) <= median]
    high = [d for d in days if float(day_records[d][value_key]) > median]
    return low, high


def stratified_expectancy(
    day_pnl: Mapping[int, float],
    strata: Sequence[Sequence[int]],
) -> Dict[str, Any]:
    """Mean unit-gross expectancy per stratum plus a wide-range flip verdict."""
    labels = ("low_participation", "high_wide_range")
    means: List[Optional[float]] = []
    entries: List[Dict[str, Any]] = []
    for idx, members in enumerate(strata):
        members_list = [int(d) for d in members]
        if not members_list:
            means.append(None)
            entries.append({"label": labels[idx], "n_days": 0, "mean": None})
            continue
        mean = math.fsum(float(day_pnl[d]) for d in members_list) / len(members_list)
        means.append(mean)
        entries.append({"label": labels[idx], "n_days": len(members_list), "mean": mean})
    populated = [m for m in means if m is not None]
    sign_flip = len(populated) == 2 and (populated[0] > 0.0) != (populated[1] > 0.0)
    return {"strata": entries, "sign_flip": sign_flip}


def wide_range_flip_probe(
    *,
    day_pnl: Mapping[int, float],
    day_records: Mapping[int, Mapping[str, float]],
    value_key: str = PARTICIPATION_RANGE_KEY,
) -> Dict[str, Any]:
    """Can this arm's expectancy flip on participation-INDEPENDENT wide ranges?

    Condition C2 demands a negative control capable of flipping under such
    days; this probe reports flip capability for whichever arm's day-level
    expectancy is handed in (anchor, day-mean control or price placebo).
    """
    low, high = split_days_by_participation(day_records, value_key=value_key)
    probe = stratified_expectancy(day_pnl, (low, high))
    probe.update(
        {
            "probe": "wide_range_flip_capability",
            "value_key": value_key,
            "split_rule": STRATUM_SPLIT_RULE,
            "diagnostic_note": STRATA_DIAGNOSTIC_NOTE,
            "low_participation_days": low,
            "high_wide_range_days": high,
            "credit_rule": (
                "control materially degrades only if BOTH strata degrade; a sign "
                "flip invalidates participation independence"
            ),
        }
    )
    return probe


def daily_cross_section_records(
    features_by_day: Mapping[int, Mapping[str, SymbolDayFeature]],
) -> Dict[int, Dict[str, float]]:
    """Diagnostic per-day cross-sectional aggregates from feature objects."""
    records: Dict[int, Dict[str, float]] = {}
    for day, feats in sorted(features_by_day.items()):
        eligible = [f for f in feats.values() if f.eligible]
        if not eligible:
            records[int(day)] = {
                "n_eligible": 0.0,
                "mean_range_fraction": 0.0,
                "mean_abs_imbalance": 0.0,
                "mean_abs_block_move": 0.0,
            }
            continue
        records[int(day)] = {
            "n_eligible": float(len(eligible)),
            "mean_range_fraction": math.fsum(f.range_fraction for f in eligible)
            / len(eligible),
            "mean_abs_imbalance": math.fsum(abs(f.imbalance_a) for f in eligible)
            / len(eligible),
            "mean_abs_block_move": math.fsum(abs(f.block_move) for f in eligible)
            / len(eligible),
        }
    return records


# --------------------------------------------------------------------------- #
# Rebalance driver: features -> books -> fills -> carry -> force-flat
# --------------------------------------------------------------------------- #
def build_rebalance_schedule(
    *,
    bars_by_symbol: Mapping[str, Sequence[M01Bar]],
    window_start_iso: str,
    window_end_iso: str,
    control_mode: str = CONTROL_ANCHOR,
    neighbour_mode: str = NEIGHBOUR_CROSS_SECTIONAL_Z,
    prewindow_end_ns: Optional[int] = None,
    prewindow_sigma: Optional[Mapping[str, Optional[float]]] = None,
    stress: Optional[StressParams] = None,
    min_eligible: int = MIN_ELIGIBLE,
    cap: float = CAP,
    gross: float = GROSS_TARGET,
    require_all_fills: bool = True,
) -> Dict[str, Any]:
    """Full deterministic daily rebalance schedule over the scored window.

    Decision days ``D_1..D_n``: books OPEN at ``D_1..D_{n-1}``; the FINAL
    scored-window boundary ``D_n`` FORCE-FLATTENS everything with the same
    next-event fill convention (spec steps 3 and 5). When any leg cannot trade
    at its allowed event and ``require_all_fills`` is set, the whole rebalance
    is skipped and prior weights carried unchanged -- the same fail-closed
    treatment as the MIN_ELIGIBLE branch. Nothing here evaluates PnL/PF/MDD.
    """
    stress = stress or StressParams()
    cohort = apply_stress_filter(sorted(bars_by_symbol), stress)
    all_days = decision_days(
        window_start_iso=window_start_iso, window_end_iso=window_end_iso
    )
    open_days, final_boundary = all_days[:-1], all_days[-1]

    sigma_table = dict(prewindow_sigma) if prewindow_sigma is not None else None
    if neighbour_mode == NEIGHBOUR_PREWINDOW_DISPERSION and sigma_table is None:
        edge = int(prewindow_end_ns) if prewindow_end_ns is not None else int(open_days[0])
        sigma_table = {
            sym: prewindow_sigma_i(bars_by_symbol.get(sym) or (), prewindow_end_ns=edge)
            for sym in cohort
        }

    state: Dict[str, Any] = {"weights": {}, "skips": 0}
    rows: List[Dict[str, Any]] = []
    unfilled_symbols: List[str] = []

    def execute_trades(day: int, new_weights: Mapping[str, float]) -> List[Dict[str, Any]]:
        """One synchronous fill sweep at the next allowed event per leg."""
        current_weights: Dict[str, float] = dict(state["weights"])
        fills: List[Dict[str, Any]] = []
        for sym in sorted(set(new_weights) | set(current_weights)):
            target = float(new_weights.get(sym, 0.0))
            current = float(current_weights.get(sym, 0.0))
            event = resolve_fill_event(
                bars_by_symbol.get(sym) or (),
                sym,
                decision_ns=day,
                event_delay_events=stress.event_delay_events,
            )
            entry: Dict[str, Any] = {
                "symbol": str(sym),
                "decision_ns": int(day),
                "target_weight": round(target, WEIGHT_ROUNDING_DECIMALS),
                "prior_weight": round(current, WEIGHT_ROUNDING_DECIMALS),
                "event_delay_events": int(stress.event_delay_events),
                "status": "NO_EVENT_AT_BOUNDARY",
                "applied": False,
            }
            if event is None:
                unfilled_symbols.append(str(sym))
            else:
                entry.update(
                    {
                        "status": "FILLED_NEXT_EVENT",
                        "fill_open_ns": int(event.fill_open_ns),
                        "fill_bar_close_ns": int(event.fill_bar_close_ns),
                        "event_offset": int(event.event_offset),
                        "price": event.price,
                        "signed_weight_change": round(
                            target - current, WEIGHT_ROUNDING_DECIMALS
                        ),
                        "applied": True,
                    }
                )
            fills.append(entry)
        # An empty sweep carries no leg, so it cannot miss an event either;
        # counting it as a skip would double-count an already-skipped day.
        complete = bool(fills) and all(e["status"] == "FILLED_NEXT_EVENT" for e in fills)
        if fills and not complete and require_all_fills:
            state["skips"] = int(state["skips"]) + 1
            for entry in fills:
                entry["applied"] = False
                entry["skip_reason"] = STATUS_SKIP_REQUIRE_ALL_FILLS
        return fills

    for index, day in enumerate(open_days):
        day_features = {
            str(sym): symbol_day_feature(
                bars_by_symbol.get(sym) or (),
                str(sym),
                day,
                prewindow_sigma=(
                    None if sigma_table is None else sigma_table.get(str(sym))
                ),
                require_prewindow_sigma=(
                    neighbour_mode == NEIGHBOUR_PREWINDOW_DISPERSION
                ),
            )
            for sym in cohort
        }
        book = compute_targets(
            features=day_features,
            control_mode=control_mode,
            neighbour_mode=neighbour_mode,
            prewindow_sigma=sigma_table,
            min_eligible=min_eligible,
            cap=cap,
            gross=gross,
        )
        note: Optional[str] = None
        status = book["status"]
        skips_before = int(state["skips"])
        if book["carried_forward"]:
            state["skips"] = skips_before + 1
            note = book.get("reason_code") or book["status"]
            new_weights = dict(state["weights"])
            fills: List[Dict[str, Any]] = []
        else:
            proposed = {sym: float(w) for sym, w in book["weights"]}
            fills = execute_trades(day, proposed)
            if int(state["skips"]) > skips_before:
                note = STATUS_SKIP_REQUIRE_ALL_FILLS
                status = STATUS_SKIP_REQUIRE_ALL_FILLS
                new_weights = dict(state["weights"])
            else:
                new_weights = proposed

        rows.append(
            {
                "day_index": index,
                "action": "OPEN_REBALANCE",
                "decision_ns": int(day),
                "date_utc": iso_from_ns(int(day))[:10],
                "status": status,
                "reason_code": note,
                "n_eligible": book["n_eligible"],
                "weights": [
                    [str(sym), round(float(w), WEIGHT_ROUNDING_DECIMALS)]
                    for sym, w in sorted(new_weights.items())
                ],
                "fills": fills,
                "turnover_one_side": round(
                    traded_notional(dict(state["weights"]), new_weights),
                    WEIGHT_ROUNDING_DECIMALS,
                ),
                "book_diagnostics": book.get("diagnostics", {}),
                "signal_sha256": payload_sha256(book.get("signals", {})),
                "features_sha256": payload_sha256(day_features),
            }
        )
        state["weights"] = new_weights

    # Force-flat the whole book at the FINAL scored-window boundary.
    fills_flat = execute_trades(final_boundary, {})
    rows.append(
        {
            "day_index": len(open_days),
            "action": FORCE_FLAT_STATUS,
            "decision_ns": int(final_boundary),
            "date_utc": iso_from_ns(int(final_boundary))[:10],
            "status": FORCE_FLAT_STATUS,
            "reason_code": FORCE_FLAT_REASON,
            "n_eligible": None,
            "weights": [],
            "fills": fills_flat,
            "turnover_one_side": round(
                traded_notional(dict(state["weights"]), {}), WEIGHT_ROUNDING_DECIMALS
            ),
            "book_diagnostics": {},
            "signal_sha256": None,
            "features_sha256": None,
        }
    )

    schedule: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "family_id": FAMILY_ID,
        "control_mode": control_mode,
        "neighbour_mode": neighbour_mode,
        "stress": {
            "fee_multiplier": float(stress.fee_multiplier),
            "tick_slip_ticks": int(stress.tick_slip_ticks),
            "event_delay_events": int(stress.event_delay_events),
            "drop_symbols": [str(s) for s in stress.drop_symbols],
            "dropped_fold_index": stress.dropped_fold_index,
        },
        "window_start_iso": window_start_iso,
        "window_end_iso": window_end_iso,
        "cohort": cohort,
        "min_eligible": int(min_eligible),
        "cap": float(cap),
        "gross_target": float(gross),
        "require_all_fills": bool(require_all_fills),
        "opening_rebalances": len(open_days),
        "skipped_rebalances": int(state["skips"]),
        "unfilled_symbols": sorted(dict.fromkeys(unfilled_symbols)),
        "final_weights": {},
        "rows": rows,
    }
    schedule["holding_spans"] = [
        {
            "symbol": span.symbol,
            "signed_weight": span.signed_weight,
            "start_ns": span.start_ns,
            "end_ns": span.end_ns,
        }
        for span in derive_holding_spans(rows)
    ]
    schedule["schedule_sha256"] = payload_sha256(schedule)
    return schedule


# --------------------------------------------------------------------------- #
# C1 field-population verification (fail-closed prerequisite, run NOW)
# --------------------------------------------------------------------------- #
#: Thresholds derive from the attestation table (a8 proposals section 8.1):
#: ATT-TAKER-QV / ATT-COUNT / ATT-QUOTEV demand present, non-null and
#: non-degenerate fields over the staged panel.
FIELD_NULL_SHARE_MAX = 0.0
FLOW_WITHIN_TOTAL_TOLERANCE = 1e-9
TAKER_COLUMN = "taker_buy_quote_volume"
QUOTE_COLUMN = "quote_volume"
COUNT_COLUMN = "count"
COLUMNS_REQUIRED: Tuple[str, ...] = (TAKER_COLUMN, QUOTE_COLUMN, COUNT_COLUMN)
_DISTINCT_SAMPLE_CAP = 5


class _FieldStat:
    """Streaming degeneracy census for one field inside one scope."""

    __slots__ = ("rows", "null_like", "zero", "negative", "_min", "_max", "_distinct")

    def __init__(self) -> None:
        self.rows = 0
        self.null_like = 0
        self.zero = 0
        self.negative = 0
        self._min: Optional[float] = None
        self._max: Optional[float] = None
        self._distinct: List[float] = []

    def observe(self, value: Optional[float]) -> None:
        self.rows += 1
        if value is None:
            self.null_like += 1
            return
        if value == 0.0:
            self.zero += 1
        if value < 0.0:
            self.negative += 1
        self._min = value if self._min is None else min(self._min, value)
        self._max = value if self._max is None else max(self._max, value)
        if value not in self._distinct and len(self._distinct) < _DISTINCT_SAMPLE_CAP:
            self._distinct.append(value)

    def observe_bound_only(self, value: Optional[float]) -> None:
        """Update range bounds WITHOUT counting a row (used by the rollup).

        The cross-symbol rollup already owns its row counts; folding each
        symbol's min/max back in must not double-count them as observations.
        """
        if value is None:
            return
        self._min = value if self._min is None else min(self._min, value)
        self._max = value if self._max is None else max(self._max, value)
        if value not in self._distinct and len(self._distinct) < _DISTINCT_SAMPLE_CAP:
            self._distinct.append(value)

    @property
    def varies(self) -> bool:
        if len(self._distinct) > 1:
            return True
        return self._min is not None and self._max is not None and self._min != self._max

    def summary(self) -> Dict[str, Any]:
        non_null = self.rows - self.null_like
        return {
            "rows": int(self.rows),
            "null_like_count": int(self.null_like),
            "non_null_share": round(non_null / self.rows, 12) if self.rows else None,
            "zero_fraction": round(self.zero / self.rows, 12) if self.rows else None,
            "negative_count": int(self.negative),
            "min": self._min,
            "max": self._max,
            "varies_flag": bool(self.varies),
            "distinct_sample_cap": _DISTINCT_SAMPLE_CAP,
        }


def verify_field_population(
    catalog_path: str | Path,
    *,
    window_start_iso: Optional[str] = SCORED_WINDOW_START_UTC,
    window_end_iso: Optional[str] = SCORED_WINDOW_END_UTC,
    symbols: Sequence[str] = FROZEN_TRADING_COHORT,
    scan_all_present_dirs: bool = True,
) -> Dict[str, Any]:
    """Streaming census of the attacker-flow fields over EVERY present dir.

    Reads the ROOT MASTER catalog directly (READ-ONLY) satisfying freeze
    condition C1: column existence, non-null share, zero/degenerate fraction,
    sane min/max ranges, ``taker <= quote`` violations, ``count == 0`` share,
    rows total, plus which frozen-universe symbols are absent from disk
    entirely. Two scopes whenever window bounds are supplied: the scoped scored
    window and the full history physically on disk. Verdict VERIFIED /
    FAIL_CLOSED per field plus an overall verdict.
    """
    bar_root = Path(catalog_path) / "data" / "binance_bar"
    if not bar_root.is_dir():
        raise CatalogUnavailable(f"no binance_bar tree under {catalog_path}")
    present = sorted(p.name for p in bar_root.iterdir() if p.is_dir())
    prefix_map = {name.split("-PERP.")[0]: name for name in present}
    wanted = [str(s) for s in symbols]
    missing = [sym for sym in wanted if prefix_map.get(sym) is None]
    extras = sorted(
        name.split("-PERP.")[0]
        for name in present
        if name.split("-PERP.")[0] not in set(wanted)
    )

    scan_order: List[str] = [s for s in wanted if s not in set(missing)]
    if scan_all_present_dirs:
        scan_order += extras

    scopes: Dict[str, Tuple[Optional[int], Optional[int]]] = {
        "full_history_on_disk": (None, None),
    }
    if window_start_iso and window_end_iso:
        lo_ns, hi_ns = _window_bounds_ns(window_start_iso, window_end_iso)
        scopes[f"scored_window:{window_start_iso}..{window_end_iso}"] = (lo_ns, hi_ns)

    per_symbol: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    columns_present_everywhere = True
    total_bytes = 0

    for sym in scan_order:
        directory = bar_root / prefix_map[sym]
        files = sorted(Path(directory).rglob("*.parquet"))
        entry: Dict[str, Any] = {
            "directory": prefix_map[sym],
            "parquet_parts": len(files),
            "bytes": sum(int(f.stat().st_size) for f in files),
            "in_frozen_universe": sym in set(wanted),
            "scopes": {},
        }
        total_bytes += entry["bytes"]
        if not files:
            entry["error"] = "no_parquet_parts"
            errors.append(f"{sym}: no parquet parts under {prefix_map[sym]}")
            per_symbol[sym] = entry
            continue
        probe_names = set(pq.read_schema(files[0]).names)
        absent = [col for col in COLUMNS_REQUIRED if col not in probe_names]
        if absent:
            # A missing attacker-flow column fails closed WITHOUT aborting the
            # census of the remaining directories; an explicit error row keeps
            # the numbers auditable instead of crashing mid-scan.
            columns_present_everywhere = False
            errors.append(f"{sym}: columns absent from parquet schema: {absent}")
        stampable = "ts_event" in probe_names
        read_columns = [name for name in COLUMNS_REQUIRED if name in probe_names]
        if stampable:
            read_columns.append("ts_event")
        if not read_columns:
            entry["error"] = f"no readable required columns under {prefix_map[sym]}"
            per_symbol[sym] = entry
            continue

        for scope_name, (lo_ns, hi_ns) in scopes.items():
            stats: Dict[str, _FieldStat] = {
                name: _FieldStat() for name in COLUMNS_REQUIRED
            }
            tqv_gt_qv = 0
            observed_rows = 0
            needs_stamp = (lo_ns is not None or hi_ns is not None) and stampable
            if (lo_ns is not None or hi_ns is not None) and not stampable:
                errors.append(f"{sym}: window scope skipped without a ts_event column")
            for path in files:
                parquet_file = pq.ParquetFile(path)
                for batch in parquet_file.iter_batches(columns=read_columns, batch_size=262144):
                    payload = batch.to_pydict()
                    quotes = payload.get(QUOTE_COLUMN)
                    counts = payload.get(COUNT_COLUMN)
                    takers = payload.get(TAKER_COLUMN)
                    stamps = payload.get("ts_event")
                    available = [len(v) for v in (quotes, counts, takers) if v is not None]
                    for i in range(max(available) if available else 0):
                        if needs_stamp:
                            stamp = int(stamps[i])
                            if lo_ns is not None and stamp < lo_ns:
                                continue
                            if hi_ns is not None and stamp > hi_ns:
                                continue
                        observed_rows += 1
                        q_val = (
                            _parse_decimal_or_none(quotes[i])
                            if quotes is not None and i < len(quotes)
                            else None
                        )
                        t_val = (
                            _parse_decimal_or_none(takers[i])
                            if takers is not None and i < len(takers)
                            else None
                        )
                        c_val = (
                            _parse_uint_or_none(counts[i])
                            if counts is not None and i < len(counts)
                            else None
                        )
                        # A physically absent column stays UNOBSERVED rather than
                        # being reported as null data (the error row records it).
                        if quotes is not None:
                            stats[QUOTE_COLUMN].observe(q_val)
                        if takers is not None:
                            stats[TAKER_COLUMN].observe(t_val)
                        if counts is not None:
                            stats[COUNT_COLUMN].observe(c_val)
                        if q_val is not None and t_val is not None:
                            tol = FLOW_WITHIN_TOTAL_TOLERANCE * max(1.0, abs(q_val))
                            if t_val > q_val + tol:
                                tqv_gt_qv += 1
            entry["scopes"][scope_name] = {
                **{name: stats[name].summary() for name in COLUMNS_REQUIRED},
                "taker_gt_quote_rows": int(tqv_gt_qv),
                "rows_total": int(observed_rows),
            }
        per_symbol[sym] = entry

    report: Dict[str, Any] = {
        "artifact": "i1_c1_field_verification",
        "schema_version": SCHEMA_VERSION,
        "family_id": FAMILY_ID,
        "freeze_condition": "C1 (selection_freeze.json)",
        "catalog_root_readonly": str(catalog_path),
        "generated_by": "research.hyp_a8_m01.verify_field_population",
        "verification_thresholds": {
            "field_null_share_max": FIELD_NULL_SHARE_MAX,
            "flow_within_total_tolerance": FLOW_WITHIN_TOTAL_TOLERANCE,
            "bound_origin": (
                "ATT-TAKER-QV / ATT-COUNT / ATT-QUOTEV (a8_proposals_v10 section 8.1)"
            ),
        },
        "scopes_scanned": list(scopes),
        "frozen_trading_cohort": list(FROZEN_TRADING_COHORT),
        "benchmark_excluded": BENCHMARK_SYMBOL_EXCLUDED,
        "directories_present": present,
        "directories_present_count": len(present),
        "scanned_symbols": scan_order,
        "universe_symbols_missing_from_disk": missing,
        "symbols_on_disk_outside_universe": extras,
        "columns_required": list(COLUMNS_REQUIRED),
        "columns_present_everywhere": bool(columns_present_everywhere),
        "bytes_scanned": int(total_bytes),
        "errors": errors,
        "per_symbol": per_symbol,
    }
    report["aggregate"] = _aggregate_c1(report)
    report["verdict_by_field"] = _c1_verdict_by_field(report)
    report["verdict"] = (
        "VERIFIED"
        if all(v == "VERIFIED" for v in report["verdict_by_field"].values())
        else "FAIL_CLOSED"
    )
    return report


def _aggregate_c1(report: Mapping[str, Any]) -> Dict[str, Any]:
    """Independent rollup of the streaming census across scanned directories."""
    out: Dict[str, Any] = {}
    for scope_name in report["scopes_scanned"]:
        merged = {name: _FieldStat() for name in COLUMNS_REQUIRED}
        tqv_total = 0
        rows_total = 0
        symbols = 0
        for entry in report["per_symbol"].values():
            scope = entry.get("scopes", {}).get(scope_name)
            if not scope:
                continue
            symbols += 1
            rows_total += int(scope["rows_total"])
            tqv_total += int(scope["taker_gt_quote_rows"])
            for name in COLUMNS_REQUIRED:
                src = scope[name]
                dst = merged[name]
                dst.rows += src["rows"]
                dst.null_like += src["null_like_count"]
                dst.zero += (
                    int(round(src["zero_fraction"] * src["rows"]))
                    if src["zero_fraction"] is not None
                    else 0
                )
                dst.negative += src["negative_count"]
                dst.observe_bound_only(src["min"])
                dst.observe_bound_only(src["max"])
        out[scope_name] = {
            "symbols_scanned": symbols,
            "rows_total_scope": rows_total,
            "taker_gt_quote_rows": tqv_total,
            "universe_symbols_missing": list(report["universe_symbols_missing_from_disk"]),
            "fields": {name: merged[name].summary() for name in COLUMNS_REQUIRED},
        }
    return out


def _iter_scope_entries(report: Mapping[str, Any]):
    for sym, entry in report["per_symbol"].items():
        for scope_name, scope in entry.get("scopes", {}).items():
            yield str(sym), str(scope_name), scope


def _field_is_clean(field_stat: Mapping[str, Any]) -> bool:
    if field_stat["rows"] == 0 or field_stat["non_null_share"] is None:
        return False
    if field_stat["non_null_share"] != 1.0 or field_stat["negative_count"]:
        return False
    return bool(field_stat["varies_flag"])


def _c1_verdict_by_field(report: Mapping[str, Any]) -> Dict[str, str]:
    """Per-field verdict over EVERY scanned directory and BOTH scopes."""
    if not report["per_symbol"]:
        return {name: "FAIL_CLOSED" for name in COLUMNS_REQUIRED}
    structural_ok = (
        bool(report["columns_present_everywhere"])
        and not report["errors"]
        and not report["universe_symbols_missing_from_disk"]
    )
    verdicts: Dict[str, str] = {}
    for field_name in COLUMNS_REQUIRED:
        ok = structural_ok
        for _sym, _scope_name, scope in _iter_scope_entries(report):
            stat = scope[field_name]
            if not _field_is_clean(stat):
                ok = False
                break
            if field_name == QUOTE_COLUMN and stat["zero_fraction"] != 0.0:
                ok = False
                break
            if field_name == TAKER_COLUMN and scope["taker_gt_quote_rows"]:
                ok = False
                break
        verdicts[field_name] = "VERIFIED" if ok else "FAIL_CLOSED"
    return verdicts


def _parse_decimal_or_none(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    try:
        value = float(str(raw))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return value


def _parse_uint_or_none(raw: Any) -> Optional[float]:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    if value < 0:
        return None
    return float(value)


def write_json_artifact(payload: Mapping[str, Any], out_path: str | Path) -> Path:
    path = Path(out_path)
    parent = path.parent
    if str(parent):
        parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json_artifact_text(payload) + "\n", encoding="utf-8")
    return path


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI: run the C1 field-population verification and emit its JSON artifact."""
    parser = argparse.ArgumentParser(description="M01 wave-I utilities")
    parser.add_argument("--catalog-root", required=True, help="root master catalog tree (read-only)")
    parser.add_argument("--out", required=True, help="JSON artifact output path")
    parser.add_argument("--verify-fields", action="store_true")
    parser.add_argument("--scan-window-start", default=SCORED_WINDOW_START_UTC)
    parser.add_argument("--scan-window-end", default=SCORED_WINDOW_END_UTC)
    args = parser.parse_args(argv)
    if not args.verify_fields:
        parser.error("nothing to do: pass --verify-fields")
    report = verify_field_population(
        args.catalog_root,
        window_start_iso=args.scan_window_start,
        window_end_iso=args.scan_window_end,
    )
    write_json_artifact(report, args.out)
    print(
        json.dumps(
            {
                "verdict": report["verdict"],
                "verdict_by_field": report["verdict_by_field"],
                "symbols_missing": report["universe_symbols_missing_from_disk"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["verdict"] == "VERIFIED" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
