"""RATES-NG1 D2 FROZEN DEFAULT PARAMETERS (P-12 commit-1 artifact).

Every parameter below is the D2 freeze of a parameter that the D1
proposals declared SYMBOLIC ("freeze at D2/S selection, never after").
The dispatch packet for task rates-ng1-d2-novelty fixes the freeze
point: the neutral/median default is declared HERE, in commit-1,
BEFORE any proposal-vs-shadow correlation is computed, and is never
re-tuned after any measurement.

Neutral-default conventions used throughout (documented per parameter):

1. Window/holding-style parameters take the cycle's own frozen
   holding convention of 5 trading days (p1_cost_contract.json,
   holding_trading_days = 5) so the shadow forms and the proposal
   forms share one placement horizon.
2. Bucket cuts are SAMPLE MEDIAN cuts of the relevant state series
   over the 1918 bookable instants (the neutral 50/50 split).  A
   sample median is a statistic of the STATE INPUT series only
   (calendar counts, curve coordinates, yield levels); no outcome,
   no PnL and no scored number of any kind enters the state
   machinery.
3. Sign conventions are the "+1 on the active/higher state" fixed
   convention.  A global sign flip of any series leaves |rho|
   invariant; the CONVENTION itself is still frozen here so the
   committed panel is exactly reproducible.
4. Trailing-history parameters take the cycle's own 252-session
   warmup constant (p2_grid_census.json warmup_sessions) and the
   named 63-session momentum constant of the momentum_63s form.
5. All series are evaluated on the P2 common grid bookable instants
   (1918) under the V7 close+1 readable-bar law, using each instant's
   ``readable_bar_date`` materialized in p2_grid_census.json.

This file contains NO measurement result: the correlation values are
produced by d2_run.run_measurement and written ONLY into the commit-2
panel artifact.
"""

from __future__ import annotations

SCHEMA = "rates_ng1_run/d2_frozen_defaults@1"

#: P-2 / selection_rubric_note novelty ceiling, identical in all four
#: D1 proposals (novelty_abs_rho_ceiling).
NOVELTY_ABS_RHO_CEILING = 0.2

#: Frozen ETP leg set (representation_identity.series.etp_legs of all
#: four D1 proposals).
ETP_LEGS = ("TLT", "IEF", "IEI", "SHY")

# ------------------------------------------------------------------ #
# Shadow (a): DGS10-level nominal-exposure form (falsification-by-
# control #14 FX-V8 / #15 FOREX-NG1 CTL-DGS10LEVEL class).
# ------------------------------------------------------------------ #
DGS10_LEVEL = {
    # Trailing-state window: the cycle's own warmup constant
    # (p2_grid_census.census.warmup_sessions), measured in COMMON GRID
    # sessions ending at the instant's readable bar (inclusive).
    "trailing_window_sessions": 252,
    # Rule family: level above its trailing state -> fixed-sign
    # position.  Frozen sign convention: +1 when the DGS10 level at the
    # readable bar is strictly above the trailing median, else -1.
    # Source: dead CTL-DGS10LEVEL trailing-state level-sign family.
    "rule": "level_strictly_above_trailing_median",
    # FRED DGS10 is a daily series; when the readable bar date carries
    # no observation (bond market closed on a grid day), the last
    # observation at or before the bar is the PIT-readable fact.  If
    # the last observation is older than this many calendar days the
    # instant is UNDEFINED for this shadow (never inferred).
    "max_staleness_calendar_days": 10,
    # Entry: fred/DGS10.json via consume_via_plane (frozen set member,
    # substrate-manifest sha256 pin, verify-on-read).
    "entry": "fred/DGS10.json",
}

