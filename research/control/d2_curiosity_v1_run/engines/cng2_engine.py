"""cng2_engine.py — CNG2-A5-P1 verbatim-construction engine (cycle D2-CURIOSITY-V1).

NON_GOVERNING_DIAGNOSTIC lane. REPLAY_NOT_PROSPECTIVE. This module builds
per-decision rows ONLY; it structurally REFUSES to compute aggregate
PnL/expectancy (``score_cells`` raises REFUSES_PRELAUNCH unless the
orchestrator sets ``ALLOW_SCORE = True`` at GO time — this lane never sets
it and there is no aggregate implementation in this lane at all).

FROZEN LAW (verbatim, no neighbours, no parameter search, no rescue):
  three_cell_contract.json cell CNG2-A5-P1
  cost_contract.json CNG2-A5-P1.pre_registered_constants_for_this_diagnostic
  sources/cng2_a5_p1_identity.json (construction + missing_data_law + arms)

Construction (identity extract, verbatim):
  press(S) = (SUM buy_quote - SUM sell_quote) / SUM quote_total over the
  three closed H1 bars B-4..B-2 = [S-4h, S-1h), where B is the boundary bar
  whose OPEN equals the funding settlement S on the 8h grid {00,08,16} UTC.
  d = sign(press); exact tie -> UNFUNDED_SKIP (counted). Decision at close
  of B-2 (S-1h); entry fill = last_price(B-2) at S-1h; exit fill =
  last_price(B) at S+1h; holds THROUGH settlement S. Transfer
  -d*rate(S) booked at S verbatim from the pulled settlement series
  (accounting only, never a direction input). Warmup: deepest family ref
  B-7 must lie inside the frozen panel bounds (bounds-based eligibility;
  the bound panels have zero empty hours, so bounds-based and
  presence-based eligibility coincide on the real data). Missing-data law
  fail-closed: UNMEASURED_BAR / BLOCKED_MISSING_BAR / UNFUNDED_SKIP /
  UNFUNDED_SKIP_NO_SETTLEMENT / BLOCKED_DATA — never imputed. Check order
  per decision follows source measure.py _mk_row lines 400-409: features,
  then fill bars, then exact tie.

Decision-set grid law: 8h grid {00,08,16} UTC, 1,094 eligible
instants/symbol on the real bound panels from 2025-08-22T08:00Z (the
2025-08-22T00:00Z instant is INELIGIBLE_WARMUP: B-7 falls before the panel
start); 3,282 pooled anchor decisions. On synthetic test panels the same
law applies and the analogous warmup instant is excluded by the same
B-7-in-bounds rule (no special-casing).

Costs: charged once per fill, 2 fills per funded decision (the settlement
transfer is a cash exchange, NOT a fill and never charged taker cost), at
the pre-registered frozen tier constants; rows book PRIMARY tier 2.0
(2 x (10 + 4) bps = 28 bps per funded decision); tier 1.0 (2 x (5 + 2) =
14 bps) is reported in decision-set metadata. Zero cost is forbidden.

Folds: NULL in source (frozen as one full-window pool; calendar thirds are
DESCRIPTIVE_ONLY reporting-layer splits, never engine splits, never fold
evidence). The engine emits ``folds: None`` and exposes no fold parameter.

PUBLIC API SURFACE (fixed, documented, introspection-enforced by the
golden tests — any other public module attribute is a violation):

PUBLIC_API = (
    "ALLOW_SCORE",
    "ARMS",
    "BLOCKED_DATA",
    "CELL_ID",
    "COST_TIERS",
    "DECISION_ROW_COLUMNS",
    "GRID_HOURS_UTC",
    "PRIMARY_TIER",
    "PUBLIC_API",
    "REFUSES_PRELAUNCH",
    "S1_ACCESS_DENIED",
    "UNIVERSE",
    "build_anchor_decisions",
    "build_ctl_fundlevel_decisions",
    "build_ctl_shiftboundminus2h_decisions",
    "load_funding_series",
    "load_panel",
    "score_cells",
)

There are NO tuning knobs: every construction constant below is a frozen
verbatim constant from the cited contracts/identity (bar offsets, grid,
universe, tier constants). ``ARMS`` and ``COST_TIERS`` are immutable
(mappingproxy). Builder signatures are exactly ``(panels, funding)``.
"""

