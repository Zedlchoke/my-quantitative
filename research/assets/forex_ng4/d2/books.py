"""Signed-exposure schedule builders for the FOREX-NG4 D2 measurement.

Builds the four ng4 D1 proposal anchors, their D2 identifiability
controls, and the kill-candidate veto shadows as signed exposure-cell
schedules on the frozen 5-pair daily 16:00-NY common grid (1842 days,
2018-04-04..2025-04-30; EURUSD removes no day -- the p0_gate
grid_extension_5pair law):

- FXNG4-A4-P1  seasonal-naive EZ HICP print-deviation on EURUSD,
               s1 = 100*(I_print_v1 / (I(m-1)*I(m-12)/I(m-13)) - 1),
               |s1| >= 0.10 pp, v2-day PIT entry, H = 5;
- FXNG4-A4-P2  trailing-YoY trend-continuation deviation,
               s2 = 100*(I_print_v1 / (I(m-12)*(1+I(m-1)/I(m-13)-1)) - 1),
               |s2| >= 0.15 pp, same clock, H = 5;
- FXNG4-A5-P1  EZ-vs-US restricted revision SIGN-OPPOSITION differential:
               fires the OPPOSED months of the 16 differential months,
               direction = sign(R_EZ), max-v2 entry, H = 5;
- FXNG4-A5-P2  MAGNITUDE-DIFF regime: D = R_EZ - R_US in pp,
               |D| >= 0.02 pp, direction = sign(D), H = 5.

Identifiability controls (schedule-comparison only, NO expectancy):

- CTL-V7RECAP (A4, plan sec1 MANDATORY): ALL 37 restricted events fire,
  direction = sign(s) -- the V7 reaction-direction re-clock test;
- CTL-V7NODIFF (A5, the exact control class that killed FXNG3-A5-P1 at
  rho 1.0): the EZ revision direction alone, differential removed;
- CTL-PPPANCESTRY (A5, kill-candidate #1): the absolute-EZ cumulative
  revision-LEVEL reversion form on the anchor's identical fired book;
- CTL-DGS10LEVEL exact-spec shape (A4): sign = +1 (LONG EURUSD, USD-weak)
  iff the DGS10 level as-of D(e) is below its trailing 252-grid-day
  median, on the anchor's fired days (V8 falsification-by-control
  #14/#15 shape, EURUSD sign law).

Kill-candidate veto shadows (rebuilt from the committed ng1/ng3 D1
proposal identities and the FAMILY_FAILURES V9 row spec):

- FXNG1-A4-P1/P2 print-deviation/acceleration forms on the ng1 census,
  US-event leg EXTENDED to EURUSD (disclosed adaptation: EURUSD was
  outside the ng1 plane; the ng1 US leg fired all four funded pairs,
  and the same USD-direction law on the ng4 plane fires EURUSD -- the
  ng1 lead-lag-rebuild adaptation precedent, in reverse);
- FXNG1-A5-P1 release-order, FXNG3-A5-P1 differential and FXNG3-A5-P2
  transfer shadows rebuilt VERBATIM with the frozen ng1/ng3 builders on
  their own funded pairs (no EURUSD leg exists in those identities;
  their comparison rows against the EURUSD-only anchors are recorded
  honestly as NO_SHARED_PAIRS, never silently dropped);
- FXFV9-A5 PPP-deviation form rebuilt on EURUSD from the FAMILY_FAILURES
  row ("real-rate deviation from evidenced vintaged CPI index levels")
  and the committed V9 P2 clocks census state definition
  (ppp_misalignment_36m), on the ng4 EZ-vs-US vintaged legs.

NO PnL, NO outcome, NO scoring anywhere in this module (D2 law).
"""

from __future__ import annotations

import math
from datetime import date
from statistics import median
from typing import Mapping, Sequence

from research.assets.forex_ng1.d2.books import (  # noqa: F401  (reuse, no edit)
    FUNDED_PAIRS, _add_cells, _new_book,
)
from research.assets.forex_ng1.d2.events import (
    exposure_days, first_grid_day_strictly_after,
)
from research.assets.forex_ng1.d2.series import (
    VintagedSeries, month_lag, s1_seasonal_naive, s2_trailing_yoy,
)
from research.assets.forex_ng2 import revision_series as ng2
from research.assets.forex_ng3.d2 import books as N3

#: The ng4 frozen 5-pair plane (grid_extension_5pair law).
PLANE_PAIRS = tuple(FUNDED_PAIRS) + ("EURUSD",)

#: ng1 economy -> pair map, extended with the ng4 anchor economy.
PAIR_BY_ECONOMY_NG4 = {"GB": "GBPUSD", "CA": "USDCAD", "AU": "AUDUSD",
                       "NZ": "NZDUSD", "EZ": "EURUSD"}

#: Q-6 recent window (last 24 calendar months of S0; the p0c census law
#: matches on v2 availability days).
RECENT_WINDOW_START = date(2023, 5, 1)
RECENT_WINDOW_END = date(2025, 4, 30)
RECENT_MONTH_WINDOW = ("2023-05", "2025-04")