# ------------------------------------------------------------------ #
# Shadow (b): FX reaction-direction form (post-event sign-following on
# event windows).
# ------------------------------------------------------------------ #
FX_REACTION_DIRECTION = {
    # Event clock for ALL FOUR proposals (documented mapping decision,
    # frozen before any measurement): the P2 auction-announcement
    # mappings (p2_auction_eligibility.json, sha-pinned in every D1
    # proposal's representation_identity).  For the event-based lane A4
    # proposals these ARE the proposal's own event windows.  For lane
    # A5 (grid-only) proposals this calendar stands in as the
    # "FOMC-style clock": NO FOMC calendar exists anywhere in the
    # frozen RATES-NG1 consumption set (plane_adapter frozen set:
    # treasury curve, FRED keyed series, ETP EOD, auction calendar), so
    # the auction announcement calendar is the only release-style
    # clock lawfully committable in this cycle.  Using the identical
    # event clock for all four proposals keeps the per-shadow rho
    # comparable across proposals.
    "event_clock": "p2_auction_eligibility.mappings.decision_session",
    # Reaction measure: sign of the change of the DGS10 level across
    # the event's decision instant (the readable-bar level at the
    # event's decision session minus the readable-bar level at the
    # previous common-grid session).  The dead FX forms followed the
    # sign of the market's reaction to a release; DGS10 is the rates
    # analogue of the FX release-reaction series and is a committed
    # frozen-set member.
    "reaction_measure": "sign(dgs10_level(b_e) - dgs10_level(b_prev))",
    # Post-event holding window: the cycle's frozen holding convention
    # (p1_cost_contract.holding_trading_days), in common-grid sessions,
    # starting at the event's decision session.
    "holding_sessions": 5,
    # Overlapping event windows: the LATER event's sign wins
    # (last-write-wins); zero reaction sign carries position 0.
    "overlap_rule": "last_write_wins",
}

# ------------------------------------------------------------------ #
# Shadow (c): FX release-order form (within-month relative-timing
# conditioning) mapped onto the auction-calendar sequencing.
# ------------------------------------------------------------------ #
FX_RELEASE_ORDER = {
    # Conditioning unit: calendar month of the announcement date.
    "conditioning_unit": "announcement_month",
    # Within-month order state: the security type of the FIRST
    # announced event of the month (min announcementDate).  Frozen
    # sign convention: bill-first month -> +1, coupon-first (Note or
    # Bond) month -> -1, held from that first event's P2 decision
    # session to month end; 0 before it.
    "order_state": "first_announced_event_security_type",
    "bill_first_sign": 1,
    "coupon_first_sign": -1,
}

# ------------------------------------------------------------------ #
# Shadow (d): momentum_63s (trailing 63-session momentum sign on the
# frozen ETP leg set).
# ------------------------------------------------------------------ #
MOMENTUM_63S = {
    # The named form's constant, in common-grid sessions.
    "lookback_sessions": 63,
    # RAW primary unadjusted closes (representation law of all four
    # proposals; adjusted channel is not consumed here).
    "price_field": "close",
    # Pooled leg state: equal-weight mean of the per-leg momentum
    # signs (values in {-1.0, -0.5, 0.0, 0.5, 1.0}).
    "pooled_rule": "equal_weight_mean_of_leg_signs",
}

# ------------------------------------------------------------------ #
# Shadow (e): generic_dow_tue (bare weekday calendar clock).
# ------------------------------------------------------------------ #
GENERIC_DOW_TUE = {
    # The literal named form: long-on-Tuesday clock, flat elsewhere.
    "rule": "tuesday_only",
    "tuesday_sign": 1,
    "other_day_sign": 0,
}

# ------------------------------------------------------------------ #
# Proposal OWN decision-state defaults (D1 symbolic -> D2 frozen).
# ------------------------------------------------------------------ #

A4_P1_CONCENTRATION = {
    # state_definition_symbolic: count of census events with issueDate
    # inside a fixed k1/k2 window around the decision session.
    # Frozen k1 = k2 = 5 common-grid sessions (the cycle's frozen
    # holding convention; the grid's own session calendar is the
    # business-day ruler -- no holiday calendar is invented).
    "k1_sessions": 5,
    "k2_sessions": 5,
    # PIT filter: an event counts only if its announcement PIT
    # decision session (p2 mapping decision_session) is at or before
    # the decision session (pre-announced supply mechanics only).
    "pit_filter": "announcement_decision_session_le_t",
    # Bucket cut: sample median of the concentration count over the
    # 1918 bookable instants (neutral 50/50 cut).
    "bucket_cut": "sample_median_of_count",
    # Direction: fixed sign convention, +1 above the cut, -1 below,
    # 0 exactly at the cut.
    "sign_convention": "plus1_above_median_minus1_below",
}

