# A3 MACRO adapter evidence — ECB SDMX / BIS CBPOL / FRED ALFRED

Lane A3 (macro) of FREE DATA FUSION V1, branch `orca/data-fusion-v1-a3-macro`,
base `ce0037bfe86f863d336b854dc2545b87f797d377`.  Everything here was produced
offline against the A1-owned shared base layer
(`research/data_fusion/adapters/base.py`); no network call, no account, no real
API key, no paid source, no click-through was involved at any point.

## Sources and contracts implemented

| source_id | endpoint | adapter | parser_version |
| --- | --- | --- | --- |
| `ECB_SDMX` | `https://data-api.ecb.europa.eu/service/data/{FLOW}/{KEY}` | `research/data_fusion/adapters/ecb.py` | `ecb-adapter-1.0.0` |
| `BIS_CBPOL` | `https://data.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0/{KEY}` | `research/data_fusion/adapters/bis.py` | `bis-adapter-1.0.0` |
| `FRED_ALFRED` | `https://api.stlouisfed.org/fred/series/vintagedates`, `https://api.stlouisfed.org/alfred/series/observations` (`file_type=json`) | `research/data_fusion/adapters/fred.py` | `fred-adapter-1.0.0` |

Shared invariants (enforced by `base.py`, asserted by the tests):

- requests are deterministic HTTPS-only GETs; `request_id()` is stable for
  equal inputs and excludes `credential_query`;
- SDMX parsing goes through `extract_sdmx_json_series` / `sdmx_series_id`
  (TIME_PERIOD must be the first observation dimension; values numeric or
  absent; schema mismatch is refused, never coerced);
- entity ids resolve from the payload structure, e.g. `ECB:EXR:D.USD.EUR.SP00.A`,
  `BIS:WS_CBPOL:US.P`, `FRED:CPIAUCSL`.

## Fail-closed availability decisions

- **ECB**: the SDMX-JSON payload carries no historical availability.
  `header.prepared` is message *metadata* (when the SDMX message was
  assembled) and is validated for shape only — it is never used as an
  availability timestamp (note `ECB_PREPARED_TIME_NOT_AVAILABILITY_PROOF`).
  `parse_series(..., release_evidence=None)` raises
  `MISSING_AVAILABLE_TIME_EVIDENCE` before any record is produced.  Date-only
  evidence yields the end-of-UTC-day upper bound plus note
  `ECB_AVAILABILITY_NOT_EXACT`.
- **BIS**: CBPOL observation dates are policy-rate *effective* dates, so
  `effective_time_utc == event_time_utc` (`BIS_EFFECTIVE_DATE_SEMANTICS`).
  Effectiveness is not availability: missing evidence fails closed with
  `MISSING_AVAILABLE_TIME_EVIDENCE`; date-only evidence yields the
  end-of-UTC-day upper bound (`BIS_AVAILABILITY_NOT_EXACT`).  A record is
  never eligible on its own effective date — no backdated carry signal.
- **FRED/ALFRED**: `api_key` is mandatory (`CREDENTIAL_REQUIRED` when
  empty/blank) and travels only in `credential_query`: swapping key values
  does not change `request_id()`, and the key never appears in the canonical
  payload, cache path or any committed artifact.  ALFRED `realtime_start` is
  the vintage date — date-only proof, so availability is the end of the
  vintage UTC day as an upper bound
  (`FRED_VINTAGE_DATE_ONLY_NOT_EXACT_RELEASE_TIME`).  Values marked `.`
  parse to null with note `FRED_MISSING_VALUE_MARKED_DOT`.  Revisions are
  append-only: two vintages of one observation date produce two distinct
  records (dedupe key `(date, realtime_start)`), never an overwrite.
  Documented ALFRED envelope keys and observation keys are enforced;
  unknown fields raise `SCHEMA_UNKNOWN_FIELD`.  Upstream error payloads
  (`{"error_code", "error_message"}`) raise `UPSTREAM_ERROR_PAYLOAD`.

## Authority verdicts (owner must ratify; nothing here self-authorizes)

| source | verdict | rationale |
| --- | --- | --- |
| `ECB_SDMX` | `AuthorityStatus.DOCUMENTED_CANDIDATE` | public anonymous API, terms documented; no historical availability evidence captured yet, so not authorized |
| `BIS_CBPOL` | `AuthorityStatus.DOCUMENTED_CANDIDATE` | same posture; `BIS_POLICY_RATE_NOT_CARRY_AUTHORIZATION`: policy rates never auto-unlock a carry strategy |
| `FRED_ALFRED` | `AuthorityStatus.CANDIDATE_NOT_AUTHORIZED` | key-gated and no key is provisioned or authorized (`entitlement_id=api-key-required-not-provisioned`) |

None of the three is `AUTHORIZED_INTERNAL_RESEARCH`; none unlocks scoring or
any strategy family (carry / macro-surprise included).  FRED additionally
declares `forbidden_fields = ("analyst_consensus", "wire_release_timestamp")`
— inference-adjacent fields this source must never produce
(`FORBIDDEN_INFERENCE_FIELD`).

## Fixture provenance (all hand-written, offline)

| file | models | hand-computed content |
| --- | --- | --- |
| `tests/data_fusion/adapters/fixtures/ecb_sdmx_exr.json` | ECB Data API SDMX-JSON shape | series `D.USD.EUR.SP00.A`; USD per EUR 1.0951 (2024-01-02) and 1.0969 (2024-01-03); `header.prepared` 2024-01-03T15:10Z present as metadata only |
| `tests/data_fusion/adapters/fixtures/bis_cbpol.json` | BIS Data API SDMX-JSON shape (WS_CBPOL) | series `US.P`; rate 4.0 effective 2024-03-20 and 4.25 effective 2024-05-01 |
| `tests/data_fusion/adapters/fixtures/fred_vintagedates.json` | FRED `file_type=json` vintagedates array | vintage dates 2024-01-12 and 2024-02-09 |
| `tests/data_fusion/adapters/fixtures/fred_alfred_obs.json` | ALFRED observations envelope (`file_type=json`, realtime window) | observation 2023-12-01 in two vintages (272.712 then revised 272.690) plus one `.` missing value for 2024-01-01 |

No fixture was downloaded, none contains production data, credentials,
tokens or account references (the FRED tests use the placeholder string
`owner-secret`).  Negative cases (missing evidence, missing
`structure`/`dataSets`, unknown fields, non-numeric observations,
duplicates, error payloads, timezone violations) are derived in-test by
mutating these files.

## Verification run (from this worktree)

```
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/data_fusion -q
  -> 90 passed  (of which 34 are the A3 ECB/BIS/FRED adapter tests)
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m compileall research/data_fusion
  -> OK
git diff --check
  -> clean
```

## Boundary statement

Zero strategy scoring, zero PnL, zero S1, zero paper/live trading, zero
account creation, zero real API keys, zero paid sources, zero click-through,
zero raw-data commits (raw bytes stay in the out-of-repo `RawCacheStore`), no
force-push/reset, no changes outside the lane-owned paths listed in the
commit, no edits to other lanes' worktrees or artifacts.
