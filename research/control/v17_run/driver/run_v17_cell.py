#!/usr/bin/env python3
"""CRYPTO-V17 A8 family-agnostic scored-cell driver + sanitized mode.

================================================================================
README (A8 driver lane, cycle CRYPTO-V17)
================================================================================

What this is
    The scored-cell driver for CRYPTO-V17.  It is FAMILY-AGNOSTIC: no arm
    rule lives in this file.  Families come from a frozen selection JSON
    (``--selection PATH``); every arm references its exposure by
    ``formula_id`` resolved through ``family_registry_v17.py`` (pure
    functions over panel rows).  Structure adapts the terminal-audited V16
    precedent driver (``research/control/v16_run/driver/run_v16_cell.py``)
    to the V17 frozen contracts:

    * data     research/control/v17_run/staging/panel_manifest_v17_published.json
    * gates    research/control/v17_run/p3_invariants_v17.json (frozen order)
    * diag     research/control/v17_run/p3_diagnostic_contract_scaffold.json
                 (10 mandatory categories, results/v17/{family}/{arm}/)

A8 families lane extensions (additive; the frozen defaults are untouched)
    The two SELECTED families (V17-A4-P2-SILRES, V17-a5-P1-ATTN-PHASE) fill
    at the PUBLISHED bucket VWAP and inside the position bucket, per their
    frozen proposals.  The family spec may therefore declare:

    * ``"fill_price": "last_price" (default) | "vwap" | "h1_bucket0_vwap"``
      -- the published price fills execute against.  ``h1_bucket0_vwap``
      (D1 clock only: the vwap of the day's first H1 bucket) realizes the
      ATTN-PHASE frozen fill law "day t bucket-0 VWAP (close_ts 01:00)".
    * ``"entry": {"lag_buckets": 0}`` -- fill inside the position bucket,
      allowed ONLY together with a non-close ``fill_price`` (the decision
      still consumes strictly-prior buckets via the one-bar lag; the
      bucket's VWAP is a published transaction price, not decision info).
      Without that declaration lag 0 is still refused (same-bucket close
      conservatism, unchanged).
    * ``"exit": {"holding_buckets": H}`` at ARM level -- per-arm override
      of the family holding (SILRES neighbour freezes K=4 vs anchor K=2).
    * ``"booking": "event" (default) | "state_machine"`` -- state_machine
      (D1 clock) books ONE round trip per maximal constant-position
      episode of the exposure path: entry at the episode's first day,
      exit at the first differing day (both at the family ``fill_price``),
      forced exit at the fold's last tradable H1 bucket VWAP when the
      episode reaches the fold edge (the ATTN-PHASE force-flat law); no
      position ever crosses a fold boundary or the +/-1-day purge.
    * ``"sham_calendar": {"calendar": str, "note": str}`` -- scored arms
      additionally emit ``sham_control_calendar.jsonl`` rows
      {cycle_id, arm_id, calendar} (diag/sham_control_calendar@1 canon)
      carrying the family's control-calendar descriptor: the ATTN-PHASE
      sham rotation, or the SILRES not-applicable marker per the D2
      re-freeze (calendar_conditioned=false for that family).

Selection JSON schema (frozen shape consumed here)
    {
      "cycle_id": "CRYPTO-V17",
      "families": [
        {
          "family_id": str,
          "clock": "H1" | "H4" | "D1",          # decision bucket granularity
          "universe": ["BTCUSDT", ...],          # subset of the manifest symbols
          "entry": {"lag_buckets": int >= 1},    # fill at close of bucket t+lag
          "exit":  {"holding_buckets": int >= 1},
          "arms": [
            {
              "arm_id": str,                     # path label of the arm
              "kind": "anchor" | "neighbour" | "control",
              "exposure":
                {"type": "panel_formula", "formula_id": str, "params": {...}}
              | {"type": "endpoint_series", "path": str, "format": "json"},
              "control_spec": {...}              # optional, opaque to the
            }                                    # driver; digested, not acted on
          ]
        }
      ]
    }
    Exactly three arms per family; kinds anchor/neighbour/control exactly
    once each.  ``endpoint_series`` paths resolve against the selection
    file's directory; the JSON must map every universe symbol to a list of
    floats (or null warmups) index-aligned with the bucket grid.

CLI (exactly)
    python run_v17_cell.py --selection PATH [--families ID[,ID]] [--sanitized]
    python run_v17_cell.py --selection PATH --families ID --smoke

    default (SCORED)  per arm, the 10 diagnostic categories under
                      results/v17/{family}/{arm}/*.jsonl exactly as the
                      scaffold declares, plus the family-level
                      results/v17/{family}/dsr_per_period_series.jsonl from
                      the ANCHOR book (V16 canon).  Example-only formulas
                      are REFUSED on this path.
    --sanitized       emits ONLY
                      research/control/v17_run/q_dry_run/{family}/{arm}/
                      decisions.jsonl with records {cycle_id, family_id,
                      arm_id, date, hour, decision_taken, symbol}; zero
                      booked decisions anywhere is a HARD FAILURE
                      (non-vacuous, V8 F-A7-1).  Nothing outcome-shaped.
    --smoke           the full scored pipeline into results/v17_smoke/ (an
                      isolated namespace that can never be confused with
                      scored output), exactly one family.  NOTE: the V17
                      task list does not define --smoke semantics; this is
                      the conservative lane choice (exercise everything,
                      write nowhere scored).

Frozen semantics implemented (each traced to its source)
* Panels: v17_data/staging_v17/panel_{SYM}_h1.csv, loaded ONLY after the
  file sha256 matches manifest panel_sha256[sym] (refuse on mismatch;
  manifest window and hourly_rows cross-checked).  H4 buckets and daily
  aggregates are derived IN MEMORY from the H1 rows (post-extraction
  derivations are authorized by the wave packet data contract).
* Availability law: the decision at bucket t consumes the exposure series
  at t-1 ONLY (no same-bucket close peeking); fills at the close of
  bucket t+lag (next-bucket default, wave packet section 5); exit
  `holding_buckets` later; PnL = pos*(P_exit/P_entry - 1)*unit notional,
  booked on the exit bucket.
* Costs (L-V14-0 remediated kernel): taker_fee_bps = 5.0 charged EXACTLY
  ONCE PER FILL,
      rate_per_unit_notional = 5.0*1e-4*fee_multiplier
                               + slip_ticks*0.01/fill_price
  with tier multipliers x1.0/x1.5/x2.0 on fees and slip floors 1/1/2
  ticks; TIER 2.0 IS THE PRIMARY BOOK and feeds every gate-bearing
  diagnostic.  (The V16 T2.0 "1 event delay" is NOT carried: the V17 task
  pins fee multipliers + slip floors only; inventing an H1 delay semantic
  would be a product decision.  Conservative choice: delay 0 everywhere.)
  Every fill record carries cost_fills (its charge) and cost_holding_terms
  EXACTLY 0.0; the cell refuses if any holding term is nonzero.
* Folds: 3 chronological folds over the S0 day grid (edges floor(i*N/3));
  1-day purge = +/-1 full UTC day around each internal fold boundary.  On
  the 365-day S0 window (2025-08-22..2026-08-21) this yields EXACTLY the
  frozen purged UTC day-indices {120, 121, 242, 243} zero-based from S0
  (asserted).  Any decision whose holding window touches a purged UTC day
  is force-flattened/refused (never booked); every booked round trip is
  ASSERTED to stay inside one fold (no position carries a boundary).
* Gates (frozen order, first FAIL kills the arm, all on the T2.0 primary
  book, PER ARM from that arm's own series): G1 expectancy > 0; G2
  PF >= 1.10; G3 folds >= 2/3; G4 largest-fold-positive-share <= 0.50;
  G5 MDD <= 0.20.  G10/G11/G12 are D2/terminal-level and are skipped
  in-cell.  margins_to_fail records carry EVERY in-cell gate with
  margin in the program-wide positive=pass convention (value-threshold on
  lower-bound gates, threshold-value on upper-bound ceilings; V16 precedent)
  value - threshold on lower-bound gates) plus arm identity
  (p3_invariants margins_attribution: "margins artifacts carry arm
  identity"; the round-2 canon validator checks required fields present,
  so arm_id rides as an extra field).
* Determinism: no wall clock in any output, no randomness; two runs are
  byte-identical (canon JSONL, sorted keys, compact separators).
* Example formula: the registry ships exactly ONE formula, marked
  EXAMPLE_TEST_ONLY (hourly mean-reversion flag on
  (last_price - vwap)/vwap).  It is used by tests and can never be scored
  in production.

Outputs are written relative to cwd; frozen inputs are read from the
repository that contains this file (independent of cwd).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import inspect
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

try:  # package import (tests: research.control.v17_run.driver.run_v17_cell)
    from research.control.v17_run.driver.family_registry_v17 import (
        is_example_only,
        resolve as registry_resolve,
    )
except ImportError:  # script execution from the driver directory
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from family_registry_v17 import (  # type: ignore
        is_example_only,
        resolve as registry_resolve,
    )

# --------------------------------------------------------------------------- #
# Frozen constants (sources in the module docstring)
# --------------------------------------------------------------------------- #
CYCLE_ID = "CRYPTO-V17"
ARM_KINDS = ("anchor", "neighbour", "control")
CLOCKS = ("H1", "H4", "D1")

#: Published fill-price conventions (family spec "fill_price").
FILL_PRICES = ("last_price", "vwap", "h1_bucket0_vwap")
#: Booking models (family spec "booking").
BOOKINGS = ("event", "state_machine")

TAKER_FEE_BPS = 5.0
TICK_SIZE = 0.01
NOTIONAL = 1.0
FOLD_COUNT = 3

STRESS_TIERS: Dict[str, Dict[str, Any]] = {
    "T1.0": {"fee_multiplier": 1.0, "slip_ticks": 1},
    "T1.5": {"fee_multiplier": 1.5, "slip_ticks": 1},
    "T2.0": {"fee_multiplier": 2.0, "slip_ticks": 2},
}
PRIMARY_TIER = "T2.0"

GATE_PF_THRESHOLD = 1.10
GATE_FOLD_POSITIVE_FRACTION = 2.0 / 3.0
GATE_FOLD_CONCENTRATION = 0.50
GATE_MDD_CEILING = 0.20

SCORED_ROOT = Path("results/v17")
SMOKE_ROOT = Path("results/v17_smoke")
SANITIZED_ROOT = Path("research/control/v17_run/q_dry_run")

PANEL_DIR = Path("v17_data/staging_v17")
PANEL_FILE = "panel_{symbol}_h1.csv"
MANIFEST_FILE = Path("research/control/v17_run/staging/panel_manifest_v17_published.json")
INVARIANTS_FILE = Path("research/control/v17_run/p3_invariants_v17.json")

S0_DATE = "2025-08-22"
S0_DAYS = 365
#: Frozen purged UTC day-indices (zero-based from S0) per the A8 task:
#: +/-1 full UTC day around each internal fold boundary of the 365-day S0
#: window.  Recomputed for any window length by purged_day_indices(); the
#: frozen set is ASSERTED whenever the window is exactly 365 days.
FROZEN_PURGED_DAY_INDICES = frozenset({120, 121, 242, 243})

H1_SCHEMA = (
    "symbol", "hour_utc", "day_utc",
    "n_trades", "buy_count", "sell_count",
    "buy_qty", "sell_qty", "buy_quote", "sell_quote",
    "quote_total", "qty_total", "vwap",
    "first_price", "last_price", "high_price", "low_price",
    "max_trade_quote", "sum_qty_squared",
    "n_price_moves", "sum_squared_log_ret",
    "gap_sum_s", "gap_count", "entry_gap_s",
    "run_close_dir", "run_close_len", "run_switch_count",
    "max_run_buy", "max_run_sell",
    "first_ts_ms", "last_ts_ms",
)
_H1_INT_COLUMNS = (
    "n_trades", "buy_count", "sell_count", "n_price_moves", "gap_count",
    "run_close_len", "run_switch_count", "max_run_buy", "max_run_sell",
    "first_ts_ms", "last_ts_ms",
)
_H1_FLOAT_COLUMNS = (
    "buy_qty", "sell_qty", "buy_quote", "sell_quote", "quote_total",
    "qty_total", "vwap", "first_price", "last_price", "high_price",
    "low_price", "max_trade_quote", "sum_qty_squared", "sum_squared_log_ret",
    "gap_sum_s", "entry_gap_s",
)
_H1_STR_COLUMNS = ("symbol", "hour_utc", "day_utc", "run_close_dir")
HOUR_KEY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}$")

# Canonical record fields = CATEGORY_REQUIRED_FIELDS of
# research/governance/diagnostic_persistability.py (round-2 canon; the
# validator checks these are PRESENT per record).  margins_to_fail records
# additionally carry arm_id per the frozen V17 margins_attribution
# invariant; sanitized decisions are the task-pinned record.
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
    "margins_to_fail": (
        "cycle_id", "gate_id", "value", "threshold", "margin", "arm_id",
    ),
    "counters": ("observed_delta", "published_delta", "budget_used", "reruns_not_trials"),
    "reproduction_inputs": ("code_freeze_sha", "data_manifest_sha", "sanitized"),
    "dsr_per_period_series": ("cycle_id", "period", "returns"),
    "sanitized_decisions": (
        "cycle_id", "family_id", "arm_id", "date", "hour", "decision_taken", "symbol",
    ),
    # Conditional (diag/sham_control_calendar@1): emitted only for families
    # whose spec declares "sham_calendar" (see the README extensions block).
    "sham_control_calendar": ("cycle_id", "arm_id", "calendar"),
}

LEAK_PATTERN = re.compile(
    r"pnl|profit|return|expectancy|pf|stress|sharpe|drawdown", re.IGNORECASE
)


class DriverError(RuntimeError):
    """Any fail-closed refusal of the driver."""


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def repo_root() -> Path:
    """The repository containing this driver (independent of cwd)."""
    root = Path(__file__).resolve().parents[4]
    if not (root / INVARIANTS_FILE).exists():
        raise DriverError(f"frozen invariants not found under {root}")
    return root


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


def sign(x: float) -> int:
    if x > 0.0:
        return 1
    if x < 0.0:
        return -1
    return 0


# --------------------------------------------------------------------------- #
# Selection (frozen family specs) -- the rules live in the file, not here
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmSpec:
    family_id: str
    arm_id: str
    kind: str
    exposure: Mapping[str, Any]
    raw: Mapping[str, Any]
    arm_config_digest: str
    #: arm-level overrides of the family entry/exit (None = family value).
    lag_override: Optional[int] = None
    holding_override: Optional[int] = None


@dataclass(frozen=True)
class FamilySpec:
    family_id: str
    clock: str
    universe: Tuple[str, ...]
    lag_buckets: int
    holding_buckets: int
    arms: Tuple[ArmSpec, ...]
    raw: Mapping[str, Any]
    fill_price: str = "last_price"
    booking: str = "event"
    sham_calendar: Optional[Mapping[str, Any]] = None


def load_selection(path: Path) -> Tuple[str, List[FamilySpec]]:
    """Load + validate the frozen selection JSON (fail closed)."""
    try:
        raw_doc = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DriverError(f"cannot read selection {path}: {exc}")
    except ValueError as exc:
        raise DriverError(f"selection {path} is not valid JSON: {exc}")
    if not isinstance(raw_doc, dict):
        raise DriverError("selection must be a JSON object")
    families_raw = raw_doc.get("families")
    if not isinstance(families_raw, list) or not families_raw:
        raise DriverError("selection.families must be a non-empty list")
    specs: List[FamilySpec] = []
    seen: Dict[str, int] = {}
    for fam_raw in families_raw:
        spec = _parse_family(fam_raw, base_dir=path.resolve().parent)
        if spec.family_id in seen:
            raise DriverError(f"duplicate family_id {spec.family_id} in selection")
        seen[spec.family_id] = 1
        specs.append(spec)
    cycle_id = str(raw_doc.get("cycle_id", CYCLE_ID))
    return cycle_id, specs


def _parse_fill_price(family_id: str, fam_raw: Mapping[str, Any], clock: str) -> str:
    fill_price = str(fam_raw.get("fill_price", "last_price"))
    if fill_price not in FILL_PRICES:
        raise DriverError(
            f"family {family_id}: fill_price {fill_price!r} not in {FILL_PRICES}"
        )
    if fill_price == "h1_bucket0_vwap" and clock != "D1":
        raise DriverError(
            f"family {family_id}: fill_price h1_bucket0_vwap requires clock D1 "
            f"(got {clock!r})"
        )
    return fill_price


def _check_lag_zero_gate(family_id: str, lag: int, fill_price: str) -> None:
    """lag 0 fills INSIDE the position bucket; allowed only when the family
    pins a published non-close fill price (never the close the decision
    could be confused with).  Without that declaration the frozen refusal
    stands (fail closed, unchanged for pre-existing specs)."""
    if lag == 0 and fill_price == "last_price":
        raise DriverError(
            f"family {family_id}: entry.lag_buckets must be >= 1 "
            "(lag 0 peeks the same-bucket close the decision consumed); "
            "declare fill_price 'vwap'|'h1_bucket0_vwap' to fill at the "
            "bucket's published VWAP inside the position bucket"
        )


def _parse_family(fam_raw: Any, *, base_dir: Path) -> FamilySpec:
    if not isinstance(fam_raw, dict):
        raise DriverError("each family must be a JSON object")
    family_id = str(fam_raw.get("family_id", "")).strip()
    if not family_id:
        raise DriverError("family_id must be a non-empty string")
    clock = str(fam_raw.get("clock", "")).strip()
    if clock not in CLOCKS:
        raise DriverError(
            f"family {family_id}: clock {clock!r} not in {CLOCKS}"
        )
    universe_raw = fam_raw.get("universe")
    if (
        not isinstance(universe_raw, list)
        or not universe_raw
        or any(not isinstance(s, str) or not s.strip() for s in universe_raw)
    ):
        raise DriverError(f"family {family_id}: universe must be a non-empty string list")
    universe = tuple(dict.fromkeys(s.strip() for s in universe_raw))
    entry = fam_raw.get("entry")
    exitp = fam_raw.get("exit")
    lag = int(entry.get("lag_buckets", 1)) if isinstance(entry, dict) else 1
    holding = int(exitp.get("holding_buckets", 1)) if isinstance(exitp, dict) else 1
    if lag < 0:
        raise DriverError(
            f"family {family_id}: entry.lag_buckets must be >= 0, got {lag}"
        )
    if holding < 1:
        raise DriverError(f"family {family_id}: exit.holding_buckets must be >= 1")
    fill_price = _parse_fill_price(family_id, fam_raw, clock)
    _check_lag_zero_gate(family_id, lag, fill_price)
    booking = str(fam_raw.get("booking", "event"))
    if booking not in BOOKINGS:
        raise DriverError(f"family {family_id}: booking {booking!r} not in {BOOKINGS}")
    if booking == "state_machine" and clock != "D1":
        raise DriverError(
            f"family {family_id}: booking state_machine requires clock D1 "
            f"(got {clock!r})"
        )
    sham_calendar = fam_raw.get("sham_calendar")
    if sham_calendar is not None:
        if not isinstance(sham_calendar, dict) or not isinstance(
            sham_calendar.get("calendar"), str
        ):
            raise DriverError(
                f"family {family_id}: sham_calendar must be an object with a "
                "string 'calendar' descriptor"
            )
    arms_raw = fam_raw.get("arms")
    if not isinstance(arms_raw, list) or len(arms_raw) != 3:
        raise DriverError(
            f"family {family_id}: exactly three arms required (anchor/neighbour/control)"
        )
    arms: List[ArmSpec] = []
    kinds_seen: Dict[str, int] = {}
    for arm_raw in arms_raw:
        if not isinstance(arm_raw, dict):
            raise DriverError(f"family {family_id}: each arm must be an object")
        arm_id = str(arm_raw.get("arm_id", "")).strip()
        kind = str(arm_raw.get("kind", "")).strip()
        if not arm_id:
            raise DriverError(f"family {family_id}: arm_id must be non-empty")
        if kind not in ARM_KINDS:
            raise DriverError(
                f"family {family_id}/{arm_id}: kind {kind!r} not in {ARM_KINDS}"
            )
        if kind in kinds_seen:
            raise DriverError(f"family {family_id}: duplicate kind {kind!r}")
        kinds_seen[kind] = 1
        exposure = arm_raw.get("exposure")
        if not isinstance(exposure, dict):
            raise DriverError(
                f"family {family_id}/{arm_id}: exposure must be an object"
            )
        etype = exposure.get("type")
        if etype == "panel_formula":
            fid = str(exposure.get("formula_id", "")).strip()
            if not fid:
                raise DriverError(
                    f"family {family_id}/{arm_id}: panel_formula needs formula_id"
                )
            params = exposure.get("params", {})
            if not isinstance(params, dict):
                raise DriverError(
                    f"family {family_id}/{arm_id}: params must be an object"
                )
        elif etype == "endpoint_series":
            epath = exposure.get("path")
            if not isinstance(epath, str) or not epath.strip():
                raise DriverError(
                    f"family {family_id}/{arm_id}: endpoint_series needs path"
                )
            if exposure.get("format", "json") != "json":
                raise DriverError(
                    f"family {family_id}/{arm_id}: endpoint_series format must be json"
                )
        else:
            raise DriverError(
                f"family {family_id}/{arm_id}: exposure.type {etype!r} unsupported "
                "(panel_formula | endpoint_series)"
            )
        control_spec = arm_raw.get("control_spec")
        if control_spec is not None and not isinstance(control_spec, dict):
            raise DriverError(
                f"family {family_id}/{arm_id}: control_spec must be an object"
            )
        # arm-level entry/exit overrides (A8 families lane: SILRES neighbour
        # freezes K=4 vs the anchor K=2 within one family).
        arm_entry = arm_raw.get("entry")
        arm_exit = arm_raw.get("exit")
        lag_override: Optional[int] = None
        holding_override: Optional[int] = None
        if arm_entry is not None:
            if not isinstance(arm_entry, dict) or "lag_buckets" not in arm_entry:
                raise DriverError(
                    f"family {family_id}/{arm_id}: arm entry override must be "
                    "an object with lag_buckets"
                )
            lag_override = int(arm_entry["lag_buckets"])
            if lag_override < 0:
                raise DriverError(
                    f"family {family_id}/{arm_id}: arm entry.lag_buckets must "
                    f"be >= 0, got {lag_override}"
                )
            _check_lag_zero_gate(f"{family_id}/{arm_id}", lag_override, fill_price)
        if arm_exit is not None:
            if not isinstance(arm_exit, dict) or "holding_buckets" not in arm_exit:
                raise DriverError(
                    f"family {family_id}/{arm_id}: arm exit override must be "
                    "an object with holding_buckets"
                )
            holding_override = int(arm_exit["holding_buckets"])
            if holding_override < 1:
                raise DriverError(
                    f"family {family_id}/{arm_id}: arm exit.holding_buckets "
                    f"must be >= 1, got {holding_override}"
                )
        arms.append(
            ArmSpec(
                family_id=family_id,
                arm_id=arm_id,
                kind=kind,
                exposure=exposure,
                raw=arm_raw,
                arm_config_digest=sha256_text(canon_json([arm_raw])),
                lag_override=lag_override,
                holding_override=holding_override,
            )
        )
    missing = [k for k in ARM_KINDS if k not in kinds_seen]
    if missing:
        raise DriverError(f"family {family_id}: arms missing kinds {missing}")
    return FamilySpec(
        family_id=family_id,
        clock=clock,
        universe=universe,
        lag_buckets=lag,
        holding_buckets=holding,
        arms=tuple(arms),
        raw=fam_raw,
        fill_price=fill_price,
        booking=booking,
        sham_calendar=sham_calendar,
    )


def select_families(specs: Sequence[FamilySpec], families_arg: Optional[str]) -> List[FamilySpec]:
    if families_arg is None:
        return list(specs)
    wanted = [tok.strip() for tok in families_arg.split(",") if tok.strip()]
    by_id = {s.family_id: s for s in specs}
    missing = [w for w in wanted if w not in by_id]
    if missing:
        raise DriverError(
            f"--families {','.join(missing)} not in the selection "
            f"(available: {sorted(by_id)})"
        )
    return [by_id[w] for w in wanted]


# --------------------------------------------------------------------------- #
# Manifest + panel loading (sha-pinned, fail closed)
# --------------------------------------------------------------------------- #
def load_manifest(path: Path) -> dict:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise DriverError(f"cannot read panel manifest {path}: {exc}")
    doc = json.loads(raw.decode("utf-8"))
    if not isinstance(doc.get("panel_sha256"), dict):
        raise DriverError("manifest lacks the panel_sha256 mapping")
    doc["_sha256"] = sha256_bytes(raw)
    return doc


def _finite_float(text: Any, column: str, symbol: str, key: str) -> float:
    try:
        value = float(text)
    except (TypeError, ValueError):
        raise DriverError(f"malformed panel row {symbol} {key}: {column}={text!r} not a float")
    if not math.isfinite(value):
        raise DriverError(f"malformed panel row {symbol} {key}: {column}={text!r} not finite")
    return value


def _finite_int(text: Any, column: str, symbol: str, key: str) -> int:
    try:
        value = int(str(text).strip())
    except (TypeError, ValueError):
        raise DriverError(f"malformed panel row {symbol} {key}: {column}={text!r} not an int")
    return value


def verify_panel_sha(path: Path, expected_sha: str, symbol: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    got = digest.hexdigest()
    if got != str(expected_sha):
        raise DriverError(
            f"panel sha256 MISMATCH for {symbol}: {path} sha256={got} "
            f"!= manifest {expected_sha}; refusing (fail closed)"
        )


def load_panel(panel_path: Path, symbol: str) -> List[dict]:
    """Load and fail-closed-validate one staged UTC-H1 panel."""
    if not panel_path.exists():
        raise DriverError(f"staged panel missing: {panel_path}")
    rows: List[dict] = []
    with panel_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [c for c in H1_SCHEMA if c not in header]
        if missing:
            raise DriverError(f"panel {panel_path} missing columns {missing}")
        for raw in reader:
            if any(v is None for v in raw.values()):
                raise DriverError(f"malformed panel row (ragged) for {symbol}: {raw!r}")
            hk = str(raw["hour_utc"]).strip()
            if not HOUR_KEY_RE.match(hk):
                raise DriverError(f"malformed panel row {symbol}: bad hour_utc {raw['hour_utc']!r}")
            dk = str(raw["day_utc"]).strip()
            if dk != hk[:10]:
                raise DriverError(
                    f"malformed panel row {symbol} {hk}: day_utc {dk!r} != hour_utc date"
                )
            sym = str(raw["symbol"]).strip()
            if sym != symbol:
                raise DriverError(f"malformed panel row: symbol {sym!r} inside {symbol} panel")
            rec: Dict[str, Any] = {"symbol": sym, "hour_utc": hk, "day_utc": dk}
            for col in _H1_FLOAT_COLUMNS:
                rec[col] = _finite_float(raw[col], col, sym, hk)
            for col in _H1_INT_COLUMNS:
                rec[col] = _finite_int(raw[col], col, sym, hk)
            rec["run_close_dir"] = str(raw["run_close_dir"]).strip()
            if rec["last_price"] <= 0.0 or rec["vwap"] <= 0.0:
                raise DriverError(f"malformed panel row {sym} {hk}: non-positive price/vwap")
            if rec["high_price"] < rec["low_price"]:
                raise DriverError(f"malformed panel row {sym} {hk}: high < low")
            rows.append(rec)
    if not rows:
        raise DriverError(f"panel {panel_path} has zero rows")
    keys = [r["hour_utc"] for r in rows]
    if sorted(keys) != keys or len(set(keys)) != len(keys):
        raise DriverError(f"panel {panel_path}: hour_utc not strictly ascending/unique")
    return rows


def load_panels(
    root: Path,
    manifest: dict,
    symbols: Sequence[str],
    *,
    panel_dir: Optional[Path] = None,
) -> Dict[str, List[dict]]:
    """Verify each file's sha256 against the manifest, then load it."""
    base = panel_dir if panel_dir is not None else root / PANEL_DIR
    pairs = manifest["panel_sha256"]
    panels: Dict[str, List[dict]] = {}
    for sym in symbols:
        expected = pairs.get(sym)
        if not isinstance(expected, str) or not expected:
            raise DriverError(f"manifest panel_sha256 lacks symbol {sym}")
        path = base / PANEL_FILE.format(symbol=sym)
        verify_panel_sha(path, expected, sym)
        rows = load_panel(path, sym)
        expected_rows = manifest.get("hourly_rows", {}).get(sym)
        if expected_rows is not None and int(expected_rows) != len(rows):
            raise DriverError(
                f"panel {sym}: {len(rows)} rows != manifest hourly_rows {expected_rows}"
            )
        panels[sym] = rows
    base_grid = [r["hour_utc"] for r in panels[symbols[0]]]
    for sym in symbols[1:]:
        if [r["hour_utc"] for r in panels[sym]] != base_grid:
            raise DriverError(f"panel hour grids differ across symbols at {sym}")
    window = manifest.get("window")
    if isinstance(window, list) and len(window) == 2:
        first_day = panels[symbols[0]][0]["day_utc"]
        last_day = panels[symbols[0]][-1]["day_utc"]
        if [first_day, last_day] != [str(window[0]), str(window[1])]:
            raise DriverError(
                f"panel window {first_day}..{last_day} != manifest window {window}"
            )
    return panels


