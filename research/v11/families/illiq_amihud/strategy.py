"""Frozen strategy primitives for the A8-V11-ILLIQ-AMIHUD family.

Spec source (FROZEN, verbatim -- never tuned):
``research/control/v11_run/selection_freeze_specs/A8-V11-ILLIQ-AMIHUD.json``

* feature   : N-day mean daily Amihud ``|daily return| / daily dollar volume``
              built from COMPLETED 15m bars aggregated to daily UTC blocks
              (28d anchor / 56d neighbour formation);
* book      : long most-illiquid / short most-liquid quintiles, equal weight,
              dollar-neutral, beta-neutral via the frozen 90d daily BTC beta;
* control   : ``ILLIQ-AMIHUD-28D-W-INV`` carries the sign-inverted book;
* clock     : decisions Mondays 00:00:00Z, features from completed bars only,
              ONE declared execution lag after availability;
* folds     : F0/F1/F2 chronological, force-flat at fold boundaries;
* costs     : generic adapter fees/slippage; native funding while held;
* diagnostics: pre-declared per-stamp reversal + size confound diagnostics
              (diagnostic artifacts only, NEVER signal inputs).

Identity payload note: the frozen ``arm_config_digest`` values were computed
by A1 over :class:`research.adapter_v10.protocol.StrategyIdentity` via
:func:`research.v11.publication_identity.arm_config_digest` with the config
mapping below (feature/book/formation_days/holding_days/decision_clock/costs/
falsification, the control inheriting the anchor feature).  The identity is
reproduced EXACTLY here; a mismatch is a bug in this package, never in the
freeze.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence
from typing import Dict, List, Tuple

from research.v11.publication_identity import arm_config_digest
from research.adapter_v10.protocol import ContractViolation, StrategyIdentity

#: UTC nanoseconds per day.
DAY_NS = 86_400_000_000_000

# --------------------------------------------------------------------------- #
# Frozen identity / window / clock
# --------------------------------------------------------------------------- #
FAMILY_ID = "A8-V11-ILLIQ-AMIHUD"
STRATEGY_ID = "A8-V11-ILLIQ-AMIHUD.v1"
DIRECTION = "long_short_beta_neutral"
BENCHMARK_SYMBOL_EXCLUDED = "BTCUSDT"
WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-21T00:00:00Z"

#: Frozen decision clock text (selection-freeze spec ``common.decision_clock``).
DECISION_CLOCK_TEXT = (
    "Mondays 00:00:00Z; features from completed 15m bars + last COMPLETED OI 5m "
    "row strictly before stamp; one declared execution lag after availability"
)
#: Frozen costs text (selection-freeze spec ``common.costs``).
COSTS_TEXT = (
    "generic adapter fees/slippage; native funding while held; "
    "stress = fee x1.5, +2 ticks, +1 event delay"
)

#: Frozen folds (selection-freeze spec ``common.folds``; force-flat at
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
FEATURE_28D = "28d mean daily Amihud |r|/dollar-volume (15m agg daily UTC)"
BOOK_ANCHOR = "long illiquid / short liquid quintiles, beta-neutral"
FEATURE_56D = "56d Amihud (slower formation)"
BOOK_NEIGHBOUR = "same, 56d"
FALSIFICATION_CONTROL = "positive after-cost spread destroys mechanism"

ARMS: Dict[str, Dict[str, Any]] = {
    "ILLIQ-AMIHUD-28D-W": {
        "role": "anchor",
        "feature": FEATURE_28D,
        "book": BOOK_ANCHOR,
        "formation_days": 28,
        "holding_days": 7,
        "falsification": "",
        "sign": 1,
    },
    "ILLIQ-AMIHUD-56D-W": {
        "role": "neighbour",
        "feature": FEATURE_56D,
        "book": BOOK_NEIGHBOUR,
        "formation_days": 56,
        "holding_days": 7,
        "falsification": "",
        "sign": 1,
    },
    "ILLIQ-AMIHUD-28D-W-INV": {
        "role": "causal_negative_control",
        "feature": FEATURE_28D,  # control inherits the anchor feature (frozen)
        "book": "sign-inverted",
        "formation_days": 28,
        "holding_days": 7,
        "falsification": FALSIFICATION_CONTROL,
        "sign": -1,
    },
}

# The anchor formation/holding inherited by arms that lack their own values.
_ANCHOR_FORMATION_DAYS = 28
_ANCHOR_HOLDING_DAYS = 7


def frozen_arm_ids() -> Tuple[str, ...]:
    """Frozen arm ids in freeze-file order (anchor, neighbour, control)."""
    return ("ILLIQ-AMIHUD-28D-W", "ILLIQ-AMIHUD-56D-W", "ILLIQ-AMIHUD-28D-W-INV")


def build_frozen_identity(arm_id: str) -> StrategyIdentity:
    """The FROZEN V11 identity for one arm (digest must match the freeze)."""
    if arm_id not in ARMS:
        raise ContractViolation(f"unknown frozen arm {arm_id!r}")
    arm = ARMS[arm_id]
    # Control arms inherit anchor formation/holding with inverted book (frozen).
    formation_days = int(arm.get("formation_days", _ANCHOR_FORMATION_DAYS))
    holding_days = int(arm.get("holding_days", _ANCHOR_HOLDING_DAYS))
    return StrategyIdentity(
        strategy_id=STRATEGY_ID,
        family_id=FAMILY_ID,
        arm_config_id=str(arm["role"]),
        direction=DIRECTION,
        window_start_iso=WINDOW_START_ISO,
        window_end_iso=WINDOW_END_ISO,
        benchmark_symbols_excluded=(BENCHMARK_SYMBOL_EXCLUDED,),
        arm_id=arm_id,
        config={
            "feature": str(arm["feature"]),
            "book": str(arm["book"]),
            "formation_days": formation_days,
            "holding_days": holding_days,
            "decision_clock": DECISION_CLOCK_TEXT,
            "costs": COSTS_TEXT,
            "falsification": str(arm.get("falsification", "")),
        },
    )


def frozen_arm_config_digest(arm_id: str) -> str:
    """``arm_config_digest`` of the frozen identity (freeze-pinned value)."""
    return arm_config_digest(build_frozen_identity(arm_id), arm_id=arm_id)


# --------------------------------------------------------------------------- #
# Frozen book / eligibility / cost parameters
# --------------------------------------------------------------------------- #
QUINTILES = 5
MIN_ELIGIBLE = 10               # >= 2 names per quintile leg on both sides
CAP = 0.30                      # repo-wide single-symbol weight ceiling
GROSS_TARGET = 1.0
BETA_WINDOW_DAYS = 90           # frozen 90d daily beta hedge window
BETA_MIN_OBS = 60               # minimum paired daily observations (declared)
TAKER_FEE_FLOOR_BPS = 5.0       # frozen V10 adapter taker-fee floor
ADVERSE_TICK_SLIP_FLOOR = 1     # frozen V10 adapter adverse-tick floor
EXECUTION_LAG_DAYS = 1          # the ONE declared execution lag (24h)
MIN_DAY_COVERAGE_FRACTION = 0.8  # min fraction of valid daily blocks in window

#: Pre-declared confound diagnostics (diagnostic ONLY, never signal inputs).
REVERSAL_DIAGNOSTIC_DAYS = 7    # per-stamp rho vs 7d reversal
SIZE_DIAGNOSTIC_DAYS = 30       # per-stamp rho vs log market-cap proxy
SIZE_PROXY = "log median daily dollar volume over trailing 30d"

STATUS_OK = "OK"
STATUS_SKIP = "SKIP_NO_SELECTION"


# --------------------------------------------------------------------------- #
# Schedule: Mondays 00:00:00Z inside (window_start, window_end]
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
    return int(moment.timestamp() * 1_000_000_000)


def iso_date_ns(date_iso: str) -> int:
    """UTC midnight ns of a ``YYYY-MM-DD`` date string."""
    return parse_iso_utc_ns(date_iso + "T00:00:00Z")


def weekly_monday_stamps(
    *, window_start_iso: str = WINDOW_START_ISO, window_end_iso: str = WINDOW_END_ISO
) -> Tuple[int, ...]:
    """Every Monday 00:00:00Z strictly inside the frozen window.

    The last stamp doubles as the terminal force-flat boundary (the generic
    runner force-flattens at the final schedule instant).
    """
    import datetime as _dt

    start_ns = parse_iso_utc_ns(window_start_iso)
    end_ns = parse_iso_utc_ns(window_end_iso)
    day = _dt.datetime.fromtimestamp(start_ns / 1_000_000_000, tz=_dt.timezone.utc)
    # advance to the first Monday strictly after the window start
    while day.weekday() != 0 or int(day.timestamp() * 1_000_000_000) <= start_ns:
        day += _dt.timedelta(days=1)
    stamps: List[int] = []
    while int(day.timestamp() * 1_000_000_000) <= end_ns:
        stamps.append(int(day.timestamp() * 1_000_000_000))
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
# Daily UTC blocks from completed bars
# --------------------------------------------------------------------------- #
def _require_bar_view(bar: Any) -> None:
    for field in ("ts_event_ns", "open", "close", "quote_volume"):
        if not hasattr(bar, field):
            raise ContractViolation(f"bar lacks required field {field!r}")


def daily_blocks(
    bars: Sequence[Any],
    *,
    decision_ns: int,
    n_days: int,
) -> Dict[int, Dict[str, float]]:
    """Aggregate completed bars into the ``n_days`` daily UTC blocks BEFORE D.

    Block ``k`` (k = 1..n_days) covers ``(D - k*day, D - (k-1)*day]`` by bar
    CLOSE stamp, so only bars completed at-or-before the decision instant can
    contribute (PIT).  Returns ``{k: {open, close, quote_volume, n_bars}}`` for
    non-empty blocks only; the caller decides validity.
    """
    if n_days <= 0:
        raise ContractViolation("n_days must be positive")
    decision = int(decision_ns)
    ordered = sorted((b for b in bars), key=lambda b: int(b.ts_event_ns))
    out: Dict[int, Dict[str, float]] = {}
    for bar in ordered:
        _require_bar_view(bar)
        close_ns = int(bar.ts_event_ns)
        if close_ns > decision:
            break  # sorted: everything after is future data (never touched)
        age = decision - close_ns
        k = age // DAY_NS + 1
        if k < 1 or k > n_days:
            continue
        open_px = float(bar.open)
        close_px = float(bar.close)
        qv = float(bar.quote_volume)
        block = out.get(k)
        if block is None:
            out[k] = {
                "open": open_px,
                "close": close_px,
                "quote_volume": qv,
                "n_bars": 1.0,
            }
        else:
            block["close"] = close_px
            block["quote_volume"] += qv
            block["n_bars"] += 1.0
    return out


def daily_amihud_series(
    bars: Sequence[Any],
    *,
    decision_ns: int,
    formation_days: int,
) -> Dict[str, Any]:
    """Daily Amihud ``|r|/dollar-volume`` over the trailing formation window.

    Returns ``{"values": [amihud per valid day], "n_valid": int,
    "first_close_ns": int|None}``.  A day is valid when its block exists and
    carries a positive finite dollar volume; ``|r| = |block_close/block_open - 1|``
    over the day's completed bars.
    """
    blocks = daily_blocks(bars, decision_ns=int(decision_ns), n_days=int(formation_days))
    values: List[float] = []
    first_close_ns: Optional[int] = None
    for bar in sorted(bars, key=lambda b: int(b.ts_event_ns)):
        if int(bar.ts_event_ns) <= int(decision_ns):
            first_close_ns = int(bar.ts_event_ns)
            break
    for k in range(1, int(formation_days) + 1):
        block = blocks.get(k)
        if block is None:
            continue
        dv = float(block["quote_volume"])
        open_px = float(block["open"])
        close_px = float(block["close"])
        if not (dv > 0.0 and math.isfinite(dv)):
            continue
        if not (open_px > 0.0 and close_px > 0.0):
            continue
        if not (math.isfinite(open_px) and math.isfinite(close_px)):
            continue
        ret = close_px / open_px - 1.0
        values.append(abs(ret) / dv)
    return {
        "values": values,
        "n_valid": len(values),
        "first_close_ns": first_close_ns,
    }


def amihud_feature(
    bars: Sequence[Any],
    *,
    decision_ns: int,
    formation_days: int,
    min_day_coverage_fraction: float = MIN_DAY_COVERAGE_FRACTION,
) -> Optional[float]:
    """Frozen formation-day mean daily Amihud feature (None = unavailable).

    PIT: only bars closing at-or-before ``decision_ns`` enter.  Eligibility by
    listing: the symbol needs at least ``formation_days`` calendar days of
    history before the stamp; coverage: at least the declared fraction of the
    trailing daily blocks must be valid.
    """
    series = daily_amihud_series(
        bars, decision_ns=int(decision_ns), formation_days=int(formation_days)
    )
    values = series["values"]
    needed = max(2, int(math.ceil(int(formation_days) * float(min_day_coverage_fraction))))
    if len(values) < needed:
        return None
    first_close_ns = series["first_close_ns"]
    if first_close_ns is None:
        return None
    listing_age_days = (int(decision_ns) - int(first_close_ns)) / DAY_NS
    if listing_age_days < float(formation_days):
        return None  # listing/PIT eligibility: insufficient history
    return math.fsum(values) / len(values)


def daily_block_return(bars: Sequence[Any], *, decision_ns: int, k: int) -> Optional[float]:
    """Completed-block daily return ``close/open - 1`` for day-offset ``k``."""
    blocks = daily_blocks(bars, decision_ns=int(decision_ns), n_days=int(k))
    block = blocks.get(int(k))
    if block is None:
        return None
    open_px = float(block["open"])
    close_px = float(block["close"])
    if not (open_px > 0.0 and close_px > 0.0):
        return None
    return close_px / open_px - 1.0


def trailing_beta(
    bars: Sequence[Any],
    benchmark_bars: Sequence[Any],
    *,
    decision_ns: int,
    window_days: int = BETA_WINDOW_DAYS,
    min_obs: int = BETA_MIN_OBS,
) -> Optional[float]:
    """Frozen trailing daily beta vs the benchmark over completed blocks.

    OLS slope of the symbol's daily block returns on the benchmark's daily
    block returns over the trailing ``window_days`` UTC days strictly before
    the decision instant.  ``None`` when fewer than ``min_obs`` paired valid
    observations exist (symbol then ineligible -- fail closed, never imputed).
    """
    symbol_blocks = daily_blocks(bars, decision_ns=int(decision_ns), n_days=int(window_days))
    bench_blocks = daily_blocks(
        benchmark_bars, decision_ns=int(decision_ns), n_days=int(window_days)
    )
    xs: List[float] = []
    ys: List[float] = []
    for k in range(1, int(window_days) + 1):
        s_block = symbol_blocks.get(k)
        b_block = bench_blocks.get(k)
        if s_block is None or b_block is None:
            continue
        s_open, s_close = float(s_block["open"]), float(s_block["close"])
        b_open, b_close = float(b_block["open"]), float(b_block["close"])
        if min(s_open, s_close, b_open, b_close) <= 0.0:
            continue
        xs.append(s_close / s_open - 1.0)
        ys.append(b_close / b_open - 1.0)
    n = len(xs)
    if n < int(min_obs):
        return None
    mean_x = math.fsum(xs) / n
    mean_y = math.fsum(ys) / n
    cov = math.fsum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_y = math.fsum((y - mean_y) ** 2 for y in ys)
    if var_y <= 0.0:
        return None
    return cov / var_y


# --------------------------------------------------------------------------- #
# Pre-declared confound diagnostics (diagnostic ONLY -- never signal inputs)
# --------------------------------------------------------------------------- #
def _rank(values: Sequence[float]) -> List[float]:
    """Average ranks (1-based) with tied values sharing their mean rank."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average = (i + j) / 2.0 + 1.0
        for idx in order[i : j + 1]:
            ranks[idx] = average
        i = j + 1
    return ranks


