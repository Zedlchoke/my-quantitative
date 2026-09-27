# G2 DATA GATE — EVENT-MECHANISMS-V1 (2026-09-27, fail-closed)

Scope: authority for the two surviving identities (EMV1-A1 filing-flow,
EMV1-A2 insider-flow) + the D3 data-plane repair. Crypto/FX directions died
at G1 (no data authority pursued — planes closed/blocked). All evidence
paths relative to repo root; probe raw bodies + sha256 in `data_gate/`.

## Authority rows

### R1 — EDGAR acceptance-datetime surface (`data.sec.gov/submissions`) — PASS (probe-scale)

- source/terms: SEC EDGAR JSON APIs, keyless, declared research UA
  (`sec.gov/developer` fair-access; same channel class DFV1 used for 4/A
  fetch state).
- measured (this cycle, PROBE_LOG + depth probes): 7 HTTP requests total;
  `CIK##########.json` 200 ×3 (AAPL/BBBY/SIRI) incl. **dead issuer BBBY
  (delisted 2023) fully served**; paged `*-submissions-001.json` 200 with
  **1,735 filings back to 1996-05-15, acceptanceDateTime present**; AAPL
  recent-1000 spans 2015-07-28..2026-09-24 + pagination. Wrong-CIK control
  (FRC guess) → clean 404: **the N4 identity map is load-bearing**.
- event/available time: acceptanceDateTime IS the release evidence (§13.7
  law: `available_at` = acceptance stamp of the correct vintage; amendments
  are separate vintages).
- coverage gap → lane work: cohort-wide staging (every cohort CIK ×
  submissions incl. paged files) = "thousands of light calls, <100 MB"
  (DFV1 N2 class, no owner action required); rate ≤ fair-access.
- BLOCKED sibling: `www.sec.gov` estate (Archives/files) measured 403
  UA-independent (environment filter class L-FIBV1-1/L-FXFF-1). No raw-XML
  re-fetch; owner action recorded in gap matrix (unblocks Dukascopy/CME
  too). NOT substituted by anything — on-disk archives serve the raw layer.

### R2 — Form-4 XML substrate + form4_stream — PASS (archive-verified; restore pending lane)

- substrate: 345,150 XMLs / 227.8 MB, `~/staging_backups/cleanup_2026-09-17/
  stocks-free-v13_integration.tar.gz` → `integration/.staging_sec_v13/
  form4_xml/`, manifest pin `5d351623…` verified EXACT by DFV1 streamed
  re-hash; skeptic re-listed the archive this cycle (member count present).
- stream: 546,039 normalized rows, AVAILABLE_VALIDATED, pin `6ac2cd5b…`
  (DFV1 full-byte verification). 4/A corpus (6,123 files + 3,062
  acceptance stamps) archived — NOT used this cycle (amendment arm dropped
  at G1 court).
- lane work: P-13 restore into the cycle worktree + digest re-verify
  fail-closed at load (PIN_STREAM_SHA256 class guard) before any panel
  build.

### R3 — EODHD EOD price planes — PASS-with-defect-carried

- stocks-search-v1 cache: 111,323 files / 2.04 GB / 142.6M rows
  2015→2026-09, delisted-inclusive (survivorship-correct), entitled
  (owner token channel, offline read); amihud-v1 staging VALIDATED
  (8,219 sym 2017-2022); NG6 death-inclusive cohort panel archived
  (2,168 tickers).
- defect carried: N9 — eod_cache identity effectively unpinned (6/111,322
  records carry shas); lane must re-pin SHA256SUMS (~2-min CPU) or stage
  from the NG6/amihud validated surfaces before panel build.
- available_at: EODHD posts after US close (DECLARED, not machine-verified
  — DFV1 row); intraday decision surfaces do not exist on this channel;
  decisions at next-session open keep the plane honest (EOD-bar state
  complete before decision).

### R4 — Dated identity map (N4) — DERIVATION REQUIRED (lane work, no blocker)

- inputs on disk: form4_stream issuer-CIK population (dated), EODHD
  tickers, Form-15 death census (3,395 filings), NG2 census-B pair resolver
  (1,877 resolvable pairs measured). Wrong-CIK 404 measured this cycle
  proves the join must be dated + verified, never name-based.

### R5 — Stocks execution-cost plane — 0/10 components MEASURED (DFV1 census #4)

- binding contract: Q-2 conditional-cost law (open 3.33×/3.35× midday) +
  L-SAMV1-3 X1/X2 fill-feasibility (volume-0 bars unfillable; notional ≤
  participation fraction; unfillable skipped AND counted).
- **all G6 ceilings are PROXY-PRIOR** (labeled; Q-8). Owner action O-cost
  (gap matrix): broker-grade equities execution data would upgrade this;
  not required for a falsification-first S0 at conservative bands.

### R6 — Crypto / FX planes — NO AUTHORITY PURSUED (G1 closed them)

- crypto measured books exist (DFV1) but every crypto direction died at G1
  (ancestry identity / BLOCKED_DATA). FX: after-cost frontier BLOCKED on R1
  owner action + owner verbatim FX scoring ban this cycle.

## Verdicts

| Surface | Verdict | Margin/notes |
|---|---|---|
| data.sec.gov acceptance estate | PASS (probe-scale; cohort staging = lane work within N2 class budgets) | depth to 1996 measured; dead issuers served; pagination proven |
| www.sec.gov raw-doc estate | BLOCKED_NETWORK_403 (owner action GA-1) | no substitution; on-disk archives cover the raw layer |
| Form-4 substrate + stream | PASS (archive digest; restore+re-pin in lane) | P-13 procedure |
| EODHD price planes | PASS-with-defect (N9 re-pin in lane) | survivorship-correct |
| Identity map N4 | DERIVATION REQUIRED (inputs verified present) | wrong-CIK 404 = proof the join must be dated |
| Stocks cost plane | PROXY-PRIOR (0/10 measured; Q-2/X1-X2 contract frozen) | upgrade path GA-2 |
| Crypto/FX scoring planes | NOT PURSUED (G1 law) | — |

G2 gate: **PASS for both identities to proceed to G3 freeze** with the
listed lane-work conditions (restore, re-pin, N4 derivation, cohort
staging) — none of which is an owner blocker.
