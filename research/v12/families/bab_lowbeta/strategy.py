"""Frozen strategy primitives for the A12-V12-BAB-LOWBETA family.

Spec sources (FROZEN, verbatim -- never tuned):

* ``research/control/v12_run/selection_freeze_specs/A12-V12-BAB-LOWBETA.json``
  (the frozen arm table incl. ``arm_config_digest`` -- binding);
* ``research/proposals/v12/a5/a5_prop1.{json,md}`` (the selected proposal
  V12-A5-P1-BAB-LOWBETA: mechanism, neighbour, control, falsification).

Frozen mechanism (no parameter menu):

* feature   : trailing 90-day daily BTC beta (anchor/control) or trailing
  90-day daily downside-correlation with BTC over BTC-down days (neighbour),
  both from COMPLETED 15m bars aggregated to daily UTC returns, PIT at the
  stamp (bars with close stamp at-or-before the decision instant only);
* book      : long the 4 lowest / short the 4 highest eligible names, equal
  weight per leg, frozen 90d BTC-beta leg-ratio hedge (BTC context-only,
  never a position), then ONE uniform scale of the whole book when needed so
  every ``|weight| <= 0.30`` (individual names are never clipped);
* control   : ``BAB-90D-W-INV`` carries the sign-inverted book (weights
  negated exactly);
* clock     : decisions Mondays 00:00:00Z, features from completed bars only,
  ONE declared execution lag (the first completed 15m bar strictly after the
  stamp; fill recorded at that bar's close);
* folds     : F0/F1/F2 chronological, force-flat at fold boundaries;
* costs     : generic adapter fees/slippage; native funding while held under
  ``LONG_PAYS_POSITIVE_RATE``;
* fail-closed: < 9 eligible names or < 4 names per leg refuses the stamp
  (``SKIP_NO_SELECTION``), never a partial book.

Identity payload note (freeze v2): the frozen ``arm_config_digest`` values
were published by the selection-freeze v2 reissue (integration commit
``39fc8821a5c8dbe9c2fd998edc3956ad6a02ec8f``, "publish full identity contract
(arm_config_id/direction/strategy_id) and reproducible digests; v1 digests
superseded pre-score -- 0 scored metrics exist").  The v2 identity contract is
reproduced EXACTLY here: strategy_id ``hyp_a12_v12_bab_lowbeta``, ONE
``direction = "long_short_beta_neutral"`` shared by ALL arms (v1 carried no
direction field; the per-arm free-text directions of the first draft are
superseded), per-arm ``arm_config_id`` and the config dict carried verbatim
from the freeze (unchanged between v1 and v2).  A digest mismatch is a bug in
this package, never in the freeze.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from research.adapter_v10.protocol import ContractViolation, StrategyIdentity
from research.v11.publication_identity import arm_config_digest

#: UTC nanoseconds per day / per 15-minute bar.
DAY_NS = 86_400_000_000_000
BAR_NS = 900_000_000_000

# --------------------------------------------------------------------------- #
# Frozen identity / window / clock
# --------------------------------------------------------------------------- #
FAMILY_ID = "A12-V12-BAB-LOWBETA"
STRATEGY_ID = "hyp_a12_v12_bab_lowbeta"
#: Freeze v2 identity contract: ONE direction shared by ALL arms (anchor,
#: neighbour and causal negative control alike).  Pinned by the freeze v2
#: reissue (integration commit 39fc8821a5c8dbe9c2fd998edc3956ad6a02ec8f).
DIRECTION = "long_short_beta_neutral"
BENCHMARK_SYMBOL_EXCLUDED = "BTCUSDT"
FUNDING_SIGN_CONVENTION = "LONG_PAYS_POSITIVE_RATE"
MATRIX_COHORT_HINT = "v12"
WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-21T00:00:00Z"

#: Frozen decision clock (selection-freeze ``common.decision_clock``).
DECISION_CLOCK_TEXT = (
    "Mondays 00:00:00Z; features from completed 15m bars strictly before "
    "stamp; one declared execution lag"
)
#: Frozen costs text (selection-freeze ``common.costs``).
COSTS_TEXT = (
    "generic adapter fees/slippage; native funding while held; "
    "stress = fee x1.5 / +2 ticks / +1 event delay"
)

#: Frozen folds (selection-freeze ``common.folds``; force-flat at
#: boundaries, warmup from pre-window staged data only).
FOLD_F0_START_ISO = "2025-08-22"
FOLD_F0_END_ISO = "2025-12-21"
FOLD_F1_START_ISO = "2025-12-22"
FOLD_F1_END_ISO = "2026-04-21"
FOLD_F2_START_ISO = "2026-04-22"
FOLD_F2_END_ISO = "2026-08-21"
FOLDS: Tuple[Tuple[str, str, str], ...] = (
    ("F0", FOLD_F0_START_ISO, FOLD_F0_END_ISO),
    ("F1", FOLD_F1_START_ISO, FOLD_F1_END_ISO),
    ("F2", FOLD_F2_START_ISO, FOLD_F2_END_ISO),
)

# --------------------------------------------------------------------------- #
# Frozen arms (verbatim from the frozen spec; digests pinned by the freeze)
# --------------------------------------------------------------------------- #
FEATURE_BETA = "btc_beta_90d_daily"
FEATURE_DOWNCORR = "btc_downside_correlation_90d_daily"
FEATURE_SOURCE = "bars_15m_completed"
REBALANCE = "weekly_monday_00z"
FALSIFICATION_CONTROL = "positive after-cost spread destroys mechanism"


def _frozen_config(feature: str, *, inverted: bool = False) -> Dict[str, Any]:
    """The frozen config dict exactly as recorded in the selection freeze."""
    config: Dict[str, Any] = {
        "feature_source": FEATURE_SOURCE,
        "rebalance": REBALANCE,
        "holding_days": 7,
        "legs": 4,
        "weight_cap_abs": 0.3,
        "beta_hedge": "frozen_90d_btc",
        "window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "feature": feature,
        "formation_days": 90,
    }
    if inverted:
        config["sign"] = "inverted"
    return config


ARMS: Dict[str, Dict[str, Any]] = {
    "BAB-90D-W": {
        "role": "anchor",
        "arm_config_id": "90D-BETA",
        "direction": DIRECTION,
        "feature": FEATURE_BETA,
        "sign": 1,
        "config": _frozen_config(FEATURE_BETA),
    },
    "BAB-DOWNCORR-90D-W": {
        "role": "neighbour",
        "arm_config_id": "90D-DOWNCORR",
        "direction": DIRECTION,
        "feature": FEATURE_DOWNCORR,
        "sign": 1,
        "config": _frozen_config(FEATURE_DOWNCORR),
    },
    "BAB-90D-W-INV": {
        "role": "causal_negative_control",
        "arm_config_id": "90D-BETA-INV",
        "direction": DIRECTION,
        "feature": FEATURE_BETA,  # control inherits the anchor feature (frozen)
        "sign": -1,
        "config": _frozen_config(FEATURE_BETA, inverted=True),
    },
}

#: Frozen arm digests -- freeze v2 (selection-freeze reissue, integration
#: commit 39fc8821a5c8dbe9c2fd998edc3956ad6a02ec8f, ``frozen_cells`` rows for
#: family A12-V12-BAB-LOWBETA).  The worktree copy of
#: ``research/control/v12_run/selection_freeze.json`` still holds the
#: SUPERSEDED v1 rows (v1 carried no direction field), so the v2 constants
#: are hard-coded here with this provenance; the strict identity test pins
#: them.  The v1 digests were voided pre-score (0 scored metrics exist).
FROZEN_ARM_CONFIG_DIGESTS: Dict[str, str] = {
    "BAB-90D-W": (
        "7a233cf4672d279408a64b84d0b5e9924323329cf246f1b582fe0eb869c0db60"
    ),
    "BAB-DOWNCORR-90D-W": (
        "c1c2ed26da54090e1c08c35a36209e0afff99540701669fa99623b45f71881ee"
    ),
    "BAB-90D-W-INV": (
        "fabeb43aa89fcbfb915bbda488b07e272f188b2da06fc648e2f3ddc021072423"
    ),
}


def frozen_arm_ids() -> Tuple[str, ...]:
    """Frozen arm ids in freeze-file order (anchor, neighbour, control)."""
    return ("BAB-90D-W", "BAB-DOWNCORR-90D-W", "BAB-90D-W-INV")


ARM_IDS: Tuple[str, ...] = frozen_arm_ids()


def build_frozen_identity(arm_id: str) -> StrategyIdentity:
    """The FROZEN V12 identity for one arm (digest must match the freeze)."""
    if arm_id not in ARMS:
        raise ContractViolation(
            f"unknown frozen arm {arm_id!r}; frozen arms are {frozen_arm_ids()}"
        )
    arm = ARMS[arm_id]
    return StrategyIdentity(
        strategy_id=STRATEGY_ID,
        family_id=FAMILY_ID,
        arm_config_id=str(arm["arm_config_id"]),
        direction=str(arm["direction"]),
        window_start_iso=WINDOW_START_ISO,
        window_end_iso=WINDOW_END_ISO,
        benchmark_symbols_excluded=(BENCHMARK_SYMBOL_EXCLUDED,),
        funding_sign_convention=FUNDING_SIGN_CONVENTION,
        matrix_cohort_hint=MATRIX_COHORT_HINT,
        arm_id=arm_id,
        config=dict(arm["config"]),
    )


def frozen_arm_config_digest(arm_id: str) -> str:
    """``arm_config_digest`` of the frozen identity (freeze-pinned value)."""
    return arm_config_digest(build_frozen_identity(arm_id), arm_id=arm_id)


# --------------------------------------------------------------------------- #
# Frozen book / eligibility / cost parameters
# --------------------------------------------------------------------------- #
FORMATION_DAYS = 90             # frozen trailing daily formation window
LEGS_PER_SIDE = 4               # frozen 4 lowest / 4 highest book
MIN_ELIGIBLE = 9                # fail-closed breadth floor (< 9 -> skip)
BETA_MIN_PAIRED_OBS = 60        # minimum valid paired daily observations
DOWNCORR_MIN_DOWN_DAYS = 2      # a correlation needs >= 2 paired down days
BARS_PER_DAY = 96               # complete UTC day = 96 fifteen-minute bars
CAP = 0.30                      # uniform whole-book scale ceiling (never clip)
GROSS_TARGET = 1.0
TAKER_FEE_FLOOR_BPS = 5.0       # frozen V10 adapter taker-fee floor
ADVERSE_TICK_SLIP_FLOOR = 1     # frozen V10 adapter adverse-tick floor
#: The ONE declared execution lag: the fill event is the first completed 15m
#: bar strictly after the stamp; the fill is recorded at that bar's close
#: (strict-later ``FILLED_NEXT_EVENT``).  Stress steps ``event_delay_events``
#: further completed events.
EXECUTION_LAG_NS = BAR_NS

STATUS_OK = "OK"
STATUS_SKIP = "SKIP_NO_SELECTION"
REASON_BELOW_MIN_ELIGIBLE = "BELOW_MIN_ELIGIBLE"
REASON_LEG_SHORT = "LEG_HAS_FEWER_THAN_4_NAMES"
REASON_BETA_NEUTRAL_INFEASIBLE = "BETA_NEUTRAL_INFEASIBLE"
REASON_WEIGHT_CAP_BREACH = "WEIGHT_CAP_BREACH"
REASON_DEGENERATE_BOOK = "DEGENERATE_BOOK"
REASON_FOLD_BOUNDARY_FORCE_FLAT = "FOLD_BOUNDARY_FORCE_FLAT"


# --------------------------------------------------------------------------- #
# Calendar helpers
# --------------------------------------------------------------------------- #
def parse_iso_utc_ns(iso: str) -> int:
    """Parse ``YYYY-MM-DD[THH:MM:SSZ]`` to UTC epoch nanoseconds (fail closed)."""
    import datetime as _dt

    text = str(iso).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    moment = _dt.datetime.fromisoformat(text)
    if moment.tzinfo is None:
        raise ContractViolation(f"naive ISO timestamp refused: {iso!r}")
    return int(moment.timestamp()) * 1_000_000_000


def iso_date_ns(date_iso: str) -> int:
    """UTC midnight ns of a ``YYYY-MM-DD`` date string."""
    return parse_iso_utc_ns(date_iso + "T00:00:00Z")


def weekly_monday_stamps(
    *, window_start_iso: str = WINDOW_START_ISO, window_end_iso: str = WINDOW_END_ISO
) -> Tuple[int, ...]:
    """Every Monday 00:00:00Z strictly inside the frozen window.

    First stamp 2025-08-25 (frozen; the 90d warmup is served by pre-window
    completed bars, A9-F verified).  The final Monday doubles as the terminal
    force-flat boundary (the generic runner owns that edge).
    """
    import datetime as _dt

    start_ns = parse_iso_utc_ns(window_start_iso)
    end_ns = parse_iso_utc_ns(window_end_iso)
    day = _dt.datetime.fromtimestamp(start_ns / 1_000_000_000, tz=_dt.timezone.utc)
    # advance to the first Monday strictly after the window start
    while day.weekday() != 0 or int(day.timestamp()) * 1_000_000_000 <= start_ns:
        day += _dt.timedelta(days=1)
    stamps: List[int] = []
    while int(day.timestamp()) * 1_000_000_000 <= end_ns:
        stamps.append(int(day.timestamp()) * 1_000_000_000)
        day += _dt.timedelta(days=7)
    if len(stamps) < 2:
        raise ContractViolation("weekly schedule needs at least two Monday stamps")
    return tuple(stamps)


def fold_label_for_stamp(stamp_ns: int) -> Optional[str]:
    """Frozen fold id (F0/F1/F2) owning ``stamp_ns`` by UTC date, else None."""
    for label, start_iso, end_iso in FOLDS:
        if iso_date_ns(start_iso) <= int(stamp_ns) <= iso_date_ns(end_iso):
            return label
    return None


# --------------------------------------------------------------------------- #
# Daily UTC blocks from completed bars (PIT: close stamp at-or-before D)
# --------------------------------------------------------------------------- #
def _require_bar_view(bar: Any) -> None:
    for field in ("ts_event_ns", "open", "close"):
        if not hasattr(bar, field):
            raise ContractViolation(f"bar lacks required field {field!r}")


def _sorted_by_close(bars: Sequence[Any]) -> Sequence[Any]:
    """Bars in close-stamp order; O(n) no-op when already sorted.

    The plugin injects bars pre-sorted by ``ts_event_ns``, so the hot paths
    never pay a Python-level sort; defensively sorting unsorted input keeps
    the public helpers total over any sequence.
    """
    items = list(bars)
    if len(items) < 2:
        return items
    previous = int(items[0].ts_event_ns)
    for bar in items[1:]:
        current = int(bar.ts_event_ns)
        if current < previous:
            return tuple(sorted(items, key=lambda b: int(b.ts_event_ns)))
        previous = current
    return items


def daily_blocks(
    bars: Sequence[Any],
    *,
    decision_ns: int,
    n_days: int,
) -> Dict[int, Dict[str, float]]:
    """Aggregate completed bars into the ``n_days`` daily UTC blocks BEFORE D.

    Block ``k`` (k = 1..n_days) covers ``(D - k*day, D - (k-1)*day]`` by bar
    CLOSE stamp, so only bars completed at-or-before the decision instant can
    contribute (PIT).  Returns ``{k: {open, close, n_bars}}`` for non-empty
    blocks only; the caller decides validity/coverage.
    """
    if int(n_days) <= 0:
        raise ContractViolation("n_days must be positive")
    decision = int(decision_ns)
    out: Dict[int, Dict[str, float]] = {}
    validated = False
    for bar in _sorted_by_close(bars):
        if not validated:
            _require_bar_view(bar)
            validated = True
        close_ns = int(bar.ts_event_ns)
        if close_ns > decision:
            break  # sorted: everything after is future data (never touched)
        age = decision - close_ns
        k = age // DAY_NS + 1
        if k < 1 or k > int(n_days):
            continue
        open_px = float(bar.open)
        close_px = float(bar.close)
        block = out.get(k)
        if block is None:
            out[k] = {"open": open_px, "close": close_px, "n_bars": 1.0}
        else:
            block["close"] = close_px
            block["n_bars"] += 1.0
    return out


def build_day_index(bars: Sequence[Any]) -> Dict[int, Dict[str, float]]:
    """Absolute-UTC-day index ``{day_index: {open, close, n_bars}}``.

    ``day_index`` is ``(close_ns - 1) // DAY_NS``: daily membership by CLOSE
    stamp over right-closed UTC days, so a bar closing EXACTLY on a midnight
    (the 96th bar of every 15m day) belongs to the day ENDING at that
    midnight.  For a MIDNIGHT-ALIGNED decision ``D`` the trailing block ``k``
    of :func:`daily_blocks` is then exactly day ``D // DAY_NS - k`` (block
    ``k`` covers closes in ``(D-k*day, D-(k-1)*day]`` = precisely day
    ``base - k``'s 96 close stamps), which makes this index an exact
    pre-computation of :func:`daily_blocks` at the frozen Monday 00:00:00Z
    stamps -- see :func:`compute_stamp_features`.  Single O(n) pass, built
    lazily by the plugin; pure acceleration, frozen semantics unchanged.
    """
    index: Dict[int, Dict[str, float]] = {}
    for bar in bars:
        close_ns = int(bar.ts_event_ns)
        day = (close_ns - 1) // DAY_NS
        record = index.get(day)
        if record is None:
            index[day] = {
                "open": float(bar.open),
                "close": float(bar.close),
                "n_bars": 1.0,
            }
        else:
            record["close"] = float(bar.close)
            record["n_bars"] += 1.0
    return index


def _valid_block_pair(symbol_block: Any, bench_block: Any) -> Optional[Tuple[float, float]]:
    """Paired daily log returns (symbol, benchmark) for one day, or None."""
    s_open, s_close = float(symbol_block["open"]), float(symbol_block["close"])
    b_open, b_close = float(bench_block["open"]), float(bench_block["close"])
    prices = (s_open, s_close, b_open, b_close)
    if not all(math.isfinite(p) and p > 0.0 for p in prices):
        return None
    return (
        math.log(s_close / s_open),
        math.log(b_close / b_open),
    )


def daily_return_pairs(
    bars: Sequence[Any],
    benchmark_bars: Sequence[Any],
    *,
    decision_ns: int,
    window_days: int = FORMATION_DAYS,
) -> Dict[int, Tuple[float, float]]:
    """Paired daily UTC log returns ``{day_offset_k: (r_sym, r_btc)}``.

    Only days where BOTH the symbol and the benchmark have a fully covered
    daily block (exactly ``BARS_PER_DAY`` completed bars) and positive finite
    prices contribute.  PIT: blocks cover ``(D-k*day, D-(k-1)*day]`` by close
    stamp, so no bar after the decision instant is ever touched.
    """
    pairs = _pairs_from_blocks(
        daily_blocks(bars, decision_ns=int(decision_ns), n_days=int(window_days)),
        daily_blocks(
            benchmark_bars, decision_ns=int(decision_ns), n_days=int(window_days)
        ),
        window_days=int(window_days),
    )
    return pairs


def _pairs_from_blocks(
    symbol_blocks: Mapping[int, Dict[str, float]],
    bench_blocks: Mapping[int, Dict[str, float]],
    *,
    window_days: int,
) -> Dict[int, Tuple[float, float]]:
    """Paired log returns from pre-aggregated daily blocks (shared helper)."""
    pairs: Dict[int, Tuple[float, float]] = {}
    for k in range(1, int(window_days) + 1):
        s_block = symbol_blocks.get(k)
        b_block = bench_blocks.get(k)
        if s_block is None or b_block is None:
            continue
        if float(s_block["n_bars"]) != float(BARS_PER_DAY):
            continue
        if float(b_block["n_bars"]) != float(BARS_PER_DAY):
            continue
        pair = _valid_block_pair(s_block, b_block)
        if pair is None:
            continue
        pairs[k] = pair
    return pairs


def _fully_covered(
    bars: Sequence[Any],
    *,
    decision_ns: int,
    window_days: int = FORMATION_DAYS,
) -> bool:
    """True iff every one of the trailing ``window_days`` daily blocks holds
    exactly ``BARS_PER_DAY`` completed bars (frozen coverage eligibility)."""
    blocks = daily_blocks(bars, decision_ns=int(decision_ns), n_days=int(window_days))
    if len(blocks) != int(window_days):
        return False
    return all(
        float(block["n_bars"]) == float(BARS_PER_DAY) for block in blocks.values()
    )


# --------------------------------------------------------------------------- #
# Frozen features (PIT at the stamp)
# --------------------------------------------------------------------------- #
def _ols_beta(xs: Sequence[float], ys: Sequence[float]) -> float:
    """OLS slope of ``ys`` on ``xs`` (plain closed form, deterministic)."""
    n = len(xs)
    mean_x = math.fsum(xs) / n
    mean_y = math.fsum(ys) / n
    cov = math.fsum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = math.fsum((x - mean_x) ** 2 for x in xs)
    if var_x <= 0.0:
        raise ValueError("degenerate beta regression (zero benchmark variance)")
    return cov / var_x


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Pearson correlation (deterministic closed form)."""
    n = len(xs)
    mean_x = math.fsum(xs) / n
    mean_y = math.fsum(ys) / n
    cov = math.fsum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = math.fsum((x - mean_x) ** 2 for x in xs)
    var_y = math.fsum((y - mean_y) ** 2 for y in ys)
    if var_x <= 0.0 or var_y <= 0.0:
        raise ValueError("degenerate correlation (zero variance)")
    return cov / math.sqrt(var_x * var_y)


