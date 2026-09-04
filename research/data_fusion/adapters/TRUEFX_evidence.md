# TRUEFX — Source Evidence (A4 Forex lane)

Status: **DISCOVERY_ONLY / CANDIDATE — NOT AUTHORIZED.**
License and internal-use status: **UNKNOWN / PENDING VERIFICATION** (fail-closed).

| Field | Value |
| --- | --- |
| `source_id` | `TRUEFX` |
| Adapter | `research/data_fusion/adapters/truefx.py` (`parser_version = truefx-adapter-1.0.0`) |
| Content | Historical monthly FX tick archives (indicative bid/ask top-of-book quotes) |
| Access pattern | Anonymous HTTPS GET, no account, no API key |
| `license_id` | `truefx-internal-use-v1` — **a pure label only; carries no authorization meaning** |
| `entitlement_id` | `anonymous-public-archive-no-key` |
| `authority_status` | `AuthorityStatus.CANDIDATE_NOT_AUTHORIZED` |
| Terms captured | **NO** — owner has not captured the applicable terms |
| Internal-research right | **UNKNOWN** |
| Local-storage right | **UNKNOWN** |
| Redistribution right | **UNKNOWN** |

## What is documented (public archive layout)

Monthly tick archives, one ZIP per pair per month:

```
https://www.truefx.com/dev/data/YYYY-MM/{PAIR}-YYYY-MM.zip
```

Example shape (documented format, NOT a captured file):
`USD/JPY,20240102 00:00:00.123,141.085,141.115` = pair, GMT timestamp, bid, ask.

- Timestamps are **GMT by specification**; the adapter parses them naive and
  attaches UTC explicitly (`TRUEFX_GMT_PARSED_AS_UTC` note).
- The archive must contain **exactly one CSV member**; anything else is
  refused (`TRUEFX_ARCHIVE_MEMBER` note records the parsed member).

## Availability policy (fail-closed)

TrueFX publishes **no publication timestamp** for a monthly archive. The
adapter therefore sets `available_time_utc` to the **end of the archive month
(UTC)** with `AvailabilityBasis.DATE_ONLY_UPPER_BOUND`
(`TRUEFX_MONTH_END_UPPER_BOUND` note). It **never** claims exact availability;
`timings.require_exact_availability()` raises
`NON_EXACT_AVAILABLE_TIME_FORBIDDEN` on every record this adapter produces.
No tick is eligible for any decision before its archive month ends.

## Role boundaries enforced by the adapter

- Forbidden inference fields: `swap`, `swap_rate`, `rollover`, `tom_next`,
  `financing` (`FORBIDDEN_INFERENCE_FIELD` on any attempt).
- Note `TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY`: TrueFX indicative bid/ask never
  authorizes swap, rollover or financing values.
- Note `TRUEFX_INDICATIVE_TOP_OF_BOOK_ONLY`: records live in dataset
  `top_of_book_ticks` with unit `PRICE` — indicative top-of-book quotes from a
  non-broker feed, **never executable broker prices**.

## Prohibited during verification (hard boundaries honored)

No account registration, no login, no "I agree" click, no bulk archive
download. All tests are fully offline: the monthly ZIP is built in memory from
the hand-written fixture `tests/data_fusion/adapters/fixtures/truefx_ticks_usdjpy.csv`
(stdlib `zipfile` + `io`); no production bytes are committed.

## What would change the verdict

Only the owner can promote this source, by capturing the actual TrueFX terms
and recording an `AuthorityEvidence` in the owner-run source registry with
`terms_captured = true` and explicit internal-storage / internal-research
rights. Until then the fail-closed evaluation yields
`CANDIDATE_NOT_AUTHORIZED` and the source is unusable for scored research.
