# DATA_READINESS_6E — Euro FX futures (lane FX-EB-CALENDAR, FUTURES-SIX-READINESS-20261004)

Generated 2026-10-04 UTC. 8-dim data-readiness. Machine twin:
`fx_eb_readiness.json` (same numbers, sha-pinned). PREP class: 0 PnL, 0 scored
cells, 0 new hypotheses/trials. Every calendar cell carries provenance
(file + sha256 or fetch-log line). IMM-rule expiry derivation never used.

## 1. Identity / tick — PASS (baseline restate)

6E = CME Euro FX futures, **EUR 125,000** vs USD, USD-per-EUR; minTick
**0.00005 = $6.25/tick**. Restated from baseline identity pack
(`dossiers_v2/6E_DEEP_v2.md` header, sha256 in `fx_eb_readiness.json`).
Baseline agrees — no flag.

## 2. O1M coverage + holes — PASS WITH DISCLOSED GAPS

- 3,054,311 outright 1m bars, 2020-01 → 2026-09-30, three eras (AV1B backfill2
  886,127 / AV1R backfill 1,823,090 / AV1T 345,094); era butts verified
  no-overlap (BACKFILL_LEDGER job GLBX-20261002-94UVSCXK6G, $3.47).
- Held chain: 1,746 sessions (held_calendar.parquet, sha pinned). Holes register:
  `analysis/6E_cache` + `6E_a6_dq.json`. O1M present for every obtained expiry
  quarter inside the panel span.

## 3. Roll / expiry — IMPROVED THIS ROUND

- **Expiry calendar 2023Q1..2026Q4: 14/16 OBTAINED.** The dispatch baseline
  (6E 64/68, family 236/272) already credited the sibling Q5 recovery (+12,
  2023-25); this round verifies it (13/13 reproduce) and adds ECH26/ECM26 →
  **6E 64/68 → 66/68; FX-family 236/272 → 248/272.** Per cell provenance:
  `fx_eb/calendar/fx_eb_expiry_2023_2026.json`. Source: archived official
  ProductCalendar/Future/58 capture @2021-07-03, independently verified this
  round (hash + own parser, 13/13 claimed values reproduce —
  `q5_independent_verify/q5_6e_verify_result.json`), extended by own extraction
  of ECH26 (2026-03-16) + ECM26 (2026-06-15).
- NOT_OBTAINED: **ECU26, ECZ26** — archived 58-calendar max capture is
  2021-07-03 (CDX-confirmed this round, `captures/cdx_future58_prefix.txt`);
  live service BLOCKED_TRANSPORT; rule derivation FORBIDDEN.
- Dispatch-correction: the dispatch claimed "6E 2027-2029 rows" inside the 6E
  capture — **not present** (rows end Jun-2026; the 2027-2029 chain exists in
  the 6B/6J XLS captures only).
- **Roll re-measured from the existing held chain (no new chain)**: 27 roll
  switches, 28 contracts, lead before official expiry 13–19 days where cells
  obtained (`cost_roll_events/cost_roll_events_fxeb.json`). Matrix baseline
  "roll_rule NOT_RUN" superseded by this measurement.

## 4. Session / holiday — PASS_EVIDENCED (archived)

- Weekly template: Globex ~23h (17:00 CT reopen), OBSERVED in dossier v2 session
  anatomy (DST-mismatch 1h shift). No verbatim weekly-hours spec capture for 6E
  (archived spec-service captures exist for ES/NQ only) — stated honestly.
- **Holiday/deviation grids: 34/42 archived windows OBTAINED** with 6E (id 58)
  deviation events; by year 2023 4/11, 2024 10/10, 2025 10/11, 2026 10/10; 8
  further windows aged out of the service's ~1y lookback (INCONCLUSIVE — 7 in
  2023 H1 + Carter-day 2025-01-05 probe), never counted as cells.
  `fx_eb/holiday/holiday_deviation_6e_6b.json`; every grid weekday/offset-validated.
- Reconciliation note: the dispatch's "6E holiday 12/12" was a mislabel of the
  sibling T2 expiry count; this artifact is the first per-product 6E holiday
  tabulation and supersedes it.

## 5. Event PIT — PASS_EVIDENCED

- **FOMC**: 31 dated statements 2023→2026-09-30 in the on-disk archive, of which
  **30 rate-decision statements** (2023: 8, 2024: 8, 2025: 8, 2026: 6); the 31st
  (2025-08-22) is the framework-review statement at 10:00 a.m. EDT, not a
  decision. All carry in-file release-time proof (58/59-proof baseline law).
- **ECB (6E primary overlay)**: 55/55 meetings 2020–2026.9 in data, decision
  14:15 CET/CEST — baseline `6E_a4_events.json` restated, not refetched.
- Vintage law: event calendars keyed to vintage as-of decision date;
  current-calendar inference FORBIDDEN; 2025 lapse-in-appropriations BLS
  anomalies already resolved in baseline bls_vintage artifacts (cited, not
  refetched).

## 6. Fee / spread / slippage / BBO — MODELED, UNDER REVIEW

- Tier-1 all-in **2.46 USD/side MODELED** (commission 0.85 + exchange 1.60 + reg
  0.01), VERIFIED_VS_ACCOUNT=**NOT_RUN**, **UNDER REVIEW** until owner-authorized
  A7. FX-group alias mapping **PARTIAL** (generic CME "Forex Futures" row; 6E not
  printed verbatim next to 1.60).
- Modeled RT **3.6–6.3 bp** (close-proxy spread 18.75 USD/side high-biased +
  1–3 tick slippage tiers). **BBO NOT_RUN stands** (D5 ruling: not purchased).
- Pins: FEES_CORRECTED.md `006d6372…5d1bef`; fx_hypotheses.json
  `013e711e…3f8816`; A7 fee packet **READY-not-run** `60b095fe…f9dfc`.

## 7. Trial budget — RECOUNTED, NO NEW TRIALS

FX-family minimal identity census **recounted from baseline**: 288 base
(4 families × 2 symbols × 36 identities; 1 identity = family×symbol×arm×tail×
delay×tier) + **360 strata contingency (declared)** = **648 program-hypothetical,
no ceiling defined by any standing ruling**. All 648 live on 6E/6B. FX-F1 census
contingency only (PB2 HOLD). `fx_eb/census/fx_census_recount.json`.

## 8. Reproduction / A7 — BASELINE A7 PASS WITH ERRATA; FEE A7 READY-not-run

Baseline A7-DEEP-6E verdict PASS WITH ERRATA (12/12 headline recomputes; errata
MAJOR-1/2 applied in dossier §11). This round's Q5 independent verify reproduces
the archived 6E calendar from raw bytes with an own parser (PASS). The FEE A7
has not been run by anyone — packet READY-not-run.

## Closing

**data-ready ≠ scored-authorized.** Dims blocking scored use for 6E: standing
NO_GO_SCORE; fee layer UNDER REVIEW (account verification NOT_RUN until A7);
BBO/execution realism NOT_RUN (D5); ECU26/ECZ26 expiry cells NOT_OBTAINED
(late-2026 rolls calendar-incomplete); 7 aged-out 2023 holiday windows
inconclusive.
