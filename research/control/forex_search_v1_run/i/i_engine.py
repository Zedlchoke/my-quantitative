#!/usr/bin/env python
"""FOREX-SEARCH-V1 I-lane exact-arm engines (lane fsearch-i, plan §8).

Implements the trading/cost/risk contract for the THREE frozen S-selected
arms (s/selection_freeze.json, commit df62d6f9):

    FSS-CLOCK-COND-MONTHPOS-SECOND-LONG   (CLOCK-COND, warmup 60)
    FSS-OPEN-GAP-CONFIRM-Q50              (OPEN-GAP,   warmup 252)
    FSS-VOL-DRIFT-MOM-L63                 (VOL-DRIFT,  warmup 252)

Construction reuse: the per-leg STATE engines are imported READ-ONLY from
the frozen P0 census module (p0/p0_census.py) — exactly the code that
produced the frozen fired census and the S-lane position series — so a
rebuilt position series is by-construction identical to the frozen one
(positions digests re-verified against s/selection_freeze.json at the
scored E run).

Laws implemented here (fail-closed everywhere):
  * 16:00-NY daily decision clock; state on completed bar t; entry at
    bar t+1 open, exit at bar t+1 close (single-session hold, §1).
  * OPEN-GAP §4 F3 timing exception: state from close(t)+open(t+1),
    forced fill AT open(t+1) — the ONE declared same-bar exception.
  * warmup per §8 (complete-window fail-closed; no expanding/partial
    windows anywhere).
  * force-flat at fold boundary by construction (a position exists at
    decision bar m only if the leg's own execution bar t+1 lies in the
    SAME fold).
  * dual books: price-only book (1.5 bps/fill charged once per fill,
    i.e. 2 fills per round trip) and conservatively-financed book
    (= price book − uniform 1.7 bps/night per session; entry→exit
    crosses exactly one rollover). STRESS TIER 2.0 multiplies BOTH
    costs and financing (operative stress worst case per round trip =
    2 x 1.5 x 2.0 + 1.7 x 2.0 = 9.4 bps). Sign invariance is CHECKED,
    never assumed: the financed book must never ADD pnl vs the price
    book and must not invert its sign.

NO scored output is produced anywhere in this lane: this module contains
NO real-data runner. The ONLY staging loader is hard-gated behind the
exact owner GO phrase and exists solely for the E phase; the I lane
never executes it (plan §9: E runs only after `GO FOREX SEARCH V1
SCORED EXECUTION` at this cycle's own gate).
"""

from __future__ import annotations

import bisect
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration")
RUN = WT / "research/control/forex_search_v1_run"
P0_DIR = RUN / "p0"
S_DIR = RUN / "s"

# FROZEN_SHA pin: s/selection_freeze.json as committed at df62d6f9
# (verified byte-identical in this worktree at lane start). Any drift is
# a FROZEN_SHA_MISMATCH stop condition for this lane.
FREEZE_SHA256 = "0a93685758e0bb317633a9eb08f14ce66061314cc15a48bb262b6ae9b0130d74"

# §4 F4 cost + financing constants (STATED-CONSERVATIVE; printed on every
# result alongside their derivation caveats — see adjudicate.DISCLOSURES).
COST_BPS_PER_FILL = 1.5
FIN_BPS_PER_NIGHT = 1.7
STRESS_MULTIPLIER_PRIMARY = 2.0
FILLS_PER_ROUND_TRIP = 2  # entry fill + exit fill; single-session hold
WORST_CASE_ROUND_TRIP_BPS = (
    FILLS_PER_ROUND_TRIP * COST_BPS_PER_FILL * STRESS_MULTIPLIER_PRIMARY
    + FIN_BPS_PER_NIGHT * STRESS_MULTIPLIER_PRIMARY)  # 9.4 bps

