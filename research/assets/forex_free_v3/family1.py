"""FOREX-FREE-V3 family1: FXFV3-A5-P1 policy-differential-gated daily trend.

Implementation of the SELECTED A5-lane family
(``research/proposals/forex_free_v3/a5_lane/proposal_1.json`` -- the binding
spec) against the runner's FAMILY API CONTRACT (module docstring of
:mod:`research.assets.forex_free_v3.scored_runner`)::

    run_arm(arm, data_paths, macro_reader, freeze_token=None)
        -> {"decisions": [...], "financing_events": [...], "meta": {...}}

Arms (frozen, one parameter set each, no grids):

* ``anchor``   -- LONG base/short quote when the 21-daily-bar price momentum
  ``m = close_t/close_(t-21) - 1 > 0`` AND the 63-daily-bar point-in-time
  policy-differential drift ``g = d(t) - d(t-63) > 0``; SHORT when both are
  negative; FLAT otherwise (strict inequalities at 0, ``g == 0`` is flat).
* ``neighbour`` -- one presumption away: the macro gate is the differential
  LEVEL ``d(t) - median(d over the 252 most recent daily as-of reads)``
  instead of the drift; combined with ``m`` exactly as the anchor.
* ``control`` (``causal_negative_control``) -- macro-direction-only:
  ``sign(g)`` with no price trend anywhere (preregistered non-reproduction
  rule is the runner's CONTROL_REPRODUCES_MECHANISM gate).
* ``benchmark_treatment`` (V3-I, finding H1) -- the frozen benchmark of
  ``baseline_invariants.json v3_benchmark_treatment`` / proposal
  ``arms.incremental_benchmark`` (arm_id ``FXFV3-A5-P1-bench``),
  implemented VERBATIM: unconditional daily momentum, LONG base when
  ``m > 0``, SHORT when ``m < 0``, FLAT when ``m == 0``; identical holding
  law (exit on ``sign(m)`` flip), clock, fills, universe, warmup, costs and
  financing formula.  ZERO macro reads enter the state (the frozen
  financing accrual still reads vintages through the reader, as every arm
  does); the runner books this arm inside the scored anchor cell and
  computes the frozen incremental alpha from it.  It is never a scored
  cell of its own.

Frozen mechanics (spec, clocks section): decisions are evaluated on completed
daily bars, each the H1 snapshot bar whose OPEN instant maps to 16:00
America/New_York wall time (20:00Z in EDT weeks, 21:00Z in EST weeks, named
zone via zoneinfo); ``decision_ts`` is that open instant.  The macro as-of
read uses the same decision instant (date-only BIS availability stamps make
this the first-eligible-decision semantics the spec freezes).  Fills are the
OPEN of the NEXT EXISTING 16:00-NY bar (one-event lag; Friday decisions fill
Monday; a missing next bar voids the action fail-closed -- recorded as a
skipped decision/exit in ``meta``, never fill-forward).  Positions hold while
the arm state persists and exit at the next existing bar open when it ceases;
fold boundaries force-flat: any open position closes at the OPEN of the last
existing 16:00-NY bar before the boundary (``force_flat=true``) and no new
entry is taken on that bar or the bar before it (an entry there would fill at
or immediately before the forced flatten).

Policy rates are read ONLY through the injected ``macro_reader``
(``policy_rate(area, ts)`` / ``differential(base_area, quote_area, ts)``);
availability gating (``available_time_utc <= T``) is the reader's job and is
never bypassed.  Vintages carry percent-per-annum values (BIS adapter unit
``PERCENT_PER_ANNUM``); this module converts to annualized decimals by
dividing by 100 at the single defined point.

data_paths (opaque to the runner; consumed here):
    ``price_h1_dir``   directory directly containing the canonical TwelveData
                       H1 window files ``<TAG>_1h_*_a.json`` (the td_loader
                       schema: datetime/open/high/low/close; error-status
                       no-coverage windows are skipped; overlapping windows
                       deduped; OHLC-inconsistent bars quarantined with a
                       0.1 percent fail-closed ceiling).
    ``macro_vintages`` the runner's mapping of rate area -> vintage JSON path
                       (used only when ``macro_reader`` is None).

Determinism: same inputs -> byte-identical output.  No wall-clock reads, no
dict-order dependence (sorted iterations everywhere floats or keys could
vary), float arithmetic in fixed order, rounding ONLY at the defined
financing rounding point (10 dp, kernel convention).  ``freeze_token`` is
accepted and ignored (dummy-vs-scored is a runner-side distinction).

NO scored PnL is computed here: this module produces schedules and carries
financing events; all booking, gating and publication belong to the runner.
"""
from __future__ import annotations

