"""RATES-NG1 I-phase family runner: the frozen decision rule.

Cycle RATES-NG1, task rates-ng1-i-implementation.  Implements the S
selection freeze VERBATIM (research/control/rates_ng1_run/
s/selection_freeze.json, BINDING):

- Family RATESNG1-A5-P1: curvature-gated slope dynamics on the
  level-orthogonalized official par curve.  Decomposition:
  slope = 30 Yr - 2 Yr; curvature = 2 Yr - 2 x 10 Yr + 30 Yr;
  level coordinate = 10 Yr (the coordinate REMOVED before any state).
- Orthogonalization: PIT-expanding OLS (with intercept) of each shape
  coordinate on the level coordinate, fitted ONLY on strictly-past
  defined pairs; min_past_points = 63; instants before the first legal
  fit are UNDEFINED (None), never inferred (Q-11).  The algorithm is
  instance-for-instance the D2 screened machinery
  (d2_states.proposal_state_a5_p1); the I tests pin exact parity on
  synthetic fixtures.
- Gate variants (the ONLY config field that differs across the 3 arms):
  NEUTRAL      = double-median double-sort (D2 frozen defaults verbatim);
  CONSERVATIVE = symmetric outer-quartile cuts (0.75 / 0.25);
  AGGRESSIVE   = single-coordinate OR gate (median cuts).
  Cuts are sample quantiles (linear interpolation on the sorted
  state-input series, cost_model.percentile convention) of the
  orthogonalized coordinate series over the bookable instants only.
- Sign convention (frozen): state +1 => LONG front leg (SHY) / SHORT
  long leg (TLT); -1 => reverse; 0 => flat.  Tenor-bracket law
  (frozen by proximity, never by performance): 2 Yr -> SHY (1-3 Yr
  track), 30 Yr -> TLT (20+ Yr track).
- Entry clock: 16:00 America/New_York close of each bookable decision
  session (clock.ny_close_utc); state input read ONLY at the instant's
  readable_bar_date (V7 close+1 law, materialized in p2_grid_census).
- Exit law: force-flat after holding_trading_days = 5 common-grid
  sessions; overlapping state changes resolve LAST-WRITE-WINS;
  force-flat at fold ends (frozen equal-thirds folds).
- Cost treatment (frozen tier 2.0, identical for every arm and every
  battery control): CS p90 per-leg stress tier charged ONCE per fill on
  BOTH legs (entry + exit fills), plus ACT/365F expense drag over the
  frozen holding convention (5 trading days ~= 7 calendar days,
  feasibility.HOLDING_CALENDAR_DAYS_CHARGED).
- Kernel booking: the P1 dual-book kernel (kernel.DualBookLedger) is
  used verbatim and long-only.  A SHORT leg orientation is booked as a
  mirror LONG round trip (BUY entry / SELL exit at TRUE prices and TRUE
  quantities; costs charged once per fill identically) with the
  runner-level sign applied by ``round_trip_leg_signed_pnl`` --
  disclosed representation, no kernel math is forked.  Every leg book
  carries the dual-book equality proof.

NO outcome numbers on real substrate are computed here (I-phase law).
Emitted decision series and structural book views carry NO after-cost
outcome fields.  The E-phase signed arithmetic surface
(``round_trip_leg_signed_pnl``) exists but is exercised only on
synthetic fixtures in I.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any, Mapping, Sequence

from research.assets.rates_ng1 import clock as ck
from research.assets.rates_ng1 import plane_adapter as pa
from research.assets.rates_ng1.cost_model import percentile
from research.assets.rates_ng1.kernel import DualBookLedger

SCHEMA = "rates_ng1/runners/runner@1"

# ------------------------------------------------------------------ #
# Frozen constants (S selection freeze; pinned by tests against the    #
# committed artifact bytes -- drift here is a test failure).           #
# ------------------------------------------------------------------ #

FAMILY_ID = "RATESNG1-A5-P1"

#: Frozen leg pair (section_2.shared_arm_law.leg_pair_freeze).
LEG_PAIR = {"front_leg": "SHY", "long_leg": "TLT"}

#: Frozen tenor-bracket mapping (leg_pair_freeze law: 2 Yr -> SHY
#: 1-3 Yr track, 30 Yr -> TLT 20+ Yr track; IEF/IEI unmapped reserves).
TENOR_BRACKET_MAPPING = {"2 Yr": "SHY", "30 Yr": "TLT"}

SLOPE_TENORS = ("30 Yr", "2 Yr")
CURVATURE_TENORS = ("2 Yr", "10 Yr", "30 Yr")
LEVEL_TENOR = "10 Yr"
MIN_PAST_POINTS = 63
HOLDING_TRADING_DAYS = 5

#: Frozen drag convention (feasibility.HOLDING_CALENDAR_DAYS_CHARGED).
HOLDING_CALENDAR_DAYS_CHARGED = 7

#: Frozen placebo misalignment (section_6: k := one holding period).
K_MISALIGN_SESSIONS = 5

#: One pair unit = this USD notional PER LEG at entry (fill quantity is
#: derived from the RAW close at the fill session; disclosed constant).
NOTIONAL_PER_LEG_USD = 10_000.0

#: Frozen equal-thirds folds (R3): the 2804-day bookable window split
#: by equal calendar-day thirds; force-flat at fold ends.
FOLD_WINDOWS = (
    ("2019-01-07", "2021-07-28"),
    ("2021-07-29", "2024-02-18"),
    ("2024-02-19", "2026-09-11"),
)

GATE_RULES = frozenset({
    "both_above_plus1_both_below_minus1_else_zero",
    "both_above_upper_q_plus1_both_below_lower_q_minus1_else_zero",
    "either_above_plus1_either_below_minus1_else_zero",
})

EXIT_REASONS = ("holding", "overwritten", "fold_end", "window_end")


class RunnerLawError(Exception):
    """Fail-closed runner construction/execution error."""


def canonical_digest(cfg: Any) -> str:
    """arm_config_digest law (freeze section_2): sha256 of the canonical
    JSON serialization (sort_keys, compact separators)."""
    blob = json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


# ------------------------------------------------------------------ #
# Cell-config assembly (structural plumbing: digest assembly of the 3  #
# frozen cell configs, verified against the committed freeze).         #
# ------------------------------------------------------------------ #

def assemble_cell_configs(freeze: Mapping[str, Any]) -> list[dict]:
    """Assemble the 3 frozen cell configs from the committed freeze and
    verify each arm_config_digest (fail-closed on any drift).  No
    measurement happens here: digest assembly is structural plumbing."""
    plan = freeze.get("section_2_arm_configuration_plan")
    if not isinstance(plan, dict):
        raise RunnerLawError("freeze lacks section_2_arm_configuration_plan")
    arms = plan.get("arms")
    if not isinstance(arms, list) or len(arms) != 3:
        raise RunnerLawError("freeze must carry exactly 3 arms")
    battery = freeze.get("section_6_control_battery_binding", {})
    cells: list[dict] = []
    for arm in arms:
        cfg = arm["config"]
        digest = canonical_digest(cfg)
        if digest != arm["arm_config_digest"]:
            raise RunnerLawError(
                f"arm_config_digest drift for {arm['arm_id']}: recomputed "
                f"{digest} != frozen {arm['arm_config_digest']}")
        cells.append({
            "cell_id": f"{FAMILY_ID}:{arm['arm_id']}",
            "family_id": FAMILY_ID,
            "arm_id": arm["arm_id"],
            "role": arm["role"],
            "config": cfg,
            "arm_config_digest": digest,
            "cost_treatment_citation": {
                "contract_path":
                    freeze["section_4_cost_contract_binding"]["contract"][
                        "path"],
                "cost_ladder_tier":
                    freeze["section_4_cost_contract_binding"][
                        "cost_ladder_tier"],
                "cost_frequency":
                    freeze["section_4_cost_contract_binding"][
                        "cost_frequency"],
                "both_legs_charged":
                    freeze["section_4_cost_contract_binding"][
                        "both_legs_charged"],
            },
            "k_misalign_sessions": battery.get("k_misalign_sessions",
                                               K_MISALIGN_SESSIONS),
        })
    digests = {c["arm_config_digest"] for c in cells}
    if len(digests) != 3:
        raise RunnerLawError("arm_config_digests must be pairwise distinct")
    return cells


# ------------------------------------------------------------------ #
# State machinery (identical algorithm to the D2 screened form).       #
# ------------------------------------------------------------------ #

def curve_coordinates(
        curve_by_date: Mapping[str, Mapping[str, float]],
        instants: Sequence[Mapping[str, Any]],
        config: Mapping[str, Any] | None = None) -> dict[str, list]:
    """slope / curvature / level coordinate per bookable instant, read
    ONLY at the instant's readable_bar_date (V7 close+1 law).  Missing
    tenor values at the readable bar are UNDEFINED (None), never
    inferred."""
    dec = (config or {}).get("decomposition", {})
    slope_tenors = tuple(dec.get("slope_tenors", SLOPE_TENORS))
    level_tenor = dec.get("level_tenor", LEVEL_TENOR)
    if slope_tenors != SLOPE_TENORS or level_tenor != LEVEL_TENOR:
        raise RunnerLawError(
            "decomposition basis drift against the frozen law: refused")

    def val(d: str, tenor: str) -> float | None:
        raw = curve_by_date.get(d, {}).get(tenor)
        return None if raw is None else float(raw)

    slope: list[float | None] = []
    curv: list[float | None] = []
    level: list[float | None] = []
    for inst in instants:
        b = str(inst["readable_bar_date"])
        y2 = val(b, "2 Yr")
        y10 = val(b, "10 Yr")
        y30 = val(b, "30 Yr")
        if None in (y2, y10, y30):
            slope.append(None)
            curv.append(None)
            level.append(None)
            continue
        slope.append(y30 - y2)               # long_end_minus_front_end
        curv.append(y2 - 2.0 * y10 + y30)    # front - 2 x belly + long
        level.append(y10)
    return {"slope": slope, "curvature": curv, "level": level}


def ols_residual_on_level(y: Sequence[float | None],
                          x: Sequence[float | None],
                          min_past: int) -> list[float | None]:
    """PIT-expanding OLS-with-intercept residual of ``y`` on ``x``.

    Instance-for-instance the D2 screened algorithm
    (d2_states._ols_residual_series): at instant i the coefficients are
    fitted on the strictly-past DEFINED pairs accumulated so far (pairs
    accumulate from the first defined instant, including pre-fit
    instants); the residual at i uses those coefficients and the pair at
    i is appended afterwards.  Instants before the first legal fit (or
    with a degenerate zero-variance design) are None.  Parity with the
    D2 module is pinned by the I tests on synthetic fixtures."""
    if len(y) != len(x):
        raise RunnerLawError("residual series length mismatch")
    out: list[float | None] = []
    sx: list[float] = []
    sy: list[float] = []
    for i in range(len(y)):
        if len(sx) >= min_past:
            mx = sum(sx) / len(sx)
            my = sum(sy) / len(sy)
            sxx = sum((a - mx) ** 2 for a in sx)
            sxy = sum((a - mx) * (b - my) for a, b in zip(sx, sy))
            if sxx > 0.0:
                beta = sxy / sxx
                alpha = my - beta * mx
                if y[i] is not None and x[i] is not None:
                    out.append(float(y[i]) - (alpha + beta * float(x[i])))
                    sx.append(float(x[i]))
                    sy.append(float(y[i]))
                else:
                    out.append(None)
                continue
        if y[i] is not None and x[i] is not None:
            sx.append(float(x[i]))
            sy.append(float(y[i]))
        out.append(None)
    return out


def quantile_cut(values: Sequence[float], q: float) -> float:
    """Sample quantile with linear interpolation on the sorted
    state-input series (frozen quantile_method; cost_model.percentile
    convention)."""
    if not values:
        raise RunnerLawError("quantile cut of empty series is undefined")
    return percentile(list(values), q)


def gate_state_series(coord_a: Sequence[float | None],
                      coord_b: Sequence[float | None],
                      gate_cfg: Mapping[str, Any]) -> list[float | None]:
    """Gate state series from the two orthogonalized shape coordinates.

    Implements the 3 frozen state_rule strings verbatim; any other rule
    string is refused (fail-closed).  Cuts are sample quantiles of the
    DEFINED state-input values over the bookable instants only.  Q-11:
    an instant with either coordinate UNDEFINED carries state None --
    dropped from denominators downstream, never inferred as zero."""
    rule = str(gate_cfg.get("state_rule", ""))
    if rule not in GATE_RULES:
        raise RunnerLawError(f"unknown frozen state_rule {rule!r}: refused")
    upper_q = float(gate_cfg.get("upper_quantile", 0.5))
    lower_q = float(gate_cfg.get("lower_quantile", 0.5))
    defined_a = [v for v in coord_a if v is not None]
    defined_b = [v for v in coord_b if v is not None]
    if not defined_a or not defined_b:
        return [None] * len(coord_a)
    cut_a_hi = quantile_cut(defined_a, upper_q)
    cut_b_hi = quantile_cut(defined_b, upper_q)
    cut_a_lo = quantile_cut(defined_a, lower_q)
    cut_b_lo = quantile_cut(defined_b, lower_q)
    out: list[float | None] = []
    for a, b in zip(coord_a, coord_b):
        if a is None or b is None:
            out.append(None)
            continue
        if rule == "either_above_plus1_either_below_minus1_else_zero":
            if a > cut_a_hi or b > cut_b_hi:
                out.append(1.0)
            elif a < cut_a_lo or b < cut_b_lo:
                out.append(-1.0)
            else:
                out.append(0.0)
        else:  # both_above... (AND family: median or outer-quartile cuts)
            if a > cut_a_hi and b > cut_b_hi:
                out.append(1.0)
            elif a < cut_a_lo and b < cut_b_lo:
                out.append(-1.0)
            else:
                out.append(0.0)
    return out


def arm_state_series(config: Mapping[str, Any],
                     curve_by_date: Mapping[str, Mapping[str, float]],
                     instants: Sequence[Mapping[str, Any]]
                     ) -> list[float | None]:
    """The frozen arm state series for ONE gate-variant config."""
    coords = curve_coordinates(curve_by_date, instants, config)
    min_past = int(config.get("orthogonalization", {}).get(
        "min_past_points", MIN_PAST_POINTS))
    res_s = ols_residual_on_level(coords["slope"], coords["level"], min_past)
    res_c = ols_residual_on_level(coords["curvature"], coords["level"],
                                  min_past)
    return gate_state_series(res_s, res_c, config.get("gate", {}))


# ------------------------------------------------------------------ #
# Battery-control state machinery (battery.py holds the comparators).  #
# ------------------------------------------------------------------ #

def level_control_state(level: Sequence[float | None]) -> list[float | None]:
    """MANDATORY level-vs-shape decomposition control state: the LEVEL
    coordinate (10 Yr) traded on the identical grid with the identical
    leg-pair machinery, sign convention and cost treatment.  A single
    coordinate makes the AND-gate degenerate to the sample-median sign
    state (in-family: the AGGRESSIVE arm's single-coordinate law); cut
    = sample median of the defined level values over the bookable
    instants (the arms' cut_series_law)."""
    defined = [v for v in level if v is not None]
    if not defined:
        return [None] * len(level)
    cut = quantile_cut(defined, 0.5)
    out: list[float | None] = []
    for v in level:
        if v is None:
            out.append(None)
        elif v > cut:
            out.append(1.0)
        elif v < cut:
            out.append(-1.0)
        else:
            out.append(0.0)
    return out


def clock_only_state(instants: Sequence[Mapping[str, Any]]) -> list[float]:
    """CLOCK_ONLY_SHADOW state: pure session-of-week clock with NO curve
    input -- the D2 frozen generic_dow_tue form verbatim (+1 on Tuesday
    decision sessions, 0 otherwise)."""
    out: list[float] = []
    for inst in instants:
        d = dt.date.fromisoformat(str(inst["decision_session"]))
        out.append(1.0 if d.weekday() == 1 else 0.0)
    return out


def misaligned_state(state: Sequence[float | None],
                     k: int = K_MISALIGN_SESSIONS) -> list[float | None]:
    """PLACEBO state: the identical shape state with a FIXED k-session
    misalignment between state session and decision session (k = 5 :=
    one frozen holding period, frozen in the freeze's section 6; never
    tuned).  state_placebo[i] = state[i - k]; the head k instants are
    UNDEFINED (None, Q-11), never inferred as zero."""
    if k <= 0:
        raise RunnerLawError("placebo misalignment k must be positive")
    return [None] * k + [state[i - k] for i in range(k, len(state))]


# ------------------------------------------------------------------ #
# Folds (frozen equal-thirds law).                                     #
# ------------------------------------------------------------------ #

def fold_bounds() -> tuple[tuple[str, str], ...]:
    """The frozen equal-thirds fold windows (R3), verbatim."""
    return FOLD_WINDOWS


def fold_of_session(session_iso: str) -> int:
    """Fold index (1-based) of a decision session under the frozen
    equal-thirds windows; a session outside all folds is fail-closed."""
    d = str(session_iso)
    for i, (lo, hi) in enumerate(FOLD_WINDOWS, start=1):
        if lo <= d <= hi:
            return i
    raise RunnerLawError(
        f"decision session {d} outside the frozen fold windows: refused")


# ------------------------------------------------------------------ #
# Position law (holding + last-write-wins + force-flat).               #
# ------------------------------------------------------------------ #

def positions_from_states(
        states: Sequence[float | None],
        instants: Sequence[Mapping[str, Any]],
        arm_id: str,
        holding: int = HOLDING_TRADING_DAYS,
) -> tuple[list[dict], list[dict], dict]:
    """Frozen position law over the bookable instants.

    - A non-zero state event at instant i (state s) LAST-WRITE-WINS:
      closes any open round trip at i (exit_reason ``overwritten``) and
      opens a new one with direction s.
    - Force-flat after ``holding`` common-grid sessions: exit at the
      instant whose session_index = entry session_index + holding
      (exit_reason ``holding``).
    - Force-flat at fold ends: a position never survives past its entry
      fold's last instant (exit_reason ``fold_end``); if the fold cap
      lands ON the entry instant itself the round trip is same-day
      (counted in meta.fold_force_flat_same_day -- the FOREX-NG1
      precedent's metric, unit adapted to decision instants).
    - Q-11: an UNDEFINED state (None) is NO event and is counted in
      meta.states_undefined -- distinct from a defined 0 (flat), never
      inferred as zero.

    Returns (decision_records, round_trips, meta) -- structural only:
    ONE decision record per bookable instant, no outcome fields.
    """
    if len(states) != len(instants):
        raise RunnerLawError("states/instants length mismatch")
    if holding <= 0:
        raise RunnerLawError("holding must be positive")
    if not instants:
        raise RunnerLawError("empty instant grid: refused")

    session_index_of = [int(inst["session_index"]) for inst in instants]
    pos_of_idx = {idx: i for i, idx in enumerate(session_index_of)}
    fold_of_idx = {int(inst["session_index"]):
                   fold_of_session(inst["decision_session"])
                   for inst in instants}
    last_idx_per_fold: dict[int, int] = {}
    for idx in session_index_of:  # ascending
        last_idx_per_fold[fold_of_idx[idx]] = idx
    last_idx_overall = session_index_of[-1]

    records: list[dict] = []
    for inst, s in zip(instants, states):
        records.append({
            "decision_id": f"{arm_id}|{inst['decision_session']}",
            "arm_id": arm_id,
            "family_id": FAMILY_ID,
            "decision_session": str(inst["decision_session"]),
            "decision_utc": str(inst["decision_utc"]),
            "readable_bar_date": str(inst["readable_bar_date"]),
            "session_index": int(inst["session_index"]),
            "fold": fold_of_idx[int(inst["session_index"])],
            "state": None if s is None else float(s),
            "position_after": 0,
            "round_trip_opened": None,
            "round_trip_closed": None,
            "events": [],
        })

    round_trips: list[dict] = []
    active: dict | None = None
    seq = 0
    n_defined = n_undefined = n_events = 0
    folds_decisions: dict[str, int] = {}
    folds_state_events: dict[str, int] = {}
    exit_reasons: dict[str, int] = {r: 0 for r in EXIT_REASONS}
    fold_force_flat_same_day = 0

    def close(active_rt: dict, at_idx: int, reason: str) -> None:
        nonlocal fold_force_flat_same_day
        if reason not in exit_reasons:
            raise RunnerLawError(f"unknown exit reason {reason!r}")
        if at_idx not in pos_of_idx:
            raise RunnerLawError(
                f"exit session index {at_idx} is not a bookable instant "
                "(fail-closed: never inferred)")
        active_rt["exit_session_index"] = at_idx
        active_rt["exit_session"] = records[pos_of_idx[at_idx]][
            "decision_session"]
        active_rt["exit_reason"] = reason
        exit_reasons[reason] += 1
        if reason == "fold_end" and at_idx == active_rt[
                "entry_session_index"]:
            fold_force_flat_same_day += 1
        rec = records[pos_of_idx[at_idx]]
        rec["round_trip_closed"] = active_rt["rt_id"]
        rec["events"].append({"type": "ROUND_TRIP_CLOSED",
                              "round_trip_id": active_rt["rt_id"],
                              "exit_reason": reason})

    for i, inst in enumerate(instants):
        idx = session_index_of[i]
        fold = fold_of_idx[idx]
        folds_decisions[str(fold)] = folds_decisions.get(str(fold), 0) + 1

        # -- scheduled exits: the EARLIER of holding expiry / fold cap -- #
        if active is not None:
            fold_cap = last_idx_per_fold[active["fold"]]
            expiry_idx = active["entry_session_index"] + holding
            cap = min(expiry_idx, fold_cap)
            if cap <= idx:
                close_at = min(cap, last_idx_overall)
                # Truthful reason trichotomy (mutually exclusive; the
                # fold cap is always <= the grid's last instant, so the
                # binding constraint is identified exactly):
                #   holding    -- the frozen expiry completes at or
                #                 before the entry fold's last instant;
                #   fold_end   -- the fold boundary binds strictly
                #                 before the grid's last instant;
                #   window_end -- the fold end coincides with the
                #                 grid's last instant and the expiry ran
                #                 past it (data truncation).
                if expiry_idx <= fold_cap:
                    reason = "holding"
                elif fold_cap < last_idx_overall:
                    reason = "fold_end"
                else:
                    reason = "window_end"
                close(active, close_at, reason)
                round_trips.append(active)
                active = None

        s = states[i]
        if s is None:
            n_undefined += 1
        else:
            n_defined += 1

        if s is not None and float(s) != 0.0:
            n_events += 1
            folds_state_events[str(fold)] = folds_state_events.get(
                str(fold), 0) + 1
            if active is not None:
                close(active, idx, "overwritten")
                round_trips.append(active)
                active = None
            seq += 1
            rt_id = f"{arm_id}|RT{seq:05d}"
            active = {
                "rt_id": rt_id,
                "arm_id": arm_id,
                "family_id": FAMILY_ID,
                "direction": 1 if float(s) > 0 else -1,
                "entry_session_index": idx,
                "entry_session": str(inst["decision_session"]),
                "fold": fold,
            }
            records[i]["round_trip_opened"] = rt_id
            records[i]["events"].append({"type": "ROUND_TRIP_OPENED",
                                         "round_trip_id": rt_id,
                                         "direction": active["direction"]})

        records[i]["position_after"] = active["direction"] \
            if active is not None else 0

    if active is not None:
        fold_cap = last_idx_per_fold[active["fold"]]
        expiry_idx = active["entry_session_index"] + holding
        cap = min(expiry_idx, fold_cap)
        close_at = min(cap, last_idx_overall)
        if expiry_idx <= fold_cap:
            reason = "holding"
        elif fold_cap < last_idx_overall:
            reason = "fold_end"
        else:
            reason = "window_end"
        close(active, close_at, reason)
        round_trips.append(active)
        active = None

    ids = [r["decision_id"] for r in records]
    meta = {
        "decisions_total": len(instants),
        "states_defined": n_defined,
        "states_undefined": n_undefined,
        "state_events_nonzero": n_events,
        "round_trips": len(round_trips),
        "folds_decisions": folds_decisions,
        "folds_state_events": folds_state_events,
        "exit_reasons": exit_reasons,
        "fold_force_flat_same_day": fold_force_flat_same_day,
        "holding_trading_days": holding,
        "decision_ids_pairwise_distinct": len(set(ids)) == len(ids),
    }
    return records, round_trips, meta


# ------------------------------------------------------------------ #
# Kernel booking (P1 dual-book kernel, used verbatim; SHORT legs are   #
# mirror-booked with a disclosed runner-level sign).                   #
# ------------------------------------------------------------------ #

class PairedLegBooks:
    """Per-(leg, orientation) dual-book ledgers for one arm.

    LONG orientation  : native kernel booking (BUY entry / SELL exit).
    SHORT orientation : the true short round trip (SELL entry / BUY
    exit) is not representable in the long-only P1 kernel, so the leg is
    MIRROR-booked (BUY entry / SELL exit at TRUE prices and TRUE
    quantities; identical once-per-fill costs) and the runner-level
    sign is applied by :func:`round_trip_leg_signed_pnl` (short PnL =
    -(mirror long PnL)).  Disclosed representation; no kernel math is
    forked; every book carries the dual-book equality proof.
    """

    def __init__(self, arm_id: str):
        self.arm_id = str(arm_id)
        self.ledgers: dict[str, DualBookLedger] = {}

    def ledger(self, leg: str, orientation: str) -> DualBookLedger:
        name = f"{self.arm_id}|{leg}|{orientation}"
        if name not in self.ledgers:
            self.ledgers[name] = DualBookLedger(name, starting_equity=0.0)
        return self.ledgers[name]

    def book(self, rt_id: str, leg: str, orientation: str, qty: float,
             entry_price: float, exit_price: float,
             spread_cost_entry: float, spread_cost_exit: float,
             er_daily: float, ts_entry: str, ts_exit: str,
             drag_days: float = HOLDING_CALENDAR_DAYS_CHARGED,
             ) -> None:
        """Book ONE leg of ONE round trip: 2 fills (spread cost charged
        ONCE per fill), 2 shared marks, 1 typed expense-drag event
        (cost book only) -- kernel primitives verbatim."""
        led = self.ledger(leg, orientation)
        led.apply_fill(fill_id=f"{rt_id}|{leg}|ENTRY", ts=ts_entry,
                       ticker=leg, side="BUY", qty=qty, price=entry_price,
                       spread_cost=spread_cost_entry)
        led.apply_mark(ts=ts_entry, ticker=leg, price=entry_price)
        led.apply_fill(fill_id=f"{rt_id}|{leg}|EXIT", ts=ts_exit,
                       ticker=leg, side="SELL", qty=qty, price=exit_price,
                       spread_cost=spread_cost_exit)
        led.apply_mark(ts=ts_exit, ticker=leg, price=exit_price)
        led.apply_expense_drag(ts=ts_exit, days=drag_days,
                               notional=qty * entry_price,
                               per_day_fraction=er_daily)

    def structural_view(self) -> dict:
        """Outcome-free structural view: row counts + equality proofs
        ONLY (no equity/price_pnl amounts -- I-phase emission law)."""
        out: dict[str, Any] = {}
        for name, led in self.ledgers.items():
            eq = led.dual_book_equality()
            out[name] = {
                "fills": len(led.fills),
                "marks": len(led.marks),
                "cost_events": len(led.cost_events),
                "dual_book_equality_ok": bool(eq["equality_ok"]),
                "sign_inverted": bool(eq["sign_record"]["sign_inverted"]),
            }
        return out


def round_trip_leg_signed_pnl(orientation: str,
                              mirror_long_pnl: float) -> float:
    """E-phase signed arithmetic surface: the SHORT orientation's true
    leg PnL is the NEGATIVE of the mirror-booked long-form PnL (all
    prices and quantities are the true market values; only the
    aggregation sign flips, exactly as short selling works: proceeds
    first, cost to close).  LONG passes through.  Exercised on
    synthetic fixtures only in I."""
    if orientation == "SHORT":
        return -float(mirror_long_pnl)
    if orientation == "LONG":
        return float(mirror_long_pnl)
    raise RunnerLawError(f"unknown leg orientation {orientation!r}")


def book_round_trips(
        arm_id: str,
        round_trips: Sequence[dict],
        leg_closes_by_date: Mapping[str, Mapping[str, float]],
        tiers_bps: Mapping[str, float],
        er_daily: Mapping[str, float],
        notional_per_leg: float = NOTIONAL_PER_LEG_USD,
) -> PairedLegBooks:
    """Book every round trip's BOTH legs through the P1 kernel.

    Cost law (frozen tier 2.0): each fill carries its leg's CS p90
    stress tier ONCE (spread = bps/1e4 x fill notional), on BOTH legs;
    plus one ACT/365F expense-drag event per leg per round trip over
    the frozen 7-calendar-day holding convention.  Fill prices are the
    RAW closes at the entry/exit decision sessions (V7 law: execution
    AT the 16:00 NY close).  Any missing/non-positive price is
    fail-closed (never inferred)."""
    books = PairedLegBooks(arm_id)
    front, long_leg = LEG_PAIR["front_leg"], LEG_PAIR["long_leg"]
    for rt in round_trips:
        direction = int(rt["direction"])
        d_in, d_out = rt["entry_session"], rt["exit_session"]
        legs: dict[str, dict] = {}
        for leg, leg_dir in ((front, direction), (long_leg, -direction)):
            prices = leg_closes_by_date.get(leg, {})
            if d_in not in prices or d_out not in prices:
                raise RunnerLawError(
                    f"missing RAW close for {leg} at {d_in}/{d_out}: "
                    "fail-closed (never inferred)")
            p_in, p_out = float(prices[d_in]), float(prices[d_out])
            if p_in <= 0 or p_out <= 0:
                raise RunnerLawError(f"non-positive {leg} close: refused")
            qty = notional_per_leg / p_in
            orientation = "LONG" if leg_dir > 0 else "SHORT"
            tier = float(tiers_bps[leg]) / 1e4
            cost_in = tier * p_in * qty
            cost_out = tier * p_out * qty
            books.book(rt["rt_id"], leg, orientation, qty, p_in, p_out,
                       cost_in, cost_out, float(er_daily[leg]),
                       ts_entry=ck.ny_close_utc(d_in).isoformat(),
                       ts_exit=ck.ny_close_utc(d_out).isoformat())
            legs[leg] = {
                "orientation": orientation,
                "qty": qty,
                "entry_price": p_in,
                "exit_price": p_out,
                "side_entry_kernel": "BUY",
                "side_exit_kernel": "SELL",
                "spread_cost_entry": cost_in,
                "spread_cost_exit": cost_out,
                "drag_days": HOLDING_CALENDAR_DAYS_CHARGED,
                "drag_notional": qty * p_in,
                "tenor_bracket": (next(t for t, l in
                                       TENOR_BRACKET_MAPPING.items()
                                       if l == leg)),
            }
        rt["legs"] = legs
        rt["cost_event_count"] = len(legs) * 3  # 2 spread + 1 drag / leg
    return books


# ------------------------------------------------------------------ #
# Arm runner.                                                          #
# ------------------------------------------------------------------ #

def run_arm(arm_id: str,
            arm_role: str,
            config: Mapping[str, Any],
            instants: Sequence[Mapping[str, Any]],
            curve_by_date: Mapping[str, Mapping[str, float]],
            leg_closes_by_date: Mapping[str, Mapping[str, float]],
            tiers_bps: Mapping[str, float],
            er_daily: Mapping[str, float],
            ) -> dict:
    """Run ONE frozen gate-variant arm end-to-end on a bookable-instant
    grid: state series -> decision series + round trips -> kernel
    books.  Structural emission only (no after-cost outcome fields)."""
    states = arm_state_series(config, curve_by_date, instants)
    decisions, round_trips, meta = positions_from_states(
        states, instants, arm_id=arm_id)
    books = book_round_trips(arm_id, round_trips, leg_closes_by_date,
                             tiers_bps, er_daily)
    return {
        "schema": SCHEMA,
        "arm_id": arm_id,
        "arm_role": arm_role,
        "family_id": FAMILY_ID,
        "arm_config_digest": canonical_digest(config),
        "state_series": list(states),
        "decision_series": decisions,
        "round_trips": round_trips,
        "books_structural": books.structural_view(),
        "books": books,
        "meta": meta,
    }


# ------------------------------------------------------------------ #
# Structural plumbing surface (Z/E phases): plane-backed loader.       #
# Not executed on real substrate anywhere in I.                        #
# ------------------------------------------------------------------ #

def load_representation(plane: "pa.RatesNG1Plane",
                        grid_census: Mapping[str, Any]) -> dict:
    """Load the P2 representation (grid census + curve tenor series +
    leg RAW closes) through the plane adapter (verify-on-read; any
    digest drift raises BLOCKED_DATA).  Structural plumbing only; NOT
    executed on real substrate anywhere in I."""
    instants = grid_census["census"]["bookable_instants"]
    grid_dates = [str(d) for d in grid_census["census"]["grid_dates"]]
    tenors = ("2 Yr", "10 Yr", "30 Yr")
    curve_by_date: dict[str, dict[str, float]] = {}
    grid_set = set(grid_dates)
    for y in sorted({int(d[:4]) for d in grid_dates}):
        for r in plane.curve_rows_for_year(y):
            d = r["date"]
            if d not in grid_set:
                continue
            rec: dict[str, float] = {}
            for t in tenors:
                try:
                    rec[t] = float((r.get(t) or "").strip())
                except ValueError:
                    pass
            curve_by_date[d] = rec
    leg_closes: dict[str, dict[str, float]] = {}
    for leg in (LEG_PAIR["front_leg"], LEG_PAIR["long_leg"]):
        rows = plane.etp_rows(leg)
        leg_closes[leg] = {str(r["date"]): float(r["close"])
                           for r in rows}
    return {
        "grid_dates": grid_dates,
        "instants": instants,
        "curve_by_date": curve_by_date,
        "leg_closes": leg_closes,
    }