A4_P2_STAGE = {
    # Stage boundaries follow the P1/P2 day-event PIT law: first grid
    # session STRICTLY after each official date (announcementDate ->
    # the mapping's decision_session; auctionDate and issueDate use
    # the identical rule recomputed on the grid).
    "stage_boundaries": "first_grid_session_strictly_after",
    # Stage map (monotone stage ordering, fixed sign convention,
    # settlement-era positive; frozen before any measurement):
    #   announcement-era [ann, auction) -> -1
    #   auction-era     [auction, issue) -> 0
    #   settlement-era  [issue, issue+5) -> +1
    #   outside any active pipeline -> 0
    "stage_signs": {"announcement": -1, "auction": 0, "settlement": 1},
    # Settlement-era length: the cycle's frozen holding convention.
    "settlement_era_sessions": 5,
    # Nearest-event rule: the event with the latest announcement PIT
    # decision session at or before t; ties broken by the larger
    # census event_index.
    "nearest_event_rule": "latest_announcement_le_t_ties_largest_index",
}

A5_P1_CURVATURE_GATED_SLOPE = {
    # Decomposition basis (frozen tenor defaults on the official par
    # curve): slope = 30Y - 2Y; curvature = 2Y - 2*10Y + 30Y; level
    # coordinate = 10 Yr.  All from the S5 official CSV rows at the
    # instant's readable bar (V7 close+1 law).
    "slope_tenors": ["30 Yr", "2 Yr"],
    "curvature_tenors": ["2 Yr", "10 Yr", "30 Yr"],
    "level_tenor": "10 Yr",
    # Level-orthogonalization: PIT-expanding OLS (with intercept) of
    # each shape coordinate on the level coordinate, fitted ONLY on
    # strictly-past bookable instants; the residual at the instant is
    # the orthogonalized coordinate.  Minimum strictly-past points
    # before the first fit: the cycle's momentum constant (63) keeps
    # the earliest fits bounded; instants before that are UNDEFINED
    # (dropped from correlation pairs, never inferred).
    "orthogonalization": "expanding_ols_residual_on_level",
    "min_past_points": 63,
    # Double-median double-sort state: +1 iff BOTH orthogonalized
    # coordinates are strictly above their sample medians, -1 iff
    # BOTH strictly below, else 0.
    "bucket_cut": "sample_median_per_coordinate",
    "state_rule": "both_above_plus1_both_below_minus1_else_zero",
}

A5_P2_FRONT_VS_BELLY = {
    # Residual definition (frozen tenor defaults): front = 2 Yr,
    # belly = 5 Yr, raw residual = front - belly; level coordinate
    # removed exactly as in A5-P1 (same expanding-OLS law).
    "front_tenor": "2 Yr",
    "belly_tenor": "5 Yr",
    "level_tenor": "10 Yr",
    "orthogonalization": "expanding_ols_residual_on_level",
    "min_past_points": 63,
    # Bucket cut: sample median of the orthogonalized residual.
    "bucket_cut": "sample_median",
    "sign_convention": "plus1_above_median_minus1_below",
}

# ------------------------------------------------------------------ #
# Correlation + verdict law (frozen).
# ------------------------------------------------------------------ #
CORRELATION_LAW = {
    "statistics": ["spearman", "pearson"],
    "alignment": "bookable_instants_both_series_defined",
    "spearman_ties": "average_ranks_pearson_on_ranks",
    "unmeasurable_rule": (
        "n_used_below_2_or_zero_variance_in_either_series"),
    "pooled_per_shadow": "max_abs_spearman_abs_pearson",
    "proposal_pooled": "max_over_shadows_pooled",
    "margin_definition": "ceiling_minus_proposal_pooled",
    "verdict_rule": (
        "all_five_shadows_measured: ELIGIBLE if proposal_pooled <= "
        "ceiling else VETO; any UNMEASURABLE shadow not documented "
        "inapplicable: VETO_PENDING (never-PASS-by-absence)"),
}

#: The five shadows every proposal is screened against, in panel key
#: order.
SHADOW_KEYS = (
    "dgs10_level_trailing_state",
    "fx_reaction_direction",
    "fx_release_order",
    "momentum_63s",
    "generic_dow_tue",
)

#: The four screened proposals, in panel key order.
PROPOSAL_IDS = (
    "RATESNG1-A4-P1",
    "RATESNG1-A4-P2",
    "RATESNG1-A5-P1",
    "RATESNG1-A5-P2",
)
