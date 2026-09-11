"""Decision-record builders for every frozen arm of the two selected
FOREX-NG1 families.

A DECISION RECORD is dry-safe by construction: identity (arm, event,
pair), direction, units, entry/exit grid days, exit reason, fold, and the
cost-contract constants.  It never carries prices, PnL, PF, expectancy,
stress or breakeven at any depth (the leak scanner enforces this).

Clocks and gates mirror the D2-verified builders in
``research.assets.forex_ng1.d2`` exactly (their structural counts
re-measured the D1 declarations); the dry-run re-asserts those counts.
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from datetime import date, timedelta

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1.d2 import events as E           # noqa: E402
from research.assets.forex_ng1.d2.books import (               # noqa: E402
    funded_pair_sign, us_event_pair_signs,
)
from research.assets.forex_ng1.d2.series import (              # noqa: E402
    s1_seasonal_naive, s2_trailing_yoy,
)
from research.assets.forex_ng1.run import config as C          # noqa: E402
from research.assets.forex_ng1.run.dgs10 import (              # noqa: E402
    Dgs10LevelSeries, extended_weekday_grid,
)

WINDOW_END = date.fromisoformat(C.S0_WINDOW["end"])


class ArmBuildError(Exception):
    """Fail-closed arm construction error."""


# --------------------------------------------------------------------------- #
# exit plan (H grid days; fold force-flat; window tail)
# --------------------------------------------------------------------------- #

def _fold_last_index(grid: list[date], fold: int) -> int:
    lo, hi = C.FOLD_BOUNDS[fold - 1]
    last = None
    for i, d in enumerate(grid):
        if d == hi:
            return i
        if d < hi:
            last = i
    return last if last is not None else len(grid) - 1


def exit_plan(entry: date, grid: list[date],
              grid_index: dict) -> tuple[date, str, int]:
    """(exit_day, reason, fold) with fold force-flat + window tail.

    - horizon: the grid day H = 5 grid-days after entry;
    - fold_force_flat: capped at the entry fold's last grid day
      (positions never span a fold boundary);
    - forced_window_end: capped at the final grid day (2025-04-30 tail
      convention).
    """
    i = grid_index[entry]
    fold = C.fold_of_day(entry)
    j = i + C.HOLD_GRID_DAYS
    cap = min(_fold_last_index(grid, fold), len(grid) - 1)
    if j <= cap:
        return grid[j], "horizon", fold
    if cap < j and cap < len(grid) - 1:
        return grid[cap], "fold_force_flat", fold
    return grid[len(grid) - 1], "forced_window_end", fold


# --------------------------------------------------------------------------- #
# record construction
# --------------------------------------------------------------------------- #

def _cost_block() -> dict:
    return {
        "bps_per_side": C.COST_BPS_PER_SIDE,
        "tier_ladder": list(C.COST_TIER_LADDER),
        "primary_tier": C.PRIMARY_TIER,
        "fills_per_round_trip": 2,
        "charged_once_per_fill": True,
        "notional_usd_per_unit": C.NOTIONAL_USD_UNIT,
    }


def _record(arm_id: str, family_id: str, role: str, ev: dict, pair: str,
            pair_direction: int, entry: date, grid: list[date],
            grid_index: dict, source: str) -> dict:
    exit_day, reason, fold = exit_plan(entry, grid, grid_index)
    eco = ev["economy"]
    return {
        "decision_id": f"{arm_id}|{eco}|{ev['publication_date']}|{pair}",
        "arm_id": arm_id,
        "family_id": family_id,
        "arm_role": role,
        "event": {
            "event_key": f"{eco}|{ev['publication_date']}",
            "economy": eco,
            "reference_period": ev["reference_period"],
            "publication_date": ev["publication_date"],
        },
        "pair": pair,
        "direction": int(pair_direction),
        "units": 1.0,
        "entry_grid_day": entry.isoformat(),
        "exit_grid_day": exit_day.isoformat(),
        "exit_reason": reason,
        "fold": fold,
        "signal_source": source,
        "cost_contract": _cost_block(),
    }


def _new_meta(arm_id: str, family_id: str) -> dict:
    return {
        "arm_id": arm_id,
        "family_id": family_id,
        "arm_role": C.ARM_ROLE[arm_id],
        "events_total": 0,
        "events_in_window": 0,
        "events_failed_closed": 0,
        "events_below_threshold": 0,
        "decisions_fired": 0,
        "by_economy_fired": {},
        "exit_reasons": {},
        "folds_decisions": {},
        "fold_force_flat_same_day": 0,
    }


def _finalize(records: list[dict], meta: dict) -> dict:
    eco = Counter(r["event"]["economy"] for r in records)
    exits = Counter(r["exit_reason"] for r in records)
    folds = Counter(str(r["fold"]) for r in records)
    meta["decisions_fired"] = len(records)
    meta["by_economy_fired"] = dict(eco)
    meta["exit_reasons"] = dict(exits)
    meta["folds_decisions"] = dict(folds)
    meta["fold_force_flat_same_day"] = sum(
        1 for r in records if r["exit_reason"] == "fold_force_flat"
        and r["exit_grid_day"] == r["entry_grid_day"])
    ids = [r["decision_id"] for r in records]
    if len(set(ids)) != len(ids):
        raise ArmBuildError(
            f"{meta['arm_id']}: duplicate decision_ids (fail-closed)")
    return {"arm_id": meta["arm_id"], "meta": meta, "decisions": records}


# --------------------------------------------------------------------------- #
# lane A5-P1 (own-pair opening follower)
# --------------------------------------------------------------------------- #

def _a5_event_months(mode: str, state: dict) -> dict:
    if mode == "anchor":
        return {m: [of] for m, of in state["unique_of"].items()}
    if mode == "coopen":
        em = {m: [of] for m, of in state["unique_of"].items()}
        for m, coe in state["co_earliest"].items():
            em[m] = list(em.get(m, [])) + list(coe)
        return em
    if mode == "v7recap":
        return {m: g["nonUS"] for m, g in state["anchored"].items()}
    if mode == "ordshuf_pool":
        return {m: g["nonUS"] for m, g in state["anchored"].items()}
    raise ArmBuildError(f"unknown a5 mode {mode!r}")


def _a5_pair_decisions(arm_id: str, mode: str, env,
                       threshold: float, direction_override=None,
                       source_tag: str = "s1") -> dict:
    """A5 own-pair decisions.  ``direction_override(event, entry) ->
    {economy_sign} | None`` replaces sign(s1) when given (controls,
    shadows); None fails the event closed."""
    family = C.FAMILY_OF_ARM[arm_id]
    meta = _new_meta(arm_id, family)
    grid, grid_index = env.grid, env.grid_index
    state = env.order_state
    records: list[dict] = []
    event_months = _a5_event_months(mode, state)
    meta["events_total"] = sum(len(v) for v in event_months.values())
    for mth in sorted(event_months):
        us_pub = date.fromisoformat(
            state["anchored"][mth]["us"]["publication_date"])
        for ev in event_months[mth]:
            eco = ev["economy"]
            operative = date.fromisoformat(
                ev["operative_vintaged_available_from"])
            bound = max(operative, us_pub)
            entry = E.first_grid_day_strictly_after(bound, grid_index,
                                                    WINDOW_END)
            if entry is None:
                continue
            meta["events_in_window"] += 1
            vs = env.series_by_eco.get(eco)
            s = None
            if vs is not None:
                try:
                    i_print = float(ev["vintaged_first_value"])
                    s, _d = s1_seasonal_naive(vs, ev["reference_period"],
                                              i_print, entry)
                except (KeyError, TypeError, ValueError):
                    s = None
            if s is None:
                meta["events_failed_closed"] += 1
                continue
            if abs(s) < threshold:
                meta["events_below_threshold"] += 1
                continue
            ssign = 1 if s > 0 else -1
            if direction_override is not None:
                ov = direction_override(ev, entry)
                if ov is None:
                    meta["events_failed_closed"] += 1
                    continue
                ssign = ov
            pair_signs = funded_pair_sign(eco, ssign)
            for pair, pdir in pair_signs.items():
                records.append(_record(
                    arm_id, family, C.ARM_ROLE[arm_id], ev, pair, pdir,
                    entry, grid, grid_index,
                    source=f"{source_tag}({s:+.6f}pp)" if
                    direction_override is None else source_tag))
    return _finalize(records, meta)


def build_a5p1_anchor(env) -> dict:
    return _a5_pair_decisions("FXNG1-A5-P1-ANCHOR", "anchor", env, 0.10)


def build_a5p1_coopen(env) -> dict:
    return _a5_pair_decisions("FXNG1-A5-P1-NEIGH-COOPEN", "coopen", env,
                              0.10)


def build_a5p1_v7recap(env) -> dict:
    return _a5_pair_decisions("FXNG1-A5-P1-CTL-V7RECAP", "v7recap", env,
                              0.10)


def build_a5p1_shadow_clock(env, anchor: dict) -> dict:
    """Identical fired anchor book, constant +1 direction."""
    return _remask_book("FXNG1-A5-P1-SHADOW-CLOCK", anchor,
                        lambda rec, ev, entry: +1,
                        "shadow_clock_constant_plus1")


def build_a5p1_ordshuf(env, anchor: dict, seed: int | None = None) -> dict:
    """PLACEBO-ORDSHUF: uniform draw of n* threshold-passing non-US
    first-release events of the 77 US-anchored months; frozen RNG numpy
    default_rng(20260911), single draw, pool canonically ordered."""
    import numpy as np

    arm_id = "FXNG1-A5-P1-PLACEBO-ORDSHUF"
    family = C.FAMILY_OF_ARM[arm_id]
    meta = _new_meta(arm_id, family)
    meta["rng"] = {"kind": C.PLACEBO_RNG_KIND,
                   "seed": C.PLACEBO_RNG_SEED if seed is None else seed,
                   "draws": 1, "replace": False}
    grid, grid_index = env.grid, env.grid_index
    state = env.order_state
    pool_months = _a5_event_months("ordshuf_pool", state)
    pool: list[dict] = []
    meta["events_total"] = sum(len(v) for v in pool_months.values())
    for mth in sorted(pool_months):
        us_pub = date.fromisoformat(
            state["anchored"][mth]["us"]["publication_date"])
        for ev in pool_months[mth]:
            eco = ev["economy"]
            operative = date.fromisoformat(
                ev["operative_vintaged_available_from"])
            bound = max(operative, us_pub)
            entry = E.first_grid_day_strictly_after(bound, grid_index,
                                                    WINDOW_END)
            if entry is None:
                continue
            meta["events_in_window"] += 1
            vs = env.series_by_eco.get(eco)
            if vs is None:
                meta["events_failed_closed"] += 1
                continue
            try:
                i_print = float(ev["vintaged_first_value"])
                s, _d = s1_seasonal_naive(vs, ev["reference_period"],
                                          i_print, entry)
            except (KeyError, TypeError, ValueError):
                s = None
            if s is None:
                meta["events_failed_closed"] += 1
                continue
            if abs(s) < 0.10:
                meta["events_below_threshold"] += 1
                continue
            pool.append({"ev": ev, "entry": entry,
                         "ssign": 1 if s > 0 else -1,
                         "s1": s})
    pool.sort(key=lambda x: (x["ev"]["publication_date"],
                             x["ev"]["economy"],
                             x["ev"]["reference_period"]))
    n_star = anchor["meta"]["decisions_fired"]
    meta["pool_size"] = len(pool)
    meta["n_star"] = n_star
    if len(pool) < n_star:
        raise ArmBuildError(
            f"ordshuf pool {len(pool)} < n* {n_star} (fail-closed)")
    rng = np.random.default_rng(
        C.PLACEBO_RNG_SEED if seed is None else seed)
    idx = rng.choice(len(pool), size=n_star, replace=False)
    chosen = [pool[i] for i in sorted(int(x) for x in idx)]
    meta["drawn_event_keys"] = [
        f"{c['ev']['economy']}|{c['ev']['publication_date']}"
        for c in chosen]
    records = []
    for c in chosen:
        ev, entry, ssign = c["ev"], c["entry"], c["ssign"]
        pair_signs = funded_pair_sign(ev["economy"], ssign)
        for pair, pdir in pair_signs.items():
            records.append(_record(
                arm_id, family, C.ARM_ROLE[arm_id], ev, pair, pdir,
                entry, grid, grid_index,
                source=f"ordshuf sign(s1)={ssign:+d}"))
    return _finalize(records, meta)


# --------------------------------------------------------------------------- #
# lane A4-P2 (trailing-YoY acceleration; US events 4 pair-decisions)
# --------------------------------------------------------------------------- #

def s2_smooth2(vs, ref_month: str, i_print: float,
               asof: date) -> tuple[float | None, dict]:
    """s2' smoother prior: pi_bar2 = mean of the last two realized YoY
    windows; I_hat = I(m-12) * (1 + pi_bar2).  Quarterly feeds use the
    corresponding observation-step lags (series.neighbour_lag_months)."""
    triple = vs.lag_months(ref_month)
    pair = vs.neighbour_lag_months(ref_month)
    if triple is None or pair is None:
        return None, {"reason": "warmup_obs_months_missing"}
    m_prev, m12, m13 = triple
    m2, m14 = pair
    i_prev = vs.value_asof(m_prev, asof)
    i_12 = vs.value_asof(m12, asof)
    i_13 = vs.value_asof(m13, asof)
    i_2 = vs.value_asof(m2, asof)
    i_14 = vs.value_asof(m14, asof)
    vals = (i_prev, i_12, i_13, i_2, i_14)
    if any(v is None for v in vals) or i_13 == 0.0 or i_14 == 0.0:
        return None, {"reason": "vintage_value_unavailable_asof"}
    pi1 = i_prev / i_13 - 1.0
    pi2 = i_2 / i_14 - 1.0
    pi_bar2 = 0.5 * (pi1 + pi2)
    i_hat = i_12 * (1.0 + pi_bar2)
    if i_hat == 0.0:
        return None, {"reason": "zero_predictor"}
    s2p = 100.0 * (i_print / i_hat - 1.0)
    return s2p, {"reason": "ok", "pi_bar2": pi_bar2, "i_hat": i_hat}


_A4_FORMS = {
    "FXNG1-A4-P2-ANCHOR": s2_trailing_yoy,
    "FXNG1-A4-P2-NEIGH-SMOOTH2": s2_smooth2,
}


def _a4_decisions(arm_id: str, env, threshold: float,
                  direction_override=None, source_tag: str = "s2") -> dict:
    family = C.FAMILY_OF_ARM[arm_id]
    meta = _new_meta(arm_id, family)
    grid, grid_index = env.grid, env.grid_index
    records: list[dict] = []
    events = env.events
    meta["events_total"] = len(events)
    sfunc = _A4_FORMS[arm_id] if direction_override is None \
        else _A4_FORMS["FXNG1-A4-P2-ANCHOR"]
    for ev in events:
        eco = ev["economy"]
        operative = date.fromisoformat(
            ev["operative_vintaged_available_from"])
        entry = E.first_grid_day_strictly_after(operative, grid_index,
                                                WINDOW_END)
        if entry is None:
            continue
        meta["events_in_window"] += 1
        vs = env.series_by_eco.get(eco)
        s = None
        if vs is not None:
            try:
                i_print = float(ev["vintaged_first_value"])
                s, _d = sfunc(vs, ev["reference_period"], i_print, entry)
            except (KeyError, TypeError, ValueError):
                s = None
        if s is None:
            meta["events_failed_closed"] += 1
            continue
        if abs(s) < threshold:
            meta["events_below_threshold"] += 1
            continue
        ssign = 1 if s > 0 else -1
        if direction_override is not None:
            ov = direction_override(ev, entry)
            if ov is None:
                meta["events_failed_closed"] += 1
                continue
            ssign = ov
        pair_signs = (us_event_pair_signs(ssign) if eco == "US"
                      else funded_pair_sign(eco, ssign))
        src = (f"{source_tag}({s:+.6f}pp)"
               if direction_override is None else source_tag)
        for pair, pdir in pair_signs.items():
            records.append(_record(
                arm_id, family, C.ARM_ROLE[arm_id], ev, pair, pdir,
                entry, grid, grid_index, source=src))
    return _finalize(records, meta)


def build_a4p2_anchor(env) -> dict:
    return _a4_decisions("FXNG1-A4-P2-ANCHOR", env, 0.15)


def build_a4p2_smooth2(env) -> dict:
    return _a4_decisions("FXNG1-A4-P2-NEIGH-SMOOTH2", env, 0.15)


def build_a4p2_shadow_clock(env, anchor: dict) -> dict:
    return _remask_book("FXNG1-A4-P2-SHADOW-CLOCK", anchor,
                        lambda rec, ev, entry: +1,
                        "shadow_clock_constant_plus1")


def build_a4p2_sham7d(env, anchor: dict) -> dict:
    """PLACEBO-SHAM7D: +7 calendar-day shift of every fired anchor event
    day; same-pair collisions reshuffle (+7 again, max 4 attempts, else
    drop); off-grid landings snap forward to the next grid day;
    direction = the source event's surprise sign."""
    arm_id = "FXNG1-A4-P2-PLACEBO-SHAM7D"
    family = C.FAMILY_OF_ARM[arm_id]
    grid, grid_index = env.grid, env.grid_index
    meta = _new_meta(arm_id, family)
    meta["source_events"] = len({r["event"]["event_key"]
                                 for r in anchor["decisions"]})
    meta["dropped_collision"] = 0
    meta["snapped_to_grid"] = 0
    # group anchor decisions by event (all pairs share the entry day)
    by_event: dict[str, dict] = {}
    for rec in anchor["decisions"]:
        key = rec["event"]["event_key"]
        by_event.setdefault(key, {"ev": None, "entry": None, "recs": []})
        by_event[key]["entry"] = date.fromisoformat(rec["entry_grid_day"])
        by_event[key]["ev"] = rec
        by_event[key]["recs"].append(rec)
    fired_days_by_pair: dict[str, set[date]] = {}
    for rec in anchor["decisions"]:
        fired_days_by_pair.setdefault(
            rec["pair"], set()).add(
                date.fromisoformat(rec["entry_grid_day"]))
    records: list[dict] = []
    for key, grp in sorted(by_event.items()):
        entry, recs = grp["entry"], grp["recs"]
        shifted = entry
        ok = False
        for _attempt in range(4):
            shifted = shifted + timedelta(days=7)
            if shifted > WINDOW_END:
                break
            j = grid_index.get(shifted)
            while j is None:
                meta["snapped_to_grid"] += 1
                shifted = shifted + timedelta(days=1)
                if shifted > WINDOW_END:
                    break
                j = grid_index.get(shifted)
            if shifted > WINDOW_END or j is None:
                break
            if any(shifted in fired_days_by_pair.get(r["pair"], ())
                   for r in recs):
                continue
            ok = True
            break
        if not ok:
            meta["dropped_collision"] += 1
            continue
        eco = recs[0]["event"]["economy"]
        ev = {"economy": eco,
              "reference_period": recs[0]["event"]["reference_period"],
              "publication_date": recs[0]["event"]["publication_date"]}
        for rec in recs:
            records.append(_record(
                arm_id, family, C.ARM_ROLE[arm_id], ev, rec["pair"],
                rec["direction"], shifted, grid, grid_index,
                source="sham7d stale sign of source event"))
    return _finalize(records, meta)