# --------------------------------------------------------------------------- #
# Derived frames: H4 buckets and daily aggregates from the H1 rows in memory
# --------------------------------------------------------------------------- #
def _aggregate_group(symbol: str, key: str, group: Sequence[dict], granularity: str) -> dict:
    """Deterministic aggregate of one bucket's H1 rows (order preserved)."""
    qty_total = math.fsum(float(r["qty_total"]) for r in group)
    quote_total = math.fsum(float(r["quote_total"]) for r in group)
    if qty_total <= 0.0:
        raise DriverError(
            f"degenerate {granularity} bucket {symbol} {key}: zero qty_total "
            "(vwap undefined, fail closed)"
        )
    return {
        "symbol": symbol,
        "hour_utc": key,
        "day_utc": group[0]["day_utc"],
        "n_trades": int(math.fsum(int(r["n_trades"]) for r in group)),
        "buy_count": int(math.fsum(int(r["buy_count"]) for r in group)),
        "sell_count": int(math.fsum(int(r["sell_count"]) for r in group)),
        "buy_qty": math.fsum(float(r["buy_qty"]) for r in group),
        "sell_qty": math.fsum(float(r["sell_qty"]) for r in group),
        "buy_quote": math.fsum(float(r["buy_quote"]) for r in group),
        "sell_quote": math.fsum(float(r["sell_quote"]) for r in group),
        "quote_total": quote_total,
        "qty_total": qty_total,
        "vwap": quote_total / qty_total,
        "first_price": float(group[0]["first_price"]),
        "last_price": float(group[-1]["last_price"]),
        "high_price": max(float(r["high_price"]) for r in group),
        "low_price": min(float(r["low_price"]) for r in group),
        "max_trade_quote": max(float(r["max_trade_quote"]) for r in group),
        "sum_qty_squared": math.fsum(float(r["sum_qty_squared"]) for r in group),
        "n_price_moves": int(math.fsum(int(r["n_price_moves"]) for r in group)),
        "sum_squared_log_ret": math.fsum(float(r["sum_squared_log_ret"]) for r in group),
        "gap_sum_s": math.fsum(float(r["gap_sum_s"]) for r in group),
        "gap_count": int(math.fsum(int(r["gap_count"]) for r in group)),
        # first-row / last-row carryovers (documented, deterministic)
        "entry_gap_s": float(group[0]["entry_gap_s"]),
        "run_close_dir": group[-1]["run_close_dir"],
        "run_close_len": int(group[-1]["run_close_len"]),
        "run_switch_count": int(math.fsum(int(r["run_switch_count"]) for r in group)),
        "max_run_buy": max(int(r["max_run_buy"]) for r in group),
        "max_run_sell": max(int(r["max_run_sell"]) for r in group),
        "first_ts_ms": int(group[0]["first_ts_ms"]),
        "last_ts_ms": int(group[-1]["last_ts_ms"]),
    }