def spearman_rho(a: Sequence[float], b: Sequence[float]) -> Optional[float]:
    """Spearman rank correlation (Pearson on average ranks); None if degenerate."""
    if len(a) != len(b) or len(a) < 5:
        return None
    ra = _rank(a)
    rb = _rank(b)
    n = len(ra)
    mean_ra = math.fsum(ra) / n
    mean_rb = math.fsum(rb) / n
    cov = math.fsum((x - mean_ra) * (y - mean_rb) for x, y in zip(ra, rb))
    var_a = math.fsum((x - mean_ra) ** 2 for x in ra)
    var_b = math.fsum((y - mean_rb) ** 2 for y in rb)
    if var_a <= 0.0 or var_b <= 0.0:
        return None
    return cov / math.sqrt(var_a * var_b)


def stamp_diagnostics(
    *,
    bars_by_symbol: Mapping[str, Sequence[Any]],
    decision_ns: int,
    eligible_symbols: Sequence[str],
    features: Mapping[str, float],
) -> Dict[str, Any]:
    """Per-stamp reversal + size confound diagnostics (artifacts only)."""
    reversals: List[float] = []
    sizes: List[float] = []
    feats_rev: List[float] = []
    feats_size: List[float] = []
    for sym in sorted(set(eligible_symbols)):
        bars = bars_by_symbol.get(str(sym)) or ()
        feature = features.get(str(sym))
        if feature is None:
            continue
        close_now = daily_block_return(bars, decision_ns=int(decision_ns), k=1)
        close_past = daily_block_return(
            bars, decision_ns=int(decision_ns), k=REVERSAL_DIAGNOSTIC_DAYS + 1
        )
        if close_now is not None and close_past is not None and close_past != 0.0:
            reversals.append(close_now / close_past - 1.0)
            feats_rev.append(float(feature))
        blocks = daily_blocks(
            bars, decision_ns=int(decision_ns), n_days=SIZE_DIAGNOSTIC_DAYS
        )
        dvs = [
            float(block["quote_volume"])
            for block in blocks.values()
            if float(block["quote_volume"]) > 0.0
        ]
        if dvs:
            median_dv = sorted(dvs)[len(dvs) // 2]
            if median_dv > 0.0:
                sizes.append(math.log(median_dv))
                feats_size.append(float(feature))
    return {
        "declared": "pre-declared confound diagnostics; never signal inputs",
        "rho_amihud_vs_reversal_7d": spearman_rho(feats_rev, reversals),
        "reversal_definition": f"{REVERSAL_DIAGNOSTIC_DAYS}d completed-block return",
        "reversal_n": len(reversals),
        "rho_amihud_vs_log_size_proxy": spearman_rho(feats_size, sizes),
        "size_proxy": SIZE_PROXY,
        "size_n": len(sizes),
    }


# --------------------------------------------------------------------------- #
# Target book: long illiquid / short liquid quintiles, dollar+beta neutral
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StampFeatures:
    """Per-stamp feature snapshot for one stamp (features + diagnostics)."""

    decision_ns: int
    features: Dict[str, float]
    betas: Dict[str, float]
    diagnostics: Dict[str, Any]


def compute_stamp_features(
    *,
    bars_by_symbol: Mapping[str, Sequence[Any]],
    universe: Sequence[str],
    benchmark_symbol: str,
    decision_ns: int,
    formation_days: int,
) -> StampFeatures:
    """PIT features + frozen 90d betas + confound diagnostics at one stamp."""
    benchmark_bars = bars_by_symbol.get(str(benchmark_symbol)) or ()
    features: Dict[str, float] = {}
    betas: Dict[str, float] = {}
    for sym in sorted(set(str(s) for s in universe)):
        bars = bars_by_symbol.get(sym) or ()
        if not bars:
            continue
        feature = amihud_feature(
            bars, decision_ns=int(decision_ns), formation_days=int(formation_days)
        )
        if feature is None or not math.isfinite(feature) or feature <= 0.0:
            continue
        beta = trailing_beta(
            bars, benchmark_bars, decision_ns=int(decision_ns)
        )
        if beta is None or not math.isfinite(beta):
            continue
        features[sym] = float(feature)
        betas[sym] = float(beta)
    diagnostics = stamp_diagnostics(
        bars_by_symbol=bars_by_symbol,
        decision_ns=int(decision_ns),
        eligible_symbols=sorted(features),
        features=features,
    )
    return StampFeatures(
        decision_ns=int(decision_ns),
        features=features,
        betas=betas,
        diagnostics=diagnostics,
    )


def build_quintile_book(
    *,
    features: Mapping[str, float],
    betas: Mapping[str, float],
    arm_sign: int,
) -> Dict[str, Any]:
    """Long illiquid / short liquid quintiles; dollar- and beta-neutral.

    Equal weights inside each quintile tail bucket (``+1/q`` long,
    ``-1/q`` short, ``q = ceil(n/5)``), then the frozen beta hedge: the
    pre-hedge book beta is ``B0 = mean(beta_long_leg) - mean(beta_short_leg)``;
    the hedge tilts each leg weight by a beta-rank-symmetric amount
    ``delta_i = +-theta/q`` with
    ``theta = |B0| / (mean(beta_top) - mean(beta_bottom)) < 1`` over the 2q
    book legs sorted by frozen 90d beta, so ``sum(w) = 0`` and
    ``sum(beta * w) = 0`` hold EXACTLY while every weight keeps its sign and
    stays within ``[(1-theta), (1+theta)]/q`` of the equal-weight base
    (bounded relative tilt, never an ill-conditioned additive projection).
    Any residual cap breach refuses the book (fail closed, deterministic).
    ``arm_sign = -1`` yields the sign-inverted causal control.
    """
    if int(arm_sign) not in (-1, 1):
        raise ContractViolation("arm_sign must be +-1")
    ranked = sorted(features, key=lambda s: (-features[s], s))  # illiquid first
    n = len(ranked)
    if n < MIN_ELIGIBLE:
        return {
            "status": STATUS_SKIP,
            "weights": {},
            "reason_code": "BELOW_MIN_ELIGIBLE",
            "diagnostics": {"n_eligible": n, "min_eligible": MIN_ELIGIBLE},
        }
    q = -(-n // QUINTILES)  # quintile tail bucket size: ceil(n/5) names per side
    longs = ranked[:q]   # most illiquid
    shorts = ranked[n - q :]  # most liquid
    legs = list(longs) + list(shorts)
    n_legs = len(legs)
    w0 = {sym: (1.0 / q if sym in set(longs) else -1.0 / q) for sym in legs}
    beta_legs = {sym: float(betas[sym]) for sym in legs}
    b0 = math.fsum(beta_legs[sym] * w0[sym] for sym in legs)
    by_beta = sorted(legs, key=lambda s: (beta_legs[s], s))
    top = by_beta[n_legs // 2 :]  # q highest-beta legs
    bottom = by_beta[: n_legs // 2]  # q lowest-beta legs
    spread = (
        math.fsum(beta_legs[s] for s in top) / len(top)
        - math.fsum(beta_legs[s] for s in bottom) / len(bottom)
    )
    adjusted: Dict[str, float]
    if spread <= 1e-12:
        if abs(b0) <= 1e-9:
            adjusted = dict(w0)  # constant-beta book is already beta-neutral
        else:
            return {
                "status": STATUS_SKIP,
                "weights": {},
                "reason_code": "BETA_NEUTRAL_INFEASIBLE",
                "diagnostics": {"book_beta_pre_hedge": b0, "n_legs": n_legs},
            }
    else:
        theta = abs(b0) / spread
        if theta >= 1.0:
            return {
                "status": STATUS_SKIP,
                "weights": {},
                "reason_code": "BETA_HEDGE_TILT_GE_1",
                "diagnostics": {
                    "book_beta_pre_hedge": b0,
                    "beta_leg_spread": spread,
                    "theta": theta,
                },
            }
        # delta must satisfy sum(delta) = 0 and sum(beta * delta) = -B0 exactly.
        tilt_sign = -1.0 if b0 > 0.0 else 1.0
        adjusted = {}
        for sym in legs:
            delta = tilt_sign * theta / q if sym in set(top) else -tilt_sign * theta / q
            adjusted[sym] = w0[sym] + delta
    for sym in legs:
        expected = 1.0 if sym in set(longs) else -1.0
        if float(adjusted[sym]) * expected <= 0.0:
            return {
                "status": STATUS_SKIP,
                "weights": {},
                "reason_code": "BETA_HEDGE_SIGN_FLIP",
                "diagnostics": {"symbol": sym, "n_legs": n_legs},
            }
    gross = math.fsum(abs(v) for v in adjusted.values())
    if gross <= 0.0:
        return {
            "status": STATUS_SKIP,
            "weights": {},
            "reason_code": "DEGENERATE_BOOK",
            "diagnostics": {},
        }
    sign = float(arm_sign)
    weights = {
        sym: adjusted[sym] / gross * sign for sym in legs
    }
    cap_breaches = sorted(
        sym for sym, w in weights.items() if abs(w) > CAP + 1e-9
    )
    if cap_breaches:
        return {
            "status": STATUS_SKIP,
            "weights": {},
            "reason_code": "WEIGHT_CAP_BREACH",
            "diagnostics": {"symbols": cap_breaches},
        }
    net = math.fsum(weights.values())
    book_beta = math.fsum(beta_legs[sym] * weights[sym] for sym in legs)
    return {
        "status": STATUS_OK,
        "weights": weights,
        "reason_code": None,
        "diagnostics": {
            "n_eligible": n,
            "quintile_size": q,
            "long_leg": list(longs),
            "short_leg": list(shorts),
            "net_exposure": net,
            "book_beta_post_hedge": book_beta,
            "book_beta_pre_hedge": b0,
        },
    }
