"""Signed-exposure schedule builders for the FOREX-NG1 D2 measurement.

Every builder returns::

    {"name": str, "cells": {"YYYY-MM-DD|PAIR": +1|-1}, "meta": {...}}

with NO PnL anywhere: only which (grid day, pair) cells carry which
signed exposure, plus counts.  Exposure-cell convention (P-12, uniform
across all books): entry grid day i, holding H grid days -> cells
i..i+H-1; overlapping same-pair cells from different events net to the
sign of their sum (collision count disclosed in meta).
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import date, datetime, timezone

from research.assets.forex_ng1.d2.events import (
    eod_month_bound, exposure_days, first_grid_day_strictly_after,
    month_key, order_state,
)
from research.assets.forex_ng1.d2.series import (
    release_sign, s1_seasonal_naive, s2_trailing_yoy,
)

#: Q-6 recent window: the last 24 months of S0 (entry-day basis).
RECENT_WINDOW_START = date(2023, 5, 1)
RECENT_WINDOW_END = date(2025, 4, 30)

PAIR_BY_ECONOMY = {"GB": "GBPUSD", "CA": "USDCAD", "AU": "AUDUSD",
                   "NZ": "NZDUSD"}
FUNDED_PAIRS = ("GBPUSD", "USDCAD", "AUDUSD", "NZDUSD")


class BookError(Exception):
    """Fail-closed book construction error."""


# --------------------------------------------------------------------------- #
# direction laws (frozen by the D1 proposals)
# --------------------------------------------------------------------------- #

def funded_pair_sign(economy: str, ssign: int) -> dict[str, int]:
    """Long the funded currency vs USD on ssign > 0 (CA pair inverts
    because long CAD = short USDCAD)."""
    if economy == "GB":
        return {"GBPUSD": ssign}
    if economy == "CA":
        return {"USDCAD": -ssign}
    if economy == "AU":
        return {"AUDUSD": ssign}
    if economy == "NZ":
        return {"NZDUSD": ssign}
    raise BookError(f"non-funded economy {economy!r}")


def us_event_pair_signs(ssign: int) -> dict[str, int]:
    """US print: long USD in all four pairs on ssign > 0."""
    return {"GBPUSD": -ssign, "USDCAD": ssign,
            "AUDUSD": -ssign, "NZDUSD": -ssign}


def _new_book(name: str, **meta) -> dict:
    return {"name": name, "cells": {}, "meta": dict(meta,
                                                    net_collisions=0)}


def _add_cells(book: dict, days: list[date], pair_signs: dict[str, int]):
    for d in days:
        for pair, sign in pair_signs.items():
            key = f"{d.isoformat()}|{pair}"
            cur = book["cells"].get(key)
            if cur is None:
                book["cells"][key] = sign
            elif cur != sign:
                book["cells"][key] = 1 if cur + sign > 0 else -1
                book["meta"]["net_collisions"] += 1


def _recent(entry: date) -> bool:
    return RECENT_WINDOW_START <= entry <= RECENT_WINDOW_END


# --------------------------------------------------------------------------- #
# lane A4 books (P1 seasonal-naive / P2 trailing-YoY)
# --------------------------------------------------------------------------- #

def build_a4_book(name: str, surprise_form: str, threshold: float,
                  events: list[dict], series_by_eco: dict,
                  grid_days: list[date], grid_index: dict,
                  window_end: date, hold: int = 5) -> dict:
    """The A4 anchor book: all census first releases (no pit_notes),
    PIT-late entry, two-sided threshold, US events 4 pair-decisions."""
    if surprise_form not in ("s1_seasonal_naive", "s2_trailing_yoy"):
        raise BookError(f"unknown surprise form {surprise_form!r}")
    sfunc = (s1_seasonal_naive if surprise_form == "s1_seasonal_naive"
             else s2_trailing_yoy)
    book = _new_book(name, surprise_form=surprise_form,
                     threshold_pp=threshold, hold_grid_days=hold,
                     clock="first grid day strictly after "
                           "operative_vintaged_available_from")
    book["fired_records"] = []      # {"entry": date, "pair_signs": {...}}
    m = book["meta"]
    m["events_total"] = len(events)
    by_eco: Counter = Counter()
    by_eco_fired: Counter = Counter()
    by_eco_failed: Counter = Counter()
    m["events_in_window"] = 0
    m["events_failed_closed"] = 0
    m["pair_decisions_eligible"] = 0
    m["pair_decisions_fired"] = 0
    m["recent_events"] = 0
    m["recent_pair_decisions_eligible"] = 0
    m["recent_pair_decisions_fired"] = 0
    m["recent_by_economy_eligible"] = {}
    recent_by_eco: Counter = Counter()
    for e in events:
        eco = e["economy"]
        operative = date.fromisoformat(e["operative_vintaged_available_from"])
        entry = first_grid_day_strictly_after(operative, grid_index,
                                              window_end)
        if entry is None:
            continue
        m["events_in_window"] += 1
        by_eco[eco] += 1
        n_pairs = 4 if eco == "US" else 1
        m["pair_decisions_eligible"] += n_pairs
        if _recent(entry):
            m["recent_events"] += 1
            m["recent_pair_decisions_eligible"] += n_pairs
            recent_by_eco[eco] += n_pairs
        vs = series_by_eco.get(eco)
        if vs is None:
            m["events_failed_closed"] += 1
            by_eco_failed[eco] += 1
            continue
        try:
            i_print = float(e["vintaged_first_value"])
        except (KeyError, TypeError, ValueError):
            m["events_failed_closed"] += 1
            by_eco_failed[eco] += 1
            continue
        s, _detail = sfunc(vs, e["reference_period"], i_print, entry)
        if s is None or abs(s) < threshold:
            continue
        ssign = 1 if s > 0 else -1
        pair_signs = (us_event_pair_signs(ssign) if eco == "US"
                      else funded_pair_sign(eco, ssign))
        days = exposure_days(entry, hold, grid_days, grid_index)
        _add_cells(book, days, pair_signs)
        book["fired_records"].append({"entry": entry,
                                      "pair_signs": dict(pair_signs)})
        m["pair_decisions_fired"] += n_pairs
        by_eco_fired[eco] += 1
        if _recent(entry):
            m["recent_pair_decisions_fired"] += n_pairs
    m["by_economy_eligible_events"] = dict(by_eco)
    m["by_economy_fired_events"] = dict(by_eco_fired)
    m["by_economy_failed_closed"] = dict(by_eco_failed)
    m["recent_by_economy_eligible"] = dict(recent_by_eco)
    m["active_cells"] = len(book["cells"])
    return book


def build_sham7d_book(source_book: dict,
                      grid_days: list[date], grid_index: dict,
                      window_end: date, hold: int = 5) -> dict:
    """PLACEBO-SHAM7D (V5/V6 house standard): every fired anchor event
    day shifted +7 calendar days; a collision with another FIRED event
    day of the same pair shifts again (+7, max 4 attempts, else drop);
    direction = the SAME surprise sign as the source event.  Consumes
    the anchor book's ``fired_records``.
    """
    from datetime import timedelta
    events_fired = source_book.get("fired_records", [])
    book = _new_book(source_book["name"] + "-SHAM7D",
                     rule="+7 calendar days, collision reshuffle max 4",
                     hold_grid_days=hold)
    m = book["meta"]
    m["source_events"] = len(events_fired)
    m["dropped_collision"] = 0
    m["snapped_to_grid"] = 0
    fired_days_by_pair: dict[str, set[date]] = {}
    for rec in events_fired:
        for pair in rec["pair_signs"]:
            fired_days_by_pair.setdefault(pair, set()).add(rec["entry"])
    for rec in events_fired:
        entry, pair_signs = rec["entry"], dict(rec["pair_signs"])
        shifted = entry
        ok = False
        for _attempt in range(4):
            shifted = shifted + timedelta(days=7)
            if shifted > window_end:
                break
            # snap forward to the next grid day when +7d lands off-grid
            j = grid_index.get(shifted)
            while j is None:
                shifted = shifted + timedelta(days=1)
                if shifted > window_end:
                    break
                j = grid_index.get(shifted)
            if shifted > window_end or j is None:
                break
            if any(shifted in fired_days_by_pair.get(p, ())
                   for p in pair_signs):
                continue
            ok = True
            break
        if not ok:
            m["dropped_collision"] += 1
            continue
        days = exposure_days(shifted, hold, grid_days, grid_index)
        _add_cells(book, days, pair_signs)
    m["active_cells"] = len(book["cells"])
    return book


# --------------------------------------------------------------------------- #
# lane A5 books
# --------------------------------------------------------------------------- #

def build_a5p1_book(name: str, mode: str, state: dict,
                    series_by_eco: dict, grid_days: list[date],
                    grid_index: dict, window_end: date,
                    threshold: float = 0.10, hold: int = 5) -> dict:
    """A5-P1 schedules on the opener's OWN pair.

    mode 'anchor'    : the 50 unique-OF events;
    mode 'coopen'    : anchor + all provable co-earliest prints of the
                       27 no-unique-OF months (NEIGH-COOPEN);
    mode 'v7recap'   : ALL non-US first releases of the 77 US-anchored
                       months (CTL-V7RECAP, the no-order form).
    """
    if mode == "anchor":
        event_months = {m: [of] for m, of in state["unique_of"].items()}
    elif mode == "coopen":
        event_months = {m: [of] for m, of in state["unique_of"].items()}
        for m, coe in state["co_earliest"].items():
            event_months[m] = list(event_months.get(m, [])) + list(coe)
    elif mode == "v7recap":
        event_months = {m: g["nonUS"] for m, g in state["anchored"].items()}
    else:
        raise BookError(f"unknown a5p1 mode {mode!r}")
    book = _new_book(name, mode=mode, threshold_pp=threshold,
                     hold_grid_days=hold,
                     clock="first grid day strictly after "
                           "max(A(e), EOD(P_us_same_month))")
    m = book["meta"]
    m["events_total"] = sum(len(v) for v in event_months.values())
    m["events_in_window"] = 0
    m["events_failed_closed"] = 0
    m["pair_decisions_eligible"] = 0
    m["pair_decisions_fired"] = 0
    m["recent_events"] = 0
    m["recent_pair_decisions_eligible"] = 0
    m["recent_pair_decisions_fired"] = 0
    m["recent_by_economy_eligible"] = {}
    recent_by_eco: Counter = Counter()
    by_eco: Counter = Counter()
    by_eco_fired: Counter = Counter()
    for mth in sorted(event_months):
        us_pub = date.fromisoformat(state["anchored"][mth]["us"]
                                    ["publication_date"])
        for e in event_months[mth]:
            eco = e["economy"]
            operative = date.fromisoformat(
                e["operative_vintaged_available_from"])
            bound = max(operative, us_pub)
            entry = first_grid_day_strictly_after(bound, grid_index,
                                                  window_end)
            if entry is None:
                continue
            m["events_in_window"] += 1
            by_eco[eco] += 1
            m["pair_decisions_eligible"] += 1
            if _recent(entry):
                m["recent_events"] += 1
                m["recent_pair_decisions_eligible"] += 1
                recent_by_eco[eco] += 1
            vs = series_by_eco.get(eco)
            s = None
            if vs is not None:
                try:
                    i_print = float(e["vintaged_first_value"])
                    s, _d = s1_seasonal_naive(vs, e["reference_period"],
                                              i_print, entry)
                except (KeyError, TypeError, ValueError):
                    s = None
            if s is None:
                m["events_failed_closed"] += 1
                continue
            if abs(s) < threshold:
                continue
            ssign = 1 if s > 0 else -1
            days = exposure_days(entry, hold, grid_days, grid_index)
            _add_cells(book, days, funded_pair_sign(eco, ssign))
            m["pair_decisions_fired"] += 1
            by_eco_fired[eco] += 1
            if _recent(entry):
                m["recent_pair_decisions_fired"] += 1
    m["by_economy_eligible_events"] = dict(by_eco)
    m["by_economy_fired_events"] = dict(by_eco_fired)
    m["recent_by_economy_eligible"] = dict(recent_by_eco)
    m["active_cells"] = len(book["cells"])
    return book


def _month_closure_bound(state: dict, mth: str) -> date:
    """max(EOD(P_us), EOD(last follower publication)) for the month."""
    us_pub = date.fromisoformat(state["anchored"][mth]["us"]
                                ["publication_date"])
    last_nonus_pub = max(date.fromisoformat(e["publication_date"])
                         for e in state["anchored"][mth]["nonUS"])
    return max(us_pub, last_nonus_pub)


def build_a5p2_book(name: str, mode: str, state: dict,
                    series_by_eco: dict, grid_days: list[date],
                    grid_index: dict, window_end: date,
                    threshold: float = 0.10, hold: int = 5) -> dict:
    """A5-P2 schedules: the opener's deviation applied to the FOLLOWER
    economies' pairs (anchor) or the no-order both-directions transfer
    (v7recap = CTL-V7RECAP).  Month-order-closed entry."""
    book = _new_book(name, mode=mode, threshold_pp=threshold,
                     hold_grid_days=hold,
                     clock="first grid day strictly after "
                           "max(A(e_src), EOD(P_us), "
                           "EOD(P_last_follower_publication))")
    m = book["meta"]
    m["pair_decisions_total"] = 0
    m["pair_decisions_eligible"] = 0
    m["pair_decisions_fired"] = 0
    m["months_total"] = 0
    m["months_in_window"] = 0
    m["months_gate_passed"] = 0
    m["months_failed_closed"] = 0
    m["recent_pair_decisions_eligible"] = 0
    m["recent_pair_decisions_fired"] = 0
    m["recent_months_eligible"] = 0
    dest_counts: Counter = Counter()
    dest_counts_fired: Counter = Counter()

    def fire(src_event, dest_economies, entry):
        vs = series_by_eco.get(src_event["economy"])
        if vs is None:
            return None
        try:
            i_print = float(src_event["vintaged_first_value"])
        except (KeyError, TypeError, ValueError):
            return None
        s, _d = s1_seasonal_naive(vs, src_event["reference_period"],
                                  i_print, entry)
        if s is None:
            return None
        ssign = 1 if s > 0 else -1
        days = exposure_days(entry, hold, grid_days, grid_index)
        for dest in dest_economies:
            _add_cells(book, days, funded_pair_sign(dest, ssign))
        return abs(s) >= threshold

    if mode == "anchor":
        for mth in sorted(state["unique_of"]):
            of = state["unique_of"][mth]
            followers = state["followers"][mth]
            m["months_total"] += 1
            dests = [f["economy"] for f in followers]
            m["pair_decisions_total"] += len(dests)
            bound = max(date.fromisoformat(
                of["operative_vintaged_available_from"]),
                _month_closure_bound(state, mth))
            entry = first_grid_day_strictly_after(bound, grid_index,
                                                  window_end)
            if entry is None:
                continue
            m["months_in_window"] += 1
            m["pair_decisions_eligible"] += len(dests)
            for d_ in dests:
                dest_counts[d_] += 1
            if _recent(entry):
                m["recent_pair_decisions_eligible"] += len(dests)
                m["recent_months_eligible"] += 1
            fired = fire(of, dests, entry)
            if fired is None:
                m["months_failed_closed"] += 1
                continue
            if fired:
                m["months_gate_passed"] += 1
                m["pair_decisions_fired"] += len(dests)
                for d_ in dests:
                    dest_counts_fired[d_] += 1
                if _recent(entry):
                    m["recent_pair_decisions_fired"] += len(dests)
    elif mode == "v7recap":
        for mth in sorted(state["anchored"]):
            nonus = state["anchored"][mth]["nonUS"]
            ecos = [e["economy"] for e in nonus]
            closure = _month_closure_bound(state, mth)
            for x in nonus:
                dests = [eco for eco in dict.fromkeys(ecos)
                         if eco != x["economy"]]
                if not dests:
                    continue
                m["pair_decisions_total"] += len(dests)
                bound = max(date.fromisoformat(
                    x["operative_vintaged_available_from"]), closure)
                entry = first_grid_day_strictly_after(bound, grid_index,
                                                      window_end)
                if entry is None:
                    continue
                m["pair_decisions_eligible"] += len(dests)
                if _recent(entry):
                    m["recent_pair_decisions_eligible"] += len(dests)
                fired = fire(x, dests, entry)
                if fired is None:
                    m["months_failed_closed"] += 1
                    continue
                if fired:
                    m["pair_decisions_fired"] += len(dests)
                    if _recent(entry):
                        m["recent_pair_decisions_fired"] += len(dests)
    else:
        raise BookError(f"unknown a5p2 mode {mode!r}")
    m["fired_by_destination"] = dict(dest_counts_fired)
    m["eligible_by_destination"] = dict(dest_counts)
    m["active_cells"] = len(book["cells"])
    return book


# --------------------------------------------------------------------------- #
# generic shadow shapes (from the pinned spot closes only)
# --------------------------------------------------------------------------- #

def build_generic_shapes(closes_by_pair: dict, grid_days: list[date],
                         grid_index: dict) -> dict[str, dict]:
    """tsmom20/60, vol28 regime, day-of-week dummies on all funded pairs
    (dense signed schedules; the veto panel's generic block)."""
    out: dict[str, dict] = {}

    def dense(name, value_fn):
        book = _new_book(name)
        n_cells = 0
        for pair in FUNDED_PAIRS:
            closes = closes_by_pair.get(pair)
            if not closes:
                continue
            for i, d in enumerate(grid_days):
                v = value_fn(pair, i, d)
                if v is None:
                    continue
                book["cells"][f"{d.isoformat()}|{pair}"] = v
                n_cells += 1
        book["meta"]["active_cells"] = n_cells
        out[name] = book

    def px(pair, i):
        return closes_by_pair[pair].get(grid_days[i])

    def tsmom(w):
        def fn(pair, i, d):
            c0, c1 = px(pair, i), px(pair, i - w)
            if c0 is None or c1 is None or c1 <= 0:
                return None
            return 1 if c0 > c1 else -1
        return fn

    dense("generic_tsmom20", tsmom(20))
    dense("generic_tsmom60", tsmom(60))

    # vol28 vs its trailing-252 median (population std of daily log rets)
    rets: dict[str, list[float]] = {}
    vols: dict[str, list[float]] = {}
    for pair in FUNDED_PAIRS:
        rs, vs_ = [], []
        for i in range(len(grid_days)):
            c0, c1 = px(pair, i), px(pair, i - 1)
            rs.append(math.log(c0 / c1) if (c0 and c1 and c1 > 0) else None)
        rets[pair] = rs
        for i in range(len(grid_days)):
            window = [r for r in rs[max(0, i - 27):i + 1]
                      if r is not None]
            vs_.append(math.sqrt(sum(r * r for r in window) / len(window))
                       if len(window) == 28 else None)
        vols[pair] = vs_

    def vol_fn(pair, i, d):
        if i < 279:
            return None
        v = vols[pair][i]
        base = [x for x in vols[pair][i - 252:i] if x is not None]
        if v is None or len(base) < 126:
            return None
        s = sorted(base)
        mid = len(s) // 2
        med = s[mid] if len(s) % 2 else 0.5 * (s[mid - 1] + s[mid])
        return 1 if v > med else -1

    dense("generic_vol28_regime", vol_fn)

    names = {0: "generic_dow_mon", 1: "generic_dow_tue",
             2: "generic_dow_wed", 3: "generic_dow_thu",
             4: "generic_dow_fri"}
    for wd, name in names.items():
        dense(name, lambda pair, i, d, _wd=wd: 1 if d.weekday() == _wd
              else 0)
    return out


# --------------------------------------------------------------------------- #
# V7 reaction-direction shadows, rebuilt from FAMILY_FAILURES rows V7
# --------------------------------------------------------------------------- #

def _ny_instant_utc(d: date) -> datetime:
    from zoneinfo import ZoneInfo
    ny = datetime(d.year, d.month, d.day, 16, 0,
                  tzinfo=ZoneInfo("America/New_York"))
    return ny.astimezone(timezone.utc)


def build_v7_spillover_shadows(events: list[dict], series_by_eco: dict,
                               grid_days: list[date], grid_index: dict,
                               window_end: date) -> dict[str, dict]:
    """FXFV7-A4-P1 form (FAMILY_FAILURES): cross-economy RELEASE-SIGN
    spillover continuation on NON-REPORTING pairs, entering at the
    publication instant, GB+CA trigger events, k4/k9 holding.

    Release sign = sign(I_print - I(previous observation as-of)) (the
    realized direction of the print; no consensus data exists).  Entry
    = the first 16:00-NY grid instant at/after the evidenced publication
    instant (V7 'first 16:00-NY >= w1' funded-decision semantics).
    Destination sign convention: + = long the destination currency vs
    USD; |rho| is invariant to any global sign flip, so the polarity
    choice cannot affect any veto verdict.
    """
    out = {}
    for hold, tag in ((4, "k4"), (9, "k9")):
        book = _new_book(f"V7rebuild_spillover_{tag}",
                         spec="FAMILY_FAILURES FXFV7-A4-P1: GB+CA "
                              "release-sign spillover, non-reporting "
                              "pairs, entry at publication",
                         hold_grid_days=hold)
        m = book["meta"]
        m["events_total"] = 0
        m["events_in_window"] = 0
        m["events_failed_closed"] = 0
        for e in events:
            eco = e["economy"]
            if eco not in ("GB", "CA"):
                continue
            m["events_total"] += 1
            pub_t = datetime.strptime(e["publication_instant_utc"],
                                      "%Y-%m-%dT%H:%M:%SZ").replace(
                                          tzinfo=timezone.utc)
            pub_day = date.fromisoformat(e["publication_date"])
            entry = None
            # first grid day whose 16:00-NY instant is at/after the
            # evidenced publication instant (V7 funded-decision rule)
            for k in range(len(grid_days)):
                if grid_days[k] < pub_day:
                    continue
                if grid_days[k] > pub_day or \
                        _ny_instant_utc(grid_days[k]) >= pub_t:
                    entry = grid_days[k]
                    break
            if entry is None or entry > window_end:
                continue
            m["events_in_window"] += 1
            vs = series_by_eco.get(eco)
            if vs is None:
                m["events_failed_closed"] += 1
                continue
            try:
                i_print = float(e["vintaged_first_value"])
            except (KeyError, TypeError, ValueError):
                m["events_failed_closed"] += 1
                continue
            rsign = release_sign(vs, e["reference_period"], i_print, entry)
            if rsign is None or rsign == 0:
                m["events_failed_closed"] += 1
                continue
            dests = [eco2 for eco2 in ("GB", "CA", "AU", "NZ") if eco2 != eco]
            pair_signs = {PAIR_BY_ECONOMY[d2]: rsign for d2 in dests}
            days = exposure_days(entry, hold, grid_days, grid_index)
            _add_cells(book, days, pair_signs)
        m["active_cells"] = len(book["cells"])
        out[book["name"]] = book
    return out


def _quantile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return float("nan")
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def build_v7_leadlag_shadows(closes_by_pair: dict, grid_days: list[date],
                             grid_index: dict, min_obs: int = 60,
                             hold: int = 5) -> dict[str, dict]:
    """FXFV7-A6-P2 form (FAMILY_FAILURES): leader-pair extreme-move
    lead-lag diffusion -- expanding-q80 trigger on the leader's daily
    |return|, same-sign follower entries, hold 5.

    ADAPTATION DISCLOSED: V7's leader was EURUSD, which is OUTSIDE this
    cycle's frozen consumption set; the form is rebuilt as a
    leader-battery over the four funded pairs (each leader triggers the
    other three).  The committed V7 book itself is ALSO carried in the
    veto panel from the V7 rerun evidence, so the battery is an
    additional (never substitutive) reconstruction.
    """
    out: dict[str, dict] = {}
    for leader in FUNDED_PAIRS:
        name = f"V7rebuild_leadlag_q80_{leader}"
        book = _new_book(name, spec="FAMILY_FAILURES FXFV7-A6-P2 form: "
                          "expanding-q80 |return| trigger, followers "
                          f"hold {hold}", hold_grid_days=hold,
                         leader=leader,
                         adaptation="EURUSD leader outside frozen set; "
                                    "leader-battery over funded pairs")
        closes = closes_by_pair.get(leader)
        followers = [p for p in FUNDED_PAIRS if p != leader]
        if closes:
            hist: list[float] = []
            for i in range(1, len(grid_days)):
                c0 = closes.get(grid_days[i])
                c1 = closes.get(grid_days[i - 1])
                if not c0 or not c1 or c1 <= 0:
                    continue
                r = math.log(c0 / c1)
                if len(hist) >= min_obs:
                    thr = _quantile(sorted(hist), 0.80)
                    if abs(r) >= thr:
                        ssign = 1 if r > 0 else -1
                        days = exposure_days(grid_days[i], hold,
                                             grid_days, grid_index)
                        _add_cells(book, days,
                                   {p: ssign for p in followers})
                hist.append(abs(r))
        book["meta"]["active_cells"] = len(book["cells"])
        out[name] = book
    return out


# --------------------------------------------------------------------------- #
# committed ancestor evidence (READ-ONLY inheritance)
# --------------------------------------------------------------------------- #

def load_committed_cells(path: str, sha256_pin: str | None = None
                         ) -> tuple[dict[str, dict], dict]:
    """Load a committed schedule-cells evidence file; verify sha256 when
    a pin is given.  Returns ({name: {"cells": ..., "meta": ...}},
    provenance meta with the file digest)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    digest = hashlib.sha256(raw).hexdigest()
    if sha256_pin is not None and digest != sha256_pin:
        raise BookError(f"committed evidence sha256 drift at {path}: "
                        f"{digest} != {sha256_pin}")
    data = json.loads(raw.decode("utf-8"))
    books = {}
    for name, cells in data.items():
        books[name] = {"name": name, "cells": dict(cells),
                       "meta": {"source": "committed_evidence",
                                "file": path}}
    prov = {"path": path, "sha256": digest, "shapes": sorted(data)}
    return books, prov
