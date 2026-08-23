# Funding is an accounting cost first

**Type:** research  
**Status:** closed

## Question

When may funding become a signal or a margin-sizing input rather than only an
audited cashflow?

## Resolution

Funding is currently applied post-trade using Binance historical settlements,
with fail-closed coverage checks. Before a margin-sensitive candidate can be
promoted, the engine must receive native funding settlement events and match the
post-trade audit. Funding must not become a signal merely because a short window
has positive or negative average funding.

See `reports/funding.py`, `reports/performance.py`, and `NOTES.md` §14.