# --------------------------------------------------------------------------- #
# nominal-exposure controls (CTL-DGS10LEVEL) on the identical fired books
# --------------------------------------------------------------------------- #

def build_dgs10_series(env, n_days_needed: int = 2200) -> Dgs10LevelSeries:
    """The DGS10 level series on an extended weekday grid (>= n_days_needed
    grid days ending at the window end), bound at each grid day.  The
    default covers the full 1842-day S0 grid PLUS the 252-day control
    warmup behind its earliest entry (spot calendars start 2007/2008;
    DGS10 numeric coverage starts 1962)."""
    from research.assets.forex_ng1.spot_series import resolve_all_pairs
    serieses = resolve_all_pairs(os.path.join(
        C.DEFAULT_CONTROL_DIR, "p1_spot/spot_pin_manifest.json"),
        env.provenance["spot"]["data_dir"])
    calendars = [list(s.days) for s in serieses.values()]
    grid_ext = extended_weekday_grid(calendars, WINDOW_END, n_days_needed)
    return Dgs10LevelSeries(env.dgs10_rows, grid_ext)


def _remask_book(arm_id: str, anchor: dict, sign_fn, source_tag: str) -> dict:
    """Rebuild the identical fired anchor book with directions replaced
    by ``sign_fn(record, event, entry)`` (a funded-currency sign; the
    pair map reapplies).  Fails closed when sign_fn returns None (e.g.
    the CTL-DGS10LEVEL state is not provably covered: the pinned vintaged
    DGS10 realtime evidence begins 2018-01-01, so entries whose trailing
    252-grid-day window extends earlier are dropped and disclosed)."""
    family = C.FAMILY_OF_ARM[arm_id]
    meta = _new_meta(arm_id, family)
    meta["book_basis"] = f"identical fired {anchor['arm_id']} book"
    meta["records_dropped_state_unavailable"] = 0
    records: list[dict] = []
    for rec in anchor["decisions"]:
        entry = date.fromisoformat(rec["entry_grid_day"])
        eco = rec["event"]["economy"]
        ev = {"economy": eco,
              "reference_period": rec["event"]["reference_period"],
              "publication_date": rec["event"]["publication_date"]}
        ssign = sign_fn(rec, ev, entry)
        if ssign is None:
            meta["events_failed_closed"] += 1
            meta["records_dropped_state_unavailable"] += 1
            continue
        pair_signs = (us_event_pair_signs(ssign) if eco == "US"
                      else funded_pair_sign(eco, ssign))
        pdir = pair_signs[rec["pair"]]
        records.append(_remask_record(arm_id, family, rec, pdir,
                                      source_tag))
    return _finalize(records, meta)


