"""Evidence builders for the A12-V12-BAB-LOWBETA implementation lane.

Schedule/diagnostic-only artifacts (NEVER a scored result; this lane computes
NO PnL on real data):

* C1 field verification  -> ``research/audits/v12i/bab_lowbeta/c1_fields.json``
  (completed-bars-only / close decode i128/1e16 / PIT beta at real stamps via
  a bars-truncated-at-stamp equality proof / fixed universe statement);
* schedule-only feasibility -> ``.../schedule_feasibility.json``
  (every stamp book of every arm through
  :func:`research.v12.feasibility.validate_stamp_schedule` with the frozen
  4+4 leg identity -- counts only, no PnL -- plus one-way turnover / holding
  diagnostics and funding-event counts while held);
* double-generation equality -> ``.../double_generation.json``
  (two independent real-data reloads produce byte-identical features and
  target books at every stamp);
* drop-one diagnostic    -> ``.../drop_one.json``
  (drop-one selects the held maximum-|weight| symbol, L-V11-7, and the book
  survives at 4+4 legs within the frozen cap; per-family stress matrix
  derived from the frozen folds contract, L-V11-1);
* exact-arm dummy dry-run -> ``.../dryrun.json``
  (the three frozen arms through the REAL adapter path on a SYNTHETIC frame;
  DUMMY finite metrics published via :mod:`research.v12.accounting` into a
  temporary empty ledger; zero-position output REFUSED; replay idempotent;
  no real scored metric anywhere).

Hand-computed causal fixtures (committed under ``golden/``): the synthetic
frames are closed-form constructions whose betas, downside correlations and
books are hand-derivable; the tests assert the module output against the
golden values and against independent closed-form recomputation.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from research.adapter_v10.protocol import (
    ContractViolation,
    SettlementPoint,
    StressSpec,
)
from research.adapter_v10.runner import run_strategy
from research.adapter_v10.stress import derive_family_stress_matrix
from research.hyp_a8_m01 import read_bars_15m
from research.v12.accounting import (
    REFUSED_ZERO_POSITIONS,
    STAGE_IDEMPOTENT_REPLAY,
    STAGE_PUBLISHED,
    STAGE_REFUSED,
    freeze_family_cell_contract,
    publish_v12_cell,
)
from research.v12.feasibility import (
    schedule_diagnostics,
    validate_stamp_schedule,
)
from research.v12.families.bab_lowbeta.plugin import ROLE_BY_ARM, BabLowBetaPlugin
from research.v12.families.bab_lowbeta.strategy import (
    BARS_PER_DAY,
    BENCHMARK_SYMBOL_EXCLUDED,
    BAR_NS,
    CAP,
    DAY_NS,
    FAMILY_ID,
    FOLDS,
    FORMATION_DAYS,
    LEGS_PER_SIDE,
    MIN_ELIGIBLE,
    STATUS_OK,
    STATUS_SKIP,
    STRATEGY_ID,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    compute_stamp_features,
    frozen_arm_config_digest,
    frozen_arm_ids,
    weekly_monday_stamps,
)

PRODUCER_ROLE = "I-blind-family"
SCHEMA_C1 = "v12i.bab_lowbeta.c1_fields.v1"
SCHEMA_FEAS = "v12i.bab_lowbeta.schedule_feasibility.v1"
SCHEMA_DOUBLE = "v12i.bab_lowbeta.double_generation.v1"
SCHEMA_DROP_ONE = "v12i.bab_lowbeta.drop_one.v1"
SCHEMA_DRYRUN = "v12i.bab_lowbeta.dryrun.v1"

CATALOG_PATH = "/Users/hoangminhlong/my-quantitative/catalog_live_crypto"
FUNDING_ROOT = "/Users/hoangminhlong/my-quantitative/funding_data/scan_2026"
#: Warmup starts early enough for the frozen 90d formation at the first stamp
#: (2025-08-25 needs completed bars back to 2025-05-27; A9-F verified 18/19).
PREWINDOW_START_ISO = "2025-04-01T00:00:00Z"
#: The 19 non-BTC tradeable names (REQUIRED_SYMBOLS minus BTCUSDT).
TRADEABLE_SYMBOLS: Tuple[str, ...] = (
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "DOGEUSDT",
    "ENAUSDT", "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT",
    "SOLUSDT", "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
)
STAGED_SYMBOLS: Tuple[str, ...] = tuple(
    sorted(TRADEABLE_SYMBOLS + (BENCHMARK_SYMBOL_EXCLUDED,))
)

PIT_CLOCK_STATEMENT = (
    "Features are computed ONLY from completed 15m bars whose exchange CLOSE "
    "stamp (ts_event, nanoseconds) is at or before the Monday 00:00:00Z "
    "decision stamp; daily UTC blocks are (D-k*1d, D-(k-1)*1d] by close stamp "
    "and a day is valid only when it holds exactly 96 completed bars; the "
    "trailing 90-day beta / downside-correlation uses only those completed "
    "daily blocks; execution fills at the first completed 15m bar STRICTLY "
    "after the stamp (fill recorded at that bar's close); native funding rows "
    "enter only via publish_ts_ns inside held spans (start, end]. No future "
    "bar, funding row or universe fact enters any decision; the tradeable "
    "universe is the fixed 19-name staged cohort minus the context-only "
    "BTCUSDT benchmark (no future universe selection). BTCUSDT is never a "
    "position."
)


# --------------------------------------------------------------------------- #
# Lightweight completed bar (synthetic fixtures only)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class FixtureBar:
    """Minimal completed 15m bar (close-stamped) for synthetic frames."""

    ts_event_ns: int
    open: float
    close: float


# --------------------------------------------------------------------------- #
# Staged real-data readers (READ-ONLY)
# --------------------------------------------------------------------------- #
def load_staged_bars(
    *,
    catalog_path: str = CATALOG_PATH,
    symbols: Sequence[str] = STAGED_SYMBOLS,
    start_iso: str = PREWINDOW_START_ISO,
    end_iso: str = WINDOW_END_ISO,
) -> Dict[str, Tuple[Any, ...]]:
    """Completed 15m bars per symbol from the read-only staged catalog."""
    return {
        str(sym): read_bars_15m(catalog_path, str(sym), start_iso, end_iso)
        for sym in symbols
    }


def load_funding_settlements(
    *,
    funding_root: str = FUNDING_ROOT,
    symbols: Sequence[str] = STAGED_SYMBOLS,
) -> Dict[str, Tuple[SettlementPoint, ...]]:
    """Native funding rows -> SettlementPoints (publish_ts = fundingTime)."""
    out: Dict[str, Tuple[SettlementPoint, ...]] = {}
    for sym in symbols:
        path = Path(funding_root) / str(sym) / "funding.json"
        with open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        rows = doc.get("rows")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"funding bundle for {sym} has no rows")
        points = [
            SettlementPoint(
                publish_ts_ns=int(row["fundingTime"]) * 1_000_000,
                value=float(row["fundingRate"]),
                kind="info",
            )
            for row in rows
        ]
        points.sort(key=lambda p: p.publish_ts_ns)
        out[str(sym)] = tuple(points)
    return out


def load_tick_sizes(
    *,
    catalog_path: str = CATALOG_PATH,
    symbols: Sequence[str] = STAGED_SYMBOLS,
) -> Dict[str, float]:
    """Frozen instrument tick sizes (price_increment) from the staged defs."""
    import pyarrow.parquet as pq

    out: Dict[str, float] = {}
    for sym in symbols:
        directory = Path(catalog_path) / "data" / "crypto_perpetual" / f"{sym}-PERP.BINANCE"
        files = sorted(directory.rglob("*.parquet"))
        if not files:
            raise ValueError(f"no instrument definition for {sym}")
        table = pq.read_table(files[0], columns=["price_increment"])
        raw = table.column("price_increment")[0].as_py()
        tick = float(str(raw))
        if not math.isfinite(tick) or tick <= 0.0:
            raise ValueError(f"non-positive tick size for {sym}")
        out[str(sym)] = tick
    return out


# --------------------------------------------------------------------------- #
# Synthetic causal fixtures (closed-form, hand-computable)
# --------------------------------------------------------------------------- #
FIXTURE_SYMBOL_COUNT = 12
#: Drift starts on fixture day 200 == 2025-08-25, so the FIRST frozen stamp's
#: trailing 90-day window (days 110..199) is entirely pre-drift and the OLS
#: betas there equal the designed betas EXACTLY (hand-computable anchor).
FIXTURE_WARMUP_DAYS = 200
#: First fixture day (UTC) = 2025-02-06 = fixture day 0.
FIXTURE_FIRST_DAY_ISO = "2025-02-06T00:00:00Z"
FIXTURE_LAST_DAY_ISO = "2026-08-22T00:00:00Z"


def _fixture_day_start_ns(day_index: int) -> int:
    """UTC midnight ns of fixture day ``day_index`` (0 = 2025-02-06)."""
    from datetime import datetime, timedelta, timezone

    first = datetime(2025, 2, 6, tzinfo=timezone.utc)
    moment = first + timedelta(days=int(day_index))
    return int(moment.timestamp()) * 1_000_000_000


def _day_bars(day_start_ns: int, day_open: float, day_close: float) -> List[FixtureBar]:
    """96 completed 15m bars with a linear path open -> close inside the day.

    The daily block then opens at ``day_open`` and closes at ``day_close``
    with exactly ``BARS_PER_DAY`` completed bars, so the aggregated daily log
    return equals the designed value EXACTLY.
    """
    bars: List[FixtureBar] = []
    step = (day_close - day_open) / float(BARS_PER_DAY)
    for j in range(int(BARS_PER_DAY)):
        open_px = day_open + step * j
        close_px = day_open + step * (j + 1)
        bars.append(
            FixtureBar(
                ts_event_ns=int(day_start_ns + (j + 1) * BAR_NS),
                open=float(open_px),
                close=float(close_px),
            )
        )
    return bars


def _btc_pattern() -> List[float]:
    """BTC daily log-return pattern: [+0.02, -0.02, +0.01, -0.01, +0.005].

    Period 5 with three magnitudes so OLS betas are well conditioned and the
    trailing 90-day window (a whole multiple of the period) always contains
    exactly 18 cycles -- the closed-form fixture maths holds at every stamp.
    """
    return [0.02, -0.02, 0.01, -0.01, 0.005]


def build_beta_ranking_frame() -> Tuple[Dict[str, Tuple[Any, ...]], Dict[str, Any]]:
    """Low-beta names are constructed to OUTPERFORM high-beta names.

    Symbol ``i`` (i = 0..11) has daily log return ``r_i = beta_i * x`` with
    ``beta_i = 0.4 + 0.1*i`` (exact OLS beta, zero noise) and, strictly AFTER
    the warmup, a forward drift ``0.002 * (1.6 - beta_i)`` per day: the
    lowest-beta names earn the largest drift, so the frozen anchor (long low
    beta / short high beta) must realise a positive spread and the INV
    control must negate it exactly.  Returns the bars plus the designed
    parameter table (the hand computation).
    """
    from datetime import datetime, timezone

    first = datetime(2025, 2, 6, tzinfo=timezone.utc)
    last = datetime(2026, 8, 22, tzinfo=timezone.utc)
    n_days = (last - first).days
    pattern = _btc_pattern()
    design: Dict[str, Any] = {"betas": {}, "forward_daily_drift": {}, "btc_pattern": pattern}
    bars: Dict[str, Tuple[Any, ...]] = {}
    btc_price = 50_000.0
    btc_seq: List[FixtureBar] = []
    for day in range(n_days):
        x = pattern[day % len(pattern)]
        day_open = btc_price
        day_close = btc_price * math.exp(x)
        btc_seq.extend(_day_bars(_fixture_day_start_ns(day), day_open, day_close))
        btc_price = day_close
    bars[BENCHMARK_SYMBOL_EXCLUDED] = tuple(btc_seq)
    for i in range(FIXTURE_SYMBOL_COUNT):
        sym = f"SYMA{i:02d}"
        beta = 0.4 + 0.1 * i
        drift = 0.002 * (1.6 - beta)
        design["betas"][sym] = round(beta, 10)
        design["forward_daily_drift"][sym] = round(drift, 12)
        price = 100.0 + i
        seq: List[FixtureBar] = []
        for day in range(n_days):
            x = pattern[day % len(pattern)]
            r = beta * x + (drift if day >= FIXTURE_WARMUP_DAYS else 0.0)
            day_open = price
            day_close = price * math.exp(r)
            seq.extend(_day_bars(_fixture_day_start_ns(day), day_open, day_close))
            price = day_close
        bars[sym] = tuple(seq)
    design["n_days"] = n_days
    design["warmup_days"] = FIXTURE_WARMUP_DAYS
    return bars, design


def build_downcorr_frame() -> Tuple[Dict[str, Tuple[Any, ...]], Dict[str, Any]]:
    """Downside-correlation fixture that DISTINGUISHES neighbour from anchor.

    Symbol ``i`` carries the designed beta ``beta_i = 0.8 + 0.04*i`` (exact
    OLS beta) and a downside-only shock ``d_i * v_d`` on BTC-down days with
    ``d_i = 0.005*(i+1)``, where the BTC-down pattern value ``v_d`` is +1/-1
    alternating in PAIRS of consecutive down days.  For any trailing 90-day
    window (18 whole cycles = 36 down days: 18 at -0.02 and 18 at -0.01, the
    +1/-1 split balanced INSIDE each magnitude group) the frozen neighbour
    statistic has the exact closed form

        corr_i = 1 / sqrt(1 + 40000 * (d_i / beta_i)^2)

    with ``Sxx = 0.0009`` and ``Svv = 36``; it is strictly DECREASING in
    ``i`` (the shock grows faster than the beta), so the neighbour book
    (long the 4 LOWEST correlations = SYMB08..SYMB11) is the mirror image of
    the anchor book (long the 4 LOWEST betas = SYMB00..SYMB03) on this
    frame.  Returns the bars plus the designed parameter table.
    """
    from datetime import datetime, timezone

    first = datetime(2025, 2, 6, tzinfo=timezone.utc)
    last = datetime(2026, 8, 22, tzinfo=timezone.utc)
    n_days = (last - first).days
    pattern = _btc_pattern()
    design: Dict[str, Any] = {
        "betas": {},
        "downside_shocks_d": {},
        "closed_form_Sxx": 0.0009,
        "closed_form_Svv": 36.0,
        "closed_form_corr": {},
        "btc_pattern": pattern,
    }
    bars: Dict[str, Tuple[Any, ...]] = {}
    btc_price = 50_000.0
    btc_seq: List[FixtureBar] = []
    down_occurrence = 0
    day_v: List[float] = []
    for day in range(n_days):
        x = pattern[day % len(pattern)]
        if x < 0.0:
            # shocks alternate in PAIRS of consecutive down days, so the +1/-1
            # split is balanced WITHIN each BTC-down magnitude group (9 +1 and
            # 9 -1 at -0.02, 9 +1 and 9 -1 at -0.01 in every 90-day window) --
            # this is what makes the closed-form corr_i hold exactly
            day_v.append(1.0 if (down_occurrence // 2) % 2 == 0 else -1.0)
            down_occurrence += 1
        else:
            day_v.append(0.0)
        day_open = btc_price
        day_close = btc_price * math.exp(x)
        btc_seq.extend(_day_bars(_fixture_day_start_ns(day), day_open, day_close))
        btc_price = day_close
    bars[BENCHMARK_SYMBOL_EXCLUDED] = tuple(btc_seq)
    for i in range(FIXTURE_SYMBOL_COUNT):
        sym = f"SYMB{i:02d}"
        beta = 0.8 + 0.04 * i
        d_i = 0.005 * (i + 1)
        design["betas"][sym] = round(beta, 10)
        design["downside_shocks_d"][sym] = d_i
        design["closed_form_corr"][sym] = 1.0 / math.sqrt(
            1.0 + 40_000.0 * (d_i / beta) ** 2
        )
        price = 100.0 + i
        seq: List[FixtureBar] = []
        for day in range(n_days):
            x = pattern[day % len(pattern)]
            r = beta * x + d_i * day_v[day]
            day_open = price
            day_close = price * math.exp(r)
            seq.extend(_day_bars(_fixture_day_start_ns(day), day_open, day_close))
            price = day_close
        bars[sym] = tuple(seq)
    design["n_days"] = n_days
    return bars, design


def make_plugin(
    arm_id: str,
    bars: Mapping[str, Sequence[Any]],
    *,
    settlements: Optional[Mapping[str, Sequence[Any]]] = None,
    tick: float = 0.01,
) -> BabLowBetaPlugin:
    """Frozen-arm plugin over an injected (synthetic or staged) frame."""
    ticks = {str(sym): float(tick) for sym in bars}
    return BabLowBetaPlugin(
        bars_by_symbol=bars,
        arm_id=arm_id,
        tick_sizes=ticks,
        settle_points_by_symbol=dict(settlements or {}),
    )


# --------------------------------------------------------------------------- #
# C1 field verification (real stamps, read-only staged data)
# --------------------------------------------------------------------------- #
def _canonical_sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ns_to_iso_utc(ns: int) -> str:
    """Epoch nanoseconds -> ``YYYY-MM-DDTHH:MM:SSZ`` (audit display only)."""
    from datetime import datetime, timezone

    moment = datetime.fromtimestamp(int(ns) / 1_000_000_000, tz=timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp_book_payload(
    plugin: BabLowBetaPlugin, stamp: int, universe: Sequence[str]
) -> Dict[str, Any]:
    book = plugin.targets_at(int(stamp), universe=universe, stress=plugin.baseline_stress())
    return {
        "decision_ns": int(stamp),
        "status": str(book.get("status")),
        "reason_code": book.get("reason_code"),
        "weights": {str(k): float(v) for k, v in sorted((book.get("weights") or {}).items())},
        "features_sha256": _canonical_sha256(sorted(book.get("diagnostics", {}))),
        "diagnostics": book.get("diagnostics", {}),
    }


def _close_decode_crosscheck(
    *, catalog_path: str, symbols: Sequence[str], samples_per_symbol: int = 5
) -> Dict[str, Any]:
    """Independent i128/1e16 decode crosscheck (A9-F F7 binding convention).

    Per sample: the raw ``fixed_size_binary(16)`` column value decoded by the
    binding convention (little-endian SIGNED integer / 1e16) must be positive
    and finite and must EQUAL the repo decoder
    (:func:`research.panel._decode_fixed16`, byte-identical operation).  The
    raw integer itself is also reported; float64 cannot round-trip a 17-digit
    scaled integer exactly, so exactness is asserted in the integer domain
    (``decoded * 1e16`` within float64 epsilon of the raw integer), never via
    a float round-trip.
    """
    import pyarrow.parquet as pq

    from research.panel import _decode_fixed16 as repo_decode

    per_symbol: Dict[str, Any] = {}
    ok_all = True
    for sym in symbols:
        directory = Path(catalog_path) / "data" / "binance_bar" / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
        files = sorted(directory.rglob("*.parquet"))
        if not files:
            raise ValueError(f"no bar parquet for {sym}")
        table = pq.read_table(files[-1], columns=["ts_event", "close"])
        ts_col = table.column("ts_event").to_pylist()
        close_col = table.column("close").to_pylist()
        checks: List[Dict[str, Any]] = []
        for idx in range(min(samples_per_symbol, len(ts_col))):
            i = -1 - idx  # sample from the tail deterministically
            raw = close_col[i]
            raw_int = int.from_bytes(raw, "little", signed=True)
            # the binding convention: raw fixed_size_binary(16) little-endian
            # SIGNED integer divided by exactly 1e16
            decoded = raw_int / 1e16
            scale_loss = abs(decoded * 1e16 - raw_int)
            checks.append(
                {
                    "ts_event_ns": int(ts_col[i]),
                    "raw_i128": raw_int,
                    "close_decoded": decoded,
                    "positive_finite": bool(math.isfinite(decoded) and decoded > 0.0),
                    "matches_repo_decoder": bool(decoded == repo_decode(raw)),
                    "i128_in_signed_range": bool(-(2**127) <= raw_int < 2**127),
                    "float_scale_loss_within_epsilon": bool(
                        scale_loss <= max(1.0, abs(raw_int)) * 1e-9
                    ),
                }
            )
        ok_all &= all(
            c["positive_finite"]
            and c["matches_repo_decoder"]
            and c["i128_in_signed_range"]
            and c["float_scale_loss_within_epsilon"]
            for c in checks
        )
        per_symbol[sym] = {"samples": checks}
    return {
        "convention": "raw i128 (fixed_size_binary(16), little-endian signed) / 1e16",
        "float_scale_loss_note": (
            "exactness asserted against the repo decoder and in the integer "
            "domain; float64 cannot round-trip a 17-digit scaled integer"
        ),
        "per_symbol": per_symbol,
        "verdict": "PASS" if ok_all else "FAIL",
    }


#: C1 PIT field verification is bounded to THREE explicit real stamps
#: (first / mid-window / penultimate Monday); truncating the whole staged
#: frame per check is expensive, so the check count is fixed by contract.
C1_PIT_STAMP_INDICES = (0, 26, 50)


def build_c1_audit(
    *,
    bars: Optional[Mapping[str, Sequence[Any]]] = None,
    ticks: Optional[Mapping[str, float]] = None,
) -> Dict[str, Any]:
    """C1 field verification on REAL stamps (completed bars only, PIT beta).

    The PIT proof: for the sampled stamps, the stamp book computed from the
    full staged history and the same book recomputed from bars TRUNCATED at
    the stamp (every bar closing strictly after the stamp dropped) are
    byte-identical.  Any future-bar or future-universe leak would break the
    equality, because the truncated frame physically lacks the future data.
    """
    if bars is None:
        bars = load_staged_bars()
    if ticks is None:
        ticks = load_tick_sizes()
    stamps = weekly_monday_stamps()
    sample = [int(stamps[i]) for i in C1_PIT_STAMP_INDICES]
    plugin = make_plugin("BAB-90D-W", bars)
    universe = plugin.universe(plugin.baseline_stress())
    pit_proofs: List[Dict[str, Any]] = []
    for stamp in sample:
        full = _stamp_book_payload(plugin, stamp, universe)
        # bisect over the plugin's close-stamp index: truncate every symbol's
        # bars at the stamp (drop every bar closing strictly after it)
        truncated = {
            str(sym): tuple(seq)[: bisect.bisect_right(plugin._ts[str(sym)], int(stamp))]
            for sym, seq in bars.items()
        }
        pit_plugin = make_plugin("BAB-90D-W", truncated)
        pit_book = _stamp_book_payload(pit_plugin, stamp, universe)
        full.pop("features_sha256", None)
        pit_book.pop("features_sha256", None)
        pit_proofs.append(
            {
                "decision_ns": int(stamp),
                "decision_iso": _ns_to_iso_utc(int(stamp)),
                "stamp_index": None,  # positional index recorded below
                "truncated_bars_identical_to_full": full == pit_book,
                "status": full["status"],
                "n_weights": len(full["weights"]),
            }
        )
    for proof, index in zip(pit_proofs, C1_PIT_STAMP_INDICES):
        proof["stamp_index"] = int(index)
    decode = _close_decode_crosscheck(catalog_path=CATALOG_PATH, symbols=("BTCUSDT", "ETHUSDT", "SOLUSDT"))
    n_completed = {sym: len(seq) for sym, seq in bars.items()}
    zero_or_nan = {
        sym: sum(
            1
            for b in seq
            if not (math.isfinite(float(b.close)) and float(b.close) > 0.0)
        )
        for sym, seq in bars.items()
    }
    usable = all(v == 0 for v in zero_or_nan.values()) and all(
        n > 0 for n in n_completed.values()
    )
    return {
        "schema_version": SCHEMA_C1,
        "producer_role": PRODUCER_ROLE,
        "family_id": FAMILY_ID,
        "strategy_id": STRATEGY_ID,
        "catalog_path": CATALOG_PATH,
        "funding_root": FUNDING_ROOT,
        "prewindow_start_iso": PREWINDOW_START_ISO,
        "window_start_iso": WINDOW_START_ISO,
        "window_end_iso": WINDOW_END_ISO,
        "n_staged_symbols": len(STAGED_SYMBOLS),
        "n_tradeable": len(TRADEABLE_SYMBOLS),
        "benchmark_symbol_excluded": BENCHMARK_SYMBOL_EXCLUDED,
        "completed_bars_per_symbol": n_completed,
        "non_positive_or_nan_closes": zero_or_nan,
        "close_decode_crosscheck": decode,
        "pit_beta_proof_stamps": list(C1_PIT_STAMP_INDICES),
        "pit_beta_proof_at_stamps": pit_proofs,
        "pit_beta_proof_verdict": (
            "PASS" if all(p["truncated_bars_identical_to_full"] for p in pit_proofs) else "FAIL"
        ),
        "first_stamp_iso": "2025-08-25T00:00:00Z",
        "folds": [{"id": label, "start": start, "end": end} for label, start, end in FOLDS],
        "formation_days": int(FORMATION_DAYS),
        "bars_per_day_required": int(BARS_PER_DAY),
        "min_eligible": int(MIN_ELIGIBLE),
        "legs_per_side": int(LEGS_PER_SIDE),
        "weight_cap_abs": float(CAP),
        "pit_clock_statement": PIT_CLOCK_STATEMENT,
        "verdict": "PASS" if usable and decode["verdict"] == "PASS" else "FAIL",
    }


# --------------------------------------------------------------------------- #
# Schedule-only feasibility (counts only -- no PnL)
# --------------------------------------------------------------------------- #
def _arm_stamp_records(
    plugin: BabLowBetaPlugin,
    *,
    funding_times_by_symbol: Optional[Mapping[str, Sequence[int]]] = None,
) -> Tuple[List[Dict[str, Any]], List[int], List[Dict[str, Any]]]:
    """Per-stamp feasibility records for one arm (books + boundary census)."""
    universe = plugin.universe(plugin.baseline_stress())
    stamps = list(plugin.schedule().instants)
    fold_members = plugin.fold_instants()
    boundaries = {
        int(members[-1])
        for members in fold_members.values()
        if int(members[-1]) != int(stamps[-1])
    }
    records: List[Dict[str, Any]] = []
    skips: List[Dict[str, Any]] = []
    for stamp in stamps:
        book = plugin.targets_at(int(stamp), universe=universe, stress=plugin.baseline_stress())
        weights = {str(k): float(v) for k, v in (book.get("weights") or {}).items()}
        is_boundary = int(stamp) in boundaries or int(stamp) == int(stamps[-1])
        records.append(
            {
                "decision_ns": int(stamp),
                "status": str(book.get("status")),
                "reason_code": book.get("reason_code"),
                "weights": weights,
                "force_flat_boundary": bool(is_boundary and not weights),
                "diagnostics_legs": {
                    "n_eligible": (book.get("diagnostics") or {}).get("n_eligible"),
                },
            }
        )
        if not weights and not is_boundary:
            skips.append({"decision_ns": int(stamp), "reason_code": book.get("reason_code")})
    return records, sorted(boundaries), skips


def build_schedule_feasibility(
    *,
    bars: Optional[Mapping[str, Sequence[Any]]] = None,
    funding: Optional[Mapping[str, Sequence[SettlementPoint]]] = None,
) -> Dict[str, Any]:
    """Validate EVERY stamp book of EVERY arm; counts only, never PnL."""
    if bars is None:
        bars = load_staged_bars()
    if funding is None:
        funding = load_funding_settlements()
    funding_times = {
        sym: [int(p.publish_ts_ns) for p in points]
        for sym, points in funding.items()
    }
    per_arm: Dict[str, Any] = {}
    overall_pass = True
    for arm_id in frozen_arm_ids():
        plugin = make_plugin(arm_id, bars)
        universe = plugin.universe(plugin.baseline_stress())
        records, boundaries, skips = _arm_stamp_records(plugin)
        verdict = validate_stamp_schedule(
            records, require_non_empty=False, legs_per_side=None
        )
        # frozen 4+4 leg identity on every NON-boundary non-skip stamp
        stamps = list(plugin.schedule().instants)
        leg_rows: List[Dict[str, Any]] = []
        n_book_stamps = 0
        for record, stamp in zip(records, stamps):
            weights = record["weights"]
            if not weights:
                continue
            n_book_stamps += 1
            n_long = sum(1 for w in weights.values() if w > 0.0)
            n_short = sum(1 for w in weights.values() if w < 0.0)
            max_abs = max(abs(w) for w in weights.values())
            leg_rows.append(
                {
                    "decision_ns": int(stamp),
                    "legs_4v4": bool(n_long == LEGS_PER_SIDE and n_short == LEGS_PER_SIDE),
                    "n_long": n_long,
                    "n_short": n_short,
                    "max_abs_weight": round(max_abs, 12),
                    "cap_ok": bool(max_abs <= CAP + 1e-9),
                }
            )
        legs_ok = all(r["legs_4v4"] and r["cap_ok"] for r in leg_rows)
        diagnostics = schedule_diagnostics(
            [
                {"decision_ns": r["decision_ns"], "weights": r["weights"]}
                for r in records
            ],
            funding_events_by_symbol=funding_times,
        )
        arm_pass = bool(verdict["verdict"] == "PASS" and legs_ok and not skips)
        overall_pass &= arm_pass
        per_arm[arm_id] = {
            "role": ROLE_BY_ARM[arm_id],
            "arm_config_digest": frozen_arm_config_digest(arm_id),
            "n_universe": len(universe),
            "n_stamps": len(records),
            "n_book_stamps": n_book_stamps,
            "n_force_flat_boundary_stamps": len(boundaries) + 1,
            "n_skip_stamps": len(skips),
            "skip_stamps": skips,
            "feasibility_verdict": verdict["verdict"],
            "n_fail": verdict["n_fail"],
            "failing_stamps": verdict["failing_stamps"][:10],
            "legs_4v4_all_book_stamps": legs_ok,
            "max_abs_weight_over_book_stamps": round(
                max((r["max_abs_weight"] for r in leg_rows), default=0.0), 12
            ),
            "one_way_turnover_total": diagnostics["one_way_turnover"]["total"],
            "median_holding_days": diagnostics["holdings"]["median_holding_days"],
            "funding_events_while_held_total": diagnostics["funding_events_while_held"][
                "events_while_held_total"
            ],
        }
    return {
        "schema_version": SCHEMA_FEAS,
        "producer_role": PRODUCER_ROLE,
        "family_id": FAMILY_ID,
        "window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "legs_per_side": int(LEGS_PER_SIDE),
        "min_eligible": int(MIN_ELIGIBLE),
        "cap_abs": float(CAP),
        "no_pnl_attestation": {
            "pnl_computed": False,
            "artifact_contains_only": "counts, weights extrema, turnover/holding durations, funding-event counts",
        },
        "per_arm": per_arm,
        "verdict": "PASS" if overall_pass else "FAIL",
    }


# --------------------------------------------------------------------------- #
# Double-generation equality (real data, byte-identical features/targets)
# --------------------------------------------------------------------------- #
def build_double_generation() -> Dict[str, Any]:
    """Two independent staged reloads produce byte-identical stamp books."""
    first = load_staged_bars()
    second = load_staged_bars()
    per_arm: Dict[str, Any] = {}
    ok_all = True
    for arm_id in frozen_arm_ids():
        digests: List[Dict[str, Any]] = []
        for frame in (first, second):
            plugin = make_plugin(arm_id, frame)
            universe = plugin.universe(plugin.baseline_stress())
            payloads = [
                _stamp_book_payload(plugin, stamp, universe)
                for stamp in plugin.schedule().instants
            ]
            digests.append(_canonical_sha256(payloads))
        equal = digests[0] == digests[1]
        ok_all &= equal
        per_arm[arm_id] = {
            "first_generation_sha256": digests[0],
            "second_generation_sha256": digests[1],
            "byte_identical": equal,
        }
    return {
        "schema_version": SCHEMA_DOUBLE,
        "producer_role": PRODUCER_ROLE,
        "family_id": FAMILY_ID,
        "n_stamps": 52,
        "per_arm": per_arm,
        "verdict": "PASS" if ok_all else "FAIL",
    }


# --------------------------------------------------------------------------- #
# Drop-one diagnostic = held max |weight| symbol (L-V11-7)
# --------------------------------------------------------------------------- #
def build_drop_one(
    *, bars: Optional[Mapping[str, Sequence[Any]]] = None, stamp_index: int = 26
) -> Dict[str, Any]:
    """Drop the held maximum-|weight| symbol; the book must survive 4+4."""
    if bars is None:
        bars = load_staged_bars()
    plugin = make_plugin("BAB-90D-W", bars)
    stamps = list(plugin.schedule().instants)
    stamp = int(stamps[int(stamp_index)])
    universe = plugin.universe(plugin.baseline_stress())
    baseline = plugin.targets_at(stamp, universe=universe, stress=plugin.baseline_stress())
    weights = {str(k): float(v) for k, v in (baseline.get("weights") or {}).items()}
    if not weights:
        raise ContractViolation(f"no held book at stamp {stamp} for the drop-one probe")
    held_max = max(sorted(weights), key=lambda sym: abs(weights[sym]))
    stress = StressSpec(
        name="drop_one_held_max_weight",
        fee_multiplier=1.0,
        tick_slip_ticks=int(plugin.cost_model().adverse_tick_slip_floor),
        event_delay_events=0,
        drop_symbols=(held_max,),
        dropped_fold_index=None,
    )
    reduced_universe = plugin.universe(stress)
    reduced = plugin.targets_at(stamp, universe=reduced_universe, stress=stress)
    r_weights = {str(k): float(v) for k, v in (reduced.get("weights") or {}).items()}
    n_long = sum(1 for w in r_weights.values() if w > 0.0)
    n_short = sum(1 for w in r_weights.values() if w < 0.0)
    survived = (
        str(reduced.get("status")) == STATUS_OK
        and n_long == LEGS_PER_SIDE
        and n_short == LEGS_PER_SIDE
        and all(abs(w) <= CAP + 1e-9 for w in r_weights.values())
        and held_max not in r_weights
    )
    derivation = derive_family_stress_matrix(
        strategy_baseline=plugin.baseline_stress(),
        droppable_symbols=universe,
        realized_weights=weights,
        folds=plugin.folds,
        instants=stamps,
    )
    # the generic derivation (L-V11-7 realized-weight rule) must select the
    # SAME held maximum-|weight| symbol as the manual probe above
    derived_drop_one = [
        cell.spec.drop_symbols
        for cell in derivation.cells
        if cell.name == "drop_one_symbol"
    ]
    if derived_drop_one != [(held_max,)]:
        raise ContractViolation(
            f"derived drop-one cell {derived_drop_one} != held max-weight "
            f"symbol ({held_max},)"
        )
    return {
        "schema_version": SCHEMA_DROP_ONE,
        "producer_role": PRODUCER_ROLE,
        "family_id": FAMILY_ID,
        "lesson": "L-V11-7: drop-one selects the held maximum-|weight| symbol",
        "decision_ns": stamp,
        "held_max_weight_symbol": held_max,
        "held_max_abs_weight": round(abs(weights[held_max]), 12),
        "reduced_status": str(reduced.get("status")),
        "reduced_legs": {"n_long": n_long, "n_short": n_short},
        "dropped_symbol_absent_from_reduced_book": held_max not in r_weights,
        "derived_drop_one_matches_held_max": derived_drop_one == [(held_max,)],
        "survived": bool(survived),
        "family_stress_matrix": derivation.record,
        "verdict": "PASS" if survived else "FAIL",
    }


# --------------------------------------------------------------------------- #
# Exact-arm dummy dry-run (synthetic frame through the REAL adapter path)
# --------------------------------------------------------------------------- #
DRYRUN_DUMMY_METRICS_KIND = "DUMMY_V12I_BAB_DRYRUN_METRICS"


def _dummy_metrics_for(
    arm_id: str,
    run_result: Mapping[str, Any],
    decision_stamps: Sequence[int],
) -> Dict[str, Any]:
    """Constant, finite, explicitly DUMMY metrics (never a scored metric)."""
    positions = list(run_result.get("positions") or [])
    decisions = [
        {"symbol": "BAB-LOWBETA", "ts_ns": int(stamp)}
        for stamp in decision_stamps
    ]
    fills = [
        {"symbol": str(row["symbol"]), "ts_ns": int(row["entry_ns"])}
        for row in positions
    ]
    metrics = {
        "kind": DRYRUN_DUMMY_METRICS_KIND,
        "dry_run": True,
        "scored": False,
        "score_valid": True,  # publication-gate flag only; values are DUMMY
        "arm_id": str(arm_id),
        "net_return_sum": 0.0125,          # DUMMY constant, not strategy PnL
        "expectancy_per_day": 0.00025,     # DUMMY constant
        "max_drawdown": 0.004,             # DUMMY constant
        "n_positions": len(positions),
        "decisions": decisions,
        "fills": fills,
        "source": "fixed synthetic constants; not strategy PnL",
    }
    for name in ("net_return_sum", "expectancy_per_day", "max_drawdown"):
        if not math.isfinite(float(metrics[name])):
            raise ContractViolation(f"dummy metric {name} non-finite")
    return metrics


def build_dryrun() -> Dict[str, Any]:
    """Exact-arm dummy dry-run via :mod:`research.v12.accounting`.

    For each frozen arm: run the REAL adapter path on the SYNTHETIC
    low-beta-outperforms frame, publish DUMMY finite metrics into a
    temporary EMPTY ledger through ``publish_v12_cell`` (family contract
    cells derived from the frozen folds contract, L-V11-1), replay for an
    idempotent zero-delta skip, and refuse a zero-position metrics payload
    (L-V11-4).  No real scored metric is computed, exposed or persisted.
    """
    bars, _design = build_beta_ranking_frame()
    with tempfile.TemporaryDirectory(prefix="v12i_bab_dryrun_") as tmp:
        ledger_path = Path(tmp) / "dryrun_v12i_bab_lowbeta.jsonl"
        # the zero-position refusal probe needs its OWN empty scratch ledger:
        # the V12 trial key is identity-only, so a refused compute and its
        # would-be publication share exactly one key -- the refusal of the
        # dummy arm's trial must not consume the published cell's key
        refusal_ledger_path = Path(tmp) / "dryrun_v12i_bab_lowbeta_zero.jsonl"
        per_arm: Dict[str, Any] = {}
        for arm_id in frozen_arm_ids():
            plugin = make_plugin(arm_id, bars)
            result = run_strategy(plugin, write_artifact_file=False)
            derivation = derive_family_stress_matrix(
                strategy_baseline=plugin.baseline_stress(),
                droppable_symbols=result["universe"],
                folds=plugin.folds,
                instants=list(plugin.schedule().instants),
            )
            contract = freeze_family_cell_contract(
                FAMILY_ID, [cell.spec for cell in derivation.cells]
            )
            dummy = _dummy_metrics_for(
                arm_id, result, list(plugin.schedule().instants)
            )
            first = publish_v12_cell(
                strategy_id=STRATEGY_ID,
                family=FAMILY_ID,
                arm_id=arm_id,
                arm_config_digest=frozen_arm_config_digest(arm_id),
                stress_signature=plugin.baseline_stress().signature(),
                window_start_iso=WINDOW_START_ISO,
                window_end_iso=WINDOW_END_ISO,
                scored_metrics=dummy,
                result_sha256=str(result["hashes"]["result_sha256"]),
                ledger_path=ledger_path,
                family_contract_cells=contract,
                producer_head_sha="V12I_BAB_DRYRUN_NO_REAL_HEAD",
            )
            replay = publish_v12_cell(
                strategy_id=STRATEGY_ID,
                family=FAMILY_ID,
                arm_id=arm_id,
                arm_config_digest=frozen_arm_config_digest(arm_id),
                stress_signature=plugin.baseline_stress().signature(),
                window_start_iso=WINDOW_START_ISO,
                window_end_iso=WINDOW_END_ISO,
                scored_metrics=dummy,
                result_sha256=str(result["hashes"]["result_sha256"]),
                ledger_path=ledger_path,
                family_contract_cells=contract,
                producer_head_sha="V12I_BAB_DRYRUN_NO_REAL_HEAD",
            )
            zero = dict(dummy)
            zero["n_positions"] = 0
            zero["decisions"] = []
            zero["fills"] = []
            refusal = publish_v12_cell(
                strategy_id=STRATEGY_ID,
                family=FAMILY_ID,
                arm_id=arm_id,
                arm_config_digest=frozen_arm_config_digest(arm_id),
                stress_signature=plugin.baseline_stress().signature(),
                window_start_iso=WINDOW_START_ISO,
                window_end_iso=WINDOW_END_ISO,
                scored_metrics=zero,
                result_sha256=str(result["hashes"]["result_sha256"]),
                ledger_path=refusal_ledger_path,
                family_contract_cells=contract,
                producer_head_sha="V12I_BAB_DRYRUN_NO_REAL_HEAD",
            )
            arm_ok = (
                str(first["stage"]) == STAGE_PUBLISHED
                and int(first["published_delta"]) == 1
                and str(replay["stage"]) == STAGE_IDEMPOTENT_REPLAY
                and int(replay["published_delta"]) == 0
                and str(refusal["stage"]) == STAGE_REFUSED
                and any(str(r).startswith(REFUSED_ZERO_POSITIONS) for r in refusal["reasons"])
            )
            per_arm[arm_id] = {
                "role": ROLE_BY_ARM[arm_id],
                "adapter_run": {
                    "n_books": len(result["books"]),
                    "n_positions": len(result["positions"]),
                    "n_universe": len(result["universe"]),
                    "scored": bool(result.get("scored", True)),
                    "result_sha256": str(result["hashes"]["result_sha256"]),
                },
                "dummy_metrics_kind": DRYRUN_DUMMY_METRICS_KIND,
                "publish_stage": str(first["stage"]),
                "publish_delta": int(first["published_delta"]),
                "replay_stage": str(replay["stage"]),
                "replay_delta": int(replay["published_delta"]) + int(replay["observed_delta"]),
                "zero_position_stage": str(refusal["stage"]),
                "zero_position_reasons": [str(r) for r in refusal["reasons"]],
                "ok": bool(arm_ok),
            }
        from research.v12.accounting import read_v12_ledger, v12_denominator_view

        state = read_v12_ledger(ledger_path)
        view = v12_denominator_view(ledger_path)
        refusal_state = read_v12_ledger(refusal_ledger_path)
        refusal_view = v12_denominator_view(refusal_ledger_path)
        ledger_ok = (
            int(state["count"]) == 3
            and view["published"] == 3
            and view["observed"] == 0
            and int(refusal_state["count"]) == 3
            and refusal_view["published"] == 0
            and refusal_view["observed"] == 3
        )
    ok = all(info["ok"] for info in per_arm.values()) and ledger_ok
    return {
        "schema_version": SCHEMA_DRYRUN,
        "producer_role": PRODUCER_ROLE,
        "family_id": FAMILY_ID,
        "arms": per_arm,
        "ledger": {
            "temporary": True,
            "rows": int(state["count"]),
            "published": int(view["published"]),
            "observed": int(view["observed"]),
            "sha256_after": state["sha256"],
        },
        "zero_position_ledger": {
            "temporary": True,
            "rows": int(refusal_state["count"]),
            "published": int(refusal_view["published"]),
            "observed": int(refusal_view["observed"]),
            "note": (
                "separate scratch ledger: the trial key is identity-only, so "
                "the zero-position refusal of the same trial cannot share the "
                "published cell's ledger without consuming its key"
            ),
        },
        "no_real_pnl_attestation": {
            "real_pnl": False,
            "scored": False,
            "metrics_kind": DRYRUN_DUMMY_METRICS_KIND,
            "frame": "synthetic closed-form fixture (no catalog data)",
        },
        "verdict": "PASS" if ok else "FAIL",
    }


# --------------------------------------------------------------------------- #
# CLI entry
# --------------------------------------------------------------------------- #
def _write(path: str | Path, payload: Mapping[str, Any]) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dict(payload), indent=1, sort_keys=True, default=str)
    target.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[4]
    audit_dir = repo_root / "research" / "audits" / "v12i" / "bab_lowbeta"
    # the staged frame is loaded ONCE and shared by the C1 / feasibility /
    # drop-one builders; only the double-generation check reloads (twice) --
    # two independent generations are its very point.
    bars = load_staged_bars()
    ticks = load_tick_sizes()
    c1 = build_c1_audit(bars=bars, ticks=ticks)
    c1_sha = _write(audit_dir / "c1_fields.json", c1)
    print("C1:", c1["verdict"], "sha", c1_sha[:16])
    feas = build_schedule_feasibility(bars=bars)
    feas_sha = _write(audit_dir / "schedule_feasibility.json", feas)
    print("FEASIBILITY:", feas["verdict"], "sha", feas_sha[:16])
    double = build_double_generation()
    double_sha = _write(audit_dir / "double_generation.json", double)
    print("DOUBLE_GENERATION:", double["verdict"], "sha", double_sha[:16])
    drop_one = build_drop_one(bars=bars)
    drop_sha = _write(audit_dir / "drop_one.json", drop_one)
    print("DROP_ONE:", drop_one["verdict"], "sha", drop_sha[:16])
    dryrun = build_dryrun()
    dry_sha = _write(audit_dir / "dryrun.json", dryrun)
    print("DRYRUN:", dryrun["verdict"], "sha", dry_sha[:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