import csv as _csv
import datetime as _dt
import hashlib as _hashlib
import json as _json
import math as _math
import re as _re
from pathlib import Path as _Path
from types import MappingProxyType as _MappingProxyType

import cells_registry as _cells_registry

# Exactly-three enforcement: the engine cannot even be imported unless the
# shared registry is exactly {SFNG2-A4-P1, FXNG3-A4-P1, CNG2-A5-P1}.
_cells_registry.assert_registry_intact()

__all__ = (
    "ALLOW_SCORE",
    "ARMS",
    "BLOCKED_DATA",
    "CELL_ID",
    "COST_TIERS",
    "DECISION_ROW_COLUMNS",
    "GRID_HOURS_UTC",
    "PRIMARY_TIER",
    "PUBLIC_API",
    "REFUSES_PRELAUNCH",
    "S1_ACCESS_DENIED",
    "UNIVERSE",
    "build_anchor_decisions",
    "build_ctl_fundlevel_decisions",
    "build_ctl_shiftboundminus2h_decisions",
    "load_funding_series",
    "load_panel",
    "score_cells",
)


# --------------------------------------------------------------------------
# Frozen identity constants (three_cell_contract.json cell CNG2-A5-P1)
# --------------------------------------------------------------------------

CELL_ID = "CNG2-A5-P1"
UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
GRID_HOURS_UTC = (0, 8, 16)  # 8h settlement grid {00,08,16} UTC

# Frozen eligibility window relative to the boundary bar B (open == S):
# deepest family ref B-7 (neighbour arm warmup) .. B+3 (family range).
_ELIGIBILITY_LO_OFFSET = -7
_ELIGIBILITY_HI_OFFSET = 3

_MS_PER_HOUR = 3_600_000
_SEC_PER_HOUR = 3_600

# Frozen arm rule table (identity extract arms_frozen_at_D1; offsets are
# bar positions relative to B, the bar whose open == the grid instant S).
# ANCHOR:    features B-4..B-2, entry close B-2 (S-1h), exit close B (S+1h),
#            transfer booked.
# SHAM:      whole rule shifted -2h off-grid (S' = S-2h): features
#            [S-6h, S-3h) = bars B-6..B-4, entry fill S-3h (close B-4),
#            exit fill S-1h (close B-2); every sham trade entirely BEFORE
#            the true boundary; NO transfer booked.
# FUNDLEVEL: d = -sign(rate(S)) (known-dead FUNDJUMP level form on the
#            anchor clock), identical grid/holds/transfer booking;
#            unpromotable by construction.
ARMS = _MappingProxyType({
    "CNG2-A5-P1-ANCHOR": _MappingProxyType({
        "feature_bar_offsets": (-4, -3, -2),
        "entry_bar_offset": -2,
        "exit_bar_offset": 0,
        "transfer_booked": True,
        "direction_rule": "PRESS_SIGN",
    }),
    "CNG2-A5-P1-CTL-SHIFTBOUNDMINUS2H": _MappingProxyType({
        "feature_bar_offsets": (-6, -5, -4),
        "entry_bar_offset": -4,
        "exit_bar_offset": -2,
        "transfer_booked": False,
        "direction_rule": "PRESS_SIGN",
    }),
    "CNG2-A5-P1-CTL-FUNDLEVEL": _MappingProxyType({
        "feature_bar_offsets": None,
        "entry_bar_offset": -2,
        "exit_bar_offset": 0,
        "transfer_booked": True,
        "direction_rule": "FUNDLEVEL_NEG_SIGN",
    }),
})

