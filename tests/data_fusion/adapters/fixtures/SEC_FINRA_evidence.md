# SEC EDGAR + FINRA short-sale adapter evidence (A2 stocks lane)

Status: **DISCOVERY_ONLY.** Both sources are
`AuthorityStatus.DOCUMENTED_CANDIDATE`.  Nothing here authorizes either
source for research use; authority decisions live in
`research.data_fusion.authority` and the owner-run source registry.

## Provenance

Every fixture in this set is **hand-written**, modeled on the *documented
public format* of its source.  None is production data, none was downloaded
from the network, and none contains a credential, token, account reference
or click-through acceptance.  Expected values in the tests are hand-computed
from the fixture bytes below; raw-response hashes are computed by the offline
harness (`response_for` / `RawResponse.sha256_hex`), never fetched.

| File | Source format it models |
| --- | --- |
| `sec_submissions.json` | `https://data.sec.gov/submissions/CIK##########.json` (column-oriented `filings.recent` object) |
| `sec_companyfacts.json` | `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` (facts → taxonomy → tag → units → fact list) |
| `finra_shortsale_daily.txt` | `https://cdn.finra.org/equity/regsho/nms/shrtYYYYMMDD` (pipe-separated daily Reg SHO file; OTC biweekly file has the same layout) |

## SEC EDGAR (`SEC_EDGAR`, `sec.py`)

### Fair access / entitlement

- Anonymous HTTPS GET; no key, no account, no click-through.
- Documented limit: no more than 10 requests/second with a declared
  User-Agent carrying owner contact.  Encoded as `RateLimitPolicy`
  (`min_interval_seconds=0.5`, client is deliberately slower than the limit).
- Built requests carry the placeholder UA
  `data-fusion-v1 DISCOVERY_ONLY (owner UA pending)`; the production
  User-Agent must be owner-approved before any real retrieval.  Headers are
  excluded from request identity by the shared base layer, so the
  placeholder cannot leak into cache identity.

### Deterministic request identity

CIK is normalized to exactly 10 zero-padded ASCII digits before it enters a
URL, so `"320193"`, `320193` and `"0000320193"` all produce the same
`request_id`.  Non-digit or >10-digit CIKs are refused
(`SCHEMA_INVARIANT_VIOLATED`).

### Point-in-time semantics

- `filingDate` is **date-only evidence**: `available_time_utc` is the end of
  the filed UTC day (`23:59:59Z`) with basis
  `DATE_ONLY_UPPER_BOUND`, noted `SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY`.
  Exact market availability is never claimed; feeding such a record to
  `Timings.require_exact_availability()` raises
  `NON_EXACT_AVAILABLE_TIME_FORBIDDEN`.
- `acceptanceDateTime` proves EDGAR acceptance only.  It may seed
  `event_time_utc` / `effective_time_utc` (with note
  `SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF`) but is never used as
  availability; an acceptance time after the end-of-filed-day bound is an
  invariant violation.
- Every record carries separated `event` / `available` / `effective` /
  `vintage` timings; `retrieved_time_utc` (harness `2026-01-01T12:00Z`) never
  substitutes for `available_time_utc`.
- Duration facts (entries carrying `start`) are skipped, counted in note
  `SEC_DURATION_FACTS_SKIPPED_V1`; V1 maps instant facts only.

### Hand-computed expectations

`sec_submissions.json` (CIK 1):

- `0000000001-24-000001`, filed 2024-01-03, accepted
  `2024-01-03T14:30:00Z`: event = `2024-01-03T14:30:00Z`,
  available = vintage = `2024-01-03T23:59:59Z`.
- `0000000001-24-000002`, filed 2024-01-08, no acceptance time: event =
  effective = `2024-01-08T00:00:00Z`, available = vintage =
  `2024-01-08T23:59:59Z`.
- Ordering: Jan 3 available < Jan 8 available; both <= retrieved time.

`sec_companyfacts.json` (CIK 1):