#: Frozen thresholds (ng4 D1 proposal identities; P-15: never moved).
A4P1_THRESHOLD_PP = 0.10
A4P2_THRESHOLD_PP = 0.15
A5_GATE_PP = 0.02
DEFAULT_HOLD = 5

#: PPP-ancestry control band (A5 proposal frozen arm config).
PPP_BAND_PP = 0.02
PPP_MIN_PRIOR = 2

#: D2 frozen bars (dispatch packet forex-ng4-d2-measurement).
NOVELTY_BAR = 0.20
IDENTIFIABILITY_KILL = 0.98

#: Q-6 law for THIS cycle: the p0c census measured the EZ recent window
#: with NO floor frozen (plans/PLAN_forex_ng4.md sec 3 freezes floors
#: only on the A4 print-event total 30 and the A5 differential-month
#: total 12; the ng3 >= 15 recent floor was CA-specific and is never
#: inferred onto EZ).  The recent counts are MEASURED and DISCLOSED,
#: never verdict-bearing.
Q6_FLOOR = None
Q6_VERDICT_LAW = ("MEASURED_NO_FLOOR_FROZEN: plan sec 3 freezes no EZ "
                  "recent-window floor (the ng3 >= 15 floor was "
                  "CA-specific); the count is measured and disclosed, no "
                  "verdict inferred")


class Ng4D2BookError(Exception):
    """Fail-closed ng4 D2 book construction error."""


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _in_recent_window(d: date) -> bool:
    return RECENT_WINDOW_START <= d <= RECENT_WINDOW_END


def _month_in_recent_window(month_key: str) -> bool:
    lo, hi = RECENT_MONTH_WINDOW
    return lo <= month_key <= hi


SURPRISE_FORMS = {
    "s1_seasonal_naive": s1_seasonal_naive,
    "s2_trailing_yoy": s2_trailing_yoy,
}


# --------------------------------------------------------------------------- #
# lane A4: EZ print-deviation anchors + CTL-V7RECAP
# --------------------------------------------------------------------------- #

def build_ng4_a4_book(name: str, mode: str, surprise_form: str,
                      threshold_pp: float,
                      events: Sequence[ng2.RevisionEvent],
                      ez_series: VintagedSeries,
                      grid_days: list[date], grid_index: dict,
                      window_end: date, hold: int = DEFAULT_HOLD) -> dict:
    """A4 signed-exposure book on EURUSD from the EZ restricted stream.

    mode 'anchor'  : fire iff |s| >= ``threshold_pp``; s >= +thr -> LONG
                     EURUSD (+1), s <= -thr -> SHORT (-1) (direction law:
                     an above-continuation EZ print reprices the ECB path
                     hawkish).
    mode 'v7recap' : CTL-V7RECAP -- ALL in-window events fire regardless
                     of |s|, direction = sign(s) (the sign-of-release
                     reaction form, magnitude removed).

    Clock (proposal identity): A(e) = EOD(v2.realtime_start); D(e) = the
    first common-grid day STRICTLY after that date.  Predictor inputs
    I(m-1), I(m-12), I(m-13) are vintaged as-of D(e) (declared PIT
    asymmetry: the frozen v1 print vs the D(e)-vintage baseline).
    """
    if mode not in ("anchor", "v7recap"):
        raise Ng4D2BookError(f"unknown ng4 A4 mode {mode!r}")
    if surprise_form not in SURPRISE_FORMS:
        raise Ng4D2BookError(f"unknown surprise form {surprise_form!r}")
    sfunc = SURPRISE_FORMS[surprise_form]
    book = _new_book(name, mode=mode, surprise_form=surprise_form,
                     threshold_pp=(None if mode == "v7recap"
                                   else threshold_pp),
                     hold_grid_days=hold,
                     clock="first grid day strictly after "
                           "EOD(v2.realtime_start)")
    m = book["meta"]
    m["events_total"] = len(events)
    m["events_in_window"] = 0
    m["events_failed_closed"] = 0
    m["below_threshold"] = 0
    m["fired_events"] = 0
    m["dropped_tail_entries"] = 0
    m["recent_events_v2_basis"] = 0
    m["recent_entries_basis"] = 0
    m["recent_fired_v2_basis"] = 0
    m["fired_v2_year_counts"] = {}
    book["fired_records"] = []
    for e in sorted(events, key=lambda x: (x.v2_realtime_start,
                                           x.obs_month)):
        bound = date.fromisoformat(e.v2_realtime_start)
        recent_v2 = _in_recent_window(bound)
        if recent_v2:
            m["recent_events_v2_basis"] += 1
        entry = first_grid_day_strictly_after(bound, grid_index, window_end)
        if entry is None:
            m["dropped_tail_entries"] += 1
            continue
        m["events_in_window"] += 1
        if _in_recent_window(entry):
            m["recent_entries_basis"] += 1
        try:
            i_print = float(e.v1_value)
        except (TypeError, ValueError):
            m["events_failed_closed"] += 1
            continue
        s, _detail = sfunc(ez_series, e.month_key, i_print, entry)
        if s is None or s == 0.0:
            m["events_failed_closed"] += 1
            continue
        if mode == "anchor" and abs(s) < threshold_pp:
            m["below_threshold"] += 1
            continue
        sign = 1 if s > 0 else -1
        days = exposure_days(entry, hold, grid_days, grid_index)
        _add_cells(book, days, {"EURUSD": sign})
        book["fired_records"].append(
            {"entry": entry, "sign": sign, "month": e.month_key,
             "surprise_pp": s, "avail_bound": bound})
        m["fired_events"] += 1
        yr = e.v2_realtime_start[:4]
        m["fired_v2_year_counts"][yr] = (
            m["fired_v2_year_counts"].get(yr, 0) + 1)
        if recent_v2:
            m["recent_fired_v2_basis"] += 1
    m["active_cells"] = len(book["cells"])
    return book


