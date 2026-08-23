# Capture the missing ETH derivatives snapshot

**Type:** task  
**Status:** closed  
**Blocked by:** none

## Question

Can the same 30-day OI and mark-price snapshot used for the six altcoins be
captured for ETH with an auditable timestamp and matching interval semantics?

## Decision needed

Store ETH funding/OI/mark data under the same snapshot ID, verify 15-minute
spacing and bar-close mapping, and fail closed if the API returns partial or
shorter coverage.

## Evidence to collect

- `captured_at`, requested start/end, response row counts, and first/last
  timestamps;
- duplicate/gap checks and mapping to completed ETH bars;
- a manifest proving ETH and altcoin overlays came from the same capture window.

## Resolution

ETH was captured into `derivatives_data/20260821/ETHUSDT` using the same
requested interval as the six existing altcoin bundles:
`2026-07-22T14:15:00Z` → `2026-08-21T14:00:00Z`.

- Funding: 90 settlements.
- OI: 2,880 rows; mark-price klines: 2,880 rows.
- OI and mark series have zero duplicates and zero non-15-minute gaps.
- 2,879 of 2,880 overlay rows map to completed ETH catalog bars. The final
  interval-open row is outside the last available ETH bar and is excluded from
  features.
- The snapshot manifest and SHA-256 hashes are recorded in
  `derivatives_data/20260821/manifest.json`.

**Decision:** ETH now satisfies the derivative-overlay coverage prerequisite for
the crowding/funding feature contract. The historical S0 window is still only a
screening window; the separate untouched S1 task remains required for promotion.