def trailing_btc_beta(
    pairs: Mapping[int, Tuple[float, float]],
) -> Optional[float]:
    """OLS beta of symbol daily log returns on BTC daily log returns.

    ``None`` when fewer than ``BETA_MIN_PAIRED_OBS`` valid paired observations
    exist or the regression is degenerate (fail closed, never imputed).
    """
    if len(pairs) < int(BETA_MIN_PAIRED_OBS):
        return None
    xs = [pair[1] for pair in pairs.values()]  # benchmark on x
    ys = [pair[0] for pair in pairs.values()]  # symbol on y
    try:
        beta = _ols_beta(xs, ys)
    except ValueError:
        return None
    return beta if math.isfinite(beta) else None


def trailing_downside_correlation(
    pairs: Mapping[int, Tuple[float, float]],
) -> Optional[float]:
    """Pearson correlation over days when the BTC daily return is < 0.

    The frozen neighbour statistic (S2: the correlation channel concentrates
    in assets most correlated with the market in bad states).  ``None`` when
    fewer than ``DOWNCORR_MIN_DOWN_DAYS`` BTC-down paired days exist or the
    correlation is degenerate (fail closed, never imputed).
    """
    down = [(r_sym, r_btc) for r_sym, r_btc in pairs.values() if r_btc < 0.0]
    if len(down) < int(DOWNCORR_MIN_DOWN_DAYS):
        return None
    xs = [pair[1] for pair in down]
    ys = [pair[0] for pair in down]
    try:
        corr = _pearson(xs, ys)
    except ValueError:
        return None
    return corr if math.isfinite(corr) else None