# Pre-registered tier constants (cost_contract.json CNG2-A5-P1
# .pre_registered_constants_for_this_diagnostic; frozen BEFORE any outcome,
# never tuned). Charged once per fill; 2 fills per funded decision.
# Tier 2.0 is PRIMARY for this cell (source-cycle law).
COST_TIERS = _MappingProxyType({
    "1.0": _MappingProxyType({"taker_bps_per_fill": 5.0, "spread_bps_per_fill": 2.0}),
    "2.0": _MappingProxyType({"taker_bps_per_fill": 10.0, "spread_bps_per_fill": 4.0}),
})
PRIMARY_TIER = "2.0"

DECISION_ROW_COLUMNS = (
    "symbol", "S", "press", "d", "entry", "exit", "rate",
    "gross_before_costs", "transfer", "costs", "net", "status",
)

# The fixed public API surface (introspection-enforced by the golden tests).
# Sorted tuple; see the module docstring for the documented rationale.
PUBLIC_API = (
    "ALLOW_SCORE",
    "ARMS",
    "BLOCKED_DATA",
    "CELL_ID",
    "COST_TIERS",
    "DECISION_ROW_COLUMNS",
    "GRID_HOURS_UTC",
    "PRIMARY_TIER",
    "PUBLIC_API",
    "REFUSES_PRELAUNCH",
    "S1_ACCESS_DENIED",
    "UNIVERSE",
    "build_anchor_decisions",
    "build_ctl_fundlevel_decisions",
    "build_ctl_shiftboundminus2h_decisions",
    "load_funding_series",
    "load_panel",
    "score_cells",
)

_DECISION_SET_SCHEMA = "cng2_engine_decision_set@1"
_LABEL = (
    "NON_GOVERNING_DIAGNOSTIC REPLAY_NOT_PROSPECTIVE — per-decision rows "
    "only; no aggregate PnL/expectancy is computed by this engine "
    "(score_cells refuses prelaunch)"
)
_FOLDS_NOTE = (
    "FOLDS_NULL_ONE_POOL: no folds in source (pre-scoring D2 kill); one "
    "full-window pool; calendar thirds are DESCRIPTIVE_ONLY reporting-layer "
    "splits and are never computed by the engine"
)


# --------------------------------------------------------------------------
# Fail-closed exception types
# --------------------------------------------------------------------------

class REFUSES_PRELAUNCH(RuntimeError):
    """Aggregate outcome computation attempted before orchestrator GO."""


class S1_ACCESS_DENIED(PermissionError):
    """Any path touching '/S1/' or 's1_' data roots is denied (S1 SEALED)."""


class BLOCKED_DATA(RuntimeError):
    """Funding/pull data failure: transfers are never assumed zero and the
    series is never fabricated (fail-closed)."""


# Module-level GO flag. ONLY the orchestrator may set cng2_engine.ALLOW_SCORE
# = True at GO time. This implementation lane never sets it.
ALLOW_SCORE = False


def score_cells(*args, **kwargs):
    """REFUSES to compute aggregate PnL/expectancy in this lane.

    Raises REFUSES_PRELAUNCH unless the orchestrator has set the module-level
    ALLOW_SCORE flag at GO time. Even with the flag set, this lane provides
    no aggregate implementation (NotImplementedError): scoring belongs to the
    orchestrator's single atomic E-phase job, never to an implementation lane.
    """
    if not ALLOW_SCORE:
        raise REFUSES_PRELAUNCH(
            "REFUSES_PRELAUNCH: aggregate PnL/expectancy computation is "
            "locked in the implementation lane; cng2_engine builds "
            "per-decision rows only. ALLOW_SCORE may be set only by the "
            "orchestrator at GO time (cycle D2-CURIOSITY-V1, "
            "NON_GOVERNING_DIAGNOSTIC)."
        )
    raise NotImplementedError(
        "score_cells has no implementation in the implementation lane; "
        "aggregate scoring runs only in the orchestrator's atomic E-phase job."
    )


