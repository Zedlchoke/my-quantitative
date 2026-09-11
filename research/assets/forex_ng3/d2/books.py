"""Signed-exposure schedule builders for the FOREX-NG3 D2 measurement.

Builds the four ng3 proposal anchor books and their D2 identifiability
controls as signed exposure-cell schedules on the frozen daily 16:00-NY
common grid (1842 days, 2018-04-04..2025-04-30):

- FXNG3-A4-P1  CA restricted revision-SIGN drift on USDCAD, H=5
               (fire on every restricted event with sign(R) != 0);
- FXNG3-A4-P2  CA restricted revision-MAGNITUDE regime on USDCAD, H=10
               (fire iff |R| >= 1e-4 fraction; R0 empty-book law);
- FXNG3-A5-P1  CA-vs-active-leg-bloc restricted revision differential on
               USDCAD, H=5, |D| >= 0.02 pp, max-v2 availability entry;
- FXNG3-A5-P2  CA<->leg bilateral differential TRANSFER onto the leg's
               own pair (GBPUSD/AUDUSD/NZDUSD), H=5, per-event clock.

Identifiability controls (schedule-comparison only, NO expectancy):

- CTL-V7NODIFF (A5-P1/A5-P2, plan section 5 lane-A5 mandatory): the
  identical fired event days and max-v2 clock as the anchor, direction
  carrying ONLY the ABSOLUTE CA revision exposure (gate on |R_CA| at
  the same 0.02 pp threshold per the frozen arm config); pooled
  max |rho| >= 0.98 vs the anchor kills pre-score (Q-11 null validity
  recorded either way);
- CTL-DGS10LEVEL exact-spec shape (A4): the nominal-yield-level exposure
  on the anchor's own fired days (sign = +1 long USDCAD iff the DGS10
  level as-of D(e) is below its trailing 252-grid-day median), built
  from the pinned DGS10 vintaged bytes (P-13 chain verified at P0).

Reuse law (inherited VERBATIM via import, never edited): the ng1 D2
builders' ``_new_book``/``_add_cells`` cell conventions and the
``first_grid_day_strictly_after``/``exposure_days`` grid clock from
``research/assets/forex_ng1/d2``; the ng2/ng3 revision-event law from
``research/assets/forex_ng3/revision_series``.  |rho| measurement itself
lives in ``research/assets/forex_ng1/d2/rho.py`` (Spearman, average-tie
ranks, three frozen variants) and is likewise reused unmodified.

Availability clock (identical for every ng3 book): A = end of day on the
binding v2 ``realtime_start`` (date-only evidence -> conservative
same-day bound); D(e) = the first 16:00-NY common-grid day STRICTLY
after that date.  A same-day 16:00-NY decision (20:00/21:00Z) never
sees a v2 whose availability bound (23:59:59Z) is that same date.
"""

from __future__ import annotations

from datetime import date
from statistics import median
from typing import Mapping, Sequence

from research.assets.forex_ng1.d2.books import (  # noqa: F401  (reuse, no edit)
    _add_cells, _new_book,
)
from research.assets.forex_ng1.d2.events import (
    exposure_days, first_grid_day_strictly_after,
)
from research.assets.forex_ng2 import revision_series as ng2

#: Q-6 recent window (the last 24 calendar months of S0): entry-day and
#: obs-month bases share these calendar bounds.
RECENT_WINDOW_START = date(2023, 5, 1)
RECENT_WINDOW_END = date(2025, 4, 30)
RECENT_MONTH_WINDOW = ("2023-05", "2025-04")

#: A5-P2 transfer destinations (leg -> the leg's own funded pair).
LEG_PAIR = {"GB": "GBPUSD", "AU": "AUDUSD", "NZ": "NZDUSD"}

#: Anchor pair of the A4 / A5-P1 books (CA -> USDCAD by plan law).
ANCHOR_PAIR = "USDCAD"

A4_MODES = ("sign", "material")
A5_MODES = ("anchor", "v7nodiff")

#: Frozen thresholds (proposal identity; P-15: never moved post-hoc).
A5_GATE_PP = 0.02          # |D| / |R_CA| gate, percentage points
A4P2_MATERIAL = 1e-4       # |R| fraction (0.01% of index level)
A4P2_HOLD = 10             # grid days
DEFAULT_HOLD = 5           # grid days (A4-P1, A5-P1, A5-P2)

#: D2 frozen bars (dispatch packet forex-ng3-d2-measurement).
NOVELTY_BAR = 0.20
IDENTIFIABILITY_KILL = 0.98

