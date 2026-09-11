"""FOREX-NG1 D2 measurement library (novelty / feasibility / identifiability).

NO PnL, expectancy or profit factor anywhere in this package.  The only
cross-book quantities produced are rank correlations (rho) between
signed exposure schedules, event/decision counts, and cost ceilings
under the REFERENCED (not measured) proxy ladder.

Representation identity (P-12): every schedule produced here is a
``{ "YYYY-MM-DD|PAIR": +1|-1 }`` signed-exposure cell map on the frozen
daily 16:00-NY common grid (1842 days, 2018-04-04..2025-04-30, spot
grid census sha256 42612576fb...).  A position entered at grid day i
with holding H grid days contributes exposure cells i..i+H-1 (the exit
fill at i+H is not an exposure cell).  This convention is identical for
every book, proposal and veto shape compared in this lane.
"""

from research.assets.forex_ng1.d2.series import (  # noqa: F401
    VintagedSeries,
    parse_realtime_observations,
    s1_seasonal_naive,
    s2_trailing_yoy,
    release_sign,
)
from research.assets.forex_ng1.d2.events import (  # noqa: F401
    CensusError,
    load_census,
    first_release_events,
    interval_bounds,
    strictly_before,
    order_state,
    month_key,
)
from research.assets.forex_ng1.d2.books import (  # noqa: F401
    BookError,
    build_a4_book,
    build_sham7d_book,
    build_a5p1_book,
    build_a5p2_book,
    build_generic_shapes,
    build_v7_spillover_shadows,
    build_v7_leadlag_shadows,
    load_committed_cells,
)
from research.assets.forex_ng1.d2.rho import (  # noqa: F401
    spearman,
    compare_schedules,
    pooled_max_abs_rho,
)