# --------------------------------------------------------------------------- #
# lane A5: EZ-vs-US restricted revision differential anchors + controls
# --------------------------------------------------------------------------- #

A5_MODES = ("anchor_p1", "v7nodiff_p1", "anchor_p2", "v7nodiff_p2")


def build_ng4_a5_book(name: str, mode: str,
                      months: Sequence[str],
                      lookup: Mapping[tuple[str, str], ng2.RevisionEvent],
                      grid_days: list[date], grid_index: dict,
                      window_end: date, gate_pp: float = A5_GATE_PP,
                      hold: int = DEFAULT_HOLD) -> dict:
    """A5 signed-exposure book on EURUSD over the EZ-US differential months.

    ``months``: the census join months (obs-month keys).  ``lookup``:
    (economy, month) -> restricted RevisionEvent for EZ and US.

    mode 'anchor_p1'    : fire iff OPPOSED (sign(R_EZ) != sign(R_US)),
                          direction = sign(R_EZ); NO magnitude gate.
    mode 'v7nodiff_p1'  : CTL-V7NODIFF (P1 shape) -- ALL months fire,
                          direction = sign(R_EZ); the US sign is never
                          read (the ng3-A5-P1 kill class).
    mode 'anchor_p2'    : fire iff |D| >= gate with D = R_EZ - R_US in
                          pp, direction = sign(D).
    mode 'v7nodiff_p2'  : CTL-V7NODIFF (P2 shape) -- identical months
                          and max-v2 clock, direction = sign(R_EZ) gated
                          on |R_EZ| >= gate; the US leg is never read.

    Clock (proposal identity): A(m) = EOD(max(v2_EZ, v2_US)); D(e) = the
    first in-window grid day strictly after A(m) (the front convention
    for pre-window A(m) is the first grid day 2018-04-04, exactly what
    the strictly-after clock yields).
    """
    if mode not in A5_MODES:
        raise Ng4D2BookError(f"unknown ng4 A5 mode {mode!r}")
    book = _new_book(name, mode=mode, gate_pp=gate_pp, hold_grid_days=hold,
                     clock="first grid day strictly after "
                           "EOD(max(v2_EZ, v2_US))")
    m = book["meta"]
    m["months_total"] = len(months)
    m["months_in_window"] = 0
    m["months_failed_closed"] = 0
    m["months_gate_passed"] = 0
    m["months_gate_failed"] = 0
    m["months_opposed"] = 0
    m["months_agreed"] = 0
    m["dropped_tail_entries"] = 0
    m["recent_months_obs_basis"] = 0
    m["recent_months_avail_basis"] = 0
    m["recent_months_entry_basis"] = 0
    m["recent_months_fired_obs_basis"] = 0
    book["fired_records"] = []
    for mth in sorted(months):
        if _month_in_recent_window(mth):
            m["recent_months_obs_basis"] += 1
        ev_ez = lookup.get(("EZ", mth))
        ev_us = lookup.get(("US", mth))
        if ev_ez is None or ev_us is None:
            m["months_failed_closed"] += 1
            continue
        r_ez = 100.0 * ev_ez.ratio
        r_us = 100.0 * ev_us.ratio
        if (r_ez > 0) != (r_us > 0):
            m["months_opposed"] += 1
        else:
            m["months_agreed"] += 1
        bound = max(date.fromisoformat(ev_ez.v2_realtime_start),
                    date.fromisoformat(ev_us.v2_realtime_start))
        if _in_recent_window(bound):
            m["recent_months_avail_basis"] += 1
        entry = first_grid_day_strictly_after(bound, grid_index, window_end)
        if entry is None:
            m["dropped_tail_entries"] += 1
            continue
        m["months_in_window"] += 1
        if _in_recent_window(entry):
            m["recent_months_entry_basis"] += 1
        if mode == "anchor_p1":
            if (r_ez > 0) == (r_us > 0):
                continue                      # AGREED: no position
            value, gate_ok, sign = r_ez, True, (1 if r_ez > 0 else -1)
        elif mode == "v7nodiff_p1":
            value, gate_ok, sign = r_ez, True, (1 if r_ez > 0 else -1)
        elif mode == "anchor_p2":
            value = r_ez - r_us
            gate_ok = abs(value) >= gate_pp
            sign = 1 if value > 0 else -1
        else:                                  # v7nodiff_p2
            value = r_ez
            gate_ok = abs(value) >= gate_pp
            sign = 1 if value > 0 else -1
        if not gate_ok:
            m["months_gate_failed"] += 1
            continue
        m["months_gate_passed"] += 1
        days = exposure_days(entry, hold, grid_days, grid_index)
        _add_cells(book, days, {"EURUSD": sign})
        book["fired_records"].append(
            {"entry": entry, "sign": sign, "month": mth,
             "r_ez_pp": r_ez, "r_us_pp": r_us, "avail_bound": bound})
        if _month_in_recent_window(mth):
            m["recent_months_fired_obs_basis"] += 1
    m["active_cells"] = len(book["cells"])
    return book


