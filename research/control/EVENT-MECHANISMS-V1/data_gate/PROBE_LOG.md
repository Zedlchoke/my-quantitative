# Data-gate probes — EVENT-MECHANISMS-V1 G0/G2 evidence (2026-09-27T08:29-08:31Z)

Etiquette: 6 HTTP requests total, declared research UA where noted, no
retries, no bypass attempts on 403. Probes run from the root checkout by the
Lead (A1); raw bodies preserved in this dir.

| # | Request | UA | Result | File |
|---|---|---|---|---|
| 1 | GET https://data.sec.gov/submissions/CIK0000320193.json | MyQuantitative Research (declared) | HTTP 200, 163,991 B; acceptanceDateTime[] present, second precision, e.g. 2026-09-24T22:30:07.000Z; form/accession arrays; 1000 recent filings | probe_submissions_aapl.json |
| 2 | HEAD https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079-index.htm | MyQuantitative Research | HTTP/2 403, 4819 B body | (headers only) |
| 3 | GET same Archives index | MyQuantitative Research | HTTP 403, 4819 B | probe_index_get.htm |
| 4 | GET same Archives index | browser-like Chrome/126 | HTTP 403, 4819 B identical | probe_index_browser_ua.htm |
| 5 | GET https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/AccountsPayableCurrent.json | MyQuantitative Research | HTTP 200, 19,480 B | probe_companyconcept.json |

## Classification

- `data.sec.gov` estate: OPEN (JSON APIs, keyless, declared UA honored).
  **Serves acceptance datetimes for all form types** — the N2 gap's enabling
  surface is reachable from this environment.
- `www.sec.gov` estate (Archives + files): **BLOCKED_NETWORK_403,
  UA-independent, identical 4819-byte denial body** — environment-level
  filter (same class as Dukascopy L-FIBV1-1 / CME L-FXFF-1). Consequences:
  no raw-XML re-fetch (Form-4 primary docs, FTD zip re-pull) from this
  environment; the lawful surfaces are (a) on-disk P-13 archives
  (substrate/4A/FTD/EODHD — DFV1 digests), (b) data.sec.gov JSON metadata
  (acceptance stamps, form types, accession numbers).
- Owner action if raw-XML re-fetch becomes necessary: unblock
  `www.sec.gov` at the network layer (one action also covers
  `*.dukascopy.com` + `*.cmegroup.com` per L-FXFF-1 systemic finding).