# --------------------------------------------------------------------------
# S1 denial + digest helpers
# --------------------------------------------------------------------------

def _deny_s1(path):
    """Raise S1_ACCESS_DENIED for any path containing '/S1/' or 's1_'."""
    s = str(path).lower()
    if "/s1/" in s or "s1_" in s:
        raise S1_ACCESS_DENIED(
            "S1_ACCESS_DENIED: path %r touches a sealed S1 data root; S1 is "
            "SEALED_UNTOUCHED for every asset in cycle D2-CURIOSITY-V1 "
            "(plans/PLAN_d2_curiosity_v1.md section 0)" % (str(path),)
        )


def _verify_digest(data, expected_sha256, path):
    observed = _hashlib.sha256(data).hexdigest()
    if observed != str(expected_sha256).lower():
        raise ValueError(
            "DIGEST_MISMATCH for %r: expected %s, observed %s (fail-closed)"
            % (str(path), expected_sha256, observed)
        )


# --------------------------------------------------------------------------
# Loaders (panels + funding settlement series)
# --------------------------------------------------------------------------

_HOUR_KEY_RE = _re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}$")
_REQUIRED_PANEL_COLUMNS = ("symbol", "hour_utc", "buy_quote", "sell_quote",
                           "quote_total", "last_price")


def load_panel(path, expected_sha256=None):
    """Load a frozen S4-style H1 panel CSV into {symbol: {hour_key: bar}}.

    hour_key format 'YYYY-MM-DDTHH' is the bar OPEN hour (bar covers
    [T, T+1h)). Fail-closed: unknown symbol, duplicate (symbol, hour) rows,
    malformed keys and non-numeric cells raise. last_price validity
    (finite, > 0) is a per-decision law (BLOCKED_MISSING_BAR), not a
    whole-file law, so it is enforced at decision time. S1 denial runs
    before any file access. Optional digest pin verification.
    """
    _deny_s1(path)
    data = _Path(path).read_bytes()
    if expected_sha256 is not None:
        _verify_digest(data, expected_sha256, path)
    reader = _csv.DictReader(data.decode("utf-8").splitlines())
    if reader.fieldnames is None or not set(_REQUIRED_PANEL_COLUMNS).issubset(set(reader.fieldnames)):
        raise ValueError(
            "panel %r missing required columns %s (have %s)"
            % (str(path), list(_REQUIRED_PANEL_COLUMNS), reader.fieldnames)
        )
    panels = {}
    seen = set()
    for row in reader:
        sym = row["symbol"]
        if sym not in UNIVERSE:
            raise ValueError(
                "non-universe symbol %r in panel %r; universe is frozen %s"
                % (sym, str(path), list(UNIVERSE))
            )
        hk = row["hour_utc"]
        if not _HOUR_KEY_RE.match(hk or ""):
            raise ValueError("malformed hour_utc %r in panel %r" % (hk, str(path)))
        key = (sym, hk)
        if key in seen:
            raise ValueError("duplicate panel row %s in %r (fail-closed)" % (key, str(path)))
        seen.add(key)
        panels.setdefault(sym, {})[hk] = {
            "buy_quote": float(row["buy_quote"]),
            "sell_quote": float(row["sell_quote"]),
            "quote_total": float(row["quote_total"]),
            "last_price": float(row["last_price"]),
        }
    if not panels:
        raise ValueError("panel %r is empty (fail-closed)" % (str(path),))
    return panels


