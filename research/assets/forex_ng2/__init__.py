"""FOREX-NG2 assets: NEW modules only (plan section 3 inheritance law).

The FOREX-NG1 machinery (research/assets/forex_ng1: plane_adapter,
spot_series, run/) is inherited VERBATIM and never edited from this
namespace; this package adds the NG2 frontier module (revision_series:
first-to-second-vintage revision-event builder) with no code changes to
frozen ng1 semantics.
"""

from research.assets.forex_ng2.revision_series import (  # noqa: F401
    RevisionEvent,
    RevisionStructureError,
    VintageMonotonicityError,
    build_revision_events,
    cross_economy_differential_months,
    dedupe_exact_rows,
    evaluate_floors,
    events_by_year,
    lookup_event,
    magnitude_distribution,
    recent_window_bounds,
    usable_events,
)