- `dei:EntityCommonStockSharesOutstanding` (shares): 1 instant record,
  val 1000, event = effective = `2023-12-31T00:00:00Z`, available =
  `2024-01-03T23:59:59Z`.
- `us-gaap:Assets` (USD): 2 instant records (original 5000 filed
  2024-01-08; revision 5100 filed 2024-04-15) — availability follows the
  *filed* date, so the revision becomes available strictly later than the
  original even though both describe the same period end.
- `us-gaap:Revenues` (USD): 1 duration fact (has `start`) — skipped, noted.

### Schema rejection (fail-closed, never coercion)

Rejected with stable reason codes, all covered by tests: unknown column in
`filings.recent` (`SCHEMA_UNKNOWN_FIELD`), unknown fact key
(`SCHEMA_UNKNOWN_FIELD`), missing required column/keys
(`SCHEMA_FIELD_MISSING`), unequal column lengths (`SCHEMA_INVARIANT_VIOLATED`),
duplicate accession number / duplicate fact
(`DUPLICATE_RECORD_ID`), malformed timestamps and dates
(`SCHEMA_TIMESTAMP_INVALID`), naive or non-UTC `acceptanceDateTime`
(`SCHEMA_TIMESTAMP_INVALID`), non-integer `fy`, bad accession format,
`filed < end`, `reportDate > filingDate`, body CIK ≠ URL CIK
(`SCHEMA_INVARIANT_VIOLATED`), non-JSON content type
(`CONTENT_TYPE_UNEXPECTED`), non-200 status (`HTTP_STATUS_UNEXPECTED`).

Envelope keys outside the parsed records (e.g. `entityName`, `entityType`,
`sic`) are tolerated on purpose: rejecting them would couple the adapter to
cosmetic upstream additions without protecting any parsed record.  Record
schemas are strict; envelopes are not.

## FINRA short-sale volume (`FINRA_SHORT`, `finra.py`)

### Format and entitlement

- Anonymous HTTPS GET of `shrtYYYYMMDD` files (daily NMS tier and biweekly
  OTC tier).  No key, no account, no click-through.
- No numeric rate limit is documented; the client policy keeps a
  conservative 1 request/second spacing.

### Row invariants (all tests-covered)

Header exactly `Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market`;
exactly 6 pipe-separated columns per row; row `Date` equal to the requested
trade date; volumes ASCII non-negative integers;
`ShortExemptVolume <= ShortVolume <= TotalVolume`; bare uppercase symbol; a
single uppercase-letter `Market` code; a repeated symbol raises
`DUPLICATE_RECORD_ID` instead of being merged or overwritten.

### Point-in-time and inference guards

- The file carries no publication timestamp: availability is the end of the
  trade UTC day (`DATE_ONLY_UPPER_BOUND`), noted
  `FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY`.  `effective_time_utc` is the
  trade-day midnight.
- **Forbidden inference:** short-sale volume is never short interest, borrow
  fee or utilization.  `forbidden_fields =
  ("short_interest", "borrow_fee", "utilization")` and
  `SourceAdapter.refuse_forbidden_field` raise
  `FORBIDDEN_INFERENCE_FIELD` at record-construction time, so no code path
  in this lane can emit those fields from FINRA data.

### Hand-computed expectations

`finra_shortsale_daily.txt`, trade date 2024-01-02 — 8 records
(4 per symbol: 3 volumes + market code):

- `FINRA:AAPL`: short_volume 1000, short_exempt_volume 100, total_volume
  5000, market `B`.
- `FINRA:MSFT`: short_volume 2000, short_exempt_volume 0, total_volume
  7000, market `Q`.
- All: event = effective = `2024-01-02T00:00:00Z`; available = vintage =
  `2024-01-02T23:59:59Z`; retrieved (2026-01-01T12:00Z) is never the
  available time.

## Determinism

Parsing is a pure function of response bytes: iteration over taxonomies,
tags and units is sorted; no wall-clock, no network, no randomness.  Two
pulls of the same response produce identical canonical record bytes
(test-enforced).
