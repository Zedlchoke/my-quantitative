"""US cash-equity data lane (owner: A3, PLAN_stocks.md section 7 A3).

Point-in-time security master, universe construction, the local parquet
bar/event loader and the PIT data audit live here.  The package deliberately
performs NO eager imports: sibling lanes add their own modules
(``calendar.py``, ``corporate_actions.py``, ...) and a partially integrated
tree must stay importable.

Everything in this lane is synthetic-fixture based: no provider entitlement
exists, so no real provider implementation may appear here (see
``research.assets.stocks.provider`` for the fail-closed entitlement policy).
"""
