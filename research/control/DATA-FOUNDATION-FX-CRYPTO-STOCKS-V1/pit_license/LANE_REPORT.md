# LANE_REPORT.md — L-PIT (PIT/license cross-asset), 2026-09-26

Cycle: DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 · branch `orca/dfv1-lane-pit` ·
worktree `...data-foundation-v1/lane-pit` · base/dispatch SHA
`189c6d23ab2a6f50475819cf6df2e2e4def92820` (verified before any write).

## What exists and what is validated (this lane's censuses)

1. **Plan §3 ruling verification** — 15/15 rows checked against source
   artifacts; 13 VERIFIED (2 with recorded compression caveats), 1 PARTIAL
   (row 13: CFTC/Treasury/CBOE/FRED evidenced; ECB reachability-only; BIS
   UNVERIFIED). All shas measured via `git rev-parse` this session.
   → `LICENSE_RULINGS_VERIFIED.md`.
2. **Authority-row schema + validator** — `authority_row_schema.json`
   (dfv1_authority_row@1) + stdlib-only `validate_rows.py`. Ran on my own
   `inventory_rows.jsonl`: first run INVALID with 3 violations (R1 ×2, R4
   ×1) — fixed honestly (two rows downgraded AVAILABLE_VALIDATED →
   AVAILABLE_UNVALIDATED because the byte-level first/last/row-count census
   was not executed this cycle; one bytes field measured) — second run
   **VALID: 16 row(s)**.
3. **Owned shared/macro dataset census (16 rows)**:
   - AVAILABLE_VALIDATED (7): nyfed_reference_rates (5/5 hash ALL_MATCH),
     ofr_stfm (6/6), eia_open_data (7/7), nws_observations (8/8),
     usda_wasde (4/4) — full corpora re-hashed this cycle from bytes vs
     committed FDF manifests; sec_ftd_archive (SAMPLED 20/435, 20/20 match;
     629 MB > 500 MB cap) and sec_nport_quarterly (2/2) hashed but
     DOWNgraded to AVAILABLE_UNVALIDATED pending a byte-level coverage
     census (validator R1) — see row status_evidence for the split.
   - AVAILABLE_UNVALIDATED (2): fred_granted_set (packet-directed status;
     key existence from prior artifacts only, key use forbidden; staged raw
     pruned with worktrees; repin artifact on `orca/rates-ng1-integration`),
     exchange_calendars_substrate (library 4.13.2 measured in .venv,
     1,744,193 bytes; 12 committed calendar gates).
   - NOT_RUN (7): treasury_par_yield_curve, cboe_vix_term_structure,
     cftc_cot_positioning (raw bytes pruned with the rates/vol/commodities
     worktrees — zero-network lane cannot re-pull; committed censuses with
     per-file shas on their branches are the inherited evidence),
     alfred_vintaged (V5 host-side fail-closed, raw pruned), sec_ftd_current_halfmonth
     (sibling archive carries the verification), bis_official (no artifact
     anywhere — ruling UNVERIFIED; any use needs P-25 license screen first),
     ecb_official (probe-only; no corpus).

## What is missing — gap candidates (with the required fields)

| Gap | Why needed | Hypothesis class opened | Recorded kill it fixes | Falsifying control | Priority | Cost/volume estimate |
|---|---|---|---|---|---|---|
| Re-stage rates/vol/commodities raw (Treasury 37y CSVs, CBOE 4 CSVs, CFTC 11 zips) | Only censuses survive; raw bytes pruned with worktrees — A7-style byte re-verification is impossible today | keeps rates curve-shape + vol term-structure + positioning classes auditable | fixes the "can't re-hash" audit gap, not a strategy kill | byte-re-pull must reproduce committed census shas | MEDIUM | ~40 MB, keyless, ~50 requests (within probe budget class) |
| ALFRED host-side unblock (V5 fail-closed: CSV hang, license text unreachable) | vintage-dated macro is the only revision-safe channel (V9 binding) | CPI revision-dynamics (measured-exhausted on pinned plane; needs new source) | V9 "current-vintage forbidden" binding becomes satisfiable | current-vintage replay must change decisions | LOW (frontier measured-closed) | owner-side network/route action; agent cost ~0 |
| BIS source capture (license screen first) | plan §3 cites BIS; no artifact exists anywhere | policy-rate differential class (WS_CBPOL was consumed via another named channel) | closes the UNVERIFIED §3 sub-part | re-pull determinism + ToS capture | LOW | ~10 requests + ToS capture |
| ECB data corpus capture (SDMX) | only a press-page reachability probe exists | EMU event clocks | none recorded | press-clock sham control | LOW | ~20 requests |
| Reverse-split bidirectional fixture (F-11 gap) + intraday DST fixture (F-3 gap) + stamp-scale grid-endpoint fixture (F-8 gap) + zero-spread unit fixture (F-9 gap) | battery gaps named in FIXTURE_BATTERY_CONTRACT.md | data-integrity guards, not strategies | L-SAMV1-1 / L-TRACKB1-1 / FOREX-V5 CA-stamp classes become reusable fixtures | mutation non-vacuity (each fixture must break its mutant) | HIGH (cheap) | pure tests/, ~0 bytes |
| F-CX-NOBOOK-1 fixture | owner crypto law needs an executable gate | n/a (integrity) | prevents candle-synthesized book/flow class wholesale | positive tape control computes | HIGH (cheap) | pure test |
| EODHD earnings entitlement (owner action) | recorded NG3 reopening condition | PEAD/SUE earnings families (genuinely unmeasured) | fixes the NG3 E1 403 kill | dead-canary census already designed | MEDIUM (owner purchase) | owner subscription add-on |
| Broker-grade FX cost book (owner action) | rows 5/12 of §3 | any FX after-cost family | fixes FOREX-NG6/NG7 F4 kills + ILLIQ-style thin-margin kills | stress ×2.0 sweep mandatory | HIGH (owner) | IBKR/OANDA account + export |

## Boundary compliance

- Zero network requests this lane. `.env` never opened (FRED key existence
  cited from prior name-only censuses). S1/ERP1 holdout content never read
  (metadata via ledger/MAP text only). `research/wayfinder/` read-only.
  One light process; first substantive chunk under `/usr/bin/time` (validator
  run: 0.05s real — no heavy-job lock needed).
- No racing reads: all hashed corpora belong to TERMINAL cycles (FDF-V1/V1R1,
  DEU) with no active workers; PWS-CX-BNBUSDT-C1 (in-flight) not touched.

## Known limitations

- The 15-row §3 count vs the packet's "~17": the committed plan table has 15
  rows; all 15 verified per above.
- Rates/VOL/Commodities "NOT_RUN" rows reflect the honest impossibility of
  byte re-measurement after worktree pruning under the zero-network rule;
  their inherited branch censuses remain sha-verifiable.
- Exposure map counts are family-level rows assembled from ledger/MAP prose
  (the ledgers do not publish per-window byte ranges); boundaries for MIXED
  corpora (post-2026-08) are stamped by convention, not byte census.
- Validator cross-field rule R5 (UNOPENED seal citation) is heuristic
  (keyword match) — stdlib-only constraint; adequate for lane use, not a
  general-purpose schema engine.
