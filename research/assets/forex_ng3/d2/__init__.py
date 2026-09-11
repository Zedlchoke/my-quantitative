"""FOREX-NG3 D2 measurement library (novelty / feasibility / identifiability).

NO PnL, expectancy or profit factor anywhere in this package.  The only
cross-book quantities produced are rank correlations (rho) between
signed exposure schedules, event/decision counts, and cost ceilings under
the REFERENCED (not measured) proxy ladder.

Representation identity (P-12, identical to the ng1 D2 machinery reused
VIA IMPORT, never edited): every schedule is a
``{"YYYY-MM-DD|PAIR": +1|-1}`` signed-exposure cell map on the frozen
daily 16:00-NY common grid (1842 days, 2018-04-04..2025-04-30).  A
position entered at grid day i with holding H grid days contributes
exposure cells i..i+H-1 (the exit fill at i+H is not an exposure cell);
overlapping same-pair cells net to the sign of their sum.  This
convention is identical for every ng3 book, ng1 kill-shadow and veto
shape compared in this lane.
"""

from research.assets.forex_ng3.d2.books import (  # noqa: F401
    Ng3D2BookError,
    A4_MODES,
    A5_MODES,
    LEG_PAIR,
    RECENT_MONTH_WINDOW,
    RECENT_WINDOW_START,
    RECENT_WINDOW_END,
    month_event_lookup,
    differential_pp,
    build_ng3_a4_book,
    build_ng3_a5p1_book,
    build_ng3_a5p2_book,
    dgs10_grid_levels,
    dgs10_z252_book,
    evaluate_q6_floor,
    proposal_verdict,
)