def build_ng4_ppp_ancestry_control(name: str, source_book: dict,
                                   ez_events: Sequence[
                                       ng2.RevisionEvent],
                                   grid_days: list[date], grid_index: dict,
                                   hold: int = DEFAULT_HOLD,
                                   band_pp: float = PPP_BAND_PP,
                                   min_prior: int = PPP_MIN_PRIOR
                                   ) -> dict:
    """CTL-PPPANCESTRY: the absolute-EZ cumulative revision-LEVEL
    reversion form on the anchor's IDENTICAL fired book.

    S(m) = cumulative sum of R_EZ (pp) over ALL EZ restricted events
    whose v2 availability day <= A(m) (the US leg is NEVER read);
    direction = +1 (LONG EURUSD) iff S(m) < median{S at those prior EZ
    restricted events} (EUR cumulatively under-revised its price path =>
    PPP-cheap => long), -1 iff above; no-position band
    |S(m) - median| < band; fail-closed no position when fewer than
    ``min_prior`` prior EZ events are PIT-readable at A(m).  Identical
    fired event days, clock, H and 1-unit magnitudes as the anchor (the
    V9 PPP-deviation re-clock kill shape, kill-candidate #1).
    """
    ordered = sorted(ez_events, key=lambda e: (e.v2_realtime_start,
                                               e.obs_month))
    cum: list[tuple[date, float]] = []
    run = 0.0
    for e in ordered:
        run += 100.0 * e.ratio
        cum.append((date.fromisoformat(e.v2_realtime_start), run))
    book = _new_book(
        name, spec="CTL-PPPANCESTRY: S(m) = cumsum R_EZ over EZ restricted "
                   "events PIT-readable at A(m); +1 long EURUSD iff S(m) < "
                   "median of prior S values (reversion), band "
                   f"{band_pp} pp, fail-closed < {min_prior} priors",
        hold_grid_days=hold)
    m = book["meta"]
    m["source_fired_events"] = len(source_book.get("fired_records", []))
    m["dropped_insufficient_priors"] = 0
    m["dropped_no_position_band"] = 0
    m["fired_events"] = 0
    m["sign_counts"] = {1: 0, -1: 0}
    for rec in source_book.get("fired_records", []):
        bound = rec["avail_bound"]
        entry = rec["entry"]
        prior = [s for v2, s in cum if v2 <= bound]
        if len(prior) < min_prior:
            m["dropped_insufficient_priors"] += 1
            continue
        s_now = prior[-1]
        med = median(prior)
        if abs(s_now - med) < band_pp:
            m["dropped_no_position_band"] += 1
            continue
        sign = 1 if s_now < med else -1
        m["sign_counts"][sign] += 1
        m["fired_events"] += 1
        days = exposure_days(entry, hold, grid_days, grid_index)
        _add_cells(book, days, {"EURUSD": sign})
    m["active_cells"] = len(book["cells"])
    return book


# --------------------------------------------------------------------------- #
# CTL-DGS10LEVEL exact-spec shape on EURUSD (A4 nominal separability)
# --------------------------------------------------------------------------- #

def build_ng4_dgs10_z252_book(name: str, source_book: dict,
                              levels: Mapping[date, float | None],
                              grid_days: list[date], grid_index: dict,
                              hold: int = DEFAULT_HOLD,
                              min_history: int = 126,
                              trailing: int = 252) -> dict:
    """The exact-spec CTL-DGS10LEVEL exposure on the A4 anchor's fired
    days, ng4 sign law: sign = +1 (LONG EURUSD, USD-weak) iff the DGS10
    level as-of D(e) is below its trailing-252-grid-day median, else -1.
    Entries with insufficient trailing history or an unreadable level
    are dropped and disclosed (fail-closed, never guessed).
    """
    book = _new_book(name, spec="CTL-DGS10LEVEL exact-spec (ng4): sign = "
                     "+1 (long EURUSD) iff DGS10 level as-of D(e) < "
                     f"trailing {trailing}-grid-day median else -1",
                     hold_grid_days=hold)
    m = book["meta"]
    m["source_fired_events"] = len(source_book.get("fired_records", []))
    m["dropped_insufficient_history"] = 0
    m["sign_counts"] = {1: 0, -1: 0}
    for rec in source_book.get("fired_records", []):
        entry = rec["entry"]
        i = grid_index[entry]
        window = [levels.get(grid_days[j])
                  for j in range(max(0, i - trailing), i)]
        hist = [v for v in window if v is not None]
        level = levels.get(entry)
        if level is None or len(hist) < min_history:
            m["dropped_insufficient_history"] += 1
            continue
        sign = 1 if level < median(hist) else -1
        m["sign_counts"][sign] += 1
        days = exposure_days(entry, hold, grid_days, grid_index)
        _add_cells(book, days, {"EURUSD": sign})
    m["active_cells"] = len(book["cells"])
    return book


