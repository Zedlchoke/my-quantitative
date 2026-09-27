# G3 ADDENDUM r3 — G5 ADJUDICATION (2026-09-27, A1 court; zero PnL exists)

G5 (Lane X independent implementation) returned `G5_PASS_WITH_ADJUDICATIONS`:
99.98% field-identity on intersections, 2 measured DEFECTS in the Lane I
engine, 16 logged spec ambiguities (AMB-01..16). Per the P-4 law (same
implementation reproduces the same bug) this is G5 working as designed.
This addendum fixes the CANONICAL reading; both implementations rebuild to
it; re-comparison must be byte-identical or every residual diff classified.

## Defect dispositions (Lane I delta — spec-compliance fixes, not spec changes)

- **D-1 (A2 entry law)**: Lane I used A1-style direction+1 sequencing for
  A2 (~1,250 records). R2-3 governs: A2 entry = FIRST session open strictly
  after the acceptance instant. FIX in engine; A2 is NOT_RUN_THIN anyway
  (see F-ADJ-1) but the code must be spec-true for the record.
- **D-2 (div/split case-miss)**: exact-case filename lookup silently missed
  79 case-differing div files → 47 corporate-action records booked despite
  R2-2. FIX: case-insensitive normalized stem matching over the restored
  div/split tables; re-census exclusions.

## F-ADJ-1 — A2 fold-floor adjudication (immutable floors law)

A2 anchor populations F1..F4 = 0 / 1,628 / 661 / 632 (substrate
form4_stream spans 2018-01..2025 — measured, no 2015–2017 bytes exist;
pre-2018 XML re-fetch is www.sec.gov 403-blocked = BLOCKED_DATA). The
frozen floor "≥100 bookable events per fold" is IMMUTABLE (BTC-H4-TWO-
REGIME precedent: no relaxation). **A2 identity = NOT_RUN_THIN this
cycle; mechanism UNADJUDICATED on merits.** Doors: (a) owner GA-1 network
unblock → pre-2018 XML extension → new freeze; (b) owner-directed new
freeze with substrate-honest folds (2020–2026) — owner decision only,
post-population fold changes are never agent-made. No scored A2 cell will
be presented at the GO gate this cycle.

## Canonical ambiguity rulings (AMB-01..16)

| # | Ruling |
|---|---|
| 1 | Weekend acceptances ARE anchor members (unmonitored by construction): stratum `WKND`, part of the unmonioned set S1∪S3∪S4∪WKND. "Separate bucket" = recording label, not exclusion. |
| 2 | A2 value = XML shares × XML per-share price (stream is index-only — measured). ACCEPT. |
| 3 | transactionCode 'P' is the frozen gate; 'D'-direction P-rows kept. ACCEPT. |
| 4 | A2 event clock = earliest qualifying acceptance of the issuer-day. ACCEPT. |
| 5 | Officer/director gate at filing level (XML schema reality). ACCEPT + recorded. |
| 6 | Unpriced A2 rows: DROP and count — NO panel-close imputation (imputation is an unstated modeling choice; conservative drop wins). |
| 7 | Exit-bar B1/X1 failure → roll exit forward to next clean bar; exhaustion = last bar + DELISTING_EXIT flag. ACCEPT. |
| 8 | B1 expressed on raw closes (R2-1). ACCEPT. |
| 9 | Fold assignment by ET-local acceptance date (bookkeeping only). ACCEPT. |
| 10 | "Close after acceptance" = strictly after. ACCEPT. |
| 11 | Direction tie (close==open) → direction 0 → EXCLUDED from book, counted. CANONICAL. |
| 12 | Dedup keeps lexicographically smallest (form, accession). ACCEPT (0 collisions measured). |
| 13 | CA exclusion check on the FINAL window after exit roll. ACCEPT. |
| 14 | X1 15%-notional participation cap is an EXECUTION law applied at the scoring fill stage, not at book build. ACCEPT. |
| 15 | CA window = full calendar interval [entry..exit]; ex-dates need not be session dates. ACCEPT. |
| 16 | B1 "both directions" = symmetric ≥10× reading on raw closes (literal formula cannot fire downward with positive prices). ACCEPT. |

## Re-run protocol

Both implementations rebuild all books to r3 canonical; re-comparison
target: **record-key sets identical + fields byte-identical**; any residual
diff must classify SPEC_AMBIGUITY (r3-closed) / DEFECT / DATA_VARIANT with
counts. G5 final verdict issued after the re-comparison. Populations re-
censused (weekend-inclusion and unpriced-drop will move counts; floors
re-checked against the SAME immutable bars).