def load_funding_series(path, expected_sha256=None):
    """Load + grid-fold the pulled funding settlement series.

    Returns {symbol: {"rates": {epoch_hour: rate}, "incidents": [...]}}.
    Grid fold: fundingTime (ms) floored to the hour (absorbs the observed
    +1..10 ms boundary jitter of the pinned pull); only hours on the frozen
    mod-8h grid {00,08,16} UTC become evidence. Off-grid rows are recorded
    as clock-defect incidents and are NEVER folded into evidence (re-clocking
    after evidence = rescue). Duplicated grid hours and non-increasing
    timestamps are recorded as incidents. Empty/missing series for a symbol
    raises BLOCKED_DATA — transfers are never assumed zero and the series is
    never fabricated. S1 denial runs before any file access.
    """
    _deny_s1(path)
    data = _Path(path).read_bytes()
    if expected_sha256 is not None:
        _verify_digest(data, expected_sha256, path)
    raw = _json.loads(data)
    if not isinstance(raw, dict) or not raw:
        raise BLOCKED_DATA(
            "funding history %r is empty or malformed: BLOCKED_DATA (the "
            "settlement series is never fabricated)" % (str(path),)
        )
    out = {}
    for sym, rows in raw.items():
        if sym not in UNIVERSE:
            raise ValueError(
                "non-universe symbol %r in funding series %r; universe is "
                "frozen %s" % (sym, str(path), list(UNIVERSE))
            )
        if not isinstance(rows, list) or not rows:
            raise BLOCKED_DATA(
                "funding series for %s is empty: BLOCKED_DATA (transfers are "
                "never assumed zero, series never fabricated)" % (sym,)
            )
        rates = {}
        incidents = []
        last_ts = None
        for r in rows:
            ts = int(r["fundingTime"])
            rate = float(r["fundingRate"])
            if last_ts is not None and ts < last_ts:
                incidents.append(
                    {"type": "NON_INCREASING_TIMESTAMPS", "funding_time_ms": ts}
                )
            last_ts = ts
            hour = ts // _MS_PER_HOUR
            if hour % 8 != 0:
                incidents.append(
                    {"type": "OFF_GRID_CLOCK_DEFECT",
                     "funding_time_ms": ts, "folded_hour": _iso_s(hour)}
                )
                continue
            if hour in rates:
                incidents.append(
                    {"type": "DUPLICATE_GRID_HOUR", "hour": _iso_s(hour)}
                )
                continue
            rates[hour] = rate
        out[sym] = {"rates": rates, "incidents": incidents}
    return out


# --------------------------------------------------------------------------
# Decision-set builders (same engine, frozen per-arm rules)
# --------------------------------------------------------------------------

def build_anchor_decisions(panels, funding):
    """CNG2-A5-P1-ANCHOR: d=sign(press B-4..B-2), entry close B-2,
    exit close B, settlement transfer booked."""
    return _build_arm("CNG2-A5-P1-ANCHOR", panels, funding)


def build_ctl_shiftboundminus2h_decisions(panels, funding):
    """CNG2-A5-P1-CTL-SHIFTBOUNDMINUS2H sham: whole rule shifted -2h
    off-grid; features [S-6h, S-3h); entry fill S-3h; exit fill S-1h;
    entirely before the true boundary; NO transfer booked."""
    return _build_arm("CNG2-A5-P1-CTL-SHIFTBOUNDMINUS2H", panels, funding)


def build_ctl_fundlevel_decisions(panels, funding):
    """CNG2-A5-P1-CTL-FUNDLEVEL: d=-sign(rate(S)) on the anchor clock,
    identical grid/holds/transfer booking; unpromotable by construction."""
    return _build_arm("CNG2-A5-P1-CTL-FUNDLEVEL", panels, funding)


# --------------------------------------------------------------------------
# Internals (private)
# --------------------------------------------------------------------------

def _iso_s(hour):
    return _dt.datetime.fromtimestamp(hour * _SEC_PER_HOUR, _dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:00:00Z"
    )


def _hour_key_to_int(hour_key):
    dt = _dt.datetime.strptime(hour_key, "%Y-%m-%dT%H").replace(tzinfo=_dt.timezone.utc)
    return int(dt.timestamp()) // _SEC_PER_HOUR


def _int_to_hour_key(hour):
    return _dt.datetime.fromtimestamp(hour * _SEC_PER_HOUR, _dt.timezone.utc).strftime(
        "%Y-%m-%dT%H"
    )