# --------------------------------------------------------------------------- #
# ng1 A4 kill-candidate shadows (US-event leg EXTENDED to EURUSD)
# --------------------------------------------------------------------------- #

def _ng1_us_event_pair_signs_with_eurusd(ssign: int) -> dict[str, int]:
    """The ng1 US-event direction law on the ng4 5-pair plane: long USD
    on ssign > 0 (EURUSD inverts: long USD = short EURUSD)."""
    return {"GBPUSD": -ssign, "USDCAD": ssign, "AUDUSD": -ssign,
            "NZDUSD": -ssign, "EURUSD": -ssign}


def build_ng1_a4_kill_shadow(name: str, surprise_form: str,
                             threshold: float, events: list[dict],
                             series_by_eco: dict, grid_days: list[date],
                             grid_index: dict, window_end: date,
                             hold: int = DEFAULT_HOLD) -> dict:
    """The dead ng1 A4 print-deviation form (P1 s1 seasonal-naive /
    P2 s2 trailing-YoY) rebuilt from the committed ng1 D1 proposal
    identity on the ng1 census, with the US-event leg EXTENDED to
    EURUSD (ADAPTATION DISCLOSED: EURUSD was outside the ng1 plane; the
    ng1 US events fired all four funded pairs and the identical
    USD-direction law fires EURUSD on the ng4 plane -- the mirror of the
    ng1 lead-lag-rebuild plane adaptation).  Non-US events fire their
    own funded pair unchanged (no EURUSD leg exists for them; their
    cells are inert in any EURUSD-restricted comparison)."""
    if surprise_form not in SURPRISE_FORMS:
        raise Ng4D2BookError(f"unknown surprise form {surprise_form!r}")
    sfunc = SURPRISE_FORMS[surprise_form]
    book = _new_book(name, surprise_form=surprise_form,
                     threshold_pp=threshold, hold_grid_days=hold,
                     clock="ng1 identity: first grid day strictly after "
                           "operative_vintaged_available_from",
                     adaptation="ng1 A4 form, US-event leg extended to "
                                "EURUSD (ng4 plane; disclosed)")
    m = book["meta"]
    m["events_total"] = len(events)
    m["events_in_window"] = 0
    m["events_failed_closed"] = 0
    m["pair_decisions_fired"] = 0
    m["eurusd_cells_fired"] = 0
    for e in events:
        eco = e["economy"]
        operative = date.fromisoformat(e["operative_vintaged_available_from"])
        entry = first_grid_day_strictly_after(operative, grid_index,
                                              window_end)
        if entry is None:
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
        s, _detail = sfunc(vs, e["reference_period"], i_print, entry)
        if s is None or abs(s) < threshold:
            continue
        ssign = 1 if s > 0 else -1
        if eco == "US":
            pair_signs = _ng1_us_event_pair_signs_with_eurusd(ssign)
            n_pairs = len(pair_signs)
        else:
            pair_signs = _funded_pair_sign(eco, ssign)
            n_pairs = 1
        days = exposure_days(entry, hold, grid_days, grid_index)
        _add_cells(book, days, pair_signs)
        m["pair_decisions_fired"] += n_pairs
        if "EURUSD" in pair_signs:
            m["eurusd_cells_fired"] += 1
    m["active_cells"] = len(book["cells"])
    return book


def _funded_pair_sign(economy: str, ssign: int) -> dict[str, int]:
    """ng1 direction law for non-US economies (CA inverts)."""
    if economy == "GB":
        return {"GBPUSD": ssign}
    if economy == "CA":
        return {"USDCAD": -ssign}
    if economy == "AU":
        return {"AUDUSD": ssign}
    if economy == "NZ":
        return {"NZDUSD": ssign}
    raise Ng4D2BookError(f"non-funded economy {economy!r}")


# --------------------------------------------------------------------------- #
# FXFV9-A5 PPP-deviation form rebuilt on EURUSD (kill-candidate #1)
# --------------------------------------------------------------------------- #

def _v1_day(series: VintagedSeries, month_key: str) -> date | None:
    """The first vintage day publishing obs ``month_key`` (date-only)."""
    starts = [r["rs"] for r in series.rows
              if r["obs"] == f"{month_key}-01" and r["value"] is not None]
    return min(starts) if starts else None


def _latest_common_obs_month(series: VintagedSeries, asof: date
                             ) -> str | None:
    """The latest obs month with a value in force at ``asof``."""
    best = None
    for r in series.rows:
        if r["value"] is None or r["rs"] > asof or asof > r["re"]:
            continue
        if best is None or r["obs"] > best:
            best = r["obs"]
    return best[:7] if best else None