#: Q-6 frozen floors (plan section 3 A4 recent floor >= 15; the A5
#: recent floors per the D2 dispatch: >= 6 differential months for
#: A5-P1, >= 2 transfer events for A5-P2).
A4_Q6_FLOOR = 15
A5P1_Q6_FLOOR = 6
A5P2_Q6_FLOOR = 2


class Ng3D2BookError(Exception):
    """Fail-closed ng3 D2 book construction error."""


# --------------------------------------------------------------------------- #
# restricted-stream lookups
# --------------------------------------------------------------------------- #

def month_event_lookup(
        restricted_by_economy: Mapping[str, Sequence[ng2.RevisionEvent]],
        ) -> dict[tuple[str, str], ng2.RevisionEvent]:
    """(economy, obs month key) -> the restricted event, fail-closed.

    The ng2 event law yields at most ONE v1->v2 event per obs month, so
    a duplicate key is a structural violation: raise, build nothing.
    """
    idx: dict[tuple[str, str], ng2.RevisionEvent] = {}
    for eco, events in restricted_by_economy.items():
        for e in events:
            key = (eco, e.month_key)
            if key in idx:
                raise Ng3D2BookError(
                    f"duplicate restricted event {(eco, e.month_key)}: the "
                    "ng2 law yields at most one v1->v2 event per obs month "
                    "(fail-closed)")
            idx[key] = e
    return idx


def differential_pp(anchor_event: ng2.RevisionEvent,
                    leg_events: Sequence[ng2.RevisionEvent]) -> float:
    """D = 100 * (R_CA - mean(R_L over the active legs)), in pp.

    R_X = 100 * (I_v2/I_v1 - 1) in percentage points per the frozen
    proposal semantics; both sides restricted-stream events.
    """
    if not leg_events:
        raise Ng3D2BookError("differential requires >= 1 active leg")
    mean_leg = sum(e.ratio for e in leg_events) / len(leg_events)
    return 100.0 * (anchor_event.ratio - mean_leg)


def _month_in_recent_window(month_key: str) -> bool:
    lo, hi = RECENT_MONTH_WINDOW
    return lo <= month_key <= hi


def _entry_in_recent_window(entry: date) -> bool:
    return RECENT_WINDOW_START <= entry <= RECENT_WINDOW_END


# --------------------------------------------------------------------------- #
# lane A4 books (own-economy CA revision drift)
# --------------------------------------------------------------------------- #

def build_ng3_a4_book(name: str, mode: str,
                      events: Sequence[ng2.RevisionEvent],
                      grid_days: list[date], grid_index: dict,
                      window_end: date,
                      material_threshold: float = A4P2_MATERIAL,
                      hold: int = DEFAULT_HOLD) -> dict:
    """A4 signed-exposure book on USDCAD from the CA restricted stream.

    mode 'sign'     (A4-P1): fire on every event with sign(R) != 0
                    (no magnitude threshold); R < 0 -> LONG USDCAD,
                    R > 0 -> SHORT USDCAD.
    mode 'material' (A4-P2): fire iff |R| >= ``material_threshold``
                    (fraction), same polarity law (R < 0 -> long).

    Entry: first grid day strictly after EOD(v2.realtime_start).
    Exposure cells i..i+hold-1; H=5 for P1, H=10 for P2 (caller binds
    the proposal's frozen horizon).
    """
    if mode not in A4_MODES:
        raise Ng3D2BookError(f"unknown ng3 A4 mode {mode!r}")
    book = _new_book(name, mode=mode, material_threshold=material_threshold,
                     hold_grid_days=hold,
                     clock="first grid day strictly after "
                           "EOD(v2.realtime_start)")
    m = book["meta"]
    m["events_total"] = len(events)
    m["events_in_window"] = 0
    m["fired_events"] = 0
    m["no_position_sign_zero"] = 0
    m["below_material_threshold"] = 0
    m["dropped_tail_entries"] = 0
    m["recent_events_eligible"] = 0
    m["recent_fired_events"] = 0
    m["recent_material_fired"] = 0
    m["fired_v2_year_counts"] = {}
    book["fired_records"] = []      # [{"entry": date, "sign": +-1}]
    for e in sorted(events, key=lambda x: (x.v2_realtime_start,
                                           x.obs_month)):
        bound = date.fromisoformat(e.v2_realtime_start)
        entry = first_grid_day_strictly_after(bound, grid_index, window_end)
        if entry is None:
            m["dropped_tail_entries"] += 1
            continue
        m["events_in_window"] += 1
        if _entry_in_recent_window(entry):
            m["recent_events_eligible"] += 1
        r_pp = 100.0 * e.ratio
        if mode == "material":
            if abs(e.ratio) < material_threshold:
                m["below_material_threshold"] += 1
                continue
        if r_pp == 0.0:
            m["no_position_sign_zero"] += 1
            continue
        sign = 1 if r_pp < 0.0 else -1      # R<0 -> LONG USDCAD (+1)
        days = exposure_days(entry, hold, grid_days, grid_index)
        _add_cells(book, days, {ANCHOR_PAIR: sign})
        book["fired_records"].append({"entry": entry, "sign": sign})
        m["fired_events"] += 1
        yr = e.v2_realtime_start[:4]
        m["fired_v2_year_counts"][yr] = m["fired_v2_year_counts"].get(yr, 0) + 1
        if _entry_in_recent_window(entry):
            m["recent_fired_events"] += 1
            if mode == "material":
                m["recent_material_fired"] += 1
    m["active_cells"] = len(book["cells"])
    return book


