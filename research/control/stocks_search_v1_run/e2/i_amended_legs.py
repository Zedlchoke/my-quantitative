"""STOCKS-SEARCH-V1 §14 amendment: build_legs_amended — a byte-copy
of the FROZEN i_engine.build_legs with exactly ONE added branch (the
DEGENERATE_ADJ_PRICE censored-leg law).  The frozen i/ chain stays
untouched; A7 verifies copy line-equality except the amendment.
Generated 2026-09-21 from i/i_engine.py @ 694c15b1.
"""

import math

import numpy as np

from i_engine import Leg, NameData, load_p0_lib, med252_series


def build_legs_amended(name: NameData, decision_idx, H: int, calendar_index: dict,
               fends: dict, stress: float, entry_offset: int = 1,
               book_id: str = "book") -> tuple[list, list, dict]:
    """§8 execution engine for ONE name's decision indices.

    Returns (legs, censored_legs, counts).  All conventions per the module
    docstring (clock, fold force-flat, BC-7 death, bands, costs).
    """
    L = load_p0_lib()
    if H <= 0:
        raise ValueError("H must be positive")
    n = len(name.dates)
    med252 = med252_series(name)
    dates = name.dates
    op = name.adj_open
    legs: list[Leg] = []
    censored: list[Leg] = []
    counts = {"fired": 0, "band_subfloor": 0, "fold_not_opened": 0,
              "censored_died_before_entry": 0, "censored_death_zero_length": 0,
              "censored_death_open": 0, "open_offset": 0}
    for t in sorted(int(i) for i in decision_idx):
        counts["fired"] += 1
        try:
            band = L.resolve_band(float(med252[t]))
        except ValueError:
            raise  # UNRESOLVED: fail-closed, never a silent default band
        if band == "SUBFLOOR":
            counts["band_subfloor"] += 1
            continue
        entry_i = t + entry_offset
        exit_i = t + entry_offset + H
        d_t = dates[t]
        fold = L.assign_fold(d_t, fends["F1"], fends["F2"])
        if entry_i > n - 1:
            lg = Leg(name.symbol, t, d_t, "-", dates[n - 1], fold, band,
                     math.nan, math.nan, censored=True,
                     censored_kind="died_before_entry")
            censored.append(lg)
            counts["censored_died_before_entry"] += 1
            continue
        entry_date = dates[entry_i]
        if entry_date > fends[fold]:
            counts["fold_not_opened"] += 1
            continue
        # force-flat anchor: last served session with date <= fold end
        ff_exit = entry_i
        while ff_exit + 1 < n and dates[ff_exit + 1] <= fends[fold]:
            ff_exit += 1
        natural_served = exit_i <= n - 1
        if natural_served and dates[exit_i] <= fends[fold]:
            # natural exit inside the decision fold
            eff_exit, exit_date, force_flat = exit_i, dates[exit_i], False
        elif not natural_served and dates[n - 1] <= fends[fold]:
            # BC-7: death binds before the fold end - exit at the
            # death-session OPEN when the name serves it (it does:
            # the death session is the last served session)
            if n - 1 <= entry_i:
                lg = Leg(name.symbol, t, d_t, entry_date, dates[n - 1],
                         fold, band, math.nan, math.nan, censored=True,
                         censored_kind="death_zero_length")
                censored.append(lg)
                counts["censored_death_zero_length"] += 1
                continue
            # §14 A7S14-1: the DEATH-OPEN price window is inside the
            # amendment's law — non-positive entry/death open makes the
            # leg UNPRICEABLE (censored, no marks), never a division or
            # a garbage -100% gross into the included-at-marks variant.
            if float(op[entry_i]) <= 0.0 or float(op[n - 1]) <= 0.0:
                lg = Leg(name.symbol, t, d_t, entry_date, dates[n - 1],
                         fold, band, math.nan, math.nan, censored=True,
                         censored_kind="unpriceable_adj_price")
                censored.append(lg)
                counts["censored_unpriceable_adj_price"] = \
                    counts.get("censored_unpriceable_adj_price", 0) + 1
                continue
            gross = float(op[n - 1]) / float(op[entry_i]) - 1.0
            lg = Leg(name.symbol, t, d_t, entry_date, dates[n - 1], fold,
                     band, gross, math.nan, censored=True,
                     censored_kind="death_open")
            censored.append(lg)
            counts["censored_death_open"] += 1
            continue
        else:
            # natural exit crosses the fold end (or death lands after it):
            # fold force-flat binds first (execution contract, c8)
            if ff_exit <= entry_i:
                counts["fold_not_opened"] += 1
                continue
            eff_exit, exit_date, force_flat = ff_exit, dates[ff_exit], True
        # §14 DEGENERATE_ADJ_PRICE law (the ONLY change vs the frozen
        # build_legs; A7 verifies line-equality elsewhere): a leg whose
        # actual price window [entry_i, eff_exit] touches a non-positive
        # adjusted open is UNPRICEABLE -> BC-7 censored, never imputed.
        if bool(np.any(op[entry_i:eff_exit + 1] <= 0.0)):
            lg = Leg(name.symbol, t, d_t, entry_date, dates[eff_exit],
                     fold, band, math.nan, math.nan, censored=True,
                     censored_kind="unpriceable_adj_price")
            censored.append(lg)
            counts["censored_unpriceable_adj_price"] = \
                counts.get("censored_unpriceable_adj_price", 0) + 1
            continue
        gross = float(op[eff_exit]) / float(op[entry_i]) - 1.0
        net = gross - 2.0 * (L.BAND_BPS[band] * stress) / 1e4
        held = list(range(entry_i, eff_exit))       # log-slice sessions
        slices = []
        for d in held:
            ci = calendar_index.get(dates[d], -1)
            if ci < 0:
                counts["open_offset"] += 1
                continue
            slices.append((ci, math.log(float(op[d + 1]) / float(op[d]))))
        lg = Leg(name.symbol, t, d_t, entry_date, exit_date, fold, band,
                 gross, net, force_flat=force_flat, log_slices=slices)
        legs.append(lg)
    return legs, censored, counts
