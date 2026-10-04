# DATA_READINESS_6B — British Pound futures (lane FX-EB-CALENDAR, FUTURES-SIX-READINESS-20261004)

Generated 2026-10-04 UTC. 8-dim data-readiness. Machine twin:
`fx_eb_readiness.json` (same numbers, sha-pinned). PREP class: 0 PnL, 0 scored
cells, 0 new hypotheses/trials. Every calendar cell carries provenance
(file + sha256 or fetch-log line). IMM-rule expiry derivation never used.

## 1. Identity / tick — PASS (baseline restate)

6B = CME British Pound futures, **GBP 62,500** vs USD, USD-per-GBP; minTick
**0.0001 = $6.25/tick**. Restated from baseline identity pack
(`dossiers_v2/6B_DEEP_v2.md` §0 + v1 §1, sha256 in `fx_eb_readiness.json`).
Baseline agrees — no flag.

## 2. O1M coverage + holes — PASS WITH DISCLOSED GAPS

- ~2.55M outright 1m bars, 2020-01 → 2026-09-30 (5 vendor parquet files, full
  shas pinned in `6B_DEEP_v2.md` §0). Held chain 1,746 sessions
  (held_calendar.parquet, sha pinned). Serials/calendar-spreads excluded by
  design, counted in dossier §7. Two-rule roll agreement 1,458/1,746 sessions
  (83.5%) documented in dossier §3. O1M present for every obtained expiry
  quarter inside the panel span.

## 3. Roll / expiry — IMPROVED THIS ROUND (still partial)

- **Expiry calendar 2023Q1..2026Q4: 10/16 OBTAINED** — BPU24 2024-09-16,
  BPZ24 2024-12-16, BPH25 2025-03-17, BPM25 2025-06-16, BPU25 2025-09-15,
  BPZ25 2025-12-15, BPH26 2026-03-16, BPM26 2026-06-15, BPU26 2026-09-14,
  BPZ26 2026-12-14 → **6B 52/68 → 62/68** (family 236/272 → 248/272).
  Provenance: this lane's Wayback fetch of the official
  `ProductCalendar/Download.xls?productId=42` @2024-09-03 (16896 wire bytes,
  sha in `fetch_log.jsonl`; parsed with own xlrd parser). This is the first
  post-2018 archived 6B calendar the round family has found — the sibling
  round's "6B 0/12" is superseded for 2024Q3–2026Q4.
- NOT_OBTAINED: **2023Q1..2024Q2 (6 cells)** — archived 6B calendars are
  Future/42 max 2018-04-08 (pre-span) and Download.xls productId=42 earliest
  2024-09-03 (the service drops expired contracts); CDX inventories captured
  this round (`captures/cdx_future42_prefix.txt`, `captures/cdx_downloadxls42.txt`).
  Live service BLOCKED_TRANSPORT; rule derivation FORBIDDEN.
- Dispatch-correction: the dispatch's "6E 2027-2029 rows in pcal_58" does not
  exist; the 2027–2029 forward chain lives in the 6B XLS (BPH27..BPM29, recorded
  in `fx_eb_expiry_2023_2026.json → future_rows_not_in_grid`) and the sibling 6J XLS.
- **Roll re-measured from the existing held chain (no new chain)**: 27 roll
  switches, 28 contracts; lead before official expiry 17 days for the 2024Q4→
  2026Q3 switches cross-referenced to the new official cells (14 days into the
  2026Q4 contract), `cost_roll_events/cost_roll_events_fxeb.json`. Matrix
  baseline "roll_rule NOT_RUN" superseded. Note: `6B_cache` has no
  contract_registry.json (6E-only artifact) — registry-gap cross-check not
  computable for 6B; official-calendar cross-ref used instead.

## 4. Session / holiday — PARTIAL (holiday hole stands)

- Weekly template: Globex ~23h, London-morning share measured 28.7%→23.7%
  (2020-21→2025-26, dossier v2 §2). No verbatim weekly-hours spec capture for 6B.
- **Holiday/deviation grid: NOT_OBTAINED 0/42 windows.** Product id 42 (6B)
  appears in NO archived trading-hours-by-product capture: this round's CDX
  probe (filter `original:.*id=42.*`) returned zero rows across both attempts;
  consistent with the sibling round's full URL-id enumeration. Live service
  BLOCKED_TRANSPORT. The FX deviation-hours model for 6B remains
  calendar-uncertain — this is the largest remaining 6B data hole.

## 5. Event PIT — PASS_EVIDENCED

- **BoE MPC**: 32 listed dates 2023–2026, **30 in panel** through 2026-09-30
  (2023: 8, 2024: 8, 2025: 8, 2026: 6); **11 rate-change decisions** in panel
  (5 in 2023, 2 in 2024, 4 in 2025) cross-checked here against
  `normalized/boe_bank_rate_tidy.parquet` — matches official Bank Rate history
  through 2025-12-18; remaining 19 in-panel dates are hold decisions. Source:
  DEEP-6B lane's bankofengland.co.uk assembly 2026-10-02 (restated, not
  refetched). 2026-11-05/2026-12-17 labeled forward-scheduled, never decisions.
- **FOMC (6B overlay)**: 30 rate-decision statements 2023–2026.9 (same inventory
  as 6E; 58/59 in-file release-time proof baseline).
- Vintage law: as-of decision date only; current-calendar inference FORBIDDEN.

## 6. Fee / spread / slippage / BBO — MODELED, UNDER REVIEW

- Tier-1 all-in **2.46 USD/side MODELED**, VERIFIED_VS_ACCOUNT=**NOT_RUN**,
  **UNDER REVIEW** until A7; FX-group alias mapping **PARTIAL** (GBP alias row).
- Modeled RT **6.3–11.2 bp** (close-proxy + 1–3 tick tiers @1.30). **BBO NOT_RUN
  stands** (D5). Pins: FEES_CORRECTED.md `006d6372…5d1bef`; fx_hypotheses.json
  `013e711e…3f8816`; A7 packet READY-not-run `60b095fe…f9dfc`.

## 7. Trial budget — RECOUNTED, NO NEW TRIALS

Same FX-family census: **648 program-hypothetical, no ceiling**; all on 6E/6B;
FX-F1 contingency only (PB2 HOLD); 6B-specific gates unchanged (F4 6B leg gated
on reopen-gap std anatomy — baseline not_run register). `fx_eb/census/fx_census_recount.json`.

## 8. Reproduction / A7 — BASELINE A7 PASS; FEE A7 READY-not-run

Baseline A7-DEEP-6B verdicts (incl. §4 row-for-row CoT tidy verification and §5
number-preservation under the M6 tidy fix). Q5-relevant: the 6B XLS this round
is this lane's own capture (verified by fetch-log + own parser, not inherited).

## Closing

**data-ready ≠ scored-authorized.** Dims blocking scored use for 6B: standing
NO_GO_SCORE; fee layer UNDER REVIEW (A7 not run); BBO NOT_RUN (D5); **holiday/
deviation grid entirely NOT_OBTAINED**; 6 expiry cells 2023Q1–2024Q2
NOT_OBTAINED; F4-6B leg gated on gap-std anatomy NOT_RUN.