def _index_panel(sym, bars_by_key):
    hours = {}
    lo = None
    hi = None
    for hk, bar in bars_by_key.items():
        h = _hour_key_to_int(hk)
        if h in hours:
            raise ValueError("duplicate panel hour %s for %s (fail-closed)" % (hk, sym))
        hours[h] = bar
        lo = h if lo is None else min(lo, h)
        hi = h if hi is None else max(hi, h)
    return hours, lo, hi


def _eligible_grid_hours(hours, lo, hi):
    """Frozen decision grid: 8h-grid instants whose family bar range
    B-7..B+3 lies inside the frozen panel bounds. The first in-panel grid
    instant is excluded by the same rule (INELIGIBLE_WARMUP: its B-7 falls
    before the panel start) — no special-casing, no outcome-driven drops.
    Bounds-based (the bound panels have zero empty hours; on real data this
    yields exactly 1,094 instants/symbol from 2025-08-22T08:00Z)."""
    out = []
    h = lo + ((-lo) % 8)  # first on-grid hour >= lo (UTC epoch hours: h%8==0 <=> {00,08,16} UTC)
    while h <= hi:
        if h + _ELIGIBILITY_LO_OFFSET >= lo and h + _ELIGIBILITY_HI_OFFSET <= hi:
            out.append(h)
        h += 8
    return out


def _sign(x):
    if x > 0.0:
        return 1
    if x < 0.0:
        return -1
    return 0


def _costs_per_funded():
    tier = COST_TIERS[PRIMARY_TIER]
    return 2.0 * (tier["taker_bps_per_fill"] + tier["spread_bps_per_fill"]) / 10000.0


def _decide(sym, s_hour, arm, bars, rates, counts):
    row = {col: None for col in DECISION_ROW_COLUMNS}
    row["symbol"] = sym
    row["S"] = _iso_s(s_hour)

    def finish(status):
        counts[status] += 1
        row["status"] = status
        return row

    # (1) Settlement evidence gate (identity missing_data_law: unevidenced
    # settlement instant -> UNFUNDED_SKIP_NO_SETTLEMENT, counted, never
    # silently dropped; transfers never assumed zero).
    if s_hour not in rates:
        return finish("UNFUNDED_SKIP_NO_SETTLEMENT")
    rate = rates[s_hour]

    # (2) Features -> press (source measure.py _mk_row lines 400-402).
    press = None
    rule = arm["direction_rule"]
    if rule == "PRESS_SIGN":
        num = 0.0
        den = 0.0
        for off in arm["feature_bar_offsets"]:
            bar = bars.get(s_hour + off)
            if bar is None:
                return finish("UNMEASURED_BAR")
            bq = bar["buy_quote"]
            sq = bar["sell_quote"]
            qt = bar["quote_total"]
            if not (_math.isfinite(bq) and _math.isfinite(sq) and _math.isfinite(qt)):
                return finish("UNMEASURED_BAR")
            num += bq - sq
            den += qt
        if not _math.isfinite(num) or not _math.isfinite(den) or den == 0.0:
            return finish("UNMEASURED_BAR")
        press = num / den
        row["press"] = press
        d = _sign(press)
    elif rule == "FUNDLEVEL_NEG_SIGN":
        d = -_sign(rate)
    else:  # pragma: no cover — frozen table only contains the two rules
        raise BLOCKED_DATA("unknown frozen direction rule %r" % (rule,))
    row["d"] = d

    # (3) Fill bars (source lines 403-406: last_price must be finite and > 0).
    entry_bar = bars.get(s_hour + arm["entry_bar_offset"])
    exit_bar = bars.get(s_hour + arm["exit_bar_offset"])
    entry = entry_bar["last_price"] if entry_bar is not None else None
    exitp = exit_bar["last_price"] if exit_bar is not None else None
    if entry is None or not (_math.isfinite(entry) and entry > 0.0):
        return finish("BLOCKED_MISSING_BAR")
    if exitp is None or not (_math.isfinite(exitp) and exitp > 0.0):
        return finish("BLOCKED_MISSING_BAR")

    # (4) Exact tie (source lines 407-409): numerator exactly 0 -> d=0 ->
    # UNFUNDED_SKIP, counted; sign is the only operator, no thresholds.
    if d == 0:
        return finish("UNFUNDED_SKIP")

    # (5) Funded decision: fills + verbatim transfer + frozen cost debit.
    transfer = -d * rate if arm["transfer_booked"] else None
    costs = _costs_per_funded()
    gross = d * (exitp / entry - 1.0)
    net = gross - costs if transfer is None else gross + transfer - costs
    row["entry"] = entry
    row["exit"] = exitp
    row["rate"] = rate
    row["gross_before_costs"] = gross
    row["transfer"] = transfer
    row["costs"] = costs
    row["net"] = net
    return finish("FUNDED")


