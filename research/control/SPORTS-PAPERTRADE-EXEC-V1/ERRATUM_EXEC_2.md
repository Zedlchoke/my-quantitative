# ERRATUM EXEC-2 — real-quote mapping gap found by first-row audit (post-GO, 2026-10-07T11:20Z)

Discovery: the first real `quote` call (11:13Z, 1 credit, 888 bytes) fetched the
payload but Lane A's stub returned WITHOUT mapping events to MARKET_QUOTE rows —
the credit's payload was not stored. Caught by the controller's first-row audit
(no MARKET_QUOTE rows after a 200 response).

Fix (controller, same session): `map_odds_payload()` implemented in execute.py —
1:1 fail-closed provider-event match on (exact commence_time + full-name team
set via the static WNBA abbreviation table), pinnacle-only, h2h, per-leg
extraction (HOME/AWAY/DRAW), per-row PIT law (fetch < tip−6h strict;
source_last_update ≤ fetch), per-event sha256, journaled NO_QUOTE DECISION rows
for every unmatched/malformed fixture (never dropped). `hashlib` import added.
Gate tests that depended on the pre-GO real-world state were made
world-independent (tmp control dir/registry seams) — same laws, stable world.
Battery: 36/36 after the patch.

Cost of the gap: 1 credit (quota journal row 11:13Z; day 4/4 incl. the two
successful mapped calls at 11:15/11:16Z, remaining 493 provider-side). No rows
were fabricated to backfill the lost payload — the successful re-fetch wrote
REAL rows only.