def _close_on_or_before(closes: Mapping[date, float], target: date
                        ) -> float | None:
    """The last available close at or before ``target`` (None if none)."""
    best_val, best_day = None, None
    for d, v in closes.items():
        if d <= target and (best_day is None or d > best_day):
            best_day, best_val = d, v
    return best_val


def build_v9_ppp_shadow(name: str, eurusd_closes: Mapping[date, float],
                        ez_series: VintagedSeries, us_series: VintagedSeries,
                        grid_days: list[date], grid_index: dict,
                        window_end: date, lookback_months: int = 36,
                        hold: int = 1) -> dict:
    """The FXFV9-A5 PPP-deviation form rebuilt on EURUSD (EZ-vs-US legs).

    Form spec (FAMILY_FAILURES row FXFV9-A5-P1/P2 + the committed V9 P2
    clocks census ``ppp_misalignment_36m``):

    - state  : misalignment = log(S[t]/S[t-36m]) - cumulative relative
               CPI, where the relative-CPI term is the sum of the last
               ``lookback_months`` monthly y/y log steps EZ minus US,
               every value read within the SINGLE as-of vintage in force
               at the decision instant (rebase-safe per the V8 AX2-C3
               class);
    - clock  : the first 16:00-NY grid day STRICTLY after the LATER
               leg's first-vintage availability day of the binding CPI
               month (obs month m = decision month - 1, both legs
               monthly on the ng4 archives);
    - law    : traded TOWARD reversion (misalignment > 0 => EURUSD
               above its PPP-implied path => SHORT; < 0 => LONG);
    - ADAPTATION DISCLOSED: the V9 books were funded-pair monthly state
      maps (committed cells keyed month|pair); FAMILY_FAILURES carries
      no threshold/hold spec, so the ng4 rebuild is the THRESHOLD-FREE
      monthly reversion form with one exposure cell per decision month
      on the ng4 anchor pair -- a form-level rebuild of the LEVEL
      misalignment axis, never a claim about the dead V9 books' exact
      parameters.

    Fail-closed: a decision month whose binding CPI month, 36-month CPI
    window or 36-month spot leg is unreadable contributes NO cell.
    """
    book = _new_book(name, spec="FXFV9-A5 PPP-deviation form on EURUSD: "
                     "misalignment_36m = log(S[t]/S[t-36m]) - sum(y/y log "
                     "steps EZ - US, single as-of vintage), reversion-"
                     "traded, monthly decision clock after the later "
                     "leg's v1 availability",
                     hold_grid_days=hold,
                     adaptation="form-level rebuild on the ng4 EZ-vs-US "
                                "legs at EURUSD (FAMILY_FAILURES row spec; "
                                "no threshold in the spec -> threshold-"
                                "free reversion form)")
    m = book["meta"]
    m["months_considered"] = 0
    m["months_pre_window_skipped"] = 0
    m["months_post_window_skipped"] = 0
    m["months_failed_closed"] = 0
    m["months_fired"] = 0
    m["sign_counts"] = {1: 0, -1: 0}
    grid_start = grid_days[0]
    # decision months: every calendar month whose binding CPI month
    # (previous month) exists on BOTH archives with a v1 day
    binding_months = sorted(
        {r["obs"][:7] for r in ez_series.rows} &
        {r["obs"][:7] for r in us_series.rows})
    for bm in binding_months:
        v1_ez = _v1_day(ez_series, bm)
        v1_us = _v1_day(us_series, bm)
        if v1_ez is None or v1_us is None:
            continue
        m["months_considered"] += 1
        bound = max(v1_ez, v1_us)
        if bound < grid_start:
            # a decision whose clock fires BEFORE the frozen window is a
            # pre-window decision (never stacked onto the window start)
            m["months_pre_window_skipped"] += 1
            continue
        entry = first_grid_day_strictly_after(bound, grid_index, window_end)
        if entry is None:
            m["months_post_window_skipped"] += 1
            continue
        # state at entry: latest obs month carried by BOTH legs as-of
        k_ez = _latest_common_obs_month(ez_series, entry)
        k_us = _latest_common_obs_month(us_series, entry)
        if k_ez is None or k_us is None:
            m["months_failed_closed"] += 1
            continue
        k = min(k_ez, k_us)
        k_start = month_lag(k, -lookback_months)
        rel_cpi = 0.0
        ok = True
        j = k_start
        for _ in range(lookback_months):
            i_ez0 = ez_series.value_asof(j, entry)
            i_ez1 = ez_series.value_asof(month_lag(j, -12), entry)
            i_us0 = us_series.value_asof(j, entry)
            i_us1 = us_series.value_asof(month_lag(j, -12), entry)
            if None in (i_ez0, i_ez1, i_us0, i_us1) or min(
                    i_ez0, i_ez1, i_us0, i_us1) <= 0.0:
                ok = False
                break
            rel_cpi += (math.log(i_ez0 / i_ez1) - math.log(i_us0 / i_us1))
            j = month_lag(j, 1)
        if not ok:
            m["months_failed_closed"] += 1
            continue
        spot_now = eurusd_closes.get(entry)
        target = date.fromisoformat(
            month_lag(entry.isoformat(), -lookback_months) + "-01")
        spot_then = _close_on_or_before(eurusd_closes, target)
        if spot_now is None or spot_then is None or spot_then <= 0.0:
            m["months_failed_closed"] += 1
            continue
        mis = math.log(spot_now / spot_then) - rel_cpi
        if mis == 0.0:
            m["months_failed_closed"] += 1
            continue
        sign = 1 if mis < 0 else -1          # reversion
        m["sign_counts"][sign] += 1
        m["months_fired"] += 1
        days = exposure_days(entry, hold, grid_days, grid_index)
        _add_cells(book, days, {"EURUSD": sign})
    m["active_cells"] = len(book["cells"])
    return book