# --------------------------------------------------------------------------- #
# Per-stamp features
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StampFeatures:
    """Per-stamp PIT feature snapshot (features + eligibility diagnostics)."""

    decision_ns: int
    features: Dict[str, float]
    betas: Dict[str, float]
    diagnostics: Dict[str, Any]


def _stamp_blocks_from_index(
    day_index: Mapping[int, Dict[str, float]],
    *,
    decision_ns: int,
    n_days: int,
) -> Dict[int, Dict[str, float]]:
    """Trailing ``n_days`` blocks for a MIDNIGHT-ALIGNED decision from the
    pre-built absolute-day index (exact equivalent of :func:`daily_blocks`
    at ``decision_ns % DAY_NS == 0`` -- block ``k`` is UTC day
    ``decision_ns // DAY_NS - k``)."""
    base = int(decision_ns) // DAY_NS
    out: Dict[int, Dict[str, float]] = {}
    for k in range(1, int(n_days) + 1):
        record = day_index.get(base - k)
        if record is not None:
            out[k] = record
    return out


def compute_stamp_features(
    *,
    bars_by_symbol: Mapping[str, Sequence[Any]],
    universe: Sequence[str],
    benchmark_symbol: str,
    decision_ns: int,
    feature: str,
    day_index_by_symbol: Optional[Mapping[str, Mapping[int, Dict[str, float]]]] = None,
) -> StampFeatures:
    """PIT features + frozen 90d betas at one stamp (fail closed per name).

    Eligibility per name: fully covered 90-day trailing daily block
    (``BARS_PER_DAY`` completed bars each day), at least
    ``BETA_MIN_PAIRED_OBS`` valid paired daily observations vs the benchmark,
    and a finite feature value.  ``feature`` selects the frozen statistic:
    ``btc_beta_90d_daily`` or ``btc_downside_correlation_90d_daily``.

    ``day_index_by_symbol`` (optional, plugin-built via
    :func:`build_day_index`) accelerates MIDNIGHT-ALIGNED decisions -- the
    frozen Monday 00:00:00Z stamps -- to dictionary lookups; it is an exact
    pre-computation of the same blocks, never a different statistic.  Any
    other decision instant (or a missing index) takes the general path.
    """
    if feature not in (FEATURE_BETA, FEATURE_DOWNCORR):
        raise ContractViolation(f"unknown frozen feature {feature!r}")
    decision = int(decision_ns)
    midnight_aligned = decision % DAY_NS == 0
    indices: Optional[Mapping[str, Mapping[int, Dict[str, float]]]] = None
    if day_index_by_symbol is not None and midnight_aligned:
        indices = day_index_by_symbol

    benchmark_bars = bars_by_symbol.get(str(benchmark_symbol)) or ()
    features: Dict[str, float] = {}
    betas: Dict[str, float] = {}
    n_full_coverage = 0

    def _symbol_blocks(sym: str, bars: Sequence[Any]) -> Dict[int, Dict[str, float]]:
        if indices is not None:
            index = indices.get(sym)
            if index is not None:
                return _stamp_blocks_from_index(
                    index, decision_ns=decision, n_days=int(FORMATION_DAYS)
                )
        return daily_blocks(bars, decision_ns=decision, n_days=int(FORMATION_DAYS))

    if indices is not None:
        bench_index = indices.get(str(benchmark_symbol))
        bench_blocks = (
            _stamp_blocks_from_index(
                bench_index, decision_ns=decision, n_days=int(FORMATION_DAYS)
            )
            if bench_index is not None
            else {}
        )
    else:
        bench_blocks = daily_blocks(
            benchmark_bars, decision_ns=decision, n_days=int(FORMATION_DAYS)
        )

    for sym in sorted({str(s) for s in universe}):
        bars = bars_by_symbol.get(sym) or ()
        if not bars:
            continue
        symbol_blocks = _symbol_blocks(sym, bars)
        if len(symbol_blocks) != int(FORMATION_DAYS) or not all(
            float(block["n_bars"]) == float(BARS_PER_DAY)
            for block in symbol_blocks.values()
        ):
            continue
        n_full_coverage += 1
        pairs = _pairs_from_blocks(
            symbol_blocks, bench_blocks, window_days=int(FORMATION_DAYS)
        )
        beta = trailing_btc_beta(pairs)
        if beta is None:
            continue
        value: Optional[float]
        if feature == FEATURE_DOWNCORR:
            value = trailing_downside_correlation(pairs)
        else:
            value = beta
        if value is None or not math.isfinite(value):
            continue
        features[sym] = float(value)
        betas[sym] = float(beta)
    diagnostics: Dict[str, Any] = {
        "n_universe": len({str(s) for s in universe}),
        "n_full_coverage_90d": n_full_coverage,
        "min_paired_obs_required": int(BETA_MIN_PAIRED_OBS),
    }
    return StampFeatures(
        decision_ns=decision,
        features=features,
        betas=betas,
        diagnostics=diagnostics,
    )