# --------------------------------------------------------------------------- #
# lane A5 books (revision differentials)
# --------------------------------------------------------------------------- #

def build_ng3_a5p1_book(name: str, mode: str,
                        months: Mapping[str, Sequence[str]],
                        lookup: Mapping[tuple[str, str], ng2.RevisionEvent],
                        grid_days: list[date], grid_index: dict,
                        window_end: date, gate_pp: float = A5_GATE_PP,
                        hold: int = DEFAULT_HOLD) -> dict:
    """A5-P1 differential book on USDCAD over the CA-anchored months.

    ``months``: month_key -> [anchor, leg1, ...] (the census join law
    output).  mode 'anchor' fires |D| >= gate with D = R_CA - mean(R_L
    over active legs); D >= +gate -> SHORT USDCAD, D <= -gate -> LONG.
    mode 'v7nodiff' (CTL-V7NODIFF) keeps the identical months and the
    identical max-v2 entry clock (computed from the anchor's active
    legs) but directions/gates carry ONLY the absolute CA revision:
    R_CA >= +gate -> SHORT USDCAD; R_CA <= -gate -> LONG; else no
    position.  Legs are never read in v7nodiff mode except for the
    clock (per the frozen arm config).
    """
    if mode not in A5_MODES:
        raise Ng3D2BookError(f"unknown ng3 A5-P1 mode {mode!r}")
    book = _new_book(name, mode=mode, gate_pp=gate_pp, hold_grid_days=hold,
                     clock="first grid day strictly after "
                           "EOD(max v2.realtime_start over CA + active legs)")
    m = book["meta"]
    m["months_total"] = len(months)
    m["months_in_window"] = 0
    m["months_failed_closed"] = 0
    m["months_gate_passed"] = 0
    m["months_gate_failed"] = 0
    m["dropped_tail_entries"] = 0
    m["recent_months_obs_basis"] = 0
    m["recent_months_eligible_entry_basis"] = 0
    m["recent_months_fired"] = 0
    m["active_leg_month_counts"] = {leg: 0 for leg in
                                    ("GB", "AU", "NZ", "US")}
    book["fired_records"] = []
    for mth in sorted(months):
        legs = list(months[mth][1:])
        recent_month = _month_in_recent_window(mth)
        if recent_month:
            m["recent_months_obs_basis"] += 1
        ev_ca = lookup.get(("CA", mth))
        leg_events = []
        missing = ev_ca is None
        for leg in legs:
            ev = lookup.get((leg, mth))
            if ev is None:
                missing = True
            else:
                leg_events.append(ev)
            m["active_leg_month_counts"][leg] = (
                m["active_leg_month_counts"].get(leg, 0) + 1)
        if missing:
            # a join month whose event is absent from the restricted
            # lookup is unmeasurable: fail closed, never inferred
            m["months_failed_closed"] += 1
            continue
        bound = max([date.fromisoformat(ev_ca.v2_realtime_start)] +
                    [date.fromisoformat(e.v2_realtime_start)
                     for e in leg_events])
        entry = first_grid_day_strictly_after(bound, grid_index, window_end)
        if entry is None:
            m["dropped_tail_entries"] += 1
            continue
        m["months_in_window"] += 1
        if _entry_in_recent_window(entry):
            m["recent_months_eligible_entry_basis"] += 1
        if mode == "anchor":
            value = differential_pp(ev_ca, leg_events)
        else:
            value = 100.0 * ev_ca.ratio
        if abs(value) < gate_pp:
            m["months_gate_failed"] += 1
            continue
        m["months_gate_passed"] += 1
        sign = -1 if value >= gate_pp else 1   # D/R_CA >= +gate -> SHORT
        days = exposure_days(entry, hold, grid_days, grid_index)
        _add_cells(book, days, {ANCHOR_PAIR: sign})
        book["fired_records"].append({"entry": entry, "sign": sign,
                                      "month": mth})
        if recent_month:
            m["recent_months_fired"] += 1
    m["active_cells"] = len(book["cells"])
    return book