import json
import math
import os
import statistics
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

__all__ = ["PROPOSAL_ID", "PAIR_AREAS", "run_arm", "load_pair_h1_bars",
           "daily_decision_bars", "pair_state_series", "schedule_pair",
           "financing_adjustment_usd"]

PROPOSAL_ID = "FXFV3-A5-P1"

PAIRS = ("EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD",
         "USD/JPY", "USD/CHF", "USD/CAD")

# Frozen market convention: pair -> (base rate area, quote rate area).
PAIR_AREAS = {
    "EUR/USD": ("EMU", "US"),
    "GBP/USD": ("GB", "US"),
    "AUD/USD": ("AU", "US"),
    "NZD/USD": ("NZ", "US"),
    "USD/JPY": ("US", "JP"),
    "USD/CHF": ("US", "CH"),
    "USD/CAD": ("US", "CA"),
}

ARMS = ("anchor", "neighbour", "causal_negative_control")
BENCHMARK_ARM = "benchmark_treatment"  # required by the runner, never a scored cell
ARM_ALIASES = {"control": "causal_negative_control"}
ARM_IDS = {
    "anchor": "FXFV3-A5-P1-anchor",
    "neighbour": "FXFV3-A5-P1-neigh",
    "causal_negative_control": "FXFV3-A5-P1-ctrl",
    "benchmark_treatment": "FXFV3-A5-P1-bench",  # proposal arms.incremental_benchmark
}

MOMENTUM_BARS = 21          # m = c_t / c_(t-21) - 1
DRIFT_BARS = 63             # g = d(t) - d(t-63), as-of reads at both instants
NEIGHBOUR_MEDIAN_BARS = 252 # neighbour gate: d(t) vs trailing 252-read median
NOTIONAL_USD = 10000        # frozen USD-unit design
MAX_FILL_LAG_DAYS = 4       # mirror of the runner's one-event-lag allowance
FINANCING_FORMULA = "V3_FROZEN_POLICY_RATE_CARRY"
FINANCING_ROUND_DP = 10     # single defined rounding point (kernel convention)
FINANCING_DISCLOSURE = (
    "policy rates are unsecured official rates, NOT swap/OIS-implied or "
    "broker rollover financing; per-calendar-day accrual at the day-start "
    "as-of differential per baseline_invariants.json v3_financing_formula")
QUARANTINE_CEILING = 0.001  # td_loader-inherited OHLC-artifact ceiling

_NY = ZoneInfo("America/New_York")
_UTC = timezone.utc
_INTERNAL_BOUNDARIES = ("2022-05-01T00:00:00+00:00", "2024-07-01T00:00:00+00:00")


# --------------------------------------------------------------------------
# price loading (td_loader schema, mirrored minimally and deterministically)
# --------------------------------------------------------------------------
def _parse_bar_ts(raw):
    """Snapshot bar stamps are UTC wall time; accept the canonical
    'YYYY-MM-DD HH:MM:SS' form and ISO-T fallback; fail closed otherwise."""
    if not isinstance(raw, str):
        raise ValueError(f"malformed bar timestamp: {raw!r}")
    text = raw.strip()
    try:
        t = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        t = datetime.fromisoformat(text)  # ISO-T fallback
    if t.tzinfo is not None:
        return t.astimezone(_UTC)
    return t.replace(tzinfo=_UTC)