# --------------------------------------------------------------------------- #
# Target book: long low / short high, beta-hedged, uniformly cap-scaled
# --------------------------------------------------------------------------- #
def build_bab_book(
    *,
    features: Mapping[str, float],
    betas: Mapping[str, float],
    arm_sign: int,
) -> Dict[str, Any]:
    """Long the 4 lowest / short the 4 highest featured names, beta-hedged.

    Frozen construction (no parameter menu):

    1. rank eligible names by the feature ascending (ties by symbol for
       determinism); long leg = the 4 lowest, short leg = the 4 highest;
    2. equal weight per leg at unit-gross base (0.5 / 0.5, ``1/4`` per name);
    3. frozen 90d BTC-beta leg-ratio hedge: the long-leg gross is scaled by
       ``m = mean(beta_short) / mean(beta_long)`` so the beta-weighted book
       sum ``sum(beta_i * w_i)`` is exactly zero on the same frozen betas;
       BTCUSDT itself is never a position (context-only);
    4. ONE uniform scale of the whole book to unit gross, then (when needed)
       one further uniform whole-book scale ``c = min(1, CAP / max|w|)`` so
       every ``|weight| <= 0.30`` -- individual names are NEVER clipped;
    5. ``arm_sign = -1`` negates every weight exactly (the sign-inverted
       causal control; the cap holds symmetrically).

    Fail closed (``SKIP_NO_SELECTION`` with a reason code, never a partial
    book): fewer than 9 eligible names, fewer than 4 names on a leg, a
    non-positive leg mean beta (hedge infeasible), or a residual cap breach
    (unreachable at 4+4 legs -- refused, not clipped).
    """
    if int(arm_sign) not in (-1, 1):
        raise ContractViolation("arm_sign must be +-1")
    ranked = sorted(features, key=lambda s: (features[s], s))  # ascending
    n = len(ranked)
    if n < int(MIN_ELIGIBLE):
        return {
            "status": STATUS_SKIP,
            "weights": {},
            "reason_code": REASON_BELOW_MIN_ELIGIBLE,
            "diagnostics": {"n_eligible": n, "min_eligible": int(MIN_ELIGIBLE)},
        }
    longs = list(ranked[: int(LEGS_PER_SIDE)])           # lowest feature
    shorts = list(ranked[n - int(LEGS_PER_SIDE):])       # highest feature
    if len(longs) != int(LEGS_PER_SIDE) or len(shorts) != int(LEGS_PER_SIDE):
        return {
            "status": STATUS_SKIP,
            "weights": {},
            "reason_code": REASON_LEG_SHORT,
            "diagnostics": {
                "n_long": len(longs),
                "n_short": len(shorts),
                "legs_required": int(LEGS_PER_SIDE),
            },
        }
    legs = longs + shorts
    beta_long = math.fsum(float(betas[s]) for s in longs) / len(longs)
    beta_short = math.fsum(float(betas[s]) for s in shorts) / len(shorts)
    if not (math.isfinite(beta_long) and math.isfinite(beta_short)):
        return {
            "status": STATUS_SKIP,
            "weights": {},
            "reason_code": REASON_BETA_NEUTRAL_INFEASIBLE,
            "diagnostics": {"beta_long": beta_long, "beta_short": beta_short},
        }
    if beta_long <= 0.0 or beta_short <= 0.0:
        return {
            "status": STATUS_SKIP,
            "weights": {},
            "reason_code": REASON_BETA_NEUTRAL_INFEASIBLE,
            "diagnostics": {"beta_long": beta_long, "beta_short": beta_short},
        }
    ratio = beta_short / beta_long
    # base leg grosses: long 0.5 * ratio, short 0.5 -> beta-weighted sum zero
    weights = {
        sym: (0.5 * ratio / len(longs) if sym in set(longs)
              else -0.5 / len(shorts))
        for sym in legs
    }
    gross = math.fsum(abs(w) for w in weights.values())
    if gross <= 0.0 or not math.isfinite(gross):
        return {
            "status": STATUS_SKIP,
            "weights": {},
            "reason_code": REASON_DEGENERATE_BOOK,
            "diagnostics": {"gross": gross},
        }
    weights = {sym: w / gross for sym, w in weights.items()}
    # ONE uniform whole-book scale for the frozen cap (never per-name clips)
    max_abs = max(abs(w) for w in weights.values())
    scale = min(1.0, float(CAP) / max_abs) if max_abs > 0.0 else 1.0
    weights = {sym: w * scale for sym, w in weights.items()}
    cap_breaches = sorted(
        sym for sym, w in weights.items() if abs(w) > float(CAP) + 1e-9
    )
    if cap_breaches:
        return {
            "status": STATUS_SKIP,
            "weights": {},
            "reason_code": REASON_WEIGHT_CAP_BREACH,
            "diagnostics": {"symbols": cap_breaches},
        }
    sign = float(arm_sign)
    final = {sym: weights[sym] * sign for sym in legs}
    book_beta = math.fsum(float(betas[sym]) * final[sym] for sym in legs)
    return {
        "status": STATUS_OK,
        "weights": final,
        "reason_code": None,
        "diagnostics": {
            "n_eligible": n,
            "legs_per_side": int(LEGS_PER_SIDE),
            "long_leg": list(longs),
            "short_leg": list(shorts),
            "beta_long_mean": beta_long,
            "beta_short_mean": beta_short,
            "hedge_ratio": ratio,
            "uniform_cap_scale": scale,
            "gross": round(math.fsum(abs(w) for w in final.values()), 12),
            "net_exposure": round(math.fsum(final.values()), 12),
            "book_beta_post_hedge": round(book_beta, 12),
            "cap_abs": float(CAP),
        },
    }