# --------------------------------------------------------------------------- #
# V7 rebuilds + generics on the 5-pair plane (ng4 adaptations, disclosed)
# --------------------------------------------------------------------------- #

def build_v7_spillover_shadows_5pair(events: list[dict],
                                     series_by_eco: dict,
                                     grid_days: list[date], grid_index: dict,
                                     window_end: date
                                     ) -> dict[str, dict]:
    """FXFV7-A4-P1 spillover form on the 5-pair plane.

    Identical law to the ng1 rebuild (GB+CA release-sign triggers,
    non-reporting destinations, entry at the publication instant,
    k4/k9 holds) with destinations EXTENDED to EURUSD: EURUSD was a
    destination pair of the TRUE V7 7-pair plane (the committed
    FXFV7-A4-P1_anchor_k4 book carries EURUSD cells), so the ng4 rebuild
    is MORE faithful than the ng1 4-pair adaptation -- adaptation
    disclosed.  |rho| is invariant to the polarity choice.
    """
    from research.assets.forex_ng1.d2.books import _ny_instant_utc
    from research.assets.forex_ng1.d2.series import release_sign
    from datetime import datetime, timezone
    out = {}
    for hold, tag in ((4, "k4"), (9, "k9")):
        book = _new_book(f"V7rebuild_spillover_{tag}_eurusd",
                         spec="FAMILY_FAILURES FXFV7-A4-P1: GB+CA "
                              "release-sign spillover, non-reporting "
                              "pairs incl. EURUSD (V7 7-pair plane), "
                              "entry at publication",
                         hold_grid_days=hold,
                         adaptation="ng1 rebuild law with EURUSD "
                                    "restored as a destination (the "
                                    "true V7 plane)")
        m = book["meta"]
        m["events_total"] = 0
        m["events_in_window"] = 0
        m["events_failed_closed"] = 0
        for e in events:
            eco = e["economy"]
            if eco not in ("GB", "CA"):
                continue
            m["events_total"] += 1
            pub_t = datetime.strptime(
                e["publication_instant_utc"],
                "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            pub_day = date.fromisoformat(e["publication_date"])
            entry = None
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
            dests = [eco2 for eco2 in ("GB", "CA", "AU", "NZ", "EZ")
                     if eco2 != eco]
            pair_signs = {PAIR_BY_ECONOMY_NG4[d2]: rsign for d2 in dests}
            days = exposure_days(entry, hold, grid_days, grid_index)
            _add_cells(book, days, pair_signs)
        m["active_cells"] = len(book["cells"])
        out[book["name"]] = book
    return out


def build_v7_leadlag_shadows_5pair(closes_by_pair: dict,
                                   grid_days: list[date], grid_index: dict,
                                   min_obs: int = 60, hold: int = 5
                                   ) -> dict[str, dict]:
    """FXFV7-A6-P2 lead-lag form on the 5-pair plane: expanding-q80
    |return| trigger on the leader, same-sign followers.

    The ng1 adaptation ran a leader battery over the four funded pairs
    because EURUSD was outside its consumption set; the ng4 plane
    INCLUDES EURUSD, so the battery extends to all five -- restoring the
    TRUE V7 form (EURUSD as leader; the leader itself never trades, so
    that book's cells sit on the funded followers only) alongside the
    four funded-leader books whose follower sets now include EURUSD.
    Adaptation disclosed; same formula as the ng1 rebuild verbatim.
    """
    def _quantile(sorted_vals: list[float], q: float) -> float:
        if not sorted_vals:
            return float("nan")
        pos = q * (len(sorted_vals) - 1)
        lo = int(math.floor(pos))
        hi = min(lo + 1, len(sorted_vals) - 1)
        frac = pos - lo
        return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac

    out: dict[str, dict] = {}
    for leader in PLANE_PAIRS:
        name = f"V7rebuild_leadlag_q80_{leader}"
        book = _new_book(name, spec="FAMILY_FAILURES FXFV7-A6-P2 form: "
                          "expanding-q80 |return| trigger, followers "
                          f"hold {hold}", hold_grid_days=hold, leader=leader,
                         adaptation="ng1 leader battery extended to the "
                                    "5-pair ng4 plane (EURUSD leader = "
                                    "the TRUE V7 form)")
        closes = closes_by_pair.get(leader)
        followers = [p for p in PLANE_PAIRS if p != leader]
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
                        _add_cells(book, days, {p: ssign for p in followers})
                hist.append(abs(r))
        book["meta"]["active_cells"] = len(book["cells"])
        out[name] = book
    return out


def build_generic_shapes_5pair(closes_by_pair: dict, grid_days: list[date],
                               grid_index: dict) -> dict[str, dict]:
    """tsmom20/60, vol28 regime, day-of-week dummies over the 5-pair
    plane (formulas identical to the ng1 generics; pair set extended
    with EURUSD -- adaptation disclosed)."""
    out: dict[str, dict] = {}

    def dense(name, value_fn):
        book = _new_book(name)
        n_cells = 0
        for pair in PLANE_PAIRS:
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

    rets: dict[str, list[float]] = {}
    vols: dict[str, list[float]] = {}
    for pair in PLANE_PAIRS:
        rs, vs_ = [], []
        for i in range(len(grid_days)):
            c0, c1 = px(pair, i), px(pair, i - 1)
            rs.append(math.log(c0 / c1) if (c0 and c1 and c1 > 0) else None)
        rets[pair] = rs
        for i in range(len(grid_days)):
            window = [r for r in rs[max(0, i - 27):i + 1] if r is not None]
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
# D2 verdict helpers (frozen laws; runner + tests)
# --------------------------------------------------------------------------- #

def evaluate_q6_no_floor(measured: int, basis: str) -> dict:
    """The ng4 Q-6 row: measured and disclosed, floor null -- the plan
    freezes NO EZ recent-window floor (plan sec 3 verified at this
    checkout; the ng3 >= 15 floor was CA-specific and is never
    inferred).  A verdict is never invented from a null floor."""
    return {"measured": measured, "floor": Q6_FLOOR, "margin": None,
            "verdict": "MEASURED_NO_FLOOR_FROZEN", "basis": basis,
            "law": Q6_VERDICT_LAW}


def proposal_verdict(*, novelty_max_abs_rho, empty_book: bool = False,
                     identifiability_kill=None,
                     kill_control_name: str = "",
                     novelty_bar: float = NOVELTY_BAR) -> str:
    """The per-proposal ng4 D2 verdict (frozen rule order).

    1. EMPTY BOOK (the anchor fires 0 in-window events; the D1
       proposals' vacuous-book law: dies cheap) -> INELIGIBLE_FAIL_CLOSED;
    2. novelty unmeasurable -> INELIGIBLE_FAIL_CLOSED (a number that
       cannot be measured is never inferred PASS);
    3. ancestry rho over the 0.20 bar -> VETO(margin) (P-2);
    4. identifiability kill (the dispatch-named control reproduces the
       anchor at |rho| >= 0.98) -> VETO;
    else ELIGIBLE.  Q-6 carries no verdict axis this cycle (no floor
    frozen; the thin recent structure is disclosed for the S rubric).
    """
    if empty_book:
        return ("INELIGIBLE_FAIL_CLOSED(EMPTY BOOK: the anchor fires 0 "
                "in-window events -- the D1 vacuous-book law, dies cheap; "
                "no threshold moves P-15)")
    if novelty_max_abs_rho is None:
        return ("INELIGIBLE_FAIL_CLOSED(novelty unmeasurable: pooled "
                "|rho| could not be computed on the frozen representation)")
    if novelty_max_abs_rho > novelty_bar:
        return (f"VETO(ANCESTRY_VETO rho={round(novelty_max_abs_rho, 4)} "
                f"margin={round(novelty_bar - novelty_max_abs_rho, 4)})")
    if identifiability_kill is not None and \
            identifiability_kill >= IDENTIFIABILITY_KILL:
        return (f"VETO(IDENTIFIABILITY_KILL {kill_control_name or 'control'}"
                f" rho={round(identifiability_kill, 4)} >= "
                f"{IDENTIFIABILITY_KILL}: the control reproduces the "
                "anchor schedule; Q-11 control null INVALID)")
    return "ELIGIBLE"


def q11_null_validity(rho: float | None, control: str,
                      anchor_signs: dict, control_signs: dict,
                      verdict: str | None = None) -> str:
    """Q-11 disclosure for an identifiability control comparison."""
    if rho is None:
        return ("UNMEASURABLE (Spearman undefined: a constant vector -- "
                f"anchor signs {anchor_signs}, control signs "
                f"{control_signs}, verdict {verdict}): the D2 "
                "identifiability kill CANNOT fire on an unmeasurable rho "
                "(NOT_RUN semantics, never an inferred PASS); the "
                "scored-phase falsification rule (>= 0.5x same-sign "
                "per-trade) remains fully binding")
    if rho >= IDENTIFIABILITY_KILL:
        return (f"control null INVALID for {control} inference at rho="
                f"{round(rho, 4)} >= {IDENTIFIABILITY_KILL}: the control "
                "form reproduces the anchor schedule, so a scored null on "
                "the anchor could not be attributed to the construction")
    return (f"control null valid at rho={round(rho, 4)} < "
            f"{IDENTIFIABILITY_KILL}: anchor and control form are "
            "schedule-separable")