def build_ng3_a5p2_book(name: str, mode: str,
                        transfer_events: Sequence[tuple[str, str]],
                        lookup: Mapping[tuple[str, str], ng2.RevisionEvent],
                        grid_days: list[date], grid_index: dict,
                        window_end: date, gate_pp: float = A5_GATE_PP,
                        hold: int = DEFAULT_HOLD) -> dict:
    """A5-P2 bilateral-differential TRANSFER book on the leg pairs.

    ``transfer_events``: (month_key, leg) with leg in {GB, AU, NZ}.
    mode 'anchor': D_L = R_CA - R_L; |D_L| >= gate -> fire on the leg's
    OWN pair, D_L >= +gate -> LONG the leg vs USD, <= -gate -> SHORT.
    mode 'v7nodiff' (CTL-V7NODIFF): identical events and per-event
    max(v2_CA, v2_L) clock, direction = +sign from R_CA alone (R_CA >=
    +gate -> long leg vs USD); the leg revision is never read.
    """
    if mode not in A5_MODES:
        raise Ng3D2BookError(f"unknown ng3 A5-P2 mode {mode!r}")
    book = _new_book(name, mode=mode, gate_pp=gate_pp, hold_grid_days=hold,
                     clock="first grid day strictly after "
                           "EOD(max(v2_CA, v2_L)) per transfer event")
    m = book["meta"]
    m["transfer_events_total"] = len(transfer_events)
    m["events_in_window"] = 0
    m["events_failed_closed"] = 0
    m["events_gate_passed"] = 0
    m["events_gate_failed"] = 0
    m["dropped_tail_entries"] = 0
    m["recent_events_obs_basis"] = 0
    m["recent_events_eligible_entry_basis"] = 0
    m["recent_events_fired"] = 0
    m["fired_by_leg"] = {leg: 0 for leg in LEG_PAIR}
    book["fired_records"] = []
    for mth, leg in sorted(transfer_events):
        if leg not in LEG_PAIR:
            raise Ng3D2BookError(
                f"transfer destination {leg!r} is not a non-USD leg "
                "(GB/AU/NZ only; US is the quote leg, never a destination)")
        recent_month = _month_in_recent_window(mth)
        if recent_month:
            m["recent_events_obs_basis"] += 1
        ev_ca = lookup.get(("CA", mth))
        ev_leg = lookup.get((leg, mth))
        if ev_ca is None or ev_leg is None:
            m["events_failed_closed"] += 1
            continue
        bound = max(date.fromisoformat(ev_ca.v2_realtime_start),
                    date.fromisoformat(ev_leg.v2_realtime_start))
        entry = first_grid_day_strictly_after(bound, grid_index, window_end)
        if entry is None:
            m["dropped_tail_entries"] += 1
            continue
        m["events_in_window"] += 1
        if _entry_in_recent_window(entry):
            m["recent_events_eligible_entry_basis"] += 1
        if mode == "anchor":
            value = differential_pp(ev_ca, [ev_leg])
        else:
            value = 100.0 * ev_ca.ratio
        if abs(value) < gate_pp:
            m["events_gate_failed"] += 1
            continue
        m["events_gate_passed"] += 1
        sign = 1 if value >= gate_pp else -1  # D/R_CA >= +gate -> LONG leg
        days = exposure_days(entry, hold, grid_days, grid_index)
        _add_cells(book, days, {LEG_PAIR[leg]: sign})
        book["fired_records"].append({"entry": entry, "sign": sign,
                                      "month": mth, "leg": leg})
        m["fired_by_leg"][leg] += 1
        if recent_month:
            m["recent_events_fired"] += 1
    m["active_cells"] = len(book["cells"])
    return book


# --------------------------------------------------------------------------- #
# CTL-DGS10LEVEL exact-spec shape (A4 nominal separability)
# --------------------------------------------------------------------------- #