__all__ = [
    "ADVERSE_TICK_SLIP_FLOOR",
    "ARM_IDS",
    "ARMS",
    "BARS_PER_DAY",
    "BENCHMARK_SYMBOL_EXCLUDED",
    "BAR_NS",
    "BETA_MIN_PAIRED_OBS",
    "CAP",
    "COSTS_TEXT",
    "DECISION_CLOCK_TEXT",
    "DAY_NS",
    "DIRECTION",
    "DOWNCORR_MIN_DOWN_DAYS",
    "EXECUTION_LAG_NS",
    "FAMILY_ID",
    "FEATURE_BETA",
    "FEATURE_DOWNCORR",
    "FOLDS",
    "FORMATION_DAYS",
    "FROZEN_ARM_CONFIG_DIGESTS",
    "FUNDING_SIGN_CONVENTION",
    "GROSS_TARGET",
    "LEGS_PER_SIDE",
    "MATRIX_COHORT_HINT",
    "MIN_ELIGIBLE",
    "REASON_BELOW_MIN_ELIGIBLE",
    "REASON_BETA_NEUTRAL_INFEASIBLE",
    "REASON_DEGENERATE_BOOK",
    "REASON_FOLD_BOUNDARY_FORCE_FLAT",
    "REASON_LEG_SHORT",
    "REASON_WEIGHT_CAP_BREACH",
    "STATUS_OK",
    "STATUS_SKIP",
    "STRATEGY_ID",
    "TAKER_FEE_FLOOR_BPS",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "build_bab_book",
    "build_day_index",
    "build_frozen_identity",
    "compute_stamp_features",
    "daily_blocks",
    "daily_return_pairs",
    "fold_label_for_stamp",
    "frozen_arm_config_digest",
    "frozen_arm_ids",
    "iso_date_ns",
    "parse_iso_utc_ns",
    "trailing_btc_beta",
    "trailing_downside_correlation",
    "weekly_monday_stamps",
]