def derive_frames(
    h1: Dict[str, List[dict]], clock: str
) -> Tuple[Dict[str, List[dict]], List[str]]:
    """Bucket frames at the family clock, derived from the H1 rows.

    H1 passes the rows through; H4 groups them into 4-hour UTC buckets
    (keys ``YYYY-MM-DDTHH`` at 00/04/08/12/16/20); D1 aggregates per UTC
    day.  Returns (frames by symbol, the shared bucket-key grid).
    """
    if clock == "H1":
        grid = [r["hour_utc"] for r in h1[next(iter(h1))]]
        return {sym: [dict(r) for r in rows] for sym, rows in h1.items()}, grid
    if clock == "H4":
        def key_of(row: dict) -> str:
            hour = int(row["hour_utc"][11:13])
            return f"{row['day_utc']}T{(hour // 4) * 4:02d}"
    elif clock == "D1":
        def key_of(row: dict) -> str:
            return row["day_utc"]
    else:  # pragma: no cover - guarded by _parse_family
        raise DriverError(f"unsupported clock {clock}")
    frames: Dict[str, List[dict]] = {}
    grid: List[str] = []
    for sym, rows in h1.items():
        groups: Dict[str, List[dict]] = {}
        for row in rows:
            groups.setdefault(key_of(row), []).append(row)
        keys = sorted(groups)
        if not grid:
            grid = keys
        elif keys != grid:
            raise DriverError(f"{clock} bucket grids differ across symbols at {sym}")
        frames[sym] = [_aggregate_group(sym, k, groups[k], clock) for k in keys]
    return frames, grid