def load_pair_h1_bars(pair: str, price_h1_dir: str) -> list:
    """Ascending, unique, validated H1 bars for one pair from the canonical
    window files (``<TAG>_1h_*_a.json``) under ``price_h1_dir``.

    Error-status provider windows (no coverage) are skipped; overlapping
    windows dedupe on the bar stamp; OHLC-inconsistent provider artifacts are
    quarantined (excluded, counted) with the inherited 0.1 percent
    fail-closed ceiling.  Each bar is ``(open_utc, open, high, low, close)``.
    """
    tag = pair.replace("/", "")
    if not os.path.isdir(price_h1_dir):
        raise RuntimeError(
            f"BLOCKED_DATA: no price H1 directory for {pair}: {price_h1_dir!r}")
    names = sorted(f for f in os.listdir(price_h1_dir)
                   if f.startswith(f"{tag}_1h_") and f.endswith("_a.json")
                   and "TRUNCATED" not in f)
    if not names:
        raise RuntimeError(
            f"BLOCKED_DATA: no canonical H1 window files for {pair} under {price_h1_dir!r}")
    rows: list = []
    seen: set = set()
    quarantined = 0
    considered = 0
    for name in names:
        with open(os.path.join(price_h1_dir, name), "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict) and payload.get("status") == "error":
            continue  # provider no-coverage window (recorded upstream in the probe)
        values = payload.get("values") if isinstance(payload, dict) else None
        if not isinstance(values, list):
            raise RuntimeError(f"BLOCKED_DATA: malformed H1 window {name!r}")
        for row in values:
            try:
                ts = _parse_bar_ts(row["datetime"])
                bar = (ts, float(row["open"]), float(row["high"]),
                       float(row["low"]), float(row["close"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError(f"BLOCKED_DATA: malformed bar in {name!r}: {exc}") from exc
            if ts in seen:
                continue  # boundary overlap between adjacent windows
            considered += 1
            o, h, lo, c = bar[1], bar[2], bar[3], bar[4]
            if not (h >= lo and h >= o and h >= c and lo <= o and lo <= c
                    and o > 0 and c > 0):
                quarantined += 1
                continue
            seen.add(ts)
            rows.append(bar)
    if considered and quarantined / considered > QUARANTINE_CEILING:
        raise RuntimeError(
            f"BLOCKED_DATA: quarantine ceiling exceeded for {pair}: "
            f"{quarantined}/{considered}")
    rows.sort(key=lambda b: b[0])
    return rows


# --------------------------------------------------------------------------
# daily decision bars (16:00 America/New_York, named zone, never fixed UTC)
# --------------------------------------------------------------------------
def daily_decision_bars(h1_bars: list) -> list:
    """The daily decision bars: H1 bars whose OPEN instant maps to 16:00
    America/New_York wall time AND fall inside the frozen trading week
    (Sun 21:00 New York -> Fri 16:00 New York).  Provider Sunday 16:00-NY
    artifacts sit BEFORE the weekly open and are excluded, so a Friday
    decision fills at Monday's bar, never a closed Sunday bar.  Returns
    ``(open_utc, open_px, close_px)`` tuples ascending; ``decision_ts`` is
    the open instant (20:00Z EDT weeks, 21:00Z EST weeks)."""
    out = []
    for ts, o, _h, _lo, c in h1_bars:
        ny = ts.astimezone(_NY)
        if ny.hour == 16 and ny.minute == 0 and ny.weekday() < 5:
            out.append((ts, o, c))
    return out


# --------------------------------------------------------------------------
# arm state series (pure; exposed for hand-computed goldens)
# --------------------------------------------------------------------------
def _asof_differential(reader, base_area: str, quote_area: str, ts) -> float | None:
    """Percent-per-annum vintages -> annualized-decimal differential; the
    single /100 conversion point.  ``None`` = NO_EVAL (reader-gated)."""
    d = reader.differential(base_area, quote_area, ts)
    if d is None:
        return None
    return d / 100.0


def pair_state_series(pair: str, daily: list, reader, arm: str) -> list:
    """Per daily decision bar, the arm's raw inputs and state.

    Returns a list of dicts ``{"ts", "m", "d", "g", "gate", "state"}`` where
    ``m``/``d``/``g`` may be ``None`` (void: fail-closed, never backfilled),
    ``gate`` is one of ``"long"``/``"short"``/``"flat"`` (the arm's go
    direction before the state machine) and ``state`` is ``+1/-1/0/None``.

    * anchor:   go long when m>0 and g>0, short when m<0 and g<0, else flat.
    * neighbour: same but the macro leg is sign(d(t) - median(d[t-251..t])).
    * control:  long when g>0, short when g<0, flat when g==0 (no m anywhere).
    * benchmark_treatment: LONG when m>0, SHORT when m<0, FLAT when m==0;
      NO macro read anywhere (the reader is never consulted; it may be
      ``None`` for this arm).
    """
    if arm not in ARM_IDS:
        raise ValueError(f"unknown arm {arm!r}")
    base_area, quote_area = PAIR_AREAS[pair]
    n = len(daily)
    benchmark = arm == BENCHMARK_ARM
    differentials: list = [None] * n
    if not benchmark:  # zero macro reads on the benchmark treatment
        for i in range(n):
            differentials[i] = _asof_differential(reader, base_area, quote_area, daily[i][0])
    states = []
    for i in range(n):
        ts, _o, c = daily[i]
        m = None
        if i >= MOMENTUM_BARS and daily[i - MOMENTUM_BARS][2] > 0:
            m = c / daily[i - MOMENTUM_BARS][2] - 1.0
        d_now = differentials[i]
        g = None
        if i >= DRIFT_BARS and d_now is not None and differentials[i - DRIFT_BARS] is not None:
            g = d_now - differentials[i - DRIFT_BARS]
        level_gap = None
        if d_now is not None and i >= NEIGHBOUR_MEDIAN_BARS - 1:
            window = differentials[i - NEIGHBOUR_MEDIAN_BARS + 1: i + 1]
            if all(v is not None for v in window):
                level_gap = d_now - statistics.median(window)
        if arm == "anchor":
            macro = g
        elif arm == "neighbour":
            macro = level_gap
        else:
            macro = g
        if benchmark:
            # Unconditional momentum: sign(m) alone, no macro leg anywhere.
            if m is None:
                gate, state = "void", None
            elif m > 0:
                gate, state = "long", 1
            elif m < 0:
                gate, state = "short", -1
            else:
                gate, state = "flat", 0
        elif macro is None or (arm != "causal_negative_control" and m is None):
            gate, state = "void", None
        elif macro > 0 and (arm == "causal_negative_control" or m > 0):
            gate, state = "long", 1
        elif macro < 0 and (arm == "causal_negative_control" or m < 0):
            gate, state = "short", -1
        else:
            gate, state = "flat", 0
        states.append({"ts": ts, "m": m, "d": d_now, "g": g,
                       "level_gap": level_gap, "gate": gate, "state": state})
    return states


# --------------------------------------------------------------------------
# state machine -> round trips (one decision row per round trip)
# --------------------------------------------------------------------------
def _iso(t: datetime) -> str:
    return t.astimezone(_UTC).isoformat()


def _next_bar_index(daily: list, i: int):
    """Index of the next EXISTING daily bar strictly after i, else None."""
    return i + 1 if i + 1 < len(daily) else None


def schedule_pair(pair: str, daily: list, states: list, arm: str) -> dict:
    """Walk the arm's frozen state machine over one pair's daily bars and
    emit round trips plus the schedule counters (schedule-level only; no PnL
    exists in this module)."""
    force_flat_idx: set = set()
    for boundary in _INTERNAL_BOUNDARIES:
        b = datetime.fromisoformat(boundary)
        if not daily or daily[-1][0] < b:
            continue  # grid ends before this boundary: nothing can span it
        before = [i for i, bar in enumerate(daily) if bar[0] < b]
        if before:
            force_flat_idx.add(before[-1])
    suppress_entry_idx = set()
    for ff in force_flat_idx:
        suppress_entry_idx.add(ff)
        if ff - 1 >= 0:
            suppress_entry_idx.add(ff - 1)  # entry would fill AT the flatten bar

    decisions: list = []
    skipped_decisions: list = []
    skipped_exits: list = []
    counters = {"n_daily_bars": len(daily), "n_evaluated_bars": 0,
                "n_void_bars": 0, "n_go_bars": 0, "n_no_go_bars": 0,
                "n_entries": 0, "n_fills": 0, "n_skipped_entry_fills": 0,
                "n_skipped_exit_fills": 0, "n_force_flats": 0,
                "n_entries_suppressed_by_boundary": 0}
    arm_id = ARM_IDS[arm]
    def _finish(side: int, entry_i: int, fill_i: int, exit_fill_i: int,
                force_flat: bool) -> None:
        did = f"{arm_id}|{pair}|{_iso(daily[entry_i][0])}"
        decisions.append({
            "decision_id": did,
            "pair": pair,
            "decision_ts": _iso(daily[entry_i][0]),
            "side": int(side),
            "notional_usd": NOTIONAL_USD,
            "entry_bar_ts": _iso(daily[fill_i][0]),
            "entry_price": daily[fill_i][1],
            "exit_bar_ts": _iso(daily[exit_fill_i][0]),
            "exit_price": daily[exit_fill_i][1],
            "force_flat": bool(force_flat),
        })

    pos = None  # {"side", "decision_i", "fill_i"}
    for i, _bar in enumerate(daily):
        st = states[i]["state"]
        if st is None:
            counters["n_void_bars"] += 1
        else:
            counters["n_evaluated_bars"] += 1
            if st == 0:
                counters["n_no_go_bars"] += 1
            else:
                counters["n_go_bars"] += 1

        # ---- exits ------------------------------------------------------
        if pos is not None:
            if i in force_flat_idx:
                _finish(pos["side"], pos["decision_i"], pos["fill_i"], i,
                        force_flat=True)  # close AT the last pre-boundary bar's open
                counters["n_force_flats"] += 1
                pos = None
            elif st != pos["side"]:
                j = _next_bar_index(daily, i)
                exit_id = f"{arm_id}|{pair}|{_iso(daily[pos['decision_i']][0])}"
                if j is None:
                    skipped_exits.append({"decision_id": exit_id,
                                          "reason": "NO_NEXT_BAR_FOR_EXIT_FILL"})
                    counters["n_skipped_exit_fills"] += 1
                    pos = None
                elif daily[j][0] - daily[i][0] > timedelta(days=MAX_FILL_LAG_DAYS):
                    skipped_exits.append({"decision_id": exit_id,
                                          "reason": "EXIT_FILL_LAG_EXCEEDS_FROZEN_ALLOWANCE"})
                    counters["n_skipped_exit_fills"] += 1
                    pos = None
                else:
                    _finish(pos["side"], pos["decision_i"], pos["fill_i"], j,
                            force_flat=False)
                    pos = None

        # ---- entries ----------------------------------------------------
        if pos is None and st in (1, -1):
            if i in suppress_entry_idx:
                counters["n_entries_suppressed_by_boundary"] += 1
                continue
            j = _next_bar_index(daily, i)
            if j is None:
                skipped_decisions.append(
                    {"decision_ts": _iso(daily[i][0]), "pair": pair,
                     "state": int(st), "reason": "NO_NEXT_BAR_FOR_ENTRY_FILL"})
                counters["n_skipped_entry_fills"] += 1
                continue
            if daily[j][0] - daily[i][0] > timedelta(days=MAX_FILL_LAG_DAYS):
                skipped_decisions.append(
                    {"decision_ts": _iso(daily[i][0]), "pair": pair,
                     "state": int(st),
                     "reason": "ENTRY_FILL_LAG_EXCEEDS_FROZEN_ALLOWANCE"})
                counters["n_skipped_entry_fills"] += 1
                continue
            pos = {"side": int(st), "decision_i": i, "fill_i": j}
            counters["n_entries"] += 1
            counters["n_fills"] += 1

    first_ts = _iso(daily[0][0]) if daily else None
    last_ts = _iso(daily[-1][0]) if daily else None
    counters["first_decision_bar_utc"] = first_ts
    counters["last_decision_bar_utc"] = last_ts
    return {"decisions": decisions, "skipped_decisions": skipped_decisions,
            "skipped_exits": skipped_exits, "counters": counters}


# --------------------------------------------------------------------------
# financing events (frozen v3_financing_formula, carried never computed by
# the runner)
# --------------------------------------------------------------------------
def financing_adjustment_usd(pair: str, decision: dict, reader) -> float:
    """``sign * notional * sum_of_daily(d) / 365`` accrued per calendar day
    at that day's 00:00Z as-of differential over the held calendar days."""
    base_area, quote_area = PAIR_AREAS[pair]
    entry = datetime.fromisoformat(decision["entry_bar_ts"])
    exit_ = datetime.fromisoformat(decision["exit_bar_ts"])
    day = entry.astimezone(_UTC).replace(hour=0, minute=0, second=0,
                                         microsecond=0) + timedelta(days=1)
    day_ds: list = []
    while day <= exit_:
        d = _asof_differential(reader, base_area, quote_area, day)
        if d is None:
            raise RuntimeError(
                "BLOCKED_DATA: financing day-start differential not evaluable for "
                f"{pair} at {day.isoformat()}; fail closed (never backfilled)")
        day_ds.append(d)
        day += timedelta(days=1)
    sign = 1.0 if decision["side"] > 0 else -1.0
    value = sign * float(decision["notional_usd"]) * math.fsum(day_ds) / 365.0
    return round(value, FINANCING_ROUND_DP)


# --------------------------------------------------------------------------
# the family API entry point
# --------------------------------------------------------------------------
def run_arm(arm: str, data_paths: dict, macro_reader, freeze_token=None) -> dict:
    """Runner contract entry point (see module docstring).  ``arm`` is one of
    ``anchor`` / ``neighbour`` / ``causal_negative_control`` (shorthand
    ``control`` accepted) or the runner-required ``benchmark_treatment``.
    ``freeze_token`` is accepted and ignored."""
    arm = ARM_ALIASES.get(arm, arm)
    if arm not in ARM_IDS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {sorted(ARM_IDS)}")
    if macro_reader is None:
        from research.assets.forex_free_v3.macro_reader import from_data_paths
        macro_reader = from_data_paths(data_paths)
    price_dir = (data_paths or {}).get("price_h1_dir")
    if not price_dir:
        raise RuntimeError("BLOCKED_DATA: data_paths is missing 'price_h1_dir'")

    all_decisions: list = []
    financing_events: list = []
    per_pair = {}
    skipped_decisions: list = []
    skipped_exits: list = []
    for pair in PAIRS:  # frozen universe order; deterministic accumulation
        h1 = load_pair_h1_bars(pair, price_dir)
        daily = daily_decision_bars(h1)
        states = pair_state_series(pair, daily, macro_reader, arm)
        sched = schedule_pair(pair, daily, states, arm)
        skipped_decisions.extend(sched["skipped_decisions"])
        skipped_exits.extend(sched["skipped_exits"])
        counters = sched["counters"]
        counters["n_round_trips"] = len(sched["decisions"])
        per_pair[pair] = counters
        for decision in sched["decisions"]:
            adjustment = financing_adjustment_usd(pair, decision, macro_reader)
            all_decisions.append(decision)
            financing_events.append({
                "decision_id": decision["decision_id"],
                "financing_adjustment_usd": adjustment,
                "formula": FINANCING_FORMULA,
            })

    all_decisions.sort(key=lambda d: (d["decision_ts"], d["pair"]))
    index = {d["decision_id"]: i for i, d in enumerate(all_decisions)}
    financing_events.sort(key=lambda ev: index[ev["decision_id"]])

    totals = {
        "n_daily_bars": sum(p["n_daily_bars"] for p in per_pair.values()),
        "n_evaluated_bars": sum(p["n_evaluated_bars"] for p in per_pair.values()),
        "n_void_bars": sum(p["n_void_bars"] for p in per_pair.values()),
        "n_go_bars": sum(p["n_go_bars"] for p in per_pair.values()),
        "n_no_go_bars": sum(p["n_no_go_bars"] for p in per_pair.values()),
        "n_entries": sum(p["n_entries"] for p in per_pair.values()),
        "n_fills": sum(p["n_fills"] for p in per_pair.values()),
        "n_round_trips": len(all_decisions),
        "n_skipped_entry_fills": sum(p["n_skipped_entry_fills"] for p in per_pair.values()),
        "n_skipped_exit_fills": sum(p["n_skipped_exit_fills"] for p in per_pair.values()),
        "n_force_flats": sum(p["n_force_flats"] for p in per_pair.values()),
        "n_entries_suppressed_by_boundary":
            sum(p["n_entries_suppressed_by_boundary"] for p in per_pair.values()),
    }
    meta = {
        "decision_clock": "daily",
        "proposal_id": PROPOSAL_ID,
        "family_id": "family1",
        "arm": arm,
        "arm_id": ARM_IDS[arm],
        "pair_universe": list(PAIRS),
        "warmup_daily_bars": DRIFT_BARS,
        # Incremental-alpha definition declared to the runner (V3-I finding
        # D1): the A5 proposal's FROZEN gate is the per-pair-day normalized
        # difference over the identical post-warmup schedule window
        # (a5_lane/proposal_1.json incremental_test.operationalization;
        # scored_runner.ALPHA_PER_PAIR_DAY_NORMALIZED).  The runner divides
        # the anchor and benchmark financing-adjusted sums by the pair-day
        # count of the window starting after this module's frozen warmup
        # (warmup_daily_bars above).
        "alpha_definition": "a5_per_pair_day_normalized_v1",
        "momentum_window_daily_bars": MOMENTUM_BARS,
        "neighbour_median_window_daily_bars": NEIGHBOUR_MEDIAN_BARS,
        "notional_usd_unit": NOTIONAL_USD,
        "financing_formula": FINANCING_FORMULA,
        "financing_disclosure": FINANCING_DISCLOSURE,
        "macro_access_note": (
            "policy rates read ONLY via macro_reader (availability-gated "
            "available_time_utc <= decision instant; percent-per-annum "
            "vintages converted to annualized decimals by /100 at one "
            "defined point); never a raw vintage file read"),
        "schedule": {"total": totals, "per_pair": per_pair},
        "skipped_decisions": skipped_decisions,
        "skipped_exits": skipped_exits,
    }
    if arm == BENCHMARK_ARM:
        meta["benchmark_treatment_note"] = (
            "the frozen v3_benchmark_treatment: unconditional 21-daily-bar "
            "momentum (LONG when m>0, SHORT when m<0, FLAT when m==0), "
            "identical clock/fills/holds/warmup/costs, ZERO macro reads in "
            "the state; financing still accrues per the frozen formula. "
            "Booked by the runner inside the scored anchor cell for the "
            "incremental-alpha gate.")
    return {"decisions": all_decisions, "financing_events": financing_events,
            "meta": meta}
