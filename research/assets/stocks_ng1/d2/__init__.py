"""STOCKS-NG1 D2 lane: novelty + feasibility + identifiability measurement.

Discipline (dispatch packet stocks-ng1-d2-measurement): feature/rank
arithmetic ONLY - rho between signal series is the sole statistic; NO
expectancy, NO PnL, NO profit factor, NO selection, NO scoring anywhere
in this package.  A killed proposal is a successful preregistered
outcome.

Representation identity (P-12, frozen in code before any number is
cited): the measurement panel is the DAILY entity-date grid
(cohort entities x decision closes 2023-01-03..substrate_end) with the
eligibility floors (>= 63 bars through t, ADV63 >= 2,000,000 USD, raw
close >= 1.00) applied BEFORE any rho computation.  No re-gridding.
"""