def _build_arm(arm_id, panels, funding):
    if arm_id not in ARMS:
        raise ValueError("unknown arm %r; frozen arms are %s" % (arm_id, sorted(ARMS)))
    arm = ARMS[arm_id]
    if not isinstance(panels, dict) or not panels:
        raise ValueError("panels must be a non-empty dict {symbol: {hour_key: bar}}")
    unknown_syms = sorted(set(panels) - set(UNIVERSE))
    if unknown_syms:
        raise ValueError(
            "panels contain non-universe symbols %s; universe is frozen %s"
            % (unknown_syms, list(UNIVERSE))
        )

    rates_by_sym = {}
    incidents = []
    for sym in sorted(panels):
        fseries = funding.get(sym) if isinstance(funding, dict) else None
        if not fseries or not fseries.get("rates"):
            raise BLOCKED_DATA(
                "funding series missing/empty for %s: BLOCKED_DATA (transfers "
                "are never assumed zero, series never fabricated)" % (sym,)
            )
        rates_by_sym[sym] = fseries["rates"]
        for inc in fseries.get("incidents", ()):
            incidents.append({"symbol": sym, **inc})

    rows = []
    counts = {
        "FUNDED": 0,
        "UNFUNDED_SKIP": 0,
        "UNMEASURED_BAR": 0,
        "BLOCKED_MISSING_BAR": 0,
        "UNFUNDED_SKIP_NO_SETTLEMENT": 0,
    }
    # Symbol-major chronological order (representation identity: pooled
    # 3-symbol book, no cross-sectional ranking or normalization).
    for sym in UNIVERSE:
        if sym not in panels:
            continue
        bars, lo, hi = _index_panel(sym, panels[sym])
        for s_hour in _eligible_grid_hours(bars, lo, hi):
            rows.append(_decide(sym, s_hour, arm, bars, rates_by_sym[sym], counts))

    return {
        "schema": _DECISION_SET_SCHEMA,
        "cell_id": CELL_ID,
        "arm_id": arm_id,
        "label": _LABEL,
        "universe": list(UNIVERSE),
        "grid_hours_utc": list(GRID_HOURS_UTC),
        "eligibility_law": (
            "every 8h-grid instant whose family bar range B-7..B+3 lies "
            "inside the frozen panel bounds AND whose settlement instant is "
            "evidenced by the pulled settlement series (unevidenced -> "
            "UNFUNDED_SKIP_NO_SETTLEMENT, counted)"
        ),
        "arm_rule": dict(arm),
        "cost_tier": PRIMARY_TIER,
        "cost_tiers_bps_per_funded_decision": {
            "1.0": 2.0 * (COST_TIERS["1.0"]["taker_bps_per_fill"]
                          + COST_TIERS["1.0"]["spread_bps_per_fill"]),
            "2.0": 2.0 * (COST_TIERS["2.0"]["taker_bps_per_fill"]
                          + COST_TIERS["2.0"]["spread_bps_per_fill"]),
        },
        "folds": None,
        "folds_note": _FOLDS_NOTE,
        "clock_defect_incidents": incidents,
        "counts": counts,
        "rows": rows,
    }