# --------------------------------------------------------------------------- #
# Folds and the 1-day purge
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Fold:
    index: int
    label: str
    member_days: Tuple[int, ...]


def fold_edges(n_days: int) -> List[int]:
    """Chronological-third edges at floor(i*N/3)."""
    if n_days < 3:
        raise DriverError(f"cannot form {FOLD_COUNT} folds from {n_days} days")
    return [i * n_days // FOLD_COUNT for i in range(FOLD_COUNT)] + [n_days]


def purged_day_indices(n_days: int) -> frozenset:
    """1-day purge: +/-1 full UTC day around each internal fold boundary.

    On the frozen 365-day S0 window this is EXACTLY
    {120, 121, 242, 243} (asserted against FROZEN_PURGED_DAY_INDICES).
    """
    edges = fold_edges(n_days)
    purged = set()
    for i in (1, 2):
        purged.add(edges[i] - 1)
        purged.add(edges[i])
    purged = {p for p in purged if 0 <= p < n_days}
    if n_days == S0_DAYS:
        if frozenset(purged) != FROZEN_PURGED_DAY_INDICES:
            raise DriverError(
                f"365-day window purge {sorted(purged)} != frozen "
                f"{sorted(FROZEN_PURGED_DAY_INDICES)}; refusing"
            )
    return frozenset(purged)


def build_folds(n_days: int) -> Tuple[List[Fold], frozenset]:
    """3 chronological folds with the 1-day purge removed from membership."""
    edges = fold_edges(n_days)
    purged = purged_day_indices(n_days)
    folds: List[Fold] = []
    for idx in range(FOLD_COUNT):
        members = tuple(d for d in range(edges[idx], edges[idx + 1]) if d not in purged)
        if not members:
            raise DriverError(f"fold F{idx} empty after the 1-day purge")
        folds.append(Fold(index=idx, label=f"F{idx}", member_days=members))
    return folds, purged


# --------------------------------------------------------------------------- #
# Exposure evaluation (registry formulas / endpoint series)
# --------------------------------------------------------------------------- #
def _formula_accepts_h1(fn: Callable[..., Any]) -> bool:
    """True iff the registered formula declares the ``h1`` keyword (or
    ``**kwargs``): such formulas receive the raw H1 rows alongside the
    family-clock frames (the ATTN-PHASE hour composition needs H1 grain)."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):  # pragma: no cover - builtins only
        return False
    if "h1" in sig.parameters:
        return True
    return any(p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())


def evaluate_exposure(
    arm: ArmSpec,
    spec: FamilySpec,
    frames: Mapping[str, Sequence[Mapping[str, Any]]],
    grid: Sequence[str],
    *,
    base_dir: Path,
    allow_example: bool,
    h1: Optional[Mapping[str, Sequence[Mapping[str, Any]]]] = None,
) -> Dict[str, List[Optional[float]]]:
    exposure = arm.exposure
    if exposure.get("type") == "panel_formula":
        formula_id = str(exposure["formula_id"])
        if is_example_only(formula_id) and not allow_example:
            raise DriverError(
                f"REFUSED: formula {formula_id!r} is EXAMPLE_TEST_ONLY and can "
                "never back a scored proposal arm"
            )
        try:
            fn = registry_resolve(formula_id)
        except KeyError as exc:
            raise DriverError(f"formula registry refusal: {exc}")
        if _formula_accepts_h1(fn):
            return fn(frames, dict(exposure.get("params", {})), h1=h1)
        return fn(frames, dict(exposure.get("params", {})))
    if exposure.get("type") == "endpoint_series":
        epath = Path(str(exposure["path"]))
        if not epath.is_absolute():
            epath = base_dir / epath
        if not epath.exists():
            raise DriverError(f"endpoint series file missing: {epath}")
        try:
            doc = json.loads(epath.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise DriverError(f"endpoint series {epath} is not valid JSON: {exc}")
        if not isinstance(doc, dict):
            raise DriverError(f"endpoint series {epath} must map symbol -> [values]")
        out: Dict[str, List[Optional[float]]] = {}
        for sym in spec.universe:
            if sym not in doc:
                raise DriverError(f"endpoint series {epath} lacks symbol {sym}")
            values = doc[sym]
            if not isinstance(values, list) or len(values) != len(grid):
                raise DriverError(
                    f"endpoint series {epath}[{sym}] length "
                    f"{len(values) if isinstance(values, list) else 'n/a'} "
                    f"!= bucket grid {len(grid)}"
                )
            series: List[Optional[float]] = []
            for v in values:
                if v is None:
                    series.append(None)
                    continue
                fv = float(v)
                if not math.isfinite(fv):
                    raise DriverError(f"endpoint series {epath}[{sym}] non-finite value")
                series.append(fv)
            out[sym] = series
        extras = sorted(set(doc) - set(spec.universe))
        if extras:
            raise DriverError(f"endpoint series {epath} carries unknown symbols {extras}")
        return out
    raise DriverError(  # pragma: no cover - guarded by _parse_family
        f"unsupported exposure type {exposure.get('type')!r}"
    )


# --------------------------------------------------------------------------- #
# Published fill prices (family "fill_price") + state-machine booking
# --------------------------------------------------------------------------- #
def build_price_map(
    spec: FamilySpec,
    frames: Mapping[str, Sequence[Mapping[str, Any]]],
    h1: Mapping[str, Sequence[Mapping[str, Any]]],
    grid: Sequence[str],
) -> Dict[str, List[float]]:
    """Per-symbol price series fills execute against (fail closed).

    * last_price (default) / vwap: the frame row's published column.
    * h1_bucket0_vwap (D1 clock): the vwap of the day's FIRST H1 bucket --
      the frozen ATTN-PHASE fill law "day t bucket-0 VWAP (close_ts 01:00)".
    """
    prices: Dict[str, List[float]] = {}
    if spec.fill_price == "h1_bucket0_vwap":
        day_of = [k[:10] for k in grid]
        for sym, rows in frames.items():
            first_vwap = {
                str(r["day_utc"]): float(r["vwap"])
                for r in h1[sym]
                if str(r["hour_utc"]).endswith("T00")
            }
            series = []
            for day in day_of:
                if day not in first_vwap:
                    raise DriverError(
                        f"fill_price h1_bucket0_vwap: {sym} lacks the hour-00 "
                        f"H1 row for {day}; refusing (fail closed)"
                    )
                series.append(first_vwap[day])
            prices[sym] = series
        return prices
    column = "last_price" if spec.fill_price == "last_price" else "vwap"
    return {sym: [float(r[column]) for r in rows] for sym, rows in frames.items()}


def h1_fold_exit_price(
    h1: Mapping[str, Sequence[Mapping[str, Any]]],
    sym: str,
    last_member_day: str,
) -> float:
    """The fold's last tradable H1 bucket VWAP: the vwap of the fold's last
    member day's hour-23 bucket (its close_ts equals the fold's last day
    boundary -- the frozen ATTN-PHASE force-flat exit price)."""
    for row in h1[sym]:
        if (
            str(row["day_utc"]) == last_member_day
            and str(row["hour_utc"]).endswith("T23")
        ):
            return float(row["vwap"])
    raise DriverError(
        f"state_machine forced exit: {sym} lacks the hour-23 H1 row for "
        f"{last_member_day}; refusing (fail closed)"
    )


def compute_state_machine_trips(
    exposures: Mapping[str, Sequence[Optional[float]]],
    spec: FamilySpec,
    grid: Sequence[str],
    folds: Sequence[Fold],
    prices: Mapping[str, Sequence[float]],
    h1: Mapping[str, Sequence[Mapping[str, Any]]],
) -> List[dict]:
    """Round trips for ``booking: "state_machine"`` (D1 long/flat books).

    The exposure formula emits the FULL position path (hold-through days
    included).  Within each fold's member days, ONE round trip is booked
    per maximal constant nonzero episode:
      entry  at the episode's first day   (family fill_price: the day's
             bucket-0 VWAP -- the frozen "decision at 00:00 fills at day t
             bucket-0 VWAP" law; the driver's one-bar lag guarantees the
             decision consumed strictly-prior days),
      exit   at the first member day whose path differs (the OFF decision
             day: "an OFF decision closes the position at that day's
             bucket-0 VWAP"),
      forced exit at the fold's LAST member day, at that day's hour-23 H1
             bucket VWAP ("closed at that fold's last tradable H1 bucket
             VWAP") when the episode reaches the fold edge -- so no
             position ever crosses a fold boundary or the +/-1-day purge,
             and the book re-enters at the next fold's first member day if
             the state is still ON ("the machinery resumes at the first
             decision after the purge").
    """
    if spec.clock != "D1":  # pragma: no cover - guarded in _parse_family
        raise DriverError("state_machine booking requires the D1 clock")
    trips: List[dict] = []
    for sym in spec.universe:
        series = exposures[sym]
        if len(series) != len(grid):
            raise DriverError(
                f"state_machine[{sym}]: path length {len(series)} != grid "
                f"{len(grid)}"
            )
        # path[b] = position held over day-b buckets (None/0 warmup = flat);
        # series[i] is the decision for day i+1 (driver one-bar lag).
        path = [0.0] * len(grid)
        for i, value in enumerate(series):
            if value is not None and value != 0.0:
                if i + 1 < len(grid):
                    path[i + 1] = float(value)
        for fold in folds:
            members = [b for b in fold.member_days if b < len(grid)]
            i = 0
            while i < len(members):
                b = members[i]
                if path[b] == 0.0:
                    i += 1
                    continue
                j = i
                while (
                    j + 1 < len(members) and path[members[j + 1]] == path[b]
                ):
                    j += 1
                entry_b = members[i]
                entry_price = float(prices[sym][entry_b])
                if j + 1 < len(members):
                    exit_b = members[j + 1]
                    exit_price = float(prices[sym][exit_b])
                else:
                    # episode reaches the fold edge: force-flat at the fold's
                    # last tradable H1 bucket VWAP
                    exit_b = members[j]
                    exit_price = h1_fold_exit_price(h1, sym, grid[exit_b][:10])
                trips.append(
                    {
                        "symbol": sym,
                        "decision_bucket": entry_b,
                        "entry_bucket": entry_b,
                        "exit_bucket": exit_b,
                        "fold_label": fold.label,
                        "fold_index": fold.index,
                        "position": path[b],
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "forced_exit": j + 1 >= len(members),
                    }
                )
                i = j + 1
    trips.sort(key=lambda t: (t["entry_bucket"], t["symbol"], t["decision_bucket"]))
    return trips


# --------------------------------------------------------------------------- #
# Books and fills (L-V14-0 remediated kernel; cost exactly once per fill)
# --------------------------------------------------------------------------- #
def fill_cost(notional: float, price: float, tier: str) -> float:
    """One fill's charge, EXACTLY ONCE (L-V14-0):
    notional * (taker_fee_bps*1e-4*fee_multiplier + slip_ticks*tick/price).

    Identical arithmetic to the audited kernel primitive
    ``GenericStrategyBase.rebalance_cost_between`` (pinned by test)."""
    t = STRESS_TIERS[tier]
    rate = (
        TAKER_FEE_BPS * 1e-4 * float(t["fee_multiplier"])
        + int(t["slip_ticks"]) * TICK_SIZE / price
    )
    return notional * rate


@dataclass
class FillRecord:
    """One fill: cost lives HERE, once; holding terms exactly zero."""

    symbol: str
    decision_bucket: int
    fold_label: str
    role: str  # "entry" | "exit"
    bucket: int
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
    n_refused_purge: int = 0
    bucket_pnl: Dict[int, float] = field(default_factory=dict)
    per_symbol: Dict[str, float] = field(default_factory=dict)
    per_fold: Dict[str, float] = field(default_factory=dict)
    fold_population: Dict[str, int] = field(default_factory=dict)
    round_trips: List[dict] = field(default_factory=list)
    fills: List[FillRecord] = field(default_factory=list)


def compute_round_trips(
    positions: Mapping[str, Mapping[int, float]],
    spec: FamilySpec,
    bucket_day: Sequence[int],
    folds: Sequence[Fold],
    purged: frozenset,
    n_buckets: int,
    *,
    lag_buckets: Optional[int] = None,
    holding_buckets: Optional[int] = None,
) -> List[dict]:
    """Bookable round trips (one per decision), force-flat on the purge.

    A decision at bucket d is REFUSED (never booked) when its holding
    window [d+lag, d+lag+holding] touches a purged UTC day, when the
    decision day is purged, when entry/exit leave the decision's fold, or
    when the round trip would run off the grid.  ``lag_buckets`` /
    ``holding_buckets`` override the family spec values (arm-level frozen
    overrides); None keeps the family value.
    """
    lag = spec.lag_buckets if lag_buckets is None else int(lag_buckets)
    holding = spec.holding_buckets if holding_buckets is None else int(holding_buckets)
    fold_by_day: Dict[int, Fold] = {}
    for fold in folds:
        for day in fold.member_days:
            fold_by_day[day] = fold
    trips: List[dict] = []
    for sym in spec.universe:
        for d in sorted(positions.get(sym, {})):
            pos = positions[sym][d]
            if pos == 0:
                continue
            decision_day = bucket_day[d]
            fold = fold_by_day.get(decision_day)
            if fold is None:
                continue  # decision on a purged day: refused
            entry = d + lag
            exit_b = entry + holding
            if entry > n_buckets - 1 or exit_b > n_buckets - 1:
                continue  # force-flat: runs off the grid
            window_days = {bucket_day[b] for b in range(entry, exit_b + 1)}
            if window_days & set(purged):
                continue  # force-flat: holding window crosses a purged UTC day
            if not window_days <= set(fold.member_days):
                continue  # force-flat: would carry across the fold boundary
            trips.append(
                {
                    "symbol": sym,
                    "decision_bucket": d,
                    "entry_bucket": entry,
                    "exit_bucket": exit_b,
                    "fold_label": fold.label,
                    "fold_index": fold.index,
                    "position": float(pos),
                }
            )
    trips.sort(key=lambda t: (t["entry_bucket"], t["symbol"], t["decision_bucket"]))
    return trips


def simulate_book(
    trips: Sequence[dict],
    prices: Mapping[str, Sequence[float]],
    tier: str,
    universe: Sequence[str],
    *,
    drop_symbols: Tuple[str, ...] = (),
) -> BookResult:
    """Book the round trips of one tier through the once-per-fill kernel."""
    active = [s for s in universe if s not in set(drop_symbols)]
    if not active:
        raise DriverError("book has no active symbols after drop")
    result = BookResult(
        tier=tier, pnl=0.0, gross_pnl=0.0, cost_fills_total=0.0,
        cost_holding_terms_total=0.0, n_fills=0, n_round_trips=0,
    )
    for trip in trips:
        sym = trip["symbol"]
        if sym not in active:
            continue
        pos = float(trip["position"])
        # state_machine trips pin their FROZEN published fill prices
        # (episode entry/exit at the family fill_price; the forced fold-edge
        # exit at the fold's last tradable H1 bucket VWAP); event trips
        # default to the family price map at the booked buckets.
        raw_entry = trip.get("entry_price")
        raw_exit = trip.get("exit_price")
        entry_price = (
            float(raw_entry) if raw_entry is not None
            else float(prices[sym][trip["entry_bucket"]])
        )
        exit_price = (
            float(raw_exit) if raw_exit is not None
            else float(prices[sym][trip["exit_bucket"]])
        )
        notional = NOTIONAL * abs(pos)
        gross = pos * (exit_price / entry_price - 1.0) * NOTIONAL
        cost_entry = fill_cost(notional, entry_price, tier)
        cost_exit = fill_cost(notional, exit_price, tier)
        net = gross - cost_entry - cost_exit
        for role, bucket, price, charge in (
            ("entry", trip["entry_bucket"], entry_price, cost_entry),
            ("exit", trip["exit_bucket"], exit_price, cost_exit),
        ):
            result.fills.append(
                FillRecord(
                    symbol=sym, decision_bucket=trip["decision_bucket"],
                    fold_label=trip["fold_label"], role=role, bucket=bucket,
                    price=price, cost_fills=charge,
                )
            )
        result.bucket_pnl[trip["exit_bucket"]] = (
            result.bucket_pnl.get(trip["exit_bucket"], 0.0) + net
        )
        result.per_symbol[sym] = result.per_symbol.get(sym, 0.0) + net
        result.per_fold[trip["fold_label"]] = (
            result.per_fold.get(trip["fold_label"], 0.0) + net
        )
        result.fold_population[trip["fold_label"]] = (
            result.fold_population.get(trip["fold_label"], 0) + 1
        )
        result.round_trips.append(trip)
        result.pnl += net
        result.gross_pnl += gross
        result.cost_fills_total += cost_entry + cost_exit
        result.n_fills += 2
        result.n_round_trips += 1
    result.pnl = r12(result.pnl)
    result.gross_pnl = r12(result.gross_pnl)
    result.cost_fills_total = r12(result.cost_fills_total)
    result.cost_holding_terms_total = r12(result.cost_holding_terms_total)
    result.per_symbol = {s: r12(v) for s, v in sorted(result.per_symbol.items())}
    result.per_fold = {f: r12(v) for f, v in sorted(result.per_fold.items())}
    result.bucket_pnl = {b: r12(v) for b, v in sorted(result.bucket_pnl.items())}
    result.fills.sort(key=lambda f: (f.bucket, f.symbol, f.role, f.decision_bucket))
    if result.cost_holding_terms_total != 0.0 or any(
        f.cost_holding_terms != 0.0 for f in result.fills
    ):
        raise DriverError(
            "cost_holding_terms must be exactly 0 by construction "
            "(remediated L-V14-0 kernel); refusing the cell"
        )
    return result


# --------------------------------------------------------------------------- #
# Arm computation (positions -> trips -> tier books -> metrics/gates)
# --------------------------------------------------------------------------- #
@dataclass
class ArmMetrics:
    expectancy: float
    pf: float
    mdd: float
    series_len: int
    positive_folds: int
    fold_concentration: float


def arm_metrics(book: BookResult, folds: Sequence[Fold], first_b: int, last_b: int) -> ArmMetrics:
    returns: List[float] = [
        book.bucket_pnl.get(b, 0.0) for b in range(first_b, last_b + 1)
    ]
    if not returns:
        raise DriverError("empty decision window for metrics")
    expectancy = math.fsum(returns) / len(returns)
    gross_profit = math.fsum(x for x in returns if x > 0.0)
    gross_loss = -math.fsum(x for x in returns if x < 0.0)
    pf = math.inf if gross_loss == 0.0 else gross_profit / gross_loss
    cum = peak = mdd = 0.0
    for x in returns:
        cum += x
        peak = max(peak, cum)
        mdd = max(mdd, peak - cum)
    fold_pos = [book.per_fold.get(f.label, 0.0) for f in folds]
    fold_pos = [v for v in fold_pos if v > 0.0]
    total_pos = math.fsum(fold_pos)
    concentration = (max(fold_pos) / total_pos) if total_pos > 0.0 else 0.0
    return ArmMetrics(
        expectancy=r12(expectancy), pf=pf, mdd=r12(mdd), series_len=len(returns),
        positive_folds=len(fold_pos), fold_concentration=r12(concentration),
    )


def gate_margins(metrics: ArmMetrics, arm_id: str) -> List[dict]:
    """In-cell frozen gates G1..G5, PER ARM, margin = threshold - value.

    G10/G11/G12 are D2/terminal-level and are skipped in-cell.  The
    arm-attribution invariant puts arm_id on every record; the artifact
    path results/v17/{family}/{arm}/ carries it as well.
    """
    n_pos = metrics.positive_folds
    # margin convention (program-wide, V16 precedent): POSITIVE = PASS.
    # lower-bound gates (value must EXCEED threshold): margin = value - threshold;
    # upper-bound gates (value must stay UNDER ceiling): margin = threshold - value.
    # direction>False encodes the upper-bound class.
    gates = [
        ("G1", metrics.expectancy, 0.0, False),
        ("G2", metrics.pf, GATE_PF_THRESHOLD, False),
        ("G3", n_pos / FOLD_COUNT, GATE_FOLD_POSITIVE_FRACTION, False),
        ("G4", metrics.fold_concentration, GATE_FOLD_CONCENTRATION, True),
        ("G5", metrics.mdd, GATE_MDD_CEILING, True),
    ]
    records = []
    for gate, value, threshold, upper_bound in gates:
        margin = (threshold - value) if upper_bound else (value - threshold)
        records.append(
            {
                "cycle_id": CYCLE_ID,
                "gate_id": gate,
                "value": r12(value),
                "threshold": r12(threshold),
                "margin": r12(margin),
                "arm_id": arm_id,
            }
        )
    return records


def first_failing_gate(metrics: ArmMetrics) -> Optional[str]:
    """Frozen gate order; first FAIL kills the arm. None == all pass."""
    if not metrics.expectancy > 0.0:
        return "G1"
    if not metrics.pf >= GATE_PF_THRESHOLD:
        return "G2"
    if not (metrics.positive_folds / FOLD_COUNT) >= GATE_FOLD_POSITIVE_FRACTION:
        return "G3"
    if not metrics.fold_concentration <= GATE_FOLD_CONCENTRATION:
        return "G4"
    if not metrics.mdd <= GATE_MDD_CEILING:
        return "G5"
    return None


def compute_family(
    spec: FamilySpec,
    h1: Dict[str, List[dict]],
    *,
    base_dir: Path,
    allow_example: bool,
) -> dict:
    """Compute all three arms of one family (anchor book feeds the DSR)."""
    frames, grid = derive_frames(h1, spec.clock)
    n_buckets = len(grid)
    days = sorted({r["day_utc"] for r in frames[spec.universe[0]]})
    day_index = {d: i for i, d in enumerate(days)}
    for sym in spec.universe:
        if sorted({r["day_utc"] for r in frames[sym]}) != days:
            raise DriverError(f"{spec.clock} day grids differ across symbols at {sym}")
    bucket_day = [day_index[k[:10]] for k in grid]
    folds, purged = build_folds(len(days))
    fold_by_day = {day: f for f in folds for day in f.member_days}

    arms_by_kind = {arm.kind: arm for arm in spec.arms}
    prices = build_price_map(spec, frames, h1, grid)
    state: Dict[str, Any] = {
        "spec": spec, "frames": frames, "grid": grid, "days": days,
        "bucket_day": bucket_day, "folds": folds, "purged": purged,
        "prices": prices, "arms_by_kind": arms_by_kind,
    }
    arms: Dict[str, dict] = {}
    for arm in spec.arms:
        exposures = evaluate_exposure(
            arm, spec, frames, grid, base_dir=base_dir, allow_example=allow_example,
            h1=h1,
        )
        if sorted(exposures) != sorted(spec.universe):
            raise DriverError(
                f"arm {arm.arm_id}: exposure symbols {sorted(exposures)} "
                f"!= universe {sorted(spec.universe)}"
            )
        positions: Dict[str, Dict[int, float]] = {}
        decision_days: List[int] = []
        for sym in spec.universe:
            series = exposures[sym]
            if len(series) != n_buckets:
                raise DriverError(
                    f"arm {arm.arm_id}[{sym}]: exposure length {len(series)} "
                    f"!= bucket grid {n_buckets}"
                )
            pos_map: Dict[int, float] = {}
            for d in range(1, n_buckets):
                signal = series[d - 1]  # one-bar lag: rows <= d-1 only
                if signal is None or signal == 0.0:
                    continue
                if not math.isfinite(float(signal)):
                    raise DriverError(
                        f"arm {arm.arm_id}[{sym}]: non-finite signal at {grid[d-1]}"
                    )
                pos_map[d] = float(signal)
                decision_days.append(d)
            positions[sym] = pos_map
        if not decision_days:
            arms[arm.arm_id] = {
                "arm": arm, "positions": positions, "trips": [],
                "books": {
                    tier: BookResult(
                        tier=tier, pnl=0.0, gross_pnl=0.0, cost_fills_total=0.0,
                        cost_holding_terms_total=0.0, n_fills=0, n_round_trips=0,
                    )
                    for tier in STRESS_TIERS
                },
                "metrics": None, "first_b": None, "last_b": None,
            }
            continue
        if spec.booking == "state_machine":
            trips = compute_state_machine_trips(
                exposures, spec, grid, folds, prices, h1
            )
        else:
            trips = compute_round_trips(
                positions, spec, bucket_day, folds, purged, n_buckets,
                lag_buckets=arm.lag_override,
                holding_buckets=arm.holding_override,
            )
        books = {
            tier: simulate_book(trips, prices, tier, spec.universe)
            for tier in STRESS_TIERS
        }
        drop_one_books = {
            omitted: simulate_book(
                trips, prices, PRIMARY_TIER, spec.universe,
                drop_symbols=(omitted,),
            )
            for omitted in spec.universe
        }
        # force-flat proof: every booked trip sits inside one fold, purge untouched
        for trip in books[PRIMARY_TIER].round_trips:
            decision_day = bucket_day[trip["decision_bucket"]]
            fold = fold_by_day.get(decision_day)
            if fold is None or trip["fold_label"] != fold.label:
                raise DriverError("force-flat violated: trip escaped its fold")
            window_days = {
                bucket_day[b]
                for b in range(trip["entry_bucket"], trip["exit_bucket"] + 1)
            }
            if window_days & set(purged) or not window_days <= set(fold.member_days):
                raise DriverError("force-flat violated: trip crossed purge/fold edge")
        decision_set = sorted(set(decision_days))
        first_b, last_b = decision_set[0], decision_set[-1]
        metrics = arm_metrics(books[PRIMARY_TIER], folds, first_b, last_b)
        arms[arm.arm_id] = {
            "arm": arm, "positions": positions, "trips": trips, "books": books,
            "drop_one_books": drop_one_books, "metrics": metrics,
            "first_b": first_b, "last_b": last_b,
        }
    state["arms"] = arms
    return state


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


def data_snapshot_digest(manifest: dict, universe: Sequence[str]) -> Dict[str, str]:
    pairs = manifest["panel_sha256"]
    return {sym: str(pairs[sym]) for sym in universe}


# --------------------------------------------------------------------------- #
# Emission
# --------------------------------------------------------------------------- #
def _emit(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canon_json(records), encoding="utf-8")


def _check_canon(category: str, records: Sequence[Mapping[str, Any]]) -> None:
    want = set(CANON_FIELDS[category])
    for rec in records:
        missing = want - set(rec)
        if missing:
            raise DriverError(
                f"{category} record missing canon fields {sorted(missing)}"
            )


def emit_scored_arm(
    spec: FamilySpec,
    state: dict,
    manifest: dict,
    arm_id: str,
    out_root: Path,
    *,
    code_freeze_sha: str,
    scored_root: Path = SCORED_ROOT,
) -> dict:
    """Scored emission for ONE arm: the 10 scaffold categories."""
    arm_state = state["arms"].get(arm_id)
    if arm_state is None:
        raise DriverError(f"arm {arm_id} not in family {spec.family_id}")
    arm = arm_state["arm"]
    if arm_state["metrics"] is None or arm_state["books"][PRIMARY_TIER].n_round_trips == 0:
        raise DriverError(
            f"VACUOUS CELL: arm {spec.family_id}/{arm_id} booked zero decisions "
            "(non-vacuity failure, V8 F-A7-1)"
        )
    book = arm_state["books"][PRIMARY_TIER]
    folds: Sequence[Fold] = state["folds"]
    grid: Sequence[str] = state["grid"]
    metrics = arm_state["metrics"]
    arm_dir = out_root / scored_root / spec.family_id / arm_id

    identity = {
        "cycle_id": CYCLE_ID,
        "family_id": spec.family_id,
        "arm_id": arm_id,
        "arm_config_digest": arm.arm_config_digest,
        "data_snapshot_digest": data_snapshot_digest(manifest, spec.universe),
        "code_freeze_sha": code_freeze_sha,
        "cost_tier": PRIMARY_TIER,
    }
    _check_canon("identity", [identity])

    series = [
        {
            "cycle_id": CYCLE_ID,
            "arm_id": arm_id,
            "period": grid[b],
            "returns": r12(book.bucket_pnl.get(b, 0.0)),
        }
        for b in range(arm_state["first_b"], arm_state["last_b"] + 1)
    ]
    _check_canon("per_period_series", series)

    per_symbol = [
        {
            "cycle_id": CYCLE_ID,
            "symbol": sym,
            "contribution_pnl": r12(book.per_symbol.get(sym, 0.0)),
        }
        for sym in sorted(spec.universe)
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
        {
            "cycle_id": CYCLE_ID,
            "tier": tier,
            "pnl": r12(arm_state["books"][tier].pnl),
        }
        for tier in sorted(STRESS_TIERS)
    ]
    _check_canon("stress_tiers", stress)

    drop_one = [
        {
            "cycle_id": CYCLE_ID,
            "omitted_symbol": omitted,
            "pnl": r12(arm_state["drop_one_books"][omitted].pnl),
        }
        for omitted in sorted(spec.universe)
    ]
    _check_canon("drop_one_inputs", drop_one)

    benchmark_name = f"EQW buy-and-hold {'+'.join(sorted(spec.universe))}"
    bucket_day: Sequence[int] = state["bucket_day"]
    prices: Mapping[str, Sequence[float]] = state["prices"]
    benchmark = []
    for fold in folds:
        member_buckets = [b for b, day in enumerate(bucket_day) if day in set(fold.member_days)]
        first_b, last_b = member_buckets[0], member_buckets[-1]
        legs = [
            prices[sym][last_b] / prices[sym][first_b] - 1.0 for sym in sorted(spec.universe)
        ]
        bench = math.fsum(legs) / len(legs)
        benchmark.append(
            {
                "cycle_id": CYCLE_ID,
                "fold_id": fold.label,
                "benchmark": benchmark_name,
                "excess_return": r12(book.per_fold.get(fold.label, 0.0) - bench),
            }
        )
    _check_canon("benchmark_context", benchmark)

    margins = gate_margins(metrics, arm_id)
    _check_canon("margins_to_fail", margins)

    counters = {
        "observed_delta": 1,
        "published_delta": 1,
        "budget_used": 1,
        "reruns_not_trials": True,
    }
    _check_canon("counters", [counters])

    reproduction = {
        "code_freeze_sha": code_freeze_sha,
        "data_manifest_sha": manifest["_sha256"],
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

    # Conditional diag/sham_control_calendar@1 rows (A8 families lane): the
    # family's frozen control-calendar descriptor -- the ATTN-PHASE sham
    # rotation, or the SILRES not-applicable marker per the D2 re-freeze.
    if spec.sham_calendar is not None:
        sham_rows = [
            {
                "cycle_id": CYCLE_ID,
                "arm_id": arm_id,
                "calendar": str(spec.sham_calendar["calendar"]),
                "note": str(spec.sham_calendar.get("note", "")),
            }
        ]
        _check_canon("sham_control_calendar", sham_rows)
        _emit(arm_dir / "sham_control_calendar.jsonl", sham_rows)

    kernel = {
        "remediated_kernel": True,
        "cost_fills": book.cost_fills_total,
        "cost_holding_terms": book.cost_holding_terms_total,
        "n_fills": book.n_fills,
        "n_round_trips": book.n_round_trips,
        "first_failing_gate": first_failing_gate(metrics),
    }
    return {"kernel": kernel, "metrics": metrics, "margins": margins, "arm": arm}


def emit_family_dsr(
    spec: FamilySpec, state: dict, out_root: Path, *,
    scored_root: Path = SCORED_ROOT,
) -> None:
    """Family-level dsr_per_period_series.jsonl from the ANCHOR book (V16 canon)."""
    anchor = state["arms"].get(_anchor_arm_id(spec))
    if anchor is None or anchor["metrics"] is None:
        raise DriverError(
            f"family {spec.family_id}: anchor book unavailable for the DSR series"
        )
    anchor_book = anchor["books"][PRIMARY_TIER]
    grid: Sequence[str] = state["grid"]
    dsr = [
        {
            "cycle_id": CYCLE_ID,
            "period": grid[b],
            "returns": r12(anchor_book.bucket_pnl.get(b, 0.0)),
        }
        for b in range(anchor["first_b"], anchor["last_b"] + 1)
    ]
    _check_canon("dsr_per_period_series", dsr)
    _emit(out_root / scored_root / spec.family_id / "dsr_per_period_series.jsonl", dsr)


def _anchor_arm_id(spec: FamilySpec) -> str:
    for arm in spec.arms:
        if arm.kind == "anchor":
            return arm.arm_id
    raise DriverError(f"family {spec.family_id}: no anchor arm")  # pragma: no cover


def emit_sanitized_arm(
    spec: FamilySpec,
    state: dict,
    arm_id: str,
    out_root: Path,
) -> int:
    """Sanitized dry-run: decision surface ONLY, zero outcome fields.

    decision_taken mirrors the T1.0 base book's booked decisions after
    force-flat.  Zero booked decisions is a HARD FAILURE (V8 F-A7-1).
    """
    arm_state = state["arms"].get(arm_id)
    if arm_state is None:
        raise DriverError(f"arm {arm_id} not in family {spec.family_id}")
    base_trips = {
        (t["symbol"], t["decision_bucket"])
        for t in simulate_book(
            arm_state["trips"], state["prices"], "T1.0", spec.universe
        ).round_trips
    }
    if spec.booking == "state_machine":
        # the OFF decision that closes an episode is a booked decision too
        base_trips |= {
            (t["symbol"], t["exit_bucket"])
            for t in arm_state["trips"]
            if not t.get("forced_exit", False)
        }
    grid: Sequence[str] = state["grid"]
    bucket_day: Sequence[int] = state["bucket_day"]
    days: Sequence[str] = state["days"]
    records: List[dict] = []
    positions = arm_state["positions"]
    decision_buckets = sorted({d for sym in spec.universe for d in positions.get(sym, {})})
    for d in decision_buckets:
        for sym in sorted(spec.universe):
            if d not in positions.get(sym, {}):
                continue
            records.append(
                {
                    "cycle_id": CYCLE_ID,
                    "family_id": spec.family_id,
                    "arm_id": arm_id,
                    "date": days[bucket_day[d]],
                    "hour": grid[d],
                    "decision_taken": (sym, d) in base_trips,
                    "symbol": sym,
                }
            )
    n_decisions = sum(1 for r in records if r["decision_taken"])
    if n_decisions == 0:
        raise DriverError(
            f"HARD FAILURE: sanitized dry-run of {spec.family_id}/{arm_id} is VACUOUS "
            "(zero booked decisions, V8 F-A7-1)"
        )
    _check_canon("sanitized_decisions", records)
    for rec in records:
        for key in rec:
            if LEAK_PATTERN.search(str(key)):
                raise DriverError(f"sanitized leak: field {key!r} is outcome-shaped")
    _emit(
        out_root / SANITIZED_ROOT / spec.family_id / arm_id / "decisions.jsonl",
        records,
    )
    return n_decisions


# --------------------------------------------------------------------------- #
# Family driver
# --------------------------------------------------------------------------- #
def run_family(
    spec: FamilySpec,
    manifest: dict,
    root: Path,
    out_root: Path,
    *,
    sanitized: bool,
    base_dir: Path,
    code_freeze_sha: Optional[str] = None,
    scored_root: Path = SCORED_ROOT,
) -> dict:
    h1 = load_panels(root, manifest, spec.universe)
    state = compute_family(
        spec, h1, base_dir=base_dir, allow_example=sanitized
    )
    head = code_freeze_sha if code_freeze_sha is not None else git_head_sha(root)
    if sanitized:
        summary = {}
        for arm in spec.arms:
            n = emit_sanitized_arm(spec, state, arm.arm_id, out_root)
            summary[arm.arm_id] = n
        return {"sanitized": True, "decisions": summary}
    results = {}
    for arm in spec.arms:
        results[arm.arm_id] = emit_scored_arm(
            spec, state, manifest, arm.arm_id, out_root,
            code_freeze_sha=head, scored_root=scored_root,
        )
    emit_family_dsr(spec, state, out_root, scored_root=scored_root)
    return {"sanitized": False, "arms": results}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="CRYPTO-V17 family-agnostic scored cell driver + sanitized mode"
    )
    parser.add_argument(
        "--selection", required=True,
        help="frozen selection JSON holding the family specs",
    )
    parser.add_argument(
        "--families", default=None,
        help="comma-separated family_ids to run (default: all in the selection)",
    )
    parser.add_argument(
        "--sanitized", action="store_true",
        help="emit the sanitized decision surface only (no outcome fields)",
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help="scored pipeline into results/v17_smoke/ (isolated namespace), "
             "exactly one family",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    selection_path = Path(args.selection)
    _, specs = load_selection(selection_path)
    selected = select_families(specs, args.families)
    if args.smoke and len(selected) != 1:
        raise DriverError("--smoke requires exactly one family (--families ID)")
    if args.smoke and args.sanitized:
        raise DriverError("--smoke and --sanitized are mutually exclusive")
    out_root = Path.cwd()
    manifest = load_manifest(root / MANIFEST_FILE)
    known = set(manifest["panel_sha256"])
    for spec in selected:
        unknown = [sym for sym in spec.universe if sym not in known]
        if unknown:
            raise DriverError(
                f"family {spec.family_id}: universe symbols {unknown} "
                "absent from the panel manifest"
            )
    if args.sanitized:
        for spec in selected:
            summary = run_family(
                spec, manifest, root, out_root,
                sanitized=True, base_dir=selection_path.resolve().parent,
            )
            for arm_id, n in summary["decisions"].items():
                print(
                    f"sanitized dry-run {spec.family_id}/{arm_id}: "
                    f"{n} booked decisions, 0 outcome fields emitted"
                )
        return 0
    scored_root = SMOKE_ROOT if args.smoke else SCORED_ROOT
    smoke_tag = " [SMOKE]" if args.smoke else ""
    for spec in selected:
        result = run_family(
            spec, manifest, root, out_root,
            sanitized=False, base_dir=selection_path.resolve().parent,
            scored_root=scored_root,
        )
        for arm_id, res in result["arms"].items():
            kernel = res["kernel"]
            print(
                f"scored emission{smoke_tag} {spec.family_id}/{arm_id}: "
                f"{kernel['n_round_trips']} round trips / {kernel['n_fills']} fills, "
                f"cost_fills={kernel['cost_fills']} "
                f"cost_holding_terms={kernel['cost_holding_terms']} "
                f"remediated_kernel={kernel['remediated_kernel']} "
                f"first_failing_gate={kernel['first_failing_gate']}"
            )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DriverError as exc:
        print(f"DRIVER_REFUSAL: {exc}", file=sys.stderr)
        sys.exit(2)