def dgs10_grid_levels(rows: Sequence, grid_days: Sequence[date]
                      ) -> dict[date, float | None]:
    """DGS10 level as-of each grid day from the pinned vintaged bytes.

    Containing-window read (realtime law): at grid day g the in-force
    vintage is the row window [realtime_start, realtime_end] containing
    g; the level is that vintage's most recent daily observation.  A
    day with no containing window or a missing value reads None
    (fail-closed, never backfilled).
    """
    from research.assets.forex_ng1.plane_adapter import FRED_MISSING
    sorted_rows = sorted(rows, key=lambda r: (r.realtime_start, r.obs_date))
    levels: dict[date, float | None] = {}
    active: list = []
    i = 0
    for g in grid_days:
        gs = g.isoformat()
        while i < len(sorted_rows) and sorted_rows[i].realtime_start <= gs:
            active.append(sorted_rows[i])
            i += 1
        active = [r for r in active if r.realtime_end >= gs]
        best = None
        for r in active:
            if r.value == FRED_MISSING:
                continue
            if best is None or r.obs_date > best.obs_date:
                best = r
        levels[g] = None if best is None else float(best.value)
    return levels


def dgs10_z252_book(name: str, source_book: dict,
                    levels: Mapping[date, float | None],
                    grid_days: list[date], grid_index: dict,
                    hold: int, min_history: int = 126,
                    trailing: int = 252) -> dict:
    """The exact-spec CTL-DGS10LEVEL exposure on the anchor's fired days.

    sign = +1 (LONG USDCAD) iff the DGS10 level as-of the entry grid day
    is below its trailing-252-grid-day median, else -1; identical event
    days, pair, horizons and 1-unit magnitudes as the fired anchor book
    (V8 falsification-by-control #14/#15 shape).  Entries with
    insufficient trailing history or an unreadable level are dropped and
    disclosed (fail-closed, never guessed).
    """
    book = _new_book(name, spec="CTL-DGS10LEVEL exact-spec: sign = +1 "
                     "(long USDCAD) iff DGS10 level as-of D(e) < trailing "
                     f"{trailing}-grid-day median else -1",
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
        _add_cells(book, days, {ANCHOR_PAIR: sign})
    m["active_cells"] = len(book["cells"])
    return book


# --------------------------------------------------------------------------- #
# D2 verdict helpers (frozen laws; used by the runner and the tests)
# --------------------------------------------------------------------------- #

def evaluate_q6_floor(measured: int, floor: int) -> dict:
    """Q-6 floor row with P-2 margin."""
    return {"measured": measured, "floor": floor,
            "margin": measured - floor,
            "verdict": "PASS" if measured >= floor else "FAIL"}


def proposal_verdict(*, novelty_max_abs_rho, q6_row, r0_empty_book=None,
                     identifiability_kill=None,
                     novelty_bar: float = NOVELTY_BAR) -> str:
    """The per-proposal D2 verdict (frozen rule order).

    1. novelty unmeasurable -> INELIGIBLE_FAIL_CLOSED (a number that
       cannot be measured is never inferred PASS);
    2. A4-P2 R0 EMPTY BOOK (its own frozen rule: the material regime
       fires 0 in-window events) -> INELIGIBLE_FAIL_CLOSED;
    3. ancestry rho over the 0.20 bar -> VETO(margin);
    4. Q-6 floor FAIL -> VETO(count);
    5. identifiability kill (CTL-V7NODIFF rho >= 0.98) -> VETO;
    else ELIGIBLE.
    """
    if r0_empty_book:
        return ("INELIGIBLE_FAIL_CLOSED(A4-P2 R0 EMPTY BOOK: material "
                "regime |R| >= 1e-4 fires 0 in-window events; frozen "
                "threshold never moves P-15)")
    if novelty_max_abs_rho is None:
        return ("INELIGIBLE_FAIL_CLOSED(novelty unmeasurable: pooled "
                "|rho| could not be computed on the frozen representation)")
    if novelty_max_abs_rho > novelty_bar:
        return (f"VETO(ANCESTRY_VETO rho={round(novelty_max_abs_rho, 4)} "
                f"margin={round(novelty_bar - novelty_max_abs_rho, 4)})")
    if q6_row is not None and q6_row["verdict"] != "PASS":
        return (f"VETO(Q6_FLOOR_FAIL {q6_row['measured']} < "
                f"{q6_row['floor']}, margin {q6_row['margin']})")
    if identifiability_kill is not None and \
            identifiability_kill >= IDENTIFIABILITY_KILL:
        kill_bar = IDENTIFIABILITY_KILL
        return (f"VETO(IDENTIFIABILITY_KILL CTL-V7NODIFF rho="
                f"{round(identifiability_kill, 4)} >= {kill_bar}: the "
                "no-differential form reproduces the anchor schedule; "
                "Q-11 control null INVALID)")
    return "ELIGIBLE"