# §8 warmup (master-calendar 1-based first decision bar), from the frozen
# D1 manifest warmup_rule (pinned verbatim in the selection freeze).
FIRST_DECISION_BAR = {"CLOCK-COND": 61, "OPEN-GAP": 253, "VOL-DRIFT": 253}

FROZEN_ARMS = [
    "FSS-CLOCK-COND-MONTHPOS-SECOND-LONG",
    "FSS-OPEN-GAP-CONFIRM-Q50",
    "FSS-VOL-DRIFT-MOM-L63",
]
LEGS = ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]
R2_PER_STATE_PER_FOLD_FLOOR = 10        # §6 R2, value frozen in the D1 manifest
R5_MAX_WEEKDAY_SHARE_FLOOR = 0.35       # §6 R5, frozen before any census read
R6_USD_DRIFT_BAR = 0.20                 # §6 R6 (standing value; NOT relaxed)
P20_BOOKS_DISTINCT_BAR = 0.98           # §5 P-20
GO_PHRASE = "GO FOREX SEARCH V1 SCORED EXECUTION"


class Stop(Exception):
    """Fail-closed stop with an incident code (handoff-visible)."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha256_obj(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_freeze() -> dict:
    """Load the frozen selection freeze; FROZEN_SHA_MISMATCH on drift."""
    path = S_DIR / "selection_freeze.json"
    dig = sha256_file(path)
    if dig != FREEZE_SHA256:
        raise Stop("FROZEN_SHA_MISMATCH",
                   f"s/selection_freeze.json sha256 {dig} != frozen "
                   f"{FREEZE_SHA256}")
    return json.loads(path.read_text())


_P0 = None


def p0():
    """Import the frozen P0 census module READ-ONLY (state engines)."""
    global _P0
    if _P0 is None:
        sys.path.insert(0, str(P0_DIR))
        import p0_census  # noqa: PLC0415 — read-only reuse, the S-lane convention
        _P0 = p0_census
    return _P0


def engine_cfg(cfg_excerpt: dict) -> dict:
    """p0_census.compute_state expects the enumerate_configs layout
    (parameters at top level); the D1 manifest nests them under
    'parameters' (keys verified identical per family at P0/D1/S)."""
    return {"config_id": cfg_excerpt["config_id"],
            "family": cfg_excerpt["family"],
            **cfg_excerpt["parameters"]}


# ------------------------------------------------------------------ calendar

def fold_ids(folds: dict, n_master: int) -> list:
    pc = p0()
    return [pc.fold_of(folds, mi) for mi in range(n_master)]


def gate_firing(mi: int, direction: str, legname: str, legs: dict, master: list,
                fold_id: list, own_index: dict | None = None) -> bool:
    """Force-flat / execution gate: the firing at decision bar mi survives
    only if the leg's own execution bar t+1 exists AND localizes to the
    SAME fold (identical to the census counting law)."""
    leg = legs[legname]
    own = own_index if own_index is not None else \
        {d: i for i, d in enumerate(leg["dates"])}
    d_t = master[mi]
    i = own.get(d_t)
    if i is None or i + 1 >= len(leg["dates"]):
        return False
    nxt = leg["dates"][i + 1]
    mi_next = bisect.bisect_left(master, nxt)
    if mi_next >= len(master):
        return False  # execution beyond the frozen sample -> force-flat
    if fold_id[mi_next] != fold_id[mi]:
        return False  # force-flat at fold boundary (§8)
    return True


# ------------------------------------------------------------------ positions

def build_positions(cfg_excerpt: dict, legs: dict, master: list, folds: dict,
                    legs_order: list) -> dict:
    """Per-leg daily position series in {-1, 0, +1} on the master calendar,
    built by the frozen P0 state engines under the census counting law
    (identical construction to the S-lane PositionBuilder)."""
    pc = p0()
    fold_id = fold_ids(folds, len(master))
    own_index = {ln: {d: i for i, d in enumerate(legs[ln]["dates"])}
                 for ln in legs_order}
    pos = {ln: np.zeros(len(master), dtype=np.int8) for ln in legs_order}
    ecfg = engine_cfg(cfg_excerpt)
    for ln in legs_order:
        om = [own_index[ln].get(d) for d in master]
        if any(x is None for x in om):
            raise Stop("INPUT_MISMATCH",
                       f"{ln}: master calendar is not a subset of the leg calendar")
        state = pc.compute_state(ecfg, legs[ln], om, master)
        for mi, direction in state.items():
            if not gate_firing(mi, direction, ln, legs, master, fold_id,
                               own_index[ln]):
                continue
            pos[ln][mi] = 1 if direction == "LONG" else -1
    return pos


def positions_digest(positions: dict, legs_order: list) -> str:
    """The S-lane digest convention (sha256 of the sort-keys compact JSON
    of {leg: [ints]}) — comparable against s/selection_freeze.json."""
    return sha256_obj({k: [int(x) for x in positions[k]] for k in legs_order})


def verify_positions_vs_freeze(freeze: dict, config_id: str, positions: dict,
                               legs_order: list) -> None:
    """INPUT_MISMATCH law: a rebuilt series MUST equal the frozen digest
    (used at the scored E run; synthetic callers may pass a hand-built
    freeze-like dict)."""
    sel = next((s for s in freeze["selections"]
                if s["config_id"] == config_id), None)
    if sel is None:
        raise Stop("INPUT_MISMATCH", f"{config_id} not in the frozen selections")
    dig = positions_digest(positions, legs_order)
    if dig != sel["positions_digest"]:
        raise Stop("INPUT_MISMATCH",
                   f"{config_id} rebuilt positions digest {dig} != frozen "
                   f"{sel['positions_digest']}")


def raw_state(cfg_excerpt: dict, legs: dict, master: list, legs_order: list,
              shift: int = 0) -> dict:
    """Raw (ungated) P0 state dict {master_index: 'LONG'|'SHORT'} per leg.
    shift=1 evaluates the state ONE BAR EARLIER (C-PIT-MUTATION)."""
    pc = p0()
    own = {ln: {d: i for i, d in enumerate(legs[ln]["dates"])}
           for ln in legs_order}
    out = {}
    ecfg = engine_cfg(cfg_excerpt)
    for ln in legs_order:
        om = [own[ln].get(d) for d in master]
        if any(x is None for x in om):
            raise Stop("INPUT_MISMATCH",
                       f"{ln}: master calendar is not a subset of the leg calendar")
        om_shift = [x - shift for x in om]
        out[ln] = pc.compute_state(ecfg, legs[ln], om_shift, master)
    return out


def pit_mutated_positions(cfg_excerpt: dict, legs: dict, master: list,
                          folds: dict, legs_order: list) -> dict:
    """C-PIT-MUTATION (§6): the one-bar-earlier recomputation. Each master
    bar m carries the state computed from the window ending at m-1,
    attributed to decision bar m under the SAME fold/execution gating of
    that m-1 decision. The gate (adjudicate.stage_a_pit_mutation) requires
    the mutated book to CHANGE or REFUSE at every originally fired
    decision."""
    fold_id = fold_ids(folds, len(master))
    raw = raw_state(cfg_excerpt, legs, master, legs_order, shift=1)
    own_index = {ln: {d: i for i, d in enumerate(legs[ln]["dates"])}
                 for ln in legs_order}
    pos = {ln: np.zeros(len(master), dtype=np.int8) for ln in legs_order}
    for ln in legs_order:
        for mi_pseudo, direction in raw[ln].items():
            mi = mi_pseudo + 1  # attributed one bar later
            if mi >= len(master):
                continue
            if not gate_firing(mi_pseudo, direction, ln, legs, master, fold_id,
                               own_index[ln]):
                continue
            pos[ln][mi] = 1 if direction == "LONG" else -1
    return pos


# ------------------------------------------------------------------- trades

def build_trades(positions: dict, legs: dict, master: list, folds: dict,
                 legs_order: list) -> list:
    """One record per fired position: single-session trade, entry at the
    leg's own bar t+1 OPEN, exit at the same bar CLOSE. Fold = fold of the
    decision bar; force-flat re-asserted per trade (fail-closed)."""
    fold_id = fold_ids(folds, len(master))
    trades = []
    for ln in legs_order:
        leg = legs[ln]
        own = {d: i for i, d in enumerate(leg["dates"])}
        pos = positions[ln]
        for mi in np.nonzero(pos)[0]:
            mi = int(mi)
            d_t = master[mi]
            i = own.get(d_t)
            if i is None or i + 1 >= len(leg["dates"]):
                raise Stop("CONTRACT_VIOLATION",
                           f"position without execution bar at {ln} {d_t}")
            nxt = leg["dates"][i + 1]
            mi_next = bisect.bisect_left(master, nxt)
            if mi_next >= len(master) or fold_id[mi_next] != fold_id[mi]:
                raise Stop("CONTRACT_VIOLATION",
                           f"force-flat breach at {ln} {d_t}")
            side = int(pos[mi])
            entry = float(leg["open"][i + 1])
            exit_ = float(leg["close"][i + 1])
            if entry <= 0:
                raise Stop("INPUT_MISMATCH", f"non-positive entry price {ln} {d_t}")
            trades.append({
                "leg": ln,
                "mi_decision": mi,
                "decision_date": d_t,
                "mi_exec": i + 1,
                "exec_date": nxt,
                "fold": fold_id[mi],
                "side": side,
                "entry": entry,
                "exit": exit_,
                "gross_bps": side * (exit_ / entry - 1.0) * 1e4,
                "state_key": f"side{side:+d}",
            })
    trades.sort(key=lambda t: (t["fold"], t["mi_decision"], t["leg"]))
    return trades


def ladder_bps(trades: list, stress: float, cost_bps: float = COST_BPS_PER_FILL,
               fin_bps: float = FIN_BPS_PER_NIGHT) -> tuple:
    """Per-trade price-only and financed book bps under the §4 F4 ladder.

    price book    = gross − costs            (2 fills x 1.5 bps x stress)
    financed book = price − financing        (1 night x 1.7 bps x stress;
                    entry→exit crosses exactly one rollover)
    stress 2.0 is PRIMARY; the worst case per round trip is
    2 x 1.5 x 2.0 + 1.7 x 2.0 = 9.4 bps. cost_bps/fin_bps overrides exist
    ONLY for checker-sensitivity fixtures (e.g. proving the sign-invariance
    check actually fires); production paths use the frozen constants.
    """
    price = np.array([t["gross_bps"] - FILLS_PER_ROUND_TRIP * cost_bps
                      * stress for t in trades], dtype=np.float64)
    financed = price - fin_bps * stress
    return price, financed


def dual_books_check(trades: list, stress: float, tol: float = 1e-9,
                     cost_bps: float = COST_BPS_PER_FILL,
                     fin_bps: float = FIN_BPS_PER_NIGHT) -> dict:
    """§6 dual-books gate on the per-trade ladder:
      (a) sign invariance: the financed book NEVER ADDS pnl vs the price
          book (financed <= price on every trade, and in aggregate);
      (b) no sign inversion of the aggregate book.
    Any breach fails the arm, fail-closed."""
    price, financed = ladder_bps(trades, stress, cost_bps, fin_bps)
    never_adds = bool(np.all(financed <= price + tol)) and \
        float(financed.sum()) <= float(price.sum()) + tol
    sp, sf = float(price.sum()), float(financed.sum())
    inversion = (sp != 0.0 and sf != 0.0 and np.sign(sp) != np.sign(sf))
    return {"price_net_bps": sp, "financed_net_bps": sf,
            "financed_never_adds_pnl": never_adds,
            "sign_inversion": bool(inversion),
            "pass": bool(never_adds and not inversion),
            "stress_multiplier": stress,
            "worst_case_round_trip_bps": WORST_CASE_ROUND_TRIP_BPS}


def summarize_book(bps: np.ndarray, trades: list) -> dict:
    """Net expectancy / profit factor / per-fold nets for one book."""
    arr = np.asarray(bps, dtype=np.float64)
    wins = arr[arr > 0].sum()
    losses = -arr[arr < 0].sum()
    per_fold = {str(f): float(arr[[i for i, t in enumerate(trades)
                                   if t["fold"] == f]].sum())
                for f in sorted({t["fold"] for t in trades})}
    return {
        "n_trades": int(arr.size),
        "net_bps": float(arr.sum()),
        "expectancy_bps": float(arr.mean()) if arr.size else None,
        "profit_factor": (float(wins / losses) if losses > 0
                          else (float("inf") if wins > 0 else None)),
        "per_fold_net_bps": per_fold,
    }


def substate_counts(trades: list) -> dict:
    """R2 population census: fired decisions per STATE per FOLD (state =
    the fired side sub-state, the finer partition — conservative)."""
    counts: dict[int, dict[str, int]] = {}
    for t in trades:
        counts.setdefault(t["fold"], {}).setdefault(t["state_key"], 0)
        counts[t["fold"]][t["state_key"]] += 1
    return {str(f): {k: v for k, v in sorted(c.items())}
            for f, c in sorted(counts.items())}


# ------------------------------------------------------- control/complement books

def complement_cfg(cfg_excerpt: dict) -> dict:
    """CTL-COMPLEMENT per the frozen D1 manifest definitions (verbatim in
    the selection freeze excerpts):
      CLOCK-COND MONTHPOS SECOND-LONG -> same fixed direction LONG on the
          complement calendar day-set (FIRST half), same warmup;
      OPEN-GAP CONFIRM-Q50 -> the enumerated FSS-OPEN-GAP-FADE-Q50;
      VOL-DRIFT MOM-L63 -> condition-flip book: the MOM-L63 position map
          applied on the HIGH-tercile days (custom engine below).
    """
    cid = cfg_excerpt["config_id"]
    if cid == "FSS-CLOCK-COND-MONTHPOS-SECOND-LONG":
        return {"config_id": "FSS-CLOCK-COND-MONTHPOS-FIRST-LONG",
                "family": "CLOCK-COND",
                "parameters": {"direction": "LONG", "monthpos": "FIRST"}}
    if cid == "FSS-OPEN-GAP-CONFIRM-Q50":
        return {"config_id": "FSS-OPEN-GAP-FADE-Q50",
                "family": "OPEN-GAP",
                "parameters": {"mode": "FADE", "pct": 50}}
    if cid == "FSS-VOL-DRIFT-MOM-L63":
        return {"config_id": "FSS-VOL-DRIFT-MOM-L63-COMPLEMENT-HIGH",
                "family": "VOL-DRIFT",
                "parameters": {"L": 63, "mode": "MOM_HIGH_CONDITION_FLIP"}}
    raise Stop("INPUT_MISMATCH", f"no frozen CTL-COMPLEMENT mapping for {cid}")


def state_vol_drift_condition_flip(leg: dict, own_of_master: list, L: int,
                                   warmup_master: int) -> dict:
    """VOL-DRIFT CTL-COMPLEMENT engine (frozen excerpt: 'condition-flip
    book: the MOM-L63 position map applied on the HIGH-tercile days').
    Identical estimator + tercile law to the P0 MOM engine; conditions on
    the HIGH tercile instead of LOW; direction map unchanged (r > 0 ->
    LONG, r < 0 -> SHORT); complete-window fail-closed."""
    c = leg["close"]
    n = len(c)
    lr = np.full(n, np.nan)
    lr[1:] = np.log(c[1:] / c[:-1])
    vol = np.full(n, np.nan)
    for i in range(L, n):
        vol[i] = np.std(lr[i - L + 1:i + 1], ddof=1)
    out = {}
    for m, i in enumerate(own_of_master):
        if m < warmup_master:
            continue
        if i < L + 251 or np.isnan(vol[i - 251:i + 1]).any():
            continue
        w = vol[i - 251:i + 1]
        b2 = float(np.quantile(w, 2.0 / 3.0))
        if vol[i] < b2:
            continue
        if i - L < 0:
            continue
        r = c[i] - c[i - L]
        if r > 0:
            out[m] = "LONG"
        elif r < 0:
            out[m] = "SHORT"
    return out


def build_control_positions(kind: str, cfg_excerpt: dict, legs: dict,
                            master: list, folds: dict, legs_order: list) -> dict:
    """Positions for CTL-COMPLEMENT ('complement'), R4 trend-only
    ('trend_only') and R5 CLOCK-ONLY ('clock_only') books, all on the SAME
    decision grid, warmup and force-flat gating as the arm book."""
    warmup = FIRST_DECISION_BAR[cfg_excerpt["family"]] - 1
    fold_id = fold_ids(folds, len(master))
    if kind == "clock_only":
        pos = {ln: np.zeros(len(master), dtype=np.int8) for ln in legs_order}
        for ln in legs_order:
            for mi in range(warmup, len(master)):
                # CLOCK-ONLY: rotation on the same daily clock, NO signal
                # input — long every session (declared here; the D1
                # manifest pins no clock-only book, this lane's harness
                # declares the always-long no-signal book and prints the
                # declaration on every R5 output).
                if gate_firing(mi, "LONG", ln, legs, master, fold_id):
                    pos[ln][mi] = 1
        return pos
    if kind == "complement":
        ccfg = complement_cfg(cfg_excerpt)
        if ccfg["parameters"].get("mode") == "MOM_HIGH_CONDITION_FLIP":
            return _custom_state_positions(
                lambda leg, om: state_vol_drift_condition_flip(
                    leg, om, ccfg["parameters"]["L"], warmup),
                legs, master, folds, legs_order)
        return build_positions(ccfg, legs, master, folds, legs_order)
    if kind == "trend_only":
        cid = cfg_excerpt["config_id"]
        if cid == "FSS-CLOCK-COND-MONTHPOS-SECOND-LONG":
            raise Stop("NOT_ADJUDICABLE",
                       "R4 trend-only: no analog exists for CLOCK-COND "
                       "(frozen D1 manifest; disclosed, never an inferred PASS)")
        if cid == "FSS-OPEN-GAP-CONFIRM-Q50":
            def st(leg, om):
                return state_open_gap_trend_only(leg, om, warmup)
            return _custom_state_positions(st, legs, master, folds, legs_order)
        if cid == "FSS-VOL-DRIFT-MOM-L63":
            def st(leg, om):
                return state_vol_drift_trend_only(leg, om, 63, warmup)
            return _custom_state_positions(st, legs, master, folds, legs_order)
        raise Stop("INPUT_MISMATCH", f"no trend-only mapping for {cid}")
    raise Stop("INPUT_MISMATCH", f"unknown control book kind {kind}")


def _custom_state_positions(state_fn, legs: dict, master: list, folds: dict,
                            legs_order: list) -> dict:
    fold_id = fold_ids(folds, len(master))
    own_index = {ln: {d: i for i, d in enumerate(legs[ln]["dates"])}
                 for ln in legs_order}
    pos = {ln: np.zeros(len(master), dtype=np.int8) for ln in legs_order}
    for ln in legs_order:
        om = [own_index[ln].get(d) for d in master]
        if any(x is None for x in om):
            raise Stop("INPUT_MISMATCH",
                       f"{ln}: master calendar is not a subset of the leg calendar")
        for mi, direction in state_fn(legs[ln], om).items():
            if not gate_firing(mi, direction, ln, legs, master, fold_id,
                               own_index[ln]):
                continue
            pos[ln][mi] = 1 if direction == "LONG" else -1
    return pos


def state_open_gap_trend_only(leg: dict, own_of_master: list,
                              warmup_master: int) -> dict:
    """OPEN-GAP R4 trend-only book (frozen D1 definition): the SIGNED gap
    traded without threshold or fade direction — g[i+1] > 0 -> LONG;
    g[i+1] < 0 -> SHORT. Same §4 F3 timing exception (state from
    close(t)+open(t+1), fill at open(t+1)); same warmup; no percentile."""
    o, c = leg["open"], leg["close"]
    n = len(c)
    g = np.full(n, np.nan)
    g[1:] = o[1:] - c[:-1]
    out = {}
    for m, i in enumerate(own_of_master):
        if m < warmup_master:
            continue
        if i + 1 >= n or np.isnan(g[i + 1]):
            continue
        if g[i + 1] > 0:
            out[m] = "LONG"
        elif g[i + 1] < 0:
            out[m] = "SHORT"
    return out


def state_vol_drift_trend_only(leg: dict, own_of_master: list, L: int,
                               warmup_master: int) -> dict:
    """VOL-DRIFT R4 trend-only book (frozen D1 definition): the L-bar price
    change traded unconditionally — r = C[i] − C[i-L] > 0 -> LONG;
    r < 0 -> SHORT; NO vol-tercile conditioning. Same warmup/decision grid
    as the arm for comparability; complete-window fail-closed."""
    c = leg["close"]
    out = {}
    for m, i in enumerate(own_of_master):
        if m < warmup_master:
            continue
        if i - L < 0:
            continue
        r = c[i] - c[i - L]
        if r > 0:
            out[m] = "LONG"
        elif r < 0:
            out[m] = "SHORT"
    return out


# ------------------------------------------------------------ series + gates

def daily_pnl_series(trades: list, bps: np.ndarray, master: list,
                     legname: str | None = None) -> np.ndarray:
    """Financed bps summed by DECISION date (master-calendar aligned)."""
    series = np.zeros(len(master), dtype=np.float64)
    for t, b in zip(trades, bps):
        if legname is not None and t["leg"] != legname:
            continue
        series[t["mi_decision"]] += float(b)
    return series


def usd_basket_series(legs: dict, master: list, legs_order: list) -> dict:
    """Equal-weighted USD basket from the SAME five legs (§6 USD-DRIFT
    gate): the USD-side open->close return per session. For XXXUSD quotes
    the USD side is the NEGATIVE of the pair return; for USDCAD it is the
    pair return itself. Per-leg series + equal-weighted pool."""
    per_leg = {}
    for ln in legs_order:
        leg = legs[ln]
        own = {d: i for i, d in enumerate(leg["dates"])}
        s = np.zeros(len(master), dtype=np.float64)
        sign = -1.0 if ln.endswith("USD") and ln != "USDCAD" else 1.0
        for mi, d in enumerate(master):
            i = own.get(d)
            if i is None or i + 1 >= len(leg["dates"]):
                continue
            r = (leg["close"][i + 1] / leg["open"][i + 1] - 1.0) * 1e4
            s[mi] = sign * r
        per_leg[ln] = s
    pooled = np.mean([per_leg[ln] for ln in legs_order], axis=0)
    return {"per_leg_usd_side_bps": per_leg, "basket_bps": pooled}


def pearson(a: np.ndarray, b: np.ndarray):
    """Pearson rho; (None, reason) when unmeasurable (zero variance)."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.size < 2 or float(np.std(a)) == 0.0 or float(np.std(b)) == 0.0:
        return None, "UNMEASURABLE_ZERO_VARIANCE_SERIES"
    cov = float(np.mean((a - a.mean()) * (b - b.mean())))
    rho = cov / (float(np.std(a)) * float(np.std(b)))
    return rho, "OK"


def max_drawdown_frac(daily_bps: np.ndarray) -> float:
    """Max drawdown (fraction) of the compounded equity of a daily bps
    series (0 when the series never moves)."""
    arr = np.asarray(daily_bps, dtype=np.float64) / 1e4
    if arr.size == 0 or float(np.std(arr)) == 0.0:
        return 0.0
    eq = np.cumprod(1.0 + arr)
    peak = np.maximum.accumulate(eq)
    return float(np.max(1.0 - eq / peak))


def weekday_share_of_firings(positions: dict, master: list,
                             legs_order: list) -> dict:
    """R5 FIRED CENSUS weekday overlay: share of fired decisions (pooled
    across legs) per ISO weekday; the max WEEKDAY (1..5) share is gated at
    0.35 (breach => the state IS a calendar condition)."""
    from datetime import date
    hist = {d: 0 for d in (1, 2, 3, 4, 5, 6, 7)}
    total = 0
    for ln in legs_order:
        for mi in np.nonzero(positions[ln])[0]:
            y, mo, dd = (int(x) for x in master[int(mi)].split("-"))
            hist[date(y, mo, dd).isoweekday()] += 1
            total += 1
    shares = {str(d): (hist[d] / total if total else 0.0)
              for d in (1, 2, 3, 4, 5, 6, 7)}
    max_weekday_share = max(shares[str(d)] for d in (1, 2, 3, 4, 5))
    return {"total_fired": total, "shares": shares,
            "max_weekday_share": max_weekday_share,
            "floor": R5_MAX_WEEKDAY_SHARE_FLOOR}


def serial_clustering_census(positions: dict, legs_order: list) -> dict:
    """§6 serial-clustering census (disclosure): fired decision bars whose
    previous master bar also fired, per leg and pooled. Trade-independence
    is DECLARED NOT ASSUMED (P0 manifest freeze)."""
    per_leg = {}
    for ln in legs_order:
        pos = positions[ln]
        idx = set(int(i) for i in np.nonzero(pos)[0])
        adj = sum(1 for i in idx if (i - 1) in idx)
        per_leg[ln] = {"fired": len(idx), "consecutive_fired": adj}
    pooled_fired = sum(v["fired"] for v in per_leg.values())
    pooled_adj = sum(v["consecutive_fired"] for v in per_leg.values())
    return {"per_leg": per_leg, "pooled_fired": pooled_fired,
            "pooled_consecutive_fired": pooled_adj,
            "trade_independence": "DECLARED NOT ASSUMED"}


def p20_pooled_rho(positions_a: dict, positions_b: dict,
                   legs_order: list):
    """P-20 pooled rho (census pooling convention: concatenation of the
    per-leg series in manifest legs order)."""
    a = np.concatenate([positions_a[k] for k in legs_order]).astype(np.float64)
    b = np.concatenate([positions_b[k] for k in legs_order]).astype(np.float64)
    return pearson(a, b)


# ------------------------------------------------------------- real-data path
# HARD-GATED: the ONLY staging loader in this lane. The I lane never calls
# it; the scored E run may, exclusively behind the exact owner GO phrase.

def load_staging_legs() -> dict:
    if os.environ.get("FOREX_SEARCH_V1_GO_PHRASE") != GO_PHRASE:
        raise Stop("SCORED_EXECUTION_NOT_AUTHORIZED",
                   "the staging loader is gated behind the exact owner GO "
                   "phrase (plan §9 GO); the I lane performs NO real-data "
                   "execution")
    pc = p0()
    pin = json.loads((P0_DIR / "manifest_pin.json").read_text())
    legs = {}
    for ln in LEGS:
        archive, member, expect = pc.PAIR_SOURCES[ln]
        path = pc.STAGING / member
        if not path.exists():
            raise Stop("INPUT_MISMATCH", f"staging member missing: {path}")
        if pc.sha256_file(path) != expect or \
                pin["pairs"][ln]["sha256"] != expect:
            raise Stop("FROZEN_SHA_MISMATCH", f"{ln} staging digest drift")
        legs[ln] = pc.load_leg(path)
    return legs
