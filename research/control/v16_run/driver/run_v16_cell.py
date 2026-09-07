#!/usr/bin/env python3
"""CRYPTO-V16 I/A8 scored cell driver + sanitized mode (lane A8).

Implements the FROZEN selection artifact
``research/control/v16_run/selection_freeze_v16.json`` VERBATIM (families
CLOSE-DISPLACE-FADE and RUNPERSIST, three arms each) and the frozen output
contracts ``research/control/v16_run/d2/diagnostic_contracts_concretized.json``
validated by ``research/governance/diagnostic_persistability.py``.

CLI (exactly):
    python run_v16_cell.py --family CLOSE-DISPLACE-FADE|RUNPERSIST \
        --arm-id anchor|neighbour|control [--sanitized]

Frozen semantics implemented here (each item traced to its frozen source):

* Arm rules (selection_freeze_v16.json frozen_families[i]["arms"], verbatim
  text digested into ``arm_config_digest``):
  - CLOSE-DISPLACE-FADE anchor:  at end of day t-1, if
    |disp[t-1]| >= rolling 60-day 80th percentile of |disp|, hold
    -sign(disp[t-1]) over day t (FADE), else flat.  disp[t] =
    (last_price[t] - vwap[t]) / (high_price[t] - low_price[t]).
  - CLOSE-DISPLACE-FADE neighbour: same mechanism, rolling 90-day 75th
    percentile of |disp|.
  - CLOSE-DISPLACE-FADE control: exposure-form placebo, identical machinery
    on |ret_z[t-1]| >= rolling 60-day 80th percentile of |ret_z| with
    position -sign(ret_z[t-1]);  ret_z[t] = (last_price[t]/last_price[t-1]
    - 1) / rolling_60d_std(daily returns)  (population std, ddof=0; the
    constant sqrt(60/59) factor a ddof=1 std would introduce scales every
    full-window value identically and cannot change any trigger).
  - RUNPERSIST anchor: identical trigger structure on |run_imb[t-1]| >=
    rolling 60-day 80th percentile of |run_imb|, position
    +sign(run_imb[t-1]) (CONTINUATION).  run_imb[t] =
    (buy_streak_max[t] - sell_streak_max[t]) /
    (buy_streak_max[t] + sell_streak_max[t]).
  - RUNPERSIST neighbour: rolling 90-day 75th percentile of |run_imb|.
  - RUNPERSIST control: reshuffled-interval placebo - the identical anchor
    rule applied to run_imb with day labels permuted within
    2025-10-21..2026-08-21 under numpy default_rng(seed=16), ONE fixed
    permutation shared by both symbols; values inside the span are relabelled
    (marginal distribution preserved), warmup rows before the span are
    untouched, and the rolling quantile is recomputed on the permuted series.
* One-bar lag: the decision at day t uses ONLY rows dated <= t-1.
* Costs (L-V14-0 remediated kernel): taker_fee_bps = 5.0 (frozen adapter
  default), charged EXACTLY ONCE per fill on position transitions only;
  rate_per_unit_notional = taker_fee_bps*1e-4*fee_multiplier
                          + slip_ticks * tick_size / fill_price,
  tick_size = 0.01 (frozen kernel convention for these symbols; the frozen
  selection spec does not state one).  Every fill record carries
  ``cost_fills`` (its charge) and ``cost_holding_terms`` which is EXACTLY
  0.0; the cell marker ``remediated_kernel`` is True and the driver refuses
  the cell if any holding term is nonzero.
* PnL: position(t) * (last_price(t)/last_price(t-1) - 1) * unit notional,
  booked daily (both fills of the 1-day round trip book on the holding day).
* Folds: chronological thirds F0/F1/F2 of the arm's eligible decision days
  (exact ``research.hyp_a8_m01.chronological_folds`` semantics: edges at
  round(i*N/3), trailing 1-day purge), books force-flat at fold boundaries -
  a booked position's exit day is asserted to fall strictly before the next
  fold's first decision day, so no position carries across a purge.
* Stress tiers on booked PnL (frozen V12 convention; T2.0 is the PRIMARY
  gate tier and feeds every gate-bearing diagnostic):
  T1.0 fee x1.0 + 1 tick slip;  T1.5 fee x1.5 + 1 tick slip;
  T2.0 fee x2.0 + 2 ticks slip + 1 event delay (on the daily clock the
  entry fill shifts one day later, exit one day after that; a delayed round
  trip that would cross a fold boundary is force-flattened, never booked).
* Gates (margins per P-2, all on the T2.0 primary book):
  G1 expectancy > 0; G2 PF >= 1.10; G3 >= 2/3 folds positive;
  G4 largest-fold-positive-share <= 0.50 (share of total positive fold PnL
  held by the largest positive fold); G5 MDD <= 0.20;
  G10 neighbour supports (neighbour expectancy > 0);
  G11 control does not reproduce (reproduced = same sign AND
  |control expectancy| >= 0.5x|anchor expectancy|; the recorded margin is
  threshold - value with threshold = 0.5x anchor expectancy);
  G12 novelty |rho| <= 0.20 carrying the measured D2 rho
  (CLOSE-DISPLACE-FADE 0.1438, RUNPERSIST 0.1927).
* SCORED mode emits, per arm, jsonl under results/v16/{family}/{arm}/ with
  EXACTLY the registered canon fields per record (set-equality; extras are
  rejected), plus the family-level dsr_per_period_series.jsonl (canon
  cycle_id/period/returns, taken from the ANCHOR book, the family's
  primary trial).
* SANITIZED mode (--sanitized) emits ONLY
  research/control/v16_run/q_dry_run/{family}/{arm}/decisions.jsonl with
  records {cycle_id, family_id, arm_id, date, decision_taken, symbol} - the
  dry-run surface mirrors the T1.0 base book's booked decisions for every
  (symbol, evaluated decision day).  Zero booked decisions is a HARD
  FAILURE (non-vacuous dry-runs, V8 F-A7-1).
* Determinism: no wall clock, no randomness beyond the frozen seed; two
  runs are byte-identical.

Reads the staged panels, the freeze and the manifest from the repository
that contains this file (independent of cwd); all outputs are written
relative to cwd.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen constants (sources in the module docstring)
# --------------------------------------------------------------------------- #
CYCLE_ID = "CRYPTO-V16"
FAMILIES = ("CLOSE-DISPLACE-FADE", "RUNPERSIST")
ARM_ROLES = ("anchor", "neighbour", "control")
UNIVERSE = ("BTCUSDT", "ETHUSDT")

TAKER_FEE_BPS = 5.0
TICK_SIZE = 0.01
NOTIONAL = 1.0
FOLD_COUNT = 3
PURGE_DAYS = 1

STRESS_TIERS: Dict[str, Dict[str, Any]] = {
    "T1.0": {"fee_multiplier": 1.0, "slip_ticks": 1, "event_delay": 0},
    "T1.5": {"fee_multiplier": 1.5, "slip_ticks": 1, "event_delay": 0},
    "T2.0": {"fee_multiplier": 2.0, "slip_ticks": 2, "event_delay": 1},
}
PRIMARY_TIER = "T2.0"
BENCHMARK_NAME = "BETC-2SYM buy-and-hold"

GATE_PF_THRESHOLD = 1.10
GATE_FOLD_POSITIVE_FRACTION = 2.0 / 3.0
GATE_FOLD_CONCENTRATION = 0.50
GATE_MDD_CEILING = 0.20
GATE_NOVELTY_RHO = 0.20
CONTROL_REPRODUCTION_FRACTION = 0.5
FAMILY_NOVELTY_RHO = {"CLOSE-DISPLACE-FADE": 0.1438, "RUNPERSIST": 0.1927}

RUNPERSIST_PERM_SEED = 16
RUNPERSIST_PERM_SPAN = ("2025-10-21", "2026-08-21")

SCORED_ROOT = "results/v16"
SANITIZED_ROOT = Path("research/control/v16_run/q_dry_run")

# Per-arm frozen parameters (numbers exactly as the frozen arm spec text
# states them; _assert_spec_tokens guards every entry against drift).
ARM_PARAMS: Dict[Tuple[str, str], Dict[str, Any]] = {
    ("CLOSE-DISPLACE-FADE", "anchor"): {
        "series": "disp", "window": 60, "quantile": 80.0, "side": -1,
        "tokens": ("|disp[t-1]|", "60-day 80th percentile", "-sign(disp[t-1])"),
    },
    ("CLOSE-DISPLACE-FADE", "neighbour"): {
        "series": "disp", "window": 90, "quantile": 75.0, "side": -1,
        "tokens": ("90-day 75th percentile", "|disp|", "identical fill/sizing"),
    },
    ("CLOSE-DISPLACE-FADE", "control"): {
        "series": "ret_z", "window": 60, "quantile": 80.0, "side": -1,
        "tokens": ("|ret_z[t-1]|", "60-day 80th percentile", "-sign(ret_z[t-1])"),
    },
    ("RUNPERSIST", "anchor"): {
        "series": "run_imb", "window": 60, "quantile": 80.0, "side": 1,
        "tokens": ("|run_imb[t-1]|", "60-day 80th percentile", "sign(run_imb[t-1])"),
    },
    ("RUNPERSIST", "neighbour"): {
        "series": "run_imb", "window": 90, "quantile": 75.0, "side": 1,
        "tokens": ("90-day 75th percentile", "|run_imb|", "identical fill/sizing"),
    },
    ("RUNPERSIST", "control"): {
        "series": "run_imb_permuted", "window": 60, "quantile": 80.0, "side": 1,
        "tokens": ("default_rng(seed=16)", "2025-10-21..2026-08-21"),
    },
}

# Canonical record fields = CATEGORY_REQUIRED_FIELDS of
# research/governance/diagnostic_persistability.py (+ the sanitized
# decisions record and the DSR conditional).  Records carry EXACTLY these.
CANON_FIELDS: Dict[str, Tuple[str, ...]] = {
    "identity": (
        "cycle_id", "family_id", "arm_id", "arm_config_digest",
        "data_snapshot_digest", "code_freeze_sha", "cost_tier",
    ),
    "per_period_series": ("cycle_id", "arm_id", "period", "returns"),
    "per_symbol_breakdown": ("cycle_id", "symbol", "contribution_pnl"),
    "per_fold_breakdown": ("cycle_id", "fold_id", "pnl", "population"),
    "stress_tiers": ("cycle_id", "tier", "pnl"),
    "drop_one_inputs": ("cycle_id", "omitted_symbol", "pnl"),
    "benchmark_context": ("cycle_id", "fold_id", "benchmark", "excess_return"),
    "margins_to_fail": ("cycle_id", "gate_id", "value", "threshold", "margin"),
    "counters": ("observed_delta", "published_delta", "budget_used", "reruns_not_trials"),
    "reproduction_inputs": ("code_freeze_sha", "data_manifest_sha", "sanitized"),
    "dsr_per_period_series": ("cycle_id", "period", "returns"),
    "sanitized_decisions": ("cycle_id", "family_id", "arm_id", "date", "decision_taken", "symbol"),
}

LEAK_PATTERN = re.compile(r"pnl|profit|return|expectancy|pf|stress|sharpe|drawdown", re.IGNORECASE)

PANEL_DIR = Path("v16_data/staging_v16")
PANEL_FILE = "panel_{symbol}_daily.csv"
FREEZE_FILE = Path("research/control/v16_run/selection_freeze_v16.json")
MANIFEST_FILE = Path("research/control/v16_run/staging/panel_manifest.json")

PANEL_COLUMNS = (
    "symbol", "date", "vwap", "last_price", "high_price", "low_price",
    "buy_streak_max", "sell_streak_max",
)


class DriverError(RuntimeError):
    """Any fail-closed refusal of the driver."""


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def repo_root() -> Path:
    """The repository containing this driver (independent of cwd)."""
    root = Path(__file__).resolve().parents[4]
    if not (root / FREEZE_FILE).exists():
        raise DriverError(f"frozen selection artifact not found under {root}")
    return root


def sign(x: float) -> int:
    if x > 0.0:
        return 1
    if x < 0.0:
        return -1
    return 0


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canon_json(records: Sequence[Mapping[str, Any]]) -> str:
    """Byte-deterministic JSONL rendering (sorted keys, compact separators)."""
    lines = [
        json.dumps(dict(rec), sort_keys=True, separators=(",", ":"))
        for rec in records
    ]
    return "".join(line + "\n" for line in lines)


def r12(x: float) -> float:
    return round(float(x), 12)


# --------------------------------------------------------------------------- #
# Frozen inputs
# --------------------------------------------------------------------------- #
def load_freeze(root: Path) -> dict:
    raw = (root / FREEZE_FILE).read_bytes()
    freeze = json.loads(raw.decode("utf-8"))
    families = tuple(f.get("family_id") for f in freeze.get("frozen_families", []))
    if families != FAMILIES:
        raise DriverError(
            f"frozen families {families} != expected {FAMILIES}; refusing (spec drift)"
        )
    return freeze


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST_FILE).read_bytes()
    return json.loads(raw.decode("utf-8"))


def _finite_float(text: Any, column: str, symbol: str, d: str) -> float:
    try:
        value = float(text)
    except (TypeError, ValueError):
        raise DriverError(f"malformed panel row {symbol} {d}: {column}={text!r} not a float")
    if not math.isfinite(value):
        raise DriverError(f"malformed panel row {symbol} {d}: {column}={text!r} not finite")
    return value


def load_panel(root: Path, symbol: str) -> List[dict]:
    """Load and fail-closed-validate one staged panel (PANEL_SCHEMA.md)."""
    path = root / PANEL_DIR / PANEL_FILE.format(symbol=symbol)
    if not path.exists():
        raise DriverError(f"staged panel missing: {path}")
    rows: List[dict] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [c for c in PANEL_COLUMNS if c not in header]
        if missing:
            raise DriverError(f"panel {path} missing columns {missing}")
        for raw in reader:
            if any(v is None for v in raw.values()):
                raise DriverError(f"malformed panel row (ragged) for {symbol}: {raw!r}")
            d = str(raw["date"]).strip()
            try:
                parsed = date.fromisoformat(d)
            except ValueError:
                raise DriverError(f"malformed panel row {symbol}: bad date {raw['date']!r}")
            sym = str(raw["symbol"]).strip()
            if sym != symbol:
                raise DriverError(f"malformed panel row: symbol {sym!r} inside {symbol} panel")
            rec = {
                "date": parsed,
                "iso": d,
                "vwap": _finite_float(raw["vwap"], "vwap", sym, d),
                "last_price": _finite_float(raw["last_price"], "last_price", sym, d),
                "high_price": _finite_float(raw["high_price"], "high_price", sym, d),
                "low_price": _finite_float(raw["low_price"], "low_price", sym, d),
            }
            try:
                bsm = int(str(raw["buy_streak_max"]).strip())
                ssm = int(str(raw["sell_streak_max"]).strip())
            except (TypeError, ValueError):
                raise DriverError(f"malformed panel row {sym} {d}: non-integer streak count")
            if bsm < 0 or ssm < 0:
                raise DriverError(f"malformed panel row {sym} {d}: negative streak count")
            rec["buy_streak_max"] = bsm
            rec["sell_streak_max"] = ssm
            if rec["last_price"] <= 0.0 or rec["vwap"] <= 0.0:
                raise DriverError(f"malformed panel row {sym} {d}: non-positive price")
            if rec["high_price"] < rec["low_price"]:
                raise DriverError(f"malformed panel row {sym} {d}: high < low")
            rows.append(rec)
    if not rows:
        raise DriverError(f"panel {path} has zero rows")
    isos = [r["iso"] for r in rows]
    if sorted(isos) != isos or len(set(isos)) != len(isos):
        raise DriverError(f"panel {path}: dates not strictly ascending/unique")
    return rows


def load_panels(root: Path) -> Dict[str, List[dict]]:
    panels = {sym: load_panel(root, sym) for sym in UNIVERSE}
    base = [r["iso"] for r in panels[UNIVERSE[0]]]
    for sym in UNIVERSE[1:]:
        if [r["iso"] for r in panels[sym]] != base:
            raise DriverError(f"panel date grids differ across symbols at {sym}")
    return panels


# --------------------------------------------------------------------------- #
# Derived features (staged columns only)
# --------------------------------------------------------------------------- #
def build_features(rows: Sequence[Mapping[str, Any]]) -> dict:
    """disp / run_imb / ret_z per the frozen feature definitions.

    Lists are index-aligned with the panel rows; ret_z is None before its
    honest 60-return warmup completes.  Degenerate rows fail closed.
    """
    n = len(rows)
    disp: List[float] = []
    for r in rows:
        span = r["high_price"] - r["low_price"]
        if span <= 0.0:
            raise DriverError(
                f"degenerate panel row {r['iso']}: high==low, disp undefined (fail closed)"
            )
        disp.append((r["last_price"] - r["vwap"]) / span)
    run_imb: List[float] = []
    for r in rows:
        denom = r["buy_streak_max"] + r["sell_streak_max"]
        if denom <= 0:
            raise DriverError(
                f"degenerate panel row {r['iso']}: zero streak sum, run_imb undefined"
            )
        run_imb.append((r["buy_streak_max"] - r["sell_streak_max"]) / denom)
    prices = [r["last_price"] for r in rows]
    ret: List[Optional[float]] = [None] * n
    for t in range(1, n):
        ret[t] = prices[t] / prices[t - 1] - 1.0
    ret_z: List[Optional[float]] = [None] * n
    for t in range(60, n):
        window = list(ret[t - 59 : t + 1])
        if len(window) != 60 or any(x is None for x in window):
            continue
        mean = math.fsum(window) / 60.0
        var = math.fsum((x - mean) ** 2 for x in window) / 60.0  # population std, ddof=0
        std = math.sqrt(var)
        if std <= 0.0:
            raise DriverError(
                f"degenerate zero-volatility 60-day return window at {rows[t]['iso']}"
            )
        ret_z[t] = ret[t] / std
    return {"disp": disp, "run_imb": run_imb, "ret": ret, "ret_z": ret_z}


def permute_run_imb(run_imb: Sequence[float], isos: Sequence[str]) -> List[float]:
    """RUNPERSIST control: permute day labels within the frozen span.

    ONE fixed permutation from numpy default_rng(seed=16), shared by both
    symbols; values inside 2025-10-21..2026-08-21 are relabelled (the
    marginal exposure distribution is preserved), rows before the span
    (honest warmup) are untouched.
    """
    lo, hi = RUNPERSIST_PERM_SPAN
    idx = [i for i, d in enumerate(isos) if lo <= d <= hi]
    if not idx:
        raise DriverError(f"permutation span {lo}..{hi} not inside the panel")
    start, stop = idx[0], idx[-1] + 1
    n = stop - start
    perm = np.random.default_rng(RUNPERSIST_PERM_SEED).permutation(n)
    out = list(run_imb)
    for j in range(n):
        out[start + j] = run_imb[start + int(perm[j])]
    return out


# --------------------------------------------------------------------------- #
# Arm resolution (verbatim spec guard + digest)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmSpec:
    family_id: str
    role: str
    spec_text: str
    arm_config_digest: str
    series: str
    window: int
    quantile: float
    side: int


def resolve_arm(freeze: dict, family_id: str, role: str) -> ArmSpec:
    if family_id not in FAMILIES or role not in ARM_ROLES:
        raise DriverError(f"unknown family/arm: {family_id}/{role}")
    fam = next(f for f in freeze["frozen_families"] if f["family_id"] == family_id)
    arms = fam.get("arms") or {}
    if role not in arms:
        raise DriverError(f"family {family_id} has no {role} arm in the freeze")
    spec_text = str(arms[role])
    params = ARM_PARAMS[(family_id, role)]
    missing = [tok for tok in params["tokens"] if tok not in spec_text]
    if missing:
        raise DriverError(
            f"frozen {family_id}/{role} spec text no longer states {missing}; "
            "refusing (spec drift - return to A1)"
        )
    return ArmSpec(
        family_id=family_id,
        role=role,
        spec_text=spec_text,
        arm_config_digest=sha256_text(spec_text),
        series=str(params["series"]),
        window=int(params["window"]),
        quantile=float(params["quantile"]),
        side=int(params["side"]),
    )


# --------------------------------------------------------------------------- #
# Decisions, folds, books
# --------------------------------------------------------------------------- #
def first_defined_index(values: Sequence[Optional[float]]) -> int:
    for i, v in enumerate(values):
        if v is not None:
            return i
    raise DriverError("feature series is never defined")


def series_for_arm(arm: ArmSpec, feats: dict) -> Sequence[Optional[float]]:
    if arm.series == "run_imb_permuted":
        values: Sequence[Optional[float]] = feats["run_imb_permuted"]
    else:
        values = feats[arm.series]
    return values


def eligible_decision_days(
    arm: ArmSpec, features_by_symbol: Dict[str, dict], n_rows: int
) -> List[int]:
    """Days t on which a decision may be taken and filled (data <= t-1 only).

    The rolling |series| window [t-W .. t-1] must be fully defined for BOTH
    symbols and the fill day t must exist in the panel.  The honest warmup
    of the conditioning series therefore shifts the first eligible day:
    disp / run_imb (defined from row 0) start at t = W; the ret_z control
    (defined from row 60) starts at t = 2W.
    """
    start = 0
    for sym in UNIVERSE:
        values = series_for_arm(arm, features_by_symbol[sym])
        base = first_defined_index(values)
        start = max(start, arm.window + base)
    return list(range(start, n_rows))


def compute_arm_positions(
    arm: ArmSpec,
    features_by_symbol: Dict[str, dict],
    n_rows: int,
) -> Tuple[Dict[str, Dict[int, int]], List[int]]:
    """Per symbol: {decision day t -> position held over day t}.

    Decision at end of day t-1 from rows <= t-1 ONLY (one-bar lag):
    trigger when |series[t-1]| >= rolling W-day `quantile`th percentile of
    |series| (linear interpolation, numpy convention); position
    side * sign(series[t-1]); else flat.
    """
    out: Dict[str, Dict[int, int]] = {}
    eligible: List[int] = []
    for sym in UNIVERSE:
        values = series_for_arm(arm, features_by_symbol[sym])
        abs_arr = np.array([0.0 if v is None else abs(float(v)) for v in values])
        positions: Dict[int, int] = {}
        for t in eligible_decision_days(arm, features_by_symbol, n_rows):
            window = abs_arr[t - arm.window : t]
            if len(window) != arm.window:
                continue
            threshold = float(np.percentile(window, arm.quantile))
            x = values[t - 1]
            if x is None:
                continue
            if abs(float(x)) >= threshold:
                positions[t] = arm.side * sign(float(x))
        out[sym] = positions
        eligible = eligible_decision_days(arm, features_by_symbol, n_rows)
    return out, eligible


@dataclass
class Fold:
    index: int
    label: str
    members: Tuple[int, ...]


def build_folds(eligible: Sequence[int]) -> List[Fold]:
    """Chronological thirds F0/F1/F2 with a 1-day purge.

    Exact ``research.hyp_a8_m01.chronological_folds`` semantics (edges at
    round(i*N/n); stop = max(edge+1, next_edge - purge)), labels F0/F1/F2.
    """
    days = sorted(int(d) for d in eligible)
    n = FOLD_COUNT
    if len(days) < n + 1:
        raise DriverError(
            f"cannot form {n} folds with purge {PURGE_DAYS} from {len(days)} decision days"
        )
    edges = [round(i * len(days) / n) for i in range(n + 1)]
    folds: List[Fold] = []
    for idx in range(n):
        stop = max(edges[idx] + 1, edges[idx + 1] - PURGE_DAYS)
        members = tuple(days[edges[idx] : stop])
        if not members:
            raise DriverError(f"fold F{idx} empty after purge={PURGE_DAYS}")
        folds.append(Fold(index=idx, label=f"F{idx}", members=members))
    return folds


@dataclass
class FillRecord:
    """One fill of the remediated kernel (L-V14-0): cost lives HERE, once,
    and the holding term carried on every record is exactly zero."""

    symbol: str
    decision_day: int
    fold_label: str
    role: str  # "entry" | "exit"
    day: int
    price: float
    cost_fills: float
    cost_holding_terms: float = 0.0


@dataclass
class BookResult:
    tier: str
    pnl: float
    gross_pnl: float
    cost_fills_total: float
    cost_holding_terms_total: float
    n_fills: int
    n_round_trips: int
    daily_pnl: Dict[int, float] = field(default_factory=dict)
    per_symbol: Dict[str, float] = field(default_factory=dict)
    per_fold: Dict[str, float] = field(default_factory=dict)
    fold_population: Dict[str, int] = field(default_factory=dict)
    round_trips: List[dict] = field(default_factory=list)
    fills: List[FillRecord] = field(default_factory=list)


def fill_cost(notional: float, price: float, tier: str) -> float:
    """One fill's charge, EXACTLY ONCE (L-V14-0 remediated kernel):
    notional * (taker_fee_bps*1e-4*fee_multiplier + slip_ticks*tick_size/price)."""
    t = STRESS_TIERS[tier]
    rate = (
        TAKER_FEE_BPS * 1e-4 * float(t["fee_multiplier"])
        + int(t["slip_ticks"]) * TICK_SIZE / price
    )
    return notional * rate


def simulate_book(
    positions: Dict[str, Dict[int, int]],
    folds: Sequence[Fold],
    prices: Dict[str, Sequence[float]],
    tier: str,
    drop_symbols: Tuple[str, ...] = (),
) -> BookResult:
    """Book the 1-day round trips of one tier, force-flat at fold boundaries.

    Base tier (delay 0): decision at end of day d -> entry fill at
    last_price[d] (decision instant), exit at last_price[d+1], booked on
    d+1.  Delay tier (1 event on the daily clock): entry fill at
    last_price[d+1], exit at last_price[d+2], booked on d+2; a delayed
    round trip that would cross the next fold boundary (or run off the
    panel) is force-flattened, never booked.  Force-flat is ASSERTED for
    every booked position: the exit day falls strictly before the next
    fold's first decision day, so no position carries across a purge.
    """
    delay = int(STRESS_TIERS[tier]["event_delay"])
    universe_set = set(UNIVERSE)
    for sym in drop_symbols:
        if sym not in universe_set:
            raise DriverError(f"drop-one symbol {sym} outside the frozen universe")
    active = [s for s in UNIVERSE if s not in set(drop_symbols)]
    if not active:
        raise DriverError("book has no active symbols after drop")
    fold_by_decision: Dict[int, Fold] = {}
    for fold in folds:
        for d in fold.members:
            fold_by_decision[d] = fold

    result = BookResult(
        tier=tier, pnl=0.0, gross_pnl=0.0, cost_fills_total=0.0,
        cost_holding_terms_total=0.0, n_fills=0, n_round_trips=0,
    )
    for sym in active:
        pos_map = positions.get(sym, {})
        n_prices = len(prices[sym])
        for fold in folds:
            next_fold_first = (
                folds[fold.index + 1].members[0] if fold.index + 1 < len(folds) else None
            )
            for d in fold.members:
                pos = pos_map.get(d, 0)
                if pos == 0:
                    continue
                entry_day = d + delay
                exit_day = d + delay + 1
                if exit_day > n_prices - 1:
                    continue  # force-flat: the round trip would run off the panel
                if next_fold_first is not None and exit_day >= next_fold_first:
                    continue  # force-flat: never carry across the fold boundary
                entry_price = prices[sym][entry_day]
                exit_price = prices[sym][exit_day]
                gross = pos * (exit_price / entry_price - 1.0) * NOTIONAL
                cost_entry = fill_cost(NOTIONAL * abs(pos), entry_price, tier)
                cost_exit = fill_cost(NOTIONAL * abs(pos), exit_price, tier)
                net = gross - cost_entry - cost_exit
                for role, day, price, charge in (
                    ("entry", entry_day, entry_price, cost_entry),
                    ("exit", exit_day, exit_price, cost_exit),
                ):
                    result.fills.append(
                        FillRecord(
                            symbol=sym, decision_day=d, fold_label=fold.label,
                            role=role, day=day, price=price, cost_fills=charge,
                        )
                    )
                result.daily_pnl[exit_day] = result.daily_pnl.get(exit_day, 0.0) + net
                result.per_symbol[sym] = result.per_symbol.get(sym, 0.0) + net
                result.per_fold[fold.label] = result.per_fold.get(fold.label, 0.0) + net
                result.fold_population[fold.label] = (
                    result.fold_population.get(fold.label, 0) + 1
                )
                result.round_trips.append(
                    {
                        "symbol": sym,
                        "decision_day": d,
                        "entry_day": entry_day,
                        "exit_day": exit_day,
                        "fold_label": fold.label,
                        "position": pos,
                    }
                )
                result.pnl += net
                result.gross_pnl += gross
                result.cost_fills_total += cost_entry + cost_exit
                result.n_fills += 2
                result.n_round_trips += 1
    # force-flat proof: every booked exit precedes the next fold's first day
    for trip in result.round_trips:
        fold = fold_by_decision[trip["decision_day"]]
        if fold.index + 1 < len(folds):
            if trip["exit_day"] >= folds[fold.index + 1].members[0]:
                raise DriverError("force-flat violated: position crosses a fold boundary")
        if trip["exit_day"] > len(prices[trip["symbol"]]) - 1:
            raise DriverError("force-flat violated: exit beyond the panel")
    result.pnl = r12(result.pnl)
    result.gross_pnl = r12(result.gross_pnl)
    result.cost_fills_total = r12(result.cost_fills_total)
    result.cost_holding_terms_total = r12(result.cost_holding_terms_total)
    result.per_symbol = {s: r12(v) for s, v in sorted(result.per_symbol.items())}
    result.per_fold = {f: r12(v) for f, v in sorted(result.per_fold.items())}
    result.daily_pnl = {d: r12(v) for d, v in sorted(result.daily_pnl.items())}
    result.fills.sort(key=lambda f: (f.day, f.symbol, f.role, f.decision_day))
    return result


# --------------------------------------------------------------------------- #
# Metrics and gates (all on the PRIMARY tier book)
# --------------------------------------------------------------------------- #
@dataclass
class ArmMetrics:
    expectancy: float
    pf: float
    mdd: float
    series_days: int
    positive_folds: int
    fold_concentration: float


def arm_metrics(book: BookResult, first_day: int, last_day: int) -> ArmMetrics:
    """Daily-booked-return metrics over the arm's full decision window.

    ``returns`` are the booked PnL per day on the unit-notional book (flat
    days book exactly 0.0); expectancy is per day over that window.
    """
    returns: List[float] = []
    for d in range(first_day, last_day + 1):
        returns.append(book.daily_pnl.get(d, 0.0))
    if not returns:
        raise DriverError("empty decision window for metrics")
    expectancy = math.fsum(returns) / len(returns)
    gross_profit = math.fsum(x for x in returns if x > 0.0)
    gross_loss = -math.fsum(x for x in returns if x < 0.0)
    pf = math.inf if gross_loss == 0.0 else gross_profit / gross_loss
    cum = 0.0
    peak = 0.0
    mdd = 0.0
    for x in returns:
        cum += x
        peak = max(peak, cum)
        mdd = max(mdd, peak - cum)
    fold_pos = [v for v in book.per_fold.values() if v > 0.0]
    total_pos = math.fsum(fold_pos)
    concentration = (max(fold_pos) / total_pos) if total_pos > 0.0 else 0.0
    return ArmMetrics(
        expectancy=r12(expectancy), pf=pf, mdd=r12(mdd), series_days=len(returns),
        positive_folds=len(fold_pos), fold_concentration=r12(concentration),
    )


def gate_margins(
    anchor_m: ArmMetrics,
    neighbour_m: ArmMetrics,
    control_m: ArmMetrics,
    family_id: str,
) -> List[dict]:
    """Margins per frozen gate (P-2).  Margin convention: for gates that fail
    when value < threshold, margin = value - threshold; for gates that fail
    when value > threshold, margin = threshold - value.  G11: value = control
    expectancy, threshold = 0.5x anchor expectancy (margin <= 0 alongside a
    same-sign control marks the G11 reproduction; the frozen rule binds only
    under a positive anchor, which G1 already gates)."""
    gates = [
        ("G1", anchor_m.expectancy, 0.0, anchor_m.expectancy - 0.0),
        ("G2", anchor_m.pf, GATE_PF_THRESHOLD, anchor_m.pf - GATE_PF_THRESHOLD),
        (
            "G3",
            anchor_m.positive_folds / FOLD_COUNT,
            GATE_FOLD_POSITIVE_FRACTION,
            anchor_m.positive_folds / FOLD_COUNT - GATE_FOLD_POSITIVE_FRACTION,
        ),
        (
            "G4",
            anchor_m.fold_concentration,
            GATE_FOLD_CONCENTRATION,
            GATE_FOLD_CONCENTRATION - anchor_m.fold_concentration,
        ),
        ("G5", anchor_m.mdd, GATE_MDD_CEILING, GATE_MDD_CEILING - anchor_m.mdd),
        ("G10", neighbour_m.expectancy, 0.0, neighbour_m.expectancy - 0.0),
        (
            "G11",
            control_m.expectancy,
            r12(CONTROL_REPRODUCTION_FRACTION * anchor_m.expectancy),
            r12(CONTROL_REPRODUCTION_FRACTION * anchor_m.expectancy - control_m.expectancy),
        ),
        (
            "G12",
            FAMILY_NOVELTY_RHO[family_id],
            GATE_NOVELTY_RHO,
            GATE_NOVELTY_RHO - FAMILY_NOVELTY_RHO[family_id],
        ),
    ]
    return [
        {
            "cycle_id": CYCLE_ID,
            "gate_id": gate,
            "value": r12(value),
            "threshold": r12(threshold),
            "margin": r12(margin),
        }
        for gate, value, threshold, margin in gates
    ]


# --------------------------------------------------------------------------- #
# Identity plumbing
# --------------------------------------------------------------------------- #
def git_head_sha(root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(root),
            capture_output=True, text=True, timeout=30,
        )
    except OSError as exc:
        raise DriverError(f"cannot resolve code freeze sha: {exc}")
    if proc.returncode != 0:
        raise DriverError(f"git rev-parse HEAD failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def data_snapshot_digest(manifest: dict) -> Dict[str, str]:
    pairs = manifest.get("panel_sha256")
    if not isinstance(pairs, dict) or set(pairs) != set(UNIVERSE):
        raise DriverError("staging manifest lacks the frozen panel sha256 pair")
    return {sym: str(pairs[sym]) for sym in UNIVERSE}


# --------------------------------------------------------------------------- #
# Emission
# --------------------------------------------------------------------------- #
def _emit(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canon_json(records), encoding="utf-8")


def _check_canon(category: str, records: Sequence[Mapping[str, Any]]) -> None:
    want = set(CANON_FIELDS[category])
    for rec in records:
        if set(rec) != want:
            raise DriverError(
                f"{category} record field set {sorted(rec)} != canon {sorted(want)}"
            )


def compute_family(freeze: dict, panels: Dict[str, List[dict]], family_id: str) -> dict:
    """Compute all three arms of one family (the family-level gates
    G10/G11/G12 need anchor + neighbour + control books regardless of which
    single arm is being emitted)."""
    if family_id not in FAMILIES:
        raise DriverError(f"unknown family {family_id}")
    n_rows = len(panels[UNIVERSE[0]])
    isos = [r["iso"] for r in panels[UNIVERSE[0]]]
    features_by_symbol: Dict[str, dict] = {}
    for sym in UNIVERSE:
        feats = build_features(panels[sym])
        if resolve_arm(freeze, family_id, "control").series == "run_imb_permuted":
            feats["run_imb_permuted"] = permute_run_imb(feats["run_imb"], isos)
        features_by_symbol[sym] = feats
    arms = {role: resolve_arm(freeze, family_id, role) for role in ARM_ROLES}
    positions: Dict[str, Dict[str, Dict[int, int]]] = {}
    eligible_by_arm: Dict[str, List[int]] = {}
    folds_by_arm: Dict[str, List[Fold]] = {}
    for role in ARM_ROLES:
        pos, eligible = compute_arm_positions(arms[role], features_by_symbol, n_rows)
        positions[role] = pos
        eligible_by_arm[role] = eligible
        folds_by_arm[role] = build_folds(eligible)
    prices = {sym: [r["last_price"] for r in panels[sym]] for sym in UNIVERSE}
    books: Dict[str, Dict[str, BookResult]] = {}
    for role in ARM_ROLES:
        books[role] = {
            tier: simulate_book(positions[role], folds_by_arm[role], prices, tier)
            for tier in STRESS_TIERS
        }
    metrics = {
        role: arm_metrics(
            books[role][PRIMARY_TIER],
            eligible_by_arm[role][0],
            eligible_by_arm[role][-1] + 1,
        )
        for role in ARM_ROLES
    }
    return {
        "family_id": family_id,
        "arms": arms,
        "positions": positions,
        "eligible": eligible_by_arm,
        "folds": folds_by_arm,
        "books": books,
        "metrics": metrics,
        "n_rows": n_rows,
        "isos": isos,
        "prices": prices,
        "features": features_by_symbol,
    }


def emit_scored(
    freeze: dict,
    manifest: dict,
    panels: Dict[str, List[dict]],
    family_id: str,
    arm_role: str,
    out_root: Path,
) -> Dict[str, Any]:
    """Scored emission for ONE arm (the requested cell of the family)."""
    if family_id not in FAMILIES:
        raise DriverError(f"unknown family {family_id}")
    state = compute_family(freeze, panels, family_id)
    arm = state["arms"][arm_role]
    book = state["books"][arm_role][PRIMARY_TIER]
    if book.n_round_trips == 0:
        raise DriverError(
            f"VACUOUS CELL: arm {family_id}/{arm_role} booked zero decisions "
            "(non-vacuity failure, V8 F-A7-1)"
        )
    metrics = state["metrics"][arm_role]
    eligible = state["eligible"][arm_role]
    folds = state["folds"][arm_role]
    isos = state["isos"]
    root = repo_root()
    head = git_head_sha(root)
    snapshot = data_snapshot_digest(manifest)
    manifest_sha = sha256_bytes((root / MANIFEST_FILE).read_bytes())
    arm_dir = out_root / SCORED_ROOT / family_id / arm_role

    identity = {
        "cycle_id": CYCLE_ID,
        "family_id": family_id,
        "arm_id": arm_role,
        "arm_config_digest": arm.arm_config_digest,
        "data_snapshot_digest": snapshot,
        "code_freeze_sha": head,
        "cost_tier": PRIMARY_TIER,
    }
    _check_canon("identity", [identity])

    series = []
    for d in range(eligible[0], eligible[-1] + 1):
        series.append(
            {
                "cycle_id": CYCLE_ID,
                "arm_id": arm_role,
                "period": isos[d],
                "returns": r12(book.daily_pnl.get(d, 0.0)),
            }
        )
    _check_canon("per_period_series", series)

    per_symbol = [
        {"cycle_id": CYCLE_ID, "symbol": sym,
         "contribution_pnl": r12(book.per_symbol.get(sym, 0.0))}
        for sym in UNIVERSE
    ]
    _check_canon("per_symbol_breakdown", per_symbol)

    per_fold = [
        {
            "cycle_id": CYCLE_ID,
            "fold_id": fold.label,
            "pnl": r12(book.per_fold.get(fold.label, 0.0)),
            "population": int(book.fold_population.get(fold.label, 0)),
        }
        for fold in folds
    ]
    _check_canon("per_fold_breakdown", per_fold)

    stress = [
        {"cycle_id": CYCLE_ID, "tier": tier, "pnl": r12(state["books"][arm_role][tier].pnl)}
        for tier in sorted(STRESS_TIERS)
    ]
    _check_canon("stress_tiers", stress)

    drop_one = []
    for omitted in UNIVERSE:
        dropped = tuple(s for s in UNIVERSE if s != omitted)
        sub_book = simulate_book(
            state["positions"][arm_role], folds, state["prices"], PRIMARY_TIER,
            drop_symbols=dropped,
        )
        drop_one.append(
            {"cycle_id": CYCLE_ID, "omitted_symbol": omitted, "pnl": r12(sub_book.pnl)}
        )
    _check_canon("drop_one_inputs", drop_one)

    benchmark = []
    for fold in folds:
        first, last = fold.members[0], fold.members[-1]
        legs = [
            state["prices"][sym][last] / state["prices"][sym][first - 1] - 1.0
            for sym in UNIVERSE
        ]
        bench = math.fsum(legs) / len(legs)
        benchmark.append(
            {
                "cycle_id": CYCLE_ID,
                "fold_id": fold.label,
                "benchmark": BENCHMARK_NAME,
                "excess_return": r12(book.per_fold.get(fold.label, 0.0) - bench),
            }
        )
    _check_canon("benchmark_context", benchmark)

    margins = gate_margins(
        state["metrics"]["anchor"],
        state["metrics"]["neighbour"],
        state["metrics"]["control"],
        family_id,
    )
    _check_canon("margins_to_fail", margins)

    counters = {
        "observed_delta": 1,
        "published_delta": 1,
        "budget_used": 1,
        "reruns_not_trials": True,
    }
    _check_canon("counters", [counters])

    reproduction = {
        "code_freeze_sha": head,
        "data_manifest_sha": manifest_sha,
        "sanitized": False,
    }
    _check_canon("reproduction_inputs", [reproduction])

    _emit(arm_dir / "identity.jsonl", [identity])
    _emit(arm_dir / "per_period_series.jsonl", series)
    _emit(arm_dir / "per_symbol_breakdown.jsonl", per_symbol)
    _emit(arm_dir / "per_fold_breakdown.jsonl", per_fold)
    _emit(arm_dir / "stress_tiers.jsonl", stress)
    _emit(arm_dir / "drop_one_inputs.jsonl", drop_one)
    _emit(arm_dir / "benchmark_context.jsonl", benchmark)
    _emit(arm_dir / "margins_to_fail.jsonl", margins)
    _emit(arm_dir / "counters.jsonl", [counters])
    _emit(arm_dir / "reproduction_inputs.jsonl", [reproduction])

    # Family-level conditional diagnostic (multiple_testing_accounting=true):
    # DSR series of the ANCHOR book - the family's primary trial.
    anchor_book = state["books"]["anchor"][PRIMARY_TIER]
    anchor_eligible = state["eligible"]["anchor"]
    dsr = []
    for d in range(anchor_eligible[0], anchor_eligible[-1] + 1):
        dsr.append(
            {"cycle_id": CYCLE_ID, "period": isos[d],
             "returns": r12(anchor_book.daily_pnl.get(d, 0.0))}
        )
    _check_canon("dsr_per_period_series", dsr)
    _emit(out_root / SCORED_ROOT / family_id / "dsr_per_period_series.jsonl", dsr)

    kernel = {
        "remediated_kernel": True,
        "cost_fills": book.cost_fills_total,
        "cost_holding_terms": book.cost_holding_terms_total,
        "cost_total": r12(book.cost_fills_total + book.cost_holding_terms_total),
        "n_fills": book.n_fills,
        "n_round_trips": book.n_round_trips,
    }
    if book.cost_holding_terms_total != 0.0 or any(
        f.cost_holding_terms != 0.0 for f in book.fills
    ):
        raise DriverError(
            "cost_holding_terms must be exactly 0 by construction "
            "(remediated L-V14-0 kernel); refusing the cell"
        )
    return {"kernel": kernel, "metrics": metrics, "gates": margins, "arm": arm}


def emit_sanitized(
    freeze: dict,
    panels: Dict[str, List[dict]],
    family_id: str,
    arm_role: str,
    out_root: Path,
) -> int:
    """Sanitized dry-run: decision surface ONLY, zero outcome fields.

    Emits decisions.jsonl with exactly {cycle_id, family_id, arm_id, date,
    decision_taken, symbol} for every (symbol, evaluated decision day);
    decision_taken mirrors the T1.0 base book's booked decisions after
    force-flat.  Zero booked decisions is a HARD FAILURE.
    """
    if family_id not in FAMILIES:
        raise DriverError(f"unknown family {family_id}")
    state = compute_family(freeze, panels, family_id)
    positions = state["positions"][arm_role]
    folds = state["folds"][arm_role]
    base_book = simulate_book(positions, folds, state["prices"], "T1.0")
    booked = {(t["symbol"], t["decision_day"]) for t in base_book.round_trips}
    records: List[dict] = []
    isos = state["isos"]
    for d in state["eligible"][arm_role]:
        for sym in UNIVERSE:
            records.append(
                {
                    "cycle_id": CYCLE_ID,
                    "family_id": family_id,
                    "arm_id": arm_role,
                    "date": isos[d],
                    "decision_taken": (sym, d) in booked,
                    "symbol": sym,
                }
            )
    n_decisions = sum(1 for r in records if r["decision_taken"])
    if n_decisions == 0:
        raise DriverError(
            f"HARD FAILURE: sanitized dry-run of {family_id}/{arm_role} is VACUOUS "
            "(zero booked decisions, V8 F-A7-1)"
        )
    _check_canon("sanitized_decisions", records)
    # Leak guard at emission: no key anywhere may match the outcome pattern.
    for rec in records:
        for key in rec:
            if LEAK_PATTERN.search(str(key)):
                raise DriverError(f"sanitized leak: field {key!r} is outcome-shaped")
    _emit(
        out_root / SANITIZED_ROOT / family_id / arm_role / "decisions.jsonl",
        records,
    )
    return n_decisions


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="CRYPTO-V16 scored cell driver + sanitized mode (frozen spec)"
    )
    parser.add_argument("--family", required=True, choices=list(FAMILIES))
    parser.add_argument("--arm-id", required=True, choices=list(ARM_ROLES))
    parser.add_argument(
        "--sanitized", action="store_true",
        help="emit the sanitized decision surface only (no outcome fields)",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    freeze = load_freeze(root)
    out_root = Path.cwd()
    if args.sanitized:
        panels = load_panels(root)
        n = emit_sanitized(freeze, panels, args.family, args.arm_id, out_root)
        print(
            f"sanitized dry-run {args.family}/{args.arm_id}: "
            f"{n} booked decisions, 0 outcome fields emitted"
        )
        return 0
    manifest = load_manifest(root)
    panels = load_panels(root)
    result = emit_scored(freeze, manifest, panels, args.family, args.arm_id, out_root)
    kernel = result["kernel"]
    print(
        f"scored emission {args.family}/{args.arm_id}: "
        f"{kernel['n_round_trips']} round trips / {kernel['n_fills']} fills, "
        f"cost_fills={kernel['cost_fills']} "
        f"cost_holding_terms={kernel['cost_holding_terms']} "
        f"remediated_kernel={kernel['remediated_kernel']}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DriverError as exc:
        print(f"DRIVER_REFUSAL: {exc}", file=sys.stderr)
        sys.exit(2)