def _remask_record(arm_id: str, family_id: str, rec: dict, pdir: int,
                   source_tag: str) -> dict:
    out = dict(rec)
    out["decision_id"] = (f"{arm_id}|{rec['event']['economy']}|"
                          f"{rec['event']['publication_date']}|"
                          f"{rec['pair']}")
    out["arm_id"] = arm_id
    out["family_id"] = family_id
    out["arm_role"] = C.ARM_ROLE[arm_id]
    out["direction"] = int(pdir)
    out["signal_source"] = source_tag
    return out


def build_dgs10_control(arm_id: str, env, anchor: dict,
                        dgs10: Dgs10LevelSeries) -> dict:
    """CTL-DGS10LEVEL: identical fired anchor book with the DGS10
    z252-median nominal-level direction (below median -> long funded
    currency vs USD; US events long USD in all four pairs)."""
    def sign_fn(rec, ev, entry):
        s = dgs10.state_sign(entry)
        return None if s is None else s

    return _remask_book(
        arm_id, anchor, sign_fn,
        "ctl_dgs10_level_z252 (below trailing 252-grid-day median)")


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #

def build_arm(arm_id: str, env, anchor_a5: dict | None = None,
              anchor_a4: dict | None = None,
              dgs10: Dgs10LevelSeries | None = None,
              seed: int | None = None) -> dict:
    """Build one arm's decision book.  Controls/shadows/placebos consume
    their family's anchor book (built on demand)."""
    if arm_id == "FXNG1-A5-P1-ANCHOR":
        return build_a5p1_anchor(env)
    if arm_id == "FXNG1-A5-P1-NEIGH-COOPEN":
        return build_a5p1_coopen(env)
    if arm_id == "FXNG1-A5-P1-CTL-V7RECAP":
        return build_a5p1_v7recap(env)
    if arm_id == "FXNG1-A5-P1-CTL-DGS10LEVEL":
        if dgs10 is None:
            dgs10 = build_dgs10_series(env)
        if anchor_a5 is None:
            anchor_a5 = build_a5p1_anchor(env)
        return build_dgs10_control(arm_id, env, anchor_a5, dgs10)
    if arm_id == "FXNG1-A5-P1-SHADOW-CLOCK":
        if anchor_a5 is None:
            anchor_a5 = build_a5p1_anchor(env)
        return build_a5p1_shadow_clock(env, anchor_a5)
    if arm_id == "FXNG1-A5-P1-PLACEBO-ORDSHUF":
        if anchor_a5 is None:
            anchor_a5 = build_a5p1_anchor(env)
        return build_a5p1_ordshuf(env, anchor_a5, seed)
    if arm_id == "FXNG1-A4-P2-ANCHOR":
        return build_a4p2_anchor(env)
    if arm_id == "FXNG1-A4-P2-NEIGH-SMOOTH2":
        return build_a4p2_smooth2(env)
    if arm_id == "FXNG1-A4-P2-CTL-DGS10LEVEL":
        if dgs10 is None:
            dgs10 = build_dgs10_series(env)
        if anchor_a4 is None:
            anchor_a4 = build_a4p2_anchor(env)
        return build_dgs10_control(arm_id, env, anchor_a4, dgs10)
    if arm_id == "FXNG1-A4-P2-SHADOW-CLOCK":
        if anchor_a4 is None:
            anchor_a4 = build_a4p2_anchor(env)
        return build_a4p2_shadow_clock(env, anchor_a4)
    if arm_id == "FXNG1-A4-P2-PLACEBO-SHAM7D":
        if anchor_a4 is None:
            anchor_a4 = build_a4p2_anchor(env)
        return build_a4p2_sham7d(env, anchor_a4)
    raise ArmBuildError(f"unknown arm {arm_id!r}")
